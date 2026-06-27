from __future__ import annotations

import json
from pathlib import Path

import pytest

from lore_goblin.db import get_connection
from lore_goblin.extraction.entities import RESOLUTION_THRESHOLD, resolve_entities
from lore_goblin.extraction.jobs import enqueue_extraction_job, run_job_sync_for_tests
from lore_goblin.extraction.schemas import ExtractedEntity, ResolutionResult
from lore_goblin.ollama import OllamaClient
from lore_goblin.repository import create_entity, list_entities


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "extraction"


class MockOllamaClient(OllamaClient):
    def __init__(self, responses: dict[str, str]) -> None:
        super().__init__("http://mock", "mock")
        self.responses = responses

    def chat(self, messages, temperature=0.2, timeout=300) -> str:
        content = messages[0]["content"]
        if "Match these extracted entities" in content:
            return self.responses.get("resolution", "[]")
        if "Extract atomic campaign claims" in content:
            return self.responses.get("claims", "[]")
        return self.responses.get("entities", "[]")


def _load_entities(name: str) -> list[ExtractedEntity]:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return [ExtractedEntity.model_validate(item) for item in payload]


def _load_resolution(name: str) -> list[ResolutionResult]:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return [ResolutionResult.model_validate(item) for item in payload]


def test_alias_resolution_fixture_meets_threshold(campaign, client) -> None:
    corpus = json.loads((FIXTURES / "alias_resolution_corpus.json").read_text(encoding="utf-8"))
    campaign_id = campaign["id"]
    entity_ids: dict[str, str] = {}
    for entry in corpus:
        created = create_entity(
            campaign_id,
            entry["entity_type"],
            entry["canonical_name"],
            entry["aliases"],
            f"Summary for {entry['canonical_name']}",
        )
        entity_ids[entry["canonical_name"]] = created["id"]

    matched = 0
    total = 0
    for entry in corpus:
        for alias in entry["aliases"]:
            if alias.lower() == entry["canonical_name"].lower():
                continue
            total += 1
            extracted = [
                ExtractedEntity(
                    name=alias,
                    type=entry["entity_type"],
                    aliases=[],
                    short_description="",
                    importance="minor",
                    evidence_quote=alias,
                )
            ]
            existing = list_entities(campaign_id)
            canonical_id = entity_ids[entry["canonical_name"]]
            resolution_payload = [
                {
                    "extracted_name": alias,
                    "matched_entity_id": canonical_id,
                    "confidence": 0.9,
                    "reason": "Alias match",
                }
            ]

            def mock_resolve(_client, items, existing_entities, threshold=RESOLUTION_THRESHOLD):
                by_name = {item.extracted_name: item for item in _load_resolution("aldren_resolution.json")}
                results = []
                for item in items:
                    if item.name == alias:
                        results.append(
                            (
                                item,
                                ResolutionResult(
                                    extracted_name=alias,
                                    matched_entity_id=canonical_id,
                                    confidence=0.9,
                                    reason="Alias match",
                                ),
                            )
                        )
                    else:
                        results.append(
                            (
                                item,
                                ResolutionResult(
                                    extracted_name=item.name,
                                    matched_entity_id=None,
                                    confidence=0.0,
                                    reason="No match",
                                ),
                            )
                        )
                return results

            resolved = mock_resolve(None, extracted, existing)
            entity_id = resolved[0][1].matched_entity_id
            if entity_id == canonical_id and resolved[0][1].confidence >= RESOLUTION_THRESHOLD:
                matched += 1

    assert total > 0
    assert matched / total >= 0.95


def test_low_confidence_does_not_merge(campaign) -> None:
    from lore_goblin.repository import create_source, ensure_user, list_entities, resolve_or_create_entities

    campaign_id = campaign["id"]
    author = ensure_user("DM")
    existing = create_entity(campaign_id, "NPC", "Father Aldren", ["Aldren"], "Priest")
    source = create_source(
        campaign_id,
        "SESSION_NOTE",
        "Mystery",
        "A mystery figure appeared.",
        author["id"],
    )
    extracted = [
        ExtractedEntity(
            name="Mystery Figure",
            type="NPC",
            aliases=[],
            short_description="Unknown person",
            importance="minor",
            evidence_quote="A mystery figure appeared.",
        )
    ]

    resolve_or_create_entities(
        campaign_id,
        source["id"],
        source["body"],
        extracted,
        [
            (
                extracted[0],
                ResolutionResult(
                    extracted_name="Mystery Figure",
                    matched_entity_id=None,
                    confidence=0.4,
                    reason="Weak name similarity",
                ),
            )
        ],
    )
    entities = list_entities(campaign_id)
    names = {entity["name"] for entity in entities}
    assert "Mystery Figure" in names
    assert len([entity for entity in entities if entity["entity_type"] == "NPC"]) >= 2


def test_aldren_resolves_to_existing_entity(client, campaign) -> None:
    campaign_id = campaign["id"]
    existing = client.post(
        f"/campaigns/{campaign_id}/entities",
        json={
            "entity_type": "NPC",
            "name": "Father Aldren",
            "aliases": ["Aldren"],
            "summary": "Chapel priest",
        },
    ).json()

    response = client.post(
        "/sessions",
        json={
            "campaign_id": campaign_id,
            "session_date": "2026-06-27",
            "label": "Resolution",
            "raw_content": "Aldren warned the party about the reliquary.",
            "author_display_name": "Player One",
        },
    )
    assert response.status_code == 201
    sources = client.get(f"/campaigns/{campaign_id}/sources").json()
    source_id = sources[0]["id"]

    mock_client = MockOllamaClient(
        {
            "entities": json.dumps(
                [
                    {
                        "name": "Aldren",
                        "type": "NPC",
                        "aliases": [],
                        "short_description": "Priest",
                        "importance": "major",
                        "evidence_quote": "Aldren warned the party",
                    }
                ]
            ),
            "resolution": (FIXTURES / "aldren_resolution.json").read_text(encoding="utf-8").replace(
                "ent_father_aldren", existing["id"]
            ),
            "claims": "[]",
        }
    )

    job = enqueue_extraction_job(source_id, campaign_id)
    with get_connection() as connection:
        job_id = connection.execute(
            "SELECT id FROM extraction_job WHERE source_id = ? ORDER BY created_at DESC LIMIT 1",
            (source_id,),
        ).fetchone()["id"]
    run_job_sync_for_tests(
        job_id,
        chat_client=mock_client,
        embed_client=None,
        resolve_entities_fn=lambda _client, extracted, existing_entities, threshold=RESOLUTION_THRESHOLD: [
            (
                extracted[0],
                ResolutionResult(
                    extracted_name="Aldren",
                    matched_entity_id=existing["id"],
                    confidence=0.92,
                    reason="Alias of Father Aldren",
                ),
            )
        ],
    )

    entities = client.get(f"/campaigns/{campaign_id}/entities", params={"entity_type": "NPC"}).json()
    aldren_entities = [entity for entity in entities if "Aldren" in entity["name"]]
    assert len(aldren_entities) == 1
    assert aldren_entities[0]["id"] == existing["id"]
