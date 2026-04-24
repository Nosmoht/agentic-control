---
id: F0002
title: work add and work next CLI
stage: v0
status: proposed
spec_refs: [§5.3, §6.2]
adr_refs: [ADR-0001]
---

# F0002 · `work add` und `work next` CLI

## Context

V0 ist „Handbetrieb mit Schema": der Nutzer braucht genau zwei Einstiegspunkte,
um das Vokabular zu testen. `work add` erzeugt neue Work Items und
Observations/Decisions, `work next` zeigt, was als Nächstes ansteht.
Agent-Runs bleiben in V0 manuell — das CLI registriert sie, ruft sie nicht
auf.

## Scope

- `agentctl work add --title "…" [--project <id>] [--priority {low,med,high}]`
  → legt Work Item mit `state=proposed` an.
- `agentctl work add --observation "…" [--source-ref <id>]`
  → legt Observation an.
- `agentctl work add --decision "…" --subject <work-item-id>`
  → legt Decision im ADR-Minimalformat (Context, Decision, Consequence als
  Multiline-Eingabe) an.
- `agentctl work next [--project <id>]` → zeigt die nächsten ≤ 3 Work Items
  im Zustand `ready` oder `accepted`, sortiert nach `priority` und
  `created_at`.
- `agentctl work show <work-item-id>` → zeigt Work Item mit verknüpften
  Observations/Decisions.
- `agentctl work transition <work-item-id> <new-state>` → erlaubt manuelle
  Lifecycle-Transitionen (in V0 keine Automation).

## Out of Scope

- Automatisches Dispatching an Agent — kommt in v1 (F0003).
- HITL-Inbox — kommt in v1.
- Budget-Gate — kommt in v1.
- Run-Lifecycle — kommt in v1 (wenn Runs existieren).
- Multi-Projekt-Dependency — kommt in v2.

## Acceptance Criteria

1. `work add --title "X"` legt genau ein Work Item in der DB an; Rückgabe
   enthält die generierte ID und bestätigt Zustand `proposed`.
2. `work add --observation` / `--decision` funktionieren analog für
   Observation und Decision.
3. `work next` zeigt maximal 3 Einträge; bei leerer DB kommt eine
   sprechende Meldung „Keine offenen Work Items".
4. `work show <id>` rendert Work Item + alle Decisions, die es als Subject
   haben, und alle Observations mit matchender `source_ref`.
5. `work transition <id> <state>` lehnt ungültige Transitionen ab (z. B.
   `proposed → completed` direkt).
6. CLI-Exit-Codes sind definiert: 0 Erfolg; 2 Nutzerfehler (ungültige
   Args); 3 Validation-Fehler (DB-Constraint); 4 State-Transition-Fehler.
7. `--help` zeigt verwendbare Dokumentation.

## Test Plan

- Unit: Argparse-Tests für jedes Sub-Command.
- Integration: realer SQLite-DB-Roundtrip für jede Acceptance 1–5.
- Manuell: nach Installation führt der Nutzer `work add`, `work next`,
  `work show`, `work transition` durch und berichtet, ob das Vokabular
  paßt. Dokumentation im Plan (v0-Exit-Kriterium: 5+ Work Items manuell
  durchgezogen).

## Rollback

CLI ist eine lokale Binary / Python-Package. Rollback = Paket entfernen;
DB bleibt konsistent, weil jede Transaction atomar war (SQLite WAL).
