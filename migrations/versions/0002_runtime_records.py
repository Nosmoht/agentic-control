"""runtime records: 8 tables for ADR-0011 (F0006)

Revision ID: 0002
Revises: 0001b
Create Date: 2026-04-30

Adds the eight Runtime-Record tables on top of the v0 + v1a domain
schema. Per F0006 the order of dependence is F0001 (project, work_item)
+ F0008 (run, artifact, evidence) + this revision (run_attempt,
audit_event, approval_request, budget_ledger_entry, tool_call_record,
policy_decision, sandbox_violation, dispatch_decision).

Pydantic-first per ADR-0018: every table mirrors a model in
``src/agentic_control/contracts/runtime_records.py``; SQL CHECKs are
defense-in-depth for shape (length, enum membership, json_valid). The
``tool_risk_match`` discriminated arm of PolicyDecisionRecord requires
specific output JSON keys that SQLite cannot validate — Pydantic owns
that gate, repository is the single insert path, and an integration
test sperrt direct-SQL bypass.

Decision log (2026-04-30):
* `audit_event.subject_ref` accepts two forms: `<kind>:<uuid>` (analog
  evidence, kinds work_item|run|run_attempt|decision) or path under
  `config/`. Two CHECK constraints cover both.
* `tool_call_record(run_attempt_ref, idempotency_key)` UNIQUE is a
  partial index via Alembic `sqlite_where=` so NULL idempotency_key
  (Tool-Calls without external effect) is permitted.
* `policy_decision.output` is `json_valid()`-checked at SQL level;
  tool_risk_match payload structure is enforced in Pydantic.
* `dispatch_decision.evidence_refs` is a JSON list column (n=1; switch
  to a join table in v2 if filter queries appear).
* No redundant `cost_usd` column on `run_attempt` — the budget ledger
  is the single source of truth (ADR-0011 §155).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001b"
branch_labels = None
depends_on = None


# Enum tuples ---------------------------------------------------------------

APPROVAL_STATES = (
    "waiting_for_approval",
    "approved",
    "rejected",
    "timed_out_rejected",
    "stale_waiting",
    "abandoned",
)
RISK_CLASSES = ("low", "medium", "high", "irreversible")
BUDGET_SCOPES = ("request", "task", "project_day", "global_day")
EFFECT_CLASSES = ("natural", "provider_keyed", "local_only")
POLICY_TAGS = (
    "admission",
    "dispatch",
    "budget_gate_override",
    "hitl_trigger",
    "tool_risk_match",
)
ADAPTERS = ("claude_code", "codex_cli")
DISPATCH_MODES = ("pinned", "cost_aware")
DISPATCH_REASONS = ("pin", "default", "cost_aware_routing")
AUDIT_EVENT_TYPES = (
    "state_transition",
    "config_write",
    "reconcile_decision",
    "lifecycle_change",
)


def _state_check(column: str, allowed: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{v}'" for v in allowed)
    return f"{column} IN ({quoted})"


# Reusable polymorphic-ref CHECK for audit_event.subject_ref. Mirrors
# contracts.audit_subject regex — kind:<uuid> in the four allowed kinds, or
# path under config/. Length checks: work_item=46, run=40, run_attempt=48,
# decision=45 (kind-prefix + ":" + 36-char uuid).
AUDIT_SUBJECT_REF_PREFIX_CHECK = (
    "subject_ref LIKE 'work_item:%' "
    "OR subject_ref LIKE 'run:%' "
    "OR subject_ref LIKE 'run_attempt:%' "
    "OR subject_ref LIKE 'decision:%' "
    "OR subject_ref LIKE 'config/%'"
)
AUDIT_SUBJECT_REF_LENGTH_CHECK = (
    "(subject_ref LIKE 'work_item:%' AND LENGTH(subject_ref) = 46) "
    "OR (subject_ref LIKE 'run:%' AND LENGTH(subject_ref) = 40) "
    "OR (subject_ref LIKE 'run_attempt:%' AND LENGTH(subject_ref) = 48) "
    "OR (subject_ref LIKE 'decision:%' AND LENGTH(subject_ref) = 45) "
    "OR (subject_ref LIKE 'config/%' AND LENGTH(subject_ref) >= 8)"
)


def upgrade() -> None:
    # 1. run_attempt -------------------------------------------------------
    op.create_table(
        "run_attempt",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("run_ref", sa.Text(length=36), nullable=False),
        sa.Column("attempt_ordinal", sa.Integer(), nullable=False),
        sa.Column("agent", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("sandbox_profile", sa.Text(), nullable=False),
        sa.Column("prompt_hash", sa.Text(length=12), nullable=False),
        sa.Column("tool_allowlist", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("logs_ref", sa.Text(), nullable=False),
        sa.Column("started_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ended_at", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["run_ref"], ["run.id"], ondelete="RESTRICT", name="fk_run_attempt_run"),
        sa.UniqueConstraint("run_ref", "attempt_ordinal", name="uq_run_attempt_ordinal"),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_run_attempt_id_uuid_length"),
        sa.CheckConstraint("LENGTH(run_ref) = 36", name="ck_run_attempt_run_ref_uuid_length"),
        sa.CheckConstraint("attempt_ordinal >= 1", name="ck_run_attempt_ordinal_positive"),
        sa.CheckConstraint("LENGTH(prompt_hash) = 12", name="ck_run_attempt_prompt_hash_length"),
        sa.CheckConstraint("json_valid(tool_allowlist)", name="ck_run_attempt_tool_allowlist_json"),
    )
    op.create_index("ix_run_attempt_run_ref", "run_attempt", ["run_ref"])
    op.create_index("ix_run_attempt_started_at", "run_attempt", ["started_at"])

    # 2. audit_event -------------------------------------------------------
    op.create_table(
        "audit_event",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("ts", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("subject_ref", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("before_hash", sa.Text(length=64), nullable=True),
        sa.Column("after_hash", sa.Text(length=64), nullable=True),
        sa.Column("before_value", sa.Text(), nullable=True),
        sa.Column("after_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("run_attempt_ref", sa.Text(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_attempt_ref"], ["run_attempt.id"], ondelete="RESTRICT", name="fk_audit_event_run_attempt"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_audit_event_id_uuid_length"),
        sa.CheckConstraint("LENGTH(actor) >= 1", name="ck_audit_event_actor_nonempty"),
        sa.CheckConstraint(
            _state_check("event_type", AUDIT_EVENT_TYPES), name="ck_audit_event_type_enum"
        ),
        sa.CheckConstraint(
            "before_hash IS NULL OR LENGTH(before_hash) = 64",
            name="ck_audit_event_before_hash_length",
        ),
        sa.CheckConstraint(
            "after_hash IS NULL OR LENGTH(after_hash) = 64",
            name="ck_audit_event_after_hash_length",
        ),
        sa.CheckConstraint(
            AUDIT_SUBJECT_REF_PREFIX_CHECK, name="ck_audit_event_subject_ref_prefix"
        ),
        sa.CheckConstraint(
            AUDIT_SUBJECT_REF_LENGTH_CHECK, name="ck_audit_event_subject_ref_format"
        ),
    )
    op.create_index("ix_audit_event_subject_ref", "audit_event", ["subject_ref", "ts"])
    op.create_index("ix_audit_event_run_attempt_ref", "audit_event", ["run_attempt_ref"])

    # 3. approval_request --------------------------------------------------
    op.create_table(
        "approval_request",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("subject_ref", sa.Text(length=36), nullable=False),
        sa.Column("risk_class", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="waiting_for_approval"),
        sa.Column("decider", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("decided_at", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Text(), nullable=True),
        sa.Column("run_attempt_ref", sa.Text(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["subject_ref"], ["work_item.id"], ondelete="RESTRICT", name="fk_approval_request_subject"
        ),
        sa.ForeignKeyConstraint(
            ["run_attempt_ref"], ["run_attempt.id"], ondelete="RESTRICT", name="fk_approval_request_run_attempt"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_approval_request_id_uuid_length"),
        sa.CheckConstraint("LENGTH(subject_ref) = 36", name="ck_approval_request_subject_ref_uuid_length"),
        sa.CheckConstraint("LENGTH(question) >= 1", name="ck_approval_request_question_nonempty"),
        sa.CheckConstraint(_state_check("risk_class", RISK_CLASSES), name="ck_approval_request_risk_class_enum"),
        sa.CheckConstraint(_state_check("state", APPROVAL_STATES), name="ck_approval_request_state_enum"),
    )
    op.create_index("ix_approval_request_subject_ref", "approval_request", ["subject_ref"])
    op.create_index("ix_approval_request_state", "approval_request", ["state"])

    # 4. budget_ledger_entry -----------------------------------------------
    op.create_table(
        "budget_ledger_entry",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("ts", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("run_attempt_ref", sa.Text(length=36), nullable=False),
        sa.Column("run_attempt_hash_anchor", sa.Text(), nullable=False),
        sa.Column("project_ref", sa.Text(length=36), nullable=True),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("pre_call_projection_usd", sa.Numeric(), nullable=False),
        sa.Column("actual_usd", sa.Numeric(), nullable=True),
        sa.Column("cache_hit", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(
            ["run_attempt_ref"], ["run_attempt.id"], ondelete="RESTRICT", name="fk_budget_run_attempt"
        ),
        sa.ForeignKeyConstraint(
            ["project_ref"], ["project.id"], ondelete="RESTRICT", name="fk_budget_project"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_budget_id_uuid_length"),
        sa.CheckConstraint("LENGTH(run_attempt_ref) = 36", name="ck_budget_run_attempt_ref_uuid_length"),
        sa.CheckConstraint(_state_check("scope", BUDGET_SCOPES), name="ck_budget_scope_enum"),
        sa.CheckConstraint("pre_call_projection_usd >= 0", name="ck_budget_pre_call_projection_nonneg"),
        sa.CheckConstraint("actual_usd IS NULL OR actual_usd >= 0", name="ck_budget_actual_nonneg"),
        sa.CheckConstraint("cache_hit IN (0, 1)", name="ck_budget_cache_hit_bool"),
        sa.CheckConstraint(
            "LENGTH(run_attempt_hash_anchor) BETWEEN 12 AND 64",
            name="ck_budget_hash_anchor_length",
        ),
    )
    op.create_index("ix_budget_run_attempt_ref", "budget_ledger_entry", ["run_attempt_ref"])
    op.create_index("ix_budget_ts", "budget_ledger_entry", ["ts"])
    op.create_index("ix_budget_scope_ts", "budget_ledger_entry", ["scope", "ts"])

    # 5. tool_call_record --------------------------------------------------
    op.create_table(
        "tool_call_record",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("run_attempt_ref", sa.Text(length=36), nullable=False),
        sa.Column("tool_call_ordinal", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.Text(), nullable=False),
        sa.Column("input_hash", sa.Text(length=12), nullable=False),
        sa.Column("output_ref", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("effect_class", sa.Text(), nullable=False),
        sa.Column("started_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ended_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_attempt_ref"], ["run_attempt.id"], ondelete="RESTRICT", name="fk_tool_call_run_attempt"
        ),
        sa.UniqueConstraint(
            "run_attempt_ref", "tool_call_ordinal", name="uq_tool_call_ordinal"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_tool_call_id_uuid_length"),
        sa.CheckConstraint(
            "LENGTH(run_attempt_ref) = 36", name="ck_tool_call_run_attempt_ref_uuid_length"
        ),
        sa.CheckConstraint("tool_call_ordinal >= 1", name="ck_tool_call_ordinal_positive"),
        sa.CheckConstraint("LENGTH(tool_name) >= 1", name="ck_tool_call_tool_name_nonempty"),
        sa.CheckConstraint("LENGTH(input_hash) = 12", name="ck_tool_call_input_hash_length"),
        sa.CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="ck_tool_call_duration_nonneg"),
        sa.CheckConstraint(
            "idempotency_key IS NULL OR LENGTH(idempotency_key) >= 1",
            name="ck_tool_call_idempotency_key_nonempty",
        ),
        sa.CheckConstraint(
            _state_check("effect_class", EFFECT_CLASSES), name="ck_tool_call_effect_class_enum"
        ),
    )
    op.create_index("ix_tool_call_run_attempt_effect", "tool_call_record", ["run_attempt_ref", "effect_class"])
    # Partial UNIQUE so multiple NULL idempotency_keys (tool calls without
    # external effect) are allowed but non-NULL keys are deduplicated per
    # run-attempt (F0006 AC 3 + ADR-0011 Pre-Send-Check).
    op.create_index(
        "uq_tool_call_idempotency_key",
        "tool_call_record",
        ["run_attempt_ref", "idempotency_key"],
        unique=True,
        sqlite_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # 6. policy_decision ---------------------------------------------------
    op.create_table(
        "policy_decision",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("ts", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("policy", sa.Text(), nullable=False),
        sa.Column("subject_ref", sa.Text(), nullable=False),
        sa.Column("inputs", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("output", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("run_attempt_ref", sa.Text(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_attempt_ref"], ["run_attempt.id"], ondelete="RESTRICT", name="fk_policy_decision_run_attempt"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_policy_decision_id_uuid_length"),
        sa.CheckConstraint(_state_check("policy", POLICY_TAGS), name="ck_policy_decision_policy_enum"),
        sa.CheckConstraint("LENGTH(subject_ref) >= 1", name="ck_policy_decision_subject_ref_nonempty"),
        sa.CheckConstraint("json_valid(inputs)", name="ck_policy_decision_inputs_json"),
        sa.CheckConstraint("json_valid(output)", name="ck_policy_decision_output_json"),
    )
    op.create_index("ix_policy_decision_run_attempt_policy", "policy_decision", ["run_attempt_ref", "policy"])
    op.create_index("ix_policy_decision_subject_ref", "policy_decision", ["subject_ref"])

    # 7. sandbox_violation -------------------------------------------------
    op.create_table(
        "sandbox_violation",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("run_attempt_ref", sa.Text(length=36), nullable=False),
        sa.Column("ts", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(
            ["run_attempt_ref"], ["run_attempt.id"], ondelete="RESTRICT", name="fk_sandbox_violation_run_attempt"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_sandbox_violation_id_uuid_length"),
        sa.CheckConstraint("LENGTH(category) >= 1", name="ck_sandbox_violation_category_nonempty"),
        sa.CheckConstraint("json_valid(detail)", name="ck_sandbox_violation_detail_json"),
    )
    op.create_index("ix_sandbox_violation_run_attempt_ts", "sandbox_violation", ["run_attempt_ref", "ts"])

    # 8. dispatch_decision -------------------------------------------------
    op.create_table(
        "dispatch_decision",
        sa.Column("id", sa.Text(length=36), primary_key=True),
        sa.Column("run_attempt_ref", sa.Text(length=36), nullable=False, unique=True),
        sa.Column("adapter", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_refs", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.Text(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["run_attempt_ref"], ["run_attempt.id"], ondelete="RESTRICT", name="fk_dispatch_decision_run_attempt"
        ),
        sa.CheckConstraint("LENGTH(id) = 36", name="ck_dispatch_decision_id_uuid_length"),
        sa.CheckConstraint(
            "LENGTH(run_attempt_ref) = 36", name="ck_dispatch_decision_run_attempt_ref_uuid_length"
        ),
        sa.CheckConstraint(_state_check("adapter", ADAPTERS), name="ck_dispatch_decision_adapter_enum"),
        sa.CheckConstraint(_state_check("mode", DISPATCH_MODES), name="ck_dispatch_decision_mode_enum"),
        sa.CheckConstraint(_state_check("reason", DISPATCH_REASONS), name="ck_dispatch_decision_reason_enum"),
        sa.CheckConstraint(
            "evidence_refs IS NULL OR json_valid(evidence_refs)",
            name="ck_dispatch_decision_evidence_refs_json",
        ),
    )


def downgrade() -> None:
    op.drop_table("dispatch_decision")
    op.drop_index("ix_sandbox_violation_run_attempt_ts", table_name="sandbox_violation")
    op.drop_table("sandbox_violation")
    op.drop_index("ix_policy_decision_subject_ref", table_name="policy_decision")
    op.drop_index("ix_policy_decision_run_attempt_policy", table_name="policy_decision")
    op.drop_table("policy_decision")
    op.drop_index("uq_tool_call_idempotency_key", table_name="tool_call_record")
    op.drop_index("ix_tool_call_run_attempt_effect", table_name="tool_call_record")
    op.drop_table("tool_call_record")
    op.drop_index("ix_budget_scope_ts", table_name="budget_ledger_entry")
    op.drop_index("ix_budget_ts", table_name="budget_ledger_entry")
    op.drop_index("ix_budget_run_attempt_ref", table_name="budget_ledger_entry")
    op.drop_table("budget_ledger_entry")
    op.drop_index("ix_approval_request_state", table_name="approval_request")
    op.drop_index("ix_approval_request_subject_ref", table_name="approval_request")
    op.drop_table("approval_request")
    op.drop_index("ix_audit_event_run_attempt_ref", table_name="audit_event")
    op.drop_index("ix_audit_event_subject_ref", table_name="audit_event")
    op.drop_table("audit_event")
    op.drop_index("ix_run_attempt_started_at", table_name="run_attempt")
    op.drop_index("ix_run_attempt_run_ref", table_name="run_attempt")
    op.drop_table("run_attempt")
