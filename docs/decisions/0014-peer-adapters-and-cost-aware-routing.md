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

**Pinned-Mode-Default ist konfigurierbar, nicht hartcodiert:** Im V1-
`pinned`-Mode wählt der Dispatcher den Adapter aus
`config/dispatch/model-inventory.yaml` (`rules.defaults.adapter`),
wenn kein Pin matched. Der V1-Vorschlag ist `claude-code`, empirisch
begründet durch das 7,6-pp-Coding-Delta in SWE-bench Verified
(Plan-Appendix A) und heutige Nutzungspraxis. Der Nutzer kann den
Default jederzeit in der Config umstellen, ohne diese ADR zu ändern.

Diese Trennung ist absichtlich: „beide Peers im Vertrag, einer ist
der V1-Default" ist ehrlicher als „beide gleichwertig" mit verstecktem
Hardcode (Counter-Review-2026-04-24, neuer Befund 1).

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
   - Wenn ein Pin matched → vorläufige DispatchDecision (Adapter +
     Modell aus Pin, Begründung "pin"), weiter zu Schritt 4.

2. Wenn kein Pin und Mode = pinned (V1-Default, dauerhaft tragbar):
   - Lies model-inventory.yaml.rules.defaults.adapter und das passende
     model-inventory.yaml.rules.defaults[<adapter-name>]-Modell.
   - Vorläufige DispatchDecision, weiter zu Schritt 4.

3. Wenn kein Pin und Mode = cost-aware (explizites Nutzer-Opt-in via
   `agentctl dispatch mode cost-aware`):
   a. Konfidenzschätzung via Haiku (confidence_probe_model aus inventory):
      "Task X — schafft ein cheap-tier Modell das mit hoher Konfidenz?"
      → {confidence: float 0..1, rationale: str}
   b. Wenn confidence >= 0.8: nutze cheap-tier Default.
   c. Wenn 0.5 <= confidence < 0.8: nutze standard-tier.
   d. Wenn confidence < 0.5: nutze premium-tier.
   e. Adapter-Wahl innerhalb Tier (Heuristik, kein Hardcode):
      - Coding-Work-Items (Match gegen
        config/dispatch/benchmark-task-mapping.yaml `coding`) →
        Default-Adapter aus Inventory (V1-Vorschlag claude-code,
        empirisch durch 7,6-pp-SWE-bench-Delta begründet).
      - Sonst → Adapter mit niedrigerem Input-Preis im gewählten Tier.
   f. Vorläufige DispatchDecision, weiter zu Schritt 4.

4. Budget-Gate-Check (ADR-0008) auf vorläufiger DispatchDecision:
   - Wenn Pre-Cost-Projektion > Projekt/Tag-Soft-Cap: Dispatcher wählt
     günstigeren Tier-Kandidaten erneut. Diese Rewahl wird als
     zusätzlicher `PolicyDecision(policy=budget_gate_override)`
     persistiert (ADR-0011) — **nicht** als zweite DispatchDecision.
   - Wenn Global-Hard-Cap erreicht: `suspend`, kein Dispatch.

5. **Nach erfolgreichem Gate-Check** wird DispatchDecision pro RunAttempt
   gefroren. Retries des Runs nutzen die gefrorene Entscheidung, es sei
   denn HITL greift.
```

Reihenfolge: **Dispatch → Budget-Gate → Freeze → Run-Start**. Dispatch
füttert die Cost-Projektion ins Gate; das Gate kann den Dispatcher
zurückzwingen, aber erst die finale post-gate-Auswahl wird gefroren.

`DispatchDecision` ist also der **post-gate-final** Record. Eine
Vor-Gate-Auswahl, die durch das Gate verdrängt wurde, wird **nicht**
als DispatchDecision persistiert — sie taucht ausschließlich als
`PolicyDecision(policy=budget_gate_override)` mit Verweis auf den
verworfenen Kandidaten auf (Counter-Review-2026-04-24, neuer Befund 2).

### Mode-Aktivierung: explizit, nicht automatisch

Der Wechsel von `pinned` zu `cost-aware` erfolgt **ausschließlich**
über `agentctl dispatch mode cost-aware` (zurück:
`agentctl dispatch mode pinned`). Es gibt **keinen** automatischen
Wechsel auf Basis von Pin-Anzahl, Zeitintervall oder anderen
Heuristiken — die frühere Regel „5+ Pins oder 4 Wochen" wurde
gestrichen, weil sie eine empirisch nicht gedeckte Architektur-
Ableitung war (Counter-Review-2026-04-24, neuer Befund 7;
RouteLLM-Evidenz bezieht sich auf API-Modell-Routing auf MT Bench,
nicht auf Headless-Agent-CLI-Routing).

Der `pinned`-Mode kann dauerhaft genutzt werden, wenn F0005 die Pins
kuratiert. `cost-aware` ist Upgrade-Pfad, kein Default-Endzustand.

### Codex Approval Mode (entscheidet: `approval=never`)

Codex CLI wird in V1 mit `--approval=never` + `--sandbox=workspace-write`
aufgerufen. Begründung:
- Single-Adapter-Approval-Architektur, keine Bridging-Komplexität.
- Protected Paths (`.git`, `.codex`, `.agents`) bleiben read-only durch
  Codex-Natives — zusätzlicher Schutz.
- HITL-Gates werden **orchestrator-seitig** durch das Tool-Risk-Inventory
  (ADR-0015, `config/execution/tool-risk-inventory.yaml`) ausgelöst,
  nicht durch Codex-native Prompts. Ohne dieses normative Artefakt
  wäre `approval=never` kein Vertragszustand, sondern ein implizites
  Versprechen (Counter-Review-2026-04-24, neuer Befund 6).

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

- **ADR-Split-Marker:** Diese ADR bündelt vier konzeptionelle
  Entscheidungen — Peer-Stance, ExecutionAdapter-Interface,
  Routing-Policy, Codex-Approval-Mode. Bei der nächsten substantiellen
  Änderung an einer dieser Achsen wird sie in eigene ADRs aufgespalten
  (Renumbering oder 0014a–0014d). Bis dahin: inline tragbar
  (Counter-Review-2026-04-24, Architekturperspektive).
- Eigene ADRs **0016** (Codex-Approval-Mode-Details, frühere Reservierung
  ADR-0015 wurde an das Tool-Risk-Inventory vergeben) und **0017/0018**
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
- ADR-0011 — Runtime Records (inkl. `DispatchDecision`,
  `PolicyDecision`)
- ADR-0012 — HITL Timeout Semantics
- ADR-0015 — Tool-Risk-Inventory (Voraussetzung für `approval=never`)
- `docs/research/01-claude-code.md`, `docs/research/02-codex-cli.md` — Adapter-Spezifika
- `docs/research/05-agent-patterns.md` — Routing als Muster
- `docs/research/13-cost.md` — Preisanker
- Plan-Appendix A — empirische Basis für Symbiose-Design (Plan-Datei
  `Plans/option-3-ich-m-chte-serialized-oasis.md`)
- Counter-Review (2026-04-23) Befund 6, 9
- RouteLLM — https://www.lmsys.org/blog/2024-07-01-routellm/
