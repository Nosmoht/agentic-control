---
title: Drittes Follow-up-System-Review — Personal Agentic Control System V0.2.3-draft
date: 2026-04-26
status: draft
reviewer: Codex
scope: V0.2.3-draft (Patches 0.2.1, 0.2.2, 0.2.3 gegen Reviews vom 2026-04-23/24)
responds_to:
  - docs/reviews/2026-04-23-critical-system-review.md
  - docs/reviews/2026-04-23-counter-review.md
  - docs/reviews/2026-04-24-followup-review.md
  - CHANGELOG.md
  - docs/spec/SPECIFICATION.md
  - docs/decisions/0011-runtime-audit-and-run-attempts.md
  - docs/decisions/0014-peer-adapters-and-cost-aware-routing.md
  - docs/decisions/0015-tool-risk-inventory-and-approval-routing.md
  - docs/features/F0001-sqlite-schema-core-objects.md
  - docs/features/F0002-work-add-cli.md
  - docs/features/F0003-cost-aware-routing-stub.md
  - docs/features/F0004-benchmark-awareness-manual-pull.md
  - docs/features/F0005-benchmark-curated-pin-refresh.md
  - docs/features/README.md
  - docs/plans/project-plan.md
  - config/dispatch/model-inventory.yaml
  - config/dispatch/routing-pins.yaml
  - config/execution/tool-risk-inventory.yaml
  - GLOSSARY.md
  - AGENTS.md
  - .claude/agents/spec-reviewer.md
---

# Drittes Follow-up-System-Review — Personal Agentic Control System V0.2.3-draft

## Executive Summary

V0.2.1 bis V0.2.3 sind mehr als kosmetische Nacharbeit. Die Patches schließen
die meisten harten Normdrifts aus meinem Follow-up vom 2026-04-24: ADR-0007
trägt jetzt explizit „kein Default-Auto-Abandon" und OR-Kriterien
(`docs/decisions/0007-inbox-hitl-cascade.md:3-5`, `:46-58`), ADR-0008 hat
die Task-Caps auf OR korrigiert (`docs/decisions/0008-four-scope-budget-gate.md:3-5`,
`:40-46`), ADR-0011 führt `DispatchDecision` und drei Effektklassen ein
(`docs/decisions/0011-runtime-audit-and-run-attempts.md:43-53`, `:73-84`),
und ADR-0015 macht das Tool-Risk-Inventar endlich zum normativen Artefakt
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:57-86`).

Kurzurteil pro Achse:

- **A · 8 alte Befunde aus 04-23:** auf Dokumentationsebene jetzt
  **8/8 geschlossen**. Einige Implementierungs-Features fehlen noch, aber die
  ursprünglichen Widersprüche sind normativ aufgelöst.
- **B · 7 neue Befunde aus 04-24:** **4 geschlossen, 3 teilweise**. Offen
  bleibt vor allem die Sichtbarkeit der Runtime-Basis als Liefer-Slice,
  Meta-Versionierung im Plan und die saubere Trennung von Evidenz und
  Architekturableitung.
- **C · 6 Sofort-Empfehlungen:** **4 erledigt, 2 teilweise**. Die alte
  Normdrift ist repariert; Runtime-Slice und Appendix-A-Evidenztrennung sind
  noch nicht sauber genug.
- **D · Neue Widersprüche:** V0.2.3 führt keine neue Blockade ein, aber zwei
  mittlere Drifts: Spec §10.4 spricht bei Crash weiter undifferenziert von
  „Idempotency-Keys" (`docs/spec/SPECIFICATION.md:622-626`), und §8.5 behauptet
  „gleiche Tiefe" beider Adapter, obwohl §8.6 und Inventory einen Claude-Code-
  Default als V1-Vorschlag setzen (`docs/spec/SPECIFICATION.md:477-495`,
  `:521-525`; `config/dispatch/model-inventory.yaml:105-114`).
- **E · F0005:** Der Workflow ist konzeptionell richtig als kalter HITL-Loop,
  aber das Schreibschema für `accept`, die nicht eingecheckte
  `benchmark-task-mapping.yaml` und die 3-pp-Schwelle sind noch zu dünn
  begründet (`docs/features/F0005-benchmark-curated-pin-refresh.md:46-64`,
  `:92-108`).
- **F · ADR-0015 / Tool-Risk:** Als Sicherheitsartefakt stark und proportional,
  aber die Klassen sind nicht ganz disjunkt, `shell_exec` ist als Seed zu breit,
  und die Drift-Detection steht nur als Follow-up, nicht als Feature
  (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:62-70`,
  `:136-144`; `config/execution/tool-risk-inventory.yaml:50-53`).

Mein Kernurteil: V0.2.3 ist jetzt eine belastbare V1-Spezifikation auf
Design-Ebene. Der nächste Reparaturbedarf liegt nicht mehr bei den alten
kritischen Architekturwidersprüchen, sondern bei lieferbaren v1a-Slices,
Config-Schreibverträgen und Drift-Detection.

