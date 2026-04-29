"""Multiline input handling for ``work add --decision``.

Hybrid pattern (precedence top → bottom):

1. ``--from-file <path>`` (with ``-`` reading stdin)
2. Three explicit flags ``--context``, ``--decision-text``, ``--consequence``
3. ``$EDITOR`` launched via ``click.edit()`` with MADR template
4. stdin (when no TTY and no other input mode)

Drafts persist in ``$XDG_STATE_HOME/agentic-control/decision-<subject>.draft.md``
so a validation error in step (3) does not lose typed text.
"""

from __future__ import annotations

import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click
from xdg_base_dirs import xdg_state_home

TEMPLATE = """\
## Context
<warum jetzt, welcher Druck>

## Decision
<was wir tun>

## Consequence
<was sich ändert, was wir aufgeben>

# Lines starting with '#' are stripped before saving.
# An empty buffer or aborted save means no decision is created (exit 0).
"""

_SECTION_RE = re.compile(
    r"^##\s+(Context|Decision|Consequence)\s*$", re.MULTILINE | re.IGNORECASE
)


@dataclass(frozen=True)
class DecisionBody:
    context: str
    decision: str
    consequence: str


class DecisionInputError(Exception):
    """Raised on parse / mode-specific input failures."""


class EmptyDecisionAbort(Exception):  # noqa: N818
    """Control-flow signal: user aborted editor or saved empty buffer (silent no-op)."""


def draft_path(subject_ref: uuid.UUID) -> Path:
    return xdg_state_home() / "agentic-control" / f"decision-{subject_ref}.draft.md"


def collect(
    *,
    subject_ref: uuid.UUID,
    from_file: Path | None,
    context: str | None,
    decision_text: str | None,
    consequence: str | None,
) -> DecisionBody:
    """Return a DecisionBody following the precedence in module docstring."""
    if from_file is not None:
        return _from_file(from_file)
    if any(v is not None for v in (context, decision_text, consequence)):
        return _from_flags(context, decision_text, consequence)
    if sys.stdin.isatty():
        return _from_editor(subject_ref)
    return _from_stdin()


def cleanup_draft(subject_ref: uuid.UUID) -> None:
    p = draft_path(subject_ref)
    if p.exists():
        p.unlink()


def _from_file(path: Path | str) -> DecisionBody:
    if str(path) == "-":
        return _parse_markdown(sys.stdin.read())
    p = Path(path)
    if not p.is_file():
        raise DecisionInputError(f"file not found: {path}")
    return _parse_markdown(p.read_text())


def _from_flags(
    context: str | None, decision_text: str | None, consequence: str | None
) -> DecisionBody:
    missing = [
        name
        for name, value in [
            ("--context", context),
            ("--decision-text", decision_text),
            ("--consequence", consequence),
        ]
        if value is None
    ]
    if missing:
        raise DecisionInputError(
            f"flag mode requires all three: missing {', '.join(missing)}"
        )
    assert context and decision_text and consequence
    return DecisionBody(
        context=context.strip(), decision=decision_text.strip(), consequence=consequence.strip()
    )


def _from_stdin() -> DecisionBody:
    raw = sys.stdin.read()
    if not raw.strip():
        raise DecisionInputError("stdin was empty (no decision body)")
    return _parse_markdown(raw)


def _from_editor(subject_ref: uuid.UUID) -> DecisionBody:
    path = draft_path(subject_ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    seed = path.read_text() if path.exists() else TEMPLATE
    if path.exists():
        ts = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
        print(f"info: continuing draft from {ts}", file=sys.stderr)

    edited = click.edit(seed, extension=".md", require_save=True)
    if edited is None or not _strip_comments(edited).strip():
        raise EmptyDecisionAbort()

    path.write_text(edited)
    return _parse_markdown(_strip_comments(edited))


def _strip_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _parse_markdown(text: str) -> DecisionBody:
    sections: dict[str, list[str]] = {"context": [], "decision": [], "consequence": []}
    current: str | None = None
    for line in text.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            current = match.group(1).lower()
            continue
        if current and not line.lstrip().startswith("#"):
            sections[current].append(line)

    body = {k: "\n".join(v).strip() for k, v in sections.items()}
    if not all(body.values()):
        missing = [k for k, v in body.items() if not v]
        raise DecisionInputError(
            f"missing or empty MADR sections: {', '.join(missing)}"
        )
    return DecisionBody(
        context=body["context"], decision=body["decision"], consequence=body["consequence"]
    )
