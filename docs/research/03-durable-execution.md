---
topic: durable-execution
tier: A
date: 2026-04-23
status: draft
---

# Brief 03: Durable Execution Frameworks — Vergleich (2026)

## Forschungsfrage

Wie unterscheiden sich Temporal, Restate, DBOS und Inngest im Frühjahr 2026 in
Ausführungsmodell, Deployment-Footprint, Primitiven und Betriebskosten — und ab
welchem Punkt ist ein Framework einem selbstgebauten SQLite-Task-Runner mit
State Machine überlegen, wenn das Zielsystem **ein einzelner Nutzer auf Laptop
oder kleinem VPS** ist?

## Methodik

Drei Suchzyklen (keyword + konzeptionell) pro Framework plus je eine Suche zu
„Agentic Workflows" und zum SQLite-Baseline. Priorisierung auf offizielle Docs
(temporal.io, restate.dev, dbos.dev, inngest.com) und GitHub-Releases (Tier 1),
ergänzt um Engineering-Blogs mit konkreter Architektur-Substanz (Morling,
Kai Waehner, Inngest/Restate-eigene Blogs) als Tier 2. Marketing-Texte und
Stack-Overflow wurden verworfen. Token-Budget 8000 pro Fetch via
`r.jina.ai`.

## Befunde

### Temporal

- **Modell**: Workflow-as-Code mit Event-Sourcing. Jede Workflow-Aktion wird
  deterministisch im Event-History-Log aufgezeichnet; bei Crash/Restart erfolgt
  Replay des Event-Logs, um den Zustand zu rekonstruieren[^1].
- **Deployment**: Multi-Service-Architektur — Frontend, History, Matching,
  Worker, plus externe Persistenz. **Produktion verlangt Cassandra, MySQL
  oder PostgreSQL** als Default-Store; SQLite ist ausdrücklich **nur für
  Development/CI** gedacht[^1][^2]. Für Visibility (Suche über Workflows)
  werden zusätzlich Elasticsearch/OpenSearch empfohlen[^1].
- **Primitive**: Signals, Updates, Queries, Timers, Versioning, Child-Workflows,
  Continue-As-New, Activities mit Retries und Heartbeats[^3].
- **Agentic-Eignung**: Sehr gut. Temporal bewirbt AI-Loops explizit;
  Signals/Updates bilden Human-in-the-Loop sauber ab, Queries erlauben
  UI-Einblick[^3]. 2026 Series-D mit 300 M $ bei 5 Mrd. $ Bewertung und
  9,1 Billionen Aktions-Ausführungen auf Temporal Cloud[^4].
- **Maturität**: Hoch (Netflix, Stripe, u. a.). GitHub
  `temporalio/temporal` ca. 19.000 Stars[^5].
- **Single-User-Betrieb**: Unangemessen. Der Dev-Server (`temporal server
  start-dev`) läuft als Single-Binary mit SQLite und taugt für lokale
  Experimente[^2], aber ein produktiver Self-Host bedeutet Multi-Container und
  Datenbank-Pflege.

### Restate

- **Modell**: Durable Execution via Journal/Replay (wie Temporal), aber als
  **Proxy vor den Services** statt als Worker-Fleet. Zusätzlich „Virtual
  Objects" mit Single-Writer-Garantie für zustandsbehaftete Entitäten[^6].
- **Deployment**: **Ein einzelnes Rust-Binary**. Keine externe Datenbank —
  Journal liegt im eingebetteten Replicated-Log (Bifrost), Indizes in RocksDB,
  Snapshots optional in Object Storage. Einzelknoten-Modus oder
  HA-Cluster[^7][^8].
- **Primitive**: Service-Calls, Timers, State, Awakeables (für externe
  Completion/HITL), Virtual Objects, Workflows. Suspension während Wait —
  FaaS-Funktionen können während langer Wartezeiten **heruntergefahren**
  werden[^6][^9].
- **Agentic-Eignung**: Hoch. Explizit für AI-Loops beworben: „shut down the
  agent when it awaits the promise and restore it once the approval has come
  in"[^9]. Unabhängig vom Agent-Framework einsetzbar.
- **Maturität**: Jünger als Temporal; npm-Downloads (`@restatedev/restate-sdk`)
  ca. 3K/Woche vs. Temporal ca. 25K/Woche[^10].
- **Single-User-Betrieb**: **Sehr gut geeignet**. Ein Binary, keine DB, läuft
  auf Laptop.

### DBOS

