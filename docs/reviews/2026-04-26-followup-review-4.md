---
title: Fuenftes Follow-up-System-Review — Personal Agentic Control System V0.3.1-draft
date: 2026-04-26
status: draft
reviewer: Codex
scope: V0.3.1-draft gegen das vierte Follow-up-Review vom 2026-04-26
responds_to:
  - docs/reviews/2026-04-23-critical-system-review.md
  - docs/reviews/2026-04-24-followup-review.md
  - docs/reviews/2026-04-26-followup-review-2.md
  - docs/reviews/2026-04-26-followup-review-3.md
  - docs/reviews/2026-04-23-counter-review.md
---

# Fuenftes Follow-up-System-Review — Personal Agentic Control System V0.3.1-draft

## Executive Summary

V0.3.1-draft ist der bisher beste Konsistenz-Patch seit Beginn der Review-Serie.
Der Changelog beschreibt ihn zutreffend als Patch fuer die drei Hoch-Befunde an
F0006 und sieben mittleren Drift-Befunde an F0007, ADR-0016, Spec und Plan
(`CHANGELOG.md:9-16`). Die groesste Reparatur ist F0008: Das Feature zieht
`Run`, `Artifact` und `Evidence` als v1a-Domain-Schema vor F0006 ein und nennt
die neue Reihenfolge F0001 -> F0008 -> F0006 -> [F0003, F0004, F0007] -> F0005
(`docs/features/F0008-v1-domain-schema.md:14-23`).

Kurzurteil pro Achse:

- **A · Zehn Befunde aus 04-26-followup-review-3:** **8 geschlossen,
  2 teilweise.** Geschlossen sind N1, N2, N3, N4, N5, N6, N7, die
  ADR-Nummern-Drift in §8.5 und N9. Teilweise bleiben N8, weil der
  Feature-Index F0003 noch ohne ADR-0016 fuehrt, und N10, weil
  `threshold_kind` in der Digest-Card-ID benutzt, aber nicht enum-artig
  benannt wird (`docs/features/README.md:81`; `docs/features/F0007-tool-risk-drift-detection.md:96-104`).
- **B · Neue Widersprueche:** Keine neue kritische Architekturblockade, aber
  fuenf mittlere bis hohe Inkonsistenzen. Die wichtigsten: F0006-AC 1 sagt noch
  "auf einer F0001-DB", obwohl Frontmatter und Scope F0008 voraussetzen
  (`docs/features/F0006-runtime-records-and-reconcile-cli.md:8`, `:29-33`,
  `:86-88`), und der `PolicyDecision(tool_risk_match)`-Datenvertrag ist fuer
  F0007 noch zu implizit (`docs/features/F0007-tool-risk-drift-detection.md:27-34`).
- **C · F0008:** Der neue Schema-Slice schliesst den alten FK-Anker sauber und
  testet `run.state` inklusive `needs_reconciliation` (`docs/features/F0008-v1-domain-schema.md:59-76`).
  Er ist als Minimal-Schema tragfaehig, aber seine ACs sollten `artifact.state`
  und negative `evidence.subject_ref`-Faelle staerker pruefen.
- **D · F0006:** Die doppelten UNIQUE-Constraints und ACs 11-13 sind die richtige
  Korrektur (`docs/features/F0006-runtime-records-and-reconcile-cli.md:91-97`,
  `:122-135`). Offen bleibt nicht die Idee, sondern die Genauigkeit: AC 1 ist
  stale, und `PolicyDecision` braucht fuer F0007 eigene Felder/Refs.
- **E · F0007:** Die Rebase auf historische `PolicyDecision`-Records ist
  fachlich richtig und beseitigt die alte Live-Matcher-Abhaengigkeit
  (`docs/features/F0007-tool-risk-drift-detection.md:27-39`, `:70-78`).
  Der naechste Patch sollte aber definieren, welche `threshold_kind`-Werte in
  die Card-ID eingehen und welche PolicyDecision-Spalten F0007 voraussetzt.
- **F · ADR-0016:** Der Inhalts-Hash-Check schliesst den manuellen Editor-Fall
  substanziell (`docs/decisions/0016-config-write-contract.md:69-89`). Der
  `before_hash` muss in V1 nicht persistent sein, weil der Vertrag den Lock
  ueber den gesamten read-modify-write-Vorgang haelt (`docs/decisions/0016-config-write-contract.md:64-68`).
- **G · Lieferbarkeit:** Der v0-Pfad bleibt sauber: F0001 liefert die vier
  v0-Tabellen, F0002 bleibt einziger v0-CLI-Einstieg (`docs/features/F0001-sqlite-schema-core-objects.md:20-29`;
  `docs/plans/project-plan.md:74-76`). Der v1a-Pfad ist jetzt start-tauglich
  als Sequenz, aber fuer "implementierungsbereit bis v1a-Exit" braucht er noch
  einen kleinen Patch an F0006/F0007/Feature-Metadaten und sichtbare
  Implementierungsfeatures fuer ADR-0010/0012/0015.

Mein Kernurteil: V0.3.1 schliesst die groesste v1a-Blockade substanziell.
Trotzdem sollte noch ein kleiner V0.3.2-Konsistenzpatch kommen, bevor man die
v1a-Implementierung als voll startklar bezeichnet.

## Quellenbasis

Gelesen wurden ausschliesslich lokale Dokumente; es gab keinen externen
Web-Check:

