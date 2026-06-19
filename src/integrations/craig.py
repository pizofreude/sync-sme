"""Craig REST API client helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request


@dataclass(slots=True)
class CraigClient:
    api_key: str
    base_url: str = "https://craig.chat/api"

    def get_recording_download_url(self, recording_id: str) -> str:
        req = request.Request(
            f"{self.base_url.rstrip('/')}/recordings/{recording_id}",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        with request.urlopen(req, timeout=30) as response:  # nosec B310 - fixed HTTPS API endpoint
            payload = json.loads(response.read().decode("utf-8"))
        return payload["download_url"]

    def download_recording(self, download_url: str) -> bytes:
        req = request.Request(download_url, headers={"Authorization": f"Bearer {self.api_key}"})
        with request.urlopen(req, timeout=30) as response:  # nosec B310 - caller provides Craig API download URL
            return response.read()
