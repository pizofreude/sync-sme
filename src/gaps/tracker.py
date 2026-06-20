"""Track candidate tasks that still need logging — SQLite-backed persistence."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass(slots=True)
class CandidateTask:
    message_id: int
    channel: str
    content: str
    author: str
    created_at: datetime


class GapTracker:
    """SQLite-backed tracker for messages that might be tasks but weren't logged.

    Tracks messages from monitored channels that don't match actionable keywords
    but could still represent tasks the user forgot to tag.
    """

    def __init__(self, db_path: str = "sync_sme.db"):
        self.db_path = db_path
        parent = Path(db_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS gap_candidates (
                    message_id INTEGER PRIMARY KEY,
                    channel TEXT NOT NULL,
                    content TEXT NOT NULL,
                    author TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved INTEGER NOT NULL DEFAULT 0
                )"""
            )

    def remember(
        self,
        message_id: int,
        content: str,
        channel: str = "",
        author: str = "",
        created_at: datetime | None = None,
    ) -> None:
        """Record a message as a potential task candidate."""
        ts = (created_at or datetime.now(UTC)).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO gap_candidates (message_id, channel, content, author, created_at) VALUES (?, ?, ?, ?, ?)",
                (message_id, channel, content, author, ts),
            )

    def resolve(self, message_id: int) -> None:
        """Mark a candidate as resolved (task was created for it)."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE gap_candidates SET resolved = 1 WHERE message_id = ?",
                (message_id,),
            )

    def overdue(self, older_than: timedelta) -> list[CandidateTask]:
        """Return unresolved candidates older than the given duration."""
        cutoff = (datetime.now(UTC) - older_than).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT message_id, channel, content, author, created_at FROM gap_candidates WHERE resolved = 0 AND created_at <= ?",
                (cutoff,),
            ).fetchall()
        return [
            CandidateTask(
                message_id=row[0],
                channel=row[1],
                content=row[2],
                author=row[3],
                created_at=datetime.fromisoformat(row[4]),
            )
            for row in rows
        ]

    def unresolved_count(self) -> int:
        """Return the number of unresolved candidates."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM gap_candidates WHERE resolved = 0"
            ).fetchone()
        return row[0] if row else 0

    def recent_candidates(self, limit: int = 10) -> list[CandidateTask]:
        """Return the most recent unresolved candidates."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT message_id, channel, content, author, created_at FROM gap_candidates WHERE resolved = 0 ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            CandidateTask(
                message_id=row[0],
                channel=row[1],
                content=row[2],
                author=row[3],
                created_at=datetime.fromisoformat(row[4]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
