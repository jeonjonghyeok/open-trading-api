# AI 자동 주식 거래 시스템 — 프로젝트 컨텍스트

> 이 파일은 Claude Code 세션이 시작될 때마다 **반드시 먼저 읽어야 할** 단일 진실의 소스입니다.
> **워크스페이스: `~/open-trading-api`**
> **최종 업데이트: 2026-04-16 (전략 스킬 마켓플레이스·implementer 선택 모델 반영)**

**Claude Code 토큰/세션 제약 시:** 스케줄 루틴·역할 분리·백로그는 **이 파일과 `kis-strategy-skills/marketplace/catalog.json` diff**만으로도 동기화할 수 있도록 유지한다. 세션 시작 시 `CLAUDE.md` → 카탈로그 → `trading-system/strategy/config.json` 순으로 읽는다.

---

## 프로젝트 한 줄 요약

한국투자증권(KIS) REST API + Claude Code Scheduled Tasks + Notion을 연결해,
AI가 전략을 스스로 선택·실행·분석·진화하는 자율 주식 거래 시스템. 현재 **모의투자 운용 중**.

---

## 핵심 설계 원칙

1. **수익률 최우선** — 전략 선택·파라미터 조정·복기 분석의 모든 판단 기준은 수익률 향상. 승률보다 기대수익(승률×평균수익)을 우선시한다.
2. **Claude는 판단이 필요할 때만 호출** — Rule-based Gate가 먼저 걸러서 의미 없는 AI 호출 차단
3. **전략은 config.json으로 관리** — AI가 파라미터를 파일 하나로 수정·진화
4. **토큰 사용량 최소화** — 비실시간 데이터는 파일 캐시 (당일 1회 또는 30분 TTL)
5. **전략 히스토리는 Notion에 자동 기록** — 매일 15:35 복기 결과 Notion DB push
6. **모든 거래에 전략 태그 부착** — orders.db strategy_id 필수
7. **전략 스킬은 마켓플레이스 카탈로그로 관리** — `strategy-implementer`는 워크스페이스 루트의 `.kis.yaml`을 **직접 해석하는 주 입력으로 쓰지 않는다.** 등록된 스킬 패키지(`kis-strategy-skills/packages/…`)와 `marketplace/catalog.json`을 기준으로 **후보를 고르고**, 승인된 패키지만 실행 엔진에 반영한다.

---

## 디렉토리 구조

```
~/open-trading-api/                     ← 워크스페이스 루트
├── CLAUDE.md                           ← 이 파일 (단일 진실의 소스)
├── ai_trading_explainer.html           ← 시스템 설명 페이지 (브라우저용)
├── kis-strategy-skills/                ← 전략 스킬 마켓플레이스 (메타 + 패키지)
│   ├── marketplace/
│   │   ├── catalog.json                ← 등록 스킬 목록 (implementer·운영자 참조)
│   │   └── catalog.schema.json         ← 카탈로그 항목 스키마 (`skill_kind` 포함)
│   ├── packages/                       ← 스킬별 폴더 (SKILL.md, strategy.meta.json 등)
│   ├── tools/
│   │   └── list_marketplace.py         ← 카탈로그를 skill_kind별 요약 출력
│   └── README.md                       ← 진입 안내
├── .cursor/skills/open-trading-kis-marketplace-authoring/  ← Cursor 스킬: 마켓 스킬 작성 가이드 (SKILL.md)
├── strategy_builder/                   ← KIS Strategy Builder (설계·export UI)
├── backtester/kis_backtest/            ← KIS Backtest (템플릿·검증)
├── .claude/
│   └── launch.json                     ← 프리뷰 서버 설정
├── MCP/
│   └── Kis Trading MCP/               ← KIS MCP 서버 (FastMCP)
│       └── .env.paper                  ← 모의투자 환경변수
└── trading-system/                     ← 실제 매매 엔진
    ├── run_cycle.py                    ✅ 장중 매매 사이클 (15분마다)
    ├── run_review.py                   ✅ 일일 성과 분석 + 전략 진화 (15:35)
    ├── pyproject.toml                  ✅ 의존성 (pandas, requests, pyyaml 등)
    ├── data/
    │   ├── cache/                      ✅ API 응답 파일 캐시 (TTL 기반)
    │   └── orders/orders.db            ✅ SQLite 주문 이력
    ├── strategy/
    │   ├── config.json                 ✅ 현재 전략 파라미터 (AI가 수정)
    │   ├── performance.json            ✅ 누적 성과 메트릭
    │   └── feedback_log.json           ✅ AI 피드백 이력
    ├── scripts/
    │   ├── cache_manager.py            ✅ 파일 캐시 유틸리티
    │   ├── kis_helper.py               ✅ KIS REST API 직접 호출
    │   ├── indicators.py               ✅ RSI/MACD/EMA/BB 계산
    │   ├── signals.py                  ✅ 매수/매도/홀드 신호 판단
    │   ├── executor.py                 ✅ 주문 실행 + orders.db 저장
    │   ├── analyzer.py                 ✅ 성과 분석 + 전략 자동 수정
    │   └── notion_reporter.py          ✅ Notion 전략 히스토리 기록
    └── logs/                           ✅ 일별 복기 JSON 리포트
```

