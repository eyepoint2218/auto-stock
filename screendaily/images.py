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


def _norm(s: str) -> str:
    return re.sub(r"[\s:·!?,.'\"-]+", "", (s or "")).lower()


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

    def find_person(self, name: str, override: str = "") -> tuple[int, str] | None:
        """배우 (id, 이름). override 는 "person/1234"."""
        if override:
            pid = int(override.split("/")[-1])
            return pid, self.get(f"person/{pid}", language="ko-KR").get("name") or name
        res = self.get("search/person", query=name, language="ko-KR", include_adult="false")
        cands = [r for r in res.get("results", []) if r.get("known_for_department") == "Acting"] \
            or res.get("results", [])
        if not cands:
            return None
        best = max(cands, key=lambda r: r.get("popularity", 0))
        return best["id"], best.get("name") or name

    def person_profile(self, pid: int) -> str | None:
        d = self.get(f"person/{pid}/images")
        profiles = d.get("profiles", [])
        if not profiles:
            return None
        return max(profiles, key=lambda x: (x.get("vote_average", 0), x.get("height", 0)))["file_path"]

    def person_tagged(self, pid: int) -> tuple[dict[str, str], list[str]]:
        """배우가 태그된 사진 {"tv/123": file_path} 과 프로필 사진 목록 (최신·인기순)."""
        tagged: dict[str, tuple] = {}
        for page in (1, 2):
            d = self.get(f"person/{pid}/tagged_images", page=page)
            for r in d.get("results", []):
                m = r.get("media") or {}
                key = f"{r.get('media_type')}/{m.get('id')}"
                if r.get("image_type") == "poster":
                    continue
                score = (r.get("vote_average", 0), r.get("width", 0))
                if key not in tagged or score > tagged[key][0]:
                    tagged[key] = (score, r["file_path"])
            if page >= d.get("total_pages", 1):
                break
        profiles = [x["file_path"] for x in sorted(self.get(f"person/{pid}/images").get("profiles", []),
                                                    key=lambda x: (-x.get("vote_average", 0), -x.get("height", 0)))]
        return {k: v[1] for k, v in tagged.items()}, profiles

    def person_credits(self, pid: int) -> tuple[dict[str, str], dict[str, str]]:
        """(배역 {"tv/123": "배역"}, 제목 {정규화된 한국어 제목: "tv/123"})"""
        d = self.get(f"person/{pid}/combined_credits", language="ko-KR")
        roles, titles = {}, {}
        for c in sorted(d.get("cast", []), key=lambda c: -(c.get("popularity") or 0)):
            key = f"{c.get('media_type')}/{c.get('id')}"
            if c.get("character") and key not in roles:
                roles[key] = c["character"]
            for t in (c.get("title"), c.get("name"), c.get("original_title"), c.get("original_name")):
                if t:
                    titles.setdefault(_norm(t), key)
        return roles, titles

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
        "piprop": "original|thumbnail|name", "pithumbsize": 1280, "pilicense": "any", "titles": "|".join(titles),
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
                "thumb": (p.get("thumbnail") or {}).get("source", ""),
            }
    return out


# 작품(영화·드라마)이 아닌 카드: TMDB 검색 안 함, 위키 사진은 썸네일 + 작가·라이선스 표기
NON_WORK = ("story", "quote", "deal", "coupon", "steps", "note", "photo")


def _shrink(path: Path, max_side: int):
    from PIL import Image
    with Image.open(path) as im:
        if max(im.size) <= max_side:
            return
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side))
        im.save(path, quality=88)


