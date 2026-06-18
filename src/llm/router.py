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
                "Authorization": f"******",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=30) as response:  # nosec B310 - fixed HTTPS API endpoint
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
