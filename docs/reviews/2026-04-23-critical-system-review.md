---
title: Kritischer System-Review — Personal Agentic Control System
date: 2026-04-23
status: draft
reviewer: Codex
scope: V1-Spezifikation, ADRs, Research-Briefs, Architekturübersicht
---

# Kritischer System-Review — Personal Agentic Control System

## Executive Summary

Die Architektur hat eine tragfähige Grundrichtung: ein persönlicher
Orchestrator, der agentische Ausführung nicht selbst "denkt", sondern
kontrolliert, budgetiert, sandboxed und nachvollziehbar macht. Die Reduktion
auf fünf Module ist für einen Single-User-Kontext plausibel. Besonders stark
sind die Control/Execution-Trennung, die explizite Sandbox, die Budget-Gates
und die Entscheidung gegen einen Enterprise-Orchestrierungsstack.

Der Entwurf ist aber noch nicht implementierungsreif. Die größten Risiken
liegen nicht in der Modulzahl, sondern in unklaren Betriebsmodi,
widersprüchlicher HITL-Semantik, zu schwach spezifizierten Datenverträgen,
fehlenden Idempotenzregeln und einer noch nicht operationalisierten
Security-Policy. Einige ADRs sind als `accepted` markiert, obwohl zentrale
Umsetzungsdetails offen oder in den Research-Briefs widersprüchlich
beschrieben sind.

Kurzurteil:

- **Architekturidee:** stark.
- **Sicherheitsanspruch:** richtig, aber noch nicht ausführbar genug.
- **Durability-Story:** plausibel, aber zu optimistisch formuliert.
- **V1-Scope:** aktuell mehr Zielarchitektur als erste umsetzbare Version.
- **Hauptarbeit vor Implementierung:** harte Verträge für Runtime, Datenmodell,
  HITL, Budget, Sandbox und Recovery definieren.

## Quellenbasis

Der Review basiert auf diesen lokalen Dokumenten:

- `docs/spec/SPECIFICATION.md`
- `ARCHITECTURE.md`
- `docs/decisions/0001-0009`
- `docs/research/01-17`
- `docs/research/99-synthesis.md`
- `docs/research/15-mvp-metrics.md`
- `GLOSSARY.md`
- `CHANGELOG.md`

Es wurde kein externer Web-Check durchgeführt. Zeitabhängige Aussagen wie
Modellnamen, Preise, Tool-Flags und Security-Claims sollten vor einer
Implementierung erneut gegen die aktuellen Primärquellen geprüft werden.

## Bewertungsmaßstab

- **Kritisch:** kann zu Datenverlust, Sicherheitsbruch, Kosten-Runaway,
  falscher Implementierungsrichtung oder blockierender Architekturdrift führen.
- **Hoch:** kann Kernziele der V1 gefährden oder muss vor Implementierung
  entschieden werden.
- **Mittel:** erzeugt spätere Reibung, Fehlinterpretationen oder erhöhte
  Wartungskosten.
- **Niedrig:** Verbesserungsbedarf an Klarheit, Terminologie oder
  Dokumentationsqualität.

## Was am Entwurf stark ist

### 1. Control/Execution-Trennung ist die richtige Grundachse

Der Entwurf hält Agent-Tools als Ausführungskontexte und macht den
Orchestrator zum Besitzer von Zustand, Policy und Budget. Das ist die
wichtigste Architekturentscheidung. Sie verhindert, dass Claude Code oder
Codex CLI implizit zum Workflow-System werden.

Positiv:

- Agent-Runs werden ephemer und stateless modelliert.
- Wiederanlauf und HITL liegen außerhalb des LLM-Kontexts.
- Entscheidungen, Budgets und Artefakte bekommen einen Ort im System.

Risiko bleibt: Die Grenze muss in der Implementierung sehr konkret gezogen
werden. Wenn die CLI-Tools doch Host-Konfiguration, globale Credentials oder
unpersistierte Session-Zustände verwenden, wird diese Trennung unterlaufen.

### 2. Fünf Module sind angemessen

Die Entscheidung gegen 13 Bounded Contexts ist überzeugend. Für einen
Einzelanwender wären 13 Kontexte eine Scheingenauigkeit mit hohem
Implementierungs- und Pflegeaufwand.

Die fünf Module sind sinnvoll:

- `Interaction`
- `Work`
- `Execution`
- `Knowledge`
- `Portfolio`

Die Grenzen sind fachlich nachvollziehbar. Besonders wichtig ist, dass
`Execution` keine fachliche Wahrheit besitzen soll und `Work` die langlebige
Steuerung hält.

### 3. Budget-Gate und Sandbox sind früh genug im Design

Kosten und Sicherheit sind nicht nachträglich angehängt, sondern Teil der
Kernstrategie. Das ist bei agentischen Systemen entscheidend. Ein später
nachgerüstetes Budget- oder Sandbox-Modell wäre deutlich schwieriger sauber zu
integrieren.

