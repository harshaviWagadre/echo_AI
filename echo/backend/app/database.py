import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = Path(os.getenv("ECHO_DATABASE", DATA_DIR / "echo.db"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_db() -> None:
    with connection() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            CREATE TABLE IF NOT EXISTS image_generations (
                id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                provider TEXT NOT NULL,
                image_url TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS video_jobs (
                id TEXT PRIMARY KEY,
                clip_name TEXT NOT NULL,
                music_name TEXT,
                status TEXT NOT NULL,
                output_path TEXT,
                created_at TEXT NOT NULL
            );
            """)


def insert(table: str, values: dict[str, Any]) -> None:
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    with connection() as db:
        db.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )


def fetch_one(table: str, record_id: str) -> dict[str, Any] | None:
    with connection() as db:
        row = db.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
    return dict(row) if row else None


def fetch_all(table: str, limit: int = 50) -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute(
            f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]
