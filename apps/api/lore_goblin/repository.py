import json
import sqlite3

from .chunking import chunk_note
from .config import get_settings
from .db import get_connection, new_id, row_to_dict
from .extraction.entities import find_mention_span, normalize_entity_type
from .extraction.schemas import ExtractedClaim, ExtractedEntity, ResolutionResult
from .models import ENTITY_TYPES, SOURCE_TYPES, EntityType, SourceType


def _enqueue_extraction(source_id: str, campaign_id: str) -> None:
    from .extraction.jobs import enqueue_extraction_job

    enqueue_extraction_job(source_id, campaign_id)


def ensure_user(display_name: str, discord_user_id: str | None = None) -> dict:
    with get_connection() as connection:
        if discord_user_id:
            existing = connection.execute(
                "SELECT * FROM users WHERE discord_user_id = ?",
                (discord_user_id,),
            ).fetchone()
            if existing:
                return row_to_dict(existing)

        user_id = new_id("usr")
        connection.execute(
            """
            INSERT INTO users (id, display_name, discord_user_id)
            VALUES (?, ?, ?)
            """,
            (user_id, display_name, discord_user_id),
        )
        return {"id": user_id, "display_name": display_name, "discord_user_id": discord_user_id}


def create_campaign(name: str, tone: str, owner_display_name: str) -> dict:
    settings = get_settings()
    owner = ensure_user(owner_display_name)
    campaign_id = new_id("cmp")
    member_id = new_id("mem")
    model_settings_id = new_id("mdl")
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO campaigns (id, name, tone) VALUES (?, ?, ?)",
            (campaign_id, name, tone),
        )
        connection.execute(
            """
            INSERT INTO campaign_members (id, campaign_id, user_id, role)
            VALUES (?, ?, ?, 'owner')
            """,
            (member_id, campaign_id, owner["id"]),
        )
        connection.execute(
            """
            INSERT INTO model_settings (id, campaign_id, provider, chat_model, base_url)
            VALUES (?, ?, 'ollama', ?, ?)
            """,
            (model_settings_id, campaign_id, settings.ollama_chat_model, settings.ollama_base_url),
        )
        campaign = connection.execute(
            "SELECT * FROM campaigns WHERE id = ?",
            (campaign_id,),
        ).fetchone()
    return row_to_dict(campaign)


def list_campaigns() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    return [row_to_dict(row) for row in rows]


