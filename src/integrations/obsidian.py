"""Filesystem-based Obsidian vault writer with optional notesmd-cli support."""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ObsidianWriter:
    """Write markdown to an Obsidian vault.

    Prefers ``notesmd-cli`` (headless write operations) when available,
    falls back to direct filesystem writes.
    """

    vault_path: Path
    _has_notesmd: bool = False

    def __post_init__(self) -> None:
        self._has_notesmd = shutil.which("notesmd") is not None
        if self._has_notesmd:
            logger.info("notesmd-cli detected — using headless vault writes")
        else:
            logger.info("notesmd-cli not found — using direct filesystem writes")

    def write_markdown(self, relative_path: str, content: str) -> Path:
        """Write a markdown file to the vault.

        Args:
            relative_path: Path relative to vault root (e.g. "Meetings/2026-06-21.md").
            content: Full markdown content to write.

        Returns:
            Absolute path to the written file.
        """
        if self._has_notesmd:
            return self._write_via_cli(relative_path, content)
        return self._write_via_filesystem(relative_path, content)

    def append_to_daily(self, daily_note: str, content: str) -> Path:
        """Append content to a daily note in the vault.

        Args:
            daily_note: Relative path to the daily note (e.g. "Daily/2026-06-21.md").
            content: Content to append.

        Returns:
            Absolute path to the daily note.
        """
        target = self.vault_path / daily_note
        target.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if not target.exists() or target.read_text(encoding="utf-8").endswith("\n") else "\n"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(f"{prefix}{content}\n")
        return target

    def _write_via_cli(self, relative_path: str, content: str) -> Path:
        """Write using notesmd-cli (headless, no Obsidian app required)."""
        target = self.vault_path / relative_path
        try:
            # notesmd write <vault> <path> --content <content>
            subprocess.run(
                ["notesmd", "write", str(self.vault_path), relative_path, "--content", content],
                check=True,
                capture_output=True,
                text=True,
                shell=False,
            )
        except subprocess.CalledProcessError as exc:
            logger.warning("notesmd-cli write failed (%s), falling back to filesystem", exc.stderr.strip())
            return self._write_via_filesystem(relative_path, content)
        return target

    def _write_via_filesystem(self, relative_path: str, content: str) -> Path:
        """Write directly to the vault filesystem."""
        target = self.vault_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target
