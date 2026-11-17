"""역사그램 2~5장: 삽화 위에 글자 합성.

사용: python render_slide.py 2 [삽화.png]
삽화가 없으면 회색 자리표시로 배치만 미리 본다.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
WHITE, YELLOW = (255, 255, 255), (255, 229, 0)
ROOT = Path(__file__).resolve().parents[2]
BLACK_FONT = str(ROOT / "assets/fonts/Pretendard-Black.otf")
BOLD_FONT = str(ROOT / "assets/fonts/Pretendard-Bold.otf")

# 장별 설정: 줄마다 [(글자, 색)], 위치(top/bottom), 크기, 연출 표기
SLIDES = {
    2: dict(lines=[[("임금은 왜", WHITE)],
                   [("이 여인에게", WHITE)],
                   [("소원", YELLOW), ("을 물었을까?", WHITE)]],
            pos="bottom", size=84, note="재구성 연출"),
}


def cover(img):
    """삽화를 1080×1350에 꽉 차게 맞춘다(가운데 기준 자르기)."""
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    l, t = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((l, t, l + W, t + H)).convert("RGB")


def placeholder():
    img = Image.new("RGB", (W, H), (70, 66, 60))
    d = ImageDraw.Draw(img)
    d.text((W / 2, H * 0.4), "삽화 자리 (2장: 궁궐 편전)", font=ImageFont.truetype(BOLD_FONT, 40),
           fill=(150, 145, 135), anchor="mm")
    return img


def gradient(pos):
    """글자 쪽 가장자리만 어둡게 (가독성용, 최소한)."""
    g = Image.new("L", (1, H))
    for y in range(H):
        r = (y - H * 0.55) / (H * 0.45) if pos == "bottom" else (H * 0.45 - y) / (H * 0.45)
        g.putpixel((0, y), int(200 * max(0.0, min(1.0, r)) ** 1.3))
    return g.resize((W, H))


def render(no, art=None):
    cfg = SLIDES[no]
    img = cover(Image.open(art)) if art else placeholder()
    img = Image.composite(Image.new("RGB", (W, H)), img, gradient(cfg["pos"]))

    font = ImageFont.truetype(BLACK_FONT, cfg["size"])
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * 1.3)
    block = lh * len(cfg["lines"])
    y0 = H - 150 - block if cfg["pos"] == "bottom" else 130

    # 최소한의 검은 그림자
    shadow = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shadow)
    text_layer = []
    y = y0
    for parts in cfg["lines"]:
        total = sum(font.getlength(t) for t, _ in parts)
        assert total <= W - 180, f"{no}장 글자 넘침: {total}"
        x = (W - total) / 2
        for t, c in parts:
            sd.text((x, y + 3), t, font=font, fill=150)
            text_layer.append((x, y, t, c))
            x += font.getlength(t)
        y += lh
    img = Image.composite(Image.new("RGB", (W, H)), img, shadow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    for x, y, t, c in text_layer:
        d.text((x, y), t, font=font, fill=c)

    if cfg.get("note"):  # 연출 표기: 오른쪽 위, 작게
        d.text((W - 40, 40), cfg["note"], font=ImageFont.truetype(BOLD_FONT, 24),
               fill=(220, 220, 220), anchor="ra")

    out = Path(__file__).with_name(f"{no:02d}{'' if art else '_layout'}.png")
    img.save(out)
    print(out)


if __name__ == "__main__":
    render(int(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
