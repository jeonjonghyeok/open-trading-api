"""
매매 사이클 메인 진입점 (15분마다 실행)
Usage:
  python run_cycle.py            # 모의투자 실제 실행
  python run_cycle.py --dry-run  # 주문 없이 신호만 확인
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

import cache_manager as cache
import kis_helper as kis
import indicators as ind_calc
import signals
import executor


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "strategy", "config.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def is_market_hours(cfg: dict) -> bool:
    now = datetime.now()
    # 평일 체크
    if now.weekday() >= 5:
        return False
    open_t = datetime.strptime(cfg["schedule"]["market_open"], "%H:%M").time()
    close_t = datetime.strptime(cfg["schedule"]["market_close"], "%H:%M").time()
    return open_t <= now.time() <= close_t


def select_candidates(cfg: dict) -> list:
    """거래량 순위 기반 종목 선별 (당일 1회 캐싱)"""
    path = cache.cache_path("candidates")
    count = cfg["stock_selection"]["candidate_count"]
    market = cfg["stock_selection"]["market"]
    min_price = cfg["stock_selection"].get("min_price", 5000)
    max_price = cfg["stock_selection"].get("max_price", 300000)

    def fetch():
        rows = kis.get_volume_rank(market)
        if not rows:
            return []
        result = []
        for r in rows:
            price = int(r.get("stck_prpr", 0))
            if min_price <= price <= max_price:
                result.append({
                    "code": r.get("mksc_shrn_iscd", ""),
                    "name": r.get("hts_kor_isnm", ""),
                    "price": price,
                    "volume": int(r.get("acml_vol", 0)),
                })
            if len(result) >= count:
                break
        return result

    return cache.get_or_fetch(path, ttl_minutes=0, fetch_fn=fetch) or []


def get_indicators_for(code: str, cfg: dict) -> dict:
    """종목 지표 계산 (분봉 30분 캐싱, 일봉 당일 1회)"""
    ohlcv_path = cache.cache_path("ohlcv", code)
    ind_path = cache.cache_path("indicators", code)

    # 기존 지표 캐시 확인 (30분 TTL)
    cached_ind = cache.load(ind_path)
    if cached_ind:
        age = (os.path.getmtime(ind_path))
        import time
        if time.time() - age < 30 * 60:
            print(f"[CACHE HIT] 지표 {code} (캐시)")
            return cached_ind

    # 일봉 데이터 (당일 1회)
    ohlcv = cache.get_or_fetch(
        ohlcv_path,
        ttl_minutes=0,
        fetch_fn=lambda: kis.get_ohlcv(code, period="D", count=120)
    )

    if not ohlcv:
        return {}

    result = ind_calc.add_indicators(ohlcv, cfg)
    if result:
        # 현재가로 close 갱신 (실시간)
        price_data = kis.get_price(code)
        if price_data:
            result["close"] = int(price_data.get("stck_prpr", result["close"]))
            result["rsi_realtime_note"] = "close는 실시간 현재가로 갱신됨"

        cache.save(ind_path, result)

    return result or {}


def run(dry_run: bool = False, force: bool = False):
    print(f"\n{'='*50}")
    print(f"[매매 사이클] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {'[DRY-RUN]' if dry_run else '[DEMO]'}")
    print(f"{'='*50}")

    cfg = load_config()
    print(f"전략 v{cfg.get('version', 1)}: {cfg.get('description', '')}")

    # 장중 시간 체크
    if not is_market_hours(cfg):
        now = datetime.now()
        if force:
            print(f"⚠️  장 시간 외 ({now.strftime('%H:%M')}) — --force 옵션으로 강제 실행")
        else:
            print(f"⏰ 장 시간 외 ({now.strftime('%H:%M')}) — 사이클 스킵")
            return

    # 현재 보유 포지션 (로컬 DB)
    holdings = executor.get_holdings()
    print(f"현재 보유: {len(holdings)}종목 / 최대 {cfg['order']['max_positions']}종목")

    # 종목 선별
    candidates = select_candidates(cfg)
    if not candidates:
        print("❌ 후보 종목 없음")
        return
    print(f"후보 종목: {[c['name'] for c in candidates]}")

    # 각 종목 신호 평가 → 주문
    orders_placed = 0
    for c in candidates:
        code = c["code"]
        name = c["name"]
        print(f"\n--- {name} ({code}) ---")

        ind = get_indicators_for(code, cfg)
        if not ind:
            print(f"  지표 없음 — 스킵")
            continue

        print(f"  RSI={ind.get('rsi', 0):.1f}  MACD_hist={ind.get('macd_hist', 0):.4f}  "
              f"EMA20={ind.get('ema_20', 0):,.0f}  현재가={ind.get('close', 0):,}")

        action = signals.evaluate(code, ind, holdings, cfg)
        print(f"  → {action['action'].upper()}: {action['reason']}")

        if action["action"] in ("buy", "sell"):
            success = executor.execute(code, action, ind, dry_run=dry_run)
            if success:
                orders_placed += 1
                if action["action"] == "buy":
                    holdings.append({"code": code, "entry_price": ind.get("close", 0), "qty": action.get("qty", 1)})
                elif action["action"] == "sell":
                    holdings = [h for h in holdings if h["code"] != code]

    print(f"\n{'='*50}")
    print(f"사이클 완료: {orders_placed}건 주문")
    cache.clear_old_cache(days=7)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    run(dry_run=dry_run, force=force)
