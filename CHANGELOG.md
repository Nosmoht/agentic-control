# Changelog

Alle signifikanten Änderungen an der Spezifikation werden hier dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versionen folgen [Semantic Versioning](https://semver.org/) für Specs
(Major = Breaking Change im Datenmodell oder in Modul-Grenzen,
Minor = additiv, Patch = Klarstellungen/Fixes).

## [0.3.5-draft] — 2026-04-29

Pre-Implementation-Patch. Schließt drei R3-Lücken (Issue Clarity per
`~/.claude/CLAUDE.md`), die F0001 und F0002 daran hinderten, als
„ready to implement" zu gelten. Nach diesem Patch sind beide v0-
Features R1–R4-konform.

### Decided

- **ADR-0019 — Primary-Key-Strategie: UUIDv7 (RFC 9562)** (Status
  `accepted`). Native Pydantic-v2- und SQLAlchemy-Unterstützung
  beidseits SQLite und Postgres; sauberer ADR-0013-Migrations-Pfad
  (PG 18 generiert UUIDv7 nativ); CLI-Komfort via Präfix-Resolution
  wie `git`/`docker`/`gh`. Backport via `uuid-utils` bis Python-3.14-
  Upgrade, dann trivialer Import-Swap auf stdlib `uuid.uuid7`.
  Alternative ULID kostet überall einen Custom-Decorator (drei
  Drift-Punkte: Generator + SQL-Spalte + JSON-Schema). INTEGER-
  ROWIDs sind nicht stabil über `VACUUM`/Sync.
- **ADR-0020 — Migrations-Tool: Alembic ohne `--autogenerate`**
  (Status `accepted`). Einziges Tool mit identischer Migrations-
  Skript-Syntax unter SQLite und Postgres (ADR-0013-Pfad). SQLAlchemy
  wird ausschließlich als Connection-/Type-Layer verwendet (kein ORM,
  per Linter-Regel erzwungen), damit ADR-0018 Pydantic-First erhalten
  bleibt. `--autogenerate` ist verboten, weil es eine dritte Schema-
  Quelle erzeugen würde (Pydantic + SQLAlchemy + Migration-File).

### Changed

- **`docs/spec/SPECIFICATION.md` §5.7** trägt jetzt einen normativen
  Block „Spaltentypen": UUIDv7 für IDs/FKs, ISO-8601 UTC für
  Timestamps, CHECK-Constraints für State-Enums; `Observation.
  classification` explizit als Freitext in v0. `Decision`-Pflichtfeld
  `created_at` ergänzt.
- **`docs/spec/SPECIFICATION.md` §6.1** ergänzt Decision-Lifecycle:
  `proposed → accepted → superseded | rejected` (MADR-konform,
  forward-only).
- **`docs/spec/SPECIFICATION.md` §9** ADR-Tabelle trägt 0019 und 0020
  als `accepted`.
- **`docs/features/F0001-sqlite-schema-core-objects.md`** vollständig
  überarbeitet: Package-Struktur (`src/agentic_control/`), UUIDv7-
  Spaltentyp mit `LENGTH(id)=36`-CHECK, Alembic-Setup, explizite
  State-Enums in CHECK-Constraints, Pydantic↔Schema-Drift-CI-Check,
  Connection-Layer-Linter-Regel. ACs von 6 auf 10 erweitert.
- **`docs/features/F0002-work-add-cli.md`** vollständig überarbeitet:
  Hybrid-Multiline-Input für `--decision` (Editor + `--from-file` +
  stdin + drei Einzelflags) mit Draft-Recovery in `$XDG_STATE_HOME`;
  explizite Lifecycle-Transition-Matrix aus Spec §6.1; Präfix-
  Resolution für UUIDv7-Argumente. ACs von 7 auf 11 erweitert.
- **`docs/plans/project-plan.md`** Open-Decisions-Liste um die zwei
  geschlossenen Punkte 7 und 8 (Primary-Key, Migrations-Tool)
  erweitert; Stand-Datum auf 2026-04-29.

### Method

Vor dem Patch hat die Pre-Implementation-Triage die R3-Lücken in
F0001/F0002 identifiziert (ID-Strategie, Migrations-Tool,
Decision-Lifecycle, Multiline-Input, Observation-Classification,
Package-Name, Transition-Matrix). Für die zwei nicht-trivialen
Entscheidungen (ID-Strategie, Multiline-Input) liefen parallele Web-
Recherchen mit Tier-1/2-Quellen. Empfehlungen wurden mit Begründung
und Trade-off-Diskussion vorgelegt; Nutzer hat beide bestätigt. Die
restlichen fünf Lücken wurden mit dokumentierten Defaults geschlossen
(`agentic_control` als Package-Name, MADR-konformer Decision-
Lifecycle, Observation-Classification als Freitext in v0,
Transition-Matrix abgeleitet aus Spec §6.1).

## [0.3.4-draft] — 2026-04-27

Entscheidungs-Patch. Schließt die zwei in V0.3.3-draft als
`proposed` geöffneten Pre-Implementation-Decisions auf Basis
empirischer Web-Verifikation und adversarieller Review der
Empfehlungen.

### Decided

- **ADR-0017 — Python ≥ 3.13 mit `uv`** (Status `accepted`).
  Strukturelle Begründung statt Treiber-Abwägung: DBOS Go-SDK ist
  Postgres-only (verifiziert in dbos-transact-golang v0.13.0,
  2026-04-22) und kollidiert mit ADR-0003 (SQLite-Substrat); kein
  Pydantic-AI-Äquivalent in Go, kollidiert mit ADR-0004; Eval-
  Stack (Arize Phoenix, Pydantic Logfire) hat keine Go-SDKs.
  Anerkanntes Risiko Transitive-Dependency-Rot ist mitigiert via
  `uv.lock`-Frozen-Snapshots + quartalsweisem Restore-Drill mit
  Test-Boot des Daemons (Spec §10.4 + §7.1).
- **ADR-0018 — Pydantic-Models als kanonische Single-Source,
  JSON-Schema-Export** (Status `accepted`). Statt 15 handgepflegter
  Standalone-JSON-Schema-Files (Empfehlung der `proposed`-Fassung
  unter Sprach-Neutralität-Argument): Pydantic-Models in
  `src/<package>/contracts/` sind die Quelle, `schemas/`-Files sind
  Build-Artefakte via `model_json_schema()`. Vermeidet die im
  Adversarial-Review benannte Drei-Quellen-Drift (Markdown +
  JSON Schema + Pydantic). ADR-0016 Write Contract validiert
  Konfig-YAMLs gegen die exportierten Schemas. Protobuf/OpenAPI
  bleiben defer bis v2+.

### Changed

- **`docs/spec/SPECIFICATION.md` §7.1** trägt jetzt eine
  Implementierungs-Zeile (Python ≥ 3.13 mit `uv`, `dbos-py`,
  Pydantic AI, Pydantic-Contracts mit JSON-Schema-Export). Die
  Restore-Drill-Beschreibung erwähnt explizit den Test-Boot-Schritt
  als Risk-Mitigation für Dependency-Rot.
- **`docs/spec/SPECIFICATION.md` §9 ADR-Tabelle** trägt für 0017
  und 0018 Status `accepted` mit der gewählten Variante als Klammer-
  Zusatz.
- **`docs/plans/project-plan.md` Open Decisions** Punkte 5 und 6
  sind jetzt geschlossen mit Verweis auf die getroffene Wahl und
  ihre Begründung. Liste bleibt sechs Einträge lang als Lese-
  Geschichte; künftige offene Entscheidungen wachsen darüber hinaus.

### Method

Vor der Festlegung wurden zwei parallele Sub-Agenten beauftragt:
(1) empirische Verifikation der Stack-Annahmen via Web-Research
mit Tier-1/Tier-2-Quellen, (2) adversarielle Review der ursprüng-
lichen Empfehlung. Der DBOS-Go-Postgres-only-Befund war der
strukturelle Showstopper; der Drei-Quellen-Drift-Befund hat die
Schema-First-Empfehlung von Standalone-JSON auf Pydantic-Single-
Source verschoben.

## [0.3.3-draft] — 2026-04-27

Pre-Implementation-Decision-Patch. Zwei neue ADRs als `proposed`
(noch keine Festlegung), die vor v0-Implementierungsstart entschieden
werden müssen. Beide Entscheidungen waren bisher implizit oder
fehlend; dieses Release macht sie explizit und liefert die
Optionsräume zur Auswahl.

### Added

- **ADR-0017 — Implementation Language for v0/v1a** (`proposed`).
  Vier Optionen mit ehrlichen Trade-offs: Python (LLM-SDK-Reichweite),
  Go (Ops-Minimum + Single-Static-Binary), TypeScript (Mitte), Rust
  (überdimensioniert). Empfehlung Python unter Vorbehalt der
  Treiber-Priorisierung. Schließt die bisherige implizite
  Python-Annahme aus F0002 und Research-Briefs als unbegründet.
- **ADR-0018 — Schema-First with JSON Schema for Data Boundaries**
  (`proposed`). Empfehlung JSON Schema Draft 2020-12 als kanonische
  Form für 7 Runtime-Records (ADR-0011), 3 Domain-Objekte (F0008)
  und 5 Konfig-YAMLs (ADR-0016). Sprach-neutral; Code-Gen pro
  Sprache. Protobuf und OpenAPI explizit defer bis v2+ (keine
  RPC-/HTTP-Boundary in v1a). Validierung wird in den
  ADR-0016-Write-Pfad eingehängt vor Lock und Conflict-Check.

### Changed

- **`docs/spec/SPECIFICATION.md` §9 ADR-Tabelle** um die zwei neuen
  Einträge erweitert; beide tragen Status `proposed`.
- **`docs/plans/project-plan.md` Open Decisions** um die zwei neuen
  Entscheidungspunkte (5: Sprache, 6: Schema-First-Werkzeug)
  erweitert. Beide blockieren den v0-Implementierungsstart.

## [0.3.2-draft] — 2026-04-26

Konsistenz-Patch nach **fünftem** Codex-Follow-up-Review
(`docs/reviews/2026-04-26-followup-review-4.md`). Schließt den letzten
Hoch-Befund (F0006 AC 1 stale gegen F0008-Abhängigkeit), die zwei
verbliebenen Teilbefunde aus dem vierten Review (N8 Index-Drift, N10
`threshold_kind`-Enum) und vier mittlere Konventionsbrüche/Lücken.
Keine neuen Architekturentscheidungen — alles Klarstellungen an
V0.3.1-Artefakten.

### Fixed

- **F0006 Acceptance Criterion 1.** „Migration läuft auf einer
  F0001-DB" → „auf einer DB mit erfolgreich ausgeführten F0001- **und**
  F0008-Migrationen". Plus Negative-Test, dass die Migration ohne
  F0008 mit klarem Fehler abbricht. Damit ist der einzige Hoch-Befund
  des fünften Reviews geschlossen.
- **`docs/features/README.md` Feature-Index F0003** trägt jetzt
  `ADR-0014, ADR-0016` (vorher nur `ADR-0014`); deckungsgleich mit
  Frontmatter und Project-Plan. Schließt N8-Restpunkt aus dem vierten
  Review.

### Changed

- **F0006 AC 12** ergänzt das Schema-Detail für
  `PolicyDecision(policy=tool_risk_match)`: `subject_ref` zeigt auf
  `tool_call_record:<id>`, `output`-JSON enthält
  `{matched_pattern, risk, approval, default_hit}`. Damit ist der
  Datenvertrag zwischen ADR-0015 (Match-Details), F0006 (Persist) und
  F0007 (Drift-Audit) geschlossen.
- **ADR-0011 Runtime-Records-Tabelle** trägt die `tool_risk_match`-
  Schema-Details als ergänzenden Vertrag in der `PolicyDecision`-
  Zeile.
- **SPECIFICATION.md §5.7** PolicyDecision-Zeile listet
  `Tool-Risk-Match` zusätzlich zu den bisherigen vier Policy-Typen,
  mit Verweis auf ADR-0011 für Schema-Details.
- **F0007 AC 4** definiert `threshold_kind ∈ {"default_hit_pct",
  "unknown_tool_count"}` als CHECK-Constraint mit exakt zwei Werten;
  `default_hit_pct` braucht ≥ 20 Tool-Calls als Mindest-Denominator,
  `unknown_tool_count` greift ab > 3 unbekannten Tool-Namen. Schließt
  N10 aus dem vierten Review.
- **F0008 ACs erweitert** um `artifact.state`-CHECK-Test (AC 5),
  Negative-Tests für `evidence.subject_ref` (AC 7: ungültige Präfixe,
  fehlendes Trennzeichen, Eigenentscheidung zur Anwendungsebene-
  Validierung), Renumbering auf 1–9.
- **F0008 Rollback** als Eigenentscheidung **Forward-Only** für
  v0+v1a markiert; Down-Migrations-Konvention für v2+ offen, eigener
  ADR bei Bedarf. Frühere Erwähnung eines `_down.sql`-Pendants
  entfernt; Rollback erfolgt über Git-Restore + manuelles `DROP
  TABLE`.
- **`docs/features/README.md` Frontmatter-Konvention** erweitert um
  optionales `depends_on`-Array. Schließt den Konventionsbruch, dass
  F0006 und F0007 das Feld bereits nutzten, der README aber „Keine
  weiteren Felder" sagte.
- **`docs/plans/project-plan.md`** neuer Abschnitt **„Open v1a-Exit
  Implementation Gaps"** listet die ADRs, für die noch
  Implementierungs-Feature-Files fehlen (ADR-0010 Harness inkl.
  Pattern-Matcher, ADR-0012 Inbox, ADR-0013 Restore-Drill). Damit
  ist die alte „Pattern-Matcher als Liefer-Slice"-Frage explizit
  verortet.
- **SPECIFICATION.md Frontmatter** `version: 0.3.1-draft → 0.3.2-draft`.
- **AGENTS.md, README.md, spec-reviewer.md, spec-navigator/SKILL.md**
  Stand auf V0.3.2-draft.

### Added

- **`docs/reviews/_prompts/2026-04-26-fifth-review-prompt.md`** als
  wiederverwendbares Template für künftige Codex-Follow-up-Reviews
  eingecheckt. Bisher untracked.

## [0.3.1-draft] — 2026-04-26

Konsistenz-Patch nach viertem Codex-Follow-up-Review
(`docs/reviews/2026-04-26-followup-review-3.md`). Adressiert die drei
**Hoch**-Befunde an F0006 (fehlender Domain-Schema-Anker, ungleichmäßige
ACs, falsche UNIQUE-Semantik) plus sieben mittlere Drift-Befunde an
F0007/ADR-0016/Spec/Plan. Keine neuen Architekturentscheidungen — alle
Änderungen sind Korrekturen an V0.3.0-Artefakten.

### Added

- **F0008 V1 Domain Schema (Run, Artifact, Evidence)** als eigener
  Liefer-Slice (Stage v1a). Schließt die Lücke, dass F0006 einen FK
  auf `run` voraussetzt, F0001 aber nur das v0-Schema liefert.
  Plan-Reihenfolge ist jetzt F0001 → F0008 → F0006 → [F0003, F0004,
  F0007] → F0005. Adressiert Counter-Counter-Counter-Review-Befund 1
  (Hoch).

### Changed

- **F0006 Acceptance Criterion 3** korrigiert: `tool_call_record` hat
  zwei UNIQUE-Constraints — `(run_attempt_id, tool_call_ordinal)` für
  Reihenfolge und `(run_attempt_id, idempotency_key)` für die Pre-
  Send-Check-Semantik aus ADR-0011. Die alte AC sicherte nur Ordinals
  und unterlief den Idempotenzanker. Adressiert Befund 3 (Hoch).
- **F0006 Scope** verweist explizit auf F0008 als FK-Anker-Voraussetzung;
  `depends_on: [F0001, F0008]` in Frontmatter.
- **F0006 Acceptance Criteria 11–13 ergänzt** für `DispatchDecision`
  (post-gate-final, UNIQUE pro RunAttempt), `PolicyDecision`
  (`policy`-Tag-Differenzierung mit fünf Klassen), `SandboxViolation`
  (Insert + Stub-Alert-Hook). Damit decken die ACs jetzt alle acht
  Runtime-Record-Typen ab. Adressiert Befund 2 (Hoch).
- **F0007 Scope** umgestellt: liest primär
  `PolicyDecision(tool_risk_match)`-Records aus F0006 (historische
  Match-Entscheidung), Re-Match nur als Fallback für Alt-Daten. Damit
  beseitigt F0007 zugleich seine Pattern-Matcher-Abhängigkeit (Out of
  Scope umformuliert). Adressiert Befunde 4 (Mittel-Hoch) und 5
  (Mittel).
- **F0007 `tools propose`-Einfügeposition** spezifiziert: spezifische
  Patterns vor Catch-all, neue Catch-alls am Ende, Dry-Run-Match
  nach jedem Insert. Adressiert Befund 6 (Mittel).
- **F0007 Acceptance Criterion 4** konkretisiert: Digest-Card-ID =
  `sha256(period_start + sorted(unmatched_tool_names) +
  threshold_kind)`; Mindest-Denominator ≥ 20 Tool-Calls für
  Prozent-Schwelle. Adressiert Befund 10 (Niedrig-Mittel).
- **F0007 Frontmatter `adr_refs`** ergänzt um ADR-0016 (vorher
  fehlend, obwohl `tools propose` darüber schreibt). Index und
  Project-Plan ziehen nach. `depends_on: [F0006]` ergänzt.
  Adressiert Befund 8 (Mittel).
- **F0003 Frontmatter `adr_refs`** ergänzt um ADR-0016; `dispatch
  pin` Beschreibung referenziert den Schreibvertrag explizit.
- **ADR-0016 Garantie 3 (Optimistic Conflict Check)** erweitert:
  zusätzlich zum Versions-/Updated-Vergleich wird der Inhalts-Hash
  (`sha256(file_content)`) als `before_hash` beim initialen Read
  gespeichert und vor `rename` erneut geprüft. Manuelle Editor-Edits
  ohne Versions-Bump werden damit zuverlässig als
  `ConflictDetected` erkannt. Adressiert Befund 7 (Mittel).
- **SPECIFICATION.md §8.5** ADR-Reservierung korrigiert: Harness-
  Profile-ADRs sind jetzt 0017 / 0018 (ADR-0016 ist an Config-Write-
  Vertrag vergeben).
- **SPECIFICATION.md Appendix A v1a** erweitert: F0005, F0006, F0007,
  F0008 und ADR-0016 jetzt namentlich im v1a-Block; explizite
  Reihenfolge F0001 → F0008 → F0006 → [F0003, F0004, F0007] → F0005.
  Adressiert Befund 9 (Mittel).
- **SPECIFICATION.md Frontmatter** `version: 0.3.0-draft → 0.3.1-draft`.
- **`docs/features/README.md` und `docs/plans/project-plan.md`**
  Feature-Index und Dependency-Graph um F0008 erweitert; F0007
  `adr_refs` aktualisiert; v1a-Pfad zeigt F0001 → F0008 → F0006 → ...
- **AGENTS.md, README.md, spec-reviewer.md, spec-navigator/SKILL.md**
  Stand auf V0.3.1-draft.

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
