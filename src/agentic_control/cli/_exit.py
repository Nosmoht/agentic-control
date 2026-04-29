"""CLI exit codes per F0002 spec."""

from __future__ import annotations

import sys

import typer

EXIT_OK = 0
EXIT_USER_ERROR = 2
EXIT_VALIDATION = 3
EXIT_TRANSITION = 4


def fail(code: int, message: str) -> None:
    """Print a stderr message and raise typer.Exit with the given code."""
    print(f"error: {message}", file=sys.stderr)
    raise typer.Exit(code=code)
