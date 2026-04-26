---
title: Viertes Follow-up-System-Review — Personal Agentic Control System V0.3.0-draft
date: 2026-04-26
status: draft
reviewer: Codex
scope: V0.2.4-draft und V0.3.0-draft gegen das dritte Follow-up-Review vom 2026-04-26
responds_to:
  - docs/reviews/2026-04-23-critical-system-review.md
  - docs/reviews/2026-04-24-followup-review.md
  - docs/reviews/2026-04-26-followup-review-2.md
  - docs/reviews/2026-04-23-counter-review.md
---

# Viertes Follow-up-System-Review — Personal Agentic Control System V0.3.0-draft

## Executive Summary

V0.2.4 und V0.3.0 sind substanzielle Reparatur-Patches. V0.2.4 korrigiert
die zwei Spec-Drifts aus §10.4 und §8.5 direkt: das Crash-Kriterium ist jetzt
in drei ADR-0011-Effektklassen gesplittet (`docs/spec/SPECIFICATION.md:628-640`),
und §8.5 sagt nur noch "vertraglich dokumentiert", während die Default-Nutzung
aus Inventory/§8.6 folgt (`docs/spec/SPECIFICATION.md:477-482`). V0.3.0 liefert
mit ADR-0016, F0006 und F0007 echte neue Artefakte statt nur Textpolitur; der
Changelog nennt sie ausdrücklich "substantielle Erweiterungen" für v1a
(`CHANGELOG.md:11-15`, `:19-36`).

Kurzurteil pro Achse:

- **A · 8 neue Befunde aus 04-26:** **6 geschlossen, 2 teilweise.** Voll
  geschlossen sind N1, N2, N4, N5, N6 und N7. Teilweise bleiben N3
  (Config-Write-Vertrag) und N8 (Tool-Risk-Drift-Detection), weil die
  neuen Artefakte zwar richtig sind, aber noch Vertragskanten offenlassen.
- **B · 3 Restbefunde aus 04-24:** **1 geschlossen, 2 teilweise.** Die
  Meta-Doku ist nachgezogen (`AGENTS.md:12`, `.claude/agents/spec-reviewer.md:45-50`),
  aber die Runtime-Basis ist durch F0006 noch nicht vollständig lieferbar und
  die 3-pp-Heuristik bleibt außerhalb von Appendix A verteidigt.
- **C · Neue Widersprüche:** Es gibt keine neue kritische Zielarchitektur-
  Blockade, aber acht neue mittlere bis hohe Befunde an den Übergängen
  F0006/F0007/ADR-0016.
- **D · F0006:** Der Slice ist notwendig und richtig platziert, aber noch
  nicht startklar, weil er `run` referenziert, obwohl F0001 `Run` explizit
  aus dem V0-Schema ausschließt (`docs/features/F0001-sqlite-schema-core-objects.md:31-36`;
  `docs/features/F0006-runtime-records-and-reconcile-cli.md:28-36`).
- **E · F0007:** Als Feature ist F0007 der richtige Ort für Drift-Detection,
  aber die Messbasis ist instabil, solange gematchte Tool-Risk-Entscheidungen
  nicht historisch aus `PolicyDecision` gelesen werden.
- **F · ADR-0016:** Die vier Garantien sind für n=1 auf Linux/macOS praktisch,
  aber der Optimistic Check erkennt manuelle Editor-Änderungen ohne
  `version`-/`updated`-Bump nicht zuverlässig (`docs/decisions/0016-config-write-contract.md:69-75`).
- **G · Lieferbarkeit:** Der v0-Pfad bleibt sauber. Der v1a-Pfad ist deutlich
  besser, aber noch nicht so klar, dass Implementierung ohne weiteren Spec-/
  Feature-Patch starten sollte.

Mein Kernurteil: V0.3.0 macht die Spezifikation implementierungsnäher als
V0.2.3. Gleichzeitig verschiebt sich die Hauptrisikozone von "fehlende
Dokumente" zu "neue Dokumente passen noch nicht ganz aneinander".

## Quellenbasis

Gelesen wurden ausschließlich lokale Dokumente, kein externer Web-Check:

- die drei Codex-Reviews und die Claude-Counter-Review
  (`docs/reviews/2026-04-23-critical-system-review.md:20-35`,
  `docs/reviews/2026-04-24-followup-review.md:44-89`,
  `docs/reviews/2026-04-26-followup-review-2.md:33-77`,
  `docs/reviews/2026-04-23-counter-review.md:27-38`)
- `CHANGELOG.md` für `[0.2.4-draft]` und `[0.3.0-draft]`
  (`CHANGELOG.md:9-75`, `:76-116`)
- ADR-0011, ADR-0014, ADR-0015, ADR-0016
  (`docs/decisions/0011-runtime-audit-and-run-attempts.md:41-147`,
  `docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:52-210`,
  `docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:71-171`,
  `docs/decisions/0016-config-write-contract.md:57-148`)
