"""인스타툰 6컷 한 장(2열 x 3행)을 p1~p6 으로 자르기.

ChatGPT 에 6컷을 한 장으로 그리게 하면 캐릭터가 컷마다 같아지고 한 번에 끝난다.
칸 사이 흰(또는 검은) 여백을 찾아 자르고, 못 찾으면 똑같이 나눈다.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

COLS, ROWS = 2, 3


def _gutter_cut(profile: np.ndarray, expected: float, span: float = 0.12) -> int:
    """profile: 줄마다 '여백다움'(0~1). expected 위치 근처에서 가장 여백다운 구간의 가운데."""
    n = len(profile)
    lo, hi = int(n * (expected - span)), int(n * (expected + span))
    seg = profile[lo:hi]
    best = seg.max()
    if best < 0.9:  # 뚜렷한 여백 없음 → 똑같이 나누기
        return int(n * expected)
    idx = np.where(seg >= best - 0.02)[0]
    # 가장 긴 연속 구간의 가운데
    runs, start = [], idx[0]
    for a, b in zip(idx, idx[1:]):
        if b != a + 1:
            runs.append((start, a)); start = b
    runs.append((start, idx[-1]))
    s, e = max(runs, key=lambda r: r[1] - r[0])
    return lo + (s + e) // 2


def _profile(gray: np.ndarray, axis: int) -> np.ndarray:
    """줄마다 거의 흰색이거나 거의 검은색인 픽셀 비율 중 큰 쪽."""
    white = (gray > 235).mean(axis=axis)
    black = (gray < 25).mean(axis=axis)
    return np.maximum(white, black)


def _trim(cell: Image.Image) -> Image.Image:
    """칸 테두리(흰 여백·검은 선)를 걷어 내고 가운데 정사각형으로."""
    g = np.asarray(cell.convert("L"), dtype=np.int16)
    h, w = g.shape

    def edge(prof, n):
        a = 0
        while a < n // 6 and prof[a] > 0.85:
            a += 1
        b = n
        while b > n - n // 6 and prof[b - 1] > 0.85:
            b -= 1
        return a, b

    x0, x1 = edge(_profile(g, 0), w)
    y0, y1 = edge(_profile(g, 1), h)
    # 테두리 선 안쪽으로 조금 더
    pad = max(2, int(min(w, h) * 0.01))
    box = (x0 + pad, y0 + pad, x1 - pad, y1 - pad)
    cell = cell.crop(box)
    cw, ch = cell.size
    s = min(cw, ch)
    left, top = (cw - s) // 2, (ch - s) // 2
    return cell.crop((left, top, left + s, top + s))


def split_sheet(sheet: Path, out_dir: Path, size: int = 1080) -> list[Path]:
    im = Image.open(sheet).convert("RGB")
    g = np.asarray(im.convert("L"), dtype=np.int16)
    h, w = g.shape
    xs = [0] + [_gutter_cut(_profile(g, 0), c / COLS) for c in range(1, COLS)] + [w]
    ys = [0] + [_gutter_cut(_profile(g, 1), r / ROWS) for r in range(1, ROWS)] + [h]
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    n = 0
    for r in range(ROWS):          # 읽는 순서: 왼→오, 위→아래
        for c in range(COLS):
            n += 1
            cell = _trim(im.crop((xs[c], ys[r], xs[c + 1], ys[r + 1])))
            cell = cell.resize((size, size), Image.LANCZOS)
            p = out_dir / f"p{n}.jpg"
            cell.save(p, quality=92)
            files.append(p)
    return files
