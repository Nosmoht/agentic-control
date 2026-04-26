# Changelog

Alle signifikanten Änderungen an der Spezifikation werden hier dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versionen folgen [Semantic Versioning](https://semver.org/) für Specs
(Major = Breaking Change im Datenmodell oder in Modul-Grenzen,
Minor = additiv, Patch = Klarstellungen/Fixes).

## [0.3.0-draft] — 2026-04-26

Minor-Release (additiv). Adressiert Schicht B des Reaktions-Plans auf
das dritte Codex-Follow-up-Review
(`docs/reviews/2026-04-26-followup-review-2.md`): drei substantielle
Erweiterungen, die Implementierbarkeit von v1a tatsächlich
herstellen.

### Added

- **ADR-0016 Config Write Contract for Dispatch and Execution.** Vier
  Garantien (Atomic Write, File-Lock, Optimistic Version Check, Audit
  Event) für alle normativen YAML-Configs unter `config/dispatch/`
  und `config/execution/`. Adressiert Counter-Counter-Review-Befund 3
  (Hoch), schließt F0005-Schreibvertrag-Lücke und definiert den
  Vertrag, den F0006/F0007 ebenfalls konsumieren.
- **F0006 Runtime Records SQLite Schema and Reconcile CLI** (Stage
  v1a). Liefert die acht Runtime-Record-Tabellen aus ADR-0011, JSONL-
  Runlog/Budget-Ledger und `agentctl runs reconcile / runs inspect /
  audit show`-CLI-Befehle. Voraussetzung für die Implementierung von
  F0003/F0004/F0005/F0007. Adressiert Counter-Counter-Review-Sofort-
  Empfehlung 1.
- **F0007 Tool-Risk-Drift Detection** (Stage v1a). `agentctl tools
  audit` liest `ToolCallRecord`-Rows, gruppiert default-Hits, erzeugt
  Digest-Card mit Inventory-Erweiterungs-Vorschlägen. `agentctl tools
  propose <name>` schreibt über ADR-0016-Vertrag in
  `tool-risk-inventory.yaml`. Adressiert Counter-Counter-Review-
  Befund 8.
- **`config/execution/tool-risk-inventory.yaml` `drift_threshold_pct`-
  Feld** (Default 5 %, Eigenentscheidung) für F0007.
- **`config/dispatch/model-inventory.yaml` `rules.adapter_assignment_
  rules`** als Pattern-Liste (`claude-* → claude-code`,
  `gpt-*`/`o-* → codex-cli`, `gemini-* → null`, Catch-all → `null`)
  für F0005 Modell-Arrival-Detection. Konsequenz: Orchestrator
  special-cased weiterhin keinen Adapter (ADR-0014 Aufruf-Disziplin).

### Changed

- **ADR-0015 / `tool-risk-inventory.yaml`** spaltet das frühere breite
  `shell_exec`-Pattern in vier disjunkte Sub-Pattern auf:
  `shell_readonly` (low, never), `shell_worktree_write` (medium,
  never), `shell_network` (high, required), `shell_dangerous`
  (irreversible, required). Übergangsregel: unklare Shell-Befehle
  klassifizieren Adapter als `shell_dangerous` (fail-closed innerhalb
  der Shell-Klasse). Inventory `version: 1 → 2`. Adressiert
  Counter-Counter-Review-Befund 7.
- **F0005** wird auf den ADR-0016-Schreibvertrag umgestellt:
  Acceptance Criterion 5 (`accept`) referenziert atomarer Rename,
  File-Lock, Optimistic Version Check, AuditEvent mit Hashes;
  Acceptance Criterion 8 (Modell-Arrival-Adapter-Zuordnung) liest aus
  `model-inventory.yaml.rules.adapter_assignment_rules` statt
  hardcodeter Prefix-Logik; Acceptance Criterion 10 verweist
  pauschal auf ADR-0016 für alle drei Schreibziele.
  `adr_refs` ergänzt um ADR-0011 und ADR-0016. Adressiert
  Counter-Counter-Review-Befunde 3 + 6.
- **`config/dispatch/model-inventory.yaml`** `version: 2 → 3`,
  `updated: 2026-04-26`.
- **`docs/features/README.md`, `docs/plans/project-plan.md`** Feature-
  Index um F0006 und F0007 erweitert; Dependency-Graph zeigt F0006
  als Voraussetzung für F0003/F0004/F0005/F0007; v1a-Pfad
  aktualisiert auf F0001 → F0006 → [F0003, F0004, F0007] → F0005.
- **SPECIFICATION.md §9** ADR-Tabelle: ADR-0016 ergänzt; ADR-0015-
  Status-Note um „V0.3.0-draft `shell_*`-Splitting".
- **SPECIFICATION.md Frontmatter** `version: 0.2.4-draft → 0.3.0-draft`.
- **AGENTS.md, README.md, spec-reviewer.md, spec-navigator/SKILL.md**
  Stand auf V0.3.0-draft.

## [0.2.4-draft] — 2026-04-26

Patch-Release nach drittem Codex-Follow-up-Review
(`docs/reviews/2026-04-26-followup-review-2.md`). Schließt fünf
konkrete Drifts, die V0.2.1/0.2.2/0.2.3 in der eigentlichen
Architekturarbeit übersehen hatten. Keine neuen Entscheidungen, keine
Scope-Erweiterung — Schicht A im 04-26-Reaktions-Plan.

### Fixed

- **SPECIFICATION.md §10.4** Crash-Akzeptanzkriterium von einer
  pauschalen Idempotency-Keys-Aussage auf drei differenzierte
  Assertions gezogen, je eine pro ADR-0011-Effektklasse (natürlich-
  idempotent / provider-keyed / lokal-only mit `agentctl runs
  reconcile`-Pfad). Adressiert 04-26-Befund 1.
- **SPECIFICATION.md §8.5** Aufruf-Disziplin: „in gleicher Tiefe
  dokumentiert und verwendet" → „in gleicher Tiefe vertraglich
  dokumentiert; Default-Nutzung folgt §8.6/Inventory". Adressiert
  04-26-Befund 2 (V0.2.3-Honest-Default driftete sonst gegen den
  Symmetrie-Wortlaut).
- **docs/plans/project-plan.md** Header von `Version: 0.2.0-draft,
  Stand: 2026-04-24` auf `Version: 0.2.4-draft, Stand: 2026-04-26`.
  In V0.2.1/0.2.2/0.2.3 jedes Mal beim Versions-Bump übersehen.

### Added

- **`config/dispatch/benchmark-task-mapping.yaml`** als Seed-Datei mit
  Schema (`task_to_benchmark`, `drift_threshold_pp`), Default-Schwelle
  3 pp und initialem Mapping für coding/reasoning/general/math/
  long_context. Adressiert 04-26-Befund 4 (Spec referenzierte den
  Pfad bereits, Datei fehlte im Repo).

### Changed

- **F0005** kennzeichnet die 3-pp-Drift-Schwelle und die Adapter-
  Prefix-Regel (`claude-*`/`gpt-*`/`o-*`/`gemini-*` → Adapter)
  ausdrücklich als **Eigenentscheidungen** mit Hinweis auf den
  ADR-0014-Konflikt der Prefix-Regel. Adressiert 04-26-Befunde 5 + 6.
- **SPECIFICATION.md Frontmatter** `version: 0.2.3-draft → 0.2.4-draft`.
- **AGENTS.md, README.md, spec-reviewer.md, spec-navigator/SKILL.md**
  Stand auf V0.2.4-draft, Datum 2026-04-26.

## [0.2.3-draft] — 2026-04-25

Adressiert die fünf verbliebenen Architekturfragen aus dem
Codex-Follow-up-Review (`docs/reviews/2026-04-24-followup-review.md`),
die V0.2.1-draft als „Urteilssachen" abgespalten hatte: Peer-Adapter-
Asymmetrie, DispatchDecision-Freeze-Zeitpunkt, Tool-Risk-Inventar,
`cost-aware`-Auto-Aktivierung, Idempotenz-Overclaim, ADR-0014-Split-
Marker.

### Added

- **ADR-0015 (Tool-Risk-Inventory and Approval Routing).** Neue
  normative Entscheidung mit vier Risk-Klassen (`low` / `medium` /
  `high` / `irreversible`), drei Approval-Modi, Orchestrator-Vertrag
  und fail-closed-Default. Voraussetzung dafür, dass Codex CLI mit
  `approval=never` betrieben werden kann.
- **`config/execution/tool-risk-inventory.yaml`** mit ~21 Seed-
  Einträgen (Datei-/Such-/Lokal-Schreib-/Git-/GitHub-/Notification-/
  Web-Pattern + Catch-all `gh_*`). Pflege wie `model-inventory.yaml`.
- **GLOSSARY.md** Einträge für `Tool-Risk-Inventory` und für die drei
  Effekt-Klassen (`Effect Classes`).
- **Reconciliation-Mechanismus** in ADR-0011: `agentctl runs reconcile
  <run-id>` als CLI-Vorgang für die lokal-only-Effekt-Klasse.

### Changed

- **ADR-0014 Peer-Adapter-Stance.** „Kein Vorrang, keine Primary-Rolle"
  ersetzt durch ehrliche Formulierung: „Peers im Vertrag, Default-
  Adapter konfigurierbar via `model-inventory.yaml.rules.defaults.adapter`,
  V1-Vorschlag claude-code". Adressiert Counter-Review-Befund 1
  (formal symmetrisch, operativ asymmetrisch).
- **ADR-0014 Cost-Aware-Routing-Policy.** Pre-Gate vs. Post-Gate
  Freeze-Zeitpunkt klargestellt: DispatchDecision wird **nach**
  Gate-Check gefroren; Gate-induzierte Rewahl erscheint als
  zusätzlicher `PolicyDecision(policy=budget_gate_override)`,
  **nicht** als zweite DispatchDecision. Adressiert
  Counter-Review-Befund 2.
- **ADR-0014 Mode-Aktivierung.** Auto-Aktivierung „5+ Pins oder
  4 Wochen Nutzung" **ersatzlos gestrichen**; Wechsel zwischen
  `pinned` und `cost-aware` ist nur noch via
  `agentctl dispatch mode <mode>` möglich. `pinned` mit F0005-Kuration
  ist legitime Endstufe. Adressiert Counter-Review-Befund 7.
- **ADR-0014 Codex-Approval-Mode-Begründung.** Verweis auf ADR-0015
  als normatives Tool-Risk-Inventar, statt impliziter
  „ADR-0007 + PolicyDecision"-Kombination.
- **ADR-0014 Follow-ups.** ADR-Split-Marker ergänzt („bei nächster
  substantieller Änderung in eigene ADRs aufspalten"); ADR-0015 ist
  jetzt das Tool-Risk-Inventory, Codex-Approval-Mode-Details auf
  ADR-0016 verschoben (frühere Reservierung).
- **ADR-0011 Idempotenz-Sektion.** Drei Effekt-Klassen (natürlich-
  idempotent / provider-keyed / lokal-only) mit jeweils eigener
  Restrisiko-Charakterisierung; Reconciliation-Mechanismus für
  lokal-only inline. Der Satz „Dual-Write-Fehler konstruktiv
  ausgeschlossen" ist auf die DB-Seite begrenzt; die externe Crash-
  Lücke wird explizit benannt. Adressiert Counter-Review-Befund 3.
- **`config/dispatch/model-inventory.yaml`** `rules.defaults.adapter`
  als neuer Schlüssel (V1: `claude-code`); `version: 2`.
- **SPECIFICATION.md §6.2** Dispatch-Flow: vorläufige Auswahl,
  Gate-Rewahl als PolicyDecision, post-gate-Freeze.
- **SPECIFICATION.md §8.3** Budget-Gate: Gate-Override erscheint als
  PolicyDecision, nicht als zweite DispatchDecision.
- **SPECIFICATION.md §8.6** Policy-Block neu sortiert (1: Pin, 2:
  pinned mit konfigurierbarem Default, 3: cost-aware, 4: Gate, 5:
  Freeze); Mode-Aktivierung explizit als Opt-in.
- **SPECIFICATION.md §9** ADR-Tabelle: ADR-0015 ergänzt; ADR-0014-
  Status-Note um „cost-aware-Auto-Aktivierung gestrichen".
- **SPECIFICATION.md Appendix A v1** „cost-aware"-Mode-Aktivierungs-
  Trigger umgeschrieben auf Opt-in.
- **SPECIFICATION.md Frontmatter** `version: 0.2.2-draft → 0.2.3-draft`.
- **`docs/plans/project-plan.md`** Open Decisions Punkt 4 auf Opt-in
  umgeschrieben.
- **AGENTS.md, README.md, spec-reviewer.md, spec-navigator/SKILL.md**
  Stand auf V0.2.3-draft, Datum 2026-04-25.
- **GLOSSARY.md `Pinned Mode`** an den V0.2.3-Stand gezogen
  (Auto-Aktivierung gestrichen, Opt-in-Wortlaut, F0005-Verweis).
- **F0003-cost-aware-routing-stub** Context und Test-Plan auf den
  V0.2.3-Stand gezogen (kein Auto-Wechsel mehr).
- **ADR-0002 Treiber** und **ADR-0013 Treiber** Dual-Write-Aussage
  explizit auf die DB-Seite begrenzt; Verweis auf
  ADR-0011-V0.2.3-Reconciliation für die orthogonale Klasse externer
  Effekte.

## [0.2.2-draft] — 2026-04-24

Additives Release. Führt den **Benchmark-kuratierten Pin-Refresh-Loop**
als eigenes Feature ein, das die Nutzer-Anforderung „wöchentlich
prüfen, welches LLM hinter welchem Tool am besten ist, und Pins
entsprechend aktualisieren" operationalisiert. **Nicht** als
Runtime-Auto-Dispatch (das bleibt empirisch verworfen), sondern als
kalter HITL-Batch-Pfad neben dem deterministischen `pinned`-Lookup.

### Added

- `docs/features/F0005-benchmark-curated-pin-refresh.md` (Stage v1a):
  - `agentctl benchmarks refresh` detektiert Modell-Arrival und
    Pin-Drift gegen aktuelle Benchmarks.
  - `agentctl dispatch review / accept / reject` als HITL-
    Kurationsoberfläche; Proposals landen in
    `config/dispatch/pending-proposals.yaml` mit 14-Tage-Expiry.
  - Neue Config `config/dispatch/benchmark-task-mapping.yaml` mappt
    Task-Klassen auf Benchmarks (`coding: swe_bench_verified`, etc.)
    und enthält die Drift-Schwelle (Default 3 pp).
- **SPECIFICATION.md §6.2:** neuer Fluss „Benchmark-Refresh →
  Pin-Kuration (F0005)" direkt unter „Benchmark-Awareness-Pull";
  explizite Abgrenzung „kein Runtime-Auto-Dispatch".

### Changed

- **`docs/features/README.md` Feature-Index** und **`docs/plans/project-plan.md`
  Feature-Index** um F0005 ergänzt; Dependency-Graph im Plan zeigt
  F0003 + F0004 → F0005; kritischer v1a-Pfad aktualisiert.
- **SPECIFICATION.md Frontmatter** `version: 0.2.1-draft → 0.2.2-draft`.
- **AGENTS.md, README.md, spec-reviewer.md, spec-navigator/SKILL.md**
  Stand auf V0.2.2-draft gezogen.

## [0.2.1-draft] — 2026-04-24

Patch-Release nach Follow-up-Review durch Codex
(`docs/reviews/2026-04-24-followup-review.md`). Behebt konkrete
Normkonsistenz-Lücken, die der V0.2.0-Patch zurückgelassen hat.
Keine neuen Entscheidungen, keine Scope-Änderung.

### Fixed

- **ADR-0007** Status-Line trägt jetzt die Präzisierung durch ADR-0012
  explizit; 72-h-Auto-Abandon durchgestrichen; „Kumulativ" → „disjunktiv
  (OR)" mit Verweis auf ADR-0012. Referenz-Liste um ADR-0012 ergänzt.
- **ADR-0008** Task-Row-Semantik von `$2 AND 25 Turns AND 15 min` zu
  `$2 OR 25 Turns OR 15 min` korrigiert (war in V0.2.0-draft nur in
  Spec §8.3 gefixt, ADR widersprach). Status-Line trägt die Korrektur.
- **ADR-0011** Runtime-Record-Tabelle um `DispatchDecision`-Zeile
  erweitert (war in V0.2.0 nur in Spec §5.7 und im Beziehungsblock
  gelistet).
- **SPECIFICATION.md §5.7** Work-Item-Lifecycle trägt die HITL-Sub-
  States (`waiting_for_approval`, `stale_waiting`, `timed_out_rejected`)
  als Unterscheidungen von `waiting/blocked`; Run-Lifecycle trägt den
  Zwischenzustand `needs_reconciliation` (gefordert durch §10.4).
- **SPECIFICATION.md §9** Status-Annotation bei ADR-0008 trägt den
  V0.2.1-Fix.
- **AGENTS.md** Stand-Line: V0.1.0-draft → V0.2.1-draft, Datum auf
  2026-04-24.
- **.claude/agents/spec-reviewer.md** Versionshinweis auf V0.2.1-draft;
  „alle 7 Invarianten" → „alle 8 Invarianten" (Inkonsistenz mit dem
  Invarianten-Block 13–29).
- **F0001** Referenz „Runtime Records kommen erst mit v1a (F0004-ff.)"
  korrigiert auf generische „v1a-Features" (F0004 ist Benchmark-
  Awareness, nicht Runtime Records).
- **docs/features/README.md** Stage-Enum um `v1a` und `v1b` erweitert;
  Feature-Index trägt ADR-0003 bei F0001 nach, F0003/F0004 auf Stage
  `v1a` gesetzt.
- **F0003, F0004** Frontmatter-Stage auf `v1a`.
- **docs/plans/project-plan.md** Feature-Index deckungsgleich mit
  `features/README.md`: F0001 → ADR-0001 + ADR-0003, F0003/F0004 → v1a.
- **docs/research/99-synthesis.md** Budget-Gate-Tabelle: AND → OR in der
  Task-Row (gleiche Korrektur wie ADR-0008).
- **README.md, .claude/skills/spec-navigator/SKILL.md** Stand-Referenzen
  von V0.1.0-draft auf V0.2.1-draft gezogen.
- **SPECIFICATION.md Frontmatter** `version: 0.2.0-draft → 0.2.1-draft`.
- **GLOSSARY.md** Einträge für `HITL-Sub-States` und `Needs Reconciliation`
  ergänzt, damit die neuen State-Machine-Zustände nicht nur in §5.7
  stehen, sondern auch im Glossar.
- **docs/research/99-synthesis.md** HITL-Abschnitt an ADR-0012 angeglichen
  (disjunktive Kriterien, kein Default-Auto-Abandon) und „Eigenentscheidungen"-
  Block entsprechend aktualisiert.

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
