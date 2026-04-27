# ADR-0017: Implementierungssprache für v0/v1a

* Status: accepted
* Date: 2026-04-27
* Context: `docs/spec/SPECIFICATION.md §7`, ADR-0002, ADR-0003, ADR-0004,
  ADR-0013

## Kontext und Problemstellung

Das Repo ist V0.3.2-draft Documentation-Only. Bisher war keine
Implementierungssprache normativ festgelegt. F0002 erwähnt beiläufig
„Python-Package", die Research-Briefs nehmen Python implizit an
(Pydantic AI, OpenAI Agents SDK, DBOS-Doku zentriert auf Python) — aber
es gibt **kein ADR**, das die Sprachwahl ausspricht oder begründet.

Vor dem v0-Implementierungsstart muss diese Wahl explizit werden, weil
sie:
- die DBOS-Bindings festlegt (Python, TS, Java oder Go),
- den Sandbox-Profil-Stack beeinflusst (Interpreter vs. Static Binary),
- das Dependency-Modell prägt (`venv`/`uv` vs. `go.mod` vs. `package.json`/`Cargo.toml`),
- die LLM-/Agent-SDK-Reichweite definiert,
- praktisch irreversibel ist, sobald ≥ 1 KLOC Code existiert.

## Entscheidungstreiber

In Reihenfolge der Spec-Kernziele (Leroy-2009-Attention-Residue +
n=1-Proportionalität):

1. **Operations-Aufwand minimieren** — ADR-0013 nennt das als Kernziel.
   Restore-Drill, Deploy, Update sollen einfach bleiben.
2. **LLM-/Agent-SDK-Reichweite** — Pydantic AI (ADR-0004), OpenAI Agents
   SDK, optional LangChain/LlamaIndex; alle Python-zentriert.
3. **DBOS-Binding-Reife** — ADR-0002 setzt DBOS voraus.
4. **Sandbox-Tauglichkeit** — ADR-0006 verlangt 8 Schichten;
   Static-Binary erleichtert seccomp/landlock-Profile.
5. **Daily-Driver des Nutzers** — n=1, Wartung erfolgt durch denselben.
6. **Cold-Start-/Subprozess-Latenz** — `agentctl`-Aufrufe sollen sich
   wie ein normales Unix-Tool anfühlen, nicht wie ein JVM-Boot.

## Erwogene Optionen

### Option 1 — Python (mit `uv` + Pydantic AI)

**Pro**
- Pydantic AI, OpenAI Agents SDK, LlamaIndex, LangChain alle nativ.
- DBOS-Doku ist Python-zentriert; Tutorials zeigen Python-First.
- Schnellstes Prototyping; Pydantic-Models = Single-Source für
  JSON-Schema-Generation (passt zu ADR-0018).
- `uv` löst venv-/Lock-Disziplin sauberer als historisch üblich.
- Ökosystem für Eval/Telemetry (OpenLLMetry, Phoenix) Python-First.

**Contra**
- Kein Single-Static-Binary. Restore = Python-Toolchain + venv neu
  aufbauen. Litestream-Restore-Drill (§10.4) wird komplexer.
- Cold-Start ~150–300 ms; Subprozess-Aufrufe spürbar.
- Dependency-Surface groß; Security-Updates häufig nötig.
- Sandbox-Profile (seccomp, landlock) müssen Python-Interpreter
  einschließen — größere Trust-Boundary.
- Typing ist Opt-in; `pydantic` mildert das, aber Drittlibs typen oft dünn.

### Option 2 — Go

**Pro**
- Single Static Binary. Restore = Binary kopieren. Trivial. ADR-0013
  Operations-Minimum bestens unterstützt.
- Cold-Start < 20 ms.
- Static-Type-System verkleinert Fehlerklassen (besonders bei DBOS-
  Workflow-Verträgen).
- Sandbox-Profil minimal (kein Interpreter im Trust-Set).
- DBOS Go-SDK existiert (via DBOS Transact); aktiv gepflegt.
- Das Codex-CLI- und Claude-Code-Subprozess-Modell ist sprach-neutral —
  Go ruft sie genauso wie Python.
- Concurrency-Primitive (Goroutines/Channels) passen zu Adapter-Fan-out.

**Contra**
- LLM-/Agent-SDK-Ökosystem in Go ist deutlich dünner. Anthropic +
  OpenAI Go-SDKs existieren, sind aber „SDK", nicht „Agent-Framework".
- Pydantic AI hat kein Go-Äquivalent; eigene Validation/Tool-Calling-Glue.
- Eval-Stack (Phoenix, OpenLLMetry) Python-First; OTel-Go ist die
  einzige Brücke.
