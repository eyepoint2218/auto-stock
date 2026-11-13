"""Instagram 콘텐츠 게시 API 클라이언트.

두 가지 토큰을 모두 지원한다 (IG_API_HOST 로 선택):
- graph.instagram.com (기본): Instagram 로그인 토큰. 권한 instagram_business_basic, instagram_business_content_publish
- graph.facebook.com: 통합 로그인/비즈니스용 Facebook 로그인, 시스템 사용자 토큰(만료 없음).
  권한 instagram_basic, instagram_content_publish. IG_USER_ID(인스타 비즈니스 계정 ID) 필수.
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
    def __init__(self, token: str, user_id: str | None = None, version: str | None = None,
                 host: str | None = None):
        if not token:
            raise InstagramError("IG_ACCESS_TOKEN 이 설정되지 않았습니다 (GitHub Secrets 확인)")
        self.token = token
        self.version = version or os.environ.get("IG_API_VERSION") or DEFAULT_VERSION
        self.host = (host or os.environ.get("IG_API_HOST") or "graph.instagram.com").strip()
        self.base = f"https://{self.host}/{self.version}"
        if self.facebook:
            if not user_id:
                raise InstagramError("graph.facebook.com 방식은 IG_USER_ID(인스타 비즈니스 계정 ID)가 필요합니다")
            self.user_id = user_id
        else:
            self.user_id = user_id or self.me()["user_id"]

    @property
    def facebook(self) -> bool:
        return self.host == "graph.facebook.com"

    @classmethod
    def from_env(cls, suffix: str = "") -> "Instagram":
        """suffix 가 있으면 IG_ACCESS_TOKEN_<SUFFIX> / IG_USER_ID_<SUFFIX> / IG_API_HOST_<SUFFIX> (다른 채널 계정)."""
        sfx = f"_{suffix.upper()}" if suffix else ""
        token = os.environ.get("IG_ACCESS_TOKEN" + sfx, "").strip()
        if suffix and not token:
            raise InstagramError(f"IG_ACCESS_TOKEN{sfx} 이 설정되지 않았습니다 (GitHub Secrets 확인)")
        host = os.environ.get("IG_API_HOST" + sfx, "").strip() or None
        return cls(token, os.environ.get("IG_USER_ID" + sfx, "").strip() or None, host=host)

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
        if self.facebook:
            info = self._call("GET", self.user_id, fields="id,username")
            return {"user_id": info.get("id"), "username": info.get("username")}
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
        try:
            return self._call("POST", f"{self.user_id}/media_publish", creation_id=container_id)["id"]
        except InstagramError:
            # 인스타가 오류를 돌려주면서도 실제로는 몇 초~몇 분 뒤 게시하는 경우가 있다 → 최대 2분 확인
            for _ in range(8):
                time.sleep(15)
                try:
                    st = self._call("GET", container_id, fields="status_code")
                except InstagramError:
                    st = {}
                if st.get("status_code") == "PUBLISHED":
                    recent = self.recent_media(1)
                    if recent:
                        return recent[0]["id"]
            raise

    def recent_media(self, limit: int = 10) -> list[dict]:
        try:
            return self._call("GET", f"{self.user_id}/media", fields="id,caption,timestamp,permalink",
                              limit=str(limit)).get("data", [])
        except InstagramError:
            return []

    def find_published(self, caption: str, limit: int = 10) -> dict | None:
        """같은 캡션으로 이미 올라간 게시물이 있으면 반환 (중복 게시 방지)."""
        key = caption.strip()[:80]
        for m in self.recent_media(limit):
            if key and (m.get("caption") or "").strip()[:80] == key:
                return m
        return None

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
        """장기 토큰(60일) 연장. 발급 후 24시간이 지나야 가능. 시스템 사용자 토큰은 만료가 없어 불필요."""
        if self.facebook:
            return {"access_token": self.token, "expires_in": 0, "never_expires": True}
        r = requests.get("https://graph.instagram.com/refresh_access_token",
                         params={"grant_type": "ig_refresh_token", "access_token": self.token}, timeout=60)
        data = r.json()
        if r.status_code >= 400 or "error" in data:
            raise InstagramError(f"토큰 갱신 실패: {data.get('error', {}).get('message', r.text[:200])}")
        return data
