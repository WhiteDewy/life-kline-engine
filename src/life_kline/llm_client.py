"""
llm_client.py — LLM 抽象层

支持多 provider（Claude / DeepSeek / Qwen），通过环境变量切换。
引擎不绑定具体 LLM——所有 provider 通过同一个 chat() 接口调用。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
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

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
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
        """发送对话请求，返回助手的文本回复。

        Args:
            system_prompt: 系统提示词（星灵 persona + 星盘 context）
            user_message: 用户当前消息
            history: 最近对话历史 [{"role": "user"|"assistant", "content": "..."}]
        """
        if not self.is_configured:
            return ""

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

        return self._call_api(messages)

    def _call_api(self, messages: list[dict[str, str]]) -> str:
        """实际的 HTTP 调用（OpenAI 兼容格式）。"""
        body = json.dumps({
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }).encode("utf-8")

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        req = Request(url, data=body)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.config.api_key}")

        try:
            with urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[LLMClient] API 调用失败: {e}")
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


def build_spirit_system_prompt(report_data: dict, planet: str, topic: str = "personal") -> str:
    """为指定行星构建 System Prompt。

    所有信息来自引擎——不做宿命预测，不发明新知识。
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

    return f"""你是{persona.get('name_zh', '一颗行星')}（{persona.get('archetype_zh', '')}），用户星盘中的行星人格。

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

## 规则
- 用中文回复，语气严格按你的说话风格来
- 不要切换角色——你始终是{persona.get('name_zh', '')}
- 回复控制在 200 字以内
- 不做宿命断言和预测
- 不给具体投资/医疗建议
- 像朋友聊天，不要像写学术报告
- 如果用户说的事情和星盘无关，你也可以像一个关心ta的朋友一样回应"""
