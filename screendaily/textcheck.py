"""공감툰 그림 속 글귀(흰 글씨)의 크기·위치를 기준 이미지와 비교.
기준: siblings_style_ref.jpg 실측(글자 높이 2.0%, 위에서 19%)에서 연재는 글자 20% 작게 → 1.6%."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

REF = {"height": 1.6, "top": 19.0, "width": 18.0}   # % (연재 기준: 기준 이미지 실측 2.0% 보다 20% 작게)
TOL = 0.25                                         # ±25%


def measure(path: Path) -> dict | None:
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    h, w = a.shape[:2]
    y0, y1, x0, x1 = int(h * 0.06), int(h * 0.5), int(w * 0.15), int(w * 0.85)
    reg = a[y0:y1, x0:x1]
    white = (reg.min(axis=2) > 225) & (reg.max(axis=2) - reg.min(axis=2) < 25)
    rows = white.sum(1) >= 3
    bands, s = [], None
    for i, r in enumerate(list(rows) + [False]):
        if r and s is None:
            s = i
        elif not r and s is not None:
            if 0.008 * h <= i - s <= 0.06 * h:
                bands.append((s, i))
            s = None
    if not bands:
        return None
    lines = bands[:2]
    hs = [(b - t) / h * 100 for t, b in lines]
    widths = []
    for t, b in lines:
        cols = np.where(white[t:b].sum(0) > 0)[0]
        widths.append((cols.max() - cols.min()) / w * 100)
    return {"height": sum(hs) / len(hs), "top": (lines[0][0] + y0) / h * 100,
            "width": max(widths), "lines": len(lines), "size": f"{w}x{h}"}


def report(path: Path) -> bool:
    m = measure(path)
    if not m:
        print(f"{path}: 흰 글귀를 찾지 못했어요 (글자가 없거나 배경이 너무 밝음). 눈으로 확인하세요.")
        return False
    ok = True
    names = {"height": "글자 높이(세로 대비)", "top": "첫 줄 위치(위에서)", "width": "한 줄 폭(가로 대비)"}
    print(f"{path} ({m['size']}, {m['lines']}줄)")
    for k, label in names.items():
        ref, v = REF[k], m[k]
        if k == "width":  # 문구 길이에 따라 달라지므로 참고만
            print(f"  참고 {label}: {v:.1f}%  (8자 줄 기준 {ref:.1f}%)")
            continue
        good = abs(v - ref) <= ref * TOL
        ok &= good
        print(f"  {'OK ' if good else '다시'} {label}: {v:.1f}%  (기준 {ref:.1f}%)")
    if not ok:
        print("  → 기준과 달라요. docs/gongam_guide.md 3장 '글자가 크거나 굵게 나오면' 문구로 글귀만 다시 요청하세요.")
    return ok
