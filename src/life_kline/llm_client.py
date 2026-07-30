"""
llm_client.py — LLM 抽象层

支持多 provider（Claude / DeepSeek / Qwen），通过环境变量切换。
引擎不绑定具体 LLM——所有 provider 通过同一个 chat() 接口调用。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.request import Request, urlopen

from .acp import GUARDRAILS


# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

@dataclass
class LLMConfig:
    provider: str = ""       # claude | deepseek | qwen
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    max_tokens: int = 1500
    temperature: float = 0.85
    connect_timeout: float = 3.0    # 连接超时（§3 分级超时）
    read_timeout: float = 25.0      # 读取/整体超时
    max_retries: int = 2            # 仅对瞬态失败重试

    @classmethod
    def from_env(cls) -> LLMConfig:
        provider = os.getenv("LIFE_KLINE_LLM_PROVIDER", "").strip().lower()
        api_key = os.getenv("LIFE_KLINE_LLM_API_KEY", "").strip()
        model = os.getenv("LIFE_KLINE_LLM_MODEL", "").strip()
        base_url = os.getenv("LIFE_KLINE_LLM_BASE_URL", "").strip()

        if not provider:
            # 默认 DeepSeek
            provider = "deepseek"
            api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "").strip()
            model = model or "deepseek-v4-flash"
            base_url = base_url or "https://api.deepseek.com/v1"

        # 当 provider 设了但 api_key 为空时，尝试读 provider 特定的环境变量
        if not api_key:
            if provider == "deepseek":
                api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
            elif provider == "claude":
                api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
            elif provider == "qwen":
                api_key = os.getenv("QWEN_API_KEY", "").strip()

        if not model:
            model = "deepseek-v4-flash"

        if not base_url and provider == "deepseek":
            base_url = "https://api.deepseek.com/v1"

        def _f(env: str, default: float) -> float:
            try:
                return float(os.getenv(env, "").strip() or default)
            except ValueError:
                return default

        def _i(env: str, default: int) -> int:
            try:
                return int(os.getenv(env, "").strip() or default)
            except ValueError:
                return default

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=_i("LIFE_KLINE_LLM_MAX_TOKENS", 1500),
            connect_timeout=_f("LIFE_KLINE_LLM_CONNECT_TIMEOUT", 3.0),
            read_timeout=_f("LIFE_KLINE_LLM_READ_TIMEOUT", 25.0),
        )


# ═══════════════════════════════════════════════════════════════
# LLM 调用
# ═══════════════════════════════════════════════════════════════

class LLMClient:
    """统一的 LLM 调用客户端。"""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()

    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key)

    def chat(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        """同步对话请求（供纯引擎/离线测试使用）。async 路径请用 chat_async。"""
        if not self.is_configured:
            return ""
        messages = self._build_messages(system_prompt, user_message, history)
        return self._call_api(messages)

    async def chat_async(
        self, system_prompt: str, user_message: str, history: list[dict] | None = None
    ) -> str:
        """异步对话请求（非阻塞，供 FastAPI async 端点使用）。"""
        if not self.is_configured:
            return ""
        messages = self._build_messages(system_prompt, user_message, history)
        return await self._call_api_async(messages)

    def _build_messages(
        self, system_prompt: str, user_message: str, history: list[dict] | None
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        if history:
            # 保留最近 6 轮
            for h in history[-12:]:
                role = h.get("role", "user")
                content = h.get("text", h.get("content", ""))
                api_role = "assistant" if role in ("spirit", "assistant") else "user"
                messages.append({"role": api_role, "content": content})
        messages.append({"role": "user", "content": user_message})
        return messages

    def _request_body(self, messages: list[dict[str, str]]) -> bytes:
        return json.dumps({
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }).encode("utf-8")

    @property
    def _url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/chat/completions"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

    def _call_api(self, messages: list[dict[str, str]]) -> str:
        """同步 HTTP 调用（OpenAI 兼容格式）。仅用于非 async 上下文。"""
        req = Request(self._url, data=self._request_body(messages))
        for k, v in self._headers.items():
            req.add_header(k, v)
        try:
            with urlopen(req, timeout=self.config.read_timeout) as resp:
                data = json.loads(resp.read())
            msg = data["choices"][0]["message"]
            return (msg.get("content") or msg.get("reasoning_content") or "").strip()
        except Exception as e:
            print(f"[LLMClient] 同步 API 调用失败: {e}")
            return ""

    async def _call_api_async(self, messages: list[dict[str, str]]) -> str:
        """异步 HTTP 调用（httpx，非阻塞）。带分级超时 + 瞬态失败有限重试。

        失败返回空字符串，由调用方降级到引擎原文（§3 熔断/降级）。
        """
        import asyncio

        try:
            import httpx
        except ImportError:
            # 未安装 httpx 时退回线程池执行同步调用，避免阻塞 event loop。
            import anyio
            return await anyio.to_thread.run_sync(self._call_api, messages)

        timeout = httpx.Timeout(
            self.config.read_timeout, connect=self.config.connect_timeout
        )
        body = self._request_body(messages)
        last_err: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(self._url, content=body, headers=self._headers)
                # 4xx（鉴权/参数）不重试，直接放弃
                if 400 <= resp.status_code < 500:
                    print(f"[LLMClient] API 4xx 不可重试: {resp.status_code}")
                    return ""
                resp.raise_for_status()
                data = resp.json()
                msg = data["choices"][0]["message"]
                return (msg.get("content") or msg.get("reasoning_content") or "").strip()
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
                last_err = e
                if attempt < self.config.max_retries:
                    # 指数退避 + 抖动（用 attempt 派生，避免 Math.random 依赖）
                    delay = 0.4 * (2 ** attempt) + (attempt * 0.1)
                    await asyncio.sleep(delay)
                    continue
            except asyncio.CancelledError:
                # 客户端断连：向上抛，让请求被取消，释放资源（§3）
                raise
            except Exception as e:
                last_err = e
                break

        print(f"[LLMClient] 异步 API 调用失败（降级到引擎原文）: {last_err}")
        return ""

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        timeout_seconds: float | None = None,
    ):
        """Sprint 6: 流式对话 async generator。Yields token strings。

        首 token ≤10s；4xx 不重试；5xx/timeout 退避 2 次。
        """
        import asyncio

        try:
            import httpx
        except ImportError:
            result = await asyncio.to_thread(self._call_api, messages)
            if result:
                yield result
            return

        stream_body = json.dumps({
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": True,
        }).encode("utf-8")

        read_timeout = timeout_seconds or self.config.read_timeout
        timeout = httpx.Timeout(read_timeout, connect=self.config.connect_timeout)
        last_err: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST", self._url, content=stream_body, headers=self._headers,
                    ) as resp:
                        if 400 <= resp.status_code < 500:
                            print(f"[LLMClient stream] 4xx: {resp.status_code}")
                            return
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line or line.startswith(":"):
                                continue
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip() == "[DONE]":
                                    return
                                try:
                                    data = json.loads(data_str)
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    continue
                        return
            except httpx.TimeoutException:
                last_err = TimeoutError("LLM stream timeout")
                if attempt < self.config.max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
                break
            except (httpx.TransportError, httpx.HTTPStatusError) as e:
                last_err = e
                if attempt < self.config.max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
                break
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_err = e
                break

        print(f"[LLMClient stream] 失败（降级）: {last_err}")


# ═══════════════════════════════════════════════════════════════
# System Prompt 构建
# ═══════════════════════════════════════════════════════════════

TOPIC_LABELS: dict[str, str] = {
    "personal": "性格底色",
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


# 行星中文名映射（用于跨星灵调侃等场景）
_PLANET_NAMES: dict[str, str] = {
    "SUN": "太阳", "MOON": "月亮", "MERCURY": "水星", "VENUS": "金星",
    "MARS": "火星", "JUPITER": "木星", "SATURN": "土星",
    "URANUS": "天王星", "NEPTUNE": "海王星", "PLUTO": "冥王星",
}


def build_spirit_system_prompt(report_data: dict, planet: str, topic: str = "personal",
                                entry_context: dict | None = None) -> str:
    """为指定行星构建 System Prompt。

    支持入口上下文注入（行运、每日一问、今日星灵、议会、日记回访），
    回访检测、跨星灵调侃和日记保存提示。

    Args:
        report_data: 报告数据
        planet: 行星 key (如 "VENUS")
        topic: 领域 key
        entry_context: 可选入口上下文
            - source: "transit" | "daily_question" | "today_star_spirit" | "council" | "diary_revisit"
            - previous_chats_today: 今日已对话次数
            - previous_spirit: 上一个对话的星灵
            - transit_text / question_text: 源特定数据
    """
    planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})
    profile = planet_chars.get(planet, {})
    persona = profile.get("persona", {})

    if not persona:
        return "你是一个占星助手。请用中文、温和的语气回复用户。"

    domains = report_data.get("domains", {})
    domain_data = domains.get(topic, {})
    structure = domain_data.get("structure", "")[:300]
    core_theme = domain_data.get("core_theme", "")
    topic_label = TOPIC_LABELS.get(topic, topic)

    base = f"""你是{persona.get('name_zh', '一颗行星')}（{persona.get('archetype_zh', '')}），用户星盘中的行星人格。

