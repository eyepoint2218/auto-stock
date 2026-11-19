# LIFE POLICY 카드뉴스 템플릿 (고정)

ISSUE 001 원본(reference/issue-001) 레이아웃을 좌표로 고정한 렌더러입니다.
디자인·순서·푸터·팔로우 장은 고정되어 있고, 매 호는 내용만 바꿉니다.

## 새 호 만들기

    cp issues/_template.json issues/issue-004.json   # ○○ 부분만 채우기
    node render.js issues/issue-004.json             # → out/issue-004/*.png (5장)

## 고정 규칙 (렌더러가 자동으로 지킴)

| 장 | 형식 | 역할 |
|---|---|---|
| 01/05 | cover | 질문만. 결과 숫자 금지 (예: "인상? 동결?") |
| 02/05 | compare | 결과 공개: 2026 vs 2027 + 파란 배너 |
| 03/05 | calc | 월급 기준 계산 + 차액 배너 + 기준 문구 |
| 04/05 | when | 시행 기간 · 대상 · 근거 · 안내 박스 |
| 05/05 | follow | 팔로우 유도 (series.json, 모든 호 동일) |

- 장 순서가 다르면 렌더링 중단
- 표지 큰 글씨에 2장 결과 숫자가 들어가면 렌더링 중단 (후킹 보호)
- `check` 값으로 3장 계산(본인 부담액·차액)을 검증, 틀리면 중단
- 푸터 문구와 05장 팔로우 내용은 `series.json`에서만 수정
- `[대괄호]` = 파란 강조, 폭을 넘는 줄은 자동 축소(원본 크기가 최대)
- 색: 남색 #0A1230 · 파랑 #0A3EC2 · 연회색 #ECECEE · 연파랑 #DCE8FD
- 폰트: Pretendard Black/ExtraBold/Bold (SIL Open Font License 1.1)

`issues/issue-001.json`은 원본 대조용 재현본이라 현재 규칙(5장·후킹)과 맞지 않습니다.
ISSUE 002는 고정 이전에 게시된 4장 버전을 그대로 보관합니다.
