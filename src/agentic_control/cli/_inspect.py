"""``agentctl runs inspect <id-or-prefix>`` (F0006 PR2).

Renders a run with its attempts, tool calls, audit events, policy
decisions, approvals, budget ledger entries, sandbox violations, and
the dispatch decision (≤ 1 per attempt).

Records sorted by their primary timestamp:
- attempts:     started_at ASC
- tool calls:   ordinal ASC (== started_at ASC by construction)
- audit:        ts ASC
- policies:     ts ASC
- approvals:    created_at ASC
- budget:       ts ASC
- sandbox:      ts ASC
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated, Any, cast

import typer
from sqlalchemy import Engine, text

from agentic_control import alerts
from agentic_control.cli._exit import EXIT_USER_ERROR, fail
from agentic_control.cli._format import emit, short_id
from agentic_control.contracts import (
    PolicyDecisionToolRiskMatch,
    PolicyTag,
    RunAttempt,
    SandboxViolation,
)
from agentic_control.persistence import (
    AmbiguousPrefixError,
    PrefixTooShortError,
    UnknownIdError,
    get_dispatch_decision_for_attempt,
    list_approval_requests_for_attempt,
    list_audit_events_for_attempt,
    list_budget_ledger_entries_for_attempt,
    list_policy_decisions_for_attempt,
    list_run_attempts_for_run,
    list_sandbox_violations_for_attempt,
    list_tool_calls_for_attempt_typed,
    make_engine,
    resolve_id,
)

_VALID_POLICY_TAGS: frozenset[str] = frozenset(
    {
        "admission",
        "dispatch",
        "tool_risk_match",
        "budget_gate_override",
        "hitl_trigger",
    }
)


def register(runs_app: typer.Typer) -> None:
    runs_app.command(
        name="inspect",
        help=(
            "Show a run with its attempts, tool calls, audit events, "
            "policy decisions, approvals, budget ledger, sandbox "
            "violations, and dispatch decision."
        ),
    )(inspect)


def inspect(
    target: Annotated[str, typer.Argument(help="Run id (full UUIDv7) or 4+-char prefix")],
    output_json: Annotated[
        bool, typer.Option("--output-json", help="JSON output")
    ] = False,
    policy: Annotated[
        str | None,
        typer.Option(
            "--policy",
            help="Filter policy_decision rows by tag (e.g. admission, tool_risk_match)",
        ),
    ] = None,
) -> None:
    if policy is not None and policy not in _VALID_POLICY_TAGS:
        fail(
            EXIT_USER_ERROR,
            f"unknown policy tag {policy!r}; valid: "
            + ", ".join(sorted(_VALID_POLICY_TAGS)),
        )

    engine = make_engine()
    try:
        run_id = resolve_id(engine, "run", target)
    except AmbiguousPrefixError as exc:
        candidates = "\n  ".join(short_id(c) + "  " + c for c in exc.candidates[:5])
        fail(
            EXIT_USER_ERROR,
            f"prefix {target!r} matches {len(exc.candidates)} ids "
            f"(need at least {exc.minimal_unique_len} chars):\n  {candidates}",
        )
    except (PrefixTooShortError, UnknownIdError) as exc:
        fail(EXIT_USER_ERROR, str(exc))

    run_row = _load_run_row(engine, run_id)
    if run_row is None:
        # resolve_id already verified existence; defensive only.
        fail(EXIT_USER_ERROR, f"no run with id {run_id}")

    attempts = list_run_attempts_for_run(engine, run_id)

    # Typed cast after fail() narrowing — line 85 already validated `policy`.
    assert run_row is not None
    policy_filter = cast("PolicyTag | None", policy)

    attempt_views: list[dict[str, Any]] = []
    sandbox_violations_seen: list[SandboxViolation] = []
    for att in attempts:
        view = _collect_attempt(engine, att, policy_filter=policy_filter)
        attempt_views.append(view)
        sandbox_violations_seen.extend(view["sandbox_violations"])

    # F0006 AC 13: emit one alert per observed sandbox violation.
    for violation in sandbox_violations_seen:
        alerts.emit_sandbox_violation_alert(violation)

    if output_json:
        emit(
            {
                "run": run_row,
                "attempts": attempt_views,
                "policy_filter": policy_filter,
            },
            True,
            "",
        )
        return

    print(_format_human(run_row, attempt_views, policy_filter=policy_filter))


# ---------- Helpers ----------


def _load_run_row(engine: Engine, run_id: uuid.UUID) -> dict[str, Any] | None:
    """Load the `run` row as a raw dict.

    There is no `Run`-typed read helper in the repository yet (PR2 is
    explicitly out of scope for adding one). The inspect CLI surfaces a
    handful of fields directly from the row dict; that means
    ``budget_cap`` round-trips as whatever SQLite gave the driver
    (str / Decimal / float depending on the NUMERIC affinity coercion).
    A future PR that adds a typed Run read helper will retire this
    asymmetry — at that point JSON output will guarantee Decimal-as-str.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM run WHERE id = :id"), {"id": str(run_id)}
        ).first()
    return dict(row._mapping) if row else None


