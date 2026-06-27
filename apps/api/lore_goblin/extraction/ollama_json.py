from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel

from ..ollama import OllamaClient

T = TypeVar("T", bound=BaseModel)


def parse_json_response(raw: str, model: type[T]) -> T | list[T]:
    text = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    data = json.loads(text)
    if isinstance(data, list):
        return [model.model_validate(item) for item in data]
    return model.model_validate(data)


def chat_json(
    client: OllamaClient,
    prompt: str,
    model: type[T],
    *,
    temperature: float = 0.1,
) -> list[T]:
    content = client.chat(
        [{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    parsed = parse_json_response(content, model)
    if isinstance(parsed, list):
        return parsed
    return [parsed]
