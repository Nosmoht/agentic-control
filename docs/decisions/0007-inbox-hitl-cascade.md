# ADR-0007: HITL-Eskalation per Inbox-Kaskade, kein synchroner Push

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §6.2, §8`

## Kontext und Problemstellung

Das System muss an bestimmten Punkten menschliche Freigabe einholen
(irreversible Aktionen, überschrittene Budgets, ungelöste Klassifikationen).
Der Nutzer ist *einer*, nicht erreichbar rund um die Uhr, und jede
Unterbrechung hat empirisch belegte kognitive Kosten (Mark 2004,
Leroy 2009).

## Entscheidungstreiber

- **Attention-Interruption-Cost**: eine Unterbrechung kostet messbar
  Folge-Performance.
- **Alert-Fatigue**: dauerhaft synchrone Push-Gates führen zu
  Approval-by-reflex (Anti-Muster aus CDSS-Forschung).
- **Response-Latenz-Realismus**: der Nutzer reagiert nicht binnen Minuten
  auf jede Anfrage.
- LangGraph und OpenAI Agents SDK verwenden Inbox-/Interrupt-Pattern als
  State-of-the-Art.

## Erwogene Optionen

1. **Synchroner Push bei jedem Gate** (Telegram/Mail sofort).
2. **Inbox-Cards, asynchron, manueller Pull** ohne Eskalation.
3. **Inbox-Cards + Eskalations-Kaskade** (4 h Push, 24 h Mail, 72 h Abandon).
4. **Auto-Continue bei niedrigem Risiko, Push nur für High-Risk**.

## Entscheidung

Gewählt: **Option 3 — Inbox-Kaskade**.

### Kaskade

| Zeit | Aktion |
|---|---|
| t=0 | Inbox-Card mit Risiko-Klasse, Kontext, Optionen |
| t=4 h | Push-Notification (nur Risiko ≥ medium) |
| t=24 h | Mail-Reminder |
| t=72 h | Work Item auto-`abandoned`, Observation geloggt, Bericht beim nächsten `work next` |

### Eskalations-Kriterien

Kumulativ:
- Irreversibilität × Blast-Radius (irreversibel + außenwirksam → Pflicht).
- Kalibrierte Konfidenz unter Schwelle (nicht rohe LLM-Confidence).
- Standardreaktionen (Clarify, Wait, Retry, Replan, Reject) erschöpft.

### Konsequenzen

**Positiv**
- Dauerbelastung des Nutzers bleibt niedrig (Alert-Fatigue-Mitigation).
- Für Low-Risk bleibt Auto-Continue möglich — HITL nicht Pflicht-Default.
- Abandoned-Pfad verhindert tote Work Items.
- Kompatibel mit LangGraph-`interrupt()`-Semantik und Pydantic-AI-HITL-
  Tool-Approval.

**Negativ**
- Niedrigere Reaktionsgeschwindigkeit als synchroner Push.
- Risiko: kritische Eskalationen werden übersehen, wenn der Nutzer Inbox
  länger nicht öffnet.
- 72-h-Abandon ist Eigenentscheidung ohne empirischen Beleg.

### Präzisierung (wichtige Klarstellung)

„Eskalation als Ausnahme" (Legacy-AD-13) gilt für **Häufigkeit**, nicht für
**Wichtigkeit**. Irreversible High-Risk-Aktionen eskalieren zwingend —
sie müssen nur selten sein.

## Referenzen

- `docs/research/09-hitl.md` — UX-Muster, Trust-Calibration, Alert-Fatigue
- Mark, Gudith & Klocke 2008 — Attention-Interruption-Cost
- Leroy 2009 OBHDP — Attention-Residue