---

## 스케줄 (Claude Code Scheduled Tasks)

| Task ID | 스케줄 (KST) | 실행 내용 |
|---------|-------------|-----------|
| `kis-data-collect` | 평일 **08:00** | `run_cycle.py --dry-run --force` — OHLCV·후보종목 캐시 워밍 |
| `kis-trading-cycle` | 평일 **09:00~15:00, 15분마다** | `run_cycle.py` — 신호 감지 + 주문 실행 |
| `kis-daily-recap` | 평일 **15:35** (장 마감 직후) | `run_review.py` — 성과 분석 + 전략 진화 + Notion 기록 |

> - 08:00 캐시 워밍 → 09:00 장 시작 시 즉시 캐시 히트
> - 전략 진화는 **매일** 실행 (테스트 기간 기준, 추후 주 1회로 전환 가능)
> - Notion 기록 → 출근 시 확인

---

## KIS Strategy Builder 활용 원칙

**역할 분리**

- `strategy_builder/` 는 **전략 설계 UI** 이다. 사람이나 AI가 전략 초안을 시각적으로 만들고 `.kis.yaml` 을 export/import 하는 용도다.
- `trading-system/` 은 **실제 실행 엔진** 이다. 실제 매매 루틴은 `strategy/config.json` 과 `run_cycle.py`, `run_review.py` 를 기준으로 동작한다.
- Claude는 Builder UI 자체를 매 루틴마다 조작하는 것이 아니라, **전략 파일과 실행 로직을 읽고 수정하는 역할** 을 맡는다.

**핵심 원칙**

1. 실시간 자동 루틴의 기준 전략은 항상 `trading-system/strategy/config.json` 이다.
2. `strategy_builder` 는 전략 아이디어를 빠르게 설계하고 `.kis.yaml` 로 보관·검증하는 용도로 사용한다.
3. Claude가 자동 루틴에서 직접 수정하는 기본 대상은 `config.json` 이며, 코드 구조 변경은 기본적으로 자동 수행하지 않는다.
4. Strategy Builder와 trading-system을 함께 쓸 때는 `.kis.yaml` ↔ `config.json` 변환 계층을 두는 것이 바람직하다.
5. 장중 자동 루틴에서는 **파라미터 수정만 허용** 하고, **코드 구조 변경은 금지** 한다.

**권장 사용 흐름 (스킬 마켓플레이스 연동)**

