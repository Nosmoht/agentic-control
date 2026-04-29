"""Pydantic-first canonical contracts for v0 domain objects (ADR-0018)."""

from agentic_control.contracts.ids import UUIDv7, new_id
from agentic_control.contracts.lifecycle import (
    WORK_ITEM_TRANSITIONS,
    DecisionState,
    ProjectState,
    WorkItemPriority,
    WorkItemState,
    is_valid_transition,
)
from agentic_control.contracts.models import Decision, Observation, Project, WorkItem

__all__ = [
    "WORK_ITEM_TRANSITIONS",
    "Decision",
    "DecisionState",
    "Observation",
    "Project",
    "ProjectState",
    "UUIDv7",
    "WorkItem",
    "WorkItemPriority",
    "WorkItemState",
    "is_valid_transition",
    "new_id",
]