### 4. V0/V1/V2/V3-Staging ist pragmatisch

Der Research-Brief `15-mvp-metrics.md` beschreibt eine gute inkrementelle
Umsetzung: erst manuelles Schema, dann ein durable Single-Loop, dann Portfolio,
dann Governance/Lernen. Das ist realistisch und schützt vor einem zu großen
ersten Wurf.

Problem: Die normative Spec liest sich teilweise so, als sei die gesamte
Zielarchitektur schon V1. Dieser Widerspruch ist einer der zentralen Befunde.

## Zentrale Befunde

### Befund 1 — Kritisch: V1-Betriebsmodus widerspricht sich bei SQLite, DBOS und VPS

Die Spec sagt:

- Laptop-only: SQLite-Datei, DBOS embedded.
- Laptop + VPS: SQLite lokal + Litestream, spiegelnde Instanz,
  Messenger-Bridge.
- Upgrade zu Postgres, sobald mehr als ein Prozess nötig ist.

Gleichzeitig sagt ADR-0003, dass Postgres Pflicht wird, sobald ein zweiter
Prozess oder Host gleichberechtigt lesen/schreiben muss. Eine Messenger-Bridge
oder spiegelnde VPS-Instanz ist genau dieser Fall, wenn sie durable reagieren
oder schreiben soll.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:243-253`
- `docs/decisions/0003-sqlite-litestream-persistence.md:62-67`
- `docs/research/03-durable-execution.md:169-173`
- `docs/research/12-persistence.md:222-236`

Warum das kritisch ist:

- Implementierer wissen nicht, ob V1 lokal-only, SQLite-prod oder
  Postgres-prod sein soll.
- DBOS wird in den Research-Briefs für Dev/SQLite und Prod/Postgres
  differenziert beschrieben, die Spec glättet das zu stark.
- Eine falsche Wahl führt später zu Migration, Locking-Problemen oder
  unechten "Mirror"-Instanzen.

Empfehlung:

Eine explizite Betriebsentscheidung ergänzen:

1. **Release v0/v1a:** lokal-only, ein Prozess, SQLite + Litestream.
2. **Release v1b mit Messenger-Bridge:** entweder Bridge pollt read-only und
   schreibt nicht, oder Postgres wird Pflicht.
3. **VPS mit aktiver Schreibrolle:** Postgres als Primärspeicher, SQLite nicht
   mehr als produktiver Workflow-State.

Die Spec sollte "Laptop + VPS" nicht als einfache Variante von SQLite
beschreiben, solange Schreib- und Ownership-Semantik nicht geklärt sind.

### Befund 2 — Kritisch: HITL-Timeout-Semantik ist widersprüchlich und potenziell unsicher

Die Spec und ADR-0007 beschreiben:

- Inbox-Card bei Gate.
- Push nach 4h.
- Mail nach 24h.
- Nach 72h ohne Antwort: Work Item auto-`abandoned`.

Der Research-Brief `09-hitl.md` sagt dagegen:

- Default-Eskalation: kein Timeout, Pause bleibt bis Entscheidung.
- Bei Deadline-Semantik: Auto-Reject bei Ablauf, nie Auto-Approve.
- Reminder nur für Risiko >= medium.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:234-239`
- `docs/decisions/0007-inbox-hitl-cascade.md:37-66`
- `docs/research/09-hitl.md:194-221`

Warum das kritisch ist:

- Ein pauschales 72h-Abandon kann echte Arbeit verlieren oder kritische
  Entscheidungen unsichtbar machen.
- "Abandoned" ist kein neutraler Timeout-Zustand. Es beendet fachliche Arbeit.
- Für irreversible oder außenwirksame Aktionen ist "nicht reagiert" kein
  ausreichender Grund, das Work Item fachlich aufzugeben.
- Die ADR sagt, irreversible High-Risk-Aktionen eskalieren zwingend, formuliert
  die Kriterien aber zugleich "kumulativ". Das kann so gelesen werden, dass
  selbst irreversible Aktionen nur eskalieren, wenn auch Konfidenz niedrig ist
  und Standardreaktionen erschöpft sind.

Empfehlung:

HITL-Zustände trennen:

- `waiting_for_approval`: wartet ohne Auto-Ende.
- `timed_out_rejected`: Deadline abgelaufen, Aktion nicht ausgeführt.
- `stale_waiting`: Nutzer wurde erinnert, aber Work Item bleibt offen.
- `abandoned`: nur explizit durch Nutzer oder für klar niedrig-riskante
  Wegwerfaufgaben nach dokumentierter Policy.

Eskalationskriterien sollten disjunktiver formuliert werden:

