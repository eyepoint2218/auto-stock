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
    sp = post_splash(post, config)
    theme = THEMES["dark"] if sp else THEMES[post.theme]
    accent = hex2rgb(config.get("labels", {}).get(post.label, config.get("labels", {}).get("default", "#FF4D4D")))
    brand = config.get("brand", "SCREEN DAILY")
    canvas = Image.new("RGBA", (W, H), theme["bg"] + (255,))

    cover = open_img(post.asset(post.cover_image or post.actor_image))
    all_imgs = [open_img(post.asset(it.image)) for it in post.items if it.image]
    posters = [open_img(post.asset(it.poster)) for it in post.items if it.poster]
    item_imgs = (posters + [im for im in all_imgs if im.height >= im.width])[:3]  # 콜라주는 세로 포스터만
    wide_imgs = [im for im in all_imgs if im.height < im.width]

    if cover and post.reveal and not post.cover_image:
        # 배우 맞히기: 알아볼 수 없게 아주 흐린 실루엣 + 큰 물음표
        canvas.paste(cover_crop(cover, (W, H), (0.5, 0.2)).filter(ImageFilter.GaussianBlur(75)), (0, 0))
        canvas.alpha_composite(Image.new("RGBA", (W, H), (10, 10, 12, 120)))
        ImageDraw.Draw(canvas).text((W / 2, H * 0.30), "?", font=font(EB, 520), fill=accent + (235,), anchor="mm")
        canvas.alpha_composite(vgrad((W, H), theme["bg"], H * 0.45, H * 0.72, 0, 245))
    elif cover:
        canvas.paste(cover_crop(cover, (W, H), (0.5, 0.2 if post.actor_image else 0.35)), (0, 0))
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
    elif sp:
        canvas = splash_bg(sp["splash"], 0)
    else:
        canvas = placeholder_bg((W, H), accent, theme)

    d = ImageDraw.Draw(canvas)
    d.text((M, 60), brand, font=font(EB, 28), fill=theme["fg"] + (230,))
    date = post.publish_at.strftime("%m.%d")
    d.text((W - M, 60), date, font=font(B, 28), fill=theme["fg"] + (200,), anchor="ra")
    if post.actor_image and not post.cover_image:
        d.text((W - M, 100), "사진 © TMDB", font=font(R, 22), fill=(255, 255, 255, 200), anchor="ra",
               stroke_width=2, stroke_fill=(0, 0, 0, 120))

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
        bx = W - M - b.width // 2 + 10 if post.actor_image else W // 2
        paste_center(canvas, b, bx, y_label - 30 - b.height // 2)
        d = ImageDraw.Draw(canvas)

    if sp:  # 흰 라벨 + 연보라 부제
        pill(d, M, y_label, post.label, font(EB, 26), (255, 255, 255), hex2rgb(sp.get("accent", "#3818C9")))
        sub_c = hex2rgb(sp["splash"].get("soft", "#B3A6F2"))
        sub_c = tuple(min(255, int(c * 0.5 + 255 * 0.5)) for c in sub_c)
    else:
        pill(d, M, y_label, post.label, font(EB, 26), accent, (15, 15, 15))
        sub_c = accent if post.theme == "dark" else theme["sub"]
    draw_lines(d, title_lines, title_f, M, y_title, theme["fg"])
    for i, ln in enumerate(sub_lines):
        d.text((M, y_sub + i * line_h(sub_f)), ln, font=sub_f, fill=sub_c)

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
    meta_h = 80 if (item.ott or item.genre or item.stage) else 0
    rf = font(B, 34)
    role_txt = f"‘{item.role}’ 역" if item.role else ""
    role_h = line_h(rf) + 6 if role_txt else 0
    text_h = meta_h + block_h(tf, tl) + role_h + (16 + block_h(df, dl) if dl else 0)
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
    d.text((M - 4, y0 - 190), item.year or f"{idx:02d}", font=font(EB, 150), fill=accent)

    if item.bubble:
        b = bubble_layer(item.bubble, size=36, angle=2.5)
        paste_center(canvas, b, W - M - b.width // 2 + 10, y0 - 110)
        d = ImageDraw.Draw(canvas)

    y, x = y0, M
    if item.stage:
        box = pill(d, x, y, item.stage, font(EB, 26), accent, (15, 15, 15))
        x = box[2] + 18
        meta = " · ".join(t for t in (item.ott, item.genre) if t)
        if meta:
            d.text((x, y + 12), meta, font=font(B, 28), fill=theme["sub"])
    elif item.ott:
        box = pill(d, x, y, item.ott, font(EB, 26), accent, (15, 15, 15))
        x = box[2] + 18
    if item.genre and not item.stage:
        d.text((x, y + 12), item.genre, font=font(B, 28), fill=theme["sub"])
    y += meta_h
    y = draw_lines(d, tl, tf, M, y, theme["fg"])
    if role_txt:
        d.text((M, y + 2), role_txt, font=rf, fill=accent)
        y += role_h
    y += 16
    draw_lines(d, dl, df, M, y, theme["sub"])

    footer(canvas, theme, brand, f"{idx + 1} / {total}")
    return canvas.convert("RGB")


# ---------------------------------------------------------------- 마지막 장

def render_outro(post: Post, config: dict) -> Image.Image:
    theme = THEMES[post.theme]
    accent = hex2rgb(config.get("labels", {}).get(post.label, "#FF4D4D"))
    brand = config.get("brand", "SCREEN DAILY")
    o = config.get("outro", {})
    sp = post_splash(post, config)
    cta_fg = (15, 15, 15)
    if sp:  # 흰 버튼 + 진한 글씨
        theme = THEMES["dark"]
        canvas = splash_bg(sp["splash"], 1)
        cta_fg, accent = hex2rgb(sp.get("accent", "#3818C9")), (255, 255, 255)
    else:
        canvas = placeholder_bg((W, H), accent, theme, 3)
        canvas.alpha_composite(Image.new("RGBA", (W, H), theme["bg"] + (90,)))
    d = ImageDraw.Draw(canvas)

    d.text((W / 2, 250), brand, font=font(EB, 34), fill=accent, anchor="ma")
    tf, tl = fit(post.outro_title or o.get("title", "매일 한 편"), EB, W - M * 2, 4, 96, 60)
    y = draw_lines(d, tl, tf, 0, 330, theme["fg"], anchor_center=True) + 60

    cta_f = font(EB, 40)
    cta = post.outro_cta or o.get("cta", "팔로우하고 매일 추천 받기")
    bw = _tw(cta_f, cta) + 100
    d.rounded_rectangle(((W - bw) / 2, y, (W + bw) / 2, y + 104), radius=52, fill=accent)
    d.text((W / 2, y + 52), cta, font=cta_f, fill=cta_fg, anchor="mm")
    y += 140
    d.text((W / 2, y), config.get("handle", ""), font=font(B, 38), fill=theme["fg"], anchor="ma")
    y += 110
    save = post.outro_save or o.get("save")
    if save:
        d.text((W / 2, y), save, font=font(B, 34), fill=theme["sub"], anchor="ma")
        y += 60
    question = post.outro_question or o.get("question")
    if question:
        d.text((W / 2, y), question, font=font(B, 34), fill=theme["sub"], anchor="ma")

    footer(canvas, theme, brand)
    return canvas.convert("RGB")


# ---------------------------------------------------------------- 인생 이야기 카드

def _story_bg(post: Post, theme, accent, idx: int, blur: float = 28, dark: int = 200) -> Image.Image:
    """배우 사진을 흐리게 깐 어두운 배경 (사진이 없으면 그라데이션)."""
    im = open_img(post.asset(post.actor_image)) if post.actor_image else None
    if im:
        bg = cover_crop(im, (W, H), (0.5, 0.25)).filter(ImageFilter.GaussianBlur(blur)).convert("RGBA")
        bg.alpha_composite(Image.new("RGBA", (W, H), (10, 10, 12, dark)))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((-W * 0.3, -H * 0.2, W * 0.7, H * 0.45), fill=accent + (60,))
        bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
        return bg
    return placeholder_bg((W, H), accent, THEMES["dark"], idx)


def _brand_bg(glows: list[tuple[int, int, int]]) -> Image.Image:
    """브랜드 색 빛이 위쪽에서 번지는 어두운 배경 (색이 2개면 좌우로 섞임)."""
    bg = Image.new("RGBA", (W, H), (12, 12, 14, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    spots = [(-0.15, 0.55)] if len(glows) == 1 else [(-0.25, 0.45), (0.45, 1.2)]
    for (x0, x1), c in zip(spots, glows):
        gd.ellipse((W * x0, -H * 0.45, W * x1, H * 0.55), fill=c + (190,))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(170)))
    return bg


def _ink(rgb) -> tuple[int, int, int]:
    """배경색 위에 읽히는 글자색 (밝으면 검정, 어두우면 흰색)."""
    r, g, b = rgb
    return (15, 15, 15) if (0.299 * r + 0.587 * g + 0.114 * b) > 160 else (255, 255, 255)


def splash_bg(sp: dict, seed: int = 0) -> Image.Image:
    """진한 바탕 + 아래쪽 강한 빛 + 모서리 옅은 빛 (앱 시작 화면 느낌). 장마다 빛 위치를 조금씩 바꿈."""
    canvas = Image.new("RGBA", (W, H), hex2rgb(sp.get("base", "#3818C9")) + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    hot, soft = hex2rgb(sp.get("hot", "#FF3E4A")), hex2rgb(sp.get("soft", "#B3A6F2"))
    dy = ((seed * 37) % 5 - 2) * 0.05
    if seed % 2 == 0:
        gd.ellipse((-W * 0.75, H * (0.32 + dy), W * 0.3, H * (1.05 + dy)), fill=hot + (255,))
        gd.ellipse((W * 0.75, -H * 0.25, W * 1.5, H * 0.2), fill=soft + (200,))
        gd.ellipse((W * 0.55, H * 0.85, W * 1.5, H * 1.4), fill=soft + (230,))
    else:  # 좌우 뒤집기
        gd.ellipse((W * 0.7, H * (0.32 + dy), W * 1.75, H * (1.05 + dy)), fill=hot + (255,))
        gd.ellipse((-W * 0.5, -H * 0.25, W * 0.25, H * 0.2), fill=soft + (200,))
        gd.ellipse((-W * 0.5, H * 0.85, W * 0.45, H * 1.4), fill=soft + (230,))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(150)))
    return canvas


def post_splash(post: Post, config: dict) -> dict | None:
    """캐러셀 전체 색(post.brand)의 brands 설정. splash 가 있을 때만."""
    b = (config.get("brands") or {}).get(post.brand.upper()) if post.brand else None
    return b if b and b.get("splash") else None


def render_panel_story(post: Post, item: Item, idx: int, total: int, config: dict, bcfg: dict) -> Image.Image:
    """밝은 하늘색 배경 + 진한 남보라 큰 글씨 + 흰 둥근 패널 (멤버십 앱 이벤트 페이지 느낌).
    desc 에서 "18 수 | 뚜레쥬르 · CGV" 처럼 | 가 있는 줄은 달력 줄(왼쪽 날짜, 오른쪽 내용)로 그린다."""
    ink = hex2rgb(bcfg.get("accent", "#3B1FD6"))
    top, bot = hex2rgb(bcfg.get("bg", "#A8DCF6")), hex2rgb(bcfg.get("bg2", "#E4F4FC"))
    dark, sub = (24, 24, 40), (70, 72, 92)
    if bcfg.get("splash"):
        canvas = splash_bg(bcfg["splash"], idx)
        fg = dark = (255, 255, 255)
    else:
        grad = Image.linear_gradient("L").resize((W, H))
        canvas = Image.composite(Image.new("RGBA", (W, H), bot + (255,)), Image.new("RGBA", (W, H), top + (255,)), grad)
        fg = ink
    hd = ImageDraw.Draw(canvas)
    brand = config.get("brand", "SCREEN DAILY")
    hd.text((M, 60), brand, font=font(EB, 28), fill=fg)
    hd.text((W - M, 64), bcfg.get("name", item.brand), font=font(EB, 28), fill=fg, anchor="ra")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # 내용은 따로 그린 뒤 세로 가운데로 옮김
    d = ImageDraw.Draw(layer)

    y = 150
    if item.year:
        yf = font(EB, 200)
        while _tw(yf, item.year) > W - M * 2 and yf.size > 120:
            yf = font(EB, yf.size - 10)
        d.text((M - 6, y - 30), item.year, font=yf, fill=fg)
        y += int(yf.size * 1.0)
    if item.stage:  # 테두리만 있는 알약 라벨
        sf_ = font(EB, 32)
        tw = _tw(sf_, item.stage)
        box = (M, y, int(M + tw + 52), y + 32 + 28)
        d.rounded_rectangle(box, radius=30, fill=(255, 255, 255), outline=ink, width=4)
        d.text((M + 26, y + 15), item.stage, font=sf_, fill=ink)
        y = box[3] + 34
    hf, hl = fit(item.title, EB, W - M * 2, 3, 76, 56)
    y = draw_lines(d, hl, hf, M, y, dark) + 36
    dark = (24, 24, 40)  # 여기부터는 흰 패널 안 글씨

    rows, notes = [], []
    for ln in (item.desc or "").split("\n"):
        if "|" in ln:
            a, b = ln.split("|", 1)
            rows.append((a.strip(), b.strip()))
        elif ln.strip():
            notes.append(ln.strip())
    # 패널 안 내용 높이를 먼저 계산해서 패널을 내용에 맞춘다
    px0, px1 = M - 16, W - M + 16
    px, pw = px0 + 40, px1 - px0 - 80
    head_h = 64 if bcfg.get("panel_title") else 0
    df_, rf, nf = font(EB, 64), font(B, 38), font(R, 38)
    col = (max(_tw(df_, a.split()[0]) for a, _ in rows) + 70) if rows else 0
    row_ls = [wrap(b, rf, pw - col) for _, b in rows]
    rows_h = sum(max(line_h(df_), 8 + block_h(rf, bl)) + 44 for bl in row_ls)
    max_bottom = H - 150
    room = max_bottom - y - head_h - 36 - rows_h - 36
    if notes:
        nf, nl = fit("\n".join(notes), R, pw, max(1, room // line_h(nf)), 38, 30)
    else:
        nl = []
    panel_h = head_h + 36 + rows_h + (block_h(nf, nl) + 10 if nl else 0) + 26
    panel = (px0, y, px1, min(max_bottom, y + panel_h))
    d.rounded_rectangle(panel, radius=40, fill=(255, 255, 255))
    py = panel[1]
    if head_h:  # 달력 머리줄 + 남보라 굵은 선
        d.text((px, py + 18), bcfg["panel_title"], font=font(EB, 30), fill=ink)
        py += head_h
        d.line((panel[0], py, panel[2], py), fill=ink, width=5)
    py += 36
    for i, ((a, _), bl) in enumerate(zip(rows, row_ls)):
        if i:
            d.line((px, py - 22, px + pw, py - 22), fill=(220, 222, 236), width=2)
        num, *rest = a.split()
        d.text((px, py), num, font=df_, fill=ink)
        if rest:
            d.text((px + _tw(df_, num) + 8, py + 30), " ".join(rest), font=font(B, 28), fill=ink)
        yy = draw_lines(d, bl, rf, px + col, py + 8, dark)
        py = max(py + line_h(df_), yy) + 44
    if nl:
        draw_lines(d, nl, nf, px, py, sub)
    shift = max(0, (H - 150 - panel[3]) // 2)
    canvas.alpha_composite(layer, (0, shift))
    panel = (panel[0], panel[1] + shift, panel[2], panel[3] + shift)
    d = hd

    if item.bubble:
        b = bubble_layer(item.bubble, size=34, angle=2.5)
        paste_center(canvas, b, W - M - b.width // 2 + 10, panel[1] - 10)
    d.line((M, H - 96, W - M, H - 96), fill=fg + (110,), width=2)
    d.text((W / 2, H - 70), brand, font=font(B, 26), fill=fg, anchor="ma")
    d.text((W - M, H - 70), f"{idx + 1} / {total}", font=font(R, 26), fill=fg, anchor="ra")
    return canvas.convert("RGB")


def render_story(post: Post, item: Item, idx: int, total: int, config: dict) -> Image.Image:
    """연도 + 헤드라인 + 본문으로 읽히는 이야기 카드. item.type == "quote" 면 인용 카드."""
    theme = THEMES["dark"]
    accent = hex2rgb(config.get("labels", {}).get(post.label, "#FF4D4D"))
    brand = config.get("brand", "SCREEN DAILY")
    bcfg = (config.get("brands") or {}).get(item.brand.upper()) if item.brand else None
    if not bcfg and post_splash(post, config):  # brand 없는 카드는 캐러셀 전체 색, 이름·머리줄 없이
        bcfg = dict(post_splash(post, config), name="", panel_title="")
    if bcfg and bcfg.get("style") == "panel" and item.type != "quote":
        return render_panel_story(post, item, idx, total, config, bcfg)
    if bcfg:
        accent = hex2rgb(bcfg.get("accent", "#FF4D4D"))
        glows = [hex2rgb(c) for c in (bcfg.get("glow") or [bcfg.get("accent", "#FF4D4D")])][:2]
        canvas = _brand_bg(glows)
    elif post.reveal:
        # 넘길수록 점점 선명해짐 (정답 공개 직전까지 알아보기 어렵게)
        n = max(1, len(post.items))
        t = (idx - 1) / max(1, n - 1)
        canvas = _story_bg(post, theme, accent, idx, blur=70 - 45 * t, dark=int(215 - 40 * t))
    else:
        canvas = _story_bg(post, theme, accent, idx)
    d = ImageDraw.Draw(canvas)
    d.text((M, 60), brand, font=font(EB, 28), fill=(255, 255, 255, 230))
    if bcfg:
        d.text((W - M, 64), bcfg.get("name", item.brand), font=font(EB, 28), fill=(255, 255, 255, 235), anchor="ra")
    elif post.reveal:
        d.text((W - M, 64), "이 배우는 누구?", font=font(B, 26), fill=accent, anchor="ra")
    elif post.actor_name or post.actor:
        d.text((W - M, 64), post.actor_name or post.actor, font=font(B, 26), fill=(255, 255, 255, 190), anchor="ra")

    top, bottom = 150, H - 150  # 글을 놓을 수 있는 영역
    if item.type == "quote":
        mark_h = 150
        qf, ql = fit(item.title, EB, W - M * 2, 5, 76, 50)
        df = font(R, 40)
        dl = fit(item.desc, R, W - M * 2, 6, 40, 40)[1] if item.desc else []
        src = " · ".join(t for t in (item.year, item.stage) if t)
        h = mark_h + block_h(qf, ql) + (40 + block_h(df, dl) if dl else 0) + (70 if src else 0)
        y = max(top, top + (bottom - top - h) // 2)
        d.text((M - 6, y - 60), "\u201c", font=font(EB, 240), fill=accent)
        y = draw_lines(d, ql, qf, M, y + mark_h, theme["fg"])
        if dl:
            y = draw_lines(d, dl, df, M, y + 40, theme["sub"])
        if src:
            d.text((M, y + 40), "— " + src, font=font(B, 32), fill=accent)
    else:
        yf, sf_ = font(EB, 170), font(EB, 28)
        hf, hl = fit(item.title, EB, W - M * 2, 3, 80, 56)
        df = font(R, 42)
        room = bottom - top - (210 if item.year else 0) - (80 if item.stage else 0) - block_h(hf, hl) - 36
        dl = fit(item.desc, R, W - M * 2, max(2, room // line_h(df)), 42, 42)[1] if item.desc else []
        h = (210 if item.year else 0) + (80 if item.stage else 0) + block_h(hf, hl) + (36 + block_h(df, dl) if dl else 0)
        y = max(top, top + (bottom - top - h) // 2)
        if item.year:
            d.text((M - 4, y - 20), item.year, font=yf, fill=(255, 255, 255) if bcfg else accent)
            y += 210
        if item.stage:
            box = pill(d, M, y, item.stage, sf_, accent, _ink(accent) if bcfg else (15, 15, 15))
            y = box[3] + 30
        y = draw_lines(d, hl, hf, M, y, theme["fg"])
        if dl:
            draw_lines(d, dl, df, M, y + 36, theme["sub"])

    if item.bubble:
        b = bubble_layer(item.bubble, size=34, angle=2.5)
        paste_center(canvas, b, W - M - b.width // 2 + 10, H - 210)
    footer(canvas, theme, brand, f"{idx + 1} / {total}")
    return canvas.convert("RGB")


def render_reveal(post: Post, idx: int, total: int, config: dict) -> Image.Image:
    """정답 공개 카드: 선명한 배우 사진 + 이름."""
    theme = THEMES["dark"]
    accent = hex2rgb(config.get("labels", {}).get(post.label, "#FF4D4D"))
    brand = config.get("brand", "SCREEN DAILY")
    canvas = Image.new("RGBA", (W, H), theme["bg"] + (255,))
    im = open_img(post.asset(post.actor_image)) if post.actor_image else None
    if im:
        canvas.paste(cover_crop(im, (W, H), (0.5, 0.2)), (0, 0))
        canvas.alpha_composite(vgrad((W, H), (0, 0, 0), 0, 220, 110, 0))
        canvas.alpha_composite(vgrad((W, H), theme["bg"], H * 0.5, H * 0.8, 0, 245))
    else:
        canvas = placeholder_bg((W, H), accent, theme, idx)
    d = ImageDraw.Draw(canvas)
    d.text((M, 60), brand, font=font(EB, 28), fill=(255, 255, 255, 230))
    if im:
        d.text((W - M, 64), "사진 © TMDB", font=font(R, 22), fill=(255, 255, 255, 200), anchor="ra",
               stroke_width=2, stroke_fill=(0, 0, 0, 120))
    name = post.actor_name or post.actor
    nf, nl = fit(name, EB, W - M * 2, 1, 150, 90)
    sub_f = font(B, 38)
    sub = wrap(post.reveal_text, sub_f, W - M * 2) if post.reveal_text else []
    y = H - 150 - block_h(sub_f, sub) - (24 if sub else 0) - block_h(nf, nl)
    pill(d, M, y - 80, "정답은", font(EB, 30), accent, (15, 15, 15))
    y = draw_lines(d, nl, nf, M, y, theme["fg"])
    for i, ln in enumerate(sub):
        d.text((M, y + 24 + i * line_h(sub_f)), ln, font=sub_f, fill=accent)
    b = bubble_layer("맞히셨나요?", size=38, angle=-3)
    paste_center(canvas, b, W - M - b.width // 2 + 10, y - 200)
    footer(canvas, theme, brand, f"{idx + 1} / {total}")
    return canvas.convert("RGB")


def render_recommend(post: Post, idx: int, total: int, config: dict) -> Image.Image:
    """정답 뒤 '이 배우 작품, 여기서 보세요' 카드: 포스터 2~4편."""
    theme = THEMES["dark"]
    accent = hex2rgb(config.get("labels", {}).get(post.label, "#FF4D4D"))
    brand = config.get("brand", "SCREEN DAILY")
    canvas = _story_bg(post, theme, accent, idx, blur=40, dark=215)
    d = ImageDraw.Draw(canvas)
    d.text((M, 60), brand, font=font(EB, 28), fill=(255, 255, 255, 230))
    name = post.actor_name or post.actor
    title = post.recommend_title or f"{name},\n이 작품에서 만나요"
    tf, tl = fit(title, EB, W - M * 2, 2, 76, 56)
    y = draw_lines(d, tl, tf, M, 150, theme["fg"]) + 50

    recs = post.recommend
    n = len(recs)
    gap = 28
    pw = int((W - M * 2 - gap * (n - 1)) / n) if n >= 3 else 380
    ph = int(pw * 1.45)
    x0 = (W - (pw * n + gap * (n - 1))) // 2
    for i, it in enumerate(recs):
        x = x0 + i * (pw + gap)
        src = open_img(post.asset(it.poster or it.image))
        if src:
            card = cover_crop(src, (pw, ph), (0.5, 0.3)).convert("RGBA")
        else:
            card = placeholder_bg((pw, ph), accent, theme, i)
        mask = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw, ph), 18, fill=255)
        sh = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((20, 26, pw + 20, ph + 26), 18, fill=(0, 0, 0, 140))
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (x - 20, y - 20))
        canvas.paste(card, (x, y), mask)
        d = ImageDraw.Draw(canvas)
        ty = y + ph + 22
        f1 = fit(it.title, EB, pw, 2, 34 if n >= 3 else 40, 24)
        ty = draw_lines(d, f1[1], f1[0], x, ty, theme["fg"]) + 4
        meta = " · ".join(t for t in ((f"‘{it.role}’ 역" if it.role else ""), it.ott) if t)
        if meta:
            mf = fit(meta, B, pw, 2, 26, 20)
            draw_lines(d, mf[1], mf[0], x, ty, accent)

    d.text((W / 2, H - 150), "저장해두고 하나씩 정주행", font=font(B, 32), fill=theme["sub"], anchor="ma")
    d.text((W - M, 64), "이미지 © TMDB", font=font(R, 22), fill=(255, 255, 255, 190), anchor="ra")
    footer(canvas, theme, brand, f"{idx + 1} / {total}")
    return canvas.convert("RGB")


# ---------------------------------------------------------------- 할인 카드 (사진 + 두 줄)

DEAL_YELLOW = (255, 214, 0)


def _deal_canvas(post: Post, img_path: str, bcfg: dict | None, seed: int) -> Image.Image:
    """사진이 있으면 꽉 채우고 아래를 어둡게, 없으면 브랜드 splash 배경."""
    im = open_img(post.asset(img_path)) if img_path else None
    if im:
        canvas = cover_crop(im, (W, H), (0.5, 0.45)).convert("RGBA")
        canvas.alpha_composite(vgrad((W, H), (0, 0, 0), 0, 260, 120, 0))
        canvas.alpha_composite(vgrad((W, H), (0, 0, 0), H * 0.42, H * 0.86, 0, 235))
        return canvas
    if bcfg and bcfg.get("splash"):
        return splash_bg(bcfg["splash"], seed)
    return placeholder_bg((W, H), (255, 77, 77), THEMES["dark"], seed)


def _deal_text(canvas: Image.Image, lines: list[tuple[str, tuple]], chip: str, chip_c, date: str, config: dict,
               page: str = ""):
    """아래쪽에 큰 두 줄(흰색 + 노란색), 위쪽에 통신사·날짜 칩, 맨 아래 작은 워터마크."""
    d = ImageDraw.Draw(canvas)
    d.text((W - M, 62), config.get("brand", "SCREEN DAILY"), font=font(EB, 26), fill=(255, 255, 255, 220), anchor="ra")
    x = M
    if chip:
        box = pill(d, x, 52, chip, font(EB, 32), chip_c, _ink(chip_c), pad=(24, 14))
        x = box[2] + 14
    if date:
        f = font(EB, 32)
        tw = _tw(f, date)
        d.rounded_rectangle((x, 52, x + tw + 48, 52 + 32 + 28), radius=30, outline=(255, 255, 255), width=3)
        d.text((x + 24, 52 + 14), date, font=f, fill=(255, 255, 255))

    y = H - 150
    fonts = []
    for text, color in lines:
        f = font(EB, 100)
        while _tw(f, text) > W - M * 2 and f.size > 56:
            f = font(EB, f.size - 4)
        fonts.append(f)
    total = sum(line_h(f) for f in fonts)
    y -= total
    for (text, color), f in zip(lines, fonts):
        d.text((M, y), text, font=f, fill=color, stroke_width=2, stroke_fill=(0, 0, 0, 90))
        y += line_h(f)
    # 워터마크 (가는 선 + 계정)
    hy = H - 72
    handle = config.get("handle", "")
    hf = font(R, 24)
    hw = _tw(hf, handle)
    d.line((W / 2 - hw / 2 - 140, hy, W / 2 - hw / 2 - 20, hy), fill=(255, 255, 255, 140), width=2)
    d.line((W / 2 + hw / 2 + 20, hy, W / 2 + hw / 2 + 140, hy), fill=(255, 255, 255, 140), width=2)
    d.text((W / 2, hy), handle, font=hf, fill=(255, 255, 255, 190), anchor="mm")
    if page:
        d.text((W - M, hy), page, font=font(R, 24), fill=(255, 255, 255, 170), anchor="rm")


def _chip_color(bcfg: dict | None) -> tuple[int, int, int]:
    """통신사 칩 색: 브랜드 색이 바탕색과 비슷해 묻히면 흰색."""
    if not bcfg:
        return (255, 255, 255)
    acc = hex2rgb(bcfg.get("accent", "#FFFFFF"))
    base = hex2rgb((bcfg.get("splash") or {}).get("base", "#000000"))
    if sum(abs(a - b) for a, b in zip(acc, base)) < 120:
        return (255, 255, 255)
    return acc


def render_deal(post: Post, item: Item, idx: int, total: int, config: dict) -> Image.Image:
    """할인 카드: title(흰색) + desc(노란색) 두 줄만 크게. stage = 통신사 칩, year = 날짜 칩."""
    brands = config.get("brands") or {}
    bcfg = brands.get(item.brand.upper()) if item.brand else post_splash(post, config)
    canvas = _deal_canvas(post, item.image, bcfg, idx)
    chip_c = _chip_color(bcfg)
    lines = [(item.title, (255, 255, 255))] + ([(item.desc, DEAL_YELLOW)] if item.desc else [])
    _deal_text(canvas, lines, item.stage, chip_c, item.year, config, f"{idx + 1} / {total}")
    if item.image and item.credit:  # 사진 출처 (오른쪽 위, 작게)
        ImageDraw.Draw(canvas).text((W - M, 132), item.credit, font=font(R, 20), fill=(255, 255, 255, 200),
                                    anchor="ra", stroke_width=2, stroke_fill=(0, 0, 0, 120))
    if item.bubble:
        b = bubble_layer(item.bubble, size=36, angle=-3)
        paste_center(canvas, b, W - M - b.width // 2, H * 0.52)
    return canvas.convert("RGB")


def render_deal_cover(post: Post, config: dict) -> Image.Image:
    """할인 모음 표지: 사진(cover_image 또는 첫 카드 사진) + 제목 줄들, 마지막 줄만 노란색."""
    bcfg = post_splash(post, config)
    img = post.cover_image or next((it.image for it in post.items if it.image), "")
    canvas = _deal_canvas(post, img, bcfg, 0)
    tl = [t for t in post.title.split("\n") if t.strip()]
    lines = [(t, (255, 255, 255)) for t in tl[:-1]] + [(tl[-1], DEAL_YELLOW)] if tl else []
    _deal_text(canvas, lines, post.label, (255, 255, 255), post.subtitle, config)
    credit = next((it.credit for it in post.items if it.image == img and it.credit), "")
    if img and credit and not post.cover_image:  # 사진 출처
        ImageDraw.Draw(canvas).text((W - M, 132), credit, font=font(R, 20), fill=(255, 255, 255, 200),
                                    anchor="ra", stroke_width=2, stroke_fill=(0, 0, 0, 120))
    if post.bubble:
        b = bubble_layer(post.bubble)
        paste_center(canvas, b, W - M - b.width // 2, H * 0.5)
    return canvas.convert("RGB")


# ---------------------------------------------------------------- 혜택알람: 알림 표지 · 쿠폰 · 알람 켜기

ALARM_DEFAULT = {"base": "#3818C9", "hot": "#FF3E4A", "soft": "#B3A6F2"}


def _post_photo(post: Post) -> str:
    return post.cover_image or next((it.image for it in post.items if it.image), "")


def _post_credit(post: Post) -> str:
    img = _post_photo(post)
    return next((it.credit for it in post.items if it.image == img and it.credit), "") if not post.cover_image else ""


def _alarm_colors(post: Post, config: dict) -> tuple[dict, tuple[int, int, int]]:
    """(배경 splash, 강조색): 항상 채널 고유 색 (config 채널의 alarm:). 통신사 brand 는 라벨에만 씀."""
    a = config.get("alarm") or {}
    sp = a.get("splash") or ALARM_DEFAULT
    return sp, hex2rgb(a.get("accent") or sp["base"])


def _label_color(post: Post, config: dict, default) -> tuple[int, int, int]:
    """게시물 brand(SKT/KT/LGU)가 있으면 그 통신사 색, 없으면 채널 강조색."""
    b = (config.get("brands") or {}).get(post.brand.upper()) if post.brand else None
    return hex2rgb(b["accent"]) if b and b.get("accent") else default


def _bell(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color):
    """종 아이콘 (폰트에 없어서 직접 그림)."""
    d.pieslice((cx - r * .7, cy - r * .85, cx + r * .7, cy + r * .55), 180, 360, fill=color)
    d.rectangle((cx - r * .7, cy - r * .16, cx + r * .7, cy + r * .45), fill=color)
    d.polygon((cx - r * .7, cy + r * .3, cx - r * .95, cy + r * .62, cx + r * .95, cy + r * .62, cx + r * .7, cy + r * .3), fill=color)
    d.ellipse((cx - r * .2, cy + r * .6, cx + r * .2, cy + r * .95), fill=color)
    d.ellipse((cx - r * .12, cy - r * 1.0, cx + r * .12, cy - r * .76), fill=color)


def _app_icon(size: int, color) -> Image.Image:
    ic = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(ic)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * .26), fill=color)
    _bell(d, size / 2, size / 2, size * .32, (255, 255, 255))
    return ic


def render_alarm_cover(post: Post, config: dict) -> Image.Image:
    """잠금화면 알림 표지: 위에 큰 날짜(alarm), 사진 위에 혜택알람 푸시 알림 카드.
    title 첫 줄 = 브랜드(굵게), 둘째 줄 = 혜택(강조색 크게), subtitle = 알림 본문."""
    sp, acc = _alarm_colors(post, config)
    im = open_img(post.asset(_post_photo(post))) if _post_photo(post) else None
    canvas = cover_crop(im, (W, H), (0.5, 0.5)).convert("RGBA") if im else splash_bg(sp, 0)
    canvas.alpha_composite(vgrad((W, H), (0, 0, 0), 0, 560, 175, 0))
    canvas.alpha_composite(vgrad((W, H), (0, 0, 0), H * 0.55, H, 0, 150))
    d = ImageDraw.Draw(canvas)
    if post.alarm_sub:
        d.text((W / 2, 110), post.alarm_sub, font=font(B, 40), fill=(255, 255, 255, 235), anchor="ma")
    if post.alarm:
        bf = font(EB, 230)
        while _tw(bf, post.alarm) > W - 80 and bf.size > 120:
            bf = font(EB, bf.size - 10)
        d.text((W / 2, 170), post.alarm, font=bf, fill=(255, 255, 255), anchor="ma")

    # 알림 카드 (뒤에 한 장 더 겹쳐 보이게)
    lines = [t for t in post.title.split("\n") if t.strip()]
    head, rest = (lines[0], lines[1:]) if lines else ("", [])
    cx0, cx1 = 48, W - 48
    pad = 40
    hf, rf_, sf = font(EB, 56), font(EB, 92), font(R, 36)
    rest_f = []
    for t in rest:
        f = rf_
        while _tw(f, t) > cx1 - cx0 - 2 * pad and f.size > 50:
            f = font(EB, f.size - 4)
        rest_f.append(f)
    body = wrap(post.subtitle, sf, cx1 - cx0 - 2 * pad) if post.subtitle else []
    ch = pad + 64 + 26 + line_h(hf) + sum(line_h(f) for f in rest_f) + (12 + block_h(sf, body) if body else 0) + pad
    cy0 = min(H - 170 - ch, 700)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((cx0 + 34, cy0 + 40, cx1 - 34, cy0 + ch + 30), radius=44, fill=(255, 255, 255, 120))
    cd.rounded_rectangle((cx0, cy0, cx1, cy0 + ch), radius=44, fill=(255, 255, 255, 240))
    canvas.alpha_composite(card)
    canvas.alpha_composite(_app_icon(64, acc), (cx0 + pad, cy0 + pad))
    d = ImageDraw.Draw(canvas)
    d.text((cx0 + pad + 84, cy0 + pad + 32), f"{config.get('brand', '')} · {post.label_text}" if post.label_text else config.get("brand", ""),
           font=font(B, 30), fill=(90, 90, 100), anchor="lm")
    d.text((cx1 - pad, cy0 + pad + 32), "지금", font=font(R, 28), fill=(140, 140, 150), anchor="rm")
    y = cy0 + pad + 64 + 26
    d.text((cx0 + pad, y), head, font=hf, fill=(20, 20, 26))
    y += line_h(hf)
    for t, f in zip(rest, rest_f):
        d.text((cx0 + pad, y - 6), t, font=f, fill=acc)
        y += line_h(f)
    if body:
        draw_lines(d, body, sf, cx0 + pad, y + 12, (80, 80, 90))
    if post.bubble:
        b = bubble_layer(post.bubble, size=38, angle=-3)
        paste_center(canvas, b, cx1 - b.width // 2, cy0 - 10)
    d = ImageDraw.Draw(canvas)
    credit = _post_credit(post)
    if credit:
        d.text((W - M, H - 112), credit, font=font(R, 20), fill=(255, 255, 255, 190), anchor="ra",
               stroke_width=2, stroke_fill=(0, 0, 0, 120))
    d.text((W / 2, H - 70), config.get("handle", ""), font=font(B, 28), fill=(255, 255, 255, 220), anchor="mm")
    return canvas.convert("RGB")


def render_coupon(post: Post, item: Item, idx: int, total: int, config: dict) -> Image.Image:
    """쿠폰 티켓: 위(stage 라벨 · year 큰 숫자 · title) / 절취선 / 아래 desc 의 "항목 | 내용" 표."""
    sp, acc = _alarm_colors(post, config)
    canvas = splash_bg(sp, idx)
    d = ImageDraw.Draw(canvas)
    d.text((M, 62), config.get("brand", ""), font=font(EB, 30), fill=(255, 255, 255, 235))
    d.text((W - M, 64), f"{idx + 1} / {total}", font=font(R, 26), fill=(255, 255, 255, 190), anchor="ra")

    tx0, tx1 = 64, W - 64
    pad = 48
    rows = []
    for ln in (item.desc or "").split("\n"):
        if "|" in ln:
            k, v = ln.split("|", 1)
            rows.append((k.strip(), v.strip()))
        elif ln.strip():
            rows.append(("", ln.strip()))
    kf, vf = font(EB, 30), font(B, 38)
    kw = max([_tw(kf, k) for k, _ in rows if k] + [60]) + 40
    vlines = [wrap(v, vf, tx1 - tx0 - 2 * pad - (kw + 24 if k else 0)) for k, v in rows]
    rows_h = sum(max(52, block_h(vf, vl)) + 30 for vl in vlines)
    big = font(EB, 170)
    tf, tl = fit(item.title, EB, tx1 - tx0 - 2 * pad, 2, 50, 38)
    top_h = pad + (66 if item.stage else 0) + (210 if item.year else 0) + block_h(tf, tl) + pad
    bot_h = 40 + rows_h + 10
    th = top_h + bot_h
    ty0 = max(140, (H - th) // 2 + 10)

    ticket = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(ticket)
    td.rounded_rectangle((tx0, ty0, tx1, ty0 + th), radius=36, fill=(255, 255, 255, 255))
    cut = ty0 + top_h
    td.ellipse((tx0 - 30, cut - 30, tx0 + 30, cut + 30), fill=(0, 0, 0, 0))  # 양옆 반달 홈
    td.ellipse((tx1 - 30, cut - 30, tx1 + 30, cut + 30), fill=(0, 0, 0, 0))
    for x in range(tx0 + 46, tx1 - 46, 26):  # 절취선
        td.line((x, cut, x + 13, cut), fill=(200, 200, 210), width=4)
    shadow = ticket.split()[3].point(lambda a: a * 0.35).filter(ImageFilter.GaussianBlur(18))
    canvas.paste((0, 0, 0), (0, 14), shadow)
    canvas.alpha_composite(ticket)
    d = ImageDraw.Draw(canvas)

    y = ty0 + pad
    if item.stage:  # 통신사 혜택이면 그 통신사 색 라벨
        pill(d, tx0 + pad, y, item.stage, font(EB, 30), _label_color(post, config, acc), (255, 255, 255), pad=(22, 12))
        y += 60 + 6
    if item.year:
        bf = big
        while _tw(bf, item.year) > tx1 - tx0 - 2 * pad and bf.size > 90:
            bf = font(EB, bf.size - 10)
        d.text((tx0 + pad - 6, y + 4), item.year, font=bf, fill=acc)
        y += 210
    draw_lines(d, tl, tf, tx0 + pad, y, (20, 20, 26))

    y = cut + 40
    for i, ((k, v), vl) in enumerate(zip(rows, vlines)):
        x = tx0 + pad
        if k:
            d.rounded_rectangle((x, y + 2, x + kw, y + 50), radius=24, outline=acc, width=3)
            d.text((x + kw / 2, y + 26), k, font=kf, fill=acc, anchor="mm")
            x += kw + 24
        draw_lines(d, vl, vf, x, y + 4, (30, 30, 36))
        y += max(52, block_h(vf, vl)) + 30
    d.text((W / 2, H - 70), config.get("handle", ""), font=font(B, 28), fill=(255, 255, 255, 220), anchor="mm")
    return canvas.convert("RGB")


def render_toggle_outro(post: Post, config: dict) -> Image.Image:
    """알람 켜기 마지막 장: 큰 문구 + '혜택 알람' 토글이 켜진 카드 + 아이디."""
    o = config.get("outro", {})
    sp, acc = _alarm_colors(post, config)
    canvas = splash_bg(sp, 1)
    d = ImageDraw.Draw(canvas)
    title = post.outro_title or o.get("title", "놓치면 끝나는 혜택\n알람 켜듯 팔로우하세요")
    y = 330
    for t in title.split("\n"):
        f = font(EB, 70)
        while _tw(f, t) > W - 100 and f.size > 40:
            f = font(EB, f.size - 2)
        d.text((W / 2, y), t, font=f, fill=(255, 255, 255), anchor="ma")
        y += int(f.size * 1.4)
    # 토글 카드
    cx0, cx1, cy0 = 80, W - 80, y + 70
    d.rounded_rectangle((cx0, cy0, cx1, cy0 + 190), radius=44, fill=(255, 255, 255))
    canvas.alpha_composite(_app_icon(104, acc), (cx0 + 40, cy0 + 43))
    d = ImageDraw.Draw(canvas)
    d.text((cx0 + 172, cy0 + 70), o.get("toggle_label", "혜택 알람"), font=font(EB, 46), fill=(20, 20, 26), anchor="lm")
    d.text((cx0 + 172, cy0 + 126), config.get("handle", ""), font=font(R, 32), fill=(110, 110, 120), anchor="lm")
    sx1, sy = cx1 - 40, cy0 + 95
    d.rounded_rectangle((sx1 - 150, sy - 42, sx1, sy + 42), radius=42, fill=acc)
    d.ellipse((sx1 - 78, sy - 34, sx1 - 10, sy + 34), fill=(255, 255, 255))
    d.text((W / 2, cy0 + 190 + 70), o.get("follow_sub", "혜택 날짜, 먼저 알려드려요"), font=font(B, 40),
           fill=(255, 255, 255, 235), anchor="ma")
    if o.get("save"):
        d.text((W / 2, cy0 + 190 + 140), o["save"], font=font(R, 32), fill=(255, 255, 255, 190), anchor="ma")
    d.text((W / 2, H - 90), config.get("brand", ""), font=font(EB, 40), fill=(255, 255, 255), anchor="mm")
    return canvas.convert("RGB")


# ---------------------------------------------------------------- 혜택알람 3장 고정 형식: 사진 표지 · 혜택 받는 법 · 팔로우 카드

def _page_tag(d: ImageDraw.ImageDraw, idx: int, total: int, color=(255, 255, 255, 220)):
    d.text((W - M, 64), f"{idx:02d}/{total:02d}", font=font(B, 28), fill=color, anchor="ra")


def _light(config: dict) -> dict:
    """밝은 테마 색 (채널 alarm: 설정). paper 배경, ink 글자, accent 메인, highlight 강조."""
    a = config.get("alarm") or {}
    return {"paper": hex2rgb(a.get("paper", "#FFF7EC")), "ink": hex2rgb(a.get("ink", "#1F1F24")),
            "accent": hex2rgb(a.get("accent", "#FF6B2C")), "hl": hex2rgb(a.get("cover_highlight", "#FFE14D")),
            "sp": a.get("splash") or ALARM_DEFAULT}


def _sticker(text: str, f, bg, fg, angle: float = 0, pad=(34, 18), radius: int = 26) -> Image.Image:
    """둥근 스티커 모양 글자 상자 (살짝 기울기 + 그림자)."""
    tw = _tw(f, text)
    w, h = int(tw + pad[0] * 2), int(f.size * 1.18 + pad[1] * 2)
    layer = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((12, 18, w + 12, h + 18), radius=radius, fill=(0, 0, 0, 70))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((12, 12, w + 12, h + 12), radius=radius, fill=bg)
    d.text((12 + pad[0], 12 + pad[1] + f.size * 0.04), text, font=f, fill=fg)
    return layer.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else layer


def _watermark(canvas: Image.Image, config: dict, color=(255, 255, 255, 170), shadow=True):
    """모든 장 하단 가운데에 작은 채널 주소 (퍼가기 방지)."""
    d = ImageDraw.Draw(canvas)
    kw = dict(stroke_width=2, stroke_fill=(0, 0, 0, 70)) if shadow else {}
    d.text((W / 2, H - 38), config.get("handle", ""), font=font(B, 24), fill=color, anchor="mm", **kw)


def _shadow_text(canvas: Image.Image, xy, text: str, f, fill, blur: int = 10, alpha: int = 170):
    """그림자 깔린 글자 (사진 위 가독성)."""
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 5), text, font=f, fill=(0, 0, 0, alpha))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(canvas).text(xy, text, font=f, fill=fill)


def render_photo_cover(post: Post, config: dict) -> Image.Image:
    """01 표지 (후킹용): 사진 + 아래쪽 굵은 고딕 두 줄. 첫 줄 브랜드(흰색), 둘째 줄 혜택(강조색, 가장 크게)."""
    c = _light(config)
    img = _post_photo(post)
    im = open_img(post.asset(img)) if img else None
    canvas = cover_crop(im, (W, H), (0.5, 0.4)).convert("RGBA") if im else splash_bg(c["sp"], 0)
    canvas.alpha_composite(vgrad((W, H), (0, 0, 0), H * 0.5, H, 0, 215))
    d = ImageDraw.Draw(canvas)
    total = 1 + len(post.items) + (1 if post.outro else 0)
    d.text((W - M, 64), f"{1:02d}/{total:02d}", font=font(B, 28), fill=(255, 255, 255, 210), anchor="ra",
           stroke_width=2, stroke_fill=(0, 0, 0, 80))
    lines = [t for t in post.title.split("\n") if t.strip()][:2]
    brand_line, benefit = (lines[0], lines[1]) if len(lines) > 1 else ("", lines[0] if lines else "")
    bf = font(EB, 150)
    while _tw(bf, benefit) > W - 2 * M and bf.size > 70:
        bf = font(EB, bf.size - 4)
    nf = font(EB, 104)
    while _tw(nf, brand_line) > W - 2 * M and nf.size > 56:
        nf = font(EB, nf.size - 4)
    y = H - 120 - line_h(bf)
    _shadow_text(canvas, (M - 4, y), benefit, bf, c["hl"])
    if brand_line:
        _shadow_text(canvas, (M, y - line_h(nf) + 6), brand_line, nf, (255, 255, 255))
    credit = post.cover_credit or _post_credit(post)
    if credit:  # 사진 출처·라이선스 표기 (왼쪽 위, 작게)
        ImageDraw.Draw(canvas).text((M, 66), credit, font=font(R, 18), fill=(255, 255, 255, 200), anchor="lm",
                                    stroke_width=2, stroke_fill=(0, 0, 0, 90))
    _watermark(canvas, config)
    return canvas.convert("RGB")


def render_steps(post: Post, item: Item, idx: int, total: int, config: dict) -> Image.Image:
    """02 혜택 받는 법: 표지 사진을 흐리고 어둡게 깐 배경 + 흰 글씨 STEP (브랜드 색 없음 → 어떤 사진에도 어울림)."""
    c = _light(config)
    img = post.cover_image or item.image or _post_photo(post)  # 표지와 같은 사진 우선
    im = open_img(post.asset(img)) if img else None
    if im:
        canvas = cover_crop(im, (W, H), (0.5, 0.45)).filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
        canvas.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 165)))
    else:
        canvas = Image.new("RGBA", (W, H), (22, 22, 24, 255))
    d = ImageDraw.Draw(canvas)
    d.text((W - M, 64), f"{idx + 1:02d}/{total:02d}", font=font(B, 28), fill=(255, 255, 255, 200), anchor="ra")
    raw = (item.desc or "").split("\n")
    cut = next((i for i, ln in enumerate(raw) if ln.strip() == "---"), len(raw))
    steps = [ln.strip() for ln in raw[:cut] if ln.strip()]
    info = [ln.split("|", 1) for ln in raw[cut + 1:] if "|" in ln]
    notes = [ln.strip() for ln in raw[cut + 1:] if ln.strip() and "|" not in ln]
    tf, sf, nf = font(EB, 72), font(B, 44), font(B, 34)
    kf, vf = font(EB, 28), font(R, 34)
    step_l = [wrap(st, sf, W - 2 * M - 170) for st in steps]
    step_h = [max(140, block_h(sf, ls) + 56) for ls in step_l]
    info_l = [wrap(v.strip(), vf, W - 2 * M - 140) for _, v in info]
    note_l = [wrap(t, nf, W - 2 * M - 40) for t in notes]
    title = item.title or "혜택 받는 법"
    content = line_h(tf) + 50 + sum(step_h) + 22 * max(0, len(steps) - 1) \
        + (40 + sum(block_h(vf, vl) + 18 for vl in info_l) if info else 0) \
        + (50 + sum(block_h(nf, nl) + 10 for nl in note_l) if notes else 0)
    top, bottom = 130, H - 110
    y = top + max(0, (bottom - top - content) // 2)
    d.text((M, y), title, font=tf, fill=(255, 255, 255))
    y += line_h(tf) + 50
    for i, (lines, h) in enumerate(zip(step_l, step_h), 1):
        box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle((M - 10, y, W - M + 10, y + h), radius=30, fill=(255, 255, 255, 38),
                                              outline=(255, 255, 255, 90), width=2)
        canvas.alpha_composite(box)
        d = ImageDraw.Draw(canvas)
        cx, cy = M + 58, y + h / 2
        d.text((cx, cy - 16), "STEP", font=font(EB, 20), fill=c["hl"], anchor="mm")
        d.text((cx, cy + 14), f"{i:02d}", font=font(EB, 44), fill=c["hl"], anchor="mm")
        draw_lines(d, lines, sf, M + 140, y + (h - block_h(sf, lines)) / 2, (255, 255, 255))
        y += h + 22
    if info:
        y += 18
        for (k, _), vl in zip(info, info_l):
            d.text((M, y + 2), k.strip(), font=kf, fill=c["hl"])
            y = draw_lines(d, vl, vf, M + 140, y, (235, 235, 235)) + 18
    if notes:
        y += 28
        for nl in note_l:
            y = draw_lines(d, nl, nf, 0, y, (255, 255, 255, 220), anchor_center=True) + 10
    _watermark(canvas, config)
    return canvas.convert("RGB")


def _channel_icon(size: int, config: dict) -> Image.Image:
    """프로필과 같은 채널 아이콘: 오렌지 둥근 사각형 + 흰 종 + 레몬 알림 점."""
    c = _light(config)
    ic = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(ic)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * .26), fill=c["accent"])
    _bell(d, size / 2, size * .53, size * .3, (255, 255, 255))
    r = size * .085
    cx, cy = size * .7, size * .27
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c["hl"])
    return ic


def render_follow_card(post: Post, config: dict) -> Image.Image:
    """03 팔로우 카드 (모든 캐러셀 공용): 무채색 배경, 채널 아이콘만 오렌지."""
    o = config.get("outro", {})
    canvas = Image.new("RGBA", (W, H), (17, 17, 19, 255))
    d = ImageDraw.Draw(canvas)
    total = 1 + len(post.items) + 1
    d.text((W - M, 64), f"{total:02d}/{total:02d}", font=font(B, 28), fill=(255, 255, 255, 170), anchor="ra")
    canvas.alpha_composite(_channel_icon(200, config), (int(W / 2 - 100), 210))
    d = ImageDraw.Draw(canvas)
    y = 520
    for t in o.get("title", "무료·할인 혜택,\n놓치기 전에 팔로우!").split("\n"):
        f = font(EB, 86)
        while _tw(f, t) > W - 2 * M and f.size > 48:
            f = font(EB, f.size - 2)
        d.text((W / 2, y), t, font=f, fill=(255, 255, 255), anchor="ma")
        y += int(f.size * 1.35)
    y += 24
    for t in o.get("sub", "매일 새로운 할인정보를\n빠르게 알려드립니다.").split("\n"):
        d.text((W / 2, y), t, font=font(R, 40), fill=(190, 190, 196), anchor="ma")
        y += 58
    hy = H - 250
    d.text((W / 2, hy), config.get("handle", ""), font=font(EB, 46), fill=(255, 255, 255), anchor="ma")
    ff = font(EB, 34)
    fw = _tw(ff, "FOLLOW") + 96
    d.rounded_rectangle((W / 2 - fw / 2, hy + 80, W / 2 + fw / 2, hy + 146), radius=33, fill=(255, 255, 255))
    d.text((W / 2, hy + 113), "FOLLOW", font=ff, fill=(17, 17, 19), anchor="mm")
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
    total = 1 + len(post.items) + (1 if post.outro else 0) + (1 if post.reveal else 0) + (1 if post.recommend else 0)
    covers = {"deal": render_deal_cover, "alarm": render_alarm_cover, "photo": render_photo_cover}
    slides = [covers.get(post.cover_style, render_cover)(post, config)]
    for i, it in enumerate(post.items, 1):
        if it.type == "deal":
            slides.append(render_deal(post, it, i, total, config))
        elif it.type == "steps":
            slides.append(render_steps(post, it, i, total, config))
        elif it.type == "coupon":
            slides.append(render_coupon(post, it, i, total, config))
        elif it.type == "photo":  # 직접 넣은 이미지를 그대로 한 장 (공식 이벤트 이미지 등)
            slides.append(cover_crop(open_img(post.asset(it.image)), (W, H), (0.5, 0.5)).convert("RGB"))
        elif it.type in ("story", "quote"):
            slides.append(render_story(post, it, i, total, config))
        else:
            slides.append(render_item(post, it, i, total, config))
    if post.reveal:
        slides.append(render_reveal(post, len(slides), total, config))
    if post.recommend:
        slides.append(render_recommend(post, len(slides), total, config))
    if post.outro:
        style = (config.get("outro") or {}).get("style")
        slides.append({"toggle": render_toggle_outro, "follow_card": render_follow_card}.get(style, render_outro)(post, config))
    return slides
