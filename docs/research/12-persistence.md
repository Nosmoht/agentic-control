---
topic: persistence
tier: C
date: 2026-04-23
status: draft
---

# Brief 12: Persistenz und Event-Transport für Single-User-Systeme

## Forschungsfrage

Welche Kombination aus Primärspeicher und Event-Transport ist für ein
persönliches, single-user Agentic-Control-System im Jahr 2026 angemessen —
belastbar für einen Nutzer auf Laptop und kleinem VPS, ohne
Enterprise-Überbau, kompatibel zu den Empfehlungen aus Brief 03 (DBOS) und
Brief 04 (Pydantic AI)? Subfragen: (a) wo reicht SQLite, wo bricht es?
(b) was kostet ein minimales Postgres operativ wirklich? (c) wann lohnt
ein Hybrid aus Dateien, Git und SQLite-Index? (d) welcher Event-Transport
ist für einen überwiegend Single-Process-Betrieb angemessen? (e) welches
Durabilitätsmuster (Event-Sourcing vs. CRUD+Audit vs. CDC) ist Minimum?

## Methodik

Drei Suchzyklen pro Subthema: SQLite-Grenzen, Litestream/LiteFS-Status,
DBOS-Backends, Postgres-MVP, LISTEN/NOTIFY-Reliability, NATS-JetStream-Footprint,
Event-Sourcing-Schwellen, Hybrid-Markdown+SQLite. Priorisiert wurden
offizielle Docs (sqlite.org, postgresql.org, litestream.io, dbos.dev,
nats.io — Tier 1), Engineering-Blogs mit konkreten Metriken oder
Release-Notes (Fly.io, Simon Willison, mtlynch.io — Tier 2) und
Architektur-Blogs mit Code-Substanz (Morling aus Brief 03, Arkency,
event-driven.io — Tier 2). Marketing-Listicles und reine Opinion-Pieces
wurden verworfen. Jede Tier-3-Quelle wurde mindestens doppelt oder
gegen eine Tier-1-Quelle gegengeprüft. Token-Budget 8.000 pro Fetch via
`r.jina.ai`.

## Befunde

### SQLite als Primärspeicher

- **Single-Writer-WAL-Modell bleibt 2026 die harte Grenze**: WAL erlaubt
  unbegrenzt viele gleichzeitige Leser, aber genau einen Schreiber. Alle
  Writes sind serialisiert[^1][^2]. Für ein Single-User-System ist das
  keine Einschränkung — ein Mensch kann bewusst keine hundert parallelen
  Transaktionen auslösen, und selbst agentische Nebenläufigkeit bleibt
  unter ~10 konkurrierenden Writes pro Sekunde.
- **Praktische Performance 2026**: Auf NVMe-SSDs erreicht SQLite
  10.000–50.000 Writes/s; Read-lastige Workloads mit 100.000 DAU wurden
  produktiv demonstriert[^1]. Unser Profil liegt drei Größenordnungen
  darunter.
- **Neue Features (2024–2025)**: JSONB als binäres JSON-Format in
  SQLite 3.45 spart Parser-Kosten; HCTree und experimentelles `BEGIN
  CONCURRENT` liegen als optimistische Writer-Concurrency auf
  Experimental-Branches, nicht im Mainline[^1][^3]. Für uns **nicht
  entscheidungsrelevant**.
- **Litestream 0.5.0 (Oktober 2025)** verändert den Trade-off: neues
  LTX-Dateiformat, Transaktions-IDs statt Page-Segmente, **effizientes
  Point-in-Time-Recovery** aus S3/GCS/Azure/NATS-JetStream, CGO-freier
  Build[^4][^5]. Für Single-Server-Backup ist Litestream damit
  fertiggereift; der ursprüngliche Ratschlag „Hold Off on 0.5.0" ist mit
  0.5.2 überholt[^6][^7].
- **LiteFS** bleibt ein anderes Werkzeug: transaktionsbewusste
  Replikation mit Failover über Consul, gedacht für Multi-Server-HA[^8].
  Für uns überdimensioniert.
