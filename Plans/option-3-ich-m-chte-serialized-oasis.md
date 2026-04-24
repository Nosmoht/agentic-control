# Plan: Option 3 + Cost-Aware Routing + Feature-Files + Project-Plan

**Date:** 2026-04-24
**Status:** proposed
**Scope:** V0.1.0-draft → V0.2.0-draft (documentation-only)
**Revision history:** initial draft (volle Wave 1+2) → Cut auf Minimal-Scope nach Nutzer-Entscheidung + Symbiose-Pivot nach empirischer Recherche.

## Context

Der Nutzer hat Option 3 gewählt (Claude Code + Codex CLI als Peer-Adapter ab v1) und vier Anforderungen gesetzt:

1. Konkreter Project-Plan im Repo.
2. Jedes Feature als eigene Markdown-Datei für gezielte Entwicklung, Test, Abnahme.
3. Symbiose CC ↔ Codex als Kernfeature, um die dahinterliegenden LLMs optimal zu nutzen.
4. Regelmäßig offizielle Benchmarks pullen, um Tasks an das beste Modell zu dispatchen.

**Wichtige Kurskorrektur nach Deep-Research (siehe Appendix A):** Die naheliegende Umsetzung von (3) und (4) — Task-Class-Specializer mit 8-Klassen-Taxonomie und Cross-Model-Review-Loop — hält empirisch nicht. Frontier-Modelle konvergieren 2026 auf < 2 % Unterschied außerhalb Coding; Cross-Model-Review leidet unter Self-Preference- und Position-Bias; Self-MoA schlägt Mixed-MoA. Statt der spekulativen Dispatch-Mathematik implementiert dieser Plan **Cost-Aware-Routing (RouteLLM-Stil)** und **Benchmarks-als-Awareness** (nicht als Dispatch-Eingabe). Das ist die empirisch gestützte Minimalform.

Weitere Eingaben: Adversarieller Review, User-Intent-Review und Architektur-Kohärenz-Review haben den ursprünglichen Entwurf als zu groß (13 ADRs, 10 Features, 5 Plan-Files, 17 Patches auf einmal) und teilweise architektonisch inkohärent (Model Inventory im falschen Modul, Triple-Modellierung der Benchmark-Objekte, fehlende ADR-Supersession-Deklarationen) identifiziert. Der Nutzer hat den Minimal-Scope gewählt.

Zielartefakt: Documentation-Only-Repo-Stand V0.2.0-draft, der die Phase-A-Korrekturen aus dem Counter-Review landet, Peer-Adapter-Entscheidung festschreibt, einen lean Cost-Aware-Router als Stub vorbereitet und das Feature-File-Pattern etabliert — alles in einem Patch.

## Recommended Approach

### 1 · Repo-Struktur-Ergänzungen

```
/
├── docs/
│   ├── features/                         # NEU
│   │   ├── README.md                     # Index, Status-Legende, "Wo gehört dieser Satz hin"-Cheatsheet
│   │   └── FNNNN-kebab-name.md           # Feature-Dateien, flache Ablage, Stage als Frontmatter
│   └── plans/                            # NEU
│       └── project-plan.md               # Master: Milestones, Feature-Index, Stage-Skizze, Open-Decisions
└── config/                               # NEU
    └── dispatch/
        ├── model-inventory.yaml          # Statische Liste Adapter × Modell × Preis × Context × Capability-Flags
        └── routing-pins.yaml             # Manuelle Task-Pins (leer zu Start)
```

**Regeln:**
- Feature-Files flach, nicht per-Stage-Subordner. Stage ist Frontmatter-Property.
- Naming: `FNNNN-kebab-name.md`, 4-stellig, monoton.
- Genau **eine** Plan-Datei (`project-plan.md`). Per-Stage-Dateien entstehen erst mit Substanz.
- `config/dispatch/*.yaml` ist normative Konfiguration, aber kein ADR-würdiges Artefakt. Änderungen werden in CHANGELOG vermerkt.

### 2 · Feature-File-Format (schlanke Version)

**Frontmatter (6 Pflichtfelder):**
```yaml
---
id: F0001
title: SQLite Schema for Core Objects
stage: v0                           # v0 | v1 | v2 | v3
status: proposed                    # Lifecycle: proposed → in_progress → done; Terminal: rejected | superseded
spec_refs: [§5.7]
adr_refs: [ADR-0001]
---
```

