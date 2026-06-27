from __future__ import annotations

import json
from pathlib import Path

from lore_goblin.db import get_connection
from lore_goblin.extraction.jobs import enqueue_extraction_job, run_job_sync_for_tests
from lore_goblin.extraction.schemas import ExtractedClaim, ExtractedEntity, ResolutionResult
from lore_goblin.ollama import OllamaClient


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "extraction"


class MockOllamaClient(OllamaClient):
    def __init__(self, responses: dict[str, str]) -> None:
        super().__init__("http://mock", "mock")
        self.responses = responses

    def chat(self, messages, temperature=0.2, timeout=300) -> str:
        content = messages[0]["content"]
        if "Extract atomic campaign claims" in content:
            return self.responses["claims"]
        if "Match these extracted entities" in content:
            return self.responses.get("resolution", "[]")
        return self.responses["entities"]


def _default_entities() -> str:
    return (FIXTURES / "chapel_entities.json").read_text(encoding="utf-8")


def _default_claims() -> str:
    return (FIXTURES / "chapel_claims.json").read_text(encoding="utf-8")


def _run_chapel_extraction(client, campaign_id: str) -> str:
    response = client.post(
        "/sessions",
        json={
            "campaign_id": campaign_id,
            "session_date": "2026-06-27",
            "label": "Chapel",
            "raw_content": (
                "The party found a silver key in the ruined chapel. "
                "Father Aldren warned them about the reliquary."
            ),
            "author_display_name": "Player One",
        },
    )
    assert response.status_code == 201
    sources = client.get(f"/campaigns/{campaign_id}/sources").json()
    return sources[0]["id"]


def _run_sync_extraction(source_id: str, campaign_id: str, mock_client: MockOllamaClient) -> None:
    with get_connection() as connection:
        job_id = connection.execute(
            "SELECT id FROM extraction_job WHERE source_id = ? ORDER BY created_at DESC LIMIT 1",
            (source_id,),
        ).fetchone()["id"]
    run_job_sync_for_tests(job_id, chat_client=mock_client, embed_client=None)


def test_claims_persist_after_extraction(client, campaign) -> None:
    source_id = _run_chapel_extraction(client, campaign["id"])
    mock_client = MockOllamaClient({"entities": _default_entities(), "claims": _default_claims()})
    _run_sync_extraction(source_id, campaign["id"], mock_client)

    with get_connection() as connection:
        claims = connection.execute(
            "SELECT * FROM claim WHERE source_id = ?",
            (source_id,),
        ).fetchall()
        relationships = connection.execute(
            "SELECT * FROM relationship WHERE source_id = ?",
            (source_id,),
        ).fetchall()

    assert len(claims) >= 2
    assert any(claim["predicate"] == "found_at" for claim in claims)
    assert len(relationships) >= 1


def test_no_invented_claims_from_empty_response(client, campaign) -> None:
    source_id = _run_chapel_extraction(client, campaign["id"])
    mock_client = MockOllamaClient({"entities": "[]", "claims": "[]"})
    _run_sync_extraction(source_id, campaign["id"], mock_client)

    with get_connection() as connection:
        claim_count = connection.execute(
            "SELECT COUNT(*) FROM claim WHERE source_id = ?",
            (source_id,),
        ).fetchone()[0]

    assert claim_count == 0


def test_relationships_persist_from_claims(client, campaign) -> None:
    source_id = _run_chapel_extraction(client, campaign["id"])
    mock_client = MockOllamaClient({"entities": _default_entities(), "claims": _default_claims()})
    _run_sync_extraction(source_id, campaign["id"], mock_client)

    with get_connection() as connection:
        relationships = connection.execute(
            """
            SELECT relationship_type
            FROM relationship
            WHERE source_id = ?
            """,
            (source_id,),
        ).fetchall()

    types = {row["relationship_type"] for row in relationships}
    assert "found_at" in types or "warned_about" in types
