---
name: spec-navigator
description: Load only the spec section or ADR relevant to the current task instead of the entire specification. Use whenever a question maps to a specific module, lifecycle, ADR, or research brief — not for repo-wide exploration.
---

# Spec Navigator

Dieses Skill realisiert Progressive Disclosure über die Spec. Es vermeidet
CLAUDE.md-/Context-Bloat durch gezieltes Nachladen.

## Wann dieses Skill greifen

- Fragen nach einem bestimmten Modul (Interaction, Work, Execution,
  Knowledge, Portfolio).
- Fragen nach einer konkreten Architekturentscheidung (ADR-NNNN).
- Fragen nach einem Research-Brief (Brief NN).
- Fragen nach einem Lifecycle, einem Kernobjekt, einer Metrik.

## Wann NICHT

- Repo-weite Suche ohne konkrete Zielsektion (dann normale Exploration).
- Trivialfragen, die bereits aus AGENTS.md beantwortet sind.
- Implementierungsarbeit (in V0.3.4-draft noch kein Code).

## Navigations-Regeln

### Schritt 1 — Fragentyp erkennen

| Frageform | Ziel |
|---|---|
| „Welches Modul?" / „Was tut X?" | `docs/spec/SPECIFICATION.md §5` (Bausteinsicht) |
| „Warum X?" / „Entscheidung zu X?" | `docs/decisions/NNNN-*.md` — passenden ADR laden |
| „Woher weiß ich X?" / „Evidenz für X?" | `docs/research/NN-*.md` — passenden Brief laden |
| „Welcher Lifecycle?" | `docs/spec/SPECIFICATION.md §6.1` |
| „Welche Metrik?" | `docs/spec/SPECIFICATION.md §10` |
| „Welches Tool?" | ADR laden, dann bei Bedarf zugehöriger Research-Brief |

### Schritt 2 — Minimal laden

- **Nie** die komplette Spec auf einmal laden, wenn eine Sektion genügt.
- Für ADRs: eine Datei = eine Entscheidung. Maximal drei ADRs parallel
  laden.
- Für Research-Briefs: gezielt den Brief, nicht das ganze `docs/research/`.
- Bei Mehrfachbezug: zuerst `ARCHITECTURE.md` lesen (kurzer Überblick),
  dann nachladen.

### Schritt 3 — Zitier-Disziplin

- Wenn eine Antwort aus einem ADR kommt, Referenz in der Antwort: „siehe
  ADR-NNNN".
- Wenn aus Research: „siehe Brief NN".
- Wenn aus Spec: „siehe SPECIFICATION.md §N.M".

## Indextabelle

### Module → Spec-Abschnitt

- Interaction → `SPECIFICATION.md §5.2`
- Work → `§5.3`
- Execution → `§5.4`
- Knowledge → `§5.5`
- Portfolio → `§5.6`

### Thema → ADR

- Modul-Schnitt → ADR-0001
- Durable Execution → ADR-0002
- Persistenz → ADR-0003
- Agent-Aufrufe & LLM-Wrapper → ADR-0004
- Standards-Lifecycle → ADR-0005
- Sandbox (8 Schichten) → ADR-0006
- HITL → ADR-0007
- Budget → ADR-0008
- AGENTS.md-Pattern → ADR-0009

### Thema → Research-Brief

- Claude Code → 01
- Codex CLI → 02
- Durable Execution → 03
- Agent-Libraries → 04
- Agent-Muster → 05
- DDD-Skalen → 06
- Trust/Sandboxing → 07
- PKM → 08
- HITL → 09
- Work-Admission → 10
- Learning → 11
- Persistenz → 12
- Kosten → 13
- Kontext-Anzahl (Design) → 14
- MVP-Staging (Design) → 15
- Doku-Struktur → 16
- Agent-Repo-Prep → 17
- Synthese → 99

## Anti-Patterns

- **Kein** Laden von `archive/**` für normative Fragen. Nur für historischen
  Kontext.
- **Kein** Volllast-Read der gesamten `docs/research/` auf einmal.
- **Kein** Duplikation von Spec-Inhalt in die Antwort — referenzieren, nicht
  kopieren.
