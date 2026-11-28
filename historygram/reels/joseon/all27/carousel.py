"""조선왕조 27명 캐러셀 (1080×1350): 표지 + 2명씩 14장 + 팔로우 = 16장.

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
    """후킹 문구 표지: 검정 배경, 글자만 (매일 캐러셀 1장과 같은 방식)."""
    lines = ["조선 왕 27명,", "[몇 명]이나", "아세요?"]
    rows = [(l, 128, a.BLACK_F) for l in lines]
    top = (H - r.block_height(rows)) / 2 - 40
    img = r.draw_block(Image.new("RGB", (W, H), (0, 0, 0)), rows, top, shadow=False, leading=1.25)
    d = ImageDraw.Draw(img)
    d.text((W / 2, H - 170), "1대 태조부터 27대 순종까지  →", font=a.font(a.BOLD_F, 40), fill=GRAY, anchor="mm")
    handle(d)
    return img


PER = 2
PAGES = (27 + PER - 1) // PER


def group(g):
    kings = list(range(g * PER + 1, min(27, g * PER + PER) + 1))
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title = f"{kings[0]}~{kings[-1]}대" if len(kings) > 1 else f"{kings[0]}대"
    d.text((60, 70), f"조선 왕 27명 · {title}", font=a.font(a.BLACK_F, 44), fill=a.WHITE, anchor="lm")
    d.text((W - 60, 70), f"초상은 상상화 · {g + 1} / {PAGES}", font=a.font(a.BOLD_F, 28), fill=GRAY, anchor="rm")
    top, rh, gap = 135, 555, 30
    pw = 420
    for i, n in enumerate(kings):
        name, years, key = a.KINGS[n - 1]
        y = top + i * (rh + gap)
        img.paste(face_crop(n, pw, rh), (60, y))
        tx = 60 + pw + 44
        nf = a.font(a.BLACK_F, 96)
        label = f"{n}대"
        d.text((tx, y + 90), label, font=a.font(a.BLACK_F, 60), fill=GRAY, anchor="lm")
        d.text((tx, y + 190), name, font=nf if nf.getlength(name) < W - tx - 50 else a.font(a.BLACK_F, 80),
               fill=a.WHITE, anchor="lm")
        d.text((tx, y + 285), years, font=a.font(a.BOLD_F, 46), fill=GRAY, anchor="lm")
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
            for ch_ in word:
                if kf.getlength(cur + ch_) > maxw:
                    lines.append(cur)
                    cur = ""
                cur += ch_
        lines.append(cur)
        for j, l in enumerate(lines[:3]):
            d.text((tx, y + 385 + j * 66), l, font=kf, fill=a.YELLOW, anchor="lm")
        if i == 0 and len(kings) > 1:
            d.line((60, y + rh + gap // 2, W - 60, y + rh + gap // 2), fill=(45, 42, 42), width=2)
    if len(kings) == 1:  # 마지막 장: 정리 한 줄
        y = top + rh + gap + 60
        d.text((W / 2, y), "가장 오래 다스린 왕", font=a.font(a.BOLD_F, 40), fill=GRAY, anchor="mm")
        d.text((W / 2, y + 80), "21대 영조 · 52년", font=a.font(a.BLACK_F, 72), fill=a.YELLOW, anchor="mm")
        d.text((W / 2, y + 200), "가장 짧았던 왕", font=a.font(a.BOLD_F, 40), fill=GRAY, anchor="mm")
        d.text((W / 2, y + 280), "12대 인종 · 8개월", font=a.font(a.BLACK_F, 72), fill=a.WHITE, anchor="mm")
    handle(d)
    return img


def main():
    out = HERE / "out" / "carousel"
    out.mkdir(parents=True, exist_ok=True)
    slides = [cover()] + [group(g) for g in range(PAGES)] + [r.slide6()]
    paths = []
    for i, s in enumerate(slides, 1):
        p = out / f"{i:02d}.png"
        s.convert("RGB").save(p)
        paths.append(p)
    sheet = Image.new("RGB", (4 * 270 + 50, 4 * 348 + 20), (240, 240, 240))
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