## Quellenbasis

Gelesen wurden ausschließlich lokale Dokumente, kein externer Web-Check:

- die beiden Codex-Reviews vom 2026-04-23 und 2026-04-24 sowie die
  Claude-Counter-Review (`docs/reviews/2026-04-23-critical-system-review.md:20-35`,
  `docs/reviews/2026-04-24-followup-review.md:44-89`,
  `docs/reviews/2026-04-23-counter-review.md:27-38`)
- `CHANGELOG.md` für `[0.2.1-draft]`, `[0.2.2-draft]`, `[0.2.3-draft]`
  (`CHANGELOG.md:9-90`, `:91-123`, `:124-172`)
- `docs/spec/SPECIFICATION.md`, insbesondere §5.7, §6.2, §8.3, §8.5, §8.6,
  §9, §10.4 und Appendix A (`docs/spec/SPECIFICATION.md:250-302`,
  `:316-375`, `:440-561`, `:563-630`, `:684-745`)
- ADR-0011, ADR-0014, ADR-0015 sowie die amendierten ADR-0002, ADR-0007,
  ADR-0008, ADR-0013 (`docs/decisions/0011-runtime-audit-and-run-attempts.md:1-186`,
  `docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:1-274`,
  `docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:1-158`)
- Feature-Dateien F0001 bis F0005, Feature-Index und Project Plan
  (`docs/features/README.md:16-84`, `docs/plans/project-plan.md:30-87`)
- Dispatch- und Tool-Risk-Konfigurationen
  (`config/dispatch/model-inventory.yaml:19-117`,
  `config/dispatch/routing-pins.yaml:1-27`,
  `config/execution/tool-risk-inventory.yaml:22-120`)
- `GLOSSARY.md`, `AGENTS.md`, `.claude/agents/spec-reviewer.md`
  (`GLOSSARY.md:217-237`, `AGENTS.md:6-13`,
  `.claude/agents/spec-reviewer.md:41-50`)

## Bewertungsmaßstab

- **Kritisch:** kann zu falscher Implementierungsrichtung, Sicherheitsbruch,
  doppelten externen Effekten, Kosten-Runaway oder Datenverlust führen.
- **Hoch:** gefährdet V1-Kernziele oder erzeugt normative Mehrdeutigkeit, die
  vor Implementierungsbeginn geklärt sein sollte.
- **Mittel:** erzeugt Reibung, Drift, Wartungskosten oder Interpretationsspiel.
- **Niedrig:** Klarheit, Terminologie oder Dokumentationspflege ohne direkte
  Architekturblockade.

## Was V0.2.3 stark macht

Erstens hat V0.2.3 die alten „accepted, aber widersprüchlich"-ADRs ernsthaft
repariert. ADR-0007 ist nicht nur durch ADR-0012 überlagert, sondern markiert
die aufgehobene 72-h-Abandon-Regel direkt in der Tabelle
(`docs/decisions/0007-inbox-hitl-cascade.md:41-47`) und ersetzt „Kumulativ"
durch OR-Kriterien (`docs/decisions/0007-inbox-hitl-cascade.md:48-58`).
ADR-0008 trägt dieselbe Art von sichtbarer Korrektur für OR-Caps
(`docs/decisions/0008-four-scope-budget-gate.md:35-46`).

Zweitens ist die Idempotenz-Story jetzt fachlich ehrlicher. ADR-0011 sagt
nicht mehr pauschal „Dual-Write gelöst", sondern trennt natürlich-idempotent,
provider-keyed und lokal-only (`docs/decisions/0011-runtime-audit-and-run-attempts.md:73-84`)
und benennt das echte Crash-Fenster zwischen externem Effekt und lokalem
Persist (`docs/decisions/0011-runtime-audit-and-run-attempts.md:105-112`).
Das ist genau die Präzisierung, die V0.2.0 noch fehlte.

Drittens ist ADR-0014 jetzt deutlich ehrlicher. Die frühere Peer-Symmetrie
wurde zu „beide Peers im Vertrag, einer ist der V1-Default" korrigiert
(`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:52-68`), der
Freeze-Zeitpunkt ist post-gate-final (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:170-178`),
und die automatische `cost-aware`-Aktivierung ist gestrichen
(`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:180-193`).

Viertens ist ADR-0015 als Sicherheitsartefakt die richtige Ergänzung zu
`approval=never`. Es definiert Schema, Fail-Closed-Default und den
Orchestrator-Vertrag vor jedem Tool-Call (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:71-105`).
Damit ist `approval=never` nicht mehr nur ein CLI-Flag-Versprechen, sondern
an eine prüfbare Config gebunden.

## Bewertung der 8 alten Befunde aus 04-23

