"""조선왕조 27명 캐러셀 (1080×1350): 표지 + 3명씩 9장 + 팔로우 = 11장.

python historygram/reels/joseon/all27/carousel.py
"""
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3]))
import all27 as a  # noqa: E402
from historygram import render as r  # noqa: E402

W, H = 1080, 1350
BG = (10, 8, 9)
GRAY = (190, 190, 190)


def face_crop(n, w, h):
    im = Image.open(a.art_path(n)).convert("RGB")
    s = w / (im.width * 0.62)                  # 가운데 62% 폭을 칸 너비에 맞춤
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int(im.height * 0.02)
    return im.crop((x, y, x + w, y + h))


def handle(d):
    d.text((W - 40, H - 40), "@historygram.kr", font=a.font(a.BOLD_F, 26), fill=(200, 200, 200), anchor="rs")


def cover():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((W / 2, 120), "조선 왕 27명", font=a.font(a.BLACK_F, 120), fill=a.YELLOW, anchor="mm")
    d.text((W / 2, 230), "한 번에 정리", font=a.font(a.BLACK_F, 68), fill=a.WHITE, anchor="mm")
    cols, gap = 6, 8
    cw = (W - 80 - (cols - 1) * gap) // cols
    ch = int(cw * 1.1)
    y0 = 300
    for i in range(27):
        row, c = divmod(i, cols)
        n_in_row = min(cols, 27 - row * cols)
        x0 = (W - (n_in_row * cw + (n_in_row - 1) * gap)) // 2
        x, y = x0 + c * (cw + gap), y0 + row * (ch + gap)
        img.paste(face_crop(i + 1, cw, ch), (x, y))
        d.text((x + cw - 6, y + ch - 6), str(i + 1), font=a.font(a.BLACK_F, 30), fill=a.YELLOW,
               anchor="rs", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((W / 2, H - 95), "1대 태조부터 27대 순종까지  →", font=a.font(a.BOLD_F, 40), fill=GRAY, anchor="mm")
    handle(d)
    return img


def group(g):
    kings = range(g * 3 + 1, g * 3 + 4)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((60, 70), f"조선 왕 27명 · {kings[0]}~{kings[-1]}대", font=a.font(a.BLACK_F, 44), fill=a.WHITE, anchor="lm")
    d.text((W - 60, 70), f"초상은 상상화 · {g + 1} / 9", font=a.font(a.BOLD_F, 28), fill=GRAY, anchor="rm")
    top, rh, gap = 130, 370, 20
    pw = 320
    for i, n in enumerate(kings):
        name, years, key = a.KINGS[n - 1]
        y = top + i * (rh + gap)
        img.paste(face_crop(n, pw, rh), (60, y))
        tx = 60 + pw + 44
        d.text((tx, y + 60), f"{n}대 {name}", font=a.font(a.BLACK_F, 84), fill=a.WHITE, anchor="lm")
        d.text((tx, y + 150), years, font=a.font(a.BOLD_F, 44), fill=GRAY, anchor="lm")
        # 핵심 한 줄 (넘치면 두 줄)
        kf = a.font(a.BLACK_F, 50)
        maxw = W - tx - 50
        lines, cur = [], ""
        for word in key.split(" "):
            t = (cur + " " + word).strip()
            if kf.getlength(t) <= maxw:
                cur = t
                continue
            if cur:
                lines.append(cur)
            cur = ""
            for ch_ in word:  # 한 단어가 너무 길면 글자 단위로
                if kf.getlength(cur + ch_) > maxw:
                    lines.append(cur)
                    cur = ""
                cur += ch_
        lines.append(cur)
        for j, l in enumerate(lines[:2]):
            d.text((tx, y + 245 + j * 66), l, font=kf, fill=a.YELLOW, anchor="lm")
        if i < 2:
            d.line((60, y + rh + gap // 2, W - 60, y + rh + gap // 2), fill=(45, 42, 42), width=2)
    handle(d)
    return img


def main():
    out = HERE / "out" / "carousel"
    out.mkdir(parents=True, exist_ok=True)
    slides = [cover()] + [group(g) for g in range(9)] + [r.slide6()]
    paths = []
    for i, s in enumerate(slides, 1):
        p = out / f"{i:02d}.png"
        s.convert("RGB").save(p)
        paths.append(p)
    sheet = Image.new("RGB", (4 * 270 + 50, 3 * 338 + 40), (240, 240, 240))
    for i, p in enumerate(paths):
        sheet.paste(Image.open(p).resize((270, 338)), (10 + (i % 4) * 280, 10 + (i // 4) * 348))
    sheet.save(out / "preview.png")
    with zipfile.ZipFile(out / "joseon_27kings_carousel.zip", "w") as z:
        for p in paths:
            z.write(p, p.name)
        z.write(HERE / "out" / "caption.txt", "caption.txt")
    print(out / "preview.png")


if __name__ == "__main__":
    main()
