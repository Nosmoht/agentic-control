# ADR-0015: Tool-Risk-Inventory and Approval Routing

* Status: accepted
* Date: 2026-04-25
* Context: `docs/spec/SPECIFICATION.md §5.4 (Execution), §6.2 (HITL),
  §8.1 (Trust-Zonen), §8.2 (Sandbox)`; präzisiert ADR-0014
  (Codex `approval=never`).

## Kontext und Problemstellung

ADR-0014 legt fest, dass Codex CLI in V1 mit `--approval=never` und
`--sandbox=workspace-write` aufgerufen wird. Diese Konfiguration ist
**nur sicher**, wenn der Orchestrator HITL-Gates **vor** dem Agent-Run
zieht, basierend auf einer präzisen Klassifikation der Tools, die der
Agent aufrufen darf. Der Counter-Review-2026-04-24 hat als neuen
Befund 6 festgehalten, dass diese Klassifikation in V0.2.0-/V0.2.2-draft
als implizite Annahme im Text steht, aber kein normatives Artefakt
existiert.

Ohne explizites Tool-Risk-Modell:

- Ist die Sicherheit von `approval=never` ein implizites Versprechen,
  nicht ein vertraglicher Zustand.
- Kann ein neuer Tool-Wrapper (zusätzlicher MCP-Server, neue
  Tool-Allowlist-Position) sicherheitsrelevant sein, ohne dass das im
  System sichtbar wird.
- Sind `PolicyDecision`-Records ohne klares Eingangsschema — der
  Orchestrator weiß nicht, welche Policy-Klasse er für ein
  `gh issue comment` ziehen soll.
- Existiert keine fail-closed-Garantie: ein vom Inventory nicht
  abgedecktes Tool fällt nicht automatisch auf die strengste Klasse
  zurück.

## Entscheidungstreiber

- **Sicherheits-Asymmetrie**: ein einziger falsch klassifizierter
  Tool-Call (z. B. `gh pr merge` oder `git push --force` ohne Gate)
  kann größeren Schaden anrichten als die gesamte Pflege des Inventars
  kostet.
- **Fail-closed Default**: jedes Tool ohne explizite Klassifikation
  bekommt automatisch die strengste Policy.
- **n=1-Kalibrierbarkeit**: der Nutzer pflegt das Inventory selbst und
  kann es bei neuen Tools schnell erweitern.
- **Doku-first-Prinzip**: Sicherheits-Artefakte gehören in V0.2-Spec,
  nicht in eine spätere Implementierungs-Phase.

## Erwogene Optionen

1. **Inline in ADR-0014** als YAML-Anhang, kein eigener ADR — bündelt
   weiter, ADR-0014 wird noch dicker.
2. **Eigener ADR + separate Config-Datei** (gewählt) — saubere
   Trennung, klares Schema, dauerhaft pflegbar.
3. **Verschieben auf v1a-Implementation** — V1-Spec hält nur die
   Anforderung; konkrete Form kommt mit Feature.
4. **Living config ohne ADR** — flexibles Format, aber kein Vertrag.

## Entscheidung

Gewählt: **Option 2** — eigener ADR und Config-Datei
`config/execution/tool-risk-inventory.yaml`.

### Vier Risk-Klassen

| Klasse | Bedeutung | Default-Approval |
|---|---|---|
| `low` | Lokal, reversibel, abgeschlossen (z. B. file_read, grep) | `never` |
| `medium` | Lokal mit Side-Effect (file_write innerhalb Worktree, lokales shell_exec ohne Netz/State-Modifikation) | `never` |
| `high` | Außenwirksam, nicht-trivial (gh issue comment, slack post) | `required` |
| `irreversible` | Außenwirksam, schwer rückgängig (git push, gh pr merge, payment) | `required` |

### Schema

`config/execution/tool-risk-inventory.yaml` enthält:

