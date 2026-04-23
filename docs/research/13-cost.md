---
topic: cost
tier: C
date: 2026-04-23
status: draft
---

# Brief 13: Kosten-, Budget- und Rate-Limit-Muster für agentische Arbeit

## Forschungsfrage

Welche aktuellen (2025–2026) Best Practices existieren für Kostenkontrolle,
Budget-Enforcement und Rate-Limit-Handling in LLM-Agentensystemen? Konkret:
Enforcement-Punkte im Call-Path, defensive Token-Zählung, Backoff- und
Shared-Quota-Muster, Runaway-Loop-Schutz, Prompt-Caching-Ökonomie,
Observability-Minimum und realistische Kostenanker für eine persönliche
Mehr-Projekt-Umgebung.

## Methodik

Drei Recherchezyklen über offizielle Anthropic/OpenAI-Dokumente
(Pricing, Prompt-Caching, Rate-Limits, Agent-SDK), Engineering-Blogs mit
harten Zahlen (Kloudedge Apex, Datadog, OpenTelemetry GenAI SIG) sowie
Erfahrungsberichte aus dem LLMOps-Feld. Priorität: Tier-1-Vendor-Docs
für Preise, Multiplikatoren und Mechanik; Tier-2/3 für Muster und
reale Tagesbudget-Anker. Quellen älter als 12 Monate wurden für Preise
verworfen, für Backoff-/Queueing-Grundlagen zugelassen.

## Befunde

### Budget-Enforcement-Muster

Produktionssysteme staffeln Budgets hierarchisch, wobei höhere Ebenen als
globale Obergrenzen und niedrigere als granulare Kontrollen wirken[^1][^7]:

- **Request-Cap:** `max_tokens` pro Call — obligatorisch und billigste
  Absicherung; verhindert einzelne Ausreißer-Antworten.
- **Task-/Session-Cap:** `max_turns` plus `max_budget_usd` als harte
  Rails. Claude Agent SDK und OpenAI Agents SDK unterstützen beides nativ,
  aber **ohne Default** — wer nichts setzt, hat keinen Schutz[^4][^8].
- **Per-Projekt-Cap:** Tag- oder Virtual-Key-Budgets; bei LiteLLM pro
  Key/Team/Org mit `max_budget` + `budget_duration` (z. B. `30d`)[^1].
- **Rolling Daily/Monthly-Cap:** Proxy-seitig; gateway erzwingt
  "reject, wenn `spend >= max_budget`" bevor der LLM-Call abgeht[^1][^7].

**Enforcement-Point:** Der Gate muss **vor** dem LLM-Call sitzen
(pre-call budget check + post-call accounting). Anthropic/OpenAI bieten
keine serverseitige Hard-Cap-Obergrenze pro Tag — nur Spend-Limits auf
Organisationsebene. Die praktische Lösung ist ein eigener Proxy
(LiteLLM, Bifrost, Portkey) oder eine In-Process-Middleware, die jede
Request durch einen Budget-Ledger schiebt[^7].

### Token-Counting

- **Anthropic:** eigener Tokenizer, **nicht** tiktoken-kompatibel.
  Offizielles Count-Tokens-Endpoint (`/v1/messages/count_tokens`) ist
  kostenlos und liefert "billing-grade"-Schätzung, kann aber um kleine
  Beträge abweichen[^2][^9].
- **OpenAI:** `tiktoken` lokal, exakt für Message-Inputs; Tool-Definitionen
  und System-Prompts zählen, Cache-Reads nicht separat sichtbar.
- **Defensive Nutzung:** Vor einem teuren Call (z. B. Opus mit großem
  Kontext) Pre-Count und Kostenprognose, erst dann fortfahren.
  `token_count × model_input_price + max_tokens × output_price` als
  Oberabschätzung; bei > N $ Stopp oder Eskalation[^2][^9].
- `tiktoken` als Approximation für Claude ist laut Anthropic
  "understandably not great" — nur als grobe Vorfilterung nutzen[^2].

### Rate-Limit-Handling

- **Anthropic:** Token-Bucket, kontinuierliche Auffüllung statt
  Fixed-Window. Limits pro Modellklasse (RPM/ITPM/OTPM), shared
  zwischen US- und Global-Endpoints. `429` + `retry-after`-Header[^3].
  Tier 1 (nach $5 Deposit) ≈ 50 RPM / 30k ITPM / 8k OTPM für Sonnet/Opus,
  50 RPM / 50k ITPM / 10k OTPM für Haiku 4.5; Tier 4 (ab $400 kumulativ)
  bis 4 000 RPM / 2 M ITPM Sonnet / 4 M ITPM Haiku[^10].
