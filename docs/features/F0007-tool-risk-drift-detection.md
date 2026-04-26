---
id: F0007
title: Tool-Risk-Drift Detection
stage: v1a
status: proposed
spec_refs: [§5.4, §8]
adr_refs: [ADR-0015, ADR-0011]
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
  - Liest `tool_call_record`-Rows (F0006) im angegebenen Zeitraum
    (Default: letzte 14 Tage).
  - Joint mit der Pattern-Matching-Engine (siehe Out of Scope) auf
    den Treffer pro Tool-Call (`pattern` oder `default`).
  - Gruppiert nach Tool-Pattern: Anzahl Calls, Anzahl Default-Hits,
    Beispiel-Aufrufe.
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
- Drift-Schwelle als optional Config-Wert in `tool-risk-
  inventory.yaml.drift_threshold_pct` (Default 5 %, Eigenentscheidung).

## Out of Scope

- **Auto-Erweiterung** des Inventars — bleibt manuell, weil jede
  Klassifikation eine Sicherheits-Entscheidung ist (fail-closed
  bedeutet bewusstes Down-Klassifizieren).
- **Pattern-Matching-Engine selbst** (Glob-Resolution, Erste-Match-
  Logik) — eigenes Feature, das F0007 als Konsument benötigt; F0007
  blockiert nicht auf seine Implementierung, kann mit Stub-Matcher
  laufen.
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
4. Wiederholter `audit`-Lauf erzeugt **keine** doppelte Digest-Card,
   wenn die letzte noch im Inbox ist (Idempotenz).
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