1. Strategy Builder에서 전략 설계 후 `.kis.yaml` export
2. **KIS Backtest**로 검증 → 리포트·지표 스냅샷 보관 (스킬 메타에 경로 기록)
3. **스킬 패키지 생성** — `kis-strategy-skills/packages/<skill_id>/`에 `SKILL.md`, `strategy.meta.json`, (선택) `config.fragment.json` 배치. 원본 `.kis.yaml`은 패키지 내 **참조용 복사 또는 경로**만 둔다.
4. **`marketplace/catalog.json` 등록** — id, version, `skill_kind`, package_path, backtest 요약, tags (`skill_kind`: `strategy` \| `market_context` \| `news_context`)
5. **파라미터만 조정 가능한 구간** — `strategy-editor`가 `trading-system/strategy/config.json`만 수정 (기존과 동일)
6. **구조 변경·신규 전략 활성화** — `strategy-implementer`가 카탈로그를 읽고 **적합한 스킬 패키지를 선택** → 수동 승인 후 코드·config 반영 (자동 루틴에서 임의 활성화 금지)
7. `run_cycle.py` / `run_review.py` 운영

**향후 (Builder 내 “스킬보내기” 버튼):** UI에서 3~4단계를 자동화하는 기능은 **별도 구현 백로그**에 둔다. 현재는 파일 기반으로 동일 절차를 수동 수행한다.

---

## 전략 스킬 마켓플레이스 (요약)

| 구분 | 위치 | 설명 |
|------|------|------|
| 카탈로그 | `kis-strategy-skills/marketplace/catalog.json` | 노출·버전·`skill_kind`·백테스트 메타. **운영 단일 목록** |
| 스키마 | `kis-strategy-skills/marketplace/catalog.schema.json` | 항목 필드 검증용 |
| 패키지 | `kis-strategy-skills/packages/<id>/` | **SKILL.md** + `strategy.meta.json` (템플릿: `_template_strategy/`, `_template_context/`) |
| 작성 가이드 (Cursor 스킬) | `.cursor/skills/open-trading-kis-marketplace-authoring/SKILL.md` | 스킬 생성·등록 절차 — **새 패키지 만들 때 에이전트가 따를 것** |
| 원본 DSL | `strategy_builder` export, `backtester/.../templates/*.kis.yaml` | **감사·재현**용. implementer의 “실행 단일 진입점”은 패키지 |

**`skill_kind`:** `strategy` = 매매 실행 후보(엔진 연결 대상). `market_context` / `news_context` = 시장·뉴스 **정보·맥락** 스킬 — 주문을 직접 내지 않으며, reviewer·승인 회의·implementer가 **후보 `strategy`를 고를 때의 근거**로만 쓴다.

**implementer 인지 절차:** 작업 시작 시 `python kis-strategy-skills/tools/list_marketplace.py` 로 카탈로그를 종류별로 훑는다. 엔진에 **직접** 붙이는 후보는 `skill_kind === "strategy"` 만이다.

**선택 규칙 (implementer):** reviewer의 “구조 변경 후보” + 시장 국면 태그(향후 `market_regime`) + 카탈로그 `tags`·`risk_tier` + (선택) 등록된 `market_context`/`news_context` 패키지의 요약을 조합해 **1개 이상 후보 `strategy` 스킬을 제안**하고, 사람이 고른 뒤에만 엔진에 합류한다. **자동 루틴에서 스킬 스위칭 금지** 원칙은 유지한다.

**수익률 원칙:** 스킬 **등록·후보 선정·승인·엔진 반영** 여부를 논할 때에도 **핵심 설계 원칙 1(수익률 최우선, 기대수익 중심)**을 따른다. 승률만 높고 기대수익이 낮은 전략을 “안전하다”는 이유만으로 우선하지 않는다.

---

## Claude 전략 스킬 운영 규칙

Claude는 아래 3개의 논리적 역할을 따른다. 실제 구현이 스킬 파일이든 내부 프롬프트 규칙이든 상관없이, 아래 책임 분리는 반드시 유지한다.

### 1) `strategy-editor`

**목적**
- 기존 전략의 파라미터를 현재 시장 상황과 복기 결과에 맞게 조정

