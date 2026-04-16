"""
성과 분석 + AI 피드백 루프
당일 체결 내역 분석 → strategy/config.json 자동 수정
"""
import json
import os
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(__file__))
import kis_helper as kis
import executor


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRATEGY_DIR = os.path.join(BASE_DIR, "strategy")
PERF_PATH = os.path.join(STRATEGY_DIR, "performance.json")
FEEDBACK_PATH = os.path.join(STRATEGY_DIR, "feedback_log.json")
CONFIG_PATH = os.path.join(STRATEGY_DIR, "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict):
    cfg["updated_at"] = datetime.now().strftime("%Y-%m-%d")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def load_performance() -> dict:
    if os.path.exists(PERF_PATH):
        with open(PERF_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"days": [], "total_trades": 0, "wins": 0, "total_pnl_pct": 0.0}


def save_performance(perf: dict):
    with open(PERF_PATH, "w", encoding="utf-8") as f:
        json.dump(perf, f, ensure_ascii=False, indent=2)


def load_feedback_log() -> list:
    if os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_feedback_log(log: list):
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def calc_daily_stats(orders: list) -> dict:
    """당일 주문 리스트 → 통계"""
    buys = [o for o in orders if o["side"] == "buy"]
    sells = [o for o in orders if o["side"] == "sell"]
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_orders": len(orders),
        "buys": len(buys),
        "sells": len(sells),
        "order_codes": list(set(o["code"] for o in orders)),
    }


def ai_feedback(stats: dict, perf: dict, cfg: dict) -> dict:
    """
    성과 기반 AI 피드백 — 수익률 최우선 원칙
    모든 파라미터 조정의 목표: 기대수익(승률 × 평균수익) 최대화
    """
    changes = {}
    notes = []
    ind_cfg = cfg.get("indicators", {})
    order_cfg = cfg.get("order", {})

    # 최근 7일 성과 분석
    recent = perf.get("days", [])[-7:]
    if len(recent) >= 3:
        win_days = [d for d in recent if d.get("pnl_pct", 0) > 0]
        loss_days = [d for d in recent if d.get("pnl_pct", 0) < 0]
        win_rate = len(win_days) / len(recent)
        avg_pnl = sum(d.get("pnl_pct", 0) for d in recent) / len(recent)

        # 기대수익 = 승률 × 평균수익 (핵심 지표)
        avg_win = sum(d.get("pnl_pct", 0) for d in win_days) / len(win_days) if win_days else 0
        avg_loss = sum(d.get("pnl_pct", 0) for d in loss_days) / len(loss_days) if loss_days else 0
        expected_return = win_rate * avg_win + (1 - win_rate) * avg_loss
        profit_factor = abs(avg_win * len(win_days)) / abs(avg_loss * len(loss_days)) if loss_days and avg_loss != 0 else 99

        notes.append(f"기대수익: {expected_return:.2f}% | 손익비: {profit_factor:.2f} | 승률: {win_rate*100:.0f}% | 평균수익: {avg_pnl:.2f}%")

        # 1순위: 수익 기회 극대화 — 익절 목표 상향
        if win_rate >= 0.5 and avg_win < order_cfg.get("take_profit_pct", 5.0) * 0.7:
            # 수익이 나고 있지만 익절이 너무 빠름 → 목표 상향
            new_tp = min(order_cfg.get("take_profit_pct", 5.0) + 1.0, 12.0)
            changes["order.take_profit_pct"] = new_tp
            notes.append(f"수익 기회 극대화: 익절 목표 상향 {order_cfg.get('take_profit_pct', 5.0)}% → {new_tp}%")

        # 2순위: 기대수익 음수 → 진입 조건 강화
        if expected_return < -0.5:
            new_rsi = max(ind_cfg.get("rsi_oversold", 35) - 3, 20)
            changes["indicators.rsi_oversold"] = new_rsi
            notes.append(f"기대수익 {expected_return:.2f}% 음수 → RSI 진입 조건 강화: {new_rsi}")

        # 3순위: 손익비 낮고 평균 손실 과대 → 손절 강화 (수익 기회 과도 차단 방지)
        if profit_factor < 1.2 and avg_loss < -2.5:
            new_stop = max(order_cfg.get("stop_loss_pct", -3.0) + 0.5, -2.0)
            changes["order.stop_loss_pct"] = new_stop
            notes.append(f"손익비 {profit_factor:.2f} 낮음 + 평균손실 {avg_loss:.1f}% → 손절 강화: {new_stop}%")

        # 4순위: 고승률 + 높은 평균수익 → 익절 목표 적극 상향
        if win_rate >= 0.6 and avg_win > 2.0:
            new_tp = min(order_cfg.get("take_profit_pct", 5.0) + 2.0, 15.0)
            if "order.take_profit_pct" not in changes:
                changes["order.take_profit_pct"] = new_tp
                notes.append(f"고성과 확인 → 익절 목표 적극 상향: {new_tp}%")

    if not changes:
        notes.append("전략 변경 없음 — 현재 수익률 구조 유지")

    return {"changes": changes, "notes": notes}


