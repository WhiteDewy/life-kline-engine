"""
pricing.py — 星灵星币定价体系

参考万象有灵双轨制（会员订阅 + 金币内购），设计三层收费架构：
  引擎占星师 — 免费额度 + VIP 无限
  AI 占星师   — 消耗星币（token 成本）
  真人占星师  — 独立定价（后续接入）

定价规则：
  1 星币 = 1 元人民币
  测试用户 18513821306 直通所有付费检查
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

# ═══════════════════════════════════════════════════════════════
# 测试用户白名单
# ═══════════════════════════════════════════════════════════════

TEST_USER_IDS: set[str] = {"18513821306"}


def is_test_user(user_id: str, phone: str = "") -> bool:
    if user_id in TEST_USER_IDS:
        return True
    if phone and phone in TEST_USER_IDS:
        return True
    return False


# ═══════════════════════════════════════════════════════════════
# 免费额度
# ═══════════════════════════════════════════════════════════════

@dataclass
class FreeQuota:
    """非 VIP 用户的免费额度（每日重置）"""
    engine_daily_rounds: int = 10        # 引擎占星师每日总轮次
    engine_per_spirit: int = 3           # 每位星灵每日最多轮次
    ai_daily_rounds: int = 3             # AI 占星师免费轮次（每日3轮体验）
    council_weekly: int = 3              # 星灵议会每周次数
    diary_daily_writes: int = 1          # 日记每日写入次数
    daily_star_spirit: int = 1           # 每日引路星灵


# ═══════════════════════════════════════════════════════════════
# VIP 会员
# ═══════════════════════════════════════════════════════════════

@dataclass
class VIPPlan:
    """VIP 订阅方案"""
    name: str
    price_cny: int
    duration_days: int
    auto_renew: bool
    ai_monthly_rounds: int = 30   # 每月赠送 AI 对话轮次
    description: str = ""


VIP_PLANS: dict[str, VIPPlan] = {
    "monthly_auto": VIPPlan(
        name="连续包月",
        price_cny=28,
        duration_days=30,
        auto_renew=True,
        ai_monthly_rounds=30,
        description="引擎无限对话 + 每月30轮AI对话，自动续费可随时取消",
    ),
    "monthly": VIPPlan(
        name="月度会员",
        price_cny=35,
        duration_days=30,
        auto_renew=False,
        ai_monthly_rounds=30,
        description="引擎无限对话 + 30轮AI对话",
    ),
    "quarterly": VIPPlan(
        name="季度会员",
        price_cny=88,
        duration_days=90,
        auto_renew=False,
        ai_monthly_rounds=30,
        description="引擎无限对话 + 每月30轮AI对话，享8.4折",
    ),
    "annual": VIPPlan(
        name="年度会员",
        price_cny=238,
        duration_days=365,
        auto_renew=False,
        ai_monthly_rounds=30,
        description="引擎无限对话 + 每月30轮AI对话，享5.7折",
    ),
}


# ═══════════════════════════════════════════════════════════════
# 星币包
# ═══════════════════════════════════════════════════════════════

@dataclass
class CoinPackage:
    """星币充值包"""
    id: str
    name: str
    coins: int
    price_cny: int
    bonus: int = 0               # 赠送星币
    popular: bool = False         # 推荐标记


COIN_PACKAGES: list[CoinPackage] = [
    CoinPackage(id="coin_30",  name="30 星币",  coins=30,  price_cny=30),
    CoinPackage(id="coin_100", name="100 星币", coins=100, price_cny=98,  bonus=2, popular=True),
    CoinPackage(id="coin_300", name="300 星币", coins=300, price_cny=288, bonus=12),
    CoinPackage(id="coin_600", name="600 星币", coins=600, price_cny=568, bonus=32),
    CoinPackage(id="coin_1200",name="1200 星币",coins=1200,price_cny=1098,bonus=102),
]


# ═══════════════════════════════════════════════════════════════
# 对话消耗规则
# ═══════════════════════════════════════════════════════════════

@dataclass
class ConsumptionRule:
    """各类型对话的消耗"""
    engine_per_round: int = 0        # 引擎对话每轮星币
    ai_per_round: int = 3            # AI 对话每轮星币（= 3 元）
    ai_deep_dive: int = 5            # AI 深度分析（议会综合等）
    human_consultation: int = 0      # 真人咨询（独立定价）


CONSUMPTION = ConsumptionRule()


# ═══════════════════════════════════════════════════════════════
# 权限检查结果
# ═══════════════════════════════════════════════════════════════

@dataclass
class AccessResult:
    """权限检查结果"""
    allowed: bool
    reason: str = ""
    remaining_free: int = 0           # 剩余免费次数
    cost_coins: int = 0               # 本次消耗星币
    user_coins: int = 0               # 用户当前星币余额
    is_vip: bool = False
    is_test_user: bool = False
    action_required: str = ""         # "purchase_coins" | "upgrade_vip" | ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "remaining_free": self.remaining_free,
            "cost_coins": self.cost_coins,
            "user_coins": self.user_coins,
            "is_vip": self.is_vip,
            "is_test_user": self.is_test_user,
            "action_required": self.action_required,
        }


# ═══════════════════════════════════════════════════════════════
# 权限检查器
# ═══════════════════════════════════════════════════════════════

class AccessChecker:
    """用户权限检查器。

    检查顺序：测试用户 → VIP → 免费额度 → 星币余额。
    """

    def __init__(self, user_state: dict | None = None):
        """
        Args:
            user_state: 用户状态 dict，包含:
                - user_id: str
                - is_vip: bool
                - vip_expiry: str (ISO date)
                - coins: int
                - engine_usage_today: dict {planet: count}
                - ai_usage_this_month: int
                - council_usage_this_week: int
        """
        self.state = user_state or {}
        self._quota = FreeQuota()

    # ── 便捷工厂 ──

    @classmethod
    def for_user(cls, user_id: str, state: dict | None = None) -> AccessChecker:
        s = dict(state or {})
        s.setdefault("user_id", user_id)
        return cls(s)

    # ── 主检查入口 ──

    def check_engine_chat(self, planet: str) -> AccessResult:
        """检查引擎占星师对话权限"""
        user_id = self.state.get("user_id", "")
        phone = self.state.get("phone", "")

        # 测试用户直通
        if is_test_user(user_id, phone):
            return AccessResult(
                allowed=True, reason="测试用户", is_test_user=True,
                remaining_free=999,
            )

        # VIP 无限
        if self._is_vip_active():
            return AccessResult(
                allowed=True, reason="VIP 无限对话", is_vip=True,
                remaining_free=999,
            )

        # 检查免费额度
        usage = self.state.get("engine_usage_today", {})
        total_used = sum(usage.values())
        planet_used = usage.get(planet, 0)

        if total_used >= self._quota.engine_daily_rounds:
            return AccessResult(
                allowed=False,
                reason=f"今日免费对话次数已用完（{self._quota.engine_daily_rounds}轮/天）",
                remaining_free=0,
                cost_coins=0,
                user_coins=self.state.get("coins", 0),
                action_required="upgrade_vip",
            )

        if planet_used >= self._quota.engine_per_spirit:
            return AccessResult(
                allowed=False,
                reason=f"今日与该星灵的免费对话已达上限（{self._quota.engine_per_spirit}轮）",
                remaining_free=self._quota.engine_daily_rounds - total_used,
                cost_coins=0,
                user_coins=self.state.get("coins", 0),
                action_required="upgrade_vip",
            )

        remaining = self._quota.engine_daily_rounds - total_used
        return AccessResult(
            allowed=True,
            reason=f"免费额度（剩余 {remaining} 轮）",
            remaining_free=remaining,
            is_vip=False,
        )

    def check_ai_chat(self) -> AccessResult:
        """检查 AI 占星师对话权限"""
        user_id = self.state.get("user_id", "")
        phone = self.state.get("phone", "")

        if is_test_user(user_id, phone):
            return AccessResult(
                allowed=True, reason="测试用户", is_test_user=True,
                remaining_free=999,
            )

        if self._is_vip_active():
            monthly_used = self.state.get("ai_usage_this_month", 0)
            monthly_quota = 30  # VIP 每月赠送
            if monthly_used < monthly_quota:
                return AccessResult(
                    allowed=True,
                    reason=f"VIP 每月赠送（剩余 {monthly_quota - monthly_used} 轮）",
                    remaining_free=monthly_quota - monthly_used,
                    is_vip=True,
                )
            # VIP 赠送用完，需消耗星币
            coins = self.state.get("coins", 0)
            cost = CONSUMPTION.ai_per_round
            if coins >= cost:
                return AccessResult(
                    allowed=True,
                    reason=f"消耗 {cost} 星币（余额 {coins}）",
                    cost_coins=cost,
                    user_coins=coins,
                    is_vip=True,
                )
            return AccessResult(
                allowed=False,
                reason=f"星币不足（需要 {cost} 星币，余额 {coins}）",
                cost_coins=cost,
                user_coins=coins,
                is_vip=True,
                action_required="purchase_coins",
            )

        # 非 VIP：先检查免费额度，再消耗星币
        ai_used = self.state.get("ai_usage_today", 0)
        if ai_used < self._quota.ai_daily_rounds:
            remaining = self._quota.ai_daily_rounds - ai_used
            return AccessResult(
                allowed=True,
                reason=f"免费AI体验（剩余 {remaining} 轮）",
                remaining_free=remaining,
            )

        coins = self.state.get("coins", 0)
        cost = CONSUMPTION.ai_per_round
        if coins >= cost:
            return AccessResult(
                allowed=True,
                reason=f"消耗 {cost} 星币（余额 {coins}）",
                cost_coins=cost,
                user_coins=coins,
            )
        return AccessResult(
            allowed=False,
            reason=f"今日免费AI次数已用完，星币不足（需要 {cost} 星币，余额 {coins}）",
            cost_coins=cost,
            user_coins=coins,
            action_required="purchase_coins",
        )

    def check_council(self) -> AccessResult:
        """检查星灵议会权限"""
        user_id = self.state.get("user_id", "")
        phone = self.state.get("phone", "")

        if is_test_user(user_id, phone):
            return AccessResult(allowed=True, reason="测试用户", is_test_user=True)

        if self._is_vip_active():
            return AccessResult(allowed=True, reason="VIP 无限", is_vip=True)

        used = self.state.get("council_usage_this_week", 0)
        if used >= self._quota.council_weekly:
            return AccessResult(
                allowed=False,
                reason=f"本周星灵议会次数已用完（{self._quota.council_weekly}次/周）",
                action_required="upgrade_vip",
            )
        return AccessResult(
            allowed=True,
            reason=f"免费额度（剩余 {self._quota.council_weekly - used} 次）",
            remaining_free=self._quota.council_weekly - used,
        )

    # ── 内部方法 ──

    def _is_vip_active(self) -> bool:
        if not self.state.get("is_vip", False):
            return False
        expiry = self.state.get("vip_expiry", "")
        if not expiry:
            return False
        try:
            expiry_date = date.fromisoformat(expiry)
            return expiry_date >= date.today()
        except (ValueError, TypeError):
            return False


# ═══════════════════════════════════════════════════════════════
# 定价信息汇总（供前端展示）
# ═══════════════════════════════════════════════════════════════

def get_pricing_info() -> dict[str, Any]:
    """返回完整的定价信息，供前端展示"""
    return {
        "currency": "星币",
        "rate": "1 星币 = 1 元",
        "free_quota": {
            "engine_daily_rounds": FreeQuota().engine_daily_rounds,
            "engine_per_spirit": FreeQuota().engine_per_spirit,
            "ai_daily_rounds": FreeQuota().ai_daily_rounds,
            "council_weekly": FreeQuota().council_weekly,
        },
        "vip_plans": {
            k: {
                "name": v.name,
                "price_cny": v.price_cny,
                "duration_days": v.duration_days,
                "auto_renew": v.auto_renew,
                "ai_monthly_rounds": v.ai_monthly_rounds,
                "description": v.description,
            }
            for k, v in VIP_PLANS.items()
        },
        "coin_packages": [
            {
                "id": p.id,
                "name": p.name,
                "coins": p.coins,
                "price_cny": p.price_cny,
                "bonus": p.bonus,
                "total_coins": p.coins + p.bonus,
                "popular": p.popular,
            }
            for p in COIN_PACKAGES
        ],
        "consumption": {
            "engine_per_round": CONSUMPTION.engine_per_round,
            "ai_per_round": CONSUMPTION.ai_per_round,
            "ai_deep_dive": CONSUMPTION.ai_deep_dive,
        },
    }
