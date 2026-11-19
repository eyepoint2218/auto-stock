# LIFE POLICY 카드뉴스 템플릿

ISSUE 001 원본(reference/issue-001) 레이아웃을 좌표로 고정한 렌더러입니다.
새 호는 `issues/issue-00N.json`의 텍스트만 바꾸고 실행하면 1080×1350 PNG 4장이 나옵니다.

    node render.js issues/issue-002.json      # → out/issue-002/*.png

- `[대괄호]` 안 텍스트는 파란색 강조
- 글자가 폭을 넘으면 그 줄만 자동 축소(원본 크기가 최대)
- `check` 항목이 있으면 3장 계산(보험료·차액)을 검증하고, 틀리면 렌더링을 중단
- 폰트: Pretendard (SIL Open Font License 1.1)
