"""
기술 지표 계산 — pandas 기반 (pandas-ta 선택적 사용)
캐시된 OHLCV 데이터를 받아 지표 계산 후 반환
"""
from typing import Optional
import json

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def ohlcv_to_df(ohlcv_rows: list) -> "pd.DataFrame":
    """KIS API 일봉 응답 → DataFrame (최신 → 과거 정렬)"""
    import pandas as pd
    df = pd.DataFrame(ohlcv_rows)

    # KIS 컬럼명 통일
    rename_map = {
        "stck_bsop_date": "date",
        "stck_oprc": "open",
        "stck_hgpr": "high",
        "stck_lwpr": "low",
        "stck_clpr": "close",
        "acml_vol": "volume",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

    return df


def calc_rsi(df: "pd.DataFrame", period: int = 14) -> "pd.Series":
    """RSI 계산"""
    import pandas as pd
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def calc_macd(df: "pd.DataFrame", fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD 계산 → {macd, signal, hist} 시리즈"""
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "hist": histogram}


def calc_ema(df: "pd.DataFrame", period: int) -> "pd.Series":
    return df["close"].ewm(span=period, adjust=False).mean()


def calc_bollinger(df: "pd.DataFrame", period: int = 20, std_mult: float = 2.0) -> dict:
    """볼린저 밴드"""
    mid = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    return {"upper": mid + std_mult * std, "mid": mid, "lower": mid - std_mult * std}


def add_indicators(ohlcv_rows: list, cfg: dict) -> Optional[dict]:
    """
    OHLCV 행 목록에 지표를 계산하여 최신 값 반환
    cfg: strategy/config.json의 indicators 섹션
    반환: {rsi, macd, macd_signal, macd_hist, ema_20, ema_60, bb_upper, bb_mid, bb_lower, close, volume}
    """
    if not HAS_PANDAS or not ohlcv_rows:
        return None

    import pandas as pd
    df = ohlcv_to_df(ohlcv_rows)
    if len(df) < 30:
        print(f"[WARNING] 데이터 부족 ({len(df)}행) — 지표 계산 불가")
        return None

    ind = cfg.get("indicators", {})

    rsi = calc_rsi(df, ind.get("rsi_period", 14))
    macd_d = calc_macd(df, ind.get("macd_fast", 12), ind.get("macd_slow", 26), ind.get("macd_signal", 9))
    bb = calc_bollinger(df, ind.get("bb_period", 20), ind.get("bb_std", 2.0))

    ema_periods = ind.get("ema_periods", [20, 60])
    emas = {p: calc_ema(df, p) for p in ema_periods}

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]

    result = {
        "date": str(last.get("date", "")),
        "close": float(last["close"]),
        "volume": float(last.get("volume", 0)),
        "rsi": round(float(rsi.iloc[-1]), 2),
        "macd": round(float(macd_d["macd"].iloc[-1]), 4),
        "macd_signal": round(float(macd_d["signal"].iloc[-1]), 4),
        "macd_hist": round(float(macd_d["hist"].iloc[-1]), 4),
        "macd_hist_prev": round(float(macd_d["hist"].iloc[-2]), 4) if len(df) >= 2 else 0,
        "bb_upper": round(float(bb["upper"].iloc[-1]), 2),
        "bb_mid": round(float(bb["mid"].iloc[-1]), 2),
        "bb_lower": round(float(bb["lower"].iloc[-1]), 2),
    }

    for p in ema_periods:
        result[f"ema_{p}"] = round(float(emas[p].iloc[-1]), 2)

    # MACD 골든크로스 여부
    result["macd_cross_up"] = (
        float(macd_d["hist"].iloc[-1]) > 0 and float(macd_d["hist"].iloc[-2]) <= 0
        if len(df) >= 2 else False
    )
    result["macd_cross_down"] = (
        float(macd_d["hist"].iloc[-1]) < 0 and float(macd_d["hist"].iloc[-2]) >= 0
        if len(df) >= 2 else False
    )

    # EMA 정렬 여부 (상승 추세)
    if len(ema_periods) >= 2:
        e1, e2 = sorted(ema_periods)
        result["ema_bullish"] = result[f"ema_{e1}"] > result[f"ema_{e2}"]

    return result
