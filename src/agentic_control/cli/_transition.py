"""``agentctl work transition <id-or-prefix> <state>``."""

from __future__ import annotations

from typing import Annotated, get_args

import typer

from agentic_control.cli._exit import EXIT_TRANSITION, EXIT_USER_ERROR, fail
from agentic_control.cli._format import short_id
from agentic_control.contracts import (
    WORK_ITEM_TRANSITIONS,
    WorkItemState,
    is_valid_transition,
)
from agentic_control.persistence import (
    AmbiguousPrefixError,
    PrefixTooShortError,
    UnknownIdError,
    get_work_item,
    make_engine,
    resolve_id,
    update_work_item_state,
)


def register(work_app: typer.Typer) -> None:
    work_app.command(name="transition", help="Transition a work item to a new lifecycle state.")(
        transition
    )


def transition(
    target: Annotated[str, typer.Argument(help="Work-item id or 4+-char prefix")],
    new_state: Annotated[str, typer.Argument(help="New lifecycle state")],
) -> None:
    engine = make_engine()
    try:
        wi_id = resolve_id(engine, "work_item", target)
    except (PrefixTooShortError, UnknownIdError, AmbiguousPrefixError) as exc:
        fail(EXIT_USER_ERROR, str(exc))

    valid_states: tuple[str, ...] = tuple(get_args(WorkItemState))
    if new_state not in valid_states:
        fail(
            EXIT_USER_ERROR,
            f"unknown state {new_state!r}; valid: {', '.join(valid_states)}",
        )

    wi = get_work_item(engine, wi_id)
    assert wi is not None
    if not is_valid_transition(wi.state, new_state):  # type: ignore[arg-type]
        allowed = sorted(WORK_ITEM_TRANSITIONS[wi.state])
        allowed_str = ", ".join(allowed) or "<none — terminal state>"
        fail(
            EXIT_TRANSITION,
            f"cannot transition {wi.state} → {new_state}; allowed from {wi.state}: {allowed_str}",
        )

    changed = update_work_item_state(engine, wi.id, new_state)  # type: ignore[arg-type]
    assert changed
    print(f"transitioned {short_id(wi.id)}  {wi.state} → {new_state}")