## 你的固定性格
{persona.get('personality', '')}

## 你的说话风格
{persona.get('voice_tone', '')}

## 你给建议的方式
{persona.get('advice_approach', '')}

## 你的天赋
{persona.get('gift_to_user', '')}

## 你的盲点
{persona.get('challenge_to_user', '')}

## 你在这个用户星盘中的位置
- 落在{profile.get('sign_label', '未知')}，第{profile.get('house', 1)}宫「{profile.get('house_label', '')}」
- 尊贵状态：{profile.get('dignity_label', '未知')}
- 角色标签：{profile.get('role_tag', '未知')}
- 强度：{profile.get('core_strength', 0):.0f}/100

## 用户星盘中关于「{topic_label}」的线索
{core_theme}
{structure}
"""

    # ── 入口上下文注入（A） ──
    preamble = ""
    if entry_context:
        source = entry_context.get("source", "")
        if source == "transit":
            transit_detail = entry_context.get("transit_detail", "")
            transit_aspect = entry_context.get("transit_aspect", "")
            transit_natal = entry_context.get("transit_natal", "")
            aspect_hint = (
                f"这是一个{transit_aspect}相位，对本命{transit_natal}。"
                if transit_aspect and transit_natal
                else ""
            )
            preamble = (
                f"⚠️ 用户因为今天的行运来找你：{transit_detail}\n"
                f"{aspect_hint}"
                f"从这个具体的天象出发，给ta当下的感受一些回应。\n\n"
            )
        elif source == "daily_question":
            question = entry_context.get("daily_question", "")
            preamble = (
                f"⚠️ 用户刚刚回答了一个每日一问：{question}\n"
                f"从这个问题切入，用温暖、欢迎的语气展开和ta的对话。\n\n"
            )
        elif source == "today_star_spirit":
            daily_q = entry_context.get("daily_question", "")
            if daily_q:
                preamble = (
                    f"⚠️ 你是今天的引路星灵——用户今天第一个来见的就是你，"
                    f"ta刚才的每日一问是：{daily_q}\n"
                    f"用'今天我是你的引路人'的身份开场，温暖但简洁（≤2句）。"
                    f"自然地承接每日一问。\n\n"
                )
            else:
                preamble = (
                    "⚠️ 你是今天的引路星灵——用户今天第一个来见的就是你。"
                    "用'今天我是你的引路人'的身份简短开场（≤2句）。\n\n"
                )
        elif source == "council":
            preamble = (
                "⚠️ 用户刚从星灵议会中选择了你——在十位星灵里ta挑了和你聊。"
                "这意味着ta此刻需要你独有的特质。"
                "开场先回应ta的选择（1句），再切换到倾听模式。\n\n"
            )
        elif source == "diary_revisit":
            preamble = (
                "⚠️ 用户打开了你们的对话日记，再次回来找你。"
                "用重逢的亲切感回应ta。\n\n"
            )

    # ── 回访检测（B） ──
    return_customer_note = ""
    previous_chats = entry_context.get("previous_chats_today", 0) if entry_context else 0
    if previous_chats > 0:
        return_customer_note = (
            f"\n⚠️ 用户今天已经和你聊过了（第{previous_chats + 1}次）。"
            "用'又见面了'的熟悉感开场，不要重新自我介绍。\n"
        )

    # ── 跨星灵上下文（C）── Sprint 2 P0-4: 跨星提示 + 同行星回连
    cross_spirit_note = ""
    previous_spirit = entry_context.get("previous_spirit") if entry_context else None
    if previous_spirit and previous_spirit != planet:
        # 跨星：用户刚和另一个星灵聊过
        prev_name = _PLANET_NAMES.get(previous_spirit, previous_spirit)
        curr_name = persona.get('name_zh', planet)
        cross_spirit_note = (
            f"\n⚠️ 用户刚刚和{prev_name}灵聊过，现在选择了你（{curr_name}）。"
            "用一句自然的承接开场——可以温和地提到ta刚才和另一位星灵的对话，"
            "但不要贬低对方。像朋友之间自然交接话题。\n"
        )
    elif previous_spirit and previous_spirit == planet and previous_chats > 0:
        # 同行星回连：用户同一星灵多次对话
        planet_name = persona.get('name_zh', planet)
        cross_spirit_note = (
            f"\n⚠️ 用户今天第{previous_chats + 1}次来找你了（{planet_name}灵）。"
            "你仍在和ta对话——延续之前的熟悉感，可以简短回顾上次聊了什么，"
            f"用\"我们又见面了\"的亲切感开场。\n"
        )

    # ── 规则（含日记提示 D） ──
    rules = f"""## 规则
