"""JSONL Runlog event contracts (F0006 AC 8).

Append-only line-oriented log under
``~/.agentic-control/logs/runs/<run_attempt_id>.jsonl``. One JSON object
per line, never multi-line.

R3-Closure (V0.3.6-draft, 2026-04-30): each line is hard-capped at 4096
bytes including the trailing newline. POSIX guarantees `O_APPEND`
atomicity only for writes ``<= PIPE_BUF (4 KB)``; the
``serialise_runlog_line`` helper raises ``RunlogLineTooLarge`` before
the write can be issued. The persistence-layer writer
(`persistence.runlog_writer.append_runlog_line`) issues the resulting
bytes in a single ``os.write`` syscall.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Discriminator, Field, TypeAdapter

from agentic_control.contracts.audit_subject import AuditSubjectRef
from agentic_control.contracts.ids import UUIDv7
from agentic_control.contracts.lifecycle import (
    BudgetScope,
    PolicyTag,
    RunlogLevel,
)

LINE_MAX_BYTES = 4096


class RunlogLineTooLargeError(ValueError):
    """Raised when a serialised RunlogEntry plus newline exceeds LINE_MAX_BYTES."""


# Public alias kept for ergonomic import; backed by the Error-suffixed class
# (ruff N818). Both names refer to the same exception type.
RunlogLineTooLarge = RunlogLineTooLargeError


class _RunlogBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ts: datetime
    level: RunlogLevel
    run_attempt_id: UUIDv7
    seq: int = Field(ge=0)


class ToolCallStartEvent(_RunlogBase):
    event_type: Literal["tool_call_start"] = "tool_call_start"
    tool_name: str = Field(min_length=1, max_length=200)
    tool_call_id: UUIDv7
    args_hash: str = Field(min_length=12, max_length=12)


class ToolCallEndEvent(_RunlogBase):
    event_type: Literal["tool_call_end"] = "tool_call_end"
    tool_name: str = Field(min_length=1, max_length=200)
    tool_call_id: UUIDv7
    args_hash: str = Field(min_length=12, max_length=12)


class AuditEventEvent(_RunlogBase):
    event_type: Literal["audit_event"] = "audit_event"
    audit_event_id: UUIDv7
    subject_ref: AuditSubjectRef


class PolicyDecisionEvent(_RunlogBase):
    event_type: Literal["policy_decision"] = "policy_decision"
    policy: PolicyTag
    decision_id: UUIDv7
    outcome: str = Field(min_length=1)


class SandboxViolationEvent(_RunlogBase):
    event_type: Literal["sandbox_violation"] = "sandbox_violation"
    category: str = Field(min_length=1)
    detail: dict[str, Any] = Field(default_factory=dict)


class BudgetEntryEvent(_RunlogBase):
    event_type: Literal["budget_entry"] = "budget_entry"
    scope: BudgetScope
    amount_usd: float = Field(ge=0.0)
    cumulative_usd: float = Field(ge=0.0)


class AgentMessageEvent(_RunlogBase):
    event_type: Literal["agent_message"] = "agent_message"
    body: str = Field(min_length=1)


class ErrorEvent(_RunlogBase):
    event_type: Literal["error"] = "error"
    error_type: str = Field(min_length=1)
    message: str = Field(min_length=1)


_RunlogUnion = (
    ToolCallStartEvent
    | ToolCallEndEvent
    | AuditEventEvent
    | PolicyDecisionEvent
    | SandboxViolationEvent
    | BudgetEntryEvent
    | AgentMessageEvent
    | ErrorEvent
)
RunlogEntry = Annotated[_RunlogUnion, Discriminator("event_type")]


_RUNLOG_ADAPTER: TypeAdapter[RunlogEntry] = TypeAdapter(RunlogEntry)


def serialise_runlog_line(entry: RunlogEntry) -> bytes:
    """Render a single RunlogEntry as JSON + ``\\n``, enforcing the 4 KB cap.

    Raises ``RunlogLineTooLarge`` if the resulting payload exceeds
    ``LINE_MAX_BYTES``. The cap matches POSIX ``PIPE_BUF`` so a downstream
    ``os.write(fd, line)`` on an ``O_APPEND``-opened fd is atomic w.r.t.
    other writers and crash boundaries.
    """
    payload = _RUNLOG_ADAPTER.dump_json(entry) + b"\n"
    if len(payload) > LINE_MAX_BYTES:
        raise RunlogLineTooLarge(
            f"runlog line is {len(payload)} bytes, exceeds {LINE_MAX_BYTES} "
            f"(POSIX PIPE_BUF); shrink the event payload"
        )
    return payload


def parse_runlog_line(line: bytes) -> RunlogEntry:
    """Round-trip helper used by reader/inspect tooling."""
    return _RUNLOG_ADAPTER.validate_json(line)


__all__ = [
    "LINE_MAX_BYTES",
    "AgentMessageEvent",
    "AuditEventEvent",
    "BudgetEntryEvent",
    "ErrorEvent",
    "PolicyDecisionEvent",
    "RunlogEntry",
    "RunlogLineTooLarge",
    "RunlogLineTooLargeError",
    "SandboxViolationEvent",
    "ToolCallEndEvent",
    "ToolCallStartEvent",
    "parse_runlog_line",
    "serialise_runlog_line",
]
