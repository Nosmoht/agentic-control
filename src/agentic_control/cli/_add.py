"""``agentctl work add`` — work item, observation, decision."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from agentic_control.cli import _decision_input
from agentic_control.cli._exit import EXIT_USER_ERROR, EXIT_VALIDATION, fail
from agentic_control.cli._format import emit, short_id
from agentic_control.contracts import Decision, Observation, Project, WorkItem, WorkItemPriority
from agentic_control.persistence import (
    AmbiguousPrefixError,
    PrefixTooShortError,
    RepositoryError,
    UnknownIdError,
    get_work_item,
    insert_decision,
    insert_observation,
    insert_project,
    insert_work_item,
    make_engine,
    resolve_id,
)


def register(work_app: typer.Typer) -> None:
    work_app.command(name="add", help="Add a work item, observation or decision.")(add)
    work_app.command(name="add-project", help="Add a project (auto-set 'active').")(add_project)


def add_project(
    title: Annotated[str, typer.Option("--title", help="Project title")],
    output_json: Annotated[bool, typer.Option("--output-json", help="JSON output")] = False,
) -> None:
    engine = make_engine()
    try:
        proj = insert_project(engine, Project(title=title, state="active"))
    except (ValidationError, RepositoryError) as exc:
        fail(EXIT_VALIDATION, str(exc))
    emit(
        proj,
        output_json,
        f"created project {short_id(proj.id)}  state={proj.state}  title={proj.title!r}",
    )


def add(
    title: Annotated[str | None, typer.Option("--title", help="Work-item title")] = None,
    project: Annotated[
        str | None, typer.Option("--project", help="Project id or prefix")
    ] = None,
    priority: Annotated[
        WorkItemPriority, typer.Option("--priority", help="low | med | high")
    ] = "med",
    observation: Annotated[
        str | None, typer.Option("--observation", help="Observation body")
    ] = None,
    source_ref: Annotated[
        str | None, typer.Option("--source-ref", help="Optional source id or prefix")
    ] = None,
    classification: Annotated[
        str | None, typer.Option("--classification", help="Free-text classification (v0)")
    ] = None,
    decision: Annotated[
        bool, typer.Option("--decision", help="Add a decision against --subject")
    ] = False,
    subject: Annotated[
        str | None, typer.Option("--subject", help="Work-item id/prefix for the decision")
    ] = None,
    from_file: Annotated[
        Path | None, typer.Option("--from-file", help="Read decision body from file ('-' = stdin)")
    ] = None,
    context: Annotated[str | None, typer.Option("--context", help="Decision context")] = None,
    decision_text: Annotated[
        str | None, typer.Option("--decision-text", help="Decision body")
    ] = None,
    consequence: Annotated[
        str | None, typer.Option("--consequence", help="Decision consequence")
    ] = None,
    output_json: Annotated[bool, typer.Option("--output-json", help="JSON output")] = False,
) -> None:
    """Add work-item, observation, or decision; mutually exclusive modes."""
    modes = [bool(title), bool(observation), decision]
    if sum(modes) != 1:
        fail(EXIT_USER_ERROR, "specify exactly one of --title, --observation, or --decision")

    engine = make_engine()

    if title:
        _add_work_item(engine, title, project, priority, output_json)
    elif observation:
        _add_observation(engine, observation, source_ref, classification, output_json)
    else:
        if not subject:
            fail(EXIT_USER_ERROR, "--decision requires --subject <work-item-id-or-prefix>")
        assert subject is not None
        _add_decision(
            engine, subject, from_file, context, decision_text, consequence, output_json
        )


def _add_work_item(
    engine, title: str, project: str | None, priority: WorkItemPriority, output_json: bool
) -> None:
    if project is None:
        fail(EXIT_USER_ERROR, "--project is required for --title")
    try:
        project_id = resolve_id(engine, "project", project)  # type: ignore[arg-type]
    except (PrefixTooShortError, UnknownIdError, AmbiguousPrefixError) as exc:
        fail(EXIT_USER_ERROR, str(exc))
    try:
        item = insert_work_item(
            engine, WorkItem(project_ref=project_id, title=title, priority=priority)
        )
    except (ValidationError, RepositoryError) as exc:
        fail(EXIT_VALIDATION, str(exc))
    emit(
        item,
        output_json,
        f"created work_item {short_id(item.id)}  state={item.state}  title={item.title!r}",
    )


def _add_observation(
    engine,
    body: str,
    source_ref: str | None,
    classification: str | None,
    output_json: bool,
) -> None:
    src: uuid.UUID | None = None
    if source_ref:
        try:
            src = resolve_id(engine, "work_item", source_ref)  # type: ignore[arg-type]
        except (PrefixTooShortError, UnknownIdError, AmbiguousPrefixError) as exc:
            fail(EXIT_USER_ERROR, str(exc))
    try:
        obs = insert_observation(
            engine,
            Observation(body=body, source_ref=src, classification=classification),
        )
    except (ValidationError, RepositoryError) as exc:
        fail(EXIT_VALIDATION, str(exc))
    emit(obs, output_json, f"created observation {short_id(obs.id)}  body={obs.body!r}")


def _add_decision(
    engine,
    subject: str,
    from_file: Path | None,
    context: str | None,
    decision_text: str | None,
    consequence: str | None,
    output_json: bool,
) -> None:
    try:
        subject_id = resolve_id(engine, "work_item", subject)  # type: ignore[arg-type]
    except (PrefixTooShortError, UnknownIdError, AmbiguousPrefixError) as exc:
        fail(EXIT_USER_ERROR, str(exc))
    if get_work_item(engine, subject_id) is None:
        fail(EXIT_USER_ERROR, f"work_item {subject_id} not found")

    try:
        body = _decision_input.collect(
            subject_ref=subject_id,
            from_file=from_file,
            context=context,
            decision_text=decision_text,
            consequence=consequence,
        )
    except _decision_input.EmptyDecisionAbort:
        return  # silent no-op (exit 0)
    except _decision_input.DecisionInputError as exc:
        fail(EXIT_USER_ERROR, str(exc))

    try:
        dec = insert_decision(
            engine,
            Decision(
                subject_ref=subject_id,
                context=body.context,
                decision=body.decision,
                consequence=body.consequence,
            ),
        )
    except (ValidationError, RepositoryError) as exc:
        # Keep draft for recovery on next run.
        fail(EXIT_VALIDATION, str(exc))

    _decision_input.cleanup_draft(subject_id)
    emit(
        dec,
        output_json,
        f"created decision {short_id(dec.id)}  on work_item {short_id(dec.subject_ref)}",
    )
