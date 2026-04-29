---
id: F0004
title: Benchmark Awareness (Manual Pull)
stage: v1a
status: proposed
spec_refs: [§5.5, §8.6, §6.2]
adr_refs: [ADR-0014]
---

# F0004 · Benchmark Awareness (Manual Pull)

## Context

Der Nutzer möchte regelmäßig offizielle Benchmark-Ergebnisse ziehen, um zu
wissen, welches LLM in welchem Bereich führt. **Wichtig:** ADR-0014 und
§8.6 haben empirisch festgehalten, dass Benchmarks **nicht automatisch** in
Dispatch-Entscheidungen fließen — weder via Rank-Composite noch via
Task-Class-Specializer. Benchmarks sind **Awareness-Evidence**: sie
informieren den Nutzer, damit dieser bei Bedarf einen Pin setzt (F0003).
In v1 ist das Pullen **manuell**; ein Scheduler entsteht frühestens in
v1.x.

## Scope

- CLI-Befehl `agentctl benchmarks pull [--source <name>]` pullt JSON aus
  den konfigurierten Quellen:
  - HuggingFace Open LLM Leaderboard (HF Datasets API:
    `open-llm-leaderboard/results`).
  - SWE-bench Verified Leaderboard (JSON).
  - LiveBench (monatliches GitHub-Release).
  - Aider Polyglot Leaderboard (JSON im Repo).
  - Chatbot Arena Community-API (z. B. `api.wulong.dev`).
- Payloads werden normalisiert nach einem internen Schema (Pydantic
  v2, Single-Source per ADR-0018, Closure R3-Lücke aus 2026-04-29
  Audit). Modell `BenchmarkScore` in
  `src/agentic_control/contracts/benchmarks.py`:

  | Feld | Typ | Pflicht | Bemerkung |
  |---|---|---|---|
  | `source` | `Literal["hf_open_llm","swe_bench_verified","livebench","aider_polyglot","arena_elo"]` | ✓ | CHECK-Constraint |
  | `pulled_at` | `datetime` (UTC) | ✓ | |
  | `model_id` | `str` | ✓ | Auflösungs-Regel siehe unten |
  | `task_class` | `str` | ✓ | freier Slug, z. B. `coding_swe_bench_verified` |
  | `metric` | `str` | ✓ | z. B. `pass_rate`, `elo`, `accuracy` |
  | `score` | `ScoreValue` | ✓ | discriminated union, siehe unten |
  | `rank` | `int \| None` | ✗ | |
  | `meta` | `dict[str, Any]` | ✗ | quellen-spezifische Extras |

  **`ScoreValue` discriminated union** (Pydantic-Tag `kind`):
  - `kind="single_float"`, `value: float` (z. B. arena Elo, accuracy)
  - `kind="ratio"`, `numerator: int`, `denominator: int` (z. B.
    SWE-bench `resolved/total`)
  - `kind="percentile"`, `pct: float` (0.0–100.0)

  **`model_id`-Auflösung** beim Insert in `evidence`/`artifact`:
  Vergleich mit Einträgen in `model-inventory.yaml`. Match → kanoni-
  scher `model_id`. Kein Match → `model_id` wird als
  `unknown:<raw>` gespeichert (sichtbar für F0005 Modell-Arrival-
  Detection), kein Fail.

  **Schema-Mismatch-Verhalten**: Source-Adapter wirft
  `BenchmarkSchemaError` mit `source`, `raw_payload_excerpt`,
  `validation_error` → wird in stderr geloggt, der konkrete Pull für
  diese Quelle wird übersprungen, der Gesamt-Pull läuft weiter (AC 5).
- Speicherung: jeder Pull erzeugt ein `Evidence(kind=benchmark)`-Record
  mit Referenz auf ein `Artifact(kind=benchmark_raw)`, das den
  Rohpayload enthält.
- CLI-Befehl `agentctl benchmarks show [--task <name>] [--model <id>]`
  zeigt aktuelle Ranking-Tabellen aus der Evidence-Datenbank.
- CLI-Befehl `agentctl benchmarks sources` listet konfigurierte Quellen +
  Freshness (letztes erfolgreiches Pull pro Quelle).

## Out of Scope

- Automatischer Scheduler (DBOS-Workflow) — kommt in v1.x.
- Auto-Dispatch basierend auf Benchmark-Rangs — empirisch verworfen
  (§8.6).
- Learned Router — v2.
- Benchmark-Disagreement-Detection mit Kendall-τ — empirisch verworfen.
- Push-Notifications zu Benchmark-Änderungen — kommt als Digest-Card in
  späterem Feature (ADR-0012).
- Pulls aus kommerziellen APIs (Artificial Analysis, Vals AI) — nicht in
  v1.

## Acceptance Criteria

1. `agentctl benchmarks pull` pullt aus mindestens 3 der 5 konfigurierten
   Quellen erfolgreich; Quellen mit Fehler werden als solche berichtet
   (nicht fatal).
2. Nach einem Pull existieren `Evidence(kind=benchmark)`-Rows in der DB,
   jede verknüpft mit einem `Artifact(kind=benchmark_raw)`, dessen Inhalt
   der unveränderte JSON-Response ist.
3. `agentctl benchmarks show --task coding_swe_bench_verified` zeigt die
   Top-5-Modelle mit Score, Datum, Quelle.
4. `agentctl benchmarks sources` zeigt pro Quelle das letzte
   `pulled_at`-Datum und eine Freshness-Spalte (grün < 14 Tage, gelb 14–60
   Tage, rot > 60 Tage).
5. Ein Source-Fehler (Netzwerk, 404, Schema-Mismatch) erzeugt einen Log-
   Eintrag mit Details, bricht aber den Gesamt-Pull nicht ab.
6. Benchmark-Daten beeinflussen **keinen** Dispatch automatisch (F0003
   liest `routing-pins.yaml` und `model-inventory.yaml`, nicht die
   Evidence-Tabelle).
7. `agentctl benchmarks show` warnt, wenn alle Quellen älter als 60 Tage
   sind (Stale-Warnung).

## Test Plan

- Unit: Source-Adapter pro Quelle mit Fixture-JSON; Normalisierung
  deterministisch.
- Integration: Voller Pull gegen 1–2 real erreichbare Quellen
  (flaky-test-tolerant); Verifikation, dass `Evidence` + `Artifact` korrekt
  verknüpft sind.
- Negative: bewusste Schema-Abweichung in Fixture → Source-Adapter-Fehler,
  kein Crash.
- Manuell: Nutzer führt `benchmarks pull` aus, betrachtet `benchmarks
  show`, prüft, ob die Zahlen plausibel sind.

## Rollback

Benchmark-Daten sind reines Evidence-Material. Rollback = Tabellen `evidence`
und `artifact` um `kind=benchmark*`-Rows säubern. Keine fachliche
Entscheidung hängt an ihnen.
