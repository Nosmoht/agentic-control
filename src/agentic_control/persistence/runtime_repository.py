"""SQL-Core CRUD for the eight ADR-0011 Runtime-Record types (F0006).

Single insert path per record type — direct-SQL bypass is sperrt by
``tests/unit/test_orm_isolation`` and by an integration test that
re-asserts repository-only insert for ``policy_decision.tool_risk_match``
(Pydantic validates ``ToolRiskMatchOutput`` keys before the SQL write,
SQL only checks ``json_valid``).

`AuditEvent.subject_ref` is mixed-domain (polymorph or config path);
`PolicyDecisionRecord` is a discriminated union over `policy`. Inserts
serialise the discriminated payloads via Pydantic's TypeAdapter.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from agentic_control.contracts import (
    ApprovalRequest,
    AuditEvent,
    BudgetLedgerEntry,
    DispatchDecision,
    PolicyDecisionRecord,
    PolicyTag,
    RunAttempt,
    SandboxViolation,
    ToolCallRecord,
)
from agentic_control.persistence.repository import RepositoryError

_POLICY_ADAPTER: TypeAdapter[PolicyDecisionRecord] = TypeAdapter(PolicyDecisionRecord)
_AUDIT_ADAPTER: TypeAdapter[AuditEvent] = TypeAdapter(AuditEvent)
_APPROVAL_ADAPTER: TypeAdapter[ApprovalRequest] = TypeAdapter(ApprovalRequest)
_BUDGET_ADAPTER: TypeAdapter[BudgetLedgerEntry] = TypeAdapter(BudgetLedgerEntry)
_SANDBOX_ADAPTER: TypeAdapter[SandboxViolation] = TypeAdapter(SandboxViolation)
_DISPATCH_ADAPTER: TypeAdapter[DispatchDecision] = TypeAdapter(DispatchDecision)
_RUN_ATTEMPT_ADAPTER: TypeAdapter[RunAttempt] = TypeAdapter(RunAttempt)
_TOOL_CALL_ADAPTER: TypeAdapter[ToolCallRecord] = TypeAdapter(ToolCallRecord)


def _to_iso(dt: datetime) -> str:
    return dt.isoformat(sep=" ", timespec="seconds")


def _to_iso_or_none(dt: datetime | None) -> str | None:
    return _to_iso(dt) if dt is not None else None


# ---------- RunAttempt ----------


def insert_run_attempt(engine: Engine, attempt: RunAttempt) -> RunAttempt:
    sql = text(
        """
        INSERT INTO run_attempt
            (id, run_ref, attempt_ordinal, agent, model, sandbox_profile,
             prompt_hash, tool_allowlist, logs_ref, started_at, ended_at, exit_code)
        VALUES
            (:id, :run_ref, :ordinal, :agent, :model, :sandbox_profile,
             :prompt_hash, :tool_allowlist, :logs_ref, :started_at, :ended_at, :exit_code)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(attempt.id),
                    "run_ref": str(attempt.run_ref),
                    "ordinal": attempt.attempt_ordinal,
                    "agent": attempt.agent,
                    "model": attempt.model,
                    "sandbox_profile": attempt.sandbox_profile,
                    "prompt_hash": attempt.prompt_hash,
                    "tool_allowlist": json.dumps(attempt.tool_allowlist),
                    "logs_ref": attempt.logs_ref,
                    "started_at": _to_iso(attempt.started_at),
                    "ended_at": _to_iso_or_none(attempt.ended_at),
                    "exit_code": attempt.exit_code,
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return attempt


# ---------- AuditEvent ----------


