"""initial core objects: project, work_item, observation, decision

Revision ID: 0001
Revises:
Create Date: 2026-04-29

Mirror of Pydantic contracts in src/agentic_control/contracts/models.py
(Pydantic-First per ADR-0018; SQL DDL is the persistence reflection).

UUIDv7 PKs per ADR-0019: TEXT(36) with LENGTH=36 CHECK as defense-in-depth;
Pydantic validates the v7-version-bit before SQL-Send.

Lifecycle states per docs/spec/SPECIFICATION.md §6.1.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


PROJECT_STATES = ("idea", "candidate", "active", "dormant", "archived")
WORK_ITEM_STATES = (
    "proposed",
    "accepted",
    "planned",
    "ready",
    "in_progress",
    "waiting",
    "blocked",
    "completed",
    "abandoned",
)
WORK_ITEM_PRIORITIES = ("low", "med", "high")
DECISION_STATES = ("proposed", "accepted", "superseded", "rejected")


def _state_check(column: str, allowed: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{v}'" for v in allowed)
    return f"{column} IN ({quoted})"


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="idea"),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("provider_binding", sa.Text(), nullable=True),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_project_id_uuid_length"),
        sa.CheckConstraint("LENGTH(title) >= 1", name="ck_project_title_nonempty"),
        sa.CheckConstraint(_state_check("state", PROJECT_STATES), name="ck_project_state_enum"),
    )

    op.create_table(
        "work_item",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("project_ref", sa.Text(length=36), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="proposed"),
        sa.Column("priority", sa.Text(), nullable=False, server_default="med"),
        sa.Column("plan_ref", sa.Text(length=36), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_ref"], ["project.id"], ondelete="RESTRICT", name="fk_work_item_project"),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_work_item_id_uuid_length"),
        sa.CheckConstraint("LENGTH(project_ref) = 36", name="ck_work_item_project_ref_uuid_length"),
        sa.CheckConstraint("LENGTH(title) >= 1", name="ck_work_item_title_nonempty"),
        sa.CheckConstraint(_state_check("state", WORK_ITEM_STATES), name="ck_work_item_state_enum"),
        sa.CheckConstraint(_state_check("priority", WORK_ITEM_PRIORITIES), name="ck_work_item_priority_enum"),
    )
    op.create_index("ix_work_item_project_ref", "work_item", ["project_ref"])
    op.create_index("ix_work_item_state", "work_item", ["state"])

    op.create_table(
        "observation",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("source_ref", sa.Text(length=36), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("classification", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_observation_id_uuid_length"),
        sa.CheckConstraint("LENGTH(body) >= 1", name="ck_observation_body_nonempty"),
        sa.CheckConstraint(
            "source_ref IS NULL OR LENGTH(source_ref) = 36",
            name="ck_observation_source_ref_uuid_length",
        ),
    )
    op.create_index("ix_observation_source_ref", "observation", ["source_ref"])

    op.create_table(
        "decision",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("subject_ref", sa.Text(length=36), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("consequence", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="proposed"),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["subject_ref"], ["work_item.id"], ondelete="RESTRICT", name="fk_decision_subject"),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_decision_id_uuid_length"),
        sa.CheckConstraint("LENGTH(subject_ref) = 36", name="ck_decision_subject_ref_uuid_length"),
        sa.CheckConstraint("LENGTH(context) >= 1", name="ck_decision_context_nonempty"),
        sa.CheckConstraint("LENGTH(decision) >= 1", name="ck_decision_decision_nonempty"),
        sa.CheckConstraint("LENGTH(consequence) >= 1", name="ck_decision_consequence_nonempty"),
        sa.CheckConstraint(_state_check("state", DECISION_STATES), name="ck_decision_state_enum"),
    )
    op.create_index("ix_decision_subject_ref", "decision", ["subject_ref"])


def downgrade() -> None:
    op.drop_index("ix_decision_subject_ref", table_name="decision")
    op.drop_table("decision")
    op.drop_index("ix_observation_source_ref", table_name="observation")
    op.drop_table("observation")
    op.drop_index("ix_work_item_state", table_name="work_item")
    op.drop_index("ix_work_item_project_ref", table_name="work_item")
    op.drop_table("work_item")
    op.drop_table("project")
