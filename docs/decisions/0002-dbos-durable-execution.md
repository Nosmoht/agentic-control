# ADR-0002: DBOS als Durable-Execution-Engine

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §4.1, §7`

## Kontext und Problemstellung

Das Work-Modul braucht verlässliche, langlebige Orchestrierung mit Wait,
Resume, Retry. Agent-Runs dauern Minuten bis Stunden. Der Prozess darf
abstürzen, ohne Zustand zu verlieren. Gleichzeitig soll die Engine nicht
Enterprise-Kosten oder -Komplexität erzeugen.

## Entscheidungstreiber

- Single-User-Betrieb, Ziel Laptop + optional kleiner VPS.
- Transaktionale Kopplung von Step-Checkpoint und Domänen-Write soll
  Dual-Write-Fehler **auf der DB-Seite** per Design ausschließen.
  (Externe Effekte mit lokal-only-Idempotenz adressiert ADR-0011
  V0.2.3-draft separat über Reconciliation; das ist eine orthogonale
  Klasse, die DBOS allein nicht löst.)
- Keine separate Cluster-Infrastruktur (Kassandra, Elasticsearch).
- Integration mit gängigen LLM/Agent-Stacks (Pydantic AI, OpenAI Agents,
  LlamaIndex) wünschenswert.

## Erwogene Optionen

1. **Temporal** — Workflow-as-Code, Industriestandard, aber Multi-Service
   + Cassandra/Postgres + optional Elasticsearch.
2. **Restate** — Single-Binary, RocksDB + Bifrost, aktivitätsbasiertes Modell.
3. **DBOS** — In-Process-Library, Step-Checkpoints in derselben DB-Transaktion.
4. **Inngest** — serverless-first, Self-Host möglich als Single-Binary.
5. **Eigenbau** — SQLite + State Machine, 500–1500 LOC.

## Entscheidung

Gewählt: **Option 3 — DBOS**.

### Konsequenzen

**Positiv**
- Step-Checkpoint und Domänen-Write im selben Commit eliminiert die
  „Schritt durch, Domäne nicht"-Fehlerklasse konstruktiv.
- Eine Abhängigkeit (Postgres in Prod, SQLite in Dev) — minimales
  Infrastruktur-Footprint.
- Erstklassige Integration zu Pydantic AI, OpenAI Agents, LlamaIndex.
- In-Process-Modell passt zu Single-User-Betrieb ohne Cluster.

**Negativ**
- DBOS + SQLite in Produktion ist offiziell dünner dokumentiert — offizielle
  Empfehlung bleibt Postgres.
- Noch junger Stack verglichen mit Temporal — geringere Community.
- Versioning-Primitive weniger reich als Temporal `getVersion`.

**Neutral**
- Bei Wachstum auf > 1 Prozess oder > 1 Sprache bleibt Upgrade-Pfad zu
  Temporal offen (Umschreibung erforderlich, aber Datenmodell portierbar).

## Pro und Contra der Optionen

| Option | Deployment | Passt n=1 | Agent-Integration | Ops-Aufwand |
|---|---|---|---|---|
| Temporal | Multi-Service + Cluster-DB | Overkill | reich | hoch |
| Restate | Single-Binary | ja | gut | mittel |
| DBOS | In-Process | ja | erstklassig | minimal |
| Inngest | Serverless/Binary | ja | mittel | mittel |
| Eigenbau | keiner | ja | keiner | trügerisch |

## Referenzen

- `docs/research/03-durable-execution.md` — Framework-Vergleich
- `docs/research/12-persistence.md` — Persistenz-Stack-Kombination
- `docs/research/04-agent-orchestration-libs.md` — Layer-Einordnung
- DBOS Docs: https://docs.dbos.dev/
