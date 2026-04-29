# ADR-0019: Primary-Key-Strategie für Domain-Tabellen

* Status: accepted
* Date: 2026-04-29
* Context: `docs/spec/SPECIFICATION.md §5.7`, ADR-0003, ADR-0013, ADR-0017,
  ADR-0018, F0001

## Kontext und Problemstellung

F0001 (SQLite-Schema für die v0-Kernobjekte) braucht eine festgelegte
Primary-Key-Strategie für `project`, `work_item`, `observation` und
`decision`. Die Spec §5.7 nennt nur „id" als Pflichtfeld, ohne den Typ
zu fixieren. Vor Implementierungsstart muss klar sein:

- Welcher ID-Generator,
- welcher Spaltentyp in SQLite **und** Postgres (ADR-0013 v2+ Pfad),
- welche Pydantic-Repräsentation (ADR-0018 Pydantic-First),
- welches CLI-UX-Verhalten bei Anzeige und Eingabe.

Die Wahl ist nach ~1 KLOC Code praktisch irreversibel — ein späterer
Wechsel zwingt zu Datenmigration aller Foreign Keys und Re-Key der
Audit-Trails.

## Entscheidungstreiber

1. **ADR-0018-Konformität** — Pydantic-Models als Single-Source. Native
   Typ-Unterstützung in Pydantic v2 reduziert Custom-Validatoren und
   hält den JSON-Schema-Export sauber.
2. **ADR-0003/0013-Postgres-Pfad** — IDs müssen verlustfrei in eine
   Postgres-Spalte übertragbar sein. Native Typ-Unterstützung in
   Postgres vermeidet Konvertierungs-Layer.
3. **CLI-Tippbarkeit** — `agentctl work show <id>` und Listenansichten
   sind die primären Nutzer-Interaktionen. Ein 36-Zeichen-Hex-String
   ist nicht praktikabel ohne Hilfsmittel.
4. **Stabilität über Restore** — IDs müssen über Litestream-Restore und
   `VACUUM`-Operationen stabil bleiben. SQLite-ROWIDs sind das **nicht**
   garantiert ohne `INTEGER PRIMARY KEY`-Deklaration und auch dann
   anfällig bei Multi-Source-Sync.
5. **Single-Node-Generierung** — Solo-Nutzer, keine verteilte Erzeugung
   notwendig (entlastet von Distributed-ID-Anforderungen).
6. **Insert-Volumen niedrig** — < 100 Inserts/Tag erwartet.
   Index-Performance-Argumente zwischen sequenziellen vs. zufälligen IDs
   greifen erst ab ~10⁶ Rows und sind hier nicht entscheidungsrelevant.

## Erwogene Optionen

### Option 1 — INTEGER (SQLite ROWID / Postgres BIGSERIAL)

**Pro**
- Maximaler CLI-Komfort (`work show 42`).
- Kompakteste Spalten, schnellste B-Tree-Inserts.
- Trivial in Pydantic (`int`) und SQLAlchemy (`Integer`).

**Contra**
- SQLite-ROWIDs sind nur stabil bei expliziter `INTEGER PRIMARY KEY`-
  Deklaration; selbst dann nicht garantiert über `VACUUM INTO` mit
  Re-Insert. Nach Litestream-Restore (ADR-0003 §10.4) kann sich
  Re-Numbering ergeben, wenn Migration neu läuft.
- Bei späterem Multi-Device- oder Sync-Szenario (potenziell v2+
  Knowledge-Capture) kollisionsanfällig — Re-Key wäre teuer.
- Keine Zeitstempel-Information im Wert; Audit-Trails brauchen
  separates `created_at`-Sortierkriterium.

### Option 2 — ULID (python-ulid)

**Pro**
- 26 Zeichen Crockford Base32 (kein I/L/O/U) — gut tippbar, lexiko-
  graphisch sortierbar mit Zeitstempel-Präfix.
- Etablierter Standard, breite Library-Unterstützung.

**Contra**
- Pydantic v2 hat **keinen** nativen `ULID`-Typ — Custom-Validator
  notwendig (`Annotated[str, AfterValidator(...)]` oder Adapter).
  JSON-Schema-Export landet als generischer String mit Custom-Format.
