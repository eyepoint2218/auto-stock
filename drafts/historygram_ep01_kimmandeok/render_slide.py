"""역사그램 EP.01 2~5장: GPT 삽화(art_0N.png) 위에 글자 합성.

사용: python render_slide.py        # 2~5장 전부
      python render_slide.py 3      # 한 장만
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
WHITE, YELLOW = (255, 255, 255), (255, 229, 0)
HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "assets/fonts"
BLACK, BOLD = str(FONTS / "Pretendard-Black.otf"), str(FONTS / "Pretendard-Bold.otf")

# lines: (조각들, 크기, 굵기). crop: 세로 자르기 기준(0=위 보존, .5=가운데, 1=아래 보존)
# shade: 글자 쪽 어둡게 하는 최대 세기(0~255)
SLIDES = {
    2: dict(crop=.5, pos="bottom", shade=170, note="재구성 연출", lines=[
        ([("임금은 왜", WHITE)], 84, BLACK),
        ([("이 여인에게", WHITE)], 84, BLACK),
        ([("소원", YELLOW), ("을 물었을까?", WHITE)], 84, BLACK)]),
    3: dict(crop=.5, pos="bottom", shade=170, lines=[
        ([("그녀는 굶주린", WHITE)], 76, BLACK),
        ([("제주 사람들을 위해", WHITE)], 76, BLACK),
        ([("자신의 재산", YELLOW), ("을", WHITE)], 76, BLACK),
        ([("내놓았다.", WHITE)], 76, BLACK)]),
    4: dict(crop=.9, pos="top", shade=110, top=100, lines=[
        ([("그녀의 선행은", WHITE)], 66, BLACK),
        ([("임금의 마음", YELLOW), ("까지 움직였다.", WHITE)], 66, BLACK)]),
    5: dict(crop=0, pos="bottom", shade=235, note="상상화", lines=[
        ([("그녀의 이름은", WHITE)], 60, BLACK),
        ([("김만덕", YELLOW)], 168, BLACK),
        ([("김만덕 (1739~1812)", WHITE)], 44, BOLD),
        ([("굶주린 제주 사람들을 구한 여성 상인", WHITE)], 44, BOLD)]),
}


def fit(img, anchor):
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    l, t = (img.width - W) // 2, round((img.height - H) * anchor)
    return img.crop((l, t, l + W, t + H)).convert("RGB")


def shade_mask(pos, strength):
    g = Image.new("L", (1, H))
    for y in range(H):
        r = (y - H * .5) / (H * .5) if pos == "bottom" else (H * .42 - y) / (H * .42)
        g.putpixel((0, y), int(strength * max(0., min(1., r)) ** 1.2))
    return g.resize((W, H))


def render(no):
    cfg = SLIDES[no]
    img = fit(Image.open(HERE / f"art_{no:02d}.png"), cfg["crop"])
    img = Image.composite(Image.new("RGB", (W, H)), img, shade_mask(cfg["pos"], cfg["shade"]))

    rows = []
    for parts, size, face in cfg["lines"]:
        font = ImageFont.truetype(face, size)
        asc, desc = font.getmetrics()
        width = sum(font.getlength(t) for t, _ in parts)
        assert width <= W - 180, f"{no}장 글자 넘침: {parts}"
        rows.append((parts, font, width, int((asc + desc) * 1.25)))
    block = sum(r[3] for r in rows)
    y = H - 140 - block if cfg["pos"] == "bottom" else cfg.get("top", 140)

    shadow = Image.new("L", (W, H))
    sd = ImageDraw.Draw(shadow)
    draws = []
    for parts, font, width, lh in rows:
        x = (W - width) / 2
        for t, c in parts:
            sd.text((x, y + 3), t, font=font, fill=160)
            draws.append((x, y, t, c, font))
            x += font.getlength(t)
        y += lh
    img = Image.composite(Image.new("RGB", (W, H)), img, shadow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    for x, y, t, c, font in draws:
        d.text((x, y), t, font=font, fill=c)

    if cfg.get("note"):  # 연출·상상화 표기: 오른쪽 위 작게
        nf = ImageFont.truetype(BOLD, 24)
        d.text((W - 38, 40), cfg["note"], font=nf, fill=(0, 0, 0), anchor="ra", stroke_width=3, stroke_fill=(0, 0, 0))
        d.text((W - 38, 40), cfg["note"], font=nf, fill=(235, 235, 235), anchor="ra")

    out = HERE / f"{no:02d}.png"
    img.save(out)
    print(out)


if __name__ == "__main__":
    for n in ([int(sys.argv[1])] if len(sys.argv) > 1 else SLIDES):
        render(n)