### Befund 1 — SQLite/DBOS/VPS-Widerspruch

**Status: geschlossen.** Die Spec trennt v1a lokal-only, v1b read-only Bridge
und v2+ Postgres (`docs/spec/SPECIFICATION.md:382-412`). ADR-0013 formuliert
dieselbe Schwelle als Entscheidungsregel: zweite schreibende Rolle → v2+
Postgres (`docs/decisions/0013-v1-deployment-mode.md:75-82`). Damit ist der
ursprüngliche Widerspruch aus „spiegelnde Instanz" vs. Postgres-Pflicht
geschlossen.

### Befund 2 — HITL-Timeout-Semantik

**Status: geschlossen.** ADR-0007 enthält jetzt die aufgehobene 72-h-Regel als
durchgestrichene Altsemantik und verweist auf ADR-0012 (`docs/decisions/0007-inbox-hitl-cascade.md:41-47`,
`:81-86`). Die Spec führt `waiting_for_approval`, `stale_waiting`,
`timed_out_rejected` und eingeschränktes `abandoned` in Lifecycle und Flow
zusammen (`docs/spec/SPECIFICATION.md:295-302`, `:337-348`). Der
04-24-Restbefund ist damit geschlossen.

### Befund 3 — Durable Execution / externe Effekte

**Status: geschlossen auf Spec-Ebene.** ADR-0011 beschreibt Runtime Records
inklusive `RunAttempt`, `ToolCallRecord` und `DispatchDecision`
(`docs/decisions/0011-runtime-audit-and-run-attempts.md:41-53`) und trennt
die Idempotenzqualität externer Effekte explizit (`docs/decisions/0011-runtime-audit-and-run-attempts.md:73-84`).
Der Reconciliation-Pfad mit `agentctl runs reconcile <run-id>` ist normiert
(`docs/decisions/0011-runtime-audit-and-run-attempts.md:105-130`). Die
Implementierung fehlt noch, aber der ursprüngliche Design-Overclaim ist
repariert.

### Befund 4 — Sandbox-Grenze operativ unklar

**Status: geschlossen.** Dieser Befund war bereits in V0.2.0 geschlossen und
bleibt geschlossen. Die Spec bindet die acht MVS-Schichten an ADR-0010
(`docs/spec/SPECIFICATION.md:423-438`), und ADR-0015 baut für Tool-Approval
auf genau diesem Sicherheitsmodell auf (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:5-7`).

### Befund 5 — Budget-Caps AND statt OR

**Status: geschlossen.** ADR-0008 trägt jetzt `OR` in Status und Tabelle
(`docs/decisions/0008-four-scope-budget-gate.md:3-5`, `:37-46`), die Spec
bestätigt „OR, nicht AND" (`docs/spec/SPECIFICATION.md:442-450`), und der
Changelog dokumentiert die Korrektur (`CHANGELOG.md:136-138`). Das ist die
Vollschließung, die V0.2.0 noch nicht geliefert hatte.

### Befund 6 — Codex-Approval-Policy

**Status: geschlossen.** ADR-0014 entscheidet `approval=never`, aber nun mit
expliziter Voraussetzung ADR-0015 (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:195-207`).
ADR-0015 liefert Fail-Closed-Default und Approval-Routing
(`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:84-105`);
die konkrete Config setzt `default: risk: high, approval: required`
(`config/execution/tool-risk-inventory.yaml:117-120`).

### Befund 7 — Fehlender Datenvertrag für Nachvollziehbarkeit

**Status: geschlossen.** Die Spec listet Runtime Records inklusive
`DispatchDecision` (`docs/spec/SPECIFICATION.md:273-289`), ADR-0011 hat dieselbe
Tabelle inklusive `DispatchDecision` (`docs/decisions/0011-runtime-audit-and-run-attempts.md:43-53`),
und Observability nennt SQLite-Audit, Runlog, Budgetledger und CLI-Inspect
(`docs/spec/SPECIFICATION.md:463-475`). Portabilität bleibt Follow-up, aber der
Nachvollziehbarkeitsvertrag ist nicht mehr strukturell lückenhaft.

### Befund 8 — Zielarchitektur vs. Release-Staging

**Status: geschlossen.** Die Spec trennt Zielarchitektur und Release-Stages
explizit (`docs/spec/SPECIFICATION.md:17-19`), §5.7 trägt Stage-Spalten
(`docs/spec/SPECIFICATION.md:254-271`, `:277-287`), und Feature-Stages erlauben
jetzt `v1a`/`v1b` (`docs/features/README.md:18-26`). F0003 und F0004 sind auf
`stage: v1a` gesetzt (`docs/features/F0003-cost-aware-routing-stub.md:1-8`,
`docs/features/F0004-benchmark-awareness-manual-pull.md:1-8`). Das löst den
04-24-Stage-Drift.