- die vier Codex-Reviews und die Claude-Counter-Review
  (`docs/reviews/2026-04-23-critical-system-review.md:20-35`,
  `docs/reviews/2026-04-24-followup-review.md:44-89`,
  `docs/reviews/2026-04-26-followup-review-2.md:33-77`,
  `docs/reviews/2026-04-26-followup-review-3.md:27-52`,
  `docs/reviews/2026-04-23-counter-review.md:27-38`)
- `CHANGELOG.md` fuer `[0.3.1-draft]`, `[0.3.0-draft]`,
  `[0.2.4-draft]` (`CHANGELOG.md:9-78`, `:80-145`, `:147-150`)
- neue/geaenderte Features F0008, F0006, F0007, F0003 sowie F0001, F0004,
  F0005 als Kontext (`docs/features/F0008-v1-domain-schema.md:14-94`,
  `docs/features/F0006-runtime-records-and-reconcile-cli.md:15-163`,
  `docs/features/F0007-tool-risk-drift-detection.md:15-127`,
  `docs/features/F0003-cost-aware-routing-stub.md:14-88`,
  `docs/features/F0001-sqlite-schema-core-objects.md:14-68`)
- ADR-0010, ADR-0011, ADR-0012, ADR-0013, ADR-0015, ADR-0016
  (`docs/decisions/0010-execution-harness-contract.md:40-100`,
  `docs/decisions/0011-runtime-audit-and-run-attempts.md:41-147`,
  `docs/decisions/0012-hitl-timeout-semantics.md:41-95`,
  `docs/decisions/0013-v1-deployment-mode.md:41-81`,
  `docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:87-171`,
  `docs/decisions/0016-config-write-contract.md:57-153`)
- `SPECIFICATION.md` Frontmatter, §5.7, §6.2, §8.5, §9, §10.4 und Appendix A
  (`docs/spec/SPECIFICATION.md:1-19`, `:250-306`, `:316-380`, `:477-505`,
  `:567-648`, `:702-757`)
- Feature-Index, Project Plan und relevante Configs
  (`docs/features/README.md:16-31`, `:73-87`,
  `docs/plans/project-plan.md:30-76`,
  `config/execution/tool-risk-inventory.yaml:1-143`,
  `config/dispatch/model-inventory.yaml:19-136`,
  `config/dispatch/benchmark-task-mapping.yaml:16-43`)
- Meta-Dokumente AGENTS, README, spec-reviewer und spec-navigator
  (`AGENTS.md:6-19`, `README.md:8-9`,
  `.claude/agents/spec-reviewer.md:41-46`,
  `.claude/skills/spec-navigator/SKILL.md:19-24`)

## Bewertungsmassstab

- **Kritisch:** fuehrt wahrscheinlich zu falscher Implementierungsrichtung,
  Sicherheitsbruch, Datenverlust, doppelten externen Effekten oder Kosten-
  Runaway.
- **Hoch:** blockiert v1a-Implementierungsstart oder laesst Tests fuer einen
  Kernvertrag nicht eindeutig schreiben.
- **Mittel:** erzeugt Drift, Wartungskosten oder Interpretationsspiel an einer
  relevanten Schnittstelle.
- **Niedrig:** Dokuqualitaet, Terminologie oder Indexpflege ohne direkte
  Architekturblockade.

Ein Befund gilt als **geschlossen**, wenn die Reparatur dort gelandet ist, wo
Implementierer starten: Spec, ADR, Feature, Config, Plan/Index. Ein Befund gilt
als **teilweise**, wenn die fachliche Richtung stimmt, aber ein normativer
Einstiegspunkt noch widerspricht oder unvollstaendig ist.

## Was V0.3.1 stark macht

Erstens repariert F0008 den schaerfsten V0.3.0-Fehler an der richtigen Stelle.
F0001 schliesst `Run`, `Artifact` und `Evidence` ausdruecklich aus dem v0-Scope
aus (`docs/features/F0001-sqlite-schema-core-objects.md:31-36`); F0008 liefert
genau diese drei Tabellen als additiven v1a-Slice vor F0006
(`docs/features/F0008-v1-domain-schema.md:14-23`, `:27-44`). Damit ist der
alte Befund "F0006 haengt an einer fehlenden `run`-Tabelle" substantiell
geschlossen.

Zweitens ist F0006 deutlich testbarer geworden. AC 3 trennt
Reihenfolgen-Eindeutigkeit von Idempotenz-Eindeutigkeit und erlaubt
`idempotency_key = NULL` fuer Tool-Calls ohne externen Effekt
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:91-97`). ACs 11-13
ziehen `DispatchDecision`, `PolicyDecision` und `SandboxViolation` aus dem
impliziten Testplan in konkrete Akzeptanzkriterien
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:122-135`).

Drittens ist F0007 jetzt auf der richtigen Zeitachse. Der Audit liest
`policy_decision` mit `policy=tool_risk_match` und damit die damals getroffene
Match-Entscheidung, nicht eine Rekonstruktion gegen das aktuelle Inventory
(`docs/features/F0007-tool-risk-drift-detection.md:27-34`). Der Fallback fuer
Alt-Daten ist explizit als "rekonstruiert, nicht historisch" markiert
(`docs/features/F0007-tool-risk-drift-detection.md:37-39`).

