from .chunking import chunk_note
from .config import get_settings
from .db import get_connection, new_id, row_to_dict


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
        connection.execute(
            """
            INSERT INTO player_characters (id, campaign_id, name, notes)
            VALUES (?, ?, ?, ?)
            """,
            (character_id, campaign_id, normalized_name, normalized_notes),
        )
        row = connection.execute(
            "SELECT * FROM player_characters WHERE id = ?",
            (character_id,),
        ).fetchone()
    return row_to_dict(row)


def list_player_characters(campaign_id: str) -> list[dict]:
    with get_connection() as connection:
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
                (new_id("chk"), campaign_id, session_id, note_id, index, chunk),
            )

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

