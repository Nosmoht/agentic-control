"""F0006c · ``agentctl runs reconcile / mark-pending-reconcile / list``.

Covers AC 5 (reconcile interactive flow), AC 7 (mark + list), AC 10
(idempotency), and the UX cases (invalid input, missing flags,
multi-tool-call ordering).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine, text
from typer.testing import CliRunner

from agentic_control.cli.main import app
from agentic_control.contracts import (
    Project,
    RunAttempt,
    ToolCallRecord,
    WorkItem,
    new_id,
)
from agentic_control.persistence import (
    insert_project,
    insert_run_attempt,
    insert_tool_call_record,
    insert_work_item,
)


@pytest.fixture
def runner(
    monkeypatch: pytest.MonkeyPatch, db_url: str, migrated_engine: Engine
) -> CliRunner:
    monkeypatch.setenv("AGENTIC_CONTROL_DB_URL", db_url)
    return CliRunner()


# ---------- Seeding helpers (raw-SQL allowed for test fixtures only) ----------


def _seed_run_in_state(engine: Engine, state: str = "running") -> uuid.UUID:
    """Insert a project → work_item → run, return the run id."""
    p = insert_project(engine, Project(title="P"))
    w = insert_work_item(engine, WorkItem(project_ref=p.id, title="WI"))
    run_id = new_id()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO run (id, work_item_ref, agent, state, "
                "budget_cap, created_at) "
                "VALUES (:id, :w, 'claude', :s, 1.0, '2026-04-30')"
            ),
            {"id": str(run_id), "w": str(w.id), "s": state},
        )
    return run_id


def _seed_attempt(
    engine: Engine, run_id: uuid.UUID, ordinal: int = 1
) -> RunAttempt:
    return insert_run_attempt(
        engine,
        RunAttempt(
            run_ref=run_id,
            attempt_ordinal=ordinal,
            agent="claude",
            model="claude-sonnet-4-6",
            sandbox_profile="standard",
            prompt_hash="abcdef012345",
            tool_allowlist=["gh.issue.comment"],
            logs_ref=f"/tmp/run-{ordinal}.jsonl",
        ),
    )


def _seed_local_only_call(
    engine: Engine,
    attempt: RunAttempt,
    ordinal: int = 1,
    tool_name: str = "gh.issue.comment",
) -> ToolCallRecord:
    base = datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)
    rec = ToolCallRecord(
        run_attempt_ref=attempt.id,
        tool_call_ordinal=ordinal,
        tool_name=tool_name,
        input_hash="abcdef012345",
        idempotency_key=f"key-{ordinal}",
        effect_class="local_only",
        started_at=base + timedelta(seconds=ordinal),
    )
    return insert_tool_call_record(engine, rec)


def _seed_attempt_with_local_only_call(
    engine: Engine, run_id: uuid.UUID
) -> tuple[RunAttempt, ToolCallRecord]:
    attempt = _seed_attempt(engine, run_id)
    tc = _seed_local_only_call(engine, attempt, ordinal=1)
    return attempt, tc


def _run_state(engine: Engine, run_id: uuid.UUID) -> str:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT state FROM run WHERE id = :id"), {"id": str(run_id)}
        ).first()
    assert row is not None
    return str(row[0])


def _audit_count_for_tool_call(engine: Engine, tc_id: uuid.UUID) -> int:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT COUNT(*) FROM audit_event "
                "WHERE subject_ref = :s AND event_type = 'reconcile_decision'"
            ),
            {"s": f"tool_call_record:{tc_id}"},
        ).first()
    assert row is not None
    return int(row[0])


def _set_run_state(engine: Engine, run_id: uuid.UUID, state: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE run SET state = :s WHERE id = :id"),
            {"s": state, "id": str(run_id)},
        )


# ---------- AC 5: reconcile happy paths (one per option) ----------


@pytest.mark.parametrize("choice", ["erfolgt", "unsicher", "nicht_erfolgt"])
def test_ac5_reconcile_writes_audit_and_resets_state(
    choice: str, runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run_in_state(migrated_engine, state="needs_reconciliation")
    _, tc = _seed_attempt_with_local_only_call(migrated_engine, run_id)

    result = runner.invoke(
        app, ["runs", "reconcile", str(run_id)], input=f"{choice}\n"
    )

    assert result.exit_code == 0, result.output
    assert "1 unreconciled local-only effect" in result.output
    assert "reconciled, state → running" in result.output
    assert _run_state(migrated_engine, run_id) == "running"
    assert _audit_count_for_tool_call(migrated_engine, tc.id) == 1

    # Verify the AuditEvent reason captures the user's choice verbatim.
    with migrated_engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT actor, reason FROM audit_event "
                "WHERE subject_ref = :s"
            ),
            {"s": f"tool_call_record:{tc.id}"},
        ).first()
    assert row is not None
    assert row[0] == "agentctl runs reconcile"
    assert row[1] == f"user-marked: {choice}"


def test_ac5_invalid_choice_reprompts_then_accepts(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run_in_state(migrated_engine, state="needs_reconciliation")
    _, tc = _seed_attempt_with_local_only_call(migrated_engine, run_id)

    # First answer is rejected; second is accepted.
    result = runner.invoke(
        app, ["runs", "reconcile", str(run_id)], input="bogus\nerfolgt\n"
    )

    assert result.exit_code == 0, result.output
    assert "invalid choice 'bogus'" in result.output
    assert _audit_count_for_tool_call(migrated_engine, tc.id) == 1
    assert _run_state(migrated_engine, run_id) == "running"


def test_ac5_run_not_in_needs_reconciliation_user_error(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run_in_state(migrated_engine, state="running")

    result = runner.invoke(app, ["runs", "reconcile", str(run_id)])

    assert result.exit_code == 2
    assert "is not in state=needs_reconciliation" in result.output
    assert _run_state(migrated_engine, run_id) == "running"


def test_ac5_no_local_only_calls_prints_nothing_and_exits_zero(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    # Run is in needs_reconciliation but has no local-only tool-calls.
    run_id = _seed_run_in_state(migrated_engine, state="needs_reconciliation")
    _seed_attempt(migrated_engine, run_id)

    result = runner.invoke(app, ["runs", "reconcile", str(run_id)])

    assert result.exit_code == 0, result.output
    assert "nothing to reconcile" in result.output
    # ADR-0011 §126-128: reset to running so the run leaves the awaiting
    # state even when there is nothing to resolve.
    assert _run_state(migrated_engine, run_id) == "running"


def test_ac5_unknown_run_user_error(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    bogus_prefix = "deadbeefdeadbeef"
    result = runner.invoke(app, ["runs", "reconcile", bogus_prefix])

    assert result.exit_code == 2


# ---------- AC 7: mark-pending-reconcile ----------


def test_ac7_mark_pending_reconcile_transitions_running_runs(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    r1 = _seed_run_in_state(migrated_engine, state="running")
    r2 = _seed_run_in_state(migrated_engine, state="running")
    r3 = _seed_run_in_state(migrated_engine, state="completed")

    result = runner.invoke(
        app, ["runs", "mark-pending-reconcile", "--all-running"]
    )

    assert result.exit_code == 0, result.output
    assert "marked 2 run(s) as needs_reconciliation" in result.output
    assert _run_state(migrated_engine, r1) == "needs_reconciliation"
    assert _run_state(migrated_engine, r2) == "needs_reconciliation"
    assert _run_state(migrated_engine, r3) == "completed"


def test_ac7_mark_pending_reconcile_idempotent(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    _seed_run_in_state(migrated_engine, state="running")

    first = runner.invoke(
        app, ["runs", "mark-pending-reconcile", "--all-running"]
    )
    second = runner.invoke(
        app, ["runs", "mark-pending-reconcile", "--all-running"]
    )

    assert first.exit_code == 0
    assert "marked 1 run(s)" in first.output
    assert second.exit_code == 0
    # Second invocation finds zero `running` rows because the first
    # invocation already promoted them.
    assert "marked 0 run(s)" in second.output


def test_ac7_mark_pending_reconcile_requires_all_running_flag(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    result = runner.invoke(app, ["runs", "mark-pending-reconcile"])

    assert result.exit_code == 2
    assert "--all-running is required" in result.output


# ---------- AC 7: list --pending-reconcile ----------


def test_ac7_list_pending_reconcile_shows_marked_runs(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    r1 = _seed_run_in_state(migrated_engine, state="needs_reconciliation")
    _seed_run_in_state(migrated_engine, state="running")  # excluded

    result = runner.invoke(app, ["runs", "list", "--pending-reconcile"])

    assert result.exit_code == 0, result.output
    assert "1 run(s) pending reconciliation" in result.output
    assert str(r1)[:8] in result.output  # short_id prefix


def test_ac7_list_pending_reconcile_empty_message(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    _seed_run_in_state(migrated_engine, state="running")

    result = runner.invoke(app, ["runs", "list", "--pending-reconcile"])

    assert result.exit_code == 0, result.output
    assert "(no runs pending reconciliation)" in result.output


def test_ac7_list_requires_pending_reconcile_flag(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    result = runner.invoke(app, ["runs", "list"])

    assert result.exit_code == 2
    assert "--pending-reconcile is required" in result.output


# ---------- AC 10: idempotency ----------


def test_ac10_reconcile_repeat_is_noop(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    """Second reconcile on an already-reconciled run writes no new audit.

    The reconcile cycle is: needs_reconciliation → reconcile (writes
    AuditEvent, sets state=running). To run reconcile a second time
    we manually re-mark the run as needs_reconciliation; the second
    invocation should find zero unreconciled candidates because the
    AuditEvent from round 1 still exists.
    """
    run_id = _seed_run_in_state(migrated_engine, state="needs_reconciliation")
    _, tc = _seed_attempt_with_local_only_call(migrated_engine, run_id)

    first = runner.invoke(
        app, ["runs", "reconcile", str(run_id)], input="erfolgt\n"
    )
    assert first.exit_code == 0
    assert _audit_count_for_tool_call(migrated_engine, tc.id) == 1

    # Re-mark the run for reconciliation.
    _set_run_state(migrated_engine, run_id, "needs_reconciliation")

    second = runner.invoke(app, ["runs", "reconcile", str(run_id)])

    assert second.exit_code == 0, second.output
    assert "nothing to reconcile" in second.output
    # Critical: NO duplicate AuditEvent was written.
    assert _audit_count_for_tool_call(migrated_engine, tc.id) == 1


# ---------- Multi-tool-call ordering ----------


def test_reconcile_processes_tool_calls_in_ordinal_order(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run_in_state(migrated_engine, state="needs_reconciliation")
    attempt = _seed_attempt(migrated_engine, run_id)
    tc1 = _seed_local_only_call(migrated_engine, attempt, ordinal=1, tool_name="tool.one")
    tc2 = _seed_local_only_call(migrated_engine, attempt, ordinal=2, tool_name="tool.two")
    tc3 = _seed_local_only_call(migrated_engine, attempt, ordinal=3, tool_name="tool.three")

    # Three answers, one per call, in ordinal order.
    result = runner.invoke(
        app,
        ["runs", "reconcile", str(run_id)],
        input="erfolgt\nunsicher\nnicht_erfolgt\n",
    )

    assert result.exit_code == 0, result.output
    assert "3 unreconciled local-only effect(s)" in result.output

    # Verify each call got an AuditEvent with the expected reason.
    with migrated_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT subject_ref, reason FROM audit_event "
                "WHERE event_type = 'reconcile_decision' "
                "ORDER BY ts ASC"
            )
        ).fetchall()
    reasons = {r[0]: r[1] for r in rows}
    assert reasons[f"tool_call_record:{tc1.id}"] == "user-marked: erfolgt"
    assert reasons[f"tool_call_record:{tc2.id}"] == "user-marked: unsicher"
    assert reasons[f"tool_call_record:{tc3.id}"] == "user-marked: nicht_erfolgt"

    # Ordinal order in the prompt label: the tool names appear in the
    # output in the order tool.one → tool.two → tool.three.
    one_pos = result.output.find("tool.one")
    two_pos = result.output.find("tool.two")
    three_pos = result.output.find("tool.three")
    assert 0 <= one_pos < two_pos < three_pos


def test_reconcile_skips_natural_effects(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    """Only ``effect_class='local_only'`` calls show up as candidates."""
    run_id = _seed_run_in_state(migrated_engine, state="needs_reconciliation")
    attempt = _seed_attempt(migrated_engine, run_id)
    base = datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)
    insert_tool_call_record(
        migrated_engine,
        ToolCallRecord(
            run_attempt_ref=attempt.id,
            tool_call_ordinal=1,
            tool_name="git.commit",  # natural effect
            input_hash="abcdef012345",
            effect_class="natural",
            started_at=base + timedelta(seconds=1),
        ),
    )
    tc_local = _seed_local_only_call(migrated_engine, attempt, ordinal=2)

    result = runner.invoke(
        app, ["runs", "reconcile", str(run_id)], input="erfolgt\n"
    )

    assert result.exit_code == 0, result.output
    assert "1 unreconciled local-only effect(s)" in result.output
    assert _audit_count_for_tool_call(migrated_engine, tc_local.id) == 1
