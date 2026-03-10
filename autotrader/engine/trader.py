"""트레이딩 엔진."""

from __future__ import annotations

import time
from typing import Any

from broker.base import Broker
from risk.rules import RiskRules
from strategy.base import Strategy


class Trader:
    """브로커/전략/리스크/저장을 조합한 실행 엔진."""

    def __init__(
        self,
        broker: Broker,
        strategy: Strategy,
        risk_rules: RiskRules,
        db: Any,
        logger: Any,
        dry_run: bool,
        symbols: list[str],
    ) -> None:
        self.broker = broker
        self.strategy = strategy
        self.risk_rules = risk_rules
        self.db = db
        self.logger = logger
        self.dry_run = dry_run
        self.symbols = symbols

    def run_once(self) -> None:
        """1회 실행 루틴."""
        account = self.broker.get_balance()
        positions = self.broker.get_positions()

        for symbol in self.symbols:
            try:
                candles = self.broker.get_ohlcv(symbol, limit=200)
                signal = self.strategy.generate_signal(symbol, candles, account, positions)
                if not signal:
                    self.logger.info("신호 없음: %s", symbol)
                    continue

                price_data = self.broker.get_price(symbol)
                current_price = int(price_data.get("price", 0))

                ok, reason = self.risk_rules.check_order(signal, account, positions, current_price)
                if not ok:
                    self.logger.warning("리스크 차단: symbol=%s reason=%s signal=%s", symbol, reason, signal)
                    self.db.insert_log("WARNING", f"리스크 차단: {reason}", str(signal))
                    continue

                self.logger.info("주문 시도 전 기록: %s", signal)
                self.db.insert_log("INFO", "주문 시도", str(signal))

                if self.dry_run:
                    order_response = {
                        "order_id": "DRY-RUN",
                        "status": "blocked",
                        "reason": "dry_run=True",
                        "signal": signal,
                    }
                    self.logger.info("Dry Run 주문 차단: %s", order_response)
                else:
                    order_response = self.broker.place_order(
                        symbol=signal["symbol"],
                        side=signal["side"],
                        qty=int(signal["qty"]),
                        order_type=signal.get("order_type", "market"),
                        price=signal.get("price"),
                    )
                    self.logger.info("주문 응답: %s", order_response)

                self.db.insert_order(
                    symbol=signal["symbol"],
                    side=signal["side"],
                    qty=int(signal["qty"]),
                    price=current_price,
                    status=order_response.get("status", "unknown"),
                    reason=signal.get("reason", ""),
                    raw_response=str(order_response),
                )

            except Exception as exc:  # 종목 단위 보호
                self.logger.exception("종목 처리 실패: %s", symbol)
                self.db.insert_log("ERROR", f"종목 처리 실패: {symbol}", str(exc))

    def run_loop(self, interval_seconds: int = 60) -> None:
        """주기적 무한 실행."""
        self.logger.info("트레이딩 루프 시작. interval=%s", interval_seconds)
        try:
            while True:
                self.run_once()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt 수신. 트레이딩 루프를 종료합니다.")
