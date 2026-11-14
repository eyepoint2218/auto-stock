import sys, math, random
from PIL import Image, ImageDraw, ImageFilter
S = 2                      # 2배로 그린 뒤 줄여서 부드럽게
W, H = 1080 * S, 1350 * S
GREEN = (0, 112, 74); DEEP = (0, 66, 45); LIGHT = (30, 160, 110)

def radial(w, h, c_in, c_out, cx, cy, r):
    im = Image.new("RGB", (w, h), c_out)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(r * 0.6))
    im.paste(Image.new("RGB", (w, h), c_in), (0, 0), mask)
    return im

bg = radial(W, H, LIGHT, DEEP, int(W * 0.62), int(H * 0.32), int(W * 0.55)).convert("RGBA")

# 커피콩 흩뿌리기
rnd = random.Random(7)
beans = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(beans)
for _ in range(16):
    x, y = rnd.randint(0, W), rnd.randint(int(H * 0.05), int(H * 0.95))
    if W * 0.35 < x < W * 0.95 and H * 0.08 < y < H * 0.62:
        continue
    s = rnd.randint(28, 46) * S
    bean = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0))
    b = ImageDraw.Draw(bean)
    b.ellipse((s * 0.4, s * 0.1, s * 1.6, s * 1.9), fill=(70, 40, 22, 235))
    b.arc((s * 0.75, s * 0.2, s * 1.25, s * 1.8), 250, 110, fill=(40, 22, 12, 255), width=max(3, s // 9))
    bean = bean.rotate(rnd.randint(0, 360), resample=Image.BICUBIC)
    beans.alpha_composite(bean, (x - s, y - s))
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.paste((0, 0, 0, 90), (0, 0), beans.split()[3].point(lambda a: a))
bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10 * S)), (6 * S, 10 * S))
bg.alpha_composite(beans)

# 아이스 라테 컵 (로고 없음)
cx, top, bot = int(W * 0.62), int(H * 0.21), int(H * 0.62)
tw, bw = int(W * 0.19), int(W * 0.145)      # 위·아래 반폭
cup = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(cup)
def xat(y, half_top=tw, half_bot=bw):
    t = (y - top) / (bot - top); return half_top + (half_bot - half_top) * t
# 음료: 위 우유층 → 아래 커피층 그라데이션
drink_top = top + int((bot - top) * 0.10)
for y in range(drink_top, bot):
    t = (y - drink_top) / (bot - drink_top)
    if t < 0.42:
        c = (238, 222, 198)
    elif t < 0.55:
        k = (t - 0.42) / 0.13; c = tuple(int(a + (b - a) * k) for a, b in zip((238, 222, 198), (150, 95, 55)))
    else:
        k = (t - 0.55) / 0.45; c = tuple(int(a + (b - a) * k) for a, b in zip((150, 95, 55), (92, 52, 28)))
    hw = xat(y) - 10 * S
    cd.line((cx - hw, y, cx + hw, y), fill=c + (255,))
# 얼음
for i, (dx, dy, s) in enumerate([(-0.45, 0.16, 70), (0.25, 0.13, 64), (-0.05, 0.25, 58), (0.4, 0.30, 52), (-0.38, 0.36, 50)]):
    y = top + int((bot - top) * dy); x = cx + int(xat(y) * dx); s *= S
    ice = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0))
    ImageDraw.Draw(ice).rounded_rectangle((s * .4, s * .4, s * 1.6, s * 1.6), radius=s // 4, fill=(255, 255, 255, 120), outline=(255, 255, 255, 200), width=3 * S)
    cup.alpha_composite(ice.rotate(18 * i - 20, resample=Image.BICUBIC), (x - s, y - s))
# 투명 컵 몸통 + 하이라이트
cd.polygon([(cx - tw, top), (cx + tw, top), (cx + bw, bot), (cx - bw, bot)], outline=(255, 255, 255, 170), width=5 * S)
cd.polygon([(cx - tw + 30 * S, top + 20 * S), (cx - tw + 58 * S, top + 20 * S), (cx - bw + 48 * S, bot - 30 * S), (cx - bw + 26 * S, bot - 30 * S)], fill=(255, 255, 255, 70))
# 바닥
cd.ellipse((cx - bw, bot - 16 * S, cx + bw, bot + 16 * S), fill=(255, 255, 255, 90))
# 돔 뚜껑
lid_y = top - 6 * S
cd.ellipse((cx - tw - 14 * S, lid_y - 20 * S, cx + tw + 14 * S, lid_y + 22 * S), fill=(250, 250, 250, 235))
cd.chord((cx - tw * 0.8, lid_y - tw * 0.55, cx + tw * 0.8, lid_y + tw * 0.4), 180, 360, fill=(255, 255, 255, 140), outline=(255, 255, 255, 220), width=4 * S)
# 초록 빨대
sx0, sy0 = cx + int(tw * 0.18), lid_y - int(tw * 0.35)
cd.line((sx0, sy0 + 40 * S, sx0 + 80 * S, sy0 - 170 * S), fill=(0, 98, 65, 255), width=26 * S)
cd.line((sx0 + 6 * S, sy0 + 30 * S, sx0 + 78 * S, sy0 - 160 * S), fill=(40, 150, 105, 255), width=8 * S)
# 크래프트 슬리브 (무지)
sl0, sl1 = top + int((bot - top) * 0.42), top + int((bot - top) * 0.66)
cd.polygon([(cx - xat(sl0) - 4 * S, sl0), (cx + xat(sl0) + 4 * S, sl0), (cx + xat(sl1) + 4 * S, sl1), (cx - xat(sl1) - 4 * S, sl1)], fill=(196, 160, 112, 255))
cd.line((cx - xat(sl0), sl0 + 10 * S, cx + xat(sl0), sl0 + 10 * S), fill=(170, 134, 90, 255), width=4 * S)
cd.line((cx - xat(sl1), sl1 - 10 * S, cx + xat(sl1), sl1 - 10 * S), fill=(170, 134, 90, 255), width=4 * S)
# 컵 그림자
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(shadow).ellipse((cx - bw * 1.4, bot - 10 * S, cx + bw * 1.4, bot + 50 * S), fill=(0, 0, 0, 120))
bg.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(20 * S)))
bg.alpha_composite(cup)
bg.convert("RGB").resize((1080, 1350), Image.LANCZOS).save(sys.argv[1], quality=94)
