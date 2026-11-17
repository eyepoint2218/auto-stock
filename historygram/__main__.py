"""역사그램 CLI.

  python -m historygram next                 # 다음에 만들 인물(people.yml) 보기
  python -m historygram new 2 김점동 kimjeomdong   # 새 회차 폴더 + episode.yml 뼈대
  python -m historygram check ep02           # 규칙 검사
  python -m historygram prompt ep02          # GPT 이미지 프롬프트(한 번에 복붙) 출력 + gpt_prompt.txt
  python -m historygram ingest ep02 2장.png 3장.png 4장.png 5장.png   # GPT 삽화를 art_02~05.jpg 로 저장
  python -m historygram render ep02          # out/ 에 PNG(삽화 없으면 배치 미리보기) + preview.png (+ 6장 다 있으면 zip)
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import yaml

from . import prompt as P
from . import render as R

PKG = Path(__file__).resolve().parent
EPISODES = PKG / "episodes"
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️]")
GREET = ("안녕하세요", "오늘은", "소개해")


def folder_of(key: str) -> Path:
    num = int(re.sub(r"\D", "", key.split("_")[0]) or 0)
    hits = sorted(EPISODES.glob(f"ep{num:02d}_*"))
    if not hits:
        sys.exit(f"회차 폴더 없음: ep{num:02d}_*")
    return hits[0]


def load(folder: Path) -> dict:
    return yaml.safe_load((folder / "episode.yml").read_text(encoding="utf-8"))


def caption_of(ep: dict) -> str:
    tags = " ".join("#" + t.lstrip("#") for t in ep["hashtags"])
    intro = (PKG / "channel_intro.txt").read_text(encoding="utf-8").strip()
    return f"{ep['caption'].strip()}\n\n{intro}\n\n{tags}\n"


def check(ep: dict) -> list[str]:
    warn = []
    name = ep["slides"][5]["name"]
    for no in (1, 2, 3, 4):
        for line in ep["slides"][no]["lines"]:
            if name in R.plain(line):
                warn.append(f"{no}장에 이름 노출: {line}")
    for no in (2, 3, 4):
        if name in ep["images"]["scenes"][no]:
            warn.append(f"{no}장 그림 프롬프트에 이름이 들어감(얼굴 공개 위험)")
    texts = [ep["caption"], *ep["hashtags"], ep["slides"][5]["desc"]]
    texts += [l for no in (1, 2, 3, 4) for l in ep["slides"][no]["lines"]]
    if any(EMOJI.search(t) for t in texts):
        warn.append("이모지 사용 금지")
    if len(ep["hashtags"]) > 5:
        warn.append(f"해시태그 {len(ep['hashtags'])}개 (최대 5개)")
    if ep["caption"].strip().startswith(GREET):
        warn.append("게시글이 인사로 시작함")
    if not ep.get("sources"):
        warn.append("sources(사료·출처) 비어 있음")
    if not ep.get("staging"):
        warn.append("staging(사실과 연출 구분) 비어 있음")
    for no in (1, 2, 3, 4):
        lines = ep["slides"][no]["lines"]
        base = ep["slides"][no].get("size", 104 if no == 1 else R.DEFAULTS[no]["size"])
        if R.fit_size(lines, R.BLACK_F, base, 0) < 60:
            warn.append(f"{no}장 글자가 길어 60px 미만으로 줄어듦 → 줄을 나누거나 줄이기")
    return warn


def main(argv: list[str]) -> None:
    if not argv:
        sys.exit(__doc__)
    cmd, *rest = argv

    if cmd == "next":
        people = yaml.safe_load((PKG / "people.yml").read_text(encoding="utf-8"))
        todo = [p for p in people if not p.get("done")]
        for p in todo[:5]:
            print(f"- {p['name']} ({p['years']}): {p['hook']}")
        return

    if cmd == "new":
        num, name, slug = int(rest[0]), rest[1], rest[2]
        folder = EPISODES / f"ep{num:02d}_{slug}"
        if folder.exists():
            sys.exit(f"이미 있음: {folder}")
        folder.mkdir(parents=True)
        tpl = (PKG / "template.yml").read_text(encoding="utf-8")
        (folder / "episode.yml").write_text(tpl.replace("{NUM}", str(num)).replace("{NAME}", name), encoding="utf-8")
        print(folder / "episode.yml")
        return

    folder = folder_of(rest[0])
    ep = load(folder)

    if cmd == "check":
        warn = check(ep)
        print("\n".join(f"경고: {w}" for w in warn) or "문제 없음")
        sys.exit(1 if warn else 0)

    if cmd == "prompt":
        text = P.build(ep)
        (folder / "gpt_prompt.txt").write_text(text, encoding="utf-8")
        print(text)
        return

    if cmd == "ingest":
        from PIL import Image
        if len(rest) != 5:
            sys.exit("사용: ingest epNN 2장 3장 4장 5장 (순서대로 이미지 4개)")
        for no, src in zip((2, 3, 4, 5), rest[1:]):
            dst = folder / f"art_{no:02d}.jpg"
            Image.open(src).convert("RGB").save(dst, quality=92)
            (folder / f"art_{no:02d}.png").unlink(missing_ok=True)
            print(dst)
        return

    if cmd == "render":
        for w in check(ep):
            print(f"경고: {w}")
        saved = R.render_episode(ep, folder)
        z = R.pack(folder, caption_of(ep))
        for p in saved:
            print(p)
        print(folder / "out/preview.png")
        print(z if z else "삽화가 아직 없는 장이 있어 zip 은 만들지 않음 (*_layout.png = 배치 미리보기)")
        return

    sys.exit(f"알 수 없는 명령: {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:])
