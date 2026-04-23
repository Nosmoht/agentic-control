---
topic: agent-orchestration-libs
tier: A
date: 2026-04-23
status: draft
---

# Brief 04: Agent-Orchestration-Libraries — Vergleich (2026)

## Forschungsfrage

Welche der vier Mainstream-Orchestrations-Libraries — **LangGraph**,
**OpenAI Agents SDK**, **Claude Agent SDK** (vormals Claude Code SDK),
**Pydantic AI** — passt als "Workflow Coordination"-Layer zu unserer Trennung
aus langlebiger Orchestrierung und delegierter Execution (Claude Code /
Codex CLI)? Oder sitzen sie in einer anderen Ebene, und unser System braucht
stattdessen ein Durable-Execution-Framework (Brief 03) plus einen dünnen
LLM-Call-Wrapper?

## Methodik

Primärquellen: offizielle Docs der vier Libraries, GitHub-Releases,
Anthropic-Engineering-Blog, Temporal/DBOS-Integrations­posts. Sekundärquellen:
unabhängige Vergleiche (Langfuse, Speakeasy), LangChain-Release-Policy. Drei
Suchzyklen, jede nicht-triviale Aussage gegen ≥ 2 Quellen validiert.

## Befunde

### LangGraph

Graph-basiert; Agent-Schritte sind Knoten, State ist typisiert, Kanten sind
explizit. Pregel-Execution-Loop mit BSP-Supersteps [^lg-deepwiki]. Built-in
Checkpointer (InMemory / SQLite / Postgres); jeder Superstep wird automatisch
persistiert, Threads isolieren Runs. PostgresSaver ist der produktive Default
[^lg-deepwiki]. Subgraphs + Supervisor-Pattern für Multi-Agent; HITL ist
First-Class (`interrupt()` pausiert den Graph, State editierbar, Resume via
Thread-ID) [^lg-blog]. Tools über LangChain-Abstraktion; MCP via Adapter,
nicht Core. Kosten-Tracking via LangSmith / Langfuse [^langfuse-cmp].
**v1.0 Oktober 2025, "keine Breaking Changes bis 2.0"-Policy**, Adopter:
Uber, LinkedIn, Klarna, Replit, Elastic [^lg-blog][^lg-gh]; einzelne
Sub-Packages wie `langgraph-prebuilt==1.0.2` brachen dennoch [^lg-issue].
Model-agnostisch, aber LangChain ist Zwangs-Dependency [^speakeasy].

### OpenAI Agents SDK

Python-First, leichtgewichtige Primitives: `Agent`, `Handoff`, `Guardrail`.
Agenten sind Klassen mit Instructions + Tools, Delegation über Handoffs
(Agent-als-Tool) [^oai-sdk]. Keine expliziten Determinismus-Garantien;
`Sessions` liefern Persistenz (SQLAlchemy / SQLite / Redis). April-2026-Update
bringt "Long-Horizon Harness" mit persistentem State, Sandboxed Execution,
explizite Subagents und "Code Mode" [^oai-evolution]. Native Function-Tools
mit Auto-Schema, MCP-Server First-Class [^oai-mcp]. HITL ist dokumentiert,
aber ohne prominente Primitives. Usage-API, OTel-Tracing. Production-ready
seit März 2025 (Evolution aus Swarm), aber Stabilitäts-Policy unklar.
Provider-agnostisch via Chat-Completions (100+ LLMs), Voice / Responses-API
sind OpenAI-exklusiv [^oai-morph].

### Anthropic Agent SDK (Claude Agent SDK)

**Kein klassisches Orchestrator-Framework**, sondern ein **Claude-Code-Harness
als Library**. Eine `query()`-Funktion startet den Claude-Code-Loop (gather
context → act → verify → repeat) in Python / TypeScript [^cc-sdk][^anth-blog].
State: Session-IDs; `resume=session_id` lädt Kontext; automatische Kompaktion
bei Context-Limit — keine pluggbare Persistenz, Session-Storage ist Claude-
Code-intern. Subagents über `AgentDefinition` mit eigenem Kontext-Fenster
(Parent-Tool-Use-ID zur Zuordnung). 10+ Built-in-Tools (Read, Write, Edit,
Bash, Glob, Grep, WebSearch, WebFetch, Monitor, Agent, AskUserQuestion);
MCP voll unterstützt. HITL über Permission-Hooks (`PreToolUse`, `PostToolUse`,
`SessionStart`, `UserPromptSubmit`, `Stop`) und `AskUserQuestion`-Tool.
OpenTelemetry mit W3C-Trace-Context zur CLI [^anth-rel]. Aktive Entwicklung,
v0.2.111+ für Opus 4.7, Rename "Claude Code SDK → Claude Agent SDK" Ende
2025 [^cc-sdk]. Anthropic-exklusiv, aber über Bedrock / Vertex / Foundry
deploybar.