Viertens schliesst ADR-0016 den manuellen Editor-Konflikt besser als V0.3.0.
Der Vertrag speichert beim initialen Read `sha256(file_content)` als
`before_hash` und bricht vor `rename` ab, wenn der aktuelle Inhalts-Hash davon
abweicht (`docs/decisions/0016-config-write-contract.md:69-84`). Das ist genau
die Reparatur des alten Befunds, dass `version`/`updated` allein nicht robust
genug sind.

Fuenftens sind Spec Appendix A und Plan endlich wieder auf derselben Sequenz.
Appendix A nennt F0008, F0006, F0003, F0004, F0007 und F0005 samt Reihenfolge
(`docs/spec/SPECIFICATION.md:724-729`), waehrend der Project Plan dieselbe
Kette im kritischen Pfad zeigt (`docs/plans/project-plan.md:74-76`).

## Bewertung der zehn Befunde aus 04-26-followup-review-3

### N1 — F0008 als FK-Anker fuer F0006

**Status: geschlossen.**

F0008 benennt die Luecke direkt: F0006 setzt einen FK auf `run` voraus, F0001
liefert aber nur das v0-Schema (`docs/features/F0008-v1-domain-schema.md:14-23`).
Der Scope legt `run`, `artifact` und `evidence` als additive Migration an
(`docs/features/F0008-v1-domain-schema.md:27-44`), und F0006 verweist im Scope
nun auf F0008 als Lieferant der Domain-Tabellen
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:29-34`).

### N2 — F0006-ACs fuer alle acht Runtime Records

**Status: geschlossen.**

Der alte Review hatte bemängelt, dass `PolicyDecision`, `SandboxViolation` und
`DispatchDecision` nur im Scope, nicht in ACs vorkamen
(`docs/reviews/2026-04-26-followup-review-3.md:312-331`). V0.3.1 ergaenzt
AC 11 fuer `DispatchDecision`, AC 12 fuer `PolicyDecision` und AC 13 fuer
`SandboxViolation` (`docs/features/F0006-runtime-records-and-reconcile-cli.md:122-135`).
Damit sind alle acht Typen aus ADR-0011 zumindest als Lieferkriterien sichtbar
(`docs/decisions/0011-runtime-audit-and-run-attempts.md:43-52`).

### N3 — Idempotency-Key-UNIQUE-Constraint

**Status: geschlossen.**

F0006 trennt jetzt zwei Constraints: `(run_attempt_id, tool_call_ordinal)` fuer
stabile Reihenfolge und `(run_attempt_id, idempotency_key)` fuer die
Pre-Send-Check-Semantik (`docs/features/F0006-runtime-records-and-reconcile-cli.md:91-97`).
Das passt zu ADR-0011s Pre-Send-Check, der vor externen Effekten nach demselben
`idempotency_key` sucht (`docs/decisions/0011-runtime-audit-and-run-attempts.md:96-103`).
Die NULL-Erlaubnis ist unproblematisch, weil sie im AC fuer nicht externe
Tool-Calls explizit genannt ist (`docs/features/F0006-runtime-records-and-reconcile-cli.md:93-95`).

### N4 — F0007 misst ueber `PolicyDecision`-Historie

**Status: geschlossen.**

F0007s primaere Datenquelle ist jetzt `policy_decision` mit
`policy=tool_risk_match`; `tool_call_record` liefert nur Tool-Namen und Details
per FK (`docs/features/F0007-tool-risk-drift-detection.md:27-34`). Der alte
Gefahrenpfad, dass ein heutiges Inventory die Vergangenheit umklassifiziert,
ist damit fuer neue Daten beseitigt.

### N5 — Pattern-Matcher-Dependency entkoppelt

**Status: geschlossen fuer F0007, neue Lieferkante unter G.**

F0007 sagt nun ausdruecklich, dass der Audit nicht auf den Live-Matcher
angewiesen ist, weil er persistierte `PolicyDecision(tool_risk_match)`-Records
liest (`docs/features/F0007-tool-risk-drift-detection.md:70-78`). Damit ist der
alte F0007-spezifische Befund geschlossen. Nicht geschlossen ist die v1a-
Lieferfrage, wo die Pattern-Matching-Engine fuer die Call-Zeit implementiert
wird; das ist unten ein neuer Befund.

### N6 — `tools propose`-Einfuegeposition normiert

**Status: geschlossen.**

F0007 definiert jetzt spezifische Patterns vor Catch-all-Patterns derselben
Familie, neue Catch-alls am Ende der Familie und einen Dry-Run-Match nach jedem
Insert (`docs/features/F0007-tool-risk-drift-detection.md:54-61`). Das adressiert
die First-Match-Semantik aus ADR-0015, wonach Catch-alls unter spezifischeren
Eintraegen stehen muessen (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:91-94`,
`:155-159`).

### N7 — ADR-0016-Conflict-Check auf Inhalts-Hash

**Status: geschlossen.**

ADR-0016 prueft jetzt nicht nur `version`/`updated`, sondern auch
`sha256(current_content)` gegen den initialen `before_hash`
(`docs/decisions/0016-config-write-contract.md:69-84`). Die Begruendung nennt
den menschlichen Editor ohne Versions-Bump explizit als Ziel des Checks
(`docs/decisions/0016-config-write-contract.md:86-89`).

### N8 — ADR-0016-Adoption in F0007/F0003, Index und Plan

**Status: teilweise geschlossen.**

