"""Meeting recorder integration built on Craig."""

from __future__ import annotations

from dataclasses import dataclass

from integrations.craig import CraigClient


@dataclass(slots=True)
class CraigRecorder:
    client: CraigClient

    def fetch_audio(self, recording_id: str) -> bytes:
        download_url = self.client.get_recording_download_url(recording_id)
        return self.client.download_recording(download_url)