- **`tools[]`**: Liste von `{pattern, risk, approval, constraint?}`.
  - `pattern`: logischer Tool-Name oder Glob (z. B. `gh_*`,
    `file_write`).
  - `risk`: eine der vier Klassen.
  - `approval`: `never` | `required` | `policy_gated` (entspricht dem
    `HarnessProfile.approval_mode`-Feld aus ADR-0014).
  - `constraint?`: optionale Bedingung als Freitext (z. B. „path within
    worktree") — für die Implementierung als zusätzlicher Pre-Flight-
    Check.
- **`default`**: Fail-closed-Default für nicht gelistete Tools
  (in V1: `risk: high, approval: required`).

### Orchestrator-Vertrag

Vor jedem Tool-Call:

1. Orchestrator matcht den geplanten Tool-Aufruf gegen
   `tools[].pattern` (erste Match in Reihenfolge gewinnt; Wildcards
   möglich; Catch-all-Patterns wie `gh_*` als Fallback unter den
   spezifischeren Einträgen).
2. Wenn kein Match: `default`-Policy gilt (fail-closed).
3. Wenn `approval: required`: HITL-Gate ziehen via `ApprovalRequest`
   (ADR-0011); Run pausiert (`waiting_for_approval`-Sub-State,
   ADR-0012), bis der Nutzer zustimmt.
4. Wenn `approval: never`: Tool-Call läuft, ein
   `PolicyDecision`-Record mit gematcheter Klasse + Risk-Klasse +
   Begründung („matched pattern X") wird persistiert.
5. Wenn `approval: policy_gated`: ADR-0007/0012-disjunktive Kriterien
   werten zusätzlich aus (z. B. wenn auch eine ungewöhnlich niedrige
   Konfidenz oder ein Standardreaktions-Erschöpfungs-Trigger
   greift, wird Gate gezogen).

### V1-Seed (Initial-Inventar)

`config/execution/tool-risk-inventory.yaml` startet mit ~21 Einträgen
(Datei-/Suche-/Grep-, Lokal-Write-, Git-, GitHub-Pattern, Notification-
und Web-Fetch). Das Catch-all `gh_*` deckt nicht explizit gelistete
GitHub-Subkommandos ab. Pflege: bei jedem neuen MCP-Server oder neuen
Tool wird das Inventar erweitert.

### Konsequenzen

**Positiv**

- `approval=never` für Codex CLI ist jetzt vertragsgesichert; ohne
  Inventory-Match → fail-closed.
- Tool-Risk-Klassifikation ist auditierbar und versionierbar (Git).
- Schema klein und n=1-pflegbar (~20 Einträge zum Start).
- Klare Verbindung zu Runtime-Records: jeder Tool-Call erzeugt einen
  `PolicyDecision`-Eintrag mit gematcheter Risk-Klasse.

**Negativ**

- Weiterer Pflege-Punkt für den Nutzer; bei neuen Tools manuell
  klassifizieren.
- Pattern-Matching ist eine eigene kleine Komplexitäts-Quelle
  (Glob-Resolution, Reihenfolge-Sensitivität — Erste-Match-gewinnt
  muss in der Implementation klar sein).
- Catch-all-Patterns (`gh_*`) müssen unter den spezifischeren
  Einträgen stehen, sonst werden die spezifischen nie erreicht.

### Follow-ups

- Implementierungs-Feature für die Pattern-Matching-Logik (eigenes
  F-Feature in v1a, sobald die Adapter implementiert werden).
- Erweiterung um eine `team`-Klasse, sobald Multi-User relevant wird
  (v2+).
- Tool-Risk-Drift-Detection (analog zu F0005): Inventar gegen
  tatsächlich aufgerufene Tools auswerten, nicht klassifizierte
  Tools als Digest-Card melden.

## Referenzen

- ADR-0007 — HITL-Inbox-Kaskade (HITL-Mechanismus konsumiert
  `ApprovalRequest`)
- ADR-0010 — Execution Harness Contract (Sandbox- und Egress-Vertrag)
- ADR-0011 — Runtime Records (`ApprovalRequest`, `PolicyDecision`)
- ADR-0012 — HITL Timeout Semantics
- ADR-0014 — Peer Adapters (`approval=never` baut auf diesem Inventory
  auf)
- `config/execution/tool-risk-inventory.yaml` — normative Config-Datei
- Counter-Review-2026-04-24 — Befund 6 (Tool-Risk-Inventar fehlt)
- OWASP LLM Top 10 — LLM02 (insecure output handling)
- NIST AI RMF — GOVERN-1.1 (risk classification)