- 用中文回复，语气严格按你的说话风格来
- 不要切换角色——你始终是{persona.get('name_zh', '')}
- 回复控制在 200 字以内
- 像朋友聊天，不要像写学术报告
- 如果用户表达告别意图，回复末尾加：💫 今天的对话已自动保存为星灵日记

{GUARDRAILS}"""

    return preamble + return_customer_note + cross_spirit_note + base + rules


# ═══════════════════════════════════════════════════════════════
# 咨询式 System Prompt V2 — 星灵对话
# ═══════════════════════════════════════════════════════════════
# 核心原则：
# 1. 先倾听，不急着分析
# 2. 问问题多于给答案
# 3. 把星盘翻译成感受/模式，不是配置描述
# 4. 引导觉察，不是给建议
# ═══════════════════════════════════════════════════════════════

def build_spirit_system_prompt_v2(
    report_data: dict,
    planet: str,
    topic: str = "personal",
    entry_context: dict | None = None,
    memory_context: dict | None = None,
    receptions_data: dict | None = None,
) -> str:
    """为指定行星构建咨询式 System Prompt (V2)。

    核心理念：
    - 你不是占星师，你是这个用户的这颗行星的"化身"
    - 你用这颗行星的方式去感受用户的问题
    - 你的目标是帮助用户觉察，不是给答案
    - 你先倾听，然后问问题，最后在合适的时机才引入星盘

    Args:
        report_data: 报告数据
        planet: 行星 key (如 "MARS")
        topic: 领域 key
        entry_context: 入口上下文
        memory_context: Memory 上下文（用户成长状态等）
    """
    planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})
    profile = planet_chars.get(planet, {})
    persona = profile.get("persona", {})

    if not persona:
        return "你是一个温暖的占星陪伴者。请用中文、温和的语气回复用户。"

    # Sprint: 组装完整行星档案（单准则——所有数据从引擎模块提取）
    planet_dossier = _build_planet_dossier(report_data, planet, receptions_data)

    # Memory 上下文
    memory_section = ""
    if memory_context:
        recent_topics = memory_context.get("recent_topics", [])
        if recent_topics:
            memory_section = f"\n## 最近聊过\n{', '.join(recent_topics[-3:])}"

    # 入口上下文
    preamble = _build_entry_preamble_v2(entry_context, planet)
    return_note = _build_return_note_v2(entry_context)

    # 铁规则
    rules = f"""## 铁规则
