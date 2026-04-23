# Forschungsplan

Dieser Plan strukturiert die wissenschaftliche Recherchearbeit, die der
Neuerfindung eines persönlichen agentischen Steuerungssystems vorausgeht.
Die Dokumente `00-11` und `REVIEW.md` im Wurzelverzeichnis sind Ausgangs-Input,
keine Quellen­wahrheit.

## Ziel

Jede architektonische Aussage, die am Ende in eine schlanke V1-Spezifikation
einfließt, soll entweder durch externe Literatur belegt oder explizit als
Design-Entscheidung gekennzeichnet sein.

## Arbeitsprodukt

- 15 einzelne Research-Briefs (`01-…` bis `15-…`) — jede Datei behandelt
  genau ein Thema.
- 1 Synthese-Dokument (`99-synthesis.md`), das die Briefs zusammenführt und
  daraus eine V1-Architektur konstruiert.

## Sprache

Deutsch, gemäß expliziter Projekt-Entscheidung vom 2026-04-23.
Quellen und Zitate bleiben in Originalsprache.

## Brief-Template

Jeder Brief folgt dieser Struktur:

```
---
topic: <Kurzname>
tier: A|B|C|D
date: <YYYY-MM-DD>
status: draft|reviewed|final
---

# Titel

## Forschungsfrage
Präzise Formulierung dessen, was dieser Brief beantworten soll.

## Methodik
Suchstrategie, konsultierte Quellenklassen.

## Befunde
Kernerkenntnisse mit inline-Belegen [^1][^2].

## Quellenbewertung
- Tier 1 (offizielle Docs, Peer-Reviewed, RFCs): n Quellen
- Tier 2 (Engineering-Blogs mit Metriken, Produktions-Cases): n Quellen
- Tier 3 (Tutorials, Meinungs-Posts): n Quellen
- Cross-Validation erfüllt: ja/nein (Regel: ≥2 unabhängige Quellen, davon
  ≥1 Tier-1/2; oder 1 Tier-1 mit konkreten Belegen wie Benchmarks).

## Implikationen für unser System
Was folgt aus den Befunden für Architektur-Entscheidungen?

## Offene Unsicherheiten
Was blieb nach maximal drei Suchzyklen ungeklärt?

## Quellen
[^1]: <URL/Zitation> — Tier, Datum, Kernaussage.
...
```

## Quellenqualität

Regeln aus `~/workspace/claude-config/rules/web-research.md`:

- **Tier 1 bevorzugt**: offizielle Hersteller-Dokumentation, Peer-Reviewed
  Paper (arXiv, ACM, IEEE), RFCs/Specs, Foundation-Dokumente (CNCF, OWASP, NIST).
- **Tier 2**: Produktions-Case-Studies mit Metriken, Engineering-Blogs mit
  Benchmarks, Konferenz-Talks.
- **Tier 3**: Tutorials, Blog-Posts ohne Metriken, Stack-Overflow. Zwei Tier-3
  allein erfüllen Cross-Validation NICHT.
- **Verwerfen**: Marketing, Meinung ohne Evidenz, Quellen älter als 18 Monate
  (außer RFCs/Specs/Paper ohne Nachfolger).

Für Tier A (aktueller Tooling-Stand) liegt die Messlatte strenger: Informationen
älter als 6 Monate sind nur gültig, wenn seit Januar 2026 keine wesentliche
Änderung dokumentiert ist.

## Themenkatalog

### Tier A — Aktueller Tooling-Stand (2025–2026)

| # | Thema | Forschungsfrage |
|---|-------|-----------------|
| 01 | Claude Code | Welche Architektur, Permission-Modelle, Subagents, Hooks, Skills, MCP-Features und Sandbox-Mechanismen bietet Claude Code aktuell? |
| 02 | Codex CLI | Welche Architektur, Permission-Modi, Sandbox, Session-Modell und Lifecycle-Eigenschaften hat die Codex CLI aktuell? |
| 03 | Durable Execution Frameworks | Wie unterscheiden sich Temporal, Restate, DBOS und Inngest 2026 in Modell, Betriebskosten und Einsatzfeld — und sind sie für Single-User-Systeme sinnvoll? |
| 04 | Agent-Orchestration-Libraries | Wie unterscheiden sich LangGraph, OpenAI Agents SDK, Anthropic Agent SDK und Pydantic AI 2026 in Modell und Maturität? |
| 05 | Aktuelle Agent-Architektur-Muster | Welche Muster gelten nach Anthropic „Building Effective Agents" (Update), OpenAI-Playbook und wissenschaftlichen Surveys 2025–2026 als stabil? |