- Feature-Dateien F0001 bis F0007, Feature-Index und Project Plan
  (`docs/features/README.md:77-85`, `docs/plans/project-plan.md:30-72`)
- Dispatch- und Execution-Configs
  (`config/dispatch/model-inventory.yaml:19-136`,
  `config/dispatch/routing-pins.yaml:25-27`,
  `config/dispatch/benchmark-task-mapping.yaml:16-43`,
  `config/execution/tool-risk-inventory.yaml:22-143`)
- `SPECIFICATION.md` §6.2, §8.5, §9, §10.4, Frontmatter und Appendix A
  (`docs/spec/SPECIFICATION.md:1-7`, `:316-380`, `:477-587`, `:622-647`,
  `:701-750`)
- `GLOSSARY.md`, `AGENTS.md`, `.claude/agents/spec-reviewer.md`,
  `.claude/skills/spec-navigator/SKILL.md`
  (`GLOSSARY.md:217-237`, `AGENTS.md:6-13`,
  `.claude/agents/spec-reviewer.md:41-50`,
  `.claude/skills/spec-navigator/SKILL.md:19-24`)

## Bewertungsmaßstab

- **Kritisch:** kann zu falscher Implementierungsrichtung, Sicherheitsbruch,
  Datenverlust, doppelten externen Effekten oder Kosten-Runaway führen.
- **Hoch:** blockiert v1a-Implementierungsstart oder macht einen Kernvertrag
  so mehrdeutig, dass Tests nicht eindeutig geschrieben werden können.
- **Mittel:** erzeugt Drift, Wartungskosten oder Implementierungsspielraum an
  einer relevanten Schnittstelle.
- **Niedrig:** Dokuqualität, Terminologie oder Versionspflege ohne direkte
  Architekturblockade.

Ein Befund gilt nur als **geschlossen**, wenn die Reparatur in den normativen
Artefakten landet, die Implementierer lesen: Spec, ADR, Feature, Config,
Plan/Index.

## Was V0.2.4 + V0.3.0 stark macht

Erstens ist der Idempotenz-Overclaim in §10.4 nicht nur sprachlich, sondern
strukturell repariert. Die Spec prüft jetzt "drei Effektklassen aus ADR-0011
separat" (`docs/spec/SPECIFICATION.md:628-640`), passend zu ADR-0011s Tabelle
"Natürlich-idempotent / Provider-keyed / Lokal-only"
(`docs/decisions/0011-runtime-audit-and-run-attempts.md:73-84`). Das schließt
den 04-26-Befund N1 sauber.

Zweitens ist ADR-0016 die richtige Antwort auf den F0005-Schreibvertrag. Der
Vertrag nennt vier Garantien: "Atomic Write", "File Lock", "Optimistic Version
Check" und "Audit Event" (`docs/decisions/0016-config-write-contract.md:57-83`).
F0005 konsumiert das jetzt explizit bei `accept` und `pending-proposals.yaml`
(`docs/features/F0005-benchmark-curated-pin-refresh.md:46-56`, `:126-131`).

Drittens ist F0006 als eigenes Runtime-Slice überfällig und richtig
positioniert. Der Context sagt selbst, F0003/F0004/F0005 hätten diese
Infrastruktur "bereits voraus" gesetzt (`docs/features/F0006-runtime-records-and-reconcile-cli.md:18-24`),
und der Project Plan setzt F0006 vor alle v1a-Slices
(`docs/plans/project-plan.md:61-66`, `:70-72`). Das ist genau die Reparatur
des 04-24-Restbefunds "Runtime-Basis unterdimensioniert".

Viertens ist das Tool-Risk-Modell konkreter und sicherer. ADR-0015 definiert
"Erste Match in Reihenfolge gewinnt" und fail-closed Default
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:91-105`),
während V0.3.0 `shell_exec` in vier `shell_*`-Sub-Pattern splittet
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:107-129`;
`config/execution/tool-risk-inventory.yaml:50-71`).

## Bewertung der 8 Befunde aus 04-26

### N1 — §10.4 Idempotenz-Drift

**Status: geschlossen.**

Der alte §10.4-Satz war zu pauschal. V0.2.4 ersetzt ihn durch drei Assertions:
natürlich-idempotent, provider-keyed und lokal-only mit `agentctl runs reconcile`
(`docs/spec/SPECIFICATION.md:628-640`). Das deckt ADR-0011s Effektklassen
eins zu eins ab (`docs/decisions/0011-runtime-audit-and-run-attempts.md:79-84`).

### N2 — §8.5 Symmetrie-Drift

**Status: geschlossen.**

§8.5 sagt jetzt, beide Adapter würden "in gleicher Tiefe vertraglich
dokumentiert"; die "tatsächliche Default-Nutzung" folgt §8.6 und dem
Inventory (`docs/spec/SPECIFICATION.md:477-482`). Das ist konsistent mit
ADR-0014s ehrlicher Formel: "beide Peers im Vertrag, einer ist der V1-Default"
(`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:66-68`).

