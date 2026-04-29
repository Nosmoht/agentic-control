---
id: F0001
title: SQLite Schema for Core Objects
stage: v0
status: proposed
spec_refs: [§5.7, §6.1]
adr_refs: [ADR-0001, ADR-0003, ADR-0017, ADR-0018, ADR-0019, ADR-0020]
---

# F0001 · SQLite Schema for Core Objects

## Context

Das System braucht ein persistentes Schema für die 4 v0-Kernobjekte
(`Project`, `Work Item`, `Observation`, `Decision`), bevor irgendein
CLI-Verhalten entsteht. V0 testet, ob das Vokabular gegen reale Arbeit
hält — das setzt voraus, dass die Objekte in SQLite geschrieben und
gelesen werden können. Tabellen für Runtime Records (ADR-0011) und das
v1-Domain-Schema (`Run`, `Artifact`, `Evidence` aus F0008) kommen in
eigenen v1a-Features.

V0.3.5-draft schließt drei R3-Lücken aus der Original-Fassung:

- **ID-Strategie**: UUIDv7 (RFC 9562) per ADR-0019.
- **Migrations-Tool**: Alembic per ADR-0020.
- **Decision-Lifecycle**: `proposed → accepted → superseded | rejected`
  per Spec §6.1.

## Scope

- **Package-Struktur**: Python-Package `agentic_control` unter
  `src/agentic_control/`. Pydantic-Contracts in
  `src/agentic_control/contracts/`. SQLAlchemy-Mapper (Connection-Layer
  only, kein ORM, ADR-0020) in `src/agentic_control/persistence/`.
- **DB-Datei**: SQLite unter `${AGENTIC_CONTROL_DB_URL}`, Default
  `sqlite:///$HOME/.agentic-control/state.db`.
- **Tabellen**: `project`, `work_item`, `observation`, `decision`.
- **Primary Keys**: UUIDv7 als `TEXT(36) NOT NULL PRIMARY KEY` mit
  `CHECK(LENGTH(id) = 36)`. Generator: `uuid_utils.uuid7()` bis
  Python-3.14-Upgrade, danach `uuid.uuid7()` (Import-Swap, kein
  Datenformat-Wechsel).
- **Foreign Keys**: aktiv per `PRAGMA foreign_keys = ON` bei jedem
  Connection-Open. `*_ref`-Spalten als `TEXT(36)` mit `FOREIGN KEY`-
  Constraint.
- **Timestamps**: ISO-8601 UTC als `TEXT NOT NULL`, Default
  `CURRENT_TIMESTAMP`.
- **Lifecycle-States**: `TEXT NOT NULL` mit `CHECK`-Constraint gegen den
  jeweiligen Enum aus Spec §6.1:
  - `project.state IN ('idea','candidate','active','dormant','archived')`
  - `work_item.state IN ('proposed','accepted','planned','ready',
    'in_progress','waiting','blocked','completed','abandoned')`
  - `decision.state IN ('proposed','accepted','superseded','rejected')`
  - `observation` hat **keinen** Lifecycle-State; nur
    `classification TEXT` (Freitext in v0).
- **Migrations**: Alembic in `migrations/versions/`, Naming
  `<NNNN>_<short_name>.py` (vier Stellen, fortlaufend). Initial-Migration
  `0001_initial_core_objects.py` legt alle 4 Tabellen an.
- **Migrations-Skripte sind manuell** (kein `alembic --autogenerate`,
  ADR-0020).
- **DB-Verzeichnis** (`$HOME/.agentic-control/`) wird beim ersten
  Migrations-Lauf automatisch erstellt.

## Out of Scope

- Tabellen für `Run`, `Dependency`, `Standard`, `Artifact`, `Evidence` —
  kommen in v1-Feature-Files (F0008 für v1-Domain-Schema).
