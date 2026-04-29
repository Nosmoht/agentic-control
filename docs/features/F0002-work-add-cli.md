---
id: F0002
title: work add and work next CLI
stage: v0
status: proposed
spec_refs: [§5.3, §6.1, §6.2]
adr_refs: [ADR-0001, ADR-0017, ADR-0019, ADR-0020]
---

# F0002 · `work add` und `work next` CLI

## Context

V0 ist „Handbetrieb mit Schema": der Nutzer braucht genau zwei
Einstiegspunkte, um das Vokabular zu testen. `work add` erzeugt neue
Work Items und Observations/Decisions, `work next` zeigt, was als
Nächstes ansteht. Agent-Runs bleiben in V0 manuell — das CLI registriert
sie, ruft sie nicht auf.

V0.3.5-draft schließt zwei R3-Lücken aus der Original-Fassung:

- **Multiline-Input für `--decision`**: Hybrid-Pattern wie `git commit`
  und `gh issue create` (Editor-Default + `--from-file` + stdin + drei
  Einzelflags), mit Draft-Recovery in `$XDG_STATE_HOME`.
- **Lifecycle-Transition-Matrix**: explizit aus Spec §6.1 abgeleitet,
  nicht implizit.

CLI-Framework: **Typer** (auf Click aufbauend, kompatibel mit
`click.edit()`).

## Scope

### Sub-Commands

- `agentctl work add --title "…" [--project <id>] [--priority {low,med,high}]`
  → legt Work Item mit `state=proposed` an. Default `--priority med`.
- `agentctl work add --observation "…" [--source-ref <id>] [--classification "…"]`
  → legt Observation an. `classification` ist Freitext (Spec §5.7,
  Enum entsteht in v1).
- `agentctl work add --decision --subject <work-item-id> [INPUT-MODUS]`
  → legt Decision an mit `state=proposed`. Input-Modi siehe unten.
- `agentctl work next [--project <id>]` → zeigt die nächsten ≤ 3 Work
  Items im Zustand `ready` oder `accepted`, sortiert nach `priority`
  (high > med > low) und `created_at` aufsteigend.
- `agentctl work show <id-or-prefix>` → zeigt Work Item mit verknüpften
  Observations/Decisions. ID-Auflösung per Präfix-Resolution
  (ADR-0019).
- `agentctl work transition <id-or-prefix> <new-state>` → erlaubt
  manuelle Lifecycle-Transition. Validiert gegen die Transition-Matrix
  unten.

### Input-Modi für `--decision`

Vier Modi, in dieser Präzedenz-Reihenfolge ausgewertet:

1. **`--from-file <path>`**: Liest komplette Markdown-Datei mit MADR-
   Sections (`## Context`, `## Decision`, `## Consequence`).
   `--from-file -` liest von stdin (für CI/Pipes).
2. **Drei Einzelflags `--context "…" --decision "…" --consequence "…"`**:
   Skript-Modus. Alle drei müssen gesetzt sein.
3. **`$EDITOR`-Launch (Default)**: Wenn weder `--from-file` noch die
   drei Flags gesetzt sind, öffnet `click.edit()` den `$EDITOR` mit
   Markdown-Template:

   ```markdown
   ## Context
   <warum jetzt, welcher Druck>

   ## Decision
   <was wir tun>

   ## Consequence
   <was sich ändert, was wir aufgeben>

   # Zeilen, die mit '#' beginnen, werden vor dem Speichern entfernt.
   # Leerer Buffer oder Abbruch ohne Save => kein Decision-Eintrag (Exit 0).
   ```

   Editor-Resolution: `$VISUAL` → `$EDITOR` → Plattform-Default
   (`vi`/Notepad). Datei-Extension `.md` für Syntax-Highlighting.
4. **stdin** (wenn TTY nicht verfügbar **und** keiner der obigen Modi):
   liest Markdown von stdin, erwartet dieselben Sektionen.

