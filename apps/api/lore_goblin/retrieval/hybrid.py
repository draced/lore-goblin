from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import sqlite3

from ..db import get_connection
from ..embeddings import EmbeddingClient
from .fts import search_fts
from .vectors import search_vectors

logger = logging.getLogger(__name__)

MERGED_LIMIT = 8
CLAIM_BONUS = 2.0
IMPORTANCE_WEIGHT = 0.1
RECENT_SESSION_BONUS = 0.5

BROAD_SESSION_TERMS = {
    "campaign",
    "happen",
    "lore",
    "recap",
    "summarize",
    "summary",
    "session",
    "story",
    "last",
    "recent",
    "latest",
}


@dataclass(frozen=True)
class RetrievedItem:
    result_type: str
    record_id: str
    text: str
    score: float
    source_id: str | None = None
    source_title: str | None = None
    source_type: str | None = None
    claim_text: str | None = None
    canon_status: str | None = None
    chunk_text: str | None = None
    entity_name: str | None = None
    entity_type: str | None = None

    @property
    def dedupe_key(self) -> str:
        return f"{self.result_type}:{self.record_id}"


def hybrid_retrieve(
    campaign_id: str,
    query: str,
    *,
    limit: int = MERGED_LIMIT,
    embed_client: EmbeddingClient | None = None,
    connection: sqlite3.Connection | None = None,
) -> list[RetrievedItem]:
    if connection is None:
        with get_connection() as managed:
            return hybrid_retrieve(
                campaign_id,
                query,
                limit=limit,
                embed_client=embed_client,
                connection=managed,
            )

    fts_hits = search_fts(connection, campaign_id, query)
    try:
        vector_hits = search_vectors(
            connection,
            campaign_id,
            query,
            embed_client=embed_client,
        )
    except sqlite3.OperationalError as exc:
        logger.warning("Vector search unavailable, using FTS-only fallback: %s", exc)
        vector_hits = []

    merged = merge_hits(connection, campaign_id, query, fts_hits, vector_hits)
    merged.sort(key=lambda item: item.score, reverse=True)
    return merged[:limit]


def merge_hits(
    connection: sqlite3.Connection,
    campaign_id: str,
    query: str,
    fts_hits: list[dict],
    vector_hits: list[dict],
) -> list[RetrievedItem]:
    by_key: dict[str, RetrievedItem] = {}
    for hit in fts_hits + vector_hits:
        item = _hit_to_item(hit)
        item = _apply_importance(connection, item)
        item = _apply_session_boost(connection, campaign_id, query, item)
        existing = by_key.get(item.dedupe_key)
        if existing:
            item = _combine_items(existing, item)
        by_key[item.dedupe_key] = item

    items = list(by_key.values())
    items = _prefer_claims_over_chunks(items)
    return items


def _hit_to_item(hit: dict) -> RetrievedItem:
    fts_score = float(hit.get("fts_score", 0.0))
    vec_score = float(hit.get("vec_score", 0.0))
    result_type = hit["result_type"]
    claim_bonus = CLAIM_BONUS if result_type == "claim" else 0.0
    score = fts_score + vec_score + claim_bonus
    return RetrievedItem(
        result_type=result_type,
        record_id=hit["record_id"],
        text=hit["text"],
        score=score,
        source_id=hit.get("source_id"),
        source_title=hit.get("source_title"),
        source_type=hit.get("source_type"),
        claim_text=hit.get("claim_text"),
        canon_status=hit.get("canon_status"),
        chunk_text=hit.get("chunk_text"),
        entity_name=hit.get("name"),
        entity_type=hit.get("entity_type"),
    )


def _combine_items(left: RetrievedItem, right: RetrievedItem) -> RetrievedItem:
    return RetrievedItem(
        result_type=left.result_type,
        record_id=left.record_id,
        text=left.text or right.text,
        score=max(left.score, right.score),
        source_id=left.source_id or right.source_id,
        source_title=left.source_title or right.source_title,
        source_type=left.source_type or right.source_type,
        claim_text=left.claim_text or right.claim_text,
        canon_status=left.canon_status or right.canon_status,
        chunk_text=left.chunk_text or right.chunk_text,
        entity_name=left.entity_name or right.entity_name,
        entity_type=left.entity_type or right.entity_type,
    )


def _apply_importance(connection: sqlite3.Connection, item: RetrievedItem) -> RetrievedItem:
    if item.result_type != "entity":
        return item
    row = connection.execute(
        "SELECT importance_score FROM entity_importance WHERE entity_id = ?",
        (item.record_id,),
    ).fetchone()
    if not row:
        return item
    bonus = float(row["importance_score"]) * IMPORTANCE_WEIGHT
    return RetrievedItem(**{**item.__dict__, "score": item.score + bonus})


def _apply_session_boost(
    connection: sqlite3.Connection,
    campaign_id: str,
    query: str,
    item: RetrievedItem,
) -> RetrievedItem:
    if not _is_broad_session_query(query):
        return item
    if not item.source_id:
        return item
    latest = connection.execute(
        """
        SELECT s.session_date
        FROM source src
        LEFT JOIN sessions s ON s.id = src.session_id
        WHERE src.campaign_id = ?
        ORDER BY s.session_date DESC
        LIMIT 1
        """,
        (campaign_id,),
    ).fetchone()
    if not latest or not latest["session_date"]:
        return item
    source = connection.execute(
        """
        SELECT s.session_date
        FROM source src
        LEFT JOIN sessions s ON s.id = src.session_id
        WHERE src.id = ?
        """,
        (item.source_id,),
    ).fetchone()
    if source and source["session_date"] == latest["session_date"]:
        return RetrievedItem(**{**item.__dict__, "score": item.score + RECENT_SESSION_BONUS})
    return item


def _prefer_claims_over_chunks(items: list[RetrievedItem]) -> list[RetrievedItem]:
    claim_sources = {item.source_id for item in items if item.result_type == "claim" and item.source_id}
    if not claim_sources:
        return items
    filtered: list[RetrievedItem] = []
    for item in items:
        if item.result_type == "chunk" and item.source_id in claim_sources:
            continue
        filtered.append(item)
    return filtered


def _is_broad_session_query(query: str) -> bool:
    tokens = set(re.findall(r"[a-z0-9']+", query.lower()))
    return bool(tokens.intersection(BROAD_SESSION_TERMS))