**주요 입력**
- `strategy/config.json`
- 필요 시 `strategy_builder` 에서 export된 `.kis.yaml` (참고·diff용)
- (참고) `kis-strategy-skills/marketplace/catalog.json` — 어떤 스킬이 “승인·활성”인지 맥락 파악용. **에디터는 카탈로그를 직접 수정하지 않는다.**
- 최근 성과 요약, 시장 국면 정보, 캐시된 지표 데이터

**허용 작업**
- RSI/MACD/EMA/BB 임계값 수정
- 손절/익절, 최대 보유 종목 수, 종목 필터 수정
- 전략 설명문과 버전 갱신

**금지 작업**
- `signals.py`, `analyzer.py`, `executor.py` 등 실행 코드 구조 변경
- 장중 자동 루틴에서 신규 파일 추가

**위험도**
- 낮음

### 2) `strategy-reviewer`

**목적**
- 당일 또는 누적 성과를 분석해 무엇을 왜 바꿔야 하는지 판단

**주요 입력**
- `strategy/performance.json`
- `strategy/feedback_log.json`
- `data/orders/orders.db`
- `logs/` 일별 리포트
- (선택) `kis-strategy-skills/marketplace/catalog.json` 및 `skill_kind`가 `market_context` / `news_context` 인 패키지의 `SKILL.md` — 맥락 근거. **카탈로그를 직접 수정하지 않는다.**

**허용 작업**
- 성과 분석
- 손익비, 기대수익, 승률, MDD 기준 개선안 제안
- 시장 국면별 전략 적합성 평가

**금지 작업**
- 직접 코드 수정
- 장중 주문 로직 개입

**위험도**
- 매우 낮음

### 3) `strategy-implementer`

**목적**
- 파라미터 조정만으로 해결되지 않는 구조 변경을 **등록된 전략 스킬 패키지**를 통해 실행 엔진에 반영한다. **루트 `.kis.yaml` 파일을 직접 열어 로직을 추론하는 주 경로로 사용하지 않는다.**

**주요 입력 (우선순위)**
1. `kis-strategy-skills/marketplace/catalog.json` — 후보 스킬 목록 (`skill_kind`로 필터)
2. `python kis-strategy-skills/tools/list_marketplace.py` (또는 `--json`) — 종류별 요약
3. 선택된 `kis-strategy-skills/packages/<id>/` — 해당 `SKILL.md`, `strategy.meta.json`, 동봉 스펙
4. reviewer가 제안한 구조 변경안·시장 국면·리스크 허용 범위
5. `scripts/signals.py`, `scripts/indicators.py`, `scripts/analyzer.py` — 실제 패치 대상
6. `.kis.yaml` — **참조·감사·DSL 재현** 용 (카탈로그 `source_kis_yaml` 경로). 패키지에 없는 임의 yaml을 새 런타임 소스로 삼지 않는다.

**작성 가이드 (Cursor):** 새 패키지를 만들거나 카탈로그 항목을 쓸 때 **프로젝트 스킬** `.cursor/skills/open-trading-kis-marketplace-authoring/SKILL.md` 를 먼저 적용한다.

**허용 작업**
- 카탈로그를 읽고 **`strategy` 스킬만** 엔진 연결 후보로 선정하고, `market_context` / `news_context` 는 근거 자료로만 활용한다.
- 승인된 `strategy` 패키지의 스펙대로 새 전략 모듈·가드·변환기 구현
- 새 지표/필터/리스크 가드 구현
- 스킬에 동봉된 `config.fragment.json`과 `strategy/config.json`의 **명시적 merge** 문서화

**금지 작업**
- 장중 스케줄에서 자동 실행
- 검증 없이 실행 엔진 핵심 로직을 빈번하게 변경
- 카탈로그에 없는 전략을 임의로 “현재 활성”으로 올리기

**위험도**
- 높음