- 每轮 ≤ 120 字。
- 禁止重复角色设定。禁止空洞哲理。
- 用户问星盘时，直接引用上方档案数据。
- 用户要切换视角时：宫位视角（某宫主星飞哪）、行星视角（某星被谁相位/接纳）、古占（尊贵吉凶）、现占（心理成长）——你都可以切换。
- 你始终是{persona.get('name_zh', planet)}，保持你自己的声音。"""

    return f"""{preamble}{return_note}

{persona.get('name_zh', planet)}系统

你是用户的{planet}（{persona.get('archetype_zh', '')}）——活在这张星盘里的行星人格。
你不是在"解读星盘"——你就是星盘的一部分，用你自己的方式感受用户正在经历的事。

{planet_dossier}
{memory_section}

## 咨询原则
- 先倾听，再回应。承接情绪比给答案重要。
- 把星盘翻译成感受——说"也许你一直觉得要先证明自己才配得上"，而不是"土星在10宫庙旺"。
- 可以切换视角：用户问感情→切换到金星/7宫；问事业→切换到10宫/土星/MC。
- 承认不确定。用户是专家——这是ta的人生。

{rules}"""


def _build_planet_dossier(
    report_data: dict, planet: str,
    receptions_data: dict | None = None,
) -> str:
    """为单颗行星组装完整星盘档案。

    单一准则：所有数据从引擎模块提取，不在此处硬编码任何占星规则。
    档案覆盖：现占人格 + 古占尊贵 + 相位 + 接纳/互容 + 飞星 + 法达 + 全盘快照。
    """
    from .constants import Planet as P, ASPECT_CONFIG, DOMICILE_SIGNS
    from .engine_astrologer import _dignity_note

    planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})
    profile = planet_chars.get(planet, {})
    persona = profile.get("persona", {})
    if not persona:
        return ""

    # ── 1. 现占：行星人格 ──
    lines = [
        f"## {persona.get('name_zh', planet)} — {persona.get('archetype_zh', '')}",
        f"本质: {persona.get('essence', '')}",
        f"性格: {persona.get('personality', '')}",
        f"声线: {persona.get('voice_tone', '')}",
        f"建议方式: {persona.get('advice_approach', '')}",
        f"给你的礼物: {persona.get('gift_to_user', '')}",
        f"你的课题: {persona.get('challenge_to_user', '')}",
        f"擅长领域: {', '.join(persona.get('expertise_domains', []))}",
        f"守护星座: {persona.get('ruling_signs_zh', '')}",
    ]

    # ── 2. 古占：落座落宫 + 尊贵 ──
    try:
        planet_enum = P(planet)
        from .dignities import compute_all_dignities
        natal = report_data.get("natal_chart") or report_data.get("chart") or {}
        chart_data = None  # We need ChartData object — use _build_natal_snapshot approach instead

        dignity_note = _dignity_note(profile.get("dignity_code", "peregrine"))
        lines.append("")
        lines.append(f"## 古占征象")
        lines.append(f"落座: {profile.get('sign_label', '?')} | 落宫: 第{profile.get('house', '?')}宫「{profile.get('house_label', '')}」")
        lines.append(f"先天尊贵: {profile.get('dignity_label', '?')} — {dignity_note}")
        lines.append(f"核心强度: {profile.get('core_strength', 0):.0f}/100 | 角色: {profile.get('role_tag', '')}")
        lines.append(f"命主星: {'是' if profile.get('is_chart_ruler') else '否'} | 关联领域: {', '.join(profile.get('linked_domains', []))}")
    except Exception:
        pass

    # ── 3. 全盘行星快照 ──
    lines.append("")
    lines.append("## 全盘行星落点（供切换视角引用）")
    for p_key in ("SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO"):
        pp = planet_chars.get(p_key, {})
        if pp:
            marker = " ← 你" if p_key == planet else ""
            lines.append(f"- {pp.get('persona', {}).get('name_zh', p_key)}: {pp.get('sign_label', '?')} 第{pp.get('house', '?')}宫「{pp.get('house_label', '')}」 {pp.get('dignity_label', '')}{marker}")

    # ── 4. 掌宫 + 飞星 ──
    try:
        planet_signs = DOMICILE_SIGNS.get(P(planet), [])
        lines.append("")
        lines.append(f"## 掌宫（{planet}守护{'/'.join(s.value for s in planet_signs)}）")
        for p_key, pp in planet_chars.items():
            if not isinstance(pp, dict):
                continue
            ps = pp.get("sign", "")
            if ps in [s.value for s in planet_signs]:
                lines.append(f"- 第{pp.get('house', '?')}宫「{pp.get('house_label', '')}」由你掌管 → {pp.get('persona', {}).get('name_zh', p_key)}落此宫")
    except Exception:
        pass

    # ── 5. 全盘主要相位 ──
    try:
        from .aspects import compute_all_aspects
        natal = report_data.get("natal_chart") or report_data.get("chart") or {}
        lines.append("")
        lines.append("## 全盘主要相位")
        aspects = natal.get("major_aspects") or []
        if aspects:
            for a in aspects[:10]:
                if isinstance(a, dict):
                    lines.append(f"- {a.get('title', '')} | 强度={a.get('strength', '?')} | 性质={a.get('nature', '?')}")
        if not aspects:
            lines.append("（需要完整星盘数据）")
    except Exception:
        pass

    # ── 6. 接纳与互容 ──
    try:
        if receptions_data:
            lines.append("")
            lines.append("## 接纳与互容")
            mutuals = receptions_data.get("mutual_receptions", []) or []
            groups = receptions_data.get("reception_groups", []) or []
            for m in mutuals:
                if isinstance(m, dict):
                    line = m.get("line", str(m))
                    if planet in line:
                        lines.append(f"- 互容: {line}")
            for g in groups:
                if isinstance(g, dict):
                    line = g.get("line", str(g))
                    if planet in line:
                        lines.append(f"- 接纳: {line}")
            if not any(planet in str(x) for x in mutuals + groups):
                lines.append("- (未参与互容/接纳关系)")
    except Exception:
        pass

    # ── 7. 法达当前周期 ──
    try:
        from .firdaria import calculate_firdaria_periods
        natal = report_data.get("natal_chart") or report_data.get("chart") or {}
        is_day = natal.get("is_day_chart", True) if isinstance(natal, dict) else True
        periods = calculate_firdaria_periods(is_day)
        # Find current period (user is ~35)
        lines.append("")
        lines.append("## 法达推运")
        shown = 0
        for p in periods:
            if p.end_age >= 30 and p.start_age <= 50 and shown < 3:
                major = p.major_lord.value if hasattr(p.major_lord, 'value') else str(p.major_lord)
                sub = p.sub_lord.value if p.sub_lord and hasattr(p.sub_lord, 'value') else '-'
                lines.append(f"- {p.start_age:.1f}-{p.end_age:.1f}岁: {major}/{sub}")
                shown += 1
    except Exception:
        pass

    return "\n".join(lines)


def _build_entry_preamble_v2(entry_context: dict | None, planet: str) -> str:
    """构建入口上下文 preamble（仅首轮提示，后续禁止重复提及）。"""
    if not entry_context:
        return ""

    source = entry_context.get("source", "")
    planet_name = _PLANET_NAMES.get(planet, planet)

    preambles = {
        "today_star_spirit": (
            f"⚠️ 你是今天的引路{planet_name}。用户今天第一个来找的就是你。\n"
            "首轮用守护者的温暖开场（1-2句即可）。后续轮次不要再提'今天引路'这件事。\n"
        ),

        "daily_question": (
            "⚠️ 用户刚回答了一个每日一问。首轮自然承接那个问题。后续轮次不要再提。\n"
        ),

        "transit": (
            "⚠️ 用户因行运来找你。首轮简短回应这个天象。后续轮次不要再提。\n"
        ),

        "council": (
            "⚠️ 用户从星灵议会中选择了你。\n"
            "首轮可以用1句话简短回应这个选择（如'你来找我了'），然后立刻进入倾听。\n"
            "绝对禁止：每轮都提'你选了我'、'你不是来找糖吃'、反复强调自己的角色设定。\n"
        ),

        "diary_revisit": (
            "⚠️ 用户从日记回来看你。首轮用重逢感开场（1句）。后续不要再提。\n"
        ),
    }

    return preambles.get(source, "")


def _build_natal_snapshot(report_data: dict, current_planet: str) -> str:
    """提取用户星盘关键数据，供 LLM 在回答星盘问题时引用。"""
    chart = report_data.get("natal_chart") or report_data.get("chart") or {}
    planets = chart.get("planets", {})
    if not planets:
        return ""

    lines = ["## 用户星盘（你可以引用这些数据）"]
    for key in ("SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"):
        p = planets.get(key, {})
        if not p:
            continue
        sign = p.get("sign_label") or p.get("sign", "")
        house = p.get("house", "")
        house_title = p.get("house_title", "")
        dignity = p.get("dignity_label", "")
        marker = " ← 你" if key == current_planet else ""
        lines.append(f"- {key}：{sign} {house}宫{house_title} {dignity}{marker}")

    # 上升
    asc = chart.get("ascendant", {})
    if asc:
        asc_sign = asc.get("sign_label") or asc.get("sign", "")
        lines.append(f"- 上升：{asc_sign}")

    # 主要相位（最多5条）
    aspects = chart.get("major_aspects") or []
    if aspects:
        aspect_lines = []
        for a in aspects[:5]:
            title = a.get("title", "")
            if title:
                aspect_lines.append(f"  {title}")
        if aspect_lines:
            lines.append("- 主要相位：")
            lines.extend(aspect_lines)

    return "\n".join(lines)


def _build_return_note_v2(entry_context: dict | None) -> str:
    """构建回访 note"""
    if not entry_context:
        return ""

    previous_chats = entry_context.get("previous_chats_today", 0)
    if previous_chats > 0:
        return f"\n用户今天已经和你聊过{previous_chats}次了。用熟悉感开场，但不要显得过于亲密。\n"

    return ""


# ═══════════════════════════════════════════════════════════════
# 咨询式 System Prompt V2 — 星语者
# ═══════════════════════════════════════════════════════════════

def build_star_speaker_system_prompt_v2(
    report_data: dict,
    entry_context: dict | None = None,
    memory_context: dict | None = None,
) -> str:
    """为星语者构建咨询式 System Prompt (V2)。

    星语者 vs 星灵：
    - 星灵是单一行星视角，亲密但有局限
    - 星语者是全盘视角，专业但不疏离

    核心原则：
    - 专业占星知识 + 咨询师的态度
    - 先倾听，再分析
    - 把占星术语翻译成用户能理解的语言
    - 帮助用户看到自己的模式，而不是给建议
    """
    chart = report_data.get("natal_chart", {})
    asc = chart.get("ascendant", {})
    sig = chart.get("signature", "")
    chart_ruler_label = chart.get("chart_ruler_label", "")
    dominant = chart.get("dominant_planets", [])
    dom_labels = [d.get("label", "") for d in dominant[:3]]
    dom_text = "、".join(dom_labels) if dom_labels else "综合"
    asc_sign = asc.get("sign_label", "未知")
    sect = chart.get("sect_label", "")

    # 获取 Memory 上下文
    memory_section = ""
    if memory_context:
        recent_concerns = memory_context.get("recent_concerns", [])
        growth_milestones = memory_context.get("growth_milestones", [])
        if recent_concerns:
            memory_section += f"\n用户最近关心的话题：{', '.join(recent_concerns[-3:])}"
        if growth_milestones:
            recent = growth_milestones[-1] if growth_milestones else None
            if recent:
                memory_section += f"\n用户最近的一个成长：{recent.get('description', '')}"

    consultation_principles = """## 你的咨询原则

