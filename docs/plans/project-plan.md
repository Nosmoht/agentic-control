# Project Plan

**Version:** 0.3.2-draft · **Stand:** 2026-04-26

Dieser Plan ist die Eine-Seite-Sicht auf die Roadmap. Details leben in der
Spec (`docs/spec/SPECIFICATION.md`), den ADRs (`docs/decisions/`), den
Feature-Files (`docs/features/`) und den Research-Briefs (`docs/research/`).

## Zielzustand

Ein persönliches Multi-Projekt-Steuerungssystem, das Claude Code und Codex
CLI als gleichwertige Peer-Adapter nutzt, Agent-Arbeit orchestriert statt
selbst ausführt, Ausführung per `ExecutionAdapter` kapselt, Kosten per
4-Scope-Budget-Gate kontrolliert und Benchmarks als Entscheidungs-Awareness
mitführt (nicht als Auto-Dispatch-Eingabe).

## Milestones

| Stage | Arbeitstitel | Ziel | Einstiegs-Kriterium | Exit-Kriterium |
|---|---|---|---|---|
| v0 | Handbetrieb mit Schema | Vokabular gegen echte Arbeit testen | Spec + ADRs + CLI-Scaffold bereit | SQLite-Schema + `work add`/`work next` laufen, 5+ Work Items manuell durchgezogen |
| v1a | Durable Single-Loop (lokal) | Work-Item-Lifecycle automatisieren | v0 Exit erfüllt | DBOS lokal, 8-Schichten-Sandbox, Budget-Gate, HITL-Inbox, Cost-Aware-Routing-Stub aktiv |
| v1b | Read-only Bridge (VPS optional) | Messenger/Mail als Adapter | v1a Exit erfüllt, Bridge-Bedarf belegt | Bridge pollt read-only, schreibt nicht |
| v2 | Portfolio-Koordination | Multi-Project, Dependencies, Knowledge | v1 Exit erfüllt | 3 parallele Projekte, Dependencies explizit, Knowledge-Capture |
| v3 | Governance & Lernen | Standards-Promotion, Bindings | v2 Exit erfüllt | ≥ 3 bound Standards in Agent-Runs wirksam |

Stage-Details entstehen in eigenen Dateien (`docs/plans/vN-*.md`), wenn sie
Substanz haben. Bis dahin genügt diese Tabelle.

## Feature-Index (manuell gepflegt)

| ID | Titel | Stage | Status | ADR | Spec | Notiz |
|---|---|---|---|---|---|---|
| F0001 | SQLite Schema for Core Objects | v0 | proposed | ADR-0001, ADR-0003 | §5.7 | Ausgangspunkt v0 |
| F0002 | `work add` / `work next` CLI | v0 | proposed | ADR-0001 | §5.3 | Einziger v0-Einstieg |
| F0003 | Cost-Aware Routing Stub | v1a | proposed | ADR-0014, ADR-0016 | §5.3, §8.6 | Minimal-Router; `dispatch pin` schreibt via ADR-0016 |
| F0004 | Benchmark Awareness (Manual Pull) | v1a | proposed | ADR-0014 | §5.5, §8.6 | `agentctl benchmarks pull`; Awareness, kein Auto-Dispatch |
| F0005 | Benchmark-Curated Pin Refresh | v1a | proposed | ADR-0014, ADR-0011, ADR-0016 | §5.3, §6.2, §8.6 | Wöchentlicher HITL-Kurations-Loop; Modell-Arrival + Pin-Drift |
| F0006 | Runtime Records SQLite Schema and Reconcile CLI | v1a | proposed | ADR-0011, ADR-0016 | §5.7, §6.2, §8.4, §10.4 | Voraussetzung für F0003/F0004/F0005/F0007; baut auf F0008 auf |
| F0007 | Tool-Risk-Drift Detection | v1a | proposed | ADR-0015, ADR-0011, ADR-0016 | §5.4, §8 | `agentctl tools audit` liest `PolicyDecision`-Historie + Digest-Card |
| F0008 | V1 Domain Schema (Run, Artifact, Evidence) | v1a | proposed | ADR-0001, ADR-0003, ADR-0016 | §5.7 | Schema-Voraussetzung für F0006 (FK-Anker `run`) |

