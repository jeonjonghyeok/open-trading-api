# 자율 AI 트레이딩 피드백 루프 시스템 — 작업 플랜

> 마지막 업데이트: 2026-04-15

---

## 🎯 목표

한국투자증권 KIS MCP 기반으로 AI가 주도적으로:
1. 종목 선별 → 기술 지표 분석 → 매수/매도 신호 생성 → 주문 실행
2. 주문 이력 분석 → 전략 파라미터 자동 개선 (피드백 루프)

**핵심 원칙: 토큰 사용량 최소화** — 비실시간 데이터는 모두 파일 캐시

---

## 📁 파일 구조

```
~/open-trading-api/trading-system/
├── PLAN.md                        ← 이 파일
├── pyproject.toml                 ← 의존성 (pandas, requests, pyyaml)
├── run_cycle.py                   ← 장중 매매 사이클 진입점 (15분마다)
├── run_review.py                  ← 일일 복기 진입점 (16:00 KST)
├── data/
│   ├── cache/                     ← API 응답 파일 캐시 (TTL 기반)
│   │   ├── YYYYMMDD_candidates.json        (당일 1회)
│   │   ├── YYYYMMDD_{code}_ohlcv.json      (당일 1회)
│   │   └── YYYYMMDD_{code}_indicators.json (30분 TTL)
│   └── orders/
│       └── orders.db              ← SQLite 주문 이력
├── strategy/
│   ├── config.json                ← 현재 전략 파라미터 (AI가 수정)
│   ├── performance.json           ← 누적 성과 메트릭
│   └── feedback_log.json          ← AI 피드백 히스토리
├── scripts/
│   ├── cache_manager.py           ← 파일 캐시 유틸리티
│   ├── kis_helper.py              ← KIS REST API 직접 호출
│   ├── indicators.py              ← RSI/MACD/EMA/BB 계산
│   ├── signals.py                 ← 매수/매도/홀드 신호 판단
│   ├── executor.py                ← 주문 실행 + orders.db 저장
│   └── analyzer.py                ← 성과 분석 + 전략 자동 수정
└── logs/
    └── YYYY-MM-DD_review.json     ← 일별 복기 리포트
```

---

## 🔄 시스템 흐름

### 장중 사이클 (15분마다, 09:00~15:30)

```
run_cycle.py
  │
  ├─ [캐시] 후보 종목 로드 (당일 1회 캐싱)
  │   └─ kis_helper.get_volume_rank() → data/cache/YYYYMMDD_candidates.json
  │
  ├─ 각 종목별:
  │   ├─ [캐시] 일봉 OHLCV 로드 (당일 1회 캐싱)
  │   │   └─ kis_helper.get_ohlcv() → data/cache/YYYYMMDD_{code}_ohlcv.json
  │   │
  │   ├─ [캐시] 지표 계산 (30분 TTL)
  │   │   └─ indicators.add_indicators() → data/cache/YYYYMMDD_{code}_indicators.json
  │   │
  │   ├─ [실시간] 현재가 조회 (캐시 갱신용, 사이클당 1회)
  │   │   └─ kis_helper.get_price()
  │   │
  │   └─ 신호 판단 → 주문 실행
  │       ├─ signals.evaluate()
  │       └─ executor.execute() → orders.db 저장
  │
  └─ 오래된 캐시 정리 (7일 이상)
```

### 일일 복기 (08:00 KST — 출근 후 확인)

```
run_review.py → analyzer.run_daily_review()
  │
  ├─ [로컬] 당일 주문 내역 (orders.db, API 불필요)
  ├─ [API 1회] 실제 체결 내역 (inquire_daily_ccld)
  ├─ 성과 통계 계산 → performance.json 누적
  ├─ AI 피드백 생성 (규칙 기반 → 추후 Claude API로 교체 가능)
  │   ├─ 승률 < 40% → RSI 임계값 강화
  │   ├─ 평균 손실 > -2% → 손절 강화
  │   └─ 승률 > 60% → 익절 목표 상향
  ├─ strategy/config.json 자동 수정
  ├─ feedback_log.json 기록
  └─ logs/YYYY-MM-DD_review.json 저장
```

