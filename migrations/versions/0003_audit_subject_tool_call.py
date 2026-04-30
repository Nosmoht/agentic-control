"""extend audit_event.subject_ref CHECKs to accept tool_call_record:<uuid>

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-30

F0006 PR3 (Recovery path) writes a `reconcile_decision` AuditEvent per
local-only ToolCallRecord that the user resolves. The natural
``subject_ref`` for those events is ``tool_call_record:<uuid>``.

The base ``audit_event`` CHECK constraint set (migration ``0002``) only
accepts ``work_item:|run:|run_attempt:|decision:|config/`` prefixes —
without this migration the reconcile insert fails with
``CHECK constraint failed: ck_audit_event_subject_ref_prefix``.

This migration is purely additive on the constraint side: it adds
``tool_call_record:<uuid>`` (kind-prefix 18 + ":" + 36 = 54 chars) to
both the prefix CHECK and the length CHECK.

SQLite does not support ``ALTER TABLE … DROP CONSTRAINT``; Alembic
emulates the change via ``batch_alter_table`` which copies the table.
The audit_event table is small in v1a (≤ low-thousands of rows) and the
migration is one-time, so the rebuild cost is negligible.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


_NEW_PREFIX_CHECK = (
    "subject_ref LIKE 'work_item:%' "
    "OR subject_ref LIKE 'run:%' "
    "OR subject_ref LIKE 'run_attempt:%' "
    "OR subject_ref LIKE 'tool_call_record:%' "
    "OR subject_ref LIKE 'decision:%' "
    "OR subject_ref LIKE 'config/%'"
)
_NEW_LENGTH_CHECK = (
    "(subject_ref LIKE 'work_item:%' AND LENGTH(subject_ref) = 46) "
    "OR (subject_ref LIKE 'run:%' AND LENGTH(subject_ref) = 40) "
    "OR (subject_ref LIKE 'run_attempt:%' AND LENGTH(subject_ref) = 48) "
    "OR (subject_ref LIKE 'tool_call_record:%' AND LENGTH(subject_ref) = 53) "
    "OR (subject_ref LIKE 'decision:%' AND LENGTH(subject_ref) = 45) "
    "OR (subject_ref LIKE 'config/%' AND LENGTH(subject_ref) >= 8)"
)

_OLD_PREFIX_CHECK = (
    "subject_ref LIKE 'work_item:%' "
    "OR subject_ref LIKE 'run:%' "
    "OR subject_ref LIKE 'run_attempt:%' "
    "OR subject_ref LIKE 'decision:%' "
    "OR subject_ref LIKE 'config/%'"
)
_OLD_LENGTH_CHECK = (
    "(subject_ref LIKE 'work_item:%' AND LENGTH(subject_ref) = 46) "
    "OR (subject_ref LIKE 'run:%' AND LENGTH(subject_ref) = 40) "
    "OR (subject_ref LIKE 'run_attempt:%' AND LENGTH(subject_ref) = 48) "
    "OR (subject_ref LIKE 'decision:%' AND LENGTH(subject_ref) = 45) "
    "OR (subject_ref LIKE 'config/%' AND LENGTH(subject_ref) >= 8)"
)


def upgrade() -> None:
    # batch_alter_table rebuilds the table with the new constraint set on
    # SQLite. The two existing CHECKs are dropped by name and the
    # widened versions reinstalled.
    with op.batch_alter_table("audit_event") as batch_op:
        batch_op.drop_constraint(
            "ck_audit_event_subject_ref_prefix", type_="check"
        )
        batch_op.drop_constraint(
            "ck_audit_event_subject_ref_format", type_="check"
        )
        batch_op.create_check_constraint(
            "ck_audit_event_subject_ref_prefix", _NEW_PREFIX_CHECK
        )
        batch_op.create_check_constraint(
            "ck_audit_event_subject_ref_format", _NEW_LENGTH_CHECK
        )

    # batch_alter_table re-creates the existing indexes after the rebuild,
    # but the order in sqlite_master (which `sqlite3 .schema` walks) is
    # non-deterministic across invocation styles (e.g. `uv run alembic`
    # vs `python -m alembic`). Drop and re-create both indexes here in a
    # canonical order to keep schema-dump-stability tests deterministic.
    op.drop_index("ix_audit_event_subject_ref", table_name="audit_event")
    op.drop_index("ix_audit_event_run_attempt_ref", table_name="audit_event")
    op.create_index("ix_audit_event_subject_ref", "audit_event", ["subject_ref", "ts"])
    op.create_index(
        "ix_audit_event_run_attempt_ref", "audit_event", ["run_attempt_ref"]
    )


def downgrade() -> None:
    # Reverting widens-then-narrows: any rows inserted with
    # `tool_call_record:<uuid>` would violate the narrowed CHECK. We
    # do NOT delete data on downgrade; the user is expected to clear
    # those rows first if they truly want to roll back.
    with op.batch_alter_table("audit_event") as batch_op:
        batch_op.drop_constraint(
            "ck_audit_event_subject_ref_prefix", type_="check"
        )
        batch_op.drop_constraint(
            "ck_audit_event_subject_ref_format", type_="check"
        )
        batch_op.create_check_constraint(
            "ck_audit_event_subject_ref_prefix", _OLD_PREFIX_CHECK
        )
        batch_op.create_check_constraint(
            "ck_audit_event_subject_ref_format", _OLD_LENGTH_CHECK
        )


# Verify the alembic op import is referenced (silences ruff F401 if any).
_ = sa.text
