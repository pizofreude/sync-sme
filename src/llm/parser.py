"""Parse Discord messages into structured task objects."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from llm.prompts import resolve_prompt

PROMPT_PATH = resolve_prompt("parse_task.txt")


@dataclass(slots=True)
class ParsedTask:
    title: str
    assignee: str | None = None
    due_date: str | None = None
    details: str | None = None


class Router(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


class TaskParser:
    def __init__(self, router: Router, prompt_path: Path = PROMPT_PATH):
        self.router = router
        self.prompt_path = prompt_path

    def parse_message(self, message: str) -> ParsedTask | None:
        raw_response = self.router.complete(
            system_prompt=self.prompt_path.read_text(encoding="utf-8"),
            user_prompt=message,
        )
        return self.parse_response(raw_response)

    @staticmethod
    def parse_response(raw_response: str) -> ParsedTask | None:
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError:
            # LLMs often wrap JSON in markdown code fences — strip them
            import re
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_response.strip(), flags=re.MULTILINE).strip()
            try:
                payload = json.loads(cleaned)
            except json.JSONDecodeError:
                return None

        title = str(payload.get("title", "")).strip()
        if not title:
            return None

        assignee = TaskParser._optional_text(payload.get("assignee"))
        due_date = TaskParser._optional_text(payload.get("due_date"))
        details = TaskParser._optional_text(payload.get("details"))
        return ParsedTask(title=title, assignee=assignee, due_date=due_date, details=details)

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
