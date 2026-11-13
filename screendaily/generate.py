"""post.yml → out/ (카드 JPG, 릴스 MP4) 생성."""
from __future__ import annotations

import shutil
from pathlib import Path

from . import ROOT
from .cards import render_all
from .letterbox import render_letterbox
from .post import Post, channel_config
from .reel import build_reel, reel_frame


def outputs(post: Post) -> list[Path]:
    """업로드에 쓰는 파일 목록 (캐러셀: 이미지들, 릴스: 영상 1개)."""
    if post.format == "reel":
        return [post.out_dir / "reel.mp4"]
    return sorted(post.out_dir.glob("[0-9][0-9].jpg"))


def is_fresh(post: Post) -> bool:
    h = post.out_dir / ".hash"
    return h.exists() and h.read_text().strip() == post.source_hash() and all(p.exists() for p in outputs(post)) \
        and bool(outputs(post))


def generate(post: Post, config: dict, force: bool = False) -> list[Path]:
    config = channel_config(config, post)
    if not force and is_fresh(post):
        return outputs(post)
    out = post.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    letterbox = post.layout == "letterbox"
    slides = render_letterbox(post, config) if letterbox else render_all(post, config)
    for i, im in enumerate(slides, 1):
        im.save(out / f"{i:02d}.jpg", "JPEG", quality=92, optimize=True, progressive=True)

    if post.format == "reel":
        fdir = out / "frames"
        fdir.mkdir()
        frames = []
        for i, im in enumerate(slides, 1):
            p = fdir / f"{i:02d}.jpg"
            # letterbox 는 이미 9:16 프레임
            (im if letterbox else reel_frame(im, config.get("brand", "SCREEN DAILY"))).save(p, "JPEG", quality=92)
            frames.append(p)
        rc = config.get("reel", {})
        bgm_rel = post.bgm or rc.get("bgm") or ""
        bgm = None
        if bgm_rel:
            cand = [post.dir / bgm_rel, ROOT / bgm_rel]
            bgm = next((c for c in cand if c.is_file()), None)
            if bgm is None:
                raise FileNotFoundError(f"[{post.name}] 배경음악 파일이 없습니다: {bgm_rel}")
        build_reel(frames, out / "reel.mp4", float(rc.get("seconds_per_slide", 3.0)),
                   float(rc.get("transition", 0.4)), bgm, float(rc.get("bgm_volume", 0.8)),
                   zoom=0.0 if letterbox else 0.05)  # letterbox: 후킹 문구가 흔들리지 않게 확대 없음

    (out / "caption.txt").write_text(post.full_caption(config), encoding="utf-8")
    (out / ".hash").write_text(post.source_hash())
    return outputs(post)
