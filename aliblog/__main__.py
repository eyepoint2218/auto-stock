"""사용법:
  python -m aliblog daily [--count 10] [--date 2026-11-18] [--sample] [--no-images]
      인기상품을 모아 blog/날짜/ 에 post.html(붙여넣기용) · post.txt · products.json 을 만든다.
      --sample : API 키 없이 예시 데이터로 모양만 확인 (기록 안 남김)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from . import BLOG_DIR
from .api import AliError
from .collect import collect, load_history, save_history
from .render import render

KST = ZoneInfo("Asia/Seoul")


def sample_products(n: int) -> list[dict]:
    return [{
        "product_id": f"sample{i}",
        "product_title": f"예시 상품 {i} (실제 상품 아님) 이름이 길게 들어가는 자리입니다",
        "product_main_image_url": "",
        "promotion_link": "https://example.com/",
        "target_sale_price": str(9900 + i * 1000), "target_original_price": str(19900 + i * 1000),
        "discount": "50%", "evaluate_rate": "96.5%", "lastest_volume": str(5000 - i * 300),
        "first_level_category_name": f"카테고리{i}",
    } for i in range(1, n + 1)]


def sample_images(out, n: int) -> None:
    from PIL import Image, ImageDraw
    for i in range(1, n + 1):
        im = Image.new("RGB", (500, 500), (225, 228, 232))
        ImageDraw.Draw(im).text((210, 240), f"SAMPLE {i}", fill=(90, 90, 90))
        im.save(out / f"{i:02d}.png")


def download_images(products: list[dict], out) -> int:
    ok = 0
    for i, p in enumerate(products, 1):
        url = p.get("product_main_image_url")
        if not url:
            continue
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            (out / f"{i:02d}.jpg").write_bytes(r.content)
            ok += 1
        except requests.RequestException as e:
            print(f"사진 {i} 받기 실패: {e}", file=sys.stderr)
    return ok


def cmd_daily(a) -> int:
    now = datetime.now(KST)
    if a.date:
        now = datetime.fromisoformat(a.date).replace(hour=now.hour, tzinfo=KST)
    if a.sample:
        products = sample_products(a.count)
    else:
        try:
            products = collect(a.count, now.date(), a.category)
        except AliError as e:
            print(f"오류: {e}", file=sys.stderr)
            return 1
        if not products:
            print("조건에 맞는 상품이 없습니다.", file=sys.stderr)
            return 1

    out = BLOG_DIR / (now.date().isoformat() + ("_sample" if a.sample else ""))
    img = out / "images"
    img.mkdir(parents=True, exist_ok=True)
    if a.sample:
        sample_images(img, len(products))
        for i, p in enumerate(products, 1):
            p["product_main_image_url"] = f"images/{i:02d}.png"
    elif not a.no_images:
        print(f"사진 {download_images(products, img)}/{len(products)}장 저장")

    title, page, text = render(products, now, sample=a.sample)
    (out / "post.html").write_text(page, encoding="utf-8")
    (out / "post.txt").write_text(title + "\n\n" + text, encoding="utf-8")
    (out / "products.json").write_text(json.dumps(products, ensure_ascii=False, indent=1), encoding="utf-8")
    if not a.sample:
        save_history(load_history(), products, now.date())
    print(f"{out.relative_to(BLOG_DIR.parent)}/post.html  ({len(products)}개) 제목: {title}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="aliblog")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("daily")
    d.add_argument("--count", type=int, default=10)
    d.add_argument("--date")
    d.add_argument("--category", default="", help="알리 카테고리 ID (쉼표로 여러 개)")
    d.add_argument("--sample", action="store_true")
    d.add_argument("--no-images", action="store_true")
    a = ap.parse_args(argv)
    return cmd_daily(a)


if __name__ == "__main__":
    sys.exit(main())
