"""
캐시 관리자 — 토큰 사용량 최소화를 위한 파일 기반 캐시
- TTL(분) 기반 만료 체크
- JSON 직렬화/역직렬화
"""
import json
import os
import time
from datetime import datetime
from typing import Any, Callable, Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def today() -> str:
    return datetime.now().strftime("%Y%m%d")


def cache_path(name: str, code: str = "") -> str:
    """캐시 파일 경로 반환"""
    filename = f"{today()}_{code}_{name}.json" if code else f"{today()}_{name}.json"
    return os.path.join(CACHE_DIR, filename)


def get_or_fetch(path: str, ttl_minutes: int, fetch_fn: Callable) -> Any:
    """
    캐시에서 데이터 로드. 없거나 만료된 경우 fetch_fn 호출 후 저장.
    ttl_minutes=0 이면 당일 1회만 (당일 파일 존재 시 재사용)
    """
    if os.path.exists(path):
        age_minutes = (time.time() - os.path.getmtime(path)) / 60
        if ttl_minutes == 0 or age_minutes < ttl_minutes:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"[CACHE HIT] {os.path.basename(path)} (age: {age_minutes:.1f}m)")
                return data
            except Exception:
                pass  # 캐시 손상 시 재조회

    print(f"[CACHE MISS] {os.path.basename(path)} — API 조회 중...")
    data = fetch_fn()
    if data is not None:
        save(path, data)
    return data


def save(path: str, data: Any) -> None:
    """데이터를 JSON 파일로 저장"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[CACHE SAVE] {os.path.basename(path)}")


def load(path: str) -> Optional[Any]:
    """파일에서 JSON 데이터 로드 (없으면 None)"""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_old_cache(days: int = 7) -> None:
    """N일 이상 된 캐시 파일 삭제"""
    cutoff = time.time() - days * 86400
    removed = 0
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        if os.path.getmtime(fpath) < cutoff:
            os.remove(fpath)
            removed += 1
    if removed:
        print(f"[CACHE CLEAN] {removed}개 오래된 캐시 삭제")
