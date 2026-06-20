"""Plane.so Prime CLI wrapper with graceful dry-run fallback."""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass

from llm.parser import ParsedTask

logger = logging.getLogger(__name__)

MENTION_PATTERN = re.compile(r"^<@!?(\d+)>$")


@dataclass(slots=True)
class CreatedIssue:
    identifier: str
    output: str


@dataclass(slots=True)
class PlaneCLI:
    workspace_slug: str
    assignee_map: dict[str, str] | None = None
    executable: str = "plane"
    dry_run: bool = False

    def create_issue(self, task: ParsedTask) -> CreatedIssue:
        assignee = self._resolve_assignee(task.assignee)

        if self.dry_run:
            return self._dry_run_create(task, assignee)

        command = [
            self.executable,
            "create-issue",
            "--workspace",
            self.workspace_slug,
            "--title",
            task.title,
        ]
        if assignee:
            command.extend(["--assignee", assignee])
        if task.due_date:
            command.extend(["--due-date", task.due_date])
        if task.details:
            command.extend(["--description", task.details])

        # Passing a list (not a shell string) — subprocess.run does NOT invoke a shell,
        # so this is safe from command injection even with user-derived task fields.
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
        issue_id = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else task.title
        return CreatedIssue(identifier=issue_id, output=completed.stdout)

    def _dry_run_create(self, task: ParsedTask, assignee: str | None) -> CreatedIssue:
        """Log the issue that would be created without calling the CLI."""
        parts = [f"[DRY-RUN] Would create Plane issue: \"{task.title}\""]
        if assignee:
            parts.append(f"  assignee: {assignee}")
        if task.due_date:
            parts.append(f"  due_date: {task.due_date}")
        if task.details:
            parts.append(f"  details: {task.details}")
        logger.warning("\n".join(parts))
        return CreatedIssue(identifier=f"dry-run:{task.title}", output="\n".join(parts))

    def _resolve_assignee(self, assignee: str | None) -> str | None:
        if not assignee:
            return None
        match = MENTION_PATTERN.match(assignee)
        if not match:
            return assignee
        mapping = self.assignee_map or {}
        return mapping.get(match.group(1), assignee)
