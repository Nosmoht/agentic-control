"""Stub alert hook for runtime events (F0006 AC 13).

For v1a this is just a stdlib-logging shim. The real alert mechanism
(Slack/email/push) is a follow-up feature; mechanical replacement
substitutes the function body.
"""

from __future__ import annotations

import logging

from agentic_control.contracts import SandboxViolation

_LOGGER = logging.getLogger("agentic_control.alerts")


def emit_sandbox_violation_alert(violation: SandboxViolation) -> None:
    # TODO(F0006-followup): replace with real alert channel (Slack/email/push).
    # Contract: side-effect only, no return value, must not raise.
    _LOGGER.warning(
        "sandbox_violation: category=%s run_attempt=%s detail=%s",
        violation.category,
        violation.run_attempt_ref,
        violation.detail,
    )


__all__ = ["emit_sandbox_violation_alert"]