def insert_audit_event(engine: Engine, event: AuditEvent) -> AuditEvent:
    sql = text(
        """
        INSERT INTO audit_event
            (id, ts, actor, subject_ref, event_type, before_hash, after_hash,
             before_value, after_value, reason, run_attempt_ref)
        VALUES
            (:id, :ts, :actor, :subject_ref, :event_type, :before_hash, :after_hash,
             :before_value, :after_value, :reason, :run_attempt_ref)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(event.id),
                    "ts": _to_iso(event.ts),
                    "actor": event.actor,
                    "subject_ref": event.subject_ref,
                    "event_type": event.event_type,
                    "before_hash": event.before_hash,
                    "after_hash": event.after_hash,
                    "before_value": event.before_value,
                    "after_value": event.after_value,
                    "reason": event.reason,
                    "run_attempt_ref": (
                        str(event.run_attempt_ref) if event.run_attempt_ref else None
                    ),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return event


# ---------- ApprovalRequest ----------


def insert_approval_request(engine: Engine, req: ApprovalRequest) -> ApprovalRequest:
    sql = text(
        """
        INSERT INTO approval_request
            (id, subject_ref, risk_class, question, state, decider,
             created_at, decided_at, deadline, run_attempt_ref)
        VALUES
            (:id, :subject_ref, :risk_class, :question, :state, :decider,
             :created_at, :decided_at, :deadline, :run_attempt_ref)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(req.id),
                    "subject_ref": str(req.subject_ref),
                    "risk_class": req.risk_class,
                    "question": req.question,
                    "state": req.state,
                    "decider": req.decider,
                    "created_at": _to_iso(req.created_at),
                    "decided_at": _to_iso_or_none(req.decided_at),
                    "deadline": _to_iso_or_none(req.deadline),
                    "run_attempt_ref": str(req.run_attempt_ref) if req.run_attempt_ref else None,
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return req


# ---------- BudgetLedgerEntry ----------


def insert_budget_ledger_entry(engine: Engine, entry: BudgetLedgerEntry) -> BudgetLedgerEntry:
    sql = text(
        """
        INSERT INTO budget_ledger_entry
            (id, ts, scope, run_attempt_ref, run_attempt_hash_anchor, project_ref,
             model, pre_call_projection_usd, actual_usd, cache_hit)
        VALUES
            (:id, :ts, :scope, :run_attempt_ref, :hash_anchor, :project_ref,
             :model, :pre_call, :actual, :cache_hit)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(entry.id),
                    "ts": _to_iso(entry.ts),
                    "scope": entry.scope,
                    "run_attempt_ref": str(entry.run_attempt_ref),
                    "hash_anchor": entry.run_attempt_hash_anchor,
                    "project_ref": str(entry.project_ref) if entry.project_ref else None,
                    "model": entry.model,
                    # Decimal → str preserves exact decimal semantics across
                    # SQLite NUMERIC. Float-bound would round-trip through
                    # IEEE 754 and accumulate error in the budget ledger.
                    "pre_call": str(entry.pre_call_projection_usd),
                    "actual": (
                        str(entry.actual_usd) if entry.actual_usd is not None else None
                    ),
                    "cache_hit": 1 if entry.cache_hit else 0,
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return entry


# ---------- ToolCallRecord ----------


def insert_tool_call_record(engine: Engine, record: ToolCallRecord) -> ToolCallRecord:
    sql = text(
        """
        INSERT INTO tool_call_record
            (id, run_attempt_ref, tool_call_ordinal, tool_name, input_hash,
             output_ref, duration_ms, exit_code, idempotency_key, effect_class,
             started_at, ended_at)
        VALUES
            (:id, :run_attempt_ref, :ordinal, :tool_name, :input_hash,
             :output_ref, :duration_ms, :exit_code, :idempotency_key, :effect_class,
             :started_at, :ended_at)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(record.id),
                    "run_attempt_ref": str(record.run_attempt_ref),
                    "ordinal": record.tool_call_ordinal,
                    "tool_name": record.tool_name,
                    "input_hash": record.input_hash,
                    "output_ref": record.output_ref,
                    "duration_ms": record.duration_ms,
                    "exit_code": record.exit_code,
                    "idempotency_key": record.idempotency_key,
                    "effect_class": record.effect_class,
                    "started_at": _to_iso(record.started_at),
                    "ended_at": _to_iso_or_none(record.ended_at),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return record


# ---------- PolicyDecisionRecord (discriminated union) ----------


def insert_policy_decision(
    engine: Engine, decision: PolicyDecisionRecord
) -> PolicyDecisionRecord:
    """Insert a PolicyDecisionRecord. Pydantic ToolRiskMatchOutput validation
    happens at model construction; the repository serialises the validated
    payload to JSON columns. Direct SQL inserts bypass this contract — the
    integration test ``test_policy_decision_tool_risk_match_repository_only``
    asserts repository-only invariance.
    """
    payload = _POLICY_ADAPTER.dump_python(decision, mode="json")
    sql = text(
        """
        INSERT INTO policy_decision
            (id, ts, policy, subject_ref, inputs, output, run_attempt_ref)
        VALUES
            (:id, :ts, :policy, :subject_ref, :inputs, :output, :run_attempt_ref)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": payload["id"],
                    "ts": payload["ts"],
                    "policy": payload["policy"],
                    "subject_ref": payload["subject_ref"],
                    "inputs": json.dumps(payload["inputs"]),
                    "output": json.dumps(payload["output"]),
                    "run_attempt_ref": payload["run_attempt_ref"],
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return decision


# ---------- SandboxViolation ----------


def insert_sandbox_violation(
    engine: Engine, violation: SandboxViolation
) -> SandboxViolation:
    sql = text(
        """
        INSERT INTO sandbox_violation
            (id, run_attempt_ref, ts, category, detail)
        VALUES
            (:id, :run_attempt_ref, :ts, :category, :detail)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(violation.id),
                    "run_attempt_ref": str(violation.run_attempt_ref),
                    "ts": _to_iso(violation.ts),
                    "category": violation.category,
                    "detail": json.dumps(violation.detail),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return violation


# ---------- DispatchDecision ----------


def insert_dispatch_decision(
    engine: Engine, decision: DispatchDecision
) -> DispatchDecision:
    sql = text(
        """
        INSERT INTO dispatch_decision
            (id, run_attempt_ref, adapter, model, mode, reason, evidence_refs, decided_at)
        VALUES
            (:id, :run_attempt_ref, :adapter, :model, :mode, :reason, :evidence_refs, :decided_at)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(decision.id),
                    "run_attempt_ref": str(decision.run_attempt_ref),
                    "adapter": decision.adapter,
                    "model": decision.model,
                    "mode": decision.mode,
                    "reason": decision.reason,
                    # Always emit a JSON array (possibly ``[]``) so reads
                    # round-trip to ``list[EvidenceRef]`` consistently.
                    "evidence_refs": json.dumps(decision.evidence_refs),
                    "decided_at": _to_iso(decision.decided_at),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return decision


# ---------- Reads (used by tests + later PRs) ----------


def get_run_attempt(engine: Engine, attempt_id: str) -> dict[str, Any] | None:
    """Fetch a run_attempt row as a raw dict.

    NOTE: this returns the raw column values; ``tool_allowlist`` is the
    JSON-encoded source string, not a parsed list, and ``started_at``/
    ``ended_at`` are ISO-8601 strings, not aware datetimes. PR2 (`runs
    inspect`) introduces a typed ``RunAttempt`` re-hydration layer; for
    F0006a this asymmetry is intentional — repository inserts go through
    Pydantic, reads return raw rows for the inspect-CLI to format.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM run_attempt WHERE id = :id"), {"id": attempt_id}
        ).first()
    return dict(row._mapping) if row else None


def list_tool_calls_for_attempt(engine: Engine, attempt_id: str) -> list[dict[str, Any]]:
    """List tool_call_record rows for a run_attempt, ordered by ordinal.

    Returns raw dicts (see ``get_run_attempt`` for the same asymmetry note).
    """
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM tool_call_record WHERE run_attempt_ref = :a "
                "ORDER BY tool_call_ordinal ASC"
            ),
            {"a": attempt_id},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


# ---------- Typed Re-Hydration (PR2: runs inspect) ----------
#
# These read helpers re-hydrate raw rows back into Pydantic models, complementing
# the existing raw-dict helpers (get_run_attempt, list_tool_calls_for_attempt).
# Inserts go through Pydantic; reads now do too — so the inspect CLI can rely on
# typed objects (Decimal money, aware-UTC datetimes, validated discriminated unions).


def _row_to_run_attempt(row: Any) -> RunAttempt:
    d = dict(row._mapping)
    return _RUN_ATTEMPT_ADAPTER.validate_python(
        {
            "id": d["id"],
            "run_ref": d["run_ref"],
            "attempt_ordinal": d["attempt_ordinal"],
            "agent": d["agent"],
            "model": d["model"],
            "sandbox_profile": d["sandbox_profile"],
            "prompt_hash": d["prompt_hash"],
            "tool_allowlist": json.loads(d["tool_allowlist"]),
            "logs_ref": d["logs_ref"],
            "started_at": d["started_at"],
            "ended_at": d["ended_at"],
            "exit_code": d["exit_code"],
        }
    )


def get_run_attempt_typed(engine: Engine, attempt_id: uuid.UUID) -> RunAttempt | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM run_attempt WHERE id = :id"), {"id": str(attempt_id)}
        ).first()
    return _row_to_run_attempt(row) if row else None


def list_run_attempts_for_run(engine: Engine, run_id: uuid.UUID) -> list[RunAttempt]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM run_attempt WHERE run_ref = :r "
                "ORDER BY attempt_ordinal ASC, started_at ASC"
            ),
            {"r": str(run_id)},
        ).fetchall()
    return [_row_to_run_attempt(r) for r in rows]


