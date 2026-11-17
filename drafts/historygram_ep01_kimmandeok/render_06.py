"""역사그램 6장: 채널 팔로우 카드 (모든 캐러셀 공용).

같은 폴더에 profile.png(프로필 원본 이미지)가 있으면 그걸 동그랗게 넣고,
없으면 글자 엠블럼을 쓴다.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
WHITE, YELLOW, GRAY = (255, 255, 255), (255, 229, 0), (170, 170, 170)
HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "assets/fonts"
BLACK, BOLD = str(FONTS / "Pretendard-Black.otf"), str(FONTS / "Pretendard-Bold.otf")
HANDLE = "@historygram.kr"


def f(path, size):
    return ImageFont.truetype(path, size)


def icon(size):
    src = HERE / "profile.png"
    if src.exists():
        im = Image.open(src).convert("RGBA")
        s = min(im.size)
        im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
        im = im.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size))
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        im.putalpha(mask)
        return im
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=(28, 28, 28), outline=YELLOW, width=6)
    d.text((size / 2, size / 2), "역사\n그램", font=f(BLACK, 52), fill=WHITE, anchor="mm",
           align="center", spacing=4)
    return im


img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
img.alpha_composite(icon(220), ((W - 220) // 2, 190))
d = ImageDraw.Draw(img)

y = 560
for parts in ([("매일 한 장", WHITE)], [("역사", YELLOW)]):
    font = f(BLACK, 128)
    total = sum(font.getlength(t) for t, _ in parts)
    assert total <= W - 180
    x = (W - total) / 2
    for t, c in parts:
        d.text((x, y), t, font=font, fill=c)
        x += font.getlength(t)
    y += 150

hy = H - 260
d.text((W / 2, hy), HANDLE, font=f(BLACK, 50), fill=WHITE, anchor="ma")
ff = f(BLACK, 36)
fw = ff.getlength("팔로우") + 120
d.rounded_rectangle((W / 2 - fw / 2, hy + 88, W / 2 + fw / 2, hy + 160), radius=36, fill=YELLOW)
d.text((W / 2, hy + 124), "팔로우", font=ff, fill=(0, 0, 0), anchor="mm")

out = HERE / "06.png"
img.convert("RGB").save(out)
print(out)
