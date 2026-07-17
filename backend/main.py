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
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from life_kline.analysis_catalog import get_analysis_type, list_analysis_types
from life_kline.service import LifeKlineService

from backend.database import get_db, init_db, _uid, _now


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

JWT_SECRET = os.getenv("LIFE_KLINE_JWT_SECRET", "dev-secret-change-in-production")


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
    lat: float
    lon: float
    timezone: float = 8.0


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
            "stored_at": datetime.utcnow().isoformat(),
        }
        save_report_record(report_id, record)

        if user_id and profile_id:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO reports (id, profile_id, user_id, analysis_type, report_data, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (report_id, profile_id, user_id, input_data.analysis_type, json.dumps(record, ensure_ascii=False), _now()),
                )
                db.commit()
                db.close()
            except Exception:
                pass

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
    user_id = ""
    profile_id = ""
    token = authorization.replace("Bearer ", "")
    uid = _parse_token(token)
    if uid:
        user_id = uid
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
    return run_analysis(input_data, user_id=user_id, profile_id=profile_id)


@app.get("/api/reports/history")
async def report_history(authorization: str = Header(default="")) -> Dict[str, Any]:
    token = authorization.replace("Bearer ", "")
    user_id = _parse_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    db = get_db()
    rows = db.execute(
        "SELECT id, profile_id, analysis_type, created_at FROM reports WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
        (user_id,),
    ).fetchall()
    db.close()
    return {"status": "success", "reports": [dict(r) for r in rows]}


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
async def get_character_profiles(report_id: str) -> Dict[str, Any]:
    """获取12星座个性化角色画像"""
    record = load_report_record(report_id)
    data = record.get("data", {})
    characters = data.get("characters", {})
    if not characters:
        raise HTTPException(status_code=404, detail="Character profiles not found in this report")
    return {"status": "success", "report_id": report_id, "data": characters}


@app.get("/api/characters/{report_id}/daily")
async def get_daily_activation(report_id: str) -> Dict[str, Any]:
    """获取今日角色激活度和登场角色"""
    record = load_report_record(report_id)
    user_info = record.get("data", {}).get("user_info", {})
    if not user_info:
        raise HTTPException(status_code=400, detail="User info missing from report")

    from life_kline.ephemeris import EphemerisEngine
    from life_kline.firdaria import FirdariaPeriod, calculate_firdaria_periods
    from life_kline.constants import Planet
    from life_kline.characters.character_engine import CharacterEngine
    from life_kline.awakening.daily_engine import DailyAwakeningEngine

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
    activation = daily_engine.compute_daily_activation()

    return {"status": "success", "report_id": report_id, "data": activation.to_dict()}


@app.post("/api/characters/{report_id}/chat")
async def chat_with_character(report_id: str, body: CharacterChatInput) -> Dict[str, Any]:
    """与指定星座角色对话"""
    record = load_report_record(report_id)
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
async def character_council(report_id: str, body: CouncilInput) -> Dict[str, Any]:
    """获取多个角色对同一话题的不同视角"""
    record = load_report_record(report_id)
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


# ── 用户系统路由 ──────────────────────────────────────────

@app.on_event("startup")
async def startup_event() -> None:
    init_db()
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


@app.get("/api/me")
async def get_me(authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    profiles = db.execute("SELECT * FROM profiles WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    db.close()
    return {"status": "success", "user": dict(user) if user else None, "profiles": [dict(p) for p in profiles]}


@app.post("/api/profiles")
async def create_profile(body: ProfileInput, authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    pid = _uid()
    db = get_db()
    db.execute("INSERT INTO profiles (id, user_id, name, gender, birth_time, lat, lon, timezone, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (pid, uid, body.name, body.gender, body.birth_time, body.lat, body.lon, body.timezone, 0, _now()))
    db.commit()
    db.close()
    return {"status": "success", "profile_id": pid}


@app.get("/api/profiles")
async def list_profiles(authorization: str = Header(default="")) -> Dict[str, Any]:
    uid = _parse_token(authorization.replace("Bearer ", ""))
    if not uid:
        raise HTTPException(status_code=401, detail="请先登录")
    db = get_db()
    rows = db.execute("SELECT * FROM profiles WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    db.close()
    return {"status": "success", "profiles": [dict(r) for r in rows]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
