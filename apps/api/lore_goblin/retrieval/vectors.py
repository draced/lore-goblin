from __future__ import annotations

import logging
import sqlite3
import struct

from ..config import get_settings
from ..db import row_to_dict
from ..embeddings import EmbeddingClient

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768
VECTOR_LIMIT = 5


def vec_available(connection: sqlite3.Connection) -> bool:
    try:
        connection.execute("SELECT vec_version()").fetchone()
        return True
    except sqlite3.OperationalError:
        return False


def sync_chunk_vectors(connection: sqlite3.Connection) -> int:
    if not vec_available(connection):
        return 0
    connection.execute("DELETE FROM chunk_vectors")
    rows = connection.execute(
        "SELECT chunk_id, campaign_id, embedding FROM chunk_embedding"
    ).fetchall()
    for row in rows:
        connection.execute(
            """
            INSERT INTO chunk_vectors(chunk_id, campaign_id, embedding)
            VALUES (?, ?, ?)
            """,
            (row["chunk_id"], row["campaign_id"], row["embedding"]),
        )
    return len(rows)


def embed_query(query: str, embed_client: EmbeddingClient | None = None) -> bytes | None:
    settings = get_settings()
    client = embed_client or EmbeddingClient(settings.ollama_base_url, settings.ollama_embed_model)
    try:
        return client.embed(query)
    except Exception as exc:
        logger.warning("Query embedding unavailable: %s", exc)
        return None


def embedding_dimension(embedding: bytes) -> int:
    return len(embedding) // struct.calcsize("f")


def search_vectors(
    connection: sqlite3.Connection,
    campaign_id: str,
    query: str,
    *,
    embed_client: EmbeddingClient | None = None,
) -> list[dict]:
    if not vec_available(connection):
        return []
    query_embedding = embed_query(query, embed_client)
    if not query_embedding:
        return []
    if embedding_dimension(query_embedding) != EMBEDDING_DIM:
        logger.warning(
            "Query embedding dimension %s does not match index dimension %s",
            embedding_dimension(query_embedding),
            EMBEDDING_DIM,
        )
        return []

    rows = connection.execute(
        """
        SELECT
            cv.chunk_id AS record_id,
            'chunk' AS result_type,
            cc.chunk_text AS text,
            cc.chunk_text,
            cc.source_id,
            s.title AS source_title,
            s.source_type,
            cv.distance
        FROM chunk_vectors cv
        JOIN content_chunks cc ON cc.id = cv.chunk_id
        LEFT JOIN source s ON s.id = cc.source_id
        WHERE cv.campaign_id = ?
          AND cv.embedding MATCH ?
          AND k = ?
        ORDER BY cv.distance
        """,
        (campaign_id, query_embedding, VECTOR_LIMIT),
    ).fetchall()

    hits: list[dict] = []
    for row in rows:
        data = row_to_dict(row)
        distance = float(data.pop("distance"))
        data["vec_score"] = 1.0 / (1.0 + distance)
        data["fts_score"] = 0.0
        hits.append(data)
    return hits