F0007 ist sauber nachgezogen: Frontmatter nennt ADR-0016
(`docs/features/F0007-tool-risk-drift-detection.md:6-8`), der Plan ebenso
(`docs/plans/project-plan.md:40`), und `tools propose` schreibt ueber den
ADR-0016-Vertrag (`docs/features/F0007-tool-risk-drift-detection.md:51-53`).
F0003 ist im Feature selbst und im Plan ebenfalls korrigiert
(`docs/features/F0003-cost-aware-routing-stub.md:6-8`,
`docs/plans/project-plan.md:36`). Der manuelle Feature-Index ist aber fuer F0003
noch stale: Er listet F0003 nur mit ADR-0014, nicht mit ADR-0016
(`docs/features/README.md:81`). Deshalb bleibt N8 teilweise.

### §8.5-Drift — ADR-Nummern fuer Harness-Profile

**Status: geschlossen.**

Spec §8.5 reserviert ADR-0016 nicht mehr fuer Harness-Profile. Die Sektion nennt
nun 0017 fuer Claude-Code-Harness-Profile und 0018 fuer Codex-CLI-Harness-
Profile und sagt ausdruecklich, dass ADR-0016 bereits an Config-Write vergeben
ist (`docs/spec/SPECIFICATION.md:502-505`).

### N9 — Appendix A hinter dem v1a-Pfad

**Status: geschlossen.**

Appendix A nennt jetzt F0008, F0006, F0003, F0004, F0007 und F0005 im v1a-Block
und dokumentiert die Reihenfolge F0001 -> F0008 -> F0006 -> [F0003, F0004,
F0007] -> F0005 (`docs/spec/SPECIFICATION.md:716-729`). Der Project Plan zeigt
denselben kritischen Pfad (`docs/plans/project-plan.md:72-76`).

### N10 — F0007 Digest-Card-Idempotenz

**Status: teilweise geschlossen.**

F0007 hat die alte Idempotenzluecke deutlich verkleinert: AC 4 bildet die
Card-ID deterministisch aus `sha256(period_start + sorted(unmatched_tool_names)
+ threshold_kind)`, verhindert Duplikate im selben 14-Tage-Fenster und fuehrt
einen Mindest-Denominator von 20 Tool-Calls fuer die Prozent-Schwelle ein
(`docs/features/F0007-tool-risk-drift-detection.md:96-104`). Teilweise bleibt
der Befund, weil `threshold_kind` in dieser Formel nicht als kleines Enum
benannt wird. Aus dem Scope sind zwei Arten ableitbar — Prozent-Schwelle und
"mehr als drei unbekannte Tool-Namen" (`docs/features/F0007-tool-risk-drift-detection.md:40-43`) —,
aber die AC sollte diese Werte explizit machen.

## Neue Befunde aus Achsen B / C / D / E / F / G

### Neuer Befund 1 — Hoch: F0006 AC 1 widerspricht der neuen F0008-Abhaengigkeit

**Beleg.** F0006-Frontmatter setzt `depends_on: [F0001, F0008]`
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:6-8`). Der Scope sagt
ebenfalls, `0002_runtime_records.sql` laufe auf dem F0001-+-F0008-Schema, weil
F0008 `run`, `artifact` und `evidence` liefert
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:29-33`). AC 1 sagt
aber weiter: "Migration `0002_runtime_records.sql` läuft auf einer F0001-DB
ohne Fehler" (`docs/features/F0006-runtime-records-and-reconcile-cli.md:86-88`).

**Bewertung.** Das ist die einzige hohe neue Inkonsistenz in V0.3.1. Sie
reaktiviert sprachlich genau die alte F0006-Luecke, obwohl Scope, Plan und F0008
sie fachlich geschlossen haben. Der Integrationstest in F0008 ist korrekt
sequenziert (`docs/features/F0008-v1-domain-schema.md:74-76`); F0006 AC 1 muss
nur denselben Stand ausdruecken.

**Empfehlung.** AC 1 aendern zu: Migration laeuft auf einer DB mit erfolgreich
ausgefuehrten F0001- und F0008-Migrationen. Zusaetzlich sollte der Negative-Test
"F0006 ohne F0008 bricht mit klarem Migrationsfehler ab" aufgenommen werden.

### Neuer Befund 2 — Mittel-Hoch: Der `PolicyDecision(tool_risk_match)`-Vertrag ist fuer F0007 noch zu duenn

**Beleg.** F0007 benoetigt `policy_decision`-Rows mit `policy=tool_risk_match`
und einen FK zu `tool_call_record`, damit Tool-Name und Details gelesen werden
koennen (`docs/features/F0007-tool-risk-drift-detection.md:27-34`). F0006 nennt
den `policy`-Tag `tool_risk_match` im Scope und prueft ihn in AC 12
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:41-42`, `:127-131`).
Die genaue Struktur bleibt aber offen: ADR-0015 verlangt "gematchete Klasse +
Risk-Klasse + Begründung ('matched pattern X')" (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:99-101`),
waehrend Spec §5.7 und ADR-0011 `PolicyDecision` noch nur als Admission,
Dispatch, Budget-Gate und HITL-Trigger beschreiben
(`docs/spec/SPECIFICATION.md:283-286`;
`docs/decisions/0011-runtime-audit-and-run-attempts.md:49-50`).

