---
topic: context-count
tier: D
date: 2026-04-23
status: draft
---

# Brief 14: Kontext-Anzahl und -Grenzen für unser System

## Forschungsfrage

Wie viele fachliche Kontexte und welche Grenzschnitte sollte das persönliche
agentische Steuerungssystem haben — begründet aus den Befunden der Briefs 01–13?

## Methodik

Synthese der Briefs 01–13. Keine neue externe Recherche. Cross-Referenzen in
Fußnoten verweisen auf die Brief-Datei und den relevanten Abschnitt.

## Ausgangslage

Die Notizen `04-bounded-contexts.md` und `09-canonical-domain-model.md`
postulieren **13 Bounded Contexts** und **12 Kernobjekte** für einen erklärten
Single-User-Einsatz (`01 §Kernannahmen`, `10 §Betriebsprämissen`).
`REVIEW.md` hat das als systematisch über-strukturiert gekennzeichnet.

## Entscheidungsrelevante Befunde

### Untergrenze: was die Literatur *fordert*

- Fowler-Linie: Monolith-Zone unter ~12–24 Personen; Bounded Contexts entstehen
  aus *organisatorischer* Kopplung, nicht aus fachlicher Komplexität allein.
  13 Contexts bei n=1 sind in keiner Tier-1/2-Quelle verteidigbar.[^B06]
- Team-Topologies-Heuristik: 1 Team trägt max. 1 komplexe oder 3 einfache
  Subdomänen. Für n=1 ergibt das **3–5 Kernmodule** als empirisches Ziel.[^B06]
- PKM-Literatur: stärkste Achse ist **Aktionabilität** (PARA: Project vs. Area
  vs. Resource; GTD: Next Action vs. Someday/Maybe vs. Reference), nicht
  Bounded Context im DDD-Sinn.[^B08]

### Obergrenze: was das System *muss*

- Control/Execution-Trennung ist 2025–2026 mainstream.[^B05] Mindestens diese
  Grenze ist zu ziehen.
- Durable Workflow-Zustand muss außerhalb des LLM liegen — das ist ein echter
  fachlicher Schnitt gegen Execution, nicht nur eine Infrastrukturfrage.[^B03][^B05]
- Knowledge/Evidence ist ein eigenständiges Objekt-Cluster mit Promotions­logik,
  deren Mehrwert **genau dann** entsteht, wenn sie die Agent-Auffindbarkeit,
  -Autorität oder Cache-Strategie verändert.[^B11]

### Was kein eigener Kontext ist

- **Event Fabric**: keine fachliche Domäne. DBOS verwendet prozess­interne
  Queues; Events signalisieren, tragen aber keine Business-Wahrheit (AD-11).
  → Infrastrukturfragment, kein Modul.[^B03][^B12]
- **Observability & Audit**: Querschnitt, keine Fach­kategorie. Audit-Log hat
  andere Integritäts­anforderungen als Telemetrie — wenn überhaupt, getrennt.
  → kein Modul in V1.
- **Intent Resolution**: Funktion innerhalb der Control-Surface, keine eigene
  Domäne.[^B05]
- **Identity, Trust & Access**: bei Single-User ein ~5-zeiliger Token-Manager,
  keine Domäne. Inhaltlich ein Teil von Interaction + Execution-Sandbox-Policy.[^B07]
- **Project Provisioning & Provider Integration**: ein Attribut pro Projekt
  (`provider_binding`), keine eigene Domäne bei n=1.

### Approval und Governance

- Approval als eigenständiges Objekt rechtfertigt sich erst bei Delegation.[^REVIEW]
  Bei n=1 ist es ein Flag am Work Item (`pending_confirmation`) plus ein
  HITL-Prompt in der Inbox.[^B09]
- Governance / Binding rechtfertigt sich als eigenes Modul erst ab 2–3
  Promotions­stufen; für V1 reicht ein Lifecycle-State am Standard
  (`candidate → accepted → bound → retired`).[^B11]

## Empfohlener Schnitt: 5 Module

### Module

1. **Interaction** — Control Surface, Intent, HITL-Inbox und -Gates,
   Single-User-Identität und Secrets.
2. **Work** — Intake + Planning + Workflow als *ein* Work-Item-Lifecycle.
   Durable Execution-Framework (DBOS) sitzt hier.[^B03][^B12]
3. **Execution** — Bounded, sandboxed Agent-Runs mit Claude Code / Codex CLI
   als Subprocess; Provisioning als Property der gestarteten Run.[^B01][^B02][^B07]
4. **Knowledge** — Capture (Observation), Atomic Decisions, Standards mit
   4-stufigem Promotions­lifecycle, Artifact-Referenzen, Evidence.[^B08][^B11]
5. **Portfolio** — Project, Dependency, Binding-Scope und Policy-Anwendung als
   Properties. Kein eigener "Policy & Governance"-Kontext.[^B06]

### Begründung der Zahl 5

- Untergrenze von Brief 06 (3–5 Module) eingehalten, Obergrenze nicht überschritten.
- Jeder Schnitt entspricht einem echten Zustands-Owner (AD-12 bleibt einhaltbar).
- PKM-Aktionabilitäts-Achse von Brief 08 durchläuft: Work (Projects, active),
  Portfolio (Areas), Knowledge (Resources/Archive), Interaction (Inbox),
  Execution (ephemer).
- Durable-Execution-Mainstream von Brief 05 gespiegelt: *ein* Modul
  orchestriert, *ein* Modul führt aus.

