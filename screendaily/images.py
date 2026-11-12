"""작품 이미지 자동 가져오기 (영문 위키백과 문서의 대표 이미지 = 보통 공식 포스터).

post.yml 의 items 에 `wiki: "Squid Game"` 처럼 영문 위키백과 문서 제목을 적으면,
image 가 비어 있을 때 대표 이미지를 내려받아 `img/` 폴더에 저장하고 image 로 연결한다.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
from pathlib import Path

import requests

API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "screendaily-card-generator/1.0 (personal Instagram card generator)"}


def _get(url: str, **kw) -> requests.Response:
    for attempt in range(5):
        r = requests.get(url, headers=UA, timeout=60, **kw)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(int(r.headers.get("retry-after", "0") or 0) + 5 * (attempt + 1))
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"요청이 계속 거절됩니다 (429/5xx): {url}")


def lookup(titles: list[str]) -> dict[str, dict]:
    """여러 문서의 대표 이미지 정보를 한 번에 조회."""
    if not titles:
        return {}
    r = _get(API, params={
        "action": "query", "format": "json", "redirects": 1,
        "prop": "pageimages", "piprop": "original|name", "pilicense": "any", "titles": "|".join(titles),
    })
    q = r.json().get("query", {})
    redir = {x["from"]: x["to"] for x in q.get("redirects", []) + q.get("normalized", [])}
    pages = {p["title"]: p for p in q.get("pages", {}).values()}
    out = {}
    for t in titles:
        key = t
        for _ in range(3):
            key = redir.get(key, key)
        p = pages.get(key, {})
        if p.get("original"):
            out[t] = {
                "page": p["title"],
                "page_url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_")),
                "file": p.get("pageimage", ""),
                "src": p["original"]["source"],
                "width": p["original"]["width"],
                "height": p["original"]["height"],
            }
    return out


def slug(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", s).strip("_").lower()[:60] or "img"


def fetch_for_post(slot_dir: Path) -> list[str]:
    """post.yml 의 wiki 항목 이미지를 내려받고 post.yml 에 image 를 채운다. 내려받은 파일 목록 반환."""
    import yaml

    path = slot_dir / "post.yml"
    text = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text) or {}
    items = raw.get("items") or []
    need = [it for it in items if isinstance(it, dict) and it.get("wiki") and not it.get("image")]
    if not need:
        return []

    info = lookup([it["wiki"] for it in need])
    img_dir = slot_dir / "img"
    img_dir.mkdir(exist_ok=True)
    sources = json.loads((img_dir / "sources.json").read_text()) if (img_dir / "sources.json").exists() else {}
    saved = []
    for it in need:
        meta = info.get(it["wiki"])
        if not meta:
            print(f"  ⚠ 위키 이미지 없음: {it['wiki']} (문서 제목 확인)")
            continue
        ext = Path(urllib.parse.urlparse(meta["src"]).path).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            print(f"  ⚠ 지원하지 않는 형식({ext}): {it['wiki']}")
            continue
        rel = f"img/{slug(it['wiki'])}{ext}"
        (slot_dir / rel).write_bytes(_get(meta["src"]).content)
        sources[rel] = meta
        saved.append(rel)
        # post.yml 에서 해당 wiki 줄 바로 아래에 image 줄 추가 (주석/서식 보존)
        pat = re.compile(r"^(\s*)wiki:\s*[\"']?" + re.escape(it["wiki"]) + r"[\"']?\s*$", re.M)
        text = pat.sub(lambda m: f"{m.group(0)}\n{m.group(1)}image: {rel}", text, count=1)
        print(f"  ✓ {it['wiki']} → {rel} ({meta['width']}x{meta['height']})")
        time.sleep(1)

    # 빈 image: "" 줄이 남아 있으면 정리
    text = re.sub(r'^\s*image:\s*""\s*\n', "", text, flags=re.M)
    (img_dir / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
    path.write_text(text, encoding="utf-8")
    return saved
