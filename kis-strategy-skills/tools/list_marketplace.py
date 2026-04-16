#!/usr/bin/env python3
"""마켓플레이스 catalog.json을 skill_kind별로 요약 출력 (strategy-implementer 인지용)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = REPO_ROOT / "kis-strategy-skills" / "marketplace" / "catalog.json"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="catalog.json 경로",
    )
    p.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = p.parse_args()

    if not args.catalog.is_file():
        print(f"catalog not found: {args.catalog}", file=sys.stderr)
        return 1

    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    skills = data.get("skills") or []

    by_kind: dict[str, list[dict]] = defaultdict(list)
    missing_kind: list[dict] = []
    for s in skills:
        kind = s.get("skill_kind")
        if not kind:
            missing_kind.append(s)
            continue
        by_kind[str(kind)].append(s)

    if args.json:
        out = {
            "catalog_version": data.get("version"),
            "path": str(args.catalog),
            "by_skill_kind": {k: v for k, v in sorted(by_kind.items())},
            "missing_skill_kind": missing_kind,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"# Marketplace summary\n# file: {args.catalog}\n# catalog version: {data.get('version')!r}\n")
    order = ("strategy", "market_context", "news_context")
    for kind in order:
        if kind not in by_kind:
            continue
        print(f"## skill_kind = {kind}\n")
        for s in by_kind[kind]:
            line = f"- **{s.get('id')}** v{s.get('version')} — {s.get('name', '')}"
            if s.get("summary"):
                line += f"\n  - {s['summary']}"
            print(line)
        print()
    other = [k for k in by_kind if k not in order]
    for kind in sorted(other):
        print(f"## skill_kind = {kind}\n")
        for s in by_kind[kind]:
            print(f"- **{s.get('id')}** v{s.get('version')} — {s.get('name', '')}")
        print()

    if missing_kind:
        print("## WARNING: missing skill_kind\n")
        for s in missing_kind:
            print(f"- {s.get('id', '?')} (add skill_kind to catalog entry)\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