**Weggefallen vs. Original-Plan:** `owner` (immer self), `created`/`updated` (Git-Log), `depends_on`/`blocks` (aus ADR/Spec-Refs ableitbar), `signed_off_at`/`signed_off_commit` (Git-Log), `supersedes`, `research_refs`.

**Body (feste Reihenfolge, alle Pflicht):** Context (≤ 6 Sätze) · Scope · Out of Scope · Acceptance Criteria (nummeriert, testbar) · Test Plan · Rollback.

**Weggefallen:** Sign-Off-Tabelle (Git-Commit ist Sign-Off), Risks & Mitigations (nur bei nicht-trivialen Features, optional).

**Status-Lifecycle (3 Zustände):**
- `proposed` — Datei existiert, Frontmatter minimal, Scope drafted. Agent darf erzeugen.
- `in_progress` — Arbeit läuft auf Branch. Agent darf setzen.
- `done` — Branch gemerged in main, Acceptance Criteria erfüllt. **Nur Nutzer transitioniert.**
- Terminal: `rejected` oder `superseded` (→ Nachfolger-F-ID). Nur Nutzer.

**Anti-Redundanz-Regel:** Features enthalten keine Decision-Abschnitte. Warum → ADR. Was das System ist → Spec. Wie dieser Slice geliefert wird → Feature. Durchsetzung manuell (keine Invariante 10).

### 3 · Neue ADRs (5 Stück, Wave 1 only)

| Nr | Titel | Zweck |
|---|---|---|
| 0010 | `execution-harness-contract.md` | Adapter-neutraler Harness-Vertrag (Mounts, Secrets, Netz, Exit). Deckt ADR-0006 Follow-up aus Counter-Review. |
| 0011 | `runtime-audit-and-run-attempts.md` | `RunAttempt`, `AuditEvent`, `ApprovalRequest`, `BudgetLedgerEntry`, `ToolCallRecord`, `PolicyDecision`, `SandboxViolation` + Idempotency-Keys für externe Effekte. |
| 0012 | `hitl-timeout-semantics.md` | 4 Zustände (`waiting_for_approval`, `timed_out_rejected`, `stale_waiting`, `abandoned`), disjunktive Eskalations-Kriterien, kein Auto-Abandon per Default. **Enthält neuen Trigger „digest card" für Low-Risk-System-Health-Signale** (z. B. Benchmarks drift, Cost-Trend). |
| 0013 | `v1-deployment-mode.md` | v1a lokal-only (ein Prozess, SQLite + Litestream), v1b read-only Bridge, v2+ Postgres-Schwelle. Klärt SPECIFICATION.md §7 Widerspruch aus Counter-Review. |
| 0014 | `peer-adapters-and-cost-aware-routing.md` | **Amends ADR-0004**. Peer-Adapter-Stance (CC + Codex gleichwertig), `ExecutionAdapter` als einziger Kopplungspunkt (5 Verben inline, kein separater ADR-0018), **Cost-Aware-Routing** als Dispatch-Policy (RouteLLM-Stil: Konfidenz × Kosten, nicht Task-Class), `routing-pins.yaml` als manueller Override. Koppelt an ADR-0008 (Budget-Gate, Reihenfolge: Dispatch → Gate). |

**Bewusst weggefallen vs. Wave-1-Entwurf:**
- ADR-0018 (separates ExecutionAdapter-Interface) — in 0014 inline, keine separate Decision-Oberfläche bei 2 Implementierungen.
- ADR-0019 (Task-Dispatch mit Kendall-τ / Borda / Shadow-Mode) — empirisch schwach; ersetzt durch Cost-Aware-Routing in 0014.