- **OpenAI:** RPM/TPM/RPD/TPD; `error.type = rate_limit_exceeded`.
  Fehlgeschlagene Requests zählen auf das Minutenlimit — naives Retry
  verschärft den Zustand ("thundering herd")[^11].
- **Muster:** Exponential Backoff + Jitter (`tenacity`, `backoff`), nie
  mehr als ~6 Retries, Circuit Breaker (z. B. 5-von-10-Fehler → 60 s
  Open), priorisierte Queue für heiße Tasks, Shared-Quota-Koordination
  über Semaphore/Redis-Leaky-Bucket, wenn mehrere Agenten denselben Key
  nutzen[^11]. Vorteil bei Anthropic: **gecachte Input-Tokens zählen
  nicht gegen ITPM** — Caching vervielfacht nicht nur Kosten-, sondern
  auch Durchsatzbudget[^3].

### Runaway-Loop-Prävention

- **Claude Code / Agent SDK:** `--max-turns` (zählt nur Tool-Use-Turns,
  nicht Finaltext), `max_budget_usd`. Standard: **keine Defaults** in
  Non-Interactive; interaktiv nur durch Kontextfenster begrenzt[^4].
- **OpenAI Agents SDK:** `max_turns` in `Runner.run()`; löst
  `MaxTurnsExceeded` aus, `error_handlers["max_turns"]` erlaubt
  kontrollierten Final-Output[^8].
- **Zusätzliche Caps (nicht nativ):** Wall-Clock-Timeout, Tool-Call-Cap
  pro Task, Repeat-Detection (gleicher Tool-Call 3× → abort), Kosten
  pro Task. Claude Code GitHub Issue #4277 dokumentiert explizit, dass
  `--max-turns` Tight Loops innerhalb weniger Turns nicht erkennt —
  externe Loop-Detection bleibt nötig[^4].
- **Kontext-Rot-Kopplung:** Lange Loops führen zu Context-Bloat, was
  Kosten pro Turn exponentiell treibt; Step-Cap ≠ Cost-Cap.

### Prompt-Caching-Ökonomie

- **Anthropic** (explizit, via `cache_control`-Breakpoints, max. 4 pro
  Request): Cache-Write 5-min = **1,25×** Base-Input, 1-h = **2×**;
  Cache-Read = **0,1×** (90 % Rabatt)[^5]. Minimum cacheable:
  4 096 Tokens für Opus 4.7/4.6/4.5 und Haiku 4.5; 2 048 für Sonnet 4.6.
  Break-even: 5-min-Write amortisiert sich **ab erstem Read**, 1-h-Write
  ab zweitem.
- **OpenAI** (automatisch, kein Code nötig): **50 % Rabatt** auf
  wiederverwendete Input-Tokens ab 1 024 Tokens Prompt-Länge, in 128-er
  Inkrementen; bis zu 80 % Latenzreduktion[^6].
