import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_PATH = Path("data/insights.db")


@contextmanager
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Создаёт таблицы, если их нет. Идемпотентно."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS insights (
                insight_id      TEXT PRIMARY KEY,
                client_id       TEXT NOT NULL,
                event_id        TEXT,
                event_title     TEXT,
                event_text      TEXT,
                interpretation  TEXT,
                risks           TEXT,
                opportunities   TEXT,
                actions         TEXT,
                alfa_view       TEXT,
                confidence      REAL,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_client ON insights(client_id);
            CREATE INDEX IF NOT EXISTS idx_created ON insights(created_at DESC);

            CREATE TABLE IF NOT EXISTS traces (
                trace_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id  TEXT NOT NULL,
                step        TEXT,
                payload     TEXT,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (insight_id) REFERENCES insights(insight_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_trace_insight ON traces(insight_id);
        """)


def save_insight(insight: dict) -> str:
    """Сохраняет или обновляет инсайт."""
    init_db()
    now = datetime.utcnow().isoformat()
    insight_id = insight.get("insight_id") or f"ins_{int(datetime.utcnow().timestamp() * 1000)}"

    with _connect() as conn:
        existing = conn.execute("SELECT created_at FROM insights WHERE insight_id = ?", (insight_id,)).fetchone()
        created_at = existing["created_at"] if existing else now

        conn.execute("""
            INSERT INTO insights (
                insight_id, client_id, event_id, event_title, event_text,
                interpretation, risks, opportunities, actions,
                alfa_view, confidence, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(insight_id) DO UPDATE SET
                interpretation = excluded.interpretation,
                risks = excluded.risks,
                opportunities = excluded.opportunities,
                actions = excluded.actions,
                alfa_view = excluded.alfa_view,
                confidence = excluded.confidence,
                updated_at = excluded.updated_at
        """, (
            insight_id, insight["client_id"], insight.get("event_id"),
            insight.get("event_title"), insight.get("event_text"),
            insight.get("interpretation"),
            json.dumps(insight.get("risks", []), ensure_ascii=False),
            json.dumps(insight.get("opportunities", []), ensure_ascii=False),
            json.dumps(insight.get("actions", []), ensure_ascii=False),
            insight.get("alfa_view"), float(insight.get("confidence", 0.0)),
            created_at, now
        ))
    return insight_id


def get_insight(insight_id: str) -> Optional[dict]:
    """Достаёт инсайт по ID."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM insights WHERE insight_id = ?", (insight_id,)).fetchone()
    return _row_to_insight(row) if row else None


def list_insights(client_id: str, limit: int = 20) -> list[dict]:
    """Последние инсайты клиента."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM insights WHERE client_id = ? ORDER BY created_at DESC LIMIT ?",
            (client_id, limit)
        ).fetchall()
    return [_row_to_insight(r) for r in rows]


def save_trace(insight_id: str, step: str, payload: dict) -> None:
    """Сохраняет шаг трассировки агента."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO traces (insight_id, step, payload, created_at) VALUES (?, ?, ?, ?)",
            (insight_id, step, json.dumps(payload, ensure_ascii=False), datetime.utcnow().isoformat())
        )


def get_traces(insight_id: str) -> list[dict]:
    """Все шаги трассировки."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM traces WHERE insight_id = ? ORDER BY trace_id ASC", (insight_id,)).fetchall()
    return [{"step": r["step"], "payload": json.loads(r["payload"]), "created_at": r["created_at"]} for r in rows]


def _row_to_insight(row: sqlite3.Row) -> dict:
    return {
        "insight_id": row["insight_id"],
        "client_id": row["client_id"],
        "event_id": row["event_id"],
        "event_title": row["event_title"],
        "event_text": row["event_text"],
        "interpretation": row["interpretation"],
        "risks": json.loads(row["risks"] or "[]"),
        "opportunities": json.loads(row["opportunities"] or "[]"),
        "actions": json.loads(row["actions"] or "[]"),
        "alfa_view": row["alfa_view"],
        "confidence": row["confidence"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }