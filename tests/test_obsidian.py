"""Tests for ObsidianWriter — filesystem-based vault writer."""

from pathlib import Path

from integrations.obsidian import ObsidianWriter


def test_write_markdown_creates_file_and_dirs(tmp_path):
    """write_markdown creates intermediate directories and writes content."""
    vault = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=vault)

    result = writer.write_markdown("Meetings/2026-06-21.md", "# Meeting Notes\n\nHello world")

    assert result == vault / "Meetings" / "2026-06-21.md"
    assert result.exists()
    assert result.read_text(encoding="utf-8") == "# Meeting Notes\n\nHello world"


def test_write_markdown_overwrites_existing_file(tmp_path):
    """write_markdown replaces existing file content."""
    vault = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=vault)

    writer.write_markdown("notes.md", "version 1")
    writer.write_markdown("notes.md", "version 2")

    content = (vault / "notes.md").read_text(encoding="utf-8")
    assert content == "version 2"


def test_append_to_daily_creates_new_file(tmp_path):
    """append_to_daily creates the file if it doesn't exist."""
    vault = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=vault)

    result = writer.append_to_daily("Daily/2026-06-21.md", "## Morning\n- Task 1")

    assert result.exists()
    assert result.read_text(encoding="utf-8") == "## Morning\n- Task 1\n"


def test_append_to_daily_appends_to_existing_file(tmp_path):
    """append_to_daily adds content after existing content."""
    vault = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=vault)

    writer.append_to_daily("Daily/2026-06-21.md", "## Morning")
    writer.append_to_daily("Daily/2026-06-21.md", "## Afternoon")

    content = (vault / "Daily" / "2026-06-21.md").read_text(encoding="utf-8")
    assert content == "## Morning\n## Afternoon\n"


def test_append_to_daily_handles_missing_trailing_newline(tmp_path):
    """append_to_daily adds a newline separator if existing content lacks one."""
    vault = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=vault)
    daily = vault / "Daily" / "2026-06-21.md"
    daily.parent.mkdir(parents=True)
    daily.write_text("existing content", encoding="utf-8")  # no trailing newline

    writer.append_to_daily("Daily/2026-06-21.md", "new section")

    content = daily.read_text(encoding="utf-8")
    assert content == "existing content\nnew section\n"


def test_write_markdown_deeply_nested_path(tmp_path):
    """write_markdown handles deeply nested paths."""
    vault = tmp_path / "vault"
    writer = ObsidianWriter(vault_path=vault)

    result = writer.write_markdown("a/b/c/d/deep.md", "deep content")

    assert result.exists()
    assert result.read_text(encoding="utf-8") == "deep content"
