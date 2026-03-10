# 미래에셋증권 연동 고려 주식 자동매매 (안전 개발용 스켈레톤)

## 프로젝트 개요
이 프로젝트는 **실거래 자동매매 시스템의 안전한 개발 골격**을 제공합니다.  
기본 브로커는 `MockBroker`이며, 미래에셋 연동은 **스켈레톤**만 제공합니다.

> 기본값은 실거래 비활성화입니다. (`ENABLE_LIVE_TRADING=false`)

## 주요 기능
- 브로커 추상화 (`Broker`)
- 완전한 개발용 `MockBroker` (가짜 잔고/포지션/주문)
- 이동평균 크로스 전략
- 리스크 규칙 기반 주문 차단
- SQLite 저장소
- 콘솔/파일 로깅
- 테스트 코드(pytest)

## 폴더 구조
```text
autotrader/
  app.py
  main.py
  config.py
  requirements.txt
  README.md
  .env.example
  broker/
  strategy/
  risk/
  engine/
  storage/
  utils/
  tests/
```

## 설치 방법
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r autotrader/requirements.txt
```

## 실행 방법
1) 환경변수 파일 준비
```bash
cp autotrader/.env.example .env
```

2) 1회 실행
```bash
python -m autotrader.main --once
```

3) 루프 실행
```bash
python -m autotrader.main
```

## MockBroker 테스트 방법
```bash
pytest autotrader/tests -q
```

## .env.example 설명
- `BROKER_TYPE=mock` : 기본 브로커
- `ENABLE_LIVE_TRADING=false` : 실거래 차단
- `DRY_RUN=true` : 주문 실행 대신 시뮬레이션
- `TRADE_SYMBOLS` : 감시 종목 코드(문자열)

## 미래에셋 연동 시 공식문서로 채워야 하는 부분
`autotrader/broker/mirae_asset.py`의 `TODO: 미래에셋 공식 API 문서 확인 필요` 항목을 반드시 채워야 합니다.
- 인증 endpoint 및 토큰 규칙
- 시세/잔고/포지션 조회 endpoint
- 주문/취소 endpoint 및 요청 스키마
- 헤더/해시/서명 규칙

## 실거래 주의사항
- 실거래는 큰 손실 위험이 있습니다.
- 운영 전 모의환경/백테스트/페이퍼트레이딩을 충분히 수행하세요.
- 본 프로젝트는 교육/개발용이며 투자 손익을 보장하지 않습니다.

## 안전 원칙
- 기본 실행은 MockBroker + DRY_RUN입니다.
- `ENABLE_LIVE_TRADING=true`가 아니면 실거래 주문은 차단됩니다.
- 미래에셋 API 세부사항은 절대 추측하지 않습니다.
