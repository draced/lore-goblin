from __future__ import annotations

from ..ollama import OllamaClient
from .entities import load_prompt
from .ollama_json import chat_json
from .schemas import ExtractedClaim


def extract_claims(
    client: OllamaClient,
    source_text: str,
    resolved_entities: list[dict],
) -> list[ExtractedClaim]:
    entity_payload = [
        {
            "id": entity["id"],
            "name": entity["name"],
            "type": entity["entity_type"],
            "aliases": entity.get("aliases_json", "[]"),
        }
        for entity in resolved_entities
    ]
    import json

    prompt = load_prompt(
        "claim_extraction_v1.txt",
        resolved_entities=json.dumps(entity_payload, indent=2),
        source_text=source_text,
    )
    return chat_json(client, prompt, ExtractedClaim)


def claims_to_relationships(claims: list[ExtractedClaim]) -> list[dict]:
    relationships: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for claim in claims:
        if not claim.object_entity_name:
            continue
        key = (
            claim.subject_entity_name.strip().lower(),
            claim.object_entity_name.strip().lower(),
            claim.predicate.strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        relationships.append(
            {
                "source_entity_name": claim.subject_entity_name,
                "target_entity_name": claim.object_entity_name,
                "relationship_type": claim.predicate,
                "description": claim.claim_text,
            }
        )
    return relationships
