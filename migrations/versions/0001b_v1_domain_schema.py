"""v1a domain schema: run, artifact, evidence (F0008)

Revision ID: 0001b
Revises: 0001
Create Date: 2026-04-29

Additive migration on top of F0001's v0 schema. Adds Run, Artifact and
Evidence as the minimal v1a domain slice ahead of F0006 (Runtime Records).

- `run` mirrors Spec §5.7 Run lifecycle (9 states incl. needs_reconciliation).
- `artifact` mirrors Spec §6.1 Artifact lifecycle.
- `evidence.subject_ref` is polymorphic (`<kind>:<uuid>`); ID-existence is
  enforced on the application layer by
  `persistence.evidence_validator.validate_subject_ref` per Spec §5.7
  eigenentscheidung. The CHECK on this column is defense-in-depth and
  matches `contracts.evidence.SUBJECT_REF_PATTERN`.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001b"
down_revision = "0001"
branch_labels = None
depends_on = None


RUN_STATES = (
    "created",
    "running",
    "paused",
    "waiting",
    "retrying",
    "needs_reconciliation",
    "completed",
    "failed",
    "aborted",
)
ARTIFACT_STATES = ("registered", "available", "consumed", "superseded", "archived")

# Mirror of contracts.evidence.SUBJECT_REF_PATTERN. SQLite GLOB cannot express
# the full regex so we split into prefix-IN check + length/format check on the
# UUID portion. Format: <kind>:<36-char-uuid> with kind in the four allowed
# discriminators.
SUBJECT_REF_CHECK = (
    "subject_ref LIKE 'work_item:%' "
    "OR subject_ref LIKE 'run:%' "
    "OR subject_ref LIKE 'artifact:%' "
    "OR subject_ref LIKE 'decision:%'"
)


def _state_check(column: str, allowed: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{v}'" for v in allowed)
    return f"{column} IN ({quoted})"


def upgrade() -> None:
    op.create_table(
        "run",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("work_item_ref", sa.Text(length=36), nullable=False),
        sa.Column("agent", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="created"),
        sa.Column("budget_cap", sa.Numeric(), nullable=False),
        sa.Column("result_ref", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["work_item_ref"], ["work_item.id"], ondelete="RESTRICT", name="fk_run_work_item"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_run_id_uuid_length"),
        sa.CheckConstraint("LENGTH(work_item_ref) = 36", name="ck_run_work_item_ref_uuid_length"),
        sa.CheckConstraint("LENGTH(agent) >= 1", name="ck_run_agent_nonempty"),
        sa.CheckConstraint("budget_cap >= 0", name="ck_run_budget_cap_nonneg"),
        sa.CheckConstraint(_state_check("state", RUN_STATES), name="ck_run_state_enum"),
    )
    op.create_index("ix_run_work_item_ref", "run", ["work_item_ref"])
    op.create_index("ix_run_state", "run", ["state"])

    op.create_table(
        "artifact",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("origin_run_ref", sa.Text(length=36), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("path_or_ref", sa.Text(), nullable=False),
        sa.Column("provenance", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="registered"),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["origin_run_ref"], ["run.id"], ondelete="RESTRICT", name="fk_artifact_origin_run"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_artifact_id_uuid_length"),
        sa.CheckConstraint(
            "LENGTH(origin_run_ref) = 36", name="ck_artifact_origin_run_ref_uuid_length"
        ),
        sa.CheckConstraint("LENGTH(kind) >= 1", name="ck_artifact_kind_nonempty"),
        sa.CheckConstraint("LENGTH(path_or_ref) >= 1", name="ck_artifact_path_or_ref_nonempty"),
        sa.CheckConstraint("LENGTH(provenance) >= 1", name="ck_artifact_provenance_nonempty"),
        sa.CheckConstraint(
            _state_check("state", ARTIFACT_STATES), name="ck_artifact_state_enum"
        ),
    )
    op.create_index("ix_artifact_origin_run_ref", "artifact", ["origin_run_ref"])
    op.create_index("ix_artifact_state", "artifact", ["state"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("subject_ref", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(length=36), nullable=True),
        sa.Column("captured_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("jsonl_blob_ref", sa.Text(), nullable=True),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_evidence_id_uuid_length"),
        sa.CheckConstraint("LENGTH(kind) >= 1", name="ck_evidence_kind_nonempty"),
        sa.CheckConstraint(
            "source_ref IS NULL OR LENGTH(source_ref) = 36",
            name="ck_evidence_source_ref_uuid_length",
        ),
        sa.CheckConstraint(SUBJECT_REF_CHECK, name="ck_evidence_subject_ref_prefix"),
        # The id portion after `<kind>:` must be exactly 36 chars (UUID).
        # 'work_item:'=10, 'run:'=4, 'artifact:'=9, 'decision:'=9 → total
        # length is kind-prefix + 36. Encode as: total length must equal
        # one of {46, 40, 45, 45}.
        sa.CheckConstraint(
            "(subject_ref LIKE 'work_item:%' AND LENGTH(subject_ref) = 46) "
            "OR (subject_ref LIKE 'run:%' AND LENGTH(subject_ref) = 40) "
            "OR (subject_ref LIKE 'artifact:%' AND LENGTH(subject_ref) = 45) "
            "OR (subject_ref LIKE 'decision:%' AND LENGTH(subject_ref) = 45)",
            name="ck_evidence_subject_ref_format",
        ),
    )
    op.create_index("ix_evidence_subject_ref", "evidence", ["subject_ref"])
    op.create_index("ix_evidence_kind", "evidence", ["kind"])


def downgrade() -> None:
    op.drop_index("ix_evidence_kind", table_name="evidence")
    op.drop_index("ix_evidence_subject_ref", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_artifact_state", table_name="artifact")
    op.drop_index("ix_artifact_origin_run_ref", table_name="artifact")
    op.drop_table("artifact")
    op.drop_index("ix_run_state", table_name="run")
    op.drop_index("ix_run_work_item_ref", table_name="run")
    op.drop_table("run")
