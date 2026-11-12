"""post.yml / config.yml 로딩과 검증."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import ROOT

GENERATOR_VERSION = "6"  # 디자인을 바꾸면 올려서 미리보기를 다시 만들게 함


def load_config() -> dict:
    with open(ROOT / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class Item:
    title: str
    ott: str = ""
    genre: str = ""
    desc: str = ""
    image: str = ""
    bubble: str = ""
    wiki: str = ""    # 영문 위키백과 문서 제목 → 이미지 자동 가져오기
    tmdb: str = ""    # TMDB 작품 지정 (예: tv/93405), 비우면 제목으로 검색
    credit: str = ""  # 카드에 작게 표시할 이미지 출처 (자동)
    poster: str = ""  # 표지 콜라주용 세로 포스터 (자동)
    layout: str = ""  # cover = 사진을 꽉 채움 (자동)


@dataclass
class Post:
    dir: Path
    publish_at: datetime
    format: str  # carousel | reel
    title: str
    label: str = "MOOD"
    subtitle: str = ""
    bubble: str = ""
    theme: str = "dark"
    cover_image: str = ""
    items: list[Item] = field(default_factory=list)
    images: list[str] = field(default_factory=list)  # 직접 만든 이미지로 올릴 때
    outro: bool = True
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    credits: str = ""
    draft: bool = False
    bgm: str = ""

    @property
    def name(self) -> str:
        return self.dir.name

    @property
    def out_dir(self) -> Path:
        return self.dir / "out"

    def asset(self, rel: str) -> Path | None:
        if not rel:
            return None
        p = (self.dir / rel).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"[{self.name}] 이미지 파일이 없습니다: {rel}")
        return p

    def full_caption(self, config: dict) -> str:
        tags: list[str] = []
        for t in list(self.hashtags) + list(config.get("default_hashtags", [])):
            t = str(t).strip().lstrip("#")
            if t and t not in tags:
                tags.append(t)
        parts = [self.caption.strip()]
        if self.credits:
            parts.append(self.credits.strip())
        if tags:
            parts.append(" ".join("#" + t for t in tags[:30]))
        return "\n\n".join(p for p in parts if p)

    def source_hash(self) -> str:
        h = hashlib.sha256(GENERATOR_VERSION.encode())
        files = [ROOT / "config.yml"]
        for f in sorted(self.dir.rglob("*")):
            rel = f.relative_to(self.dir)
            if f.is_file() and rel.parts[0] != "out" and f.name not in ("failures.json", "result.json"):
                files.append(f)
        for f in files:
            h.update(f.name.encode())
            h.update(f.read_bytes())
        return h.hexdigest()


def _parse_time(value, tz: ZoneInfo) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip().replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"publish_at 형식이 잘못됐습니다: {value!r} (예: 2026-11-17 19:00)")
    return dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)


def load_post(slot_dir: Path, config: dict) -> Post:
    path = slot_dir / "post.yml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    tz = ZoneInfo(config.get("timezone", "Asia/Seoul"))

    if "publish_at" not in raw:
        raise ValueError(f"[{slot_dir.name}] publish_at 이 없습니다")
    fmt = str(raw.get("format", "carousel")).lower()
    if fmt not in ("carousel", "reel"):
        raise ValueError(f"[{slot_dir.name}] format 은 carousel 또는 reel 이어야 합니다")

    sources_file = slot_dir / "img" / "sources.json"
    sources = json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else {}
    by_title = sources.get("by_title", {})
    via = {"tmdb": "TMDB", "wikipedia": "Wikipedia"}

    items = []
    for i, it in enumerate(raw.get("items") or [], 1):
        if isinstance(it, str):
            it = {"title": it}
        if not it.get("title"):
            raise ValueError(f"[{slot_dir.name}] items {i}번에 title 이 없습니다")
        item = Item(**{k: str(v) for k, v in it.items() if k in Item.__dataclass_fields__ and v is not None})
        auto = by_title.get(item.title)
        if not item.image and auto and (slot_dir / auto["image"]).is_file():
            item.image = auto["image"]
            item.poster = auto.get("poster", "")
            item.layout = auto.get("layout", "")
            if not item.credit:
                item.credit = f"이미지 © {item.ott or '제작사'} · via {via.get(auto.get('source'), '웹')}"
        items.append(item)

    post = Post(
        dir=slot_dir,
        publish_at=_parse_time(raw["publish_at"], tz),
        format=fmt,
        title=str(raw.get("title", "")),
        label=str(raw.get("label", "MOOD")).upper(),
        subtitle=str(raw.get("subtitle", "") or ""),
        bubble=str(raw.get("bubble", "") or ""),
        theme=str(raw.get("theme", "dark")).lower(),
        cover_image=str(raw.get("cover_image", "") or ""),
        items=items,
        images=[str(x) for x in raw.get("images") or []],
        outro=bool(raw.get("outro", True)),
        caption=str(raw.get("caption", "") or ""),
        hashtags=[str(x) for x in raw.get("hashtags") or []],
        credits=str(raw.get("credits", "") or ""),
        draft=bool(raw.get("draft", False)),
        bgm=str(raw.get("bgm", "") or ""),
    )

    if not post.images:
        if not post.title:
            raise ValueError(f"[{slot_dir.name}] title 이 없습니다")
        slides = 1 + len(items) + (1 if post.outro else 0)
        if slides > 10:
            raise ValueError(f"[{slot_dir.name}] 표지+작품+마지막장이 {slides}장입니다. 최대 10장(작품 최대 8개)")
        if post.format == "carousel" and slides < 2:
            raise ValueError(f"[{slot_dir.name}] 캐러셀은 최소 2장이 필요합니다")
    if post.theme not in ("dark", "light"):
        raise ValueError(f"[{slot_dir.name}] theme 은 dark 또는 light")
    if len(post.full_caption(config)) > 2200:
        raise ValueError(f"[{slot_dir.name}] 캡션이 2200자를 넘습니다")
    return post


def list_posts(base: Path, config: dict) -> list[Post]:
    posts = []
    for d in sorted(p for p in base.iterdir() if p.is_dir() and (p / "post.yml").exists()):
        posts.append(load_post(d, config))
    return posts
