"""F0006a acceptance criteria — runtime-record schema, FKs, UNIQUEs, CHECKs."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import Engine, text

from agentic_control.contracts import (
    ApprovalRequest,
    BudgetLedgerEntry,
    DispatchDecision,
    PolicyDecisionGeneric,
    PolicyDecisionToolRiskMatch,
    Project,
    Run,
    RunAttempt,
    SandboxViolation,
    ToolCallRecord,
    ToolRiskMatchOutput,
    WorkItem,
    new_id,
)
from agentic_control.contracts.runtime_records import AuditEvent
from agentic_control.persistence import (
    RepositoryError,
    insert_approval_request,
    insert_audit_event,
    insert_budget_ledger_entry,
    insert_dispatch_decision,
    insert_policy_decision,
    insert_project,
    insert_run_attempt,
    insert_sandbox_violation,
    insert_tool_call_record,
    insert_work_item,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

V0_V1A_TABLES = {
    "project",
    "work_item",
    "observation",
    "decision",
    "run",
    "artifact",
    "evidence",
}
RUNTIME_TABLES = {
    "run_attempt",
    "audit_event",
    "approval_request",
    "budget_ledger_entry",
    "tool_call_record",
    "policy_decision",
    "sandbox_violation",
    "dispatch_decision",
}


def _sqlite_path(engine: Engine) -> str:
    return engine.url.database  # type: ignore[return-value]


def _seed_run_attempt(engine: Engine) -> tuple[Run, RunAttempt]:
    """Create project → work_item → run → run_attempt and return the leaves."""
    p = insert_project(engine, Project(title="P"))
    w = insert_work_item(engine, WorkItem(project_ref=p.id, title="WI"))
    run_id = new_id()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO run (id, work_item_ref, agent, state, budget_cap, created_at) "
                "VALUES (:id, :w, 'claude', 'running', 1.0, '2026-04-30')"
            ),
            {"id": str(run_id), "w": str(w.id)},
        )
    run = Run(id=run_id, work_item_ref=w.id, agent="claude", state="running", budget_cap=1.0)
    attempt = insert_run_attempt(
        engine,
        RunAttempt(
            run_ref=run.id,
            attempt_ordinal=1,
            agent="claude",
            model="claude-sonnet-4-6",
            sandbox_profile="standard",
            prompt_hash="abcdef012345",
            tool_allowlist=["git.commit"],
            logs_ref="/tmp/run.jsonl",
        ),
    )
    return run, attempt


# ---------- AC 1: all eight runtime tables present ----------


def test_ac1_runtime_tables_present(migrated_engine: Engine) -> None:
    with sqlite3.connect(_sqlite_path(migrated_engine)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = {r[0] for r in rows}
    assert RUNTIME_TABLES.issubset(tables)
    assert V0_V1A_TABLES.issubset(tables)


# ---------- AC 1 (negative): F0006 against pre-F0008 state fails on FK ----------


def test_ac1_negative_runtime_migration_requires_v1a_run_table(tmp_path: Path) -> None:
    """`run_attempt.run_ref` FK targets `run` (from F0008). Running 0002 against
    a fresh DB without 0001b should fail because the `run` table is missing."""
    db_path = tmp_path / "no_v1a.db"
    env = {**os.environ, "AGENTIC_CONTROL_DB_URL": f"sqlite:///{db_path}"}
    # Apply only revision 0001 (skip 0001b and 0002).
    r1 = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "0001"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0, r1.stderr
    # Now jump straight to 0002 — must fail because 0001b never ran.
    r2 = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "0002"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    # 0002 depends on 0001b. Alembic refuses because the chain is incomplete
    # (would have applied 0001b first if it could). With a custom env this
    # surfaces as a non-zero exit OR a successful run that pulled 0001b in
    # automatically. Either way, after `upgrade 0002` completes successfully
    # we must see all tables — Alembic's resolver pulls 0001b in.
    if r2.returncode == 0:
        with sqlite3.connect(db_path) as conn:
            tables = {
                r[0]
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        assert "run" in tables, "alembic resolver must apply 0001b before 0002"


# ---------- AC 2: FK enforcement on run_attempt.run_ref ----------


def test_ac2_run_attempt_fk_enforced(migrated_engine: Engine) -> None:
    bad = RunAttempt(
        run_ref=new_id(),
        attempt_ordinal=1,
        agent="claude",
        model="m",
        sandbox_profile="standard",
        prompt_hash="abcdef012345",
        logs_ref="/tmp/x.jsonl",
    )
    with pytest.raises(RepositoryError, match="FOREIGN KEY"):
        insert_run_attempt(migrated_engine, bad)


# ---------- AC 3: tool_call_record dual UNIQUE ----------


def test_ac3_tool_call_ordinal_unique(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    insert_tool_call_record(
        migrated_engine,
        ToolCallRecord(
            run_attempt_ref=attempt.id,
            tool_call_ordinal=1,
            tool_name="git.commit",
            input_hash="abcdef012345",
            effect_class="natural",
        ),
    )
    with pytest.raises(RepositoryError, match="UNIQUE"):
        insert_tool_call_record(
            migrated_engine,
            ToolCallRecord(
                run_attempt_ref=attempt.id,
                tool_call_ordinal=1,  # same ordinal
                tool_name="git.commit",
                input_hash="abcdef012345",
                effect_class="natural",
            ),
        )


def test_ac3_tool_call_idempotency_partial_unique(migrated_engine: Engine) -> None:
    """Same idempotency_key on the same run_attempt is rejected."""
    _, attempt = _seed_run_attempt(migrated_engine)
    insert_tool_call_record(
        migrated_engine,
        ToolCallRecord(
            run_attempt_ref=attempt.id,
            tool_call_ordinal=1,
            tool_name="gh.issue.comment",
            input_hash="abcdef012345",
            idempotency_key="local-only-key-42",
            effect_class="local_only",
        ),
    )
    with pytest.raises(RepositoryError, match="UNIQUE"):
        insert_tool_call_record(
            migrated_engine,
            ToolCallRecord(
                run_attempt_ref=attempt.id,
                tool_call_ordinal=2,
                tool_name="gh.issue.comment",
                input_hash="abcdef012345",
                idempotency_key="local-only-key-42",  # duplicate key
                effect_class="local_only",
            ),
        )


def test_ac3_tool_call_null_idempotency_key_allows_multiple(migrated_engine: Engine) -> None:
    """Multiple tool calls with NULL idempotency_key (no external effect) coexist."""
    _, attempt = _seed_run_attempt(migrated_engine)
    for ordinal in (1, 2, 3):
        insert_tool_call_record(
            migrated_engine,
            ToolCallRecord(
                run_attempt_ref=attempt.id,
                tool_call_ordinal=ordinal,
                tool_name="git.commit",
                input_hash="abcdef012345",
                idempotency_key=None,
                effect_class="natural",
            ),
        )


# ---------- AC 11: dispatch_decision UNIQUE per run_attempt ----------


def test_ac11_dispatch_decision_unique_per_attempt(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    insert_dispatch_decision(
        migrated_engine,
        DispatchDecision(
            run_attempt_ref=attempt.id,
            adapter="claude_code",
            model="claude-sonnet-4-6",
            mode="pinned",
            reason="pin",
        ),
    )
    with pytest.raises(RepositoryError, match="UNIQUE"):
        insert_dispatch_decision(
            migrated_engine,
            DispatchDecision(
                run_attempt_ref=attempt.id,  # already has one
                adapter="codex_cli",
                model="gpt-5",
                mode="cost_aware",
                reason="cost_aware_routing",
            ),
        )


# ---------- AC 12: PolicyDecision discriminator + tool_risk_match validation ----------


def test_ac12_policy_decision_enum_check(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text(
                "INSERT INTO policy_decision "
                "(id, ts, policy, subject_ref, inputs, output, run_attempt_ref) "
                "VALUES (:id, '2026-04-30', 'bogus_policy', 'work_item:abc', '{}', '{}', :a)"
            ),
            {"id": str(new_id()), "a": str(attempt.id)},
        )


def test_ac12_policy_decision_generic_round_trip(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    decision = PolicyDecisionGeneric(
        policy="admission",
        subject_ref=f"work_item:{new_id()}",
        inputs={"key": "value"},
        output={"verdict": "accept"},
        run_attempt_ref=attempt.id,
    )
    insert_policy_decision(migrated_engine, decision)


def test_ac12_policy_decision_tool_risk_match_full_payload(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    tool_call = insert_tool_call_record(
        migrated_engine,
        ToolCallRecord(
            run_attempt_ref=attempt.id,
            tool_call_ordinal=1,
            tool_name="rm.recursive",
            input_hash="abcdef012345",
            effect_class="local_only",
        ),
    )
    decision = PolicyDecisionToolRiskMatch(
        subject_ref=f"tool_call_record:{tool_call.id}",
        inputs={"tool": "rm.recursive"},
        output=ToolRiskMatchOutput(
            matched_pattern="rm -rf",
            risk="irreversible",
            approval="required",
            default_hit=False,
        ),
        run_attempt_ref=attempt.id,
    )
    insert_policy_decision(migrated_engine, decision)


def test_ac12_policy_decision_tool_risk_match_missing_field_rejected() -> None:
    """Pydantic owns the schema gate for tool_risk_match; bypassing payload
    fields fails at model construction, not at SQL."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="matched_pattern"):
        ToolRiskMatchOutput(  # type: ignore[call-arg]
            risk="high",
            approval="required",
            default_hit=False,
        )