**Bewusst verschoben (nicht jetzt):**
- ADR-0015 (Codex-Approval-Mode) — Entscheidung in 0014 als Default `approval=never`; ein eigener ADR entsteht, sobald das Gegenteil (`on-request`) nötig wird.
- ADR-0016 (Claude-Code-Harness-Profile) / ADR-0017 (Codex-CLI-Harness-Profile) — Per-Adapter-Details in 0014; eigene ADRs, wenn Detaillierung konkret wird.
- ADR-0020 (Benchmark-Ingestion) — manueller Pull in F0004 reicht für V0.2; eigener ADR bei Scheduler-Einführung.
- ADR-0021 (Task-Class-Taxonomie) — **fällt weg** (empirisch nicht gerechtfertigt, siehe Appendix A).
- ADR-0022 (Model-Inventory) — **fällt weg**; Inventory lebt als `config/dispatch/model-inventory.yaml`, keine Decision-Oberfläche.

### 4 · Spec-Patches

**Phase-A-Patches (aus Counter-Review, Wave 1):**
- §5.7: `stage`-Spalte in Kernobjekt-Tabelle + Unterabschnitt „Runtime Records" (aus ADR-0011).
- §6.2: HITL-Zustände + disjunktive Kriterien + digest-card-Trigger.
- §7: Drei Betriebsmodi sauber getrennt (aus ADR-0013).
- §8.2: Verweis auf ADR-0010.
- §8.3: `AND` → `OR` (unabhängige harte Caps) + Hinweis „Dispatch feeds cost projection" (Budget-Gate-Reihenfolge).
- §8.4: Observability-Minimum normativ (SQLite-Audit, JSONL-Runlog, JSONL-Budgetledger, `agentctl`-CLI — dokumentiert, nicht gebaut).
- §8.5: Peer-Adapter-Framing; Claude-Code- und Codex-CLI-Aufruf mit gleicher Tiefe dokumentiert.
- §10: Restore-Drill + V1-Testmatrix als Akzeptanzkriterien.
- Appendix A: Trennung Zielarchitektur / Release-Stages; `stage`-Annotationen pro Modul/Objekt.

**Option-3-Patches (minimal):**
- §3.2: „Evidence-Eingang: Benchmark-APIs (HuggingFace, LMSYS, SWE-bench, LiveBench, Aider) — nur für Awareness, nicht als Dispatch-Eingabe."
- §4.1: Leitentscheidungen-Tabelle um Peer-Adapters und Cost-Aware-Routing (→ ADR-0014) ergänzen.
- §5.3 Work: **Dispatcher als Sub-Component** nennen — Policy (Konfidenz × Kosten), nicht Execution. Verweis auf `config/dispatch/*.yaml`.
- §5.4 Execution: Neu-Framing als Peer-Adapter; `ExecutionAdapter`-Interface (5 Verben) als Interface-Form; Verweis auf ADR-0014.
- §5.5 Knowledge: `Evidence(kind=benchmark)` als explizites Subtyp (provenance envelope; kein `trust_class`, das wurde im Counter-Review bewusst entfernt).
- §5.7: `DispatchDecision` als Runtime Record (frozen pro Run). **Keine** `BenchmarkSnapshot`/`BenchmarkScore` als eigenständige Objekte — Benchmark-Daten leben als `Evidence(kind=benchmark)` mit JSONL-Blob-Referenz.
- §6.2: Neuer Fluss „Work Item → Dispatch → Run".
- §8.6 (NEU): **Agent-Auswahl** als Querschnitt. Inhalt: Cost-Aware-Routing-Policy, `routing-pins.yaml` als Override, Benchmarks-als-Awareness-only. Empirische Belegkette zu Appendix A.
- §10.1: Neue Metriken — Benchmark-Freshness, Dispatch-Override-Rate, Adapter-Mix (CC vs. Codex-Share).
- §11.1: Neue Risiken — Router-Collapse (Mitigation: Cost-Routing mit Rank-Tie-Break auf Benchmark-Rang, nicht Scalar-Score), Benchmark-Disagreement (Mitigation: Benchmarks nur Awareness, kein Auto-Dispatch).
- §11.3: CC-vs-Codex-Frage geschlossen (beide, Peer, cost-routed per ADR-0014). Neuer Eintrag: „Spezialisierung oder Cross-Review — empirisch geprüft und verworfen für V1, Evidenz in Appendix A des Plans."
- Appendix A v1: Dispatcher zunächst im `pinned`-Modus (manuelle Zuordnung); `cost-aware`-Modus aktiviert, sobald `config/dispatch/routing-pins.yaml` > 5 Einträge hat oder nach 4 Wochen Nutzung, je nachdem, was zuerst eintritt.

