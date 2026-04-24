# ADR-0014: Peer Adapters and Cost-Aware Routing

* Status: accepted
* Date: 2026-04-24
* Context: `docs/spec/SPECIFICATION.md §5.3, §5.4, §8.5, §8.6`
* **Amends ADR-0004** (headless-agents-pydantic-ai) in den Abschnitten
  „Aufruf-Disziplin" und „Entscheidung". ADR-0004 bleibt in allen anderen
  Teilen gültig.

## Kontext und Problemstellung

ADR-0004 legt fest, dass Claude Code headless und Codex CLI exec genutzt
werden — ohne expliziten Primary. Der Counter-Review (Befund 9) hat
empfohlen, Claude Code als Primary zu wählen, um Adapter-Komplexität in
v1 zu vermeiden. Der Nutzer hat am 2026-04-24 **Option 3** gewählt: beide
Adapter als **gleichwertige Peers** ab v1.

Der Nutzer hat zusätzlich eine „Symbiose CC ↔ Codex"-Anforderung formuliert
mit zwei Vermutungen: (a) Modell-Spezialisierung, (b) Cross-Model-Review.
Die empirische Recherche (siehe Plan-Appendix A) hat beide als schwach
belegt identifiziert — stattdessen ist Cost-Aware-Routing (RouteLLM-Stil)
das robuste Muster.

Zusammenhängende offene Entscheidungen:
- Wie sieht die `ExecutionAdapter`-Schnittstelle aus?
- Welche Routing-Policy wählt pro Run einen Adapter + Modell aus?
- Wie mit Codex-Approval-Modus umgehen (`approval=never` vs. `on-request`)?

## Entscheidungstreiber

- Nutzer-Anforderung: beide Adapter als Peers.
- Empirisch: Modell-Unterschiede sind außerhalb Coding < 2 pp (Rauschen);
  Harness-Varianz ±16 pp schlägt Modell-Varianz; Cost-Aware-Routing spart
  85 % Kosten bei 95 % Qualität (RouteLLM).