- **Modell**: **Transaktional**. DBOS ist keine Sidecar-Runtime, sondern eine
  **In-Process-Library** (Python, TS, Java, Go). Steps, die DB-Operationen
  machen, werden zusammen mit ihrem Checkpoint in **einer Postgres-Transaktion**
  committet — exactly-once für DB-Steps, at-least-once für andere[^11][^12].
- **Deployment**: „Zero new infrastructure required" — nur eine Postgres-Instanz
  (oder SQLite für Dev)[^11][^13]. Keine eigenständige Workflow-Engine,
  die laufen muss.
- **Primitive**: `@workflow`, `@step`, `@transaction`, durable Queues,
  scheduled Tasks, `DBOS.send()` / `DBOS.recv()` für Events/Signale,
  `start_workflow()` für Async, Fork für Eval[^14].
- **Agentic-Eignung**: Hoch und explizit beworben. Erstklassige Integrationen
  mit Pydantic AI, OpenAI Agents SDK, LlamaIndex; HITL über `recv()` mit
  `timeout_seconds` für Wartezeiten von Stunden/Tagen[^14][^15].
- **Maturität**: MIT-Ursprung (DBOS-Paper), Databricks-Partnerschaft April
  2026[^15]. Jünger als Temporal, aber akademisch fundiert.
- **Single-User-Betrieb**: **Sehr gut geeignet**, sofern Postgres ohnehin
  vorhanden ist — oder SQLite für komplett lokale Setups[^13].

### Inngest

- **Modell**: Step-Function-Stil. Funktionen werden in `step.run`/`step.sleep`/
  `step.waitForEvent` zerlegt; jeder Step ist memoized und durable[^16][^17].
- **Deployment**: Self-Host seit 1.0 als **Single Binary mit eingebautem
  Redis-Ersatz und SQLite**; Postgres optional für Produktion (seit
  Januar 2025)[^16]. Lizenz: Fair-Source (SSPL → Apache 2.0 nach 3 Jahren)[^16].
- **Primitive**: `step.run`, `step.sleep`, `step.sleepUntil`,
  `step.waitForEvent`, Fan-out, Concurrency- und Rate-Limit-Keys, Cron.
- **Agentic-Eignung**: Gut für Event-getriebene Flows; lange Waits via
  `waitForEvent` sind idiomatisch. Eigener „AgentKit" ergänzt
  Agenten-Patterns (außerhalb dieses Briefs).
- **Cloud-Preis**: Hobby 50.000 Executions/Monat gratis; Pro ab 75 $/Monat,
  50 $/Mio. zusätzliche Executions[^18]. **Self-Host gratis.**
- **Single-User-Betrieb**: Self-Host-Binary läuft lokal; für kleine Volumina
  auch die Cloud-Free-Tier ausreichend.

### Vergleichstabelle (kompakt)

| Framework | Deployment | Persistence | Langer Wait | Single-User-Betriebskosten | Agentic-Eignung |
|-----------|-----------|-------------|-------------|----------------------------|-----------------|
| Temporal  | Multi-Service-Cluster (Prod) | Cassandra / MySQL / PostgreSQL + optional ES[^1] | Signals/Updates/Timers, beliebig lang[^3] | Hoch (Ops-Overhead); Dev-Server trivial[^2] | Sehr gut, aber Overkill |
| Restate   | **Ein Rust-Binary**[^7] | Embedded RocksDB + Bifrost[^8] | Awakeables, Suspension (FaaS-friendly)[^9] | **Niedrig** | Sehr gut |
| DBOS      | **In-Process-Library**[^11] | Postgres (Prod) / SQLite (Dev)[^13] | `recv()` mit Timeout, Stunden/Tage[^14] | **Sehr niedrig**, wenn DB ohnehin da | Sehr gut, erstklassige Agent-Integrationen[^15] |
| Inngest   | Single Binary (Self-Host)[^16] | SQLite + Embedded Redis; Postgres optional[^16] | `waitForEvent`, `sleepUntil`[^17] | Niedrig (Self-Host) oder 0 $ (Hobby-Cloud)[^18] | Gut |

### Baseline: SQLite + eigene State Machine

