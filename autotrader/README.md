# 한국투자증권 Open API 기반 자동매매 프로젝트 (학습/개발용)

## 1) 프로젝트 소개
이 프로젝트는 **학습 및 개발용 자동매매 시스템 골격**입니다.  
기본 브로커는 `MockBroker`이며, 실거래는 기본적으로 비활성화됩니다.

> ⚠️ 투자에는 원금 손실 가능성이 있으며, 본 프로젝트 코드는 운영 수익을 보장하지 않습니다.

## 2) 지원 기능
- 브로커 추상화(`Broker`) + Mock 브로커 완전 구현
- 한국투자증권 Open API 연동용 브로커 구조 제공
- 이동평균선 골든/데드크로스 전략
- 주문 전 리스크 규칙 검사
- Dry Run 모드 지원
- 주문/로그 SQLite 저장
- pytest 기반 테스트

## 3) 폴더 구조
```text
autotrader/
  app.py
  main.py
  config.py
  requirements.txt
  README.md
  .env.example
  broker/
    __init__.py
    base.py
    mock_broker.py
    koreainvestment.py
  strategy/
    __init__.py
    base.py
    moving_average_cross.py
  risk/
    __init__.py
    rules.py
  engine/
    __init__.py
    trader.py
  storage/
    __init__.py
    db.py
  utils/
    __init__.py
    logger.py
    time_utils.py
  tests/
    test_strategy.py
    test_risk.py
    test_mock_broker.py
```

## 4) 설치 방법
```bash
cd autotrader
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 5) 실행 방법
### 단발 실행
```bash
python main.py
```

### 반복 실행
```bash
python main.py --loop
```

## 6) MockBroker 테스트 방법
```bash
pytest -q
```

`BROKER_TYPE=mock` 상태에서 외부 API 호출 없이 전략/엔진 동작을 검증할 수 있습니다.

## 7) Dry Run 설명
- `DRY_RUN=true`이면 주문 시도는 로깅/DB 저장만 수행하고 실제 주문은 실행하지 않습니다.
- 실거래 연동 브로커를 사용해도 Dry Run이 우선 적용됩니다.

## 8) 실거래 보호장치 설명
- `ENABLE_LIVE_TRADING=false`가 기본값입니다.
- `KoreaInvestmentBroker.place_order()`에서 `ENABLE_LIVE_TRADING=true`가 아니면 예외를 발생시켜 실제 주문을 차단합니다.
- 따라서 환경변수 오설정 시 무의식적 실거래를 방지합니다.

## 9) 한국투자증권 연동 시 필요한 환경변수
- `KIS_APP_KEY`, `KIS_APP_SECRET`: API 인증 키
- `KIS_ACCOUNT_NO`, `KIS_PRODUCT_CODE`: 계좌 정보
- `KIS_BASE_URL`: 실전/모의투자 API 기본 URL
- `KIS_IS_PAPER_TRADING`: 모의투자 여부
- `ENABLE_LIVE_TRADING`: 실거래 보호 스위치(기본 false)

## 10) 공식 API 문서 확인이 필요한 항목
아래 항목은 반드시 한국투자증권 공식 문서 최신 버전으로 확인해야 합니다.
- OAuth 토큰 발급 엔드포인트/요청/응답 상세
- 시세/OHLCV/잔고/주문/주문조회/취소 API의 정확한 endpoint
- `tr_id` 값(매수/매도, 조회 종류별 상이)
- 계좌 체계(`CANO`, `ACNT_PRDT_CD`) 및 주문 파라미터 규칙
- 응답 성공/실패 코드(`rt_cd`, `msg_cd`, `msg1`) 해석 규칙

코드에는 해당 부분마다 `TODO: 한국투자증권 공식 API 문서 확인 필요` 주석이 포함되어 있습니다.

## 11) 주의사항
1. 본 프로젝트는 **학습/개발용**입니다.
2. 기본값은 실거래 비활성화이며, MockBroker/Dry Run 중심으로 검증하세요.
3. 자동매매 운영 전에는 전략 검증(백테스트/모의투자), 장애 대응, 모니터링 체계를 충분히 갖춰야 합니다.
