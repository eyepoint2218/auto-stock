"""인기상품 고르기: 평점·판매량 거르기, 최근 14일 중복 빼기, 카테고리 고르게."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, timedelta

from . import HISTORY
from .api import hot_products

MIN_RATE = 90.0      # 긍정 평가율(%) 이상
MIN_VOLUME = 100     # 최근 판매량 이상
REPEAT_DAYS = 14     # 이 기간 안에 소개한 상품은 다시 안 씀
PER_CATEGORY = 2     # 한 카테고리 최대 개수


def _num(v) -> float:
    m = re.search(r"[\d.]+", str(v or "").replace(",", ""))
    return float(m.group()) if m else 0.0


def load_history() -> dict:
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_history(hist: dict, picked: list[dict], today: date) -> None:
    cutoff = (today - timedelta(days=60)).isoformat()
    hist = {k: v for k, v in hist.items() if v >= cutoff}
    for p in picked:
        hist[str(p["product_id"])] = today.isoformat()
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def pick(products: list[dict], count: int, today: date, hist: dict) -> list[dict]:
    recent = (today - timedelta(days=REPEAT_DAYS)).isoformat()
    seen, cats, out = set(), Counter(), []
    ok = [p for p in products
          if p.get("promotion_link")
          and _num(p.get("evaluate_rate")) >= MIN_RATE
          and _num(p.get("lastest_volume")) >= MIN_VOLUME
          and hist.get(str(p.get("product_id")), "") < recent]
    ok.sort(key=lambda p: _num(p.get("lastest_volume")), reverse=True)
    for p in ok:
        pid, cat = str(p["product_id"]), p.get("first_level_category_name") or "기타"
        if pid in seen or cats[cat] >= PER_CATEGORY:
            continue
        seen.add(pid)
        cats[cat] += 1
        out.append(p)
        if len(out) == count:
            break
    return out


def collect(count: int = 10, today: date | None = None, category_ids: str = "") -> list[dict]:
    today = today or date.today()
    hist = load_history()
    pool: list[dict] = []
    for page in range(1, 5):
        pool += hot_products(page_size=50, page_no=page, category_ids=category_ids)
        picked = pick(pool, count, today, hist)
        if len(picked) >= count:
            break
    return picked