def _collect_attempt(
    engine: Engine,
    attempt: RunAttempt,
    policy_filter: PolicyTag | None,
) -> dict[str, Any]:
    # 8 SELECTs per attempt. Acceptable at n=1 scale (Spec §1: ≤ 2 active
    # items). Revisit with prefetch-by-run_id when M ≥ 3 attempts becomes
    # typical.
    return {
        "attempt": attempt,
        "dispatch": get_dispatch_decision_for_attempt(engine, attempt.id),
        "tool_calls": list_tool_calls_for_attempt_typed(engine, attempt.id),
        "audit_events": list_audit_events_for_attempt(engine, attempt.id),
        "policy_decisions": list_policy_decisions_for_attempt(
            engine, attempt.id, policy=policy_filter
        ),
        "approvals": list_approval_requests_for_attempt(engine, attempt.id),
        "budget_entries": list_budget_ledger_entries_for_attempt(engine, attempt.id),
        "sandbox_violations": list_sandbox_violations_for_attempt(engine, attempt.id),
    }


def _format_human(
    run_row: dict[str, Any],
    attempt_views: list[dict[str, Any]],
    policy_filter: PolicyTag | None,
) -> str:
    lines: list[str] = []
    run_id_str = str(run_row["id"])
    state = run_row.get("state", "?")
    agent = run_row.get("agent", "?")
    budget_cap = run_row.get("budget_cap", "?")
    lines.append(
        f"run {short_id(run_id_str)} ({run_id_str})  state={state}  "
        f"agent={agent}  budget_cap=${budget_cap}"
    )

    if not attempt_views:
        lines.append("")
        lines.append("(no attempts)")
        return "\n".join(lines)

    for view in attempt_views:
        lines.append("")
        lines.extend(_format_attempt(view, policy_filter=policy_filter))

    return "\n".join(lines)


