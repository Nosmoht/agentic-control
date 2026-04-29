# ADR-0020: Migrations-Tool für SQLite-Schema

* Status: accepted
* Date: 2026-04-29
* Context: `docs/spec/SPECIFICATION.md §5.7`, ADR-0003, ADR-0013,
  ADR-0017, ADR-0018, F0001

## Kontext und Problemstellung

F0001 fordert ein Migrations-Tool, das forward-only Schema-Änderungen
nachvollziehbar macht. Der ursprüngliche Feature-Text nennt es nur
beispielhaft („z. B. simple Forward-Only-Migration-Datei-Folge"), was
R3 verletzt: zwei Implementierer würden plausibel verschiedene Tools
wählen (Alembic vs. yoyo-migrations vs. plain SQL + eigener Runner).

Vor v0-Implementierungsstart muss das Tool festgelegt sein, weil:

- Die Wahl prägt das Verhältnis Pydantic-Models ↔ DB-Schema
  (ADR-0018).
- Die Wahl beeinflusst den Postgres-Migrations-Pfad (ADR-0013), weil
  dieselbe Migrations-Historie unter beiden Backends laufen können
  muss.
- Der Restore-Drill (§10.4) muss die Migrations-Historie deterministisch
  wiederherstellen.

## Entscheidungstreiber

1. **ADR-0013 Postgres-Pfad** — Migrationen müssen ohne Re-Authoring
   auf Postgres laufen, sobald v2+ den Backend-Wechsel macht.
2. **ADR-0018 Pydantic-First** — Wir definieren Schemas in Pydantic-
   Models, **nicht** in SQLAlchemy ORM-Models. Das Migrations-Tool
   sollte ohne ORM-Zwang funktionieren oder den ORM-Mode optional
   lassen.
3. **Operations-Minimum (ADR-0013)** — Das Tool muss in `uv sync`
   einlaufen und nach Restore-Drill ohne Zusatz-Setup funktionieren.
4. **Iterativität** — In v0/v1a entstehen erfahrungsgemäß viele
   Schema-Korrekturen. Das Tool muss niedrige Friction für „neue
   Migration anlegen" bieten.
5. **Rollback ist nicht Treiber.** F0001 spezifiziert Forward-Only;
   Rollback erfolgt per Datei-Restore aus Litestream.

## Erwogene Optionen

### Option 1 — Alembic

**Pro**
- De-facto Standard im Python-DB-Ökosystem.
- Funktioniert nativ auf SQLite **und** Postgres mit identischer
  Migrations-Skript-Syntax (Dialekt-Unterschiede via SQLAlchemy
  abstrahiert).
- Auto-Generate aus SQLAlchemy-Models (optional; wir nutzen es
  **nicht**, weil ADR-0018 Pydantic-First setzt).
- `alembic upgrade head` ist deterministisch und idempotent.
- Reife Community, breite Doku, viele Production-Beispiele.
- Branching/Merging von Migrations-Histories unterstützt (relevant
  für spätere Multi-Feature-Branches).

**Contra**
- Bringt SQLAlchemy als transitive Dependency mit. Wir verwenden
  SQLAlchemy als **Connection-/Type-Layer**, nicht als ORM (siehe
  Konsequenzen). Diese Aufteilung muss diszipliniert eingehalten
  werden.
- Konfigurations-Boilerplate (`alembic.ini`, `env.py`, `versions/`-
  Verzeichnis) ist nicht trivial.
- Migrations-Skripte sind Python-Code, nicht plain SQL — leichter
  zu schreiben, schwerer per Hand zu auditieren.

### Option 2 — yoyo-migrations

**Pro**
- Plain-SQL-Files (mit optionalen Python-Steps).
- Kein ORM-Zwang; passt zu Pydantic-First ohne SQLAlchemy.
- Sehr kleine Dependency-Surface.
- Migrations sind menschenlesbar als SQL.

**Contra**
- Dialekt-Unterschiede SQLite ↔ Postgres müssen im Migrations-File
  manuell unterschieden werden (separate `*.sql` pro Backend oder
  bedingte Logik). Bei v2+ Postgres-Wechsel: jede Migration muss
  potenziell rewritten werden.
- Kleinere Community, weniger Production-Beispiele.
- Branching/Merging weniger ausgereift.

### Option 3 — Plain SQL Files + eigener 30-Zeilen-Runner

**Pro**
- Null externe Abhängigkeit.
- Maximale Transparenz.

**Contra**
- Selbstgebauter Code für ein gelöstes Problem (verletzt
  `deterministic-hierarchy.md` Stufe 2 → 4: ein existierendes CLI
  würde den selbst-gebauten Runner ersetzen).
- Idempotenz, Concurrency-Locks, Migration-Tabelle, Dialekt-
  Abstraktion: alles selbst zu lösen.
- Bei Postgres-Wechsel komplette Re-Implementation des Runners
  oder Wechsel zu Standard-Tool unter Zwang.

## Entscheidung

Gewählt: **Option 1 — Alembic**.

### Begründung

1. **ADR-0013-Postgres-Pfad ist der Schwerpunkt.** Alembic ist das
   einzige der drei Tools, das identische Migrations-Skripte unter
   SQLite und Postgres ausführt — ohne dass jede Migration für
   beide Backends zweimal geschrieben werden muss. Das spart in v2+
   eine teure Reauthoring-Runde.
2. **SQLAlchemy als Type-Layer, nicht ORM.** Wir nutzen SQLAlchemy
   ausschließlich für (a) Connection-Pool, (b) Dialekt-Abstraktion,
   (c) `Uuid(as_uuid=True)`-Typ aus ADR-0019. Domain-Logik bleibt in
   Pydantic-Models und Repository-Funktionen, die SQL via
   SQLAlchemy-Core (nicht ORM-Session) ausführen. Diese Trennung
   ist dokumentiert und in CI prüfbar (Linter-Regel: kein Import
   von `sqlalchemy.orm.declarative_base` in Anwendungs-Code).
3. **Pydantic-First bleibt erhalten.** Migrations-Skripte werden
   **nicht** per Auto-Generate aus SQLAlchemy-Models erzeugt
   (`alembic revision --autogenerate` wird **nicht** verwendet). Sie
   werden manuell geschrieben und referenzieren die Pydantic-Schema-
   Versionen aus `src/agentic_control/contracts/`.
4. **Reife schlägt Minimalismus.** Das Volumen an Production-
   Patterns (Online-DDL, Branching, Squash) ist bei Alembic so groß,
   dass spätere Probleme bekannte Lösungen haben. yoyo und
   eigene-Runner kosten diesen Vorteil.

### Ausschluss von `--autogenerate`

ADR-0018 macht Pydantic die Single-Source. SQLAlchemy-Models existieren
nur als dünner Mapper für die Connection-Layer-Aufgaben oben. Würde
Alembic per `--autogenerate` aus SQLAlchemy-Models Migrationen
generieren, entstünde eine dritte Schema-Quelle (Pydantic + SQLAlchemy
+ Migration-File) mit Drift-Risiko. Daher:

- Alle Migrations-Skripte werden **manuell** geschrieben.
- Sie verweisen im Docstring auf den Pydantic-Model-Commit-SHA, gegen
  den sie das Schema ausrichten.
- Ein CI-Check vergleicht den Schema-Dump nach `alembic upgrade head`
  mit dem aus den Pydantic-Models abgeleiteten Erwartungs-Schema
  (Acceptance Criterion in F0001).

## Konsequenzen

**Positiv**
- v2+ Postgres-Migration läuft ohne Re-Authoring der bestehenden
  Migrations-Skripte.
- Standard-Tooling, breite Doku, geringes Wartungs-Risiko.
- `alembic upgrade head` ist idempotent (erfüllt F0001 Acceptance 6).

**Negativ**
- SQLAlchemy als zusätzliche Top-Level-Dependency. Mitigation:
  Verwendung auf Core/Connection-Layer beschränkt; ORM-Imports per
  Linter-Regel verboten.
- `alembic.ini` + `migrations/env.py` + `migrations/versions/`-
  Struktur ist Boilerplate.
- Migrations-Skripte sind Python, nicht SQL — Audit-Komfort etwas
  geringer als bei plain SQL.

**Neutral**
- Migrations-Verzeichnis: `migrations/versions/` im Repo-Root.
- Naming-Konvention für Migration-Files: `<NNNN>_<short_name>.py`
  (vier Stellen, fortlaufend).
- DB-Pfad konfigurierbar via `AGENTIC_CONTROL_DB_URL`-Env-Var; Default
  `sqlite:///$HOME/.agentic-control/state.db`.

## Follow-ups

- F0001 Acceptance Criteria erweitern um:
  - „`alembic upgrade head` läuft auf leerer DB ohne Fehler."
  - „`alembic upgrade head` ist idempotent (zweite Ausführung
    no-op)."
  - „CI-Check vergleicht Schema-Dump nach Migration mit dem aus
    Pydantic-Contracts abgeleiteten Erwartungs-Schema."
- Linter-Regel (z. B. `ruff` custom rule oder `import-linter`): kein
  Import von `sqlalchemy.orm` außerhalb des Connection-Layer-Moduls.
- Initial-Migration (0001) erstellt die 4 Tabellen aus F0001-Scope.

## Referenzen

- ADR-0003 — SQLite + Litestream-Persistenz
- ADR-0013 — V1 Deployment Mode (Postgres v2+)
- ADR-0017 — Implementierungssprache (Python ≥ 3.13)
- ADR-0018 — Schema-First mit Pydantic als Single-Source
- ADR-0019 — Primary-Key-Strategie (UUIDv7)
- F0001 — SQLite Schema for Core Objects
- Alembic Documentation: <https://alembic.sqlalchemy.org/>
- yoyo-migrations: <https://ollycope.com/software/yoyo/latest/>
- `~/.claude/CLAUDE.md` `deterministic-hierarchy.md` Stufe 2 (CLI vor
  Eigenbau)
