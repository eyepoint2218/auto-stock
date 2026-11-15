"""리스크 관리 규칙."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from autotrader.utils.time_utils import is_within_no_trade_window


@dataclass
class RiskRules:
    """주문 전 검증 규칙 모음."""

    max_position_per_symbol: int
    max_daily_loss: int
    max_order_amount: int
    allow_duplicate_orders: bool = False
    no_trade_minutes_after_open: int = 0
    stop_loss_pct: float = 0.0
    take_profit_pct: float = 0.0
    submitted_signatures: set[tuple[str, str, int]] = field(default_factory=set)

    def check_order(
        self,
        signal: dict,
        account: dict,
        positions: list[dict],
        current_price: int,
        now: datetime | None = None,
    ) -> tuple[bool, str]:
        """신호에 대해 주문 가능 여부를 판단한다."""
        side = signal.get("side")
        qty = int(signal.get("qty", 0))
        symbol = signal.get("symbol")

        if qty < 1:
            return False, "수량은 1 이상이어야 합니다."
        if side not in {"buy", "sell"}:
            return False, "side는 buy/sell만 허용됩니다."
        if is_within_no_trade_window(self.no_trade_minutes_after_open, now=now):
            return False, "장 시작 직후 매매 금지 시간입니다."

        order_amount = qty * int(current_price)
        if order_amount > self.max_order_amount:
            return False, "주문금액이 max_order_amount를 초과했습니다."

        position_qty = 0
        for p in positions:
            if p.get("symbol") == symbol:
                position_qty = int(p.get("qty", 0))
                break

        if side == "buy":
            if position_qty + qty > self.max_position_per_symbol:
                return False, "종목당 최대 보유 수량 한도를 초과합니다."
            if int(account.get("cash", 0)) < order_amount:
                return False, "현금 잔고가 부족합니다."
        else:
            if position_qty < qty:
                return False, "보유 수량보다 많은 매도 주문은 허용되지 않습니다."

        signature = (symbol, side, qty)
        if not self.allow_duplicate_orders and signature in self.submitted_signatures:
            return False, "중복 주문이 감지되어 차단했습니다."

        self.submitted_signatures.add(signature)
        return True, "OK"