def _row_to_tool_call(row: Any) -> ToolCallRecord:
    d = dict(row._mapping)
    return _TOOL_CALL_ADAPTER.validate_python(
        {
            "id": d["id"],
            "run_attempt_ref": d["run_attempt_ref"],
            "tool_call_ordinal": d["tool_call_ordinal"],
            "tool_name": d["tool_name"],
            "input_hash": d["input_hash"],
            "output_ref": d["output_ref"],
            "duration_ms": d["duration_ms"],
            "exit_code": d["exit_code"],
            "idempotency_key": d["idempotency_key"],
            "effect_class": d["effect_class"],
            "started_at": d["started_at"],
            "ended_at": d["ended_at"],
        }
    )


def list_tool_calls_for_attempt_typed(
    engine: Engine, attempt_id: uuid.UUID
) -> list[ToolCallRecord]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM tool_call_record WHERE run_attempt_ref = :a "
                "ORDER BY tool_call_ordinal ASC"
            ),
            {"a": str(attempt_id)},
        ).fetchall()
    return [_row_to_tool_call(r) for r in rows]


def _row_to_audit_event(row: Any) -> AuditEvent:
    d = dict(row._mapping)
    return _AUDIT_ADAPTER.validate_python(
        {
            "id": d["id"],
            "ts": d["ts"],
            "actor": d["actor"],
            "subject_ref": d["subject_ref"],
            "event_type": d["event_type"],
            "before_hash": d["before_hash"],
            "after_hash": d["after_hash"],
            "before_value": d["before_value"],
            "after_value": d["after_value"],
            "reason": d["reason"],
            "run_attempt_ref": d["run_attempt_ref"],
        }
    )


