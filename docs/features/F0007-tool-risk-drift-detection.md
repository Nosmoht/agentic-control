---
id: F0007
title: Tool-Risk-Drift Detection
stage: v1a
status: proposed
spec_refs: [§5.4, §8]
adr_refs: [ADR-0015, ADR-0011, ADR-0016]
depends_on: [F0006]
---

# F0007 · Tool-Risk-Drift Detection

## Context

ADR-0015 etabliert das Tool-Risk-Inventory (`config/execution/tool-
risk-inventory.yaml`) als Voraussetzung für `approval=never`. Der
fail-closed-Default schützt vor neuen, nicht klassifizierten Tools
— aber unsichtbar: jeder unbekannte Tool-Aufruf landet auf
`default: high, approval: required` und löst HITL-Gates aus, ohne
dass der Nutzer den Drift sieht. Mit wachsendem Adapter-/MCP-Bestand
führt das zu unnötigem HITL-Rauschen und schwer rückzuverfolgenden
Inventory-Lücken. Der dritte Codex-Follow-up-Review (Befund 8) hat
F0007 als kleines additives Feature vorgeschlagen.

## Scope

- CLI-Befehl `agentctl tools audit [--since <date>] [--default-only]`:
  - **Primäre Datenquelle:** `policy_decision`-Rows mit
    `policy=tool_risk_match` (F0006), gefiltert auf den angegebenen
    Zeitraum (Default: letzte 14 Tage). Damit liest F0007 die
    **damals** getroffene Match-Entscheidung — nicht eine Re-
    Klassifikation gegen das aktuelle Inventory (Counter-Counter-
    Counter-Review-2026-04-26 Befund 4). `tool_call_record` liefert
    den Tool-Namen und Aufrufdetails per FK.
  - Gruppiert nach gematchtem Pattern: Anzahl Calls, Anzahl
    Default-Hits, Beispiel-Aufrufe.
  - **Fallback** für Alt-Daten ohne `PolicyDecision` (z. B. vor
    F0006-Implementierung): Re-Match gegen aktuelles Inventory mit
    expliziter Warnung „rekonstruiert, nicht historisch".
- **Digest-Card-Generation** (ADR-0012):
  - Wenn Default-Hit-Anteil > Schwelle (Default 5 %) ODER mehr als
    drei verschiedene unbekannte Tool-Namen im Zeitraum → Digest-
    Card `tool_risk_drift` mit Tool-Liste und Vorschlag.
  - Status `info` (kein Work-Item-Block, ADR-0012); Verfall nach
    14 Tagen.
- **Inventory-Erweiterungs-Vorschläge:**
  - Pro unbekanntem Tool: schlägt minimalen Eintrag vor (`pattern:
    <tool-name>, risk: high, approval: required` als
    konservativer Default; Nutzer kann manuell zu medium/never
    senken).
  - CLI-Befehl `agentctl tools propose <tool-name>` startet einen
    Editor-Workflow, der den Vorschlag in
    `tool-risk-inventory.yaml` einfügt (über ADR-0016-Vertrag).
  - **Einfügepositions-Regel** (Counter-Counter-Counter-Review-
    2026-04-26 Befund 6): Spezifische Patterns werden **vor** dem
    nächsten Catch-all-Pattern derselben Familie eingefügt
    (`gh_issue_reopen` vor `gh_*`). Neue Catch-alls (`*` am Ende,
    `<prefix>_*`-Pattern) landen am Ende ihrer Familie. Nach jedem
    `propose` läuft ein Dry-Run-Match gegen Fixture-Tool-Namen, der
    bestätigt, dass das neue Pattern tatsächlich gewinnt; sonst
    Abbruch mit Hinweis und Rollback der Änderung.
- Drift-Schwelle als optional Config-Wert in `tool-risk-
  inventory.yaml.drift_threshold_pct` (Default 5 %, Eigenentscheidung).

## Out of Scope

- **Auto-Erweiterung** des Inventars — bleibt manuell, weil jede
  Klassifikation eine Sicherheits-Entscheidung ist (fail-closed
  bedeutet bewusstes Down-Klassifizieren).
