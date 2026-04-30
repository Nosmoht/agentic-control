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

__all__ = [
    "DEFAULT_DB_URL",
    "MIN_PREFIX_LEN",
    "AmbiguousPrefixError",
    "IdResolutionError",
    "PrefixTooShortError",
    "RepositoryError",
    "UnknownIdError",
    "get_work_item",
    "insert_decision",
    "insert_observation",
    "insert_project",
    "insert_work_item",
    "list_decisions_for_subject",
    "list_next_work_items",
    "list_observations_for_source",
    "make_engine",
    "resolve_db_url",
    "resolve_id",
    "update_work_item_state",
    "validate_subject_ref",
]
