"""카드뉴스 이미지(1080x1350, 4:5) 생성."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from . import FONT_DIR
from .post import Item, Post

W, H = 1080, 1350
M = 64  # 좌우 여백

EB, B, R = "NanumSquareEB.ttf", "NanumSquareB.ttf", "NanumSquareR.ttf"

THEMES = {
    "dark": {"bg": (14, 14, 16), "fg": (255, 255, 255), "sub": (200, 200, 208), "muted": (130, 130, 140)},
    "light": {"bg": (243, 238, 230), "fg": (20, 20, 22), "sub": (70, 66, 60), "muted": (140, 132, 120)},
}
BUBBLE_RED = (230, 40, 40)


@lru_cache(maxsize=64)
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _tw(fnt, text: str) -> float:
    return fnt.getlength(text)


def wrap(text: str, fnt, max_w: float) -> list[str]:
    """띄어쓰기 우선으로 줄바꿈, 너무 긴 단어는 글자 단위로 자름. \\n 은 강제 줄바꿈."""
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = word if not cur else f"{cur} {word}"
            if _tw(fnt, cand) <= max_w:
                cur = cand
                continue
            if cur:
                lines.append(cur)
                cur = ""
            while _tw(fnt, word) > max_w:
                i = len(word)
                while i > 1 and _tw(fnt, word[:i]) > max_w:
                    i -= 1
                lines.append(word[:i])
                word = word[i:]
            cur = word
        lines.append(cur)
    return lines


def fit(text: str, name: str, max_w: float, max_lines: int, start: int, minimum: int):
    size = start
    while True:
        f = font(name, size)
        lines = wrap(text, f, max_w)
        if len(lines) <= max_lines or size <= minimum:
            break
        size -= 4
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and _tw(f, last + "…") > max_w:
            last = last[:-1]
        lines[-1] = last + "…"
    return f, lines


def line_h(f) -> int:
    return int(f.size * 1.22)


def block_h(f, lines) -> int:
    return line_h(f) * len(lines)


def draw_lines(d: ImageDraw.ImageDraw, lines, f, x, y, fill, anchor_center=False) -> int:
    for ln in lines:
        if anchor_center:
            d.text((W / 2, y), ln, font=f, fill=fill, anchor="ma")
        else:
            d.text((x, y), ln, font=f, fill=fill)
        y += line_h(f)
    return y


def open_img(path: Path | None) -> Image.Image | None:
    if not path:
        return None
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def cover_crop(im: Image.Image, size, centering=(0.5, 0.35)) -> Image.Image:
    return ImageOps.fit(im, size, Image.LANCZOS, centering=centering)


def vgrad(size, color, y0: float, y1: float, a0=0, a1=255) -> Image.Image:
    """y0~y1 구간에서 color 의 투명도가 a0→a1 로 바뀌는 오버레이."""
    w, h = size
    col = Image.new("L", (1, h))
    for y in range(h):
        t = 0 if y <= y0 else 1 if y >= y1 else (y - y0) / (y1 - y0)
        t = t * t * (3 - 2 * t)  # smoothstep
        col.putpixel((0, y), int(a0 + (a1 - a0) * t))
    layer = Image.new("RGBA", size, color + (0,))
    layer.putalpha(col.resize(size))
    return layer


def pill(d, x, y, text, f, bg, fg, pad=(22, 12)) -> tuple[int, int, int, int]:
    tw = _tw(f, text)
    box = (x, y, int(x + tw + pad[0] * 2), int(y + f.size + pad[1] * 2))
    d.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=bg)
    d.text((x + pad[0], y + pad[1] + f.size * 0.02), text, font=f, fill=fg)
    return box


def bubble_layer(text: str, size=40, angle=-2.5) -> Image.Image:
    """main.today 스타일: 흰 바탕 + 빨간 테두리 반응 말풍선."""
    f = font(EB, size)
    lines = wrap(text, f, 760)
    tw = max(_tw(f, ln) for ln in lines)
    bw, bh = int(tw + 64), int(block_h(f, lines) + 34)
    pad = 30
    layer = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((pad + 6, pad + 8, pad + bw + 6, pad + bh + 8), 14, fill=(0, 0, 0, 120))
    layer = Image.alpha_composite(layer, shadow.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((pad, pad, pad + bw, pad + bh), 14, fill=(255, 255, 255), outline=BUBBLE_RED, width=6)
    y = pad + 17
    for ln in lines:
        d.text((pad + bw / 2, y), ln, font=f, fill=(20, 20, 20), anchor="ma")
        y += line_h(f)
    return layer.rotate(angle, resample=Image.BICUBIC, expand=True)


def paste_center(canvas: Image.Image, layer: Image.Image, cx: int, cy: int):
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def footer(canvas, theme, brand: str, page: str = ""):
    d = ImageDraw.Draw(canvas)
    fg = theme["fg"]
    d.line((M, H - 96, W - M, H - 96), fill=fg + (110,), width=2)
    f = font(B, 26)
    d.text((W / 2, H - 70), brand, font=f, fill=fg + (220,), anchor="ma")
    if page:
        d.text((W - M, H - 70), page, font=font(R, 26), fill=fg + (170,), anchor="ra")


def poster_card(im: Image.Image, w: int, angle: float) -> Image.Image:
    """폴라로이드 느낌의 기울어진 포스터."""
    h = int(w * 1.42)
    poster = cover_crop(im, (w, h), (0.5, 0.3))
    border = 12
    frame = Image.new("RGBA", (w + border * 2, h + border * 2), (255, 255, 255, 255))
    frame.paste(poster, (border, border))
    pad = 24
    out = Image.new("RGBA", (frame.width + pad * 2, frame.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((pad + 6, pad + 10, pad + frame.width + 6, pad + frame.height + 10), fill=(0, 0, 0, 110))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(10)))
    out.alpha_composite(frame, (pad, pad))
    return out.rotate(angle, resample=Image.BICUBIC, expand=True)


def placeholder_bg(size, accent, theme, seed: int = 0) -> Image.Image:
    """이미지가 없을 때 쓰는 그라데이션 배경."""
    w, h = size
    base = Image.new("RGBA", size, theme["bg"] + (255,))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx = int(w * (0.25 + 0.5 * ((seed * 37) % 10) / 10))
    gd.ellipse((cx - w * 0.6, -h * 0.5, cx + w * 0.6, h * 0.6), fill=accent + (150,))
    return Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(160)))


# ---------------------------------------------------------------- 표지

def render_cover(post: Post, config: dict) -> Image.Image:
    theme = THEMES[post.theme]
    accent = hex2rgb(config.get("labels", {}).get(post.label, config.get("labels", {}).get("default", "#FF4D4D")))
    brand = config.get("brand", "SCREEN DAILY")
    canvas = Image.new("RGBA", (W, H), theme["bg"] + (255,))

    cover = open_img(post.asset(post.cover_image))
    all_imgs = [open_img(post.asset(it.image)) for it in post.items if it.image]
    posters = [open_img(post.asset(it.poster)) for it in post.items if it.poster]
    item_imgs = (posters + [im for im in all_imgs if im.height >= im.width])[:3]  # 콜라주는 세로 포스터만
    wide_imgs = [im for im in all_imgs if im.height < im.width]

    if cover:
        canvas.paste(cover_crop(cover, (W, H)), (0, 0))
        canvas.alpha_composite(vgrad((W, H), (0, 0, 0), 0, 220, 110, 0))
        canvas.alpha_composite(vgrad((W, H), theme["bg"], H * 0.38, H * 0.74, 0, 245))
    elif item_imgs:
        bg = cover_crop(item_imgs[0], (W, H)).filter(ImageFilter.GaussianBlur(40))
        canvas.paste(bg, (0, 0))
        canvas.alpha_composite(Image.new("RGBA", (W, H), theme["bg"] + (205,)))
        spots = [(300, 430, -7), (790, 400, 6), (560, 520, -1)]
        widths = [330, 330, 360]
        order = [0, 1, 2][:len(item_imgs)]
        for i in order[:-1] + order[-1:]:
            x, y, a = spots[i] if len(item_imgs) > 1 else (W // 2, 470, -3)
            paste_center(canvas, poster_card(item_imgs[i], widths[i], a), x, y)
        canvas.alpha_composite(vgrad((W, H), theme["bg"], H * 0.48, H * 0.66, 0, 255))
    elif wide_imgs:
        im = wide_imgs[0]
        canvas.paste(cover_crop(im, (W, H)).filter(ImageFilter.GaussianBlur(40)), (0, 0))
        canvas.alpha_composite(Image.new("RGBA", (W, H), theme["bg"] + (150,)))
        fw = W - 2 * M
        fh = min(int(fw * im.height / im.width), 420)
        fw = int(fh * im.width / im.height)
        canvas.alpha_composite(im.resize((fw, fh), Image.LANCZOS).convert("RGBA"), ((W - fw) // 2, 150))
        canvas.alpha_composite(vgrad((W, H), theme["bg"], H * 0.45, H * 0.62, 0, 255))
    else:
        canvas = placeholder_bg((W, H), accent, theme)

    d = ImageDraw.Draw(canvas)
    d.text((M, 60), brand, font=font(EB, 28), fill=theme["fg"] + (230,))
    date = post.publish_at.strftime("%m.%d")
    d.text((W - M, 60), date, font=font(B, 28), fill=theme["fg"] + (200,), anchor="ra")

    # 아래에서 위로 쌓기: 부제 → 제목 → 라벨 → 말풍선
    y_bottom = H - 140
    sub_f = font(B, 38)
    sub_lines = wrap(post.subtitle, sub_f, W - M * 2) if post.subtitle else []
    sub_h = block_h(sub_f, sub_lines)
    title_f, title_lines = fit(post.title, EB, W - M * 2, 4, 104, 64)
    title_h = block_h(title_f, title_lines)

    y_sub = y_bottom - sub_h
    y_title = y_sub - (24 if sub_lines else 0) - title_h
    y_label = y_title - 70

    if post.bubble:
        b = bubble_layer(post.bubble)
        paste_center(canvas, b, W // 2, y_label - 30 - b.height // 2)
        d = ImageDraw.Draw(canvas)

    pill(d, M, y_label, post.label, font(EB, 26), accent, (15, 15, 15))
    draw_lines(d, title_lines, title_f, M, y_title, theme["fg"])
    for i, ln in enumerate(sub_lines):
        d.text((M, y_sub + i * line_h(sub_f)), ln, font=sub_f, fill=accent if post.theme == "dark" else theme["sub"])

    footer(canvas, theme, brand)
    return canvas.convert("RGB")


# ---------------------------------------------------------------- 작품 카드

def render_item(post: Post, item: Item, idx: int, total: int, config: dict) -> Image.Image:
    theme = THEMES[post.theme]
    accent = hex2rgb(config.get("labels", {}).get(post.label, "#FF4D4D"))
    brand = config.get("brand", "SCREEN DAILY")
    # 글자 블록을 아래에 붙이고, 남는 위쪽 전체를 사진으로 채운다
    tf, tl = fit(item.title, EB, W - M * 2, 2, 80, 52)
    df = font(R, 38)
    dl = fit(item.desc, R, W - M * 2, 4, 38, 38)[1] if item.desc else []
    meta_h = 80 if (item.ott or item.genre) else 0
    text_h = meta_h + block_h(tf, tl) + (16 + block_h(df, dl) if dl else 0)
    y0 = H - 150 - text_h  # 글자 블록 시작
    img_h = y0 + 40

    canvas = Image.new("RGBA", (W, H), theme["bg"] + (255,))
    im = open_img(post.asset(item.image))
    if im and item.layout == "cover":
        # 공식 스틸컷: 꽉 채움
        canvas.paste(cover_crop(im, (W, img_h), (0.5, 0.4)), (0, 0))
    elif im and im.width > im.height * 1.3:
        # 가로로 긴 이미지(로고·타이틀 카드): 자르지 않고 전체를 보여줌
        bg = cover_crop(im, (W, img_h)).filter(ImageFilter.GaussianBlur(40))
        canvas.paste(bg, (0, 0))
        canvas.alpha_composite(Image.new("RGBA", (W, img_h), (0, 0, 0, 110)), (0, 0))
        fw = W - 2 * M
        fh = min(int(fw * im.height / im.width), img_h - 330)
        fw = int(fh * im.width / im.height)
        frame = im.resize((fw, fh), Image.LANCZOS).convert("RGBA")
        canvas.alpha_composite(frame, ((W - fw) // 2, max(130, (img_h - 200 - fh) // 2 + 40)))
    elif im and (im.width < 800 or im.height > im.width * 1.1):
        # 작은 이미지·세로 포스터: 흐린 배경 + 가운데 포스터
        bg = cover_crop(im, (W, img_h)).filter(ImageFilter.GaussianBlur(30))
        canvas.paste(bg, (0, 0))
        canvas.alpha_composite(Image.new("RGBA", (W, img_h), (0, 0, 0, 90)), (0, 0))
        pw = min(420, int((img_h - 170) / 1.42))
        if im.width > im.height:  # 작은 가로 이미지
            frame = cover_crop(im, (W - 2 * M, int((W - 2 * M) * 0.56)), (0.5, 0.5)).convert("RGBA")
            canvas.alpha_composite(frame, (M, max(120, (img_h - frame.height) // 2 - 60)))
        else:
            paste_center(canvas, poster_card(im, pw, -2 if idx % 2 else 2), W // 2 + 140, img_h // 2 - 20)
    elif im:
        canvas.paste(cover_crop(im, (W, img_h), (0.5, 0.3)), (0, 0))
    else:
        canvas.alpha_composite(placeholder_bg((W, img_h), accent, theme, idx), (0, 0))
    canvas.alpha_composite(vgrad((W, H), theme["bg"], y0 - 320, y0 + 20, 0, 255))
    canvas.alpha_composite(vgrad((W, H), (0, 0, 0), 0, 160, 90, 0))

    d = ImageDraw.Draw(canvas)
    d.text((M, 60), brand, font=font(EB, 28), fill=(255, 255, 255, 230))
    if item.credit:
        d.text((W - M, 64), item.credit, font=font(R, 22), fill=(255, 255, 255, 200), anchor="ra",
               stroke_width=2, stroke_fill=(0, 0, 0, 120))
    d.text((M - 4, y0 - 190), f"{idx:02d}", font=font(EB, 150), fill=accent)

    if item.bubble:
        b = bubble_layer(item.bubble, size=36, angle=2.5)
        paste_center(canvas, b, W - M - b.width // 2 + 10, y0 - 110)
        d = ImageDraw.Draw(canvas)

    y, x = y0, M
    if item.ott:
        box = pill(d, x, y, item.ott, font(EB, 26), accent, (15, 15, 15))
        x = box[2] + 18
    if item.genre:
        d.text((x, y + 12), item.genre, font=font(B, 28), fill=theme["sub"])
    y += meta_h
    y = draw_lines(d, tl, tf, M, y, theme["fg"]) + 16
    draw_lines(d, dl, df, M, y, theme["sub"])

    footer(canvas, theme, brand, f"{idx + 1} / {total}")
    return canvas.convert("RGB")


# ---------------------------------------------------------------- 마지막 장

def render_outro(post: Post, config: dict) -> Image.Image:
    theme = THEMES[post.theme]
    accent = hex2rgb(config.get("labels", {}).get(post.label, "#FF4D4D"))
    brand = config.get("brand", "SCREEN DAILY")
    o = config.get("outro", {})
    canvas = placeholder_bg((W, H), accent, theme, 3)
    canvas.alpha_composite(Image.new("RGBA", (W, H), theme["bg"] + (90,)))
    d = ImageDraw.Draw(canvas)

    d.text((W / 2, 250), brand, font=font(EB, 34), fill=accent, anchor="ma")
    tf, tl = fit(o.get("title", "매일 한 편"), EB, W - M * 2, 4, 96, 60)
    y = draw_lines(d, tl, tf, 0, 330, theme["fg"], anchor_center=True) + 60

    cta_f = font(EB, 40)
    cta = o.get("cta", "팔로우하고 매일 추천 받기")
    bw = _tw(cta_f, cta) + 100
    d.rounded_rectangle(((W - bw) / 2, y, (W + bw) / 2, y + 104), radius=52, fill=accent)
    d.text((W / 2, y + 52), cta, font=cta_f, fill=(15, 15, 15), anchor="mm")
    y += 140
    d.text((W / 2, y), config.get("handle", ""), font=font(B, 38), fill=theme["fg"], anchor="ma")
    y += 110
    if o.get("save"):
        d.text((W / 2, y), o["save"], font=font(B, 34), fill=theme["sub"], anchor="ma")
        y += 60
    if o.get("question"):
        d.text((W / 2, y), o["question"], font=font(B, 34), fill=theme["sub"], anchor="ma")

    footer(canvas, theme, brand)
    return canvas.convert("RGB")


def render_all(post: Post, config: dict) -> list[Image.Image]:
    if post.images:
        out = []
        for rel in post.images:
            im = open_img(post.asset(rel))
            # 인스타 피드 비율(4:5 ~ 1.91:1) 밖이면 4:5 로 맞춤
            ratio = im.width / im.height
            if ratio < 0.8 or ratio > 1.91:
                im = cover_crop(im, (W, H), (0.5, 0.5))
            out.append(im)
        return out
    total = 1 + len(post.items) + (1 if post.outro else 0)
    slides = [render_cover(post, config)]
    for i, it in enumerate(post.items, 1):
        slides.append(render_item(post, it, i, total, config))
    if post.outro:
        slides.append(render_outro(post, config))
    return slides
