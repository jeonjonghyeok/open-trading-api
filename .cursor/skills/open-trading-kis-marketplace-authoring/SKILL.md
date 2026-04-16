---
name: open-trading-kis-marketplace-authoring
description: >-
  open-trading-api 전용 KIS 마켓플레이스에 매매 전략 스킬·시장/뉴스 맥락 스킬을 만들고 catalog.json에 등록하는 절차.
  strategy-implementer가 카탈로그를 읽고 종류별로 올바른 스킬을 고를 수 있게 패키지·메타를 맞출 때 사용한다.
---

# open-trading-api · KIS 마켓플레이스 스킬 작성 가이드

이 스킬은 **이 저장소만의 규칙**이다. 범용 OKX/다른 마켓 스킬 규칙과 섞지 않는다.

## 1. 스킬 종류 (`skill_kind`)

`kis-strategy-skills/marketplace/catalog.json`의 각 항목에 반드시 넣는다.

| `skill_kind` | 용도 | `strategy-implementer` |
|----------------|------|---------------------------|
| `strategy` | 매매 신호·진입/청산 규칙을 실행 엔진에 연결할 패키지 | 후보 전략 선택·엔진 반영의 **주 대상** |
| `market_context` | 지수·시장 국면·변동성 등 **맥락 정보** 수집·요약 | 전략 후보를 고를 때 **참고 입력** (단독으로 주문하지 않음) |
| `news_context` | 뉴스·공시·캘린더 등 **텍스트/이벤트** 수집·요약 | 동일, **참고 입력** |

**원칙:** `market_context` / `news_context`는 **주문 실행 스킬이 아니다.** 실행은 항상 `strategy` + `trading-system/strategy/config.json` + 기존 스크립트 흐름을 따른다.

## 2. 폴더 구조 (패키지)

저장소 루트 기준 `kis-strategy-skills/packages/<id>/` 아래에 둔다. `<id>`는 `catalog.json`의 `id`와 같게 한다.

권장 파일:

| 파일 | 필수 | 설명 |
|------|------|------|
| `SKILL.md` | 권장 | 사람·Claude가 읽는 운영 설명 (진입 철학, 금지 장면, 수익률 우선 근거) |
| `strategy.meta.json` | 예 | `id`, `version`, `skill_kind`, 소비자, 업스트림 소스 |
| `config.fragment.json` | 선택 | `trading-system/strategy/config.json`에 merge 가능한 JSON 조각 |
| `context_spec.md` | `market_context` / `news_context` 시 권장 | 어떤 API/피드·갱신 주기·출력 스키마(요약 필드) |

복사 시작: `packages/_template_strategy/`, `packages/_template_context/`.

## 3. `strategy.meta.json` 최소 스키마

```json
{
  "id": "my.team.strategy_name",
  "version": "1.0.0",
  "skill_kind": "strategy",
  "name": "표시 이름",
  "summary": "한 줄 요약",
  "profit_priority": "수익률·기대수익 근거 또는 백테스트 요약 한 줄",
  "downstream_consumers": ["strategy-implementer"],
  "upstream_sources": ["optional: builder export path or API name"],
  "catalog_sync": "kis-strategy-skills/marketplace/catalog.json"
}
```

`market_context` / `news_context`는 `upstream_sources`에 피드·API·파일 경로를 구체적으로 쓴다.

## 4. `catalog.json` 항목 작성

`kis-strategy-skills/marketplace/catalog.schema.json`을 따른다. 공통 필수:

- `id`, `version`, `name`, `package_path`, **`skill_kind`**
- `strategy`인 경우: `backtest` 블록 채우기(엔진·리포트 경로·검증일) 권장
- `tags`, `risk_tier`로 implementer·리뷰어가 후보를 거른다

등록 후 로컬에서 요약 확인:

```bash
python3 kis-strategy-skills/tools/list_marketplace.py
```

## 5. `strategy-implementer`가 카탈로그를 쓰는 방법

1. **항상** `catalog.json`을 읽고 `skill_kind`로 나눈다.
2. **구조 변경·신규 전략 활성화**는 `skill_kind === "strategy"`만 엔진에 직접 연결 후보로 삼는다.
3. `market_context` / `news_context`는 해당 패키지의 `context_spec.md`·`SKILL.md`를 읽어 **reviewer 제안·에디터 파라미터·사람 승인** 단계의 근거 자료로만 쓴다 (장중 자동 스위칭 금지는 `CLAUDE.md` 유지).
4. 수익률 최우선: 후보 `strategy` 스킬 간 비교 시 승률만이 아니라 **기대수익·손익비**를 `SKILL.md` / 백테스트 요약에 남긴다.

## 6. Cursor 스킬(이 파일) vs 마켓플레이스 패키지

| 구분 | 위치 | 역할 |
|------|------|------|
| **작성 가이드 스킬** | `.cursor/skills/open-trading-kis-marketplace-authoring/` | 지금 문서 — 스킬을 **어떻게 만들지** 교육 |
| **마켓플레이스 패키지** | `kis-strategy-skills/packages/<id>/` | **배포된** 전략·맥락 스킬 본체 |
| **목록** | `kis-strategy-skills/marketplace/catalog.json` | implementer가 **인지**하는 단일 인덱스 |

## 7. 체크리스트 (PR 전)

- [ ] `id`가 소문자·점·하이픈 규칙을 따름
- [ ] `package_path`가 실제 폴더와 일치
- [ ] `skill_kind`가 목적과 일치
- [ ] `strategy`면 백테스트·수익 우선 근거가 문서에 있음
- [ ] `context`면 출력 필드·갱신 주기·한계(지연·누락)가 명시됨
- [ ] `CLAUDE.md`의 자동 루틴 금지 범위를 위반하는 문구 없음

## 8. Claude가 못 하는 나머지 (수동/후속)

- Builder UI에서 “스킬 패키지로보내기” 버튼
- 원격 마켓플레이스 URL 동기화
- CI에서 `catalog.json` 스키마 검증

위 항목은 `CLAUDE.md`의 **Claude 후속 구현 백로그**를 따른다.
