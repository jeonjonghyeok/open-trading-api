"""
KIS API 헬퍼 — MCP 없이 직접 KIS REST API 호출
kis_devlp.yaml 설정 기반으로 인증 + 데이터 조회
"""
import json
import os
import time
from datetime import datetime
from typing import Any, Optional

import requests
import yaml


CONFIG_PATH = os.path.expanduser("~/KIS/config/kis_devlp.yaml")
TOKEN_CACHE = os.path.expanduser("~/KIS/config/paper_token.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_token(cfg: dict) -> str:
    """
    모의투자 토큰 발급 (캐싱, 만료 30분 전 자동 갱신)
    """
    if os.path.exists(TOKEN_CACHE):
        try:
            with open(TOKEN_CACHE, "r") as f:
                cached = json.load(f)
            expired_at = datetime.strptime(cached["expired_at"], "%Y-%m-%d %H:%M:%S")
            remaining = (expired_at - datetime.now()).total_seconds()
            if remaining > 1800:  # 만료 30분 이상 남음
                print(f"[TOKEN] 캐시 사용 (만료까지 {remaining/3600:.1f}h)")
                return cached["access_token"]
        except Exception:
            pass

    print("[TOKEN] 신규 발급 중...")
    url = cfg["vps"] + "/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey": cfg["paper_app"],
        "appsecret": cfg["paper_sec"],
    }
    resp = requests.post(url, json=body, headers={"content-type": "application/json"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    expired_at = data["access_token_token_expired"]

    os.makedirs(os.path.dirname(TOKEN_CACHE), exist_ok=True)
    with open(TOKEN_CACHE, "w") as f:
        json.dump({"access_token": token, "expired_at": expired_at}, f)
    print(f"[TOKEN] 발급 완료 (만료: {expired_at})")
    return token


def build_headers(cfg: dict, token: str, tr_id: str, use_real_url: bool = False) -> dict:
    """
    use_real_url=True: 시장 데이터 조회 시 실전 앱키 사용 (모의환경에서 막힌 API 우회)
    주문/잔고 등 계좌 관련은 항상 paper 앱키 사용
    """
    app_key = cfg["my_app"] if use_real_url and cfg.get("my_app") else cfg["paper_app"]
    app_sec = cfg["my_sec"] if use_real_url and cfg.get("my_sec") else cfg["paper_sec"]
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_sec,
        "tr_id": tr_id,
        "custtype": "P",
    }


# KOSPI 대형주 fallback 목록 (거래량 순위 API 불가 시 사용)
FALLBACK_CANDIDATES = [
    {"code": "005930", "name": "삼성전자"},
    {"code": "000660", "name": "SK하이닉스"},
    {"code": "035420", "name": "NAVER"},
    {"code": "005380", "name": "현대차"},
    {"code": "051910", "name": "LG화학"},
    {"code": "006400", "name": "삼성SDI"},
    {"code": "035720", "name": "카카오"},
    {"code": "068270", "name": "셀트리온"},
    {"code": "105560", "name": "KB금융"},
    {"code": "055550", "name": "신한지주"},
]


def get_price(code: str) -> Optional[dict]:
    """주식 현재가 조회 (시세 조회는 모의/실전 동일 TR ID)"""
    cfg = load_config()
    token = get_token(cfg)
    url = cfg["vps"] + "/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = build_headers(cfg, token, "FHKST01010100")
    params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": code}
    time.sleep(0.5)  # 초당 거래건수 제한 방지 (모의투자: 초당 2건 제한)
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    data = resp.json()
    if data.get("rt_cd") == "0":
        return data["output"]
    print(f"[ERROR] 현재가 조회 실패: {data.get('msg1')}")
    return None


def get_ohlcv(code: str, period: str = "D", count: int = 100) -> Optional[list]:
    """
    일봉/주봉/월봉 조회 (시세 조회는 모의/실전 동일 TR ID)
    period: D=일, W=주, M=월
    """
    cfg = load_config()
    token = get_token(cfg)
    url = cfg["vps"] + "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    headers = build_headers(cfg, token, "FHKST03010100")
    today_str = datetime.now().strftime("%Y%m%d")
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
        "fid_input_date_1": "19000101",
        "fid_input_date_2": today_str,
        "fid_period_div_code": period,
        "fid_org_adj_prc": "0",
    }
    time.sleep(0.5)  # Rate limit 방지
    resp = requests.get(url, headers=headers, params=params, timeout=15)
    data = resp.json()
    if data.get("rt_cd") == "0":
        rows = data.get("output2", [])[:count]
        return rows
    print(f"[ERROR] 일봉 조회 실패 ({code}): {data.get('msg1')}")
    return None


