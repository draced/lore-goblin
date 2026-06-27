from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import logging
import sqlite3
import uuid

from .config import get_settings
from .migrations.runner import apply_pending_migrations

logger = logging.getLogger(__name__)

_database_path_override: str | None = None


def load_sqlite_extensions(connection: sqlite3.Connection) -> None:
    if not hasattr(connection, "enable_load_extension"):
        logger.warning("SQLite extension loading is unavailable; vector search disabled")
        return
    try:
        import sqlite_vec

        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
    except Exception as exc:
        logger.warning("Failed to load sqlite-vec extension: %s", exc)


def set_database_path(database_path: str) -> None:
    global _database_path_override
    _database_path_override = database_path


def resolve_database_path(database_path: str | None = None) -> str:
    if database_path:
        return database_path
    if _database_path_override:
        return _database_path_override
    return get_settings().database_path


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def initialize_database(database_path: str | None = None) -> None:
    db_path = Path(resolve_database_path(database_path))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(__file__).with_name("schema.sql")
    with sqlite3.connect(db_path) as connection:
        load_sqlite_extensions(connection)
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        apply_pending_migrations(connection)
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    initialize_database()
    connection = sqlite3.connect(resolve_database_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    load_sqlite_extensions(connection)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database_at(path: str | Path) -> None:
    initialize_database(str(path))


@contextmanager
def connection_at(path: str | Path) -> Iterator[sqlite3.Connection]:
    initialize_database_at(path)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    load_sqlite_extensions(connection)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
