import sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
prod_src, store_src, out = sys.argv[1:4]
W, H = 1080, 1350
# 1) 배경: 매장 사진 크게 + 흐리게 + 살짝 어둡게
st = Image.open(store_src).convert("RGB")
s = max(W / st.width, H / st.height)
st = st.resize((int(st.width * s) + 1, int(st.height * s) + 1), Image.LANCZOS)
l, t = (st.width - W) // 2, int((st.height - H) * 0.35)
bg = st.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(14)).convert("RGBA")
bg.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 70)))
# 2) 제품: 빨간 배경 지우기 (색 거리로 투명도)
pr = Image.open(prod_src).convert("RGB")
pr = pr.crop((26, 782, 1054, 1856))
a = np.asarray(pr).astype(np.float64)
red = np.array([239, 26, 58], dtype=np.float64)
dist = np.sqrt(((a - red) ** 2).sum(2))
alpha = np.clip((dist - 60) / 90, 0, 1)
# 빨간 기운 빼기 (반투명 가장자리·유리 손잡이)
redness = np.clip((a[..., 0] - (a[..., 1] + a[..., 2]) / 2) / 255, 0, 1)
gray = a.mean(2, keepdims=True)
a2 = a * (1 - redness[..., None] * 0.9) + gray * redness[..., None] * 0.9
rgba = np.dstack([np.clip(a2, 0, 255), alpha * 255]).astype(np.uint8)
mug = Image.fromarray(rgba, "RGBA")
bbox = mug.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox()
mug = mug.crop(bbox)
mw = int(W * 0.52)
mug = mug.resize((mw, int(mug.height * mw / mug.width)), Image.LANCZOS)
mug = Image.fromarray(np.dstack([np.asarray(mug)[..., :3], np.asarray(mug.split()[3].filter(ImageFilter.GaussianBlur(1)))]), "RGBA")
x, y = int(W * 0.40), int(H * 0.24)
# 그림자
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((x + mw * 0.08, y + mug.height - 40, x + mw * 0.85, y + mug.height + 40), fill=(0, 0, 0, 190))
bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(25)))
bg.alpha_composite(mug, (x, y))
bg.convert("RGB").save(out, quality=94)
