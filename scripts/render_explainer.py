#!/usr/bin/env python3
"""Generate ai_trading_explainer.html from UTF-8 explainer_content.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "scripts" / "explainer_content.json"
OUT_PATH = ROOT / "ai_trading_explainer.html"


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


HTML_KEYS = frozenset(
    {
        "hero_deck",
        "sec_what_lead",
        "sec_what_p1",
        "sec_what_p2",
        "m1_body",
        "m2_body",
        "m3_body",
        "role_engine_p",
        "role_cards_p",
        "recipe_p",
        "sec_claude_p",
        "sec_mcp_p",
        "sec_goal_lead",
        "aside_dev_p",
    }
)


def main() -> int:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    t = {}
    for k, v in data.items():
        s = str(v)
        t[k] = s if k in HTML_KEYS else esc(s)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t["meta_title"]}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&family=Noto+Serif+KR:wght@500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --ink: #141820;
      --ink-soft: #4a5568;
      --paper: #faf8f5;
      --card: #ffffff;
      --line: #e6e1d9;
      --accent: #0f766e;
      --accent-soft: #e0f2f1;
      --sun: #c2410c;
      --sun-soft: #ffedd5;
      --sea: #1d4ed8;
      --sea-soft: #dbeafe;
      --eve: #6d28d9;
      --eve-soft: #ede9fe;
      --radius: 18px;
      --shadow: 0 4px 20px rgba(20, 24, 32, 0.06);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Noto Sans KR", system-ui, sans-serif;
      font-size: 17px;
      line-height: 1.75;
      color: var(--ink);
      background: var(--paper);
    }}
    .wrap {{ max-width: 680px; margin: 0 auto; padding: 44px 20px 72px; }}
    header {{
      margin-bottom: 40px;
      padding-bottom: 36px;
      border-bottom: 1px solid var(--line);
    }}
    .kicker {{
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
      margin: 0 0 14px;
    }}
    h1 {{
      font-family: "Noto Serif KR", "Noto Sans KR", serif;
      font-size: clamp(30px, 5.5vw, 40px);
      font-weight: 600;
      line-height: 1.25;
      letter-spacing: -0.02em;
      margin: 0 0 18px;
    }}
    .deck {{
      font-size: 18px;
      color: var(--ink-soft);
      line-height: 1.65;
      margin: 0;
      max-width: 36em;
    }}
    .deck strong {{ color: var(--ink); font-weight: 600; }}
    section {{ margin-bottom: 48px; }}
    h2 {{
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--ink-soft);
      margin: 0 0 16px;
    }}
    .lead {{
      font-size: 18px;
      font-weight: 600;
      line-height: 1.55;
      color: var(--ink);
      margin: 0 0 14px;
    }}
    p {{ margin: 0 0 14px; color: var(--ink-soft); }}
    p:last-child {{ margin-bottom: 0; }}
    .timeline {{ display: grid; gap: 14px; margin-top: 10px; }}
    .moment {{
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 14px 18px;
      align-items: start;
      padding: 20px;
      background: var(--card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--line);
    }}
    .moment .badge {{
      grid-row: 1 / span 2;
      width: 52px;
      height: 52px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
    }}
    .moment.morning .badge {{ background: var(--accent-soft); }}
    .moment.day .badge {{ background: var(--sea-soft); }}
    .moment.eve .badge {{ background: var(--eve-soft); }}
    .moment h3 {{ margin: 0; font-size: 17px; font-weight: 700; color: var(--ink); }}
    .moment .when {{ font-size: 13px; font-weight: 600; color: var(--ink-soft); margin-bottom: 6px; }}
    .moment .body {{ grid-column: 2; font-size: 15px; color: var(--ink-soft); line-height: 1.7; }}
    .pill {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--paper);
      color: var(--ink-soft);
      border: 1px solid var(--line);
      margin-top: 10px;
    }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    @media (max-width: 600px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
    .tile {{
      padding: 18px;
      border-radius: var(--radius);
      background: var(--card);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }}
    .tile h3 {{ margin: 0 0 8px; font-size: 15px; font-weight: 700; }}
    .tile p {{ font-size: 14px; margin: 0; }}
    .recipe {{
      background: linear-gradient(160deg, var(--sun-soft) 0%, var(--card) 50%);
      border: 1px solid rgba(194, 65, 12, 0.2);
      border-radius: var(--radius);
      padding: 24px 22px;
      box-shadow: var(--shadow);
    }}
    .recipe ol {{ margin: 14px 0 0; padding-left: 1.15em; color: var(--ink-soft); font-size: 15px; }}
    .recipe li + li {{ margin-top: 8px; }}
    .split {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }}
    @media (max-width: 600px) {{ .split {{ grid-template-columns: 1fr; }} }}
    .split .box {{
      padding: 18px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.65;
    }}
    .split .box.a {{ background: var(--accent-soft); border: 1px solid rgba(15, 118, 110, 0.25); }}
    .split .box.b {{ background: var(--sea-soft); border: 1px solid rgba(29, 78, 216, 0.2); }}
    .split .box strong {{ display: block; font-size: 12px; margin-bottom: 6px; color: var(--ink); }}
    aside.dev {{
      margin-top: 40px;
      padding: 18px 20px;
      background: #f0f2f5;
      border-radius: 14px;
      font-size: 13px;
      color: var(--ink-soft);
      border: 1px solid var(--line);
      line-height: 1.65;
    }}
    aside.dev strong {{ display: block; color: var(--ink); font-size: 12px; margin-bottom: 6px; }}
    footer {{
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--line);
      font-size: 12px;
      color: var(--ink-soft);
    }}
  </style>
</head>
<body>
  <div class="wrap">

    <header>
      <p class="kicker">{t["kicker"]}</p>
      <h1>{t["hero_title_line1"]}<br>{t["hero_title_line2"]}</h1>
      <p class="deck">{t["hero_deck"]}</p>
    </header>

    <section>
      <h2>{t["sec_what_h2"]}</h2>
      <p class="lead">{t["sec_what_lead"]}</p>
      <p>{t["sec_what_p1"]}</p>
      <p>{t["sec_what_p2"]}</p>
    </section>

    <section>
      <h2>{t["sec_day_h2"]}</h2>
      <p>{t["sec_day_intro"]}</p>

      <div class="timeline">
        <article class="moment morning">
          <div class="badge" aria-hidden="true">{t["badge_morning"]}</div>
          <div>
            <p class="when">{t["m1_when"]}</p>
            <h3>{t["m1_title"]}</h3>
          </div>
          <div class="body">
            {t["m1_body"]}
            <span class="pill">{t["m1_pill"]}</span>
          </div>
        </article>

        <article class="moment day">
          <div class="badge" aria-hidden="true">{t["badge_day"]}</div>
          <div>
            <p class="when">{t["m2_when"]}</p>
            <h3>{t["m2_title"]}</h3>
          </div>
          <div class="body">
            {t["m2_body"]}
            <span class="pill">{t["m2_pill"]}</span>
          </div>
        </article>

        <article class="moment eve">
          <div class="badge" aria-hidden="true">{t["badge_eve"]}</div>
          <div>
            <p class="when">{t["m3_when"]}</p>
            <h3>{t["m3_title"]}</h3>
          </div>
          <div class="body">
            {t["m3_body"]}
            <span class="pill">{t["m3_pill"]}</span>
          </div>
        </article>
      </div>
    </section>

    <section>
      <h2>{t["sec_roles_h2"]}</h2>
      <div class="grid-2">
        <div class="tile">
          <h3>{t["role_builder_h"]}</h3>
          <p>{t["role_builder_p"]}</p>
        </div>
        <div class="tile">
          <h3>{t["role_engine_h"]}</h3>
          <p>{t["role_engine_p"]}</p>
        </div>
        <div class="tile">
          <h3>{t["role_cards_h"]}</h3>
          <p>{t["role_cards_p"]}</p>
        </div>
        <div class="tile">
          <h3>{t["role_claude_h"]}</h3>
          <p>{t["role_claude_p"]}</p>
        </div>
      </div>
    </section>

    <section>
      <h2>{t["sec_recipe_h2"]}</h2>
      <div class="recipe">
        <p class="lead" style="margin-bottom:8px;">{t["recipe_lead"]}</p>
        <p style="margin:0; font-size:15px; color:var(--ink-soft);">{t["recipe_p"]}</p>
        <ol>
          <li>{t["recipe_li1"]}</li>
          <li>{t["recipe_li2"]}</li>
          <li>{t["recipe_li3"]}</li>
          <li>{t["recipe_li4"]}</li>
        </ol>
      </div>
    </section>

    <section>
      <h2>{t["sec_claude_h2"]}</h2>
      <p>{t["sec_claude_p"]}</p>
      <div class="split">
        <div class="box a">
          <strong>{t["split_auto_h"]}</strong>
          {t["split_auto_p"]}
        </div>
        <div class="box b">
          <strong>{t["split_helper_h"]}</strong>
          {t["split_helper_p"]}
        </div>
      </div>
      <p style="margin-top:16px;">{t["sec_mcp_p"]}</p>
    </section>

    <section>
      <h2>{t["sec_goal_h2"]}</h2>
      <p class="lead">{t["sec_goal_lead"]}</p>
      <p>{t["sec_goal_p"]}</p>
    </section>

    <aside class="dev">
      <strong>{t["aside_dev_h"]}</strong>
      {t["aside_dev_p"]}
    </aside>

    <footer>
      {t["footer"]}
    </footer>
  </div>
</body>
</html>
"""
    OUT_PATH.write_text(html.replace("\r\n", "\n"), encoding="utf-8")
    print(f"Wrote {OUT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
