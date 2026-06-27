from __future__ import annotations

import json
import time
from pathlib import Path

from lore_goblin.db import get_connection
from lore_goblin.extraction.importance import compute_importance_score
from lore_goblin.extraction.jobs import enqueue_extraction_job, get_extraction_status, run_job_sync_for_tests
from lore_goblin.extraction.schemas import ExtractedEntity, ResolutionResult
from lore_goblin.ollama import OllamaClient


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "extraction"


class MockOllamaClient(OllamaClient):
    def __init__(self) -> None:
        super().__init__("http://mock", "mock")

    def chat(self, messages, temperature=0.2, timeout=300) -> str:
        content = messages[0]["content"]
        if "Extract atomic campaign claims" in content:
            return "[]"
        if "Match these extracted entities" in content:
            return "[]"
        return (FIXTURES / "chapel_entities.json").read_text(encoding="utf-8")


def test_enqueue_creates_pending_job(client, campaign) -> None:
    response = client.post(
        "/sessions",
        json={
            "campaign_id": campaign["id"],
            "session_date": "2026-06-27",
            "label": "Pipeline",
            "raw_content": "The party met Father Aldren.",
            "author_display_name": "Player One",
        },
    )
    assert response.status_code == 201
    sources = client.get(f"/campaigns/{campaign['id']}/sources").json()
    source_id = sources[0]["id"]

    status_response = client.get(f"/sources/{source_id}/extraction-status")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["source_id"] == source_id
    assert body["status"] in {"pending", "running", "complete", "failed"}


def test_job_lifecycle_complete(client, campaign) -> None:
    response = client.post(
        "/sessions",
        json={
            "campaign_id": campaign["id"],
            "session_date": "2026-06-28",
            "label": "Lifecycle",
            "raw_content": "The party found a silver key in the ruined chapel.",
            "author_display_name": "Player One",
        },
    )
    sources = client.get(f"/campaigns/{campaign['id']}/sources").json()
    source_id = sources[0]["id"]
    jobs = []
    with get_connection() as connection:
        jobs = connection.execute(
            "SELECT id FROM extraction_job WHERE source_id = ?",
            (source_id,),
        ).fetchall()
    job_id = jobs[0]["id"]
    run_job_sync_for_tests(job_id, chat_client=MockOllamaClient(), embed_client=None)

    status = get_extraction_status(source_id)
    assert status is not None
    assert status["status"] == "complete"


def test_importance_formula() -> None:
    score = compute_importance_score(
        mention_count=3,
        session_count=2,
        relationship_count=1,
        unresolved_claim_count=1,
        manually_pinned=True,
        recent_session_bonus=True,
    )
    assert score == 3 + 2 + 1 + 1 + 10 + 5


def test_entity_mentions_created_after_pipeline(client, campaign) -> None:
    response = client.post(
        "/sessions",
        json={
            "campaign_id": campaign["id"],
            "session_date": "2026-06-29",
            "label": "Mentions",
            "raw_content": "Father Aldren warned them about the reliquary.",
            "author_display_name": "Player One",
        },
    )
    assert response.status_code == 201
    sources = client.get(f"/campaigns/{campaign['id']}/sources").json()
    source_id = sources[0]["id"]
    with get_connection() as connection:
        job_id = connection.execute(
            "SELECT id FROM extraction_job WHERE source_id = ?",
            (source_id,),
        ).fetchone()["id"]
    run_job_sync_for_tests(job_id, chat_client=MockOllamaClient(), embed_client=None)

    with get_connection() as connection:
        mentions = connection.execute(
            "SELECT * FROM entity_mention WHERE source_id = ?",
            (source_id,),
        ).fetchall()
    assert len(mentions) >= 1