- **Anti-Patterns, die Cache brechen:**
  - Tool-Definitionen mitten im Session ändern → invalidiert System-
    und Messages-Cache (Hierarchie tools → system → messages)[^5].
  - Web-Search/Citations toggeln, Images hinzufügen/entfernen,
    Extended-Thinking-Param wechseln.
  - Plugin-State-Wechsel in Claude Code (dokumentierter Bug #27048).
  - Non-tool-result User-Messages strippen prior Thinking-Blocks.
- **Praktische Regel:** Cache-Breakpoint nach statischem Prefix
  (System + stabile Tools + langes Referenzdokument) setzen; alles
  Dynamische **nach** dem Breakpoint. Reale Ersparnis-Anekdote:
  $720 → $72/Monat (90 %) bei hohem Wiederverwendungsgrad[^5].

### Observability

- **Standard:** OpenTelemetry **GenAI Semantic Conventions** (SIG
  aktiv seit 04/2024, AI-Agent-Convention 2025 finalisiert). Attribute
  `gen_ai.request.model`, `gen_ai.usage.input_tokens`,
  `gen_ai.usage.output_tokens`, `gen_ai.operation.name`,
  `gen_ai.provider.name`; Prompt-Content in **Span-Events**, nicht
  Attributes (Collector-Filterbarkeit)[^12].
- **Inline-Receipts** (Claude Code, Codex CLI, Agent SDK liefern
  `total_cost_usd`, `usage`, `num_turns` in jeder `ResultMessage`[^4])
  sind ausreichend für Single-User; Telemetrie-Backend (Datadog,
  Uptrace, Langfuse) ist Over-Engineering unter ~50 $/Tag.
- **Minimum für Single-User-V1:** Append-only JSONL-Ledger pro Task
  mit `{task_id, model, input_tok, output_tok, cache_read, cache_write,
  cost_usd, ts, duration_s}`; Tages-Rollup via `jq`/DuckDB.

### Preisanker 2026 (Stand 2026-04)

| Modell            | Input $/M | Output $/M | Cache-Read $/M | Batch 50 % |
| ----------------- | --------- | ---------- | -------------- | ---------- |
| Claude Opus 4.7   | 5,00      | 25,00      | 0,50           | ja[^14]    |
| Claude Sonnet 4.6 | 3,00      | 15,00      | 0,30           | ja[^14]    |
| Claude Haiku 4.5  | 1,00      | 5,00       | 0,10           | ja[^14]    |
| GPT-5.4           | 2,50      | 15,00      | ~1,25 (50 %)   | ja[^13]    |
| GPT-5.4 mini      | 0,40      | 1,60       | ~0,20          | ja[^13]    |
| GPT-5.4 nano      | 0,20      | 1,25       | ~0,10          | ja[^13]    |

Long-Context-Surcharge bei GPT-5.4 > 272 k Tokens: $5,00 / $22,50[^13].
Claude Opus 4.7 und Sonnet 4.6 haben 1 M Kontext flat (kein Surcharge)[^14].

**Realer Tagesbedarf:** Tracker-Studie 24/7-Agent: ~$6,20/Tag
($187/Monat), Spanne $1,50 (ruhiger Sonntag) bis $8 (30 Tasks);
Stuck-Loop-Vorfall: $12 in einem Nachmittag[^15]. Kloudedge Apex
14-Agent-Workforce: ~$8/Tag. Ohne Controls sind $300/Tag realistisch[^15].

## Quellenbewertung

Preise, Rate-Limits und Caching-Mechanik aus offiziellen Anthropic-
und OpenAI-Docs (Tier 1) — belastbar, zwei unabhängige Vendor-Docs
pro Claim. Budget-Muster aus LiteLLM-Docs (Tier 1 für das Tool) plus
Produktionsberichte (Tier 2/3). Tagesanker $5–8 aus zwei unabhängigen
Tier-3-Trackern mit konsistenten Zahlen; Extremwerte $300/Tag nur mit
einer Quelle — als Obergrenze zu lesen, nicht als Erwartung.
OpenTelemetry-GenAI ist Tier 1 (CNCF-Projekt). Unsicher: genaue
Cache-Read-Preise für OpenAI (50 % auf Input, keine separate Linie).

## Implikationen für unser System

**Empfohlenes Budget-Schema** (4-stufig, additiv, pre-call enforced):

| Scope       | Default-Cap | Reset      | Hard/Soft   | Override           |
| ----------- | ----------- | ---------- | ----------- | ------------------ |
| Request     | `max_tokens`=8k output; pre-count × price < $0,50 | — | Hard | Explicit flag  |
| Task        | $2,00 und 25 Turns und 15 min Wall-Clock          | per task | Hard | HITL-Eskalation |
| Projekt     | $5,00/Tag (low) · $15,00/Tag (high) pro Projekt   | 24 h    | Soft → Hard | HITL-Freigabe   |
| Global/Tag  | $25,00/Tag über alle Projekte                     | 24 h    | Hard        | Manuell +$X        |
| Monat       | $500                                              | 30 d    | Hard        | Manuell            |

- Defaults orientieren sich am $6–8/Tag-Anker + 3–4× Sicherheitsfaktor;
  sollten nach 2 Wochen realer Nutzung kalibriert werden.
- **Enforcement-Point:** Thin-Gateway-Modul (Python/TS) vor jedem
  SDK-Call: liest Ledger, prüft alle 4 Scopes, bricht mit typisiertem
  `BudgetExceeded`-Error ab. Nach Response: Atomic-Append in Ledger
  plus Ablage der `usage`-Felder inkl. Cache-Read/Write.
- **Runaway-Schutz obligatorisch:** `max_turns=25`, `max_budget_usd=2`
  (entspricht Task-Cap), Wall-Clock 15 min, Repeat-Tool-Call-Detection
  (3× gleiche Signatur → abort).
- **Caching-Strategie:** Immer Cache-Breakpoint nach stabilem Prefix
  (System + Tools + geladene Docs). **Niemals** Tool-Set mitten in
  Task ändern — erzwingt Re-Invalidation. Bei langlebigen Sessions
  (> 5 min Idle, < 1 h) 1-h-TTL nutzen (break-even ab 2. Read).
- **Minimum-Observability V1:** JSONL-Append-Ledger pro Task
  (`~/.agentctl/ledger/YYYY-MM-DD.jsonl`), Tages-Rollup-Command
  (`agentctl costs today`), Warn-Schwelle bei 80 % Tagesbudget,
  Hard-Stop bei 100 %. OTel-GenAI-Span-Names reservieren, aber noch
  nicht exportieren.
- **Modell-Routing als Kosten-Hebel:** Haiku 4.5 für Klassifikation/
  Formatierung/Triage (20×–25× günstiger als Opus 4.7); Sonnet 4.6
  als Default; Opus 4.7 nur für explizit markierte Deep-Work-Tasks.
  Faustregel: < 5 % der Calls auf Premium[^16].
- **Grobe Tagesobergrenze Single-User 2026:** $15–25/Tag für
  "seriously used" (tägliche Codearbeit + Research + Automationen);
  Hard-Cap bei $25, Monats-Cap $500 als Feuerlöscher.

## Offene Unsicherheiten

- Reale Cache-Hit-Rate bei unserem Multi-Projekt-Setup ist unbekannt —
  90 %-Ersparnis-Anekdote gilt für stabile Long-Context-Workloads,
  nicht zwingend für heterogene Projekte.
- OpenAI-Cache-Verhalten ist automatisch, aber intransparent
  (keine manuelle Breakpoint-Kontrolle); Metriken zur realen Hit-Rate
  in Agent-Workloads fehlen.
- Tight-Loop-Detection unterhalb des Turn-Caps bleibt ungelöst; ein
  eigener Repeat-Signatur-Detector ist machbar, aber nicht erprobt.
- Shared-Quota-Koordination zwischen mehreren parallel laufenden
  Agenten gegen einen API-Key ist unter-dokumentiert (Anthropic
  bestätigt "shared across `inference_geo`", sagt aber nichts zu
  Multi-Process-Koordination auf Client-Seite).
- Realistische Spanne $6–8/Tag basiert auf zwei Trackern; persönliche
  Arbeitsmuster können 2–3× höher liegen (Opus-lastig) oder niedriger
  (Caching + Haiku-Routing).

## Quellen

[^1]: LiteLLM Docs — Budgets/Virtual Keys. docs.litellm.ai/docs/proxy/{users,virtual_keys,cost_tracking} — Tier 1.
[^2]: Anthropic — Token Counting. platform.claude.com/docs/en/build-with-claude/token-counting — Tier 1.
[^3]: Anthropic — Rate Limits. docs.claude.com/en/api/rate-limits — Tier 1.
[^4]: Claude Agent SDK — Agent Loop. code.claude.com/docs/en/agent-sdk/agent-loop; GitHub anthropics/claude-code#4277 — Tier 1 + 2.
[^5]: Anthropic — Prompt Caching. platform.claude.com/docs/en/build-with-claude/prompt-caching; Lightfoot "$720→$72" Medium 2025 — Tier 1 + 3.
[^6]: OpenAI — Prompt Caching. openai.com/index/api-prompt-caching/; platform.openai.com/docs/guides/prompt-caching — Tier 1.
[^7]: TrueFoundry — LLM Cost Tracking. truefoundry.com/blog/llm-cost-tracking-solution — Tier 2.
[^8]: OpenAI Agents SDK — Runner. openai.github.io/openai-agents-python/ref/run/; Issue #844 — Tier 1.
[^9]: Propel — Token Counting Guide 2025. propelcode.ai/blog/token-counting-tiktoken-anthropic-gemini-guide-2025 — Tier 3 (kreuzvalidiert).
[^10]: Claude API Quota Tiers 2026. aifreeapi.com/en/posts/claude-api-quota-tiers-limits; Anthropic Console — Tier 3 cross-checked.
[^11]: OpenAI Cookbook — Handle Rate Limits. cookbook.openai.com/examples/how_to_handle_rate_limits — Tier 1.
[^12]: OpenTelemetry — GenAI Semantic Conventions. opentelemetry.io/docs/specs/semconv/gen-ai/; Datadog Blog 2025 — Tier 1 + 2.
[^13]: OpenAI — API Pricing. openai.com/api/pricing/; nxcode.io GPT-5.4 — Tier 1 + 3.
[^14]: Anthropic — Pricing. platform.claude.com/docs/en/about-claude/pricing; Finout 2026 — Tier 1 + 3.
[^15]: Mireille, Dev.to 2026 "Tracked Every Dollar"; Kloudedge Apex "Unit Economics" Medium 2026-02 — Tier 3, zwei unabh. Tracker.
[^16]: CIO.com 2026 "Without controls, an AI agent can cost more than an employee". cio.com/article/4152601 — Tier 2.