- **Pattern-Matching-Engine zur Call-Zeit** (Glob-Resolution, Erste-
  Match-Logik im Orchestrator) — F0007 ist **nicht** auf den
  Live-Matcher angewiesen, weil es `PolicyDecision(tool_risk_match)`-
  Records aus F0006 liest. Der Live-Matcher wird im Rahmen der
  Execution-Harness-Implementierung (ADR-0010) als eigenes Feature
  geliefert (Counter-Counter-Counter-Review-2026-04-26 Befund 5).
  Fallback-Re-Match (siehe Scope) nutzt eine kleine in-process
  Glob-Implementierung — Test-Fixture-tauglich, nicht
  produktionsbindend.
- **Tool-Klassifikations-Vorschläge mit ML** (z. B. „dieses Tool
  sieht aus wie file_write") — v2-Kandidat, hier explizit
  ausgeschlossen.
- **Cross-Inventory-Drift** (ein Tool wird in zwei Adaptern unter
  verschiedenen Namen klassifiziert) — eigenes Feature, falls nötig.

## Acceptance Criteria

1. `agentctl tools audit` mit Fixture-`tool_call_record`-Rows
   (10 calls, davon 3 default-hits): liefert Tabelle mit Anzahl
   pro Pattern + Default-Hit-Spalte.
2. Default-Hit-Anteil 30 % (über Schwelle 5 %): Digest-Card mit
   Status `info` wird erzeugt; `agentctl inbox` zeigt sie.
3. `agentctl tools propose <tool-name>` öffnet Editor mit
   vorgeschlagenem YAML-Snippet (`pattern: <name>, risk: high,
   approval: required`), Speichern schreibt über ADR-0016-Vertrag
   in `tool-risk-inventory.yaml` (Atomic, Lock, Audit-Event).
4. **Digest-Card-Idempotenz** (Counter-Counter-Counter-Review-
   2026-04-26 Befund 10, V0.3.2-Verfeinerung): Card-ID wird
   deterministisch aus `sha256(period_start +
   sorted(unmatched_tool_names) + threshold_kind)` gebildet, wobei
   `threshold_kind ∈ {"default_hit_pct", "unknown_tool_count"}`
   (CHECK-Constraint, exakt zwei Werte). Wiederholter `audit`-Lauf
   im selben 14-Tage-Fenster mit identischer unbekannter Tool-Menge
   und gleichem `threshold_kind` erzeugt **keine** zweite Card.
   Ändert sich die Tool-Menge oder die ausgelöste Schwelle, entsteht
   eine neue Card mit neuer ID. Mindest-Denominator für
   `default_hit_pct`: ≥ 20 Tool-Calls im Zeitraum (sonst Skip);
   `unknown_tool_count` greift ab > 3 unbekannten Tool-Namen
   unabhängig von der Anzahl Calls.
5. Drift-Schwelle ist über `drift_threshold_pct` konfigurierbar;
   Default 5 % wird bei nicht gesetztem Feld verwendet.
6. `--default-only`-Flag filtert die Audit-Tabelle auf Default-Hits.
7. **Stale-Detection:** Audit liefert eine Warnung, wenn das letzte
   Inventory-Update älter als 60 Tage ist (analog zu F0004).

## Test Plan

- **Unit:** Aggregations-Logik gegen Mock-Records; Schwellen-
  Berechnung; Digest-Card-Idempotenz-Check.
- **Integration:** Voller Audit-Roundtrip auf temporärer DB mit
  Beispiel-Records; `tools propose` schreibt korrekt in temp-YAML.
- **Negative:** `audit` ohne `tool_call_record`-Tabelle (F0006
  noch nicht migriert); `propose` mit existierendem Pattern.
- **Manuell:** Nutzer läuft `audit` über reale 14-Tage-Run-Historie,
  identifiziert ein wachsend genutztes Tool (z. B. neuer
  MCP-Server), fügt es via `propose` ins Inventar ein.

## Rollback

`agentctl tools audit` und `propose` sind reine CLI-Lese-/Schreib-
Operationen. Rollback = Befehle entfernen; Inventar bleibt manuell
pflegbar. Digest-Cards verfallen nach 14 Tagen automatisch (ADR-0012).