- Tabellen für Runtime Records (ADR-0011) — kommen in v1 (F0006).
- Backup/Restore (Litestream-Konfiguration) — separates v1-Feature.
- Postgres-Migration (ADR-0013 v2+) — Migrations-Skripte sind dafür
  vorbereitet, aber kein v0-Test-Run gegen Postgres.
- ORM-Layer (`sqlalchemy.orm`) — ADR-0020 verbietet ORM-Imports
  außerhalb des Connection-Layer-Moduls.
- CLI-Verhalten (`work add`, `work show` …) — F0002.

## Acceptance Criteria

1. **Migration auf leerer DB**: `alembic upgrade head` läuft auf einer
   frisch angelegten DB ohne Fehler. Das DB-Verzeichnis wird angelegt,
   falls es nicht existiert.
2. **Schema-Vollständigkeit**: Nach Migration existieren alle 4 Tabellen
   mit den Pflichtfeldern aus Spec §5.7 (inkl. `created_at`-Spalten und
   den UUIDv7-PK-/-FK-Constraints).
3. **Foreign-Key-Enforcement**: Insert eines `work_item` mit nicht-
   existentem `project_ref` schlägt mit `IntegrityError` fehl.
4. **State-CHECK-Enforcement**: Insert eines `work_item.state = "bogus"`
   schlägt mit `CHECK constraint failed` fehl. Analog für
   `project.state`, `decision.state`.
5. **UUIDv7-CHECK-Enforcement**: Insert eines `id`-Werts mit
   abweichender Länge (z. B. UUIDv4 ohne Hyphens, ULID-26-Zeichen)
   schlägt am `LENGTH(id) = 36` CHECK fehl.
6. **Pydantic-Validation**: Application-Layer-Insert eines UUIDv4
   (richtige Länge, falsches Versions-Bit) wird vom Pydantic-`UUID7`-
   Typ vor SQL-Send abgelehnt.
7. **Idempotente Migration**: Eine zweite Ausführung von `alembic
   upgrade head` auf der bereits migrierten DB ist no-op (keine Fehler,
   keine Schema-Änderung).
8. **Schema-Dump-Stabilität**: `sqlite3 state.db .schema` liefert
   reproduzierbar denselben Schema-Output (verglichen mit Expected-
   Fixture in `tests/fixtures/schema-0001.sql`).
9. **Pydantic ↔ Schema-Konsistenz** (CI-Check): Ein Test vergleicht den
   Schema-Dump nach `alembic upgrade head` mit dem aus den Pydantic-
   Contracts abgeleiteten Erwartungs-Schema und schlägt bei Drift fehl.
10. **Connection-Layer-Disziplin** (CI-Check): Linter (z. B. `ruff`
    custom rule oder `import-linter`) lehnt `sqlalchemy.orm`-Imports
    außerhalb von `src/agentic_control/persistence/` ab.

## Test Plan

- **Unit**: Migration auf leerer DB; Schema-Dump vergleicht mit
  Expected-Fixture; Pydantic-Model-Roundtrip (instanziieren, in DB
  schreiben, lesen, vergleichen).
- **Integration**: Insert sample Project + Work Item + Observation +
  Decision; Roundtrip `SELECT` liefert identische Werte; FK-Violation;
  CHECK-Violation; UUIDv7-Format-Violation.
- **Migration-Re-Run**: `alembic upgrade head` zweimal hintereinander,
  beide Läufe Exit 0.
- **CI**: Schema-Drift-Check (AC 9) und Connection-Layer-Linter (AC 10)
  als Pflicht-Stages in der CI-Pipeline.
- **Manuell**: Nach `uv sync` und `alembic upgrade head` führt der
  Nutzer einen rohen `sqlite3 state.db .tables` aus und sieht alle 4
  Tabellen.

## Rollback

SQLite-DB ist eine einzelne Datei. Rollback = Datei löschen oder in
vorheriger Commit-SHA wiederherstellen. Kein Schema-Downgrade-Skript
nötig in V0 (Forward-Only-Migration; bei Bedarf in v1 via Alembic-
`downgrade`-Funktionen nachrüstbar).