## Bewertung der 7 neuen Befunde aus 04-24

### N1 — Peer-Asymmetrie

**Status: geschlossen.** ADR-0014 formuliert jetzt offen, dass Claude Code und
Codex CLI Peers im Vertrag sind, aber der `pinned`-Default aus
`model-inventory.yaml.rules.defaults.adapter` kommt und der V1-Vorschlag
`claude-code` ist (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:52-68`).
Das Inventory macht diese Entscheidung konfigurierbar
(`config/dispatch/model-inventory.yaml:105-114`).

### N2 — `DispatchDecision` Freeze-Zeitpunkt

**Status: geschlossen.** Spec §6.2 sagt: vorläufige Auswahl, Budget-Gate,
dann finale Persistierung und Freeze (`docs/spec/SPECIFICATION.md:316-331`).
Spec §8.3 sagt zusätzlich, Gate-Rewahl sei `PolicyDecision`, nicht zweite
`DispatchDecision` (`docs/spec/SPECIFICATION.md:452-458`). ADR-0014 spiegelt
das als „Dispatch → Budget-Gate → Freeze → Run-Start"
(`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:158-178`).

### N3 — Idempotenz-Overclaim

**Status: geschlossen.** ADR-0011 begrenzt die DBOS-Garantie ausdrücklich auf
die DB-Schreibseite (`docs/decisions/0011-runtime-audit-and-run-attempts.md:135-147`).
ADR-0002 und ADR-0013 tragen denselben Grenzsatz in ihren Treibern
(`docs/decisions/0002-dbos-durable-execution.md:16-21`,
`docs/decisions/0013-v1-deployment-mode.md:24-27`). Das ist die richtige
Korrektur des 04-24-Overclaims.

### N4 — Stage-/State-Drift

**Status: geschlossen.** Die HITL-Substates und `needs_reconciliation` stehen
jetzt in der Spec-Lifecycle-Liste (`docs/spec/SPECIFICATION.md:295-302`) und
im Glossar (`GLOSSARY.md:107-113`, `:137-141`). Feature-README und Feature-
Index nutzen `v1a` (`docs/features/README.md:18-26`, `:77-83`). Dieser Befund
ist repo-weit ausreichend repariert.

### N5 — Runtime-Basis unterdimensioniert

**Status: teilweise.** Der Plan erkennt weiterhin an, dass ADRs 0010–0013 erst
später eigene Feature-Files bekommen (`docs/plans/project-plan.md:40-42`), aber
F0003 persistiert bereits `DispatchDecision` „sobald ADR-0011 implementiert ist"
(`docs/features/F0003-cost-aware-routing-stub.md:54-55`) und F0004 erwartet
`Evidence` plus `Artifact` (`docs/features/F0004-benchmark-awareness-manual-pull.md:60-62`).
F0005 setzt zusätzlich `AuditEvent` und YAML-Write-Locking voraus
(`docs/features/F0005-benchmark-curated-pin-refresh.md:46-50`, `:106-108`).
Die Architektur ist klarer, aber der lieferbare Runtime-/Audit-Slice fehlt
weiter als eigenes Feature.

### N6 — Meta-Doku-Drift

**Status: teilweise.** `AGENTS.md` ist auf V0.2.3-draft gezogen
(`AGENTS.md:6-13`), und der Spec-Reviewer spricht korrekt von V0.2.3 und 8
Invarianten (`.claude/agents/spec-reviewer.md:41-50`). Der Project Plan trägt
aber im Kopf weiter `Version: 0.2.0-draft` (`docs/plans/project-plan.md:1-4`),
obwohl der Changelog behauptet, der Plan sei in V0.2.3 aktualisiert worden
(`CHANGELOG.md:78-81`). Das ist klein, aber bei Agent-gelesenen Metadaten
relevant.

### N7 — Appendix A Evidenz vs. Ableitung

**Status: teilweise.** Die riskanteste Ableitung, der automatische Wechsel in
`cost-aware`, ist gestrichen (`docs/spec/SPECIFICATION.md:713-719`;
`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:180-190`). Damit
ist der operative Schaden behoben. Die explizite Trennung „Evidenz stützt X"
vs. „wir leiten Y als Eigenentscheidung ab" bleibt aber nur indirekt; Anhang B
verweist pauschal auf Plan-Appendix A als empirische Basis
(`docs/spec/SPECIFICATION.md:742-745`). F0005 führt zusätzlich eine 3-pp-
Schwelle ein, ohne sie in Appendix A zu verteidigen
(`docs/features/F0005-benchmark-curated-pin-refresh.md:33-38`, `:63-64`).

## Bewertung der 6 Sofort-Empfehlungen aus 04-24

1. **Normkonsistenz der Alt-ADRs herstellen — erledigt.** ADR-0007 und
   ADR-0008 sind direkt korrigiert (`docs/decisions/0007-inbox-hitl-cascade.md:3-5`,
   `docs/decisions/0008-four-scope-budget-gate.md:3-5`).

2. **State-Machines glätten — erledigt.** HITL-Substates und
   `needs_reconciliation` stehen in Spec und Glossar
   (`docs/spec/SPECIFICATION.md:295-302`; `GLOSSARY.md:107-113`, `:137-141`).

3. **Peer-Adapter-Asymmetrie offen entscheiden — erledigt.** ADR-0014 sagt
   ausdrücklich „Peers im Vertrag, einer ist der V1-Default"
   (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:66-68`).