- Postgres hat keinen nativen `ULID`-Typ — Spalte als `TEXT(26)` oder
  `BYTEA(16)`. Verlustfrei, aber kein nativer Index-Support, keine
  Built-in-Generierung.
- SQLAlchemy braucht `TypeDecorator` für saubere Roundtrips.

### Option 3 — UUIDv7 (RFC 9562)

**Pro**
- Pydantic v2 hat nativen `UUID7`-Typ; JSON-Schema exportiert sauber
  als `format: uuid`. Keine Custom-Decorator-Last (ADR-0018-Alignment).
- SQLAlchemy 2.x hat nativen `Uuid`-Typ, der in SQLite (TEXT/BLOB)
  und Postgres (`UUID`-Spalte) transparent funktioniert.
- Postgres 18 (released 2025) bringt `gen_random_uuidv7()` builtin —
  Migration v2+ erbt nativen Generator-Support.
- Zeitstempel-Präfix: lexikographisch sortierbar, B-Tree-freundlich
  (relevant erst bei großen Volumen, hier zukunftsoffen).
- RFC-konform, sprachneutral — kein Lock-in auf Python-Spezifika.

**Contra**
- 36 Zeichen mit Hyphens (`01964e5a-1234-7abc-9def-0123456789ab`) sind
  in CLI-Listen unhandlich.
- `uuid.uuid7()` ist erst ab Python **3.14** in stdlib; in 3.13
  (ADR-0017-Mindestversion) braucht es einen Backport.
- Pydantic-`UUID7`-Typ validiert das Versions-Bit, **generiert
  nicht** — Generator bleibt extern.

## Entscheidung

Gewählt: **Option 3 — UUIDv7 mit `uuid-utils`-Backport für Python 3.13**.

### Begründung

1. **ADR-0018-Konformität entscheidend.** UUIDv7 ist der einzige Typ
   mit nativer Pydantic-v2- *und* nativer SQLAlchemy-Unterstützung
   beidseits SQLite und Postgres. ULID kostet überall einen Custom-
   Decorator und erzeugt drei Drift-Punkte (Generator, SQL-Spalte,
   JSON-Schema). INTEGER bricht den Abstraktions-Vorteil von Pydantic
   sobald Sync-Szenarien entstehen.
2. **ADR-0013-Postgres-Pfad sauber.** PG18 generiert UUIDv7 nativ —
   die Migration ist ein 1:1-Spaltentyp-Match ohne Custom-Conversion.
3. **CLI-Komfort via Präfix-Resolution mitigierbar.** `agentctl work
   show 01a3` matcht eindeutig per `WHERE id LIKE '01a3%'` — Pattern,
   das `git`, `docker`, `gh` und viele andere Tools etabliert haben.
   Solange < 1000 Rows/Tabelle sind 4–6 Zeichen kollisionsfrei
   ausreichend.
4. **Stabilität über Restore** garantiert, weil IDs in Application-
   Layer generiert werden und nicht von SQLite-internen ROWIDs
   abhängen.
5. **Insert-Performance irrelevant** im n=1-Volumen. Der Vorteil
   sequenzieller IDs ist zukunftsoffen, aber nicht der Treiber.

### Backport-Strategie

Solange Python 3.13 die Mindestversion ist (ADR-0017):

- Generator: `uuid_utils.uuid7()` aus dem `uuid-utils`-Paket
  (C-Backed, RFC 9562 v0.10+, 2024). Liefert standardkonforme
  `uuid.UUID`-Objekte, keine eigene Klasse.
- Pydantic-Typ: `UUID7` aus `pydantic.types` (validiert v7-Bit).
- SQLAlchemy-Spalte: `Uuid(as_uuid=True)`.

Bei späterem Upgrade auf Python 3.14:

- Import-Swap `from uuid_utils import uuid7` → `from uuid import uuid7`.
- `uuid-utils` aus `pyproject.toml` entfernen.
- Kein Datenformat-Wechsel, keine Migration nötig.

### CLI-Präfix-Resolution

Die CLI implementiert Präfix-Auflösung für alle Subcommands, die eine
ID als Argument nehmen (`work show`, `work transition`):

