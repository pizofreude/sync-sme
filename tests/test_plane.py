import logging

import pytest
from unittest.mock import patch

from integrations.plane import PlaneCLI
from llm.parser import ParsedTask


@patch("integrations.plane.subprocess.run")
def test_plane_cli_builds_expected_command(run_mock):
    run_mock.return_value.stdout = "ISSUE-123\n"
    client = PlaneCLI(workspace_slug="workspace", assignee_map={"123": "plane-user"})

    issue = client.create_issue(
        ParsedTask(
            title="Follow up with design",
            assignee="<@123>",
            due_date="2026-06-20",
            details="From Discord thread",
        )
    )

    run_mock.assert_called_once_with(
        [
            "plane",
            "create-issue",
            "--workspace",
            "workspace",
            "--title",
            "Follow up with design",
            "--assignee",
            "plane-user",
            "--due-date",
            "2026-06-20",
            "--description",
            "From Discord thread",
        ],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    assert issue.identifier == "ISSUE-123"


@pytest.mark.parametrize(
    "assignee, expect_assignee_flag",
    [
        (None, False),
        ("<@999>", True),  # unmapped mention — passed through as-is
    ],
)
@patch("integrations.plane.subprocess.run")
def test_plane_cli_assignee_optional_and_unmapped(run_mock, assignee, expect_assignee_flag):
    run_mock.return_value.stdout = "ISSUE-456\n"
    client = PlaneCLI(workspace_slug="workspace", assignee_map={"123": "plane-user"})

    issue = client.create_issue(
        ParsedTask(
            title="Task with optional assignee",
            assignee=assignee,
            due_date="2026-06-21",
            details="Check assignee handling",
        )
    )

    run_mock.assert_called_once()
    cmd = run_mock.call_args[0][0]
    assert ("--assignee" in cmd) is expect_assignee_flag
    assert issue.identifier == "ISSUE-456"


@pytest.mark.parametrize(
    "due_date, details, expect_due_flag, expect_details_flag",
    [
        ("2026-06-22", "Has all fields", True, True),
        (None, "No due date", False, True),
        ("2026-06-23", None, True, False),
        (None, None, False, False),
    ],
)
@patch("integrations.plane.subprocess.run")
def test_plane_cli_omits_flags_for_missing_optional_fields(
    run_mock, due_date, details, expect_due_flag, expect_details_flag
):
    run_mock.return_value.stdout = "ISSUE-789\n"
    client = PlaneCLI(workspace_slug="workspace", assignee_map={})

    issue = client.create_issue(
        ParsedTask(
            title="Optional fields coverage",
            assignee=None,
            due_date=due_date,
            details=details,
        )
    )

    run_mock.assert_called_once()
    cmd = run_mock.call_args[0][0]
    assert ("--due-date" in cmd) is expect_due_flag
    assert ("--description" in cmd) is expect_details_flag
    assert issue.identifier == "ISSUE-789"


@pytest.mark.parametrize(
    "stdout_value",
    [
        "",
        "   ",
        "\n",
        "   \n",
    ],
)
@patch("integrations.plane.subprocess.run")
def test_plane_cli_falls_back_to_title_when_stdout_empty(run_mock, stdout_value):
    run_mock.return_value.stdout = stdout_value
    client = PlaneCLI(workspace_slug="workspace", assignee_map={})

    task = ParsedTask(
        title="Fallback title task",
        assignee=None,
        due_date=None,
        details=None,
    )

    issue = client.create_issue(task)

    run_mock.assert_called_once()
    assert issue.identifier == task.title


# --- Assignee mapping verification (Day 1) ---


def test_plane_cli_resolves_mapped_discord_mention():
    """Verify a mapped Discord mention resolves to the Plane member."""
    client = PlaneCLI(
        workspace_slug="ws",
        assignee_map={"111": "alice-plane", "222": "bob-plane"},
    )
    assert client._resolve_assignee("<@111>") == "alice-plane"
    assert client._resolve_assignee("<@222>") == "bob-plane"


def test_plane_cli_resolves_nick_format_mention():
    """Verify nick-format mentions (<@!111>) also resolve correctly."""
    client = PlaneCLI(workspace_slug="ws", assignee_map={"111": "alice-plane"})
    assert client._resolve_assignee("<@!111>") == "alice-plane"


def test_plane_cli_passes_through_unmapped_mention():
    """Verify unmapped mentions are passed through as-is."""
    client = PlaneCLI(workspace_slug="ws", assignee_map={"111": "alice-plane"})
    assert client._resolve_assignee("<@999>") == "<@999>"


def test_plane_cli_passes_through_plain_name():
    """Verify plain text assignees pass through unchanged."""
    client = PlaneCLI(workspace_slug="ws", assignee_map={"111": "alice-plane"})
    assert client._resolve_assignee("John Doe") == "John Doe"


def test_plane_cli_handles_none_assignee():
    """Verify None assignee returns None."""
    client = PlaneCLI(workspace_slug="ws", assignee_map={})
    assert client._resolve_assignee(None) is None


def test_plane_cli_handles_empty_assignee_map():
    """Verify empty assignee map passes through all mentions."""
    client = PlaneCLI(workspace_slug="ws", assignee_map={})
    assert client._resolve_assignee("<@123>") == "<@123>"


# --- Dry-run mode (Day 1 e2e fallback) ---


def test_plane_cli_dry_run_does_not_call_subprocess():
    """Verify dry-run mode logs instead of calling the CLI."""
    client = PlaneCLI(workspace_slug="ws", assignee_map={}, dry_run=True)

    issue = client.create_issue(ParsedTask(
        title="Dry run task",
        assignee="Alice",
        due_date="2026-06-22",
        details="Should not call plane CLI",
    ))

    assert issue.identifier == "dry-run:Dry run task"
    assert "DRY-RUN" in issue.output
    assert "Dry run task" in issue.output


def test_plane_cli_dry_run_logs_assignee_and_details(caplog):
    """Verify dry-run output includes all task fields."""
    client = PlaneCLI(workspace_slug="ws", assignee_map={}, dry_run=True)

    with caplog.at_level(logging.WARNING):
        client.create_issue(ParsedTask(
            title="Task with details",
            assignee="Bob",
            due_date="2026-06-23",
            details="Important context",
        ))

    assert "Task with details" in caplog.text
    assert "Bob" in caplog.text
    assert "2026-06-23" in caplog.text
    assert "Important context" in caplog.text
