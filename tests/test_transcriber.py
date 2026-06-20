"""Tests for WhisperTranscriber."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from meeting.transcriber import WhisperTranscriber


def _mock_whisper():
    """Create a mock whisper module and inject it into sys.modules."""
    mock_whisper = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    return mock_whisper, mock_model


def test_transcriber_calls_whisper_with_correct_model():
    """Verify transcriber loads the specified model and transcribes."""
    mock_whisper, mock_model = _mock_whisper()
    mock_model.transcribe.return_value = {"text": "Hello, this is a test transcript."}

    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        transcriber = WhisperTranscriber(model_name="base")
        result = transcriber.transcribe(Path("audio.flac"))

    mock_whisper.load_model.assert_called_once_with("base")
    mock_model.transcribe.assert_called_once_with("audio.flac")
    assert result == "Hello, this is a test transcript."


def test_transcriber_strips_whitespace_from_result():
    """Verify transcriber strips leading/trailing whitespace."""
    mock_whisper, mock_model = _mock_whisper()
    mock_model.transcribe.return_value = {"text": "  padded text  "}

    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        transcriber = WhisperTranscriber(model_name="tiny")
        result = transcriber.transcribe(Path("audio.ogg"))

    assert result == "padded text"


def test_transcriber_handles_empty_transcript():
    """Verify transcriber handles empty transcript gracefully."""
    mock_whisper, mock_model = _mock_whisper()
    mock_model.transcribe.return_value = {"text": ""}

    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        transcriber = WhisperTranscriber(model_name="base")
        result = transcriber.transcribe(Path("silence.flac"))

    assert result == ""


def test_transcriber_handles_missing_text_key():
    """Verify transcriber handles missing 'text' key in whisper output."""
    mock_whisper, mock_model = _mock_whisper()
    mock_model.transcribe.return_value = {}

    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        transcriber = WhisperTranscriber(model_name="base")
        result = transcriber.transcribe(Path("audio.flac"))

    assert result == ""


def test_transcriber_raises_on_missing_whisper():
    """Verify transcriber raises RuntimeError when whisper is not installed."""
    # Ensure whisper is NOT in sys.modules
    saved = sys.modules.pop("whisper", None)
    try:
        transcriber = WhisperTranscriber(model_name="base")
        try:
            transcriber.transcribe(Path("audio.flac"))
            assert False, "Should have raised RuntimeError"
        except RuntimeError as exc:
            assert "openai-whisper" in str(exc)
    finally:
        if saved is not None:
            sys.modules["whisper"] = saved
