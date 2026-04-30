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

Money fields use ``Decimal`` end-to-end (USD, six-decimal quantize) per
the F0006a follow-up review — float-USD is a known rounding-error class
in audit ledgers. Repository serialises ``Decimal`` as a string so the
SQLite NUMERIC column round-trips exact decimal semantics.

Timestamps are timezone-aware UTC (``datetime.now(tz=UTC)``); naive
timestamps gave wrong ordering on non-UTC hosts post-DST.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Discriminator, Field, model_validator

from agentic_control.contracts.audit_subject import AuditSubjectRef
from agentic_control.contracts.evidence import EvidenceRef
from agentic_control.contracts.hashes import HashAnchor, Hex12
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
    return datetime.now(tz=UTC)


_USD_QUANTUM = Decimal("0.000001")  # six-decimal precision (micro-USD)


def _quantize_usd(value: Decimal) -> Decimal:
    return value.quantize(_USD_QUANTUM)


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
    prompt_hash: Hex12
    tool_allowlist: list[str] = Field(default_factory=list)
    logs_ref: str = Field(min_length=1)
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: datetime | None = None
    exit_code: int | None = Field(default=None, ge=-1, le=255)


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

_APPROVAL_PENDING = frozenset({"waiting_for_approval", "stale_waiting"})


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

    @model_validator(mode="after")
    def _decided_at_consistent_with_state(self) -> Self:
        """``decided_at`` must be NULL while pending and SET once terminal."""
        is_pending = self.state in _APPROVAL_PENDING
        if is_pending and self.decided_at is not None:
            raise ValueError(
                f"approval_request in state={self.state!r} cannot have decided_at set"
            )
        terminal = {"approved", "rejected", "timed_out_rejected", "abandoned"}
        if self.state in terminal and self.decided_at is None:
            raise ValueError(
                f"approval_request in terminal state={self.state!r} requires decided_at"
            )
        return self


# ---------- BudgetLedgerEntry ----------


class BudgetLedgerEntry(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    ts: datetime = Field(default_factory=_utcnow)
    scope: BudgetScope
    run_attempt_ref: UUIDv7
    run_attempt_hash_anchor: HashAnchor
    project_ref: UUIDv7 | None = None
    model: str = Field(min_length=1, max_length=200)
    pre_call_projection_usd: Decimal = Field(ge=Decimal("0"))
    actual_usd: Decimal | None = Field(default=None, ge=Decimal("0"))
    cache_hit: bool = False

    @model_validator(mode="after")
    def _quantize(self) -> Self:
        object.__setattr__(
            self, "pre_call_projection_usd", _quantize_usd(self.pre_call_projection_usd)
        )
        if self.actual_usd is not None:
            object.__setattr__(self, "actual_usd", _quantize_usd(self.actual_usd))
        return self


# ---------- ToolCallRecord ----------


class ToolCallRecord(_RecordBase):
    id: UUIDv7 = Field(default_factory=new_id)
    run_attempt_ref: UUIDv7
    tool_call_ordinal: int = Field(ge=1)
    tool_name: str = Field(min_length=1, max_length=200)
    input_hash: Hex12
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
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
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