### 5 · Erste Feature-Files (4 Stück)

| ID | Titel | Stage | Purpose |
|---|---|---|---|
| F0001 | sqlite-schema-core-objects | v0 | 9-Objekt-SQLite-Schema aus Spec §5.7. Minimaler V0-Ausgangspunkt. |
| F0002 | work-add-cli | v0 | `work add`/`work next` CLI als einziger V0-Einstieg. Manuelle Agent-Runs, kein Workflow. |
| F0003 | cost-aware-routing-stub | v1 | Implementiert ADR-0014 als Minimal-Router: `routing-pins.yaml` als Lookup, optional Konfidenzschätzung via Haiku. Keine Kendall-τ-Mathematik. |
| F0004 | benchmark-awareness-manual-pull | v1 | `agentctl benchmarks pull` als manueller Befehl. Pullt JSON aus 3–5 Quellen (HF-Dataset, SWE-bench, LiveBench), speichert als `Evidence(kind=benchmark)`. Zeigt Übersicht „welches Modell führt wo", **beeinflusst Dispatch nicht automatisch**. |

**Rationale der 4:** F0001 + F0002 liefern V0-Entry (2 V0-Features). F0003 + F0004 decken den Dispatch- und Benchmark-Kern der Nutzer-Anforderungen (3) + (4) in lean Form. ADRs 0010–0013 bekommen in dieser Runde keine eigenen Feature-Files — sie sind Implementation-Blueprints, nicht lieferbare Feature-Slices. Entsprechende Feature-Files entstehen in späteren Wellen, wenn die Implementierung in Reichweite ist.

### 6 · AGENTS.md + spec-reviewer-Ergänzungen

**AGENTS.md — neuer kurzer Abschnitt „Feature-Disziplin":**
- Wo Features leben, Naming.
- 3-Status-Lifecycle.
- Transition-Regel: `done` nur vom Nutzer.
- Anti-Redundanz-Hinweis: Features enthalten keine Decision-Abschnitte.
- Keine Plan-Sync-Logik, keine Autogeneration (explizit zurückgestellt).

**spec-reviewer — eine neue Invariante 8:**
- (8) Alle `adr_refs`/`spec_refs` in Feature-Frontmatter resolven auf existierende Dateien bzw. Spec-Sektionen.

Invarianten 9 (Sign-Off-SHA-Check), 10 (No-Decision-Abschnitt), 11 (Autogen-Konsistenz) **fallen weg**.

### 7 · Ausführungsreihenfolge (8 Schritte, ein Commit)

1. **`docs/features/README.md`** anlegen — Index, Lifecycle-Legende, Anti-Redundanz-Cheatsheet.
2. **`docs/plans/project-plan.md`** anlegen — Milestones, Feature-Index-Tabelle (manuell gepflegt, keine Autogen), Open-Decisions-Liste.
3. **`config/dispatch/model-inventory.yaml` + `routing-pins.yaml`** anlegen — erstere mit 5-6 bekannten Modellen (Opus 4.7, Sonnet 4.6, Haiku 4.5, GPT-5.4, GPT-5 mini, Gemini 3.1 Pro), letztere leer.
4. **5 ADRs schreiben** (0010–0014). ADR-0014 markiert explizit „amends ADR-0004".
5. **Spec-Patches anwenden** (Phase-A-Patches + Option-3-Minimal-Patches aus §4).
6. **4 Feature-Files anlegen** (F0001–F0004) mit Status `proposed`.
7. **AGENTS.md** um „Feature-Disziplin" erweitern. **spec-reviewer.md** um Invariante 8 erweitern. **GLOSSARY.md** um neue Begriffe erweitern (`ExecutionAdapter`, `HarnessProfile`, `DispatchDecision`, `Cost-Aware Routing`, `Benchmark Evidence`, `Routing-Pin`, `Benchmark Awareness`). **CHANGELOG.md** `[0.2.0-draft] — 2026-04-24`.
8. **spec-reviewer-Lauf** (alle 8 Invarianten) + **Commit + Push** als `docs: v0.2.0-draft — option 3 peer adapters, cost-aware routing, feature-files, project-plan`.

### 8 · Bewusst VERSCHOBEN

