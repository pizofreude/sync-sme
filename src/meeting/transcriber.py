"""Whisper transcription wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class WhisperTranscriber:
    model_name: str = "base"

    def transcribe(self, audio_path: Path) -> str:
        try:
            import whisper
        except ImportError as exc:  # pragma: no cover - depends on optional runtime dependency
            raise RuntimeError("openai-whisper must be installed to transcribe meetings") from exc

        model = whisper.load_model(self.model_name)
        result = model.transcribe(str(audio_path))
        return str(result.get("text", "")).strip()
