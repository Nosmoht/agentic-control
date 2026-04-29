"""``agentctl work next``."""

from __future__ import annotations

from typing import Annotated

import typer

from agentic_control.cli._exit import EXIT_USER_ERROR, fail
from agentic_control.cli._format import emit, short_id
from agentic_control.persistence import (
    AmbiguousPrefixError,
    PrefixTooShortError,
    UnknownIdError,
    list_next_work_items,
    make_engine,
    resolve_id,
)


def register(work_app: typer.Typer) -> None:
    work_app.command(name="next", help="Show the next ready/accepted work items (max 3).")(
        next_items
    )


def next_items(
    project: Annotated[
        str | None, typer.Option("--project", help="Limit to project id or prefix")
    ] = None,
    output_json: Annotated[bool, typer.Option("--output-json", help="JSON output")] = False,
) -> None:
    engine = make_engine()
    project_ref = None
    if project:
        try:
            project_ref = resolve_id(engine, "project", project)
        except (PrefixTooShortError, UnknownIdError, AmbiguousPrefixError) as exc:
            fail(EXIT_USER_ERROR, str(exc))

    items = list_next_work_items(engine, project_ref=project_ref)
    if not items:
        emit({"items": []}, output_json, "No open work items.")
        return

    lines = [
        f"{short_id(i.id)}  [{i.priority:>4}]  {i.state:>11}  {i.title}"
        for i in items
    ]
    emit({"items": items}, output_json, "\n".join(lines))
