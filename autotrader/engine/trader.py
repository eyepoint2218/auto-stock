"""트레이딩 엔진."""

from __future__ import annotations

import time
from typing import Any

from autotrader.broker.base import Broker
from autotrader.risk.rules import RiskRules
from autotrader.strategy.base import Strategy


class Trader:
    """종목 순회형 자동매매 엔진."""

    def __init__(
        self,
        broker: Broker,
        strategy: Strategy,
        risk_rules: RiskRules,
        db: Any,
        logger: Any,
        symbols: list[str],
        dry_run: bool = True,
    ) -> None:
        self.broker = broker
        self.strategy = strategy
        self.risk_rules = risk_rules
        self.db = db
        self.logger = logger
        self.symbols = symbols
        self.dry_run = dry_run

    def run_once(self) -> None:
        """한 번의 사이클을 실행한다."""
        account = self.broker.get_balance()
        positions = self.broker.get_positions()

        for symbol in self.symbols:
            try:
                candles = self.broker.get_ohlcv(symbol, limit=200)
                signal = self.strategy.generate_signal(symbol, candles, account, positions)
                if signal is None:
                    self.logger.info("[%s] 신호 없음", symbol)
                    continue

                price_info = self.broker.get_price(symbol)
                current_price = int(price_info["price"])

                allowed, reason = self.risk_rules.check_order(
                    signal=signal,
                    account=account,
                    positions=positions,
                    current_price=current_price,
                )
                if not allowed:
                    self.logger.warning("[%s] 리스크 차단: %s", symbol, reason)
                    self.db.insert_log("WARNING", f"{symbol} risk blocked: {reason}")
                    continue

                if self.dry_run:
                    order_result = {
                        "order_id": "DRY-RUN",
                        "symbol": symbol,
                        "side": signal["side"],
                        "qty": signal["qty"],
                        "price": current_price,
                        "status": "simulated",
                    }
                    self.logger.info("[%s] DRY_RUN 주문 시뮬레이션: %s", symbol, order_result)
                else:
                    order_result = self.broker.place_order(
                        symbol=symbol,
                        side=signal["side"],
                        qty=int(signal["qty"]),
                        order_type="market",
                    )
                    self.logger.info("[%s] 주문 실행: %s", symbol, order_result)

                self.db.insert_order(order_result)
                if order_result.get("status") in {"filled", "simulated"}:
                    self.db.insert_execution(order_result)
            except Exception as exc:  # 종목 단위 보호
                self.logger.exception("[%s] 처리 중 예외 발생: %s", symbol, exc)
                self.db.insert_log("ERROR", f"{symbol}: {exc}")

    def run_loop(self, interval_seconds: int = 60) -> None:
        """지속 루프 실행."""
        self.logger.info("트레이딩 루프 시작 (interval=%s초)", interval_seconds)
        try:
            while True:
                self.run_once()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            self.logger.info("사용자 인터럽트로 트레이딩 루프를 종료합니다.")
