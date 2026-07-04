import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings


def connect() -> sqlite3.Connection:
    db_path = Path(get_settings().db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seasons (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            seed INTEGER NOT NULL,
            config_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_season(season_id: str, seed: int, config: dict[str, Any], payload: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO seasons VALUES (?, ?, ?, ?, ?)",
            (season_id, datetime.now(timezone.utc).isoformat(), seed, json.dumps(config), json.dumps(payload)),
        )
        conn.commit()


def list_seasons(limit: int = 12) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, seed, config_json FROM seasons ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"id": row["id"], "created_at": row["created_at"], "seed": row["seed"], "config": json.loads(row["config_json"])}
        for row in rows
    ]


def get_season(season_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT payload_json FROM seasons WHERE id = ?", (season_id,)).fetchone()
    return json.loads(row["payload_json"]) if row else None
