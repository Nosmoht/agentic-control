"""Shared pytest fixtures: per-test SQLite DB with full Alembic upgrade."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine

from agentic_control.persistence import make_engine

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'state.db'}"


@pytest.fixture
def migrated_engine(db_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    monkeypatch.setenv("AGENTIC_CONTROL_DB_URL", db_url)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={**__import__("os").environ, "AGENTIC_CONTROL_DB_URL": db_url},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic upgrade failed: {result.stderr}"
    engine = make_engine(db_url)
    yield engine
    engine.dispose()
