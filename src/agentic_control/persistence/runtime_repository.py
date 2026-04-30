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
from datetime import datetime
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
    RunAttempt,
    SandboxViolation,
    ToolCallRecord,
)
from agentic_control.persistence.repository import RepositoryError

_POLICY_ADAPTER: TypeAdapter[PolicyDecisionRecord] = TypeAdapter(PolicyDecisionRecord)


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
                    "pre_call": entry.pre_call_projection_usd,
                    "actual": entry.actual_usd,
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
                    "evidence_refs": json.dumps(decision.evidence_refs)
                    if decision.evidence_refs
                    else None,
                    "decided_at": _to_iso(decision.decided_at),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return decision


# ---------- Reads (used by tests + later PRs) ----------


def get_run_attempt(engine: Engine, attempt_id: str) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM run_attempt WHERE id = :id"), {"id": attempt_id}
        ).first()
    return dict(row._mapping) if row else None


def list_tool_calls_for_attempt(engine: Engine, attempt_id: str) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM tool_call_record WHERE run_attempt_ref = :a "
                "ORDER BY tool_call_ordinal ASC"
            ),
            {"a": attempt_id},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


__all__ = [
    "get_run_attempt",
    "insert_approval_request",
    "insert_audit_event",
    "insert_budget_ledger_entry",
    "insert_dispatch_decision",
    "insert_policy_decision",
    "insert_run_attempt",
    "insert_sandbox_violation",
    "insert_tool_call_record",
    "list_tool_calls_for_attempt",
]
