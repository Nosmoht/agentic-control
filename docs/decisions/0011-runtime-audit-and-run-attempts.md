# ADR-0011: Runtime Audit and Run Attempts

* Status: accepted
* Date: 2026-04-24
* Context: `docs/spec/SPECIFICATION.md §5.7 (Runtime Records), §8.4 (Observability)`

## Kontext und Problemstellung

Die V1-Spec verspricht Nachvollziehbarkeit („jede Entscheidung, jedes
Ergebnis hat eine Spur zu Auslöser, Eingaben und Artefakten"). Die 9
Kernobjekte der Spec tragen diese Spur nicht — sie sind Domain-Objekte,
keine Audit-Primitive. DBOS (ADR-0002) liefert Exactly-Once für DB-Steps,
aber At-Least-Once für **externe Effekte** (Git-Commits, GitHub-Calls,
Notifications, LLM-Kosten). Ohne Idempotenz-Modell und Run-Attempt-
Tracking können Retries doppelte Commits, doppelte Kosten, widersprüchliche
Artefakte erzeugen.

Der Counter-Review hat diese Lücke als Kritisch-Befund 3 und Hoch-Befund 7
markiert.

## Entscheidungstreiber

- Nachvollziehbarkeit ist Qualitätsziel der Spec (§1.2).
- Retries müssen sicher sein — kein doppelter externer Effekt.
- Audit-Daten müssen abfragbar sein (SQLite-Tabellen, JSONL-Logs).
- Domain-Objekte bleiben schlank — Technik-Querschnitt separat.

## Erwogene Optionen

1. Audit als Funktion in jedes Kernobjekt einflechten — bloated, verstößt
   gegen Objekt-Grenzen.
2. **Runtime Records als technischer Querschnitts-Layer**, separat von
   Domain-Objekten, persistiert in eigenen Tabellen und JSONL-Logs.
3. Externes Observability-System (OTEL-Collector etc.) — unproportional für
   n=1.

## Entscheidung

Gewählt: **Option 2** — Runtime Records als Technik-Querschnitt.

### Neue Runtime-Record-Typen

| Record | Persistenz | Zweck |
|---|---|---|
| `RunAttempt` | SQLite-Tabelle | Konkreter Versuch einer Run; Startzeit, Endzeit, Agent, Modell, Sandbox-Profil, Prompt-Hash, Tool-Allowlist, Exit-Code, Kosten, Logs-Ref |
| `AuditEvent` | SQLite-Tabelle | Zustandsänderung an einem Domain-Objekt (Work Item → state=X); Timestamp, Actor, Before, After, Reason |
| `ApprovalRequest` | SQLite-Tabelle | HITL-Gate-Instanz; Subject-Ref, Risiko-Klasse, gestellte Frage, Entscheidung, Entscheider, Timestamp |
| `BudgetLedgerEntry` | SQLite-Tabelle + tägliches JSONL | Kosten pro Request/Task/Projekt-Tag/Global-Tag; Pre-Call-Projektion, Actual, Cache-Hit, Modell, RunAttempt-Ref |
| `ToolCallRecord` | SQLite-Tabelle | Einzelner Tool-Call innerhalb einer RunAttempt; Tool, Input-Hash, Output-Ref, Duration, Exit, Idempotency-Key falls extern wirksam |
| `PolicyDecision` | SQLite-Tabelle | Entscheidung einer Policy (Admission, Dispatch, Budget-Gate, HITL-Trigger); Subject-Ref, Policy-Name, Inputs, Output, Timestamp |
| `SandboxViolation` | SQLite-Tabelle + Alert | Verweigerter Egress, Config-Write, cgroup-Limit; RunAttempt-Ref, Timestamp, Kategorie, Details |

### Beziehungen

```
Run (Domain, aus §5.7)
  └── RunAttempt (1..n, technisch)
        ├── ToolCallRecord (1..n)
        ├── BudgetLedgerEntry (1..n)
        ├── SandboxViolation (0..n)
        └── AuditEvent (auf Run-State-Changes)

Work Item (Domain)
  └── AuditEvent (auf Lifecycle-Changes)
  └── ApprovalRequest (0..n, wenn HITL gezogen)
  └── PolicyDecision (zu Admission, Dispatch)

DispatchDecision (Runtime Record, aus ADR-0014)
  └── Frozen pro RunAttempt; enthält Adapter, Modell, Pin-Referenz oder Router-Output.
```

### Idempotenz-Keys für externe Effekte

Jeder externe Effekt bekommt einen stabilen Idempotency-Key, abgelegt im
`ToolCallRecord.idempotency_key`:

| Effekt | Key-Schema |
|---|---|
| Git-Commit | Commit-Hash (natürliche Idempotenz) |
| GitHub-Issue-Comment | `sha256(run_attempt_id + tool_call_ordinal + body)` |
| GitHub-PR-Create | `sha256(run_attempt_id + branch_name + title)` |
| Notification (Slack/Mail) | `sha256(run_attempt_id + tool_call_ordinal + channel)` |
| File-Write | Datei-Pfad + Content-SHA256 (natürliche Idempotenz) |

Regel: Vor Ausführung eines externen Effekts prüft der Orchestrator, ob ein
`ToolCallRecord` mit demselben `idempotency_key` bereits existiert. Wenn
ja, wird der Effekt übersprungen und der vorhandene Output zurückgegeben.

### Post-Flight-Vertrag

Der Harness (ADR-0010) liefert die strukturierten Exit-Artefakte; der
Orchestrator schreibt sie in die Runtime-Record-Tabellen. Schritt-Checkpoints
in DBOS und diese Writes liegen **in derselben Transaktion** (DBOS-
Eigenschaft, ADR-0002) — Dual-Write-Fehler konstruktiv ausgeschlossen.

### Konsequenzen

**Positiv**
- Retry-Sicherheit für externe Effekte (Idempotency-Keys).
- Nachvollziehbarkeit komplett: von User-Input über Policy-Entscheidungen
  bis Artefakt-Registrierung.
- Budget-Ledger separates Objekt — Cost-Queries ohne Join-Orgie.
- Domain-Objekte bleiben schlank; Technik-Querschnitt klar abgegrenzt.

**Negativ**
- Zusätzliches Schema (7 neue Tabellen).
- JSONL-Logs wachsen — Retention-Policy nötig (siehe §8.4).
- Mehr Code-Paths in DBOS-Workflows (Checkpoint + Audit in einer Txn).

### Follow-ups

- Retention-Policy für JSONL-Logs (vorschlagen: 90 Tage lokal, danach
  archivieren nach S3).
- Export-Schema für den Fall, dass der Nutzer Runtime-Records ausführen
  exportieren will (Portabilitäts-Anforderung aus Spec §2).

## Referenzen

- Spec §1.2 (Qualitätsziel Nachvollziehbarkeit), §5.7, §8.4
- ADR-0002 — DBOS
- ADR-0008 — Budget-Gate (konsumiert `BudgetLedgerEntry`)
- ADR-0010 — Execution Harness Contract (liefert Exit-Artefakte)
- ADR-0012 — HITL (konsumiert `ApprovalRequest`)
- ADR-0014 — Peer-Adapters (liefert `DispatchDecision`)
- `docs/research/03-durable-execution.md` — DBOS-Konsistenz-Modell
- `docs/research/12-persistence.md` — CRUD + Audit-Log-Pattern
- `docs/research/13-cost.md` — JSONL-Ledger-Pattern
- Counter-Review (2026-04-23) Befund 3, 7
