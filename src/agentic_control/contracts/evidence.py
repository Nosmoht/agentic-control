"""Evidence subject-reference contracts (F0008).

The `EvidenceSubjectRef` discriminated union encodes the polymorphic
``<kind>:<id>`` reference stored in the `evidence.subject_ref` column.
Pydantic owns canonical shape per ADR-0018; the migration adds a CHECK
constraint that mirrors the same regex as defense-in-depth.

Spec §5.7: Evidence has subject_ref pointing at one of work_item, run,
artifact, decision. ID-existence is enforced on the application layer
by `persistence.evidence_validator.validate_subject_ref` — SQLite cannot
express a polymorphic FK without trigger-magic that is overkill for n=1.
"""

from __future__ import annotations

import re
import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Discriminator

from agentic_control.contracts.ids import UUIDv7
from agentic_control.contracts.lifecycle import EvidenceSubjectKind

SUBJECT_REF_PATTERN = re.compile(r"^(work_item|run|artifact|decision):([0-9a-fA-F-]{36})$")


class _SubjectRefBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: UUIDv7

    def render(self) -> str:
        return f"{self.kind}:{self.id}"  # type: ignore[attr-defined]


class WorkItemSubjectRef(_SubjectRefBase):
    kind: Literal["work_item"] = "work_item"


class RunSubjectRef(_SubjectRefBase):
    kind: Literal["run"] = "run"


class ArtifactSubjectRef(_SubjectRefBase):
    kind: Literal["artifact"] = "artifact"


class DecisionSubjectRef(_SubjectRefBase):
    kind: Literal["decision"] = "decision"


EvidenceSubjectRef = Annotated[
    WorkItemSubjectRef | RunSubjectRef | ArtifactSubjectRef | DecisionSubjectRef,
    Discriminator("kind"),
]

_SUBJECT_KIND_CLASSES: dict[EvidenceSubjectKind, type[_SubjectRefBase]] = {
    "work_item": WorkItemSubjectRef,
    "run": RunSubjectRef,
    "artifact": ArtifactSubjectRef,
    "decision": DecisionSubjectRef,
}


def parse_subject_ref(rendered: str) -> _SubjectRefBase:
    """Parse a ``<kind>:<id>`` string into the matching subject-ref model.

    Raises ``ValueError`` if the format is malformed or the kind is unknown.
    """
    match = SUBJECT_REF_PATTERN.match(rendered)
    if not match:
        raise ValueError(f"malformed evidence subject_ref: {rendered!r}")
    kind, raw_id = match.group(1), match.group(2)
    cls = _SUBJECT_KIND_CLASSES.get(kind)  # type: ignore[arg-type]
    if cls is None:  # pragma: no cover — pattern enforces enum
        raise ValueError(f"unknown evidence subject kind: {kind!r}")
    return cls(id=uuid.UUID(raw_id))


__all__ = [
    "SUBJECT_REF_PATTERN",
    "ArtifactSubjectRef",
    "DecisionSubjectRef",
    "EvidenceSubjectRef",
    "RunSubjectRef",
    "WorkItemSubjectRef",
    "parse_subject_ref",
]