1. Versuche exakten Match auf vollständige UUIDv7.
2. Wenn kein Match: `WHERE id LIKE '<prefix>%'` mit user-eingegebenem
   Präfix (mindestens 4 Zeichen).
3. Bei genau einem Treffer: akzeptieren.
4. Bei mehreren Treffern: Fehler mit Auflistung der Kandidaten und
   minimaler eindeutiger Präfix-Länge.
5. Bei keinem Treffer: Exit-Code 2 (Nutzerfehler).

Listenausgaben (`work next`, `work show` Sub-Listen) zeigen die
ersten 8 Zeichen der UUIDv7 als Default; volle UUID nur in
maschinenlesbaren Outputs (`--output json`).

## Konsequenzen

**Positiv**
- ADR-0018 Pydantic-Single-Source bleibt konsistent (nativer Typ).
- ADR-0013-Postgres-Migration trivial (nativer `UUID`-Typ beidseits).
- Restore-Stabilität (ADR-0003 §10.4) durch Application-Layer-IDs
  garantiert.
- Sprachneutral: ein späterer Re-Implement in TS/Go würde dieselben
  IDs lesen können.

**Negativ**
- Eine externe Abhängigkeit (`uuid-utils`) bis Python-3.14-Upgrade.
  Mitigation: in `uv.lock` gepinnt, beim 3.14-Upgrade trivialer
  Import-Swap.
- 36-Zeichen-Display in CLI ist unkomfortabel; Mitigation per
  Präfix-Resolution + 8-Zeichen-Default in Listen.
- Pydantic-`UUID7`-Typ generiert nicht selbst — Generator-Aufruf
  muss bewusst `uuid_utils.uuid7()` sein, nicht `uuid.uuid4()`.

**Neutral**
- v0-Schema speichert IDs als `TEXT(36)` in SQLite (über SQLAlchemy
  `Uuid(as_uuid=True)`); v2+ Postgres-Spalte als `UUID`.
- F0001-Migrationen müssen `id` als `TEXT NOT NULL PRIMARY KEY` mit
  CHECK-Constraint `LENGTH(id) = 36` deklarieren — verhindert
  versehentliches Insert von ULIDs/INTs.

## Follow-ups

- F0001 Acceptance Criteria erweitern um:
  - „Insert eines `work_item.id` mit UUIDv4 (statt v7) wird im
    Application-Layer abgelehnt."
  - „Insert eines Strings, der nicht UUID-Format erfüllt, schlägt
    am SQL-CHECK fehl."
- F0002 Acceptance Criteria erweitern um die Präfix-Resolution
  (mindestens 4 Zeichen, Mehrdeutigkeit liefert Exit 2 mit
  Kandidaten-Liste).
- Spec §5.7 trägt `id: UUIDv7 (RFC 9562)` als normativen Spaltentyp.

## Referenzen

- ADR-0003 — SQLite + Litestream-Persistenz
- ADR-0013 — V1 Deployment Mode (Postgres als v2+ Upgrade-Pfad)
- ADR-0017 — Implementierungssprache (Python ≥ 3.13)
- ADR-0018 — Schema-First mit Pydantic als Single-Source
- F0001 — SQLite Schema for Core Objects
- RFC 9562 (UUID Version 7): <https://datatracker.ietf.org/doc/rfc9562/>
- `uuid-utils` Library: <https://github.com/aminalaee/uuid-utils>
- Python 3.14 `uuid.uuid7` (cpython issue #89083):
  <https://github.com/python/cpython/issues/89083>
- Pydantic v2 Standard Library Types (UUID1–8):
  <https://docs.pydantic.dev/latest/api/standard_library_types/>
- SQLModel UUID-Doku (SQLAlchemy `Uuid` SQLite/Postgres-Verhalten):
  <https://sqlmodel.tiangolo.com/advanced/uuid/>
- ardentperf — UUID Benchmark War (Page-Splits, Index-Größe):
  <https://ardentperf.com/2024/02/03/uuid-benchmark-war/>
- thenile.dev — UUIDv7 in PostgreSQL 18 (native `uuidv7()`):
  <https://www.thenile.dev/blog/uuidv7>
