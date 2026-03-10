"""외부 API 없이 동작하는 Mock 브로커 구현."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import count

from broker.base import Broker
from utils.time_utils import seoul_now


@dataclass
class Position:
    """보유 포지션 정보."""

    symbol: str
    qty: int
    avg_price: int


class MockBroker(Broker):
    """테스트/학습용 Mock 브로커."""

    def __init__(self, initial_cash: int = 10_000_000) -> None:
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}
        self.orders: dict[str, dict] = {}
        self.price_map: dict[str, int] = {}
        self.ohlcv_map: dict[str, list[dict]] = {}
        self._order_seq = count(1)

    def authenticate(self) -> None:
        """Mock 브로커는 인증이 필요 없다."""

    def set_price(self, symbol: str, price: int) -> None:
        """테스트용 현재가 주입."""
        self.price_map[symbol] = int(price)

    def set_ohlcv(self, symbol: str, candles: list[dict]) -> None:
        """테스트용 캔들 데이터 주입."""
        self.ohlcv_map[symbol] = candles

    def get_price(self, symbol: str) -> dict:
        price = self.price_map.get(symbol)
        if price is None:
            raise ValueError(f"가격이 설정되지 않은 종목입니다: {symbol}")
        return {"symbol": symbol, "price": price, "time": seoul_now().isoformat()}

    def get_ohlcv(self, symbol: str, limit: int = 100) -> list[dict]:
        candles = self.ohlcv_map.get(symbol, [])
        return candles[-limit:]

    def get_balance(self) -> dict:
        positions_value = 0
        for pos in self.positions.values():
            current_price = self.price_map.get(pos.symbol, pos.avg_price)
            positions_value += current_price * pos.qty
        return {
            "cash": self.cash,
            "positions_value": positions_value,
            "total_equity": self.cash + positions_value,
            "updated_at": seoul_now().isoformat(),
        }

    def get_positions(self) -> list[dict]:
        rows: list[dict] = []
        for pos in self.positions.values():
            current_price = self.price_map.get(pos.symbol, pos.avg_price)
            rows.append(
                {
                    "symbol": pos.symbol,
                    "qty": pos.qty,
                    "avg_price": pos.avg_price,
                    "current_price": current_price,
                }
            )
        return rows

    def place_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: int | None = None,
        order_type: str = "market",
    ) -> dict:
        if side not in {"buy", "sell"}:
            raise ValueError("side는 buy 또는 sell 이어야 합니다.")
        if qty <= 0:
            raise ValueError("qty는 1 이상이어야 합니다.")
        if order_type not in {"market", "limit"}:
            raise ValueError("order_type은 market 또는 limit 이어야 합니다.")

        market_price = self.get_price(symbol)["price"]
        executed_price = market_price if order_type == "market" else price
        if executed_price is None or executed_price <= 0:
            raise ValueError("지정가 주문은 유효한 price가 필요합니다.")

        order_amount = executed_price * qty
        order_id = f"MOCK-{next(self._order_seq):08d}"
        now = seoul_now().isoformat()

        if side == "buy":
            if self.cash < order_amount:
                raise ValueError("현금 잔고가 부족합니다.")
            self.cash -= order_amount
            prev = self.positions.get(symbol)
            if prev is None:
                self.positions[symbol] = Position(symbol=symbol, qty=qty, avg_price=executed_price)
            else:
                total_qty = prev.qty + qty
                weighted_avg = int((prev.avg_price * prev.qty + executed_price * qty) / total_qty)
                self.positions[symbol] = Position(symbol=symbol, qty=total_qty, avg_price=weighted_avg)
        else:
            prev = self.positions.get(symbol)
            if prev is None or prev.qty < qty:
                raise ValueError("매도 가능한 수량이 부족합니다.")
            self.cash += order_amount
            remain_qty = prev.qty - qty
            if remain_qty == 0:
                del self.positions[symbol]
            else:
                self.positions[symbol] = Position(symbol=symbol, qty=remain_qty, avg_price=prev.avg_price)

        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": executed_price,
            "order_type": order_type,
            "status": "filled",
            "created_at": now,
            "filled_at": now,
        }
        self.orders[order_id] = order
        return order

    def get_order_status(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            raise KeyError(f"존재하지 않는 주문 ID 입니다: {order_id}")
        return order

    def cancel_order(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            raise KeyError(f"존재하지 않는 주문 ID 입니다: {order_id}")
        if order["status"] == "filled":
            return {
                "order_id": order_id,
                "status": "not_cancelable",
                "reason": "이미 체결된 주문입니다.",
                "time": seoul_now().isoformat(),
            }
        order["status"] = "canceled"
        order["canceled_at"] = seoul_now().isoformat()
        return order
