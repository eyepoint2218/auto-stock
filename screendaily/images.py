"""작품 이미지 자동 가져오기.

우선순위: post.yml 에 직접 적은 image > TMDB(공식 포스터·스틸컷) > 영문 위키백과 대표 이미지

- TMDB: 환경변수 TMDB_TOKEN (API 읽기 액세스 토큰 또는 v3 API 키) 이 있으면 사용.
  작품 제목으로 검색하며, 헷갈리면 items[].tmdb 에 "tv/93405" 처럼 지정.
  스틸컷(backdrop)은 작품 카드에, 포스터는 표지 콜라주에 쓴다.
- 위키백과: items[].wiki 에 영문 문서 제목.

받은 결과는 <게시물>/img/ 에 저장하고 img/sources.json 에 작품 제목별로 기록한다.
post.yml 은 건드리지 않는다.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from pathlib import Path

import requests
import yaml

UA = {"User-Agent": "screendaily-card-generator/1.0 (personal Instagram card generator)"}
WIKI_API = "https://en.wikipedia.org/w/api.php"
TMDB_API = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p"


def _get(url: str, headers: dict | None = None, **kw) -> requests.Response:
    for attempt in range(5):
        r = requests.get(url, headers={**UA, **(headers or {})}, timeout=60, **kw)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(int(r.headers.get("retry-after", "0") or 0) + 5 * (attempt + 1))
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"요청이 계속 거절됩니다 (429/5xx): {url.split('?')[0]}")


def slug(s: str) -> str:
    """파일 이름용 (이미지 주소에 쓰이므로 영문·숫자만)."""
    import hashlib
    base = re.sub(r"[^0-9A-Za-z]+", "_", s).strip("_").lower()[:40]
    return (base + "_" if base else "") + hashlib.md5(s.encode()).hexdigest()[:6]


# ------------------------------------------------------------------ TMDB

class TMDB:
    def __init__(self, token: str):
        token = token.strip()
        if re.fullmatch(r"[0-9a-f]{32}", token):  # v3 API 키
            self.headers, self.params = {}, {"api_key": token}
        else:  # v4 읽기 액세스 토큰
            self.headers, self.params = {"Authorization": f"Bearer {token}"}, {}

    def get(self, path: str, **params) -> dict:
        return _get(f"{TMDB_API}/{path.lstrip('/')}", headers=self.headers,
                    params={**self.params, **params}).json()

    def find(self, title: str, override: str = "") -> tuple[str, int, str] | None:
        """(tv|movie, id, 이름) 반환.

        override 형식: "tv/93405"(ID 지정) · "tv" 또는 "movie"(종류만 지정) · "movie:글래스 어니언"(종류+검색어)
        """
        kind_filter, query = "", title
        if override:
            kind, sep, rest = override.partition("/")
            if sep and rest.strip().isdigit():
                d = self.get(f"{kind}/{rest.strip()}", language="ko-KR")
                return kind, int(rest), d.get("name") or d.get("title") or title
            kind, _, q = override.partition(":")
            kind_filter = kind.strip() if kind.strip() in ("tv", "movie") else ""
            query = q.strip() or title
        norm = lambda s: re.sub(r"[\s:·!?,.'\"-]+", "", (s or "")).lower()  # noqa: E731
        queries = [query]
        short = re.split(r"[:：]", query)[0].strip()
        if short and short != query:
            queries.append(short)  # "글래스 어니언: 나이브스 아웃 미스터리" → "글래스 어니언"
        for q in queries:
            if kind_filter:
                res = self.get(f"search/{kind_filter}", query=q, language="ko-KR", include_adult="false")
                cands = [{**r, "media_type": kind_filter} for r in res.get("results", [])]
            else:
                res = self.get("search/multi", query=q, language="ko-KR", include_adult="false")
                cands = [r for r in res.get("results", []) if r.get("media_type") in ("tv", "movie")]
            if not cands:
                continue
            exact = [r for r in cands if norm(r.get("name") or r.get("title")) in (norm(title), norm(q))]
            # 같은 이름이면 인기도(popularity)가 높은 쪽
            best = max(exact, key=lambda r: r.get("popularity", 0)) if exact else cands[0]
            return best["media_type"], best["id"], best.get("name") or best.get("title")
        return None

    def images(self, kind: str, tid: int) -> tuple[str | None, str | None]:
        """(스틸컷 경로, 포스터 경로)"""
        d = self.get(f"{kind}/{tid}/images", include_image_language="ko,null,en")

        def pick(items, langs):
            for lang in langs:
                xs = [x for x in items if x.get("iso_639_1") == lang]
                if xs:
                    return max(xs, key=lambda x: (x.get("vote_average", 0), x.get("width", 0)))["file_path"]
            return items[0]["file_path"] if items else None

        backdrop = pick(d.get("backdrops", []), [None, "ko", "en"])  # 글자 없는 스틸 우선
        poster = pick(d.get("posters", []), ["ko", "en", None])       # 한국어 포스터 우선
        return backdrop, poster


# ------------------------------------------------------------------ 위키백과

def wiki_lookup(titles: list[str]) -> dict[str, dict]:
    if not titles:
        return {}
    r = _get(WIKI_API, params={
        "action": "query", "format": "json", "redirects": 1, "prop": "pageimages",
        "piprop": "original|name", "pilicense": "any", "titles": "|".join(titles),
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
                "page_url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_")),
                "src": p["original"]["source"],
            }
    return out


# ------------------------------------------------------------------ 게시물 단위

def load_sources(slot_dir: Path) -> dict:
    f = slot_dir / "img" / "sources.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return data if "by_title" in data else {"by_title": {}}


def fetch_for_post(slot_dir: Path, refresh: bool = False) -> list[str]:
    raw = yaml.safe_load((slot_dir / "post.yml").read_text(encoding="utf-8")) or {}
    items = [it for it in raw.get("items") or [] if isinstance(it, dict) and it.get("title")]
    img_dir = slot_dir / "img"
    sources = load_sources(slot_dir)
    by_title = sources["by_title"]
    token = os.environ.get("TMDB_TOKEN", "").strip()
    tmdb = TMDB(token) if token else None
    saved: list[str] = []

    def save(url: str, name: str) -> str:
        ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
        rel = f"img/{name}{ext}"
        img_dir.mkdir(exist_ok=True)
        (slot_dir / rel).write_bytes(_get(url).content)
        saved.append(rel)
        return rel

    # 1) TMDB
    for it in items:
        title = str(it["title"])
        if it.get("image") or not tmdb:
            continue
        cur = by_title.get(title, {})
        if cur.get("source") == "tmdb" and not refresh:
            continue
        try:
            found = tmdb.find(title, str(it.get("tmdb") or ""))
            if not found:
                print(f"  ⚠ TMDB 검색 결과 없음: {title} (items 에 tmdb: \"tv/ID\" 지정)")
                continue
            kind, tid, name = found
            backdrop, poster = tmdb.images(kind, tid)
            entry = {"source": "tmdb", "tmdb": f"{kind}/{tid}", "tmdb_name": name,
                     "page_url": f"https://www.themoviedb.org/{kind}/{tid}"}
            if backdrop:
                entry["image"] = save(f"{TMDB_IMG}/w1280{backdrop}", slug(title) + "_still")
                entry["layout"] = "cover"
            if poster:
                entry["poster"] = save(f"{TMDB_IMG}/w780{poster}", slug(title) + "_poster")
                entry.setdefault("image", entry["poster"])
            if "image" in entry:
                by_title[title] = entry
                print(f"  ✓ TMDB {title} → {name} ({kind}/{tid})")
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ TMDB 실패: {title}: {e}")
        time.sleep(0.3)

    # 2) 위키백과 (TMDB 결과가 없는 작품만)
    need = [it for it in items if it.get("wiki") and not it.get("image") and str(it["title"]) not in by_title]
    if need:
        try:
            info = wiki_lookup([str(it["wiki"]) for it in need])
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ 위키백과 조회 실패: {e}")
            info = {}
        for it in need:
            meta = info.get(str(it["wiki"]))
            if not meta:
                print(f"  ⚠ 위키 이미지 없음: {it['wiki']}")
                continue
            if not meta["src"].lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                print(f"  ⚠ 지원하지 않는 형식: {it['wiki']}")
                continue
            try:
                rel = save(meta["src"], slug(str(it["wiki"])))
            except Exception as e:  # noqa: BLE001
                print(f"  ⚠ 위키 이미지 다운로드 실패: {it['wiki']}: {e}")
                continue
            by_title[str(it["title"])] = {"source": "wikipedia", "image": rel, "page_url": meta["page_url"]}
            print(f"  ✓ 위키 {it['title']} → {rel}")
            time.sleep(1)

    if saved or by_title:
        img_dir.mkdir(exist_ok=True)
        (img_dir / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
    # 더 이상 안 쓰는 이미지 정리
    used = {v for e in by_title.values() for k, v in e.items() if k in ("image", "poster")}
    for it in items:
        if it.get("image"):
            used.add(str(it["image"]))
    if img_dir.exists():
        for f in img_dir.iterdir():
            if f.name != "sources.json" and f"img/{f.name}" not in used:
                f.unlink()
    return saved