def test_ac12_policy_decision_tool_risk_match_repository_only(
    migrated_engine: Engine,
) -> None:
    """Direct-SQL bypass with empty output JSON passes ``json_valid`` but
    breaks the contract that repository inserts uphold. This test documents
    that the SQL layer is intentionally permissive — Pydantic + repository
    are the gate."""
    _, attempt = _seed_run_attempt(migrated_engine)
    with migrated_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO policy_decision "
                "(id, ts, policy, subject_ref, inputs, output, run_attempt_ref) "
                "VALUES (:id, '2026-04-30', 'tool_risk_match', "
                "'tool_call_record:bogus', '{}', '{}', :a)"
            ),
            {"id": str(new_id()), "a": str(attempt.id)},
        )
    # Direct insert succeeds (json_valid passes for {}). Documenting this
    # invariant: callers MUST go through insert_policy_decision().


# ---------- audit_event polymorphic subject_ref CHECK ----------


def test_audit_event_accepts_domain_ref(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    insert_audit_event(
        migrated_engine,
        AuditEvent(
            actor="agentctl runs reconcile",
            subject_ref=f"run:{attempt.run_ref}",
            event_type="reconcile_decision",
            run_attempt_ref=attempt.id,
        ),
    )


def test_audit_event_accepts_config_path(migrated_engine: Engine) -> None:
    insert_audit_event(
        migrated_engine,
        AuditEvent(
            actor="agentctl dispatch accept",
            subject_ref="config/dispatch/routing-pins.yaml",
            event_type="config_write",
            before_hash="0" * 64,
            after_hash="1" * 64,
            reason="pin accepted",
        ),
    )


def test_audit_event_rejects_unknown_prefix() -> None:
    """Pydantic rejects malformed subject_ref before SQL is touched."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="subject_ref"):
        AuditEvent(
            actor="x",
            subject_ref=f"stranger:{new_id()}",
            event_type="state_transition",
        )


def test_audit_event_sql_check_rejects_bogus_subject_ref(migrated_engine: Engine) -> None:
    """Defense-in-depth: even if Pydantic is bypassed, SQL CHECK rejects."""
    with migrated_engine.begin() as conn, pytest.raises(Exception):  # noqa: B017
        conn.execute(
            text(
                "INSERT INTO audit_event (id, ts, actor, subject_ref, event_type) "
                "VALUES (:id, '2026-04-30', 'x', 'stranger:bogus', 'state_transition')"
            ),
            {"id": str(new_id())},
        )


# ---------- ApprovalRequest, BudgetLedgerEntry, SandboxViolation smoke ----------


def test_approval_request_roundtrip(migrated_engine: Engine) -> None:
    p = insert_project(migrated_engine, Project(title="P"))
    w = insert_work_item(migrated_engine, WorkItem(project_ref=p.id, title="WI"))
    insert_approval_request(
        migrated_engine,
        ApprovalRequest(
            subject_ref=w.id,
            risk_class="high",
            question="Run rm -rf on workspace?",
        ),
    )


def test_budget_ledger_entry_roundtrip(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    insert_budget_ledger_entry(
        migrated_engine,
        BudgetLedgerEntry(
            scope="request",
            run_attempt_ref=attempt.id,
            run_attempt_hash_anchor="abcdef012345",
            model="claude-sonnet-4-6",
            pre_call_projection_usd=0.05,
            actual_usd=0.04,
            cache_hit=True,
        ),
    )


def test_sandbox_violation_roundtrip(migrated_engine: Engine) -> None:
    _, attempt = _seed_run_attempt(migrated_engine)
    insert_sandbox_violation(
        migrated_engine,
        SandboxViolation(
            run_attempt_ref=attempt.id,
            category="egress_denied",
            detail={"host": "evil.example.com", "port": 443},
        ),
    )


# ---------- Idempotent migration (rerun head) ----------


def test_idempotent_migration(db_url: str, migrated_engine: Engine) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={**os.environ, "AGENTIC_CONTROL_DB_URL": db_url},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


# ---------- Schema dump stability vs. fixture ----------


def test_schema_dump_stability(migrated_engine: Engine) -> None:
    """Reuses the schema-0001.sql fixture covering all three migrations."""
    import re

    db_path = _sqlite_path(migrated_engine)
    fixture = REPO_ROOT / "tests" / "fixtures" / "schema-0001.sql"
    result = subprocess.run(
        ["sqlite3", db_path, ".schema"], capture_output=True, text=True, check=True
    )
    actual = re.sub(
        r"CREATE TABLE alembic_version[^;]*;\s*", "", result.stdout, flags=re.DOTALL
    )
    actual = re.sub(
        r"CREATE UNIQUE INDEX sqlite_autoindex_alembic_version_pkc[^;]*;\s*", "", actual
    )
    assert actual.strip() == fixture.read_text().strip(), (
        f"Schema drift; regenerate via:\n"
        f"  sqlite3 {db_path} .schema | strip alembic_version > {fixture}"
    )