### N3 — F0005 Config-Write-Vertrag

**Status: teilweise geschlossen.**

F0005 selbst ist deutlich besser: `accept` schreibt in `routing-pins.yaml` oder
`model-inventory.yaml` "gemäß ADR-0016-Config-Write-Vertrag" und nennt
Atomic-Write, File-Lock, optimistische Versionsprüfung und `AuditEvent`
(`docs/features/F0005-benchmark-curated-pin-refresh.md:46-56`). ADR-0016 gilt
für alle normativ zitierten Configs, darunter `routing-pins.yaml`,
`model-inventory.yaml`, `benchmark-task-mapping.yaml`, `pending-proposals.yaml`
und `tool-risk-inventory.yaml` (`docs/decisions/0016-config-write-contract.md:84-94`).

Teilweise bleibt der Befund, weil der neue Vertrag nicht überall sauber
ankommt: F0003 schreibt weiterhin mit `agentctl dispatch pin` in
`routing-pins.yaml`, referenziert aber ADR-0016 nicht
(`docs/features/F0003-cost-aware-routing-stub.md:31-35`, `:58-60`). Außerdem
erkennt ADR-0016 manuelle Editor-Änderungen nur, wenn `version` oder `updated`
verändert wurden (`docs/decisions/0016-config-write-contract.md:69-75`).

### N4 — `benchmark-task-mapping.yaml`-Drift

**Status: geschlossen.**

Die Seed-Datei existiert jetzt mit `version`, `updated`, `drift_threshold_pp`
und `task_to_benchmark`-Mapping (`config/dispatch/benchmark-task-mapping.yaml:16-38`).
F0005 referenziert denselben Pfad als kleine YAML für Task-Klassen auf
Benchmarks (`docs/features/F0005-benchmark-curated-pin-refresh.md:61-69`).

### N5 — 3-pp-Schwelle als Eigenentscheidung

**Status: geschlossen für F0005, teilweise für Appendix-A-Evidenzdisziplin.**

F0005 markiert die Schwelle ausdrücklich: "Eigenentscheidung (V0.2.4-draft)"
und "ohne empirischen Anker" (`docs/features/F0005-benchmark-curated-pin-refresh.md:71-78`).
Die Config wiederholt das als "Eigenentscheidung" und nennt den pragmatischen
Startwert (`config/dispatch/benchmark-task-mapping.yaml:19-27`). Damit ist
der 04-26-Befund auf Feature-/Config-Ebene geschlossen; unter Achse B bleibt
die Appendix-A-Frage separat teilweise.

### N6 — Adapter-Prefix-Regel als versteckte Heuristik

**Status: geschlossen.**

Die Prefix-Regel lebt nicht mehr in F0005, sondern in
`model-inventory.yaml.rules.adapter_assignment_rules`, mit "erste Match
gewinnt" und Catch-all `* → null` (`config/dispatch/model-inventory.yaml:119-136`).
F0005 sagt explizit, es hardcodet "keine eigene Prefix-Regel" mehr und liest
aus diesem Inventory-Schema (`docs/features/F0005-benchmark-curated-pin-refresh.md:114-122`).

Der Catch-all kollidiert nicht mit `rules.defaults.adapter`: Defaults gelten
für Runtime-Dispatch bei fehlendem Pin (`config/dispatch/model-inventory.yaml:105-117`),
während `adapter_assignment_rules` nur neue, noch nicht inventarisierte Modelle
für F0005-Arrival-Detection betrifft (`config/dispatch/model-inventory.yaml:119-124`).

### N7 — `shell_exec` zu breit

**Status: geschlossen mit kleiner Doku-Restkante.**

ADR-0015 splittet `shell_exec` in `shell_readonly`, `shell_worktree_write`,
`shell_network` und `shell_dangerous` (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:107-129`).
Die Config bildet diese vier Einträge in sicherer Reihenfolge ab
(`config/execution/tool-risk-inventory.yaml:50-71`). First-match-Regeln bleiben
intakt: ADR-0015 sagt "erste Match in Reihenfolge gewinnt" und Catch-alls
unter spezifische Einträge (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:91-94`,
`:155-159`), die Config setzt `gh_*` nach den konkreten GitHub-Patterns
(`config/execution/tool-risk-inventory.yaml:91-113`).

Restkante: Der Kommentarblock der Config nennt bei `medium` noch
"shell_exec ohne Netzwerk/State-Modifikation" (`config/execution/tool-risk-inventory.yaml:10-15`).
Das ist niedrig, aber eine neue Leser:in sieht dort noch den alten Begriff.

### N8 — Tool-Risk-Drift-Detection nicht lieferbar

**Status: teilweise geschlossen.**

F0007 existiert und ist im Index/Plan verankert (`docs/features/README.md:83-85`;
`docs/plans/project-plan.md:38-40`). Der Scope ist sinnvoll: `agentctl tools
audit` liest `tool_call_record`, gruppiert Default-Hits, erzeugt eine
`tool_risk_drift`-Digest-Card und bietet `agentctl tools propose` an
(`docs/features/F0007-tool-risk-drift-detection.md:26-48`).

