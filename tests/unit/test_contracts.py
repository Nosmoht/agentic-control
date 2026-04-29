"""Unit tests for Pydantic contracts: validators, lifecycle, JSON-Schema export."""

from __future__ import annotations

import itertools
import uuid

import pytest
from pydantic import ValidationError

from agentic_control.contracts import (
    WORK_ITEM_TRANSITIONS,
    Decision,
    Project,
    WorkItem,
    is_valid_transition,
    new_id,
)


def test_new_id_returns_uuidv7() -> None:
    u = new_id()
    assert u.version == 7
    assert len(str(u)) == 36


def test_uuidv4_rejected_for_id_field() -> None:
    with pytest.raises(ValidationError):
        WorkItem(id=uuid.uuid4(), project_ref=new_id(), title="x")


def test_invalid_state_rejected() -> None:
    with pytest.raises(ValidationError):
        Project(title="t", state="bogus")  # type: ignore[arg-type]


def test_empty_title_rejected() -> None:
    with pytest.raises(ValidationError):
        Project(title="")


def test_decision_requires_all_three_madr_sections() -> None:
    wi_id = new_id()
    with pytest.raises(ValidationError):
        Decision(subject_ref=wi_id, context="", decision="d", consequence="c")


def test_lifecycle_matrix_forward_only_completed_terminal() -> None:
    assert WORK_ITEM_TRANSITIONS["completed"] == frozenset()
    assert WORK_ITEM_TRANSITIONS["abandoned"] == frozenset()


def test_lifecycle_proposed_to_completed_is_invalid() -> None:
    assert not is_valid_transition("proposed", "completed")


def test_lifecycle_full_happy_path() -> None:
    chain = ["proposed", "accepted", "planned", "ready", "in_progress", "completed"]
    for current, target in itertools.pairwise(chain):
        assert is_valid_transition(current, target), f"{current}->{target} should be valid"  # type: ignore[arg-type]


def test_json_schema_export_includes_uuid_format() -> None:
    schema = WorkItem.model_json_schema()
    assert schema["properties"]["id"]["format"] == "uuid"
    assert schema["properties"]["state"]["enum"]
