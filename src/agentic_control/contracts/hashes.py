"""Hex-string validators used across runtime contracts (F0006a follow-up).

Centralises the recurring `12-char sha256 prefix` and `64-char sha256
full` shapes so that callers cannot pass arbitrary 12/64-char garbage
through the type system. SQL CHECKs enforce length only; Pydantic owns
the character-set gate.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator

_HEX12 = re.compile(r"^[0-9a-f]{12}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX_ANCHOR = re.compile(r"^([0-9a-f]{12}|[0-9a-f]{64})$")


def _validate_hex12(value: str) -> str:
    if not _HEX12.match(value):
        raise ValueError(f"expected 12-char lowercase hex, got {value!r}")
    return value


def _validate_hex64(value: str) -> str:
    if not _HEX64.match(value):
        raise ValueError(f"expected 64-char lowercase hex (sha256), got {value!r}")
    return value


def _validate_hash_anchor(value: str) -> str:
    if not _HEX_ANCHOR.match(value):
        raise ValueError(
            f"expected 12-char prefix or 64-char full sha256 hex, got {value!r}"
        )
    return value


Hex12 = Annotated[str, AfterValidator(_validate_hex12)]
Hex64 = Annotated[str, AfterValidator(_validate_hex64)]
HashAnchor = Annotated[str, AfterValidator(_validate_hash_anchor)]


__all__ = ["HashAnchor", "Hex12", "Hex64"]
