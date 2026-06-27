from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

MIGRATION_FILE_PATTERN = re.compile(r"^(\d+)_.+\.sql$")


@dataclass(frozen=True)
class MigrationResult:
    dry_run: bool
    sources_created: int
    entities_created: int
    chunks_linked: int
    errors: list[str]


def _migration_files() -> list[tuple[int, Path]]:
    migrations_dir = Path(__file__).parent
    files: list[tuple[int, Path]] = []
    for path in migrations_dir.glob("*.sql"):
        match = MIGRATION_FILE_PATTERN.match(path.name)
        if match:
            files.append((int(match.group(1)), path))
    return sorted(files, key=lambda item: item[0])


def get_schema_version(connection: sqlite3.Connection) -> int:
    table = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'schema_version'
        """
    ).fetchone()
    if not table:
        return 0
    row = connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()
    return int(row[0]) if row else 0


def apply_pending_migrations(connection: sqlite3.Connection) -> list[int]:
    applied: list[int] = []
    current_version = get_schema_version(connection)
    for version, path in _migration_files():
        if version == 2:
            connection.executescript(path.read_text(encoding="utf-8"))
            if current_version < 2:
                applied.append(version)
            continue
        if version <= current_version:
            continue
        connection.executescript(path.read_text(encoding="utf-8"))
        applied.append(version)
        current_version = version
    return applied


def count_pending_legacy_sources(connection: sqlite3.Connection) -> int:
    if not _table_exists(connection, "source"):
        return _count_rows(connection, "session_notes")
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM session_notes sn
        WHERE NOT EXISTS (
            SELECT 1 FROM source existing WHERE existing.legacy_note_id = sn.id
        )
        """
    ).fetchone()
    return int(row[0]) if row else 0


def count_pending_legacy_entities(connection: sqlite3.Connection) -> int:
    if not _table_exists(connection, "entity"):
        return _count_rows(connection, "player_characters")
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM player_characters pc
        WHERE NOT EXISTS (
            SELECT 1 FROM entity existing WHERE existing.legacy_pc_id = pc.id
        )
        """
    ).fetchone()
    return int(row[0]) if row else 0


def count_pending_legacy_pc_sources(connection: sqlite3.Connection) -> int:
    if not _table_exists(connection, "source"):
        return _count_rows(connection, "player_characters")
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM player_characters pc
        WHERE NOT EXISTS (
            SELECT 1 FROM source existing
            WHERE existing.entity_id = pc.id
              AND existing.source_type = 'PLAYER_CHARACTER_DESC'
        )
        """
    ).fetchone()
    return int(row[0]) if row else 0


def count_pending_chunk_links(connection: sqlite3.Connection) -> int:
    if not _table_exists(connection, "source"):
        return 0
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM content_chunks cc
        WHERE cc.source_type = 'session_note'
          AND EXISTS (
              SELECT 1
              FROM session_notes sn
              WHERE sn.id = cc.source_id
          )
        """
    ).fetchone()
    return int(row[0]) if row else 0


def run_migration(connection: sqlite3.Connection, *, dry_run: bool = False) -> MigrationResult:
    note_sources = count_pending_legacy_sources(connection)
    pc_sources = count_pending_legacy_pc_sources(connection)
    pending_entities = count_pending_legacy_entities(connection)
    pending_chunks = count_pending_chunk_links(connection)
    total_sources = note_sources + pc_sources

    if dry_run:
        return MigrationResult(
            dry_run=True,
            sources_created=total_sources,
            entities_created=pending_entities,
            chunks_linked=pending_chunks,
            errors=[],
        )

    try:
        apply_pending_migrations(connection)
    except sqlite3.Error as exc:
        return MigrationResult(
            dry_run=False,
            sources_created=0,
            entities_created=0,
            chunks_linked=0,
            errors=[str(exc)],
        )

    return MigrationResult(
        dry_run=False,
        sources_created=total_sources,
        entities_created=pending_entities,
        chunks_linked=pending_chunks,
        errors=[],
    )


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (name,),
    ).fetchone()
    return row is not None


def _count_rows(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0
