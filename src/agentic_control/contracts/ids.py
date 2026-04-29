"""UUIDv7 generator and parser used by all domain objects (ADR-0019)."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import AfterValidator


def new_id() -> uuid.UUID:
    """Generate a fresh UUIDv7 (RFC 9562) using stdlib (Python 3.14+)."""
    return uuid.uuid7()


def _ensure_v7(value: uuid.UUID) -> uuid.UUID:
    if value.version != 7:
        raise ValueError(f"expected UUID version 7, got version {value.version}")
    return value


UUIDv7 = Annotated[uuid.UUID, AfterValidator(_ensure_v7)]
