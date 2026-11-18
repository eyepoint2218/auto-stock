"""GPT 이미지 프롬프트(한 번에 복붙) 만들기."""
from __future__ import annotations

STYLE = """[4장 모두 공통]
- 한국 역사 웹툰풍 일러스트. 실사와 웹툰의 중간 정도로 자연스럽게 묘사한 인물. 손으로 그린 듯한 선화와 차분하고 자연스러운 채색, 은은한 종이 질감.
- {era} 배경과 복식 고증.
- 4장 모두 같은 화풍, 같은 색감, 같은 주인공({hero})으로 일관되게 그릴 것.
- 2~4번째 그림에서는 주인공의 얼굴과 옆얼굴을 절대 보이지 않게(뒷모습·손·실루엣만). 마지막 그림에서만 정면 얼굴 공개.
- 지나치게 매끈한 AI 질감, 과한 광택, 과장된 표정, 시대에 맞지 않는 복식, 중국·일본풍 복식 금지.
- 그림 안에 글자·한자·로고·서명·워터마크를 넣지 말 것.
- 나중에 글자를 올릴 자리를 비워 둘 것(각 장에 적힌 위치). 중요한 요소는 위아래 가장자리에 두지 않는다."""

SPACE = {"bottom": "화면 아래 1/3은 어둡고 단순하게 비워 둔다.",
         "top": "화면 위 1/3은 하늘이나 지붕처럼 단순하게 비워 둔다."}


def build(ep: dict) -> str:
    from .render import story_keys
    img = ep["images"]
    keys = [*story_keys(ep), 5]
    n = len(keys)
    order = " → ".join(f"{i}번" for i in range(1, n + 1))
    head = (f"역사 인스타그램 캐러셀에 쓸 삽화 {n}장을 차례로 만들어줘. 각 장은 별도의 이미지 1장씩, "
            f"세로 1024×1536으로 생성해줘. 한 장 만들 때마다 멈추지 말고 {order} 순서로 이어서 만들어줘.")
    body = [head, "", STYLE.format(era=img["era"], hero=img["hero"]).replace("4장 모두", f"{n}장 모두")
            .replace("2~4번째 그림", f"1~{n - 1}번째 그림"), ""]
    for i, no in enumerate(keys, 1):
        pos = ep["slides"][no].get("pos", "top" if no == 4 else "bottom")
        scene = img["scenes"][no].strip()
        if no == 5:
            scene += " 인물은 화면 가운데 위쪽에 두고, 화면 아래 1/3은 단순하게 비워 둔다."
        else:
            scene += " " + SPACE[pos]
        body.append(f"[{i}번 그림] {scene}")
        body.append("")
    return "\n".join(body).strip() + "\n"
