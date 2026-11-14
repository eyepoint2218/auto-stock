"""실행 진입점."""

from __future__ import annotations

import argparse

from app import build_trader
from config import Settings
from utils.logger import get_logger


def main() -> None:
    parser = argparse.ArgumentParser(description="한국투자증권 기반 자동매매 학습용 프로젝트")
    parser.add_argument("--loop", action="store_true", help="반복 실행 모드")
    args = parser.parse_args()

    settings = Settings.load()
    logger = get_logger(level=settings.LOG_LEVEL)

    try:
        trader = build_trader(settings)
        if args.loop:
            trader.run_loop(settings.LOOP_INTERVAL_SECONDS)
        else:
            trader.run_once()
    except Exception:
        logger.exception("애플리케이션 실행 중 치명적 예외 발생")
        raise


if __name__ == "__main__":
    main()
