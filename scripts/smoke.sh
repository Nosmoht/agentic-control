#!/usr/bin/env bash
# End-to-end smoke test: exercises every v0 CLI subcommand non-interactively.
# Used by the Dockerfile's `smoke` stage and as a manual sanity check.
#
# Exit 0 iff every step succeeds. Stops at first failure (set -e).
# Re-runnable: wipes the smoke DB before starting.

set -euo pipefail

DB_DIR="${SMOKE_DB_DIR:-/tmp/agentctl-smoke}"
export AGENTIC_CONTROL_DB_URL="sqlite:///${DB_DIR}/state.db"

rm -rf "${DB_DIR}"
mkdir -p "${DB_DIR}"

echo "==> alembic upgrade head"
alembic upgrade head

echo "==> add project"
PROJECT_OUT=$(agentctl work add-project --title "Smoke Project" --output-json)
PROJECT_ID=$(printf '%s' "${PROJECT_OUT}" | python -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "    project=${PROJECT_ID}"

echo "==> add 5 work items"
declare -a WI_IDS=()
for i in 1 2 3 4 5; do
  OUT=$(agentctl work add --title "smoke item ${i}" --project "${PROJECT_ID}" --priority high --output-json)
  ID=$(printf '%s' "${OUT}" | python -c "import json,sys; print(json.load(sys.stdin)['id'])")
  WI_IDS+=("${ID}")
  echo "    wi[${i}]=${ID}"
done

echo "==> work next (expect 0 — none ready yet)"
agentctl work next

echo "==> drive item 1 through full lifecycle"
WI1="${WI_IDS[0]}"
for STATE in accepted planned ready in_progress completed; do
  agentctl work transition "${WI1}" "${STATE}"
done

echo "==> reject invalid transition (proposed -> completed) — expect exit 4"
WI2="${WI_IDS[1]}"
set +e
agentctl work transition "${WI2}" completed
RC=$?
set -e
if [ "${RC}" -ne 4 ]; then
  echo "FAIL: expected exit 4 for invalid transition, got ${RC}"
  exit 1
fi
echo "    OK exit=${RC}"

echo "==> add observation linked to item 2"
agentctl work add --observation "saw something on smoke run" --source-ref "${WI2}" --classification "manual"

echo "==> add decision via --from-file (heredoc)"
DECISION_FILE=$(mktemp)
cat > "${DECISION_FILE}" <<'EOF'
## Context
The smoke script needed to exercise the decision input path.

## Decision
Use --from-file with a heredoc-generated tempfile.

## Consequence
End-to-end coverage without an interactive editor.
EOF
agentctl work add --decision --subject "${WI2}" --from-file "${DECISION_FILE}"
rm -f "${DECISION_FILE}"

echo "==> add decision via stdin"
cat <<'EOF' | agentctl work add --decision --subject "${WI2}" --from-file -
## Context
Verify the stdin path works in headless mode.

## Decision
Pipe heredoc directly through --from-file -.

## Consequence
CI pipelines can drive the decision flow without touching the filesystem.
EOF

echo "==> show item 2 (expect 1 observation, 2 decisions)"
agentctl work show "${WI2}"

echo "==> ambiguous prefix detection — expect exit 2"
set +e
agentctl work show "0"
RC=$?
set -e
if [ "${RC}" -ne 2 ]; then
  echo "FAIL: expected exit 2 for prefix-too-short, got ${RC}"
  exit 1
fi
echo "    OK exit=${RC}"

echo "==> idempotent re-migration"
alembic upgrade head

echo
echo "smoke OK — DB at ${DB_DIR}/state.db"