Teilweise bleibt der Befund, weil F0007 seine wichtigste Abhängigkeit
wegdefiniert: die Pattern-Matching-Engine ist "Out of Scope", obwohl `audit`
mit ihr joint (`docs/features/F0007-tool-risk-drift-detection.md:29-30`,
`:55-58`). Zusätzlich fehlt ADR-0016 in F0007s Frontmatter, obwohl `propose`
über ADR-0016 schreibt (`docs/features/F0007-tool-risk-drift-detection.md:6-8`,
`:44-48`).

## Bewertung der 3 verbliebenen 04-24-Befunde

### N5 alt — Runtime-Basis unterdimensioniert

**Status: teilweise.**

F0006 schließt die größte Lücke: Es definiert acht Runtime-Record-Tabellen,
JSONL-Runlogs, Budget-Ledger, `runs reconcile`, `runs inspect` und `audit show`
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:28-66`). Der Plan
setzt F0006 folgerichtig als Voraussetzung für F0003/F0004/F0005/F0007
(`docs/plans/project-plan.md:61-66`).

Nicht geschlossen ist die Schema-Basis darunter. F0006 verlangt
`run_attempt` "mit FK auf `run`" (`docs/features/F0006-runtime-records-and-reconcile-cli.md:28-31`),
aber F0001 nimmt Tabellen für `Run`, `Artifact` und `Evidence` ausdrücklich
aus dem Scope (`docs/features/F0001-sqlite-schema-core-objects.md:31-36`).
Damit kann `0002_runtime_records.sql` auf einer reinen F0001-DB nicht sauber
laufen, obwohl Acceptance Criterion 1 genau das fordert
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:82-86`).

### N6 alt — Meta-Doku-Drift

**Status: geschlossen.**

Der Project Plan steht auf `0.3.0-draft` und Datum 2026-04-26
(`docs/plans/project-plan.md:1-4`). AGENTS und spec-reviewer sind ebenfalls
auf V0.3.0 gezogen (`AGENTS.md:6-13`, `.claude/agents/spec-reviewer.md:41-50`),
und `CLAUDE.md` ist weiterhin Symlink auf `AGENTS.md` (ADR-0009-Invariante;
lokal geprüft).

### N7 alt — Appendix A Evidenz vs. Ableitung

**Status: teilweise.**

Die riskanteste neue Heuristik ist nun korrekt als Eigenentscheidung markiert:
F0005 sagt "ohne empirischen Anker" (`docs/features/F0005-benchmark-curated-pin-refresh.md:71-78`),
und die Mapping-Config wiederholt diese Markierung (`config/dispatch/benchmark-task-mapping.yaml:22-27`).
Das reicht, um die falsche Behauptung "Research belegt 3 pp" zu vermeiden.

Nicht ganz sauber ist Appendix B: Die Spec sagt pauschal, "alle nicht-trivialen
Aussagen" seien auf Research-Briefs zurückführbar (`docs/spec/SPECIFICATION.md:753-757`).
Der Default `Delta ≥ Schwelle (Default 3 pp)` steht aber im normativen Flow
(`docs/spec/SPECIFICATION.md:362-365`), ohne dort als Eigenentscheidung
markiert oder auf F0005/Mapping verwiesen zu werden.

## Neue Befunde aus Achsen C / D / E / F / G

### Neuer Befund 1 — Hoch: F0006 hängt an einer `run`-Tabelle, die F0001 bewusst nicht liefert

**Beleg.** F0006 verlangt `run_attempt` mit "FK auf `run`"
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:28-31`) und AC 2
prüft, dass `run_attempt` ohne existierenden `run_ref` fehlschlägt
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:85-86`). F0001
liefert aber nur `project`, `work_item`, `observation`, `decision`
(`docs/features/F0001-sqlite-schema-core-objects.md:20-29`) und schiebt
`Run`, `Artifact`, `Evidence` in spätere v1-Feature-Files
(`docs/features/F0001-sqlite-schema-core-objects.md:31-36`).

**Bewertung.** Das ist der stärkste neue v1a-Blocker. Der Plan sagt
"F0001 → F0006" (`docs/plans/project-plan.md:70-72`), aber F0006 kann nicht
auf F0001 alleine migrieren, wenn die referenzierte Domain-Tabelle `run` fehlt.
Dass Appendix A v1a `Run`, `Artifact`, `Evidence` als "drin" nennt
(`docs/spec/SPECIFICATION.md:715-719`), ersetzt kein lieferbares Schema-Feature.

**Empfehlung.** Vor F0006 entweder ein F0008 "v1 Domain Schema" für `run`,
`artifact`, `evidence` einziehen oder F0006 explizit um diese minimalen
Domain-Tabellen erweitern. Sonst ist der neue v1a-Pfad formal schön, aber
migrationsseitig nicht ausführbar.

