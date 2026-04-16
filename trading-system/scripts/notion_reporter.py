"""
Notion 전략 히스토리 리포터
매일 복기 후 전략 파라미터·성과를 Notion DB에 자동 기록
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, date
from typing import Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRATEGY_DIR = os.path.join(BASE_DIR, "strategy")
CONFIG_PATH = os.path.join(STRATEGY_DIR, "config.json")

# Notion API 설정 — 환경변수 또는 ~/KIS/config/notion.json 에서 읽음
NOTION_CONFIG_PATH = os.path.expanduser("~/KIS/config/notion.json")
NOTION_API_VERSION = "2022-06-28"


def load_notion_config() -> Optional[dict]:
    """Notion API 토큰 + DB ID 로드"""
    # 1) 환경변수 우선
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_STRATEGY_DB_ID")
    if token and db_id:
        return {"token": token, "db_id": db_id}

    # 2) 파일에서 읽기
    if os.path.exists(NOTION_CONFIG_PATH):
        try:
            with open(NOTION_CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass

    return None


def save_notion_config(token: str, db_id: str):
    """Notion 설정 저장"""
    os.makedirs(os.path.dirname(NOTION_CONFIG_PATH), exist_ok=True)
    with open(NOTION_CONFIG_PATH, "w") as f:
        json.dump({"token": token, "db_id": db_id}, f, indent=2)
    print(f"[NOTION] 설정 저장: {NOTION_CONFIG_PATH}")


def notion_request(method: str, path: str, token: str, body: Optional[dict] = None) -> Optional[dict]:
    """Notion API 호출"""
    url = f"https://api.notion.com/v1{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"[NOTION ERROR] {e.code}: {err_body}")
        return None
    except Exception as e:
        print(f"[NOTION ERROR] {e}")
        return None


def _get_nested(d: dict, key: str):
    """'indicators.rsi_oversold' 형태 키로 중첩 dict 값 조회"""
    parts = key.split(".")
    for p in parts:
        if not isinstance(d, dict):
            return None
        d = d.get(p)
    return d


def report_to_notion(
    stats: dict,
    feedback: dict,
    cfg: dict,
    filled_count: int = 0,
    old_cfg: Optional[dict] = None,
    filled_orders: Optional[list] = None,
    holdings: Optional[list] = None,
    balance_summary: Optional[dict] = None,
    perf: Optional[dict] = None,
    report_path: str = "",
) -> bool:
    """
    일일 복기 결과를 Notion DB에 기록
    stats: calc_daily_stats() 결과
    feedback: ai_feedback() 결과
    cfg: 변경 후 strategy/config.json
    old_cfg: 변경 전 config (없으면 cfg와 동일하게 처리)
    """
    ncfg = load_notion_config()
    if not ncfg:
        print("[NOTION] 설정 없음 — 스킵 (~/KIS/config/notion.json 또는 환경변수 NOTION_TOKEN, NOTION_STRATEGY_DB_ID 설정 필요)")
        return False

    token = ncfg["token"]
    db_id = ncfg["db_id"]

    if old_cfg is None:
        old_cfg = cfg
    if filled_orders is None:
        filled_orders = []
    if holdings is None:
        holdings = []
    if balance_summary is None:
        balance_summary = {}
    if perf is None:
        perf = {}

    today_str = stats.get("date", date.today().isoformat())
    ind = cfg.get("indicators", {})
    order = cfg.get("order", {})
    version = cfg.get("version", 1)
    description = cfg.get("description", "RSI 과매도 반등 + MACD 골든크로스")

    # 상태 판단
    changes = feedback.get("changes", {})
    if not changes:
        status = "파라미터유지"
    elif any("rsi" in k or "macd" in k for k in changes):
        status = "파라미터수정"
    else:
        status = "전략변경"

    # AI 피드백 텍스트
    notes_text = "\n".join(f"• {n}" for n in feedback.get("notes", ["변경 없음"]))

    # 변경내역 텍스트 — "변경전값 → 변경후값" 형식
    if changes:
        lines = []
        for k, new_val in changes.items():
            old_val = _get_nested(old_cfg, k)
            lines.append(f"{k}: {old_val} → {new_val}")
        changes_text = "\n".join(lines)
    else:
        changes_text = "없음"

    # 종목 캐시 정보
    cached_codes = ", ".join(stats.get("order_codes", [])) or "없음"

    page_title = f"{today_str} | v{version} | {description[:20]}"

    # ── 상세 페이지 본문 블록 ───────────────────────────────────
    old_ind = old_cfg.get("indicators", {})
    old_order = old_cfg.get("order", {})

    def changed(key_new, key_old=None):
        """변경된 파라미터면 '← 구값' 접미사 반환"""
        if key_old is None:
            key_old = key_new
        old_v = old_ind.get(key_old) if key_old in old_ind else old_order.get(key_old)
        new_v = ind.get(key_new) if key_new in ind else order.get(key_new)
        if old_v is not None and old_v != new_v:
            return f"  ← 기존: {old_v}"
        return ""

    status_emoji = {"파라미터유지": "🟢", "파라미터수정": "🟡", "전략변경": "🔴", "오류": "❌"}.get(status, "⚪")

    page_content = _build_page_blocks(
        today_str=today_str,
        version=version,
        status=status,
        status_emoji=status_emoji,
        description=description,
        stats=stats,
        filled_count=filled_count,
        ind=ind,
        old_ind=old_ind,
        order=order,
        old_order=old_order,
        changes=changes,
        changes_text=changes_text,
        notes_text=notes_text,
        cached_codes=cached_codes,
        filled_orders=filled_orders,
        holdings=holdings,
        balance_summary=balance_summary,
        perf=perf,
        report_path=report_path,
    )

    body = {
        "parent": {"database_id": db_id},
        "properties": {
            "전략명": {
                "title": [{"text": {"content": page_title}}]
            },
            "날짜": {
                "date": {"start": today_str}
            },
            "버전": {
                "number": version
            },
            "상태": {
                "select": {"name": status}
            },
            "총주문수": {
                "number": stats.get("total_orders", 0)
            },
            "체결수": {
                "number": filled_count
            },
            "RSI과매도기준": {
                "number": ind.get("rsi_oversold", 35)
            },
            "RSI과매수기준": {
                "number": ind.get("rsi_overbought", 70)
            },
            "손절%": {
                "number": order.get("stop_loss_pct", -3.0)
            },
            "익절%": {
                "number": order.get("take_profit_pct", 5.0)
            },
            "AI피드백": {
                "rich_text": [{"text": {"content": notes_text[:2000]}}]
            },
            "변경내역": {
                "rich_text": [{"text": {"content": changes_text[:2000]}}]
            },
            "일봉캐시종목": {
                "rich_text": [{"text": {"content": cached_codes[:500]}}]
            },
        },
        "children": page_content,
    }

    result = notion_request("POST", "/pages", token, body)
    if result and result.get("id"):
        print(f"[NOTION] ✅ 전략 히스토리 기록 완료: {page_title}")
        print(f"         https://notion.so/{result['id'].replace('-', '')}")
        return True
    else:
        print("[NOTION] ❌ 기록 실패")
        return False


def _txt(content: str, bold: bool = False, color: str = "default") -> dict:
    ann = {"bold": bold, "color": color}
    return {"type": "text", "text": {"content": content}, "annotations": ann}


def _heading(text: str, level: int = 2) -> dict:
    kind = f"heading_{level}"
    return {
        "object": "block",
        "type": kind,
        kind: {"rich_text": [_txt(text, bold=True)]},
    }


def _para(text: str, bold: bool = False, color: str = "default") -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [_txt(text, bold=bold, color=color)]},
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _callout(text: str, emoji: str = "💡", color: str = "yellow_background") -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [_txt(text)],
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
        },
    }


def _bullet(text: str, color: str = "default") -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [_txt(text, color=color)]},
    }


def _table_row(cells: list) -> dict:
    return {
        "type": "table_row",
        "table_row": {"cells": [[_txt(c)] for c in cells]},
    }


def _table(header: list, rows: list) -> dict:
    children = [_table_row(header)] + [_table_row(r) for r in rows]
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(header),
            "has_column_header": True,
            "has_row_header": False,
            "children": children,
        },
    }


def _build_page_blocks(
    today_str, version, status, status_emoji, description,
    stats, filled_count, ind, old_ind, order, old_order,
    changes, changes_text, notes_text, cached_codes,
    filled_orders, holdings, balance_summary, perf, report_path,
) -> list:
    """상세 페이지 Notion 블록 목록 생성"""

    def diff(new_val, old_val):
        """변경된 값이면 '변경 전 → 변경 후' 형태, 아니면 그냥 값"""
        if old_val is not None and old_val != new_val:
            return f"{old_val}  →  {new_val}  ✏️"
        return str(new_val)

    blocks = []

    # ── 상단 요약 callout ──
    change_summary = f"파라미터 {len(changes)}개 수정됨" if changes else "전략 변경 없음"
    callout_color = "yellow_background" if changes else "green_background"
    callout_emoji = "🟡" if changes else "🟢"
    blocks.append(_callout(
        f"{status_emoji} {status}  |  {change_summary}  |  전략 v{version}",
        emoji=callout_emoji,
        color=callout_color,
    ))
    blocks.append(_para(""))

    # ── 오늘의 매매 현황 ──
    blocks.append(_heading("📊 오늘의 매매 현황", level=2))
    blocks.append(_table(
        ["항목", "값"],
        [
            ["날짜", today_str],
            ["총 주문수", str(stats.get("total_orders", 0))],
            ["실제 체결수", str(filled_count)],
            ["매수", str(stats.get("buys", 0))],
            ["매도", str(stats.get("sells", 0))],
            ["거래 종목", cached_codes],
        ],
    ))
    blocks.append(_para(""))
    blocks.append(_divider())

    # ── 현재 전략 파라미터 ──
    blocks.append(_heading("⚙️ 전략 파라미터 (적용 후)", level=2))
    blocks.append(_para(description))
    blocks.append(_para(""))

    blocks.append(_heading("진입 지표", level=3))
    blocks.append(_table(
        ["지표", "파라미터", "값"],
        [
            ["RSI", "기간", str(ind.get("rsi_period", 14))],
            ["RSI", "과매도 기준 (매수)", diff(ind.get("rsi_oversold", 35), old_ind.get("rsi_oversold"))],
            ["RSI", "과매수 기준 (매도)", diff(ind.get("rsi_overbought", 70), old_ind.get("rsi_overbought"))],
            ["MACD", "Fast / Slow / Signal",
             f"{ind.get('macd_fast',12)} / {ind.get('macd_slow',26)} / {ind.get('macd_signal',9)}"],
            ["EMA", "기간", str(ind.get("ema_periods", [20, 60]))],
            ["볼린저밴드", "기간 / 표준편차",
             f"{ind.get('bb_period',20)} / {ind.get('bb_std',2.0)}"],
        ],
    ))
    blocks.append(_para(""))

    blocks.append(_heading("주문 설정", level=3))
    blocks.append(_table(
        ["항목", "값"],
        [
            ["모드", order.get("mode", "demo")],
            ["최대 보유 종목수", str(order.get("max_positions", 3))],
            ["종목당 수량", str(order.get("qty_per_trade", 1))],
            ["손절 %", diff(order.get("stop_loss_pct", -3.0), old_order.get("stop_loss_pct"))],
            ["익절 %", diff(order.get("take_profit_pct", 5.0), old_order.get("take_profit_pct"))],
            ["주문 방식", "시장가 (01)" if order.get("order_type") == "01" else "지정가 (00)"],
        ],
    ))
    blocks.append(_para(""))
    blocks.append(_divider())

    # ── 체결 내역 ──
    blocks.append(_heading("🧾 체결 내역", level=2))
    fill_rows = _build_fill_rows(filled_orders)
    if fill_rows:
        blocks.append(_table(
            ["시간", "종목", "구분", "수량", "가격", "상태"],
            fill_rows[:10],
        ))
    else:
        blocks.append(_para("당일 체결 내역이 없습니다."))
    blocks.append(_para(""))
    blocks.append(_divider())

    # ── 보유 포지션 ──
    blocks.append(_heading("💼 보유 포지션", level=2))
    holding_rows = _build_holding_rows(holdings)
    if holding_rows:
        blocks.append(_table(
            ["종목", "수량", "평균단가", "현재가", "평가손익", "수익률"],
            holding_rows[:10],
        ))
    else:
        blocks.append(_para("보유 포지션이 없습니다."))

    if balance_summary:
        summary_lines = [
            f"예수금: {_pick_first(balance_summary, ['dnca_tot_amt', 'dnca_tot_amt2']) or '-'}",
            f"총평가금액: {_pick_first(balance_summary, ['tot_evlu_amt', 'tot_evlu_pfls_amt']) or '-'}",
            f"총평가손익: {_pick_first(balance_summary, ['evlu_pfls_smtl_amt', 'tot_evlu_pfls_amt']) or '-'}",
        ]
        blocks.append(_callout(" | ".join(summary_lines), emoji="📌", color="blue_background"))
    blocks.append(_para(""))
    blocks.append(_divider())

    # ── 전략 성과 ──
    blocks.append(_heading("📈 전략 성과", level=2))
    perf_rows = _build_perf_rows(perf)
    blocks.append(_table(["지표", "값"], perf_rows))
    blocks.append(_para(""))
    blocks.append(_divider())

    # ── AI 피드백 ──
    blocks.append(_heading("🤖 AI 피드백", level=2))
    for note in notes_text.split("\n"):
        if note.strip():
            blocks.append(_bullet(note.strip("• ").strip()))
    blocks.append(_para(""))

    # ── 파라미터 변경 내역 ──
    if changes:
        blocks.append(_heading("✏️ 파라미터 변경 내역", level=2))
        blocks.append(_table(
            ["파라미터", "변경 전", "변경 후"],
            [
                [k, str(_get_nested(old_ind if k.startswith("indicators") else old_order,
                                    k.split(".")[-1])), str(v)]
                for k, v in changes.items()
            ],
        ))
        blocks.append(_para(""))
        blocks.append(_divider())

    # ── 일일 리포트 ──
    blocks.append(_heading("🗂️ 일일 리포트", level=2))
    report_text = report_path if report_path else "리포트 경로 정보 없음"
    blocks.append(_bullet(f"리포트 파일: {report_text}"))
    blocks.append(_bullet("포함 데이터: stats, fills, holdings, balance_summary, performance, feedback"))
    blocks.append(_bullet("이 페이지는 장 마감 후 run_review.py 결과를 요약한 Notion 뷰입니다."))

    return blocks


def _pick_first(d: dict, keys: list) -> str:
    for key in keys:
        val = d.get(key)
        if val not in (None, ""):
            return str(val)
    return ""


def _build_fill_rows(filled_orders: list) -> list:
    rows = []
    for fill in filled_orders:
        if not isinstance(fill, dict):
            continue
        time_val = _pick_first(fill, ["ord_tmd", "ord_time", "tot_ccld_tmd", "ord_tm"])
        if len(time_val) == 6 and time_val.isdigit():
            time_val = f"{time_val[:2]}:{time_val[2:4]}:{time_val[4:]}"
        code = _pick_first(fill, ["pdno", "mksc_shrn_iscd", "code"])
        name = _pick_first(fill, ["prdt_name", "hts_kor_isnm", "name"])
        side = _pick_first(fill, ["sll_buy_dvsn_cd_name", "trad_dvsn_name", "side"])
        qty = _pick_first(fill, ["tot_ccld_qty", "ord_qty", "qty"])
        price = _pick_first(fill, ["avg_prvs", "avg_prvs_1", "ord_unpr", "price"])
        status = _pick_first(fill, ["ord_gno_brno", "ccld_yn", "status"])
        rows.append([
            time_val or "-",
            f"{name} ({code})" if name else (code or "-"),
            side or "-",
            qty or "-",
            price or "-",
            status or "-",
        ])
    return rows


def _build_holding_rows(holdings: list) -> list:
    rows = []
    for item in holdings:
        if not isinstance(item, dict):
            continue
        code = _pick_first(item, ["pdno", "code"])
        name = _pick_first(item, ["prdt_name", "name"])
        qty = _pick_first(item, ["hldg_qty", "qty"])
        avg_price = _pick_first(item, ["pchs_avg_pric", "entry_price"])
        current_price = _pick_first(item, ["prpr", "price"])
        pnl = _pick_first(item, ["evlu_pfls_amt", "pnl_amt"])
        pnl_rate = _pick_first(item, ["evlu_pfls_rt", "pnl_pct"])
        rows.append([
            f"{name} ({code})" if name else (code or "-"),
            qty or "-",
            avg_price or "-",
            current_price or "-",
            pnl or "-",
            pnl_rate or "-",
        ])
    return rows


def _build_perf_rows(perf: dict) -> list:
    days = perf.get("days", []) if isinstance(perf, dict) else []
    total_days = len(days)
    total_trades = perf.get("total_trades", 0) if isinstance(perf, dict) else 0
    wins = perf.get("wins", 0) if isinstance(perf, dict) else 0
    total_pnl = perf.get("total_pnl_pct", 0.0) if isinstance(perf, dict) else 0.0

    recent = days[-7:]
    recent_avg = sum(d.get("pnl_pct", 0.0) for d in recent) / len(recent) if recent else 0.0
    recent_fills = sum(d.get("fills", 0) for d in recent) if recent else 0

    return [
        ["누적 기록 일수", str(total_days)],
        ["누적 주문 수", str(total_trades)],
        ["누적 승리 일수", str(wins)],
        ["누적 손익률", f"{total_pnl:.2f}%"],
        ["최근 7일 평균 손익률", f"{recent_avg:.2f}%"],
        ["최근 7일 체결 수", str(recent_fills)],
    ]


def setup_notion_interactive():
    """최초 1회 Notion 설정 (토큰 + DB ID 저장)"""
    print("\n=== Notion 연동 설정 ===")
    print("1. https://www.notion.so/my-integrations 에서 Integration 생성")
    print("2. Integration Token (secret_xxx...)을 입력하세요")
    token = input("Notion Token: ").strip()

    print("\n3. 전략 히스토리 DB ID를 입력하세요")
    print("   (Notion DB 주소에서 복사: notion.so/{page_id}?v=...)")
    db_id = input("DB ID: ").strip().replace("-", "")

    save_notion_config(token, db_id)
    print("✅ 설정 완료")


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup_notion_interactive()
    else:
        # 테스트 모드: 샘플 데이터로 기록
        print("[TEST] 샘플 데이터로 Notion 기록 테스트...")
        sample_stats = {
            "date": date.today().isoformat(),
            "total_orders": 2,
            "buys": 1,
            "sells": 1,
            "order_codes": ["005930", "035420"],
        }
        sample_feedback = {
            "changes": {},
            "notes": ["전략 변경 없음 (현재 성과 유지)"],
        }
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)

        ok = report_to_notion(sample_stats, sample_feedback, cfg, filled_count=1)
        if not ok:
            print("\n설정이 없습니다. 아래 명령으로 초기 설정:")
            print("  python notion_reporter.py --setup")
