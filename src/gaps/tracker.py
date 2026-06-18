"""Track candidate tasks that still need logging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(slots=True)
class CandidateTask:
    message_id: int
    content: str
    created_at: datetime


class GapTracker:
    def __init__(self):
        self._candidates: dict[int, CandidateTask] = {}

    def remember(self, message_id: int, content: str, created_at: datetime | None = None) -> None:
        self._candidates[message_id] = CandidateTask(
            message_id=message_id,
            content=content,
            created_at=created_at or datetime.now(UTC),
        )

    def overdue(self, older_than: timedelta) -> list[CandidateTask]:
        cutoff = datetime.now(UTC) - older_than
        return [candidate for candidate in self._candidates.values() if candidate.created_at <= cutoff]