- Betriebsdisziplin: Dispatcher ist Policy, Execution ist bounded (ADR-0001,
  AD „Control is not execution").
- Minimalität: keine separate ADR-Oberfläche für jede Adapter-Eigenheit,
  solange zwei Implementierungen reichen.

## Erwogene Optionen

1. Claude Code als Primary (Counter-Review Befund 9 Empfehlung).
2. Beide Adapter, Task-Class-Specializer (Nutzer-Vermutung a).
3. Beide Adapter, Cross-Model-Review-Loop (Nutzer-Vermutung b).
4. **Beide Adapter, Cost-Aware-Routing (Konfidenz × Kosten)**.
5. Beide Adapter, Zufalls-Dispatch für Datensammlung (MoA-ähnlich).

## Entscheidung

Gewählt: **Option 4**.

### Peer-Adapter-Stance

Claude Code und Codex CLI sind gleichwertige `ExecutionAdapter`-
Implementierungen. Der Orchestrator unterscheidet sie nur dort, wo die
Schnittstelle es vorschreibt (Tool-Allowlist-Übersetzung, Approval-Mode).
Kein Vorrang, keine „Primary"-Rolle.

### `ExecutionAdapter`-Interface (inline, kein separater ADR-0018)

Fünf Verben + eine Profiltypen-Menge:

```
ExecutionAdapter:
  supports(profile: HarnessProfile) -> bool
  prepare(run: RunAttempt, profile: HarnessProfile) -> PreparedInvocation
  execute(invocation: PreparedInvocation) -> AdapterResult
  cancel(invocation_id: str) -> None
  describe() -> AdapterDescriptor
```

**HarnessProfile** (neutral):
- `model_ref` — logische ID aus `config/dispatch/model-inventory.yaml`.
- `tool_allowlist` — logische Tool-Namen; Adapter übersetzt in eigene
  Tool-Grammatik.
- `sandbox_contract` — Verweis auf ADR-0010 (Mount-Tabelle, Netz, Secrets).
- `context_budget` — Token-Caps aus ADR-0008.
- `approval_mode` — `never` | `on_request` | `policy_gated`.
- `output_schema` — JSON-Schema-Ref oder `freeform`.
- `secrets_scope` — welche Credentials zur Laufzeit verfügbar.

**AdapterResult**:
- `attempt_id`, `exit_status`, `turns`, `cost_estimate`, `token_usage`,
  `tool_calls[]`, `artifacts[]`, `stdout_jsonl_ref`, `idempotency_keys{}`.

**AdapterDescriptor** (statisch):
- `name`, `version`, `supported_tool_kinds[]`, `supported_models[]`,
  `structured_output_capable`, `approval_modes_supported[]`, `known_limits[]`.

Adapter-spezifische Übersetzung (logischer Tool-Name → CLI-Flag, logisches
Modell → CLI-Flag, logischer Approval-Modus → Wrapper) lebt **innerhalb**
jedes Adapters, in `translate/`-Submodulen. Der Orchestrator special-cased
keinen Adapter außerhalb einer `describe()`-Abfrage.

### Konkrete Aufruf-Disziplin

**Claude Code:**
```
claude -p --output-format json --bare \
  --allowedTools=<derived> \
  --model=<derived> \
  [HarnessProfile wird über --system-prompt-append + Env injiziert]
```
Subagents, Skills und MCP-Server werden nur genutzt, wenn der Adapter sie in
`describe().supported_tool_kinds` anzeigt und der HarnessProfile es erlaubt.

**Codex CLI:**
```
codex exec --json --output-schema <file> --ephemeral \
  --approval=never \
  --sandbox=workspace-write \
  [HarnessProfile wird über Env + Arguments injiziert]
```
Protected Paths bleiben `ro` (ADR-0010-Mount-Tabelle).

### Cost-Aware-Routing-Policy

Der Dispatcher (Work-Sub-Component, §5.3) wählt pro Work Item einen
Adapter + Modell. Entscheidungsfunktion:

```
1. Prüfe routing-pins.yaml:
   - Wenn ein Pin matched → Adapter + Modell aus Pin, begründete
     DispatchDecision, Ende.

2. Wenn kein Pin, aber Nutzer in 'pinned'-Mode (default bis 5+ Pins
   gepflegt oder 4 Wochen vergangen):
   - Nutze model-inventory.defaults[adapter] mit adapter=claude-code als
     globalem Default.
   - Begründete DispatchDecision, Ende.

3. Wenn 'cost-aware'-Mode aktiv:
   a. Konfidenzschätzung via Haiku (confidence_probe_model aus inventory):
      "Task X — schafft ein cheap-tier Modell das mit hoher Konfidenz?"
      → {confidence: float 0..1, rationale: str}
   b. Wenn confidence >= 0.8: nutze cheap-tier Default (Haiku oder
      GPT-5 mini).
   c. Wenn 0.5 <= confidence < 0.8: nutze standard-tier (Sonnet oder
      GPT-5 mini, je nach Budget).
   d. Wenn confidence < 0.5: nutze premium-tier (Opus oder GPT-5.4), mit
      Budget-Gate-Prüfung.
   e. Adapter-Wahl innerhalb Tier:
      - Wenn Work Item hat `work_item_type: coding_*` → Claude Code
        (7,6-pp-Vorteil in SWE-bench Verified gerechtfertigt).
      - Sonst → Adapter mit niedrigerem Input-Preis im gewählten Tier.
   f. Begründete DispatchDecision.

4. Budget-Gate-Check (ADR-0008) mit dem gewählten Modell:
   - Wenn Pre-Cost-Projektion > Projekt/Tag-Soft-Cap: Dispatcher wählt
     günstigeren Tier-Kandidaten erneut.
   - Wenn Global-Hard-Cap erreicht: `suspend`, kein Dispatch.
```

Reihenfolge: **Dispatch → Budget-Gate-Check → Run-Start**. Dispatch füttert
die Cost-Projektion ins Gate, nicht umgekehrt.

`DispatchDecision` wird als Runtime Record (ADR-0011) persistiert und pro
`RunAttempt` **frozen** — Retries nutzen dieselbe Entscheidung, es sei denn,
HITL greift.

### Codex Approval Mode (entscheidet: `approval=never`)

Codex CLI wird in V1 mit `--approval=never` + `--sandbox=workspace-write`
aufgerufen. Begründung:
- Single-Adapter-Approval-Architektur, keine Bridging-Komplexität.
- Protected Paths (`.git`, `.codex`, `.agents`) bleiben read-only durch
  Codex-Natives — zusätzlicher Schutz.
- HITL-Gates werden **orchestrator-seitig** durch den Tool-Risk-Inventory
  (ADR-0007, ADR-0011 `PolicyDecision`) ausgelöst, nicht durch Codex-native
  Prompts.

`on-request`-Mode bleibt als `policy_gated`-Profil dokumentiert; aktiviert
über einen künftigen ADR, sobald Bedarf entsteht (z. B. Codex-Cloud-Nutzung
mit fremden Repos).

### Bewusst NICHT getan

- **Task-Class-Specializer** (8 Klassen, Haiku-Classifier, Dispatch nach
  Class) — empirisch nicht gerechtfertigt. Frontier-Modelle sind außerhalb
  Coding ununterscheidbar; Harness-Varianz überwiegt.
- **Cross-Model-Review-Loop** — Self-Preference-Bias, Position-Bias, Self-MoA
  schlägt Mixed-MoA. Production-Tools vermeiden es.
- **Kendall-τ-Disagreement-Detection, Borda-Rank-Composite, Shadow-Mode** —
  Mathematik baut auf Benchmark-Signal auf, das empirisch für Dispatch-
  Entscheidungen zu schwach ist.
- **Learned Router (RouteLLM-Training)** — v2-Kandidat, nicht V1.

### Konsequenzen

**Positiv**
- Peer-Adapter-Stance schließt Nutzer-Anforderung (Option 3).
- Cost-Aware-Routing ist empirisch solide (RouteLLM: 85 % / 95 %).
- `pinned`-Default ist safe — kein Kaltstart-Desaster.
- Routing-Pins geben Nutzer Kontrolle; `cost-aware`-Mode ist Upgrade, kein
  Default.
- Interface ist klein (5 Verben, 1 Profil-Typ, 1 Ergebnis-Typ).

**Negativ**
- Zwei Adapter erhöhen Test-Matrix (2× Harness-Profile, 2× Tool-Allowlist-
  Mapping, 2× Credential-Policy).
- Haiku-Confidence-Probe kostet zusätzlichen LLM-Call pro Work Item (ca.
  $0,005 bei aktuellen Preisen).
- `approval=never` für Codex verschiebt Verantwortung komplett zum
  Orchestrator — Tool-Risk-Inventar muss präzise sein.

### Follow-ups

- Eigene ADRs **0015** (Codex-Approval-Mode-Details) und **0016/0017**
  (Adapter-spezifische Harness-Profile), sobald die Adapter implementiert
  werden (v1a-Scope).
- Learned Router als v2-Kandidat evaluieren, wenn 100+ DispatchDecisions
  vorliegen.

## Referenzen

- ADR-0004 — headless-agents-pydantic-ai (diese ADR amends §Aufruf-Disziplin)
- ADR-0006 — 8-Schichten-MVS (konsumiert)
- ADR-0007 — HITL-Inbox-Kaskade
- ADR-0008 — 4-Scope-Budget-Gate (nachgelagert zum Dispatch)
- ADR-0010 — Execution Harness Contract
- ADR-0011 — Runtime Records (inkl. `DispatchDecision`)
- ADR-0012 — HITL Timeout Semantics
- `docs/research/01-claude-code.md`, `docs/research/02-codex-cli.md` — Adapter-Spezifika
- `docs/research/05-agent-patterns.md` — Routing als Muster
- `docs/research/13-cost.md` — Preisanker
- Plan-Appendix A — empirische Basis für Symbiose-Design (Plan-Datei
  `Plans/option-3-ich-m-chte-serialized-oasis.md`)
- Counter-Review (2026-04-23) Befund 6, 9
- RouteLLM — https://www.lmsys.org/blog/2024-07-01-routellm/
