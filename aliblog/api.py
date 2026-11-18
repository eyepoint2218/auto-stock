"""알리익스프레스 어필리에이트(Portals) Open API 클라이언트.

필요한 환경변수 (GitHub Secrets):
  ALI_APP_KEY, ALI_APP_SECRET, ALI_TRACKING_ID
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time

import requests

ENDPOINT = "https://api-sg.aliexpress.com/sync"

FIELDS = ",".join([
    "product_id", "product_title", "product_main_image_url", "product_detail_url",
    "promotion_link", "target_sale_price", "target_original_price",
    "target_sale_price_currency", "discount", "evaluate_rate", "lastest_volume",
    "first_level_category_name", "second_level_category_name",
])


class AliError(RuntimeError):
    pass


def _sign(params: dict, secret: str) -> str:
    base = "".join(f"{k}{params[k]}" for k in sorted(params))
    return hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest().upper()


def call(method: str, **biz) -> dict:
    key = os.environ.get("ALI_APP_KEY")
    secret = os.environ.get("ALI_APP_SECRET")
    if not key or not secret:
        raise AliError("ALI_APP_KEY / ALI_APP_SECRET 가 없습니다 (GitHub Secrets 에 등록). 예시로 보려면 --sample")
    params = {
        "app_key": key,
        "method": method,
        "sign_method": "sha256",
        "timestamp": str(int(time.time() * 1000)),
        **{k: str(v) for k, v in biz.items() if v not in (None, "")},
    }
    params["sign"] = _sign(params, secret)
    r = requests.post(ENDPOINT, data=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "error_response" in data:
        e = data["error_response"]
        raise AliError(f"API 오류 {e.get('code')}: {e.get('msg')}")
    return data


def hot_products(page_size: int = 50, page_no: int = 1, category_ids: str = "",
                 sort: str = "LAST_VOLUME_DESC", method: str = "aliexpress.affiliate.hotproduct.query") -> list[dict]:
    """인기상품 목록. 가격은 원화, 제목은 한국어, 배송지는 한국 기준."""
    missing = [k for k in ("ALI_APP_KEY", "ALI_APP_SECRET", "ALI_TRACKING_ID") if not os.environ.get(k)]
    if missing:
        raise AliError(f"{', '.join(missing)} 가 없습니다 (GitHub Secrets 에 등록). 예시로 보려면 --sample")
    tracking = os.environ["ALI_TRACKING_ID"]
    data = call(
        method,
        fields=FIELDS, page_size=page_size, page_no=page_no, sort=sort,
        category_ids=category_ids, tracking_id=tracking,
        target_currency="KRW", target_language="KO", ship_to_country="KR",
    )
    resp = next(iter(data.values()))  # aliexpress_affiliate_..._response
    result = (resp.get("resp_result") or {})
    if str(result.get("resp_code")) not in ("200", "None"):
        raise AliError(f"API 응답 {result.get('resp_code')}: {result.get('resp_msg')}")
    products = ((result.get("result") or {}).get("products") or {}).get("product") or []
    return products
