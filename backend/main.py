"""
FastAPI entrypoint for the Life K-Line backend.
"""

import json
import math
import os
import sys
import uuid
import random
import hashlib
import time as _time
import anyio
from datetime import datetime, timedelta, timezone
from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
# Load .env before any application imports that depend on environment variables
_BACKEND_DIR = os.path.dirname(__file__)

def _load_env_file(file_path: str) -> None:
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r', encoding='utf-8-sig') as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ[key] = value

for _env_filename in ('.env', '.env.local'):
    _load_env_file(os.path.join(_BACKEND_DIR, _env_filename))

sys.path.insert(0, os.path.abspath(os.path.join(_BACKEND_DIR, '..', 'src')))

from life_kline.analysis_catalog import get_analysis_type, list_analysis_types
from life_kline.service import LifeKlineService

from backend.database import get_db, init_db, _uid, _now
from backend import admin as _admin
from backend import dao as _dao
from fastapi import Depends
from typing import Annotated



DATA_DIR = os.path.join(_BACKEND_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
BACKEND_DIR = _BACKEND_DIR


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


def _geocode_place(query: str) -> tuple[float, float]:
    """Geocode a place name. Returns (lat, lon) or (0.0, 0.0) on any failure."""
    import socket
    import urllib.error
    import urllib.parse
    import urllib.request

    if not query or not query.strip():
        return (0.0, 0.0)

    query = query.strip()

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

        for provider in providers:
            try:
                provider_data = fetch_json(provider["url"])
                normalized_result = provider["parser"](provider_data, query)
                if normalized_result:
                    return (normalized_result["lat"], normalized_result["lon"])
            except Exception:
                continue
    except Exception:
        pass

    return (0.0, 0.0)


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


class ServiceResponse(FlexibleModel):
    status: str
    report_id: Optional[str] = None
    analysis: Optional[AnalysisDefinitionModel] = None
    data: Dict[str, Any]


class AnalysisTypesResponse(FlexibleModel):
    status: str
    data: list[AnalysisDefinitionModel]


class GeocodeInput(FlexibleModel):
    query: str = Field(..., description="Location query text")


class GeocodeResult(FlexibleModel):
    status: str
    data: Dict[str, Any]


# ── 用户系统 ──────────────────────────────────────────────

JWT_SECRET = os.getenv("LIFE_KLINE_JWT_SECRET", "")
JWT_SECRET_DEFAULT = "dev-secret-change-in-production"

if not JWT_SECRET or JWT_SECRET == JWT_SECRET_DEFAULT:
    raise RuntimeError(
        "环境变量 LIFE_KLINE_JWT_SECRET 未设置或使用了默认值。"
        "请在 backend/.env 中配置一个强随机字符串，例如：\n"
        "  LIFE_KLINE_JWT_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')\n"
        "这是生产环境的安全要求，启动已终止。"
    )


def _make_token(user_id: str) -> str:
    payload = f"{user_id}:{int(_time.time())}"
    sig = hashlib.sha256(f"{payload}:{JWT_SECRET}".encode()).hexdigest()[:16]
    return f"{payload}:{sig}"


def _parse_token(token: str) -> Optional[str]:
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id, ts, sig = parts
        expected = hashlib.sha256(f"{user_id}:{ts}:{JWT_SECRET}".encode()).hexdigest()[:16]
        if sig != expected:
            return None
        if int(_time.time()) - int(ts) > 86400 * 30:
            return None
        return user_id
    except Exception:
        return None


class SendCodeInput(FlexibleModel):
    phone: str


class VerifyCodeInput(FlexibleModel):
    phone: str
    code: str


class ProfileInput(FlexibleModel):
    name: str = ""
    gender: str = ""
    birth_time: str
    lat: float = 0.0
    lon: float = 0.0
    timezone: float = 8.0
    birth_place: str = ""
    house_system: str = "B"
    daylight_saving: bool = False
    residence_place: str = ""
    residence_lat: float = 0.0
    residence_lon: float = 0.0


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
    """落盘：DB 优先，JSON 兜底。"""
    user_id = record.get("user_id") or ""
    profile_id = record.get("profile_id") or ""
    analysis_type = (record.get("analysis") or {}).get("key") or "phase_navigation"
    report_data = record.get("report") or {}
    kline_summary = ""
    if isinstance(report_data, dict):
        kline_summary = (
            report_data.get("summary", "")
            or report_data.get("hero", {}).get("core_theme", "")
            or ""
        )[:500]

    try:
        if user_id:
            _dao.save_report(
                report_id=report_id,
                user_id=user_id,
                profile_id=profile_id or "",
                analysis_type=analysis_type,
                report_data=record,
                kline_summary=kline_summary,
            )
    except Exception:
        pass

    # 保留 JSON 兜底
    file_path = os.path.join(DATA_DIR, f"{report_id}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(record, file, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_report_record(report_id: str) -> Dict[str, Any]:
    """读报告：DB 优先，JSON 兜底。"""
    try:
        row = _dao.load_report(report_id)
        if row:
            payload = row.get("report_data") or {}
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
    except Exception:
        pass

    # 2) JSON 兜底
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


def _report_owner(report_id: str) -> Optional[str]:
    """返回报告归属的 user_id。DB 优先，JSON 兜底；不存在返回 None。"""
    try:
        row = _dao.load_report(report_id)
        if row is not None:
            return row.get("user_id") or ""
    except Exception:
        pass
    file_path = os.path.join(DATA_DIR, f"{report_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                payload = json.load(file)
            if isinstance(payload, dict):
                return payload.get("user_id") or ""
        except Exception:
            return None
    return None


def require_report_owner(report_id: str, authorization: str) -> str:
    """校验调用者是报告归属者。

    规则（不允许游客创建报告，分享功能后续单独实现）：
      - 报告不存在 → 404
      - 无有效 token → 401
      - token 的 user_id 与报告 owner 不一致（含无主报告）→ 403
    返回校验通过的 user_id。
    """
    owner = _report_owner(report_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="Report not found")
    uid = _parse_token((authorization or "").replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    if owner != uid:
        raise HTTPException(status_code=403, detail="无权访问该报告")
    return uid


def load_owned_report(report_id: str, authorization: str) -> Dict[str, Any]:
    """校验归属后加载报告，供只读端点统一调用。"""
    require_report_owner(report_id, authorization)
    return load_report_record(report_id)


def run_analysis(input_data: AnalysisRequest, user_id: str = "", profile_id: str = "") -> Dict[str, Any]:
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
        elif input_data.analysis_type == "monthly_lunar_return":
            subject = subjects[0]
            report = service.generate_monthly_lunar_return(
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
            "user_id": user_id,
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
async def create_analysis(input_data: AnalysisRequest, authorization: str = Header(default="")) -> Dict[str, Any]:
    # 不允许游客创建报告：必须携带有效 token，禁止产生无主报告。
    token = authorization.replace("Bearer ", "")
    uid = _parse_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录后再创建分析报告")
    user_id = uid
    profile_id = ""
    if input_data.subjects:
        s = input_data.subjects[0]
        profile_id = _uid()
        try:
            db = get_db()
            db.execute(
                "INSERT INTO profiles (id, user_id, name, gender, birth_time, lat, lon, timezone, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (profile_id, user_id, s.name or "", s.gender or "", s.birth_time, s.lat, s.lon, s.timezone, 0, _now()),
            )
            db.commit()
            db.close()
        except Exception:
            profile_id = ""
    return await anyio.to_thread.run_sync(
        lambda: run_analysis(input_data, user_id=user_id, profile_id=profile_id)
    )


@app.get("/api/reports/history")
async def report_history(authorization: str = Header(default="")) -> Dict[str, Any]:
    token = authorization.replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    rows = _dao.list_reports_by_user(user_id=user_id, limit=50)
    # 兼容：columns = id / profile_id / analysis_type / created_at / kline_summary
    out = []
    for r in rows:
        out.append({
            "id": r.get("id"),
            "report_id": r.get("id"),
            "profile_id": r.get("profile_id", ""),
            "analysis_type": r.get("analysis_type", ""),
            "kline_summary": r.get("kline_summary", ""),
            "created_at": r.get("created_at", ""),
        })
    return {"status": "success", "reports": out}


@app.get("/api/analyses/{report_id}", response_model=ServiceResponse)
async def get_analysis(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    record = load_owned_report(report_id, authorization)
    return {
        "status": "success",
        "report_id": report_id,
        "analysis": record["analysis"],
        "data": record["data"],
    }


# ═══════════════════════════════════════════════════════════════
# 本命盘 API（结构化数据，含行星 / 四轴 / 宫位 / 相位 / 接纳 / 状态 / 法达）
# ═══════════════════════════════════════════════════════════════

# 中文星座映射（与 PRD 风格保持一致）
_NATAL_SIGN_ZH: Dict[str, str] = {
    "ARIES": "白羊",
    "TAURUS": "金牛",
    "GEMINI": "双子",
    "CANCER": "巨蟹",
    "LEO": "狮子",
    "VIRGO": "处女",
    "LIBRA": "天秤",
    "SCORPIO": "天蝎",
    "SAGITTARIUS": "射手",
    "CAPRICORN": "摩羯",
    "AQUARIUS": "水瓶",
    "PISCES": "双鱼",
}

# 相位类型中英文映射
_NATAL_ASPECT_ZH: Dict[str, str] = {
    "CONJUNCTION": "合相",
    "SEXTILE": "六合",
    "SQUARE": "刑相",
    "TRINE": "拱相",
    "OPPOSITION": "冲相",
    "QUINCUNX": "梅花相",
}

_NATAL_ASPECT_NATURE: Dict[str, str] = {
    "CONJUNCTION": "neutral",
    "SEXTILE": "harmonious",
    "SQUARE": "challenging",
    "TRINE": "harmonious",
    "OPPOSITION": "challenging",
    "QUINCUNX": "neutral",
}

# 法达主题（按大运主星）
_NATAL_FIRDARIA_THEME: Dict[str, str] = {
    "sun": "自我表达与名望",
    "venus": "关系与价值",
    "mercury": "学习与沟通",
    "moon": "情感与根基",
    "saturn": "结构与责任",
    "jupiter": "信仰与扩张",
    "mars": "行动与突破",
    "north_node": "命运转折",
    "south_node": "内在沉淀",
}

# 黄道状态含义
_NATAL_DIGNITY_MEANING: Dict[str, Dict[str, str]] = {
    "domicile": {"zh": "庙旺", "meaning": "入庙得位，力量充沛，可自如发挥"},
    "exaltation": {"zh": "擢升", "meaning": "被高看一眼，做事有外力加持"},
    "detriment": {"zh": "失势", "meaning": "在本不擅长的领域，需要额外努力"},
    "fall": {"zh": "落陷", "meaning": "与环境相克，节奏需要调整"},
    "peregrine": {"zh": "平常", "meaning": "中性位置，状态依靠其他配置激活"},
}


def _natal_format_degree(degree: float) -> str:
    """xx°xx′ 格式（度·分）。"""
    if degree is None:
        return ""
    d = int(degree)
    minutes_total = round((float(degree) - d) * 60.0 + 1e-9)
    if minutes_total >= 60:
        d += 1
        minutes_total = 0
    return f"{d}°{int(minutes_total):02d}′"


def _natal_format_orb(orb: float) -> str:
    """容许度 0°xx′ 格式。"""
    if orb is None:
        return ""
    d = int(orb)
    minutes_total = round((float(orb) - d) * 60.0 + 1e-9)
    if minutes_total >= 60:
        d += 1
        minutes_total = 0
    return f"{d}°{int(minutes_total):02d}′"


def _natal_dignity_state(planet: Planet, sign: Sign) -> str:
    """根据行星 + 落座返回 5 类状态之一。"""
    from life_kline.constants import (
        DOMICILE_SIGNS, EXALTATION_SIGNS, DETRIMENT_SIGNS, FALL_SIGNS,
    )
    if sign in DOMICILE_SIGNS.get(planet, []):
        return "domicile"
    if sign in EXALTATION_SIGNS.get(planet, []):
        return "exaltation"
    if sign in DETRIMENT_SIGNS.get(planet, []):
        return "detriment"
    if sign in FALL_SIGNS.get(planet, []):
        return "fall"
    return "peregrine"


def _natal_reception_zh(reception_type: str) -> str:
    """接纳类型 → 中文标签。"""
    return {
        "DOMICILE": "接纳(庙宫)",
        "EXALTATION": "接纳(擢升)",
        "DETRIMENT": "接纳(失势)",
        "FALL": "接纳(落陷)",
        "MUTUAL_DOMICILE": "互容(庙庙)",
        "MUTUAL_EXALTATION": "互容(旺旺)",
        "MUTUAL_OTHER": "互容(其他)",
    }.get(reception_type, "接纳")


def _build_natal_chart_response(report_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """
    构造完整的本命盘 API 响应。

    数据来源：
    1) report["natal_chart"]（已有结构，含行星 / 宫头 / 上升 / 命主星）
    2) EphemerisEngine.calculate_chart() —— 用 user_info 重建实时星盘
    3) aspects.detect_aspect_between() 遍历所有行星对
    4) receptions.check_mutual_reception() 遍历所有行星对
    5) firdaria.calculate_firdaria_periods(max_age=100) 扩展法达
    """
    from life_kline.constants import (
        Planet, Sign, AspectType,
        DOMICILE_SIGNS, EXALTATION_SIGNS, DETRIMENT_SIGNS, FALL_SIGNS,
    )
    from life_kline.ephemeris import EphemerisEngine
    from life_kline.aspects import detect_aspect_between
    from life_kline.receptions import check_mutual_reception
    from life_kline.firdaria import calculate_firdaria_periods
    from life_kline.models import ChartData

    report_data = record.get("data", {}) or {}
    user_info = report_data.get("user_info", {}) or {}
    natal_chart_payload = report_data.get("natal_chart", {}) or {}

    planets_payload = natal_chart_payload.get("planets", {}) or {}

    # ── 1) 尝试用 EphemerisEngine 重建 ChartData，获取权威行星位置 ──
    chart: Optional[ChartData] = None
    birth_time_iso = (
        user_info.get("birth_time_utc")
        or user_info.get("birth_time_local")
        or ""
    )
    try:
        if birth_time_iso and service is not None:
            birth_dt = datetime.fromisoformat(birth_time_iso)
            lat = float(user_info.get("lat", 0.0) or 0.0)
            lon = float(user_info.get("lon", 0.0) or 0.0)
            chart = service.engine.calculate_chart(birth_dt, lat, lon)
    except Exception:
        chart = None

    # ── 2) 行星数据：sign_raw 用 chart.planets（权威），否则用 natal_chart_payload ──
    planets_out: Dict[str, Dict[str, Any]] = {}
    target_planets = [
        Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
        Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
    ]

    for planet in target_planets:
        key = planet.value.lower()
        sign_value = ""
        degree_value = 0.0

        if chart is not None:
            info = chart.get_planet_info(planet)
            if info is not None:
                sign_value = info.sign.value
                degree_value = float(info.degree)
        if not sign_value:
            # fallback 到 report 中的 payload
            p_payload = planets_payload.get(planet.value) or planets_payload.get(key) or {}
            sign_value = p_payload.get("sign", "")
            degree_value = float(p_payload.get("degree", 0.0) or 0.0)

        if not sign_value:
            continue

        sign_zh = _NATAL_SIGN_ZH.get(sign_value.upper(), sign_value)
        planets_out[key] = {
            "sign": sign_zh,
            "degree": _natal_format_degree(degree_value),
            "sign_raw": sign_value.lower(),
        }

    # ── 3) 四轴（从 chart 或 natal_chart_payload）──
    angles_out: Dict[str, Dict[str, Any]] = {}

    def _set_angle(name: str, sign_value: str, degree_value: float) -> None:
        if not sign_value:
            return
        sign_zh = _NATAL_SIGN_ZH.get(sign_value.upper(), sign_value)
        angles_out[name] = {
            "sign": sign_zh,
            "degree": _natal_format_degree(degree_value),
        }

    asc_payload = natal_chart_payload.get("ascendant", {}) or {}

    if chart is not None and getattr(chart, "houses", None):
        # ASC = 第 1 宫头，MC = 第 10 宫头，DESC = 第 7 宫头，IC = 第 4 宫头
        houses_attr = chart.houses
        if len(houses_attr) >= 12:
            asc_sign, asc_deg = houses_attr[0]
            ic_sign, ic_deg = houses_attr[3]
            desc_sign, desc_deg = houses_attr[6]
            mc_sign, mc_deg = houses_attr[9]
            _set_angle("asc", asc_sign.value, float(asc_deg))
            _set_angle("ic", ic_sign.value, float(ic_deg))
            _set_angle("desc", desc_sign.value, float(desc_deg))
            _set_angle("mc", mc_sign.value, float(mc_deg))

    # ASC 用 asc_payload 兜底
    if not angles_out.get("asc"):
        _set_angle("asc", asc_payload.get("sign", ""), float(asc_payload.get("degree", 0.0) or 0.0))

    # ── 4) 宫位列表（1-12） ──
    houses_out: List[Dict[str, Any]] = []
    if chart is not None and getattr(chart, "houses", None):
        houses_attr = chart.houses
        for idx in range(min(12, len(houses_attr))):
            sign_value, degree_value = houses_attr[idx]
            houses_out.append({
                "house": idx + 1,
                "sign": _NATAL_SIGN_ZH.get(sign_value.upper(), sign_value),
                "degree": _natal_format_degree(float(degree_value)),
            })
    else:
        # fallback
        for h in natal_chart_payload.get("houses", []) or []:
            sign_value = h.get("sign", "")
            if not sign_value:
                continue
            houses_out.append({
                "house": int(h.get("house", 0)),
                "sign": _NATAL_SIGN_ZH.get(sign_value.upper(), sign_value),
                "degree": _natal_format_degree(float(h.get("degree", 0.0) or 0.0)),
            })

    # ── 5) 相位表 ──
    aspects_out: List[Dict[str, Any]] = []

    if chart is not None:
        chart_planets = list(chart.planets.keys())
        for i in range(len(chart_planets)):
            for j in range(i + 1, len(chart_planets)):
                p1 = chart_planets[i]
                p2 = chart_planets[j]
                aspect = detect_aspect_between(p1, p2, chart)
                if aspect is None:
                    continue

                actual_angle = float(aspect.actual_angle)
                orb = float(aspect.orb)
                aspect_type_key = aspect.aspect_type.value
                aspects_out.append({
                    "planet1": p1.value.lower(),
                    "planet2": p2.value.lower(),
                    "type": aspect_type_key.lower(),
                    "type_zh": _NATAL_ASPECT_ZH.get(aspect_type_key, aspect_type_key),
                    "degree": _natal_format_degree(actual_angle),
                    "orb": _natal_format_orb(orb),
                    "nature": _NATAL_ASPECT_NATURE.get(aspect_type_key, "neutral"),
                })

    # 按容许度从紧到宽排序，精确相位在前
    aspects_out.sort(key=lambda item: float(item["orb"].replace("°", "").replace("′", "")) if item["orb"] else 99)

    # ── 6) 互溶接纳表 ──
    receptions_out: List[Dict[str, Any]] = []

    if chart is not None:
        chart_planets = list(chart.planets.keys())
        for i in range(len(chart_planets)):
            for j in range(i + 1, len(chart_planets)):
                p1 = chart_planets[i]
                p2 = chart_planets[j]
                mutual = check_mutual_reception(p1, p2, chart)
                if mutual is None:
                    continue

                m_type_value = mutual["type"].value
                sign1 = chart.get_planet_info(p1).sign.value if chart.get_planet_info(p1) else ""
                sign2 = chart.get_planet_info(p2).sign.value if chart.get_planet_info(p2) else ""

                receptions_out.append({
                    "from": p1.value.lower(),
                    "to": p2.value.lower(),
                    "type": m_type_value.lower(),
                    "type_zh": _natal_reception_zh(m_type_value),
                    "description": (
                        f"{p1.value}在{sign1}，{p2.value}在{sign2}，"
                        f"形成{_natal_reception_zh(m_type_value)}"
                    ),
                })

    # ── 7) 黄道状态 ──
    zodiac_state_out: List[Dict[str, Any]] = []

    for planet in target_planets:
        key = planet.value.lower()
        if key not in planets_out:
            continue
        sign_value = planets_out[key]["sign_raw"].upper()
        try:
            sign_enum = Sign(sign_value)
        except ValueError:
            continue

        state = _natal_dignity_state(planet, sign_enum)
        state_meta = _NATAL_DIGNITY_MEANING.get(state, {"zh": state, "meaning": ""})

        zodiac_state_out.append({
            "planet": key,
            "sign": planets_out[key]["sign"],
            "degree": planets_out[key]["degree"],
            "state": state,
            "state_zh": state_meta["zh"],
            "meaning": state_meta["meaning"],
        })

    # ── 8) 法达周期（扩展到 100 年）──
    firdaria_out: List[Dict[str, Any]] = []
    is_day_chart = bool(user_info.get("is_day_chart", True))
    if chart is None:
        # 没有 chart 时从 natal_chart_payload 推断昼夜
        sect_label = (natal_chart_payload.get("sect") or "day").lower()
        is_day_chart = sect_label != "night"

    try:
        periods = calculate_firdaria_periods(is_day_chart=is_day_chart, max_age=100.0)
    except Exception:
        periods = []

    # 仅保留大运级别（一行 = 一个 major），子序列内嵌 sub_lords
    # 实现策略：以 start_age 找每个主运的第一个子项
    grouped: List[Dict[str, Any]] = []
    current_major_key = None
    for p in periods:
        major_key = p.major_lord.value.lower()
        if major_key != current_major_key:
            current_major_key = major_key
            grouped.append({
                "start_age": round(p.start_age, 2),
                "end_age": round(p.end_age, 2),
                "lord": major_key,
                "lord_zh": "",
                "sub_lords": [],
                "theme": _NATAL_FIRDARIA_THEME.get(major_key, "—"),
            })
        # 收集子序列（交点期无子运，沿用主运标签）
        if grouped:
            sub_key = major_key if p.sub_lord is None else p.sub_lord.value.lower()
            grouped[-1]["sub_lords"].append(sub_key)

    # 用 service.PLANET_LABELS 填充中文名
    try:
        from life_kline.service import PLANET_LABELS as _PLANET_LABELS  # noqa: WPS433
        for entry in grouped:
            try:
                entry["lord_zh"] = _PLANET_LABELS.get(Planet(entry["lord"].upper()), entry["lord"])
            except Exception:
                entry["lord_zh"] = entry["lord"]
    except Exception:
        for entry in grouped:
            entry["lord_zh"] = entry["lord"]

    firdaria_out = grouped

    return {
        "status": "success",
        "data": {
            "report_id": report_id,
            "planets": planets_out,
            "angles": angles_out,
            "houses": houses_out,
            "aspects": aspects_out,
            "receptions": receptions_out,
            "zodiac_state": zodiac_state_out,
            "firdaria": firdaria_out,
        },
    }


@app.post("/api/analyze", response_model=ServiceResponse)
async def analyze_life_path(input_data: UserInput, authorization: str = Header(default="")) -> Dict[str, Any]:
    # 遗留端点：同样不允许游客创建报告，必须携带有效 token。
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录后再创建分析报告")
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
    return await anyio.to_thread.run_sync(
        lambda: run_analysis(request_payload, user_id=uid)
    )


@app.get("/api/report/{report_id}", response_model=ServiceResponse)
async def get_report(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    record = load_owned_report(report_id, authorization)
    return {
        "status": "success",
        "report_id": report_id,
        "analysis": record["analysis"],
        "data": record["data"],
    }


# ═══════════════════════════════════════════════════════════════
# 角色系统 API
# ═══════════════════════════════════════════════════════════════

class CharacterChatInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    sign: str = Field(..., description="Sign key, e.g. 'ARIES'")
    topic: str = Field(default="personal", description="Domain key")
    message: Optional[str] = Field(default=None)
    history: Optional[list[dict]] = Field(default_factory=list)

class CouncilInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    topic: str = Field(..., description="Topic to discuss")
    signs: Optional[list[str]] = Field(default=None, description="Signs to include; auto-selects top 3 if omitted")
    message: Optional[str] = Field(default=None)


@app.get("/api/characters/{report_id}")
async def get_character_profiles(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    """获取12星座个性化角色画像"""
    record = load_owned_report(report_id, authorization)
    data = record.get("data", {})
    characters = data.get("characters", {})
    if not characters:
        raise HTTPException(status_code=404, detail="Character profiles not found in this report")
    return {"status": "success", "report_id": report_id, "data": characters}


@app.get("/api/characters/{report_id}/daily")
async def get_daily_activation(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    """获取今日角色激活度和登场角色"""
    record = load_owned_report(report_id, authorization)
    user_info = record.get("data", {}).get("user_info", {})
    if not user_info:
        raise HTTPException(status_code=400, detail="User info missing from report")

    from life_kline.ephemeris import EphemerisEngine
    from life_kline.firdaria import FirdariaPeriod, calculate_firdaria_periods
    from life_kline.constants import Planet
    from life_kline.characters.character_engine import CharacterEngine
    from life_kline.awakening.daily_engine import DailyAwakeningEngine

    def _compute():
        # 重建本命盘
        engine = EphemerisEngine()
        birth_time = datetime.fromisoformat(user_info.get("birth_time_utc", user_info.get("birth_time_local", "")))
        lat = user_info.get("lat", 0.0)
        lon = user_info.get("lon", 0.0)
        chart = engine.calculate_chart(birth_time, lat, lon)

        # 当前法达周期
        is_day = user_info.get("is_day_chart", True)
        birth_time_local = datetime.fromisoformat(user_info.get("birth_time_local", user_info.get("birth_time_utc", "")))
        current_age = (datetime.now() - birth_time_local.replace(tzinfo=None)).days / 365.2422
        periods = calculate_firdaria_periods(is_day)
        current_period = None
        for p in periods:
            if p.start_age <= current_age < p.end_age:
                current_period = p
                break

        # 计算每日激活
        char_engine = CharacterEngine(chart)
        daily_engine = DailyAwakeningEngine(chart, char_engine, current_period)
        return daily_engine.compute_daily_activation()

    activation = await anyio.to_thread.run_sync(_compute)

    return {"status": "success", "report_id": report_id, "data": activation.to_dict()}


@app.get("/api/natal-chart/{report_id}")
async def get_natal_chart(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    """获取本命盘详情：星盘数据 + 相位 + 接纳/互溶 + 100年法达周期。"""
    from life_kline.firdaria import calculate_firdaria_periods
    from life_kline.constants import Planet
    from life_kline.service import planet_label

    record = load_owned_report(report_id, authorization)
    data = record.get("data", {})
    natal_chart = data.get("natal_chart", {}) or {}
    advanced = data.get("advanced_patterns", {}) or {}
    user_info = data.get("user_info", {}) or {}

    if not natal_chart:
        raise HTTPException(status_code=404, detail="本命盘数据不存在，请先完成分析")

    is_day_chart = bool(user_info.get("is_day_chart", True))

    # 计算当前年龄
    current_age = 0.0
    birth_time_local = user_info.get("birth_time_local") or user_info.get("birth_time_utc")
    if birth_time_local:
        try:
            birth_dt = datetime.fromisoformat(birth_time_local)
            current_age = (datetime.now() - birth_dt.replace(tzinfo=None)).days / 365.2422
        except Exception:
            current_age = 0.0

    def _planet_zh(planet_value: str) -> str:
        if not planet_value:
            return ""
        return planet_label(planet_value) or planet_value

    # 计算法达周期 (100 年)
    periods = calculate_firdaria_periods(is_day_chart, max_age=100.0)
    firdaria_payload = []
    for p in periods:
        major_lord = p.major_lord
        sub_lord = p.sub_lord
        major_value = major_lord.value if hasattr(major_lord, "value") else str(major_lord)
        sub_value = sub_lord.value if sub_lord and hasattr(sub_lord, "value") else (str(sub_lord) if sub_lord else "")
        is_node = major_lord in (Planet.NORTH_NODE, Planet.SOUTH_NODE)
        firdaria_payload.append({
            "start_age": round(p.start_age, 2),
            "end_age": round(p.end_age, 2),
            "lord": major_value,
            "lord_zh": _planet_zh(major_value),
            "sub_lord": sub_value,
            "sub_lord_zh": _planet_zh(sub_value),
            "is_node": is_node,
        })

    # 整理接纳/互溶
    receptions = []
    for grp in (advanced.get("reception_groups") or []):
        for guest in (grp.get("guests") or []):
            from_value = guest.get("planet") or ""
            to_value = grp.get("receiver") or ""
            receptions.append({
                "from": from_value,
                "from_zh": guest.get("label") or _planet_zh(from_value),
                "to": to_value,
                "to_zh": grp.get("receiver_label") or _planet_zh(to_value),
                "type": "reception",
                "type_zh": "庙宫接纳",
                "description": grp.get("line") or grp.get("summary") or "",
            })

    for m in (advanced.get("mutual_receptions") or []):
        pair = m.get("pair") or []
        labels = m.get("labels") or []
        if len(pair) >= 2:
            p1 = str(pair[0])
            p2 = str(pair[1])
            receptions.append({
                "from": p1,
                "from_zh": labels[0] if len(labels) > 0 else _planet_zh(p1),
                "to": p2,
                "to_zh": labels[1] if len(labels) > 1 else _planet_zh(p2),
                "type": "mutual_reception",
                "type_zh": "互溶",
                "description": m.get("line") or m.get("summary") or "",
            })

    return {
        "status": "success",
        "report_id": report_id,
        "data": {
            "natal_chart": natal_chart,
            "firdaria_periods": firdaria_payload,
            "receptions": receptions,
            "is_day_chart": is_day_chart,
            "current_age": round(current_age, 2),
        },
    }


@app.post("/api/characters/{report_id}/chat")
async def chat_with_character(report_id: str, body: CharacterChatInput, authorization: str = Header(default="")) -> Dict[str, Any]:
    """与指定星座角色对话"""
    record = load_owned_report(report_id, authorization)
    data = record.get("data", {})

    from life_kline.constants import Sign
    try:
        sign = Sign(body.sign.upper())
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid sign: {body.sign}")

    # 获取角色画像
    characters = data.get("characters", {}).get("characters", {})
    char_data = characters.get(sign.value, {})
    if not char_data:
        raise HTTPException(status_code=404, detail=f"Character {body.sign} not found")

    persona = char_data.get("persona", {})

    # 构建角色风格的回复（规则驱动，不依赖 LLM）
    topic_labels: dict[str, str] = {
        "personal": "你的性格底色",
        "career": "事业方向",
        "finance": "财务格局",
        "romance": "桃花感情",
        "marriage": "婚姻画像",
        "family": "原生家庭",
        "work_skill": "工作技能",
        "education": "学业方向",
        "health": "健康体质",
        "appearance": "外形气质",
        "partnership": "事业合伙",
        "children": "亲子关系",
    }
    topic_label = topic_labels.get(body.topic, body.topic)

    # 领域洞察
    domain_data = data.get("domains", {}).get(body.topic, {})
    core_theme = domain_data.get("core_theme", "")
    structure = domain_data.get("structure", "")[:300]

    # 角色声音
    voice_tone = persona.get("voice_tone", "")
    advice_approach = persona.get("advice_approach", "")
    archetype = persona.get("archetype", "")
    gift = persona.get("gift_to_user", "")

    user_msg = body.message or ""
    has_user_msg = bool(user_msg.strip())

    # 构造回复
    if has_user_msg:
        response = (
            f"你说的'{user_msg[:50]}{'...' if len(user_msg) > 50 else ''}'——我听到了。\n\n"
            f"从我的视角来看（我是你的{archetype}），关于{topic_label}：\n"
            f"{core_theme}\n\n"
            f"{structure[:200]}{'...' if len(structure) > 200 else ''}\n\n"
            f"{gift}"
        )
    else:
        response = (
            f"嘿，关于{topic_label}，让我用我的方式跟你说——\n\n"
            f"{core_theme}\n\n"
            f"{structure[:200]}{'...' if len(structure) > 200 else ''}\n\n"
            f"我的风格是：{advice_approach}\n\n"
            f"你想具体聊聊什么？"
        )

    suggested_followup = persona.get("expertise_domains", ["personal"])[0]

    # 记录对话到成长追踪器
    try:
        from life_kline.growth.growth_tracker import GrowthTracker
        tracker = GrowthTracker(report_id)
        tracker.record_conversation(sign, body.topic, body.message or "(开场)", response)
    except Exception:
        pass  # 成长追踪失败不影响对话

    return {
        "status": "success",
        "data": {
            "character": sign.value,
            "character_name": persona.get("name", sign.value),
            "response": response,
            "emotional_tone": persona.get("element", "火"),
            "suggested_followup": suggested_followup,
        },
    }


@app.post("/api/characters/{report_id}/council")
async def character_council(report_id: str, body: CouncilInput, authorization: str = Header(default="")) -> Dict[str, Any]:
    """获取多个角色对同一话题的不同视角"""
    record = load_owned_report(report_id, authorization)
    data = record.get("data", {})

    from life_kline.constants import Sign
    characters = data.get("characters", {}).get("characters", {})

    # 选择角色：指定或自动选 top 3
    if body.signs:
        selected = body.signs
    else:
        sorted_chars = data.get("characters", {}).get("sorted_by_presence", [])
        selected = [c["sign"] for c in sorted_chars[:3]]

    topic_labels: dict[str, str] = {
        "personal": "你的性格底色", "career": "事业方向", "finance": "财务格局",
        "romance": "桃花感情", "marriage": "婚姻画像", "family": "原生家庭",
        "work_skill": "工作技能", "education": "学业方向", "health": "健康体质",
    }
    topic_label = topic_labels.get(body.topic, body.topic)
    domain_data = data.get("domains", {}).get(body.topic, {})
    core_theme = domain_data.get("core_theme", "")

    perspectives = []
    for sign_str in selected:
        char_data = characters.get(sign_str, {})
        persona = char_data.get("persona", {})
        role_tag = char_data.get("role_tag", "")

        if role_tag == "天赋角色":
            angle = f"从我的角度看，{topic_label}是你的天然优势——{core_theme}"
        elif role_tag == "课题角色":
            angle = f"说实话，{topic_label}这个领域对你来说不太舒服。但正是因为不容易，你在这里的成长最有分量。"
        else:
            angle = f"关于{topic_label}，我的视角是：{core_theme}"

        perspectives.append({
            "character": sign_str,
            "character_name": persona.get("name", sign_str),
            "archetype": persona.get("archetype", ""),
            "perspective": angle,
            "visual_color": persona.get("visual_color", ""),
        })

    # 合成
    role_tags = set()
    for s in selected:
        cd = characters.get(s, {})
        role_tags.add(cd.get("role_tag", ""))
    if len(role_tags) >= 2:
        synthesis = f"你看，不同的角色看到了不同的东西——这说明{topic_label}对你来说是多维度的。整合这些视角，你会看得更全面。"
    else:
        synthesis = f"这些角色从不同角度看了{topic_label}。它们说的其实不冲突——加在一起，是一张更完整的地图。"

    if body.message:
        synthesis = f"关于你说的'{body.message[:50]}'——{synthesis}"

    return {
        "status": "success",
        "data": {
            "topic": body.topic,
            "topic_label": topic_label,
            "perspectives": perspectives,
            "synthesis": synthesis,
        },
    }


@app.get("/api/characters/{report_id}/growth")
async def get_growth_data(report_id: str) -> Dict[str, Any]:
    """获取用户成长数据"""
    try:
        from life_kline.growth.growth_tracker import GrowthTracker
        tracker = GrowthTracker.load(report_id)
        summary = tracker.get_growth_summary()
        milestones = [m.to_dict() for m in tracker.milestones]
        return {
            "status": "success",
            "report_id": report_id,
            "data": {
                "summary": summary.to_dict(),
                "milestones": milestones,
                "recent_conversations": [
                    c.to_dict() for c in tracker.get_conversation_history(limit=10)
                ],
            },
        }
    except Exception as e:
        return {
            "status": "success",
            "report_id": report_id,
            "data": {
                "summary": {"total_conversations": 0, "streak_days": 0},
                "milestones": [],
                "recent_conversations": [],
                "note": f"Growth tracker not yet initialized: {e}",
            },
        }


# ═══════════════════════════════════════════════════════════════
# 今日星灵 & 每日一问
# ═══════════════════════════════════════════════════════════════


def _reconstruct_chart_from_user_info(user_info: dict):
    """从 user_info 重建本命盘 ChartData"""
    from life_kline.ephemeris import EphemerisEngine

    engine = EphemerisEngine()
    birth_time = datetime.fromisoformat(
        user_info.get("birth_time_utc", user_info.get("birth_time_local", ""))
    )
    lat = user_info.get("lat", 0.0)
    lon = user_info.get("lon", 0.0)
    chart = engine.calculate_chart(birth_time, lat, lon)
    chart.location = {"lat": lat, "lon": lon}
    return chart


@app.get("/api/today-star-spirit/{report_id}")
async def get_today_star_spirit(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    """获取用户今日引路星灵"""
    record = load_owned_report(report_id, authorization)
    user_info = record.get("data", {}).get("user_info", {})
    if not user_info:
        raise HTTPException(status_code=400, detail="User info missing from report")

    try:
        from life_kline.today_engine import TodayStarSpiritEngine

        def _compute():
            chart = _reconstruct_chart_from_user_info(user_info)
            spirit_engine = TodayStarSpiritEngine(service)
            return spirit_engine.compute_today_star_spirit(chart)

        result = await anyio.to_thread.run_sync(_compute)

        return {
            "status": "success",
            "report_id": report_id,
            "data": result.to_dict(),
        }
    except Exception as exc:
        import traceback

        traceback.print_exc()
        # 优雅回退：返回月亮
        return {
            "status": "success",
            "report_id": report_id,
            "data": {
                "planet": "MOON",
                "planet_label": "月亮",
                "symbol": "☽",
                "reason": f"计算暂时不可用，月亮为你默默引路。（{exc}）",
                "confidence": 20.0,
                "sign": "UNKNOWN",
                "sign_label": "未知",
            },
        }


@app.get("/api/daily-question/{report_id}")
async def get_daily_question(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    """获取每日一问"""
    record = load_owned_report(report_id, authorization)
    user_info = record.get("data", {}).get("user_info", {})
    if not user_info:
        raise HTTPException(status_code=400, detail="User info missing from report")

    try:
        from life_kline.today_engine import TodayStarSpiritEngine
        from life_kline.daily_question_engine import DailyQuestionEngine
        from life_kline.llm_client import LLMClient

        def _compute():
            chart = _reconstruct_chart_from_user_info(user_info)
            spirit_engine = TodayStarSpiritEngine(service)
            today_spirit = spirit_engine.compute_today_star_spirit(chart)
            question_engine = DailyQuestionEngine(llm_client=LLMClient())
            transits = service.compute_transits(chart)
            return question_engine.generate(
                today_spirit=today_spirit,
                chart=chart,
                transits=transits,
            )

        question = await anyio.to_thread.run_sync(_compute)

        return {
            "status": "success",
            "report_id": report_id,
            "data": question.to_dict(),
        }
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return {
            "status": "success",
            "report_id": report_id,
            "data": {
                "question": "今天你照顾好自己了吗？",
                "spirit_planet": "MOON",
                "spirit_planet_label": "月亮",
                "context_note": "暂时无法读取你的星灵数据，月亮代你问候。",
                "voice_text": "月亮想知道：今天你照顾好自己了吗？",
                "generated_at": datetime.utcnow().isoformat(),
            },
        }


class DiaryInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    chat_context: Optional[str] = Field(default=None, description="用户对话上下文")
    spirit_planet: Optional[str] = Field(default=None, description="关联星灵")
    mood_emoji: Optional[str] = Field(default=None, description="情绪 emoji")
    user_messages: Optional[list[str]] = Field(default=None, description="用户消息列表")
    spirit_responses: Optional[list[str]] = Field(default=None, description="星灵回复列表")
    diary_style: Optional[str] = Field(default="summary", description="日记风格")
    evening_expectation: Optional[str] = Field(default=None, description="下班后的期待")


DIARY_DIR = os.path.join(os.path.dirname(__file__), "data", "diary")


@app.get("/api/spirit-diary/{report_id}/styles")
async def get_diary_style_suggestions(
    report_id: str,
    request: Request,
    spirit_planet: str = "",
    mood_emoji: str = "",
    message: str = "",
) -> Dict[str, Any]:
    """获取日记风格建议（基于最近的对话上下文）。

    用于前端"创建日记前"展示可选风格。
    """
    try:
        from life_kline.diary_engine import DiaryEngine

        engine = DiaryEngine(diary_dir=DIARY_DIR)
        suggestions = engine.get_style_suggestions(
            report_id=report_id,
            chat_context=message or "",
            spirit_planet=spirit_planet,
            mood_emoji=mood_emoji,
        )
        return {"status": "success", "report_id": report_id, "data": suggestions}
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return {
            "status": "error",
            "report_id": report_id,
            "detail": f"Failed to build style suggestions: {exc}",
        }


@app.post("/api/spirit-diary/{report_id}/entry")
async def create_diary_entry(report_id: str, body: DiaryInput, request: Request) -> Dict[str, Any]:
    """创建星灵日记条目 — 优先写入 DB，其次 JSON 兜底

    支持 diary_style 字段（check_in / dialogue / reflection / spirit / summary）。
    """
    user_id = ""
    profile_id = ""
    try:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            user_id = _parse_token(auth[7:]) or ""
    except Exception:
        user_id = ""

    try:
        from life_kline.diary_engine import DiaryEngine

        engine = DiaryEngine(diary_dir=DIARY_DIR, user_id=user_id, profile_id=profile_id)

        # 生成多风格预览（前端可选风格）
        try:
            previews = engine.get_style_suggestions(
                report_id=report_id,
                chat_context=body.chat_context or "",
                spirit_planet=body.spirit_planet or "",
                mood_emoji=body.mood_emoji or "",
                user_messages=body.user_messages,
                spirit_responses=body.spirit_responses,
            )
        except Exception:
            previews = []

        entry = engine.extract_and_generate(
            report_id=report_id,
            chat_context=body.chat_context or "",
            spirit_planet=body.spirit_planet or "",
            mood_emoji=body.mood_emoji or "",
            user_messages=body.user_messages,
            spirit_responses=body.spirit_responses,
            diary_style=body.diary_style or "summary",
            evening_expectation=body.evening_expectation or "",
        )

        return {
            "status": "success",
            "report_id": report_id,
            "data": entry.to_dict(),
            "diary_preview": previews,
        }
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return {
            "status": "error",
            "report_id": report_id,
            "detail": f"Failed to create diary entry: {exc}",
        }


@app.get("/api/spirit-diary/{report_id}")
async def get_diary_timeline(
    report_id: str,
    limit: int = 30,
    offset: int = 0,
    authorization: str = Header(default=""),
) -> Dict[str, Any]:
    """获取星灵日记时间线 — 从 DB 读取"""
    require_report_owner(report_id, authorization)
    try:
        rows = _dao.list_star_diary(
            report_id=report_id, limit=limit, offset=offset,
        )
        total = _dao.count_star_diary(report_id=report_id)
        return {
            "status": "success",
            "report_id": report_id,
            "data": {
                "entries": rows,
                "total": total,
            },
        }
    except Exception as exc:
        import traceback

        traceback.print_exc()
        # 兜底：JSON
        try:
            from life_kline.diary_engine import DiaryEngine

            engine = DiaryEngine(diary_dir=DIARY_DIR)
            entries = engine.get_timeline(
                report_id=report_id,
                limit=limit,
                offset=offset,
            )
            return {
                "status": "success",
                "report_id": report_id,
                "data": {
                    "entries": [e.to_dict() for e in entries],
                    "total": len(entries),
                },
            }
        except Exception:
            return {
                "status": "error",
                "report_id": report_id,
                "detail": f"Failed to load diary entries: {exc}",
            }


class DiaryUpdateInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    entry_text: Optional[str] = Field(default=None, description="更新后的日记正文")
    keywords: Optional[list[str]] = Field(default=None, description="更新后的关键词")
    mood_emoji: Optional[str] = Field(default=None, description="更新后的 emoji")
    diary_style: Optional[str] = Field(default=None, description="日记风格")
    evening_expectation: Optional[str] = Field(default=None, description="下班后的期待")
    topic_tag: Optional[str] = Field(default=None, description="话题标签")
    energy_level: Optional[int] = Field(default=None, description="电量百分比")


@app.patch("/api/spirit-diary/{entry_id}")
async def update_diary_entry(
    entry_id: str,
    body: DiaryUpdateInput,
    authorization: str = Header(default=""),
) -> Dict[str, Any]:
    """更新日记条目（仅本人可编辑）。

    可更新字段：entry_text / keywords / mood_emoji。
    """
    token = authorization.replace("Bearer ", "")
    user_id = _parse_token(token) or ""

    # 至少有 token 才能编辑（非匿名数据可改；匿名数据要求 token）
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录后再编辑日记")

    if (
        body.entry_text is None
        and body.keywords is None
        and body.mood_emoji is None
        and body.diary_style is None
        and body.evening_expectation is None
        and body.topic_tag is None
        and body.energy_level is None
    ):
        raise HTTPException(status_code=400, detail="没有可更新的字段")

    row = _dao.update_star_diary(
        entry_id=entry_id,
        user_id=user_id,
        entry_text=body.entry_text,
        keywords=body.keywords,
        mood_emoji=body.mood_emoji,
        diary_style=body.diary_style,
        evening_expectation=body.evening_expectation,
        topic_tag=body.topic_tag,
        energy_level=body.energy_level,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="日记不存在或无权编辑")
    return {"status": "success", "data": row}


@app.delete("/api/spirit-diary/{entry_id}")
async def delete_diary_entry(
    entry_id: str,
    authorization: str = Header(default=""),
) -> Dict[str, Any]:
    """删除日记条目（仅本人可删）。

    采用硬删除（DB DELETE）。前端删除后需要刷新列表。
    """
    token = authorization.replace("Bearer ", "")
    user_id = _parse_token(token) or ""
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录后再删除日记")

    deleted = _dao.delete_star_diary(entry_id=entry_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="日记不存在或无权删除")
    return {"status": "success", "entry_id": entry_id}


# ═══════════════════════════════════════════════════════════════
# 定价与权限
# ═══════════════════════════════════════════════════════════════

@app.get("/api/pricing")
async def get_pricing() -> Dict[str, Any]:
    """获取完整的定价信息"""
    from life_kline.pricing import get_pricing_info
    return {"status": "success", "data": get_pricing_info()}


@app.get("/api/access/{user_id}")
async def get_user_access(user_id: str) -> Dict[str, Any]:
    """获取用户当前的权限状态"""
    from life_kline.pricing import AccessChecker, is_test_user
    # 从存储加载用户状态（暂时用空状态 = 新用户）
    state = load_user_state(user_id)
    checker = AccessChecker(state)
    engine_check = checker.check_engine_chat("SUN")
    ai_check = checker.check_ai_chat()
    council_check = checker.check_council()
    return {
        "status": "success",
        "data": {
            "user_id": user_id,
            "is_test_user": is_test_user(user_id),
            "is_vip": checker._is_vip_active(),
            "coins": state.get("coins", 0),
            "engine": engine_check.to_dict(),
            "ai": ai_check.to_dict(),
            "council": council_check.to_dict(),
        },
    }


def load_user_state(user_id: str) -> dict:
    """加载用户状态 — DB 优先，JSON 兜底。"""
    state: Optional[Dict[str, Any]] = None
    try:
        state = _dao.get_user_state(user_id)
        if not state:
            state = {
                "user_id": user_id, "coins": 0, "is_vip": False,
                "vip_expire_at": "", "ai_usage_today": 0,
                "ai_usage_date": "", "extra": {},
            }
    except Exception:
        state = None

    if state is None:
        state = {"user_id": user_id, "coins": 0, "is_vip": False}

    # 从 users 表补全 phone（用于测试用户匹配）
    if "phone" not in state or not state.get("phone"):
        try:
            db = get_db()
            row = db.execute(
                "SELECT phone FROM users WHERE id=?", (user_id,)
            ).fetchone()
            db.close()
            if row and row["phone"]:
                state["phone"] = row["phone"]
        except Exception:
            pass
    return state


# ═══════════════════════════════════════════════════════════════
# AI 星灵对话（引擎 + LLM 双层）
# ═══════════════════════════════════════════════════════════════

class SpiritChatInput(BaseModel):
    planet: str = Field(..., description="行星 key，如 'VENUS'")
    topic: str = Field(default="personal")
    message: str = Field(..., description="用户消息")
    history: list[dict] = Field(default_factory=list)
    entry_context: dict | None = None


@app.post("/api/spirit-chat/{report_id}")
async def spirit_chat(report_id: str, body: SpiritChatInput, request: Request) -> Dict[str, Any]:
    """星灵对话 — 引擎占星师 + AI 增强双层架构。

    引擎层（永远在线）：路由意图 → 读取星盘证据 → 渲染结构化回复。
    AI 层（可选增强）：拿到引擎的结构化输出后，做语音翻译美化。

    权限：引擎对话有免费额度，AI 对话消耗星币或 VIP 额度。
    必须携带 Authorization header 以识别用户身份。
    """
    record = load_report_record(report_id)
    report_data = record.get("data", {})

    from life_kline.llm_client import (
        LLMClient, build_spirit_system_prompt,
        SpiritChatTracker,
    )
    from life_kline.engine_astrologer import EngineAstrologer
    from life_kline.pricing import AccessChecker

    # ── 用户认证 ──
    # 身份只来自签名 token，禁止信任客户端可伪造的 header（如 X-User-Id）。
    # 无有效 token 时以匿名游客身份处理（严格限额），不得冒充任何用户。
    auth_header = request.headers.get("Authorization", "")
    user_id = ""
    if auth_header.startswith("Bearer "):
        user_id = _parse_token(auth_header[7:]) or ""
    # 归属校验：只能用自己的报告对话，禁止凭他人 report_id 越权。
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    if (_report_owner(report_id) or "") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该报告")
    state = load_user_state(user_id)
    access_checker = AccessChecker(state)
    engine_access = access_checker.check_engine_chat(body.planet)
    if not engine_access.allowed:
        return {
            "status": "error",
            "error_code": "QUOTA_EXCEEDED",
            "data": {
                "message": engine_access.reason,
                "access": engine_access.to_dict(),
            },
        }

    # ── 对话追踪 ──
    chat_tracker = SpiritChatTracker()
    today_chats = chat_tracker.get_today_chats(report_id)
    previous_chats_today = 0
    if body.planet in today_chats:
        previous_chats_today = today_chats[body.planet].get("count", 0)
    previous_spirit = chat_tracker.get_last_spirit(report_id)

    # 构建 entry_context
    entry_context = body.entry_context or {}
    if previous_chats_today > 0:
        entry_context["previous_chats_today"] = previous_chats_today
    if previous_spirit and previous_spirit != body.planet:
        entry_context["previous_spirit"] = previous_spirit

    # ── 第 1 层：引擎占星师（永远运行） ──
    engine = EngineAstrologer(report_data)
    engine_response = engine.consult(
        report_id=report_id,
        planet=body.planet,
        user_message=body.message,
        topic_hint=body.topic,
        history=body.history,
        entry_context=entry_context,
    )
    engine_dict = engine_response.to_dict()

    # ── 危机短路：命中危机信号时脱离占星话术，禁止 AI 增强改写干预文案 ──
    if engine_response.is_crisis:
        return {
            "status": "success",
            "source": "crisis_guard",
            "data": {
                "spirit_response": engine_response.full_text,
                "is_crisis": True,
                "crisis": engine_response.crisis,
                "engine": engine_dict,
            },
        }

    # ── 第 2 层：AI 增强（可选） ──
    client = LLMClient()
    final_response = engine_response.full_text
    source = "engine"
    ai_access_info = None

    if client.is_configured:
        # ── AI 权限检查 ──
        ai_access = access_checker.check_ai_chat()
        ai_access_info = ai_access.to_dict()
        if ai_access.allowed:
            # 用引擎的结构化输出作为 AI 的上下文
            try:
                astro_instruction = (
                    "本轮已触发星盘切入：必须先原样输出情感承接句，再用一小段自然语言引用下方最多一条证据；不要倾倒完整占星结构。"
                    if engine_response.mirroring else
                    "本轮只做情感承接：必须先原样输出情感承接句，禁止提及星盘、宫位、星座、相位或命盘配置。"
                )
                engine_hint = (
                    f"[引擎占星师已分析]\n"
                    f"触发规则：{astro_instruction}\n"
                    f"情感承接句：{engine_response.acknowledgment}\n"
                    f"领域：{engine_response.domain_label}\n"
                    f"情绪：{engine_response.emotional_state}\n"
                    f"星盘证据：{'; '.join(engine_response.evidence[:4])}\n"
                    f"引擎回答（参考）：{engine_response.full_text[:300]}\n"
                    f"\n请基于以上引擎分析，用你的方式自然地回复用户。"
                    f"保持引擎的占星学准确性，但可以让语言更温暖流畅。"
                )

                system_prompt = build_spirit_system_prompt(
                    report_data, body.planet, engine_response.domain,
                    entry_context=entry_context,
                )
                system_prompt = engine_hint + "\n\n" + system_prompt

                ai_response = await client.chat_async(
                    system_prompt=system_prompt,
                    user_message=body.message,
                    history=body.history,
                )
                if ai_response:
                    final_response = ai_response
                    source = "llm_enhanced"
            except Exception:
                pass  # AI 失败 → 降级到引擎输出

    # ── 记录对话到成长追踪器 ──
    try:
        from life_kline.growth.growth_tracker import GrowthTracker
        tracker = GrowthTracker.load(report_id)
        tracker.record_conversation(
            sign=body.planet,
            topic=engine_response.domain,
            user_message=body.message[:200],
            character_response=final_response[:200],
            emotional_context=engine_response.emotional_state,
        )
    except Exception:
        pass

    # ── 追踪 AI 使用量（数据库） ──
    if source == "llm_enhanced" and user_id:
        try:
            _dao.increment_ai_usage(user_id)
        except Exception:
            pass

    # ── 对话追踪 ──
    try:
        # role/content 仍保留通用聊天模型，同时响应显式返回双方字段。
        if user_id:
            _dao.insert_chat_message(
                user_id=user_id, role="user", content=body.message,
                report_id=report_id, spirit_planet=body.planet,
            )
            _dao.insert_chat_message(
                user_id=user_id, role="assistant", content=final_response,
                report_id=report_id, spirit_planet=body.planet,
            )
    except Exception:
        pass
    chat_tracker.record_chat(report_id, body.planet)

    # 生成多风格日记预览（前端"创建日记"按钮旁推荐风格）
    diary_style_suggestions: list[dict] = []
    try:
        from life_kline.diary_engine import DiaryEngine
        _diary_engine = DiaryEngine(diary_dir=DIARY_DIR)
        diary_style_suggestions = _diary_engine.get_style_suggestions(
            report_id=report_id,
            chat_context=body.message,
            spirit_planet=body.planet,
            mood_emoji="",
            user_messages=[body.message],
            spirit_responses=[final_response],
        )
    except Exception:
        pass

    return {
        "status": "success",
        "data": {
            "planet": body.planet,
            "response": final_response,
            "user_message": body.message,
            "spirit_response": final_response,
            "domain": engine_response.domain,
            "emotional_state": engine_response.emotional_state,
            "engine_reading": {
                "acknowledgment": engine_response.acknowledgment,
                "mirroring": engine_response.mirroring,
                "guidance": engine_response.guidance,
                "evidence": engine_response.evidence,
            },
            "source": source,
            "ai_access": ai_access_info,
            "suggested_followup": getattr(engine_response, "suggested_followup", "") or "",
            "diary_style_suggestions": diary_style_suggestions,
        },
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
        chart = await anyio.to_thread.run_sync(
            service.engine.calculate_chart, now_utc, 39.9, 116.4
        )

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


@app.get("/api/daily-transits/{report_id}")
async def get_daily_transits(report_id: str, authorization: str = Header(default="")) -> Dict[str, Any]:
    """Get layered daily transit report for a user's natal chart."""
    record = load_owned_report(report_id, authorization)
    report_data = record.get("data", {})
    user_info = report_data.get("user_info", {})
    if not user_info:
        raise HTTPException(status_code=400, detail="User info missing from report")

    from life_kline.transit_engine import DailyTransitEngine
    from life_kline.ephemeris import EphemerisEngine

    def _compute():
        chart = _reconstruct_chart_from_user_info(user_info)
        engine = DailyTransitEngine(EphemerisEngine())
        return engine.compute_daily_transits(chart)

    report = await anyio.to_thread.run_sync(_compute)

    return {"status": "success", "report_id": report_id, "data": asdict(report)}


# ═══════════════════════════════════════════════════════════════
# 花园 API — 分析工具集
# ═══════════════════════════════════════════════════════════════

from life_kline.garden_catalog import to_dict as garden_catalog_dict
from life_kline.chart_structure import ChartStructureAnalyzer
from life_kline.consultation_engine import (
    ConsultationEngine, ConsultationSessionManager, ConsultationState,
)

# 全局会话管理器 + LLM 客户端（AI 增强星语者）
_garden_session_mgr = ConsultationSessionManager()
_garden_llm_client = None
try:
    from life_kline.llm_client import LLMClient
    _garden_llm_client = LLMClient()
except Exception:
    pass

# 输入模型
class GardenConsultStartInput(BaseModel):
    category: str = Field(..., description="分类 key，如 'love'")
    question_key: str = Field(..., description="问题 key，如 'love_pattern'")

class GardenConsultContinueInput(BaseModel):
    session_id: str = Field(..., description="会话 ID")
    user_response: str = Field(..., description="用户回复")


@app.get("/api/garden/categories")
async def get_garden_categories() -> Dict[str, Any]:
    """获取花园分类和抓手问题列表"""
    return {"status": "success", "data": garden_catalog_dict()}


@app.get("/api/garden/checkin")
async def get_checkin_status(request: Request) -> Dict[str, Any]:
    """获取今日签到状态"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    today = datetime.utcnow().strftime("%Y-%m-%d")
    db = get_db()
    row = db.execute(
        "SELECT * FROM checkins WHERE user_id=? AND checkin_date=? ORDER BY created_at DESC LIMIT 1",
        (user_id, today),
    ).fetchone()
    db.close()

    if row:
        return {
            "status": "success",
            "data": {
                "checked_in": True,
                "streak_count": row["streak_count"],
                "checkin_date": row["checkin_date"],
            },
        }

    # 查最近一次签到获取 streak
    db2 = get_db()
    last_row = db2.execute(
        "SELECT * FROM checkins WHERE user_id=? ORDER BY checkin_date DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    db2.close()

    return {
        "status": "success",
        "data": {
            "checked_in": False,
            "streak_count": last_row["streak_count"] if last_row else 0,
            "checkin_date": today,
        },
    }


@app.post("/api/garden/checkin")
async def do_checkin(request: Request) -> Dict[str, Any]:
    """执行每日签到"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    today = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    db = get_db()

    # 检查今天是否已签到
    existing = db.execute(
        "SELECT * FROM checkins WHERE user_id=? AND checkin_date=?",
        (user_id, today),
    ).fetchone()
    if existing:
        db.close()
        return {
            "status": "success",
            "data": {
                "checked_in": True,
                "streak_count": existing["streak_count"],
                "checkin_date": today,
                "message": "今天已经签到过了 ✨",
            },
        }

    # 计算连续签到
    streak = 1
    yesterday_row = db.execute(
        "SELECT * FROM checkins WHERE user_id=? AND checkin_date=?",
        (user_id, yesterday),
    ).fetchone()
    if yesterday_row:
        streak = yesterday_row["streak_count"] + 1

    checkin_id = _uid()
    db.execute(
        "INSERT INTO checkins (id, user_id, checkin_date, streak_count, created_at) VALUES (?, ?, ?, ?, ?)",
        (checkin_id, user_id, today, streak, _now()),
    )
    db.commit()
    db.close()

    streak_msgs = {
        1: "第一天！花园的门为你敞开 🌱",
        3: "连续三天了，花园在记住你 🌿",
        7: "一周！你已经和花园建立联结了 🌸",
        30: "一个月！星辰见证了你的坚持 🌟",
    }
    msg = streak_msgs.get(streak, f"连续第{streak}天签到，真棒！")

    return {
        "status": "success",
        "data": {
            "checked_in": True,
            "streak_count": streak,
            "checkin_date": today,
            "message": msg,
        },
    }


@app.post("/api/garden/consultation/{report_id}/start")
async def start_consultation(
    report_id: str, body: GardenConsultStartInput, request: Request,
) -> Dict[str, Any]:
    """开始新咨询 — Step 1 锚定"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    if (_report_owner(report_id) or "") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该报告")
    record = load_report_record(report_id)
    report_data = record.get("data", {})

    engine = ConsultationEngine(report_data, _garden_llm_client)
    try:
        state = await anyio.to_thread.run_sync(
            engine.start_consultation, body.category, body.question_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 持久化会话
    _garden_session_mgr.store(state)
    try:
        db = get_db()
        import json as _json
        db.execute(
            "INSERT INTO consultation_sessions (id, user_id, report_id, category, question_key, state_json, step, is_complete, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (state.session_id, user_id, report_id, state.category, state.question_key,
             _json.dumps(state.to_dict(), ensure_ascii=False),
             state.step, 1 if state.is_complete else 0, _now(), _now()),
        )
        db.commit()
        db.close()
    except Exception:
        pass

    return {
        "status": "success",
        "data": state.to_dict(),
    }


@app.post("/api/garden/consultation/{report_id}/continue")
async def continue_consultation(
    report_id: str, body: GardenConsultContinueInput, request: Request,
) -> Dict[str, Any]:
    """继续咨询 — 推进到下一步"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    state = _garden_session_mgr.load(body.session_id)
    if not state:
        # 尝试从 DB 恢复
        try:
            db = get_db()
            import json as _json
            row = db.execute(
                "SELECT * FROM consultation_sessions WHERE id=? AND user_id=?",
                (body.session_id, user_id),
            ).fetchone()
            db.close()
            if row:
                sd = _json.loads(row["state_json"])
                state = ConsultationState(**sd)
                _garden_session_mgr.store(state)
        except Exception:
            pass

    if not state:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    if (_report_owner(report_id) or "") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该报告")
    record = load_report_record(report_id)
    report_data = record.get("data", {})

    engine = ConsultationEngine(report_data, _garden_llm_client)
    state = await anyio.to_thread.run_sync(
        engine.continue_consultation, state, body.user_response
    )

    # 更新持久化
    _garden_session_mgr.store(state)
    try:
        db = get_db()
        import json as _json
        db.execute(
            "UPDATE consultation_sessions SET state_json=?, step=?, is_complete=?, updated_at=? WHERE id=?",
            (_json.dumps(state.to_dict(), ensure_ascii=False),
             state.step, 1 if state.is_complete else 0, _now(), state.session_id),
        )
        db.commit()
        db.close()
    except Exception:
        pass

    return {
        "status": "success",
        "data": state.to_dict(),
    }


@app.post("/api/garden/consultation/{report_id}/report")
async def generate_consultation_report(
    report_id: str, body: GardenConsultContinueInput, request: Request,
) -> Dict[str, Any]:
    """生成最终咨询报告"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    state = _garden_session_mgr.load(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    if (_report_owner(report_id) or "") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该报告")
    record = load_report_record(report_id)
    report_data = record.get("data", {})

    engine = ConsultationEngine(report_data, _garden_llm_client)
    # 如果还没完成，先完成
    if not state.is_complete:
        state.step = 3
        state = await anyio.to_thread.run_sync(engine._run_chart_verify, state)

    report = await anyio.to_thread.run_sync(engine.generate_report, state)

    # 存到 consultation_reports
    try:
        db = get_db()
        import json as _json
        db.execute(
            "INSERT INTO consultation_reports (id, user_id, session_id, category, question_key, report_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (report.report_id, user_id, state.session_id, report.category,
             report.question_key, _json.dumps(report.to_dict(), ensure_ascii=False), _now()),
        )
        db.commit()
        db.close()
    except Exception:
        pass

    # 顺手记一条星灵日记
    try:
        from life_kline.diary_engine import DiaryEngine
        diary_engine = DiaryEngine(diary_dir=DIARY_DIR)
        diary_engine.extract_and_generate(
            report_id=report_id,
            chat_context=(
                f"星语者咨询：{report.question_label}\n"
                f"{report.anchor_summary[:200]}\n"
                f"{report.scenario_summary[:200]}"
            ),
            spirit_planet="",
            mood_emoji="",
        )
    except Exception:
        pass

    return {
        "status": "success",
        "data": report.to_dict(),
    }


@app.get("/api/garden/reports")
async def list_garden_reports(
    request: Request,
    category: str = "",
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """获取花园咨询报告历史"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    db = get_db()
    if category:
        rows = db.execute(
            "SELECT id, category, question_key, report_json, created_at FROM consultation_reports WHERE user_id=? AND category=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, category, limit, offset),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id, category, question_key, report_json, created_at FROM consultation_reports WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        ).fetchall()
    db.close()

    from life_kline.garden_catalog import get_category as gc

    items = []
    for r in rows:
        try:
            import json as _json
            rj = _json.loads(r["report_json"])
        except Exception:
            rj = {}
        cat = gc(r["category"])
        items.append({
            "id": r["id"],
            "category": r["category"],
            "category_label": cat.label if cat else r["category"],
            "question_key": r["question_key"],
            "question_label": rj.get("question_label", ""),
            "summary": (rj.get("fused_narrative", "") or rj.get("anchor_summary", ""))[:150],
            "created_at": r["created_at"],
        })

    return {"status": "success", "data": {"reports": items, "total": len(items)}}


@app.get("/api/garden/reports/{report_id}")
async def get_garden_report(report_id: str, request: Request) -> Dict[str, Any]:
    """获取单份花园咨询报告"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    db = get_db()
    row = db.execute(
        "SELECT * FROM consultation_reports WHERE id=? AND user_id=?",
        (report_id, user_id),
    ).fetchone()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail="报告不存在")

    try:
        import json as _json
        report = _json.loads(row["report_json"])
    except Exception:
        report = {}

    return {"status": "success", "data": report}


# ── 用户系统路由 ──────────────────────────────────────────

@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    from backend.database import migrate_db
    migrate_db()
    try:
        _admin.ensure_root_admin()
    except Exception as exc:
        print(f"[admin] init failed: {exc}")
    global service
    service = LifeKlineService()
    provider_names = ["nominatim_global", "nominatim_cn", "maps_co"]
    if AMAP_KEY:
        provider_names.insert(0, "amap")
    print(f"[life-kline] geocode providers: {', '.join(provider_names)}")


@app.post("/api/auth/send-code")
async def send_code(body: SendCodeInput) -> Dict[str, Any]:
    phone = body.phone.strip()
    if not phone or len(phone) < 10:
        raise HTTPException(status_code=400, detail="请输入有效的手机号")
    code = str(random.randint(100000, 999999))
    db = get_db()
    db.execute(
        "INSERT INTO verify_codes (phone, code, expires_at) VALUES (?, ?, ?)",
        (phone, code, (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()),
    )
    db.commit()
    db.close()
    print(f"[sms] {phone}: {code}")
    return {"status": "success", "message": "验证码已发送（开发模式：查看控制台）"}


@app.post("/api/auth/verify-code")
async def verify_code(body: VerifyCodeInput) -> Dict[str, Any]:
    phone, code = body.phone.strip(), body.code.strip()

    # Development bypass: if phone matches VITE_DEV_BYPASS_PHONE and code is "000000", skip SMS verification
    dev_bypass_phone = os.getenv("LIFE_KLINE_DEV_BYPASS_PHONE", "").strip()
    if dev_bypass_phone and phone == dev_bypass_phone and code == "000000":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        if not user:
            user_id = _uid()
            db.execute("INSERT INTO users (id, phone, nickname, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)",
                       (user_id, phone, "", _now(), _now()))
        else:
            user_id = user["id"]
            db.execute("UPDATE users SET last_login_at=? WHERE id=?", (_now(), user_id))
        db.commit()
        db.close()
        return {"status": "success", "token": _make_token(user_id), "user_id": user_id}

    db = get_db()

    row = db.execute(
        "SELECT id, code, expires_at FROM verify_codes WHERE phone=? AND used=0 ORDER BY id DESC LIMIT 1",
        (phone,),
    ).fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=400, detail="请先获取验证码")
    if row["code"] != code:
        db.close()
        raise HTTPException(status_code=400, detail="验证码错误")
    if row["expires_at"] < _now():
        db.close()
        raise HTTPException(status_code=400, detail="验证码已过期")
    db.execute("UPDATE verify_codes SET used=1 WHERE id=?", (row["id"],))

    user = db.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
    if not user:
        user_id = _uid()
        db.execute("INSERT INTO users (id, phone, nickname, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)", (user_id, phone, "", _now(), _now()))
    else:
        user_id = user["id"]
        db.execute("UPDATE users SET last_login_at=? WHERE id=?", (_now(), user_id))
    db.commit()
    db.close()
    return {"status": "success", "token": _make_token(user_id), "user_id": user_id}


@app.get("/api/auth/check")
async def auth_check(authorization: str = Header(default="")) -> Dict[str, Any]:
    """Check if the current token is valid. Returns user_id if valid."""
    token = authorization.replace("Bearer ", "")
    uid = _parse_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail="Token invalid or expired")
    return {"status": "success", "user_id": uid}


@app.get("/api/me")
async def get_me(authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    db = get_db()
    user = db.execute(
        "SELECT id, nickname, role, created_at, last_login_at FROM users WHERE id=?",
        (uid,),
    ).fetchone()
    rows = db.execute(
        "SELECT id, name, gender, birth_time, lat, lon, timezone, birth_place, "
        "house_system, daylight_saving, residence_place, residence_lat, residence_lon, "
        "is_default, created_at FROM profiles WHERE user_id=? ORDER BY created_at DESC",
        (uid,),
    ).fetchall()
    db.close()
    return {"status": "success", "user": dict(user) if user else None, "profiles": [dict(r) for r in rows]}


def _auto_detect_dst(birth_time: str, lat: float) -> bool:
    """中国夏令时自动判定：1986-1991年期间适用。
    规则：每年4月中旬至9月中旬，中国大陆实行夏令时（+1h）。
    返回 True 表示该出生时间可能涉及夏令时，需提示用户确认。"""
    try:
        dt = datetime.fromisoformat(birth_time)
    except Exception:
        return False
    # 仅适用于中国经度范围（约73°E~135°E）
    if not (73.0 <= abs(lat) <= 135.0):
        return False
    if not (1986 <= dt.year <= 1991):
        return False
    month, day = dt.month, dt.day
    # 各年夏令时起止日期
    dst_rules = {
        1986: ((4, 13), (9, 14)),
        1987: ((4, 12), (9, 13)),
        1988: ((4, 10), (9, 11)),
        1989: ((4, 16), (9, 17)),
        1990: ((4, 15), (9, 16)),
        1991: ((4, 14), (9, 15)),
    }
    (start_m, start_d), (end_m, end_d) = dst_rules.get(dt.year, ((4, 15), (9, 15)))
    start = dt.replace(month=start_m, day=start_d)
    end = dt.replace(month=end_m, day=end_d)
    return start <= dt <= end


@app.post("/api/profiles")
async def create_profile(body: ProfileInput, authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")

    db = get_db()

    # 一账户一 profile：已有则拒绝
    existing = db.execute("SELECT id FROM profiles WHERE user_id=? LIMIT 1", (uid,)).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=409, detail="该账户已存在档案，请使用编辑功能")

    lat = body.lat
    lon = body.lon
    # Auto-geocode if birth_place is set and coordinates are empty/zero
    if body.birth_place and (lat == 0.0 and lon == 0.0):
        geo_lat, geo_lon = _geocode_place(body.birth_place)
        if geo_lat != 0.0 or geo_lon != 0.0:
            lat, lon = geo_lat, geo_lon

    # 现居地 geocode
    res_lat = body.residence_lat
    res_lon = body.residence_lon
    if body.residence_place and (res_lat == 0.0 and res_lon == 0.0):
        geo_lat, geo_lon = _geocode_place(body.residence_place)
        if geo_lat != 0.0 or geo_lon != 0.0:
            res_lat, res_lon = geo_lat, geo_lon

    # DST 自动判定
    dst = body.daylight_saving or _auto_detect_dst(body.birth_time, lat)

    pid = _uid()
    db.execute(
        "INSERT INTO profiles (id, user_id, name, gender, birth_time, lat, lon, timezone, birth_place, house_system, daylight_saving, residence_place, residence_lat, residence_lon, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (pid, uid, body.name, body.gender, body.birth_time, lat, lon, body.timezone, body.birth_place, body.house_system, 1 if dst else 0, body.residence_place, res_lat, res_lon, 1, _now()),
    )
    db.commit()
    db.close()
    return {"status": "success", "profile_id": pid, "geocoded": (lat != body.lat or lon != body.lon), "dst_auto": dst}


@app.get("/api/profiles")
async def list_profiles(authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    db = get_db()
    rows = db.execute("SELECT * FROM profiles WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    db.close()
    return {"status": "success", "profiles": [dict(r) for r in rows]}


@app.put("/api/profiles/{profile_id}")
async def update_profile(profile_id: str, body: ProfileInput, authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")

    db = get_db()
    existing = db.execute("SELECT * FROM profiles WHERE id=? AND user_id=?", (profile_id, uid)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(status_code=404, detail="Profile not found")

    # Partial update: only override fields that were explicitly sent
    # (Pydantic's default values tell us which fields were not provided —
    #  we check model_dump(exclude_unset=True) for true partial update)
    update_data = body.model_dump(exclude_unset=True)

    # Auto-geocode if birth_place changed and coordinates are empty/zero
    lat = float(update_data.get("lat", existing["lat"]))
    lon = float(update_data.get("lon", existing["lon"]))
    birth_place = update_data.get("birth_place", existing["birth_place"] or "")
    if birth_place and (lat == 0.0 and lon == 0.0):
        geo_lat, geo_lon = _geocode_place(birth_place)
        if geo_lat != 0.0 or geo_lon != 0.0:
            lat, lon = geo_lat, geo_lon
            update_data["lat"] = lat
            update_data["lon"] = lon

    # 现居地 geocode
    res_lat = float(update_data.get("residence_lat", existing["residence_lat"] or 0.0))
    res_lon = float(update_data.get("residence_lon", existing["residence_lon"] or 0.0))
    residence_place = update_data.get("residence_place", existing["residence_place"] or "")
    if residence_place and (res_lat == 0.0 and res_lon == 0.0):
        geo_lat, geo_lon = _geocode_place(residence_place)
        if geo_lat != 0.0 or geo_lon != 0.0:
            update_data["residence_lat"] = geo_lat
            update_data["residence_lon"] = geo_lon

    # DST 自动判定
    if "daylight_saving" not in update_data:
        auto_dst = _auto_detect_dst(
            update_data.get("birth_time", existing["birth_time"]),
            lat,
        )
        if auto_dst and not bool(existing["daylight_saving"]):
            update_data["daylight_saving"] = True

    # Build SET clause dynamically
    field_map = {
        "name": "name",
        "gender": "gender",
        "birth_time": "birth_time",
        "lat": "lat",
        "lon": "lon",
        "timezone": "timezone",
        "birth_place": "birth_place",
        "house_system": "house_system",
        "daylight_saving": "daylight_saving",
        "residence_place": "residence_place",
        "residence_lat": "residence_lat",
        "residence_lon": "residence_lon",
    }
    set_parts = []
    values = []
    for body_key, col_name in field_map.items():
        if body_key in update_data:
            val = update_data[body_key]
            # Convert bool to int for SQLite
            if body_key == "daylight_saving":
                val = 1 if val else 0
            set_parts.append(f"{col_name}=?")
            values.append(val)

    if not set_parts:
        db.close()
        return {"status": "success", "profile_id": profile_id, "updated": []}

    values.append(profile_id)
    db.execute(f"UPDATE profiles SET {', '.join(set_parts)} WHERE id=?", values)
    db.commit()
    updated_profile = db.execute("SELECT * FROM profiles WHERE id=?", (profile_id,)).fetchone()
    db.close()

    return {
        "status": "success",
        "profile_id": profile_id,
        "updated": list(update_data.keys()),
        "profile": dict(updated_profile) if updated_profile else None,
    }


@app.get("/api/users/chart")
async def get_user_chart(
    profile_id: str = "",
    house_system: str = "B",
    daylight_saving: Optional[bool] = None,
    authorization: str = Header(default=""),
) -> Dict[str, Any]:
    """Get natal chart for the user's profile with the specified house system."""
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")

    db = get_db()
    if profile_id:
        profile = db.execute("SELECT * FROM profiles WHERE id=? AND user_id=?", (profile_id, uid)).fetchone()
    else:
        # Use default profile, or the first one
        profile = db.execute(
            "SELECT * FROM profiles WHERE user_id=? ORDER BY is_default DESC, created_at DESC LIMIT 1",
            (uid,),
        ).fetchone()
    db.close()

    if not profile:
        raise HTTPException(status_code=404, detail="No profile found. Create one first.")

    # Use query params to override profile settings
    hs = house_system or profile["house_system"] or "B"
    ds = daylight_saving if daylight_saving is not None else bool(profile["daylight_saving"])

    if service is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    try:
        report = service.generate_report(
            birth_time_iso=profile["birth_time"],
            lat=profile["lat"],
            lon=profile["lon"],
            timezone_offset=profile["timezone"],
            gender=profile["gender"],
            house_system=hs,
            daylight_saving=ds,
        )

        # ── 扩展数据：receptions + firdaria + age + day/night ──
        from life_kline.firdaria import calculate_firdaria_periods
        from life_kline.constants import Planet
        from life_kline.service import planet_label as _planet_label_fn

        def _planet_label(planet_value: str) -> str:
            if not planet_value:
                return ""
            return _planet_label_fn(planet_value) or str(planet_value)

        natal_chart = report.get("natal_chart", {})
        advanced = report.get("advanced_patterns", {})
        user_info = report.get("user_info", {})

        is_day_chart = bool(user_info.get("is_day_chart", True))

        # 当前年龄
        current_age = 0.0
        birth_time_local = user_info.get("birth_time_local") or user_info.get("birth_time_utc")
        if birth_time_local:
            try:
                from datetime import datetime as dt
                birth_dt = dt.fromisoformat(birth_time_local)
                current_age = (dt.now() - birth_dt.replace(tzinfo=None)).days / 365.2422
            except Exception:
                current_age = 0.0

        # 法达周期
        periods = calculate_firdaria_periods(is_day_chart, max_age=100.0)
        firdaria_payload = []
        for p in periods:
            major_lord = p.major_lord
            sub_lord = p.sub_lord
            major_value = major_lord.value if hasattr(major_lord, "value") else str(major_lord)
            sub_value = sub_lord.value if sub_lord and hasattr(sub_lord, "value") else (str(sub_lord) if sub_lord else "")
            is_node = major_lord in (Planet.NORTH_NODE, Planet.SOUTH_NODE)
            firdaria_payload.append({
                "start_age": round(p.start_age, 2),
                "end_age": round(p.end_age, 2),
                "lord": major_value,
                "lord_zh": _planet_label(major_value),
                "sub_lord": sub_value,
                "sub_lord_zh": _planet_label(sub_value),
                "is_node": is_node,
            })

        # 接纳/互溶
        receptions = []
        for grp in (advanced.get("reception_groups") or []):
            for guest in (grp.get("guests") or []):
                from_value = guest.get("planet") or ""
                to_value = grp.get("receiver") or ""
                receptions.append({
                    "from": from_value,
                    "from_zh": guest.get("label") or _planet_label(from_value),
                    "to": to_value,
                    "to_zh": grp.get("receiver_label") or _planet_label(to_value),
                    "type": "reception",
                    "type_zh": "庙宫接纳",
                    "description": grp.get("line") or grp.get("summary") or "",
                })

        for m in (advanced.get("mutual_receptions") or []):
            pair = m.get("pair") or []
            labels = m.get("labels") or []
            if len(pair) >= 2:
                p1 = str(pair[0])
                p2 = str(pair[1])
                receptions.append({
                    "from": p1,
                    "from_zh": labels[0] if len(labels) > 0 else _planet_label(p1),
                    "to": p2,
                    "to_zh": labels[1] if len(labels) > 1 else _planet_label(p2),
                    "type": "mutual_reception",
                    "type_zh": "互溶",
                    "description": m.get("line") or m.get("summary") or "",
                })

        return {
            "status": "success",
            "profile_id": profile["id"],
            "house_system": hs,
            "daylight_saving": ds,
            "data": {
                "natal_chart": natal_chart,
                "firdaria_periods": firdaria_payload,
                "receptions": receptions,
                "is_day_chart": is_day_chart,
                "current_age": round(current_age, 2),
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {exc}") from exc


# ═══════════════════════════════════════════════════════════════
# Admin CMS — 后台管理 API
# ═══════════════════════════════════════════════════════════════

class AdminLoginInput(BaseModel):
    username: str
    password: str


class AdminUpdateUserInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    nickname: Optional[str] = None
    disabled: Optional[bool] = None


class AdminDiaryModerationInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: str = Field(..., description="visible / hidden / flagged")
    reason: str = ""


class AdminSettingInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    key: str
    value: str


class AdminCreateAdminInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    username: str
    password: str
    role: str = "admin"


@app.post("/api/admin/login")
async def admin_login(body: AdminLoginInput, request: Request) -> Dict[str, Any]:
    """管理员登录"""
    admin = _dao.get_admin_by_username(body.username)
    if not admin or not admin.get("is_active"):
        raise HTTPException(status_code=400, detail="账号不存在或已停用")

    # 用真正的方法校验
    from backend.admin import _verify_password
    if not _verify_password(body.password, admin["password_hash"]):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    _dao.update_admin_last_login(admin["id"])
    token = _admin._make_admin_token(admin["id"], admin["username"], admin["role"])
    return {
        "status": "success",
        "data": {
            "token": token,
            "admin": {
                "id": admin["id"],
                "username": admin["username"],
                "role": admin["role"],
            },
        },
    }


@app.get("/api/admin/stats")
async def admin_stats(ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)]) -> Dict[str, Any]:
    """数据统计面板"""
    stats = _dao.get_system_stats()
    return {"status": "success", "data": stats}


@app.get("/api/admin/users")
async def admin_list_users(
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
    keyword: str = "",
    is_disabled: int = -1,
    limit: int = 30,
    offset: int = 0,
) -> Dict[str, Any]:
    """用户列表"""
    disabled = None if is_disabled < 0 else is_disabled
    rows = _dao.list_all_users(
        keyword=keyword, is_disabled=disabled, limit=limit, offset=offset
    )
    total = _dao.count_all_users(keyword=keyword, is_disabled=disabled)
    return {
        "status": "success",
        "data": {"users": rows, "total": total},
    }


@app.get("/api/admin/users/{user_id}")
async def admin_get_user(
    user_id: str,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    """用户详情"""
    db = get_db()
    row = db.execute(
        "SELECT u.*, "
        "(SELECT COUNT(*) FROM reports r WHERE r.user_id=u.id) AS report_count, "
        "(SELECT COUNT(*) FROM star_diary d WHERE d.user_id=u.id) AS diary_count "
        "FROM users u WHERE u.id=?",
        (user_id,),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "success", "data": dict(row)}


@app.patch("/api/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    body: AdminUpdateUserInput,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    """编辑用户（禁用/启用、改昵称）"""
    if body.disabled is not None:
        _dao.set_user_disabled(user_id, body.disabled)
        ctx.log(
            "disable_user" if body.disabled else "enable_user",
            "user", user_id,
            detail=f"disabled={body.disabled}",
        )
    if body.nickname is not None:
        _dao.update_user_profile(user_id, nickname=body.nickname)
        ctx.log("update_user", "user", user_id, detail=f"nickname={body.nickname}")

    return {"status": "success"}


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_super_admin)],
) -> Dict[str, Any]:
    """软删除用户（仅 super_admin）"""
    _dao.soft_delete_user(user_id)
    ctx.log("delete_user", "user", user_id)
    return {"status": "success"}


@app.get("/api/admin/diary")
async def admin_list_diary(
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
    keyword: str = "",
    status: str = "all",
    spirit_planet: str = "",
    user_id: str = "",
    limit: int = 30,
    offset: int = 0,
) -> Dict[str, Any]:
    """日记管理列表"""
    rows = _dao.list_all_diary(
        keyword=keyword,
        status=status,
        spirit_planet=spirit_planet,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    total = _dao.count_all_diary(
        keyword=keyword,
        status=status,
        spirit_planet=spirit_planet,
        user_id=user_id,
    )
    return {
        "status": "success",
        "data": {"entries": rows, "total": total},
    }


@app.get("/api/admin/diary/{entry_id}")
async def admin_get_diary(
    entry_id: str,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    """日记详情"""
    db = get_db()
    row = db.execute(
        "SELECT d.*, COALESCE(m.status, 'visible') AS mod_status, m.reason AS mod_reason "
        "FROM star_diary d LEFT JOIN diary_moderation m ON d.id = m.diary_id "
        "WHERE d.id=?",
        (entry_id,),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="日记不存在")
    data = dict(row)
    # 尝试解析 keywords JSON
    if data.get("keywords"):
        try:
            data["keywords"] = json.loads(data["keywords"])
        except Exception:
            data["keywords"] = []
    return {"status": "success", "data": data}


@app.patch("/api/admin/diary/{entry_id}")
async def admin_moderate_diary(
    entry_id: str,
    body: AdminDiaryModerationInput,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    """日记审核（visible/hidden/flagged）"""
    row = _dao.set_diary_moderation(
        diary_id=entry_id,
        status=body.status,
        moderator_id=ctx.admin_id,
        reason=body.reason,
    )
    ctx.log("moderate_diary", "diary", entry_id, detail=f"status={body.status} reason={body.reason}")
    return {"status": "success", "data": row}


@app.delete("/api/admin/diary/{entry_id}")
async def admin_delete_diary(
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
    entry_id: str,
    user_id: str = "",
) -> Dict[str, Any]:
    """删除日记"""
    deleted = _dao.delete_star_diary(entry_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="日记不存在")
    ctx.log("delete_diary", "diary", entry_id)
    return {"status": "success"}


@app.get("/api/admin/reports")
async def admin_list_reports(
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
    keyword: str = "",
    user_id: str = "",
    analysis_type: str = "",
    limit: int = 30,
    offset: int = 0,
) -> Dict[str, Any]:
    """星语者报告列表"""
    rows = _dao.list_all_reports(
        keyword=keyword,
        user_id=user_id,
        analysis_type=analysis_type,
        limit=limit,
        offset=offset,
    )
    total = _dao.count_all_reports(
        keyword=keyword, user_id=user_id, analysis_type=analysis_type,
    )
    return {"status": "success", "data": {"reports": rows, "total": total}}


@app.get("/api/admin/reports/{report_id}")
async def admin_get_report(
    report_id: str,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    """报告详情（含 JSON 文件内容）"""
    db = get_db()
    row = db.execute(
        "SELECT r.id, r.user_id, r.profile_id, r.analysis_type, "
        "r.kline_summary, r.report_data, r.created_at, "
        "u.phone, u.nickname "
        "FROM reports r LEFT JOIN users u ON r.user_id=u.id "
        "WHERE r.id=?",
        (report_id,),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="报告不存在")
    meta = dict(row)

    # 优先尝试读取 JSON 报告文件（fallback 内容）
    fp = os.path.join(DATA_DIR, f"{report_id}.json")
    report_body = None
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                report_body = json.load(f)
        except Exception:
            report_body = None

    # 若无 JSON 文件，尝试从 DB 的 report_data 字段解析
    if report_body is None and meta.get("report_data"):
        try:
            report_body = json.loads(meta["report_data"])
            meta.pop("report_data", None)
        except Exception:
            pass

    return {
        "status": "success",
        "data": {"meta": meta, "report": report_body},
    }


@app.delete("/api/admin/reports/{report_id}")
async def admin_delete_report(
    report_id: str,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    """删除报告（DB + JSON）"""
    db = get_db()
    cur = db.execute("DELETE FROM reports WHERE id=?", (report_id,))
    db.commit()
    db.close()
    deleted = cur.rowcount > 0
    if not deleted:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 同步 JSON 兜底删除
    fp = os.path.join(DATA_DIR, f"{report_id}.json")
    try:
        if os.path.exists(fp):
            os.remove(fp)
    except Exception:
        pass

    ctx.log("delete_report", "report", report_id)
    return {"status": "success"}


@app.get("/api/admin/audit-logs")
async def admin_list_audit(
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
    admin_username: str = "",
    action: str = "",
    target_type: str = "",
    limit: int = 30,
    offset: int = 0,
) -> Dict[str, Any]:
    """审计日志"""
    rows = _dao.list_audit_logs(
        admin_username=admin_username,
        action=action,
        target_type=target_type,
        limit=limit,
        offset=offset,
    )
    total = _dao.count_audit_logs(
        admin_username=admin_username,
        action=action,
        target_type=target_type,
    )
    return {"status": "success", "data": {"logs": rows, "total": total}}


@app.get("/api/admin/settings")
async def admin_get_settings(
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    return {"status": "success", "data": _dao.list_settings()}


@app.put("/api/admin/settings")
async def admin_put_setting(
    body: AdminSettingInput,
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    _dao.set_setting(body.key, body.value)
    ctx.log("set_setting", "system", body.key, detail=f"value={body.value[:60]}")
    return {"status": "success"}


@app.get("/api/admin/admins")
async def admin_list_admins(
    ctx: Annotated[_admin.AdminContext, Depends(_admin.require_admin)],
) -> Dict[str, Any]:
    return {"status": "success", "data": _dao.list_admins()}


@app.post("/api/admin/admins")
async def admin_create_admin(
    body: AdminCreateAdminInput,
    ctx: _admin.AdminContext = __import__("fastapi").Depends(_admin.require_super_admin),
) -> Dict[str, Any]:
    """新增管理员（仅 super_admin）"""
    existing = _dao.get_admin_by_username(body.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    from backend.admin import _hash_password
    admin = _dao.create_admin(
        username=body.username,
        password_hash=_hash_password(body.password),
        role=body.role,
    )
    ctx.log("create_admin", "admin", admin.get("id", ""), detail=f"username={body.username}")
    return {"status": "success", "data": admin}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