---

## 📊 초기 전략 (strategy/config.json v1)

### 전략명: RSI 과매도 반등 + MACD 골든크로스 복합 진입

**배경:**
- RSI는 단기 과매도/과매수를 측정하는 모멘텀 지표
- MACD는 추세 전환 신호를 감지하는 지표
- 두 지표의 조건이 동시에 충족될 때만 진입 → 허위 신호 감소

**매수 조건 (AND):**
1. `RSI < 35` — 과매도 구간 (단기 낙폭 과대)
2. `MACD 히스토그램이 음→양 전환` — 추세 반전 시작

**매도 조건 (OR):**
1. `RSI > 70` — 과매수 구간 도달
2. `MACD 히스토그램이 양→음 전환` — 추세 꺾임
3. 손절: `-3%`
4. 익절: `+5%`

**종목 선별:**
- KOSPI 거래량 순위 상위 5종목 (실전 앱키 없으면 대형주 10종목 중 5개)
- 가격 범위: 5,000 ~ 300,000원

**포지션 관리:**
- 최대 3종목 동시 보유
- 종목당 1주 (모의투자 테스트 단계)
- 시장가 주문 (ord_dvsn='01')

---

## 🚀 실행 방법

```bash
cd ~/open-trading-api/trading-system

# 신호 테스트 (주문 없이)
uv run python run_cycle.py --dry-run

# 장 시간 외 강제 실행 (테스트용)
uv run python run_cycle.py --dry-run --force

# 모의투자 실제 주문
uv run python run_cycle.py

# 일일 복기
uv run python run_review.py
```

---

## ⏰ 스케줄 등록 (Claude Code /schedule)

```
장중 사이클: */15 9-15 * * 1-5 (평일 09:00~15:45, 15분마다)
일일 복기:   3 8 * * 1-5 (평일 08:03 — 출근 후 전날 복기 확인)
```

---

## 📈 구현 현황

| 단계 | 상태 | 내용 |
|------|------|------|
| Phase 1: 인프라 | ✅ 완료 | cache_manager, kis_helper, indicators, config.json |
| Phase 2: 매매 엔진 | ✅ 완료 | signals, executor, run_cycle.py |
| Phase 3: 피드백 루프 | ✅ 완료 | analyzer, run_review.py |
| Phase 4: 스케줄 등록 | ✅ 완료 | 장중 */15분 + 일일복기 08:03 등록 완료 |
| Phase 5: 실전 앱키 연동 | ⏳ 대기 | 실전 앱키 설정 시 거래량순위 API 활성화 |

---

## 🔧 향후 개선 계획

1. **Claude API 연동**: analyzer.py의 규칙 기반 피드백을 Claude API 호출로 교체
   - 더 복잡한 패턴 분석 가능
   - 자연어 설명 포함 피드백 생성

2. **실전 앱키 추가**: `kis_devlp.yaml`에 `my_app`, `my_sec` 설정 시
   - 실시간 거래량 순위 기반 종목 선별 가능
   - 더 다양한 시장 데이터 접근

3. **전략 다변화**: 피드백 누적 후 다음 전략 추가 가능
   - 볼린저밴드 돌파 전략
   - EMA 골든크로스 전략
   - 거래량 급증 모멘텀 전략

4. **웹소켓 실시간 체결**: `vops` URL로 실시간 체결 데이터 수신

5. **성과 시각화**: matplotlib 기반 손익 곡선, 지표 차트 생성

---

## ⚠️ 주의사항

- **모의투자 전용**: `strategy/config.json`의 `order.mode: "demo"` 설정 확인
- **KIS 모의투자 제한**: 초당 2건 API 호출 제한 (sleep 0.5s 내장)
- **장 시간**: 평일 09:00~15:30 KST만 유효 (토/일/공휴일 자동 스킵)
- **토큰 갱신**: 24시간 유효, 만료 30분 전 자동 갱신 (`~/KIS/config/paper_token.json`)