- Irreversible oder außenwirksame Aktion: immer Approval.
- Policy-Klasse erfordert Approval: immer Approval.
- Niedrige kalibrierte Konfidenz: Approval oder Clarify.
- Erschöpfte Standardreaktionen: Approval oder Abbruch.

### Befund 3 — Kritisch: Durable Execution wird zu stark als gelöst dargestellt

DBOS kann eine wichtige Fehlerklasse reduzieren: DB-Step und Checkpoint können
in derselben Transaktion landen. Das löst aber nicht automatisch externe
Seiteneffekte.

Agent-Runs erzeugen externe Effekte:

- Dateien im Worktree.
- Git-Commits oder Branches.
- GitHub-Operationen.
- Netzwerkzugriffe.
- Tool-Aufrufe.
- Benachrichtigungen.
- LLM-Kosten.

Research-Brief `03-durable-execution.md` nennt DBOS selbst als exactly-once für
DB-Steps und at-least-once für andere Effekte. Die Spec beschreibt den
DBOS-Workflow aber noch ohne Idempotenzverträge.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:227-232`
- `docs/decisions/0002-dbos-durable-execution.md:38-44`
- `docs/research/03-durable-execution.md:76-88`
- `docs/research/03-durable-execution.md:174-177`

Warum das kritisch ist:

- Wiederholte Steps können doppelte Commits, doppelte Kommentare, doppelte
  Kosten oder widersprüchliche Artefakte erzeugen.
- Ohne `RunAttempt`-Modell ist nicht klar, welche Ausgabe zu welchem Versuch
  gehört.
- Ohne Idempotency-Key ist nicht klar, ob ein externer Effekt schon passiert
  ist.

Empfehlung:

Vor der Implementierung minimale Runtime-Verträge definieren:

- `Run` ist fachliche Ausführungseinheit.
- `RunAttempt` ist ein konkreter Versuch mit Startzeit, Endzeit, Agent,
  Sandbox-Profil, Prompt-Hash, Tool-Allowlist, Exit-Code, Kosten und Logs.
- Jeder externe Effekt bekommt einen Idempotency-Key oder eine
  Nachweisstrategie.
- Post-Flight registriert Artefakte nur, wenn der Attempt eindeutig ist.
- Wiederholung eines Attempts darf keine unkontrollierten externen Effekte
  duplizieren.

### Befund 4 — Kritisch: Sandbox-Grenze ist konzeptionell richtig, aber operativ unklar

Die Spec fordert eine 8-Schichten-MVS:

- Worktree pro Run.
- Container oder Bubblewrap/Seatbelt.
- Non-root.
- Read-only root FS.
- Egress-Proxy.
- Config-Write-Schutz.
- Ressourcenlimits.
- Secret-Injection pro Run.

Gleichzeitig beschreibt sie Claude Code und Codex CLI als lokale Prozesse.
Nicht eindeutig ist:

- Läuft die Agent-CLI selbst im Container?
- Oder läuft nur der ausgeführte Code im Container?
- Wo liegen `~/.claude`, `~/.codex`, Auth-Dateien und Token?
- Wie wird verhindert, dass die CLI Host-Konfiguration liest?
- Wie wird Tooling installiert, wenn root FS read-only ist?
- Wie werden Netzwerkzugriffe technisch erzwungen: Proxy-ENV,
  Firewall-Regeln, Netzwerk-Namespace oder beides?

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:243-247`
- `docs/spec/SPECIFICATION.md:266-275`
- `docs/decisions/0006-eight-layer-sandbox-mvs.md:37-63`
- `docs/research/01-claude-code.md:148-173`
- `docs/research/02-codex-cli.md:100-111`

Warum das kritisch ist:

Eine Sandbox, die nur im Dokument existiert, schützt nicht. Gerade Agent-CLIs
lesen häufig globale Konfigurationen, Auth-States und Projektdateien. Wenn die
CLI außerhalb der Isolation läuft, kann der eigentliche Sicherheitsgewinn
verloren gehen.

Empfehlung:

Ein eigenes Dokument oder einen Spec-Abschnitt "Execution Harness Contract"
ergänzen:

- Prozessbaum: welche Prozesse laufen innerhalb welcher Isolation?
- Mount-Tabelle: welche Pfade sind `rw`, `ro`, `masked`, `tmpfs`?
- Credentials: welche Tokens werden wie und wo injiziert?
- Netzwerk: wie wird Egress technisch erzwungen?
- Config: welche Host-Konfiguration ist verboten, kopiert oder synthetisch?
- Exit-Vertrag: welche Logs, Artefakte und Kosten werden zurückgegeben?

Ohne diesen Vertrag sollte ADR-0006 nicht als "vollständig" gelten.

### Befund 5 — Hoch: Budget-Caps haben missverständliche `AND`-Semantik

Die Budget-Tabelle beschreibt den Task-Cap als:

