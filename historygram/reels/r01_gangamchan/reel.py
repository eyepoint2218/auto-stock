"""역사그램 릴스 R01 강감찬: 자막 레이어와 미리보기 프레임 생성.

python historygram/reels/r01_gangamchan/reel.py preview
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLACK_F = str(ROOT / "assets/fonts/Pretendard-Black.otf")
BOLD_F = str(ROOT / "assets/fonts/Pretendard-Bold.otf")

W, H = 1080, 1920
BG = (0, 0, 0)
WHITE, YELLOW = (255, 255, 255), (255, 229, 0)
HANDLE = "@historygram.kr"
SIDE = 110            # 좌우 여백 (오른쪽 아이콘 영역 고려)
TEXT_SIZE = 96
TOP_CENTER = 0.38     # 01~03 자막 덩어리 세로 중심 (화면 비율)

SCENES = [
    dict(lines=["거란 [10만] 대군이", "무너졌습니다."], art="scene01_from_grid.png"),
    dict(lines=["1019년,", "고려의 [귀주]에서."], art="scene02_from_grid.png"),
    dict(lines=["이 전투를 이끈", "장수는 [누구]일까요?"], art="scene03_from_grid.png", center=0.68),
    dict(reveal=True, art="scene04_from_grid.png"),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def parts(line):
    out = []
    for m in re.finditer(r"\[([^\]]+)\]|([^\[]+)", line):
        out.append((m.group(1), YELLOW) if m.group(1) else (m.group(2), WHITE))
    return out


def plain(line):
    return line.replace("[", "").replace("]", "")


def fit(lines, size):
    while size > 60 and max(font(BLACK_F, size).getlength(plain(l)) for l in lines) > W - 2 * SIDE:
        size -= 2
    return size


def draw_lines(img, lines, center_y, size, shadow):
    f = font(BLACK_F, size)
    lh = int(size * 1.42)
    top = int(center_y - lh * len(lines) / 2)
    if shadow:
        sh = Image.new("L", (W, H))
        sd = ImageDraw.Draw(sh)
        for i, l in enumerate(lines):
            x = (W - f.getlength(plain(l))) / 2
            sd.text((x, top + i * lh), plain(l), font=f, fill=150)
        img.paste((0, 0, 0), mask=sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        x = (W - f.getlength(plain(l))) / 2
        for text, color in parts(l):
            d.text((x, top + i * lh), text, font=f, fill=color)
            x += f.getlength(text)
    return top, top + lh * len(lines)


def watermark(img):
    d = ImageDraw.Draw(img)
    f = font(BOLD_F, 30)
    d.text((W / 2, 300), HANDLE, font=f, fill=(0, 0, 0), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((W / 2, 300), HANDLE, font=f, fill=(235, 235, 235), anchor="mm")


def label(img, text):
    d = ImageDraw.Draw(img)
    f = font(BOLD_F, 26)
    d.text((W - 150, 300), text, font=f, fill=(0, 0, 0), anchor="rm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((W - 150, 300), text, font=f, fill=(235, 235, 235), anchor="rm")


def cover(path):
    src = Image.open(path).convert("RGB")
    s = max(W / src.width, H / src.height)
    src = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    x, y = (src.width - W) // 2, (src.height - H) // 2
    return src.crop((x, y, x + W, y + H))


def dim(img, band):
    """전체 30% 어둡게 + 자막 띠 주변을 부드럽게 더 어둡게."""
    g = Image.new("L", (1, H))
    y0, y1 = band
    for y in range(H):
        a = 77
        dist = 0 if y0 <= y <= y1 else min(abs(y - y0), abs(y - y1))
        a += int(max(0, 1 - dist / 260) * 70)
        g.putpixel((0, y), a)
    return Image.composite(Image.new("RGB", (W, H)), img, g.resize((W, H)))


def reveal(img, shadow):
    d = ImageDraw.Draw(img)
    name_f, sub_f = font(BLACK_F, 190), font(BLACK_F, 56)
    cy = int(H * 0.66)
    if shadow:
        sh = Image.new("L", (W, H))
        sd = ImageDraw.Draw(sh)
        sd.text((W / 2, cy), "강감찬", font=name_f, fill=160, anchor="mm")
        sd.text((W / 2, cy + 160), "역사그램 | HISTORYGRAM", font=sub_f, fill=160, anchor="mm")
        img.paste((0, 0, 0), mask=sh.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(img)
    d.text((W / 2, cy), "강감찬", font=name_f, fill=YELLOW, anchor="mm")
    d.text((W / 2, cy + 160), "역사그램 | HISTORYGRAM", font=sub_f, fill=WHITE, anchor="mm")


def frame(scene, kind, base=None):
    """kind: 'A'(검정) / 'B'(영상·삽화 위). base: B일 때 배경 프레임."""
    is_b = kind == "B"
    if scene.get("reveal"):
        img = dim(base, (int(H * 0.58), int(H * 0.78))) if is_b else Image.new("RGB", (W, H), BG)
        reveal(img, is_b)
        if is_b:
            label(img, "상상화")
    else:
        size = fit(scene["lines"], TEXT_SIZE)
        lh = int(size * 1.42)
        cy = int(H * scene.get("center", TOP_CENTER))
        band = (cy - lh, cy + lh)
        img = dim(base, band) if is_b else Image.new("RGB", (W, H), BG)
        draw_lines(img, scene["lines"], cy, size, is_b)
    watermark(img)
    return img


def preview():
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    sheet = Image.new("RGB", (4 * 270 + 50, 2 * 480 + 30), (240, 240, 240))
    for i, sc in enumerate(SCENES):
        a = frame(sc, "A")
        b = frame(sc, "B", cover(HERE / "art" / sc["art"]))
        a.save(out / f"preview_A_{i + 1:02d}.png")
        b.save(out / f"preview_B_{i + 1:02d}.png")
        sheet.paste(a.resize((270, 480)), (10 + i * 280, 10))
        sheet.paste(b.resize((270, 480)), (10 + i * 280, 500))
    sheet.save(out / "preview_sheet.png")
    print(out / "preview_sheet.png")


if __name__ == "__main__":
    {"preview": preview}[sys.argv[1] if len(sys.argv) > 1 else "preview"]()
