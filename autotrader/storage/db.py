"""SQLite 저장소."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class SQLiteStorage:
    """주문/체결/로그 저장용 SQLite 래퍼."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    raw_response TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    executed_price INTEGER NOT NULL,
                    executed_at TEXT NOT NULL,
                    raw_response TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: int,
        status: str,
        reason: str,
        raw_response: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO orders(symbol, side, qty, price, status, reason, raw_response, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (symbol, side, qty, price, status, reason, raw_response, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def insert_execution(
        self,
        order_id: str,
        symbol: str,
        qty: int,
        executed_price: int,
        raw_response: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO executions(order_id, symbol, qty, executed_price, executed_at, raw_response)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (order_id, symbol, qty, executed_price, datetime.utcnow().isoformat(), raw_response),
            )
            conn.commit()

    def insert_log(self, level: str, message: str, detail: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO logs(level, message, detail, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (level, message, detail, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def get_recent_orders(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
