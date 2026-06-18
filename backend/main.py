"""
FastAPI entrypoint for the Life K-Line backend.
"""

import json
import math
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from life_kline.analysis_catalog import get_analysis_type, list_analysis_types
from life_kline.service import LifeKlineService


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
BACKEND_DIR = os.path.dirname(__file__)


def load_env_file(file_path: str) -> None:
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", encoding="utf-8-sig") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


for env_filename in (".env", ".env.local"):
    load_env_file(os.path.join(BACKEND_DIR, env_filename))


def parse_cors_origins(origins_env: Optional[str]) -> list[str]:
    if not origins_env:
        return ["*"]

    normalized = origins_env.strip()
    if normalized == "*":
        return ["*"]

    return [origin.strip() for origin in normalized.split(",") if origin.strip()]


APP_HOST = os.getenv("LIFE_KLINE_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("LIFE_KLINE_PORT", "8000"))
CORS_ORIGINS = parse_cors_origins(os.getenv("LIFE_KLINE_CORS_ORIGINS"))
GEOCODE_TIMEOUT_SECONDS = float(os.getenv("LIFE_KLINE_GEOCODE_TIMEOUT", "4"))
AMAP_KEY = os.getenv("LIFE_KLINE_AMAP_KEY", "").strip()

GCJ02_AXIS = 6378245.0
GCJ02_EE = 0.00669342162296594323


def is_outside_china(lat: float, lon: float) -> bool:
    return not (73.66 < lon < 135.05 and 3.86 < lat < 53.55)


def transform_lat(x: float, y: float) -> float:
    value = (
        -100.0
        + 2.0 * x
        + 3.0 * y
        + 0.2 * y * y
        + 0.1 * x * y
        + 0.2 * math.sqrt(abs(x))
    )
    value += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    value += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    value += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return value


def transform_lon(x: float, y: float) -> float:
    value = (
        300.0
        + x
        + 2.0 * y
        + 0.1 * x * x
        + 0.1 * x * y
        + 0.1 * math.sqrt(abs(x))
    )
    value += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    value += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    value += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return value


def gcj02_to_wgs84(lat: float, lon: float) -> tuple[float, float]:
    if is_outside_china(lat, lon):
        return lat, lon

    d_lat = transform_lat(lon - 105.0, lat - 35.0)
    d_lon = transform_lon(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1 - GCJ02_EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((GCJ02_AXIS * (1 - GCJ02_EE)) / (magic * sqrt_magic) * math.pi)
    d_lon = (d_lon * 180.0) / (GCJ02_AXIS / sqrt_magic * math.cos(rad_lat) * math.pi)
    mg_lat = lat + d_lat
    mg_lon = lon + d_lon
    return lat * 2 - mg_lat, lon * 2 - mg_lon


def parse_public_geocode_result(provider_data: Any, query: str) -> Optional[Dict[str, Any]]:
    if not isinstance(provider_data, list) or not provider_data:
        return None

    top = provider_data[0]
    return {
        "lat": float(top.get("lat")),
        "lon": float(top.get("lon")),
        "display_name": top.get("display_name", query),
        "timezone": 8.0,
    }


def parse_amap_geocode_result(provider_data: Any, query: str) -> Optional[Dict[str, Any]]:
    if not isinstance(provider_data, dict):
        raise RuntimeError("Unexpected AMap geocoding payload.")

    if provider_data.get("status") != "1":
        detail = provider_data.get("info") or provider_data.get("infocode") or "AMap geocoding request failed."
        raise RuntimeError(str(detail))

    geocodes = provider_data.get("geocodes") or []
    if not geocodes:
        return None

    top = geocodes[0]
    location = top.get("location")
    if not location or "," not in location:
        raise RuntimeError("AMap geocoding response did not include coordinates.")

    lon_gcj, lat_gcj = [float(value.strip()) for value in location.split(",", 1)]
    lat_wgs84, lon_wgs84 = gcj02_to_wgs84(lat_gcj, lon_gcj)

    return {
        "lat": lat_wgs84,
        "lon": lon_wgs84,
        "display_name": top.get("formatted_address") or query,
        "timezone": 8.0,
    }


def get_geocode_unavailable_detail(timeout: bool) -> str:
    action = (
        "Geocoding providers timed out. Retry later or enter coordinates manually."
        if timeout
        else "Geocoding providers are temporarily unavailable. Retry later or enter coordinates manually."
    )
    if AMAP_KEY:
        return action
    return (
        f"{action} For more stable mainland China lookups, set "
        "LIFE_KLINE_AMAP_KEY in backend/.env."
    )


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class AnalysisDefinitionModel(FlexibleModel):
    key: str
    title: str
    tagline: str
    description: str
    category: str
    status: str
    subjects_count: int
    required_inputs: list[str]
    engines: list[str]
    modules: list[str]
    primary_cta: str
    output_route: str


class AnalysisSubject(FlexibleModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_time: str = Field(..., description="Birth time in ISO 8601 format")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    timezone: float = Field(default=8.0, description="UTC offset in hours")


class AnalysisRequest(FlexibleModel):
    analysis_type: str = Field(..., description="Registered analysis type key")
    subjects: list[AnalysisSubject] = Field(..., min_length=1, description="Input subjects")


class UserInput(FlexibleModel):
    gender: Optional[str] = None
    birth_time: str = Field(..., description="Birth time in ISO 8601 format")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    timezone: float = Field(default=8.0, description="UTC offset in hours")


class ReportMeta(FlexibleModel):
    generated_at: str
    engine_version: str


class UserInfo(FlexibleModel):
    gender: Optional[str] = None
    birth_time_local: str
    birth_time_utc: str
    lat: float
    lon: float
    timezone: str
    is_day_chart: bool


class TimingModel(FlexibleModel):
    start_age: float
    end_age: float
    start_date: str
    end_date: str
    duration_years: float


class LordsModel(FlexibleModel):
    major: str
    sub: Optional[str] = None


class TrendModel(FlexibleModel):
    bonus_coefficient: float
    type: str


class DomainsModel(FlexibleModel):
    career: float
    wealth: float
    relationship: float
    health: float
    family: float


class AstrologyModel(FlexibleModel):
    sign: str
    house: int
    dignity: str


class AscendantModel(FlexibleModel):
    sign: str
    degree: float


class NatalPlanetModel(FlexibleModel):
    sign: str
    house: int
    dignity: str


class NatalChartModel(FlexibleModel):
    ascendant: AscendantModel
    planets: Dict[str, NatalPlanetModel]


class CurrentPhaseModel(FlexibleModel):
    age_range: str
    major_lord: str
    sub_lord: str
    trend_type: str
    score: float
    keywords: list[str]
    feeling: str
    description: str


class PeriodModel(FlexibleModel):
    index: int
    timing: TimingModel
    lords: LordsModel
    trend: TrendModel
    domains: DomainsModel
    astrology: AstrologyModel
    type: str


class KlineDataModel(FlexibleModel):
    periods: list[PeriodModel]


class LifeKlineReport(FlexibleModel):
    meta: ReportMeta
    user_info: UserInfo
    kline_data: KlineDataModel
    natal_chart: Optional[NatalChartModel] = None
    current_phase: Optional[CurrentPhaseModel] = None
    life_model: Optional[Dict[str, Any]] = None


class ServiceResponse(FlexibleModel):
    status: str
    report_id: Optional[str] = None
    analysis: Optional[AnalysisDefinitionModel] = None
    data: LifeKlineReport


class AnalysisTypesResponse(FlexibleModel):
    status: str
    data: list[AnalysisDefinitionModel]


class GeocodeInput(FlexibleModel):
    query: str = Field(..., description="Location query text")


class GeocodeResult(FlexibleModel):
    status: str
    data: Dict[str, Any]


app = FastAPI(
    title="Life K-Line Engine API",
    description="Backend API for Life K-Line analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service: Optional[LifeKlineService] = None


def save_report_record(report_id: str, record: Dict[str, Any]) -> None:
    file_path = os.path.join(DATA_DIR, f"{report_id}.json")
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(record, file, ensure_ascii=False, indent=2)


def load_report_record(report_id: str) -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, f"{report_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read report: {exc}") from exc

    if isinstance(payload, dict) and "report" in payload:
        analysis = payload.get("analysis") or get_analysis_type("phase_navigation")
        report = payload.get("report") or {}
        return {
            "report_id": report_id,
            "analysis": analysis,
            "data": report,
        }

    return {
        "report_id": report_id,
        "analysis": get_analysis_type("phase_navigation"),
        "data": payload,
    }


def run_analysis(input_data: AnalysisRequest) -> Dict[str, Any]:
    if service is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    analysis_definition = get_analysis_type(input_data.analysis_type)
    if not analysis_definition:
        raise HTTPException(status_code=404, detail="Unknown analysis type")

    if analysis_definition.get("status") != "active":
        raise HTTPException(status_code=409, detail="This analysis type is not active yet")

    subjects = input_data.subjects
    expected_count = int(analysis_definition.get("subjects_count", 1))
    if len(subjects) != expected_count:
        raise HTTPException(
            status_code=400,
            detail=f"{analysis_definition['title']} requires {expected_count} subject(s).",
        )

    try:
        if input_data.analysis_type in {"phase_navigation", "natal_blueprint"}:
            subject = subjects[0]
            report = service.generate_report(
                birth_time_iso=subject.birth_time,
                lat=subject.lat,
                lon=subject.lon,
                timezone_offset=subject.timezone,
                gender=subject.gender,
            )
        else:
            raise HTTPException(status_code=501, detail="Analysis engine not implemented yet")

        report_id = str(uuid.uuid4())
        record = {
            "analysis": analysis_definition,
            "request": input_data.model_dump(),
            "report": report,
            "stored_at": datetime.utcnow().isoformat(),
        }
        save_report_record(report_id, record)

        return {
            "status": "success",
            "report_id": report_id,
            "analysis": analysis_definition,
            "data": report,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc


@app.on_event("startup")
async def startup_event() -> None:
    global service
    service = LifeKlineService()
    provider_names = ["nominatim_global", "nominatim_cn", "maps_co"]
    if AMAP_KEY:
        provider_names.insert(0, "amap")
    print(f"[life-kline] geocode providers: {', '.join(provider_names)}")


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Life K-Line Engine API is running. Visit /docs for documentation."}


@app.get("/api/analysis-types", response_model=AnalysisTypesResponse)
async def get_analysis_types() -> Dict[str, Any]:
    return {
        "status": "success",
        "data": list_analysis_types(),
    }


@app.post("/api/analyses", response_model=ServiceResponse)
async def create_analysis(input_data: AnalysisRequest) -> Dict[str, Any]:
    return run_analysis(input_data)


@app.get("/api/analyses/{report_id}", response_model=ServiceResponse)
async def get_analysis(report_id: str) -> Dict[str, Any]:
    record = load_report_record(report_id)
    return {
        "status": "success",
        "report_id": report_id,
        "analysis": record["analysis"],
        "data": record["data"],
    }


@app.post("/api/analyze", response_model=ServiceResponse)
async def analyze_life_path(input_data: UserInput) -> Dict[str, Any]:
    request_payload = AnalysisRequest(
        analysis_type="phase_navigation",
        subjects=[
            AnalysisSubject(
                gender=input_data.gender,
                birth_time=input_data.birth_time,
                lat=input_data.lat,
                lon=input_data.lon,
                timezone=input_data.timezone,
            )
        ],
    )
    return run_analysis(request_payload)


@app.get("/api/report/{report_id}", response_model=ServiceResponse)
async def get_report(report_id: str) -> Dict[str, Any]:
    record = load_report_record(report_id)
    return {
        "status": "success",
        "report_id": report_id,
        "analysis": record["analysis"],
        "data": record["data"],
    }


@app.post("/api/geocode", response_model=GeocodeResult)
async def geocode_location(input_data: GeocodeInput) -> Dict[str, Any]:
    import socket
    import urllib.error
    import urllib.parse
    import urllib.request

    query = input_data.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Please enter a valid location.")

    def is_timeout_error(exc: Exception) -> bool:
        if isinstance(exc, (TimeoutError, socket.timeout)):
            return True
        if isinstance(exc, urllib.error.URLError):
            reason = exc.reason
            if isinstance(reason, (TimeoutError, socket.timeout)):
                return True
            return "timed out" in str(reason).lower()
        return "timed out" in str(exc).lower()

    def fetch_json(url: str) -> Any:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "LifeKline-Geocoder/1.0 (contact: dev@lifekline.local)",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )
        with urllib.request.urlopen(request, timeout=GEOCODE_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        encoded_query = urllib.parse.quote(query)
        providers: list[Dict[str, Any]] = []
        if AMAP_KEY:
            amap_query = urllib.parse.urlencode({"address": query, "key": AMAP_KEY})
            providers.append(
                {
                    "name": "amap",
                    "url": f"https://restapi.amap.com/v3/geocode/geo?{amap_query}",
                    "parser": parse_amap_geocode_result,
                }
            )

        providers.extend(
            [
                {
                    "name": "nominatim_global",
                    "url": f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1",
                    "parser": parse_public_geocode_result,
                },
                {
                    "name": "nominatim_cn",
                    "url": f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1&countrycodes=cn",
                    "parser": parse_public_geocode_result,
                },
                {
                    "name": "maps_co",
                    "url": f"https://geocode.maps.co/search?q={encoded_query}&format=json&limit=1",
                    "parser": parse_public_geocode_result,
                },
            ]
        )

        result = None
        provider_errors: list[str] = []
        timeout_count = 0
        successful_responses = 0

        for provider in providers:
            provider_name = provider["name"]
            try:
                provider_data = fetch_json(provider["url"])
                normalized_result = provider["parser"](provider_data, query)
                successful_responses += 1
                if normalized_result:
                    result = normalized_result
                    break
            except Exception as provider_exc:
                provider_errors.append(f"{provider_name}: {provider_exc}")
                if is_timeout_error(provider_exc):
                    timeout_count += 1

        if not result:
            if timeout_count == len(providers):
                raise HTTPException(
                    status_code=504,
                    detail=get_geocode_unavailable_detail(timeout=True),
                )
            if successful_responses > 0:
                raise HTTPException(status_code=404, detail="No matching location was found.")
            if provider_errors:
                raise HTTPException(
                    status_code=502,
                    detail=get_geocode_unavailable_detail(timeout=False),
                )
            raise HTTPException(status_code=404, detail="No matching location was found.")

        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {exc}") from exc


@app.get("/api/transit/now")
async def get_current_transit() -> Dict[str, Any]:
    if service is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    try:
        from life_kline.constants import Planet

        now_utc = datetime.utcnow()
        chart = service.engine.calculate_chart(now_utc, 39.9, 116.4)

        planets: Dict[str, Dict[str, Any]] = {}
        target_planets = [
            Planet.SUN,
            Planet.MOON,
            Planet.MERCURY,
            Planet.VENUS,
            Planet.MARS,
            Planet.JUPITER,
            Planet.SATURN,
        ]

        for planet in target_planets:
            info = chart.get_planet_info(planet)
            if info:
                planets[planet.value] = {
                    "sign": info.sign.value,
                    "degree": round(info.degree, 1),
                    "retrograde": info.is_retrograde,
                }

        interpretation = (
            "Current cosmic weather favors planning, review, and long-horizon decisions."
        )
        if planets.get("MERCURY", {}).get("retrograde"):
            interpretation = (
                "Mercury is retrograde. Double-check communication details and revisit old plans."
            )

        return {
            "status": "success",
            "data": {
                "timestamp": now_utc.isoformat(),
                "planets": planets,
                "interpretation": interpretation,
            },
        }
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
