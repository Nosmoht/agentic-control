---
topic: agent-patterns
tier: A
date: 2026-04-23
status: draft
---

# Brief 05: Aktuelle Agent-Architektur-Muster (2025–2026)

## Forschungsfrage

Welche LLM-Agent-Architektur-Muster haben sich bis Anfang 2026 als Best Practice
stabilisiert? Konkret: Empfehlungen von Anthropic und OpenAI, Konsens akademischer
Surveys, Lehren aus Industrie-Postmortems, sowie Entscheidungskriterien für
Single-Loop vs. Multi-Agent, durable vs. ephemeral State, wiederkehrende Failure-Modes
und Produktionsmuster für lange Laufzeiten. Ziel: die Control-vs-Execution-Trennung
unserer V1-Architektur gegen aktuelle Praxis prüfen.

## Methodik

- Tier-1-Primärquellen (Anthropic Engineering Blog, OpenAI Cookbook/Guide, arXiv-Surveys)
  direkt via `r.jina.ai` gefetcht.
- Tier-2-Retrospektiven (Cognition/Devin, LangChain, Replit+Temporal, GitHub Copilot) als
  Cross-Check zu den Primärempfehlungen.
- Jede nicht-triviale Behauptung mit ≥ 2 unabhängigen Quellen belegt, mindestens eine Tier 1/2.
- Scope-Limit: Fokus auf Architektur/Orchestration, nicht auf Prompt- oder Tool-Design im Detail
  (separat in Briefs 03, 04, 14).

## Befunde

### Anthropic "Building Effective Agents" — Stand Anfang 2026

Kernaussage unverändert seit 19.12.2024: starte immer beim einfachsten Muster, eskaliere nur
wenn Messmetriken das rechtfertigen. Anthropic unterscheidet klar zwischen **Workflows**
(LLMs über vordefinierte Codepfade orchestriert) und **Agents** (LLMs steuern ihren Prozess
selbst)[^1].

Die sechs empfohlenen Bausteine[^1]:

- **Prompt Chaining** — sequentielle Zerlegung mit programmatischen Checks dazwischen; wenn
  die Zerlegung statisch klar ist.
- **Routing** — Klassifikation und Weiterleitung; bei distinct Kategorien mit separatem
  Handling.
- **Parallelization** — Sectioning (unabhängige Subtasks) oder Voting (mehrere Versuche);
  für Speed oder höhere Konfidenz.
- **Orchestrator-Workers** — zentraler LLM zerlegt Tasks dynamisch, Workers führen aus,
  Synthese am Ende; wenn Subtasks nicht vorhersehbar (z. B. Multi-File-Coding-Changes).
- **Evaluator-Optimizer** — Generator-LLM + Kritiker-LLM im Loop; wenn klare Eval-Kriterien
  existieren und Iteration nachweisbar hilft.
- **Autonomous Agents** — Tool-Use-Loop mit Ground-Truth aus Environment; für offene
  Probleme mit unbekannter Schrittzahl, aber nur wenn Vertrauen ins Environment besteht.

Drei übergeordnete Prinzipien: **Simplicity**, **Transparency** (Planning-Schritte sichtbar
machen), **sorgfältiges Agent-Computer-Interface** (ACI / Tool-Design)[^1].

Ergänzend 2025: Anthropic veröffentlichte Folgeposts zu **Context Engineering**[^2] und
**Harnesses für Long-Running Agents**[^3], die die ursprünglichen Patterns in Produktion
konkretisieren (siehe unten).

### OpenAI Agent-Guidance

OpenAIs "A Practical Guide to Building AI Agents" (2025) und das zugehörige Cookbook
empfehlen fast deckungsgleich zu Anthropic[^4][^5]:

- **Single-Agent-Loop**: ein Model + Tools in einem Loop; Default. "Keep complexity
  manageable by incrementally adding tools."[^4]
- **Manager Pattern** (≈ Anthropic Orchestrator-Workers): zentraler Manager-LLM delegiert
  per Tool-Calls an spezialisierte Sub-Agents und synthetisiert.
- **Decentralized / Handoff Pattern**: Agents auf gleicher Ebene reichen Kontrolle via
  Handoffs weiter; gut für Triage-artige Flows, schlecht wenn zentrale Synthese nötig.

