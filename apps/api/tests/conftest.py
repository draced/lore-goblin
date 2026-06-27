from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lore_goblin.config import Settings, get_settings
from lore_goblin.db import connection_at, initialize_database_at
from lore_goblin.main import create_app


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "test.sqlite3"


@pytest.fixture
def legacy_database_path(tmp_path: Path) -> Path:
    path = tmp_path / "legacy.sqlite3"
    schema_path = Path(__file__).resolve().parents[1] / "lore_goblin" / "schema.sql"
    with sqlite3.connect(path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.commit()
    return path


@pytest.fixture
def migrated_database_path(database_path: Path) -> Path:
    initialize_database_at(database_path)
    return database_path


@pytest.fixture
def test_settings(database_path: Path) -> Settings:
    return Settings(
        database_path=str(database_path),
        ollama_base_url="http://localhost:11434",
        ollama_chat_model="test-model",
        allow_migrate=True,
        extraction_auto_run=False,
        cors_origins=["http://localhost:5173"],
    )


@pytest.fixture
def client(test_settings: Settings, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("LORE_GOBLIN_DATABASE_PATH", test_settings.database_path)
    monkeypatch.setenv("LORE_GOBLIN_ALLOW_MIGRATE", "1")
    monkeypatch.setenv("LORE_GOBLIN_DISABLE_EXTRACTION_AUTO_RUN", "1")
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture
def legacy_client(legacy_database_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    get_settings.cache_clear()
    monkeypatch.setenv("LORE_GOBLIN_DATABASE_PATH", str(legacy_database_path))
    monkeypatch.setenv("LORE_GOBLIN_ALLOW_MIGRATE", "1")
    settings = Settings(
        database_path=str(legacy_database_path),
        allow_migrate=True,
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture
def campaign(client: TestClient) -> dict:
    response = client.post(
        "/campaigns",
        json={
            "name": "Test Campaign",
            "tone": "A helpful goblin.",
            "owner_display_name": "DM",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def legacy_campaign(legacy_client: TestClient, legacy_database_path: Path) -> dict:
    response = legacy_client.post(
        "/campaigns",
        json={
            "name": "Legacy Campaign",
            "tone": "A helpful goblin.",
            "owner_display_name": "DM",
        },
    )
    assert response.status_code == 201
    campaign = response.json()
    with sqlite3.connect(legacy_database_path) as connection:
        connection.row_factory = sqlite3.Row
        owner = connection.execute(
            """
            SELECT user_id
            FROM campaign_members
            WHERE campaign_id = ? AND role = 'owner'
            """,
            (campaign["id"],),
        ).fetchone()
        assert owner is not None
        campaign["owner_user_id"] = owner["user_id"]
    return campaign


def seed_legacy_session_note(
    connection: sqlite3.Connection,
    *,
    campaign_id: str,
    user_id: str,
    raw_content: str = "The party found a silver key.",
) -> dict:
    session_id = "ses_legacy001"
    note_id = "snt_legacy001"
    connection.execute(
        """
        INSERT INTO sessions (id, campaign_id, session_date, label)
        VALUES (?, ?, '2026-06-01', 'Chapel')
        """,
        (session_id, campaign_id),
    )
    connection.execute(
        """
        INSERT INTO session_notes (id, session_id, campaign_id, author_user_id, raw_content)
        VALUES (?, ?, ?, ?, ?)
        """,
        (note_id, session_id, campaign_id, user_id, raw_content),
    )
    connection.execute(
        """
        INSERT INTO content_chunks (
            id, campaign_id, session_id, source_type, source_id, chunk_index, chunk_text
        )
        VALUES ('chk_legacy001', ?, ?, 'session_note', ?, 0, ?)
        """,
        (campaign_id, session_id, note_id, raw_content),
    )
    connection.commit()
    return {"session_id": session_id, "note_id": note_id}


def seed_legacy_player_character(
    connection: sqlite3.Connection,
    *,
    campaign_id: str,
    name: str = "Nyra",
    notes: str = "Half-elf ranger",
) -> dict:
    character_id = "pc_legacy001"
    connection.execute(
        """
        INSERT INTO player_characters (id, campaign_id, name, notes)
        VALUES (?, ?, ?, ?)
        """,
        (character_id, campaign_id, name, notes),
    )
    connection.commit()
    return {"id": character_id, "campaign_id": campaign_id, "name": name, "notes": notes}


@pytest.fixture
def legacy_connection(legacy_database_path: Path):
    with connection_at(legacy_database_path) as connection:
        yield connection
