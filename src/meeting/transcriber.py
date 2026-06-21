"""Speechmatics transcription wrapper via Pipecat."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

SPEECHMATICS_BATCH_URL = "https://asr.api.speechmatics.com/v2/jobs"
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 120  # 10 minutes max


@dataclass(slots=True)
class SpeechmaticsTranscriber:
    """Transcribe audio files using Speechmatics batch API.

    Requires ``pipecat-ai[speechmatics]`` and a ``SPEECHMATICS_API_KEY``.
    """

    api_key: str
    language: str = "en"
    operating_point: str = "enhanced"

    def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file and return the full transcript text.

        Args:
            audio_path: Path to the audio file (FLAC, OGG, WAV, MP3, etc.).

        Returns:
            The transcribed text, stripped of whitespace.

        Raises:
            RuntimeError: If the API key is missing or the transcription fails.
        """
        if not self.api_key:
            raise RuntimeError(
                "SPEECHMATICS_API_KEY must be set to transcribe meetings"
            )

        headers = {"Authorization": f"Bearer {self.api_key}"}
        audio_bytes = audio_path.read_bytes()

        # --- Submit batch transcription job ---
        config = {
            "type": "transcription",
            "transcription_config": {
                "language": self.language,
                "operating_point": self.operating_point,
            },
        }
        files = {
            "config": (None, json.dumps(config), "application/json"),
            "data_file": (audio_path.name, audio_bytes),
        }
        logger.info("Submitting audio to Speechmatics batch API: %s", audio_path.name)
        resp = requests.post(SPEECHMATICS_BATCH_URL, headers=headers, files=files)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Speechmatics job creation failed ({resp.status_code}): {resp.text}"
            )

        job_id = resp.json()["id"]
        logger.info("Speechmatics job created: %s", job_id)

        # --- Poll until complete ---
        for _ in range(MAX_POLL_ATTEMPTS):
            time.sleep(POLL_INTERVAL_SECONDS)
            status_resp = requests.get(
                f"{SPEECHMATICS_BATCH_URL}/{job_id}", headers=headers
            )
            if status_resp.status_code != 200:
                raise RuntimeError(
                    f"Speechmatics status check failed ({status_resp.status_code}): {status_resp.text}"
                )

            status = status_resp.json().get("job", {}).get("status")
            if status == "done":
                break
            if status == "rejected":
                raise RuntimeError(
                    f"Speechmatics job {job_id} rejected: {status_resp.text}"
                )
        else:
            raise RuntimeError(
                f"Speechmatics job {job_id} timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s"
            )

        # --- Fetch transcript ---
        transcript_resp = requests.get(
            f"{SPEECHMATICS_BATCH_URL}/{job_id}/transcript",
            headers={**headers, "Accept": "application/json"},
        )
        if transcript_resp.status_code != 200:
            raise RuntimeError(
                f"Speechmatics transcript fetch failed ({transcript_resp.status_code}): {transcript_resp.text}"
            )

        data = transcript_resp.json()
        # Batch API returns {"results": [{"alternatives": [{"content": "..."}]}]}
        results = data.get("results", [])
        words = []
        for result in results:
            alternatives = result.get("alternatives", [])
            if alternatives:
                content = alternatives[0].get("content", "").strip()
                if content:
                    words.append(content)
        return " ".join(words)
