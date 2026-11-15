"""실행 진입점."""

from __future__ import annotations

import argparse
import sys

from autotrader.app import create_app
from autotrader.config import load_settings
from autotrader.utils.logger import init_logger


def main() -> int:
    parser = argparse.ArgumentParser(description="안전한 자동매매 개발용 스켈레톤")
    parser.add_argument("--once", action="store_true", help="한 번만 실행")
    args = parser.parse_args()

    logger = init_logger()

    try:
        settings = load_settings()
        trader = create_app(settings)

        if args.once:
            trader.run_once()
        else:
            trader.run_loop(interval_seconds=settings.LOOP_INTERVAL_SECONDS)
        return 0
    except Exception as exc:
        logger.exception("프로그램 실행 중 오류가 발생했습니다: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
