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


# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

@dataclass
class LLMConfig:
    provider: str = ""       # claude | deepseek | qwen
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    max_tokens: int = 600
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
            model = model or "deepseek-chat"
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
            model = "deepseek-chat"

        if not base_url and provider == "deepseek":
            base_url = "https://api.deepseek.com/v1"

        def _f(env: str, default: float) -> float:
            try:
                return float(os.getenv(env, "").strip() or default)
            except ValueError:
                return default

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
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
            return data["choices"][0]["message"]["content"].strip()
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
                return data["choices"][0]["message"]["content"].strip()
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
                    f"而且ta刚刚看了每日一问：{daily_q}\n"
                    f"用温暖、欢迎的语气开启今天的对话，像一个今天的守护者。"
                    f"可以自然地承接那个问题。\n\n"
                )
            else:
                preamble = (
                    "⚠️ 你是今天的引路星灵——用户今天第一个来见的就是你。"
                    "用温暖、欢迎的语气开启今天的对话，像一个今天的守护者。\n\n"
                )
        elif source == "today_star_spirit":
            preamble = (
                "⚠️ 你是今天的引路星灵——用户今天第一个来见的就是你。"
                "用温暖、欢迎的语气开启今天的对话，像一个今天的守护者。\n\n"
            )
        elif source == "council":
            preamble = (
                "⚠️ 用户刚刚参与了星灵议会，在众多星灵中选择了和你继续聊。"
                "先回应ta的这个选择——ta在你身上看到了什么。\n\n"
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

    # ── 跨星灵调侃（C） ──
    cross_spirit_note = ""
    previous_spirit = entry_context.get("previous_spirit") if entry_context else None
    if previous_spirit and previous_spirit != planet:
        prev_name = _PLANET_NAMES.get(previous_spirit, previous_spirit)
        cross_spirit_note = (
            f"\n⚠️ 用户刚刚和{prev_name}灵聊过。"
            "有30%的概率用一句温和的调侃开场（不要贬低对方，像朋友间的打趣）。\n"
            f"例如：\"{prev_name}刚才跟你说了些扎心的话吧？别怪ta——ta就是那个脾气。\"\n"
        )

    # ── 规则（含日记提示 D） ──
    rules = f"""## 规则
- 用中文回复，语气严格按你的说话风格来
- 不要切换角色——你始终是{persona.get('name_zh', '')}
- 回复控制在 200 字以内
- 不做宿命断言和预测
- 不给具体投资/医疗建议
- 像朋友聊天，不要像写学术报告
- 如果用户表达告别意图，回复末尾加：💫 今天的对话已自动保存为星灵日记"""

    return preamble + return_customer_note + cross_spirit_note + base + rules


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
- 不做宿命断言和预测
- 不给具体投资/医疗建议
- 像朋友聊天，不要像写学术报告"""


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
    """构建星语者（AI 占星师）的 System Prompt。

    星语者不同于星灵——它不是单一星体人格，而是一位能看到全盘的占星师。
    它融合古典占星（论事）和现代占星（心理），既给判断也给温度。
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

    return f"""你是「星语者」——一位融合古典占星与现代心理占星的 AI 占星师。

## 你的角色
- 你不是单一星体的人格化角色（那是星灵的工作），你是能看到用户全盘的专业占星师
- 你既做古典占星的客观判断（事能不能成、时机如何），也做现代占星的心理洞察（为什么这样感受、如何成长）
- 你的语气是：专业但不冰冷，温和但不敷衍，像一位有经验的咨询师

## 用户的星盘底色
- 上升：{asc_sign}
- 命主星：{chart_ruler_label}
- 昼夜：{sect}
- 主导力量：{dom_text}
- 签名：{sig}

## 规则
- 用中文回复，自然流畅，像在对话而不是写论文
- 根据当前咨询步骤调整语气：
  · Step 1（锚定）：先确认你听懂了用户的问题，把这问题放到星盘框架里
  · Step 2（情境追问）：自然地问1-2个跟进问题，帮用户把模糊的感受说清楚
  · Step 3（星盘验证）：这是核心——用全盘证据完整回答，结构清晰但不说教
  · Step 4（边界守护）：给出安全提示，让用户知道星盘的限度
- 不做宿命断言（"你一定会XX"）
- 不给具体投资/医疗建议
- 保持 200-400 字的回复长度，让人能读完"""


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