Konvergenz: Beide Hersteller nennen (a) Single-Loop als Default, (b) Orchestrator/Manager
als bevorzugtes Muster wenn Multi-Agent nötig wird, (c) dezentrale/Handoff-Pattern als
Spezialfall. Divergenz ist marginal: OpenAI formuliert die Patterns stärker als
SDK-Primitive (Handoff = explizite API), Anthropic stärker als Designmuster[^1][^4].

### Akademische Surveys 2025–2026

- **"LLM-based Agentic Reasoning Frameworks" (arXiv 2508.17692, Aug 2025)** klassifiziert
  Multi-Agent-Organisation in **centralized / decentralized / hierarchical** und stellt
  fest, dass zentralisierte und hierarchische Muster produktionsreif sind (AutoGen,
  MetaGPT, ChatDev), dezentrale bleiben forschungsorientiert[^6].
- **"Agentic AI: Architectures, Taxonomies, Evaluation" (arXiv 2601.12560, Jan 2026)**
  berichtet einen Industrie-Shift **weg von offenen Multi-Agent-Chat-Loops hin zu expliziten
  Workflow-Graphen** — Zustandsmaschinen mit Knoten = Tool-Call/LLM-Call, Kanten =
  erlaubte Transitionen; LangGraph als Referenzumsetzung[^7].
- **"Orchestration of Multi-Agent Systems" (arXiv 2601.13671, Jan 2026)** beschreibt MCP
  (Tool-Access-Standard) und A2A (Peer-Coordination) als sich stabilisierende
  Interoperabilitäts-Protokolle[^8].
- Gemeinsamer Befund: Der Trend geht zu **explizitem Controller-Layer außerhalb des LLM**;
  das Model macht lokales Reasoning + Tool-Parameter, die Control-Flow-Semantik lebt im
  Code[^6][^7].

### Industrie-Postmortems

- **Cognition (Devin-Team), "Don't Build Multi-Agents" (12.06.2025)**[^9]: in Produktion
  sind parallele Sub-Agents fragil, weil Sub-Agents Context voneinander fehlt → konfligierende
  implizite Entscheidungen. Empfehlung: **single-threaded linear agent** mit aggressivem
  Context-Engineering; wenn Context gesprengt, dediziertes Compression-LLM einschieben, aber
  Entscheidungshoheit zentral halten.
- **Anthropic, "Multi-Agent Research System" (Juni 2025)**[^10]: Multi-Agent lohnt sich
  nur bei **parallel-lastiger Breitensuche**, wo Kontext einzelne Fenster sprengt und
  Task-Value die **~15× höheren Token-Kosten** gegenüber Chat rechtfertigt; 90.2 % besser
  als Single-Agent-Opus auf internem Research-Benchmark. Ungeeignet: Coding (zu viele
  Interdependenzen, Shared-Context nötig).
- **Replit Agent + Temporal (2025)**[^11]: jeder Agent = eine Temporal-Workflow mit
  stabiler ID; Activities kapseln non-deterministische Logik; Workflow-Updates erlauben
  Human-in-the-Loop-Pause; automatische Git-Commits als Checkpoint-Backbone. Agent 3 läuft
  bis 200 min autonom. Aufbau auf LangGraph.
- **GitHub Copilot Coding Agent / Agent HQ (ab Sep 2025)**[^12]: Sub-Agent-Architektur mit
  isolierten GitHub-Actions-Sandboxen pro Session, Draft-PR als Ausgangs-Artefakt,
  Context-Sharding per Sub-Task mit zusammengefassten Summaries. Reliability via
  Branch-Protection + Required-Checks als Gate.
- **LangChain, "How and when to build multi-agent" (2025)**[^13]: Single-Agent skaliert
  bei wachsender Tool-/Context-Zahl nachweislich schlechter; Multi-Agent rechtfertigt sich
  vor allem durch **Modularität / Team-Boundaries**, nicht durch reine Task-Performance.

### Entscheidungsraster

**Single-Loop vs. Multi-Agent**[^1][^4][^9][^10][^13]:

