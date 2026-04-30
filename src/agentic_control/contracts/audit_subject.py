"""Audit-event subject-reference contracts (F0006).

`AuditEvent.subject_ref` is mixed-domain: it points at either a domain
object via the polymorphic ``<kind>:<uuid>`` form (analog F0008
`EvidenceSubjectRef`) or at a config-file path (ADR-0016, e.g.
``config/dispatch/routing-pins.yaml``). The migration installs CHECK
constraints that mirror these two forms; this module is the canonical
Pydantic validator (ADR-0018).

Design decision: a discriminated union over kind versus a freer regex
type was rejected because config-file refs do not naturally have a
``kind`` discriminator. Instead a single Annotated string type runs an
AfterValidator that accepts either pattern.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator

DOMAIN_REF_PATTERN = re.compile(
    r"^(work_item|run|run_attempt|decision):[0-9a-f-]{36}$"
)
CONFIG_PATH_PATTERN = re.compile(r"^config/[A-Za-z0-9_./\-]+$")


def _validate_audit_subject_ref(value: str) -> str:
    if DOMAIN_REF_PATTERN.match(value):
        return value
    if CONFIG_PATH_PATTERN.match(value):
        return value
    raise ValueError(
        f"audit_event.subject_ref must be either '<kind>:<uuid>' "
        f"(kind in work_item|run|run_attempt|decision) or a path under "
        f"'config/'; got {value!r}"
    )


AuditSubjectRef = Annotated[str, AfterValidator(_validate_audit_subject_ref)]


__all__ = [
    "CONFIG_PATH_PATTERN",
    "DOMAIN_REF_PATTERN",
    "AuditSubjectRef",
]
