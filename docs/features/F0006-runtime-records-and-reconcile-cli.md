---
id: F0006
title: Runtime Records SQLite Schema and Reconcile CLI
stage: v1a
status: proposed
spec_refs: [§5.7, §6.2, §8.4, §10.4]
adr_refs: [ADR-0001, ADR-0003, ADR-0011, ADR-0016]
---

# F0006 · Runtime Records SQLite Schema and Reconcile CLI

## Context

ADR-0011 spezifiziert acht Runtime-Record-Typen (`RunAttempt`,
`AuditEvent`, `ApprovalRequest`, `BudgetLedgerEntry`, `ToolCallRecord`,
`PolicyDecision`, `SandboxViolation`, `DispatchDecision`), drei
Effektklassen mit Reconciliation-Pfad und einen `agentctl runs
reconcile`-CLI-Befehl. F0003 (Cost-Aware-Routing-Stub), F0004
(Benchmark-Awareness) und F0005 (Pin-Refresh) setzen diese
Infrastruktur **bereits voraus**, ohne dass sie als eigenes Liefer-
Slice existiert. Der dritte Codex-Follow-up-Review (Sofort-Empfehlung
1) hat diese Lücke als blockierend für v1a-Implementierungsstart
markiert. F0006 schließt sie als minimal tragfähiges Runtime-Slice
zwischen F0001 (v0-Schema) und F0003/F0004/F0005.

## Scope

- **SQLite-Tabellen für die acht Runtime-Record-Typen** aus ADR-0011,
  als Migration `0002_runtime_records.sql` auf das F0001-Schema:
  - `run_attempt` mit FK auf `run`.
  - `audit_event`, polymorphe `subject_ref`-Spalte (Typ + ID).
  - `approval_request` mit FK auf Work Item.
  - `budget_ledger_entry` mit Scope-Tagging (request/task/project-day/
    global-day) und Hash-Anker auf `RunAttempt`.
  - `tool_call_record` mit `idempotency_key`-Index (UNIQUE pro
    Run/Tool).
  - `policy_decision` mit `policy`-Tag (`admission` / `dispatch` /
    `budget_gate_override` / `hitl_trigger` / `tool_risk_match`).
  - `sandbox_violation` mit Kategorie und Detail-JSON.
  - `dispatch_decision` (post-gate-final, frozen pro `RunAttempt`,
    ADR-0014).
- **JSONL-Runlog pro RunAttempt** als Append-only-Datei unter
  `~/.agentic-control/logs/runs/<run-attempt-id>.jsonl` (stdout der
  Agent-CLI, strukturiert).
- **JSONL-Budget-Ledger pro Tag** als Tagesdatei
  `~/.agentic-control/logs/budget/<YYYY-MM-DD>.jsonl` (Aggregation
  der `BudgetLedgerEntry`-Rows zur Tagessicht).
- **CLI-Befehl `agentctl runs reconcile <run-id>`** (ADR-0011):
  - Iteriert über alle nicht persistierten lokal-only-Effekte aus dem
    JSONL-Runlog.
  - Stellt pro Effekt drei Optionen (interaktiv): `erfolgt` (Persist
    nachholen) / `unsicher` (Provider-Side-Check, sofern verfügbar) /
    `nicht erfolgt` (regulär weiterlaufen lassen).
  - Schreibt `AuditEvent`-Records mit Reconcile-Resultat.
  - Setzt Run-Lifecycle von `needs_reconciliation` zurück in
    `running` oder `failed`, sobald alle lokal-only-Effekte abgehakt
    sind.
- **CLI-Befehl `agentctl runs inspect <id>`** zeigt: Run-Lifecycle,
  alle `RunAttempt`-Rows, Tool-Calls (mit Idempotency-Key-Status),
  Audit-Events, Policy-Decisions.
- **CLI-Befehl `agentctl audit show [--subject <ref>] [--since
  <date>]`** filtert Audit-Events; zeigt Diff-Hashes für Config-
  Writes (ADR-0016).
- **`needs_reconciliation`-Erkennung** beim Start: nach Litestream-
  Restore wird jeder offene Run als `needs_reconciliation` markiert,
  bis er via `runs reconcile` abgeschlossen ist (Spec §5.7, §10.4).

## Out of Scope

- **Idempotency-Key-Matching-Engine** (Pre-Send-Check vor jedem
  externen Effekt) — eigenes Sub-Feature, sobald F0006 steht.
