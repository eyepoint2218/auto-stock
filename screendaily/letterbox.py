"""위쪽 검은 칸 릴스 (layout: letterbox).

잘된 영화·드라마 릴스에서 많이 쓰는 구성:
  위쪽 검은 칸에 후킹 문구(영상 내내 고정) → 가운데 장면 → 장면 아래쪽 자막 → 작품 제목.
카드(4:5)를 흐린 배경에 올리는 기본 릴스와 달리 9:16 프레임을 바로 그린다.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

from .cards import B, EB, R, cover_crop, fit, font, hex2rgb, line_h, open_img, placeholder_bg, THEMES
from .post import Item, Post

RW, RH = 1080, 1920
M = 72
HOOK_BOTTOM = 640          # 후킹 문구 칸 아래 끝
IMG_Y, IMG_H = 680, 760    # 가운데 장면 (아래 약 400px 는 인스타 UI 에 가려짐)
LABEL_Y = IMG_Y + IMG_H + 70
WHITE = (255, 255, 255)


def _scene(im: Image.Image | None, seed: int, accent) -> Image.Image:
    """장면 이미지. 가로 사진은 꽉 채우고, 세로 사진(배우 프로필)은 흐린 배경 위에 가운데 정렬."""
    size = (RW, IMG_H)
    if im is None:
        return placeholder_bg(size, accent, THEMES["dark"], seed).convert("RGB")
    im = im.convert("RGB")
    if im.width / im.height >= 1.2:
        return cover_crop(im, size, (0.5, 0.4))
    bg = cover_crop(im, size, (0.5, 0.3)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", size, (0, 0, 0)), 0.45)
    h = IMG_H
    w = int(im.width * h / im.height)
    bg.paste(im.resize((w, h), Image.LANCZOS), ((RW - w) // 2, 0))
    return bg


def _shadow_text(canvas: Image.Image, lines, f, y: int, fill=WHITE):
    """장면 위 자막: 검은 외곽선으로 어떤 배경에서도 읽히게."""
    d = ImageDraw.Draw(canvas)
    lh = line_h(f)
    for i, ln in enumerate(lines):
        d.text((RW / 2, y + i * lh), ln, font=f, fill=fill, anchor="ma", stroke_width=5, stroke_fill=(0, 0, 0))


def _frame(post: Post, config: dict, im: Image.Image | None, subtitle: str, label: str, seed: int) -> Image.Image:
    accent = hex2rgb(config.get("labels", {}).get(post.label, config.get("labels", {}).get("default", "#FF4D4D")))
    canvas = Image.new("RGB", (RW, RH), (0, 0, 0))
    d = ImageDraw.Draw(canvas)

    # 1) 후킹 문구 (모든 장면에서 같은 위치에 고정)
    f, lines = fit(post.title.replace("\\n", "\n"), EB, RW - M * 2, 3, 84, 60)
    lh = line_h(f)
    y = HOOK_BOTTOM - 40 - lh * len(lines)
    for i, ln in enumerate(lines):
        d.text((RW / 2, y + i * lh), ln, font=f, fill=WHITE, anchor="ma")

    # 2) 장면
    canvas.paste(_scene(im, seed, accent), (0, IMG_Y))

    # 3) 장면 아래쪽 자막
    if subtitle:
        sf, sl = fit(subtitle, EB, RW - M * 2, 2, 52, 38)
        _shadow_text(canvas, sl, sf, IMG_Y + IMG_H - 40 - line_h(sf) * len(sl))

    # 4) 작품 제목 · 연도
    if label:
        d.text((RW / 2, LABEL_Y), label, font=font(B, 38), fill=(225, 225, 230), anchor="ma")
    d.text((RW / 2, LABEL_Y + 70), config.get("handle", ""), font=font(R, 28), fill=(140, 140, 150), anchor="ma")
    return canvas


def _label(it: Item) -> str:
    t = it.title
    return f"{t} ({it.year})" if it.year else t


def render_letterbox(post: Post, config: dict) -> list[Image.Image]:
    frames = []
    for i, it in enumerate(post.items, 1):
        # 배우 이야기에서 작품 스틸을 쓰면 다른 배우 얼굴 위에 자막이 얹힐 수 있어,
        # 배우 게시물은 작품 포스터(세로 → 가운데 정렬)를 우선한다
        rel = (it.poster or it.image) if post.actor else it.image
        im = open_img(post.asset(rel)) or open_img(post.asset(post.actor_image))
        frames.append(_frame(post, config, im, it.desc, _label(it), i))
    if post.outro:
        q = post.outro_question or config.get("outro", {}).get("question", "")
        last = post.items[-1] if post.items else None
        im = open_img(post.asset(post.cover_image or post.actor_image)) or (
            open_img(post.asset(last.image)) if last else None)
        cta = config.get("outro", {}).get("cta", "팔로우하고 매일 추천 받기")
        frames.append(_frame(post, config, im, q, cta, 99))
    return frames