### Tier B — Konzeptionelle Fundamente

| # | Thema | Forschungsfrage |
|---|-------|-----------------|
| 06 | DDD-Skalenschwellen | Ab welcher Systemgröße rentiert sich Domain-Driven Design, und welche Alternativen existieren für kleine/Single-User-Systeme? |
| 07 | Trust-Zonen & Agent-Sandboxing | Was sagen OWASP LLM Top 10, NIST AI RMF und aktuelle Forschung zu Trust-Zonen und Sandboxing für code­ausführende Agenten? |
| 08 | Personal Knowledge Management | Welche PKM-Architekturen (GTD, PARA, Zettelkasten, Johnny.Decimal) haben empirische Evidenz, und wie integrieren sie Task-Tracking? |
| 09 | Human-in-the-Loop-Eskalation | Welche UX- und System-Muster für Eskalation an den Menschen funktionieren empirisch in agentischen Systemen? |
| 10 | Work-Admission & Queueing | Welche Erkenntnisse aus Queueing-Theorie, Kanban und WIP-Limits sind für aufmerksamkeits­limitierte Single-User-Systeme relevant? |
| 11 | Learning in kleinen Systemen | Wann unterscheidet sich eine „Standards-Promotion-Pipeline" von einer einfachen Notiz, und was ist der minimale sinnvolle Promotion-Mechanismus? |

### Tier C — Implementierungs-Constraints

| # | Thema | Forschungsfrage |
|---|-------|-----------------|
| 12 | Persistenz & Event-Transport | Welche Persistenz- und Event-Transport-Kombinationen sind für ein Single-User-System aktuell sinnvoll (SQLite, Postgres, LiteFS, NATS-lite, file-based)? |
| 13 | Kosten- & Budget-Muster | Welche Muster zur Kosten-Kontrolle agentischer Arbeit (Token-Caps, Rate-Limiting, Circuit-Breaker, Budget-Tracking) sind 2025–2026 Stand der Technik? |

### Tier D — Design-Entscheidungen (informiert, nicht determiniert)

| # | Thema | Forschungsfrage |
|---|-------|-----------------|
| 14 | Kontext-Anzahl & -Grenzen | Welche Anzahl und Zuschnitt fachlicher Kontexte ist für ein persönliches agentisches Steuerungssystem angemessen — basierend auf den Befunden aus Briefs 01–13? |
| 15 | MVP-Staging & Erfolgsmetriken | Welche MVP-Stufung und welche Erfolgsmetriken sind für ein persönliches Multi-Projekt-System sinnvoll? |

## Synthese

`99-synthesis.md` führt die 15 Briefs zu einer schlanken V1-Spezifikation zusammen.
Struktur (vorläufig):

1. Zielbild (verkürzt)
2. Kontext-Schnitt (aus Brief 14)
3. Kernobjekte (verkürzt aus `09` + Briefs 06, 08)
4. Lifecycle-Skelett (verkürzt aus `05` + Brief 11)
5. Execution- und Trust-Modell (aus Briefs 01, 02, 07)
6. Orchestrierung und Persistenz (aus Briefs 03, 12)
7. Kosten- und Eskalationsdisziplin (aus Briefs 09, 13)
8. MVP-Staging und Erfolgsmetriken (aus Brief 15)
9. Offene Entscheidungen

## Reihenfolge der Bearbeitung

1. Tier A (5 Briefs) — zuerst, parallelisierbar wo sinnvoll.
2. Tier B (6 Briefs) — konzeptionell, sequenziell wegen Querverweisen.
3. Tier C (2 Briefs) — nach Tier A, weil sie auf Tier-A-Befunden aufbauen.
4. Tier D (2 Briefs) — zuletzt, weil Querverweise auf Tier A–C.
5. Synthese.
