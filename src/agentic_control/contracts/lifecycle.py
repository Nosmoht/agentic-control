"""Lifecycle states and transition matrices for v0 domain objects.

Source of truth: docs/spec/SPECIFICATION.md §6.1.
"""

from typing import Final, Literal

ProjectState = Literal["idea", "candidate", "active", "dormant", "archived"]

WorkItemState = Literal[
    "proposed",
    "accepted",
    "planned",
    "ready",
    "in_progress",
    "waiting",
    "blocked",
    "completed",
    "abandoned",
]

DecisionState = Literal["proposed", "accepted", "superseded", "rejected"]

WorkItemPriority = Literal["low", "med", "high"]

RunState = Literal[
    "created",
    "running",
    "paused",
    "waiting",
    "retrying",
    "needs_reconciliation",
    "completed",
    "failed",
    "aborted",
]

ArtifactState = Literal["registered", "available", "consumed", "superseded", "archived"]

EvidenceSubjectKind = Literal["work_item", "run", "artifact", "decision"]

# Runtime Records (F0006, ADR-0011)

ApprovalRequestState = Literal[
    "waiting_for_approval",
    "approved",
    "rejected",
    "timed_out_rejected",
    "stale_waiting",
    "abandoned",
]

RiskClass = Literal["low", "medium", "high", "irreversible"]

ApprovalRouting = Literal["never", "required", "policy_gated"]

BudgetScope = Literal["request", "task", "project_day", "global_day"]

EffectClass = Literal["natural", "provider_keyed", "local_only"]

PolicyTag = Literal[
    "admission",
    "dispatch",
    "budget_gate_override",
    "hitl_trigger",
    "tool_risk_match",
]

Adapter = Literal["claude_code", "codex_cli"]

DispatchMode = Literal["pinned", "cost_aware"]

DispatchReason = Literal["pin", "default", "cost_aware_routing"]

# JSONL Runlog

RunlogLevel = Literal["debug", "info", "warn", "error"]

RunlogEventType = Literal[
    "tool_call_start",
    "tool_call_end",
    "audit_event",
    "policy_decision",
    "sandbox_violation",
    "budget_entry",
    "agent_message",
    "error",
]

# AuditEvent (ADR-0011 + ADR-0016)

AuditEventType = Literal[
    "state_transition",
    "config_write",
    "reconcile_decision",
    "lifecycle_change",
]

AuditSubjectKind = Literal["work_item", "run", "run_attempt", "decision"]


WORK_ITEM_TRANSITIONS: Final[dict[WorkItemState, frozenset[WorkItemState]]] = {
    "proposed": frozenset({"accepted", "abandoned"}),
    "accepted": frozenset({"planned", "abandoned"}),
    "planned": frozenset({"ready", "abandoned"}),
    "ready": frozenset({"in_progress", "abandoned"}),
    "in_progress": frozenset({"waiting", "blocked", "completed", "abandoned"}),
    "waiting": frozenset({"in_progress", "blocked", "abandoned"}),
    "blocked": frozenset({"in_progress", "waiting", "abandoned"}),
    "completed": frozenset(),
    "abandoned": frozenset(),
}


def is_valid_transition(current: WorkItemState, target: WorkItemState) -> bool:
    """Return True if `current → target` is allowed by the work-item lifecycle."""
    return target in WORK_ITEM_TRANSITIONS.get(current, frozenset())
