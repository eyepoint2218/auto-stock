"""Instagram API (Instagram 로그인 방식, graph.instagram.com) 업로드 클라이언트.

필요 권한: instagram_business_basic, instagram_business_content_publish
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

DEFAULT_VERSION = "v22.0"


class InstagramError(RuntimeError):
    pass


class Instagram:
    def __init__(self, token: str, user_id: str | None = None, version: str | None = None):
        if not token:
            raise InstagramError("IG_ACCESS_TOKEN 이 설정되지 않았습니다 (GitHub Secrets 확인)")
        self.token = token
        self.version = version or os.environ.get("IG_API_VERSION") or DEFAULT_VERSION
        self.base = f"https://graph.instagram.com/{self.version}"
        self.user_id = user_id or self.me()["user_id"]

    @classmethod
    def from_env(cls) -> "Instagram":
        return cls(os.environ.get("IG_ACCESS_TOKEN", "").strip(), os.environ.get("IG_USER_ID", "").strip() or None)

    # ------------------------------------------------------------ 공통
    def _call(self, method: str, path: str, **params) -> dict:
        url = path if path.startswith("http") else f"{self.base}/{path.lstrip('/')}"
        params["access_token"] = self.token
        for attempt in range(3):
            try:
                if method == "GET":
                    r = requests.get(url, params=params, timeout=60)
                else:
                    r = requests.post(url, data=params, timeout=120)
            except requests.RequestException as e:
                if attempt == 2:
                    raise InstagramError(f"네트워크 오류: {e}") from None
                time.sleep(5 * (attempt + 1))
                continue
            data = r.json() if r.content else {}
            if r.status_code >= 500 and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code >= 400 or "error" in data:
                err = data.get("error", {})
                msg = err.get("error_user_msg") or err.get("message") or r.text[:300]
                raise InstagramError(f"API 오류 {r.status_code} ({path.split('?')[0]}): {msg}")
            return data
        raise InstagramError("API 호출 실패")

    def me(self) -> dict:
        return self._call("GET", "me", fields="user_id,username")

    # ------------------------------------------------------------ 컨테이너
    def wait_ready(self, container_id: str, timeout: int = 600) -> None:
        start = time.time()
        while True:
            st = self._call("GET", container_id, fields="status_code,status")
            code = st.get("status_code")
            if code in ("FINISHED", "PUBLISHED"):
                return
            if code in ("ERROR", "EXPIRED"):
                raise InstagramError(f"미디어 처리 실패: {st.get('status')}")
            if time.time() - start > timeout:
                raise InstagramError(f"미디어 처리 시간 초과 ({code})")
            time.sleep(5)

    def publish(self, container_id: str) -> str:
        self.wait_ready(container_id)
        return self._call("POST", f"{self.user_id}/media_publish", creation_id=container_id)["id"]

    def permalink(self, media_id: str) -> str:
        try:
            return self._call("GET", media_id, fields="permalink").get("permalink", "")
        except InstagramError:
            return ""

    # ------------------------------------------------------------ 게시
    def post_image(self, url: str, caption: str) -> str:
        c = self._call("POST", f"{self.user_id}/media", image_url=url, caption=caption)
        return self.publish(c["id"])

    def post_carousel(self, urls: list[str], caption: str) -> str:
        if len(urls) == 1:
            return self.post_image(urls[0], caption)
        if not 2 <= len(urls) <= 10:
            raise InstagramError(f"캐러셀은 2~10장이어야 합니다 (현재 {len(urls)}장)")
        children = []
        for u in urls:
            c = self._call("POST", f"{self.user_id}/media", image_url=u, is_carousel_item="true")
            children.append(c["id"])
        for cid in children:
            self.wait_ready(cid, timeout=300)
        c = self._call("POST", f"{self.user_id}/media", media_type="CAROUSEL",
                       children=",".join(children), caption=caption)
        return self.publish(c["id"])

    def post_reel_file(self, path: Path, caption: str, share_to_feed: bool = True) -> str:
        """로컬 영상 파일을 resumable 업로드 방식으로 올린다 (공개 URL 불필요)."""
        c = self._call("POST", f"{self.user_id}/media", media_type="REELS", upload_type="resumable",
                       caption=caption, share_to_feed=str(share_to_feed).lower())
        uri = c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{self.version}/{c['id']}"
        data = path.read_bytes()
        r = requests.post(uri, data=data, timeout=600, headers={
            "Authorization": f"OAuth {self.token}",
            "offset": "0",
            "file_size": str(len(data)),
        })
        if r.status_code >= 400:
            raise InstagramError(f"영상 업로드 실패 {r.status_code}: {r.text[:300]}")
        return self.publish(c["id"])

    def post_reel_url(self, url: str, caption: str, share_to_feed: bool = True) -> str:
        c = self._call("POST", f"{self.user_id}/media", media_type="REELS", video_url=url,
                       caption=caption, share_to_feed=str(share_to_feed).lower())
        return self.publish(c["id"])

    # ------------------------------------------------------------ 토큰
    def refresh_token(self) -> dict:
        """장기 토큰(60일) 연장. 발급 후 24시간이 지나야 가능."""
        r = requests.get("https://graph.instagram.com/refresh_access_token",
                         params={"grant_type": "ig_refresh_token", "access_token": self.token}, timeout=60)
        data = r.json()
        if r.status_code >= 400 or "error" in data:
            raise InstagramError(f"토큰 갱신 실패: {data.get('error', {}).get('message', r.text[:200])}")
        return data
