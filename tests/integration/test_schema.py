"""F0001 acceptance criteria — schema, FK, CHECK, idempotency, dump stability."""

from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import Engine, text

from agentic_control.contracts import Decision, Observation, Project, WorkItem, new_id
from agentic_control.persistence import (
    RepositoryError,
    insert_decision,
    insert_observation,
    insert_project,
    insert_work_item,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "schema-0001.sql"

EXPECTED_TABLES = {"project", "work_item", "observation", "decision", "alembic_version"}


def _sqlite_path(engine: Engine) -> str:
    return engine.url.database  # type: ignore[return-value]


def test_ac1_migration_on_empty_db(migrated_engine: Engine) -> None:
    db_path = _sqlite_path(migrated_engine)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = {r[0] for r in rows}
    assert EXPECTED_TABLES.issubset(tables)


def test_ac2_pk_and_fk_definitions(migrated_engine: Engine) -> None:
    with sqlite3.connect(_sqlite_path(migrated_engine)) as conn:
        fks = conn.execute("PRAGMA foreign_key_list(work_item)").fetchall()
        assert any(f[2] == "project" and f[3] == "project_ref" for f in fks)
        fks_dec = conn.execute("PRAGMA foreign_key_list(decision)").fetchall()
        assert any(f[2] == "work_item" and f[3] == "subject_ref" for f in fks_dec)


def test_ac3_fk_enforcement(migrated_engine: Engine) -> None:
    bad = WorkItem(project_ref=new_id(), title="orphan")
    with pytest.raises(RepositoryError, match="FOREIGN KEY"):
        insert_work_item(migrated_engine, bad)


def test_ac4_state_check_enforcement(migrated_engine: Engine) -> None:
    p = insert_project(migrated_engine, Project(title="p"))
    valid = insert_work_item(migrated_engine, WorkItem(project_ref=p.id, title="ok"))
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text("UPDATE work_item SET state='bogus' WHERE id=:id"),
            {"id": str(valid.id)},
        )


def test_ac5_uuid_length_check(migrated_engine: Engine) -> None:
    p = insert_project(migrated_engine, Project(title="p"))
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text(
                "INSERT INTO work_item (id, project_ref, title, state, priority, created_at) "
                "VALUES (:id, :p, 't', 'proposed', 'med', '2026-01-01')"
            ),
            {"id": "too-short", "p": str(p.id)},
        )


def test_ac6_pydantic_rejects_uuidv4_before_sql() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        WorkItem(id=uuid.uuid4(), project_ref=new_id(), title="x")


def test_ac7_idempotent_migration(db_url: str, migrated_engine: Engine) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={**os.environ, "AGENTIC_CONTROL_DB_URL": db_url},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_ac8_schema_dump_stability(migrated_engine: Engine) -> None:
    db_path = _sqlite_path(migrated_engine)
    result = subprocess.run(
        ["sqlite3", db_path, ".schema"], capture_output=True, text=True, check=True
    )
    actual = _strip_alembic_version(result.stdout)
    expected = FIXTURE.read_text()
    assert actual.strip() == expected.strip(), (
        "Schema drift detected. Inspect with:\n"
        f"  diff <(sqlite3 {db_path} .schema | grep -v alembic_version) "
        f"{FIXTURE}"
    )


def test_ac8b_round_trip_full_object_graph(migrated_engine: Engine) -> None:
    p = insert_project(migrated_engine, Project(title="Round-trip"))
    w = insert_work_item(migrated_engine, WorkItem(project_ref=p.id, title="WI"))
    obs = insert_observation(
        migrated_engine,
        Observation(source_ref=w.id, body="seen something", classification="manual"),
    )
    dec = insert_decision(
        migrated_engine,
        Decision(
            subject_ref=w.id,
            context="we noticed X",
            decision="we will Y",
            consequence="Z follows",
        ),
    )
    assert obs.id and dec.id


def _strip_alembic_version(schema: str) -> str:
    schema = re.sub(r"CREATE TABLE alembic_version[^;]*;\s*", "", schema, flags=re.DOTALL)
    schema = re.sub(
        r"CREATE UNIQUE INDEX sqlite_autoindex_alembic_version_pkc[^;]*;\s*", "", schema
    )
    return schema
