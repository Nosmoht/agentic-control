"""F0006a · AC 8 — JSONL Runlog 4 KB cap and atomic append-only writes."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from agentic_control.contracts import (
    LINE_MAX_BYTES,
    AgentMessageEvent,
    RunlogLineTooLarge,
    SandboxViolationEvent,
    ToolCallStartEvent,
    new_id,
    parse_runlog_line,
    serialise_runlog_line,
)
from agentic_control.persistence import append_runlog_line, runlog_writer


def _ts() -> datetime:
    return datetime(2026, 4, 30, 12, 0, 0)


def _tool_start_event(seq: int = 0) -> ToolCallStartEvent:
    return ToolCallStartEvent(
        ts=_ts(),
        level="info",
        run_attempt_id=new_id(),
        seq=seq,
        tool_name="git.commit",
        tool_call_id=new_id(),
        args_hash="abcdef012345",
    )


# ---------- Serialisation cap ----------


def test_small_event_serialises_under_cap() -> None:
    payload = serialise_runlog_line(_tool_start_event())
    assert len(payload) <= LINE_MAX_BYTES
    assert payload.endswith(b"\n")
    parsed = parse_runlog_line(payload.rstrip(b"\n"))
    assert parsed.event_type == "tool_call_start"


def test_oversize_event_raises_runlog_line_too_large() -> None:
    """An AgentMessage with a 5 KB body must trip the 4 KB cap."""
    huge_body = "x" * 5000
    event = AgentMessageEvent(
        ts=_ts(),
        level="info",
        run_attempt_id=new_id(),
        seq=0,
        body=huge_body,
    )
    with pytest.raises(RunlogLineTooLarge, match="exceeds 4096"):
        serialise_runlog_line(event)


def test_serialise_round_trip_for_each_event_type() -> None:
    """Serialising and re-parsing preserves the discriminator + payload."""
    base = {
        "ts": _ts(),
        "level": "info",
        "run_attempt_id": new_id(),
        "seq": 0,
    }
    sandbox = SandboxViolationEvent(
        **base, category="egress_denied", detail={"host": "example.com"}
    )
    payload = serialise_runlog_line(sandbox)
    parsed = parse_runlog_line(payload.rstrip(b"\n"))
    assert parsed == sandbox


# ---------- O_APPEND single-syscall write ----------


def test_append_runlog_line_is_single_os_write(tmp_path: Path) -> None:
    """append_runlog_line must call os.write exactly once per event with the
    full serialised payload (atomicity guarantee)."""
    log = tmp_path / "run.jsonl"
    with runlog_writer(log) as fd:
        n = append_runlog_line(fd, _tool_start_event(seq=0))
    assert n > 0
    assert n == log.stat().st_size
    text_lines = log.read_text().splitlines()
    assert len(text_lines) == 1
    json.loads(text_lines[0])  # parses


def test_append_three_events_yields_three_lines(tmp_path: Path) -> None:
    log = tmp_path / "run.jsonl"
    rid = new_id()
    events = [
        ToolCallStartEvent(
            ts=_ts(),
            level="info",
            run_attempt_id=rid,
            seq=i,
            tool_name="x",
            tool_call_id=new_id(),
            args_hash="abcdef012345",
        )
        for i in range(3)
    ]
    with runlog_writer(log) as fd:
        for ev in events:
            append_runlog_line(fd, ev)
    lines = log.read_text().splitlines()
    assert len(lines) == 3
    assert all(json.loads(line)["seq"] == i for i, line in enumerate(lines))


def test_open_runlog_fd_uses_o_append(tmp_path: Path) -> None:
    """Re-opening an existing file must append, not truncate."""
    log = tmp_path / "run.jsonl"
    log.write_text('{"prior": true}\n')
    with runlog_writer(log) as fd:
        append_runlog_line(fd, _tool_start_event(seq=0))
    lines = log.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"prior": True}
    assert json.loads(lines[1])["event_type"] == "tool_call_start"


def test_o_append_flag_set_on_fd(tmp_path: Path) -> None:
    """The fd opened by runlog_writer must carry O_APPEND so the kernel does
    the seek-to-end + write atomically in one syscall."""
    import fcntl

    log = tmp_path / "run.jsonl"
    with runlog_writer(log) as fd:
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    assert flags & os.O_APPEND, f"fd flags={flags:o} missing O_APPEND ({os.O_APPEND:o})"