`$2 AND 25 Turns AND 15 min`

Das kann so gelesen werden, dass ein Run erst abgebrochen wird, wenn alle drei
Grenzen gleichzeitig überschritten sind. Für Runaway-Schutz wäre das falsch.
Harte Caps sollten typischerweise unabhängig greifen: Abbruch bei Kostenlimit
oder Turnlimit oder Wall-Clock-Limit.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:279-286`
- `docs/decisions/0008-four-scope-budget-gate.md:33-40`
- `docs/research/13-cost.md:174-192`

Warum das hoch relevant ist:

- Ein Run kann 15 Minuten überschreiten, ohne $2 zu kosten.
- Ein Run kann $2 überschreiten, bevor 25 Turns erreicht sind.
- Ein Tool-Loop kann unterhalb des Turn-Caps hängen.

Empfehlung:

Formulierung ändern zu:

> Task-Run wird abgebrochen, sobald **eine** harte Grenze überschritten ist:
> `$2` Kosten **oder** `25` Turns **oder** `15 min` Wall-Clock **oder**
> Repeat-Tool-Call-Detector schlägt an.

Zusätzlich sollte der Budget-Ledger als Pflichtobjekt in der Spec stehen:

- Pre-call estimate.
- Reserved budget.
- Actual usage.
- Cache read/write tokens.
- Provider/model.
- RunAttempt-ID.
- Daily/project rollup.

### Befund 6 — Hoch: Codex-Approval-Policy widerspricht dem Research-Harness

Die Spec fordert:

`codex exec --json --output-schema <file> --ephemeral --approval=never --sandbox=workspace-write`

Der Research-Brief `02-codex-cli.md` empfiehlt dagegen einen Wrapper mit
`--ask-for-approval on-request`, nie `--yolo`, nie danger bypass.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:295-300`
- `docs/research/02-codex-cli.md:106-111`

Warum das hoch relevant ist:

Beide Varianten können sinnvoll sein, aber sie bedeuten unterschiedliche
Architekturen:

- `approval=never`: Der Orchestrator muss vorab alle riskanten Aktionen
  erkennen und den Agenten so einschränken, dass keine native Approval-Frage
  nötig wird.
- `on-request`: Native Approval-Anfragen müssen abgefangen, persistiert und in
  die HITL-Inbox übersetzt werden.

Aktuell ist nicht entschieden, welches Modell gilt.

Empfehlung:

Für V1 eine klare Policy wählen:

- Entweder **orchestrator-only approvals**: `approval=never`, aber dann nur
  mit restriktiven Tool-Sets und vorheriger Tool-Risk-Klassifikation.
- Oder **bridged native approvals**: `on-request`, aber dann mit Adapter, der
  native Prompts in `ApprovalRequest`-Objekte übersetzt.

Nicht beides implizit vermischen.

### Befund 7 — Hoch: Nachvollziehbarkeit ist Ziel, aber kein vollständiger Datenvertrag

Die Spec nennt Nachvollziehbarkeit als Qualitätsziel:

> jede Entscheidung, jedes Ergebnis hat eine Spur zu Auslöser, Eingaben und
> Artefakten

Das Kernobjektmodell enthält aber keine expliziten Objekte für:

- Audit Events.
- Run Attempts.
- Approval Requests.
- Budget Ledger.
- Tool Calls.
- Policy Decisions.
- Sandbox Violations.

Research-Brief `12-persistence.md` fordert CRUD + Audit-Log. Research-Brief
`13-cost.md` fordert ein JSONL-Append-Ledger pro Task. Beides ist in der Spec
nicht normativ genug abgebildet.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:28-39`
- `docs/spec/SPECIFICATION.md:189-205`
- `docs/spec/SPECIFICATION.md:291-293`
- `docs/research/12-persistence.md:228-244`
- `docs/research/13-cost.md:186-201`

Warum das hoch relevant ist:

Ohne diese Datenverträge kann die Implementierung zwar Work Items und Runs
speichern, aber nicht zuverlässig erklären:

- warum ein Run gestartet wurde,
- welche Policy ihn erlaubt hat,
- welche Tools erlaubt waren,
- was er gekostet hat,
- welche Approval-Entscheidung galt,
- ob ein Retry dieselbe oder neue Arbeit war,
- ob ein Artefakt vertrauenswürdig konsumiert werden darf.

Empfehlung:

Mindestens diese zusätzlichen technischen Objekte normativ beschreiben:

- `AuditEvent`
- `RunAttempt`
- `ApprovalRequest`
- `BudgetLedgerEntry`
- `ToolCallRecord`
- `PolicyDecision`
- `SandboxViolation`

Diese müssen nicht alle "fachliche Module" werden. Sie können technische
Querschnittsobjekte sein. Aber sie brauchen Schema, Ownership und Retention.

### Befund 8 — Hoch: V1-Zielarchitektur und Release-Staging sind vermischt

Die Spec heißt V1-Spezifikation und beschreibt Portfolio, Dependencies,
Knowledge, Standards und Binding. Appendix A und Research-Brief 15 sagen aber,
dass:

- v0 nur manuelles Schema ist,
- v1 nur Durable Single-Loop ist,
- v2 Portfolio-Koordination bringt,
- v3 Governance & Lernen bringt.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:189-216`
- `docs/spec/SPECIFICATION.md:384-395`
- `docs/research/15-mvp-metrics.md:56-88`
- `docs/research/15-mvp-metrics.md:90-127`

