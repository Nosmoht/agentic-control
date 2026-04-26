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
| `PolicyDecision` | SQLite-Tabelle | Entscheidung einer Policy (Admission, Dispatch, Budget-Gate-Override, HITL-Trigger, **Tool-Risk-Match**); Subject-Ref, Policy-Tag, Inputs, Output, Timestamp. Für `tool_risk_match` (ADR-0015) trägt `output` zusätzlich `{matched_pattern, risk, approval, default_hit}` und `subject_ref` zeigt auf `tool_call_record:<id>` — F0007 liest diese Records als historische Match-Quelle (Counter-Counter-Counter-Counter-Review-2026-04-26 Befund 2). |
| `SandboxViolation` | SQLite-Tabelle + Alert | Verweigerter Egress, Config-Write, cgroup-Limit; RunAttempt-Ref, Timestamp, Kategorie, Details |
| `DispatchDecision` | SQLite-Tabelle | Adapter + Modell + Begründung (Pin vs. Default vs. Cost-Aware) pro RunAttempt; frozen; Evidence-Refs; Definition siehe ADR-0014 §Cost-Aware-Routing-Policy |

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

### Drei Effektklassen mit unterschiedlicher Idempotenz-Qualität

Externe Effekte sind nicht alle gleich behandelbar. V0.2.3-draft (nach
Counter-Review-2026-04-24, neuer Befund 3) unterscheidet drei Klassen,
weil sie verschiedene Crash-Fenster und Recovery-Pfade haben:

| Klasse | Beispiel | Idempotenz-Mechanismus | Restrisiko |
|---|---|---|---|
| **Natürlich-idempotent** | Git-Commit, File-Write innerhalb Worktree | Inhalts-Hash; Wiederholung ergibt denselben Hash → System erkennt Duplikat trivial. | Keine Duplikate möglich. |
| **Provider-keyed** | GitHub-PR-Create mit `Idempotency-Key`-Header (wo Provider unterstützt) | Key wird providerseitig deduplikiert; Crash zwischen Send und lokalem Persist führt nicht zu Duplikat, sondern zu sicherem Retry mit demselben Key. | Restrisiko nur, wenn Provider den Key nicht respektiert. |
| **Lokal-only** | Slack/Mail-Post, GitHub-Issue-Comment (kein providerseitiger Key) | Lokaler Idempotenz-Key in `ToolCallRecord.idempotency_key`; **Crash zwischen externem Effekt und Persist erzeugt echten Duplikat-Pfad.** | Reconciliation nötig (siehe unten). |

#### Key-Schema pro Klasse

| Effekt | Klasse | Key |
|---|---|---|
| Git-Commit | natürlich | Commit-Hash |
| File-Write innerhalb Worktree | natürlich | Datei-Pfad + Content-SHA256 |
| GitHub-PR-Create (mit GH-Idempotency-Key) | provider-keyed | `gh-{run_attempt_id}-{tool_call_ordinal}` als Header |
| GitHub-Issue-Comment | lokal-only | `sha256(run_attempt_id + tool_call_ordinal + body)` |
| Slack-Post | lokal-only | `sha256(run_attempt_id + tool_call_ordinal + channel + body)` |
| Mail-Send | lokal-only | `sha256(run_attempt_id + tool_call_ordinal + recipient + subject)` |

#### Pre-Send-Check für alle Klassen

Vor Ausführung eines externen Effekts prüft der Orchestrator, ob ein
`ToolCallRecord` mit demselben `idempotency_key` bereits existiert. Wenn
ja, wird der Effekt übersprungen und der vorhandene Output
zurückgegeben. Dieser Check schützt **gegen Retries innerhalb desselben
Run-Lifecycles** — er löst die Crash-Lücke der lokal-only-Klasse
**nicht** auf.

### Reconciliation-Mechanismus für lokal-only-Klasse

Für die lokal-only-Klasse besteht ein verbleibendes Crash-Fenster
zwischen externem Effekt und lokalem `ToolCallRecord`-Persist. Wenn der
Prozess in genau diesem Fenster stirbt, läuft der nächste Restart in
eine echte At-Least-Once-Situation: der Effekt **könnte** schon gesendet
sein oder noch nicht.

Mechanismus:

1. **Run-Lifecycle-Zwischenzustand `needs_reconciliation`** (Spec §5.7)
   markiert nach Litestream-Restore alle laufenden Runs als
   reconciliation-pflichtig.
2. **CLI-Befehl `agentctl runs reconcile <run-id>`** geht durch alle
   nicht persistierten lokal-only-Effekte und stellt dem Nutzer pro
   Effekt drei Optionen:
   - **erfolgt** → Persist nachholen, Duplikat verhindern.
   - **unsicher** → Provider-Side-Check (z. B. `gh issue list --search
     "<idempotency_key in body>"`), wenn der Provider eine solche
     Suche unterstützt; sonst manuell prüfen.
   - **nicht erfolgt** → Run regulär weiterlaufen lassen.
3. **Abschluss**: Run wechselt von `needs_reconciliation` zurück in den
   Lifecycle-Pfad (`running` oder `failed` je nach Reconcile-Resultat),
   sobald alle lokal-only-Effekte abgehakt sind. Der Reconcile-Vorgang
   selbst erzeugt eigene `AuditEvent`-Records.

Diese Klasse ist klein in der Praxis (n=1, wenige `gh comment`-Calls
pro Tag), aber asymmetrisch teuer wenn übersehen — daher der explizite
Mechanismus.

### Post-Flight-Vertrag

Der Harness (ADR-0010) liefert die strukturierten Exit-Artefakte; der
Orchestrator schreibt sie in die Runtime-Record-Tabellen. Schritt-
Checkpoints in DBOS und diese Writes liegen **in derselben Transaktion**
(DBOS-Eigenschaft, ADR-0002) — auf der **DB-Seite** sind Dual-Write-
Fehler konstruktiv ausgeschlossen.

**Wichtig (V0.2.3-draft):** Diese Garantie gilt nur für die
DB-Schreibseite. Sie schließt **nicht** die Lücke zwischen einem
bereits abgesetzten externen Effekt der lokal-only-Klasse und seinem
lokalen `ToolCallRecord`-Persist. Diese orthogonale Klasse adressiert
der oben beschriebene Reconciliation-Mechanismus.

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
- Export-Schema für den Fall, dass der Nutzer Runtime-Records
  exportieren will (Portabilitäts-Anforderung aus Spec §2).
- `agentctl runs reconcile`-CLI als eigenes F-Feature in v1a, sobald
  der Mechanismus implementiert wird.
- Provider-Side-Check-Wrapper (z. B. GitHub-Search-API, Slack-API)
  als Hilfsbibliothek für den Reconcile-Pfad — separates Feature,
  optional.

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