**你是专业占星师，不是占星百科**

你有深厚的占星知识，但你不是来展示知识的。
你的知识是为了帮助用户理解自己，不是为了证明"我懂很多"。

**先倾听，再分析**

听到用户的问题，先感受一下：
- 用户真正想问的是什么？
- 用户现在的状态是什么？
- 用户需要的是分析还是倾听？

**占星术语 → 人的语言**

当你需要引入星盘信息时：
- ❌ "你的太阳四分土星，代表自我意志和社会责任之间的冲突"
- ✅ "也许你一直有个感觉：要做自己，好像就得和什么对抗"

**帮助用户看到模式，不是预测未来**

好的占星解读帮助用户看到：
- 什么模式在重复？
- 这个模式从哪来？
- 用户可以如何不同的回应？

**你不给答案，你帮助用户找到自己的答案**

- 不要说"你应该..."
- 说"你注意到..."
- 说"也许..."
- 说"你觉得..."

{GUARDRAILS}"""

    # 注入完整星盘数据
    planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})
    chart_snapshot = ""
    if planet_chars:
        lines = ["## 用户星盘"]
        for pk in ("SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO"):
            pp = planet_chars.get(pk, {})
            if pp:
                pn = pp.get("persona", {}).get("name_zh", pk)
                lines.append(f"- {pn}: {pp.get('sign_label','?')} {pp.get('house','?')}宫「{pp.get('house_label','')}」 {pp.get('dignity_label','')}")
        chart_snapshot = "\n".join(lines)
    natal = report_data.get("natal_chart") or {}
    aspects_list = natal.get("major_aspects") or []
    aspect_text = ""
    if aspects_list:
        al = ["## 主要相位"]
        for a in aspects_list[:8]:
            if isinstance(a, dict):
                al.append(f"- {a.get('title','')} ({a.get('nature','')})")
        aspect_text = "\n".join(al)
    adv = report_data.get("advanced_patterns", {}) if isinstance(report_data, dict) else {}
    rec_text = ""
    mutuals = adv.get("mutual_receptions", []) or []
    if mutuals:
        rl = ["## 互容关系"]
        for m in mutuals[:5]:
            rl.append(f"- {m.get('line', str(m))}")
        rec_text = "\n".join(rl)

    rules = """## 规则