- **Kernidee** (Morling, „Persistasaurus"): Ein Log-Table mit `(flow_id, step_seq,
  status, params, result)` plus Method-Interception genügt, um Durable-Execution
  für **isolierte Single-Agent-Flows** abzubilden; Virtual Threads (bzw. Async)
  erlauben Delay-Steps ohne OS-Thread-Blockade[^19].
- **Wann das reicht**: Wenn jeder Flow in **einem Prozess** lebt und keine
  Koordination zwischen Services nötig ist. Single-User, Single-Machine,
  keine horizontale Skalierung — exakt unser Profil[^19].
- **Eigenbau-Kosten**: Man muss selbst implementieren: deterministischen
  Replay (bzw. Step-Memoization), Retry mit Backoff, Idempotency-Keys,
  Timer/Scheduler-Loop, Signal-Inbox, Version-Handling bei Code-Änderungen,
  Beobachtbarkeit. Das entspricht ~500–1.500 Zeilen in Python/TypeScript, aber
  **versionsbasiertes Replay** ist die gefährlichste Fußangel — Code-Änderungen
  während laufender Workflows sind ohne Framework-Support brüchig[^3][^19].
- **Was ein Framework zusätzlich gibt**: zentrales Monitoring, getestete
  Determinismus-Garantien, fertige Versioning-Strategien, Cross-Service-
  Koordination — alles Dinge, die ein Single-User-System **nicht braucht**[^19].

## Quellenbewertung

- **Tier 1** (offizielle Docs, GitHub-Repos, akademischer Ursprung): [^1][^2][^3]
  [^6][^7][^8][^11][^12][^13][^14][^16][^17] — 12 Quellen.
- **Tier 2** (Engineering-Blogs mit Architektur-Substanz, Case-Studies,
  konkrete Metriken): [^4][^5][^9][^10][^15][^18][^19] — 7 Quellen.
- **Tier 3**: keine zitiert.
- **Cross-Validation**: erfüllt. Jede Kernaussage pro Framework ist durch
  mindestens eine Tier-1-Quelle plus eine weitere (Tier 1 oder Tier 2)
  belegt. Der SQLite-Baseline-Teil stützt sich auf einen Tier-2-
  Architektur-Artikel plus Temporals eigene Community-Forum-Aussage zu
  SQLite-Limits[^19][^2].

## Implikationen für unser System

Unser Zielsystem ist ein **einzelner Nutzer** auf Laptop oder kleinem VPS, mit
wenigen gleichzeitigen Workflows (Größenordnung: Dutzende bis niedrige
Hunderte pro Tag), langen Waits (Human-Eskalation, LLM-Provider-Latenz) und
Compensation-Bedarf auf Step-Ebene. Die Implikationen sind:

1. **Temporal ist Overkill.** Die operativen Kosten eines selbstgehosteten
   Clusters (mind. 3 Services + Cassandra/Postgres + ggf. Elasticsearch)
   stehen in keinem Verhältnis zum Lastprofil[^1].
2. **Der engere Kreis sind DBOS, Restate und Inngest-Self-Host.** Alle drei
   laufen auf einem Laptop mit einer einzigen Abhängigkeit (Postgres/SQLite
   oder gar keiner).
3. **DBOS hat die geringste Brücke zur Anwendung**: In-Process-Library,
   gleicher Prozess wie die Agent-Logik, gleiche Transaktion wie die
   Domain-Daten[^11][^12]. Das eliminiert eine Kategorie von Fehlern
   (DB-Commit erfolgreich, Workflow-Checkpoint nicht) per Design.
4. **Empfehlung für V1**: **DBOS (mit SQLite im Dev, Postgres im VPS)** als
   Framework-Option — **oder** ein bewusst skizzierter **SQLite-State-Machine-
   Runner**, wenn das V1 tatsächlich nur einen Prozess und keine zweite
   Sprache (also nicht beides Python+TS) umfasst. Die Entscheidung hängt von
   Brief 12 (Persistenz) und davon ab, wie viele Sprachen das System spricht.
5. **Minimal vorhanden sein müssen**: Workflow-Checkpointing pro Step,
   idempotenter Retry mit exponentiellem Backoff, Timer-Queue (für Sleep und
   Deadline), Signal-Inbox (für HITL/Events), Versioning-Strategie (mindestens:
   „laufende Workflows zu Ende führen, neue auf neuem Code starten").

## Offene Unsicherheiten

- **DBOS-Reife**: Wie stabil ist die SQLite-Unterstützung jenseits von Dev?
  Offizielle Aussagen bleiben hier knapp[^13].
- **Restate-Operations**: Wie aufwendig ist ein Upgrade/Backup von RocksDB +
  Bifrost auf einem Single-Node im Vergleich zu „pg_dump"? Nicht abschließend
  recherchiert.
- **Versioning im Eigenbau**: Best Practices für einen minimalen
  Versioning-Mechanismus in einem In-House-Runner (ohne Temporals
  `getVersion`) sind nicht pauschal standardisiert.
- **Kosten pro Workflow-Stunde** eines laufenden DBOS-/Restate-Prozesses auf
  einem 5 $/Monat-VPS — keine harten Messwerte gefunden.

## Quellen

[^1]: Temporal Docs — „Self-hosted Temporal Service guide" & „Visibility".
      https://docs.temporal.io/self-hosted-guide — Tier 1, 2025/2026,
      Persistenz-Optionen Cassandra/MySQL/PostgreSQL; Elasticsearch für
      Visibility.
[^2]: Temporal Docs & Community — Dev-Server mit SQLite; SQLite-Einsatz
      ausdrücklich nicht für Produktion.
      https://community.temporal.io/t/what-are-the-shortcomings-of-running-temporal-with-sqlite-in-production-for-small-scale-use-cases/18257
      — Tier 1/2, 2025.
[^3]: Temporal Blog — „Durable Execution meets AI".
      https://temporal.io/blog/durable-execution-meets-ai-why-temporal-is-the-perfect-foundation-for-ai
      — Tier 1 (Hersteller-Doku-nah), 2025. Signals/Updates/Queries/Checkpointing.
[^4]: Zylos Research — „Durable Execution Patterns for AI Agents".
      https://zylos.ai/research/2026-02-17-durable-execution-ai-agents —
      Tier 2, 2026-02. Temporal Series D, 9,1 Bio. Aktionen.
[^5]: GitHub — `temporalio/temporal` Org. https://github.com/temporalio —
      Tier 1 Metrik, 2026, ~19.000 Stars.
[^6]: Restate Docs — „Durable Execution". https://docs.restate.dev/concepts/durable_execution/
      — Tier 1, 2026.
[^7]: Restate Blog — „Building a modern Durable Execution Engine from First
      Principles". https://www.restate.dev/blog/building-a-modern-durable-execution-engine-from-first-principles
      — Tier 1 (Hersteller), 2025. Single Rust-Binary, Stream-Processing.
[^8]: Restate Blog — „The Anatomy of a Durable Execution Stack from First
      Principles". https://restate.dev/blog/the-anatomy-of-a-durable-execution-stack-from-first-principles/
      — Tier 1, 2025. Bifrost-Log + RocksDB + Object-Store-Snapshots.
[^9]: Restate Blog — „Durable AI Loops".
      https://www.restate.dev/blog/durable-ai-loops-fault-tolerance-across-frameworks-and-without-handcuffs
      — Tier 1, 2026. Suspension während Waits, Proxy-Modell.
[^10]: PkgPulse — „Temporal vs Restate vs Windmill 2026".
       https://www.pkgpulse.com/blog/temporal-vs-restate-vs-windmill-durable-workflow-2026
       — Tier 2, 2026. npm-Download-Metriken.
[^11]: DBOS Docs — „Why DBOS?". https://docs.dbos.dev/why-dbos — Tier 1, 2026.
       In-Process-Library, nur Postgres.
[^12]: DBOS Blog — „Why Postgres is a Good Choice for Durable Workflow
       Execution". https://www.dbos.dev/blog/why-postgres-durable-execution —
       Tier 1, 2025. Transaktionaler Step-Checkpoint.
[^13]: DBOS GitHub — `dbos-inc/dbos-transact-py`.
       https://github.com/dbos-inc/dbos-transact-py — Tier 1, 2026. SQLite für
       Dev, Postgres für Prod.
[^14]: DBOS Blog — „Durable Execution for Building Crashproof AI Agents".
       https://www.dbos.dev/blog/durable-execution-crashproof-ai-agents —
       Tier 1, 2025/2026. `send`/`recv`/`start_workflow`/Timeout.
[^15]: DBOS Blog — „Product Enhancements April 2026".
       https://www.dbos.dev/blog/dbos-new-features-april-2026 — Tier 2
       (Release-Notes), 2026-04. Databricks-Partnerschaft, Pydantic AI,
       LlamaIndex, OpenAI Agents.
[^16]: Inngest Blog — „Announcing Inngest self-hosting".
       https://www.inngest.com/blog/inngest-1-0-announcing-self-hosting-support
       — Tier 1, 2025. Single-Binary, SSPL→Apache, Postgres seit Jan 2025.
[^17]: Inngest GitHub — `inngest/inngest`. https://github.com/inngest/inngest
       — Tier 1, 2026. Step-Primitive (`step.run`/`sleep`/`waitForEvent`).
[^18]: Inngest — Pricing Page. https://www.inngest.com/pricing — Tier 1
       (Hersteller-Preis), 2026. Hobby 50k Executions, Pro 75 $/Monat.
[^19]: Gunnar Morling — „Building a Durable Execution Engine With SQLite".
       https://www.morling.dev/blog/building-durable-execution-engine-with-sqlite/
       — Tier 2 (Architektur-Blog mit Code), 2025. SQLite-basierter Ansatz,
       Tradeoffs vs. Server-basierte Systeme.
