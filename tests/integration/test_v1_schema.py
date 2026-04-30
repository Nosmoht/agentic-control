"""F0008 acceptance criteria — v1a domain schema (run, artifact, evidence)."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import Engine, text

from agentic_control.contracts import (
    ArtifactSubjectRef,
    DecisionSubjectRef,
    Project,
    RunSubjectRef,
    WorkItem,
    WorkItemSubjectRef,
    new_id,
    parse_subject_ref,
)
from agentic_control.persistence import (
    RepositoryError,
    insert_project,
    insert_work_item,
    validate_subject_ref,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

V0_TABLES = {"project", "work_item", "observation", "decision"}
V1A_TABLES = {"run", "artifact", "evidence"}
ALL_TABLES = V0_TABLES | V1A_TABLES | {"alembic_version"}


def _sqlite_path(engine: Engine) -> str:
    return engine.url.database  # type: ignore[return-value]


def _seed_run(engine: Engine, run_id: str | None = None, state: str = "created") -> str:
    p = insert_project(engine, Project(title="P"))
    w = insert_work_item(engine, WorkItem(project_ref=p.id, title="WI"))
    rid = run_id or str(new_id())
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO run (id, work_item_ref, agent, state, budget_cap, created_at) "
                "VALUES (:id, :w, 'claude', :s, 1.0, '2026-04-29')"
            ),
            {"id": rid, "w": str(w.id), "s": state},
        )
    return rid


# ---------- AC1: tables present after migration ----------


def test_ac1_v1a_tables_present(migrated_engine: Engine) -> None:
    with sqlite3.connect(_sqlite_path(migrated_engine)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = {r[0] for r in rows}
    assert V0_TABLES.issubset(tables)
    assert V1A_TABLES.issubset(tables)


# ---------- AC2: FK on run.work_item_ref ----------


def test_ac2_run_fk_to_work_item_enforced(migrated_engine: Engine) -> None:
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text(
                "INSERT INTO run (id, work_item_ref, agent, state, budget_cap, created_at) "
                "VALUES (:id, :w, 'claude', 'created', 1.0, '2026-04-29')"
            ),
            {"id": str(new_id()), "w": str(new_id())},
        )


# ---------- AC3: run.state CHECK enforces all 9 lifecycle states ----------


def test_ac3_run_state_bogus_rejected(migrated_engine: Engine) -> None:
    rid = _seed_run(migrated_engine)
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text("UPDATE run SET state='bogus' WHERE id=:id"), {"id": rid}
        )


@pytest.mark.parametrize(
    "state",
    [
        "created",
        "running",
        "paused",
        "waiting",
        "retrying",
        "needs_reconciliation",
        "completed",
        "failed",
        "aborted",
    ],
)
def test_ac3_run_state_all_nine_lifecycle_states_accepted(
    migrated_engine: Engine, state: str
) -> None:
    _seed_run(migrated_engine, state=state)


# ---------- AC4: FK on artifact.origin_run_ref ----------


def test_ac4_artifact_fk_to_run_enforced(migrated_engine: Engine) -> None:
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text(
                "INSERT INTO artifact "
                "(id, origin_run_ref, kind, path_or_ref, provenance, state, created_at) "
                "VALUES (:id, :r, 'file_diff', '/x', 'manual', 'registered', '2026-04-29')"
            ),
            {"id": str(new_id()), "r": str(new_id())},
        )


# ---------- AC5: artifact.state CHECK enforces 5 lifecycle states ----------


def test_ac5_artifact_state_bogus_rejected(migrated_engine: Engine) -> None:
    rid = _seed_run(migrated_engine)
    aid = str(new_id())
    with migrated_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO artifact "
                "(id, origin_run_ref, kind, path_or_ref, provenance, state, created_at) "
                "VALUES (:id, :r, 'file_diff', '/x', 'manual', 'registered', '2026-04-29')"
            ),
            {"id": aid, "r": rid},
        )
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text("UPDATE artifact SET state='bogus' WHERE id=:id"), {"id": aid}
        )


@pytest.mark.parametrize(
    "state", ["registered", "available", "consumed", "superseded", "archived"]
)
def test_ac5_artifact_all_five_lifecycle_states_accepted(
    migrated_engine: Engine, state: str
) -> None:
    rid = _seed_run(migrated_engine)
    with migrated_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO artifact "
                "(id, origin_run_ref, kind, path_or_ref, provenance, state, created_at) "
                "VALUES (:id, :r, 'file_diff', '/x', 'manual', :s, '2026-04-29')"
            ),
            {"id": str(new_id()), "r": rid, "s": state},
        )


# ---------- AC6: polymorphic evidence.subject_ref accepts all four kinds ----------


@pytest.mark.parametrize("prefix", ["work_item", "run", "artifact", "decision"])
@pytest.mark.parametrize("kind", ["benchmark", "decision_evidence"])
def test_ac6_evidence_subject_ref_accepts_all_kinds(
    migrated_engine: Engine, prefix: str, kind: str
) -> None:
    rendered = f"{prefix}:{new_id()}"
    with migrated_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO evidence (id, subject_ref, kind, captured_at) "
                "VALUES (:id, :s, :k, '2026-04-29')"
            ),
            {"id": str(new_id()), "s": rendered, "k": kind},
        )


# ---------- AC7: negative subject_ref tests + polymorphic-FK Eigenentscheidung ----------


def test_ac7a_evidence_subject_ref_without_separator_rejected(
    migrated_engine: Engine,
) -> None:
    bogus = f"work_item{new_id()}"  # no colon
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text(
                "INSERT INTO evidence (id, subject_ref, kind, captured_at) "
                "VALUES (:id, :s, 'benchmark', '2026-04-29')"
            ),
            {"id": str(new_id()), "s": bogus},
        )


def test_ac7b_evidence_subject_ref_unknown_prefix_rejected(
    migrated_engine: Engine,
) -> None:
    bogus = f"stranger:{new_id()}"
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text(
                "INSERT INTO evidence (id, subject_ref, kind, captured_at) "
                "VALUES (:id, :s, 'benchmark', '2026-04-29')"
            ),
            {"id": str(new_id()), "s": bogus},
        )


def test_ac7c_validate_subject_ref_rejects_missing_row(
    migrated_engine: Engine,
) -> None:
    """Polymorpher-Ref-Validierungs-Hook (AC10): app-layer FK enforcement."""
    ghost = WorkItemSubjectRef(id=new_id())
    with pytest.raises(RepositoryError, match="missing work_item"):
        validate_subject_ref(migrated_engine, ghost)


def test_ac7c_validate_subject_ref_accepts_existing_row(
    migrated_engine: Engine,
) -> None:
    p = insert_project(migrated_engine, Project(title="P"))
    w = insert_work_item(migrated_engine, WorkItem(project_ref=p.id, title="WI"))
    ref = WorkItemSubjectRef(id=w.id)
    validate_subject_ref(migrated_engine, ref)


def test_ac7c_validate_subject_ref_branches_per_kind(migrated_engine: Engine) -> None:
    """Each subject kind hits its own table — verify all four arms."""
    rid = _seed_run(migrated_engine)
    aid = str(new_id())
    with migrated_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO artifact "
                "(id, origin_run_ref, kind, path_or_ref, provenance, state, created_at) "
                "VALUES (:id, :r, 'file_diff', '/x', 'manual', 'registered', '2026-04-29')"
            ),
            {"id": aid, "r": rid},
        )
    p = insert_project(migrated_engine, Project(title="P2"))
    w = insert_work_item(migrated_engine, WorkItem(project_ref=p.id, title="WI2"))

    validate_subject_ref(migrated_engine, RunSubjectRef(id=uuid.UUID(rid)))
    validate_subject_ref(migrated_engine, ArtifactSubjectRef(id=uuid.UUID(aid)))
    validate_subject_ref(migrated_engine, WorkItemSubjectRef(id=w.id))

    # decision needs a subject row pointing back at the work_item
    with migrated_engine.begin() as conn:
        did = str(new_id())
        conn.execute(
            text(
                "INSERT INTO decision "
                "(id, subject_ref, context, decision, consequence, state, created_at) "
                "VALUES (:id, :s, 'c', 'd', 'g', 'proposed', '2026-04-29')"
            ),
            {"id": did, "s": str(w.id)},
        )
    validate_subject_ref(migrated_engine, DecisionSubjectRef(id=uuid.UUID(did)))


# ---------- AC8: idempotent migration ----------


def test_ac8_idempotent_full_upgrade(db_url: str, migrated_engine: Engine) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={**os.environ, "AGENTIC_CONTROL_DB_URL": db_url},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


# ---------- AC9: F0001 + F0008 produce 4 + 3 = 7 tables (F0006 lands later) ----------


def test_ac9_table_count_after_v0_plus_v1a(migrated_engine: Engine) -> None:
    with sqlite3.connect(_sqlite_path(migrated_engine)) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'"
        ).fetchall()
    assert {r[0] for r in rows} == V0_TABLES | V1A_TABLES


# ---------- AC10: subject-ref Pydantic round-trip ----------


def test_ac10_subject_ref_round_trip() -> None:
    ref = WorkItemSubjectRef(id=new_id())
    rendered = ref.render()
    parsed = parse_subject_ref(rendered)
    assert parsed == ref


def test_ac10_parse_subject_ref_rejects_bogus_prefix() -> None:
    with pytest.raises(ValueError, match="malformed"):
        parse_subject_ref(f"stranger:{new_id()}")


def test_ac10_parse_subject_ref_rejects_missing_separator() -> None:
    with pytest.raises(ValueError, match="malformed"):
        parse_subject_ref(f"work_item{new_id()}")
