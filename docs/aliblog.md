# 알리익스프레스 인기상품 → 네이버 블로그 (반자동)

매일 아침 07:47(한국시간)에 인기상품 10개로 블로그 초안을 자동으로 만들고, **올리는 건 직접** 합니다.
네이버 블로그는 자동 글쓰기 API가 없어서 복사·붙여넣기로 올립니다.

## 1. 처음 한 번: 알리 어필리에이트 키 받기
1. [portals.aliexpress.com](https://portals.aliexpress.com) 가입 → 블로그 주소를 홍보 채널로 등록
2. 메뉴 **Tools → Tracking ID** 에서 Tracking ID 만들기
3. [openservice.aliexpress.com](https://openservice.aliexpress.com) 에서 앱 등록 (Affiliate API) → 승인 후 **App Key, App Secret** 확인 (승인에 며칠 걸릴 수 있음)
4. 레포 **Settings → Secrets and variables → Actions** 에 저장 (채팅·코드에 붙여넣지 마세요)

| 이름 | 값 |
|---|---|
| `ALI_APP_KEY` | App Key |
| `ALI_APP_SECRET` | App Secret |
| `ALI_TRACKING_ID` | Tracking ID (없으면 수수료가 안 붙음) |

키가 없으면 예시 초안만 만들어집니다. 매일 자동 실행은 main 브랜치에 합쳐야 동작합니다.

## 2. 매일 할 일 (5분)
1. **Actions → 알리 블로그 초안** → 오늘 실행 → 아래 **Artifacts** 의 zip 받기 → 압축 풀고 `post.html` 열기 (PC)
2. **제목 복사** → 네이버 블로그 글쓰기 제목에 붙여넣기
3. **본문 전체 복사** → 본문에 붙여넣기. 사진이 안 붙으면 `images/` 의 사진을 번호대로 끌어다 넣기
4. 상품마다 한두 줄 직접 느낀 점 추가 (같은 형식 글만 반복하면 검색 노출이 떨어질 수 있음)
5. **태그 복사** → 태그 칸에 넣고, 링크 몇 개 눌러 확인 후 발행

zip 없이 레포의 `blog/날짜/post.txt` 만 봐도 됩니다 (휴대폰용, 링크 포함 글자만).

## 3. 고르는 기준 (`aliblog/collect.py`)
- 최근 판매량 많은 순, 긍정 평가 90% 이상, 최근 판매 100개 이상
- 최근 14일 안에 소개한 상품은 빼기 (`blog/history.json`)
- 한 카테고리 최대 2개 (같은 종류만 몰리지 않게)
- 특정 카테고리만: `python -m aliblog daily --category 카테고리ID`

## 4. 지켜야 할 것
- **맨 위 수수료 안내 문구는 지우지 않는다.** (공정위 추천·보증 심사지침, 본문 첫머리에 표시)
- 가격·판매량은 만든 시각 기준이라고 적혀 있다. "최저가", "역대급" 같은 확인 안 된 표현은 쓰지 않는다.
- 상품 사진은 알리 API 가 주는 상품 대표 이미지만 쓴다.

## 컴퓨터에서 직접 만들기
```bash
python -m aliblog daily --sample   # 키 없이 모양 확인 (blog/날짜_sample/post.html)
ALI_APP_KEY=... ALI_APP_SECRET=... ALI_TRACKING_ID=... python -m aliblog daily
```
