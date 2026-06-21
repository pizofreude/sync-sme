"""Tests for SpeechmaticsTranscriber."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meeting.transcriber import SpeechmaticsTranscriber


def _make_transcriber(api_key: str = "test-key") -> SpeechmaticsTranscriber:
    return SpeechmaticsTranscriber(api_key=api_key)


# --- Submit response helpers ---


def _submit_response(job_id: str = "job-123") -> MagicMock:
    resp = MagicMock()
    resp.status_code = 201
    resp.json.return_value = {"id": job_id}
    return resp


def _status_response(status: str = "done") -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"job": {"status": status}}
    return resp


def _transcript_response(words: list[str] | None = None) -> MagicMock:
    if words is None:
        words = ["Hello", "world", "this", "is", "a", "test"]
    results = [{"alternatives": [{"content": w}]} for w in words]
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"results": results}
    return resp


# --- Tests ---


def test_transcriber_calls_speechmatics_api(tmp_path):
    """Verify transcriber submits audio to Speechmatics and returns transcript."""
    audio = tmp_path / "meeting.flac"
    audio.write_bytes(b"fake-audio-data")

    transcriber = _make_transcriber()

    with patch("meeting.transcriber.requests") as mock_requests:
        mock_requests.post.return_value = _submit_response("job-1")
        mock_requests.get.side_effect = [
            _status_response("done"),
            _transcript_response(["Hello", "world"]),
        ]
        result = transcriber.transcribe(audio)

    assert result == "Hello world"
    mock_requests.post.assert_called_once()
    assert mock_requests.get.call_count == 2  # status poll + transcript fetch


def test_transcriber_strips_whitespace(tmp_path):
    """Verify transcriber strips leading/trailing whitespace from transcript."""
    audio = tmp_path / "audio.flac"
    audio.write_bytes(b"fake")

    transcriber = _make_transcriber()

    with patch("meeting.transcriber.requests") as mock_requests:
        mock_requests.post.return_value = _submit_response()
        mock_requests.get.side_effect = [
            _status_response("done"),
            _transcript_response(["  padded  ", "  text  "]),
        ]
        result = transcriber.transcribe(audio)

    assert result == "padded text"


def test_transcriber_handles_empty_transcript(tmp_path):
    """Verify transcriber handles empty results gracefully."""
    audio = tmp_path / "silence.flac"
    audio.write_bytes(b"fake")

    transcriber = _make_transcriber()

    with patch("meeting.transcriber.requests") as mock_requests:
        mock_requests.post.return_value = _submit_response()
        mock_requests.get.side_effect = [
            _status_response("done"),
            _transcript_response([]),
        ]
        result = transcriber.transcribe(audio)

    assert result == ""


def test_transcriber_handles_no_alternatives(tmp_path):
    """Verify transcriber handles results with no alternatives."""
    audio = tmp_path / "audio.flac"
    audio.write_bytes(b"fake")

    transcriber = _make_transcriber()

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"results": [{"type": "punctuation"}]}

    with patch("meeting.transcriber.requests") as mock_requests:
        mock_requests.post.return_value = _submit_response()
        mock_requests.get.side_effect = [_status_response("done"), resp]
        result = transcriber.transcribe(audio)

    assert result == ""


def test_transcriber_raises_on_missing_api_key():
    """Verify transcriber raises RuntimeError when API key is empty."""
    transcriber = SpeechmaticsTranscriber(api_key="")

    with pytest.raises(RuntimeError, match="SPEECHMATICS_API_KEY"):
        transcriber.transcribe(Path("audio.flac"))


def test_transcriber_raises_on_submit_failure(tmp_path):
    """Verify transcriber raises RuntimeError on API submission error."""
    audio = tmp_path / "audio.flac"
    audio.write_bytes(b"fake")

    transcriber = _make_transcriber()

    resp = MagicMock()
    resp.status_code = 401
    resp.text = "Unauthorized"

    with patch("meeting.transcriber.requests") as mock_requests:
        mock_requests.post.return_value = resp
        with pytest.raises(RuntimeError, match="job creation failed"):
            transcriber.transcribe(audio)


def test_transcriber_raises_on_rejected_job(tmp_path):
    """Verify transcriber raises RuntimeError when job is rejected."""
    audio = tmp_path / "audio.flac"
    audio.write_bytes(b"fake")

    transcriber = _make_transcriber()

    with patch("meeting.transcriber.requests") as mock_requests:
        mock_requests.post.return_value = _submit_response()
        mock_requests.get.return_value = _status_response("rejected")
        with pytest.raises(RuntimeError, match="rejected"):
            transcriber.transcribe(audio)


def test_transcriber_uses_configured_language(tmp_path):
    """Verify transcriber passes language and operating_point to the API."""
    audio = tmp_path / "audio.flac"
    audio.write_bytes(b"fake")

    transcriber = SpeechmaticsTranscriber(
        api_key="key-123", language="ms", operating_point="standard"
    )

    with patch("meeting.transcriber.requests") as mock_requests:
        mock_requests.post.return_value = _submit_response()
        mock_requests.get.side_effect = [
            _status_response("done"),
            _transcript_response(["Selamat", "pagi"]),
        ]
        result = transcriber.transcribe(audio)

    assert result == "Selamat pagi"
    # Verify the config was passed in the POST request
    call_kwargs = mock_requests.post.call_args
    files = call_kwargs.kwargs.get("files") or call_kwargs[1].get("files")
    config_json = files["config"][1]
    config = json.loads(config_json)
    assert config["transcription_config"]["language"] == "ms"
    assert config["transcription_config"]["operating_point"] == "standard"
