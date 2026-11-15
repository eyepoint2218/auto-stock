"""SQLite 저장소."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    """간단한 주문/체결/로그 저장소."""

    def __init__(self, db_path: str = "autotrader.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    qty INTEGER,
                    price INTEGER,
                    status TEXT,
                    created_at TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    qty INTEGER,
                    price INTEGER,
                    status TEXT,
                    created_at TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    message TEXT,
                    created_at TEXT
                )
                """
            )
            conn.commit()

    def insert_order(self, order: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO orders(order_id, symbol, side, qty, price, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.get("order_id"),
                    order.get("symbol"),
                    order.get("side"),
                    int(order.get("qty", 0)),
                    int(order.get("price", 0)),
                    order.get("status"),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def insert_execution(self, execution: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO executions(order_id, symbol, side, qty, price, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution.get("order_id"),
                    execution.get("symbol"),
                    execution.get("side"),
                    int(execution.get("qty", 0)),
                    int(execution.get("price", 0)),
                    execution.get("status"),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def insert_log(self, level: str, message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO logs(level, message, created_at) VALUES (?, ?, ?)",
                (level, message, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def list_orders(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