**Bewertung.** Die F0007-Rebase ist fachlich richtig, aber F0006 definiert noch
nicht genug Schema, damit ein Implementierer weiss, ob ein Default-Hit
historisch eindeutig erkennbar ist. Fuer Drift-Detection braucht der Record
mindestens `tool_call_record_ref`, `matched_pattern`, `risk`, `approval` und
ein Default-Hit-Merkmal oder eine eindeutige Konvention, dass `matched_pattern`
auf den `default`-Zweig zeigt.

**Empfehlung.** F0006 AC 12 konkretisieren und Spec/ADR-0011 an ADR-0015
angleichen: `PolicyDecision` umfasst auch `tool_risk_match`. Fuer diesen
Policy-Typ werden ToolCall-FK, matched pattern, risk, approval und
default-hit-Flag testbar festgelegt.

### Neuer Befund 3 — Mittel: `depends_on` kollidiert mit der Feature-Frontmatter-Konvention

**Beleg.** `docs/features/README.md` definiert sechs Pflichtfelder und sagt
ausdruecklich: "Keine weiteren Felder"; `depends_on` faellt weg und ist aus
Git-Log oder ADR/Spec-Refs ableitbar (`docs/features/README.md:16-31`). F0006
und F0007 fuehren trotzdem `depends_on` im Frontmatter ein
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:6-8`;
`docs/features/F0007-tool-risk-drift-detection.md:6-8`).

**Bewertung.** Inhaltlich ist `depends_on` fuer F0006/F0007 sinnvoll. Formal
bricht es aber die eigene Feature-Konvention und erzeugt genau die Art von
Agenten-Drift, die der manuell gepflegte Index verhindern soll. Der Plan hat
bereits einen Dependency-Graphen (`docs/plans/project-plan.md:47-70`); entweder
ist dieser der einzige Ort fuer Dependencies oder die Feature-Konvention muss
aktualisiert werden.

**Empfehlung.** Entweder `depends_on` offiziell als optionales Frontmatter-Feld
zulassen und Index/Plan-Regel ergaenzen, oder die Felder aus F0006/F0007
entfernen und die Abhaengigkeiten ausschliesslich im Project Plan fuehren.

### Neuer Befund 4 — Mittel: F0008 prueft `run.state`, aber nicht genug `artifact`- und `evidence`-Integritaet

**Beleg.** F0008 definiert `artifact` mit Pflichtfeld `state`
(`docs/features/F0008-v1-domain-schema.md:33-35`), und die Spec hat einen
Artifact-Lifecycle `registered -> available -> consumed -> superseded ->
archived` (`docs/spec/SPECIFICATION.md:303-306`). Die F0008-ACs pruefen aber
nur den FK auf `artifact.origin_run_ref`, nicht den `artifact.state`-CHECK
(`docs/features/F0008-v1-domain-schema.md:67-68`). Bei `evidence.subject_ref`
prueft AC 5 nur positive Beispiele fuer `work_item:<id>`, `run:<id>`,
`artifact:<id>` und `decision:<id>` (`docs/features/F0008-v1-domain-schema.md:69-71`).

**Bewertung.** Fuer ein Minimal-Schema ist das nicht kritisch, aber fuer ein
Schema-Feature sind die Tests asymmetrisch: `run.state` ist sauber als CHECK
abgesichert, `artifact.state` nicht. Ausserdem bleibt unklar, ob
`evidence.subject_ref` nur das Praefixformat prueft oder auch ungueltige
Praefixe bzw. nicht existierende IDs ablehnt. Bei polymorphen Referenzen ist ein
voller FK nicht trivial, aber die Validierungsgrenze sollte explizit sein.

**Empfehlung.** F0008 um ACs fuer `artifact.state`-CHECK, invalides
`evidence.subject_ref`-Praefix und mindestens einen Soft-Validation-Test fuer
nicht existierende Subject-IDs ergaenzen. Wenn die ID-Existenz bewusst nicht in
SQLite erzwungen wird, sollte das als Eigenentscheidung im Feature stehen.

### Neuer Befund 5 — Mittel: Migration-Rollback ist nicht mit der Forward-Only-Konvention abgeglichen

**Beleg.** F0001 beschreibt ein Forward-Only-Migration-Datei-Skelett
(`docs/features/F0001-sqlite-schema-core-objects.md:28-29`) und sagt im Rollback
ausdruecklich, dass in V0 kein Schema-Downgrade-Skript noetig ist
(`docs/features/F0001-sqlite-schema-core-objects.md:64-68`). F0008 nutzt laut
Out of Scope dieses bestehende Forward-Only-Skelett
(`docs/features/F0008-v1-domain-schema.md:52-55`), definiert im Rollback aber
ein Down-Migration-Pendant `0001b_v1_domain_schema_down.sql`
(`docs/features/F0008-v1-domain-schema.md:89-94`).

**Bewertung.** Ein Down-Skript kann sinnvoll sein, aber es ist eine
Migrationskonvention, keine reine Feature-Notiz. Wenn v1a ploetzlich Down-
Migrations unterstuetzt, muss das Migration-Skelett aus F0001 entsprechend
erweitert werden. Wenn nicht, sollte F0008 beim F0001-Muster bleiben und den
Rollback als Datei-/Git-Restore formulieren.

**Empfehlung.** Entscheiden: ab v1a Down-Migrationen ja oder nein. Bei "ja" die
Migration-Konvention in F0001/F0008 konsistent beschreiben; bei "nein" F0008-
Rollback auf Backup/Git-Restore statt Down-Skript umstellen.

### Neuer Befund 6 — Mittel: Pattern-Matcher-Lieferung ist sichtbar, aber noch nicht eindeutig verortet

**Beleg.** ADR-0015 nennt ein eigenes v1a-Implementierungsfeature fuer die
Pattern-Matching-Logik als Follow-up (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:161-164`).
F0007 sagt dagegen, der Live-Matcher werde im Rahmen der Execution-Harness-
Implementierung von ADR-0010 geliefert (`docs/features/F0007-tool-risk-drift-detection.md:70-75`).
Appendix A spricht von spaeteren Feature-Files fuer ADRs 0010-0013 und setzt in
Klammern "Execution-Harness inkl. Pattern-Matcher" dazu
(`docs/spec/SPECIFICATION.md:724-728`). Der Project Plan laesst die ADR-
Implementierungen pauschal nach F0005 kommen (`docs/plans/project-plan.md:74-76`).

