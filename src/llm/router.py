"""Minimal 9router.com API client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request


@dataclass(slots=True)
class NineRouterClient:
    api_key: str
    model: str
    endpoint: str = "https://9router.com/api/v1/chat/completions"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0,
            }
        ).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=60) as response:  # nosec B310 - fixed HTTPS API endpoint
            raw = response.read().decode("utf-8")
        # Use raw_decode to handle trailing SSE data (e.g. "data: [DONE]")
        body, _ = json.JSONDecoder().raw_decode(raw)
        return body["choices"][0]["message"]["content"]