- Default: Single-Agent-Loop mit wachsender Tool-Palette.
- Wechsel zu Orchestrator/Manager wenn: (a) Tool-Set > ~20 oder Context > Kapazität,
  (b) parallele unabhängige Subtasks (Breitensuche, Guardrail-Checks), (c) klare
  Team-/Domain-Boundaries motivieren getrennte Agents.
- Nicht Multi-Agent wenn: dichte Interdependenzen, Shared-Context nötig, Coding über
  viele verzahnte Dateien, Realtime-Koordination — hier verliert Multi-Agent laut
  Cognition und Anthropic.

**Durable vs. Ephemeral State**[^3][^10][^11]:

- Ephemeral (nur In-Context) reicht für Tasks kürzer als ein Context-Window und ohne
  Recovery-Anforderung.
- Durable Pflicht sobald: Session-Grenzen überschritten werden, Human-in-the-Loop-Pausen
  möglich sind, Fehler mid-task erwartbar sind, oder Auditability gefordert ist.
- Konkrete Primitive aus Produktion: Git als Checkpoint/Revert (Anthropic Harnesses,
  Replit), Feature-Checkliste als JSON (Anthropic), Temporal-Workflow-IDs (Replit),
  persistente Pläne + Filesystem-Artefakte (Anthropic Research).

**Wiederkehrende Failure-Modes**[^2][^9][^10][^11]:

- **Context Rot**: Recall fällt mit Token-Zahl, lange bevor das Hard-Limit erreicht ist[^2].
- **Tool Bloat / Tool-Ambiguität**: zu viele oder überlappende Tools erzeugen falsche Wahl[^2].
- **System-Prompt-Brittleness**: zu spezifische Prompts = spröde, zu vage = keine Signale[^2].
- **Kontextverlust zwischen Sessions**: halb-implementierte Features, verlorene
  Safety-Rails nach Kompaktierung[^2][^3].
- **Konflikt paralleler Sub-Agents**: implizite Entscheidungen divergieren (Cognition's
  Flappy-Bird-Beispiel)[^9].
- **State-Drift in Long-Running Agents**: kleine Fehler akkumulieren über viele Tool-Calls
  ohne Checkpoint[^10].
- **Fehlende End-to-End-Verifikation**: Agents melden "fertig" ohne Testbelege[^3].

**Long-Running Arbeit (Stunden–Tage) in Produktion**[^3][^10][^11]:

- Session-Teilung in **Initializer-Agent** (Setup, 1×) + **Worker-Agent** (inkrementelle
  Schritte, n×)[^3].
- Externalisierter State in drei Artefakten: strukturierte Feature-Liste (JSON) mit
  Pass/Fail, Progress-Log (human-readable), Git-History[^3].
- Workflow-Engine als Harness (Temporal bei Replit[^11]), Sub-Agents mit kompakten
  Summaries (1–2 k Tokens) zurück an Koordinator[^2].
- Rainbow-Deployments für Agent-Version-Upgrades während laufender Workflows[^10].
- End-to-End-Tests (Browser-Automation) als expliziter Abschluss-Check, nicht als optionaler
  Schritt[^3].

## Quellenbewertung

- Tier 1 (Primär, direkt gefetcht): Anthropic-Blog-Posts[^1][^2][^3][^10], OpenAI Practical
  Guide[^4][^5], arXiv-Surveys[^6][^7][^8].
- Tier 2 (Industrie-Postmortem mit Substanz): Cognition[^9], Replit+Temporal[^11],
  GitHub[^12], LangChain[^13].
- Kreuzvalidierung erfüllt: jede Pattern-Empfehlung steht in ≥ 2 unabhängigen Tier-1/2-Quellen;
  die Multi-Agent-Kontroverse (Anthropic "do carefully" vs. Cognition "don't") ist explizit
  als Kontroverse gekennzeichnet, nicht als Konsens.
- Nicht genutzt: Tutorial-/Blog-Content ohne Metriken, marketing-lastige Framework-Vergleiche.

## Implikationen für unser System

**Hält Control/Execution-Trennung gegen aktuelle Praxis?** — Ja, sie ist **Mainstream 2026**.
Der akademische Trend "explizite Workflow-Graphen mit State-Persistenz"[^7], Replits
"Temporal-Workflow pro Agent + Activities für non-deterministische Logik"[^11] und
Anthropics "Harness trennt Orchestrierung von agentischem Schritt"[^3] spiegeln genau diese
Trennung. Unser Control-Layer (Workflow-Coordination) ≈ Orchestrator/Harness/Controller,
unser Execution-Layer ≈ LLM-Calls + Tools in Activities.