Warum das hoch relevant ist:

Implementierer könnten entweder:

- zu viel bauen, weil die Spec alle Zielobjekte normativ macht,
- oder zu wenig bauen, weil Appendix A sagt, dass wichtige Teile erst später
  kommen.

Empfehlung:

Die Dokumente klar trennen:

- `SPECIFICATION.md`: Zielarchitektur V1 Target.
- `docs/releases/v0.md`: Handbetrieb mit Schema.
- `docs/releases/v1.md`: Durable Single-Loop.
- `docs/releases/v2.md`: Portfolio.
- `docs/releases/v3.md`: Governance.

Alternativ die Spec selbst um eine Spalte `stage` pro Objekt und Modul
erweitern.

### Befund 9 — Mittel: Beide Agent-Adapter in erster Automation erhöhen Risiko

Die Spec lässt Claude Code und Codex CLI als gleichwertige V1-Execution zu.
Die Research-Synthese sagt explizit, dass gleichzeitiger Support zusätzliche
V1-Komplexität ist.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:373-375`
- `docs/research/99-synthesis.md:266-270`
- `docs/research/15-mvp-metrics.md:178-181`

Warum das relevant ist:

Claude Code und Codex CLI unterscheiden sich bei:

- Auth-Modell.
- Approval-Modell.
- Sandbox-Modell.
- JSON/Event-Ausgabe.
- Tool-Policy.
- Session-State.
- Cloud-/Lokal-Optionen.

Zwei Adapter gleichzeitig bedeuten zwei Security-Profile, zwei Failure-Modi
und zwei Testmatrizen.

Empfehlung:

Für den ersten automatisierten Release genau einen Primary Adapter wählen.
Der zweite Adapter sollte erst dann aktiviert werden, wenn das Interface stabil
ist:

- `ExecutionAdapter`
- `RunRequest`
- `RunAttemptResult`
- `ArtifactManifest`
- `CostReceipt`
- `PolicyReceipt`

### Befund 10 — Mittel: Policy ist als Querschnitt richtig, aber nicht ausführbar genug

Es ist plausibel, Policy nicht als eigenes Modul zu modellieren. Trotzdem
braucht das System eine konkrete Policy-Auswertung.

Research-Brief `07-trust-sandboxing.md` nennt explizit:

- Tool-Scope pro Task.
- Human-Approval für irreversible Aktionen.
- Autonomy Tiering.
- Tool-Use Risk Inventory.

Die Spec beschreibt Trust-Zonen und Sandbox, aber kein normatives
Tool-Risk-Inventar und keine Policy-Evaluation.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:181-185`
- `docs/spec/SPECIFICATION.md:257-275`
- `docs/research/07-trust-sandboxing.md:163-171`

Warum das relevant ist:

Ohne Policy-Evaluator ist unklar:

- welche Tools in welchem Run erlaubt sind,
- wann ein Approval erforderlich ist,
- welche Domains im Egress erlaubt sind,
- ob eine Operation reversibel ist,
- welcher Blast-Radius angenommen wird,
- wie Standards in konkrete Runtime-Regeln übersetzt werden.

Empfehlung:

Ein minimales Policy-Modell definieren:

- `ToolRisk`: Tool, Wirkung, Reversibilität, Scope, Default-Approval.
- `AutonomyTier`: z. B. observe, suggest, edit-local, external-effect.
- `PolicyDecision`: allow, deny, require_approval, require_replan.
- `BindingResolution`: welche Standards gelten in welcher Reihenfolge?
- Fail-closed-Default: unbekanntes Tool oder unbekannter Scope wird nicht
  automatisch erlaubt.

### Befund 11 — Mittel: Secrets und Identity sind zu stark verharmlost

