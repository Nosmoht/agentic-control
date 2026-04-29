"""SQL-Core CRUD functions for v0 domain objects.

No ORM. Pydantic-In, Pydantic-Out, raw SQL via SQLAlchemy Core in between
(ADR-0020). The import-linter contract forbids ``sqlalchemy.orm`` imports
in this codebase outside of this package.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from agentic_control.contracts import (
    Decision,
    Observation,
    Project,
    WorkItem,
    WorkItemPriority,
    WorkItemState,
)


class RepositoryError(Exception):
    """Raised for domain-level persistence failures (FK, CHECK, ambiguous prefix)."""


def _to_iso(dt: datetime) -> str:
    return dt.isoformat(sep=" ", timespec="seconds")


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def insert_project(engine: Engine, project: Project) -> Project:
    sql = text(
        """
        INSERT INTO project (id, title, state, created_at, provider_binding)
        VALUES (:id, :title, :state, :created_at, :provider_binding)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(project.id),
                    "title": project.title,
                    "state": project.state,
                    "created_at": _to_iso(project.created_at),
                    "provider_binding": project.provider_binding,
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return project


def insert_work_item(engine: Engine, item: WorkItem) -> WorkItem:
    sql = text(
        """
        INSERT INTO work_item
            (id, project_ref, title, state, priority, plan_ref, created_at)
        VALUES (:id, :project_ref, :title, :state, :priority, :plan_ref, :created_at)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(item.id),
                    "project_ref": str(item.project_ref),
                    "title": item.title,
                    "state": item.state,
                    "priority": item.priority,
                    "plan_ref": str(item.plan_ref) if item.plan_ref else None,
                    "created_at": _to_iso(item.created_at),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return item


def insert_observation(engine: Engine, obs: Observation) -> Observation:
    sql = text(
        """
        INSERT INTO observation (id, source_ref, body, classification, captured_at)
        VALUES (:id, :source_ref, :body, :classification, :captured_at)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(obs.id),
                    "source_ref": str(obs.source_ref) if obs.source_ref else None,
                    "body": obs.body,
                    "classification": obs.classification,
                    "captured_at": _to_iso(obs.captured_at),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return obs


def insert_decision(engine: Engine, dec: Decision) -> Decision:
    sql = text(
        """
        INSERT INTO decision
            (id, subject_ref, context, decision, consequence, state, created_at)
        VALUES (:id, :subject_ref, :context, :decision, :consequence, :state, :created_at)
        """
    )
    try:
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "id": str(dec.id),
                    "subject_ref": str(dec.subject_ref),
                    "context": dec.context,
                    "decision": dec.decision,
                    "consequence": dec.consequence,
                    "state": dec.state,
                    "created_at": _to_iso(dec.created_at),
                },
            )
    except IntegrityError as exc:
        raise RepositoryError(str(exc.orig)) from exc
    return dec


def get_work_item(engine: Engine, work_item_id: uuid.UUID) -> WorkItem | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM work_item WHERE id = :id"),
            {"id": str(work_item_id)},
        ).first()
    return _row_to_work_item(row) if row else None


def update_work_item_state(
    engine: Engine, work_item_id: uuid.UUID, new_state: WorkItemState
) -> bool:
    sql = text("UPDATE work_item SET state = :state WHERE id = :id")
    with engine.begin() as conn:
        result = conn.execute(sql, {"state": new_state, "id": str(work_item_id)})
    return result.rowcount > 0


_PRIORITY_ORDER: dict[WorkItemPriority, int] = {"high": 0, "med": 1, "low": 2}


def list_next_work_items(
    engine: Engine, project_ref: uuid.UUID | None = None, limit: int = 3
) -> list[WorkItem]:
    base = "SELECT * FROM work_item WHERE state IN ('ready', 'accepted')"
    params: dict[str, Any] = {"limit": limit}
    if project_ref is not None:
        base += " AND project_ref = :project_ref"
        params["project_ref"] = str(project_ref)
    base += " ORDER BY created_at ASC"
    with engine.connect() as conn:
        rows = conn.execute(text(base), params).fetchall()
    items = [_row_to_work_item(r) for r in rows]
    items.sort(key=lambda i: (_PRIORITY_ORDER[i.priority], i.created_at))
    return items[:limit]


def list_decisions_for_subject(engine: Engine, subject_ref: uuid.UUID) -> list[Decision]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM decision WHERE subject_ref = :s ORDER BY created_at ASC"),
            {"s": str(subject_ref)},
        ).fetchall()
    return [_row_to_decision(r) for r in rows]


def list_observations_for_source(engine: Engine, source_ref: uuid.UUID) -> list[Observation]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM observation WHERE source_ref = :s ORDER BY captured_at ASC"),
            {"s": str(source_ref)},
        ).fetchall()
    return [_row_to_observation(r) for r in rows]


def _row_to_work_item(row: Any) -> WorkItem:
    d = _row_to_dict(row)
    return WorkItem(
        id=uuid.UUID(d["id"]),
        project_ref=uuid.UUID(d["project_ref"]),
        title=d["title"],
        state=d["state"],
        priority=d["priority"],
        plan_ref=uuid.UUID(d["plan_ref"]) if d["plan_ref"] else None,
        created_at=datetime.fromisoformat(d["created_at"]),
    )


def _row_to_decision(row: Any) -> Decision:
    d = _row_to_dict(row)
    return Decision(
        id=uuid.UUID(d["id"]),
        subject_ref=uuid.UUID(d["subject_ref"]),
        context=d["context"],
        decision=d["decision"],
        consequence=d["consequence"],
        state=d["state"],
        created_at=datetime.fromisoformat(d["created_at"]),
    )


def _row_to_observation(row: Any) -> Observation:
    d = _row_to_dict(row)
    return Observation(
        id=uuid.UUID(d["id"]),
        source_ref=uuid.UUID(d["source_ref"]) if d["source_ref"] else None,
        body=d["body"],
        classification=d["classification"],
        captured_at=datetime.fromisoformat(d["captured_at"]),
    )