### Warum nicht weniger

- 3 Module (Work / Execution / Knowledge) fusionieren Interaction in Work.
  Das verletzt die Control/Execution-Trennung aus Brief 05 und macht
  HITL-Inbox-Design schwieriger.
- 4 Module (ohne Portfolio) kollabieren Multi-Projekt-Koordination in Work.
  Bei ≥ 3 aktiven Projekten (Brief 10 WIP-Empfehlung) entsteht sofort Kopplung.

### Warum nicht mehr

- 6+ Module fügen entweder Infrastruktur (Event Fabric), Querschnitte
  (Observability), oder Single-User-Fiktionen (Identity, Intent Resolution)
  als Fach­domänen ein — alle durch Briefs 05, 06, 07 als falsche Kategorie
  identifiziert.
- Policy/Governance als eigenes Modul hat in V1 keinen eigenen Zustands-Owner;
  Binding ist ein Lifecycle-State am Standard, Scope ist ein Property.

## Kernobjekte (reduziert)

Aus den 12 Objekten in `09-canonical-domain-model.md`:

| Objekt | Entscheidung | Modul |
|---|---|---|
| Project | behalten | Portfolio |
| Work Item | behalten | Work |
| Workflow | umbenennen zu `Run` | Work |
| Dependency | behalten | Portfolio |
| Approval | als Flag am Work Item, nur bei Delegation separat | Work |
| Standard | behalten, 4-Stufen-Lifecycle | Knowledge |
| Observation | behalten | Knowledge |
| Decision | behalten (ADR-Minimalformat)[^B11] | Knowledge |
| Artifact | behalten | Knowledge |
| Evidence | behalten, `trust_class` streichen[^REVIEW] | Knowledge |
| Context Bundle | Funktion, kein Objekt | Knowledge |
| Provider Binding | Property an `Run`, kein Objekt | Execution |

Von 12 → **9 Objekte**. Die Aktionabilitäts-Achse aus Brief 08 verteilt sie
sauber über die 5 Module.

## Lifecycles (verkürzt)

- `Project`: `idea → candidate → active → dormant → archived`
  — `provisioning` fällt weg (war Drift-Quelle, siehe `REVIEW.md`).
- `Work Item`: `proposed → accepted → planned → ready → in_progress → waiting/blocked → completed/abandoned`
  — `planned` bleibt, `current_plan_ref` auch; nur eine Quelle für Plan-Inhalt
  in `work_plan` innerhalb Work.
- `Run` (ehemals Workflow): `created → running → paused/waiting/retrying → completed/failed/aborted`
  — Compensating-Variante fällt weg, wenn V1 keine kompensierbaren Ketten hat.
- `Dependency`: unverändert.
- `Standard`: `candidate → accepted → bound → retired` (von 6 → 4 Stufen).[^B11]
- `Artifact`: `registered → available → consumed → superseded → archived`.

## Trust-Zonen (vereinfacht)

Die 6 Zonen aus `06-trust-failure-and-escalation.md` reduzieren sich auf 4,
weil Identity als Single-User-Querschnitt und Audit als Observability-Querschnitt
wegfallen:

1. **External Untrusted** — Eingaben über Control Surface.
2. **Interpreted Control** — Interaction-Modul.
3. **Decision Core** — Work + Portfolio + Knowledge.
4. **Restricted Execution** — Execution-Modul, sandboxed.[^B07]

## Offene Entscheidungen

- Approval-Objekt wiederherstellen, sobald Delegation geplant wird.
- Governance als eigenes Modul, sobald > 2 Promotions­stufen oder
  mehrere Bindungs-Scopes pro Standard nötig werden.
- Observability/Audit explizit trennen, sobald Compliance-Audits anfallen —
  für V1 nicht der Fall.
- Wenn Multi-Device-Sync wichtig wird (Brief 12), bekommt Knowledge einen
  CRDT-Layer, was ein vierter Promotions­zustand an `Standard` werden könnte.

## Quellenverweise

[^B01]: `01-claude-code.md` — Claude Code nur im Headless-Modus als
  Execution-Kontext tragfähig.
[^B02]: `02-codex-cli.md` — `codex exec --json` als orchestrierbare
  Schnittstelle.
[^B03]: `03-durable-execution.md` — DBOS-Empfehlung; durable state
  außerhalb des LLM.
[^B05]: `05-agent-patterns.md` — Control/Execution-Trennung als
  Mainstream; Single-Agent-Loop als Default.
[^B06]: `06-ddd-scale.md` — Fowler-Linie, Team-Topologies-Heuristik,
  Urteil zu 13 Contexts bei n=1.
[^B07]: `07-trust-sandboxing.md` — MVS-Empfehlung.
[^B08]: `08-pkm.md` — Aktionabilitäts-Achse als wichtigste Leseachse.
[^B09]: `09-hitl.md` — Inbox-Queue statt Push.
[^B10]: `10-work-admission.md` — WIP ≤ 2 aktive Work Items, 3–5
  aktive Projekte.
[^B11]: `11-learning.md` — 2–3 Promotions­stufen; Stufe nur, wenn sie
  Agent-Auffindbarkeit / Autorität / Cache-Strategie ändert.
[^B12]: `12-persistence.md` — DBOS + SQLite + Litestream.
[^REVIEW]: `REVIEW.md` — Kritik an Approval-Objekt, `trust_class`, 13 Contexts.
