"""테스트/개발용 Mock 브로커."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import count

from .base import Broker


@dataclass
class Position:
    """포지션 데이터."""

    symbol: str
    qty: int
    avg_price: int


class MockBroker(Broker):
    """외부 주문이 전혀 발생하지 않는 가짜 브로커 구현체."""

    def __init__(self, initial_cash: int = 10_000_000) -> None:
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}
        self.orders: dict[str, dict] = {}
        self.prices: dict[str, int] = {}
        self.ohlcv_map: dict[str, list[dict]] = {}
        self._order_counter = count(1)
        self._authenticated = False

    def authenticate(self) -> None:
        self._authenticated = True

    def set_price(self, symbol: str, price: int) -> None:
        """테스트용 현재가 주입."""
        self.prices[symbol] = price

    def set_ohlcv(self, symbol: str, candles: list[dict]) -> None:
        """테스트용 캔들 주입."""
        self.ohlcv_map[symbol] = candles

    def get_price(self, symbol: str) -> dict:
        price = self.prices.get(symbol)
        if price is None:
            raise ValueError(f"Mock 현재가가 없습니다: {symbol}")
        return {"symbol": symbol, "price": price, "timestamp": datetime.utcnow().isoformat()}

    def get_ohlcv(self, symbol: str, limit: int = 100) -> list[dict]:
        candles = self.ohlcv_map.get(symbol, [])
        return candles[-limit:]

    def get_balance(self) -> dict:
        return {"cash": self.cash, "currency": "KRW"}

    def get_positions(self) -> list[dict]:
        return [
            {"symbol": p.symbol, "qty": p.qty, "avg_price": p.avg_price}
            for p in self.positions.values()
            if p.qty > 0
        ]

    def place_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: int | None = None,
        order_type: str = "market",
    ) -> dict:
        if qty < 1:
            raise ValueError("주문 수량은 1 이상이어야 합니다.")
        if side not in {"buy", "sell"}:
            raise ValueError("side는 buy/sell만 가능합니다.")
        if order_type not in {"market", "limit"}:
            raise ValueError("order_type은 market/limit만 지원합니다.")

        current = self.get_price(symbol)["price"]
        fill_price = current if order_type == "market" else (price or current)
        order_amount = fill_price * qty

        if side == "buy":
            if self.cash < order_amount:
                raise ValueError("잔고 부족으로 매수할 수 없습니다.")
            self.cash -= order_amount
            old = self.positions.get(symbol)
            if old is None:
                self.positions[symbol] = Position(symbol=symbol, qty=qty, avg_price=fill_price)
            else:
                total_cost = old.avg_price * old.qty + fill_price * qty
                total_qty = old.qty + qty
                old.qty = total_qty
                old.avg_price = total_cost // total_qty
        else:
            pos = self.positions.get(symbol)
            if pos is None or pos.qty < qty:
                raise ValueError("보유 수량 부족으로 매도할 수 없습니다.")
            pos.qty -= qty
            self.cash += order_amount
            if pos.qty == 0:
                del self.positions[symbol]

        order_id = f"MOCK-{next(self._order_counter):06d}"
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": fill_price,
            "order_type": order_type,
            "status": "filled",
            "filled_qty": qty,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.orders[order_id] = order
        return order

    def get_order_status(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            raise ValueError(f"주문을 찾을 수 없습니다: {order_id}")
        return order

    def cancel_order(self, order_id: str) -> dict:
        order = self.get_order_status(order_id)
        if order["status"] == "filled":
            return {"order_id": order_id, "status": "not_cancellable"}
        order["status"] = "cancelled"
        return {"order_id": order_id, "status": "cancelled"}
