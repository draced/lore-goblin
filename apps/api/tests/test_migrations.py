from __future__ import annotations

import sqlite3
from pathlib import Path

from lore_goblin.db import initialize_database_at
from lore_goblin.migrations.runner import (
    apply_pending_migrations,
    count_pending_legacy_entities,
    count_pending_legacy_sources,
    get_schema_version,
    run_migration,
)
from tests.conftest import seed_legacy_player_character, seed_legacy_session_note


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def test_migration_applies_on_fresh_database(database_path: Path) -> None:
    initialize_database_at(database_path)
    with _connect(database_path) as connection:
        version = get_schema_version(connection)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert version == 3
    assert "source" in tables
    assert "entity" in tables
    assert "claim" in tables


def test_migration_is_idempotent(database_path: Path) -> None:
    initialize_database_at(database_path)
    with _connect(database_path) as connection:
        first_version = get_schema_version(connection)
        applied = apply_pending_migrations(connection)
        connection.commit()
        second_version = get_schema_version(connection)
    assert first_version == 3
    assert applied == []
    assert second_version == 3


def test_dry_run_reports_pending_counts(legacy_database_path: Path, legacy_campaign: dict) -> None:
    with _connect(legacy_database_path) as connection:
        seed_legacy_session_note(
            connection,
            campaign_id=legacy_campaign["id"],
            user_id=legacy_campaign["owner_user_id"],
        )
        seed_legacy_player_character(connection, campaign_id=legacy_campaign["id"])
        result = run_migration(connection, dry_run=True)

    assert result.dry_run is True
    assert result.sources_created == 2
    assert result.entities_created == 1
    assert result.chunks_linked == 1
    assert result.errors == []


def test_backfill_counts_after_migration(legacy_database_path: Path, legacy_campaign: dict) -> None:
    with _connect(legacy_database_path) as connection:
        seed_legacy_session_note(
            connection,
            campaign_id=legacy_campaign["id"],
            user_id=legacy_campaign["owner_user_id"],
        )
        seed_legacy_player_character(connection, campaign_id=legacy_campaign["id"])
        pending_sources = count_pending_legacy_sources(connection)
        pending_entities = count_pending_legacy_entities(connection)
        result = run_migration(connection, dry_run=False)
        source_count = connection.execute("SELECT COUNT(*) FROM source").fetchone()[0]
        entity_count = connection.execute("SELECT COUNT(*) FROM entity").fetchone()[0]
        chunk = connection.execute(
            "SELECT source_id FROM content_chunks WHERE id = 'chk_legacy001'"
        ).fetchone()

    assert pending_sources == 1
    assert pending_entities == 1
    assert result.sources_created == 2
    assert result.entities_created == 1
    assert source_count == 2
    assert entity_count == 1
    assert chunk["source_id"].startswith("src_")


def test_legacy_session_notes_migrate_to_sources(legacy_database_path: Path, legacy_campaign: dict) -> None:
    with _connect(legacy_database_path) as connection:
        seeded = seed_legacy_session_note(
            connection,
            campaign_id=legacy_campaign["id"],
            user_id=legacy_campaign["owner_user_id"],
        )
        run_migration(connection, dry_run=False)
        source = connection.execute(
            "SELECT * FROM source WHERE legacy_note_id = ?",
            (seeded["note_id"],),
        ).fetchone()

    assert source is not None
    assert source["source_type"] == "SESSION_NOTE"
    assert source["body"] == "The party found a silver key."


def test_legacy_player_characters_migrate_to_entities(legacy_database_path: Path, legacy_campaign: dict) -> None:
    with _connect(legacy_database_path) as connection:
        seeded = seed_legacy_player_character(connection, campaign_id=legacy_campaign["id"])
        run_migration(connection, dry_run=False)
        entity = connection.execute(
            "SELECT * FROM entity WHERE legacy_pc_id = ?",
            (seeded["id"],),
        ).fetchone()
        source = connection.execute(
            """
            SELECT * FROM source
            WHERE entity_id = ? AND source_type = 'PLAYER_CHARACTER_DESC'
            """,
            (seeded["id"],),
        ).fetchone()

    assert entity is not None
    assert entity["entity_type"] == "PC"
    assert entity["name"] == "Nyra"
    assert source is not None


def test_re_run_migration_creates_zero_new_rows(legacy_database_path: Path, legacy_campaign: dict) -> None:
    with _connect(legacy_database_path) as connection:
        seed_legacy_session_note(
            connection,
            campaign_id=legacy_campaign["id"],
            user_id=legacy_campaign["owner_user_id"],
        )
        run_migration(connection, dry_run=False)
        second = run_migration(connection, dry_run=True)

    assert second.sources_created == 0
    assert second.entities_created == 0
    assert second.chunks_linked == 0
