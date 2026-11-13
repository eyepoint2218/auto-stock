"""post.yml / config.yml 로딩과 검증."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import ROOT

GENERATOR_VERSION = "11"  # 디자인을 바꾸면 올려서 미리보기를 다시 만들게 함


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
    role: str = ""    # 배우 소개: 배역 이름 (비우면 TMDB 출연 기록에서 자동)
    year: str = ""    # 배우 스토리: 큰 숫자 대신 연도 표시 (예: 1997)
    stage: str = ""   # 배우 스토리: 단계 표시 (예: 데뷔, 첫 주연, 전환점)
    type: str = ""    # story = 글 중심 이야기 카드, quote = 인용 카드 (작품 사진 없음), deal = 사진 + 두 줄 할인 카드
    brand: str = ""   # 이야기 카드 색을 config.yml brands: 의 브랜드 색으로 (예: SKT, KT, LGU)


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
    actor: str = ""            # 배우 소개 게시물: 배우 이름
    actor_tmdb: str = ""       # 동명이인일 때 person/ID
    actor_image: str = ""      # (자동) 배우 프로필 사진
    actor_name: str = ""       # (자동) TMDB 의 배우 이름
    outro_question: str = ""   # 마지막 장 질문 문구 (비우면 config 기본값)
    cover_style: str = ""      # deal = 표지도 할인 카드처럼 (사진 + 마지막 줄 노란 글씨)
    brand: str = ""            # 캐러셀 전체 색 (config.yml brands: 의 splash). 표지·마지막 장·brand 없는 이야기 카드에 적용
    reveal: bool = False       # 배우 맞히기: 이름을 숨기고 마지막에 정답 공개
    reveal_text: str = ""      # 정답 카드의 한 줄 소개
    recommend: list[Item] = field(default_factory=list)  # 정답 뒤 추천작 카드 (최대 4편)
    recommend_title: str = ""  # 추천작 카드 제목
    layout: str = ""           # letterbox = 위쪽 검은 칸 릴스 (format: reel 전용)

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

    def hashtag_split(self, config: dict) -> tuple[list[str], list[str]]:
        """(붙일 해시태그, 개수 제한으로 빠진 해시태그).
        게시물 hashtags 를 먼저, 그다음 config 의 default_hashtags. 본문에 직접 쓴 #태그도 개수에 포함."""
        limit = int(config.get("hashtag_limit", 5))
        in_body = len(re.findall(r"(?<![\w&])#[^\s#]+", self.caption or ""))
        tags: list[str] = []
        for t in list(self.hashtags) + list(config.get("default_hashtags", [])):
            t = str(t).strip().lstrip("#")
            if t and t not in tags:
                tags.append(t)
        n = max(0, limit - in_body)
        return tags[:n], tags[n:]

    def full_caption(self, config: dict) -> str:
        tags, _ = self.hashtag_split(config)
        parts = [self.caption.strip()]
        if self.credits:
            parts.append(self.credits.strip())
        if tags:
            parts.append(" ".join("#" + t for t in tags))
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

    def parse_items(lst, kind="items"):
        out = []
        for i, it in enumerate(lst or [], 1):
            if isinstance(it, str):
                it = {"title": it}
            if not it.get("title"):
                raise ValueError(f"[{slot_dir.name}] {kind} {i}번에 title 이 없습니다")
            item = Item(**{k: str(v) for k, v in it.items() if k in Item.__dataclass_fields__ and v is not None})
            auto = by_title.get(item.title)
            if auto and not item.role and re.search(r"[가-힣]", auto.get("role") or ""):
                item.role = auto["role"]
            if not item.image and auto and (slot_dir / auto["image"]).is_file():
                item.image = auto["image"]
                item.poster = auto.get("poster", "")
                item.layout = auto.get("layout", "")
                if not item.credit:
                    item.credit = f"이미지 © {item.ott or '제작사'} · via {via.get(auto.get('source'), '웹')}"
            out.append(item)
        return out

    recommend = parse_items(raw.get("recommend"), "recommend")[:4]
    items = []
    for i, it in enumerate(raw.get("items") or [], 1):
        if isinstance(it, str):
            it = {"title": it}
        if not it.get("title"):
            raise ValueError(f"[{slot_dir.name}] items {i}번에 title 이 없습니다")
        item = Item(**{k: str(v) for k, v in it.items() if k in Item.__dataclass_fields__ and v is not None})
        auto = by_title.get(item.title)
        # TMDB 배역은 영어인 경우가 많아, 한글이 들어 있을 때만 자동으로 쓴다 (아니면 role: 로 직접)
        if auto and not item.role and re.search(r"[가-힣]", auto.get("role") or ""):
            item.role = auto["role"]
        if not item.image and auto and (slot_dir / auto["image"]).is_file():
            item.image = auto["image"]
            item.poster = auto.get("poster", "")
            item.layout = auto.get("layout", "")
            if not item.credit:
                item.credit = auto.get("credit") or \
                    f"이미지 © {item.ott or '제작사'} · via {via.get(auto.get('source'), '웹')}"
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
        actor=str(raw.get("actor", "") or ""),
        actor_tmdb=str(raw.get("actor_tmdb", "") or ""),
        outro_question=str(raw.get("outro_question", "") or ""),
        brand=str(raw.get("brand", "") or ""),
        cover_style=str(raw.get("cover_style", "") or ""),
        reveal=bool(raw.get("reveal", False)),
        reveal_text=str(raw.get("reveal_text", "") or ""),
        recommend=recommend,
        recommend_title=str(raw.get("recommend_title", "") or ""),
        layout=str(raw.get("layout", "") or "").lower(),
    )

    act = sources.get("actor", {})
    if post.actor and act.get("image") and (slot_dir / act["image"]).is_file():
        post.actor_image = act["image"]
        post.actor_name = act.get("name", "")

    if not post.images:
        if not post.title:
            raise ValueError(f"[{slot_dir.name}] title 이 없습니다")
        slides = 1 + len(items) + (1 if post.outro else 0) + (1 if post.reveal else 0) + (1 if recommend else 0)
        if slides > 10:
            raise ValueError(f"[{slot_dir.name}] 표지+작품+마지막장이 {slides}장입니다. 최대 10장(작품 최대 8개)")
        if post.format == "carousel" and slides < 2:
            raise ValueError(f"[{slot_dir.name}] 캐러셀은 최소 2장이 필요합니다")
    if post.layout not in ("", "letterbox"):
        raise ValueError(f"[{slot_dir.name}] layout 은 letterbox 만 쓸 수 있습니다")
    if post.layout == "letterbox" and post.format != "reel":
        raise ValueError(f"[{slot_dir.name}] layout: letterbox 는 format: reel 에서만 쓸 수 있습니다")
    if post.layout == "letterbox" and not post.items:
        raise ValueError(f"[{slot_dir.name}] layout: letterbox 는 items(장면)가 필요합니다")
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
