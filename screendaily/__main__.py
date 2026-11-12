"""사용법:
  python -m screendaily new 2026-11-17 19:00 [--reel]   # 예약 게시물 폴더 만들기
  python -m screendaily preview [폴더명 ...]             # 미리보기 이미지/영상 생성 (queue/*/out)
  python -m screendaily list                            # 예약 목록
  python -m screendaily publish-due [--dry-run] [--no-git]  # 시간이 된 게시물 업로드
  python -m screendaily check                           # 토큰/계정 확인
  python -m screendaily refresh-token                   # 토큰 60일 연장
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from . import PUBLISHED_DIR, QUEUE_DIR, ROOT
from .generate import generate
from .post import list_posts, load_config

MAX_ATTEMPTS = 3

TEMPLATE = """\
# 예약 시간 (config.yml 의 timezone 기준, 기본 한국시간)
publish_at: "{when}"
format: {fmt}            # carousel(넘겨보기) 또는 reel(릴스 영상)
draft: false             # true 면 업로드하지 않음

label: MOOD              # MOOD / WEEKEND / HIDDEN / ISSUE
theme: dark              # dark 또는 light
title: "퇴근하고\\n아무 생각 없이\\n보는 것들"     # \\n = 줄바꿈
subtitle: "머리 비우고 보기 좋은 5편"
bubble: "출근 전날 밤 필수ㅠ"                   # 빨간 테두리 반응 말풍선 (비워도 됨)
cover_image: ""          # 표지 사진 (이 폴더 안 파일명, 예: cover.jpg)

items:                   # 최대 8개
  - title: 작품 제목
    ott: 넷플릭스
    genre: 코미디 · 드라마
    desc: 스포일러 없는 한 줄 소개를 적어 주세요.
    image: ""            # 예: 01.jpg (이 폴더에 넣기)
    bubble: ""           # 작품별 반응 말풍선 (선택)

caption: |
  오늘 뭐 볼지 고민될 때 🍿
  여기서 본 거 몇 개인가요? 댓글로 알려주세요!

  저장해두고 주말에 꺼내 보기 🔖
