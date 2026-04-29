"""``agentctl`` Typer entrypoint.

Subcommand layout:

    agentctl work add ...
    agentctl work next
    agentctl work show <id-or-prefix>
    agentctl work transition <id-or-prefix> <state>
"""

from __future__ import annotations

import typer

from agentic_control.cli import _add, _next, _show, _transition

app = typer.Typer(
    name="agentctl",
    help="Personal Agentic Control System — v0 CLI",
    no_args_is_help=True,
)

work = typer.Typer(
    name="work",
    help="Work-item, observation and decision commands",
    no_args_is_help=True,
)
app.add_typer(work, name="work")

_add.register(work)
_next.register(work)
_show.register(work)
_transition.register(work)


if __name__ == "__main__":
    app()