### Pydantic AI

Function-Dekoratoren auf Agent-Instanzen (`@agent.tool`,
`@agent.instructions`), type-safe via Pydantic-Validation von In-/Output
[^pyd-docs][^speakeasy]. Stateless by default; jeder `agent.run()` ist
isoliert sofern keine `message_history` übergeben wird — strukturierte
Outputs sind per Validierung deterministisch typisiert. **Kein built-in
Checkpoint-Store im Core**; stattdessen **co-gepflegte Integrationen** mit
**Temporal, DBOS, Prefect, Restate** [^pyd-docs][^pyd-dbos][^temp-pyd].
Multi-Agent-Patterns + Agent2Agent (A2A); `pydantic-deep` für Produktion.
MCP First-Class. HITL als `Human-in-the-Loop Tool Approval` (bedingte
Freigabe je nach Args / History / User-Prefs). Tight-Integration mit Pydantic
Logfire (OTel + Cost-Tracing). v1.85.1 am 2026-04-22, dokumentierte Version
Policy [^pypi-pyd]. Framework-agnostisch; Logfire optional.

### Vergleichstabelle

| Library            | Modell              | State                                  | Multi-Agent              | HITL                              | Kosten-Tracking     | Lock-in                         |
|--------------------|---------------------|----------------------------------------|--------------------------|-----------------------------------|---------------------|---------------------------------|
| LangGraph          | Graph + Nodes       | Built-in Checkpointer (Postgres/SQLite)| Subgraphs / Supervisor   | First-Class (`interrupt()`)       | LangSmith/Langfuse  | Model-agnostisch, LangChain-dep |
| OpenAI Agents SDK  | Python-Primitives   | `Sessions` (SQLAlchemy / Redis)        | Handoffs + Subagents     | Dokumentiert, dünn                | OAI-Tracing / Usage | OAI-Features exklusiv, sonst offen |
| Claude Agent SDK   | Single-Loop `query()`| Session-ID (intern)                   | Subagents (Kontext-Iso)  | Permission-Hooks, AskUserQuestion | OTel                | Claude-Modelle (Bedrock/Vertex/Azure) |
| Pydantic AI        | Typed Decorators    | Extern (Temporal / DBOS / Prefect / Restate) | A2A + Deep Agents  | Tool-Approval                     | Logfire (OTel)      | Framework-agnostisch            |

### Layer-Einordnung

- **LangGraph** ist der einzige echte **Orchestrator** im klassischen Sinn:
  eigener Checkpointer, eigenes Execution-Modell, eigene Thread-Semantik —
  ein leichtes Durable-Execution-Framework für Agenten [^lg-deepwiki].
- **Pydantic AI** ist ein **typsicherer LLM-Call-Wrapper mit Agent-Semantik**,
  der Durability bewusst **an Temporal / DBOS / Prefect / Restate delegiert**
  [^pyd-docs][^temp-pyd]. Das ist exakt die Komposition "durable execution +
  thin LLM layer".
- **OpenAI Agents SDK** ist ein **provider-nahes Agent-Loop-SDK**; Sessions
  sind leichtgewichtige Persistenz, echte Orchestrierung fehlt.
- **Claude Agent SDK** ist eine **Library-Form von Claude Code**, kein
  General-Orchestrator — Anthropic grenzt es explizit gegen den Client SDK ab:
  der Agent-Loop ist der USP [^cc-sdk]. In unserer Architektur liegt es auf
  der **Execution-Seite**, nicht auf der Coordination-Seite.

Konsens 2025–2026: für **durable, orchestration-heavy** Workloads gilt
entweder LangGraph (mit Postgres) oder **Pydantic AI + Temporal / DBOS**;
für **ephemere in-process** Agents reichen OpenAI Agents SDK oder Pydantic AI
stateless [^temp-pyd][^zylos][^speakeasy].

## Quellenbewertung

- Tier 1 (7): LangGraph GitHub & DeepWiki, Pydantic AI Docs, DBOS-Integration,
  Temporal-Blog, OpenAI Agents SDK Docs, Claude Agent SDK Docs,
  Anthropic-Engineering-Blog.
- Tier 2 (3): Langfuse-Vergleich, Speakeasy-Vergleich, LangChain-1.0-Blog.
- Tier 3 (1): morphllm-Übersicht — nur als Plausibilitäts-Check.
- Cross-Validation: erfüllt (jede nicht-triviale Aussage ≥ 1 Tier-1/2-Quelle).

## Implikationen für unser System

1. **Keine dieser Libraries ersetzt ein Durable-Execution-Framework** (vgl.
   Brief 03), wenn wir "langlebige Workflow-Koordination mit Crash-Recovery"
   ernst meinen. LangGraph kommt am nächsten, bindet aber an LangChain und
   erzwingt Graph-Denken, das unser Solo-Tool-Szenario nicht braucht.