### Neuer Befund 2 — Hoch: F0006 Acceptance Criteria decken die acht Runtime Records nicht gleichmäßig ab

**Beleg.** Der Scope listet acht Tabellen inklusive `policy_decision`,
`sandbox_violation` und `dispatch_decision`
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:28-41`). Die
Acceptance Criteria prüfen aber konkret Migration, FK, einen `tool_call_record`
Index, `runs inspect` mit 2 Tool-Calls + 1 ApprovalRequest + 1
BudgetLedgerEntry, Reconcile, Audit-Show und JSONL (`docs/features/F0006-runtime-records-and-reconcile-cli.md:80-113`).
`PolicyDecision`, `SandboxViolation` und `DispatchDecision` haben kein eigenes
Akzeptanzkriterium.

**Bewertung.** Der Testplan verspricht zwar eine "Simulation ... mit allen
acht Record-Typen" (`docs/features/F0006-runtime-records-and-reconcile-cli.md:120-122`),
aber Acceptance Criteria sind der eigentliche Liefervertrag. Gerade
`DispatchDecision` und `PolicyDecision` sind Voraussetzungen für F0003/F0007;
sie dürfen nicht nur implizit in einem Integrationstest erscheinen.

**Empfehlung.** ACs ergänzen: je ein Insert-/Inspect-/Query-Kriterium für
`PolicyDecision(policy=budget_gate_override|tool_risk_match)`,
`SandboxViolation` und `DispatchDecision` mit post-gate-final Freeze.

### Neuer Befund 3 — Hoch: `tool_call_record.idempotency_key` ist nicht wirklich als Key gesichert

**Beleg.** F0006 Scope sagt, `tool_call_record` habe einen
"`idempotency_key`-Index (UNIQUE pro Run/Tool)"
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:35-36`). AC 3
prüft aber UNIQUE pro `run_attempt_id, tool_call_ordinal`
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:87-89`). Das ist
eine Ordinal-Eindeutigkeit, keine Idempotency-Key-Eindeutigkeit.

**Bewertung.** ADR-0011s Pre-Send-Check sucht ausdrücklich nach demselben
`idempotency_key` (`docs/decisions/0011-runtime-audit-and-run-attempts.md:96-103`).
Wenn die DB nur Ordinals eindeutig macht, kann derselbe externe Effekt mit
anderem Ordinal erneut persistiert werden. Das unterläuft genau die
Retry-Semantik, die F0006 liefern soll.

**Empfehlung.** Den Unique-Index auf `(run_attempt_id, idempotency_key)` oder
für externe Effekte auf `(tool_name, idempotency_key)` definieren; Ordinal kann
zusätzlich eindeutig bleiben, ist aber nicht der Idempotenzanker.

### Neuer Befund 4 — Mittel bis Hoch: F0007 misst Drift gegen den aktuellen Matcher statt gegen die historische Policy-Entscheidung

**Beleg.** ADR-0015 verlangt vor jedem Tool-Call einen `PolicyDecision`-Record
mit gematchter Klasse und Begründung "matched pattern X"
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:99-101`).
F0006 nimmt dafür `policy_decision` mit `policy`-Tag `tool_risk_match` auf
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:37-38`). F0007 liest
aber `tool_call_record`-Rows und joint sie mit der Pattern-Matching-Engine
(`docs/features/F0007-tool-risk-drift-detection.md:26-31`).

**Bewertung.** Wenn F0007 die Klassifikation nachträglich mit dem aktuellen
Inventory rekonstruiert, verändert ein späteres `tools propose` die
Vergangenheit: ein früherer Default-Hit kann nachträglich wie ein normaler
Match aussehen. Für Drift-Detection muss das System wissen, was **zum
Zeitpunkt des Calls** gematcht wurde.

**Empfehlung.** F0007 sollte primär `PolicyDecision(policy=tool_risk_match)`
lesen und nur fehlende Alt-Daten mit dem Matcher rekonstruieren. `ToolCallRecord`
bleibt Call-Quelle; der Default-Hit selbst gehört in den PolicyDecision-Record.

### Neuer Befund 5 — Mittel: Pattern-Matching ist für F0007 und ADR-0015 zugleich Voraussetzung und Out of Scope

**Beleg.** ADR-0015 macht Glob-/First-Match-Logik zum Orchestrator-Vertrag
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:91-105`).
F0007 braucht die "Pattern-Matching-Engine" für seine Audit-Tabelle
(`docs/features/F0007-tool-risk-drift-detection.md:29-31`), schließt sie aber
aus dem Scope aus und sagt, F0007 könne mit "Stub-Matcher" laufen
(`docs/features/F0007-tool-risk-drift-detection.md:55-58`). F0006 schiebt die
Tool-Risk-Pattern-Matching-Engine ebenfalls in ein "eigenes Feature"
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:70-73`).

**Bewertung.** Das ist kein Sicherheitsbruch, weil der Default fail-closed ist.
Aber es ist eine Lieferlücke: v1a hat F0007 als Feature, aber kein Feature für
die Engine, deren Ergebnisse F0007 auditieren soll. Ein Stub-Matcher kann
Tests bestehen und trotzdem nicht die erste-Match-/Catch-all-Semantik
abbilden.

**Empfehlung.** Entweder F0007 auf "liest bereits persistierte
PolicyDecision-Matches" umstellen oder ein kleines F-Feature für die
Pattern-Matching-Engine vor F0007 einschieben.

### Neuer Befund 6 — Mittel: `agentctl tools propose` definiert keine sichere Einfügeposition im First-Match-Inventar

**Beleg.** F0007s `tools propose` fügt ein YAML-Snippet in
`tool-risk-inventory.yaml` ein (`docs/features/F0007-tool-risk-drift-detection.md:72-75`).
ADR-0015 sagt aber, erste Match gewinnt, und Catch-all-Patterns wie `gh_*`
müssen unter spezifischeren Einträgen stehen
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:91-94`,
`:155-159`). Die aktuelle Config hat genau so einen Catch-all
(`config/execution/tool-risk-inventory.yaml:91-113`).

