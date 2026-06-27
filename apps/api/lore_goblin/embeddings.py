from __future__ import annotations

import json
import struct
from urllib import request


class EmbeddingClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed(self, text: str, timeout: int = 120) -> bytes:
        payload = {"model": self.model, "prompt": text}
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/embeddings",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        vector = body.get("embedding", [])
        return struct.pack(f"{len(vector)}f", *vector)
