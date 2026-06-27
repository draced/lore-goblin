from __future__ import annotations

import json
import sqlite3

import pytest

from lore_goblin.db import connection_at, get_connection, new_id
from lore_goblin.models import EntityType, SourceType
from lore_goblin.retrieval.hybrid import hybrid_retrieve, merge_hits


@pytest.fixture
def hybrid_campaign(database_path, campaign) -> dict:
    with connection_at(database_path) as connection:
        _seed_hybrid_data(connection, campaign["id"])
    return campaign


def _seed_hybrid_data(connection: sqlite3.Connection, campaign_id: str) -> None:
    owner = connection.execute(
        """
        SELECT user_id
        FROM campaign_members
        WHERE campaign_id = ? AND role = 'owner'
        LIMIT 1
        """,
        (campaign_id,),
    ).fetchone()
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
    body = "The party found a silver key in the ruined chapel."
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
            body,
            owner_id,
            session_id,
        ),
    )
    chunk_id = new_id("chk")
    connection.execute(
        """
        INSERT INTO content_chunks (
            id, campaign_id, session_id, source_type, source_id, chunk_index, chunk_text
        )
        VALUES (?, ?, ?, 'session_note', ?, 0, ?)
        """,
        (chunk_id, campaign_id, session_id, source_id, body),
    )
    silver_key_id = new_id("ent")
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
            "A silver key.",
        ),
    )
    claim_id = new_id("clm")
    connection.execute(
        """
        INSERT INTO claim (
            id, campaign_id, claim_text, subject_entity_id, predicate,
            object_entity_id, canon_status, source_id
        )
        VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
        """,
        (
            claim_id,
            campaign_id,
            "The party found the silver key in the ruined chapel.",
            silver_key_id,
            "found_at",
            "CONFIRMED",
            source_id,
        ),
    )


def test_merge_dedup_prefers_single_claim(hybrid_campaign) -> None:
    campaign_id = hybrid_campaign["id"]
    with get_connection() as connection:
        fts_hits = [
            {
                "record_id": "clm_test",
                "result_type": "claim",
                "text": "Claim one",
                "claim_text": "Claim one",
                "canon_status": "CONFIRMED",
                "source_id": "src_test",
                "source_title": "Session 8 — Chapel",
                "source_type": "SESSION_NOTE",
                "fts_score": 0.8,
                "vec_score": 0.0,
            },
            {
                "record_id": "clm_test",
                "result_type": "claim",
                "text": "Claim one",
                "claim_text": "Claim one",
                "canon_status": "CONFIRMED",
                "source_id": "src_test",
                "source_title": "Session 8 — Chapel",
                "source_type": "SESSION_NOTE",
                "fts_score": 0.5,
                "vec_score": 0.0,
            },
        ]
        merged = merge_hits(connection, campaign_id, "silver key", fts_hits, [])
    assert len(merged) == 1


def test_claim_preferred_over_chunk(hybrid_campaign) -> None:
    campaign_id = hybrid_campaign["id"]
    results = hybrid_retrieve(campaign_id, "silver key")
    types = [item.result_type for item in results]
    assert "claim" in types
    chunk_ids = {item.record_id for item in results if item.result_type == "chunk"}
    claim_sources = {item.source_id for item in results if item.result_type == "claim"}
    assert not chunk_ids.intersection(
        {
            item.record_id
            for item in results
            if item.result_type == "chunk" and item.source_id in claim_sources
        }
    )
