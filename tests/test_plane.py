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
    )
    assert issue.identifier == "ISSUE-123"
