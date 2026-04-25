# Glossary

Zentrales Glossar für das Personal Agentic Control System.
Begriffe sind alphabetisch geordnet. Abgleich gegen
[`docs/spec/SPECIFICATION.md`](docs/spec/SPECIFICATION.md).

## Admission Control
4-Klassen-Klassifikation jedes neuen Inputs (`reject` / `defer` /
`delegate-to-agent` / `accept`) im Work-Modul, inklusive Kosten-/Scope-
Schätzung vor Annahme. Siehe `docs/research/10-work-admission.md`.

## ADR (Architecture Decision Record)
Einzelne Architekturentscheidung im MADR-Format in `docs/decisions/`.

## Artifact
Erzeugtes, registriertes Ergebnisobjekt eines Runs (Datei, Commit-Hash,
Spec-Eintrag, externe Ressource). Hat Provenance.

## Attention Residue
Kognitive Restbelastung aus unvollständig abgeschlossenen Aufgaben
(Leroy 2009). Primärindikator für die Gesundheit des Systems.

## Binding (Standard)
Zustand eines Standards, der ihn für einen definierten Scope verbindlich
macht. Wird materialisiert (z. B. als Claude-Skill, `CLAUDE.md`-Eintrag).
Siehe ADR-0005.

## Budget Gate
Middleware-Schicht vor jedem LLM-Call mit 4 Scopes (Request, Task,
Projekt/Tag, Global/Tag). Siehe ADR-0008.

## Control Surface
Interaktionskanal — CLI-first, optional Messenger/Mail. Nie direkt
ausführend.

## Cost-Aware Routing
Dispatch-Policy, bei der der Dispatcher pro Work Item Adapter und Modell
anhand einer Konfidenzschätzung × Kosten-Tier wählt, nicht anhand Task-Class-
Zuordnung. Basis: RouteLLM-Stil (85 % Kostenersparnis bei 95 %
Qualitätserhalt). Siehe ADR-0014, SPECIFICATION.md §8.6.

## DBOS
In-Process-Library für Durable Execution; Schritte checkpoints in der
gleichen Transaktion wie Domänen-Writes. Siehe ADR-0002.

## Decision
Dokumentierte Wahl im ADR-Minimalformat (Kontext, Entscheidung, Konsequenz).
Kennzahl im Knowledge-Modul.

## Dispatcher
Sub-Komponente des Work-Moduls, die pro Work Item Adapter und Modell wählt
und das Ergebnis als `DispatchDecision` persistiert. Policy, nicht
Execution. Abgrenzung: „Agent-Auswahl" (§8.6) ist das Konzept, „Dispatcher"
ist die konkrete Komponente. Siehe ADR-0014.

## DispatchDecision
Runtime Record (ADR-0011), frozen pro `RunAttempt`. Enthält Adapter,
Modell, Begründung (Pin vs. Default vs. Cost-Aware) und Evidence-Refs.

## ExecutionAdapter
Interface mit fünf Verben (`supports`, `prepare`, `execute`, `cancel`,
`describe`), über das der Orchestrator beide Agent-Tools (Claude Code,
Codex CLI) uniform ansteuert. Implementierungen sind gleichwertige Peers.
Siehe ADR-0014, SPECIFICATION.md §5.4.

## Dependency
Strukturelle Abhängigkeit zwischen Projekten, Work Items oder Artifacts.
First-Class-Objekt mit `satisfaction_basis`.

## Durable Execution
Orchestrierungs-Muster, bei dem der Workflow-Zustand so persistiert wird,
dass er einen Prozess-Absturz übersteht und deterministisch fortgesetzt
werden kann.

## Evidence
Beleg- und Herkunftsinformation für Observations, Decisions, Standards oder
Artifacts. Kein `trust_class`-Attribut (Kategorienfehler in Legacy).
Subtyp `Evidence(kind=benchmark)` (siehe **Benchmark Evidence**).

