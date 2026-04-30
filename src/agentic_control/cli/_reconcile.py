"""``agentctl runs reconcile / mark-pending-reconcile / list --pending-reconcile``.

Implements the recovery-path commands from F0006 (PR3):

- ``reconcile``: interactive resolution of non-persisted local-only
  effects (ADR-0011 §118-128).
- ``mark-pending-reconcile``: explicit command run after Litestream
  restore to flag all ``running`` runs as ``needs_reconciliation``
  (F0006 R3-closure for AC 7 — no Daemon, no boot-id detection).
- ``list --pending-reconcile``: surface runs awaiting reconciliation.

Idempotency contract (F0006 AC 10): reconcile only operates on
local-only tool-calls that *lack* a prior ``reconcile_decision``
AuditEvent. A second invocation on an already-reconciled run finds
zero candidates, prints "nothing to reconcile", exits 0, and writes
no duplicate AuditEvent.
"""

from __future__ import annotations

from typing import Annotated

import typer

from agentic_control.cli._exit import EXIT_USER_ERROR, fail
from agentic_control.cli._format import short_id
from agentic_control.contracts import AuditEvent, ToolCallRecord
from agentic_control.persistence import (
    AmbiguousPrefixError,
    PrefixTooShortError,
    UnknownIdError,
    insert_audit_event,
    list_runs_in_state,
    list_unreconciled_local_only_tool_calls,
    make_engine,
    mark_running_runs_as_needs_reconciliation,
    resolve_id,
    update_run_state,
)

_RECONCILE_OPTIONS = ("erfolgt", "unsicher", "nicht_erfolgt")


def register(runs_app: typer.Typer) -> None:
    runs_app.command(
        name="reconcile",
        help=(
            "Interactively resolve non-persisted local-only effects of a run. "
            "Run must be in state=needs_reconciliation."
        ),
    )(reconcile)
    runs_app.command(
        name="mark-pending-reconcile",
        help=(
            "Mark all `running` runs as `needs_reconciliation` "
            "(post-Litestream-restore recovery)."
        ),
    )(mark_pending_reconcile)
    runs_app.command(
        name="list",
        help="List runs (filtered by --pending-reconcile).",
    )(list_runs)


# ---------- runs reconcile ----------


def reconcile(
    target: Annotated[
        str, typer.Argument(help="Run id (full UUIDv7) or 4+-char prefix")
    ],
) -> None:
    engine = make_engine()
    try:
        run_id = resolve_id(engine, "run", target)
    except AmbiguousPrefixError as exc:
        candidates = "\n  ".join(short_id(c) + "  " + c for c in exc.candidates[:5])
        fail(
            EXIT_USER_ERROR,
            f"prefix {target!r} matches {len(exc.candidates)} ids:\n  {candidates}",
        )
    except (PrefixTooShortError, UnknownIdError) as exc:
        fail(EXIT_USER_ERROR, str(exc))

    # Verify the run is in needs_reconciliation. We use `list_runs_in_state`
    # rather than a typed Run reader because v1a does not yet expose one
    # (consistent with `_inspect.py:_load_run_row`).
    pending_runs = list_runs_in_state(engine, "needs_reconciliation")
    run_row = next((r for r in pending_runs if r["id"] == str(run_id)), None)
    if run_row is None:
        fail(
            EXIT_USER_ERROR,
            f"run {short_id(run_id)} is not in state=needs_reconciliation; "
            f"reconcile only operates on that state",
        )

    pending = list_unreconciled_local_only_tool_calls(engine, run_id)
    if not pending:
        # AC 10: idempotent — re-running on a fully-reconciled run is a
        # no-op for AuditEvents. We still reset the lifecycle so the run
        # leaves needs_reconciliation. ADR-0011 §126-128 says post-
        # reconcile state is `running`. (Manual escalation to `failed`
        # is a separate `runs transition` operation, out of scope here.)
        print(f"run {short_id(run_id)}: nothing to reconcile")
        update_run_state(engine, run_id, "running")
        return

    print(
        f"run {short_id(run_id)}: {len(pending)} unreconciled local-only effect(s)"
    )
    print(f"options: {', '.join(_RECONCILE_OPTIONS)}")

    for tc in pending:
        choice = _prompt_for_choice(tc)
        # Write the AuditEvent BEFORE any state change so a crash mid-
        # reconcile leaves the lifecycle stale rather than the audit log
        # incomplete.
        insert_audit_event(
            engine,
            AuditEvent(
                actor="agentctl runs reconcile",
                subject_ref=f"tool_call_record:{tc.id}",
                event_type="reconcile_decision",
                reason=f"user-marked: {choice}",
                run_attempt_ref=tc.run_attempt_ref,
            ),
        )

    # ADR-0011 §126-128: post-reconcile, run returns to `running`.
    # Manual escalation to `failed` is a separate `runs transition`
    # operation, out of scope for this PR.
    update_run_state(engine, run_id, "running")
    print(f"run {short_id(run_id)}: reconciled, state → running")


def _prompt_for_choice(tc: ToolCallRecord) -> str:
    """Prompt until the user picks one of ``_RECONCILE_OPTIONS``.

    Empty input or any value outside the allowed set is rejected; the
    prompt re-asks. There is no default — every effect must be
    explicitly resolved (ADR-0011 §122-124: "manuell prüfen" for the
    ``unsicher`` arm; the user still has to *say* unsicher).
    """
    label = (
        f"  {tc.tool_name}  "
        f"(attempt={tc.run_attempt_ref}, ordinal={tc.tool_call_ordinal})"
    )
    while True:
        answer: str = typer.prompt(label)
        normalised = answer.strip().lower()
        if normalised in _RECONCILE_OPTIONS:
            return normalised
        typer.echo(
            f"  invalid choice {answer!r}; pick one of: "
            f"{', '.join(_RECONCILE_OPTIONS)}"
        )


# ---------- runs mark-pending-reconcile ----------


def mark_pending_reconcile(
    all_running: Annotated[
        bool,
        typer.Option(
            "--all-running",
            help="Mark all `running` runs (only mode supported)",
        ),
    ] = False,
) -> None:
    if not all_running:
        fail(
            EXIT_USER_ERROR,
            "--all-running is required (no other mode supported)",
        )
    engine = make_engine()
    n = mark_running_runs_as_needs_reconciliation(engine)
    print(f"marked {n} run(s) as needs_reconciliation")


# ---------- runs list --pending-reconcile ----------


def list_runs(
    pending_reconcile: Annotated[
        bool,
        typer.Option(
            "--pending-reconcile",
            help="List runs in state=needs_reconciliation",
        ),
    ] = False,
) -> None:
    if not pending_reconcile:
        fail(
            EXIT_USER_ERROR,
            "--pending-reconcile is required (no other mode supported)",
        )
    engine = make_engine()
    runs = list_runs_in_state(engine, "needs_reconciliation")
    if not runs:
        print("(no runs pending reconciliation)")
        return
    print(f"{len(runs)} run(s) pending reconciliation:")
    for r in runs:
        print(
            f"  {short_id(r['id'])}  "
            f"work_item={short_id(r['work_item_ref'])}  "
            f"agent={r['agent']}  created={r['created_at']}"
        )