**Bewertung.** Gegenueber V0.3.0 ist das kein F0007-Blocker mehr, weil F0007
historische Records liest. Fuer v1a-Exit bleibt es aber ein Lieferblocker:
`approval=never` ist laut ADR-0015 nur sicher, wenn der Orchestrator vor jedem
Tool-Call das Inventory matcht (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:11-18`,
`:87-105`). Die Spezifikation sagt jetzt, dass ein Feature kommen soll, aber
nicht, ob es ein eigenes F0009 ist oder Teil des ADR-0010-Harness-Features.

**Empfehlung.** Ein kleines Feature fuer "Tool-Risk Pattern Matcher" anlegen
oder im kommenden ADR-0010-Implementierungsfeature explizit als Scope und AC
aufnehmen. Es sollte vor produktivem `approval=never` laufen und Fixture-Tests
fuer First-Match, Catch-all und `shell_*`-Fallback enthalten.

## F0008-Bewertung

F0008 ist als additiver v1a-Domain-Slice genau richtig dimensioniert. Es liefert
`run`, `artifact` und `evidence`, ohne F0006s Runtime-Tabellen zu vermischen
(`docs/features/F0008-v1-domain-schema.md:27-49`). Die Run-Lifecycle-States
decken die Spec inklusive `needs_reconciliation` ab
(`docs/features/F0008-v1-domain-schema.md:29-32`;
`docs/spec/SPECIFICATION.md:300-302`).

Die ACs sind stark fuer `run`: FK auf `work_item`, CHECK fuer alle neun States,
Idempotenz und Integrationstest mit F0001+F0008+F0006
(`docs/features/F0008-v1-domain-schema.md:59-76`). Schwaecher sind `artifact`
und `evidence`: `artifact.state` hat keinen expliziten CHECK-Test, und
`evidence.subject_ref` hat nur positive Akzeptanzbeispiele
(`docs/features/F0008-v1-domain-schema.md:67-71`). Das Open-Enum fuer
`artifact.kind` und `evidence.kind` ist fuer V1 vertretbar, weil F0008 nur
Mindestwerte nennt und Erweiterung pro Bedarf erlaubt
(`docs/features/F0008-v1-domain-schema.md:39-43`); ein eigener ADR waere erst
noetig, wenn daraus Policy oder Interop-Verhalten entsteht.

## F0006-Korrekturen-Bewertung

Die doppelten UNIQUE-Constraints sind orthogonal nutzbar. Ein Tool-Call mit
`idempotency_key = NULL` kann weiterhin nur den Ordinal-Constraint verletzen,
wenn dieselbe `tool_call_ordinal` doppelt eingefuegt wird; der Idempotency-
Constraint ist fuer externe Effekte gedacht und AC 3 dokumentiert NULL fuer
nicht externe Tool-Calls (`docs/features/F0006-runtime-records-and-reconcile-cli.md:91-97`).

ACs 11-13 sind konkret genug, um Basistests zu schreiben: eine zweite
`dispatch_decision` pro `run_attempt_id` muss scheitern, `policy` hat eine
CHECK-Liste, und `SandboxViolation` mit `egress_denied` muss in `runs inspect`
erscheinen (`docs/features/F0006-runtime-records-and-reconcile-cli.md:122-135`).
Der Stub-Alert-Hook in AC 13 ist fuer V1 ausreichend, weil der Scope nur einen
Logger und spaeteres echtes Alerting verlangt (`docs/features/F0006-runtime-records-and-reconcile-cli.md:132-135`).
Die offene Kante liegt nicht bei `SandboxViolation`, sondern beim noch zu
duennen `PolicyDecision(tool_risk_match)`-Schema fuer F0007.

## F0007-Rebase-Bewertung

Die Umstellung auf historische Records ist sauber durchgezogen. Der Scope
definiert `policy_decision(policy=tool_risk_match)` als primaere Quelle und
nennt Live-Re-Match nur fuer Alt-Daten mit Warnung
(`docs/features/F0007-tool-risk-drift-detection.md:27-39`). Im Out of Scope
steht ausserdem, dass F0007 nicht vom Live-Matcher abhaengt
(`docs/features/F0007-tool-risk-drift-detection.md:70-78`).

`tools propose` deckt die wichtigste Catch-all-Klasse ab: spezifische Patterns
vor `gh_*`, neue Catch-alls am Ende der Familie und Dry-Run-Match mit Rollback
bei Nicht-Gewinn (`docs/features/F0007-tool-risk-drift-detection.md:54-61`).
Edge Cases bleiben moeglich, etwa mehrere ueberlappende Familien oder globale
`*`-Catch-alls; fuer V1 reicht aber eine Fixture-Liste mit GitHub-, Shell- und
globalen Fallbacks. Der Digest-Key ist fast fertig, braucht aber das explizite
`threshold_kind`-Enum.

## ADR-0016-Erweiterung

Der Inhalts-Hash-Check ist proportional. ADR-0016 nennt selbst den kleinen
Lese-Overhead und begrenzt das Risiko durch kleine V1-Configs von etwa 100-500
Zeilen (`docs/decisions/0016-config-write-contract.md:146-153`). Der
`before_hash` muss nicht persistent gespeichert werden, solange der
read-modify-write-Vorgang innerhalb einer CLI-Operation und unter File-Lock
laeuft (`docs/decisions/0016-config-write-contract.md:64-72`).

F0005s Diff-Anzeige bleibt konsistent genug: `accept` zeigt einen Diff vor dem
Schreibvorgang, und bei `ConflictDetected` bricht der Vorgang ab
(`docs/features/F0005-benchmark-curated-pin-refresh.md:46-56`). Wenn ein
Editor zwischen Diff und `rename` schreibt, ist der angezeigte Diff zwar gegen
den initialen Stand, aber ADR-0016 verhindert den Write und zwingt den Nutzer,
`dispatch review` erneut zu starten (`docs/decisions/0016-config-write-contract.md:82-84`).

## Lieferbarkeitsblick V0.3.1

Der **v0-Pfad** ist unveraendert sauber. F0001 liefert die vier v0-Tabellen und
ein Forward-Only-Migrationsskelett (`docs/features/F0001-sqlite-schema-core-objects.md:20-29`),
F0002 bleibt laut Plan der CLI-Gate fuer v0 (`docs/plans/project-plan.md:63-76`).

Der **v1a-Pfad** ist jetzt als Reihenfolge start-tauglich: F0001 -> F0008 ->
F0006 -> [F0003, F0004, F0007] -> F0005 -> ADR-Implementierungen
(`docs/plans/project-plan.md:74-76`). Fuer v1a-Exit fehlen aber noch sichtbare
Implementierungsfeatures: ADR-0010 braucht das Harness inklusive Sandbox,
Egress, Secrets und Exit-Vertrag (`docs/decisions/0010-execution-harness-contract.md:40-100`);
ADR-0012 braucht Inbox/ApprovalRequest-Verhalten und Digest-Card-Kanal
(`docs/decisions/0012-hitl-timeout-semantics.md:41-85`); ADR-0015 braucht den
Tool-Risk-Matcher vor jedem Tool-Call (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:87-105`).
ADR-0013 ist fuer v1a weniger blockierend als Betriebsrahmen, wird aber fuer
Litestream/Restore-Drills relevant (`docs/decisions/0013-v1-deployment-mode.md:43-61`).

