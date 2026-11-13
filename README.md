# 스크린데일리 인스타 자동 업로드

`post.yml` 하나만 적어 두면 **카드뉴스(캐러셀)나 릴스 영상을 자동으로 만들고, 예약한 시간에 인스타그램에 올립니다.**
서버 없이 GitHub Actions(무료)로 돌아갑니다.

```
queue/2026-11-17_1900/post.yml  ──▶  카드 이미지 / 릴스 영상 자동 생성  ──▶  예약 시간에 업로드  ──▶  published/ 로 이동
```

---

## 1. 처음 한 번만: 준비

### ① 인스타그램 + Meta 앱 (토큰 발급)
1. 인스타 계정을 **프로페셔널(크리에이터/비즈니스)** 계정으로 전환
2. [developers.facebook.com](https://developers.facebook.com) → **내 앱 → 앱 만들기**
   → 사용 사례 **"Instagram에서 메시지 및 콘텐츠 관리"** 선택
3. 앱 대시보드 → **Instagram → Instagram 로그인을 통한 API 설정**
   - **앱 역할 → Instagram 테스터 추가** 에 스크린데일리 계정 입력
   - 인스타 **설정 → 웹사이트 권한 → 앱 및 웹사이트 → 테스터 초대** 수락
4. 같은 화면에서 **액세스 토큰 생성** (권한: `instagram_business_basic`, `instagram_business_content_publish`)
   → 60일짜리 장기 토큰이 나옵니다. **절대 채팅·코드에 붙여넣지 마세요.**

### ② GitHub Secrets 등록
레포 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 | 필수 |
|---|---|---|
| `IG_ACCESS_TOKEN` | 위에서 받은 토큰 | ✅ |
| `IG_USER_ID` | 비워도 됨 (자동 조회) | |
| `SECRETS_PAT` | 토큰 자동 갱신 저장용 GitHub 토큰 (아래 참고) | 선택 |

### ②-B. 통합 로그인(비즈니스 설정의 시스템 사용자 토큰)을 쓰는 경우
Meta 화면에 "Instagram 로그인" 대신 **통합 로그인**만 보이면 이 방식으로 합니다. 이 토큰은 **만료되지 않습니다.**
1. business.facebook.com/settings → **계정 → Instagram 프로필** 에 계정 연결, **계정 → 앱** 에 앱 연결
2. **사용자 → 시스템 사용자 → 추가** (관리자) → **자산 할당**: 앱·Instagram 프로필 전체 관리
3. **토큰 생성**: 만료 "사용 안 함", 권한 `instagram_basic`, `instagram_content_publish`
4. GitHub 에 저장
   - Secrets: `IG_ACCESS_TOKEN` (토큰), `IG_USER_ID` (인스타 계정 숫자 ID, 보통 17841…)
   - **Variables**: `IG_API_HOST` = `graph.facebook.com`

### ③ 기본 브랜치에 합치기 + 연결 테스트
- 예약 실행(schedule)은 **기본 브랜치(main)에서만** 동작합니다. 이 코드를 main 에 합쳐 주세요.
- **Actions 탭 → "인스타 연결 테스트" → Run workflow** → 로그에 `연결 확인: @아이디` 가 나오면 성공.
- `config.yml` 의 `handle` 을 실제 인스타 아이디로 바꿔 주세요 (마지막 장에 표시됨).

---

## 2. 매주 할 일: 게시물 예약

### 방법 A. 휴대폰/웹에서 (GitHub 사이트)
1. 레포에서 **Add file → Create new file**
2. 파일 이름에 `queue/2026-11-17_1900/post.yml` 입력 (폴더가 자동 생성됨)
3. [`examples/mood_carousel/post.yml`](examples/mood_carousel/post.yml) 내용을 복사해서 고쳐 쓰고 **Commit**
4. 사진이 있으면 같은 폴더에 **Add file → Upload files** 로 올리고 `image:` 에 파일명 적기
5. 1~2분 뒤 같은 폴더의 `out/` 에 **미리보기 이미지**가 생깁니다 → 확인!

### 방법 B. 컴퓨터에서
```bash
pip install -r requirements.txt          # 릴스는 ffmpeg 도 필요
python -m screendaily new 2026-11-17 19:00          # 캐러셀
python -m screendaily new 2026-11-18 19:00 --reel   # 릴스
python -m screendaily preview            # queue/*/out 에 미리보기 생성
python -m screendaily list               # 예약 목록
python -m screendaily lint               # 후킹 규칙 검사 (CLAUDE.md 참고, 경고만)
git add queue && git commit -m "다음 주 예약" && git push
```

### post.yml 항목
| 항목 | 설명 |
|---|---|
| `publish_at` | 올릴 시간 `"2026-11-17 19:00"` (한국시간) |
| `format` | `carousel` (넘겨보기) / `reel` (릴스 영상) |
| `label` | `MOOD` / `WEEKEND` / `HIDDEN` / `ISSUE` (색이 다름, `config.yml` 에서 추가 가능) |
| `theme` | `dark` / `light` (베이지 톤) |
| `title` | 표지 제목. `\n` 으로 줄바꿈 |
| `subtitle` | 제목 아래 한 줄 |
| `bubble` | 빨간 테두리 반응 말풍선 ("3화부터 미쳐요ㅠ") |
| `cover_image` | 표지 사진 (없으면 작품 사진들로 콜라주) |
| `items` | 작품 목록 최대 8개: `title`, `ott`, `genre`, `desc`, `image`, `bubble`, `wiki` |
| `items[].tmdb` | TMDB 작품 지정. `tv/93405`(ID) · `tv` 또는 `movie`(드라마/영화만 검색) · `movie:검색어`(검색어 지정). 비우면 제목으로 검색 |
| `items[].wiki` | 영문 위키백과 문서 제목 (예: `Squid Game`). 사진을 안 넣으면 대표 이미지(보통 공식 포스터)를 자동으로 가져오고 카드에 출처를 표시 |
| `images` | 직접 만든 이미지로 올릴 때 (이걸 쓰면 자동 디자인 생략) |
| `outro` | `false` 면 마지막 팔로우 유도 장 생략 |
| `outro_title` / `outro_cta` / `outro_save` / `outro_question` | 마지막 장 문구를 게시물마다 바꿀 때 (비우면 `config.yml` 기본값) |
| `caption` / `hashtags` / `credits` | 본문, 해시태그, 출처. 해시태그는 **최대 5개**: 게시물 `hashtags` 먼저, 남는 자리에 `config.yml` 기본 해시태그 |
| `draft` | `true` 면 올리지 않음 |
| `bgm` | 릴스 배경음악 파일 (아래 참고) |

---

## 공식 포스터·스틸컷 자동 가져오기 (TMDB)
1. [themoviedb.org](https://www.themoviedb.org) 가입 → 설정 → API → 개인용 키 신청
2. **API 읽기 액세스 토큰**(eyJ… 로 시작)을 GitHub **Secrets** 에 `TMDB_TOKEN` 으로 저장
3. 이후 `queue/` 에 게시물을 올리면 미리보기 워크플로가 작품 제목으로 검색해
   **글자 없는 공식 스틸컷**(작품 카드)과 **한국어 포스터**(표지 콜라주)를 `img/` 에 저장합니다.
- TMDB 에 없으면 `wiki:` 로 적은 영문 위키백과 대표 이미지를 씁니다. 직접 넣은 `image:` 가 항상 우선입니다.
- 카드 오른쪽 위에 `이미지 © OTT · via TMDB` 가 표시됩니다.
- This product uses the TMDB API but is not endorsed or certified by TMDB.

## 배우 소개 게시물
`post.yml` 에 `actor: 배우이름` 과 `label: ACTOR` 를 적으면
- 표지에 TMDB 배우 프로필 사진이 들어가고 (`사진 © TMDB` 표시)
- 작품은 **그 배우의 출연작 안에서** 찾아서 동명 작품과 헷갈리지 않습니다.
- 작품 카드에 **배역 이름**(예: ‘영숙’ 역)이 들어갑니다. TMDB 배역은 영어인 경우가 많아 `role: 영숙` 처럼 한국어로 적는 것을 권장합니다 (한글 배역만 자동 표시).
- 동명이인이면 `actor_tmdb: person/ID`, 마지막 장 질문은 `outro_question:` 으로 바꿀 수 있습니다.
- 예시: `examples/actor_jeonjongseo/` (대표작 소개), `examples/actor_story_ohjungse/` (데뷔부터 지금까지 타임라인)
- 배우 스토리 형식: 작품마다 `year: "1997"`(큰 숫자 대신 연도) 와 `stage: 데뷔`(단계 라벨) 를 적습니다.
- **배우 맞히기**: `reveal: true` 면 표지는 흐린 실루엣과 물음표, 이야기 카드는 이름 없이 넘길수록 배경이 선명해지고, 마지막에 정답 카드(사진과 이름, `reveal_text`)가 나옵니다.
- **추천작 카드**: `recommend:` 에 작품 2~4편(title, ott, role)을 적으면 정답 카드 다음에 "○○○, 이 작품에서 만나요" 포스터 카드가 들어갑니다 (제목은 `recommend_title`). 캐러셀 최대 10장이라 이야기 카드는 6장까지 쓸 수 있습니다.
- **인생 이야기 카드**: `type: story` 는 작품 사진 없이 연도·헤드라인·본문으로 읽히는 카드 (배경은 배우 사진을 흐리게), `type: quote` 는 수상 소감·인터뷰 한마디를 크게 보여주는 인용 카드입니다.
- **브랜드 색 카드**: 이야기 카드에 `brand: SKT` / `KT` / `LGU` 를 적으면 그 카드만 해당 브랜드 색(배경 빛·라벨)과 이름으로 바뀝니다. 로고는 쓰지 않습니다. 색은 `config.yml` 의 `brands:` 에서 추가·수정. `style: panel` 이면 밝은 배경 + 흰 패널 구성(SKT 기본값)이고, `desc` 에 `18 수 | 뚜레쥬르 · CGV` 처럼 `|` 를 넣은 줄은 달력 줄(왼쪽 날짜, 오른쪽 내용)로 그립니다. 게시물 맨 위에 `brand: SKT` 를 적으면 표지·마지막 장·brand 없는 카드까지 캐러셀 전체가 그 색이 됩니다. 예시: `drafts/telecom_tday_nov/`
- 출연 기록에 없는 작품은 동명 작품이 잡히지 않도록 사진 없이 진행합니다. `tmdb: none` 으로 직접 끌 수도 있습니다.

## 할인 정보 카드 (사진 + 두 줄)
- 혜택알람 채널(`channel: deals`)에서 통신사·카드·브랜드 할인 정보를 올릴 때: `items` 에 `type: deal` 을 적고 `title`(흰 글씨, 브랜드) + `desc`(노란 글씨, 혜택) 두 줄만 씁니다. 줄마다 12자 이하 권장 (lint 경고).
- `stage` = 왼쪽 위 칩 (예: KT), `year` = 날짜 칩 (예: ~11.30), `brand` = 칩·배경 색, `image` = 꽉 채울 사진 (없으면 통신사 색 배경)
- `wiki: Hamburger` 처럼 영문 위키백과 문서를 적으면 미리보기 워크플로가 대표 사진(자유 라이선스)을 받아 꽉 채우고, 카드에 작가·라이선스를 표시합니다. 할인 카드는 TMDB 검색을 하지 않습니다.
- 미리보기 워크플로는 `drafts/*/post.yml` 이 바뀌어도 돌아서 초안 사진·미리보기도 자동으로 만듭니다.
- 표지도 같은 모양으로: 게시물에 `cover_style: deal` (제목 마지막 줄이 노란색, `subtitle` 은 날짜 칩)
- 예시: `drafts/telecom_deals_nov/`

## 채널 여러 개 운영 (스크린데일리 외)
- `config.yml` 의 `channels:` 에 채널을 추가하고, 게시물에 `channel: deals` 처럼 적으면 그 채널의 이름(`brand`)·아이디(`handle`)·기본 해시태그·마지막 장 문구로 만들어집니다. 안 적으면 스크린데일리.
- 업로드 계정은 채널마다 다릅니다. GitHub **Secrets** 에 `IG_ACCESS_TOKEN_DEALS`, `IG_USER_ID_DEALS` (통합 로그인 방식이면 **Variables** 에 `IG_API_HOST_DEALS` = `graph.facebook.com`). 이름 끝은 채널의 `ig_secret_suffix`.
- 연결 확인: Actions → "인스타 연결 테스트" (DEALS 토큰이 있으면 같이 확인), 또는 `python -m screendaily check --channel deals`
- 같은 시간에 두 채널을 예약하면 폴더 이름이 겹치니 `queue/2026-11-15_1900_deals/` 처럼 뒤에 붙이세요 (예약 시간은 post.yml 의 `publish_at` 기준).

## 단일 혜택 캐러셀 (혜택알람)
혜택 하나를 3장 안팎으로: 표지(사진 + 두 줄) → 메모 카드 → (공식 이미지) → 팔로우 유도
- 표지: 게시물에 `cover_style: deal`, `title` 두 줄(마지막 줄 노란색), `label` = 왼쪽 위 칩, `subtitle` = 날짜 칩
- 메모 카드: `type: note` — `year` = 기간(시계 아이콘), `title` = 형광펜 핵심 혜택, `desc` 줄마다 앞글자로 아이콘
  `!` 주의(경고 삼각형) · `+` 추가 혜택 · `>` 받는 방법(빨간 글씨) · `-` 조건(체크) · 그 외는 일반 줄
- 공식 이벤트 이미지를 그대로 한 장 넣으려면 `type: photo` + `image:` (저작권 주의)
- 배경 사진: 메모 카드의 `wiki:` 또는 `image:` (표지·메모·마지막 장이 같은 사진을 씀)
- 마지막 장은 채널 설정 `outro.style: follow` 이면 프로필 알약 모양 팔로우 유도 장
- 예시: `drafts/deal_touslesjours_1118/`

## 3. 릴스(영상)
- `format: reel` 이면 같은 카드들을 **9:16 영상**으로 만듭니다: 흐린 배경 + 천천히 확대 + 장면 전환.
- 장당 시간·전환 속도는 `config.yml` 의 `reel:` 에서 조절.
- **배경음악**: API 로 올리는 영상에는 인스타 음악 라이브러리를 붙일 수 없습니다.
  저작권 없는 음원(예: YouTube 오디오 라이브러리)을 `assets/bgm/` 에 넣고 `bgm:` 에 경로를 적으세요.
  음악 없이 올린 뒤, 인기 음원을 쓰고 싶으면 앱에서 직접 올리는 게 낫습니다.
- **위쪽 검은 칸 릴스** (`layout: letterbox`): 위쪽 검은 칸에 후킹 문구를 영상 내내 고정하고, 가운데 장면, 장면 아래 자막, 작품 제목 순으로 보여 줍니다.
  - `title` = 후킹 문구 (2줄 이하), `items[].desc` = 장면 자막 (30자 이하), `items[].title` + `year` = 아래 작품 제목
  - 배우 게시물(`actor:`)은 다른 배우 얼굴 위에 자막이 얹히지 않도록 작품 포스터를 씁니다. 마지막 장은 `cover_image` (없으면 배우 사진) + `outro_question`
  - 예시: `drafts/letterbox_ohjungse/`

---

## 4. 업로드는 어떻게 되나요?
- **30분마다** Actions 가 `queue/` 를 확인해서 시간이 지난 게시물을 올립니다. (GitHub 사정으로 수십 분 늦을 수 있음)
- 성공하면 폴더가 `published/` 로 옮겨지고 `result.json` 에 게시물 링크가 남습니다.
- 실패하면 폴더에 `failures.json` 이 생기고 Actions 가 ❌ 로 표시됩니다(GitHub 이 메일로 알려줌).
  3번 실패하면 더 시도하지 않으니, 원인을 고친 뒤 `failures.json` 을 지우세요.
- 캐러셀 이미지는 공개 레포의 주소(raw.githubusercontent.com)로 인스타에 전달됩니다. **레포는 공개 상태여야 합니다.**

## 5. 토큰 만료 (60일)
- "인스타 토큰 연장" 워크플로가 한 달에 두 번 자동으로 연장합니다.
- 연장 시 토큰 문자열이 바뀌는 경우를 대비해 `SECRETS_PAT` 을 넣어 두면 새 토큰을 자동 저장합니다.
  (GitHub → Settings → Developer settings → Fine-grained token → 이 레포만, **Secrets: Read and write** 권한)
- 업로드가 `API 오류 190` 등으로 실패하면 토큰을 새로 발급해 `IG_ACCESS_TOKEN` 을 바꿔 주세요.

## 6. 주의
- 포스터·스틸컷은 저작권이 있습니다. 공식 보도자료 이미지를 쓰고 `credits:` 로 출처를 남기세요.
- 레포가 공개이므로 **예약 중인 게시물 내용도 공개**됩니다.
- 60일 동안 레포에 아무 활동이 없으면 GitHub 이 예약 실행을 멈춥니다. 꾸준히 올리면 문제없습니다.

## 폴더 구조
```
config.yml                 브랜드명, 인스타 아이디, 해시태그, 색상, 릴스 설정
queue/                     예약 대기 게시물 (폴더 1개 = 게시물 1개)
published/                 올라간 게시물 + result.json
examples/                  post.yml 예시
assets/fonts/              나눔스퀘어 (OFL 라이선스)
assets/bgm/                릴스 배경음악
screendaily/               코드 (cards.py 디자인 · reel.py 영상 · instagram.py 업로드)
.github/workflows/         자동 실행 (업로드 · 미리보기 · 토큰 연장 · 연결 테스트)
```
