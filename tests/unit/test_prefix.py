"""Unit tests for UUIDv7 prefix resolution."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine

from agentic_control.contracts import Project
from agentic_control.persistence import (
    AmbiguousPrefixError,
    PrefixTooShortError,
    UnknownIdError,
    insert_project,
    resolve_id,
)


def test_resolve_full_uuid(migrated_engine: Engine) -> None:
    p = insert_project(migrated_engine, Project(title="t"))
    resolved = resolve_id(migrated_engine, "project", str(p.id))
    assert resolved == p.id


def test_resolve_prefix(migrated_engine: Engine) -> None:
    p = insert_project(migrated_engine, Project(title="t"))
    resolved = resolve_id(migrated_engine, "project", str(p.id)[:8])
    assert resolved == p.id


def test_prefix_too_short(migrated_engine: Engine) -> None:
    with pytest.raises(PrefixTooShortError):
        resolve_id(migrated_engine, "project", "01")


def test_unknown_prefix(migrated_engine: Engine) -> None:
    with pytest.raises(UnknownIdError):
        resolve_id(migrated_engine, "project", "ffffffff")


def test_ambiguous_prefix(migrated_engine: Engine) -> None:
    # UUIDv7 starts with milliseconds; create two in same ms-burst → likely shared 8-char prefix
    p1 = insert_project(migrated_engine, Project(title="a"))
    p2 = insert_project(migrated_engine, Project(title="b"))
    common = ""
    for i in range(min(len(str(p1.id)), len(str(p2.id)))):
        if str(p1.id)[i] == str(p2.id)[i]:
            common += str(p1.id)[i]
        else:
            break
    if len(common) < 4:
        pytest.skip("UUIDv7 prefix divergence happened earlier than 4 chars")
    with pytest.raises(AmbiguousPrefixError) as excinfo:
        resolve_id(migrated_engine, "project", common)
    assert excinfo.value.minimal_unique_len > len(common)
    assert len(excinfo.value.candidates) == 2
