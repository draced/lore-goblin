from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from lore_goblin.answering import ADMIT_UNKNOWN_ANSWER, answer_question
from lore_goblin.db import connection_at, get_connection, new_id
from lore_goblin.models import EntityType, SourceType
from lore_goblin.ollama import OllamaClient


class MockOllamaClient(OllamaClient):
    def __init__(self, answer: str = "The silver key was in the ruined chapel.") -> None:
        super().__init__("http://mock", "mock")
        self.answer = answer
        self.last_messages: list[dict] | None = None

    def chat(self, messages, temperature=0.2, timeout=300) -> str:
        self.last_messages = messages
        return self.answer


@pytest.fixture
def citation_campaign(database_path, campaign) -> dict:
    with connection_at(database_path) as connection:
        owner = connection.execute(
            """
            SELECT user_id
            FROM campaign_members
            WHERE campaign_id = ? AND role = 'owner'
            LIMIT 1
            """,
            (campaign["id"],),
        ).fetchone()
        session_id = new_id("ses")
        connection.execute(
            """
            INSERT INTO sessions (id, campaign_id, session_date, label)
            VALUES (?, ?, '2026-06-08', 'Chapel')
            """,
            (session_id, campaign["id"]),
        )
        source_id = new_id("src")
        connection.execute(
            """
            INSERT INTO source (
                id, campaign_id, source_type, title, body, author_user_id, session_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                campaign["id"],
                SourceType.SESSION_NOTE,
                "Session 8 — Chapel",
                "The party found a silver key in the ruined chapel.",
                owner["user_id"],
                session_id,
            ),
        )
        entity_id = new_id("ent")
        connection.execute(
            """
            INSERT INTO entity (id, campaign_id, entity_type, name, aliases_json, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entity_id,
                campaign["id"],
                EntityType.ITEM,
                "Silver Key",
                json.dumps(["silver key"]),
                "A silver key.",
            ),
        )
        connection.execute(
            """
            INSERT INTO claim (
                id, campaign_id, claim_text, subject_entity_id, predicate,
                object_entity_id, canon_status, source_id
            )
            VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (
                new_id("clm"),
                campaign["id"],
                "The party found the silver key in the ruined chapel.",
                entity_id,
                "found_at",
                "CONFIRMED",
                source_id,
            ),
        )
    return campaign


def test_citation_shape_with_source_title(citation_campaign) -> None:
    mock_client = MockOllamaClient()
    with patch("lore_goblin.answering.OllamaClient", return_value=mock_client):
        result = answer_question(citation_campaign["id"], "Where is the silver key?")
    assert result["citations"]
    citation = result["citations"][0]
    assert citation["label"] == "Session 8 — Chapel"
    assert citation["source_type"] == SourceType.SESSION_NOTE
    assert "silver key" in (citation.get("claim_quote") or "").lower()


def test_admit_unknown_when_no_context(citation_campaign) -> None:
    result = answer_question(citation_campaign["id"], "What is the name of the lost moon?")
    assert result["answer"] == ADMIT_UNKNOWN_ANSWER
    assert result["citations"] == []
    assert result["used_model"] is None


def test_disputed_claim_surfaced_in_prompt(citation_campaign) -> None:
    with get_connection() as connection:
        claim = connection.execute(
            "SELECT id, source_id, subject_entity_id FROM claim LIMIT 1"
        ).fetchone()
        connection.execute(
            """
            INSERT INTO claim (
                id, campaign_id, claim_text, subject_entity_id, predicate,
                object_entity_id, canon_status, source_id
            )
            VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (
                new_id("clm"),
                citation_campaign["id"],
                "The silver key was stolen before the party arrived.",
                claim["subject_entity_id"],
                "stolen_before",
                "DISPUTED",
                claim["source_id"],
            ),
        )
    mock_client = MockOllamaClient("Sources disagree about the silver key.")
    with patch("lore_goblin.answering.OllamaClient", return_value=mock_client):
        answer_question(citation_campaign["id"], "silver key")
    assert mock_client.last_messages is not None
    system_prompt = mock_client.last_messages[0]["content"]
    assert "DISPUTED" in system_prompt


def test_no_pc_roster_in_prompt(citation_campaign, client) -> None:
    client.post(
        "/player-characters",
        json={
            "campaign_id": citation_campaign["id"],
            "name": "Nyra",
            "notes": "Half-elf ranger in the party.",
        },
    )
    mock_client = MockOllamaClient("Nyra is a half-elf ranger.")
    with patch("lore_goblin.answering.OllamaClient", return_value=mock_client):
        answer_question(citation_campaign["id"], "Who is Nyra?")
    user_prompt = mock_client.last_messages[1]["content"]
    assert "Player character roster" not in user_prompt
    assert "[PC roster]" not in user_prompt


def test_ask_endpoint_uses_hybrid_path(client, citation_campaign) -> None:
    mock_client = MockOllamaClient()
    with patch("lore_goblin.answering.OllamaClient", return_value=mock_client):
        response = client.post(
            "/ask",
            json={
                "campaign_id": citation_campaign["id"],
                "question": "Where is the silver key?",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]
    assert "PC roster" not in {citation["label"] for citation in body["citations"]}