**Bewertung.** Wenn `tools propose gh_issue_reopen` den Eintrag nach `gh_*`
einfügt, ist der Vorschlag wirkungslos, weil `gh_*` vorher matcht. F0007s
Schema passt zu ADR-0015, aber die Schreibsemantik fehlt.

**Empfehlung.** `propose` muss Einfügepositionen kennen: spezifische Pattern
vor Catch-all derselben Familie, neue Catch-alls nur am Ende, und nach dem
Write ein Dry-Run-Match gegen Fixture-Toolnamen.

### Neuer Befund 7 — Mittel: ADR-0016 erkennt manuelle Editor-Konflikte nur, wenn der Mensch die Version mitpflegt

**Beleg.** ADR-0016 identifiziert den Fall "User editiert manuell + F0005
schreibt → Last-Write-Wins-Verlust" als Problem
(`docs/decisions/0016-config-write-contract.md:26-30`). Die Lösung liest vor
`rename` erneut und bricht nur ab, wenn `version` oder `updated` sich seit dem
ersten Read geändert haben (`docs/decisions/0016-config-write-contract.md:69-75`).

**Bewertung.** Ein normaler Editor hält keinen CLI-Lock und muss `version`/
`updated` nicht bumpen. Bei date-only `updated` wie `updated: 2026-04-26`
(`config/dispatch/benchmark-task-mapping.yaml:16-17`) können sogar mehrere
Änderungen am selben Tag unverändert aussehen. Der vorhandene `before_hash`
aus dem Audit-Konzept (`docs/decisions/0016-config-write-contract.md:76-83`)
wäre der robustere Conflict-Check, ist aber nicht als Abbruchbedingung
normiert.

**Empfehlung.** Optimistic Conflict auf Inhalts-Hash statt nur
`version`/`updated`: Wenn `sha256(current_file)` vor `rename` nicht mehr dem
initialen `before_hash` entspricht, `ConflictDetected`. `version` bleibt
Schema-/Migrationssignal, nicht alleiniger Konfliktschutz.

### Neuer Befund 8 — Mittel: ADR-0016-Adoption ist nicht repo-weit kohärent

**Beleg.** F0007 schreibt via ADR-0016 in `tool-risk-inventory.yaml`
(`docs/features/F0007-tool-risk-drift-detection.md:44-48`), aber sein
Frontmatter nennt nur ADR-0015 und ADR-0011 (`docs/features/F0007-tool-risk-drift-detection.md:1-8`).
Feature-Index und Project Plan übernehmen diese unvollständige ADR-Liste
(`docs/features/README.md:83-85`; `docs/plans/project-plan.md:38-40`).
Zusätzlich reserviert §8.5 noch "0016 Claude-Code-Harness-Profile", obwohl
ADR-0016 jetzt der Config-Write-Vertrag ist (`docs/spec/SPECIFICATION.md:502-504`;
`docs/decisions/0016-config-write-contract.md:1-6`).

**Bewertung.** Das ist kein fachlicher Widerspruch, aber ein klassischer
Agenten-Drift. Implementierer, die über Feature-Frontmatter starten, sehen
ADR-0016 bei F0007 nicht. Implementierer, die §8.5 lesen, glauben, ADR-0016
sei für Harness-Profile reserviert.

**Empfehlung.** F0007 `adr_refs`, Feature-Index und Plan um ADR-0016 ergänzen;
Spec §8.5 auf "geplant: spätere ADRs für Harness-Profile" ohne feste Nummern
ändern.

### Neuer Befund 9 — Mittel: Spec Appendix A ist hinter dem neuen v1a-Pfad zurück

**Beleg.** Der Project Plan beschreibt den v1a-Pfad als
"F0001 → F0006 → [F0003, F0004, F0007] → F0005"
(`docs/plans/project-plan.md:70-72`). Appendix A der Spec nennt für v1a aber
nur F0003, F0004 und "später hinzukommende Feature-Files für ADRs 0010–0013"
(`docs/spec/SPECIFICATION.md:715-723`). F0006, F0007, F0005 und ADR-0016 fehlen
dort.

