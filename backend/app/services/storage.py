import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel


DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "foodverse.sqlite3"
SESSION_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def require_session(value: str | None) -> str:
    if not value or not SESSION_PATTERN.fullmatch(value):
        raise HTTPException(status_code=400, detail="A valid browser session is required for history.")
    return value


def connect() -> sqlite3.Connection:
    path = Path(os.getenv("FOODVERSE_DB_PATH", str(DEFAULT_DB)))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS reports_session_time ON reports(session_id, id DESC)")
    return connection


def save_report(session: str | None, kind: str, title: str, summary: str, value: BaseModel) -> None:
    if not session:
        return
    require_session(session)
    with closing(connect()) as db:
        db.execute("INSERT INTO reports(session_id, kind, title, summary, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                   (session, kind, title[:120], summary[:240], value.model_dump_json(), datetime.now(timezone.utc).isoformat()))
        db.commit()


def list_reports(session: str) -> list[dict]:
    session = require_session(session)
    with closing(connect()) as db:
        rows = db.execute("SELECT id, kind, title, summary, created_at FROM reports WHERE session_id = ? ORDER BY id DESC LIMIT 30", (session,)).fetchall()
    return [dict(row) for row in rows]


def clear_reports(session: str) -> int:
    session = require_session(session)
    with closing(connect()) as db:
        cursor = db.execute("DELETE FROM reports WHERE session_id = ?", (session,))
        db.commit()
        return cursor.rowcount