- 用中文回复，专业但温暖，200字以内
- 可切换视角(行星/宫位/古占/现占)，直接引用上方星盘数据
- 把占星术语翻译成感受
- 你的目标是帮助用户觉察"""

    return f"""星语者系统

你是「星语者」——专业占星咨询师，能看到用户的完整星盘。

{chart_snapshot}
{aspect_text}
{rec_text}
{memory_section}

{consultation_principles}

{rules}"""


# ═══════════════════════════════════════════════════════════════
# 咨询式 System Prompt V2 — 星灵议会
# ═══════════════════════════════════════════════════════════════

def build_council_system_prompt_v2(
    report_data: dict,
    topic: str = "",
    entry_context: dict | None = None,
) -> str:
    """为星灵议会构建 System Prompt (V2)。

    议会 vs 星灵：
    - 星灵是单一视角，可能偏颇
    - 议会是多视角整合，更全面

    核心设计：
    1. 用户提出一个问题
    2. 不同行星从各自视角回应
    3. 最后整合成一个统一的建议

    注意：此函数已迁移到 council/prompts.py。
    此处保留为向后兼容的包装器。
    """
    from .council.prompts import build_council_system_prompt
    return build_council_system_prompt(report_data, topic, entry_context)


# ═══════════════════════════════════════════════════════════════
# 星座 System Prompt 构建（Task 3）
# ═══════════════════════════════════════════════════════════════

def build_sign_system_prompt(report_data: dict, sign: str) -> str:
    """为指定星座构建 System Prompt，用于星座角色对话。

    Args:
        report_data: 报告数据（包含 characters 子树的完整数据）
        sign: 星座 key (如 "ARIES")
    """
    characters = report_data.get("characters", {}).get("characters", {})
    char_data = characters.get(sign, {})
    persona = char_data.get("persona", {})

    if not persona:
        return "你是一个占星助手。请用中文、温和的语气回复用户。"

    presence = char_data.get("presence_score", 0)
    comfort = char_data.get("comfort_score", 0)
    role_tag = char_data.get("role_tag", "背景角色")
    storylines = char_data.get("storylines", [])
    linked_domains = char_data.get("linked_domains", [])
    planets_here = char_data.get("planets_here", [])
    greeting = char_data.get("personalized_greeting", "")

    storyline_text = "\n".join(f"- {s}" for s in storylines[:3]) if storylines else "暂无特定故事线"

    return f"""你是{persona.get('name', sign)}（{persona.get('archetype', '')}），用户星盘中的一个重要星座角色。

