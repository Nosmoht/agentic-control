---
id: F0001
title: SQLite Schema for Core Objects
stage: v0
status: proposed
spec_refs: [§5.7]
adr_refs: [ADR-0001, ADR-0003]
---

# F0001 · SQLite Schema for Core Objects

## Context

Das System braucht ein persistentes Schema für die 9 Kernobjekte, bevor
irgendein CLI-Verhalten entsteht. V0 testet, ob das Vokabular gegen reale
Arbeit hält — das setzt voraus, dass die Objekte in SQLite geschrieben und
gelesen werden können. Tabellen für Runtime Records (ADR-0011) kommen in
eigenen v1a-Features, sobald die Implementierung beginnt.

## Scope

- SQLite-DB-Datei unter `~/.agentic-control/state.db`.
- Tabellen für die v0-relevanten Kernobjekte: `project`, `work_item`,
  `observation`, `decision`.
- Foreign-Key-Constraints aktiv (`PRAGMA foreign_keys = ON`).
- Timestamps in UTC, ISO-8601 als TEXT.
- Lifecycle-States als TEXT-Enum per CHECK-Constraint.
- Migrations-Tool (z. B. simple Forward-Only-Migration-Datei-Folge) so
  konfiguriert, dass spätere Schema-Änderungen nachvollziehbar sind.

## Out of Scope

- Tabellen für `Run`, `Dependency`, `Standard`, `Artifact`, `Evidence` —
  kommen in v1-Feature-Files.
- Tabellen für Runtime Records (ADR-0011) — kommen in v1 (separates
  Feature).
- Backup/Restore (Litestream-Konfiguration) — separates v1-Feature.
- Postgres-Migration (ADR-0013 v2+) — nicht V0.

## Acceptance Criteria

1. Frische Installation kann die Migration ausführen und die DB anlegen,
   ohne Fehler.
2. Alle 4 Tabellen existieren nach Migration mit den Pflichtfeldern aus
   Spec §5.7.
3. Foreign-Key-Constraints sind aktiv: Insert eines `work_item` mit
   nicht-existentem `project_ref` schlägt fehl.
4. Lifecycle-State-CHECK-Constraints sind aktiv: Insert eines
   `work_item.state = "bogus"` schlägt fehl.
5. Ein Export via `sqlite3 state.db .dump` liefert reproduzierbar denselben
   Schema-Header wie das Migrations-Skript beschreibt.
6. Eine zweite Ausführung der Migration auf der bereits migrierten DB ist
   idempotent (keine Fehler, keine Duplikate).

## Test Plan

- Unit: Migration auf leerer DB; Schema-Dump vergleicht mit Expected-Fixture.
- Integration: Insert sample Project + Work Item + Observation + Decision;
  Roundtrip `SELECT` liefert identische Werte.
- Negative: Fremdschlüssel-Violation, CHECK-Violation, Migrations-Re-Run.
- Manuell: `work add --title "test"` (sobald F0002 vorhanden) schreibt
  tatsächlich in die DB.

## Rollback

SQLite-DB ist eine einzelne Datei. Rollback = Datei löschen oder in
vorheriger Commit-SHA wiederherstellen. Kein Schema-Downgrade-Skript nötig
in V0 (Forward-Only-Migration; bei Bedarf in v1 nachrüstbar).
