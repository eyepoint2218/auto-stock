"""역사그램 EP.01 1장: 검정 배경 + 글자만."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
WHITE, YELLOW = (255, 255, 255), (255, 229, 0)
ROOT = Path(__file__).resolve().parents[2]
font = ImageFont.truetype(str(ROOT / "assets/fonts/Pretendard-Black.otf"), 104)


HANDLE = "@historygram.kr"


def stamp(img):
    """오른쪽 아래 채널명 (작게, 옅은 그림자)."""
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(Path(__file__).resolve().parents[2] / "assets/fonts/Pretendard-Bold.otf"), 26)
    d.text((1080 - 40, 1350 - 40), HANDLE, font=f, fill=(0, 0, 0), anchor="rs", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((1080 - 40, 1350 - 40), HANDLE, font=f, fill=(230, 230, 230), anchor="rs")

# 줄마다 (글자, 색) 조각
lines = [
    [("“제 두 눈으로", WHITE)],
    [("금강산", YELLOW), ("을 직접", WHITE)],
    [("보고 싶습니다.”", WHITE)],
]
img = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(img)
asc, desc = font.getmetrics()
line_h = int((asc + desc) * 1.4)
y = (H - line_h * len(lines)) // 2 + (line_h - asc - desc) // 2
for parts in lines:
    total = sum(d.textlength(t, font=font) for t, _ in parts)
    assert total <= W - 180, f"글자 넘침: {total}"
    x = (W - total) / 2
    for t, c in parts:
        d.text((x, y), t, font=font, fill=c)
        x += d.textlength(t, font=font)
    y += line_h
stamp(img)
out = Path(__file__).with_name("01.png")
img.save(out)
print(out, img.size)
