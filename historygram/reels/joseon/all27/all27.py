"""조선왕조 27명 1분 영상 (특별 콘텐츠).

python historygram/reels/joseon/all27/all27.py sample 4   # 한 장 미리보기
python historygram/reels/joseon/all27/all27.py build      # 60초 영상
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BLACK_F = str(ROOT / "assets/fonts/Pretendard-Black.otf")
BOLD_F = str(ROOT / "assets/fonts/Pretendard-Bold.otf")
W, H, FPS = 1080, 1920, 30
WHITE, YELLOW = (255, 255, 255), (255, 229, 0)

KINGS = [
    ("태조", "1392~1398", "조선 건국·한양 천도"),
    ("정종", "1398~1400", "2년 만에 동생에게 양위"),
    ("태종", "1400~1418", "6조 직계제·호패법"),
    ("세종", "1418~1450", "훈민정음 창제"),
    ("문종", "1450~1452", "세자 시절 측우기 제작"),
    ("단종", "1452~1455", "열두 살 왕, 숙부에게 왕위를 잃다"),
    ("세조", "1455~1468", "계유정난·『경국대전』 편찬 시작"),
    ("예종", "1468~1469", "재위 1년 남짓"),
    ("성종", "1469~1494", "『경국대전』 완성·반포"),
    ("연산군", "1494~1506", "두 번의 사화, 쫓겨난 왕"),
    ("중종", "1506~1544", "중종반정·조광조 개혁"),
    ("인종", "1544~1545", "재위 8개월"),
    ("명종", "1545~1567", "을사사화·문정왕후 수렴청정"),
    ("선조", "1567~1608", "임진왜란"),
    ("광해군", "1608~1623", "중립 외교·대동법 시작"),
    ("인조", "1623~1649", "병자호란·삼전도"),
    ("효종", "1649~1659", "북벌 준비"),
    ("현종", "1659~1674", "예송 논쟁"),
    ("숙종", "1674~1720", "환국·상평통보"),
    ("경종", "1720~1724", "재위 4년, 신임옥사"),
    ("영조", "1724~1776", "탕평책·균역법, 최장 52년"),
    ("정조", "1776~1800", "규장각·수원 화성"),
    ("순조", "1800~1834", "세도 정치·홍경래의 난"),
    ("헌종", "1834~1849", "여덟 살 즉위, 세도 정치"),
    ("철종", "1849~1863", "강화도령·임술 농민 봉기"),
    ("고종", "1863~1907", "대한제국 선포"),
    ("순종", "1907~1910", "마지막 왕, 국권 피탈"),
]


def font(p, s):
    return ImageFont.truetype(p, s)


def art_path(n):
    for name in (f"k{n:02d}.png", f"k{n:02d}.jpg", f"k{n:02d}_grid.png"):
        p = HERE / "art" / name
        if p.exists():
            return p
    return None


def portrait(n):
    """초상을 화면 위쪽에 꽉 차게(가로 기준), 아래는 어둡게 이어지게."""
    bg = Image.new("RGB", (W, H), (14, 11, 12))
    p = art_path(n)
    if p is None:
        return bg
    src = Image.open(p).convert("RGB")
    s = W / src.width
    src = src.resize((W, round(src.height * s)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    y = 150
    bg.paste(src, (0, y))
    # 아래로 자연스럽게 어두워지는 그라데이션
    g = Image.new("L", (1, H))
    top = y + int(src.height * 0.60)
    for yy in range(H):
        a = 0 if yy < top else min(255, int((yy - top) / 260 * 255))
        if yy < y + 140:
            a = max(a, 255 - int(max(0, yy - y) / 140 * 255))
        g.putpixel((0, yy), a)
    return Image.composite(Image.new("RGB", (W, H), (14, 11, 12)), bg, g.resize((W, H)))


def text_layer(n):
    name, years, key = KINGS[n - 1]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # 위쪽 배지
    d.text((W / 2, 300), "조선왕조 518년", font=font(BOLD_F, 34), fill=(235, 235, 235), anchor="mm")
    # 이름·재위·핵심 (인스타 하단 UI 위쪽, y<1500)
    d.text((W / 2, 1215), f"{n}대 {name}", font=font(BLACK_F, 150), fill=WHITE, anchor="mm")
    d.text((W / 2, 1322), years, font=font(BOLD_F, 52), fill=(215, 215, 215), anchor="mm")
    kf = font(BLACK_F, 66)
    while kf.getlength(key) > W - 160:
        kf = font(BLACK_F, kf.size - 2)
    d.text((W / 2, 1408), key, font=kf, fill=YELLOW, anchor="mm")
    # 진행 막대
    x0, x1, by = 160, W - 160, 1468
    d.rounded_rectangle((x0, by, x1, by + 8), radius=4, fill=(70, 70, 70))
    d.rounded_rectangle((x0, by, x0 + (x1 - x0) * n / 27, by + 8), radius=4, fill=YELLOW)
    d.text((W / 2, by + 36), f"{n} / 27 · @historygram.kr · 초상은 상상화", font=font(BOLD_F, 24),
           fill=(175, 175, 175), anchor="mm")
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(8))
    shadow = Image.merge("RGBA", (*[Image.new("L", (W, H))] * 3, sh.point(lambda v: int(v * .7))))
    return Image.alpha_composite(shadow, lay)


def sample(n):
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    img = portrait(n).convert("RGBA")
    img = Image.alpha_composite(img, text_layer(n)).convert("RGB")
    img.save(out / f"sample_k{n:02d}.png")
    print(out / f"sample_k{n:02d}.png")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if cmd == "sample":
        sample(int(sys.argv[2]) if len(sys.argv) > 2 else 4)


# ---------- 60초 영상 ----------
INTRO_F, KING_F, OUTRO_F, FADE_F = 90, 60, 90, 6


def title_card(lines, sub=None):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(BLACK_F, 104)
    lh = 150
    top = int(H * 0.42) - lh * len(lines) // 2
    for i, l in enumerate(lines):
        segs, x = [], 0
        import re
        for m in re.finditer(r"\[([^\]]+)\]|([^\[]+)", l):
            t, c = (m.group(1), YELLOW) if m.group(1) else (m.group(2), WHITE)
            segs.append((t, c))
            x += f.getlength(t)
        x = (W - x) / 2
        for t, c in segs:
            d.text((x, top + i * lh), t, font=f, fill=c)
            x += f.getlength(t)
    if sub:
        d.text((W / 2, top + lh * len(lines) + 70), sub, font=font(BOLD_F, 44), fill=(200, 200, 200), anchor="mm")
    d.text((W / 2, 300), "@historygram.kr", font=font(BOLD_F, 30), fill=(220, 220, 220), anchor="mm")
    return img


def king_frames(n):
    base = portrait(n)
    text = text_layer(n)
    for i in range(KING_F):
        z = 1 + 0.04 * i / (KING_F - 1)
        cw, ch = round(W / z), round(H / z)
        x, y = (W - cw) // 2, int((H - ch) * 0.3)
        fr = base.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
        yield Image.alpha_composite(fr, text).convert("RGB")


def build():
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    final = out / "joseon_27kings_60s.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)],
                         stdin=subprocess.PIPE)
    segments = [[title_card(["조선 518년,", "왕 [27명]을 1분에"])] * INTRO_F]
    segments += [king_frames(n) for n in range(1, 28)]
    segments.append([title_card(["가장 오래 다스린 왕은", "[영조] 52년"], "저장해 두고 복습하세요")] * OUTRO_F)
    prev_tail = []
    count = 0
    for seg in segments:
        frames = list(seg)
        # 앞 구간 마지막 FADE_F 프레임과 이번 구간 첫 프레임들을 섞어 크로스페이드
        if prev_tail:
            for k in range(FADE_F):
                frames[k] = Image.blend(prev_tail[k], frames[k], (k + 1) / (FADE_F + 1))
        body, prev_tail = frames, frames[-FADE_F:]
        for fr in body:
            p.stdin.write(fr.tobytes())
            count += 1
    p.stdin.close()
    p.wait()
    print(final, count)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "build":
    build()
