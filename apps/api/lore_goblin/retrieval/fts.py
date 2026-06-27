from __future__ import annotations

import re
import sqlite3

from ..db import row_to_dict
from ..retrieval_legacy import STOP_WORDS

FTS_LIMIT = 5


def build_fts_query(query: str) -> str:
    tokens = re.findall(r"[a-z0-9']+", query.lower())
    terms = [token for token in tokens if token not in STOP_WORDS and len(token) > 1]
    if not terms:
        terms = tokens
    if not terms:
        return ""
    return " ".join(f'"{token}"' for token in terms)


def fts_bm25_to_score(rank: float) -> float:
    return 1.0 / (1.0 + abs(rank))


def search_entities(connection: sqlite3.Connection, campaign_id: str, query: str) -> list[dict]:
    fts_query = build_fts_query(query)
    if not fts_query:
        return []
    rows = connection.execute(
        """
        SELECT
            e.id AS record_id,
            'entity' AS result_type,
            e.name || CASE WHEN e.summary != '' THEN ': ' || e.summary ELSE '' END AS text,
            e.name,
            e.summary,
            e.entity_type,
            bm25(entities_fts) AS rank
        FROM entities_fts
        JOIN entity e ON e.id = entities_fts.entity_id
        WHERE entities_fts MATCH ?
          AND entities_fts.campaign_id = ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, campaign_id, FTS_LIMIT),
    ).fetchall()
    return [_row_to_hit(row) for row in rows]


def search_claims(connection: sqlite3.Connection, campaign_id: str, query: str) -> list[dict]:
    fts_query = build_fts_query(query)
    if not fts_query:
        return []
    rows = connection.execute(
        """
        SELECT
            c.id AS record_id,
            'claim' AS result_type,
            c.claim_text AS text,
            c.claim_text,
            c.canon_status,
            c.source_id,
            s.title AS source_title,
            s.source_type,
            bm25(claims_fts) AS rank
        FROM claims_fts
        JOIN claim c ON c.id = claims_fts.claim_id
        JOIN source s ON s.id = c.source_id
        WHERE claims_fts MATCH ?
          AND claims_fts.campaign_id = ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, campaign_id, FTS_LIMIT),
    ).fetchall()
    return [_row_to_hit(row) for row in rows]


def search_sources(connection: sqlite3.Connection, campaign_id: str, query: str) -> list[dict]:
    fts_query = build_fts_query(query)
    if not fts_query:
        return []
    rows = connection.execute(
        """
        SELECT
            s.id AS record_id,
            'source' AS result_type,
            s.title || ': ' || s.body AS text,
            s.title AS source_title,
            s.source_type,
            s.id AS source_id,
            bm25(sources_fts) AS rank
        FROM sources_fts
        JOIN source s ON s.id = sources_fts.source_id
        WHERE sources_fts MATCH ?
          AND sources_fts.campaign_id = ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, campaign_id, FTS_LIMIT),
    ).fetchall()
    return [_row_to_hit(row) for row in rows]


def search_fts(connection: sqlite3.Connection, campaign_id: str, query: str) -> list[dict]:
    hits: list[dict] = []
    hits.extend(search_entities(connection, campaign_id, query))
    hits.extend(search_claims(connection, campaign_id, query))
    hits.extend(search_sources(connection, campaign_id, query))
    return hits


def _row_to_hit(row: sqlite3.Row) -> dict:
    data = row_to_dict(row)
    data["fts_score"] = fts_bm25_to_score(float(data.pop("rank")))
    data["vec_score"] = 0.0
    return data
