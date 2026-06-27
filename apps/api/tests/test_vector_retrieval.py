from __future__ import annotations

import struct

import pytest

from lore_goblin.db import connection_at, get_connection, new_id
from lore_goblin.retrieval.vectors import EMBEDDING_DIM, search_vectors, sync_chunk_vectors, vec_available


class MockEmbedClient:
    def __init__(self, vector: list[float]) -> None:
        self.vector = vector

    def embed(self, text: str, timeout: int = 120) -> bytes:
        return struct.pack(f"{len(self.vector)}f", *self.vector)


def _unit_vector(index: int, dim: int = EMBEDDING_DIM) -> list[float]:
    vector = [0.0] * dim
    vector[index] = 1.0
    return vector


@pytest.fixture
def vector_campaign(database_path, campaign) -> dict:
    with connection_at(database_path) as connection:
        if not vec_available(connection):
            pytest.skip("sqlite-vec extension unavailable")
        session_id = new_id("ses")
        connection.execute(
            """
            INSERT INTO sessions (id, campaign_id, session_date, label)
            VALUES (?, ?, '2026-06-08', 'Chapel')
            """,
            (session_id, campaign["id"]),
        )
        chunk_id = new_id("chk")
        connection.execute(
            """
            INSERT INTO content_chunks (
                id, campaign_id, session_id, source_type, source_id, chunk_index, chunk_text
            )
            VALUES (?, ?, ?, 'session_note', ?, 0, ?)
            """,
            (
                chunk_id,
                campaign["id"],
                session_id,
                "legacy-note",
                "The party found a silver key in the ruined chapel.",
            ),
        )
        embedding = struct.pack(f"{EMBEDDING_DIM}f", *_unit_vector(0))
        connection.execute(
            """
            INSERT INTO chunk_embedding (chunk_id, campaign_id, embedding, model_name)
            VALUES (?, ?, ?, 'test-model')
            """,
            (chunk_id, campaign["id"], embedding),
        )
        sync_chunk_vectors(connection)
    return campaign


def test_vector_knn_retrieval(vector_campaign) -> None:
    campaign_id = vector_campaign["id"]
    embed_client = MockEmbedClient(_unit_vector(0))
    with get_connection() as connection:
        hits = search_vectors(
            connection,
            campaign_id,
            "broken church key",
            embed_client=embed_client,
        )
    assert len(hits) == 1
    assert "silver key" in hits[0]["chunk_text"].lower()
    assert hits[0]["vec_score"] > 0


def test_sync_chunk_vectors(vector_campaign) -> None:
    with get_connection() as connection:
        count = sync_chunk_vectors(connection)
        stored = connection.execute("SELECT COUNT(*) FROM chunk_vectors").fetchone()[0]
    assert count >= 1
    assert stored == count
