"""Append-only JSONL Runlog writer (F0006 AC 8).

Single-syscall write under POSIX ``O_APPEND``. Linux ``open(2)`` and
macOS APFS make the seek-to-end + write atomic for any size on a
regular file when ``O_APPEND`` is set; ``PIPE_BUF`` only bounds
atomicity on pipes/FIFOs. The 4 KB cap enforced upstream by
``serialise_runlog_line`` is a sanity guard against bloated events,
not the source of atomicity.

Short-write handling: on a regular file a partial ``os.write`` indicates
disk-full or signal-interrupt; the contract is **fail-loud**, because
re-issuing the remainder would split the line into two append-blocks
and break the atomicity invariant for parallel readers.

Usage:

    fd = open_runlog_fd(Path("~/.agentic-control/logs/runs/<id>.jsonl"))
    try:
        append_runlog_line(fd, entry)
    finally:
        os.close(fd)

A higher-level context manager lives below for the common case.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from pathlib import Path

from agentic_control.contracts.runlog import RunlogEntry, serialise_runlog_line


def open_runlog_fd(path: Path) -> int:
    """Open *path* for append-only writes; create parents if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)


def append_runlog_line(fd: int, entry: RunlogEntry) -> int:
    """Serialise *entry* via the 4 KB-capped helper and emit one ``os.write``.

    Returns the number of bytes written. Raises ``OSError`` if the kernel
    reports a short write — re-issuing would tear the JSONL line, so the
    caller must surface the failure.
    """
    payload = serialise_runlog_line(entry)
    n = os.write(fd, payload)
    if n != len(payload):
        raise OSError(
            f"runlog short write: wrote {n} of {len(payload)} bytes; "
            "torn JSONL line — disk full or signal-interrupted"
        )
    return n


@contextlib.contextmanager
def runlog_writer(path: Path) -> Iterator[int]:
    """Context-managed append-only fd. Closes the fd on exit."""
    fd = open_runlog_fd(path)
    try:
        yield fd
    finally:
        os.close(fd)


__all__ = ["append_runlog_line", "open_runlog_fd", "runlog_writer"]
