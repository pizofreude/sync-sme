"""Tests for MeetingPipeline — end-to-end meeting processing."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from llm.parser import ParsedTask
from meeting.pipeline import MeetingPipeline


def _make_pipeline():
    """Create a MeetingPipeline with mock components."""
    recorder = MagicMock()
    transcriber = MagicMock()
    summarizer = MagicMock()
    obsidian = MagicMock()
    plane = MagicMock()
    return MeetingPipeline(
        recorder=recorder,
        transcriber=transcriber,
        summarizer=summarizer,
        obsidian=obsidian,
        plane=plane,
    )


def test_process_recording_runs_full_pipeline(tmp_path):
    """process_recording should: fetch → transcribe → summarize → write."""
    pipeline = _make_pipeline()
    pipeline.recorder.fetch_audio.return_value = b"audio-bytes"
    pipeline.transcriber.transcribe.return_value = "Speaker 1: Hello everyone."
    pipeline.summarizer.summarize.return_value = "# Meeting\n\n## Summary\nHello."
    pipeline.obsidian.write_markdown.return_value = tmp_path / "notes.md"

    audio_path = tmp_path / "recording.flac"
    result = pipeline.process_recording("rec-123", audio_path, "Meetings/today.md")

    pipeline.recorder.fetch_audio.assert_called_once_with("rec-123")
    assert audio_path.read_bytes() == b"audio-bytes"
    pipeline.transcriber.transcribe.assert_called_once_with(audio_path)
    pipeline.summarizer.summarize.assert_called_once_with("Speaker 1: Hello everyone.")
    pipeline.obsidian.write_markdown.assert_called_once_with("Meetings/today.md", "# Meeting\n\n## Summary\nHello.")
    assert result == "# Meeting\n\n## Summary\nHello."


def test_extract_action_items_parses_json_array():
    """extract_action_items should parse LLM JSON response into ParsedTask list."""
    pipeline = _make_pipeline()
    router = MagicMock()
    router.complete.return_value = json.dumps([
        {"title": "Deploy to staging", "assignee": "Alice", "due_date": "2026-06-22", "details": "From meeting"},
        {"title": "Update docs", "assignee": None, "due_date": None, "details": None},
    ])

    tasks = pipeline.extract_action_items("# Meeting content", router)

    assert len(tasks) == 2
    assert tasks[0] == ParsedTask(title="Deploy to staging", assignee="Alice", due_date="2026-06-22", details="From meeting")
    assert tasks[1] == ParsedTask(title="Update docs")


def test_extract_action_items_handles_code_fenced_json():
    """extract_action_items should strip markdown code fences from LLM response."""
    pipeline = _make_pipeline()
    router = MagicMock()
    router.complete.return_value = '```json\n[{"title": "Fix bug"}]\n```'

    tasks = pipeline.extract_action_items("minutes", router)

    assert len(tasks) == 1
    assert tasks[0].title == "Fix bug"


def test_extract_action_items_returns_empty_on_invalid_json():
    """extract_action_items should return empty list for unparseable responses."""
    pipeline = _make_pipeline()
    router = MagicMock()
    router.complete.return_value = "I don't see any action items."

    tasks = pipeline.extract_action_items("minutes", router)

    assert tasks == []


def test_extract_action_items_skips_empty_titles():
    """extract_action_items should skip items with empty titles."""
    pipeline = _make_pipeline()
    router = MagicMock()
    router.complete.return_value = json.dumps([
        {"title": "Valid task"},
        {"title": ""},
        {"title": "  "},
    ])

    tasks = pipeline.extract_action_items("minutes", router)

    assert len(tasks) == 1
    assert tasks[0].title == "Valid task"


def test_create_action_items_calls_plane_for_each_task():
    """create_action_items should create a Plane issue for each task."""
    pipeline = _make_pipeline()
    pipeline.plane.create_issue.side_effect = [
        MagicMock(identifier="ISSUE-1"),
        MagicMock(identifier="ISSUE-2"),
    ]

    tasks = [
        ParsedTask(title="Task 1"),
        ParsedTask(title="Task 2"),
    ]
    issues = pipeline.create_action_items(tasks)

    assert len(issues) == 2
    assert pipeline.plane.create_issue.call_count == 2


def test_create_action_items_continues_on_failure():
    """create_action_items should continue even if one issue creation fails."""
    pipeline = _make_pipeline()
    pipeline.plane.create_issue.side_effect = [
        Exception("API error"),
        MagicMock(identifier="ISSUE-2"),
    ]

    tasks = [ParsedTask(title="Failing task"), ParsedTask(title="Working task")]
    issues = pipeline.create_action_items(tasks)

    assert len(issues) == 1
    assert issues[0].identifier == "ISSUE-2"


def test_process_and_extract_full_pipeline(tmp_path):
    """process_and_extract should run the full pipeline and create issues."""
    pipeline = _make_pipeline()
    pipeline.recorder.fetch_audio.return_value = b"audio"
    pipeline.transcriber.transcribe.return_value = "transcript"
    pipeline.summarizer.summarize.return_value = "# Minutes\n- Deploy to staging"
    pipeline.obsidian.write_markdown.return_value = tmp_path / "notes.md"
    pipeline.plane.create_issue.return_value = MagicMock(identifier="ISSUE-99")

    router = MagicMock()
    router.complete.return_value = json.dumps([{"title": "Deploy to staging"}])

    minutes, issues = pipeline.process_and_extract(
        "rec-1", tmp_path / "audio.flac", "Meetings/today.md", router
    )

    assert minutes == "# Minutes\n- Deploy to staging"
    assert len(issues) == 1
    assert issues[0].identifier == "ISSUE-99"