**원칙**
- `strategy-implementer` 는 기본적으로 **수동 승인형 작업** 으로 취급한다.
- 자동 Scheduled Task 안에서 상시 실행하지 않는다.
- **스킬 = 마켓플레이스에 등록된 패키지**이다. Builder/Backtest 산출물은 반드시 패키지화·카탈로그 등록을 거친다.

---

## 루틴별 스킬 매핑

현재 Claude 루틴 3개에서 각 역할은 아래와 같이 사용한다.

| 루틴 | 기본 목적 | 기본 사용 스킬 | 허용 범위 | 금지 범위 |
|------|-----------|----------------|-----------|-----------|
| `kis-data-collect` | OHLCV/후보종목 캐시 워밍 | 기본적으로 스킬 없음 | 데이터 수집, 캐시 준비 | 전략 파라미터 수정, 코드 수정 |
| `kis-trading-cycle` | 장중 신호 감지 + 주문 실행 | `strategy-editor` 제한적 사용 | `config.json` 파라미터 미세조정, 전략 버전 메모 | 코드 구조 변경, 새 전략 추가 |
| `kis-daily-recap` | 성과 분석 + 전략 진화 + 기록 | `strategy-reviewer` → `strategy-editor` | 성과 분석, 파라미터 조정, 변경 이력 기록 | 무승인 구조 변경 |

**중요**

- `kis-data-collect` 에는 기본적으로 전략 스킬을 붙이지 않는다.
- `kis-trading-cycle` 에서는 가능하면 기존 `config.json` 을 그대로 사용하고, 꼭 필요할 때만 `strategy-editor` 가 제한적으로 파라미터를 조정한다.
- `kis-daily-recap` 는 전략 진화의 중심 루틴이다. 여기서 `strategy-reviewer` 가 먼저 판단하고, 그 결과를 `strategy-editor` 가 `config.json` 에 반영한다.
- `strategy-implementer` 는 **카탈로그에 등록된 스킬**을 고르는 방식으로 새 전략을 엔진에 합류시키고, `market_regime.py`, `risk_guard.py`, 변환기 구현 같은 **개발 작업 전용** 이다. 스케줄 루틴의 기본 단계로 넣지 않는다.

---

## 자동화 안전 규칙

자동 루틴은 아래 순서를 따라야 한다.

1. `reviewer` 가 먼저 분석한다.
2. 분석 결과가 **파라미터 변경** 으로 해결 가능하면 `editor` 만 사용한다.
3. 분석 결과가 **코드 구조 변경** 을 요구하면 즉시 구현하지 말고 `implementer` 작업 후보로 기록한다.
4. `implementer` 성격의 변경은 수동 세션에서 테스트와 검토 후 반영한다.

**장중 안전 규칙**

- 장중(`kis-trading-cycle`)에는 `config.json` 의 수치형 파라미터만 조정 가능하다.
- 진입/청산 함수 구조, 주문 실행 방식, DB 스키마는 장중 자동 변경 금지.
- 신규 전략 활성화는 장 마감 후 또는 수동 세션에서만 허용.

**권장 기본값**

- `kis-data-collect`: 스킬 비활성
- `kis-trading-cycle`: `strategy-editor` 비활성 또는 매우 제한적
- `kis-daily-recap`: `strategy-reviewer` 활성 + `strategy-editor` 활성
- `strategy-implementer`: 자동 루틴 비활성

---

## Notion 기록 원칙

Notion에는 매일 단순 성과뿐 아니라 **전략 운영 의사결정** 이 남아야 한다.

- `kis-daily-recap` 실행 시 아래 내용을 함께 기록하는 것을 권장한다.
- 오늘 사용한 판단 주체: `reviewer`, `editor` 사용 여부
- 변경 종류: `파라미터 유지` / `파라미터 수정` / `구조 변경 후보`
- 구조 변경 후보가 있다면 실제 반영하지 말고 "후속 구현 필요" 로만 기록

**Notion 상태 해석 기준**

