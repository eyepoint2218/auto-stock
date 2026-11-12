"""카드 이미지로 릴스 영상(1080x1920, 9:16) 만들기. ffmpeg 필요."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageFilter

from .cards import cover_crop

RW, RH = 1080, 1920
CARD_Y = 230  # 카드 위치 (아래쪽 릴스 UI 를 피해서 살짝 위로)
FPS = 30


def reel_frame(card: Image.Image, brand: str) -> Image.Image:
    """4:5 카드를 흐린 배경 위에 올린 9:16 프레임."""
    bg = cover_crop(card, (RW, RH), (0.5, 0.5)).filter(ImageFilter.GaussianBlur(45))
    bg = Image.blend(bg, Image.new("RGB", (RW, RH), (0, 0, 0)), 0.55)
    c = card.resize((RW, int(card.height * RW / card.width)), Image.LANCZOS)
    bg.paste(c, (0, CARD_Y))
    return bg


def build_reel(frames: list[Path], out: Path, seconds: float = 3.0, transition: float = 0.4,
               bgm: Path | None = None, bgm_volume: float = 0.8) -> float:
    """프레임 이미지들을 천천히 확대 + 페이드 전환하는 영상으로 만든다. 길이(초)를 반환."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg 가 설치되어 있지 않습니다")
    n = len(frames)
    durs = [seconds] * n
    durs[0] = max(2.0, seconds - 0.5)  # 표지는 조금 짧게
    total = sum(durs) - transition * (n - 1)

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for f in frames:
        cmd += ["-i", str(f)]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm)]
    else:
        cmd += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]

    parts = []
    for i, d in enumerate(durs):
        nf = int(round(d * FPS))
        # 2배로 키운 뒤 zoompan 하면 확대가 덜 떨린다
        parts.append(
            f"[{i}:v]scale={RW * 2}:{RH * 2},"
            f"zoompan=z='1+0.05*on/{nf}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s={RW}x{RH}:fps={FPS},"
            f"setsar=1,format=yuv420p[v{i}]"
        )
    last = "v0"
    offset = 0.0
    for i in range(1, n):
        offset += durs[i - 1] - transition
        parts.append(f"[{last}][v{i}]xfade=transition=fade:duration={transition}:offset={offset:.3f}[x{i}]")
        last = f"x{i}"
    a = n
    if bgm:
        parts.append(
            f"[{a}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={bgm_volume},"
            f"afade=t=in:d=0.5,afade=t=out:st={max(0, total - 1.5):.3f}:d=1.5[aout]"
        )
    else:
        parts.append(f"[{a}:a]anull[aout]")

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", f"[{last}]", "-map", "[aout]",
        "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-profile:v", "high",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return total