4. **Tool-Risk-Modell explizit machen — erledigt.** ADR-0015 und
   `config/execution/tool-risk-inventory.yaml` existieren normativ
   (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:57-86`;
   `config/execution/tool-risk-inventory.yaml:22-120`).

5. **Runtime-Basis als Liefer-Slice sichtbar machen — teilweise.** Der Plan
   nennt spätere Feature-Files für ADRs 0010–0013 (`docs/plans/project-plan.md:40-42`),
   aber noch kein konkretes Feature für Runtime Records, Reconciliation,
   AuditEvents oder ToolRisk-Matching. F0003/F0004/F0005 hängen weiter daran.

6. **Appendix A zwischen Evidenz und Ableitung trennen — teilweise.** Die
   falsche Auto-Aktivierung ist entfernt (`docs/spec/SPECIFICATION.md:713-719`),
   aber neue F0005-Heuristiken und die 3-pp-Schwelle bleiben
   Architekturableitung ohne eigene ADR-/Appendix-A-Verteidigung
   (`docs/features/F0005-benchmark-curated-pin-refresh.md:63-64`, `:99-102`).

## Neue Befunde aus Achsen D / E / F

### Neuer Befund 1 — Mittel: Spec §10.4 ist hinter ADR-0011s Effektklassen zurück

**Beleg.** Die Testmatrix sagt: „Crash: Prozess stirbt nach Agent-Call vor
Post-Flight — Retry dupliziert externe Effekte nicht (Idempotency-Keys,
ADR-0011)" (`docs/spec/SPECIFICATION.md:622-626`). ADR-0011 sagt dagegen
präziser: lokal-only-Effekte haben ein echtes Crash-Fenster und brauchen
Reconciliation (`docs/decisions/0011-runtime-audit-and-run-attempts.md:105-130`).

**Bewertung.** Die Testmatrix ist nicht falsch gemeint, aber zu grob. Sie
kann wieder als Exactly-Once-Versprechen gelesen werden, obwohl V0.2.3 gerade
die drei Effektklassen eingeführt hat.

**Empfehlung.** §10.4 in drei Assertions aufspalten: natürlich-idempotent
dedupliziert automatisch, provider-keyed retried mit Provider-Key, lokal-only
geht nach Crash in `needs_reconciliation` statt „dupliziert nicht" pauschal zu
versprechen.

### Neuer Befund 2 — Mittel: §8.5 „gleiche Tiefe" driftet gegen den ehrlichen Claude-Default

**Beleg.** §8.5 sagt: „Beide Adapter werden in gleicher Tiefe dokumentiert und
verwendet" (`docs/spec/SPECIFICATION.md:477-480`). §8.6 sagt gleichzeitig,
im `pinned`-Default komme der Adapter aus `model-inventory.yaml`, V1-Vorschlag
`claude-code` (`docs/spec/SPECIFICATION.md:521-525`). Das Inventory setzt
`adapter: claude-code` (`config/dispatch/model-inventory.yaml:105-114`).

**Bewertung.** Kein harter Widerspruch, aber die Formulierung „verwendet" ist
zu stark. V0.2.3 hat die operative Asymmetrie bewusst ehrlich gemacht; §8.5
sollte nicht zurück in rhetorische Symmetrie rutschen.

**Empfehlung.** §8.5 auf „beide Adapter werden in gleicher Tiefe vertraglich
dokumentiert; die tatsächliche Default-Nutzung folgt §8.6/Inventory" ändern.

### Neuer Befund 3 — Hoch: F0005 schreibt normative Configs, ohne ein Schreibschema zu definieren

**Beleg.** F0005 `accept` schreibt in `routing-pins.yaml` bzw.
`model-inventory.yaml`, zeigt einen Diff, erzeugt `AuditEvent` und entfernt
die Proposal (`docs/features/F0005-benchmark-curated-pin-refresh.md:46-50`,
`:92-94`). Gleichzeitig ist nur für `pending-proposals.yaml` strukturelle
Stabilität gegen parallele Writes gefordert (`docs/features/F0005-benchmark-curated-pin-refresh.md:106-108`).
`routing-pins.yaml` hat ein vorläufiges Match-Schema (`config/dispatch/routing-pins.yaml:6-16`),
`model-inventory.yaml` enthält Preise, Adapter, Tiers und Defaults
(`config/dispatch/model-inventory.yaml:22-117`).

**Bewertung.** Das ist der stärkste neue F0005-Befund. Ein wöchentlicher
Kurationsloop ist sinnvoll, aber `accept` verändert genau die Dateien, die
Runtime-Dispatch liest. Ohne normiertes Diff-/Lock-/Conflict-Modell kann ein
paralleler F0003-Read oder ein manueller Edit inkonsistente Pins oder
Inventory-Einträge sehen.

**Empfehlung.** Ein kleines Config-Write-Protokoll ergänzen: parse-modify-
serialize über YAML-AST, atomarer Rename, file lock für alle drei Dateien,
optimistische Version (`updated`/hash), Konfliktmeldung statt Blind-Write,
und AuditEvent mit vorherigem/nachherigem Hash.

### Neuer Befund 4 — Mittel: F0005 referenziert eine Config, die nicht im Repo liegt

**Beleg.** Spec §6.2 und F0005 referenzieren
`config/dispatch/benchmark-task-mapping.yaml` (`docs/spec/SPECIFICATION.md:362-365`;
`docs/features/F0005-benchmark-curated-pin-refresh.md:55-64`). Im aktuellen
`config/dispatch/` liegen nur `model-inventory.yaml` und `routing-pins.yaml`.
Der Project Plan beschreibt F0005 als v1a-Feature, aber ohne diese Config im
Index (`docs/plans/project-plan.md:30-39`).

**Bewertung.** Für ein vorgeschlagenes Feature ist eine fehlende Config-Datei
kein kritischer Fehler. Weil die Spec den Mapping-Pfad aber bereits im
normativen Flow nennt, entsteht ein kleiner Norm-/Repo-Drift.

**Empfehlung.** Entweder Seed-Datei mit nur Schema/Default-Schwelle einchecken
oder Spec/F0005 klar sagen lassen: „wird von F0005 erzeugt, existiert vor
Implementierung nicht".

### Neuer Befund 5 — Mittel: 3-pp-Drift-Schwelle ist eine neue Heuristik ohne ADR-Begründung

**Beleg.** F0005 setzt `top_score - pinned_score ≥ drift_threshold_pp`
mit Default 3 (`docs/features/F0005-benchmark-curated-pin-refresh.md:33-38`)
und wiederholt „Default 3 pp" als Config-Wert (`docs/features/F0005-benchmark-curated-pin-refresh.md:63-64`).
Appendix A sagt nur, der `cost-aware`-Wechsel sei explizites Opt-in und Pins
mit F0005-Kuration seien legitim (`docs/spec/SPECIFICATION.md:713-719`).

**Bewertung.** Die Schwelle kann pragmatisch sein, aber sie ist eine
Verhaltensentscheidung: sie bestimmt, wann der Nutzer wöchentlich Arbeit sieht.
Bei Benchmark-Rauschen und Harness-Varianz ist 3 pp erklärungsbedürftig.

**Empfehlung.** Als Eigenentscheidung markieren oder in ADR-0014/F0005
begründen: Default 3 pp als konservativer Startwert, konfigurierbar, keine
Qualitätsgarantie; bei Coding ggf. andere Schwelle als bei Arena/Reasoning.

### Neuer Befund 6 — Mittel: Modell-Arrival-Adapter-Zuordnung ist eine versteckte Dispatch-Heuristik

**Beleg.** F0005 Acceptance Criterion 8 fordert Prefix-Regeln:
`claude-* → claude-code`, `gpt-*`/`o-* → codex-cli`, `gemini-* → adapter: null`
(`docs/features/F0005-benchmark-curated-pin-refresh.md:99-102`). ADR-0014
sagt dagegen, Adapter-spezifische Übersetzung lebe in Adaptern und der
Orchestrator special-cased keinen Adapter außerhalb von `describe()`
(`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:101-104`).

**Bewertung.** Die Prefix-Regel ist praktisch, aber sie ist ein Adapter-
Mapping. Sie gehört entweder ins `model-inventory`-Schema oder in einen
Adapter-Discovery-Vertrag, nicht als versteckte Feature-Heuristik.

**Empfehlung.** F0005 sollte Modell-Arrival nur als Proposal erzeugen und
Adapter-Zuordnung aus `AdapterDescriptor.supported_models[]` bzw. einem
Inventory-Mapping ableiten. Prefix-Regeln höchstens als fallback mit
Warnung, nicht als normative Zuordnung.

### Neuer Befund 7 — Mittel: Tool-Risk-Klassen sind nützlich, aber nicht ganz disjunkt

**Beleg.** ADR-0015 definiert `medium` als lokal mit Side-Effect, inklusive
`shell_exec ohne Netz/State-Modifikation` (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:64-70`).
Die Config klassifiziert `shell_exec` als medium mit Constraint „no network,
no state-modifying syscalls" (`config/execution/tool-risk-inventory.yaml:50-53`).

