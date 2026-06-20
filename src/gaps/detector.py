"""Detect overdue candidate tasks and format alerts."""

from __future__ import annotations

from datetime import timedelta

from gaps.tracker import CandidateTask, GapTracker


class GapDetector:
    """Checks for messages that might be tasks but weren't logged.

    Works with GapTracker to find unresolved candidates older than
    the configured detection window (default: 24 hours).
    """

    def __init__(self, tracker: GapTracker, detection_hours: int = 24):
        self.tracker = tracker
        self.detection_hours = detection_hours

    def detect(self) -> list[CandidateTask]:
        """Return overdue unresolved candidates."""
        return self.tracker.overdue(timedelta(hours=self.detection_hours))

    def format_alert(self, candidates: list[CandidateTask] | None = None) -> str | None:
        """Format gap candidates into a Discord-ready alert message.

        Returns None if no candidates are found.
        """
        if candidates is None:
            candidates = self.detect()
        if not candidates:
            return None

        lines = [
            f"⚠️ **{len(candidates)} message(s)** in #action-items might be tasks but haven't been logged:",
            "",
        ]
        for c in candidates[:5]:  # Cap at 5 to avoid message length limits
            snippet = c.content[:100] + ("..." if len(c.content) > 100 else "")
            author = c.author or "unknown"
            lines.append(f"• **{author}**: \"{snippet}\"")

        if len(candidates) > 5:
            lines.append(f"• ... and {len(candidates) - 5} more")

        lines.append("")
        lines.append("Use `todo:` or `need to:` prefix to log them as tasks.")
        return "\n".join(lines)

    def format_briefing_section(self, candidates: list[CandidateTask] | None = None) -> str:
        """Format gap candidates for inclusion in the daily briefing."""
        if candidates is None:
            candidates = self.detect()
        if not candidates:
            return "No unlogged task candidates detected."

        lines = [f"**{len(candidates)} unlogged task candidate(s):**"]
        for c in candidates[:10]:
            snippet = c.content[:80] + ("..." if len(c.content) > 80 else "")
            lines.append(f"- {snippet}")
        return "\n".join(lines)