hashtags: [퇴근후드라마, 힐링드라마]
credits: "이미지 출처: 각 제작사 및 OTT"
"""


def tz(config) -> ZoneInfo:
    return ZoneInfo(config.get("timezone", "Asia/Seoul"))


# ---------------------------------------------------------------- git

def git(*args: str, check=True) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True, text=True).stdout.strip()


def git_commit_push(message: str) -> str:
    git("add", "-A", "queue", "published")
    if git("status", "--porcelain", "queue", "published"):
        git("commit", "-m", message)
    for attempt in range(4):
        try:
            git("pull", "--rebase", "--autostash")
            git("push")
            break
        except subprocess.CalledProcessError as e:
            if attempt == 3:
                raise RuntimeError(f"git push 실패: {e.stderr}") from None
            time.sleep(2 ** (attempt + 1))
    return git("rev-parse", "HEAD")


def raw_url(sha: str, path) -> str:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        url = git("remote", "get-url", "origin")
        repo = url.rstrip("/").removesuffix(".git").split("github.com")[-1].lstrip(":/")
        repo = "/".join(repo.split("/")[-2:])
    rel = path.relative_to(ROOT).as_posix()
    return f"https://raw.githubusercontent.com/{repo}/{sha}/{rel}"


def wait_urls(urls: list[str], timeout=120):
    deadline = time.time() + timeout
    for u in urls:
        while True:
            try:
                if requests.head(u, timeout=20).status_code == 200:
                    break
            except requests.RequestException:
                pass
            if time.time() > deadline:
                raise RuntimeError(f"이미지 주소에 접근할 수 없습니다(레포가 공개인지 확인): {u}")
            time.sleep(5)


# ---------------------------------------------------------------- 명령

def cmd_new(a, config):
    when = f"{a.date} {a.time}"
    datetime.strptime(when, "%Y-%m-%d %H:%M")
    d = QUEUE_DIR / f"{a.date}_{a.time.replace(':', '')}"
    if d.exists():
        sys.exit(f"이미 있습니다: {d}")
    d.mkdir(parents=True)
    (d / "post.yml").write_text(TEMPLATE.format(when=when, fmt="reel" if a.reel else "carousel"), encoding="utf-8")
    print(f"만들었습니다: {d.relative_to(ROOT)}/post.yml")


def cmd_list(a, config):
    now = datetime.now(tz(config))
    for p in list_posts(QUEUE_DIR, config):
        state = "초안" if p.draft else ("업로드 대기(시간 지남)" if p.publish_at <= now else "예약됨")
        print(f"{p.publish_at:%Y-%m-%d %H:%M}  {p.format:8s}  [{state}]  {p.name}  {p.title.splitlines()[0]}")


def cmd_preview(a, config):
    posts = list_posts(QUEUE_DIR, config)
    if a.slots:
        posts = [p for p in posts if p.name in a.slots]
    changed = False
    for p in posts:
        before = (p.out_dir / ".hash").read_text() if (p.out_dir / ".hash").exists() else ""
        files = generate(p, config, force=a.force)
        after = (p.out_dir / ".hash").read_text()
        changed |= before != after
        print(f"{p.name}: {len(files)}개 파일 → {p.out_dir.relative_to(ROOT)}")
    if a.commit and changed:
        git_commit_push("chore: 미리보기 생성")


def cmd_due(a, config):
    """시간이 된 게시물 수 (워크플로에서 불필요한 설치를 건너뛰는 용도)."""
    now = datetime.now(tz(config))
    n = sum(1 for p in list_posts(QUEUE_DIR, config) if not p.draft and p.publish_at <= now)
    print(n)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"count={n}\n")


def cmd_check(a, config):
    from .instagram import Instagram
    ig = Instagram.from_env()
    info = ig.me()
    print(f"연결 확인: @{info.get('username')} (user_id {info.get('user_id')})")


def cmd_refresh(a, config):
    from .instagram import Instagram
    ig = Instagram.from_env()
    data = ig.refresh_token()
    new = data["access_token"]
    days = int(data.get("expires_in", 0)) // 86400
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::add-mask::{new}")
    print(f"토큰 연장 완료: 앞으로 약 {days}일 유효")
    if new != ig.token:
        if os.environ.get("GH_TOKEN") and shutil.which("gh"):
            subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--body", new], check=True, cwd=ROOT)
            print("새 토큰을 GitHub Secret(IG_ACCESS_TOKEN)에 저장했습니다")
        else:
            print("⚠ 새 토큰 문자열이 발급됐습니다. SECRETS_PAT 을 설정하면 자동 저장됩니다(README 참고).")


def cmd_publish_due(a, config):
    now = datetime.now(tz(config))
    due = [p for p in list_posts(QUEUE_DIR, config) if not p.draft and p.publish_at <= now]
    if not due:
        print("지금 올릴 게시물이 없습니다.")
        return 0

    ig = None
    if not a.dry_run:
        from .instagram import Instagram
        ig = Instagram.from_env()

    errors = 0
    for post in due:
        fail_file = post.dir / "failures.json"
        fails = json.loads(fail_file.read_text()) if fail_file.exists() else []
        if len(fails) >= MAX_ATTEMPTS:
            print(f"[{post.name}] {MAX_ATTEMPTS}번 실패해서 건너뜁니다. failures.json 확인 후 삭제하면 다시 시도합니다.")
            continue
        print(f"[{post.name}] 업로드 시작 ({post.format})")
        try:
            files = generate(post, config)
            caption = post.full_caption(config)
            if a.dry_run:
                print(f"  (테스트) {len(files)}개 파일, 캡션 {len(caption)}자 — 실제 업로드 안 함")
                continue
            if post.format == "carousel":
                sha = git_commit_push(f"chore: {post.name} 업로드 준비") if a.git else git("rev-parse", "HEAD")
                urls = [raw_url(sha, f) for f in files]
                wait_urls(urls)
                media_id = ig.post_carousel(urls, caption)
            elif os.environ.get("REEL_UPLOAD_MODE") == "url":
                sha = git_commit_push(f"chore: {post.name} 업로드 준비") if a.git else git("rev-parse", "HEAD")
                url = raw_url(sha, files[0])
                wait_urls([url])
                media_id = ig.post_reel_url(url, caption)
            else:
                media_id = ig.post_reel_file(files[0], caption)

            link = ig.permalink(media_id)
            dest = PUBLISHED_DIR / post.name
            if dest.exists():
                dest = PUBLISHED_DIR / f"{post.name}_{int(time.time())}"
            shutil.move(str(post.dir), dest)
            (dest / "failures.json").unlink(missing_ok=True)
            (dest / "result.json").write_text(json.dumps({
                "media_id": media_id, "permalink": link,
                "published_at": datetime.now(tz(config)).isoformat(timespec="seconds"),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✅ 완료 {link or media_id}")
            if a.git:
                git_commit_push(f"post: {post.name} 업로드 완료")
        except Exception as e:  # noqa: BLE001
            errors += 1
            print(f"  ❌ 실패: {e}", file=sys.stderr)
            fails.append({"at": datetime.now(tz(config)).isoformat(timespec="seconds"), "error": str(e)[:500]})
            if post.dir.exists():
                fail_file.write_text(json.dumps(fails, ensure_ascii=False, indent=2), encoding="utf-8")
                if a.git:
                    try:
                        git_commit_push(f"chore: {post.name} 업로드 실패 기록")
                    except Exception as ge:  # noqa: BLE001
                        print(f"  (실패 기록 push 도 실패: {ge})", file=sys.stderr)
    return 1 if errors else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="screendaily", description="스크린데일리 자동 업로드")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="예약 게시물 폴더 만들기")
    s.add_argument("date", help="2026-11-17")
    s.add_argument("time", help="19:00")
    s.add_argument("--reel", action="store_true", help="릴스 영상으로 만들기")

    sub.add_parser("list", help="예약 목록")

    s = sub.add_parser("preview", help="미리보기 생성")
    s.add_argument("slots", nargs="*")
    s.add_argument("--force", action="store_true")
    s.add_argument("--commit", action="store_true", help="생성 결과를 커밋/푸시")

    s = sub.add_parser("publish-due", help="시간이 된 게시물 업로드")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--no-git", dest="git", action="store_false")

    sub.add_parser("due", help="시간이 된 게시물 수")
    sub.add_parser("check", help="토큰/계정 확인")
    sub.add_parser("refresh-token", help="토큰 연장")

    a = ap.parse_args(argv)
    config = load_config()
    handler = {
        "new": cmd_new, "list": cmd_list, "due": cmd_due, "preview": cmd_preview, "check": cmd_check,
        "refresh-token": cmd_refresh, "publish-due": cmd_publish_due,
    }[a.cmd]
    sys.exit(handler(a, config) or 0)


if __name__ == "__main__":
    main()