**Bewertung.** Die Spec sagt, §1–§11 seien Zielarchitektur und Appendix A
beschreibe, "welche Stufe welche Teile tatsächlich liefert"
(`docs/spec/SPECIFICATION.md:17-19`). Wenn Appendix A den aktuellen v1a-Pfad
nicht zeigt, driftet die normative Release-Sicht gegen den Plan.

**Empfehlung.** Appendix A an den Plan angleichen: v1a-Feature-Files
F0003/F0004/F0006/F0007/F0005 nennen und klar markieren, dass ADR-0010-0013
eigene Umsetzungsfeatures noch ausstehen.

### Neuer Befund 10 — Niedrig bis Mittel: F0007 Digest-Card-Idempotenz und 5-%-Schwelle sind zu dünn spezifiziert

**Beleg.** F0007 erzeugt eine Digest-Card, wenn der Default-Hit-Anteil über
5 % liegt oder mehr als drei unbekannte Tool-Namen auftreten
(`docs/features/F0007-tool-risk-drift-detection.md:33-38`). AC 4 sagt nur,
ein wiederholter Audit-Lauf erzeuge keine doppelte Digest-Card, "wenn die
letzte noch im Inbox ist" (`docs/features/F0007-tool-risk-drift-detection.md:76-77`).
Die Config markiert 5 % als "Eigenentscheidung" und "konservativer Startwert"
(`config/execution/tool-risk-inventory.yaml:135-138`).

**Bewertung.** Für eine Info-Card ist das nicht hochriskant, aber die Semantik
ist unklar: Zählt ein einzelner Default-Hit bei einem Tool-Call als 100 %?
Ist die Card-ID pro Zeitraum, pro unbekanntem Toolset oder pro Schwellenart?
Was passiert nach Expiry, wenn dieselben Default-Hits weiter im 14-Tage-Fenster
liegen?

**Empfehlung.** AC 4 konkretisieren: Digest-Key =
`tool_risk_drift:<period_start>:<sorted_unknown_tools_hash>`, Mindestdenominator
z. B. `>= 20 ToolCalls` für Prozent-Schwelle, sonst nur die "mehr als drei
unbekannte Namen"-Regel.

## Perspektivenreview

### Architektur

Die Architektur ist mit V0.3.0 stringenter, weil F0006 den technischen
Runtime-Layer aus dem impliziten Bereich herauszieht
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:12-24`). Der neue
Config-Write-ADR ist ebenfalls am richtigen Ort, weil mehrere Features dieselbe
YAML-Schreibklasse nutzen (`docs/decisions/0016-config-write-contract.md:10-16`).
Die Architekturdrift sitzt jetzt in der Sequenzierung: Plan sagt F0006 direkt
nach F0001, aber die Domain-Tabellen für `Run`/`Artifact`/`Evidence` fehlen
noch (`docs/plans/project-plan.md:70-72`; `docs/features/F0001-sqlite-schema-core-objects.md:31-36`).

### Sicherheit

Das `shell_*`-Splitting ist eine echte Sicherheitsverbesserung, weil unklare
Shell-Befehle fail-closed als `shell_dangerous` gelten
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:125-129`).
F0007 verbessert die Wartbarkeit des Fail-Closed-Modells, indem Default-Hits
sichtbar werden (`docs/features/F0007-tool-risk-drift-detection.md:14-22`).
Sicherheitsseitig bleibt offen, ob der Pattern-Matcher als prüfbarer Vertrag
existiert, bevor `approval=never` praktisch eingesetzt wird
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:11-18`;
`docs/features/F0007-tool-risk-drift-detection.md:55-58`).

### Betrieb

Für Betrieb ist ADR-0016 gut proportional: POSIX-Lock, atomarer Rename und
kleine YAML-Dateien passen zu n=1 Linux/macOS
(`docs/decisions/0016-config-write-contract.md:57-68`, `:132-139`). Die
Windows-Einschränkung ist ehrlich als negativ benannt
(`docs/decisions/0016-config-write-contract.md:132-135`). Der manuelle
Editor-Fall ist aber noch nicht robust genug, und genau dieser Fall ist bei
YAML+Git als menschlich editierbarer Konfigurationsfläche wahrscheinlich.

### Daten

Das Datenmodell ist besser, weil Runtime Records, JSONL-Runlogs und
Budget-Ledger jetzt als Lieferumfang erscheinen
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:28-47`). Die
Idempotenzidee bleibt richtig, aber AC 3 verwechselt Ordinal-Eindeutigkeit mit
Idempotency-Key-Eindeutigkeit (`docs/features/F0006-runtime-records-and-reconcile-cli.md:87-89`).
Außerdem fehlt der minimale v1-Domain-Schema-Slice, der `run_attempt` überhaupt
referenzierbar macht.

### Kosten

