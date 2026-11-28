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




# ---------- 영상 합성 ----------
import subprocess

FPS, SCENE_FRAMES, FADE_FRAMES = 30, 150, 6
CLIPS = ["clip01.mp4", "clip02.mp4", "clip03.mp4", "clip04.mp4"]


def overlay(scene, kind):
    """(고정 레이어, 자막 레이어). 고정: B 어둡게 덮기 + 워터마크 + 상상화. 자막: 장면 전환 때 페이드."""
    is_b = kind == "B"
    if scene.get("reveal"):
        band = (int(H * 0.58), int(H * 0.78))
    else:
        size = fit(scene["lines"], TEXT_SIZE)
        lh = int(size * 1.42)
        cy = int(H * scene.get("center", TOP_CENTER))
        band = (cy - lh, cy + lh)

    def text_layer(draw_fn, shadow):
        txt = Image.new("RGB", (W, H), (0, 0, 0))
        draw_fn(txt)
        mask = txt.convert("L").point(lambda v: 255 if v > 8 else v * 32)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if shadow:
            sh = mask.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.6))
            lay = Image.merge("RGBA", (*[Image.new("L", (W, H))] * 3, sh))
        t = txt.convert("RGBA")
        t.putalpha(mask)
        return Image.alpha_composite(lay, t)

    static = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if is_b:
        g = Image.new("L", (1, H))
        y0, y1 = band
        for y in range(H):
            dist = 0 if y0 <= y <= y1 else min(abs(y - y0), abs(y - y1))
            g.putpixel((0, y), 77 + int(max(0, 1 - dist / 260) * 70))
        static.putalpha(g.resize((W, H)))

    def marks(img):
        watermark(img)
        if is_b and scene.get("reveal"):
            label(img, "상상화")
    static = Image.alpha_composite(static, text_layer(marks, is_b))
    if scene.get("reveal"):
        text = text_layer(lambda im: reveal(im, False), is_b)
    else:
        text = text_layer(lambda im: draw_lines(im, scene["lines"], cy, size, False), is_b)
    return static, text


def build(kind):
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    parts_ = []
    for i, sc in enumerate(SCENES):
        ov = out / f"overlay_{kind}_{i + 1:02d}.png"
        st = out / f"static_{kind}_{i + 1:02d}.png"
        static, text = overlay(sc, kind)
        static.save(st)
        text.save(ov)
        part = out / f"part_{kind}_{i + 1:02d}.mp4"
        dur = SCENE_FRAMES / FPS
        fd = FADE_FRAMES / FPS
        fades = []
        if i > 0:
            fades.append(f"fade=t=in:st=0:d={fd}:alpha=1")
        if i < len(SCENES) - 1:
            fades.append(f"fade=t=out:st={dur - fd}:d={fd}:alpha=1")
        ovf = ",".join(["format=rgba"] + fades)
        if kind == "A":
            src = ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={dur}"]
            bg = "[0:v]setsar=1[bg]"
        else:
            src = ["-i", str(HERE / "video" / CLIPS[i])]
            bg = (f"[0:v]fps={FPS},scale=-2:{H}:flags=lanczos,crop={W}:{H},"
                  f"unsharp=5:5:0.6,setsar=1,trim=end_frame={SCENE_FRAMES},setpts=PTS-STARTPTS[bg]")
        fc = (f"{bg};[1:v]format=rgba[st];[2:v]{ovf}[ov];[bg][st]overlay=0:0[b2];"
              f"[b2][ov]overlay=0:0,format=yuv420p[v]")
        cmd = ["ffmpeg", "-v", "error", "-y", *src,
               "-loop", "1", "-t", str(dur), "-framerate", str(FPS), "-i", str(st),
               "-loop", "1", "-t", str(dur), "-framerate", str(FPS), "-i", str(ov), "-filter_complex", fc, "-map", "[v]", "-frames:v", str(SCENE_FRAMES),
               "-r", str(FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-an", str(part)]
        subprocess.run(cmd, check=True)
        parts_.append(part)
    lst = out / f"list_{kind}.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts_))
    final = out / f"R01_gangamchan_TYPE{kind}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-r", str(FPS), "-movflags", "+faststart", "-an", str(final)], check=True)
    print(final)


def thumbs():
    out = HERE / "out"
    for kind in "AB":
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.0", "-i",
                        str(out / f"R01_gangamchan_TYPE{kind}.mp4"), "-frames:v", "1",
                        str(out / f"R01_gangamchan_TYPE{kind}_thumb.png")], check=True)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] in ("A", "B", "thumbs"):
    build(sys.argv[1]) if sys.argv[1] != "thumbs" else thumbs()

if __name__ == "__main__" and (len(sys.argv) == 1 or sys.argv[1] == "preview"):
    preview()
