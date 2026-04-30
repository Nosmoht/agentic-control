"""Application-layer validator for polymorphic ``evidence.subject_ref`` (F0008).

SQLite cannot express a polymorphic FK without trigger-magic that is overkill
for n=1. The ``evidence`` table's CHECK constraints enforce shape (prefix,
length); existence of the referenced row in the kind-specific table is
enforced here, called by F0006's repository ahead of every evidence insert.

Adding a new subject kind is an atomic three-file change (see F0008 §AC10):
1. extend the migration's ``ck_evidence_subject_ref_*`` CHECK constraints,
2. add a new arm to ``EvidenceSubjectRef`` in ``contracts.evidence``,
3. add a new branch below.
"""

from __future__ import annotations

from sqlalchemy import Engine, text

from agentic_control.contracts.evidence import (
    ArtifactSubjectRef,
    DecisionSubjectRef,
    EvidenceSubjectRef,
    RunSubjectRef,
    WorkItemSubjectRef,
)
from agentic_control.persistence.repository import RepositoryError

_TABLE_BY_REF_TYPE: dict[type, str] = {
    WorkItemSubjectRef: "work_item",
    RunSubjectRef: "run",
    ArtifactSubjectRef: "artifact",
    DecisionSubjectRef: "decision",
}


def validate_subject_ref(engine: Engine, ref: EvidenceSubjectRef) -> None:
    """Raise ``RepositoryError`` if no row matches ``ref`` in its target table.

    ``ref`` is a discriminated-union instance built either by Pydantic from
    user input or by ``contracts.evidence.parse_subject_ref`` from a stored
    ``<kind>:<id>`` string.
    """
    table = _TABLE_BY_REF_TYPE.get(type(ref))
    if table is None:  # pragma: no cover — discriminator covers all kinds
        raise RepositoryError(f"unsupported evidence subject kind: {ref!r}")
    sql = text(f"SELECT 1 FROM {table} WHERE id = :id LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(sql, {"id": str(ref.id)}).first()
    if row is None:
        raise RepositoryError(
            f"evidence.subject_ref points at missing {table}: {ref.render()}"
        )


__all__ = ["validate_subject_ref"]
