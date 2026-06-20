"""Daily briefing generation and Obsidian write."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from llm.prompts import resolve_prompt

logger = logging.getLogger(__name__)

PROMPT_PATH = resolve_prompt("daily_briefing.txt")


class Router(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


class ObsidianWriter(Protocol):
    def write_markdown(self, relative_path: str, content: str) -> Path:
        ...

    def append_to_daily(self, daily_note: str, content: str) -> Path:
        ...


class DailyBriefingGenerator:
    """Generates a morning briefing from pending tasks, deadlines, and gaps.

    Uses the LLM to produce a concise markdown briefing, then writes it
    to the Obsidian vault as a daily note section.
    """

    def __init__(self, router: Router, prompt_path: Path = PROMPT_PATH):
        self.router = router
        self.prompt_path = prompt_path

    def generate(self, pending_tasks: str, upcoming_deadlines: str, gaps_detected: str) -> str:
        """Generate a briefing from the three data inputs.

        Args:
            pending_tasks: Summary of tasks pending in Plane.
            upcoming_deadlines: Summary of deadlines approaching.
            gaps_detected: Summary of unlogged task candidates.

        Returns:
            Markdown-formatted briefing text.
        """
        prompt = (
            f"Pending tasks:\n{pending_tasks}\n\n"
            f"Upcoming deadlines:\n{upcoming_deadlines}\n\n"
            f"Gaps detected:\n{gaps_detected}"
        )
        return self.router.complete(
            system_prompt=self.prompt_path.read_text(encoding="utf-8"),
            user_prompt=prompt,
        )

    def write_to_obsidian(self, briefing: str, obsidian: ObsidianWriter, vault_subdir: str = "Daily") -> Path:
        """Write the briefing to the Obsidian vault.

        Args:
            briefing: The generated briefing markdown.
            obsidian: An ObsidianWriter instance.
            vault_subdir: Subdirectory in the vault for daily notes.

        Returns:
            Path to the written briefing file.
        """
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        relative_path = f"{vault_subdir}/{today}-briefing.md"
        header = f"# Daily Briefing — {today}\n\n"
        return obsidian.write_markdown(relative_path, header + briefing)

    def generate_and_write(
        self,
        pending_tasks: str,
        upcoming_deadlines: str,
        gaps_detected: str,
        obsidian: ObsidianWriter,
    ) -> tuple[str, Path]:
        """Generate a briefing and write it to Obsidian.

        Returns:
            Tuple of (briefing text, path in vault).
        """
        briefing = self.generate(pending_tasks, upcoming_deadlines, gaps_detected)
        path = self.write_to_obsidian(briefing, obsidian)
        logger.info("Daily briefing written to %s", path)
        return briefing, path