- **ADRs 0015–0017 (Per-Adapter-Profile), 0020 (Benchmark-Scheduler), 0021 (Task-Class-Taxonomie → verworfen), 0022 (Model-Inventory → verworfen).**
- **Plan-Sync-Skill** und Autogeneration der Feature-Index-Tabelle.
- **Kendall-τ-Disagreement-Detection, Borda-Rank-Composite, Shadow-Mode-3-Stufen-Staffelung** (empirisch nicht gerechtfertigt; siehe Appendix A).
- **Cross-Model-Review-Loop, Ensemble-Dispatch, Debate-Protokolle** (empirisch nicht gerechtfertigt).
- **Per-Stage-Plan-Files** (v0/v1/v2/v3 je eigene Datei) — entstehen mit Substanz.
- **Feature-Files F0003–F0008 als ADR-Duplikate** — ADRs tragen diese Inhalte selbst.
- **Sign-Off-Frontmatter-Bürokratie** (signed_off_at/commit) — Git-Log ist Quelle.
- **Transition-Permissions-Matrix** — einzige harte Regel: `done` nur vom Nutzer.
- **Standards-Binding-Compiler** (v3-Thema, wie im Counter-Review Befund 14).
- **Dedicated Event-Broker, Multi-Device-Sync, Compliance-Audit-Trennung.**

## Critical Files (repo-relativ)

**Neu anzulegen:**
- `docs/features/README.md`
- `docs/features/F0001-sqlite-schema-core-objects.md`
- `docs/features/F0002-work-add-cli.md`
- `docs/features/F0003-cost-aware-routing-stub.md`
- `docs/features/F0004-benchmark-awareness-manual-pull.md`
- `docs/plans/project-plan.md`
- `docs/decisions/0010-execution-harness-contract.md`
- `docs/decisions/0011-runtime-audit-and-run-attempts.md`
- `docs/decisions/0012-hitl-timeout-semantics.md`
- `docs/decisions/0013-v1-deployment-mode.md`
- `docs/decisions/0014-peer-adapters-and-cost-aware-routing.md`
- `config/dispatch/model-inventory.yaml`
- `config/dispatch/routing-pins.yaml`

**Zu ändern:**
- `docs/spec/SPECIFICATION.md` — Spec-Patches aus §4.
- `AGENTS.md` — neuer kurzer Abschnitt „Feature-Disziplin".
- `.claude/agents/spec-reviewer.md` — Invariante 8.
- `CHANGELOG.md` — `[0.2.0-draft]`-Eintrag.
- `GLOSSARY.md` — neue Begriffe.

**Wiederzuverwenden (existierend):**
- `docs/research/13-cost.md` — Preisanker; Basis für `model-inventory.yaml` und `config/dispatch/*.yaml`.
- `docs/research/05-agent-patterns.md` — „Routing"-Pattern; Literaturverweis in ADR-0014.
- `docs/research/04-agent-orchestration-libs.md` — Pydantic AI als LLM-Wrapper.
- `docs/research/01-claude-code.md`, `docs/research/02-codex-cli.md` — Adapter-Spezifika; Basis für ADR-0014.
- `docs/reviews/2026-04-23-counter-review.md` — dokumentiert Phase-A-Absicht.

## Verification

Documentation-Only — strukturelle, nicht Runtime-Verifikation:

1. **Strukturcheck (bash):**
   - `docs/features/FNNNN-*.md` zählt 4 Dateien.
   - `docs/decisions/NNNN-*.md` zählt 14 Dateien (9 alt + 5 neu).
   - `docs/plans/project-plan.md` existiert.
   - `config/dispatch/{model-inventory,routing-pins}.yaml` existieren.
2. **ADR-Schema-Check:** `spec-reviewer`-Invariante 3 (MADR-Pflichtfelder) läuft durch.
3. **Feature-Referenz-Check:** `spec-reviewer`-Invariante 8 läuft durch.
4. **Spec-Konsistenz-Check:** `spec-reviewer`-Invarianten 1–7 laufen grün.
5. **ADR-Supersession-Check (manuell):** ADR-0014 enthält expliziten „Amends ADR-0004"-Hinweis.
6. **Glossar-Check (manuell):** Alle neuen Termini haben GLOSSARY-Eintrag; keine Verwechslung „Dispatcher" vs. „Agent-Auswahl" (letzteres ist der §8.6-Begriff für das Konzept, ersterer der Komponentenname).
7. **CHANGELOG-Check:** Eintrag `[0.2.0-draft] — 2026-04-24` vorhanden.
8. **Push-Gate:** Nach Commit `git push` erfolgreich, `git log @{u}..` danach leer.

