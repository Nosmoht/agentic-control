---
topic: mvp-metrics
tier: D
date: 2026-04-23
status: draft
---

# Brief 15: MVP-Staging und Erfolgsmetriken

## Forschungsfrage

In welchen Stufen wird das System gebaut, und woran erkennen wir, ob V1 für
einen einzelnen Nutzer funktioniert?

## Methodik

Synthese der Briefs 01–14. Keine neue externe Recherche.

## Leitprinzipien für das Staging

- **Bootstrap-Wert vor Vollständigkeit** — jede Stufe muss für sich allein
  nutzbar sein, sonst wird sie nie fertig.[^B11-LLM]
- **Self-hosting zuerst** — das erste Projekt des Systems ist das System
  selbst. Alles andere hat zu wenig Feedback.
- **Minimalen Datenbesitz früh** — Stufen ohne eigene Persistenz sind
  Sackgassen, weil später ein Datenimport an zu vielen Stellen nötig wäre.[^B12]
- **Keine vorgezogene Governance** — Policy/Standards kommen zuletzt, weil sie
  erst Material zum Binden brauchen.[^B11]

## Staging

### v0 — „Handbetrieb mit Schema" (2–4 Wochen)

**Zweck:** Das Vokabular gegen echte Arbeit testen.

**Umfang:**
- SQLite-Schema für `Project`, `Work Item`, `Observation`, `Decision`.
- Zwei CLI-Befehle: `work add`, `work next`.
- Claude Code / Codex CLI laufen **manuell** in Worktrees; das System
  registriert die Run-Resultate manuell als Artefakt.
- Keine Durable-Execution-Engine, keine HITL-Inbox, keine Automation.
- Persistenz: SQLite-Datei im Git-Repo des Systems selbst.

**Abbruch­kriterien:**
- Nach 2 Wochen passt das Vokabular (Project / Work Item / Observation /
  Decision) nicht zur tatsächlichen Arbeit → Schema refaktorieren, bevor v1
  startet.
- Nach 4 Wochen ist das System seltener als 1× pro Woche benutzt → falsches
  Zielbild, neu bewerten.

**Bewusst weggelassen:**
- Workflow-State (Runs werden als Observation geloggt, nicht als eigenes Objekt).
- Knowledge-Promotion (nur flache Notes in `Decision`).
- Portfolio-Koordination.

### v1 — „Durable Single-Loop" (8–12 Wochen)

**Zweck:** Work-Lifecycle automatisieren, ohne die Kontroll-Disziplin zu
verlieren.

**Umfang:**
- DBOS als In-Process-Layer, Postgres (prod) oder SQLite (dev).[^B03][^B12]
- `Run` als eigenes Objekt mit Lifecycle (Brief 14).
- **Sandbox-MVS**: Worktree + bubblewrap/seatbelt, non-root, read-only
  root-FS + tmpfs, Egress-Proxy mit Allowlist, Config-Write-Schutz,
  cgroup-Limits.[^B07]
- **Budget-Gate als Middleware** vor jedem LLM-Call: Request-Cap $0,50,
  Task-Cap $2 / 25 Turns / 15 min, Global-Hard-Cap $25/Tag.[^B13]
- **HITL-Inbox** mit Cards; Push erst nach 4 h, E-Mail nach 24 h. Kein
  synchroner Push-Prompt als Default.[^B09]
- Headless-Claude-Code-Aufruf: `claude -p --output-format json --bare
  --allowedTools=<explizit>`; Headless-Codex-Aufruf: `codex exec --json
  --output-schema <file> --ephemeral`.[^B01][^B02]
- Pydantic AI als dünner LLM-Call-Wrapper für alles, was nicht direkt an
  einen Agent geht (z. B. Intake-Klassifikation).[^B04]
- Persistenz: SQLite WAL + Litestream → Object Storage. Knowledge als
  Markdown im Git-Repo mit SQLite-FTS5-Index.[^B12]

**Erfolgsbedingung:**
- Ein Work Item kann von `proposed` bis `completed` ohne manuellen Eingriff
  außer HITL-Gates durchlaufen.
- Kosten pro Work Item sind messbar und bleiben unter Cap.
- Keine Runaway-Loops in 4 Wochen.

**Bewusst weggelassen:**
- Dependency zwischen Projekten.
- Standards-Promotion.
- Mehrere gleichzeitige Projekte (WIP 1).

### v2 — „Portfolio-Koordination" (8–10 Wochen)

**Zweck:** Mehrere Projekte sauber parallel steuern.

**Umfang:**
- `Project` mit Lifecycle und `Dependency` als First-Class.
- WIP-Limits: 2 aktive Work Items, 3–5 aktive Projekte, 2–3 Agent-Runs
  pro Work Item.[^B10]
- `Work Intake & Triage` wird zu einem echten Prozess­schritt: 4-Klassen-
  Admission (`reject` / `defer` / `delegate-to-agent` / `accept`), explizite
  Kosten-/Scope-Schätzung vor Annahme.[^B10]
- Knowledge-Capture: `Observation` als Standard-Inbox, `Decision` im
  ADR-Minimalformat, `Artifact` mit Provenance.[^B08][^B11]
- Periodischer Review-Hook alle 2–4 Wochen.[^B11]

