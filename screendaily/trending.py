"""한국 OTT 최신작 목록 (TMDB).

최근 N일 안에 공개된 작품 중, 한국에서 넷플릭스·티빙·디즈니+·쿠팡플레이·웨이브·왓챠로
볼 수 있는 인기작을 모아 data/trending.json 과 data/trending.md 로 저장한다.
기획할 때 이 목록에서 최신작을 골라 지난 명작과 섞는다 (CLAUDE.md 규칙 12).
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

from . import ROOT
from .images import TMDB

DATA_DIR = ROOT / "data"
# TMDB 제공사 이름(영문) → 카드에 쓸 이름
PROVIDERS = {
    "Netflix": "넷플릭스",
    "Disney Plus": "디즈니+",
    "TVING": "티빙",
    "Coupang Play": "쿠팡플레이",
    "Wavve": "웨이브",
    "Watcha": "왓챠",
}


def _provider_ids(tmdb: TMDB) -> dict[int, str]:
    ids: dict[int, str] = {}
    for kind in ("tv", "movie"):
        res = tmdb.get(f"watch/providers/{kind}", watch_region="KR", language="ko-KR")
        for p in res.get("results", []):
            name = p.get("provider_name", "")
            for key, label in PROVIDERS.items():
                if name.lower() == key.lower():
                    ids[p["provider_id"]] = label
    return ids


def collect(days: int = 365, per_provider: int = 15) -> list[dict]:
    token = os.environ.get("TMDB_TOKEN", "").strip()
    if not token:
        raise SystemExit("TMDB_TOKEN 이 없습니다")
    tmdb = TMDB(token)
    since = (date.today() - timedelta(days=days)).isoformat()
    today = date.today().isoformat()
    found: dict[str, dict] = {}
    for pid, label in _provider_ids(tmdb).items():
        for kind in ("tv", "movie"):
            date_key = "first_air_date" if kind == "tv" else "primary_release_date"
            res = tmdb.get(f"discover/{kind}", watch_region="KR", with_watch_providers=pid,
                           language="ko-KR", sort_by="popularity.desc",
                           **{f"{date_key}.gte": since, f"{date_key}.lte": today})
            for r in res.get("results", [])[:per_provider]:
                key = f"{kind}/{r['id']}"
                if key in found:
                    if label not in found[key]["ott"]:
                        found[key]["ott"].append(label)
                    continue
                found[key] = {
                    "tmdb": key,
                    "type": "시리즈" if kind == "tv" else "영화",
                    "title": r.get("name") or r.get("title"),
                    "original": r.get("original_name") or r.get("original_title"),
                    "date": r.get("first_air_date") or r.get("release_date") or "",
                    "ott": [label],
                    "popularity": round(r.get("popularity", 0), 1),
                    "overview": (r.get("overview") or "").strip(),
                }
            time.sleep(0.2)
    # 출연진 (상위 작품만)
    items = sorted(found.values(), key=lambda x: -x["popularity"])
    for it in items[:60]:
        try:
            c = tmdb.get(f"{it['tmdb']}/credits", language="ko-KR")
            it["cast"] = [p["name"] for p in c.get("cast", [])[:3]]
        except Exception:  # noqa: BLE001
            it["cast"] = []
        time.sleep(0.1)
    return items


def save(items: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "trending.json").write_text(json.dumps(
        {"updated": date.today().isoformat(), "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# 한국 OTT 최신작 (최근 1년 공개, TMDB 인기순) — {date.today().isoformat()} 기준", "",
             "기획할 때 게시물마다 여기서 최신작 1~2편 + 지난 명작 1~2편을 섞는다. "
             "`tmdb:` 에 아래 번호를 그대로 쓰면 이미지가 정확히 잡힌다.", "",
             "| 제목 | 종류 | 공개일 | OTT | 출연 | tmdb |", "|---|---|---|---|---|---|"]
    for it in items:
        lines.append(f"| {it['title']} | {it['type']} | {it['date']} | {', '.join(it['ott'])} | "
                     f"{', '.join(it.get('cast', []))} | {it['tmdb']} |")
    lines += ["", "## 줄거리 (TMDB 한국어 소개)", ""]
    for it in items:
        if it["overview"]:
            lines.append(f"- **{it['title']}** ({it['tmdb']}): {it['overview']}")
    (DATA_DIR / "trending.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
