# ADR-0012: HITL Timeout Semantics

* Status: accepted
* Date: 2026-04-24
* Context: `docs/spec/SPECIFICATION.md §6.2, §8`; präzisiert ADR-0007.

## Kontext und Problemstellung

ADR-0007 hat den HITL-Mechanismus als Inbox-Kaskade (Push nach 4 h, Mail
nach 24 h, Auto-Abandon nach 72 h) festgelegt und Eskalations-Kriterien als
„kumulativ" (Irreversibilität × Blast-Radius, kalibrierte Konfidenz,
erschöpfte Standardreaktionen) formuliert.

Der Counter-Review (2026-04-23, Befund 2) hat zwei Probleme identifiziert:
- **Pauschales 72-h-Abandon** kann echte Arbeit verlieren und widerspricht
  `docs/research/09-hitl.md`, wo „Default-Eskalation: kein Timeout; bei
  Deadline: Auto-Reject, nie Auto-Approve" empfohlen wird.
- **„Kumulativ"** ist grammatikalisch gefährlich — kann als „alle vier
  Bedingungen zugleich nötig" gelesen werden, was irreversible High-Risk-
  Aktionen entschärfen würde.

## Entscheidungstreiber

- Nie Arbeit aufgeben, die rezensierbar ist.
- Nie Arbeit auto-approven.
- Irreversible High-Risk-Aktionen immer approvieren (unabhängig von Konfidenz).
- Low-Risk-System-Health-Signale (Benchmark-Drift, Cost-Trend) sollen den
  Nutzer informieren, aber keine Work Items pausieren.

## Erwogene Optionen

1. 72-h-Abandon als Default beibehalten — User-Vertrauen leidet.
2. Nie Auto-Abandon — alle HITL-Gates bleiben offen, Inbox wächst.
3. **Vier Zustände + disjunktive Kriterien + Digest-Card-Kanal.**
4. Approval nur synchron — kein asynchroner Modus, keine Timeouts.

## Entscheidung

Gewählt: **Option 3**.

### Vier HITL-Zustände

| Zustand | Bedeutung | Trigger | Exit |
|---|---|---|---|
| `waiting_for_approval` | Approval steht aus | Gate gezogen | `approved` (User entscheidet) |
| `timed_out_rejected` | Deadline erreicht | Work Item hat harte Deadline, sie läuft ab | Auto-Reject (**nie** Auto-Approve) |
| `stale_waiting` | Reminder gesendet, Work Item bleibt offen | 24 h ohne Reaktion | User kommt zurück → `approved` oder `rejected` |
| `abandoned` | Explizit beendet | **Nur** User-Kommando, Deadline-Timeout bei Low-Risk, oder 30-Tage-Inaktivität bei explizit low-risk-markierten Items | Terminal |

### Disjunktive Eskalations-Kriterien (OR, nicht AND)

Ein HITL-Gate wird getriggert, wenn **mindestens eine** der folgenden
Bedingungen greift:

1. **Irreversible oder außenwirksame Aktion** — immer, unabhängig von
   Konfidenz. Beispiel: Git-Push auf main, GitHub-Issue-Kommentar,
   Payment-Call, File-Delete außerhalb Worktree.
2. **Niedrige kalibrierte Konfidenz** (Orchestrator-Konfidenz, nicht rohe
   LLM-Confidence; Schwelle ADR-spezifisch pro Work Item-Typ).
3. **Erschöpfte Standardreaktionen** — Clarify, Wait, Retry, Replan, Reject
   wurden versucht und griffen nicht.
4. **Policy-Klasse verlangt Approval** (z. B. Work Item mit Tag
   `needs_human_review`).

Jede Bedingung allein reicht. „Kumulativ" aus ADR-0007 ist damit explizit
aufgelöst.

### Digest-Card-Kanal (neu)

Für **Low-Risk-System-Health-Signale**, die kein Work Item blockieren:
- Benchmark-Drift („Opus 4.7 ist seit letztem Pull auf SWE-bench um 3 pp
  gefallen").
- Cost-Trend („Tages-Ausgaben liegen 40 % über 14-Tage-Mittel").
- Sandbox-Violation-Trend („3 Config-Write-Versuche diese Woche").
- Modell-Inventory-Staleness („HuggingFace Leaderboard nicht mehr
  erreichbar seit 7 Tagen").

Diese Signale erzeugen eine **Digest-Card** in der Inbox mit:
- Status `info` (nicht `pending`).
- Kein Block auf Work Items.
- Keine Eskalations-Kaskade (Push/Mail).
- Tägliche Batch-Zusammenfassung, nicht pro-Event.

Der Nutzer kann Digest-Cards ignorieren; sie verfallen automatisch nach 14
Tagen.

### Kaskade (angepasst gegenüber ADR-0007)

| Zeit | Risiko ≥ medium | Risiko < medium |
|---|---|---|
| t=0 | Inbox-Card `waiting_for_approval` | Inbox-Card `waiting_for_approval` |
| t=4 h | Push (OS-Notification) | — |
| t=24 h | Mail + `stale_waiting`-Flag | `stale_waiting`-Flag |
| t=72 h | kein Auto-Abandon (ADR-0007 Widerruf), aber zweite Mail | kein Auto-Abandon |
| t=30 Tage | bei explizit low-risk-markierten Items: `abandoned` | bei explizit low-risk-markierten Items: `abandoned` |

### Präzisierung „Eskalation als Ausnahme"

„Eskalation als Ausnahme" (AD-13 in den Legacy-Notizen, SPEC §8 Framing)
gilt für **Häufigkeit**, nicht für **Wichtigkeit**. Irreversible High-Risk-
Aktionen eskalieren zwingend — sie müssen nur selten sein.

### Konsequenzen

**Positiv**
- Kein Arbeitsverlust durch Pauschal-Timeout.
- Auto-Reject statt Auto-Approve bei Deadline — konservativ.
- Digest-Card-Kanal trennt Work-Item-Blocker von System-Info.
- Disjunktive Kriterien schließen die Fehlinterpretations-Klasse.

**Negativ**
- Inbox kann bei vielen `stale_waiting`-Items anwachsen. Mitigation: Nutzer
  sieht in CLI `agentctl inbox stale`.
- 30-Tage-Rule für `abandoned` setzt explizite Low-Risk-Markierung voraus —
  minimalen Annotations-Aufwand pro Work Item.

## Referenzen

- ADR-0007 — Inbox-Kaskade (diese ADR präzisiert, ersetzt aber nicht den
  gesamten Rahmen)
- ADR-0011 — `ApprovalRequest` als Persistenz-Objekt
- `docs/research/09-hitl.md` — HITL-Literatur (Mark 2004, Leroy 2009, CDSS-
  Alert-Fatigue, LangGraph-`interrupt()`)
- Counter-Review (2026-04-23) Befund 2