### Draft-Recovery

Bei Editor-Modus (Modus 3):

- Vor Editor-Launch wird Draft in
  `${XDG_STATE_HOME:-$HOME/.local/state}/agentic-control/decision-<work-item-id>.draft.md`
  geschrieben (Template oder bereits vorhandener Draft).
- Nach Save wird der Draft aktualisiert.
- Bei DB-Validation-Fehler bleibt der Draft stehen; bei nächstem Aufruf
  wird er als Seed verwendet (statt Template), und CLI weist darauf hin:
  „Continuing draft from <ISO-Timestamp>".
- Nach erfolgreichem Insert wird der Draft gelöscht.

### Exit-Codes

- `0` Erfolg (auch leerer Editor-Save = silent no-op).
- `2` Nutzerfehler (ungültige Args, Mehrdeutigkeit bei Präfix-
  Resolution, fehlende Editor-Auflösung).
- `3` Validation-Fehler (DB-Constraint, Pydantic-Validation, falsches
  UUIDv7-Format).
- `4` Lifecycle-Transition-Fehler (ungültige Transition gemäß Matrix).

### Lifecycle-Transition-Matrix (Work Item, abgeleitet aus Spec §6.1)

Erlaubte Transitionen (forward-only, Quelle → erlaubte Ziele):

| Quelle | Erlaubte Ziele |
|---|---|
| `proposed` | `accepted`, `abandoned` |
| `accepted` | `planned`, `abandoned` |
| `planned` | `ready`, `abandoned` |
| `ready` | `in_progress`, `abandoned` |
| `in_progress` | `waiting`, `blocked`, `completed`, `abandoned` |
| `waiting` | `in_progress`, `blocked`, `abandoned` |
| `blocked` | `in_progress`, `waiting`, `abandoned` |
| `completed` | (terminal) |
| `abandoned` | (terminal) |

`work transition` lehnt jede nicht in dieser Matrix gelistete Transition
mit Exit 4 ab. HITL-Sub-States von `waiting` (`waiting_for_approval`,
`stale_waiting`, `timed_out_rejected` aus ADR-0012) sind in v0 **nicht**
verfügbar — sie kommen mit der HITL-Inbox in v1.

### ID-Präfix-Resolution

Für `work show <id>` und `work transition <id> <state>`:

- Eingabe ist entweder vollständige UUIDv7 (36 Zeichen) oder Präfix
  (mindestens 4 Zeichen).
- Bei vollständiger UUIDv7: exakter Match.
- Bei Präfix: `WHERE id LIKE '<prefix>%'`. Genau ein Treffer →
  akzeptieren. Mehrere Treffer → Exit 2 mit Auflistung der ersten 5
  Kandidaten und der minimal eindeutigen Präfix-Länge. Kein Treffer →
  Exit 2 mit Hinweis.

### Listenausgabe

`work next` und Sub-Listen in `work show` zeigen die ersten 8 Zeichen
der UUIDv7 als Default-Anzeige. Volle UUID nur in `--output json`.

## Out of Scope

- Automatisches Dispatching an Agent — kommt in v1 (F0003).
- HITL-Inbox + HITL-Sub-States — kommt in v1.
- Budget-Gate — kommt in v1.
- Run-Lifecycle — kommt in v1 (wenn Runs existieren).
- Multi-Projekt-Dependency — kommt in v2.
- Decision-Lifecycle-Transitions (`accepted` / `superseded` /
  `rejected`) — Decisions werden in v0 nur als `proposed` erzeugt;
  Transitionen kommen mit dem ADR-Workflow in v1.
- TUI / Interactive-Picker — v0 ist plain CLI.

## Acceptance Criteria

1. **`work add --title "X"`** legt genau ein Work Item in der DB an;
   Rückgabe enthält die generierte UUIDv7 (verkürzt auf 8 Zeichen für
   Display, voll in `--output json`) und bestätigt Zustand `proposed`.
