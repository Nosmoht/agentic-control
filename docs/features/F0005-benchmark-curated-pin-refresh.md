---
id: F0005
title: Benchmark-Curated Pin Refresh
stage: v1a
status: proposed
spec_refs: [§5.3, §6.2, §8.6]
adr_refs: [ADR-0014, ADR-0011, ADR-0016]
---

# F0005 · Benchmark-Curated Pin Refresh

## Context

F0004 pullt Benchmarks und zeigt Awareness-Tabellen; F0003 liest
`routing-pins.yaml` deterministisch. Zwischen beidem fehlt ein Workflow,
der Benchmarks **konsumiert** und daraus **Pin-Vorschläge** ableitet —
insbesondere wenn neue Modelle auftauchen oder das aktuell gepinnte
Modell von einem anderen meaningful überholt wird. Dieser Workflow ist
explizit **kein** Runtime-Auto-Dispatch (Plan-Appendix A verwirft das
empirisch), sondern eine wöchentliche Human-in-the-Loop-Kuration:
Benchmarks → Vorschlag → Nutzer akzeptiert oder verwirft → Pins
aktualisiert. Ziel: initiale Modellwahl bleibt aktuell, besonders für
Coding-Tasks mit belegtem 7,6-pp-Delta; Token-Reduktion indirekt durch
weniger Fix-Runden bei besserer Erstwahl.

## Scope

- CLI-Befehl `agentctl benchmarks refresh` (setzt auf F0004 auf):
  - Prüft Freshness des letzten `benchmarks pull` (Warnung bei > 14 Tagen).
  - **Modell-Arrival-Detection:** `model_id` in aktueller Benchmark-
    Response, die nicht in `config/dispatch/model-inventory.yaml` steht
    → `candidate_new_model`-Proposal.
  - **Pin-Drift-Detection:** für jeden Pin in `routing-pins.yaml`,
    vergleiche Benchmark-Score des gepinnten Modells gegen Top-Modell
    der zugeordneten Task-Klasse (siehe
    `config/dispatch/benchmark-task-mapping.yaml`). Wenn
    `top_score - pinned_score ≥ drift_threshold_pp` (Default 3, siehe
    Anmerkung unten): `candidate_pin_change`-Proposal.
  - Schreibt Proposals in `config/dispatch/pending-proposals.yaml`
    (Append-only, Expiry 14 Tage).
- CLI-Befehl `agentctl dispatch review`:
  - Zeigt pending Proposals sortiert nach Relevanz (Delta-Size +
    Arrival-Recency).
  - Pro Proposal: Payload (Modell, alter Score, neuer Score,
    Adapter-Empfehlung), Rationale (menschlich lesbar), Expiry.
- CLI-Befehl `agentctl dispatch accept <proposal-id>`:
  - Schreibt den Vorschlag in `routing-pins.yaml` bzw.
    `model-inventory.yaml` **gemäß ADR-0016-Config-Write-Vertrag**
    (Atomic-Write, File-Lock, optimistische Versionsprüfung,
    `AuditEvent` mit `before_hash`/`after_hash`).
  - Zeigt Diff vor dem Schreibvorgang.
  - Bei `ConflictDetected` (Datei wurde zwischen Read und Write
    extern modifiziert): Abbruch mit klarer Fehlermeldung; Nutzer
    muss `dispatch review` erneut aufrufen.
  - Entfernt akzeptierte Proposal aus `pending-proposals.yaml`
    (ebenfalls über ADR-0016-Vertrag).
- CLI-Befehl `agentctl dispatch reject <proposal-id> [--reason <text>]`:
  - Entfernt Proposal.
  - Schreibt `Observation(kind=dispatch_rejection)` mit optionaler
    Begründung.
- `config/dispatch/benchmark-task-mapping.yaml` als kleine YAML, die
  Task-Klassen auf Benchmarks mappt:
  ```yaml
  coding: swe_bench_verified
  reasoning: gpqa_diamond
  general: arena_elo
  math: aime_2025
  ```
- Drift-Schwelle als Config-Wert in derselben Datei (Default 3 pp).

> **Eigenentscheidung (V0.2.4-draft):** Die 3-pp-Default-Schwelle ist
> ein konservativer Startwert ohne empirischen Anker. Begründung:
> größer als typisches Benchmark-Run-Rauschen (~1 pp), kleiner als das
> einzig belegte Inter-Modell-Delta (Coding 7,6 pp, Plan-Appendix A).
> Konfigurierbar pro Repo. Erwartung: bei zu vielen Wochen-Vorschlägen
> Schwelle erhöhen, bei verpasstem Modell-Arrival senken. Eventuell
> spätere ADR, falls die Kalibrierung Komplexität bekommt
> (Counter-Counter-Review-2026-04-26, neuer Befund 5).

## Out of Scope

- **Automatische Annahme** von Proposals — jede Änderung an Pins oder
  Inventory läuft zwingend über `accept`.
- **Scheduler** (DBOS-Scheduled-Workflow) — kommt in v1.x.
- **Runtime-Auto-Dispatch** auf Benchmark-Rang — bleibt verworfen
  (Appendix A).
- **Multi-Benchmark-Composite** (Kendall-τ, Borda) — verworfen.
- **Pricing-Refresh** (Preise in `model-inventory.yaml` aktualisieren) —
  separates späteres Feature; hier nur Benchmark-Scores.