**Bewertung.** `shell_exec` ist kein einzelnes Tool-Risiko, sondern ein
Container für beliebige Befehle. Die Constraint ist als Freitext nicht
ausführbar genug, um medium sicher von high/irreversible zu trennen. Für n=1
ist das als Seed akzeptabel, aber nicht als endgültiger Sicherheitsvertrag.

**Empfehlung.** `shell_exec` entweder splitten (`shell_readonly`,
`shell_worktree_write`, `shell_network`, `shell_dangerous`) oder im V1-Seed
auf `policy_gated` setzen, bis ein parser-/profilebasiertes Constraint-Modell
existiert.

### Neuer Befund 8 — Niedrig bis Mittel: Tool-Risk-Drift-Detection ist erkannt, aber nicht lieferbar verankert

**Beleg.** ADR-0015 nennt Tool-Risk-Drift-Detection als Follow-up: tatsächlich
aufgerufene Tools gegen Inventory auswerten und nicht klassifizierte Tools als
Digest-Card melden (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:142-144`).
Es gibt aber kein Feature dafür; Feature-Index endet bei F0005
(`docs/features/README.md:77-84`).

**Bewertung.** Durch Fail-Closed ist das kein Sicherheitsbruch. Für
Wartbarkeit ist es aber wichtig, weil ein wachsender Adapter-/MCP-Bestand sonst
leise immer mehr `default: high` trifft und HITL-Rauschen erzeugt.

**Empfehlung.** Als kleines v1a-Feature nach Runtime-Records anlegen:
`agentctl tools audit` liest `ToolCallRecord`, gruppiert unmatched/default
matches, erzeugt Digest-Card und schlägt Inventory-Erweiterungen vor.

## Perspektivenreview

### Architektur

Die Architektur ist gegenüber V0.2.0 deutlich konsistenter. Der Dispatcher ist
weiterhin Policy, nicht Execution (`docs/spec/SPECIFICATION.md:182-192`), und
`DispatchDecision` ist jetzt post-gate-final (`docs/spec/SPECIFICATION.md:539-546`).
ADR-0014 bleibt dicht, aber der Split-Marker ist ein angemessener Stopper für
weitere Bündelung (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:242-253`).
Die nächste Schwachstelle ist weniger ADR-Zuschnitt als die fehlende Umsetzung
der Runtime-Basis in Feature-Slices.