- Mehr Boilerplate als Python für gleiche Logik (15–30 % LOC mehr).

### Option 3 — TypeScript (Bun oder Deno)

**Pro**
- DBOS first-class TS-Binding.
- Anthropic + OpenAI SDKs sehr ausgereift in TS.
- Bun/Deno bringen Single-Binary-Compilation (`bun build --compile`,
  `deno compile`) — Go-Niveau für Distribution.
- Strenge Typen mit Zod/Effect für Schema-Validation.
- Asynchron als Default — passt zu Subprozess-Ketten.

**Contra**
- Pydantic AI hat kein direktes Äquivalent (Vercel AI SDK ist näher
  an Edge-Use-Cases als an Daemon-Workloads).
- Sandbox-Profil mittel: V8-Runtime im Trust-Set, aber Bun/Deno haben
  Permission-System on-by-default.
- `npm`-/`bun`-Lock-Disziplin nötig, ähnlich Python.
- Doppeltes Tooling, falls später doch Python-Skripte für Eval dazukommen.

### Option 4 — Rust

**Pro**
- Maximaler Static-Binary-/Sicherheits-Diskurs.
- Kleinste Trust-Boundary für Sandbox.
- Performance konkurrenzlos (irrelevant für n=1).

**Contra**
- DBOS hat **kein** Rust-Binding. Ports-Aufwand wäre erheblich.
- LLM-/Agent-SDK-Stack in Rust ist Hobbyist (rust-genai, async-openai
  ohne Agent-Layer).
- Schreibaufwand 2–3× Python für gleiche Funktionalität.
- Compile-Zeiten merkbar; Inkrementelle Entwicklung langsamer.
- Für n=1 Doku-First-System mit hoher Iteration nicht proportional.

## Entscheidung

Gewählt: **Option 1 — Python (mit `uv` + Pydantic AI)**.

Die ursprüngliche Fassung dieses ADR (V0.3.3-draft, `proposed`)
empfahl Python „unter Vorbehalt der Treiber-Priorisierung" und
benannte Go als gleichwertige Alternative bei Ops-Minimum-Dominanz.
Die empirische Verifikation am 2026-04-27 hat diese Symmetrie
aufgelöst: **Go bricht strukturell mit drei accepted ADRs**, während
Python nur Trade-offs einkauft, die mitigierbar sind.

### Strukturelle Befunde (verifiziert 2026-04-27)

1. **DBOS Go-SDK ist Postgres-only.** `dbos-inc/dbos-transact-golang`
   v0.13.0 (2026-04-22) dokumentiert ausschließlich Postgres als
   Backend; SQLite ist im Go-Pfad nicht unterstützt. Das **kollidiert
   mit ADR-0003** (SQLite + Litestream als V1-Substrat). Eine
   Go-Wahl würde ADR-0003 brechen oder v1a sofort auf Postgres
   zwingen — letzteres widerspricht ADR-0013 (Operations-Minimum).
2. **Kein Pydantic-AI-Äquivalent in Go.** Nähere Kandidaten
   (`instructor-go`, `go-llms`, `langchaingo`, `eino`, `genkit-go`)
   liefern Teilfunktionen, aber keine Kombination aus Schema-Validation
   + Tool-Orchestration + Multi-Provider + HITL-Primitiven in einem
   Paket. **Verletzt ADR-0004** im Kern.
3. **Eval-/Telemetrie-Stack ist Python-first.** Arize Phoenix und
   Pydantic Logfire haben **kein** Go-SDK — Go bekommt nur
   OTLP-Raw-Export. OpenLLMetry-Go ist explizit „early-alpha,
   manual logging". Reduziert die Beobachtbarkeit für n=1.
4. **`uv sync` ist im Restore-Budget.** Cold-Restore dauert 5–10 s,
   ~180 Pakete < 60 s; Lockfile-Drift wirft `uv sync` mit Fehler ab,
   statt zu mutieren — passt zur quartalsweisen Restore-Drill-
   Disziplin (§10.4).

### Zusammenfassung

- Go bricht ADR-0003 (SQLite), ADR-0004 (Pydantic AI) und reduziert
  die Beobachtbarkeit. Drei ADR-Brüche, kein einziges Mitigations-
  Pfad, der ohne Stack-Re-Design auskäme.
- TypeScript bleibt strukturell zulässig (DBOS-TS first-class), hat
  aber kein Pydantic-AI-Äquivalent (Vercel AI SDK ≠ Pydantic AI für
  Daemon-Workloads); doppeltes Tooling, falls Eval-Stack
  hinzukommt.
