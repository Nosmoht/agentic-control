"""Append-only JSONL Runlog writer (F0006 AC 8).

Single-syscall write under POSIX ``O_APPEND``. The contract layer
(`contracts.runlog.serialise_runlog_line`) enforces the 4 KB cap before
the bytes ever reach this module, so the ``os.write(fd, payload)`` call
is guaranteed atomic w.r.t. other writers and crash boundaries (POSIX
``PIPE_BUF`` = 4096 on Linux/macOS).

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

    Returns the number of bytes written.
    """
    payload = serialise_runlog_line(entry)
    return os.write(fd, payload)


@contextlib.contextmanager
def runlog_writer(path: Path) -> Iterator[int]:
    """Context-managed append-only fd. Closes the fd on exit."""
    fd = open_runlog_fd(path)
    try:
        yield fd
    finally:
        os.close(fd)


__all__ = ["append_runlog_line", "open_runlog_fd", "runlog_writer"]