### Sicherheit

ADR-0015 hebt die Sicherheitslage klar an: Fail-Closed-Default und
Approval-Routing sind dokumentiert (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:87-105`).
Die Seed-Datei ist proportional für n=1, weil sie GitHub, Git, File, Web und
Notifications abdeckt (`config/execution/tool-risk-inventory.yaml:25-120`).
Der breite `shell_exec`-Seed ist die wichtigste verbleibende Kante
(`config/execution/tool-risk-inventory.yaml:50-53`). Tool-Risk-Drift muss
nicht vor v0, aber vor breiter Adapter-/MCP-Nutzung lieferbar werden.

### Betrieb

Deployment ist jetzt sauber: v1a lokal, v1b read-only, v2+ Postgres bei
zweiter Schreibrolle (`docs/spec/SPECIFICATION.md:382-412`). Reconciliation
ist als CLI-Pfad beschrieben (`docs/decisions/0011-runtime-audit-and-run-attempts.md:118-130`).
Die Testmatrix sollte nur nachziehen, damit Crash-Tests die drei Effektklassen
abbilden (`docs/spec/SPECIFICATION.md:622-630`). Der Project-Plan-Kopf
`0.2.0-draft` ist ein kleiner Betriebsdoku-Drift (`docs/plans/project-plan.md:1-4`).

### Daten

Runtime Records sind jetzt vollständig genug, um Audit und Retry zu tragen
(`docs/spec/SPECIFICATION.md:273-289`). F0005 verschiebt aber neue
Datenverträge in YAML-Dateien: pending proposals, pins, inventory und mapping
(`docs/features/F0005-benchmark-curated-pin-refresh.md:39-64`). Diese
Config-Dateien werden faktisch zu kleinen Datenbanken. Dafür braucht es
atomare Writes, Konfliktregeln und Hash-/Version-Audit.

### Kosten

OR-Caps und Global-Hard-Cap sind jetzt konsistent dokumentiert
(`docs/spec/SPECIFICATION.md:442-450`; `docs/decisions/0008-four-scope-budget-gate.md:37-46`).
Die Streichung der automatischen `cost-aware`-Aktivierung reduziert das Risiko
eines unkalibrierten teureren Modus (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:180-193`).
F0005 kann Kosten indirekt verbessern, aber der Testplan misst nur qualitativ
über 2–4 Wochen Token-Ausgaben (`docs/features/F0005-benchmark-curated-pin-refresh.md:121-123`).
Eine spätere Kostenmessung sollte Pins nicht nur nach Benchmark-Score, sondern
auch nach tatsächlichen Fix-Runden und Token pro erfolgreichem Work Item prüfen.

