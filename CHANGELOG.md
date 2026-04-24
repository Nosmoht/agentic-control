# Changelog

Alle signifikanten Änderungen an der Spezifikation werden hier dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versionen folgen [Semantic Versioning](https://semver.org/) für Specs
(Major = Breaking Change im Datenmodell oder in Modul-Grenzen,
Minor = additiv, Patch = Klarstellungen/Fixes).

## [0.2.0-draft] — 2026-04-24

### Added
- `docs/features/` mit Index-Datei und 4 Initial-Features (F0001–F0004)
  für v0/v1-Scope (SQLite-Schema, `work add` CLI, Cost-Aware-Routing-Stub,
  Benchmark-Awareness).
- `docs/plans/project-plan.md` als Master-Plan mit Milestones, Feature-Index,
  Dependency-Graph, Erfolgsmetriken pro Stage und Anti-Zielen.
- `config/dispatch/model-inventory.yaml` (statische Liste Adapter × Modell
  × Preis × Context × Capability-Flags für 6 Modelle: Opus 4.7, Sonnet 4.6,
  Haiku 4.5, GPT-5.4, GPT-5 mini, Gemini 3.1 Pro).
- `config/dispatch/routing-pins.yaml` (leer, bereit für manuelle Pins).
- 5 neue MADR-ADRs:
  - **ADR-0010** Execution Harness Contract (operativer Vertrag zu ADR-0006,
    Mount-Tabelle, Secret-Injection, Egress-Proxy, Exit-Artefakte).
  - **ADR-0011** Runtime Audit and Run Attempts (7 Runtime-Record-Typen +
    Idempotency-Keys für externe Effekte).
  - **ADR-0012** HITL Timeout Semantics (4 Zustände, disjunktive Kriterien,
    kein Auto-Abandon-Default, Digest-Card-Trigger).
  - **ADR-0013** V1 Deployment Mode (v1a lokal / v1b read-only Bridge /
    v2+ Postgres).
  - **ADR-0014** Peer Adapters and Cost-Aware Routing (überschreibt
    Befund 9, amends ADR-0004, führt ExecutionAdapter-Interface inline
    und Cost-Aware-Routing-Policy).
- `docs/reviews/2026-04-23-critical-system-review.md` (Codex-Review, der
  Wave 1 ausgelöst hat) und `docs/reviews/2026-04-23-counter-review.md`
  (meine Antwort).
- `Plans/option-3-ich-m-chte-serialized-oasis.md` mit Appendix A
  (empirische Basis für Symbiose-Design: Benchmark-Evidenz 2026,
  RouteLLM, MoA, Stanford AI Index).

### Changed
- **SPECIFICATION.md Version 0.1.0-draft → 0.2.0-draft.** Vollständiger
  Rewrite mit Phase-A-Korrekturen und Option-3-Erweiterungen.
- **Modul-Schnitt:** Work-Modul erhält expliziten **Dispatcher** als
  Sub-Komponente (§5.3, Policy, nicht Execution).
- **§5.4 Execution:** Claude Code und Codex CLI als gleichwertige
  Peer-Adapter (Befund 9 überschrieben). `ExecutionAdapter`-Interface mit
  5 Verben als Kopplungspunkt.
- **§5.5 Knowledge:** `Evidence(kind=benchmark)` als explizites Subtyp.
- **§5.7 Kernobjekte:** `stage`-Spalte pro Objekt; neuer Unterabschnitt
  „Runtime Records" (aus ADR-0011).
- **§6.2 Hauptflüsse:** Neuer Fluss „Work Item → Dispatch → Run";
  HITL-Flow gemäß ADR-0012; Benchmark-Awareness-Pull als eigener Fluss.
- **§7 Verteilungssicht:** Widerspruch aus Counter-Review Befund 1 gelöst;
  drei Modi (v1a, v1b, v2+) klar getrennt.
- **§8.3 Budget-Gate:** `AND` → `OR` (unabhängige harte Caps, Befund 5);
  Reihenfolge klar (Dispatch füttert Gate).
- **§8.4 Observability:** Normatives Minimum (SQLite-Audit, JSONL-Runlog,
  JSONL-Budgetledger, `agentctl`-CLI-Commands, 90-Tage-Retention).
- **§8.5 Agent-Aufruf-Disziplin:** Peer-Adapter-Framing; CC und Codex in
  gleicher Tiefe.
- **§8.6 (NEU) Agent-Auswahl:** Cost-Aware-Routing-Policy mit `pinned`-
  Default, `cost-aware`-Aktivierungs-Trigger (5+ Pins oder 4 Wochen),
  empirischer Ausschluss von Task-Class-Specializer und Cross-Model-Review.
- **§10.1 Primärmetriken:** Neue Metriken (Benchmark-Freshness,
  Dispatch-Override-Rate, Adapter-Mix).
- **§10.4 (NEU) Akzeptanzkriterien-Testmatrix:** Restore-Drill, Retry-
  Sicherheit, HITL-Restart-Invariante.
- **§11.1 Risiken:** Router-Collapse, Benchmark-Disagreement, Classifier-
  Drift neu.
- **§11.3 Offene Entscheidungen:** CC-vs-Codex-Frage geschlossen;
  Task-Class-Specializer und Cross-Model-Review **verworfen** mit
  Evidenz-Verweis in Plan-Appendix A.
- **Appendix A:** Zielarchitektur vs. Release-Stages klar getrennt.
- **AGENTS.md:** neuer Abschnitt „Feature-Disziplin".
- **`.claude/agents/spec-reviewer.md`:** Invariante 8 ergänzt (Feature-
  Frontmatter-Refs resolven).
- **GLOSSARY.md:** neue Einträge (`Cost-Aware Routing`, `Dispatcher`,
  `DispatchDecision`, `ExecutionAdapter`, `HarnessProfile`, `Benchmark
  Evidence`, `Benchmark Puller`, `Model Inventory`, `Pinned Mode`,
  `Routing Pin`, `RunAttempt`); Evidence-Eintrag erweitert.

### Superseded
- **ADR-0004 §Aufruf-Disziplin** wird von ADR-0014 amended (Peer-Stance).
- **ADR-0007 72-h-Auto-Abandon** wird von ADR-0012 durch vier HITL-Zustände
  und `timed_out_rejected` ersetzt.

## [0.1.0-draft] — 2026-04-23

### Added
- `docs/spec/SPECIFICATION.md` — V1-Spec in arc42-Struktur.
- `docs/decisions/0001-0009` — 9 MADR-Architekturentscheidungen.
- `docs/research/01-15` — 15 Research-Briefs (Tier A–D).
- `docs/research/16-17` — 2 Research-Briefs zu Doku-Struktur und
  Agent-Repo-Preparation (Tier E).
- `docs/research/99-synthesis.md` — Synthese der Research-Briefs als Brücke
  zur Spec.
- `AGENTS.md` als Single-Source-of-Truth für Agent-Instruktionen,
  `CLAUDE.md` als Symlink darauf.
- `.claude/` und `.codex/` Projekt-Konfigurationen für Claude Code bzw.
  Codex CLI.
- `.mcp.json` mit Filesystem- und GitHub-MCP-Servern.
- `.claude/skills/spec-navigator/` als Progressive-Disclosure-Skill.
- `.claude/agents/spec-reviewer.md` als read-only Subagent für
  Konsistenz-Checks.
- `GLOSSARY.md` als zentrales Glossar.
- `README.md`, `ARCHITECTURE.md` als Einstiegspunkte.
- `archive/` mit den ursprünglichen 12 Brainstorm-Notizen, `REVIEW.md` und
  `12-open-questions.md` (nicht mehr normativ).

### Changed
- Modul-Schnitt: 13 Bounded Contexts → **5 Module** (Interaction, Work,
  Execution, Knowledge, Portfolio).
- Kernobjekte: 12 → **9**. Entfallen: `Approval` (Flag am Work Item),
  `Context Bundle` (Funktion in Knowledge), `Provider Binding` (Property
  an Run). `Workflow` umbenannt zu `Run`.
- Standards-Lifecycle: 6 → **4 Stufen**.
- Trust-Zonen: 6 → **4 Zonen**.

### Removed
- Legacy-Status für `archive/legacy-notes/` — nicht löschen, nicht mehr
  normativ.
- `Evidence.trust_class` (Kategorienfehler).
- Eigenständige Kontexte: Identity/Trust/Access, Intent Resolution,
  Event Fabric, Observability/Audit, Project Provisioning/Provider
  Integration (alle als Querschnitt oder Property integriert).
