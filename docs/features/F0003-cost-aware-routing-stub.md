---
id: F0003
title: Cost-Aware Routing Stub
stage: v1
status: proposed
spec_refs: [§5.3, §8.6]
adr_refs: [ADR-0014]
---

# F0003 · Cost-Aware Routing Stub

## Context

ADR-0014 legt Cost-Aware-Routing als Dispatch-Policy fest. In v1 startet das
System im `pinned`-Modus: `routing-pins.yaml` dient als Lookup-Tabelle,
Default-Fallback aus `model-inventory.yaml`. Erst nach 5+ Pins oder 4
Wochen Nutzung wird der `cost-aware`-Modus aktiviert (Haiku-Confidence-
Probe, Tier-Routing). Dieser Stub liefert die minimale tragfähige Form.

## Scope

- Dispatcher-Komponente in Work als reine Lookup-Funktion im `pinned`-Mode:
  - Liest `config/dispatch/routing-pins.yaml`.
  - Falls keine Pin matched: liest `config/dispatch/model-inventory.yaml`
    `rules.defaults` (Claude Code + Sonnet als Default).
  - Erzeugt `DispatchDecision` (Runtime Record, ADR-0011) mit Adapter,
    Modell, Begründung (Pin vs. Default).
- CLI-Befehl `agentctl dispatch show <work-item-id>` zeigt, welcher Adapter
  + Modell aktuell gewählt würde (Dry-Run, ohne Run-Start).
- CLI-Befehl `agentctl dispatch pin --work-item-type <x> --adapter <a> --model <m>` schreibt einen Pin in `routing-pins.yaml`.
- **`cost-aware`-Modus als dokumentierter Aktivierungspfad**, aber in v1
  noch nicht implementiert — der Code-Pfad existiert als klar markierter
  `TODO` mit Verweis auf künftiges Feature.

## Out of Scope

- Haiku-Confidence-Probe (aktiviert in späterem Feature, wenn v1-Nutzung
  zeigt, dass Pins nicht reichen).
- Kendall-τ-Disagreement-Detection, Borda-Rank-Composite, Shadow-Mode —
  empirisch verworfen (siehe Plan-Appendix A).
- Learned Router — v2-Kandidat.
- Automatisches Anlegen von Pins aus Benchmarks — Awareness-Only-Prinzip
  (siehe F0004).
- Multi-Adapter-Ensemble/MoA — empirisch verworfen.

## Acceptance Criteria

1. `agentctl dispatch show <wid>` liefert für ein Work Item ohne Pin-Match
   den Default aus `model-inventory.yaml` (Claude Code + Sonnet 4.6).
2. Nach `agentctl dispatch pin --work-item-type long_coding_refactor
   --adapter claude-code --model claude-opus-4-7` matched ein Work Item mit
   `work_item_type=long_coding_refactor` den Pin, und `show` zeigt Opus 4.7.
3. `DispatchDecision` wird als Runtime Record persistiert (sobald ADR-0011
   implementiert ist; bis dahin als JSONL-Log).
4. Ausgabe von `show` enthält die Begründung: „Pin match" oder „Default
   (kein Pin)".
5. `agentctl dispatch pin` schreibt YAML, das von
   `config/dispatch/routing-pins.yaml` via normalem YAML-Parser wieder
   gelesen werden kann — keine Kommentar-Zerstörung.
6. Wird ein ungültiger Adapter oder ein Modell ohne Adapter angegeben,
   gibt `pin` einen klaren Fehler zurück.
7. Bestehende Pins werden beim Hinzufügen nicht überschrieben ohne
   `--force`-Flag.
8. CLI zeigt Warnung, wenn Pin ein Modell mit `adapter: null` referenziert
   (z. B. Gemini 3.1 Pro, das in v1 keinen Adapter hat).

## Test Plan

- Unit: Pin-Lookup-Logik gegen Fixture-YAMLs (leer, ein Pin, mehrere
  Pins, Kollision).
- Integration: Vollständiger `dispatch show`-Roundtrip mit echter YAML-
  Datei und temporärer DB.
- Manuell: Nutzer pint ein Work-Item-Type und prüft via `show`, dass das
  Pin tatsächlich greift.
- Regression: nach 5+ Pins + `agentctl dispatch mode` wird der
  Pfad-Hinweis auf `cost-aware`-Modus sichtbar (UI-Hinweis, noch keine
  Logik).

## Rollback

Dispatcher ist eine Code-Schicht vor dem Run-Start. Rollback = Dispatcher-
Code entfernen, Work-Item → Run verwendet fixen Claude-Code-Default.
`DispatchDecision`-Tabelle kann leer bleiben oder gedroppt werden (keine
fachliche Wahrheit hängt an ihr).