- **Deprecation von Modellen** (Modell verschwindet aus Inventar) —
  separates späteres Feature.

## Acceptance Criteria

1. `agentctl benchmarks refresh` gegen drei Fixture-Responses (eine mit
   neuem Modell, eine mit Drift, eine stabil) erzeugt genau drei
   Proposals: 1× `candidate_new_model`, 1× `candidate_pin_change`,
   0× bei stabil.
2. Jede Proposal in `pending-proposals.yaml` hat die Felder: `id`,
   `created_at`, `expires_at`, `type`, `payload`, `rationale`.
3. Proposals älter als `expires_at` werden beim nächsten `refresh`
   automatisch entfernt und als `expired` in das Observation-Log
   geschrieben.
4. `agentctl dispatch review` ohne pending zeigt eine klare
   „Nichts zu tun"-Meldung; mit pending zeigt sie sortiert nach
   Relevanz.
5. `accept <id>` modifiziert die Ziel-YAML korrekt, zeigt einen Diff,
   erzeugt `AuditEvent`, entfernt die Proposal; ungültige ID → klare
   Fehlermeldung.
6. `reject <id>` entfernt die Proposal; `--reason` landet im
   Observation-Log.
7. Benchmark-Task-Mapping wird beim Refresh validiert (alle Benchmarks
   bekannt, sonst Warnung + Skip der Klasse, kein Abbruch).
8. Modell-Arrival-Proposal liest die Adapter-Zuordnung aus
   `config/dispatch/model-inventory.yaml.rules.adapter_assignment_rules`
   (V0.3.0-draft). F0005 hardcodet **keine** eigene Prefix-Regel
   mehr — die Zuordnung lebt im Inventory-Schema, damit der
   Orchestrator weiterhin keinen Adapter special-casen muss
   (ADR-0014 Aufruf-Disziplin). Bei Match `adapter: null` wird eine
   Warnung emittiert („Modell hat keinen unterstützten Adapter in
   V1"); der Vorschlag bleibt im Proposal sichtbar, kann aber nicht
   `accept`-iert werden, bis ein Adapter zugeordnet ist.

   **Schema von `adapter_assignment_rules`** (V0.3.6-draft, Closure
   R3-Lücke aus 2026-04-29 Audit). Liste ordered, first-match-wins:

   ```yaml
   rules:
     adapter_assignment_rules:
       - provider_pattern: "anthropic/*"
         adapter: claude_code
       - provider_pattern: "openai/*"
         adapter: codex_cli
       - provider_pattern: "x-ai/*"
         adapter: codex_cli      # via OpenRouter compatibility
       - provider_pattern: "*"   # fall-through
         adapter: null
   ```

   Pydantic-Modell `AdapterAssignmentRule` mit:
   - `provider_pattern: str` (Glob via stdlib `fnmatch`, gegen
     `model_id` der Form `<provider>/<model-name>`)
   - `adapter: Literal["claude_code","codex_cli"] | None`

   Validator-Regel: letzter Eintrag muss `provider_pattern: "*"` sein
   (Fail-Closed für unbekannte Provider; explicit catch-all). Schreibt
   Validierung beim Lesen der `model-inventory.yaml`, bricht
   `agentctl benchmarks refresh` ab, wenn die Datei keinen Catch-all
   enthält.
9. Drift-Detection respektiert Benchmark-Freshness: Benchmarks älter
   als 60 Tage werden für Drift ignoriert (zu unsicheres Signal),
   eine Warnung wird angezeigt.
10. Alle drei beschriebenen Config-Dateien (`routing-pins.yaml`,
    `model-inventory.yaml`, `pending-proposals.yaml`) werden über den
    **ADR-0016-Config-Write-Vertrag** beschrieben: atomarer Rename,
    File-Lock, optimistische Versionsprüfung, `AuditEvent`-Eintrag
    mit Before/After-Hash. Parallele CLI-Sessions blockieren oder
    fehlschlagen mit klarer Fehlermeldung.

## Test Plan

- **Unit:** Drift-Berechnung gegen Mock-Benchmark-Daten,
  Arrival-Detection gegen Inventory-Mock, Expiry-Logik,
  YAML-Write-Roundtrip mit Kommentar-Erhalt.
- **Integration:** Voller `refresh` → `review` → `accept`-Zyklus mit
  Fixture-Benchmarks; danach `agentctl dispatch show <wid>` aus F0003
  liefert das neue Modell.
- **Negative:** Invalide Benchmark-Task-Mapping (unbekannter Benchmark-
  Name), korrupte `pending-proposals.yaml`, Proposal für bereits
  entfernten Pin, Proposal nach Expiry angenommen.
- **Manuell:** Nutzer führt den Loop wöchentlich durch, beobachtet über
  2–4 Wochen qualitativ, ob Token-Ausgaben auf Coding-Tasks sinken
  (Primärsignal); Metrik-Gegenstück in Spec §10.2.

## Rollback

`pending-proposals.yaml` und `benchmark-task-mapping.yaml` löschen —
keine fachliche Wahrheit hängt daran. `routing-pins.yaml` und
`model-inventory.yaml` via Git auf vorherigen Commit zurücksetzen;
jede Änderung durch diesen Workflow ist durch `AuditEvent`-Einträge
(ADR-0011) nachverfolgbar.
