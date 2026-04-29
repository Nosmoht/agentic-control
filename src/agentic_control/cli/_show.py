"""``agentctl work show <id-or-prefix>``."""

from __future__ import annotations

from typing import Annotated

import typer

from agentic_control.cli._exit import EXIT_USER_ERROR, fail
from agentic_control.cli._format import emit, short_id
from agentic_control.persistence import (
    AmbiguousPrefixError,
    PrefixTooShortError,
    UnknownIdError,
    get_work_item,
    list_decisions_for_subject,
    list_observations_for_source,
    make_engine,
    resolve_id,
)


def register(work_app: typer.Typer) -> None:
    work_app.command(name="show", help="Show a work item with its decisions and observations.")(
        show
    )


def show(
    target: Annotated[str, typer.Argument(help="Work-item id (full UUIDv7) or 4+-char prefix")],
    output_json: Annotated[bool, typer.Option("--output-json", help="JSON output")] = False,
) -> None:
    engine = make_engine()
    try:
        wi_id = resolve_id(engine, "work_item", target)
    except AmbiguousPrefixError as exc:
        candidates = "\n  ".join(short_id(c) + "  " + c for c in exc.candidates[:5])
        fail(
            EXIT_USER_ERROR,
            f"prefix {target!r} matches {len(exc.candidates)} ids "
            f"(need at least {exc.minimal_unique_len} chars):\n  {candidates}",
        )
    except (PrefixTooShortError, UnknownIdError) as exc:
        fail(EXIT_USER_ERROR, str(exc))

    wi = get_work_item(engine, wi_id)
    assert wi is not None  # resolve_id verified existence

    decisions = list_decisions_for_subject(engine, wi.id)
    observations = list_observations_for_source(engine, wi.id)

    if output_json:
        emit(
            {"work_item": wi, "decisions": decisions, "observations": observations},
            True,
            "",
        )
        return

    lines = [
        f"work_item {wi.id}",
        f"  state    : {wi.state}",
        f"  priority : {wi.priority}",
        f"  project  : {wi.project_ref}",
        f"  title    : {wi.title}",
        f"  created  : {wi.created_at:%Y-%m-%d %H:%M:%S}",
    ]
    if decisions:
        lines.append("")
        lines.append(f"decisions ({len(decisions)}):")
        for d in decisions:
            lines.append(f"  {short_id(d.id)}  [{d.state:>10}]  {d.context.splitlines()[0][:60]}")
    if observations:
        lines.append("")
        lines.append(f"observations ({len(observations)}):")
        for o in observations:
            cls = f"  ({o.classification})" if o.classification else ""
            lines.append(f"  {short_id(o.id)}{cls}  {o.body.splitlines()[0][:60]}")

    print("\n".join(lines))