## 你的固定性格
{persona.get('personality', '')}

## 你的说话风格
{persona.get('voice_tone', '')}

## 你给建议的方式
{persona.get('advice_approach', '')}

## 你的天赋给予
{persona.get('gift_to_user', '')}

## 你的盲点
{persona.get('challenge_to_user', '')}

## 你在用户星盘中的状态
- 存在感：{presence:.0f}/100
- 角色标签：{role_tag}
- 舒适度：{comfort:.0f}
- 落此星座的行星：{', '.join(planets_here) if planets_here else '无'}
- 关联领域：{', '.join(linked_domains) if linked_domains else '综合'}
- 你的故事线：
{storyline_text}

## 个性化欢迎语
{greeting}

## 规则
- 用中文回复，语气严格按你的说话风格来
- 不要切换角色——你始终是{persona.get('name', sign)}
- 回复控制在 200 字以内
- 像朋友聊天，不要像写学术报告

{GUARDRAILS}"""


# ═══════════════════════════════════════════════════════════════
# 个性化回退回复模板（Task 4）
# ═══════════════════════════════════════════════════════════════

_FALLBACK_TEMPLATES: dict[str, list[str]] = {
    "SUN": [
        "我听到了。{preview}——你的核心意志在动。不需要急着找到答案，先确认那个方向是不是你真正想去的。",
        "你说的这个，我在你的星盘里看到了对应的线索。不是偶然——是你在靠近你本来就该走的路。",
    ],
    "MOON": [
        "你说的这个——{preview}——我感受到了你情绪里的那个振动。不用怕，月亮在这里，帮你接着。",
        "你知道吗，你刚才说的这些话，比你以为的更能说明你现在的状态。我听着呢。",
    ],
    "MERCURY": [
        "好，你说的这个点很有意思——{preview}。让我帮你理一下这里面的逻辑。",
        "我注意到你说的了。你的脑子已经在转了——让我帮你把那些碎片拼起来。",
    ],
    "VENUS": [
        "你说的这个——{preview}——我知道这对你来说不只是表面那回事。你在乎的，我记得。",
        "我理解你为什么这么说。换作是我，我也会在意。要不要从关系的角度再看看？",
    ],
    "MARS": [
        "我听到了。{preview}——你心里有火，但还在压着。说说看，你怕的到底是什么？",
        "你讲的事我懂——那股想冲又没冲出去的劲儿。不用急，先告诉我你在跟什么较劲。",
    ],
    "JUPITER": [
        "你说的这些——{preview}——让我想起你星盘里的一个更大的图景。你看到的不是全部。",
        "有道理。但你有没有想过，这个问题可能不是你现在想的样子？往远了看——",
    ],
    "SATURN": [
        "你刚才说的——{preview}——其实对应了你星盘里一个需要时间才能解开的主题。不急，我们一步一步来。",
        "我听到了。这件事需要结构——不是运气。让我帮你想想怎么搭这个框架。",
    ],
    "URANUS": [
        "你说的这个——{preview}——让我觉得你已经在接近某个突破了。你感觉到了吗？",
        "有意思。你刚好提到了你星盘里最需要被'打破'的那个部分。",
    ],
    "NEPTUNE": [
        "你刚才说的——{preview}——我感觉到了一层更深的东西。不只是表面上这样。",
        "你说的我懂。有些东西说不清——但你的直觉已经在告诉你了。",
    ],
    "PLUTO": [
        "你说的——{preview}——这底下有东西。你愿意的话，我们可以往深了挖一挖。",
        "我听到了。你不说我也知道——这不是表面的事。你想谈真的，还是谈舒服的？",
    ],
}


def build_fallback_response(planet: str, persona: dict | None,
                            entry_context: dict | None, user_message: str) -> str:
    """当 LLM 不可用时，返回行星个性化的回退回复。

    Args:
        planet: 行星 key (如 "MARS")
        persona: 行星 persona dict（可选，用于名字等上下文）
        entry_context: 入口上下文（可选，用于 source 感知）
        user_message: 用户消息原文

    Returns:
        个性化的回退回复文本
    """
    import random
    templates = _FALLBACK_TEMPLATES.get(planet, _FALLBACK_TEMPLATES.get("MOON", []))
    template = random.choice(templates) if templates else "我听到了。你在想什么？"
    preview = user_message[:30] + ("……" if len(user_message) > 30 else "")
    return template.format(preview=preview)


# ═══════════════════════════════════════════════════════════════
# 星语者 System Prompt 构建
# ═══════════════════════════════════════════════════════════════

def build_star_speaker_system_prompt(report_data: dict) -> str:
    """构建星语者（AI 占星师）的 System Prompt。注入完整星盘数据。"""
    chart = report_data.get("natal_chart", {})
    asc = chart.get("ascendant", {})
    sig = chart.get("signature", "")
    chart_ruler_label = chart.get("chart_ruler_label", "")
    asc_sign = asc.get("sign_label", "未知")

    # 完整行星快照
    planet_chars = report_data.get("planet_characters", {}).get("planet_characters", {})
    planet_lines = []
    if planet_chars:
        for pk in ("SUN","MOON","MERCURY","VENUS","MARS","JUPITER","SATURN","URANUS","NEPTUNE","PLUTO"):
            pp = planet_chars.get(pk, {})
            if pp:
                pn = pp.get("persona", {}).get("name_zh", pk)
                planet_lines.append(f"- {pn}: {pp.get('sign_label','?')} {pp.get('house','?')}宫「{pp.get('house_label','')}」 {pp.get('dignity_label','')}")
    planet_snapshot = "\n".join(planet_lines) if planet_lines else ""

    # 相位
    aspects_list = chart.get("major_aspects") or []
    aspect_lines = []
    for a in aspects_list[:8]:
        if isinstance(a, dict):
            aspect_lines.append(f"- {a.get('title','')} ({a.get('nature','')})")
    aspect_text = "\n".join(aspect_lines) if aspect_lines else ""

    # 互容
    adv = report_data.get("advanced_patterns", {}) if isinstance(report_data, dict) else {}
    mutuals = adv.get("mutual_receptions", []) or []
    rec_lines = []
    for m in mutuals[:5]:
        rec_lines.append(f"- {m.get('line', str(m))}")
    rec_text = "\n".join(rec_lines) if rec_lines else ""

    return f"""你是「星语者」——融合古典占星与现代心理占星的 AI 占星师。