## Perspektivenreview

### Architektur

Architektonisch ist V0.3.1 deutlich stringenter als V0.3.0, weil das neue
F0008 die Domain-Schicht vor die Runtime-Schicht setzt
(`docs/features/F0008-v1-domain-schema.md:21-23`). Die Trennung zwischen
Domain-Objekten und Runtime Records bleibt erhalten: F0008 liefert `Run`,
`Artifact`, `Evidence`, F0006 liefert die acht technischen Records
(`docs/features/F0008-v1-domain-schema.md:46-55`;
`docs/features/F0006-runtime-records-and-reconcile-cli.md:29-45`). Die
Architekturdrift sitzt jetzt nicht mehr in der Schichtung, sondern in
Metadaten-Konventionen und einzelnen AC-Formulierungen. Der Plan ist gut
genug, um die naechsten Slices zu bauen, aber die ADR-Implementierungsfeatures
muessen bald sichtbar werden.

### Sicherheit

Sicherheitsseitig ist die F0007-Rebase ein Fortschritt, weil Audit und
Drift-Detection nicht die Vergangenheit mit heutigem Inventory umdeuten
(`docs/features/F0007-tool-risk-drift-detection.md:27-39`). ADR-0015s
Fail-Closed-Modell bleibt stark: kein Match bedeutet `risk: high`,
`approval: required` (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:84-105`;
`config/execution/tool-risk-inventory.yaml:140-143`). Der kritische Rest ist
die Call-Zeit-Engine, die diese Regel wirklich vor jedem Tool-Call ausfuehrt.
Solange sie nur als Follow-up oder Teil eines spaeteren Harness-Features
existiert, ist `approval=never` noch Spezifikationsversprechen, nicht
implementierte Sicherheit.

### Betrieb

Betrieblich ist ADR-0016 jetzt robust genug fuer n=1 und menschlich editierte
YAML-Dateien. Atomic Write, POSIX-Lock und Inhalts-Hash-Conflict-Check decken
Crash, parallele CLI-Sessions und manuelle Editor-Edits ab
(`docs/decisions/0016-config-write-contract.md:59-89`). Die Performance-Kosten
werden ehrlich begrenzt: V1-Configs sind klein, sehr grosse Configs waeren erst
spaeter ein Problem (`docs/decisions/0016-config-write-contract.md:146-153`).
Der v1a-Betrieb braucht aber weiterhin Litestream-Restore- und
Reconcile-Tests, weil Spec §10.4 Restore als Akzeptanzkriterium fuehrt
(`docs/spec/SPECIFICATION.md:646-648`).

### Daten

Das Datenmodell ist substanziell besser, weil `run_attempt` nun einen echten
`run`-FK-Anker bekommt (`docs/features/F0008-v1-domain-schema.md:27-33`;
`docs/features/F0006-runtime-records-and-reconcile-cli.md:29-34`). Die
Idempotenzseite ist mit zwei UNIQUE-Constraints jetzt sinnvoll getrennt
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:91-97`). Die groesste
Datenluecke ist `PolicyDecision(tool_risk_match)`: F0007 braucht historische
Match-Details, aber F0006 testet bisher nur den Policy-Tag. F0008 sollte
zusaetzlich die Integritaetsgrenzen fuer `artifact.state` und polymorphe
`evidence.subject_ref` klaeren.

