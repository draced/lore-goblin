from __future__ import annotations

import logging
from typing import Callable

from ..chunking import chunk_note
from ..config import get_settings
from ..db import get_connection, new_id
from ..embeddings import EmbeddingClient
from ..ollama import OllamaClient
from ..repository import (
    clear_extraction_artifacts,
    ensure_source_chunks,
    get_model_settings,
    get_source,
    list_entities,
    merge_entity_aliases,
    persist_claims,
    persist_entity_mentions,
    persist_relationships,
    resolve_or_create_entities,
)
from .claims import extract_claims
from .entities import extract_entities, resolve_entities
from .importance import recompute_entity_importance
from .relationships import extract_relationships

logger = logging.getLogger(__name__)


def run_extraction_pipeline(source_id: str) -> None:
    source = get_source(source_id)
    if not source:
        raise ValueError(f"Source not found: {source_id}")

    campaign_id = source["campaign_id"]
    model_settings = get_model_settings(campaign_id)
    settings = get_settings()
    chat_client = OllamaClient(model_settings["base_url"], model_settings["chat_model"])
    embed_client = EmbeddingClient(settings.ollama_base_url, settings.ollama_embed_model)

    with get_connection() as connection:
        clear_extraction_artifacts(connection, source_id)
        ensure_source_chunks(connection, source)
        connection.commit()

    source = get_source(source_id)
    assert source is not None
    source_text = source["body"]

    _embed_source_chunks(source_id, campaign_id, embed_client)

    extracted = extract_entities(chat_client, source_text)
    existing = list_entities(campaign_id)
    resolutions = resolve_entities(chat_client, extracted, existing)

    entity_map = resolve_or_create_entities(
        campaign_id,
        source_id,
        source_text,
        extracted,
        resolutions,
    )

    resolved_entities = list_entities(campaign_id)
    resolved_for_source = [
        entity for entity in resolved_entities if entity["id"] in entity_map.values()
    ]
    claims = extract_claims(chat_client, source_text, resolved_for_source or resolved_entities)
    persist_claims(campaign_id, source_id, claims, entity_map)
    relationships = extract_relationships(claims)
    persist_relationships(campaign_id, source_id, relationships, entity_map)

    with get_connection() as connection:
        recompute_entity_importance(connection, campaign_id)


def _embed_source_chunks(source_id: str, campaign_id: str, embed_client: EmbeddingClient) -> None:
    settings = get_settings()
    with get_connection() as connection:
        chunks = connection.execute(
            """
            SELECT id, chunk_text
            FROM content_chunks
            WHERE source_id = ?
            ORDER BY chunk_index
            """,
            (source_id,),
        ).fetchall()
        for chunk in chunks:
            embedding = embed_client.embed(chunk["chunk_text"])
            connection.execute(
                """
                INSERT INTO chunk_embedding (chunk_id, campaign_id, embedding, model_name)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    embedding = excluded.embedding,
                    model_name = excluded.model_name,
                    created_at = CURRENT_TIMESTAMP
                """,
                (chunk["id"], campaign_id, embedding, settings.ollama_embed_model),
            )


def run_extraction_pipeline_with_clients(
    source_id: str,
    *,
    chat_client: OllamaClient,
    embed_client: EmbeddingClient | None = None,
    extract_entities_fn: Callable | None = None,
    resolve_entities_fn: Callable | None = None,
    extract_claims_fn: Callable | None = None,
) -> None:
    """Test hook allowing mocked Ollama clients."""
    source = get_source(source_id)
    if not source:
        raise ValueError(f"Source not found: {source_id}")

    campaign_id = source["campaign_id"]
    settings = get_settings()
    embed = embed_client or EmbeddingClient(settings.ollama_base_url, settings.ollama_embed_model)
    extract_fn = extract_entities_fn or extract_entities
    resolve_fn = resolve_entities_fn or resolve_entities
    claims_fn = extract_claims_fn or extract_claims

    with get_connection() as connection:
        clear_extraction_artifacts(connection, source_id)
        ensure_source_chunks(connection, source)
        connection.commit()

    source = get_source(source_id)
    assert source is not None
    source_text = source["body"]

    if embed_client is not None:
        _embed_source_chunks(source_id, campaign_id, embed)

    extracted = extract_fn(chat_client, source_text)
    existing = list_entities(campaign_id)
    resolutions = resolve_fn(chat_client, extracted, existing)

    entity_map = resolve_or_create_entities(
        campaign_id,
        source_id,
        source_text,
        extracted,
        resolutions,
    )

    resolved_entities = list_entities(campaign_id)
    resolved_for_source = [
        entity for entity in resolved_entities if entity["id"] in entity_map.values()
    ]
    claims = claims_fn(chat_client, source_text, resolved_for_source or resolved_entities)
    persist_claims(campaign_id, source_id, claims, entity_map)
    relationships = extract_relationships(claims)
    persist_relationships(campaign_id, source_id, relationships, entity_map)

    with get_connection() as connection:
        recompute_entity_importance(connection, campaign_id)
