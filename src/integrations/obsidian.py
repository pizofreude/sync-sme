"""Filesystem-based Obsidian vault writer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ObsidianWriter:
    vault_path: Path

    def write_markdown(self, relative_path: str, content: str) -> Path:
        target = self.vault_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def append_to_daily(self, daily_note: str, content: str) -> Path:
        target = self.vault_path / daily_note
        target.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if not target.exists() or target.read_text(encoding="utf-8").endswith("\n") else "\n"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(f"{prefix}{content}\n")
        return target