- `파라미터유지`: reviewer가 변경 불필요 판단
- `파라미터수정`: editor가 `config.json` 수치/조건을 조정
- `전략변경`: implementer 수준의 구조 변경이 수동 반영된 경우에만 사용

---

## 다음 Claude 세션을 위한 지시사항

다음 Claude는 이 파일만 읽고 아래 순서로 판단해야 한다.

1. 자동 루틴의 기준 전략 파일은 `trading-system/strategy/config.json` 임을 먼저 인식한다.
2. `strategy_builder/` 는 설계 보조 도구이지 자동 실행의 기준 엔진이 아님을 유지한다.
3. 구조 변경이 필요하면 **`kis-strategy-skills/marketplace/catalog.json`**에서 `skill_kind`별로 후보를 찾고, `list_marketplace.py`로 요약한다. 없으면 “신규 스킬 패키지 등록 필요”로 백로그에만 적는다 (임의 yaml 직접 연동 금지).
4. 루틴이 `kis-daily-recap` 이면 먼저 `strategy-reviewer` 관점으로 분석한다.
5. 분석 결과가 파라미터 조정 수준이면 `strategy-editor` 관점으로 `config.json` 만 수정한다.
6. 분석 결과가 코드 구조 변경이면 자동 반영하지 말고, `strategy-implementer` 후보 작업으로 남긴다 (선택 스킬 id·근거·리스크를 Notion에 적을 것).
7. 장중 루틴에서는 실행 코드 변경을 시도하지 않는다.
8. 모든 변경은 수익률 최우선 원칙과 Notion 기록 가능성을 기준으로 판단한다.

---

## 현재 전략 (strategy/config.json v1)

**RSI 과매도 반등 + MACD 골든크로스 복합 진입**

| 항목 | 값 |
|------|-----|
| 매수 조건 | RSI < 35 AND MACD 히스토그램 음→양 전환 |
| 매도 조건 | RSI > 70 OR MACD 양→음 OR 손절 -3% OR 익절 +5% |
| 종목 선별 | KOSPI 거래량 순위 상위 5종목 (실전 앱키 없으면 대형주 fallback) |
| 가격 범위 | 5,000 ~ 300,000원 |
| 포지션 | 최대 3종목 / 종목당 1주 / 시장가 |
| 모드 | demo (모의투자) |

**AI 피드백 원칙 — 수익률 최우선:**
- 모든 파라미터 조정의 목표는 **기대수익(승률 × 평균수익) 최대화**
- 승률이 높아도 평균수익이 낮으면 의미 없음 → 익절 목표 상향 우선
- 손실 제한보다 수익 기회 포착을 우선하되, MDD(최대낙폭) -10% 초과 시 손절 강화
- 복기 시 "왜 수익이 나지 않았는가"를 중심으로 분석, 단순 승률이 아닌 손익비(Profit Factor) 기준으로 판단

**AI 피드백 규칙 (analyzer.py):**
- 기대수익 < 0 → 진입 조건 강화 (RSI 임계값, MACD 필터 추가)
- 손익비(총수익/총손실) < 1.5 → 익절 목표 상향 or 손절 완화로 수익 극대화
- 평균 손실 > -2% → 손절 강화 (단, 수익 기회를 과도하게 차단하지 않는 선에서)
- 승률 > 60% + 평균수익 > 1.5% → 익절 목표 상향으로 수익 극대화

---

## 외부 연동

| 서비스 | 상태 | 설정 위치 |
|--------|------|-----------|
| KIS REST API (모의투자) | ✅ 연결됨 | `~/KIS/config/kis_devlp.yaml` |
| KIS 토큰 캐시 | ✅ 자동갱신 | `~/KIS/config/paper_token.json` |
| Notion | ✅ 연결됨 | `~/KIS/config/notion.json` |
| KIS REST API (실전) | ⏳ 미설정 | `my_app`, `my_sec` 추가 시 거래량순위 활성화 |

---

## Notion 연동

