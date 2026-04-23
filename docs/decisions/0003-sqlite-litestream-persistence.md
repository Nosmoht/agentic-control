# ADR-0003: SQLite WAL + Litestream, Postgres als Upgrade-Pfad

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §4.1, §7`

## Kontext und Problemstellung

Das System braucht einen Primärspeicher für Work Items, Runs, Dependencies,
Observations, Standards, Artifacts. Anforderungen: durable, portabel,
kostenminimal, Backup automatisch, nicht Enterprise.

## Entscheidungstreiber

- Single-User, Single-Prozess in V1.
- Kostendeckel ≤ ~$5/Monat Infrastruktur.
- Datenportabilität (kein Lock-in).
- Automatisiertes Backup ohne manuelles Skript-Hygiene.
- Kompatibilität mit DBOS (ADR-0002), das SQLite im Dev und Postgres in Prod
  unterstützt.

## Erwogene Optionen

1. **SQLite WAL + Litestream** → S3-kompatibles Object Storage.
2. **Postgres** (self-host auf kleinem VPS) mit `pg_dump` nightly.
3. **Files + SQLite + Git** (Hybrid: Markdown in Git, SQLite nur als Index).
4. **Embedded Postgres** (z. B. embedded-postgres) im Prozess.

## Entscheidung

Gewählt: **Option 1 für V1 (SQLite WAL + Litestream), Option 2 als
Upgrade-Pfad**. Option 3 ergänzend für Knowledge-Modul (Markdown in Git
bleibt Quelle, SQLite-FTS5 als rebuildbarer Index).

### Konsequenzen

**Positiv**
- Minimale Abhängigkeiten — SQLite ist überall verfügbar.
- Litestream liefert Point-in-Time-Recovery automatisch.
- Markdown-im-Git für Knowledge: Git ist das natürliche Versionierungs­system
  für Notizen; SQLite-Index ist rebuildbar und wegwerfbar.
- Upgrade-Pfad zu Postgres ist einmaliger Datenimport, DBOS-Schema portabel.

**Negativ**
- DBOS + SQLite in Produktion offiziell dünn dokumentiert.
- Single-Writer-Model von SQLite beschränkt Concurrency; Upgrade zu Postgres
  wird Pflicht sobald > 1 Schreibprozess.
- Litestream-Restore-Latenz für > 1 GB-DBs aus Object Storage nicht gemessen.

**Neutral**
- Kosten: lokal $0, VPS-Variante ~$5/Monat (Hetzner CX22 + Object Storage).

## Pro und Contra der Optionen

| Option | Ops | Kosten | Upgrade-Pfad | Backup |
|---|---|---|---|---|
| SQLite + Litestream | minimal | $0–$5 | klar | automatisch |
| Postgres | moderat | $5+ | direkt | manuell oder WAL-Archivierung |
| Files + SQLite + Git | niedrig | $0 | komplex bei Volumen | Git-nativ |
| Embedded Postgres | moderat | $0 | offen | manuell |

## Upgrade-Trigger zu Postgres

- Zweiter Prozess oder Host muss gleichberechtigt lesen/schreiben.
- Sustained Writes > ~50/s.
- Messenger-Bridge als separater Prozess soll durable auf Events reagieren
  (LISTEN/NOTIFY + Outbox).

## Referenzen

- `docs/research/12-persistence.md` — Stack-Empfehlung + Betriebskosten
- `docs/research/03-durable-execution.md` — DBOS-Storage-Support
- Litestream: https://litestream.io/
- SQLite WAL: https://www.sqlite.org/wal.html
