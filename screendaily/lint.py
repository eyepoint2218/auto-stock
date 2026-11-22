"""후킹 규칙 검사. 업로드를 막지 않고 경고만 냅니다 (CLAUDE.md '후킹 규칙' 참고)."""
from __future__ import annotations

import re

from .post import Post, channel_config

TITLE_MAX = 20      # 표지 제목 글자 수 (공백·줄바꿈 제외)
BUBBLE_MAX = 10     # 말풍선 글자 수 (공백 제외)
REEL_ITEMS_MAX = 4  # 릴스 작품 수 (표지·마지막 장 포함 약 15~18초)
TOON_REEL_MAX = 5  # 인스타툰 릴스 칸 수 (표지 + 5칸 + 팔로우 카드 = 약 18초)

# 카드 폰트(나눔스퀘어)에 없는 이모지·기호
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
GREETING = re.compile(r"^\s*(안녕|오늘은|여러분|이번\s*시간)")


def _len(s: str) -> int:
    return len(re.sub(r"\s", "", s or ""))


def lint_post(p: Post, config: dict | None = None) -> list[str]:
    w: list[str] = []
    if config is not None:
        config = channel_config(config, p)
    sched = (config or {}).get("schedule") or {}
    if sched and not p.draft:  # 연재 요일·시간 (예: 공감툰 월·수·금 21:00)
        days = [int(x) for x in sched.get("days") or []]
        if days and p.publish_at.weekday() not in days:
            names = "월화수목금토일"
            w.append(f"연재일이 아닌 날이에요: {p.publish_at:%m/%d}({names[p.publish_at.weekday()]}). "
                     f"연재일: {'·'.join(names[d] for d in days)}")
        if sched.get("time") and f"{p.publish_at:%H:%M}" != sched["time"]:
            w.append(f"게시 시간이 {p.publish_at:%H:%M} 이에요. 이 채널 연재 시간은 {sched['time']}.")
    if p.images:  # 직접 만든 이미지는 글자 검사 생략 (게시글 이모지만 확인)
        if EMOJI.search(p.caption or ""):
            w.append("게시글(caption)에는 이모지를 넣지 않아요.")
        return w
    if p.channel == "deals" and p.cover_style == "photo":  # docs/cover_guide.md 표지 고정 지침
        lines = [t for t in p.title.splitlines() if t.strip()]
        if len(lines) > 3:
            w.append(f"혜택알람 표지는 최대 3줄이에요 (지금 {len(lines)}줄).")
        if _len(p.title) > 25:
            w.append(f"혜택알람 표지가 {_len(p.title)}자예요. 공백 제외 25자 이내로.")
        if len(lines) > 1 and _len(lines[0]) > 10:
            w.append(f"표지 첫 줄(멤버십·브랜드)이 {_len(lines[0])}자예요. 10자 이하로.")
        for b in lines[1:]:
            if _len(b) > 12:
                w.append(f"표지 혜택 줄 '{b}' 이 {_len(b)}자예요. 12자 이하로 줄이거나 줄을 나누세요.")
    elif _len(p.title) > TITLE_MAX:
        w.append(f"표지 제목이 {_len(p.title)}자예요. {TITLE_MAX}자 이하로 줄이면 1초 안에 읽혀요.")
    if GREETING.search(p.title):
        w.append("표지 제목이 인사로 시작해요. 첫 화면은 후킹 문장으로 시작하세요.")
    if _len(p.bubble) > BUBBLE_MAX:
        w.append(f"말풍선이 {_len(p.bubble)}자예요. {BUBBLE_MAX}자 이하, 감정 하나만 담으세요.")

    fields = [("title", p.title), ("subtitle", p.subtitle), ("bubble", p.bubble),
              ("outro_question", p.outro_question), ("reveal_text", p.reveal_text),
              ("reveal_name", p.reveal_name), ("reveal_hint", p.reveal_hint),
              ("outro_title", p.outro_title), ("outro_cta", p.outro_cta), ("outro_save", p.outro_save)]
    fields += [(f"reveal_info[{i}]", v) for i, v in enumerate(p.reveal_info, 1)]
    for i, it in enumerate(p.items, 1):
        fields += [(f"items[{i}].{k}", getattr(it, k)) for k in ("title", "genre", "desc", "bubble", "year", "stage")]
    for name, val in fields:
        if val and EMOJI.search(val):
            w.append(f"{name} 에 이모지가 있어요. 카드에서 네모로 깨지니 caption 에만 쓰세요.")

    for i, it in enumerate(p.items, 1):
        if it.type == "deal":
            for k in ("title", "desc"):
                if _len(getattr(it, k)) > 12:
                    w.append(f"items[{i}].{k} 가 {_len(getattr(it, k))}자예요. 할인 카드는 줄마다 12자 이하로 짧게.")
        if it.type == "toon":
            if _len(it.bubble) > BUBBLE_MAX:
                w.append(f"items[{i}].bubble 이 {_len(it.bubble)}자예요. {BUBBLE_MAX}자 이하, 감정 하나만.")
            if _len(it.title) > 22 or _len(it.desc) > 30:
                w.append(f"items[{i}] 인스타툰 상자 글이 길어요. 위 상자 22자·아래 상자 30자 이하로 한눈에 읽히게.")
    steps = [it for it in p.items if it.type == "steps"]
    if p.channel == "deals" and steps and not any(
            "~" in (it.desc or "") or re.search(r"\d{1,2}/\d{1,2}\s*(오늘\s*)?하루", it.desc or "") for it in steps):
        w.append("혜택알람 2장 STEP 에 기간이 없어요. STEP 안에 '11/19~11/30' 처럼 시작~마감 날짜를 (하루 행사는 '11/19 하루') 넣으세요.")
    if EMOJI.search(p.caption or ""):
        w.append("게시글(caption)에는 이모지를 넣지 않아요.")
    toon = bool(p.items) and all(it.type == "toon" for it in p.items)
    reel_max = TOON_REEL_MAX if toon else REEL_ITEMS_MAX
    if p.format == "reel" and len(p.items) > reel_max:
        what = "인스타툰 칸" if toon else "릴스 작품"
        w.append(f"{what}이 {len(p.items)}개예요. {reel_max}개 이하면 15~18초 안에 끝나요.")
    if p.layout == "letterbox":
        if len(p.title.splitlines()) > 2:
            w.append("letterbox 후킹 문구는 2줄 이하가 좋아요 (영상 내내 위에 고정됨).")
        for i, it in enumerate(p.items, 1):
            if _len(it.desc) > 30:
                w.append(f"items[{i}].desc 자막이 {_len(it.desc)}자예요. 3초 안에 읽히게 30자 이하로 줄이세요.")
    if config is not None:
        _, dropped = p.hashtag_split(config)
        own = {str(t).strip().lstrip("#") for t in p.hashtags}
        dropped = [t for t in dropped if t in own]  # 기본 해시태그가 밀려나는 건 정상
        if dropped:
            w.append(f"해시태그는 최대 {config.get('hashtag_limit', 5)}개라 빠지는 태그: "
                     + " ".join("#" + t for t in dropped) + " (중요한 태그를 hashtags 앞쪽에)")
    if p.reveal and not p.reveal_text:
        w.append("reveal: true 인데 reveal_text 가 없어요. 마지막 정답 카드로 약속을 지켜 주세요.")
    return w
