from __future__ import annotations

from pathlib import Path

from ..models import ENTITY_TYPES
from ..ollama import OllamaClient
from .ollama_json import chat_json
from .schemas import ExtractedEntity, ResolutionResult

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
RESOLUTION_THRESHOLD = 0.75


def load_prompt(name: str, **variables: str) -> str:
    template = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    for key, value in variables.items():
        template = template.replace(f"{{{key}}}", value)
    return template


def normalize_entity_type(raw_type: str) -> str:
    normalized = raw_type.strip().upper()
    if normalized in ENTITY_TYPES:
        return normalized
    if normalized == "UNKNOWN":
        return "ORGANIZATION"
    return "ORGANIZATION"


def find_mention_span(source_text: str, mention: str) -> tuple[int, int] | None:
    if not mention.strip():
        return None
    lowered = source_text.lower()
    target = mention.lower()
    index = lowered.find(target)
    if index < 0:
        return None
    return index, index + len(mention)


def extract_entities(client: OllamaClient, source_text: str) -> list[ExtractedEntity]:
    prompt = load_prompt("entity_extraction_v1.txt", source_text=source_text)
    entities = chat_json(client, prompt, ExtractedEntity)
    for entity in entities:
        entity.type = normalize_entity_type(entity.type)
    return entities


def resolve_entities(
    client: OllamaClient,
    extracted: list[ExtractedEntity],
    existing_entities: list[dict],
    *,
    threshold: float = RESOLUTION_THRESHOLD,
) -> list[tuple[ExtractedEntity, ResolutionResult]]:
    if not extracted:
        return []

    candidate_payload = [
        {
            "id": entity["id"],
            "name": entity["name"],
            "type": entity["entity_type"],
            "aliases": entity.get("aliases_json", "[]"),
        }
        for entity in existing_entities
    ]
    new_payload = [entity.model_dump() for entity in extracted]
    prompt = load_prompt(
        "entity_resolution_v1.txt",
        candidate_entities=json_dumps(candidate_payload),
        new_entities=json_dumps(new_payload),
    )
    results = chat_json(client, prompt, ResolutionResult)
    by_name = {result.extracted_name: result for result in results}
    resolved: list[tuple[ExtractedEntity, ResolutionResult]] = []
    for entity in extracted:
        result = by_name.get(entity.name)
        if result is None:
            result = ResolutionResult(
                extracted_name=entity.name,
                matched_entity_id=None,
                confidence=0.0,
                reason="No resolution result returned",
            )
        if result.confidence < threshold:
            result = ResolutionResult(
                extracted_name=result.extracted_name,
                matched_entity_id=None,
                confidence=result.confidence,
                reason=result.reason,
            )
        resolved.append((entity, result))
    return resolved


def json_dumps(payload: object) -> str:
    import json

    return json.dumps(payload, indent=2)