2. **`work add --observation "…"`** legt Observation an; `--source-ref`
   und `--classification` werden, falls gesetzt, persistiert.
3. **`work add --decision`** in allen vier Input-Modi:
   - `--from-file path.md` parst Markdown mit drei Sections korrekt.
   - `--from-file -` liest von stdin.
   - Drei Einzelflags `--context/--decision/--consequence` werden
     korrekt zusammengesetzt; Fehlen eines Flags = Exit 2.
   - `$EDITOR`-Launch öffnet Template; nach Save wird Markdown geparst,
     `#`-Kommentar-Zeilen gestrippt; leerer Buffer = silent no-op
     (Exit 0, kein Insert).
4. **Draft-Recovery**: Bei DB-Validation-Fehler im Editor-Modus bleibt
   Draft-Datei stehen. Folgender `work add --decision --subject <id>`
   nutzt diesen Draft als Seed und gibt „Continuing draft from
   <Timestamp>" aus.
5. **`work next`** zeigt maximal 3 Einträge; bei leerer DB kommt eine
   sprechende Meldung „Keine offenen Work Items".
6. **`work show <id-or-prefix>`** rendert Work Item + alle Decisions
   mit `subject_ref = <id>` und alle Observations mit `source_ref =
   <id>`. Präfix-Resolution funktioniert ab 4 Zeichen.
7. **`work transition <id> <state>`** akzeptiert nur Transitionen aus
   der Matrix. `proposed → completed` direkt = Exit 4 mit Hinweis auf
   erlaubte Ziele.
8. **Mehrdeutige Präfix-Resolution** liefert Exit 2 mit Kandidaten-
   Liste und minimaler eindeutiger Präfix-Länge.
9. **Exit-Codes** sind in jedem Fehlerfall der Definition entsprechend
   (0/2/3/4); Tests prüfen jeden Code mindestens einmal.
10. **`agentctl --help`** und **`agentctl work --help`** zeigen
    verwendbare Dokumentation aller Sub-Commands inklusive der vier
    Input-Modi für `--decision`.
11. **Headless-Tauglichkeit**: In CI ohne TTY funktionieren
    `--from-file` und stdin; Editor-Modus liefert sprechenden Fehler
    statt zu hängen (Exit 2, „No editor available, use --from-file or
    stdin").

## Test Plan

- **Unit**: Typer-CLI-Tests für jedes Sub-Command und jeden Input-Modus
  (CliRunner). Markdown-Parser mit Edge-Cases (fehlende Section,
  verschachtelte `#`-Kommentare, leerer Body).
- **Integration**: realer SQLite-DB-Roundtrip für jede Acceptance 1–9.
  Präfix-Resolution mit künstlich erzeugten kollidierenden UUIDs.
- **Editor-Modus**: Test mit Mock-Editor (Env-Var `EDITOR=/bin/true`
  für leerer Save; `EDITOR=cat` für Identity-Edit; eigenes Skript für
  Validation-Fehler-Pfad).
- **Headless**: Subprocess-Test ohne TTY (`stdin=PIPE`), prüft
  `--from-file -`-Modus und Editor-Modus-Fehlerpfad.
- **Manuell**: Nach Installation führt der Nutzer `work add`, `work
  next`, `work show`, `work transition` durch und berichtet, ob das
  Vokabular passt. Dokumentation im Plan (v0-Exit-Kriterium: 5+ Work
  Items manuell durchgezogen).

## Rollback

CLI ist eine lokale Binary / Python-Package. Rollback = Paket entfernen
(`uv pip uninstall agentic-control`); DB bleibt konsistent, weil jede
Transaction atomar war (SQLite WAL). Draft-Files in
`$XDG_STATE_HOME/agentic-control/` bleiben liegen; manuell entfernen
oder beim nächsten Install wiederverwenden.