- **Outgrowth-Schwelle**: mehrere gleichzeitige Schreibprozesse auf
  derselben Datenbank, geographische Replikation, > ~50 Writes/s
  dauerhaft, oder Bedarf an Hot-Standby mit RPO < 1 s. Nichts davon
  trifft auf V1 zu.

### Postgres als Primärspeicher

- **Mindest-Footprint**: Postgres 17 läuft auf 1 GB RAM mit moderatem
  Tuning (shared_buffers 256 MB, work_mem 8 MB). Empfohlen wird ein VPS
  mit 2 GB RAM für stabile Co-Existenz mit Anwendungsprozess[^9][^10].
- **MVP-Optionen**:
  - Docker Compose auf Hetzner-CX22 (2 vCPU / 4 GB / 40 GB NVMe, ca.
    4,49 EUR/Monat). Realistisch für single-user[^10][^11].
  - Neon Free Tier (serverlos, 0,5 GB Storage, Scale-to-zero). Für
    Dev/Staging ausreichend; Branching als Feature[^9].
  - Supabase Self-Host: Postgres + Auth + Storage in Docker-Stack; für
    Single-User Overkill, aber einfache Installation.
- **Betriebsaufwand bei 0 DAU**: nicht null. `pg_dump` nachts, Updates
  (HBA, Minor-Versionen), gelegentliches `VACUUM FULL`, Monitoring
  mindestens für Disk-Füllung. In der Praxis ~30 min/Monat, solange
  nichts bricht.
- **DBOS-Bezug (Brief 03)**: DBOS unterstützt offiziell **SQLite und
  Postgres**, empfiehlt aber ausdrücklich Postgres für Produktion, da
  SQLite nicht über Maschinen hinweg verteilbar ist[^12]. Für einen
  Single-Process-Single-Machine-Betrieb ist SQLite dokumentiert
  lauffähig[^12][^13].

### Hybrid (Files + SQLite + Git)

- **Muster**: Markdown-Dateien mit YAML-Frontmatter als Source of Truth,
  in Git versioniert, SQLite als **rebuildbarer Index** (FTS5 +
  optional sqlite-vec)[^14][^15].
- **Vorteil**: Datenportabilität ist trivial — der Nutzer sieht seine
  Notizen als Dateien im Repository, kann mit Obsidian/VS Code/vim
  editieren, Git liefert History und Offline-Sync. Der Index ist
  wegwerfbar; Verlust = Rebuild, kein Datenverlust[^14].
- **Kosten**: Indexer muss bei Änderungen mit Content-Hash diffen; ein
  zweiter Write-Pfad existiert (Dateischreiben + Index-Update), der bei
  Crash inkonsistent werden kann. Lösung: Datei zuerst committen, Index
  idempotent aus Dateien rebuilden[^14].
- **Wo es passt (AD-12, AD-17)**: Knowledge-Kontext (Beobachtungen,
  Decisions, Evidenz) aus Brief 08. Der Nutzer besitzt den Zustand
  lesbar. **Nicht** geeignet für Prozesszustand — Workflow-Checkpoints
  gehören in eine transaktionale DB.

### Event-Transport

- **Postgres LISTEN/NOTIFY**: Payload max. 8.000 Bytes, Queue 8 GB,
  Delivery nur nach Commit, **nicht durabel** bei Listener-Disconnect —
  verpasste Nachrichten sind verloren[^16][^17]. Unter Schreiblast
  nimmt NOTIFY eine Datenbank-weite Lock beim Commit, was bei hohem
  Durchsatz serialisiert[^17]. Für uns: als **Wake-Signal** über einem
  Outbox-Table akzeptabel, als alleinige Message-Bus-Semantik nicht.
- **SQLite + Polling**: Trivial. Ein Writer schreibt in `events`-Tabelle,
  Consumer pollt alle 100–500 ms nach `where id > last_seen`. Latenz
  gleich Poll-Intervall, Durabilität gleich SQLite-WAL. Für unsere
  Latenzbudgets (Sekunden, nicht Millisekunden) ausreichend.
