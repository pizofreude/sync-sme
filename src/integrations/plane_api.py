"""Plane.so REST API client — alternative to the CLI wrapper.

Uses the Plane.so REST API when the ``plane`` CLI binary is not available.
Requires a Plane API token (``PLANE_API_TOKEN`` env var).

API docs: https://developers.plane.so/
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request

from llm.parser import ParsedTask
from integrations.plane import CreatedIssue


@dataclass(slots=True)
class PlaneAPIClient:
    """Create Plane issues via the REST API instead of the CLI."""

    workspace_slug: str
    api_token: str
    project_id: str = ""
    base_url: str = "https://api.plane.so"

    def create_issue(self, task: ParsedTask) -> CreatedIssue:
        """POST a new issue to Plane.so via the REST API."""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/issues/"

        payload: dict[str, object] = {"name": task.title}
        if task.details:
            payload["description_html"] = f"<p>{task.details}</p>"
        if task.due_date:
            payload["target_date"] = task.due_date
        if task.assignee:
            # Plane API expects member IDs, not display names.
            # Assignee mapping must be handled upstream or via a lookup.
            payload["assignees"] = [task.assignee]

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            headers={
                "X-Api-Key": self.api_token,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=30) as response:  # nosec B310 - Plane API endpoint
            result = json.loads(response.read().decode("utf-8"))

        issue_id = result.get("id", task.title)
        return CreatedIssue(identifier=str(issue_id), output=json.dumps(result))
