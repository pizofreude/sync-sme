"""Tests for DailyBriefingGenerator."""

from pathlib import Path
from unittest.mock import MagicMock

from gaps.briefing import DailyBriefingGenerator


def _make_generator(tmp_path, briefing_response="# Briefing\nAll good."):
    """Create a DailyBriefingGenerator with a mock router and prompt file."""
    prompt_path = tmp_path / "daily_briefing.txt"
    prompt_path.write_text("Generate a morning briefing.", encoding="utf-8")
    router = MagicMock()
    router.complete.return_value = briefing_response
    return DailyBriefingGenerator(router=router, prompt_path=prompt_path)


def test_generate_calls_router_with_all_inputs(tmp_path):
    """generate() sends pending tasks, deadlines, and gaps to the LLM."""
    gen = _make_generator(tmp_path)

    result = gen.generate(
        pending_tasks="Task A, Task B",
        upcoming_deadlines="Task A due Friday",
        gaps_detected="2 unlogged candidates",
    )

    gen.router.complete.assert_called_once()
    call_args = gen.router.complete.call_args
    assert "Task A, Task B" in call_args.kwargs["user_prompt"]
    assert "Task A due Friday" in call_args.kwargs["user_prompt"]
    assert "2 unlogged candidates" in call_args.kwargs["user_prompt"]
    assert result == "# Briefing\nAll good."


def test_generate_uses_briefing_prompt(tmp_path):
    """generate() reads the daily_briefing.txt prompt as system prompt."""
    gen = _make_generator(tmp_path)

    gen.generate("tasks", "deadlines", "gaps")

    call_args = gen.router.complete.call_args
    assert call_args.kwargs["system_prompt"] == "Generate a morning briefing."


def test_write_to_obsidian_creates_briefing_file(tmp_path):
    """write_to_obsidian() writes the briefing to the vault with correct path."""
    gen = _make_generator(tmp_path)
    vault = tmp_path / "vault"
    obsidian = MagicMock()
    obsidian.write_markdown.return_value = vault / "Daily" / "2026-06-21-briefing.md"

    path = gen.write_to_obsidian("# Briefing content", obsidian)

    obsidian.write_markdown.assert_called_once()
    call_args = obsidian.write_markdown.call_args
    assert "Daily/" in call_args.args[0]
    assert "briefing.md" in call_args.args[0]
    assert "# Briefing content" in call_args.args[1]


def test_generate_and_write_returns_briefing_and_path(tmp_path):
    """generate_and_write() returns both the briefing text and the vault path."""
    gen = _make_generator(tmp_path, briefing_response="# Generated briefing")
    obsidian = MagicMock()
    obsidian.write_markdown.return_value = Path("/vault/Daily/briefing.md")

    briefing, path = gen.generate_and_write(
        pending_tasks="tasks",
        upcoming_deadlines="deadlines",
        gaps_detected="gaps",
        obsidian=obsidian,
    )

    assert briefing == "# Generated briefing"
    assert path == Path("/vault/Daily/briefing.md")