**Was wir übernehmen sollten**:

- Single-Agent-Loop als Default für jedes Einzelprojekt; Multi-Agent nur wenn Parallelität
  oder Tool-Explosion messbar zwingt[^1][^4][^9].
- Git als Checkpoint-Primitive auch in unserem PKM-/Projekt-Kontext[^3][^11].
- Feature-Liste (JSON) + Progress-Log (Markdown) als explizite Long-Running-Artefakte[^3].
- Sub-Agent-Summaries auf 1–2 k Tokens; Koordinator arbeitet nie mit Roh-Traces[^2][^10].
- End-to-End-Verifikation als obligatorischer letzter Schritt, nicht optional[^3].

**Was wir vermeiden sollten**:

- Parallele Sub-Agents, die sich Context-frei auf verzahnte Teilprobleme stürzen (Coding,
  Schema-Änderungen)[^9][^10].
- Reine In-Context-State-Haltung über Session-Grenzen hinaus[^2][^3].
- Dezentrale Handoff-Pattern ohne zentrale Synthese — in Single-User-Personal-Setting
  entsteht kein Triage-Volumen, das das rechtfertigt[^4][^6].

## Offene Unsicherheiten

- Der Langfristwert von MCP/A2A-Protokollen[^8] für ein **Single-User-Personal-System**
  ist unklar — sie adressieren primär Enterprise-Interop.
- Anthropic und Cognition haben eine offene Kontroverse zu Multi-Agent; ob es sich um
  Task-Klassen- oder Reife-Dissens handelt, ist nicht abschließend klar.
- Keine Quelle adressiert explizit den **Personal/Home-Use-Skalenbereich** (1 Nutzer,
  n Projekte); Empfehlungen extrapolieren aus Enterprise/Dev-Tools-Szenarien.
- Langzeitstudien zu Drift von externalisierten Memory-Dateien (CLAUDE.md, NOTES.md) über
  Monate existieren noch nicht.

## Quellen

[^1]: Anthropic, "Building Effective Agents", 19.12.2024.
  https://www.anthropic.com/engineering/building-effective-agents
[^2]: Anthropic, "Effective Context Engineering for AI Agents", 2025.
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
[^3]: Anthropic, "Effective Harnesses for Long-Running Agents", 2025.
  https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
[^4]: OpenAI, "A Practical Guide to Building AI Agents", 2025.
  https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
[^5]: OpenAI Cookbook, "Agents" topic index.
  https://developers.openai.com/cookbook/topic/agents
[^6]: Survey, "LLM-based Agentic Reasoning Frameworks: Methods to Scenarios",
  arXiv 2508.17692, August 2025. https://arxiv.org/html/2508.17692v1
[^7]: Survey, "Agentic AI: Architectures, Taxonomies, Evaluation", arXiv 2601.12560,
  Januar 2026. https://arxiv.org/html/2601.12560v1
[^8]: Survey, "The Orchestration of Multi-Agent Systems: Architectures, Protocols,
  Enterprise Adoption", arXiv 2601.13671, Januar 2026. https://arxiv.org/html/2601.13671v1
[^9]: Cognition, "Don't Build Multi-Agents", 12.06.2025.
  https://cognition.ai/blog/dont-build-multi-agents
[^10]: Anthropic, "How We Built Our Multi-Agent Research System", Juni 2025.
  https://www.anthropic.com/engineering/multi-agent-research-system
[^11]: Temporal, "Replit uses Temporal to power Replit Agent reliably at scale", 2025.
  https://temporal.io/resources/case-studies/replit-uses-temporal-to-power-replit-agent-reliably-at-scale
[^12]: InfoQ, "GitHub Expands Copilot Ecosystem with AgentHQ", November 2025.
  https://www.infoq.com/news/2025/11/github-copilot-agenthq/
[^13]: LangChain Blog, "How and when to build multi-agent systems", 2025.
  https://blog.langchain.com/how-and-when-to-build-multi-agent-systems/
