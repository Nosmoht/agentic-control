# ADR-0017: Implementierungssprache für v0/v1a

* Status: proposed
* Date: 2026-04-27
* Context: `docs/spec/SPECIFICATION.md §7`, ADR-0002, ADR-0013

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

## Empfehlung (nicht Entscheidung)

**Python (Option 1)** als Default-Empfehlung — aber mit aufrichtigem
Caveat:

- **Wenn** „Operations-Aufwand minimieren" der dominante Treiber ist
  (Litestream-Restore-Drill quartalsweise, Kein-venv-Wunsch,
  Single-Binary-Distribution), **dann ist Go (Option 2) die bessere
  Wahl** — Pydantic AI lohnt den Restore-Schmerz nicht.
- **Wenn** „LLM-/Agent-SDK-Reichweite" der dominante Treiber ist
  (Pydantic AI, Eval-Stack, schnelles Erkunden neuer Frameworks),
  **dann ist Python richtig**.
- TypeScript ist die ehrliche Mitte, scheitert aber am
  Pydantic-AI-Äquivalent.
- Rust ist für dieses Stadium überdimensioniert.

Die Empfehlung Python steht unter dem Vorbehalt, dass der Nutzer „LLM-
SDK-Reichweite" über „Ops-Minimum" priorisiert. Wird die Priorität
umgekehrt, wechselt die Empfehlung auf Go.

## Konsequenzen (für die ausgewählte Option)

**Wenn Python**
- v0-Skelett mit `uv` + `pyproject.toml`; CLI via `typer` oder `click`.
- DBOS via `dbos-py`. Pydantic-Models als Source-of-Truth für
  JSON-Schemas (ADR-0018).
- Restore-Drill (§10.4) muss `uv sync` als Schritt enthalten und
  zeitlich messen.
- Sandbox-Profil enthält `python3` + `uv`-Cache.

**Wenn Go**
- v0-Skelett mit `go.mod`; CLI via `cobra` oder `urfave/cli`.
- DBOS Go-SDK; Schema-Validierung manuell oder via `go-jsonschema`.
- Restore-Drill = Binary-Copy + DB-Restore; einfacher als Python.
- Eigenes Glue-Layer für Pydantic-AI-Funktionalität nötig.

**Wenn TypeScript**
- v0-Skelett mit Bun oder Deno; CLI via `commander` oder `cliffy`.
- DBOS TS-SDK; Schema via `zod` oder `effect/Schema`.
- Restore-Drill = Compiled-Binary, vergleichbar Go.
- Pydantic-AI-Funktionalität via Vercel AI SDK + eigene Glue-Layer.

**Wenn Rust** — siehe Contra; nicht empfohlen.

### Reversibilität

Die Wahl ist nach ~1 KLOC Code praktisch irreversibel. ADR-0018
(Schema-First) reduziert die Bindungstiefe für **Datentypen**, nicht
für Logik. DBOS-Workflow-Definitionen sind sprach-spezifisch.

## Follow-ups

- Sobald die Sprache gewählt ist: dieses ADR auf `accepted` setzen,
  Datum aktualisieren, Spec §7 um „Implementierung in {Sprache}"
  ergänzen.
- F0001-Acceptance-Kriterien um sprachspezifische Build-/Test-Schritte
  ergänzen.
- ADR-0018 (Schema-First) abhängig: Tooling-Auswahl wird klarer.

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
