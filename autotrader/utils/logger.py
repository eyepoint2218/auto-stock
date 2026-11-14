"""로거 유틸."""

from __future__ import annotations

import logging
from pathlib import Path


def get_logger(name: str = "autotrader", level: str = "INFO") -> logging.Logger:
    """콘솔+파일 로거를 생성한다."""
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if logger.handlers:
        return logger

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(logs_dir / "autotrader.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
