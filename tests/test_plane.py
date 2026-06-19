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