## Offene Entscheidungen (vor Execution)

Diese Punkte sind verteidigbare Defaults im Plan; Nutzer kann ändern:

1. **Benchmark-Quellen für F0004:** Vorschlag HuggingFace Open LLM Leaderboard + SWE-bench Verified + LiveBench + Aider polyglot + Chatbot Arena (community API). Nutzer kann Set verkleinern/erweitern.
2. **`model-inventory.yaml`-Initialbefüllung:** Vorschlag Opus 4.7 / Sonnet 4.6 / Haiku 4.5 / GPT-5.4 / GPT-5 mini / Gemini 3.1 Pro mit aktuellen Preisen aus `docs/research/13-cost.md`. Nutzer kann Set anpassen.
3. **Feature-Lifecycle 3 Zustände:** Reicht für Solo-Betrieb. Nutzer kann später erweitern, wenn Review/QA-Gate nötig wird.

Nicht-blockierend. Default-Vorschläge sind verteidigbar.

## Risk-Register (kondensiert)

- **Cost-Aware-Routing zu dünn für realen Nutzen:** Router-Lookup ohne Konfidenzschätzung ist trivial. Mitigation: Optional Konfidenzschätzung via Haiku-Call (F0003 als Stub); scharfere Variante in v2.
- **Benchmark-Awareness wird zu Benchmark-Obsession:** Nutzer verbringt Zeit mit Benchmark-Vergleichen, statt Arbeit zu machen. Mitigation: Benchmarks sind explizit Awareness, nicht Dispatch; kein Scheduler, manuelles Pullen.
- **ADR-0014 überlädt:** Kombiniert Peer-Adapters + ExecutionAdapter-Interface + Cost-Aware-Routing in einem ADR. Mitigation: Abschnitte klar trennen; bei Wachstum als getrennte ADRs extrahierbar (0014 supersedes durch 0014a/b/c).
- **Feature-File-Pattern wird nicht genutzt:** Nutzer vergisst Features anzulegen, macht stattdessen ADRs. Mitigation: `AGENTS.md` „Feature-Disziplin" ist ultra-kurz; bei Nicht-Nutzung nach 4 Wochen ist das Pattern ein Fehlversuch und darf verworfen werden.

---

## Appendix A — Empirische Basis für Symbiose-Design-Entscheidung

Der Nutzer hat „Symbiose CC ↔ Codex" mit zwei möglichen Lesarten benannt: (a) Modell-Spezialisierung, (b) Cross-Model-Review. Er bat ausdrücklich um empirische Prüfung seiner Annahmen. Dieser Appendix dokumentiert die Befunde.

### Claim A — Modell-Spezialisierung: teilweise wahr, aber marginal

**Benchmark-Evidenz 2026:**
- SWE-bench Verified (Coding): Opus 4.7 = **87,6 %**; Gemini 3.1 Pro = 80,6 %; GPT-5.4 = ~80,0 %. **Abstand 7,6 pp** — einziges Feld mit verteidigbarem Delta.
- GPQA Diamond (Reasoning): Gemini 3.1 Pro = **94,3 %**; Opus 4.7 = 94,2 %; GPT-5.4 = 92,0 %. Abstand 2,3 pp — Rauschen.
- Humanity's Last Exam: Gemini 3.1 Pro = 46,44 %; GPT-5.4 = 44,32 %. Abstand 2,1 pp.
- MMLU-Pro, ARC-AGI: saturiert bei 85–90 %, keine Differenzierung.

**Stanford AI Index April 2026:** „capability differentiation at the model layer is collapsing" — Top 4 Modelle liegen bei < 25 Arena-ELO-Punkten Spread (< 1,25 % Range).

**Kritisches Finding:** Harness-Qualität (Claude Code vs. Codex CLI) schwankt am selben Modell **bis ±16 pp** — größer als der Inter-Modell-Abstand. Routing nach Modell-Klasse ist damit **Kostenoptimierung, keine Kapazitätsoptimierung**.

