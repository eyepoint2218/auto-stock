"""역사그램 카드 렌더러.

1장: 검정 배경 + 글자 / 2~5장: GPT 삽화(art_0N.png) + 글자 / 6장: 공용 팔로우 카드.
글자 안의 [대괄호] 부분은 노란색 강조.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
SIDE = 90                       # 좌우 안전 여백
WHITE, YELLOW, GRAY = (255, 255, 255), (255, 229, 0), (170, 170, 170)
ROOT = Path(__file__).resolve().parents[1]
PKG = Path(__file__).resolve().parent
BLACK_F = str(ROOT / "assets/fonts/Pretendard-Black.otf")
BOLD_F = str(ROOT / "assets/fonts/Pretendard-Bold.otf")
HANDLE = "@historygram.kr"
PROFILE = PKG / "assets/profile.png"

# 2~4장 기본값 (episode.yml 의 slides.N 에서 덮어쓸 수 있음)
DEFAULTS = {
    2: dict(pos="bottom", size=96, crop=.5, shade=180),
    3: dict(pos="bottom", size=96, crop=.5, shade=180),
    4: dict(pos="top", size=96, crop=.5, shade=190),
}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def parse(line: str) -> list[tuple[str, tuple]]:
    """'[금강산]을 직접' → [('금강산', 노랑), ('을 직접', 흰색)]"""
    parts = []
    for m in re.finditer(r"\[([^\]]+)\]|([^\[]+)", line):
        if m.group(1):
            parts.append((m.group(1), YELLOW))
        elif m.group(2):
            parts.append((m.group(2), WHITE))
    return parts


def plain(line: str) -> str:
    return line.replace("[", "").replace("]", "")


def fit_size(lines: list[str], face: str, size: int, min_size: int = 48) -> int:
    """가장 긴 줄이 좌우 여백 안에 들어갈 때까지 글자 크기를 줄인다."""
    while size > min_size and max(font(face, size).getlength(plain(l)) for l in lines) > W - 2 * SIDE:
        size -= 2
    return size


def cover(img: Image.Image, anchor: float) -> Image.Image:
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    l, t = (img.width - W) // 2, round((img.height - H) * anchor)
    return img.crop((l, t, l + W, t + H)).convert("RGB")


def shade(img: Image.Image, pos: str, strength: int) -> Image.Image:
    g = Image.new("L", (1, H))
    for y in range(H):
        r = (y - H * .5) / (H * .5) if pos == "bottom" else (H * .42 - y) / (H * .42)
        g.putpixel((0, y), int(strength * max(0., min(1., r)) ** 1.2))
    return Image.composite(Image.new("RGB", (W, H)), img, g.resize((W, H)))


def draw_block(img: Image.Image, rows: list[tuple[str, int, str]], y: float,
               shadow: bool = True, leading: float = 1.25) -> Image.Image:
    """rows: (마크업 줄, 크기, 글꼴). 가운데 정렬, 최소한의 검은 그림자."""
    items, sh = [], Image.new("L", (W, H))
    sd = ImageDraw.Draw(sh)
    for line, size, face in rows:
        f = font(face, size)
        asc, desc = f.getmetrics()
        parts = parse(line)
        width = sum(f.getlength(t) for t, _ in parts)
        if width > W - 2 * SIDE:
            raise ValueError(f"글자가 여백을 넘음: {plain(line)}")
        x = (W - width) / 2
        for t, c in parts:
            sd.text((x, y + 3), t, font=f, fill=160)
            items.append((x, y, t, c, f))
            x += f.getlength(t)
        y += int((asc + desc) * leading)
    if shadow:
        img = Image.composite(Image.new("RGB", (W, H)), img, sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    for x, yy, t, c, f in items:
        d.text((x, yy), t, font=f, fill=c)
    return img


def block_height(rows) -> int:
    total = 0
    for _, size, face in rows:
        asc, desc = font(face, size).getmetrics()
        total += int((asc + desc) * 1.25)
    return total


def corner_note(img: Image.Image, text: str) -> None:
    """'재구성 연출'·'상상화' 같은 표기: 오른쪽 위 작게."""
    d = ImageDraw.Draw(img)
    f = font(BOLD_F, 24)
    d.text((W - 38, 40), text, font=f, fill=(0, 0, 0), anchor="ra", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((W - 38, 40), text, font=f, fill=(235, 235, 235), anchor="ra")


def stamp(img: Image.Image) -> None:
    """채널명: 오른쪽 아래 작게."""
    d = ImageDraw.Draw(img)
    f = font(BOLD_F, 26)
    d.text((W - 40, H - 40), HANDLE, font=f, fill=(0, 0, 0), anchor="rs", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((W - 40, H - 40), HANDLE, font=f, fill=(230, 230, 230), anchor="rs")


def placeholder(stem: str) -> Image.Image:
    img = Image.new("RGB", (W, H), (70, 66, 60))
    ImageDraw.Draw(img).text((W / 2, H * .4), f"삽화 자리 ({stem}.jpg)",
                             font=font(BOLD_F, 40), fill=(150, 145, 135), anchor="mm")
    return img


# ------------------------------------------------------------------ 장별

def slide1(ep: dict) -> Image.Image:
    cfg = ep["slides"][1]
    lines = cfg["lines"]
    size = fit_size(lines, BLACK_F, cfg.get("size", 104))
    img = Image.new("RGB", (W, H), (0, 0, 0))
    f = font(BLACK_F, size)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.4)
    y = (H - lh * len(lines)) / 2 + (lh - asc - desc) / 2
    img = draw_block(img, [(l, size, BLACK_F) for l in lines], y, shadow=False, leading=1.4)
    if cfg.get("note"):
        corner_note(img, cfg["note"])
    if ep.get("badge"):
        badge(img, ep["badge"])
    stamp(img)
    return img


def badge(img: Image.Image, text: str) -> None:
    """표지(1장) 위쪽 가운데 특집 표시: 노란 테두리 알약 + 노란 글자."""
    d = ImageDraw.Draw(img)
    f = font(BLACK_F, 44)
    tw = f.getlength(text)
    x0, y0 = (W - tw) / 2 - 36, 150
    d.rounded_rectangle((x0, y0, x0 + tw + 72, y0 + 80), radius=40, outline=YELLOW, width=4)
    d.text((W / 2, y0 + 40), text, font=f, fill=YELLOW, anchor="mm")


def story_keys(ep: dict) -> list:
    """삽화가 들어가는 스토리 장 키(2, 3, 3.5, 4 ...). 3.5 처럼 소수 키로 중간에 장을 끼워 넣는다."""
    return sorted(k for k in ep["slides"] if k not in (1, 5))


def art_stem(key) -> str:
    return f"art_{key:02d}" if float(key).is_integer() else "art_" + str(key).replace(".", "_")


def slide_art(ep: dict, folder: Path, no) -> tuple[Image.Image, bool]:
    stem = art_stem(int(no) if float(no).is_integer() else no)
    art = next((p for p in (folder / f"{stem}.jpg", folder / f"{stem}.png") if p.exists()), None)
    cfg = {**DEFAULTS.get(no, DEFAULTS[2]), **ep["slides"][no]}
    has_art = art is not None
    img = cover(Image.open(art), cfg["crop"]) if has_art else placeholder(stem)
    img = shade(img, cfg["pos"], cfg["shade"])
    return img, has_art


def slide_story(ep: dict, folder: Path, no) -> tuple[Image.Image, bool]:
    cfg = {**DEFAULTS.get(no, DEFAULTS[2]), **ep["slides"][no]}
    img, has_art = slide_art(ep, folder, no)
    size = fit_size(cfg["lines"], BLACK_F, cfg["size"])
    rows = [(l, size, BLACK_F) for l in cfg["lines"]]
    y = H - 140 - block_height(rows) if cfg["pos"] == "bottom" else cfg.get("top", 120)
    img = draw_block(img, rows, y)
    if cfg.get("note"):
        corner_note(img, cfg["note"])
    stamp(img)
    return img, has_art


def slide5(ep: dict, folder: Path) -> tuple[Image.Image, bool]:
    cfg = {"crop": 0, "pos": "bottom", "shade": 235, **ep["slides"][5]}
    ep["slides"][5] = cfg
    img, has_art = slide_art(ep, folder, 5)
    name = cfg["name"]
    rows = [(cfg.get("intro", "그의 이름은"), 60, BLACK_F),
            (f"[{name}]", fit_size([name], BLACK_F, 168), BLACK_F),
            (f"{name} ({cfg['years']})", 44, BOLD_F),
            (cfg["desc"], fit_size([cfg["desc"]], BOLD_F, 44, 32), BOLD_F)]
    img = draw_block(img, rows, H - 140 - block_height(rows))
    if cfg.get("note", "상상화"):
        corner_note(img, cfg.get("note", "상상화"))
    stamp(img)
    return img, has_art


def slide_quiz(ep: dict) -> Image.Image:
    """인물 공개 직전 퀴즈 카드: 검은 배경에 아주 큰 글자 'O는 / [누구]일까?'."""
    intro = ep["slides"][5].get("intro", "그의 이름은")
    lines = ep.get("quiz") or [f"{'그녀' if '그녀' in intro else '그'}는", "[누구]일까요?"]
    size = fit_size(lines, BLACK_F, 240)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    f = font(BLACK_F, size)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.15)
    y = (H - lh * len(lines)) / 2 + (lh - asc - desc) / 2
    img = draw_block(img, [(l, size, BLACK_F) for l in lines], y, shadow=False, leading=1.15)
    stamp(img)
    return img


def slide6(copy: tuple[str, ...] = ("매일 한 장", "[역사]")) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if PROFILE.exists():
        size = 260
        im = Image.open(PROFILE).convert("RGBA")
        s = min(im.size)
        im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
        im = im.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size))
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", (size, size)), mask))
        img.alpha_composite(im, ((W - size) // 2, 170))
    img = draw_block(img.convert("RGB"), [(c, 128, BLACK_F) for c in copy], 560, shadow=False, leading=1.2)
    d = ImageDraw.Draw(img)
    hy = H - 260
    d.text((W / 2, hy), HANDLE, font=font(BLACK_F, 50), fill=WHITE, anchor="ma")
    ff = font(BLACK_F, 36)
    fw = ff.getlength("팔로우") + 120
    d.rounded_rectangle((W / 2 - fw / 2, hy + 88, W / 2 + fw / 2, hy + 160), radius=36, fill=YELLOW)
    d.text((W / 2, hy + 124), "팔로우", font=ff, fill=(0, 0, 0), anchor="mm")
    return img


# ------------------------------------------------------------------ 묶음

def render_episode(ep: dict, folder: Path) -> list[Path]:
    """완성 PNG 를 out/ 에 저장. 삽화가 없는 장은 *_layout.png (배치 미리보기)."""
    out = folder / "out"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    saved = []

    def save(img, no, final=True):
        p = out / f"{no:02d}{'' if final else '_layout'}.png"
        img.save(p)
        saved.append(p)

    n = 1
    save(slide1(ep), n)
    for key in story_keys(ep):
        n += 1
        img, ok = slide_story(ep, folder, key)
        save(img, n, ok)
    n += 1
    save(slide_quiz(ep), n)                    # 퀴즈 카드 '그는 누구일까요?'
    n += 1
    img, ok = slide5(ep, folder)               # 인물 공개 (삽화 art_05)
    save(img, n, ok)
    n += 1
    save(slide6(tuple(ep.get("follow_copy", ["매일 한 장", "[역사]"]))), n)
    return saved


def pack(folder: Path, caption: str) -> Path | None:
    """모든 장이 완성됐으면 미리보기 시트와 zip(PNG 전부 + caption.txt)을 만든다."""
    out = folder / "out"
    SLIDE_COUNT = len({p.name[:2] for p in out.glob("[0-9][0-9]*.png")})
    pngs = [out / f"{i:02d}.png" for i in range(1, SLIDE_COUNT + 1)]
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    g, cols = 16, 4
    rows_n = -(-SLIDE_COUNT // cols)
    sheet = Image.new("RGB", (cols * 300 + (cols + 1) * g, rows_n * 375 + (rows_n + 1) * g), (240, 240, 240))
    for i in range(SLIDE_COUNT):
        p = pngs[i] if pngs[i].exists() else out / f"{i + 1:02d}_layout.png"
        sheet.paste(Image.open(p).resize((300, 375), Image.LANCZOS),
                    (g + (i % cols) * (300 + g), g + (i // cols) * (375 + g)))
    sheet.save(out / "preview.png")
    if not all(p.exists() for p in pngs):
        return None
    z = out / f"{folder.name}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in pngs:
            zf.write(p, p.name)
        zf.write(out / "caption.txt", "caption.txt")
    return z