Weitere Features entstehen mit ADR-Implementierung:
- ADRs 0010–0013 bekommen Feature-Files, sobald die Implementierung in
  Reichweite ist (v1a).

## Abhängigkeiten (informell)

```mermaid
graph LR
  F0001 --> F0002
  F0001 --> F0008
  F0008 --> F0006
  F0006 --> F0003
  F0006 --> F0004
  F0006 --> F0007
  F0003 --> F0005
  F0004 --> F0005
  F0002 -.no direct dep.- F0003
  F0002 -.no direct dep.- F0004
```

F0001 (v0-Schema) ist Voraussetzung für alles. F0002 (CLI) ist v0-Gate.
F0008 (V1-Domain-Schema mit `Run`/`Artifact`/`Evidence`) ist die
Schema-Voraussetzung für F0006 (FK-Anker `run`). F0006 (Runtime-
Records-Schema + Reconcile-CLI) ist Voraussetzung für **alle**
v1a-Slices, weil F0003/F0004/F0005/F0007 auf Runtime-Records und
ADR-0016-Schreibvertrag aufbauen. F0005 ist der Kurations-Loop und
hängt an F0003 + F0004. F0007 ist die Drift-Detection auf Tool-Risk-
Inventar (liest `PolicyDecision`-Historie aus F0006).

## Kritische Pfade

- **v0-Pfad:** F0001 → F0002 → v0-Exit.
- **v1a-Pfad:** F0001 → F0008 → F0006 → [F0003, F0004, F0007] →
  F0005 → Implementierung der ADRs 0010–0016 → v1a-Exit.

## Open v1a-Exit Implementation Gaps

Vor v1a-Exit (nicht vor v1a-Implementierungsstart) brauchen folgende
ADRs eigene Implementierungs-Feature-Files. V0.3.2-draft macht diese
Lücken explizit (Counter-Counter-Counter-Counter-Review-2026-04-26
Befund 6):

| ADR | Was implementiert werden muss | Mögliche Form |
|---|---|---|
| ADR-0010 | Execution-Harness: Sandbox-Mounts, Egress-Proxy, Secret-Injection, Exit-Vertrag | Eigenes F-Feature, ggf. zerlegt in Sub-Features |
| ADR-0010 / ADR-0015 | **Tool-Risk Pattern Matcher** zur Call-Zeit (First-Match-Glob, Catch-all, fail-closed Default) — Voraussetzung für sicheres `approval=never` | Eigenes F-Feature **oder** Bestandteil des ADR-0010-Harness-Features mit eigenen ACs |
| ADR-0012 | HITL-Inbox: `ApprovalRequest`-Lifecycle, Push/Mail-Eskalation, `stale_waiting`/`timed_out_rejected`-Übergänge, Digest-Card-Kanal | Eigenes F-Feature |
| ADR-0013 | Litestream-Restore-Drill, `needs_reconciliation`-Startup-Hook, v1b-Read-only-Bridge (optional) | Eigenes F-Feature, wenn quartalsweiser Drill produktiv wird |

Diese Liste ist normativ für die Frage „kann v1a-Exit erreicht
werden". Implementierungsstart kann aber sofort nach F0006-Doku
beginnen — F0003/F0004/F0005/F0007 brauchen nur F0001 + F0008 + F0006
als Doku-Voraussetzung, nicht die ADR-Implementierungs-Features.

## Offene Entscheidungen

Diese Punkte sind im Plan als Defaults gesetzt; Nutzer kann jederzeit
anpassen.

