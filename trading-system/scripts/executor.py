"""
주문 실행 + 이력 관리
SQLite(orders.db)에 모든 주문 기록
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(__file__))
import kis_helper as kis


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "orders", "orders.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            code        TEXT NOT NULL,
            side        TEXT NOT NULL,
            qty         INTEGER,
            price       INTEGER,
            order_no    TEXT,
            status      TEXT DEFAULT 'placed',
            entry_price REAL,
            exit_price  REAL,
            pnl_pct     REAL,
            reason      TEXT,
            indicators  TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def save_order(code: str, side: str, qty: int, price: int,
               order_no: str = "", reason: str = "", ind: dict = None) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("""
        INSERT INTO orders (timestamp, code, side, qty, price, order_no, reason, indicators)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        code, side, qty, price, order_no, reason,
        json.dumps(ind, ensure_ascii=False) if ind else ""
    ))
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_holdings() -> list:
    """현재 보유 포지션 (orders.db 기반, 미청산 포지션)"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT code, price AS entry_price,
               SUM(CASE WHEN side='buy' THEN qty ELSE -qty END) AS net_qty
        FROM orders
        WHERE status IN ('placed', 'filled')
        GROUP BY code
        HAVING net_qty > 0
    """).fetchall()
    conn.close()
    return [{"code": r[0], "entry_price": r[1], "qty": r[2]} for r in rows]


def execute(code: str, action: dict, ind: dict, dry_run: bool = False) -> bool:
    """
    신호에 따라 주문 실행
    action: signals.evaluate() 반환값 {action, reason, qty}
    dry_run=True: 주문 없이 로그만
    """
    side = action.get("action")
    if side not in ("buy", "sell"):
        return False

    qty = int(action.get("qty", 1))
    price = int(ind.get("close", 0))  # 시장가 주문 (price=0 도 가능)
    reason = action.get("reason", "")

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}주문: {code} {side.upper()} {qty}주 @{price:,}원")
    print(f"  사유: {reason}")

    if dry_run:
        save_order(code, side, qty, price, order_no="DRY", reason=reason, ind=ind)
        return True

    result = kis.place_order(code, qty, price, side)
    if result:
        order_no = result.get("ODNO", "")
        print(f"  ✅ 주문 접수: {order_no}")
        save_order(code, side, qty, price, order_no=order_no, reason=reason, ind=ind)
        return True
    else:
        print(f"  ❌ 주문 실패")
        return False


def get_today_orders() -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, timestamp, code, side, qty, price, order_no, status, reason
        FROM orders WHERE timestamp LIKE ?
        ORDER BY timestamp DESC
    """, (f"{today}%",)).fetchall()
    conn.close()
    return [
        {"id": r[0], "timestamp": r[1], "code": r[2], "side": r[3],
         "qty": r[4], "price": r[5], "order_no": r[6], "status": r[7], "reason": r[8]}
        for r in rows
    ]
