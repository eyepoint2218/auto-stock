# JARVIS (GitHub Web Edition)

요청하신 대로 **GitHub 웹에서 바로 실행 가능한 JARVIS**로 구성했습니다.

## 1) 웹 실행 (GitHub Pages)

1. GitHub 저장소 → **Settings → Pages** 이동
2. **Build and deployment / Source**를 `GitHub Actions`로 선택
3. Actions 탭에서 `Deploy static JARVIS web` 워크플로우 실행(또는 `work` 브랜치에 push)
4. 배포 완료 후 URL 접속

### 접속 URL 규칙

- 기본 URL: `https://eyepoint2218.github.io/javis/`
- 커스텀 도메인을 설정하지 않았다면 위 URL로 접속됩니다.
- **정확한 최종 URL**은 Actions 실행 결과의 `Deploy to GitHub Pages` 단계에서 표시됩니다.

## 2) 사용 방법

웹 페이지에서 입력창에 다음처럼 입력:

- `jarvis help`
- `jarvis time`
- `jarvis date`
- `jarvis calc 12 * (8 + 2)`
- `jarvis note 아크 리액터 점검`
- `jarvis notes`
- `jarvis search iron man suit ai`

## 3) 포함 기능

- Wake-word 스타일: `jarvis ...`
- 시간/날짜/계산
- 메모 저장/조회 (브라우저 `localStorage`)
- 검색 링크 열기
- 대화 로그 출력

## 4) 로컬 미리보기 (즉시 확인용)

```bash
python3 -m http.server 8000
```

브라우저에서 `http://localhost:8000` 접속.


## 5) URL 확인

웹 페이지 상단에 `현재 실행 URL`이 자동으로 표시됩니다.


## 6) GitHub 업로드 설정 (자동화 스크립트)

아래 스크립트로 origin 설정 + push를 한 번에 할 수 있습니다.

```bash
./setup_github_push.sh
# 기본값: javis/<현재 브랜치>
# 필요 시: ./setup_github_push.sh https://github.com/eyepoint2218/javis.git work
```

### 인증 필요 사항
- GitHub에서 HTTPS push 시 로그인/토큰(PAT) 인증이 필요합니다.
- 인증이 안 되면 push가 실패할 수 있습니다.


## 7) 레포지토리 설정

자세한 GitHub 저장소 설정 절차는 `REPO_SETUP.md`를 참고하세요.
