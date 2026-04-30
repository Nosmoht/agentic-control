"""UUIDv7 prefix resolution for CLI ID arguments (ADR-0019).

Pattern: user types `agentctl work show 01a3` → SQL `WHERE id LIKE '01a3%'`.
- Exact match (36 chars) bypasses prefix logic.
- Minimum prefix length: 4 chars.
- Multiple matches: AmbiguousPrefixError with candidates and minimal-unique length.
- No matches: UnknownIdError.
"""

from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy import Engine, text

MIN_PREFIX_LEN = 4

Table = Literal["project", "work_item", "observation", "decision", "run"]


class IdResolutionError(Exception):
    """Base for ID-resolution failures."""


class PrefixTooShortError(IdResolutionError):
    pass


class UnknownIdError(IdResolutionError):
    pass


class AmbiguousPrefixError(IdResolutionError):
    def __init__(self, prefix: str, candidates: list[str]) -> None:
        self.prefix = prefix
        self.candidates = candidates
        self.minimal_unique_len = _minimal_unique_prefix_length(candidates)
        super().__init__(
            f"prefix {prefix!r} matches {len(candidates)} ids; "
            f"need at least {self.minimal_unique_len} chars to disambiguate"
        )


def _minimal_unique_prefix_length(candidates: list[str]) -> int:
    if len(candidates) <= 1:
        return MIN_PREFIX_LEN
    for length in range(MIN_PREFIX_LEN, 37):
        prefixes = {c[:length] for c in candidates}
        if len(prefixes) == len(candidates):
            return length
    return 36


def resolve_id(engine: Engine, table: Table, value: str) -> uuid.UUID:
    """Resolve a full UUID or prefix to a single UUID from `table`."""
    if len(value) == 36:
        try:
            parsed = uuid.UUID(value)
        except ValueError as exc:
            raise UnknownIdError(f"not a valid UUID: {value!r}") from exc
        with engine.connect() as conn:
            row = conn.execute(
                text(f"SELECT id FROM {table} WHERE id = :id"),
                {"id": str(parsed)},
            ).first()
        if row is None:
            raise UnknownIdError(f"no {table} with id {value}")
        return parsed

    if len(value) < MIN_PREFIX_LEN:
        raise PrefixTooShortError(
            f"prefix {value!r} too short (minimum {MIN_PREFIX_LEN} chars)"
        )

    pattern = value + "%"
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT id FROM {table} WHERE id LIKE :p"),
            {"p": pattern},
        ).fetchall()

    if not rows:
        raise UnknownIdError(f"no {table} matching prefix {value!r}")

    candidates = [r[0] for r in rows]
    if len(candidates) > 1:
        raise AmbiguousPrefixError(value, candidates)

    return uuid.UUID(candidates[0])
