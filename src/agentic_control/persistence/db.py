"""SQLAlchemy engine factory for SQLite with FK enforcement."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import Engine, create_engine, event

DEFAULT_DB_URL = f"sqlite:///{Path.home() / '.agentic-control' / 'state.db'}"


def resolve_db_url() -> str:
    return os.environ.get("AGENTIC_CONTROL_DB_URL", DEFAULT_DB_URL)


def _ensure_sqlite_parent(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    db_path = Path(urlparse(url).path)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def make_engine(url: str | None = None) -> Engine:
    resolved = url or resolve_db_url()
    _ensure_sqlite_parent(resolved)
    engine = create_engine(resolved, future=True)

    if resolved.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_fk(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys = ON")
            finally:
                cursor.close()

    return engine