### Implementierung

V0 bleibt gut geschnitten: F0001/F0002 sind klein und schema-/CLI-fokussiert
(`docs/features/F0001-sqlite-schema-core-objects.md:20-38`;
`docs/features/README.md:77-80`). V1a ist dagegen noch unscharf, weil F0003,
F0004 und F0005 auf Runtime Records, Artifacts, Evidence und AuditEvents
aufsetzen, ohne dass diese als Feature geliefert sind
(`docs/features/F0003-cost-aware-routing-stub.md:54-55`;
`docs/features/F0004-benchmark-awareness-manual-pull.md:60-62`;
`docs/features/F0005-benchmark-curated-pin-refresh.md:46-50`). Das ist kein
Designfehler, aber ein Planungsfehler vor Implementierungsstart.

## Priorisierte Empfehlungen

### Sofort

1. **V1a-Runtime-Basis als Feature sichtbar machen.** Ein Feature für
   `Run`, `RunAttempt`, Runtime-Record-Tabellen, `AuditEvent`,
   `BudgetLedgerEntry`, `DispatchDecision`, `needs_reconciliation` und
   `agentctl runs reconcile` anlegen. Begründung: F0003/F0004/F0005 setzen
   genau diese Basis voraus (`docs/features/F0003-cost-aware-routing-stub.md:54-55`,
   `docs/features/F0005-benchmark-curated-pin-refresh.md:46-50`).

2. **F0005-Config-Write-Vertrag ergänzen.** `accept` darf nicht nur „Diff wird
   angezeigt" sagen (`docs/features/F0005-benchmark-curated-pin-refresh.md:92-94`),
   sondern muss atomare Writes, Locks, Konflikte, Hashes und AuditEvent-
   Payloads normieren.

3. **Spec §10.4 gegen ADR-0011 nachziehen.** Crash-Kriterium in drei
   Effektklassen aufteilen, statt pauschal „Idempotency-Keys" zu nennen
   (`docs/spec/SPECIFICATION.md:622-626`;
   `docs/decisions/0011-runtime-audit-and-run-attempts.md:73-84`).

### Danach

1. **`benchmark-task-mapping.yaml` entweder seed-en oder als von F0005 erzeugt
   markieren.** Aktuell referenziert die Spec einen Pfad, der nicht im Repo
   liegt (`docs/spec/SPECIFICATION.md:362-365`).

2. **F0005-Heuristiken als Eigenentscheidung kennzeichnen.** 3 pp Schwelle und
   Prefix-Adapter-Mapping sind pragmatische Defaults, keine belegte Wahrheit
   (`docs/features/F0005-benchmark-curated-pin-refresh.md:63-64`, `:99-102`).

3. **Tool-Risk-Drift-Detection als kleines Feature aufnehmen.** ADR-0015 kennt
   den Bedarf bereits (`docs/decisions/0015-tool-risk-inventory-and-approval-routing.md:142-144`).

4. **Project Plan Version aktualisieren.** Kopfzeile auf V0.2.3-draft ziehen
   (`docs/plans/project-plan.md:1-4`), damit Agenten nicht wieder alte
   Annahmen laden.

### Verschoben

1. **ADR-0014 aufspalten.** Erst bei der nächsten substantiellen Änderung, wie
   die ADR selbst fordert (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:242-253`).

2. **Learned Router / RouteLLM-Training.** Weiter v2-Kandidat, erst nach echter
   lokaler Dispatch-Historie (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:254-255`).

3. **Benchmark-Scheduler.** V1 bleibt manuell; F0004 verschiebt Scheduler auf
   v1.x (`docs/features/F0004-benchmark-awareness-manual-pull.md:43-51`).

## Schlussurteil

Claude hat die alten Befunde diesmal nicht nur teilweise geschlossen. V0.2.1
hat die Normdrifts aus V0.2.0 sauber repariert, V0.2.3 hat die sechs
„Urteilssachen" weitgehend richtig entschieden, und ADR-0015 ist die fehlende
Sicherheitsstütze für `approval=never`.

Die verbleibenden Probleme sind anders gelagert: F0005 ist ein sinnvoller
Workflow, aber noch kein ausreichend spezifizierter Config-Schreiber; Tool-Risk
ist stark, aber Drift-Detection und `shell_exec` brauchen Nacharbeit; und v1a
braucht ein sichtbares Runtime-Basis-Feature. Damit ist die Spec heute
implementierungsnäher als am 24.04., aber der Start in v1a sollte nicht
beginnen, bevor diese kleinen Verträge explizit gemacht sind.