def get_volume_rank(market: str = "J") -> Optional[list]:
    """
    거래량 순위 조회 (종목 선별용)
    실전 API가 있으면 실전 URL 사용, 없으면 fallback 목록 반환
    """
    cfg = load_config()

    # 실전 앱키가 없으면 fallback
    if not cfg.get("my_app"):
        print("[INFO] 실전 앱키 없음 — KOSPI 대형주 fallback 사용")
        return _get_fallback_with_price(cfg)

    try:
        token = get_token(cfg)
        url = cfg["prod"] + "/uapi/domestic-stock/v1/quotations/volume-rank"
        headers = build_headers(cfg, token, "FHPST01710000", use_real_url=True)
        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_cond_scr_div_code": "20171",
            "fid_input_iscd": "0001",
            "fid_div_cls_code": "0",
            "fid_blng_cls_code": "0",
            "fid_trgt_cls_code": "111111111",
            "fid_trgt_exls_cls_code": "000000",
            "fid_input_price_1": "5000",
            "fid_input_price_2": "500000",
            "fid_vol_cnt": "100000",
            "fid_input_date_1": "",
        }
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        data = resp.json()
        if data.get("rt_cd") == "0":
            return data.get("output", [])
        print(f"[WARNING] 거래량순위 API 실패: {data.get('msg1')} — fallback 사용")
    except Exception as e:
        print(f"[WARNING] 거래량순위 조회 오류: {e} — fallback 사용")

    return _get_fallback_with_price(cfg)


def _get_fallback_with_price(cfg: dict) -> list:
    """Fallback 종목 목록에 현재가 붙여서 반환"""
    token = get_token(cfg)
    result = []
    for item in FALLBACK_CANDIDATES:
        try:
            price_data = get_price(item["code"])
            price = int(price_data.get("stck_prpr", 0)) if price_data else 0
            volume = int(price_data.get("acml_vol", 0)) if price_data else 0
            result.append({
                "mksc_shrn_iscd": item["code"],
                "hts_kor_isnm": item["name"],
                "stck_prpr": str(price),
                "acml_vol": str(volume),
            })
        except Exception:
            pass
    return result


def place_order(code: str, qty: int, price: int, side: str = "buy") -> Optional[dict]:
    """
    모의투자 현금 주문
    side: 'buy' | 'sell'
    price: 0 이면 시장가 (ord_dvsn='01'), 지정가는 ord_dvsn='00'
    """
    cfg = load_config()
    token = get_token(cfg)
    tr_id = "VTTC0012U" if side == "buy" else "VTTC0011U"
    url = cfg["vps"] + "/uapi/domestic-stock/v1/trading/order-cash"
    headers = build_headers(cfg, token, tr_id)
    body = {
        "CANO": cfg["my_paper_stock"],
        "ACNT_PRDT_CD": cfg["my_prod"],
        "PDNO": code,
        "ORD_DVSN": "01" if price == 0 else "00",
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
        "EXCG_ID_DVSN_CD": "KRX",
        "SLL_TYPE": "" if side == "buy" else "01",
        "CNDT_PRIC": "",
    }
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    data = resp.json()
    if data.get("rt_cd") == "0":
        return data["output"]
    print(f"[ERROR] 주문 실패 ({code} {side}): {data.get('msg1')}")
    return None


def get_balance() -> Optional[dict]:
    """잔고 조회"""
    cfg = load_config()
    token = get_token(cfg)
    url = cfg["vps"] + "/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = build_headers(cfg, token, "VTTC8434R")
    params = {
        "CANO": cfg["my_paper_stock"],
        "ACNT_PRDT_CD": cfg["my_prod"],
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "N",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    data = resp.json()
    if data.get("rt_cd") == "0":
        return {
            "holdings": data.get("output1", []),
            "summary": data.get("output2", [{}])[0] if data.get("output2") else {},
        }
    print(f"[ERROR] 잔고 조회 실패: {data.get('msg1')}")
    return None


def get_daily_orders(start: str = "", end: str = "") -> Optional[list]:
    """당일(또는 기간) 체결 내역 조회"""
    cfg = load_config()
    token = get_token(cfg)
    today_str = datetime.now().strftime("%Y%m%d")
    url = cfg["vps"] + "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    headers = build_headers(cfg, token, "VTTC8001R")
    params = {
        "CANO": cfg["my_paper_stock"],
        "ACNT_PRDT_CD": cfg["my_prod"],
        "INQR_STRT_DT": start or today_str,
        "INQR_END_DT": end or today_str,
        "SLL_BUY_DVSN_CD": "00",
        "INQR_DVSN": "00",
        "PDNO": "",
        "CCLD_DVSN": "00",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    data = resp.json()
    if data.get("rt_cd") == "0":
        return data.get("output1", [])
    print(f"[ERROR] 체결내역 조회 실패: {data.get('msg1')}")
    return None
