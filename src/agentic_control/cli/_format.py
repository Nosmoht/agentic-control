"""Output helpers for human and JSON modes."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

DISPLAY_PREFIX_LEN = 8


def short_id(value: uuid.UUID | str) -> str:
    return str(value)[:DISPLAY_PREFIX_LEN]


def to_jsonable(obj: Any) -> Any:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat(sep=" ", timespec="seconds")
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    raise TypeError(f"not jsonable: {type(obj).__name__}")


def emit(payload: Any, output_json: bool, human_text: str) -> None:
    if output_json:
        print(json.dumps(payload, default=to_jsonable, indent=2))
    else:
        print(human_text)
