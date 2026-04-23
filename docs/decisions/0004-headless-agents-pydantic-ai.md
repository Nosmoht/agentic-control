# ADR-0004: Headless-Agent-Aufrufe + Pydantic AI als LLM-Wrapper

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §5.4, §8.5`

## Kontext und Problemstellung

Das System soll Claude Code und Codex CLI als Ausführungskontext nutzen —
**nicht** als Steuerungsinstanz. Gleichzeitig müssen interne LLM-Aufrufe
(Klassifikation, Zusammenfassung, Plan-Extraktion) ohne vollen Agent-Loop
möglich sein. Die Auswahl der LLM-Layer und der Interaktionsart ist
architektur­bestimmend.

## Entscheidungstreiber

- Control/Execution-Trennung als Fundament.
- Claude-Code-Sessions sind aus Orchestrator-Sicht unzuverlässig persistent
  (Resume dokumentiert kaputt — Issue #43696).
- Codex CLI `exec` liefert strukturiertes JSONL — ein erstklassiges
  Orchestrator-Interface.
- Tool-Use-Validation und Token-Tracking sollen im Orchestrator-Code liegen,
  nicht in einem Framework mit eigenem Loop.
- Kein LangGraph / OpenAI Agents SDK, solange Workflow-Coordination in
  DBOS liegt (ADR-0002) — sonst zwei Orchestrator-Schichten.

## Erwogene Optionen

### Für Agent-Aufruf

1. **Claude Code interaktiv** (mit `--continue`/`--resume`).
2. **Claude Code headless** (`claude -p --output-format json --bare`).
3. **Codex CLI interaktiv**.
4. **Codex CLI exec** (`codex exec --json --output-schema --ephemeral`).

### Für interne LLM-Aufrufe

A. **LangGraph** als Orchestrator-Framework.
B. **OpenAI Agents SDK** / **Anthropic Agent SDK**.
C. **Pydantic AI** als dünner Typ-sicherer LLM-Wrapper.
D. **Direkter Provider-SDK-Aufruf** (anthropic-sdk, openai-sdk).

## Entscheidung

Gewählt: **Option 2 + Option 4 für Agent-Aufrufe**, **Option C (Pydantic AI)
für interne LLM-Aufrufe**.

### Konsequenzen

**Positiv**
- Headless-Calls liefern strukturierte Resultate zu DBOS-Workflows — saubere
  Integrationspunkte.
- Stateless-Modell auf Agent-Seite vereinfacht Wiederanlauf.
- Pydantic AI bringt Typ-Validation, Tool-Call-Struktur, HITL-Primitive,
  ohne einen zweiten Orchestrator zu erzwingen.
- Kein Lock-in an LangGraph oder Agent-SDKs.

**Negativ**
- Kein `--continue` bedeutet: bei Mehrschritt-Aufgaben muss der Orchestrator
  jeden Teilschritt als neuen Headless-Aufruf mit Kontext-Prompt starten.
- Pydantic AI hat keine native Cost-Caps — das Budget-Gate (ADR-0008) muss
  als Middleware davor sitzen.

**Neutral**
- LangGraph als Durable-Layer wäre technisch möglich gewesen, hätte aber
  Redundanz zu DBOS erzeugt.

## Aufruf-Disziplin (Minimum)

- **Claude Code:** `claude -p --output-format json --bare --allowedTools=<explizit>`.
- **Codex CLI:** `codex exec --json --output-schema <file> --ephemeral
  --approval=never --sandbox=workspace-write`. Protected Paths bleiben ro.
- Immer in frischem Git-Worktree (ADR-0006).

## Referenzen

- `docs/research/01-claude-code.md` — Headless-Modus, Session-Unsicherheit
- `docs/research/02-codex-cli.md` — exec-Stream, Permission-Modell
- `docs/research/04-agent-orchestration-libs.md` — Pydantic AI als Thin-Layer
- `docs/research/05-agent-patterns.md` — Control/Execution-Mainstream
