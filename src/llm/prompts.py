"""Robust prompt file resolution for development and installed environments."""

from __future__ import annotations

from pathlib import Path


def resolve_prompt(filename: str) -> Path:
    """Return the absolute path to a prompt file under ``prompts/``.

    Resolution order:
    1. Walk up from this file to the repo root and look for ``prompts/<filename>``
       (works when running from source / ``PYTHONPATH=src``).
    2. Fall back to ``Path.cwd() / "prompts" / filename``
       (works when the bot is started from the repo root).

    Raises ``FileNotFoundError`` if neither location exists.
    """
    # Strategy 1: repo-root relative to this source file
    candidate = Path(__file__).resolve()
    for _ in range(5):  # cap ascent to avoid infinite walk
        candidate = candidate.parent
        prompt = candidate / "prompts" / filename
        if prompt.is_file():
            return prompt

    # Strategy 2: cwd-relative (e.g. installed but started from repo root)
    cwd_prompt = Path.cwd() / "prompts" / filename
    if cwd_prompt.is_file():
        return cwd_prompt

    raise FileNotFoundError(
        f"Cannot locate prompts/{filename}. "
        "Run from the repo root or ensure the prompts/ directory is accessible."
    )
