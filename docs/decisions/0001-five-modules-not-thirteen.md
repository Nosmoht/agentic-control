# ADR-0001: Fünf Module, keine dreizehn Bounded Contexts

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §5`
* Supersedes: Legacy-Annahme von 13 Bounded Contexts in `archive/legacy-notes/04-bounded-contexts.md`

## Kontext und Problemstellung

Die ursprünglichen Notizen postulieren 13 Bounded Contexts mit eigenen
State-Ownern, Lifecycles und Schnittstellen für einen erklärten
Single-User-Einsatz. Das verursacht erheblichen konzeptionellen und
implementierungsseitigen Overhead ohne belegbare Motivation.

## Entscheidungstreiber

- Fowler-Linie: Bounded Contexts entstehen aus organisatorischer Kopplung,
  nicht aus fachlicher Komplexität allein. Monolith-Zone unter ~12–24 Personen.
- Team-Topologies-Heuristik: 1 Team ↔ max. 1 komplexe oder 3 einfache
  Subdomänen → bei n=1 empirisch 3–5 Kernmodule.
- PKM-Literatur: wichtigste Leseachse ist Aktionabilität (PARA: Project /
  Area / Resource / Archive), nicht Typ oder Thema.
- Control/Execution-Trennung ist 2025–2026 Mainstream für agentische Systeme.

## Erwogene Optionen

1. **13 Bounded Contexts beibehalten** (Legacy-Zustand).
2. **3 Module** (Work / Execution / Knowledge) — Interaction in Work fusioniert.
3. **5 Module** — Interaction, Work, Execution, Knowledge, Portfolio.
4. **6–7 Kontexte** mit separatem Policy-Modul.

## Entscheidung

Gewählt: **Option 3 — 5 Module**.

### Konsequenzen

**Positiv**
- Jedes Modul hat genau einen Zustands-Owner (AD-12 bleibt einhaltbar).
- Aktionabilitäts-Achse liegt sauber auf den 5: Work (active), Portfolio
  (Areas), Knowledge (Resources/Archive), Interaction (Inbox), Execution
  (ephemer).
- Drei der ursprünglich 13 Kontexte (Identity, Intent Resolution, Event
  Fabric) werden korrekt als Querschnitte statt Domänen modelliert.
- Policy/Governance ist Querschnitt, nicht Modul — bis Promotions-Stufen
  oder Bindung-Scopes separate Autorität erfordern.

**Negativ**
- Anpassungsaufwand der Legacy-Notizen.
- Wenn später Delegation hinzukommt, muss Approval als eigenes Objekt
  wiedereingeführt werden.
- Die Trennung Portfolio / Policy ist in V1 weich; kann bei wachsender
  Governance separat werden.

## Pro und Contra der Optionen

| Option | Pro | Contra |
|---|---|---|
| 13 Contexts | bekannt | empirisch unverteidigbar für n=1 |
| 3 Module | maximal schlank | verletzt Control/Execution-Trennung |
| 5 Module | Literatur-gestützt, aktionabilitäts-gerecht | Portfolio/Policy-Grenze ist weich |
| 6–7 Kontexte | gibt Governance ein eigenes Zuhause | Policy in V1 zu dünn für eigenen Kontext |

## Referenzen

- `docs/research/06-ddd-scale.md` — Fowler-Linie, Team-Topologies
- `docs/research/08-pkm.md` — Aktionabilitäts-Achse
- `docs/research/14-context-count.md` — Synthese-Brief
- `docs/research/05-agent-patterns.md` — Control/Execution-Mainstream
- `archive/REVIEW.md` — ursprüngliche Kritik an 13 Contexts
