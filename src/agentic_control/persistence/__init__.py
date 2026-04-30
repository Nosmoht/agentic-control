"""Connection layer (SQLAlchemy Core) — no ORM imports allowed beyond this package."""

from agentic_control.persistence.db import DEFAULT_DB_URL, make_engine, resolve_db_url
from agentic_control.persistence.evidence_validator import validate_subject_ref
from agentic_control.persistence.prefix import (
    MIN_PREFIX_LEN,
    AmbiguousPrefixError,
    IdResolutionError,
    PrefixTooShortError,
    UnknownIdError,
    resolve_id,
)
from agentic_control.persistence.repository import (
    RepositoryError,
    get_work_item,
    insert_decision,
    insert_observation,
    insert_project,
    insert_work_item,
    list_decisions_for_subject,
    list_next_work_items,
    list_observations_for_source,
    update_work_item_state,
)
from agentic_control.persistence.runlog_writer import (
    append_runlog_line,
    open_runlog_fd,
    runlog_writer,
)
from agentic_control.persistence.runtime_repository import (
    get_run_attempt,
    insert_approval_request,
    insert_audit_event,
    insert_budget_ledger_entry,
    insert_dispatch_decision,
    insert_policy_decision,
    insert_run_attempt,
    insert_sandbox_violation,
    insert_tool_call_record,
    list_tool_calls_for_attempt,
)

__all__ = [
    "DEFAULT_DB_URL",
    "MIN_PREFIX_LEN",
    "AmbiguousPrefixError",
    "IdResolutionError",
    "PrefixTooShortError",
    "RepositoryError",
    "UnknownIdError",
    "append_runlog_line",
    "get_run_attempt",
    "get_work_item",
    "insert_approval_request",
    "insert_audit_event",
    "insert_budget_ledger_entry",
    "insert_decision",
    "insert_dispatch_decision",
    "insert_observation",
    "insert_policy_decision",
    "insert_project",
    "insert_run_attempt",
    "insert_sandbox_violation",
    "insert_tool_call_record",
    "insert_work_item",
    "list_decisions_for_subject",
    "list_next_work_items",
    "list_observations_for_source",
    "list_tool_calls_for_attempt",
    "make_engine",
    "open_runlog_fd",
    "resolve_db_url",
    "resolve_id",
    "runlog_writer",
    "update_work_item_state",
    "validate_subject_ref",
]
