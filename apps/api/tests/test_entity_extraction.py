from __future__ import annotations

import json
from pathlib import Path

import pytest

from lore_goblin.extraction.entities import find_mention_span
from lore_goblin.extraction.ollama_json import parse_json_response
from lore_goblin.extraction.schemas import ExtractedEntity, ResolutionResult


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "extraction"


def test_parse_entity_json_fixture() -> None:
    payload = json.loads((FIXTURES / "chapel_entities.json").read_text(encoding="utf-8"))
    entities = [ExtractedEntity.model_validate(item) for item in payload]
    assert len(entities) == 3
    assert entities[0].name == "Father Aldren"
    assert entities[0].type == "NPC"


def test_parse_json_response_strips_markdown_fence() -> None:
    raw = '```json\n[{"name":"Aldren","type":"NPC","importance":"major","evidence_quote":"Aldren spoke."}]\n```'
    parsed = parse_json_response(raw, ExtractedEntity)
    assert isinstance(parsed, list)
    assert parsed[0].name == "Aldren"


def test_find_mention_span_returns_offsets() -> None:
    source = "The party found a silver key in the ruined chapel."
    span = find_mention_span(source, "silver key")
    assert span == (18, 28)


def test_find_mention_span_missing_returns_none() -> None:
    assert find_mention_span("hello world", "missing") is None


@pytest.mark.parametrize(
    ("raw", "expected_name"),
    [
        ("Father Aldren", "Father Aldren"),
        ("Aldren", "Aldren"),
    ],
)
def test_resolution_schema_accepts_fixture_values(raw: str, expected_name: str) -> None:
    payload = json.loads((FIXTURES / "aldren_resolution.json").read_text(encoding="utf-8"))
    result = ResolutionResult.model_validate(payload[0])
    assert result.extracted_name == "Aldren"
    assert result.matched_entity_id == "ent_father_aldren"
    assert result.confidence >= 0.75
