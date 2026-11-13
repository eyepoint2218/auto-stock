"""후킹 규칙 검사. 업로드를 막지 않고 경고만 냅니다 (CLAUDE.md '후킹 규칙' 참고)."""
from __future__ import annotations

import re

from .post import Post

TITLE_MAX = 20      # 표지 제목 글자 수 (공백·줄바꿈 제외)
BUBBLE_MAX = 10     # 말풍선 글자 수 (공백 제외)
REEL_ITEMS_MAX = 4  # 릴스 작품 수 (표지·마지막 장 포함 약 15~18초)

# 카드 폰트(나눔스퀘어)에 없는 이모지·기호
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
GREETING = re.compile(r"^\s*(안녕|오늘은|여러분|이번\s*시간)")


def _len(s: str) -> int:
    return len(re.sub(r"\s", "", s or ""))


def lint_post(p: Post) -> list[str]:
    w: list[str] = []
    if p.images:  # 직접 만든 이미지는 검사하지 않음
        return w
    if _len(p.title) > TITLE_MAX:
        w.append(f"표지 제목이 {_len(p.title)}자예요. {TITLE_MAX}자 이하로 줄이면 1초 안에 읽혀요.")
    if GREETING.search(p.title):
        w.append("표지 제목이 인사로 시작해요. 첫 화면은 후킹 문장으로 시작하세요.")
    if _len(p.bubble) > BUBBLE_MAX:
        w.append(f"말풍선이 {_len(p.bubble)}자예요. {BUBBLE_MAX}자 이하, 감정 하나만 담으세요.")

    fields = [("title", p.title), ("subtitle", p.subtitle), ("bubble", p.bubble),
              ("outro_question", p.outro_question), ("reveal_text", p.reveal_text)]
    for i, it in enumerate(p.items, 1):
        fields += [(f"items[{i}].{k}", getattr(it, k)) for k in ("title", "genre", "desc", "bubble", "year", "stage")]
    for name, val in fields:
        if val and EMOJI.search(val):
            w.append(f"{name} 에 이모지가 있어요. 카드에서 네모로 깨지니 caption 에만 쓰세요.")

    if p.format == "reel" and len(p.items) > REEL_ITEMS_MAX:
        w.append(f"릴스 작품이 {len(p.items)}개예요. {REEL_ITEMS_MAX}개 이하면 15~18초 안에 끝나요.")
    if p.layout == "letterbox":
        if len(p.title.splitlines()) > 2:
            w.append("letterbox 후킹 문구는 2줄 이하가 좋아요 (영상 내내 위에 고정됨).")
        for i, it in enumerate(p.items, 1):
            if _len(it.desc) > 30:
                w.append(f"items[{i}].desc 자막이 {_len(it.desc)}자예요. 3초 안에 읽히게 30자 이하로 줄이세요.")
    if p.reveal and not p.reveal_text:
        w.append("reveal: true 인데 reveal_text 가 없어요. 마지막 정답 카드로 약속을 지켜 주세요.")
    return w