### Kosten

Kostenlogisch fuehrt V0.3.1 keine neue Risk-Klasse ein. Der Project Plan haelt
`pinned` als V1-Default und `cost-aware` nur als explizites Opt-in
(`docs/plans/project-plan.md:91-97`), waehrend F0005 weiterhin eine kalte
HITL-Kuration statt Runtime-Auto-Dispatch beschreibt
(`docs/features/F0005-benchmark-curated-pin-refresh.md:14-24`). F0006 liefert
das Budget-Ledger als Runtime-Record und Tages-JSONL
(`docs/features/F0006-runtime-records-and-reconcile-cli.md:37-51`). Die offenen
Kostenrisiken liegen eher bei noch fehlendem Harness/Budget-Gate-Code als bei
den V0.3.1-Dokumenten.

### Implementierung

Implementierungsseitig ist V0.3.1 naeher an einem echten Backlog als V0.3.0.
Man kann F0001 und F0008 jetzt als Schema-Basis lesen, danach F0006 als Runtime-
Slice und anschliessend F0003/F0004/F0007 parallel angehen
(`docs/plans/project-plan.md:47-76`). Vor einem v1a-Start sollte aber der
kleine Widerspruch in F0006 AC 1 repariert werden. Vor produktivem v1a-Exit
braucht es ausserdem konkrete Feature-Dateien fuer Harness, HITL-Inbox und
Tool-Risk-Matcher.

## Priorisierte Empfehlungen

### Sofort

1. **F0006 AC 1 korrigieren.** "F0001-DB" muss "F0001+F0008-DB" heissen; ein
   Negative-Test fuer fehlendes F0008 waere sinnvoll.
2. **`PolicyDecision(tool_risk_match)` konkretisieren.** F0006, Spec §5.7 und
   ADR-0011 sollten ADR-0015s Match-Details aufnehmen: ToolCall-FK, Pattern,
   Risk, Approval, Default-Hit.
3. **F0003 im Feature-Index nachziehen.** `docs/features/README.md` muss bei
   F0003 ADR-0016 nennen, wie Frontmatter und Plan es bereits tun.
4. **Feature-Frontmatter-Konvention klaeren.** `depends_on` entweder offiziell
   zulassen oder aus F0006/F0007 wieder entfernen.
5. **F0008-ACs ergaenzen.** `artifact.state`-CHECK, negative
   `evidence.subject_ref`-Tests und Migrations-Rollback-Konvention klaeren.

### Danach

1. **Pattern-Matcher als Liefer-Slice sichtbar machen.** Eigenes Feature oder
   eindeutiger Bestandteil des ADR-0010-Harness-Features.
2. **F0007 `threshold_kind` enum-artig definieren.** Zum Beispiel
   `default_hit_pct` und `unknown_tool_count`.
3. **F0007-Fixtures fuer `tools propose` erweitern.** GitHub-Familie,
   `shell_*`-Familie und globales `*` sollten Dry-Run-Match-Tests haben.
4. **ADR-0016/F0005-Diff-Anzeige praezisieren.** Bei Konflikt nach Diff:
   Abbruch und erneutes Review, kein stilles Rebase.

### Verschoben

1. **Open-Enum-ADR fuer `artifact.kind`/`evidence.kind`.** Erst noetig, wenn
   Erweiterungen policy-relevant werden.
2. **Performance-Optimierung fuer grosse Configs.** ADR-0016 benennt das Thema,
   aber V1-Configs sind klein.
3. **Provider-Side-Check-Wrapper fuer Reconcile.** Bleibt optionales
   Hilfsfeature, wie F0006 es aus dem Scope nimmt
   (`docs/features/F0006-runtime-records-and-reconcile-cli.md:78-79`).

## Schlussurteil

V0.3.1-draft schliesst die alten V0.3.0-Befunde ueberwiegend substanziell. Aus
zehn Pruefpunkten sind acht geschlossen und zwei teilweise: die F0003-Zeile im
Feature-Index fehlt noch, und `threshold_kind` ist noch zu implizit. F0008 ist
die entscheidende Verbesserung, weil es den F0006-FK-Anker als eigenes
v1a-Schema-Feature liefert.

Ich wuerde V0.3.1 trotzdem noch nicht als voll implementierungsbereit fuer v1a
freigeben. Fuer v0 ja, fuer den v1a-Einstieg fast; fuer einen sauberen Start
braucht es einen kleinen Konsistenzpatch an F0006 AC 1, am
`PolicyDecision(tool_risk_match)`-Vertrag, am Feature-Index und an der
`depends_on`-Konvention. Danach ist der Pfad F0001 -> F0008 -> F0006 belastbar
genug, um mit Implementierung zu beginnen.