| 항목 | 값 |
|------|-----|
| 상위 페이지 | https://www.notion.so/344275c10f8e8044891cd8242c78e3ed |
| 전략 히스토리 DB | https://www.notion.so/cc3163894f234ca7873ef0f5e42925fe |
| 데이터소스 ID | `fe32674e-0d66-42fd-9037-087e6e7677d1` |
| 뷰 | 📅 날짜별 (Table) / 🔄 상태별 (Board) |
| 기록 시점 | 매일 15:35 `run_review.py` 실행 후 자동 push |

**각 행 상세 페이지 포함 내용:**
- 당일 매매 현황 (주문수·체결수·거래종목)
- 체결내역 (KIS 일일 체결 기준)
- 보유포지션 스냅샷 (잔고 조회 기준)
- 전략성과 요약 (누적/최근 성과)
- 일일리포트 경로 및 구성 요소
- 전략 파라미터 전체 (변경 전→후 비교)
- AI 피드백 내용
- 변경 내역 테이블

**운영 문서 동기화 원칙**
- `CLAUDE.md` 가 최상위 단일 진실 소스다.
- `ai_trading_explainer.html` 은 사람에게 설명하기 위한 시각화 문서이며, 항상 `CLAUDE.md` 기준으로 현행화한다.
- Notion 메인 페이지는 운영 개요와 데이터 구조를 설명하는 문서 역할을 한다.
- Notion DB 상세 페이지는 일일 복기 실행 결과를 기록하는 운영 로그 역할을 한다.

---

## 설정 파일

### ~/KIS/config/kis_devlp.yaml 구조
```yaml
vps: https://openapivts.koreainvestment.com:29443   # 모의투자
prod: https://openapi.koreainvestment.com:9443       # 실전
paper_app: <모의투자 앱키>
paper_sec: <모의투자 시크릿>
my_paper_stock: <모의투자 계좌번호>
my_prod: "01"
# my_app: <실전 앱키>   ← 추가 시 거래량순위 API 활성화
# my_sec: <실전 시크릿>
```

### ~/KIS/config/notion.json 구조
```json
{
  "token": "<Notion Integration Token>",
  "db_id": "cc3163894f234ca7873ef0f5e42925fe"
}
```

---

## 실행 방법

```bash
cd ~/open-trading-api/trading-system

# 신호 테스트 (주문 없이)
uv run python run_cycle.py --dry-run

# 장 시간 외 강제 실행 (캐시 워밍 테스트)
uv run python run_cycle.py --dry-run --force

# 모의투자 실제 주문
uv run python run_cycle.py

# 일일 성과 분석 + Notion 기록
uv run python run_review.py

# Notion 연동 초기 설정 (최초 1회)
uv run python scripts/notion_reporter.py --setup

# HTML 설명 페이지 프리뷰
# launch.json의 ai-trading-explainer → http://localhost:3002/ai_trading_explainer.html
```

```bash
cd ~/open-trading-api

# 마켓플레이스 카탈로그 요약 (strategy-implementer 인지용)
python3 kis-strategy-skills/tools/list_marketplace.py
python3 kis-strategy-skills/tools/list_marketplace.py --json
```

---

## 2026-04-16 세션 작업 내역

### 완료된 작업
- [x] `trading-system/` 전체 구현 (Phase 1~3)
- [x] Claude Code Scheduled Tasks 등록 (3개)
- [x] Notion "📊 전략 히스토리" DB 생성 + 뷰 2개
- [x] `notion_reporter.py` 작성 + `analyzer.py` 연동
- [x] Notion API 토큰 설정 완료 (`~/KIS/config/notion.json`)
- [x] 상세 페이지 본문 블록 (파라미터 비교 테이블, AI 피드백)
- [x] 변경 전/후 파라미터 `old_cfg` 전달 구조 수정
- [x] `ai_trading_explainer.html` 현행화 (3루틴·Notion·실구현 반영)
- [x] Notion 메인 페이지 현행화
- [x] CLAUDE.md 머지 + 현행화
- [x] 워크스페이스 `~/open-trading-api` 로 변경
- [x] `.claude/launch.json` OKX 관련 내용 제거
- [x] `kis-strategy-skills/` 마켓플레이스 스캐폴딩 (`catalog.json`, `catalog.schema.json`, `packages/_example/`)
- [x] CLAUDE.md: 전략 스킬 마켓플레이스·`strategy-implementer` 스킬 선택 모델·토큰 부족 시 동기화 규칙·Claude 후속 백로그
- [x] Cursor 스킬 `open-trading-kis-marketplace-authoring` · `skill_kind` · `list_marketplace.py` · 패키지 템플릿 (`_template_strategy` / `_template_context`)

