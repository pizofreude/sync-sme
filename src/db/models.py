"""SQLite models for local Sync-SME state."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SQLiteStateStore:
    path: str

    def __post_init__(self) -> None:
        parent = Path(self.path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS processed_messages (message_id INTEGER PRIMARY KEY)"
            )

    def is_processed(self, message_id: int) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM processed_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()
        return row is not None

    def mark_processed(self, message_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)",
                (message_id,),
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)
