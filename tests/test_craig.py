"""Tests for Craig REST API client."""

import json
from unittest.mock import patch, MagicMock

from integrations.craig import CraigClient


def test_craig_client_builds_correct_auth_header():
    """Verify the Authorization header uses Bearer token format."""
    client = CraigClient(api_key="test-key-123", base_url="https://craig.chat/api")

    with patch("integrations.craig.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"download_url": "https://example.com/audio.flac"}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        url = client.get_recording_download_url("rec-abc")

        # Verify the request was made with correct auth
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert req.get_header("Authorization") == "Bearer test-key-123"
        assert "rec-abc" in req.full_url
        assert url == "https://example.com/audio.flac"


def test_craig_client_download_recording_returns_bytes():
    """Verify download_recording returns raw audio bytes."""
    client = CraigClient(api_key="key", base_url="https://craig.chat/api")
    audio_bytes = b"\x00\x01\x02audio-data"

    with patch("integrations.craig.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = audio_bytes
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = client.download_recording("https://example.com/audio.flac")

        assert result == audio_bytes


def test_craig_client_strips_trailing_slash_in_base_url():
    """Verify base_url trailing slash doesn't cause double-slash in URLs."""
    client = CraigClient(api_key="key", base_url="https://craig.chat/api/")

    with patch("integrations.craig.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"download_url": "url"}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client.get_recording_download_url("rec-123")

        req = mock_urlopen.call_args[0][0]
        assert "//api//recordings" not in req.full_url
        assert "/api/recordings/rec-123" in req.full_url