Die Spec beschreibt Single-User-Identität und Secrets als internen
"~50-Zeilen-Teil" im Interaction-Modul. Für ein privates System kann die
Domäne klein sein, aber die Sicherheitswirkung ist groß.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:144-148`
- `docs/spec/SPECIFICATION.md:272-275`
- `docs/research/02-codex-cli.md:104-111`

Warum das relevant ist:

Secrets sind ein zentraler Exfiltrationspunkt. Selbst bei Single-User gilt:

- Agenten dürfen nicht die interaktiven Login-Credentials erben.
- Pro Run sollten dedizierte, minimale Credentials verwendet werden.
- Cloud-Agenten und lokale Agenten brauchen unterschiedliche Secret-Policies.
- Logs und Artefakte müssen Secret-Masking erzwingen.

Empfehlung:

Secrets nicht als eigene Domäne aufblasen, aber einen klaren Secret-Vertrag
ergänzen:

- Secret-Quelle.
- erlaubte Scopes.
- Injection-Mechanismus.
- Masking-Regeln.
- Rotation.
- Verbot globaler Env-Vererbung.
- Trennung interaktiver Nutzer-Logins von Agent-Service-Credentials.

### Befund 12 — Mittel: Observability ist proportional, aber zu knapp

Kein OTEL-Stack für V1 ist vernünftig. Das heißt aber nicht, dass
Observability selbst optional ist. Die Spec sagt nur, Primärmetriken seien aus
SQLite + Audit-Log ableitbar.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:291-293`
- `docs/spec/SPECIFICATION.md:321-341`
- `docs/research/13-cost.md:197-201`
- `docs/research/15-mvp-metrics.md:160-165`

Warum das relevant ist:

Bei Agent-Runs braucht man für Debugging und Kontrolle mindestens:

- strukturierte Run-Events,
- Kosten-Receipts,
- Sandbox-Denials,
- Tool-Calls,
- Prompt-/Context-Hashes,
- Retry-Gründe,
- HITL-Latenzen.

Empfehlung:

OTEL weiter weglassen, aber ein lokales Observability-Minimum normativ machen:

- SQLite-Audit-Tabellen für Domain-Zustandsänderungen.
- JSONL-Runlog pro Attempt.
- JSONL-Budgetledger pro Tag.
- `agentctl status`, `agentctl costs today`, `agentctl runs inspect`.
- Retention-Policy.

### Befund 13 — Mittel: Backup/Restore ist beschrieben, aber nicht als Akzeptanzkriterium

