"""Tests for Plane.so REST API client."""

import json
from unittest.mock import patch, MagicMock

from integrations.plane_api import PlaneAPIClient
from llm.parser import ParsedTask


def test_plane_api_client_sends_correct_payload():
    """Verify the API client sends the correct JSON payload."""
    client = PlaneAPIClient(
        workspace_slug="my-workspace",
        api_token="test-token",
        project_id="proj-123",
    )

    with patch("integrations.plane_api.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "issue-abc"}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        issue = client.create_issue(ParsedTask(
            title="Fix login bug",
            assignee="user-1",
            due_date="2026-06-22",
            details="Auth flow broken",
        ))

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["name"] == "Fix login bug"
        assert body["target_date"] == "2026-06-22"
        assert body["description_html"] == "<p>Auth flow broken</p>"
        assert body["assignees"] == ["user-1"]
        assert req.headers.get("X-api-key") == "test-token"
        assert issue.identifier == "issue-abc"


def test_plane_api_client_omits_optional_fields():
    """Verify optional fields are omitted from the payload when not provided."""
    client = PlaneAPIClient(workspace_slug="ws", api_token="tok", project_id="p1")

    with patch("integrations.plane_api.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "id-1"}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client.create_issue(ParsedTask(title="Simple task"))

        body = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        assert "description_html" not in body
        assert "target_date" not in body
        assert "assignees" not in body


def test_plane_api_client_constructs_correct_url():
    """Verify the API URL is constructed correctly."""
    client = PlaneAPIClient(workspace_slug="freuden-systems", api_token="tok", project_id="proj-1")

    with patch("integrations.plane_api.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "id"}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client.create_issue(ParsedTask(title="Test"))

        req = mock_urlopen.call_args[0][0]
        assert "freuden-systems" in req.full_url
        assert "proj-1" in req.full_url
