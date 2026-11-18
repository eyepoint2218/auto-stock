"""네이버 블로그 붙여넣기용 글 만들기 (post.html + post.txt)."""
from __future__ import annotations

import html
import re
from datetime import datetime

DISCLOSURE = ("이 포스팅은 알리익스프레스 어필리에이트 활동의 일환으로, "
              "이를 통해 구매 시 일정액의 수수료를 제공받습니다.")
TAGS = ["알리익스프레스", "알리추천템", "알리인기상품", "알리직구", "해외직구", "알리꿀템"]
TITLES = [
    "알리익스프레스 인기상품 TOP 10 ({md}) 최근 판매량 순",
    "알리 직구 인기템 10가지 정리 ({md})",
    "{md} 알리익스프레스에서 많이 팔린 상품 10개",
]


def clean_title(t: str, limit: int = 48) -> str:
    t = re.sub(r"\s+", " ", html.unescape(t or "")).strip()
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0]
    return (cut or t[:limit]) + "…"


def won(v) -> str:
    try:
        return f"{round(float(str(v).replace(',', ''))):,}원"
    except ValueError:
        return ""


def blog_title(now: datetime) -> str:
    md = f"{now.month}월 {now.day}일"
    return TITLES[now.toordinal() % len(TITLES)].format(md=md)


def _facts(p: dict) -> list[str]:
    out = []
    sale, orig = won(p.get("target_sale_price")), won(p.get("target_original_price"))
    if sale:
        s = f"가격: {sale}"
        if orig and orig != sale:
            s += f" (정가 {orig}" + (f", {p['discount']} 할인)" if p.get("discount") else ")")
        out.append(s)
    if p.get("evaluate_rate"):
        out.append(f"긍정 평가: {p['evaluate_rate']}")
    if p.get("lastest_volume"):
        out.append(f"최근 판매: {int(float(p['lastest_volume'])):,}개")
    return out


def render(products: list[dict], now: datetime, sample: bool = False) -> tuple[str, str, str]:
    """(title, html, text) 반환."""
    title = blog_title(now)
    when = f"{now.month}/{now.day} {now.hour:02d}시"
    intro = (f"알리익스프레스에서 최근 많이 팔린 상품 가운데 평가가 좋은 {len(products)}개를 골랐습니다. "
             f"가격과 판매량은 {when} 기준이며, 할인·쿠폰에 따라 바뀔 수 있으니 구매 전 상품 페이지에서 꼭 확인하세요.")

    e = html.escape
    body = [f'<p><b>{e(DISCLOSURE)}</b></p>', f"<p>{e(intro)}</p>", "<p>&nbsp;</p>"]
    text = [DISCLOSURE, "", intro, ""]
    for i, p in enumerate(products, 1):
        name = clean_title(p.get("product_title", ""))
        link = p.get("promotion_link", "")
        body.append(f"<h3>{i}. {e(name)}</h3>")
        if p.get("product_main_image_url"):
            body.append(f'<p><a href="{e(link)}"><img src="{e(p["product_main_image_url"])}" '
                        f'alt="{e(name)}" width="500"></a></p>')
        facts = _facts(p)
        body += [f"<p>{e(f)}</p>" for f in facts]
        body.append(f'<p><a href="{e(link)}"><b>상품 보러가기</b></a></p>')
        body.append("<p>&nbsp;</p>")
        text += [f"{i}. {name}", *facts, f"상품 보러가기: {link}", ""]
    outro = "가격과 재고는 수시로 바뀌니 구매 전에 상품 페이지에서 다시 확인해 주세요."
    body.append(f"<p>{e(outro)}</p>")
    text += [outro, "", "태그: " + " ".join("#" + t for t in TAGS)]

    banner = ('<div class="warn">예시 데이터입니다. 실제 상품이 아니므로 올리지 마세요. '
              'API 키를 등록하면 실제 상품으로 바뀝니다.</div>') if sample else ""
    page = PAGE.format(
        title=e(title), banner=banner, article="\n".join(body),
        tags=e(" ".join(TAGS)), count=len(products),
    )
    return title, page, "\n".join(text)


PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>블로그 초안 - {title}</title>
<style>
 :root {{ color-scheme: light; }}
 body {{ margin:0; background:#f4f5f7; color:#222; font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif; }}
 .wrap {{ max-width:720px; margin:0 auto; padding:16px; }}
 .tool {{ background:#fff; border:1px solid #ddd; border-radius:10px; padding:16px; margin-bottom:16px; }}
 .tool h1 {{ font-size:18px; margin:0 0 8px; }}
 .row {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:8px 0; }}
 .row code {{ background:#f0f0f0; padding:6px 8px; border-radius:6px; font-size:14px; word-break:break-all; }}
 button {{ background:#03c75a; color:#fff; border:0; border-radius:6px; padding:8px 14px; font-size:14px; cursor:pointer; }}
 button.sub {{ background:#555; }}
 ol {{ margin:8px 0 0 18px; padding:0; font-size:14px; line-height:1.7; }}
 .warn {{ background:#fff3cd; border:1px solid #e0c060; padding:10px; border-radius:6px; margin-bottom:12px; }}
 #article {{ background:#fff; border:1px solid #ddd; border-radius:10px; padding:24px; }}
 #article img {{ max-width:100%; height:auto; }}
 #msg {{ color:#03a04a; font-size:14px; }}
</style></head><body><div class="wrap">
{banner}
<div class="tool">
 <h1>네이버 블로그 초안 (상품 {count}개)</h1>
 <div class="row"><b>제목</b> <code id="t">{title}</code> <button class="sub" onclick="copyText('t')">제목 복사</button></div>
 <div class="row"><b>태그</b> <code id="g">{tags}</code> <button class="sub" onclick="copyText('g')">태그 복사</button></div>
 <div class="row"><button onclick="copyArticle()">본문 전체 복사</button> <span id="msg"></span></div>
 <ol>
  <li>블로그 글쓰기에서 제목을 붙여넣고, 본문 칸을 누른 뒤 <b>본문 전체 복사</b> 한 것을 붙여넣습니다.</li>
  <li>사진이 안 보이면 같은 폴더 <code>images/</code> 의 사진을 번호대로 끌어다 넣습니다.</li>
  <li>맨 위 광고 문구(수수료 안내)는 지우지 마세요. 공정위 지침상 꼭 있어야 합니다.</li>
  <li>상품마다 한두 줄 직접 느낀 점을 덧붙이면 검색 노출에 유리합니다.</li>
  <li>링크 몇 개를 눌러 상품 페이지가 열리는지 확인한 뒤 발행합니다.</li>
 </ol>
</div>
<div id="article">
{article}
</div></div>
<script>
function say(m){{document.getElementById('msg').textContent=m;setTimeout(()=>say2(),2500)}}
function say2(){{document.getElementById('msg').textContent=''}}
function sel(el){{const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);return s}}
function copyArticle(){{const s=sel(document.getElementById('article'));let ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}s.removeAllRanges();say(ok?'복사됐습니다. 블로그 본문에 붙여넣으세요.':'자동 복사가 안 됩니다. 본문을 직접 드래그해서 복사하세요.')}}
function copyText(id){{const s=sel(document.getElementById(id));try{{document.execCommand('copy')}}catch(e){{}}s.removeAllRanges();say('복사됐습니다.')}}
</script></body></html>
"""
