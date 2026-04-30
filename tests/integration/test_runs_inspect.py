"""F0006b · `agentctl runs inspect <id>` — AC 4, 11, 12, 13 + UX cases."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import Engine, text
from typer.testing import CliRunner

from agentic_control.cli.main import app
from agentic_control.contracts import (
    ApprovalRequest,
    AuditEvent,
    BudgetLedgerEntry,
    DispatchDecision,
    PolicyDecisionGeneric,
    PolicyDecisionToolRiskMatch,
    Project,
    RunAttempt,
    SandboxViolation,
    ToolCallRecord,
    ToolRiskMatchOutput,
    WorkItem,
    new_id,
)
from agentic_control.persistence import (
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


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch, db_url: str, migrated_engine: Engine) -> CliRunner:
    monkeypatch.setenv("AGENTIC_CONTROL_DB_URL", db_url)
    return CliRunner()


def _seed_run(engine: Engine) -> uuid.UUID:
    """Insert a project → work_item → run, return the run id."""
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
    return run_id


def _seed_attempt(engine: Engine, run_id: uuid.UUID, ordinal: int = 1) -> RunAttempt:
    return insert_run_attempt(
        engine,
        RunAttempt(
            run_ref=run_id,
            attempt_ordinal=ordinal,
            agent="claude",
            model="claude-sonnet-4-6",
            sandbox_profile="standard",
            prompt_hash="abcdef012345",
            tool_allowlist=["git.commit"],
            logs_ref=f"/tmp/run-{ordinal}.jsonl",
        ),
    )


def _seed_full_run(engine: Engine) -> tuple[uuid.UUID, RunAttempt]:
    """Seed a run with 1 attempt, 2 tool calls, 1 approval, 1 budget entry, dispatch."""
    run_id = _seed_run(engine)
    attempt = _seed_attempt(engine, run_id)
    base = datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)

    insert_dispatch_decision(
        engine,
        DispatchDecision(
            run_attempt_ref=attempt.id,
            adapter="claude_code",
            model="claude-sonnet-4-6",
            mode="pinned",
            reason="pin",
            decided_at=base,
        ),
    )
    insert_tool_call_record(
        engine,
        ToolCallRecord(
            run_attempt_ref=attempt.id,
            tool_call_ordinal=1,
            tool_name="git.commit",
            input_hash="abcdef012345",
            effect_class="natural",
            started_at=base + timedelta(seconds=1),
        ),
    )
    insert_tool_call_record(
        engine,
        ToolCallRecord(
            run_attempt_ref=attempt.id,
            tool_call_ordinal=2,
            tool_name="gh.issue.comment",
            input_hash="abcdef012345",
            idempotency_key="key-42",
            effect_class="local_only",
            started_at=base + timedelta(seconds=3),
        ),
    )
    p = insert_project(engine, Project(title="P-approval-host"))
    w = insert_work_item(engine, WorkItem(project_ref=p.id, title="WI"))
    insert_approval_request(
        engine,
        ApprovalRequest(
            subject_ref=w.id,
            risk_class="high",
            question="Run rm -rf?",
            created_at=base + timedelta(seconds=2),
            run_attempt_ref=attempt.id,
        ),
    )
    insert_budget_ledger_entry(
        engine,
        BudgetLedgerEntry(
            scope="request",
            run_attempt_ref=attempt.id,
            run_attempt_hash_anchor="abcdef012345",
            model="claude-sonnet-4-6",
            pre_call_projection_usd=Decimal("0.05"),
            actual_usd=Decimal("0.04"),
            ts=base + timedelta(seconds=4),
        ),
    )
    return run_id, attempt


# ---------- AC 4: all four record types appear, sorted by timestamp ----------


def test_ac4_inspect_shows_all_record_types_sorted(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id, _ = _seed_full_run(migrated_engine)
    result = runner.invoke(app, ["runs", "inspect", str(run_id)])
    assert result.exit_code == 0, result.output
    assert "tool calls (2)" in result.output
    assert "git.commit" in result.output
    assert "gh.issue.comment" in result.output
    assert "approvals (1)" in result.output
    assert "Run rm -rf?" in result.output
    assert "budget (1 entries" in result.output
    # The 2nd tool call (ordinal=2) appears after the 1st.
    idx_first = result.output.index("git.commit")
    idx_second = result.output.index("gh.issue.comment")
    assert idx_first < idx_second


# ---------- AC 11: dispatch_decision shows exactly once per attempt ----------


def test_ac11_dispatch_decision_appears_once(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id, _ = _seed_full_run(migrated_engine)
    result = runner.invoke(app, ["runs", "inspect", str(run_id)])
    assert result.exit_code == 0
    assert result.output.count("dispatch: adapter=claude_code") == 1


def test_ac11_attempt_without_dispatch_renders_cleanly(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run(migrated_engine)
    _seed_attempt(migrated_engine, run_id)
    result = runner.invoke(app, ["runs", "inspect", str(run_id)])
    assert result.exit_code == 0
    assert "dispatch:" not in result.output  # no dispatch row yet


# ---------- AC 12: --policy filter + tool_risk_match payload visibility ----------


def test_ac12_policy_filter_narrows_to_one_tag(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run(migrated_engine)
    attempt = _seed_attempt(migrated_engine, run_id)
    insert_policy_decision(
        migrated_engine,
        PolicyDecisionGeneric(
            policy="admission",
            subject_ref=f"work_item:{new_id()}",
            inputs={},
            output={"verdict": "accept"},
            run_attempt_ref=attempt.id,
        ),
    )
    insert_policy_decision(
        migrated_engine,
        PolicyDecisionGeneric(
            policy="dispatch",
            subject_ref=f"work_item:{new_id()}",
            inputs={},
            output={"adapter": "claude_code"},
            run_attempt_ref=attempt.id,
        ),
    )
    result = runner.invoke(
        app, ["runs", "inspect", str(run_id), "--policy", "admission"]
    )
    assert result.exit_code == 0, result.output
    assert "policies (1)" in result.output
    assert "admission" in result.output
    assert "dispatch  " not in result.output  # the dispatch policy row is filtered out


def test_ac12_unknown_policy_tag_user_error(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run(migrated_engine)
    result = runner.invoke(app, ["runs", "inspect", str(run_id), "--policy", "bogus"])
    assert result.exit_code != 0
    assert "unknown policy tag" in result.output


def test_ac12_tool_risk_match_payload_visible(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run(migrated_engine)
    attempt = _seed_attempt(migrated_engine, run_id)
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
    insert_policy_decision(
        migrated_engine,
        PolicyDecisionToolRiskMatch(
            subject_ref=f"tool_call_record:{tool_call.id}",
            inputs={"tool": "rm.recursive"},
            output=ToolRiskMatchOutput(
                matched_pattern="rm -rf",
                risk="irreversible",
                approval="required",
                default_hit=False,
            ),
            run_attempt_ref=attempt.id,
        ),
    )
    result = runner.invoke(
        app, ["runs", "inspect", str(run_id), "--policy", "tool_risk_match"]
    )
    assert result.exit_code == 0, result.output
    for needle in ("matched=rm -rf", "risk=irreversible", "approval=required", "default_hit=False"):
        assert needle in result.output


# ---------- AC 13: SandboxViolation appears + alert hook fires ----------


def test_ac13_sandbox_violation_triggers_alert_logger(
    runner: CliRunner, migrated_engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    run_id = _seed_run(migrated_engine)
    attempt = _seed_attempt(migrated_engine, run_id)
    insert_sandbox_violation(
        migrated_engine,
        SandboxViolation(
            run_attempt_ref=attempt.id,
            category="egress_denied",
            detail={"host": "evil.example.com", "port": 443},
        ),
    )
    with caplog.at_level(logging.WARNING, logger="agentic_control.alerts"):
        result = runner.invoke(app, ["runs", "inspect", str(run_id)])
    assert result.exit_code == 0
    assert "sandbox violations (1)" in result.output
    assert "egress_denied" in result.output
    warns = [r for r in caplog.records if r.name == "agentic_control.alerts"]
    assert any("egress_denied" in r.getMessage() for r in warns), warns


# ---------- Prefix resolution + UX errors ----------


def test_inspect_resolves_4_char_prefix(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run(migrated_engine)
    prefix = str(run_id)[:8]
    result = runner.invoke(app, ["runs", "inspect", prefix])
    assert result.exit_code == 0
    assert str(run_id) in result.output


def test_inspect_short_prefix_user_error(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    _seed_run(migrated_engine)
    result = runner.invoke(app, ["runs", "inspect", "abc"])  # 3 chars < MIN_PREFIX_LEN
    assert result.exit_code != 0
    assert "too short" in result.output


def test_inspect_unknown_run_user_error(runner: CliRunner) -> None:
    result = runner.invoke(app, ["runs", "inspect", str(new_id())])
    assert result.exit_code != 0
    assert "no run" in result.output


# ---------- JSON output ----------


def test_inspect_output_json_emits_valid_dict(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id, _ = _seed_full_run(migrated_engine)
    result = runner.invoke(app, ["runs", "inspect", str(run_id), "--output-json"])
    assert result.exit_code == 0, result.output
    parsed = json.loads(result.output)
    assert "run" in parsed
    assert "attempts" in parsed
    assert isinstance(parsed["attempts"], list)
    assert len(parsed["attempts"]) == 1
    attempt_view = parsed["attempts"][0]
    assert attempt_view["attempt"]["agent"] == "claude"
    assert len(attempt_view["tool_calls"]) == 2

    # Decimal preserved as string (not float) per ADR-0018 invariant.
    budget_entry = attempt_view["budget_entries"][0]
    assert budget_entry["pre_call_projection_usd"] == "0.050000"
    assert budget_entry["actual_usd"] == "0.040000"

    # Aware-UTC datetime preserved with offset (ISO-8601 form).
    started = attempt_view["attempt"]["started_at"]
    assert started.endswith("+00:00") or started.endswith("Z"), started


# ---------- Empty run ----------


def test_inspect_run_with_no_attempts_exits_zero(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run(migrated_engine)
    result = runner.invoke(app, ["runs", "inspect", str(run_id)])
    assert result.exit_code == 0
    assert "(no attempts)" in result.output


# ---------- AC 13 follow-up: per-violation alert contract ----------


def test_ac13_alert_fires_per_violation(
    runner: CliRunner, migrated_engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    run_id = _seed_run(migrated_engine)
    attempt = _seed_attempt(migrated_engine, run_id)
    for cat in ("egress_denied", "fs_write_denied"):
        insert_sandbox_violation(
            migrated_engine,
            SandboxViolation(run_attempt_ref=attempt.id, category=cat, detail={}),
        )
    with caplog.at_level(logging.WARNING, logger="agentic_control.alerts"):
        result = runner.invoke(app, ["runs", "inspect", str(run_id)])
    assert result.exit_code == 0, result.output
    warns = [r for r in caplog.records if r.name == "agentic_control.alerts"]
    assert len(warns) == 2
    categories_seen = {r.getMessage() for r in warns}
    assert any("egress_denied" in m for m in categories_seen)
    assert any("fs_write_denied" in m for m in categories_seen)


# ---------- AC 12 follow-up: filter with no matches surfaces the empty set ----------


def test_ac12_filter_with_no_matches_shows_zero_count(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    """Per #11 review: a `--policy <tag>` filter that matches no rows must
    still surface the filter context so the user can tell their query ran."""
    run_id = _seed_run(migrated_engine)
    attempt = _seed_attempt(migrated_engine, run_id)
    insert_policy_decision(
        migrated_engine,
        PolicyDecisionGeneric(
            policy="admission",
            subject_ref=f"work_item:{new_id()}",
            inputs={},
            output={},
            run_attempt_ref=attempt.id,
        ),
    )
    result = runner.invoke(
        app, ["runs", "inspect", str(run_id), "--policy", "tool_risk_match"]
    )
    assert result.exit_code == 0, result.output
    assert "policies (0) [filter=tool_risk_match]" in result.output


# ---------- Audit events display ----------


def test_inspect_renders_audit_events(
    runner: CliRunner, migrated_engine: Engine
) -> None:
    run_id = _seed_run(migrated_engine)
    attempt = _seed_attempt(migrated_engine, run_id)
    insert_audit_event(
        migrated_engine,
        AuditEvent(
            actor="agentctl test",
            subject_ref=f"run:{run_id}",
            event_type="state_transition",
            run_attempt_ref=attempt.id,
        ),
    )
    result = runner.invoke(app, ["runs", "inspect", str(run_id)])
    assert result.exit_code == 0, result.output
    assert "audit (1)" in result.output
    assert "state_transition" in result.output
