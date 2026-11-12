"""스크린데일리 카드뉴스/릴스 생성 및 인스타그램 예약 업로드."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "queue"
PUBLISHED_DIR = ROOT / "published"
FONT_DIR = ROOT / "assets" / "fonts"
