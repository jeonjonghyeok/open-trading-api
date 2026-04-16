---
name: kis-strategy-example
description: KIS 전략 스킬 패키지 예시 (skill_kind strategy). 작성 규칙은 .cursor/skills/open-trading-kis-marketplace-authoring 참고.
---

# KIS 전략 스킬 (예시)

## 역할

- `strategy-implementer` 는 **이 패키지의 SKILL.md와 동봉 메타**만을 기준으로 동작한다.
- 원본 `.kis.yaml` 은 **참조·감사(audit)** 용이며, 런타임 로직의 단일 소스가 되지 않는다.

## 패키지에 포함할 것 (권장)

- `SKILL.md` — 진입 규칙, 파라미터 스키마, `trading-system` 반영 절차
- `strategy.meta.json` — `catalog.json` 항목과 동일 id/version, 태그, 백테스트 요약 URI
- `config.fragment.json` — `strategy/config.json` 에 merge 가능한 조각 (선택)
- `signals_spec.md` 또는 Python 모듈 경로 — 엔진 확장 시 `scripts/` 연동 명세 (수동 승인 후)

## 등록

`kis-strategy-skills/marketplace/catalog.json` 에 항목 추가 후 PR·수동 검증.
