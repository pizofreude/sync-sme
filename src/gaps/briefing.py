"""Daily briefing generation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from llm.prompts import resolve_prompt

PROMPT_PATH = resolve_prompt("daily_briefing.txt")


class Router(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


class DailyBriefingGenerator:
    def __init__(self, router: Router, prompt_path: Path = PROMPT_PATH):
        self.router = router
        self.prompt_path = prompt_path

    def generate(self, pending_tasks: str, upcoming_deadlines: str, gaps_detected: str) -> str:
        prompt = (
            f"Pending tasks:\n{pending_tasks}\n\n"
            f"Upcoming deadlines:\n{upcoming_deadlines}\n\n"
            f"Gaps detected:\n{gaps_detected}"
        )
        return self.router.complete(
            system_prompt=self.prompt_path.read_text(encoding="utf-8"),
            user_prompt=prompt,
        )