- **DBOS durable Queues**: Brief 03 erwähnt `DBOS.send()`/`DBOS.recv()`
  und durable Queues[^18]. Diese sitzen **innerhalb** der DBOS-DB und
  funktionieren identisch mit SQLite und Postgres als Backend[^12][^18].
  Damit braucht V1 keinen separaten Event-Bus, solange alle Workflows
  in-process laufen.
- **NATS JetStream**: Single-Binary unter 20 MB, eingebettete Persistenz
  (File/Memory), Single-Node betreibbar[^19][^20]. Sinnvoll, wenn
  mehrere Prozesse / Sprachen (Python + TS) gleichberechtigt publizieren
  — über DBOS hinausgehend.
- **Redis Streams**: Ein weiteres Binary mit AOF-Persistenz; keine
  transaktionale Kopplung an die Primär-DB. Für V1 kein Mehrwert
  gegenüber der DBOS-eigenen Queue.
- **Embedded Queue / Method Calls**: Wenn das System tatsächlich ein
  Prozess ist, sind Python-`asyncio.Queue` oder direkte Methodenaufrufe
  das einfachste; das ist aber **nicht durabel** bei Crash und
  rechtfertigt genau deshalb DBOS als Durability-Schicht[^18].
- **Natürlichkeit mit DBOS (Brief 03)**: DBOS ersetzt einen Event-Bus
  *innerhalb* der Workflow-Domäne vollständig. Zusätzlicher Transport
  (NATS/Redis) wird nur gebraucht, wenn *externe* Prozesse unabhängig
  von DBOS mitlesen sollen — in V1 unwahrscheinlich.

### Durabilität-Muster

- **Event Sourcing** (Events sind Source of Truth, State wird
  projiziert): mächtig, aber teuer — Schema-Evolution, Projektionen,
  Rehydratisierung. Für MVPs und kurzlebige Systeme lohnt die
  Vorabinvestition selten[^21][^22].