def _format_attempt(
    view: dict[str, Any], policy_filter: PolicyTag | None
) -> list[str]:
    att: RunAttempt = view["attempt"]
    out: list[str] = []
    started = att.started_at.isoformat(sep=" ", timespec="seconds")
    ended = (
        att.ended_at.isoformat(sep=" ", timespec="seconds")
        if att.ended_at is not None
        else "—"
    )
    exit_code = "—" if att.exit_code is None else str(att.exit_code)
    out.append(
        f"attempt {att.attempt_ordinal}  agent={att.agent}  model={att.model}  "
        f"started={started}  ended={ended}  exit={exit_code}"
    )

    dispatch = view["dispatch"]
    if dispatch is not None:
        out.append(
            f"  dispatch: adapter={dispatch.adapter} model={dispatch.model} "
            f"mode={dispatch.mode} reason={dispatch.reason}"
        )

    tool_calls = view["tool_calls"]
    if tool_calls:
        out.append(f"  tool calls ({len(tool_calls)}):")
        for tc in tool_calls:
            idem = tc.idempotency_key or "—"
            status = "ok" if tc.exit_code in (None, 0) else f"exit={tc.exit_code}"
            out.append(
                f"    {tc.tool_call_ordinal}. {tc.tool_name}  effect={tc.effect_class}  "
                f"idem={idem}  hash={tc.input_hash}  status={status}"
            )

    audit_events = view["audit_events"]
    if audit_events:
        out.append(f"  audit ({len(audit_events)}):")
        for ev in audit_events:
            ts = ev.ts.isoformat(sep=" ", timespec="seconds")
            subj = _truncate(str(ev.subject_ref), 40)
            out.append(f"    {ts}  {ev.actor}  {ev.event_type}  {subj}")

    policies = view["policy_decisions"]
    suffix = f" [filter={policy_filter}]" if policy_filter else ""
    if policies:
        out.append(f"  policies ({len(policies)}){suffix}:")
        for pd in policies:
            ts = pd.ts.isoformat(sep=" ", timespec="seconds")
            subj = _truncate(pd.subject_ref, 40)
            if isinstance(pd, PolicyDecisionToolRiskMatch):
                payload = (
                    f"matched={pd.output.matched_pattern}  "
                    f"risk={pd.output.risk}  approval={pd.output.approval}  "
                    f"default_hit={pd.output.default_hit}"
                )
            else:
                payload = _summarize_dict(pd.output)
            out.append(f"    {ts}  {pd.policy}  {subj}  {payload}")
    elif policy_filter:
        # Filter explicitly set but matched zero rows — surface that.
        out.append(f"  policies (0){suffix}")

    approvals = view["approvals"]
    if approvals:
        out.append(f"  approvals ({len(approvals)}):")
        for ap in approvals:
            q = _truncate(ap.question, 60)
            out.append(
                f"    {short_id(ap.id)}  {ap.state}  {ap.risk_class}  {q}"
            )

    budget = view["budget_entries"]
    if budget:
        # Split: settled charges (actual) vs. open projections. Mixing the
        # two into one sum hid two bugs — `Decimal("0")` is falsy so a
        # literal-zero actual_usd would silently fall back to the
        # projection, and "actual + projected" is semantically incoherent.
        actual_total = sum(
            (b.actual_usd for b in budget if b.actual_usd is not None),
            Decimal("0"),
        )
        projected_total = sum(
            (b.pre_call_projection_usd for b in budget if b.actual_usd is None),
            Decimal("0"),
        )
        out.append(
            f"  budget ({len(budget)} entries, "
            f"actual=${actual_total} projected=${projected_total}):"
        )
        for b in budget:
            ts = b.ts.isoformat(sep=" ", timespec="seconds")
            actual = "—" if b.actual_usd is None else f"${b.actual_usd}"
            out.append(
                f"    {ts}  {b.scope}  {b.model}  "
                f"pre=${b.pre_call_projection_usd}  actual={actual}"
            )

    violations = view["sandbox_violations"]
    if violations:
        out.append(f"  sandbox violations ({len(violations)}):")
        for sv in violations:
            ts = sv.ts.isoformat(sep=" ", timespec="seconds")
            detail = _summarize_dict(sv.detail)
            out.append(f"    {ts}  {sv.category}  {detail}")

    return out


def _truncate(value: str, length: int) -> str:
    if len(value) <= length:
        return value
    return value[: length - 1] + "…"


def _summarize_dict(d: dict[str, Any]) -> str:
    if not d:
        return "{}"
    items = list(d.items())[:3]
    rendered = ", ".join(f"{k}={v}" for k, v in items)
    suffix = ", …" if len(d) > 3 else ""
    return "{" + rendered + suffix + "}"
