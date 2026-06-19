"""Meeting transcript summarization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from llm.prompts import resolve_prompt

PROMPT_PATH = resolve_prompt("meeting_minutes.txt")


class Router(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


class MeetingSummarizer:
    def __init__(self, router: Router, prompt_path: Path = PROMPT_PATH):
        self.router = router
        self.prompt_path = prompt_path

    def summarize(self, transcript: str) -> str:
        return self.router.complete(
            system_prompt=self.prompt_path.read_text(encoding="utf-8"),
            user_prompt=transcript,
        )