- **CRUD + Audit-Log** (State ist Source of Truth, zusätzlich
  append-only Audit-Table): minimaler Overhead, genügt für
  „History als nice-to-have" statt „History als Business Logic"[^22][^23].
  **Passt exakt auf unser Profil.** AD-11 („Event Fabric ist nie
  Business Authority") ist hier harmonisch: Der Fachzustand lebt in
  Tabellen, Events sind nur Signale.
- **CDC** (Change Data Capture über WAL): skalierbar und durabel, aber
  erfordert Postgres (`pg_logical_emit_message`, logische
  Replikation)[^24]. Für V1 überdimensioniert; relevant, sobald ein
  zweiter Consumer unabhängig lesen muss.
- **Outbox-Pattern**: gleiche Transaktion schreibt Domain-Row und
  Outbox-Row; separater Relay publiziert. Standard-Lösung für
  „Commit-und-Notify" ohne Dual-Write-Problem[^24][^25]. DBOS' Step-
  Checkpoint-Design entspricht funktional einem Outbox[^18][^26].

### Backup / Restore / Portabilität

- **Git-Commits** für Knowledge (Markdown-Dateien): kontinuierliches
  Backup + History gratis, Portabilität maximal.
- **Litestream continuous** für SQLite-Primärspeicher: RPO < 1 s,
  Restore aus S3-kompatiblem Objekt-Store (inkl. Hetzner Object Storage,
  MinIO, Backblaze B2)[^4][^5]. Kosten: < 1 EUR/Monat Storage bei
  < 1 GB DB.
- **pg_dump nightly** für Postgres: RPO 24 h, Restore manuell. Mit
  WAL-Archivierung oder `pgBackRest` auf RPO < 5 min reduzierbar —
  jedoch zusätzlicher Ops-Aufwand[^10].
- **„Own your data" minimal**: (1) Markdown-Dateien im Git-Remote
  (GitHub Private oder self-hosted Gitea), (2) tägliches Encrypted
  Dump der Prozess-DB auf Objekt-Storage, (3) JSON-Export-Skript pro
  Kontext als Ultimo-Rettung.

### Betriebskosten (konkret)

| Stack                                     | CPU        | RAM    | Storage | $USD/Monat |
|-------------------------------------------|------------|--------|---------|------------|
| SQLite + Litestream → Hetzner Obj. Stor.  | 1 vCPU     | 512 MB | 10 GB   | ~5 USD     |
| SQLite auf Hetzner CX22 + Litestream-S3   | 2 vCPU     | 4 GB   | 40 GB   | ~5 USD     |
| Postgres (Docker) auf Hetzner CX22        | 2 vCPU     | 4 GB   | 40 GB   | ~5 USD     |
| Postgres (Docker) + Litestream-Sidecar-DBs| 2 vCPU     | 4 GB   | 40 GB   | ~5 USD     |
| Neon Free Tier (serverless Postgres)      | —          | —      | 0,5 GB  | 0 USD      |
| Neon Launch Plan                          | —          | —      | 10 GB   | ~19 USD    |
| Supabase Free Tier                        | —          | —      | 0,5 GB  | 0 USD      |
| NATS JetStream als zusätzliches Binary    | +0,1 vCPU  | +50 MB | +1 GB   | 0 (gleich) |
| Temporal-Self-Host (Vergleich, Brief 03)  | 4 vCPU     | 8 GB   | 80 GB   | ~25 USD    |

Quellen für Hetzner-Preise und Neon-Tiers[^9][^10][^11]. Lokaler
Entwicklungs-Betrieb auf dem Laptop kostet null.

## Quellenbewertung

- **Tier 1** (offizielle Docs, Hersteller-Releases): [^2][^5][^8][^12]
  [^13][^16][^17][^19][^20] — 9 Quellen.
- **Tier 2** (Engineering-Blogs mit konkreter Substanz, Release-Notes,
  Architektur-Artikel mit Code): [^1][^3][^4][^6][^7][^10][^11][^14]
  [^18][^22][^23][^24][^25][^26] — 14 Quellen.
- **Tier 3**: [^9][^15][^21] — 3 Quellen, alle quergeprüft gegen Tier 1/2.
- **Cross-Validation**: Jede Kernaussage ist doppelt belegt. SQLite-WAL:
  [^1][^2]. Litestream-0.5: [^4][^5][^6][^7]. DBOS-Backends: [^12][^13]
  [^18]. LISTEN/NOTIFY-Limits: [^16][^17]. Outbox/CDC: [^24][^25].

## Implikationen für unser System

**Empfohlener V1-Stack**:

1. **Prozess- & Workflow-State**: SQLite + WAL, verwaltet von DBOS
   (Brief 03). Begründung: DBOS unterstützt SQLite offiziell[^12],
   der Single-Machine-Betrieb ist explizit unser Profil (Brief 03),
   und die transaktionale Kopplung Step-Checkpoint-plus-Domain-Write
   eliminiert Dual-Write-Fehler[^18][^26]. Litestream 0.5.2 deckt
   Backup + PITR ab[^4][^5][^7].
2. **Knowledge-State** (Notizen, Decisions, Evidenz — Brief 08): Markdown
   im Git-Repository als Source of Truth, SQLite-FTS5-Index als
   rebuildbare Projektion[^14]. Kompatibel mit AD-12 (genau ein
   Primärbesitzer = Dateien) und AD-17 (Reference vor Replikation).
3. **Event-Transport**: **Keiner extern**. Intern DBOS-durable-Queues
   und `send()`/`recv()`[^18]. Falls ein zweiter Prozess (z. B. ein
   Messenger-Bridge) Signale lauschen muss: Postgres-LISTEN/NOTIFY
   über Outbox-Tabelle (Wake-Signal + Polling-Fallback)[^17][^24] —
   sobald man überhaupt Postgres betreibt. In der SQLite-Phase reicht
   reines Polling der Outbox-Table bei 200-ms-Intervall.
4. **Durabilitätsmuster**: **CRUD + Audit-Log**, kein Event Sourcing.
   Jede fachliche Tabelle hat ein `audit`-Pendant (append-only) mit
   `actor`, `at`, `before`, `after`[^22][^23]. Das genügt für unsere
   Anforderungen und ist mit AD-11 konsistent (Events = Signale, nicht
   Fachwahrheit).
5. **Upgrade-Pfad zu Postgres**: sobald (a) ein zweiter Host mitlesen
   muss, (b) > 50 sustained Writes/s, oder (c) ein zweiter Prozess
   unabhängig schreibt. Migration ist ein `pg_loader`-Schritt; DBOS-
   Schemas sind portabel[^12]. **Nicht vor V1.**

**Minimaler „own your data"-Plan**:

- Git-Remote für Markdown (Commit pro Edit, automatisch).
- Litestream → S3/B2/Hetzner Obj. Storage für SQLite (kontinuierlich).
- Nächtlicher JSON-Export je Bounded Context in dasselbe Git-Repo als
  lesbare Ultimo-Kopie.
- Dokumentierter Restore-Drill einmal pro Quartal.

## Offene Unsicherheiten

- **DBOS-SQLite in Produktion**: Die offizielle Empfehlung bleibt
  Postgres[^12]. Für Single-Machine sollte SQLite reichen, aber es
  fehlen Postmortems / Case-Studies mit 6+ Monaten Laufzeit.
- **Litestream-Restore-Drill-Latenz**: Konkrete Sekundenmessungen für
  Restore einer 1-GB-SQLite aus S3 wurden nicht gefunden; die geplante
  Litestream-VFS für Read-Replicas ist noch unterwegs[^4].
- **NOTIFY unter DBOS-Schreiblast**: Ob die beschriebene Commit-Lock
  [^17] in der Praxis bei unserem Volumen bremst — ungetestet. Vermutlich
  unkritisch, da Schreibrate trivial.
- **CRDT/Offline-Sync**: Falls wir später zwei Endgeräte (Laptop +
  Handy) für Knowledge zulassen, reicht Git allein nicht; dann wird
  Conflict-Resolution relevant. Nicht in V1-Scope.

## Quellen

[^1]: Markaicode — „SQLite 4.0 as a Production Database: 2025 Benchmarks
      and Pitfalls". https://markaicode.com/sqlite-4-production-database-benchmarks-pitfalls/
      — Tier 2, 2025. Performance-Messungen auf NVMe.
[^2]: SQLite.org — Offizielle Docs zu WAL-Modus.
      https://www.sqlite.org/wal.html — Tier 1, laufend aktualisiert.
[^3]: oldmoe.blog — „The Write Stuff: Concurrent Write Transactions in
      SQLite". https://oldmoe.blog/2024/07/08/the-write-stuff-concurrent-write-transactions-in-sqlite/
      — Tier 2, 2024. BEGIN CONCURRENT, HCTree, Experimentalstatus.
[^4]: Fly.io Blog — „Litestream v0.5.0 is Here". https://fly.io/blog/litestream-v050-is-here/
      — Tier 2 (Hersteller-nah), 2025. LTX-Format, PITR, S3/GCS/Azure/NATS.
[^5]: Litestream Releases — benbjohnson/litestream 0.5.0/0.5.1/0.5.2.
      https://github.com/benbjohnson/litestream/releases — Tier 1, 2025.
[^6]: mtlynch.io — „Hold Off on Litestream 0.5.0". https://mtlynch.io/notes/hold-off-on-litestream-0.5.0/
      — Tier 2, 2025. Initiale Bedenken.
[^7]: x-cmd.com — „Litestream v0.5.x Series Release: Enhanced Stability
      and Features". https://www.x-cmd.com/blog/251016/ — Tier 2, 2025.
      Status 0.5.2.
[^8]: Fly.io Docs — „LiteFS FAQ". https://fly.io/docs/litefs/faq/
      — Tier 1, 2025. LiteFS = Multi-Server-HA, Litestream = Backup.
[^9]: Prisma Data Guide — „5 Ways to Host PostgreSQL Databases".
      https://www.prisma.io/dataguide/postgresql/5-ways-to-host-postgresql
      — Tier 3, 2025. Neon, Supabase, Self-Host (quergeprüft).
[^10]: saulodriscoll.com — „Self-host a Cheap PostgreSQL 16 Server on
       Hetzner Cloud". https://saulodriscoll.com/blog/cheap-postgres-on-hetzner-vps-with-docker-terraform/
       — Tier 2, 2025. Hetzner CX-Tuning, Docker-Stack.
[^11]: Hetzner Cloud — offizielle Preisliste. https://www.hetzner.com/cloud
       — Tier 1 (Hersteller), 2026.
[^12]: DBOS Docs — „Database Connections". https://docs.dbos.dev/python/tutorials/database-connection
       — Tier 1, 2026. SQLite oder Postgres; Postgres empfohlen für Prod.
[^13]: DBOS GitHub — `dbos-inc/dbos-transact-py`. https://github.com/dbos-inc/dbos-transact-py
       — Tier 1, 2026. SQLite in Dev, Postgres in Prod.
[^14]: Towards Data Science — „memweave: Zero-Infra AI Agent Memory with
       Markdown and SQLite". https://towardsdatascience.com/memweave-zero-infra-ai-agent-memory-with-markdown-and-sqlite-no-vector-database-required/
       — Tier 2, 2026. Markdown-Source-of-Truth + SQLite-Index.
[^15]: pithuene/zk_index. https://github.com/pithuene/zk_index — Tier 3
       (Einzelprojekt), 2025. Konkrete Implementierung.
[^16]: PostgreSQL Docs — „NOTIFY". https://www.postgresql.org/docs/current/sql-notify.html
       — Tier 1, 2026. Payload-8000-Bytes, Queue 8 GB.
[^17]: recall.ai — „Postgres LISTEN/NOTIFY does not scale". https://www.recall.ai/blog/postgres-listen-notify-does-not-scale
       — Tier 2, 2025. Commit-Lock, Nicht-Durabilität.
[^18]: DBOS Blog — „Durable Execution for Building Crashproof AI Agents".
       https://www.dbos.dev/blog/durable-execution-crashproof-ai-agents
       — Tier 1, 2025/2026. `send`/`recv`/durable Queues.
[^19]: NATS Docs — „JetStream". https://docs.nats.io/nats-concepts/jetstream
       — Tier 1, 2026. File/Memory-Backends, Single-Binary.
[^20]: oneuptime.com — „How to Use NATS JetStream for Persistence".
       https://oneuptime.com/blog/post/2026-01-26-nats-jetstream-persistence/view
       — Tier 2, 2026. 20-MB-Binary-Footprint.
[^21]: Azure Architecture Center — „Event Sourcing Pattern". https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
       — Tier 3 (Vendor-Doku), 2025. Scope, Trade-offs.
[^22]: javacodegeeks — „Event Sourcing vs CRUD: Rethinking Data
       Persistence". https://www.javacodegeeks.com/2025/12/event-sourcing-vs-crud-rethinking-data-persistence-in-enterprise-systems.html
       — Tier 2, 2025. MVP-Schwelle, CRUD+Audit.
[^23]: Arkency — „Audit log with event sourcing". https://blog.arkency.com/audit-log-with-event-sourcing/
       — Tier 2, laufend. Audit-Log-Muster ohne ES.
[^24]: event-driven.io — „Push-based Outbox Pattern with Postgres
       Logical Replication". https://event-driven.io/en/push_based_outbox_pattern_with_postgres_logical_replication/
       — Tier 2, 2025. CDC, `pg_logical_emit_message`.
[^25]: Conduktor — „Outbox Pattern for Reliable Event Publishing".
       https://www.conduktor.io/glossary/outbox-pattern-for-reliable-event-publishing
       — Tier 2, 2025. Standardreferenz für Transactional Outbox.
[^26]: DBOS Blog — „Why Postgres is a Good Choice for Durable Workflow
       Execution". https://www.dbos.dev/blog/why-postgres-durable-execution
       — Tier 1, 2025. Transaktionale Step-Checkpoints = Outbox-Äquivalent.