### 다음 세션 시작점

1. **실전 앱키 연동** — `kis_devlp.yaml`에 `my_app`, `my_sec` 추가 → 거래량순위 API 활성화
2. **market_regime.py** — KOSPI 장 국면 분류 (추세/횡보/급등락)로 스킬 `tags`와 매칭
3. **risk_guard.py** — 주문 전 한도 검증 (종목당 최대 비중, 당일 최대 손실 한도)
4. **전략 다변화** — 우선 **카탈로그에 스킬 등록** 후 `strategy_vol_surge` 등 패키지화
5. **실 성과 확인** — `run_cycle.py` 실행 후 Notion에서 히스토리 누적 확인
6. **Google Sheets 연동** — 체결내역 실시간 기록 (Google Drive MCP)

---

## Claude 후속 구현 백로그 (스킬 마켓플레이스)

> 아래는 **코드/제품 작업**으로, 사람 또는 수동 Claude 세션에서 처리. **3개 Scheduled Task에는 넣지 않는다.**

| 우선순위 | 작업 | 설명 |
|----------|------|------|
| P0 | Builder **“스킬 패키지보내기”** | export 시 `packages/<id>/` 골격 + `strategy.meta.json` 초안 + `catalog.json` 항목 JSON 조각 생성 |
| P0 | Backtest **리포트 경로 자동 기록** | 검증 완료 시 스킬 메타에 `backtest.report_path`, `verified_at` 채우기 |
| P1 | **카탈로그 검증 CI** | PR 시 `catalog.json` ↔ `catalog.schema.json` 검증, `skill_kind` 필수·enum 준수 |
| P1 | **원격 마켓플레이스** (선택) | 별도 Git repo 또는 정적 JSON URL — 로컬 `catalog.json`은 미러 또는 서브셋 |
| P1 | Cursor **개별 전략 패키지 노출** (선택) | 승인된 `packages/<id>` 를 개발자 `.cursor/skills/`에 symlink 등으로 노출하는 팀 정책 (작성 가이드 스킬은 이미 `.cursor/skills/open-trading-kis-marketplace-authoring/`에 있음) |
| P2 | `strategy-implementer` **선택 헬퍼** | reviewer 출력 + `tags` + `risk_tier` + context 스킬 요약으로 후보 `strategy` 랭킹 (읽기 전용) |
| P2 | `ai_trading_explainer.html` | 마켓플레이스·스킬 등록 흐름 시각 반영 |

**플레이스홀더 제거:** `catalog.json`의 `example.placeholder`는 첫 실제 스킬 등록 시 삭제한다.

---

## 주의사항

- **모의투자 전용**: `strategy/config.json`의 `order.mode: "demo"` 확인 필수
- **KIS 모의투자 제한**: 초당 2건 API 호출 제한 (sleep 0.5s 내장)
- **장 시간**: 평일 09:00~15:30 KST (토/일/공휴일 자동 스킵)
- **토큰 갱신**: 24시간 유효, 만료 30분 전 자동갱신
- **Notion 기록**: `~/KIS/config/notion.json` 토큰 만료 시 재설정 필요
- **캐시 정리**: 7일 이상 된 캐시는 `run_cycle.py` 실행 시 자동 삭제