def get_campaign(campaign_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    return row_to_dict(row) if row else None


def _get_campaign_owner_user_id(connection, campaign_id: str) -> str:
    row = connection.execute(
        """
        SELECT user_id
        FROM campaign_members
        WHERE campaign_id = ? AND role = 'owner'
        LIMIT 1
        """,
        (campaign_id,),
    ).fetchone()
    if not row:
        raise ValueError("Campaign owner not found")
    return row["user_id"]


def create_source(
    campaign_id: str,
    source_type: str,
    title: str,
    body: str,
    author_user_id: str,
    session_id: str | None = None,
    entity_id: str | None = None,
    legacy_note_id: str | None = None,
) -> dict:
    normalized_title = title.strip()
    normalized_body = body.strip()
    if not normalized_title:
        raise ValueError("Source title is required")
    if not normalized_body:
        raise ValueError("Source body is required")
    if source_type not in SOURCE_TYPES:
        raise ValueError("Invalid source type")

    source_id = new_id("src")
    with get_connection() as connection:
        campaign = connection.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        if not campaign:
            raise ValueError("Campaign not found")
        connection.execute(
            """
            INSERT INTO source (
                id, campaign_id, source_type, title, body, author_user_id,
                session_id, entity_id, legacy_note_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                campaign_id,
                source_type,
                normalized_title,
                normalized_body,
                author_user_id,
                session_id,
                entity_id,
                legacy_note_id,
            ),
        )
        row = connection.execute("SELECT * FROM source WHERE id = ?", (source_id,)).fetchone()
    source = row_to_dict(row)
    _enqueue_extraction(source_id, campaign_id)
    return source


def get_source(source_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM source WHERE id = ?", (source_id,)).fetchone()
    return row_to_dict(row) if row else None


def list_sources(campaign_id: str, source_type: str | None = None) -> list[dict]:
    query = """
        SELECT *
        FROM source
        WHERE campaign_id = ?
    """
    params: list[str] = [campaign_id]
    if source_type:
        if source_type not in SOURCE_TYPES:
            raise ValueError("Invalid source type")
        query += " AND source_type = ?"
        params.append(source_type)
    query += " ORDER BY created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [row_to_dict(row) for row in rows]


def create_entity(
    campaign_id: str,
    entity_type: str,
    name: str,
    aliases: list[str] | None = None,
    summary: str = "",
    legacy_pc_id: str | None = None,
) -> dict:
    normalized_name = name.strip()
    normalized_summary = summary.strip()
    alias_list = aliases or []
    if not normalized_name:
        raise ValueError("Entity name is required")
    if entity_type not in ENTITY_TYPES:
        raise ValueError("Invalid entity type")
    if not isinstance(alias_list, list) or not all(isinstance(alias, str) for alias in alias_list):
        raise ValueError("Aliases must be a list of strings")

    entity_id = legacy_pc_id or new_id("ent")
    with get_connection() as connection:
        campaign = connection.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        if not campaign:
            raise ValueError("Campaign not found")
        connection.execute(
            """
            INSERT INTO entity (
                id, campaign_id, entity_type, name, aliases_json, summary, legacy_pc_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_id,
                campaign_id,
                entity_type,
                normalized_name,
                json.dumps(alias_list),
                normalized_summary,
                legacy_pc_id,
            ),
        )
        row = connection.execute("SELECT * FROM entity WHERE id = ?", (entity_id,)).fetchone()
    return row_to_dict(row)


def list_entities(campaign_id: str, entity_type: str | None = None) -> list[dict]:
    query = """
        SELECT *
        FROM entity
        WHERE campaign_id = ?
    """
    params: list[str] = [campaign_id]
    if entity_type:
        if entity_type not in ENTITY_TYPES:
            raise ValueError("Invalid entity type")
        query += " AND entity_type = ?"
        params.append(entity_type)
    query += " ORDER BY name COLLATE NOCASE, created_at"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [row_to_dict(row) for row in rows]


def create_player_character(campaign_id: str, name: str, notes: str) -> dict:
    normalized_name = name.strip()
    normalized_notes = notes.strip()
    if not normalized_name:
        raise ValueError("Player character name is required")
    if not normalized_notes:
        raise ValueError("Player character notes are required")

    character_id = new_id("pc")
    with get_connection() as connection:
        campaign = connection.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        if not campaign:
            raise ValueError("Campaign not found")

        owner_user_id = _get_campaign_owner_user_id(connection, campaign_id)

        connection.execute(
            """
            INSERT INTO player_characters (id, campaign_id, name, notes)
            VALUES (?, ?, ?, ?)
            """,
            (character_id, campaign_id, normalized_name, normalized_notes),
        )

        connection.execute(
            """
            INSERT INTO entity (
                id, campaign_id, entity_type, name, aliases_json, summary, legacy_pc_id
            )
            VALUES (?, ?, ?, ?, '[]', ?, ?)
            """,
            (character_id, campaign_id, EntityType.PC, normalized_name, normalized_notes, character_id),
        )

        source_id = new_id("src")
        connection.execute(
            """
            INSERT INTO source (
                id, campaign_id, source_type, title, body, author_user_id, entity_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                campaign_id,
                SourceType.PLAYER_CHARACTER_DESC,
                normalized_name,
                normalized_notes,
                owner_user_id,
                character_id,
            ),
        )

        row = connection.execute(
            "SELECT * FROM player_characters WHERE id = ?",
            (character_id,),
        ).fetchone()
    _enqueue_extraction(source_id, campaign_id)
    return row_to_dict(row)


def list_player_characters(campaign_id: str) -> list[dict]:
    with get_connection() as connection:
        entity_rows = connection.execute(
            """
            SELECT
                e.id,
                e.campaign_id,
                e.name,
                e.summary AS notes,
                e.created_at,
                e.updated_at
            FROM entity e
            WHERE e.campaign_id = ?
              AND e.entity_type = ?
            ORDER BY e.name COLLATE NOCASE, e.created_at
            """,
            (campaign_id, EntityType.PC),
        ).fetchall()
        if entity_rows:
            return [row_to_dict(row) for row in entity_rows]

        rows = connection.execute(
            """
            SELECT *
            FROM player_characters
            WHERE campaign_id = ?
            ORDER BY name COLLATE NOCASE, created_at
            """,
            (campaign_id,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def link_discord_guild(campaign_id: str, guild_id: str) -> dict:
    link_id = new_id("dgl")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO discord_guild_links (id, campaign_id, guild_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET campaign_id = excluded.campaign_id
            """,
            (link_id, campaign_id, guild_id),
        )
        row = connection.execute(
            "SELECT * FROM discord_guild_links WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
    return row_to_dict(row)


def get_campaign_for_guild(guild_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT c.*
            FROM campaigns c
            JOIN discord_guild_links dgl ON dgl.campaign_id = c.id
            WHERE dgl.guild_id = ?
            """,
            (guild_id,),
        ).fetchone()
    return row_to_dict(row) if row else None


def _session_title(session_date: str, label: str | None) -> str:
    if label and label.strip():
        return label.strip()
    return session_date


def add_session_note(
    campaign_id: str,
    session_date: str,
    label: str | None,
    raw_content: str,
    author_display_name: str,
    discord_user_id: str | None = None,
) -> dict:
    author = ensure_user(author_display_name, discord_user_id)
    session_id = new_id("ses")
    note_id = new_id("snt")
    normalized_label = label.strip() if label and label.strip() else None

    with get_connection() as connection:
        existing_session = connection.execute(
            """
            SELECT * FROM sessions
            WHERE campaign_id = ?
              AND session_date = ?
              AND COALESCE(label, '') = COALESCE(?, '')
            """,
            (campaign_id, session_date, normalized_label),
        ).fetchone()
        if existing_session:
            session = row_to_dict(existing_session)
            session_id = session["id"]
        else:
            connection.execute(
                """
                INSERT INTO sessions (id, campaign_id, session_date, label)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, campaign_id, session_date, normalized_label),
            )
            session = {
                "id": session_id,
                "campaign_id": campaign_id,
                "session_date": session_date,
                "label": normalized_label,
            }

        source_id = new_id("src")
        source_title = _session_title(session_date, normalized_label)
        connection.execute(
            """
            INSERT INTO source (
                id, campaign_id, source_type, title, body, author_user_id,
                session_id, legacy_note_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                campaign_id,
                SourceType.SESSION_NOTE,
                source_title,
                raw_content,
                author["id"],
                session_id,
                note_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO session_notes (id, session_id, campaign_id, author_user_id, raw_content)
            VALUES (?, ?, ?, ?, ?)
            """,
            (note_id, session_id, campaign_id, author["id"], raw_content),
        )

        chunks = chunk_note(raw_content)
        for index, chunk in enumerate(chunks):
            connection.execute(
                """
                INSERT INTO content_chunks (
                    id, campaign_id, session_id, source_type, source_id, chunk_index, chunk_text
                )
                VALUES (?, ?, ?, 'session_note', ?, ?, ?)
                """,
                (new_id("chk"), campaign_id, session_id, source_id, index, chunk),
            )

    _enqueue_extraction(source_id, campaign_id)
    return {
        "session": session,
        "note": {
            "id": note_id,
            "session_id": session_id,
            "campaign_id": campaign_id,
            "author_user_id": author["id"],
        },
        "chunk_count": len(chunks),
    }


def _ensure_chunk_session(connection: sqlite3.Connection, source: dict) -> str:
    if source.get("session_id"):
        return source["session_id"]
    existing = connection.execute(
        """
        SELECT id
        FROM sessions
        WHERE campaign_id = ? AND session_date = '0000-01-01' AND label = 'Unassigned'
        """,
        (source["campaign_id"],),
    ).fetchone()
    if existing:
        return existing["id"]
    session_id = new_id("ses")
    connection.execute(
        """
        INSERT INTO sessions (id, campaign_id, session_date, label)
        VALUES (?, ?, '0000-01-01', 'Unassigned')
        """,
        (session_id, source["campaign_id"]),
    )
    return session_id


def ensure_source_chunks(connection: sqlite3.Connection, source: dict) -> None:
    existing = connection.execute(
        "SELECT COUNT(*) FROM content_chunks WHERE source_id = ?",
        (source["id"],),
    ).fetchone()[0]
    if existing:
        return
    session_id = _ensure_chunk_session(connection, source)
    source_type = "session_note" if source["source_type"] == SourceType.SESSION_NOTE else "wiki_page"
    chunks = chunk_note(source["body"])
    for index, chunk in enumerate(chunks):
        connection.execute(
            """
            INSERT INTO content_chunks (
                id, campaign_id, session_id, source_type, source_id, chunk_index, chunk_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("chk"),
                source["campaign_id"],
                session_id,
                source_type,
                source["id"],
                index,
                chunk,
            ),
        )


def clear_extraction_artifacts(connection: sqlite3.Connection, source_id: str) -> None:
    connection.execute("DELETE FROM entity_mention WHERE source_id = ?", (source_id,))
    connection.execute("DELETE FROM claim WHERE source_id = ?", (source_id,))
    connection.execute("DELETE FROM relationship WHERE source_id = ?", (source_id,))


def merge_entity_aliases(connection: sqlite3.Connection, entity_id: str, aliases: list[str]) -> None:
    row = connection.execute(
        "SELECT aliases_json FROM entity WHERE id = ?",
        (entity_id,),
    ).fetchone()
    if not row:
        return
    existing_aliases = json.loads(row["aliases_json"] or "[]")
    canonical = connection.execute(
        "SELECT name FROM entity WHERE id = ?",
        (entity_id,),
    ).fetchone()["name"]
    merged: list[str] = []
    seen = {canonical.lower()}
    for alias in [*existing_aliases, *aliases]:
        normalized = alias.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(normalized)
    connection.execute(
        """
        UPDATE entity
        SET aliases_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (json.dumps(merged), entity_id),
    )


def persist_entity_mentions(
    connection: sqlite3.Connection,
    source_id: str,
    source_text: str,
    entity_id: str,
    names: list[str],
) -> None:
    for name in names:
        span = find_mention_span(source_text, name)
        if span is None:
            continue
        start, end = span
        connection.execute(
            """
            INSERT INTO entity_mention (
                id, source_id, entity_id, mention_text, start_offset, end_offset
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_id("men"), source_id, entity_id, name, start, end),
        )


def resolve_or_create_entities(
    campaign_id: str,
    source_id: str,
    source_text: str,
    extracted: list[ExtractedEntity],
    resolutions: list[tuple[ExtractedEntity, ResolutionResult]],
) -> dict[str, str]:
    name_to_id: dict[str, str] = {}
    with get_connection() as connection:
        for entity, resolution in resolutions:
            aliases = list({entity.name, *entity.aliases})
            if resolution.matched_entity_id:
                entity_id = resolution.matched_entity_id
                merge_entity_aliases(connection, entity_id, aliases)
            else:
                entity_id = new_id("ent")
                connection.execute(
                    """
                    INSERT INTO entity (
                        id, campaign_id, entity_type, name, aliases_json, summary
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entity_id,
                        campaign_id,
                        normalize_entity_type(entity.type),
                        entity.name.strip(),
                        json.dumps([alias for alias in entity.aliases if alias.strip()]),
                        entity.short_description.strip(),
                    ),
                )
            name_to_id[entity.name.strip().lower()] = entity_id
            for alias in entity.aliases:
                if alias.strip():
                    name_to_id[alias.strip().lower()] = entity_id
            persist_entity_mentions(
                connection,
                source_id,
                source_text,
                entity_id,
                aliases,
            )
    return name_to_id


def _lookup_entity_id(name_to_id: dict[str, str], name: str | None) -> str | None:
    if not name:
        return None
    return name_to_id.get(name.strip().lower())


def persist_claims(
    campaign_id: str,
    source_id: str,
    claims: list[ExtractedClaim],
    entity_map: dict[str, str],
) -> None:
    with get_connection() as connection:
        for claim in claims:
            subject_id = _lookup_entity_id(entity_map, claim.subject_entity_name)
            if not subject_id:
                continue
            object_id = _lookup_entity_id(entity_map, claim.object_entity_name)
            connection.execute(
                """
                INSERT INTO claim (
                    id, campaign_id, claim_text, subject_entity_id, predicate,
                    object_entity_id, canon_status, source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("clm"),
                    campaign_id,
                    claim.claim_text.strip(),
                    subject_id,
                    claim.predicate.strip(),
                    object_id,
                    claim.canon_status,
                    source_id,
                ),
            )


def persist_relationships(
    campaign_id: str,
    source_id: str,
    relationships: list[dict],
    entity_map: dict[str, str],
) -> None:
    with get_connection() as connection:
        for relationship in relationships:
            source_entity_id = _lookup_entity_id(entity_map, relationship["source_entity_name"])
            target_entity_id = _lookup_entity_id(entity_map, relationship["target_entity_name"])
            if not source_entity_id or not target_entity_id:
                continue
            connection.execute(
                """
                INSERT INTO relationship (
                    id, campaign_id, source_entity_id, target_entity_id,
                    relationship_type, description, source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("rel"),
                    campaign_id,
                    source_entity_id,
                    target_entity_id,
                    relationship["relationship_type"],
                    relationship.get("description", ""),
                    source_id,
                ),
            )


def list_sessions(campaign_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                s.*,
                COUNT(sn.id) AS note_count
            FROM sessions s
            LEFT JOIN session_notes sn ON sn.session_id = s.id
            WHERE s.campaign_id = ?
            GROUP BY s.id
            ORDER BY s.session_date DESC, s.created_at DESC
            """,
            (campaign_id,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_model_settings(campaign_id: str) -> dict:
    settings = get_settings()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM model_settings WHERE campaign_id = ?",
            (campaign_id,),
        ).fetchone()
    if row:
        return row_to_dict(row)
    return {
        "provider": "ollama",
        "chat_model": settings.ollama_chat_model,
        "base_url": settings.ollama_base_url,
    }