Die Kostenperspektive profitiert davon, dass `cost-aware` weiterhin explizites
Opt-in bleibt und `pinned` mit F0005-Kuration als legitime Endstufe gilt
(`docs/spec/SPECIFICATION.md:551-554`; `docs/plans/project-plan.md:87-93`).
F0006 liefert das Tages-Budget-Ledger als JSONL-Aggregation
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:45-47`, `:107-109`).
Noch offen ist, ob Budget-Records in ACs so geprüft werden, dass Gate-Overrides
und Dispatch-Freeze gemeinsam auswertbar sind.

### Implementierung

Der v0-Pfad bleibt gut geschnitten: F0001/F0002 sind klein und liefern Schema
plus manuelle CLI (`docs/features/F0001-sqlite-schema-core-objects.md:20-29`;
`docs/features/F0002-work-add-cli.md:20-35`). Der v1a-Pfad ist deutlich besser
als in V0.2.3, weil F0006/F0007 jetzt eigene Dateien haben
(`docs/features/README.md:83-85`). Implementierungsstart für v1a sollte aber
noch einen kurzen Doku-Patch abwarten: Domain-Schema vor F0006, Pattern-Matcher
oder PolicyDecision-Lesepfad vor F0007, ADR0016-Refs konsistent ziehen.

## Priorisierte Empfehlungen

### Sofort

1. **V1-Domain-Schema vor F0006 klären.** Entweder neues Feature für `run`,
   `artifact`, `evidence` oder Erweiterung von F0006. Ohne das ist
   `0002_runtime_records.sql` gegen F0001 nicht ausführbar.
2. **F0006 Idempotency-Index korrigieren.** AC 3 muss den
   `idempotency_key` selbst sichern, nicht nur `tool_call_ordinal`.
3. **F0006 ACs für alle acht Runtime Records ergänzen.** Besonders
   `DispatchDecision`, `PolicyDecision` und `SandboxViolation` brauchen eigene
   Lieferkriterien.
4. **F0007 auf historische `PolicyDecision(tool_risk_match)` umstellen.**
   Drift muss aus der damaligen Match-Entscheidung kommen, nicht aus einer
   Rekonstruktion mit heutigem Inventory.
5. **ADR-0016 Conflict-Check auf Inhalts-Hash ziehen.** Manuelle Editor-Edits
   ohne Versions-Bump müssen `ConflictDetected` auslösen.

### Danach

1. **Pattern-Matching-Lieferung sichtbar machen.** Entweder als eigenes kleines
   Feature oder als Teil von F0007/F0006, aber nicht gleichzeitig Voraussetzung
   und Out of Scope.
2. **`tools propose`-Einfügeposition normieren.** Spezifische Pattern vor
   Catch-all, danach Dry-Run-Match.
3. **ADR-0016-Refs repo-weit nachziehen.** F0007-Frontmatter, Feature-Index,
   Project Plan und F0003-Schreibpfad angleichen.
4. **Spec §8.5 ADR-Nummern korrigieren.** Keine Reservierung von ADR-0016 für
   Harness-Profile, weil 0016 jetzt Config-Write ist.
5. **Appendix A an den neuen v1a-Pfad angleichen.** F0006/F0007/F0005 und
   ADR-0016 müssen dort sichtbar sein.

### Verschoben

1. **Provider-Side-Check-Wrapper** für Reconcile bleibt optional, wie F0006 es
   aus dem Scope nimmt (`docs/features/F0006-runtime-records-and-reconcile-cli.md:74-75`).
2. **Parser-/profilbasierter Shell-Matcher** kann v2 bleiben, solange unklare
   Shell-Befehle fail-closed als `shell_dangerous` laufen
   (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:125-129`).
3. **Learned Router / RouteLLM-Training** bleibt v2-Kandidat
   (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:254-255`).

## Schlussurteil

V0.2.4 und V0.3.0 schließen die meisten 04-26-Befunde substanziell. Die besten
Reparaturen sind der §10.4-Crash-Split, die §8.5-Wording-Korrektur, die Seed-
Config für Benchmark-Mapping, die Relocation der Adapter-Zuordnung ins
Inventory und das `shell_*`-Splitting.

Die neuen Kernartefakte sind aber nicht ganz durchgehend konsistent. ADR-0016
ist die richtige Entscheidung, erkennt manuelle Konflikte aber zu schwach und
ist noch nicht bei allen Config-Writern referenziert. F0006 ist der richtige
v1a-Fundament-Slice, hängt aber an fehlenden v1-Domain-Tabellen und schwachen
ACs. F0007 ist richtig als Feature, misst aber besser über persistierte
PolicyDecision-Matches als über eine rekonstruierte aktuelle Matcher-Sicht.

Damit ist mein Urteil strenger als "V0.3.0 ist implementierungsbereit": Der
Entwurf ist **implementierungsnah**, aber v1a sollte noch einen kleinen
Konsistenzpatch bekommen. Danach wäre der Einstieg mit F0001/F0002 und dem
Runtime-Schema deutlich belastbarer.