1. **Benchmark-Quellen-Auswahl.** Default: HuggingFace Open LLM Leaderboard,
   SWE-bench Verified, LiveBench, Aider polyglot, Chatbot Arena (community
   API). Revidierbar in ADR-0014 oder Feature-File F0004.
2. **Model-Inventory-Initialbefüllung.** Default: Opus 4.7, Sonnet 4.6,
   Haiku 4.5, GPT-5.4, GPT-5 mini, Gemini 3.1 Pro. Preise aus
   `docs/research/13-cost.md`. Pflegeintervall monatlich manuell.
3. **Feature-Lifecycle 3 Zustände.** Reicht für Solo-Betrieb. Ausdehnung
   auf 4–6 Zustände, sobald Review/QA-Gate gebraucht wird.
4. **Cost-Aware-Routing-Aktivierung.** Default `pinned` (`routing-pins.yaml`
   als Lookup) in v1a. `cost-aware`-Modus (Konfidenz × Kosten) wird
   **ausschließlich per explizitem Nutzer-Opt-in** über
   `agentctl dispatch mode cost-aware` aktiviert (V0.2.3-draft, ADR-0014;
   die frühere „5+ Pins oder 4 Wochen"-Auto-Aktivierung wurde
   gestrichen, weil empirisch nicht gedeckt). `pinned` mit
   F0005-Pin-Kuration ist eine legitime Endstufe.

## Anti-Ziele (bewusst NICHT in diesem Plan)

- **Task-Class-Specializer** (8 Klassen, Kendall-τ, Borda) — empirisch
  nicht gerechtfertigt, siehe Plan-Appendix A in
  `Plans/option-3-ich-m-chte-serialized-oasis.md`.
- **Cross-Model-Review-Loop** — empirisch nicht gerechtfertigt.
- **Learned Router** (RouteLLM-Training) — v2-Kandidat, nicht v1.
- **Benchmark-Scheduler** (DBOS-Workflow) — manueller Pull reicht für v1.
- **Per-Stage-Plan-Dateien mit Substanz** — leere Skelette produzieren
  keinen Wert.
- **Standards-Binding-Compiler** — v3-Thema.
- **Multi-Device-Sync, Event-Broker, Compliance-Audit-Trennung,
  Approval-Delegation.**

## Erfolgsmetriken (pro Stage)

v0:
- 5+ Work Items manuell durchgezogen (Vokabular-Test).
- Median-Zeit Idee → aktiv < 3 Tage (manueller Workflow).
- Keine Schema-Migration nötig nach 2 Wochen (Vokabular hält).

v1a:
- Runaway-Vorfälle (Global-Hard-Cap erreicht) = 0/Woche.
- Kosten/Tag < $25.
- Eskalations-Rate HITL/Work Item 10–25 %.
- Worktree-Sandbox-Verletzungen = 0.

v1b:
- Bridge-Latenz (Push → Inbox-Card) < 5 Minuten.
- Keine ungewollten Writes aus Bridge (Read-Only-Invariante).

v2:
- 3 parallele Projekte aktiv, WIP ≤ 5.
- Blocked-Lag < 1 Tag.

v3:
- ≥ 3 bound Standards in Agent-Runs nachweislich wirksam.
- Override-Rate Pin < 40 % (d. h. Cost-Aware-Routing gewinnt).

## Verweise

- Plan-Dokument (inkl. empirische Belege, Appendix A):
  [`../../Plans/option-3-ich-m-chte-serialized-oasis.md`](../../Plans/option-3-ich-m-chte-serialized-oasis.md).
- Spec: [`../spec/SPECIFICATION.md`](../spec/SPECIFICATION.md).
- ADRs: [`../decisions/`](../decisions/).
- Features: [`../features/`](../features/).
- Counter-Review (2026-04-23):
  [`../reviews/2026-04-23-counter-review.md`](../reviews/2026-04-23-counter-review.md).
