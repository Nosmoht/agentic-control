"""Pydantic v2 contracts for v0 domain objects.

Source-of-truth field shapes per docs/spec/SPECIFICATION.md §5.7 and §6.1.
ADR-0018 (Pydantic-First) makes these the canonical schema; SQL DDL in
migrations/versions/0001 mirrors the same shape.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from agentic_control.contracts.ids import UUIDv7, new_id
from agentic_control.contracts.lifecycle import (
    DecisionState,
    ProjectState,
    WorkItemPriority,
    WorkItemState,
)


def _utcnow() -> datetime:
    return datetime.now()


class _DomainBase(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")


class Project(_DomainBase):
    id: UUIDv7 = Field(default_factory=new_id)
    title: str = Field(min_length=1, max_length=200)
    state: ProjectState = "idea"
    created_at: datetime = Field(default_factory=_utcnow)
    provider_binding: str | None = None


class WorkItem(_DomainBase):
    id: UUIDv7 = Field(default_factory=new_id)
    project_ref: UUIDv7
    title: str = Field(min_length=1, max_length=200)
    state: WorkItemState = "proposed"
    priority: WorkItemPriority = "med"
    plan_ref: uuid.UUID | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class Observation(_DomainBase):
    id: UUIDv7 = Field(default_factory=new_id)
    source_ref: UUIDv7 | None = None
    body: str = Field(min_length=1)
    classification: str | None = None
    captured_at: datetime = Field(default_factory=_utcnow)


class Decision(_DomainBase):
    id: UUIDv7 = Field(default_factory=new_id)
    subject_ref: UUIDv7
    context: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    consequence: str = Field(min_length=1)
    state: DecisionState = "proposed"
    created_at: datetime = Field(default_factory=_utcnow)
