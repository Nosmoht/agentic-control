# ADR-0005: 4-Stufen-Standards-Lifecycle (statt 6)

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §6.1`

## Kontext und Problemstellung

Die Legacy-Notizen definieren einen 6-Stufen-Lifecycle für Standards
(`observed_candidate → review_candidate → accepted_standard → bound_standard
→ deprecated → retired`). Für einen Single-User ist jede zusätzliche Stufe
Overhead ohne organisatorischen Gewinn.

## Entscheidungstreiber

- Empirisch: keine RCT-Evidenz für Zettelkasten-Promotion oder
  vielstufige Standards-Pipelines am Einzelplatz.
- Argumentative Rechtfertigung nur dann, wenn eine Stufe
  **Agent-Auffindbarkeit, Autorität oder Cache-Strategie ändert**.
- LLM-Agent-Kontext-Reset erzwingt *materielle* Repräsentation — Skills,
  `CLAUDE.md`, Standards-Dateien — nicht bloße Klassifikation.

## Erwogene Optionen

1. **6 Stufen** (Legacy).
2. **4 Stufen:** `candidate → accepted → bound → retired`.
3. **3 Stufen:** `draft → active → retired`.
4. **2 Stufen:** `active → retired` (nur Bindung als Flag).

## Entscheidung

Gewählt: **Option 2 — 4 Stufen**.

### Konsequenzen

**Positiv**
- Jede Stufe ist agent-seitig unterscheidbar wahrnehmbar:
  - `candidate` — existiert, aber nicht auffindbar für Agenten.
  - `accepted` — in Knowledge-Modul, referenzierbar, aber nicht verbindlich.
  - `bound` — wird als Skill / `CLAUDE.md`-Eintrag materialisiert;
    Binding-Scope (Projekt-Typ/ID/Tag/Pfad) aktiv.
  - `retired` — existiert als Historie, hat aber keinen Bindungseffekt mehr.
- Vier Stufen bilden die minimale verteidigbare Progression ab.

**Negativ**
- Kein Zwischenstand für `deprecated` (aktiv, aber im Abbau).
- Keine dedizierte Review-Phase vor `accepted`.

**Neutral**
- Upgrade auf 5–6 Stufen möglich, sobald (a) Review-Rundgänge nötig werden
  oder (b) ein „deprecated"-Flag wirklich gebraucht wird.

## Pro und Contra der Optionen

| Stufenzahl | Differenzierbarkeit | Overhead | Agent-Auffindbarkeit |
|---|---|---|---|
| 6 | fein | hoch | identisch zu 4 |
| 4 | ausreichend | moderat | klar materialisiert |
| 3 | grob | niedrig | Bindung-Scope schwer ausdrückbar |
| 2 | unzureichend | minimal | verliert candidate-Zustand |

## Referenzen

- `docs/research/11-learning.md` — Learning in kleinen Systemen
- `docs/research/14-context-count.md` — Synthese
- MADR-Format: https://adr.github.io/madr/