def commons_license(src: str) -> str:
    """위키미디어 사진의 작가·라이선스 한 줄 (예: 사진 홍길동 · CC BY-SA 3.0)."""
    name = urllib.parse.unquote(urllib.parse.urlparse(src).path.split("/")[-1])
    if "/thumb/" in src and "px-" in name:  # 썸네일 주소면 원본 파일명만
        name = name.split("px-", 1)[1]
    try:
        r = _get(WIKI_API, params={"action": "query", "format": "json", "titles": "File:" + name,
                                   "prop": "imageinfo", "iiprop": "extmetadata"})
        md = next(iter(r.json()["query"]["pages"].values()))["imageinfo"][0]["extmetadata"]
    except Exception:  # noqa: BLE001
        return ""
    artist = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", md.get("Artist", {}).get("value", ""))).strip()
    # "This photo was taken by 홍길동 (아이디) ..." 같은 긴 설명은 이름만 남김
    artist = re.sub(r"^(this )?(photo|picture|image)( was)? (taken|made|created) by ", "", artist, flags=re.I)
    artist = re.split(r" \(|\. |, ", artist)[0].strip()
    lic = md.get("LicenseShortName", {}).get("value", "")
    return "사진 출처 · " + " · ".join(x for x in (artist[:30], lic, "Wikimedia Commons") if x)


def commons_thumb(url: str, width: int = 1280) -> str:
    """위키미디어 공용 파일 페이지(commons.wikimedia.org/wiki/File:...) → API 로 썸네일 주소."""
    name = urllib.parse.unquote(url.split("/wiki/", 1)[1]).replace("_", " ")
    r = _get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "titles": name, "prop": "imageinfo",
        "iiprop": "url", "iiurlwidth": width})
    ii = next(iter(r.json()["query"]["pages"].values()))["imageinfo"][0]
    return ii.get("thumburl") or ii["url"]


def page_image(url: str) -> str:
    """웹페이지 주소면 대표 이미지(og:image / twitter:image) 주소를, 이미지 주소면 그대로 돌려줌."""
    if "commons.wikimedia.org/wiki/File:" in url:
        return commons_thumb(url)
    if urllib.parse.urlparse(url).path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return url
    r = _get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; screendaily-card-generator/1.0)"})
    if r.headers.get("content-type", "").startswith("image/"):
        return url
    html = r.text
    for prop in ("og:image", "twitter:image", "og:image:url"):
        m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']+)' % re.escape(prop), html, re.I) \
            or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']%s["\']' % re.escape(prop), html, re.I)
        if m:
            return urllib.parse.urljoin(url, m.group(1).replace("&amp;", "&"))
    raise RuntimeError(f"대표 이미지를 찾지 못했습니다: {url}")


def fetch_cover(slot_dir: Path, raw: dict, sources: dict) -> str | None:
    """표지 이미지를 웹에서: cover_url(이미지 주소 또는 기사·페이지 주소) → cover_wiki(위키 대표 사진)."""
    if raw.get("cover_image"):
        return None
    url, wiki = str(raw.get("cover_url") or "").strip(), str(raw.get("cover_wiki") or "").strip()
    key = url or (f"wiki:{wiki}" if wiki else "")
    if not key:
        return None
    cur = sources.get("cover") or {}
    if cur.get("key") == key and (slot_dir / cur.get("image", "_")).is_file():
        return None
    entry = {"key": key}
    if url:
        src = page_image(url)
        entry["page_url"] = url
    else:
        meta = wiki_lookup([wiki]).get(wiki)
        if not meta:
            raise RuntimeError(f"위키 이미지 없음: {wiki}")
        src = meta.get("thumb") or meta["src"]
        entry["page_url"] = meta["page_url"]
        lic = commons_license(meta["src"])
        if lic:
            entry["credit"] = lic
    ext = Path(urllib.parse.urlparse(src).path).suffix.lower()
    ext = ext if ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"
    rel = f"img/cover_web{ext}"
    (slot_dir / "img").mkdir(exist_ok=True)
    r = _get(src)
    if not r.headers.get("content-type", "").startswith("image/"):
        raise RuntimeError(f"이미지가 아닌 응답: {r.headers.get('content-type')} ({src[:80]})")
    (slot_dir / rel).write_bytes(r.content)
    if "wikimedia.org" in src and "credit" not in entry:
        lic = commons_license(src)
        if lic:
            entry["credit"] = lic
    _shrink(slot_dir / rel, 1800)
    entry["image"], entry["src"] = rel, src
    sources["cover"] = entry
    return rel


