"""
신호 생성 — config.json 기반 매수/매도 신호 판단
"""
import json
import os
from typing import Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "strategy", "config.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def check_buy_signal(ind: dict, cfg: dict) -> tuple[bool, list[str]]:
    """
    매수 신호 판단
    반환: (신호여부, 매칭된 조건 목록)
    """
    signal_cfg = cfg.get("signal", {})
    ind_cfg = cfg.get("indicators", {})

    rsi_oversold = ind_cfg.get("rsi_oversold", 35)
    reasons = []

    # RSI 과매도
    rsi_ok = ind.get("rsi", 100) < rsi_oversold
    if rsi_ok:
        reasons.append(f"RSI={ind['rsi']:.1f} < {rsi_oversold} (과매도)")

    # MACD 골든크로스 또는 히스토그램 상향전환
    macd_ok = (
        ind.get("macd_cross_up", False) or
        (ind.get("macd_hist", 0) > 0 and ind.get("macd_hist_prev", 0) <= 0)
    )
    if macd_ok:
        reasons.append(f"MACD 상향전환 (hist={ind.get('macd_hist', 0):.4f})")

    # EMA 정렬 체크 (옵션)
    ema_required = signal_cfg.get("require_ema_bullish", False)
    ema_ok = ind.get("ema_bullish", True) if ema_required else True
    if not ema_ok:
        return False, ["EMA 하락 추세 — 매수 차단"]

    # 최종: RSI + MACD 둘 다 충족
    triggered = rsi_ok and macd_ok
    return triggered, reasons


def check_sell_signal(ind: dict, cfg: dict, entry_price: float) -> tuple[bool, str]:
    """
    매도 신호 판단
    반환: (신호여부, 사유)
    """
    ind_cfg = cfg.get("indicators", {})
    order_cfg = cfg.get("order", {})

    rsi_overbought = ind_cfg.get("rsi_overbought", 70)
    stop_loss_pct = order_cfg.get("stop_loss_pct", -3.0)
    take_profit_pct = order_cfg.get("take_profit_pct", 5.0)

    current_price = ind.get("close", entry_price)
    pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0

    # 손절
    if pnl_pct <= stop_loss_pct:
        return True, f"손절 ({pnl_pct:.1f}% ≤ {stop_loss_pct}%)"

    # 익절
    if pnl_pct >= take_profit_pct:
        return True, f"익절 ({pnl_pct:.1f}% ≥ {take_profit_pct}%)"

    # RSI 과매수
    if ind.get("rsi", 0) > rsi_overbought:
        return True, f"RSI={ind['rsi']:.1f} > {rsi_overbought} (과매수)"

    # MACD 데드크로스
    if ind.get("macd_cross_down", False):
        return True, f"MACD 하향전환"

    return False, ""


def evaluate(code: str, ind: dict, holdings: list, cfg: Optional[dict] = None) -> dict:
    """
    단일 종목에 대해 매수/매도/홀드 판단
    holdings: 현재 보유 포지션 목록 [{code, entry_price, qty}, ...]
    반환: {action: 'buy'|'sell'|'hold', reason: str}
    """
    if cfg is None:
        cfg = load_config()

    # 이미 보유 중인지 확인
    holding = next((h for h in holdings if h.get("code") == code), None)

    if holding:
        # 보유 중 → 매도 판단
        sell_ok, reason = check_sell_signal(ind, cfg, float(holding.get("entry_price", 0)))
        if sell_ok:
            return {"action": "sell", "reason": reason, "qty": holding.get("qty", 1)}
        return {"action": "hold", "reason": f"보유 유지 (RSI={ind.get('rsi', 0):.1f})"}
    else:
        # 미보유 → 매수 판단
        max_pos = cfg.get("order", {}).get("max_positions", 3)
        if len(holdings) >= max_pos:
            return {"action": "hold", "reason": f"최대 보유 종목 수 초과 ({max_pos})"}

        buy_ok, reasons = check_buy_signal(ind, cfg)
        if buy_ok:
            return {"action": "buy", "reason": " + ".join(reasons), "qty": cfg.get("order", {}).get("qty_per_trade", 1)}
        return {"action": "hold", "reason": f"신호 없음 (RSI={ind.get('rsi', 0):.1f}, MACD_hist={ind.get('macd_hist', 0):.4f})"}
