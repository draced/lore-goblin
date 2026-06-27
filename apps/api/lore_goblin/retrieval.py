"""Deprecated lexical retrieval — use lore_goblin.retrieval.hybrid instead."""

from __future__ import annotations

import warnings

from .retrieval.hybrid import RetrievedItem, hybrid_retrieve

__all__ = ["RetrievedChunk", "RetrievedItem", "hybrid_retrieve", "retrieve_chunks"]


# Re-export legacy types for backward compatibility
from .retrieval_legacy import (  # noqa: E402
    RetrievedChunk,
    retrieve_chunks as _legacy_retrieve_chunks,
)


def retrieve_chunks(campaign_id: str, query: str, limit: int = 4) -> list[RetrievedChunk]:
    warnings.warn(
        "retrieve_chunks is deprecated; use lore_goblin.retrieval.hybrid_retrieve instead",
        DeprecationWarning,
        stacklevel=2,
    )
    items = hybrid_retrieve(campaign_id, query, limit=limit)
    if items:
        return [_item_to_chunk(item) for item in items if item.result_type == "chunk"]
    return _legacy_retrieve_chunks(campaign_id, query, limit=limit)


def _item_to_chunk(item: RetrievedItem) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=item.record_id,
        chunk_text=item.chunk_text or item.text,
        score=item.score,
        source_type=item.source_type or "session_note",
        source_id=item.source_id or "",
        session_id="",
        session_date=item.source_title or "",
        session_label=None,
        author_display_name=None,
    )
