# Repository Setup Guide (javis)

이 문서는 `javis` 저장소를 push/배포 가능 상태로 설정하는 절차입니다.

## 1. GitHub 저장소 준비

- 저장소: `https://github.com/eyepoint2218/javis`
- Settings → General → Default branch를 `main` 권장

## 2. 로컬 저장소 연결

```bash
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/eyepoint2218/javis.git
git remote -v
```

## 3. 브랜치 push

```bash
git checkout -B main
git push -u origin main
```

## 4. GitHub Pages 설정

1. Settings → Pages
2. Source를 **GitHub Actions** 선택
3. Actions에서 `Deploy static JARVIS web` 워크플로우 실행
4. 배포 URL: `https://eyepoint2218.github.io/javis/`

## 5. 필수 권한/보안

- HTTPS push는 비밀번호 대신 PAT 사용
- PAT 최소 권한: repo (private 저장소면 필수)
- 노출된 토큰은 즉시 폐기하고 재발급

## 6. 문제 해결

- 403: 토큰 권한/만료/조직 정책 확인
- repository not found: URL 오타/권한 없음 확인
- protected branch: PR 방식으로 merge


## 7. 자동 push 스크립트

```bash
./setup_github_push.sh
```

- 인자 없이 실행하면 `origin=https://github.com/eyepoint2218/javis.git`, `branch=현재 체크아웃 브랜치`으로 push합니다.
- 브랜치를 바꾸려면 `./setup_github_push.sh https://github.com/eyepoint2218/javis.git work` 형태로 실행하세요.