# ------------------------------------------------------------------ 게시물 단위

def load_sources(slot_dir: Path) -> dict:
    f = slot_dir / "img" / "sources.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return data if "by_title" in data else {"by_title": {}}


def fetch_for_post(slot_dir: Path, refresh: bool = False) -> list[str]:
    raw = yaml.safe_load((slot_dir / "post.yml").read_text(encoding="utf-8")) or {}
    items = [it for it in (raw.get("items") or []) + (raw.get("recommend") or [])
             if isinstance(it, dict) and it.get("title")]
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

    # 0) 배우 소개: 배우를 먼저 찾고, 작품은 그 배우의 출연작 안에서 고른다 (동명 작품 방지)
    actor = str(raw.get("actor") or "").strip()
    roles: dict[str, str] = {}
    credit_titles: dict[str, str] = {}
    if actor and tmdb:
        cur = sources.get("actor", {})
        try:
            if cur.get("name_query") != actor or refresh or not (slot_dir / cur.get("image", "_")).is_file():
                found = tmdb.find_person(actor, str(raw.get("actor_tmdb") or ""))
                if not found:
                    print(f"  ⚠ TMDB 배우 검색 결과 없음: {actor} (actor_tmdb: \"person/ID\" 지정)")
                    cur = {}
                else:
                    pid, pname = found
                    cur = {"name_query": actor, "name": pname, "tmdb": f"person/{pid}",
                           "page_url": f"https://www.themoviedb.org/person/{pid}"}
                    prof = tmdb.person_profile(pid)
                    if prof:
                        cur["image"] = save(f"{TMDB_IMG}/h632{prof}", "actor_" + slug(actor))
                    sources["actor"] = cur
                    print(f"  ✓ TMDB 배우 {actor} → {pname} (person/{pid})")
            if cur.get("tmdb"):
                roles, credit_titles = tmdb.person_credits(int(cur["tmdb"].split("/")[-1]))
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ TMDB 배우 정보 실패: {actor}: {e}")

    # 1) TMDB
    for it in items:
        title = str(it["title"])
        if it.get("image") or not tmdb or str(it.get("tmdb") or "").lower() == "none" \
                or str(it.get("type") or "") in NON_WORK:
            continue
        cur = by_title.get(title, {})
        override = str(it.get("tmdb") or "")
        if not override and credit_titles:
            override = credit_titles.get(_norm(title), "")
            if not override:
                # 배우 게시물에서 출연 기록에 없는 작품은 엉뚱한 동명 작품이 잡히지 않도록 건너뜀
                print(f"  ⚠ {actor} 출연작에서 찾지 못함: {title} (사진 없이 진행. 필요하면 tmdb: \"movie/ID\" 지정)")
                continue
        if cur.get("source") == "tmdb" and not refresh and (not override or "/" not in override
                                                            or cur.get("tmdb") == override):
            if roles:
                cur["role"] = roles.get(cur.get("tmdb"), "")
            continue
        try:
            found = tmdb.find(title, override)
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
            if roles:
                entry["role"] = roles.get(entry["tmdb"], "")
            if "image" in entry:
                by_title[title] = entry
                print(f"  ✓ TMDB {title} → {name} ({kind}/{tid})")
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ TMDB 실패: {title}: {e}")
        time.sleep(0.3)

    # 1-3) 배우 게시물: 작품 스틸 대신 "그 배우가 나온 사진"을 우선 사용
    if actor and tmdb and sources.get("actor", {}).get("tmdb"):
        try:
            pid = int(sources["actor"]["tmdb"].split("/")[-1])
            tagged, profiles = tmdb.person_tagged(pid)
            spare = [p for p in profiles[1:]]  # 첫 번째는 표지에 사용
            for it in items:
                title = str(it["title"])
                if it.get("image") or str(it.get("type") or "") in NON_WORK:
                    continue
                e = by_title.get(title)
                if e and e.get("tmdb") in tagged:
                    if e.get("actor_photo") != tagged[e["tmdb"]] or "_actor" not in e.get("image", ""):
                        e["image"] = save(f"{TMDB_IMG}/w1280{tagged[e['tmdb']]}", slug(title) + "_actor")
                        e["actor_photo"] = tagged[e["tmdb"]]
                        e["layout"] = "cover"
                        print(f"  ✓ {title}: {actor} 태그 사진 사용")
                elif spare and not (e and e.get("image") and "_profile" not in e.get("image", "")):
                    # 작품 사진이 아예 없을 때만 배우 프로필 사진으로 채움
                    fp = spare.pop(0)
                    entry = e or {"source": "tmdb"}
                    if entry.get("actor_photo") != fp or "_profile" not in entry.get("image", ""):
                        entry["image"] = save(f"{TMDB_IMG}/h632{fp}", slug(title) + "_profile")
                        entry["actor_photo"] = fp
                        entry.pop("layout", None)
                    by_title[title] = entry
                    print(f"  ✓ {title}: 작품 속 사진이 없어 {actor} 프로필 사진 사용")
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ 배우 사진 가져오기 실패: {e}")

    # 1-5) 표지 이미지 (cover_url / cover_wiki)
    try:
        rel = fetch_cover(slot_dir, raw, sources)
        if rel:
            saved.append(rel)
            print(f"  ✓ 표지 이미지 → {rel}")
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠ 표지 이미지 가져오기 실패: {e}")

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
            if not urllib.parse.urlparse(meta["src"]).path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                print(f"  ⚠ 지원하지 않는 형식: {it['wiki']}")
                continue
            is_deal = str(it.get("type") or "") in NON_WORK
            try:  # 할인 카드는 1280px 썸네일 (원본은 수 MB 라 위키미디어가 자주 거절함)
                rel = save(meta.get("thumb") or meta["src"] if is_deal else meta["src"], slug(str(it["wiki"])))
            except Exception as e:  # noqa: BLE001
                print(f"  ⚠ 위키 이미지 다운로드 실패: {it['wiki']}: {e}")
                continue
            entry = {"source": "wikipedia", "image": rel, "page_url": meta["page_url"]}
            if str(it.get("type") or "") in NON_WORK:
                # 할인 카드용 일반 사진: 크기 줄이고, 사진 작가·라이선스를 카드에 표시
                _shrink(slot_dir / rel, 1600)
                lic = commons_license(meta["src"])
                if lic:
                    entry["credit"] = lic
            by_title[str(it["title"])] = entry
            print(f"  ✓ 위키 {it['title']} → {rel}")
            time.sleep(1)

    if saved or by_title or sources.get("actor") or sources.get("cover"):
        img_dir.mkdir(exist_ok=True)
        (img_dir / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
    # 더 이상 안 쓰는 이미지 정리
    used = {v for e in by_title.values() for k, v in e.items() if k in ("image", "poster")}
    if sources.get("actor", {}).get("image"):
        used.add(sources["actor"]["image"])
    if sources.get("cover", {}).get("image"):
        used.add(sources["cover"]["image"])
    if raw.get("cover_image"):  # 직접 넣은 표지 이미지는 절대 지우지 않음
        used.add(str(raw["cover_image"]))
    for it in items:
        if it.get("image"):
            used.add(str(it["image"]))
    if img_dir.exists():
        for f in img_dir.iterdir():
            if f.name != "sources.json" and f"img/{f.name}" not in used:
                f.unlink()
    return saved
