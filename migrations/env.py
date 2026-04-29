"""Alembic environment for agentic-control.

DB URL resolution (in priority order):
1. ``-x url=...`` command-line argument.
2. ``AGENTIC_CONTROL_DB_URL`` environment variable.
3. Default: ``sqlite:///$HOME/.agentic-control/state.db``.

The DB parent directory is auto-created on first migration if missing.
"""

from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path
from urllib.parse import urlparse

from alembic import context
from sqlalchemy import engine_from_config, event, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

DEFAULT_DB_URL = f"sqlite:///{Path.home() / '.agentic-control' / 'state.db'}"


def _resolve_db_url() -> str:
    cli_args = context.get_x_argument(as_dictionary=True)
    if "url" in cli_args:
        return cli_args["url"]
    return os.environ.get("AGENTIC_CONTROL_DB_URL", DEFAULT_DB_URL)


def _ensure_sqlite_parent_dir(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    parsed = urlparse(url)
    db_path = Path(parsed.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _enforce_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()


def run_migrations_offline() -> None:
    url = _resolve_db_url()
    _ensure_sqlite_parent_dir(url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=url.startswith("sqlite"),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _resolve_db_url()
    _ensure_sqlite_parent_dir(url)
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = url
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)

    if url.startswith("sqlite"):
        event.listen(connectable, "connect", _enforce_foreign_keys)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=url.startswith("sqlite"),
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