- **Tool-Risk-Pattern-Matching-Engine** (Glob-Resolution für
  ADR-0015) — eigenes Feature.
- **Provider-Side-Check-Wrapper** (z. B. `gh issue list --search
  <key>`) — als Hilfsbibliothek optional, eigenes Feature.
- **Log-Retention/Archivierung nach S3** — kommt in v1.x.
- **Runtime-Record-Export-Schema für Postgres-Migration** — Follow-up
  in ADR-0011, kein V1-Liefer-Slice.

## Acceptance Criteria

1. Migration `0002_runtime_records.sql` läuft auf einer F0001-DB
   ohne Fehler; `sqlite3 .schema` zeigt acht neue Tabellen mit den
   Pflichtfeldern aus ADR-0011.
2. Foreign-Key-Constraints sind aktiv: `run_attempt` ohne
   existierenden `run_ref` schlägt fehl.
3. `tool_call_record.idempotency_key` ist UNIQUE pro
   (`run_attempt_id`, `tool_call_ordinal`); doppelter Insert schlägt
   fehl.
4. `agentctl runs inspect <id>` liefert für eine Beispiel-Run mit
   2 Tool-Calls + 1 ApprovalRequest + 1 BudgetLedgerEntry alle vier
   Records sortiert nach Timestamp.
5. `agentctl runs reconcile <id>` auf einer Run mit
   `state=needs_reconciliation` und einem nicht persistierten
   lokal-only-Effekt: zeigt die drei Optionen, akzeptiert
   Nutzer-Eingabe, schreibt `AuditEvent`, setzt Lifecycle zurück.
6. `agentctl audit show --subject config/dispatch/routing-pins.yaml`
   listet alle `AuditEvent`-Rows mit `before_hash`/`after_hash` und
   Actor-Spalte (Voraussetzung für ADR-0016-Audit-Trail).
7. Nach Litestream-Restore auf einem frischen Host markiert ein
   Startup-Hook alle Runs in `state=running` als
   `state=needs_reconciliation`; `agentctl runs list --pending-
   reconcile` zeigt diese Liste.
8. JSONL-Runlog pro RunAttempt ist append-only und übersteht einen
   Crash mid-write (kein partieller Eintrag, weil Append-Semantik
   per `O_APPEND`).
9. JSONL-Budget-Ledger aggregiert die Tages-`BudgetLedgerEntry`-
   Rows beim Tageswechsel automatisch (Cron oder Lazy-Aggregation
   beim ersten `agentctl costs today`-Aufruf).
10. **Reconcile-Idempotenz:** Wiederholtes `agentctl runs reconcile
    <id>` auf einer bereits reconcileten Run zeigt eine klare
    „Nichts zu tun"-Meldung und erzeugt keine doppelten
    `AuditEvent`-Rows.

## Test Plan

- **Unit:** Migrations-Roundtrip auf leerer DB; Constraint-Tests
  pro Tabelle (FK, UNIQUE, CHECK); Reconcile-State-Machine gegen
  Mock-Run.
- **Integration:** Volle Run-Lifecycle-Simulation (Pre-Flight →
  Tool-Calls → Approval → Post-Flight) mit allen acht
  Record-Typen; Inspection liefert deckungsgleiche Sicht.
- **Crash:** Run mit zwei lokal-only-Effekten; Prozess wird zwischen
  Send und Persist beendet; Restart erkennt
  `state=needs_reconciliation`; Reconcile-Roundtrip führt zurück
  in `running`.
- **Negative:** Reconcile auf nicht-existierender Run-ID;
  `audit show` mit ungültigem Subject-Filter; doppelter
  Idempotency-Key-Insert.
- **Manuell:** Nutzer führt Run mit echter `gh issue comment`-
  Sequenz, killt den Prozess vor Persist, läuft `runs reconcile`
  und prüft, dass kein Duplikat-Comment auf GitHub entsteht.

## Rollback

`0002_runtime_records.sql` hat ein Down-Migration-Pendant
(`0002_runtime_records_down.sql`), das die acht Tabellen droppt.
JSONL-Logs bleiben als Dateien liegen — der Nutzer kann sie löschen.
F0003/F0004/F0005-Implementierungen würden ohne F0006 nicht
funktionieren; ein Rollback von F0006 setzt den v1a-Pfad zurück auf
F0001+F0002.
