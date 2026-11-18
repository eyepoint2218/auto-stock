"""알리익스프레스 인기상품 → 네이버 블로그 반자동 초안.

매일 인기상품 10개를 어필리에이트 API 로 모아 blog/날짜/ 에 복사용 글(post.html)을 만든다.
네이버 블로그는 글쓰기 API 가 없으므로 사람이 확인하고 붙여넣어 올린다.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "blog"
HISTORY = BLOG_DIR / "history.json"
