"""로깅 유틸."""

from __future__ import annotations

import logging
from pathlib import Path


def init_logger(name: str = "autotrader", log_file: str = "logs/autotrader.log") -> logging.Logger:
    """콘솔 + 파일 로거를 초기화한다."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
