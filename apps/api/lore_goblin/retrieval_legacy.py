import math
import re
from dataclasses import dataclass

from .db import get_connection, row_to_dict

STOP_WORDS = {
    "a",
    "an",
    "and",
    "about",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "did",
    "for",
    "from",
    "give",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "our",
    "please",
    "should",
    "tell",
    "that",
    "the",
    "to",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
}

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
class RetrievedChunk:
    chunk_id: str
    chunk_text: str
    score: float
    source_type: str
    source_id: str
    session_id: str
    session_date: str
    session_label: str | None
    author_display_name: str | None

    @property
    def citation_label(self) -> str:
        if self.session_label:
            return f"{self.session_date} - {self.session_label}"
        return self.session_date


def normalize_token(token: str) -> str:
    token = token.removesuffix("'s")
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9']+", text.lower())
    return [
        normalize_token(token)
        for token in tokens
        if token not in STOP_WORDS and len(token) > 1
    ]


def retrieve_chunks(campaign_id: str, query: str, limit: int = 4) -> list[RetrievedChunk]:
    query_terms = tokenize(query)
    if not query_terms:
        return []

    with get_connection() as connection:
        rows = load_campaign_chunks(connection, campaign_id)

    if is_only_broad_session_query(query_terms):
        scored = latest_session_chunks(rows)
    else:
        scored = score_chunks(rows, query_terms)
    if not scored and is_broad_session_query(query_terms):
        scored = latest_session_chunks(rows)

    scored.sort(key=lambda chunk: chunk.score, reverse=True)
    return scored[:limit]


def load_campaign_chunks(connection, campaign_id: str):
    return connection.execute(
        """
        SELECT
            cc.id AS chunk_id,
            cc.chunk_text,
            cc.source_type,
            cc.source_id,
            cc.session_id,
            s.session_date,
            s.label AS session_label,
            u.display_name AS author_display_name
        FROM content_chunks cc
        JOIN sessions s ON s.id = cc.session_id
        LEFT JOIN source src ON src.id = cc.source_id
        LEFT JOIN session_notes sn ON sn.id = COALESCE(src.legacy_note_id, cc.source_id)
        LEFT JOIN users u ON u.id = COALESCE(src.author_user_id, sn.author_user_id)
        WHERE cc.campaign_id = ?
        """,
        (campaign_id,),
    ).fetchall()


def score_chunks(rows, query_terms: list[str]) -> list[RetrievedChunk]:
    scored: list[RetrievedChunk] = []
    query_set = set(query_terms)
    for row in rows:
        row_dict = row_to_dict(row)
        chunk_terms = tokenize(row_dict["chunk_text"])
        if not chunk_terms:
            continue
        chunk_set = set(chunk_terms)
        overlap = query_set.intersection(chunk_set)
        if not overlap:
            continue
        term_frequency = sum(chunk_terms.count(term) for term in overlap)
        coverage = len(overlap) / len(query_set)
        density = term_frequency / math.sqrt(len(chunk_terms))
        label_bonus = score_session_label(row_dict, query_set)
        score = coverage + density + label_bonus
        scored.append(RetrievedChunk(score=score, **row_dict))
    return scored


def score_session_label(row_dict: dict, query_set: set[str]) -> float:
    label_text = " ".join(
        value
        for value in [row_dict["session_date"], row_dict["session_label"]]
        if value
    )
    label_terms = set(tokenize(label_text))
    if not label_terms:
        return 0.0
    return len(query_set.intersection(label_terms)) * 0.35


def is_broad_session_query(query_terms: list[str]) -> bool:
    return bool(set(query_terms).intersection(BROAD_SESSION_TERMS))


def is_only_broad_session_query(query_terms: list[str]) -> bool:
    query_set = set(query_terms)
    return bool(query_set) and query_set.issubset(BROAD_SESSION_TERMS)


def latest_session_chunks(rows) -> list[RetrievedChunk]:
    if not rows:
        return []
    latest_session_date = max(row["session_date"] for row in rows)
    latest_rows = [row for row in rows if row["session_date"] == latest_session_date]
    return [
        RetrievedChunk(score=0.1, **row_to_dict(row))
        for row in latest_rows
    ]
