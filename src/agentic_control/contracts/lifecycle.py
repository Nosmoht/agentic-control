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
