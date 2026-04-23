---
topic: hitl
tier: B
date: 2026-04-23
status: draft
---

# Brief 09: Human-in-the-Loop-Eskalation in agentischen Systemen

## Forschungsfrage

Wann soll ein agentisches System auf den Menschen eskalieren statt autonom
weiterzuarbeiten? Welche UX-Muster kalibrieren Vertrauen, ohne Automation
Bias oder Alert-Fatigue zu erzeugen? Welche Timeout- und Fallback-Regeln
sind realistisch für einen Single-User, der Stunden oder Tage nicht
antwortet? Ist die Architekturentscheidung AD-13 ("Eskalation ist
Ausnahme, nicht Default") empirisch verteidigbar?

## Methodik

Iterative Recherche (drei Zyklen). Tier-1-Primärquellen: Anthropic-
und OpenAI-Agent-Guides, LangChain/LangGraph-Dokumentation, NVIDIA
Developer Blog, ICLR-2025-Paper, Lee & See 2004, Parasuraman/Sheridan
2000. Tier-2: Knight-Institute-Report zu Autonomy Levels, JMIR 2025
Review zu Alert-Fatigue, Gloria-Mark-Studien zu Task-Switching. Tier-3:
kuratierte Community-Posts zu LangGraph-Interrupt und Coding-Agents,
explizit als solche markiert. Abgelehnt: allgemeine "AI safety"-Essays
ohne konkrete Muster, Marketing-Posts von Notification-Vendors.
Cross-Validierung: jede Kernaussage stützt sich auf mindestens eine
Tier-1- oder Tier-2-Quelle; wo nur Tier-3 vorliegt, kennzeichne ich das.

## Befunde

### Kriterien: wann eskalieren?

Die Literatur konvergiert auf vier Eskalations-Trigger, die sich
multiplikativ kombinieren lassen (AND-Logik senkt Eskalationsrate):

- **Irreversibilität/Seiteneffekte**: OpenAIs Guide nennt explizit
  "cancellations, edits, shell commands, or sensitive MCP actions" als
  Pflicht-Approval-Kandidaten und empfiehlt, Tools pro Risikoklasse
  (low/medium/high) auf Read-only, Reversibilität, benötigte Scopes und
  finanziellen Impact zu bewerten[^1]. Anthropic empfiehlt Checkpoints
  "before irreversible actions, like approving financial transactions or
  deleting data"[^2].
- **Konfidenzschwelle**: "Trust or Escalate" (ICLR 2025) etabliert ein
  Cascade-Verfahren mit formaler Garantie menschlicher Zustimmung via
  Fixed-Sequence-Testing auf kleinem Kalibrierungs-Set; Eskalation nur
  dann, wenn ein kleineres Modell unsicher ist[^3]. LLM-Performance-
  Predictors (Arxiv 2026) lernen ein Meta-Modell, das kalibrierte
  Unsicherheit schätzt und per Threshold entscheidet, ob vertraut oder
  eskaliert wird[^4].
- **Risikoklasse/Blast-Radius**: NVIDIA koppelt Approval-Pflicht an die
  Autonomie-Stufe: Level-2-Systeme erfordern "time-of-use manual
  approval" für riskante Datenpfade, Level-3 "mandatory taint tracing
  and sanitization; human approval gates for sensitive actions"[^5].
- **Blocker/Ambiguität**: Anthropic nennt als letztes Kriterium, dass
  Agenten eskalieren sollen, "when agents encounter challenges they
  can't resolve" statt zu raten[^2]. Das deckt sich mit AD-13: vor
  Eskalation Clarify/Retry/Wait/Replan/Reject prüfen.

Konvergenter Befund: Eskalation ist **keine Funktion niedriger Konfidenz
allein**, sondern das Produkt aus Konfidenz × Reversibilität × Blast-
Radius. Reine Konfidenz-Gates erzeugen entweder False Positives
(Alert-Fatigue) oder False Negatives (Schaden), weil LLM-Konfidenz
schlecht kalibriert ist[^6].

### UX-Muster

Drei Hauptmuster dominieren Produktionssysteme:

- **Inline-Approval/Interrupt-Resume**: LangGraph `interrupt()` pausiert
  den Graphen am Node, persistiert State via Checkpointer, resümiert mit
  `Command(resume=value)` – drei Entscheidungstypen: approve, edit,
  reject[^7]. OpenAI Agents SDK modelliert Approvals als
  "interruptions" mit serialisierbarem State, der erst später genehmigt
  werden darf[^8]. Kern-Invariante: State überlebt Prozessneustart, damit
  Approval asynchron erfolgen kann.
- **Batched/Digest-Review**: Für AI-Agents, die viele kleine Aktionen
  ausführen, wird explizit empfohlen "one summary, not a play-by-play"
  zu emittieren[^9]. Airship-Daten 2025: Smartphone-Nutzer empfangen
  46–63 Push-Notifications/Tag – AI-Agents drohen diese Zahl weiter zu
  erhöhen[^9].
- **Inbox/Queue mit Prioritäten**: JMIR-2025-Review zu Clinical-
  Alerts fand, dass Alerts überhört werden, sobald Volumen kognitive
  Kapazität überschreitet ("so many things popping up"); belegte
  Mitigations sind Farbcodierung, patientenspezifischer Kontext und
  Frequenzlimit[^10].

**Trust-Kalibrierung (Lee & See 2004)**: "Calibrated trust" –
Nutzervertrauen soll den tatsächlichen Fähigkeiten entsprechen; Unter-
und Übervertrauen sind beide dysfunktional[^11]. CalTruIAS (2024)
überträgt das Modell auf intelligente Automatisierungssysteme als
Ko-Arbeiter[^12]. Praktische Konsequenz für UX: Unsicherheit sichtbar
machen, nicht nur Ergebnisse[^13].

**Automation Bias**: Systematische Reviews und eine 2024er Studie zu
AI-CDSS zeigen zwei Fehlerklassen – Omissions (menschlicher Reviewer
übersieht AI-Fehler) und Commissions (menschlicher Reviewer übernimmt
falsche AI-Empfehlung gegen bessere eigene Evidenz); in ECG-Studien
wechselten Ärzte in 6 % der Fälle von korrekter eigener Diagnose auf
falsche CDSS-Empfehlung[^14]. Konsequenz: reine "Approve/Reject"-
Prompts ohne Kontext produzieren Rubber-Stamping.

### Agent-spezifische HITL-Primitive

| System | Primitive | Semantik |
|--------|-----------|----------|
| LangGraph | `interrupt()` + Checkpointer | Pause/Persist/Resume mit approve/edit/reject[^7] |
| OpenAI Agents SDK | `needsApproval: true` auf Tool | Run pausiert, Interruption + State serialisierbar[^8] |
| Anthropic Guidance | Checkpoints vor irreversiblen Aktionen | konzeptionell, nicht in ein API-Primitive gegossen[^2] |
| Claude Code (CLI) | Tool-Approval-Prompt pro Invocation | synchroner Inline-Prompt; Community lobt UX-Transparenz[^15] |
| Cline/Cursor/Aider | File-Write-Approvals, Auto-Approve-Listen | konfigurierbare Allowlists pro Tool[^15] |

Konvergenz: Alle produktiven Systeme implementieren **Tool-granulare
Approval-Gates**, nicht globale Stop-Points. State-Persistenz ist
Voraussetzung für asynchrone Approvals. Die MCP-Task-Extension (Rev.
2025-11-25) standardisiert lang laufende asynchrone Operationen als
"call-now, fetch-later"-Protokoll[^16] – direkt relevant für
Approval-Flows, die Stunden dauern.

### Timeouts und Fallbacks

Blind Spot der akademischen Literatur: "long-running HITL" mit
Stunden/Tagen Wartezeit ist kaum untersucht. Produktionssysteme
improvisieren:

- LangGraph-Doku adressiert **keine** Timeout-Semantik explizit; State
  liegt im Checkpointer und wartet unbegrenzt[^7].
- OpenAI Agents SDK: State kann serialisiert und später fortgesetzt
  werden, "if approval takes time"[^8]; kein Default-Timeout.
- ESCALATE.md (Community-Konvention, Tier 3) schlägt explizite
  Timeouts + Fallback via "KILLSWITCH.md" vor – wenn niemand innerhalb
  Timeout antwortet, Shutdown[^17]. Nur eine Quelle; als
  Referenzpattern, nicht als empirische Evidenz einzuordnen.
- Chatbot-Handoff-Playbooks aus 2025 nutzen Sentiment-/Intent-Trigger
  und Multi-Channel-Fallback (Chat → E-Mail → Ticket)[^18].

Realistische Policy-Bausteine: (a) Pause-statt-Abort für legitime
spätere Auflösung (AD-13 sagt dasselbe), (b) Heartbeat mit Reminder
nach N Stunden, (c) Eskalations-Channel-Wechsel (In-App → Push →
E-Mail → SMS) nur für hohe Risikoklasse, (d) Auto-Reject als sicherer
Default für irreversible Aktionen nach Deadline, Auto-Continue nur für
reversible Low-Risk-Fälle.

### Kosten der Eskalation

Mark et al.: nach Interruption braucht ein Knowledge-Worker im Schnitt
~23 Minuten, um vollständig zur Ursprungsaufgabe zurückzukehren; Worker
switchen im Mittel alle 3 Minuten[^19]. Microsoft Work Trend Index
2025: Interruption alle zwei Minuten, 45 % der Notifications
irrelevant[^9]. Alert-Fatigue in Medizin gilt als hinreichend belegt,
um Design-Reviews zu rechtfertigen; Haupt-Mitigations sind Frequenz-
limit, Kontext-Spezifität, Workflow-Integration[^10][^14].

Für einen Single-User-Betreiber bedeutet das: **jede Eskalation kostet
ca. 25 Minuten Fokuszeit**. Bei 10 Eskalationen/Tag ist der Workflow
fokus-technisch ruiniert – empirisches Argument für AD-13.

### Levels of Automation

Parasuraman/Sheridan/Wickens 2000 etablieren vier Funktionsklassen
(Information Acquisition, Analysis, Decision, Action Implementation) ×
10 Automatisierungsstufen[^20]. Das Modell ist bis heute am meisten
zitiert, aber nicht LLM-spezifisch. Jüngere Taxonomien:

- **Knight-Institute (2025)**: fünf Stufen anhand Nutzerrolle –
  Operator, Collaborator, Consultant, Approver, Observer; Autonomie
  ist Design-Wahl, unabhängig von Capability[^21].
- **NVIDIA (2025)**: vier Stufen (Inference API → Deterministic →
  Weakly Autonomous → Fully Autonomous); Sicherheits-Controls
  skalieren nichtlinear mit Autonomie-Level[^5].
- Interface-EU-Klassifikation schlägt autonomy-basierte Regulation vor
  und knüpft Haftung an Stufe[^22].

Konsens: Autonomie-Stufe ist pro Task konfigurierbar, nicht globale
System-Eigenschaft. Eskalationspolicy sollte an Stufe gekoppelt sein,
nicht an Agent-Identität.

## Quellenbewertung

Tier-1 (belastbar): Lee & See 2004, Parasuraman/Sheridan 2000,
Anthropic- und OpenAI-Agent-Guides, LangChain-Doku, NVIDIA Developer
Blog, JMIR-Review 2025, ICLR-2025-Paper, Knight-First-Amendment-
Institute-Report. Tier-2 (belastbar mit Kontext): Gloria-Mark-Papers
(CHI), CDSS-Empirik-Studie PubMed 2024, Arxiv-Preprints zu
Konfidenz-Kalibrierung (peer-review-pending). Tier-3 (Kontext, nicht
Evidenz): ESCALATE.md, Chatbot-Handoff-Blogposts, Coding-Agent-
Vergleichsblogs – konsistent mit Tier-1-Aussagen, aber einzeln nicht
ausreichend. Lücke: kein gutes empirisches Paper zu asynchronem HITL
mit Tagen-Latenz bei Single-User-Systemen – hier extrapoliere ich aus
Produktionsmustern.

## Implikationen für unser System

**Eskalations-Kriterien V1** (AND-verknüpft, Eskalation nur wenn alle
drei zutreffen):
1. Aktion ist irreversibel ODER wirkt außerhalb der Trust-Zone
   "Restricted Execution" (konform zu 06-trust-failure-and-escalation).
2. Standardreaktionen (Clarify, Retry, Wait, Replan, Reject) wurden
   begründet verworfen – Protokollierung als Audit-Evidenz.
3. Policy-Klasse erfordert Approval ODER Konfidenz unter kalibriertem
   Threshold.

**Empfohlenes UX-Muster (Single-User)**: Inbox-Queue mit priorisierten
Approval-Cards + Digest-Zusammenfassung. Begründung: Inline-Prompts
triggern 23-Minuten-Interruption-Cost[^19]; Batched-Review
(stündlich/täglich) reduziert Alert-Fatigue[^9]; Approval-Card enthält
Aktion, Blast-Radius, Alternative, Auto-Default-at-Timeout. Pure
Messenger-Notifications nur für die höchste Risikoklasse
(z. B. Identity/Produktion). Muster deckt sich mit LangGraph-
Interrupt-Semantik (State persistiert, Mensch antwortet asynchron)[^7].

**Timeout- & Fallback-Policy V1**:
- Default-Eskalation: kein Timeout, Pause bleibt bis Entscheidung.
- Für Aktionen mit Deadline-Semantik (z. B. externer Cutoff):
  Auto-Reject bei Ablauf, nie Auto-Approve.
- Reminder-Kaskade: Inbox → Push nach 4 h → E-Mail nach 24 h; nur für
  Risikoklasse ≥ medium.
- Kein automatischer Channel-Wechsel zu "lauteren" Kanälen, solange
  Inbox nicht geprüft wurde (Anti-Alert-Fatigue).

**Ist AD-13 empirisch verteidigbar?** Ja, mit Präzisierung. Der Satz
"Eskalation ist Ausnahme, nicht Default" wird direkt gestützt durch
Anthropic ("match oversight to risk, low-risk runs autonomously"[^2]),
NVIDIAs Level-Staffelung[^5] und die Interruption-Cost-Daten[^19].
Präzisierung: AD-13 sollte explizit machen, dass "Ausnahme" sich auf
**Eskalationshäufigkeit** bezieht – nicht auf Kritikalität. Für
irreversible High-Risk-Aktionen ist Eskalation der Standard, nur eben
selten, weil solche Aktionen selten sein sollten. Ohne diese Schärfung
riskiert AD-13, als "Auto-Continue-by-default" fehlgelesen zu werden,
was die Automation-Bias-Literatur[^14] als gefährlich identifiziert.

## Offene Unsicherheiten

- Keine harten Daten zu Single-User-Response-Latenzen in async
  HITL-Systemen (wie lange wartet eine Person realistisch?).
- Unklar, ob Konfidenz-basiertes Eskalieren (ICLR 2025[^3]) außerhalb
  Evaluation-Settings übertragbar ist; LLM-Selbst-Konfidenz ist
  bekannt schlecht kalibriert.
- Gloria-Marks 23-Minuten-Zahl stammt aus Büro-Knowledge-Work;
  Übertragbarkeit auf Solo-Operator mit selbstgebautem Agent-System
  nicht empirisch belegt.
- Parasuraman-Sheridan-Modell wurde bis heute **nicht formal** auf
  LLM-Agents erweitert; Knight- und NVIDIA-Taxonomien sind Proposals,
  keine validierten Instrumente.
- Interaktionseffekte zwischen Batching und Dringlichkeit: ein zu
  aggressives Digest-Fenster kann Deadlines verpassen – kein
  Benchmark verfügbar.

## Quellen

[^1]: OpenAI, "A practical guide to building agents" (2025).
  https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
[^2]: Anthropic, "Building Effective AI Agents" (2024/2025).
  https://www.anthropic.com/engineering/building-effective-agents
[^3]: "Trust or Escalate: LLM Judges with Provable Guarantees for
  Human Agreement", ICLR 2025.
  https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf
[^4]: "LLM Performance Predictors: Learning When to Escalate in Hybrid
  Human-AI Moderation Systems", Arxiv 2026.
  https://arxiv.org/html/2601.07006v1
[^5]: NVIDIA Developer Blog, "Agentic Autonomy Levels and Security"
  (2025). https://developer.nvidia.com/blog/agentic-autonomy-levels-and-security/
[^6]: "Mind the Confidence Gap: Overconfidence, Calibration, and
  Distractor Effects in LLMs", Arxiv 2025.
  https://arxiv.org/html/2502.11028v3
[^7]: LangChain Docs, "Human-in-the-loop".
  https://docs.langchain.com/oss/python/langchain/human-in-the-loop
[^8]: OpenAI Developers, "Guardrails and human review".
  https://developers.openai.com/api/docs/guides/agents/guardrails-approvals
[^9]: Courier, "Notification Fatigue Is About to Get 10x Worse" (2026);
  Microsoft Work Trend Index 2025 (sekundär zitiert).
  https://courier-com.medium.com/notification-fatigue-is-about-to-get-10x-worse-60c151909440
[^10]: JMIR 2025, "Understanding Alert Fatigue in Primary Care:
  Qualitative Systematic Review". https://www.jmir.org/2025/1/e62763
[^11]: Lee, J. D., & See, K. A. (2004). "Trust in automation: Designing
  for appropriate reliance". Human Factors, 46(1), 50–80.
  https://philpapers.org/rec/LEETIA-3
[^12]: "Calibrating workers' trust in intelligent automated systems"
  (PMC, 2024). https://pmc.ncbi.nlm.nih.gov/articles/PMC11573890/
[^13]: "Addressing Uncertainty in LLM Outputs for Trust Calibration
  through Visualization and UI Design", Visible Language 59-2.
  https://www.visible-language.org/Issue-59-2/addressing-uncertainty-in-llm-outputs-for-trust-calibration-through-visualization-and-user-interface-design.pdf
[^14]: "Automation Bias in AI-Decision Support: Empirical Study",
  PubMed 2024. https://pubmed.ncbi.nlm.nih.gov/39234734/
  und "Automation complacency" (Springer 2025).
  https://link.springer.com/article/10.1007/s43681-025-00825-2
[^15]: Cline/Cursor/Aider Comparison (Tier 3, UX-Evidenz).
  https://www.qodo.ai/blog/cline-vs-cursor/
  und "10 Things Developers Want from Agentic IDEs in 2025" (Redmonk).
  https://redmonk.com/kholterhoff/2025/12/22/10-things-developers-want-from-their-agentic-ides-in-2025/
[^16]: WorkOS, "MCP Async Tasks: Building long-running workflows for
  AI Agents" (2025). https://workos.com/blog/mcp-async-tasks-ai-agent-workflows
[^17]: ESCALATE.md Protocol (Community, Tier 3). https://escalate.md/
[^18]: Robylon, "Smarter AI Escalations: 4 Steps to Perfect Human
  Handoffs" (2025). https://www.robylon.ai/blog/smarter-ai-escalations-customer-support
[^19]: Mark, G., Gudith, D., Klocke, U. (2008/CHI). "The Cost of
  Interrupted Work: More Speed and Stress".
  https://ics.uci.edu/~gmark/chi08-mark.pdf
[^20]: Parasuraman, R., Sheridan, T. B., Wickens, C. D. (2000). "A
  Model for Types and Levels of Human Interaction with Automation".
  IEEE Trans. SMC-A 30(3). https://dl.acm.org/doi/10.1109/3468.844354
[^21]: Knight First Amendment Institute, "Levels of Autonomy for AI
  Agents" (2025). https://knightcolumbia.org/content/levels-of-autonomy-for-ai-agents-1
[^22]: Interface EU, "An Autonomy-Based Classification for AI Agents".
  https://www.interface-eu.org/publications/ai-agent-classification