## Benchmark Evidence
`Evidence(kind=benchmark)` — extern gepullte Benchmark-Daten (HuggingFace
Open LLM Leaderboard, SWE-bench, LiveBench, Aider, Arena), normalisiert
und mit Referenz auf den Roh-`Artifact(kind=benchmark_raw)`. Dient der
Awareness („welches Modell führt wo") — **beeinflusst keine
Dispatch-Entscheidung automatisch**. Siehe SPECIFICATION.md §5.5, §8.6,
Feature F0004.

## Benchmark Puller
Code-Komponente (in v1 manuell via `agentctl benchmarks pull`, ab v1.x
optional als DBOS-Scheduled-Workflow), die konfigurierte Benchmark-Quellen
abfragt und `Benchmark Evidence` erzeugt.

## Execution
Modul, das bounded Agent-Runs ausführt. Sandboxed, stateless, ephemer.

## HarnessProfile
Neutraler Profil-Typ, den der Dispatcher für einen geplanten Run erzeugt und
an den `ExecutionAdapter` übergibt. Enthält Modell-Ref, Tool-Allowlist,
Sandbox-Vertrag, Context-Budget, Approval-Mode, Output-Schema, Secrets-
Scope. Siehe ADR-0014.

## HITL (Human in the Loop)
Punkte, an denen das System menschliche Freigabe einholt. Per Inbox-Kaskade
(4h/24h/72h), nicht synchroner Push. Siehe ADR-0007 und ADR-0012 (Timeout-
Semantik: vier Zustände, disjunktive Kriterien, kein Default-Auto-Abandon).

## HITL-Sub-States
Vier explizite Sub-Zustände eines wartenden Work Items (ADR-0012):
`waiting_for_approval` (Gate gezogen, Approval steht aus), `stale_waiting`
(Reminder gesendet nach 24 h, Work Item bleibt offen), `timed_out_rejected`
(harte Deadline abgelaufen → Auto-Reject, **nie** Auto-Approve),
`abandoned` (explizit beendet oder 30-Tage-Inaktivität bei low-risk-
markierten Items). Siehe SPECIFICATION.md §5.7, §6.2.

## Interaction
Modul für Control Surface, Intent-Klassifikation, HITL-Inbox, Single-User-
Identität.

## Knowledge
Modul für Observations, Decisions, Standards, Artifacts, Evidence.
Organisierte Wissensbasis, periodischer Review alle 2–4 Wochen.

## Litestream
Continuous-Replication-Tool für SQLite → S3-kompatibles Object Storage.
Liefert Point-in-Time-Recovery. Siehe ADR-0003.

## Model Inventory
Statische YAML-Konfiguration (`config/dispatch/model-inventory.yaml`) mit
allen bekannten Adapter × Modell × Preis × Context × Capability-Flags-
Kombinationen. Vom Dispatcher gelesen, nicht Runtime-veränderlich.
Pflege: monatlich manuell.

## MADR
Markdown Architecture Decision Record. Format für Entscheidungen in
`docs/decisions/`.

## Needs Reconciliation
Zwischenzustand einer Run nach Litestream-Restore auf einem frischen Host
(§10.4 Testmatrix). Solange externe Effekte nicht per Idempotency-Key
(ADR-0011) abgeglichen sind, bleibt die Run in diesem Zustand — kein
automatischer Weitergang zu `completed`/`failed`.

## Modular Monolith
Architektur-Idiom mit klaren Modul-Grenzen, aber ohne Service-Deployment.
Für V1 gewählt (ADR-0001).

## MVS (Minimum Viable Sandbox)
8-Schichten-Isolation pro Agent-Run. Siehe ADR-0006.

## Observation
Erfasste, nicht-normative Beobachtung im Knowledge-Modul. Ursprung in GTD-
Capture-Primitive.

## Portfolio
Modul für Projekte, Dependencies, Binding-Scope. Policy als Querschnitt
(nicht eigenes Modul).

## Pinned Mode
Betriebsmodus des Dispatchers, in dem `routing-pins.yaml` als Lookup dient
und bei fehlender Pin der globale Default aus `model-inventory.yaml`
(`rules.defaults.adapter` + adapter-spezifischer Default) gewählt wird.
V1-Default und legitime dauerhafte Endstufe (mit F0005-Pin-Kuration).
Wechsel zu **Cost-Aware Mode** ist **explizites Nutzer-Opt-in** via
`agentctl dispatch mode cost-aware` — kein automatischer Wechsel auf
Basis von Pin-Anzahl oder Zeitintervall (V0.2.3-draft, ADR-0014).

## Progressive Disclosure
Muster, bei dem nicht die ganze Spec auf einmal geladen wird, sondern per
Skill (`spec-navigator`) gezielt Abschnitte.

## Project
Langfristige Portfolio-Entität mit Identität, Lifecycle und Beziehungen.
Kann mehrere Work Items haben.

## Pydantic AI
Dünner, typ-sicherer LLM-Call-Wrapper; arbeitet mit Durable-Execution-
Frameworks zusammen, ist kein Orchestrator. Siehe ADR-0004.

## Research Brief
Evidenz-Dokument in `docs/research/NN-*.md` mit wissenschaftlich zitierten
Quellen (Tier 1/2/3).

## Routing Pin
Eintrag in `config/dispatch/routing-pins.yaml`, der einen bestimmten
Match-Ausdruck (z. B. `work_item_type: long_coding_refactor`) fest auf
Adapter + Modell bindet. Überschreibt Cost-Aware-Routing-Entscheidungen.
Siehe ADR-0014, Feature F0003.

## Run
Konkrete Ausführung eines Work Items in Execution. Umbenannt von Legacy
`Workflow`. Stateless aus Orchestrator-Sicht.

## RunAttempt
Runtime Record (ADR-0011) für einen konkreten Versuch einer Run. Enthält
Startzeit, Endzeit, Agent, Modell, Sandbox-Profil, Prompt-Hash, Tool-
Allowlist, Exit-Code, Kosten, Logs-Referenz. Mehrere `RunAttempt` pro
`Run` möglich (Retries). Idempotency-Keys für externe Effekte.

## Sandbox
Siehe MVS.

## Standard
Wiederverwendbares Muster oder Regel mit 4-Stufen-Lifecycle
(candidate → accepted → bound → retired). Siehe ADR-0005.

## Subagent
Delegierter Agent-Kontext in Claude Code (Tiefe ≤ 2) oder Codex CLI.
In unserem System nur für Parallelismus, nicht für Sicherheitsgrenzen.

## SPECIFICATION.md
`docs/spec/SPECIFICATION.md` — die normative V1-Spec in arc42-Struktur.

## Synthesis Document
`docs/research/99-synthesis.md` — Brücke zwischen den 17 Research-Briefs
und der normativen Spec.

## Tool-Risk-Inventory
Normative Konfigurations-Datei (`config/execution/tool-risk-inventory.yaml`,
ADR-0015), die jedem Tool-Aufrufmuster eine Risk-Klasse (`low` / `medium`
/ `high` / `irreversible`) und einen Approval-Modus (`never` / `required`
/ `policy_gated`) zuordnet. Voraussetzung dafür, dass Codex CLI mit
`approval=never` betrieben werden kann (HITL-Gate wird orchestrator-
seitig vor dem Tool-Call gezogen). Erste Match gewinnt; nicht
klassifizierte Tools fallen auf einen fail-closed Default zurück.

## Effect Classes (Idempotenz-Klassen)
Drei Klassen für externe Effekte mit unterschiedlicher Idempotenz-
Qualität (ADR-0011 V0.2.3-draft):
- **natürlich-idempotent** (Git-Commit, File-Write): Inhalts-Hash, keine
  Duplikate möglich.
- **provider-keyed** (z. B. GitHub-PR-Create mit Idempotency-Key-Header):
  Provider deduplikiert; Crash zwischen Send und Persist führt nur zu
  sicherem Retry.
- **lokal-only** (GitHub-Issue-Comment, Slack-Post, Mail): nur lokaler
  Idempotency-Key in `ToolCallRecord`; Crash-Fenster zwischen externem
  Effekt und Persist erzeugt echten Duplikat-Pfad → Reconciliation
  via `agentctl runs reconcile <run-id>`.

## Trust Zone
Architektur-Zone mit definierter Vertrauensqualität. 4 Zonen: External
Untrusted, Interpreted Control, Decision Core, Restricted Execution.

## WIP (Work in Progress)
Limit auf gleichzeitige aktive Arbeit. V1-Werte: 2 Work Items, 3–5
Projekte, 2–3 Agent-Runs pro Work Item. Siehe `docs/research/10-work-admission.md`.

## Work Item
Fachliche Arbeitseinheit im Work-Modul. Hat Lifecycle
(`proposed → accepted → … → completed/abandoned`), kann Runs haben.

## Worktree
Git-Worktree als Isolationsschicht (Schicht 1 des MVS). Pro Run einer.