- Rust bleibt überdimensioniert (kein DBOS-Rust-Binding).

Damit ist die Wahl strukturell determiniert — nicht eine Treiber-
Abwägung, sondern eine ADR-Konsistenz-Frage.

### Anerkanntes Risiko und Mitigation

Die schärfste Schwachstelle der Python-Wahl ist **transitive-
Dependency-Rot über 12–24 Monate** für n=1 ohne CI-Babysitter
(Pydantic-Core-/cryptography-ABI-Drift, Wheel-Inkompatibilitäten).
Mitigation in der Spec verankert:

- `uv.lock` als hard-frozen Snapshot pro Release (kein
  „lockfile drift" beim Restore).
- Quartalsweiser Restore-Drill (§10.4) **enthält Test-Boot** auf
  frischem System, nicht nur DB-Restore. Schlägt der Boot fehl, ist
  das ein erkannter Befund, nicht stiller Zerfall.
- Python ≥ 3.13 als Mindestversion; `uv python pin 3.13.x`.
- Mindestens jährliches Lockfile-Refresh als geplante
  Wartungsaufgabe (kein Drift, sondern bewusste Bewegung).
- Keine Pre-Release-Pakete in `requirements`; nur stabile Tags.

## Konsequenzen

**Positiv**
- ADR-0002 (DBOS), ADR-0003 (SQLite + Litestream), ADR-0004 (Pydantic
  AI), ADR-0013 (Operations-Minimum lokal-only) bleiben konsistent.
- Pydantic-Models werden Single-Source für Daten-Verträge — siehe
  ADR-0018 für die abgeleitete Schema-First-Strategie.
- Eval-/Telemetrie-Stack (Phoenix, Logfire, OpenLLMetry) ist nativ.
- `uv` löst die historische venv-/Lock-Disziplin-Schwäche.

**Negativ**
- Kein Single-Static-Binary; Restore = Python-Toolchain + `uv sync`.
  Akzeptabel im quartalsweisen Drill-Budget, aber nicht in derselben
  Klasse wie Go.
- Cold-Start ~150–300 ms für `agentctl`-Aufrufe (für Daemon-
  Workloads vernachlässigbar, für Subkommandos spürbar).
- Transitive-Dependency-Surface groß; Mitigation siehe oben.
- Sandbox-Profil enthält `python3` + `uv`-Cache als Trust-Set —
  größer als ein statisches Go-Binary.

**Neutral**
- v0-Skelett: `pyproject.toml` + `uv`; CLI via `typer` (oder `click`);
  DBOS via `dbos-py`.
- Sandbox-Profile (ADR-0006 Schicht 5) müssen Python-Interpreter
  whitelisten — bekanntes Muster, kein neues Risiko.

### Reversibilität

Die Wahl ist nach ~1 KLOC Code praktisch irreversibel. ADR-0018
reduziert die Bindungstiefe für **Datentypen** (Pydantic ↔ JSON
Schema), nicht für Logik. DBOS-Workflow-Definitionen, Adapter-
Steuerung und CLI-Implementierung bleiben sprach-gebunden.

## Follow-ups

- Spec §7 (Verteilungssicht) um „Implementierung in Python ≥ 3.13
  mit `uv`" ergänzen — eigenes V0.3.4-Patch oder mit dem
  v0-Implementierungsstart-Patch.
- F0001-Acceptance-Kriterien um Build-/Test-Schritte (`uv sync`,
  `uv run pytest`) ergänzen, sobald die Implementierung beginnt.
- §10.4 (Restore-Drill) um Test-Boot-Schritt erweitern (eigene
  Akzeptanzkriterium-Zeile, nicht nur Litestream-Restore).
- ADR-0018 verfolgt Pydantic-Models als kanonische Form mit
  JSON-Schema-Export — Tooling ist damit fixiert
  (`datamodel-code-generator` entfällt; `model_json_schema()` ist
  der Pfad).

## Referenzen

- ADR-0002 — DBOS als Durable-Execution-Engine
- ADR-0004 — Headless Agents + Pydantic AI
- ADR-0006 — 8-Schichten-Sandbox
- ADR-0013 — V1 Deployment Mode (Operations-Minimum)
- ADR-0018 — Schema-First mit JSON Schema (verwandt)
- `docs/research/03-durable-execution.md` — DBOS-Bindings
- `docs/research/04-agent-orchestration-libs.md` — Pydantic AI, OpenAI
  Agents SDK
- DBOS Go-SDK: <https://github.com/dbos-inc/dbos-transact-go>
- Bun-Compile: <https://bun.sh/docs/bundler/executables>