**Verdikt:** Spezialisierung real, aber schmal. Nur Coding hat verteidigbares 7,6-pp-Delta. Im Routing-Kontext überwiegt die Harness-Varianz.

### Claim B — Cross-Model-Review: empirisch falsch

- **Self-Preference-Bias:** LLMs bewerten eigene Stile systematisch höher (arXiv 2410.21819).
- **Position-Bias:** GPT-4 zeigt **40 % Position-Bias**; Output-Reihenfolge-Swap wirft Judgment um >10 % um (IJCNLP 2025).
- **Self-MoA schlägt Mixed-MoA:** Mehrfach-Sampling desselben Modells ist **6,6 % besser** als Mischen verschiedener Modelle auf AlpacaEval 2.0 (arXiv 2502.00674).
- **Produktions-Praxis:** Cursor, Replit Agent 4, Sourcegraph Cody verwenden **kein automatisches Cross-Model-Review**. User wählen manuell.
- **Multi-Agent-Debate (2025):** „often fails to outperform single-agent strategies" (A-HMAD-Paper, Nov 2025).

**Verdikt:** Cross-Model-Review-Loops sind durch Judge-Bias kontaminiert. Self-Consistency im selben Modell dominiert.

### Frontier-Modell-Konvergenz

Artificial Analysis Intelligence Index April 2026: Opus 4.7, GPT-5.4, Gemini 3.1 Pro alle mit Score **57** (tied). Arena-ELO-Spread Top 6 < 20 Punkte = < 1 % effektive Distanz. Modelle erreichen denselben Score über **unterschiedliche Wege** — kein Modell dominiert universal.

### Was empirisch funktioniert

1. **Cost-Aware-Routing (RouteLLM-Stil):** 85 % Kostenreduktion bei 95 % Qualitätserhalt auf MT Bench. Route nach Konfidenz + Kosten, nicht Task-Class.
2. **Self-Consistency (Majority-Vote auf 2–3 Samples desselben Modells):** Schlägt Cross-Model-Ensembles bei < 1/3 der Kosten.
3. **Harness-Qualität verbessern** hat größeren Hebel als Modell-Wahl.

### Konsequenz für V1-Design

- **Kein Task-Class-Specializer.** ADR-0019 / ADR-0021 fallen weg.
- **Kein Cross-Model-Review.** Keine LLM-als-Judge-Loops.
- **Cost-Aware-Router** (Konfidenz × Kosten) als Minimalform (ADR-0014).
- **Benchmarks als Awareness, nicht als Dispatch-Eingabe** (F0004). Nutzer sieht, welches Modell führt; System routet nicht automatisch nach Benchmark-Rank.
- **Harness-Qualität** (ADR-0010 Execution Harness Contract) ist der eigentliche Qualitätshebel.

### Quellen

1. SWE-bench Leaderboard April 2026 — https://www.marc0.dev/en/leaderboard (Tier 2)
2. Artificial Analysis Intelligence Index April 2026 — https://smartchunks.com/artificial-analysis-intelligence-index-april-2026-explained/ (Tier 2)
3. Mixture-of-Agents Paper — arXiv 2406.04692 (Tier 1)
4. Self-MoA vs. Mixed-MoA — arXiv 2502.00674 (Tier 1)
5. Self-Preference Bias — arXiv 2410.21819 (Tier 1)
6. Position Bias — ACL IJCNLP 2025 (Tier 1)
7. RouteLLM — https://www.lmsys.org/blog/2024-07-01-routellm/ (Tier 1)
8. Stanford AI Index 2026 — https://hai.stanford.edu/ai-index/2026-ai-index-report/ (Tier 1)
9. Arena-ELO-Rankings April 2026 — https://aidevdayindia.org/blogs/lmsys-chatbot-arena-current-rankings/ (Tier 2)
10. Claude Code vs. Codex CLI Harness — https://thoughts.jock.pl/p/ai-coding-harness-agents-2026 (Tier 2)
11. Aider polyglot leaderboard — https://aider.chat/docs/leaderboards/ (Tier 2)
12. Multi-Agent-Debate — arXiv 2305.14325, A-HMAD Nov 2025 (Tier 1)