Litestream, Git-Remote und JSON-Export werden in Research-Brief 12 erwähnt.
Die Spec nennt Litestream, aber ein Restore-Drill ist nicht als
Qualitätsanforderung verankert.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:249-255`
- `docs/research/12-persistence.md:238-244`
- `docs/research/12-persistence.md:246-258`

Warum das relevant ist:

Ein Backup ohne getesteten Restore ist nur eine Hoffnung. Gerade bei
SQLite+Litestream muss klar sein:

- welches Recovery Point Objective gilt,
- welches Recovery Time Objective gilt,
- wie Workflows nach Restore weiterlaufen,
- was mit halb fertigen RunAttempts passiert,
- wie Markdown/Git und SQLite wieder konsistent werden.

Empfehlung:

Akzeptanzkriterium ergänzen:

- Quartalsweiser Restore-Drill.
- Dokumentierter Restore-Befehl.
- Test: Restore auf frischem Host, `work next` zeigt konsistente Lage.
- Nach Restore werden laufende Runs als `needs_reconciliation` markiert.

### Befund 14 — Mittel: Standards-Promotion ist gut, aber Materialisierung bleibt offen

Der 4-Stufen-Lifecycle für Standards ist sinnvoll. Kritisch ist die
Materialisierung von `bound` Standards in echte Agent-Kontexte.

Relevante Stellen:

- `docs/spec/SPECIFICATION.md:171-177`
- `docs/decisions/0005-four-stage-standards-lifecycle.md`
- `docs/research/15-mvp-metrics.md:111-127`

Warum das relevant ist:

Ein Standard im Zustand `bound` muss tatsächlich Agent-Verhalten verändern.
Sonst ist die Governance nur Dokumentation. Der Entwurf sagt:

- Skills,
- `CLAUDE.md`-Einträge,
- Standards-Dateien.

Nicht geklärt ist:

- welche Materialisierungsform für welches Tool gilt,
- wie Konflikte zwischen Standards aufgelöst werden,
- wie Agenten nachweislich mit dem gebundenen Standard gestartet wurden,
- wie Retire/Supersede technisch zurückgenommen wird.

Empfehlung:

Für `bound` Standards einen Binding-Compiler spezifizieren:

- Input: Standard + Scope.
- Output: konkrete Datei, Skill, Prompt-Snippet oder Tool-Policy.
- Hash: wird im RunAttempt gespeichert.
- Konfliktregel: spezifischer Scope gewinnt vor allgemeinem Scope.
- Retire: erzeugt Entfernung oder Deaktivierung in der Materialisierung.

### Befund 15 — Mittel: Test- und Verifikationsstrategie fehlt

Die Spec beschreibt Zielzustände, aber keine systematische Verifikation.
Gerade bei einem Agent-Controller reichen klassische Unit-Tests nicht.

Warum das relevant ist:

Die riskantesten Fehler sind systemisch:

- Budget-Gate greift nicht.
- Sandbox erlaubt Egress.
- Agent schreibt außerhalb des Worktrees.
- Retry dupliziert externe Effekte.
- HITL-Abbruch verliert Arbeit.
- Restore erzeugt inkonsistente Zustände.

Empfehlung:

Vor Implementierung eine V1-Testmatrix ergänzen:

- Unit-Tests für Policy- und Budget-Entscheidungen.
- Integrationstest: Run im Worktree darf nicht außerhalb schreiben.
- Integrationstest: denied Egress wird protokolliert und blockiert.
- Crash-Test: Prozess stirbt nach Agent-Call vor Post-Flight.
- Retry-Test: externer Effekt wird nicht doppelt registriert.
- HITL-Test: Approval bleibt über Restart erhalten.
- Restore-Test: Litestream/Git-Recovery auf frischem Host.

### Befund 16 — Niedrig bis Mittel: ADR-Status wirkt zu final

Alle ADRs sind am selben Datum `accepted`. Inhaltlich gibt es aber Bereiche,
die noch offene Implementierungsentscheidungen enthalten:

- SQLite vs Postgres im Betrieb.
- HITL-Timeouts.
- Codex approval mode.
- Sandbox-Harness.
- konkrete Budget-Ledger-Semantik.

Warum das relevant ist:

`accepted` signalisiert Implementierbarkeit. Bei einigen ADRs ist eher die
Richtung akzeptiert, nicht der ausführbare Vertrag.

Empfehlung:

ADR-Status oder ADR-Inhalt präzisieren:

- Richtung akzeptiert.
- Offene Umsetzungsfragen als "Decision follow-ups".
- Neue ADRs für Runtime-Verträge, wenn Verhalten geändert wird.

## Perspektivenreview

### Architekturperspektive

Stärken:

- Passende Modulzahl.
- Gute Control/Execution-Trennung.
- Keine unnötigen Services.
- Kein zweiter Orchestrator durch LangGraph/Agents SDK.

Risiken:

- Target Architecture und Release-Stages vermischt.
- Policy ist fachlich richtig eingeordnet, aber technisch noch nicht
  greifbar.
- Technische Querschnittsobjekte fehlen im Kernmodell.

Bewertung: **gut, aber noch zu viel Zielbild und zu wenig Runtime-Vertrag.**

### Sicherheitsperspektive

Stärken:

- Native Agent-Sandbox wird nicht als ausreichende Grenze betrachtet.
- Egress-Kontrolle und Config-Write-Schutz sind früh im Design.
- Kein Hook-Automatismus in `.claude/settings.json`.

Risiken:

- Agent-CLI-Prozessgrenze unklar.
- Secret-Injection nicht konkret genug.
- Tool-Risk-Inventar fehlt.
- Approval-Policy zwischen Orchestrator und nativen Agent-Approvals unklar.

Bewertung: **richtige Prinzipien, aber nicht operational genug.**

### Betriebsperspektive

Stärken:

- Geringer Infrastrukturanspruch.
- SQLite/Litestream/Git ist für lokale V0/V1 attraktiv.
- Postgres-Upgrade-Pfad ist grundsätzlich vorgesehen.

Risiken:

- SQLite/VPS/Messenger-Bridge widersprüchlich.
- Restore nicht als Akzeptanzkriterium.
- Keine klare Reconciliation nach Crash oder Restore.
- DBOS+SQLite-Produktionsreife ist selbst in den Research-Briefs offen.

Bewertung: **lokal plausibel, verteilter Betrieb noch nicht sauber.**

### Produkt- und UX-Perspektive

Stärken:

- Inbox statt synchronem Push schützt Aufmerksamkeit.
- WIP-Limits passen zum Ziel "Entlastung, nicht Zweitjob".
- Anti-Metriken sind gut gewählt.

Risiken:

- 72h-Abandon kann Nutzervertrauen beschädigen.
- Eskalationssemantik ist nicht eindeutig.
- Unklar, wie Inbox-Cards priorisiert und erklärt werden.
- WIP- und HITL-Metriken müssen kalibriert werden, nicht absolut gelten.

Bewertung: **gute Richtung, aber Timeout- und Card-Semantik müssen neu
geschärft werden.**

### Daten- und Durability-Perspektive

Stärken:

- Durable Execution wird als Kernanforderung erkannt.
- Markdown+Git für Knowledge ist portabel.
- CRUD+Audit ist in Research angelegt.

Risiken:

- Audit ist nicht normativ genug.
- Externe Effekte nicht idempotent spezifiziert.
- Kein `RunAttempt`.
- Kein klares Modell für partially completed runs.

Bewertung: **Datenmodell ist fachlich schlank, technisch aber noch
unvollständig.**

### Kostenperspektive

Stärken:

- Budget wird pre-call gedacht.
- Mehrere Scopes sind sinnvoll.
- Tages-Hard-Cap ist richtig.

Risiken:

- `AND`-Semantik missverständlich.
- Monats-Cap aus Research fehlt in der Spec.
- Tight-loop detection ist nur in Research erwähnt.
- Shared quota bei parallelen Agenten offen.

Bewertung: **gut angelegt, aber Enforcement-Details müssen normativ werden.**

### Implementierungsperspektive

Stärken:

- V0 "Handbetrieb mit Schema" ist ein guter Einstieg.
- Separater Execution Adapter ist naheliegend.
- Modular Monolith minimiert Setup-Kosten.

Risiken:

- Zwei Agent-Adapter gleichzeitig erhöhen Komplexität.
- Kein Harness-Vertrag.
- Keine Testmatrix.
- Zu viele accepted ADRs können falsche Sicherheit erzeugen.

Bewertung: **erst V0/V1a bauen, nicht die gesamte Zielarchitektur.**

## Priorisierte Empfehlungen

### Sofort vor Implementierung klären

1. Betriebsmodus: lokal-only SQLite oder Postgres für alles mit zweitem
   Prozess.
2. HITL-Semantik: kein pauschales 72h-Abandon für Approvals.
3. Budget-Semantik: harte Caps als unabhängige Abbruchbedingungen.
4. Execution Harness Contract: Prozessgrenze, Mounts, Netzwerk, Secrets,
   Config, Logs.
5. Primärer Agent-Adapter für ersten automatisierten Release.

### Danach in Spec/ADRs ergänzen

1. Technische Kernobjekte: `RunAttempt`, `ApprovalRequest`, `AuditEvent`,
   `BudgetLedgerEntry`, `ToolCallRecord`, `PolicyDecision`.
2. Idempotenzmodell für externe Effekte.
3. Tool-Risk-Inventar und Autonomy Tiers.
4. Restore- und Reconciliation-Vertrag.
5. Testmatrix für Budget, Sandbox, HITL, Retry, Restore.

### Für spätere Stufen bewusst verschieben

1. Standards-Promotion und Binding-Compiler erst nach realem Material.
2. Multi-Projekt-Dependencies erst nach stabilem Single-Loop.
3. Zweiter Agent-Adapter erst nach stabilem Adapter-Interface.
4. Messenger/Mail erst nach geklärter Postgres/SQLite-Entscheidung.

## Empfohlene nächste Dokumentationsänderungen

### Neue ADRs

1. `0010-execution-harness-contract.md`
   - Agent-Prozessgrenze, Container/Bubblewrap, Mounts, Netzwerk, Secrets.

2. `0011-runtime-audit-and-run-attempts.md`
   - `RunAttempt`, Audit, Budget-Ledger, Tool-Calls, Artefakt-Manifest.

3. `0012-hitl-timeout-semantics.md`
   - Approval-Zustände, Timeout, Auto-Reject, Abandon-Regeln.

4. `0013-v1-deployment-mode.md`
   - SQLite lokal-only vs Postgres bei Bridge/VPS.

### Spec-Patches

- In `§5.7 Kernobjekte` technische Querschnittsobjekte ergänzen oder als
  separaten Abschnitt "Runtime Records" aufnehmen.
- In `§6.2 HITL-Eskalation` Timeout-Regeln korrigieren.
- In `§8.2 Sandbox` den Harness-Vertrag referenzieren.
- In `§8.3 Budget-Gate` `AND` durch klare unabhängige harte Caps ersetzen.
- In Appendix A klar zwischen Zielarchitektur und Release-Stages trennen.

## Schlussurteil

Das System ist als Architekturkonzept deutlich überdurchschnittlich: Es
vermeidet die üblichen Fehler agentischer Systeme, nämlich unklare
Zustandsverantwortung, unkontrollierte Agent-Loops, fehlende Budgets und
blindes Vertrauen in Tool-Sandboxes.

Die nächste Qualitätsstufe entsteht nicht durch mehr Module oder mehr
Frameworks, sondern durch härtere Verträge:

- Was darf ein Run?
- Was kostet ein Run?
- Was wurde wirklich ausgeführt?
- Was passiert bei Crash, Retry, Timeout und Restore?
- Warum war eine Aktion erlaubt?
- Welche Entscheidung hat ein Artefakt vertrauenswürdig gemacht?

Wenn diese Fragen vor der Implementierung präzisiert werden, ist der Entwurf
eine solide Basis für ein persönliches agentisches Steuerungssystem. Wenn sie
offen bleiben, besteht das Risiko, dass die Implementierung entweder zu viel
auf einmal baut oder an genau den Stellen unsicher wird, die die Architektur
eigentlich kontrollieren soll.

