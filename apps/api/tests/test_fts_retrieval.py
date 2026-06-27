from __future__ import annotations

import json
import struct
import sqlite3

import pytest

from lore_goblin.db import connection_at, get_connection, new_id
from lore_goblin.models import EntityType, SourceType
from lore_goblin.retrieval.fts import search_claims, search_entities, search_fts


@pytest.fixture
def search_campaign(database_path, campaign) -> dict:
    with connection_at(database_path) as connection:
        _seed_search_data(connection, campaign["id"])
    return campaign


def _seed_search_data(connection: sqlite3.Connection, campaign_id: str) -> None:
    owner = connection.execute(
        """
        SELECT user_id
        FROM campaign_members
        WHERE campaign_id = ? AND role = 'owner'
        LIMIT 1
        """,
        (campaign_id,),
    ).fetchone()
    assert owner is not None
    owner_id = owner["user_id"]

    session_id = new_id("ses")
    connection.execute(
        """
        INSERT INTO sessions (id, campaign_id, session_date, label)
        VALUES (?, ?, '2026-06-08', 'Chapel')
        """,
        (session_id, campaign_id),
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
            campaign_id,
            SourceType.SESSION_NOTE,
            "Session 8 — Chapel",
            "The party found a silver key in the ruined chapel.",
            owner_id,
            session_id,
        ),
    )

    silver_key_id = new_id("ent")
    chapel_id = new_id("ent")
    connection.execute(
        """
        INSERT INTO entity (id, campaign_id, entity_type, name, aliases_json, summary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            silver_key_id,
            campaign_id,
            EntityType.ITEM,
            "Silver Key",
            json.dumps(["silver key"]),
            "A silver key found in the chapel.",
        ),
    )
    connection.execute(
        """
        INSERT INTO entity (id, campaign_id, entity_type, name, aliases_json, summary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            chapel_id,
            campaign_id,
            EntityType.LOCATION,
            "Ruined Chapel",
            json.dumps(["the chapel"]),
            "An abandoned chapel where the party found a key.",
        ),
    )

    claim_id = new_id("clm")
    connection.execute(
        """
        INSERT INTO claim (
            id, campaign_id, claim_text, subject_entity_id, predicate,
            object_entity_id, canon_status, source_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            campaign_id,
            "The party found the silver key in the ruined chapel.",
            silver_key_id,
            "found_at",
            chapel_id,
            "CONFIRMED",
            source_id,
        ),
    )


def test_entity_name_fts_match(search_campaign) -> None:
    campaign_id = search_campaign["id"]
    with get_connection() as connection:
        hits = search_entities(connection, campaign_id, "Where is the silver key?")
    assert any(hit["record_id"] and "Silver" in hit.get("name", hit["text"]) for hit in hits)


def test_entity_alias_fts_match(search_campaign) -> None:
    campaign_id = search_campaign["id"]
    with get_connection() as connection:
        hits = search_entities(connection, campaign_id, "the chapel")
    assert any("Ruined Chapel" in hit.get("name", hit["text"]) for hit in hits)


def test_claim_fts_match(search_campaign) -> None:
    campaign_id = search_campaign["id"]
    with get_connection() as connection:
        hits = search_claims(connection, campaign_id, "silver key ruined chapel")
    assert len(hits) >= 1
    assert "silver key" in hits[0]["claim_text"].lower()


def test_fts_campaign_scope(search_campaign, client) -> None:
    other = client.post(
        "/campaigns",
        json={"name": "Other", "tone": "Quiet.", "owner_display_name": "DM"},
    ).json()
    with get_connection() as connection:
        _seed_search_data(connection, other["id"])
        campaign_hits = search_entities(connection, search_campaign["id"], "silver key")
        other_hits = search_entities(connection, other["id"], "silver key")
    assert campaign_hits
    assert all("Silver Key" in hit.get("name", hit["text"]) for hit in campaign_hits)
    assert all("Silver Key" in hit.get("name", hit["text"]) for hit in other_hits)
    assert campaign_hits[0]["record_id"] != other_hits[0]["record_id"]
