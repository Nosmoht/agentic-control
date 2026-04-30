"""Pydantic v2 contracts for the eight ADR-0011 Runtime-Record types (F0006).

ADR-0018 makes these the canonical schema; SQL DDL in
`migrations/versions/0002` mirrors the same shape. Per CLAUDE.md decision
log (2026-04-30) the validation responsibility split is:

* SQL CHECK constraints enforce shape (length, enum membership,
  json_valid, FK).
* Pydantic enforces structural payload requirements that SQLite cannot
  express — most notably the ``tool_risk_match`` discriminated arm of
  ``PolicyDecisionRecord``, whose ``output`` JSON must carry the four
  fields ``matched_pattern``/``risk``/``approval``/``default_hit``
  (ADR-0015 §85, F0006 AC 12).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Discriminator, Field

from agentic_control.contracts.audit_subject import AuditSubjectRef
from agentic_control.contracts.ids import UUIDv7, new_id
from agentic_control.contracts.lifecycle import (
    Adapter,
    ApprovalRequestState,
    AuditEventType,
    BudgetScope,
    DispatchMode,
    DispatchReason,
    EffectClass,
    RiskClass,
)


def _utcnow() -> datetime:
    return datetime.now()


class _RecordBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------- RunAttempt ----------


class RunAttempt(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    run_ref: UUIDv7
    attempt_ordinal: int = Field(ge=1)
    agent: str = Field(min_length=1, max_length=200)
    model: str = Field(min_length=1, max_length=200)
    sandbox_profile: str = Field(min_length=1, max_length=200)
    prompt_hash: str = Field(min_length=12, max_length=12)
    tool_allowlist: list[str] = Field(default_factory=list)
    logs_ref: str = Field(min_length=1)
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: datetime | None = None
    exit_code: int | None = None


# ---------- AuditEvent ----------


class AuditEvent(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    ts: datetime = Field(default_factory=_utcnow)
    actor: str = Field(min_length=1, max_length=200)
    subject_ref: AuditSubjectRef
    event_type: AuditEventType
    before_hash: str | None = Field(default=None, min_length=64, max_length=64)
    after_hash: str | None = Field(default=None, min_length=64, max_length=64)
    before_value: str | None = None
    after_value: str | None = None
    reason: str | None = None
    run_attempt_ref: UUIDv7 | None = None


# ---------- ApprovalRequest ----------


class ApprovalRequest(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    subject_ref: UUIDv7
    risk_class: RiskClass
    question: str = Field(min_length=1)
    state: ApprovalRequestState = "waiting_for_approval"
    decider: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    decided_at: datetime | None = None
    deadline: datetime | None = None
    run_attempt_ref: UUIDv7 | None = None


# ---------- BudgetLedgerEntry ----------


class BudgetLedgerEntry(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    ts: datetime = Field(default_factory=_utcnow)
    scope: BudgetScope
    run_attempt_ref: UUIDv7
    run_attempt_hash_anchor: str = Field(min_length=12, max_length=64)
    project_ref: UUIDv7 | None = None
    model: str = Field(min_length=1, max_length=200)
    pre_call_projection_usd: float = Field(ge=0.0)
    actual_usd: float | None = Field(default=None, ge=0.0)
    cache_hit: bool = False


# ---------- ToolCallRecord ----------


class ToolCallRecord(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    run_attempt_ref: UUIDv7
    tool_call_ordinal: int = Field(ge=1)
    tool_name: str = Field(min_length=1, max_length=200)
    input_hash: str = Field(min_length=12, max_length=12)
    output_ref: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    exit_code: int | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)
    effect_class: EffectClass
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: datetime | None = None


# ---------- PolicyDecisionRecord (discriminated union) ----------


class ToolRiskMatchOutput(BaseModel):
    """Required output payload for ``policy='tool_risk_match'`` (ADR-0015, F0006 AC 12)."""

    model_config = ConfigDict(extra="forbid")
    matched_pattern: str = Field(min_length=1)
    risk: RiskClass
    approval: Literal["never", "required", "policy_gated"]
    default_hit: bool


class _PolicyDecisionBase(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    ts: datetime = Field(default_factory=_utcnow)
    subject_ref: str = Field(min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    run_attempt_ref: UUIDv7 | None = None


class PolicyDecisionGeneric(_PolicyDecisionBase):
    """admission | dispatch | budget_gate_override | hitl_trigger — opaque output JSON."""

    policy: Literal["admission", "dispatch", "budget_gate_override", "hitl_trigger"]
    output: dict[str, Any] = Field(default_factory=dict)


class PolicyDecisionToolRiskMatch(_PolicyDecisionBase):
    """tool_risk_match — output payload is structurally constrained (ADR-0015)."""

    policy: Literal["tool_risk_match"] = "tool_risk_match"
    output: ToolRiskMatchOutput


PolicyDecisionRecord = Annotated[
    PolicyDecisionGeneric | PolicyDecisionToolRiskMatch,
    Discriminator("policy"),
]


# ---------- SandboxViolation ----------


class SandboxViolation(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    run_attempt_ref: UUIDv7
    ts: datetime = Field(default_factory=_utcnow)
    category: str = Field(min_length=1, max_length=200)
    detail: dict[str, Any] = Field(default_factory=dict)


# ---------- DispatchDecision ----------


class DispatchDecision(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    run_attempt_ref: UUIDv7
    adapter: Adapter
    model: str = Field(min_length=1, max_length=200)
    mode: DispatchMode
    reason: DispatchReason
    evidence_refs: list[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=_utcnow)


__all__ = [
    "ApprovalRequest",
    "AuditEvent",
    "BudgetLedgerEntry",
    "DispatchDecision",
    "PolicyDecisionGeneric",
    "PolicyDecisionRecord",
    "PolicyDecisionToolRiskMatch",
    "RunAttempt",
    "SandboxViolation",
    "ToolCallRecord",
    "ToolRiskMatchOutput",
]
