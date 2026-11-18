"""리스크 관리 규칙."""

from __future__ import annotations

from dataclasses import dataclass, field

from utils.time_utils import is_within_minutes_after_market_open


@dataclass
class RiskRules:
    """주문 전 리스크 검사 규칙."""

    max_position_per_symbol: int = 10
    max_daily_loss: float = 100000
    max_order_amount: float = 500000
    allow_duplicate_orders: bool = False
    no_trade_minutes_after_open: int = 5
    stop_loss_pct: float = 0.03
    take_profit_pct: float = 0.05
    recent_signals: set[tuple[str, str, int]] = field(default_factory=set)

    def check_order(
        self,
        signal: dict,
        account: dict,
        positions: list[dict],
        current_price: int,
    ) -> tuple[bool, str]:
        """신호 기준으로 주문 허용 여부를 반환한다."""
        side = signal.get("side")
        qty = int(signal.get("qty", 0))
        symbol = str(signal.get("symbol", ""))

        if side not in {"buy", "sell"}:
            return False, "side 값이 유효하지 않습니다."
        if qty <= 0:
            return False, "주문 수량은 1 이상이어야 합니다."
        if current_price <= 0:
            return False, "현재가가 유효하지 않습니다."

        order_amount = current_price * qty
        if order_amount > self.max_order_amount:
            return False, f"주문 금액 한도 초과: {order_amount} > {self.max_order_amount}"

        if is_within_minutes_after_market_open(self.no_trade_minutes_after_open):
            return False, f"장 시작 후 {self.no_trade_minutes_after_open}분 이내 매매 금지"

        if not self.allow_duplicate_orders:
            key = (symbol, side, qty)
            if key in self.recent_signals:
                return False, "중복 주문 신호가 감지되었습니다."

        symbol_position = next((p for p in positions if p.get("symbol") == symbol), None)
        held_qty = int(symbol_position.get("qty", 0)) if symbol_position else 0

        if side == "buy":
            if held_qty + qty > self.max_position_per_symbol:
                return False, "종목별 최대 보유 수량 한도를 초과합니다."
            if float(account.get("cash", 0)) < order_amount:
                return False, "현금 잔고가 부족합니다."
        else:
            if held_qty < qty:
                return False, "보유 수량보다 많은 매도 주문입니다."

        # 일일 손실 제한: 실제 손익 집계가 필요하므로 확장 포인트만 제공
        # TODO: 거래 체결내역 기반 일일 실현손익 계산 연동
        _ = self.max_daily_loss

        # 손절/익절 구조 확장 포인트
        # TODO: 포지션별 평균단가 대비 손절/익절 자동 청산 로직 추가
        _ = (self.stop_loss_pct, self.take_profit_pct)

        if not self.allow_duplicate_orders:
            self.recent_signals.add((symbol, side, qty))

        return True, "허용"