def apply_changes(cfg: dict, changes: dict) -> dict:
    """피드백 변경사항을 config에 적용"""
    for key, val in changes.items():
        parts = key.split(".")
        obj = cfg
        for part in parts[:-1]:
            obj = obj.setdefault(part, {})
        old_val = obj.get(parts[-1])
        obj[parts[-1]] = val
        print(f"  [CONFIG] {key}: {old_val} → {val}")
    return cfg


def run_daily_review():
    """일일 복기 실행 (16:00 KST 스케줄)"""
    print(f"\n{'='*50}")
    print(f"[일일 복기] {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")

    # 1. 당일 주문 내역 (로컬 DB)
    today_orders = executor.get_today_orders()
    stats = calc_daily_stats(today_orders)
    print(f"당일 주문: {stats['total_orders']}건 (매수:{stats['buys']}, 매도:{stats['sells']})")

    # 2. KIS API 체결 내역 (토큰 1회 사용)
    filled = kis.get_daily_orders()
    fills_count = len(filled) if filled else 0
    print(f"실제 체결: {fills_count}건")

    # 2-1. 현재 잔고/보유 포지션 스냅샷
    balance = kis.get_balance()
    holdings = balance.get("holdings", []) if balance else []
    balance_summary = balance.get("summary", {}) if balance else {}
    print(f"보유 포지션 스냅샷: {len(holdings)}건")

    # 3. 성과 기록
    perf = load_performance()
    day_stat = {
        **stats,
        "fills": fills_count,
        "pnl_pct": 0.0,  # TODO: 잔고 비교로 계산 가능
    }
    perf["days"].append(day_stat)
    perf["total_trades"] += stats["total_orders"]
    save_performance(perf)

    # 4. AI 피드백
    cfg = load_config()
    old_cfg = json.loads(json.dumps(cfg))  # 변경 전 스냅샷
    feedback = ai_feedback(stats, perf, cfg)

    print(f"\n[피드백]")
    for note in feedback["notes"]:
        print(f"  • {note}")

    if feedback["changes"]:
        print(f"\n[전략 파라미터 수정]")
        cfg = apply_changes(cfg, feedback["changes"])
        cfg["version"] = cfg.get("version", 1) + 1
        save_config(cfg)

    # 5. 피드백 로그 저장
    log = load_feedback_log()
    log.append({
        "date": stats["date"],
        "stats": stats,
        "feedback": feedback,
    })
    save_feedback_log(log)

    # 6. 일일 리포트 저장
    report_path = os.path.join(LOGS_DIR, f"{stats['date']}_review.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "stats": stats,
                "fills": filled,
                "holdings": holdings,
                "balance_summary": balance_summary,
                "performance": perf,
                "feedback": feedback,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n✅ 리포트 저장: {report_path}")

    # 7. Notion 전략 히스토리 기록
    try:
        import notion_reporter
        notion_reporter.report_to_notion(
            stats,
            feedback,
            cfg,
            filled_count=fills_count,
            old_cfg=old_cfg,
            filled_orders=filled or [],
            holdings=holdings,
            balance_summary=balance_summary,
            perf=perf,
            report_path=report_path,
        )
    except Exception as e:
        print(f"[NOTION] 기록 중 오류 (무시): {e}")

    return feedback