def list_audit_events_for_attempt(
    engine: Engine, attempt_id: uuid.UUID
) -> list[AuditEvent]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM audit_event WHERE run_attempt_ref = :a ORDER BY ts ASC"
            ),
            {"a": str(attempt_id)},
        ).fetchall()
    return [_row_to_audit_event(r) for r in rows]


def _row_to_policy_decision(row: Any) -> PolicyDecisionRecord:
    d = dict(row._mapping)
    # The discriminated union resolves on `policy`. The TypeAdapter validates the
    # raw `output` dict; for `policy='tool_risk_match'` rows it re-instantiates
    # `PolicyDecisionToolRiskMatch` whose `output` is a `ToolRiskMatchOutput`.
    return _POLICY_ADAPTER.validate_python(
        {
            "id": d["id"],
            "ts": d["ts"],
            "policy": d["policy"],
            "subject_ref": d["subject_ref"],
            "inputs": json.loads(d["inputs"]),
            "output": json.loads(d["output"]),
            "run_attempt_ref": d["run_attempt_ref"],
        }
    )


def list_policy_decisions_for_attempt(
    engine: Engine,
    attempt_id: uuid.UUID,
    policy: PolicyTag | None = None,
) -> list[PolicyDecisionRecord]:
    if policy is None:
        sql = text(
            "SELECT * FROM policy_decision WHERE run_attempt_ref = :a ORDER BY ts ASC"
        )
        params: dict[str, Any] = {"a": str(attempt_id)}
    else:
        sql = text(
            "SELECT * FROM policy_decision WHERE run_attempt_ref = :a AND policy = :p "
            "ORDER BY ts ASC"
        )
        params = {"a": str(attempt_id), "p": policy}
    with engine.connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_policy_decision(r) for r in rows]


def _row_to_approval_request(row: Any) -> ApprovalRequest:
    d = dict(row._mapping)
    return _APPROVAL_ADAPTER.validate_python(
        {
            "id": d["id"],
            "subject_ref": d["subject_ref"],
            "risk_class": d["risk_class"],
            "question": d["question"],
            "state": d["state"],
            "decider": d["decider"],
            "created_at": d["created_at"],
            "decided_at": d["decided_at"],
            "deadline": d["deadline"],
            "run_attempt_ref": d["run_attempt_ref"],
        }
    )