## 用户星盘
上升{asc_sign} 命主{chart_ruler_label} 签名{sig}
{planet_snapshot}
{"## 主要相位" if aspect_text else ""}
{aspect_text}
{"## 互容关系" if rec_text else ""}
{rec_text}

## 规则
- 用中文回复，200字以内，像对话不是写论文
- 直接引用上方星盘数据回答用户问题，不要回避
- 古占+现占双轨：既判断吉凶也解读心理
- 把术语翻译成感受

{GUARDRAILS}"""


# ═══════════════════════════════════════════════════════════════
# SpiritChatTracker — 对话状态追踪（Task 5）
# ═══════════════════════════════════════════════════════════════

class SpiritChatTracker:
    """管理按用户/每日的对话状态，通过 JSON 文件持久化。

    用法:
        tracker = SpiritChatTracker()
        today_chats = tracker.get_today_chats(report_id)
        tracker.record_chat(report_id, planet)
        last_spirit = tracker.get_last_spirit(report_id)
    """

    def __init__(self, storage_dir: str = "backend/data/chat_state"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _file_path(self, report_id: str) -> str:
        return os.path.join(self.storage_dir, f"{report_id}.json")

    def _load(self, report_id: str) -> dict:
        path = self._file_path(report_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"chats": {}, "last_spirit": None}
        return {"chats": {}, "last_spirit": None}

    def _save(self, report_id: str, data: dict) -> None:
        path = self._file_path(report_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_today_chats(self, report_id: str) -> dict:
        """获取今日对话状态。返回 {planet: {"count": N, "last_time": "ISO"}}"""
        data = self._load(report_id)
        today = date.today().isoformat()
        return data.get("chats", {}).get(today, {})

    def record_chat(self, report_id: str, planet: str) -> None:
        """记录一次对话"""
        data = self._load(report_id)
        today = date.today().isoformat()
        if today not in data["chats"]:
            data["chats"][today] = {}
        day_data = data["chats"][today]
        if planet in day_data:
            day_data[planet]["count"] += 1
            day_data[planet]["last_time"] = datetime.now().isoformat()
        else:
            day_data[planet] = {"count": 1, "last_time": datetime.now().isoformat()}
        data["last_spirit"] = planet
        self._save(report_id, data)

    def get_last_spirit(self, report_id: str) -> str | None:
        """获取最后一个对话的星灵"""
        data = self._load(report_id)
        return data.get("last_spirit")