**Erfolgsbedingung:**
- Drei parallele Projekte sauber gesteuert, ohne dass WIP eskaliert.
- Dependencies werden vor Run-Start geprüft; kein Blockage-Lag > 1 Tag.
- Attention-Residue-Indikator (halboffene Work Items > 2 Wochen) bleibt
  niedrig.

### v3 — „Governance & Lernen" (8–10 Wochen)

**Zweck:** Stille Standard-Erosion verhindern.

**Umfang:**
- 4-stufige Promotion `candidate → accepted → bound → retired`.[^B11]
- Binding-Scope pro Standard (projekt-typ, projekt-id, tag, pfad).
- Policy als Querschnitt, *nicht* eigenes Modul.
- Standards werden als Claude-Skills / `CLAUDE.md`-Einträge materialisiert —
  Promotion ändert also tatsächlich Agent-Auffindbarkeit.[^B11-LLM]
- Optional: Observability-/Audit-Trennung einführen, wenn Compliance-Audits
  relevant werden.

**Erfolgsbedingung:**
- Mindestens 3 Standards im Zustand `bound` mit echtem Scope.
- Bindings werden bei Agent-Runs nachweislich angewandt (Promotion wirkt).
- Keine unstatierte „Schatten-Policy" in Knowledge (AD-07/`07`).

## Erfolgsmetriken

### Primärmetriken (Führungsgrößen)

| Metrik | Zielrichtung | Basis |
|---|---|---|
| Aktive Work Items | ≤ 2 gleichzeitig | Swellers Arbeitsgedächtnis, Brief 10 |
| Aktive Projekte | 3–5 | Personal Kanban, Brief 10 |
| Attention-Residue-Count | niedrig, trendet ↓ | Leroy 2009, Brief 10 |
| Kosten pro Tag | < $25 hard | Brief 13 |
| Kosten pro Work Item (Median) | stabil nach Kalibrierung | Brief 13 |
| Eskalations­rate (HITL / Work Item) | 10–25 % | Brief 09 (nicht < 5 %, nicht > 40 %) |
| Zeit Idee → aktives Work Item (Median) | < 3 Tage | eigener Anker |
| Runaway-Vorfälle (Hard-Cap erreicht) | 0 pro Woche | Brief 13 |

### Sekundärmetriken (Verhaltensindikatoren)

- Prompt-Cache-Hit-Rate Claude Code: ≥ 60 % (Anthropic-Anker 90 % gilt nur
  für homogene Workloads).[^B13]
- Verhältnis Haiku : Sonnet : Opus-Calls — wenn Opus > 30 %, prüfen.[^B13]
- `Standard`-Bindings angewandt pro Woche: > 0 (wenn 0: Pipeline unbewohnt).
- Worktree-Sandbox-Verletzungen (Denied-Egress, Config-Write-Versuche):
  dokumentieren, nie zulassen.[^B07]

### Anti-Metriken (nicht optimieren)

- **Erledigte Work Items / Tag** — Goodhart's Law, fördert Zerhacken.
- **Anzahl aufgenommener Ideen / Tag** — fördert Inbox-Bloat.
- **„Velocity"** — bei n=1 methodisch ohne Inhalt.
- **Anzahl `bound` Standards** — Promotion-Quoten fördern willkürliches Binden.

### Messbarkeit

Alle Primärmetriken sind aus SQLite + Audit-Log ableitbar, ohne separate
Telemetrie. Periodischer Review-Hook (v2) gibt die Zahlen aus. Ein OTEL-Stack
ist für V1 nicht nötig und würde gegen die Proportionalitäts­heuristik aus
Brief 12 verstoßen.

## Was am Ende von v3 *nicht* da sein muss

- Cloud-Variante für Claude Code / Codex Cloud (optional, nicht Pflicht).[^B01][^B02]
- Multi-Device-Sync / CRDT-Knowledge.[^B12]
- Approval als eigenständiges Objekt (nur bei Delegation).[^REVIEW]
- Separate Identity-/Trust-/Access-Domäne.
- Event Fabric als eigener Kontext.
- Observability als eigenes Modul (außer bei Audit-Compliance-Bedarf).

## Offene Entscheidungen vor v1-Start

- Lokaler Laptop-only oder Laptop + VPS? Brief 12 zeigt beide als tragfähig.
- Nur Claude Code, nur Codex CLI, oder beides? Beide haben distinkte
  Trust-Profile (lokal vs. Cloud) — evtl. gleichzeitiger Support als
  zusätzliche v1-Komplexität.[^B01][^B02]
- Control Surface: CLI, Telegram, Matrix, Mail? Nicht in den Briefs
  beantwortet — offene Produktfrage aus `12-open-questions.md`.

## Quellenverweise

[^B01]: `01-claude-code.md`.
[^B02]: `02-codex-cli.md`.
[^B03]: `03-durable-execution.md`.
[^B04]: `04-agent-orchestration-libs.md`.
[^B07]: `07-trust-sandboxing.md`.
[^B08]: `08-pkm.md`.
[^B09]: `09-hitl.md`.
[^B10]: `10-work-admission.md`.
[^B11]: `11-learning.md`.
[^B11-LLM]: `11-learning.md` §LLM-Agent-Spezifika — Stufen nur, wenn
  Agent-Auffindbarkeit/Autorität/Cache-Strategie verändert.
[^B12]: `12-persistence.md`.
[^B13]: `13-cost.md`.
[^REVIEW]: `REVIEW.md` — Approval-Objekt nur bei Delegation.
