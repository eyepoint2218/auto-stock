"""역사그램 EP.01 1장: 검정 배경 + 글자만."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
WHITE, YELLOW = (255, 255, 255), (255, 229, 0)
ROOT = Path(__file__).resolve().parents[2]
font = ImageFont.truetype(str(ROOT / "assets/fonts/Pretendard-Black.otf"), 104)

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
out = Path(__file__).with_name("01.png")
img.save(out)
print(out, img.size)