2. **Empfehlung V1**:
   - **Workflow Coordination**: Durable-Execution-Engine aus Brief 03
     (DBOS / Temporal / Restate) — nicht LangGraph.
   - **LLM-Call-Abstraktion**: **Pydantic AI als dünner Wrapper** für
     strukturierte Tool-Calls, Validation, HITL-Tool-Approval; integriert
     nativ in DBOS / Temporal. Passt 1:1 auf unsere Zwei-Layer-Trennung.
   - **Execution & Verification**: **Claude Agent SDK und Codex CLI als
     Subprozesse / Sandboxen** — keine Orchestrierer, sondern beauftragte
     Agenten mit eigenem Loop. Aufruf als Activity / Step im Durable-Workflow.
3. **OpenAI Agents SDK und LangGraph** bleiben Option B, falls wir doch einen
   Graph-Orchestrator oder OpenAI-native Features benötigen. Für V1: nein.
4. Die gesuchte Abstraktionsebene ist also: `Durable-Workflow-Engine` (State,
   Retries, Replay) + `Pydantic-AI-Agent` (typisierte LLM-Calls, HITL) +
   `CLI-Agent-Invocation` (Claude Code / Codex als externe, zeitlich
   begrenzte Worker). Die vier Libraries gehören **nicht** in dieselbe Schicht.

## Offene Unsicherheiten

- **Operative Reife der Pydantic-AI-Temporal-Integration in Solo-Setups**:
  Docs beschreiben Enterprise-Szenarien; DBOS (Postgres-only) könnte
  betriebs­einfacher sein — gehört in Brief 03 / 12.
- **Claude Agent SDK API-Stabilität**: < 12 Monate alt, aktive Umbenennung
  Ende 2025; Version-Policy nicht öffentlich wie bei LangGraph.
- **OpenAI Agents SDK April-2026-Update** (Sandbox, Long-Horizon Harness,
  Subagents) zu frisch für Produktions­belege.
- **Budget-Enforcement** (Hard-Cap statt nur Logging) ist bei keiner Library
  First-Class — gehört in Brief 13.

## Quellen

[^lg-gh]: langchain-ai/langgraph — GitHub. <https://github.com/langchain-ai/langgraph>
[^lg-deepwiki]: Checkpointing Architecture — DeepWiki. <https://deepwiki.com/langchain-ai/langgraph/4.1-checkpointing-architecture>
[^lg-blog]: "LangChain and LangGraph 1.0 Milestones". <https://blog.langchain.com/langchain-langgraph-1dot0/>
[^lg-issue]: Issue #6363 — Breaking Change `langgraph-prebuilt==1.0.2`. <https://github.com/langchain-ai/langgraph/issues/6363>
[^oai-sdk]: OpenAI Agents SDK — Official Docs. <https://openai.github.io/openai-agents-python/>
[^oai-evolution]: "The next evolution of the Agents SDK" — openai.com, April 2026. <https://openai.com/index/the-next-evolution-of-the-agents-sdk/>
[^oai-mcp]: MCP — OpenAI Agents SDK JS. <https://openai.github.io/openai-agents-js/guides/mcp/>
[^oai-morph]: "AI Agent Frameworks 2026" — morphllm.com. <https://www.morphllm.com/ai-agent-framework>
[^cc-sdk]: Claude Agent SDK Overview. <https://code.claude.com/docs/en/agent-sdk/overview>
[^anth-blog]: "Building agents with the Claude Agent SDK". <https://claude.com/blog/building-agents-with-the-claude-agent-sdk>
[^anth-rel]: Anthropic Release Notes April 2026. <https://releasebot.io/updates/anthropic>
[^pyd-docs]: Pydantic AI — Official Docs. <https://ai.pydantic.dev/>
[^pyd-dbos]: "Pydantic AI + DBOS Durable Execution". <https://pydantic.dev/articles/pydantic-ai-dbos>
[^temp-pyd]: "Durable AI agents with Pydantic AI and Temporal". <https://temporal.io/blog/build-durable-ai-agents-pydantic-ai-and-temporal>
[^pypi-pyd]: pydantic-ai v1.85.1 on PyPI. <https://pypi.org/project/pydantic-ai/>
[^langfuse-cmp]: "Comparing Open-Source AI Agent Frameworks" — Langfuse. <https://langfuse.com/blog/2025-03-19-ai-agent-comparison>
[^speakeasy]: "Choosing an agent framework" — Speakeasy. <https://www.speakeasy.com/blog/ai-agent-framework-comparison>
[^zylos]: "Durable Execution Patterns for AI Agents" — Zylos, 2026-02-17. <https://zylos.ai/research/2026-02-17-durable-execution-ai-agents>
