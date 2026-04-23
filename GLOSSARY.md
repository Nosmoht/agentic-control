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

## DBOS
In-Process-Library für Durable Execution; Schritte checkpoints in der
gleichen Transaktion wie Domänen-Writes. Siehe ADR-0002.

## Decision
Dokumentierte Wahl im ADR-Minimalformat (Kontext, Entscheidung, Konsequenz).
Kennzahl im Knowledge-Modul.

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

## Execution
Modul, das bounded Agent-Runs ausführt. Sandboxed, stateless, ephemer.

## HITL (Human in the Loop)
Punkte, an denen das System menschliche Freigabe einholt. Per Inbox-Kaskade
(4h/24h/72h), nicht synchroner Push. Siehe ADR-0007.

## Interaction
Modul für Control Surface, Intent-Klassifikation, HITL-Inbox, Single-User-
Identität.

## Knowledge
Modul für Observations, Decisions, Standards, Artifacts, Evidence.
Organisierte Wissensbasis, periodischer Review alle 2–4 Wochen.

## Litestream
Continuous-Replication-Tool für SQLite → S3-kompatibles Object Storage.
Liefert Point-in-Time-Recovery. Siehe ADR-0003.

## MADR
Markdown Architecture Decision Record. Format für Entscheidungen in
`docs/decisions/`.

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

## Run
Konkrete Ausführung eines Work Items in Execution. Umbenannt von Legacy
`Workflow`. Stateless aus Orchestrator-Sicht.

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