def list_approval_requests_for_attempt(
    engine: Engine, attempt_id: uuid.UUID
) -> list[ApprovalRequest]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM approval_request WHERE run_attempt_ref = :a "
                "ORDER BY created_at ASC"
            ),
            {"a": str(attempt_id)},
        ).fetchall()
    return [_row_to_approval_request(r) for r in rows]


def _row_to_budget_ledger_entry(row: Any) -> BudgetLedgerEntry:
    d = dict(row._mapping)
    # USD round-trip via Decimal(str(...)) — SQLite's NUMERIC affinity may have
    # coerced a string-bound value back to REAL on read. Forcing through `str`
    # recovers the textual decimal representation that the writer bound.
    pre_call = Decimal(str(d["pre_call_projection_usd"]))
    actual_raw = d["actual_usd"]
    actual = Decimal(str(actual_raw)) if actual_raw is not None else None
    return _BUDGET_ADAPTER.validate_python(
        {
            "id": d["id"],
            "ts": d["ts"],
            "scope": d["scope"],
            "run_attempt_ref": d["run_attempt_ref"],
            "run_attempt_hash_anchor": d["run_attempt_hash_anchor"],
            "project_ref": d["project_ref"],
            "model": d["model"],
            "pre_call_projection_usd": pre_call,
            "actual_usd": actual,
            "cache_hit": bool(d["cache_hit"]),
        }
    )


def list_budget_ledger_entries_for_attempt(
    engine: Engine, attempt_id: uuid.UUID
) -> list[BudgetLedgerEntry]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM budget_ledger_entry WHERE run_attempt_ref = :a "
                "ORDER BY ts ASC"
            ),
            {"a": str(attempt_id)},
        ).fetchall()
    return [_row_to_budget_ledger_entry(r) for r in rows]


def _row_to_sandbox_violation(row: Any) -> SandboxViolation:
    d = dict(row._mapping)
    return _SANDBOX_ADAPTER.validate_python(
        {
            "id": d["id"],
            "run_attempt_ref": d["run_attempt_ref"],
            "ts": d["ts"],
            "category": d["category"],
            "detail": json.loads(d["detail"]),
        }
    )


def list_sandbox_violations_for_attempt(
    engine: Engine, attempt_id: uuid.UUID
) -> list[SandboxViolation]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM sandbox_violation WHERE run_attempt_ref = :a "
                "ORDER BY ts ASC"
            ),
            {"a": str(attempt_id)},
        ).fetchall()
    return [_row_to_sandbox_violation(r) for r in rows]


def _row_to_dispatch_decision(row: Any) -> DispatchDecision:
    d = dict(row._mapping)
    return _DISPATCH_ADAPTER.validate_python(
        {
            "id": d["id"],
            "run_attempt_ref": d["run_attempt_ref"],
            "adapter": d["adapter"],
            "model": d["model"],
            "mode": d["mode"],
            "reason": d["reason"],
            "evidence_refs": json.loads(d["evidence_refs"]),
            "decided_at": d["decided_at"],
        }
    )


def get_dispatch_decision_for_attempt(
    engine: Engine, attempt_id: uuid.UUID
) -> DispatchDecision | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM dispatch_decision WHERE run_attempt_ref = :a"),
            {"a": str(attempt_id)},
        ).first()
    return _row_to_dispatch_decision(row) if row else None


__all__ = [
    "get_dispatch_decision_for_attempt",
    "get_run_attempt",
    "get_run_attempt_typed",
    "insert_approval_request",
    "insert_audit_event",
    "insert_budget_ledger_entry",
    "insert_dispatch_decision",
    "insert_policy_decision",
    "insert_run_attempt",
    "insert_sandbox_violation",
    "insert_tool_call_record",
    "list_approval_requests_for_attempt",
    "list_audit_events_for_attempt",
    "list_budget_ledger_entries_for_attempt",
    "list_policy_decisions_for_attempt",
    "list_run_attempts_for_run",
    "list_sandbox_violations_for_attempt",
    "list_tool_calls_for_attempt",
    "list_tool_calls_for_attempt_typed",
]
