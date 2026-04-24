---
title: Counter-Review — Antwort auf Codex System-Review
date: 2026-04-23
status: draft
reviewer: Claude (Autor der V1-Spec)
responds_to: 2026-04-23-critical-system-review.md
---

# Counter-Review

## Zweck

Punkt-für-Punkt Antwort auf den kritischen System-Review von Codex. Zweck:
Entscheidungslogik pro Befund transparent machen, bevor Spec oder ADRs
geändert werden.

## Ehrlichkeits-Rahmen

- Ich bin Autor der kritisierten V1-Spec und neige zur Selbstverteidigung.
  Der Counter-Review versucht, dieser Verzerrung bewusst entgegenzuhalten.
- Wo ein Befund valide ist, sage ich das ohne Relativierung.
- Pushback nur, wo ich eine inhaltliche Differenz habe — nicht, um mein
  Dokument zu retten.
- Wo die Umsetzung des Befunds V1-Scope sprengt, wird das als bewusste
  Verschiebung markiert, nicht als Ablehnung.

## Zusammenfassung

| Kategorie | Zahl |
|---|---|
| Vollständig zugestimmt | 11 |
| Teilweise zugestimmt, mit Nuance | 4 |
| Pushback (inhaltliche Differenz) | 0 |
| Bewusste Verschiebung (Scope-Grund, nicht Ablehnung) | 1 (Befund 14) |

**Gesamturteil:** Der Codex-Review ist substantiell und fachlich korrekt.
Kein Befund ist Stilkritik. Die vier kritischen Befunde sind echte Lücken,
die vor einer ersten Implementierung geschlossen werden müssen.

## Per-Befund-Position

### Befund 1 — SQLite/DBOS/VPS-Widerspruch (Kritisch)

**Position:** Vollständig zugestimmt.

**Reasoning:** Ich habe in `SPECIFICATION.md §7` „Laptop + VPS: spiegelnde
Instanz" geschrieben und in ADR-0003 „Postgres wird Pflicht, sobald > 1
Prozess gleichberechtigt schreibt". Eine Spiegel-Instanz ist *genau* dieser
Fall. Kein Interpretationsspielraum, kein Detail — ein harter Widerspruch.

**Aktion:** Neuer ADR-0013 `v1-deployment-mode.md`, der drei Betriebsvarianten
klar trennt:
- v0/v1a lokal-only (ein Prozess, SQLite + Litestream).
- v1b read-only Messenger-Bridge (liest via Litestream-Restore, schreibt
  nicht).
- v2+ Postgres als Primärspeicher, sobald eine zweite schreibende Rolle
  existiert.

Spec-Patch in §7 und Appendix A entsprechend.

### Befund 2 — HITL-Timeout-Widerspruch (Kritisch)

**Position:** Vollständig zugestimmt, mit Nuance zur Abandon-Semantik.

**Reasoning:** Die 72h-Abandon-Regel ist meine Eigenentscheidung, die Brief 09
nicht stützt. Brief 09 sagt explizit „Default-Eskalation: kein Timeout; bei
Deadline: Auto-Reject, nie Auto-Approve; Reminder nur für Risiko ≥ medium".
Das habe ich zu pauschal geglättet.

Die „kumulativen" Kriterien sind zusätzlich grammatikalisch gefährlich — sie
können gelesen werden als „alle vier Bedingungen gleichzeitig nötig", was
irreversible High-Risk-Aktionen entschärfen würde. Das ist klar nicht die
Intention, aber die Formulierung erlaubt die Fehlinterpretation.

**Nuance:** Codex schlägt vier Zustände vor
(`waiting_for_approval`, `timed_out_rejected`, `stale_waiting`, `abandoned`).
Ich stimme zu, aber `abandoned` sollte im Runtime-Modell nur durch **explizite
Nutzeraktion** entstehen. Low-risk Wegwerf-Items können eine dokumentierte
Policy haben, aber nie per Default-Timeout.

**Aktion:** Neuer ADR-0012 `hitl-timeout-semantics.md` mit:
- 4 Zustände wie von Codex vorgeschlagen.
- Eskalationskriterien **disjunktiv** (oder-verknüpft), nicht kumulativ.
- Kein Default-72h-Abandon. Stattdessen: Deadline-Semantik optional pro
  Work Item, `timed_out_rejected` bei Ablauf, nie `abandoned` per Timer.
- Irreversible/außenwirksame Aktionen: Approval immer Pflicht, unabhängig
  von Konfidenz.

Spec-Patch in §6.2 und ADR-0007 bekommt ein `Follow-ups`-Verweis auf 0012.

### Befund 3 — Durable Execution zu optimistisch (Kritisch)

**Position:** Vollständig zugestimmt.

**Reasoning:** DBOS liefert Exactly-Once für DB-Steps, At-Least-Once für
externe Effekte (siehe Brief 03). Die Spec hat letzteres nicht adressiert.
Ohne `RunAttempt`-Modell und Idempotency-Keys können Retries doppelte
Git-Commits, doppelte Kommentare oder doppelte LLM-Kosten erzeugen.

**Aktion:** Neuer ADR-0011 `runtime-audit-and-run-attempts.md`, der definiert:
- `Run` ist die fachliche Einheit (1 Work Item → 1 oder mehr Runs).
- `RunAttempt` ist der konkrete Versuch mit Startzeit, Endzeit, Agent,
  Sandbox-Profil, Prompt-Hash, Tool-Allowlist, Exit-Code, Kosten, Logs.
- Jeder externe Effekt bekommt einen Idempotency-Key oder eine
  Nachweisstrategie (z. B. Git-Commit-Hash, GitHub-Operation-ID).
- Post-Flight registriert Artefakte nur mit eindeutigem Attempt-Bezug.
- Wiederholung eines Attempts darf keine externen Effekte duplizieren.

Spec-Patch in §5.7 (Kernobjekte erweitern um Runtime Records).

### Befund 4 — Sandbox operativ unklar (Kritisch)

**Position:** Vollständig zugestimmt.

**Reasoning:** Ich habe die 8-Schichten-MVS als Abstraktion beschrieben, aber
nicht gesagt, wie Agent-CLI-Prozess und Nutz-Code sich zur Isolationsgrenze
verhalten. Das ist der Kern der Isolation — wenn die CLI außerhalb läuft,
hat sie Zugriff auf `~/.claude`, `~/.codex`, SSH-Keys und Shell-Profile.

**Aktion:** Neuer ADR-0010 `execution-harness-contract.md`, der explizit
beschreibt:
- Prozessbaum: welche Prozesse laufen innerhalb welcher Isolation.
- Mount-Tabelle: welche Pfade `rw` / `ro` / `masked` / `tmpfs`.
- Credentials: Secret-Injection-Mechanismus pro Run, keine Env-Vererbung.
- Netzwerk: Proxy-ENV *und* Namespace *und* Egress-Allowlist
  (defense-in-depth).
- Config: welche Host-Konfiguration ist verboten, kopiert oder synthetisch.
- Exit-Vertrag: welche Logs, Artefakte, Kosten zurückgegeben werden.

ADR-0006 bekommt einen `Follow-ups`-Verweis auf 0010 und der Status bleibt
`accepted` (Richtung richtig), der Vertrag lebt in 0010.

### Befund 5 — Budget-Caps `AND`-Semantik (Hoch)

**Position:** Vollständig zugestimmt.

**Reasoning:** Grammatikalisch-logisch falsch. `$2 AND 25 Turns AND 15 min`
liest sich als Und-Bedingung; gemeint war Oder-Bedingung (irgendeine erste
Grenze bricht ab).

**Aktion:** Spec-Patch in §8.3 und ADR-0008-Decision-Abschnitt:
> Task-Run wird abgebrochen, sobald *eine* harte Grenze überschritten ist:
> $2 Kosten **oder** 25 Turns **oder** 15 min Wall-Clock **oder**
> Repeat-Tool-Call-Detector schlägt an.

### Befund 6 — Codex-Approval-Widerspruch (Hoch)

**Position:** Vollständig zugestimmt.

**Reasoning:** Spec sagt `approval=never`, Brief 02 empfiehlt `on-request`
mit Wrapper. Das sind zwei unterschiedliche Architekturen mit sehr
unterschiedlichen Implikationen. Nicht entschieden.

**Entscheidung (für V1):** `approval=never` mit orchestrator-seitiger
Tool-Risk-Klassifikation. Begründung:
- Passt zum Single-Adapter-V1-Ansatz.
- Eliminiert Bridging-Komplexität (native Prompts → ApprovalRequest-
  Objekte) in der ersten Iteration.
- Tool-Allowlist muss ohnehin pro Run erstellt werden (Brief 07,
  „Tool-Use Risk Inventory").

`on-request`-Mode bleibt als v2-Option dokumentiert, aktiviert über ein
neues Profil (nicht default).

**Aktion:** ADR-0004 bekommt einen `Follow-ups`-Abschnitt oder neuer
ADR-0014 `codex-approval-mode-v1.md`. Spec-Patch in §8.5.

### Befund 7 — Fehlender Datenvertrag für Nachvollziehbarkeit (Hoch)

**Position:** Vollständig zugestimmt.

**Reasoning:** Die Spec verspricht Nachvollziehbarkeit, aber das
Datenmodell liefert keine Objekte, die diese Nachvollziehbarkeit tragen.
`RunAttempt`, `AuditEvent`, `ApprovalRequest`, `BudgetLedgerEntry`,
`ToolCallRecord`, `PolicyDecision`, `SandboxViolation` sind alle
„technische Querschnittsobjekte" — sie müssen keine fachlichen Module
werden, brauchen aber Schema, Ownership, Retention.

**Aktion:** ADR-0011 (aus Befund 3) erweitert um diese Objekte. Spec-Patch
in §5.7 als neuer Unterabschnitt „Runtime Records" — abgegrenzt von den
fachlichen Kernobjekten.

### Befund 8 — Zielarchitektur vs. Release-Staging vermischt (Hoch)

**Position:** Vollständig zugestimmt.

**Reasoning:** SPECIFICATION.md §5–10 liest sich als normative V1, aber
Appendix A sagt: v0 nur Schema, v1 nur Durable Single-Loop, Portfolio erst
v2, Governance erst v3. Implementierer weiß nicht, was zu bauen ist.

**Aktion:** Spec-Patch in §5.7 (Kernobjekt-Tabelle bekommt `stage`-Spalte)
und Appendix A. Zusätzlich Option: ein `docs/releases/v0.md`, `v1.md`, `v2.md`,
`v3.md` anlegen. Ich neige zur leichtgewichtigen Variante — `stage`-Spalte in
§5.7 und §6.1 reicht vermutlich, separate Release-Dokumente entstehen erst,
wenn sie Substanz haben.

### Befund 9 — Dual-Adapter in V1 (Mittel)

**Position:** Vollständig zugestimmt.

**Reasoning:** Brief 99 und 15 sagen selbst, dass gleichzeitiger Support
zusätzliche V1-Komplexität ist. Die Spec hätte das als Scope-Entscheidung
festlegen müssen.

**Entscheidung:** Primärer Adapter für v1 = **Claude Code**. Begründung:
- Subagent-Delegation, Skills, MCP, Hooks sind reicher als Codex-Äquivalente
  (Brief 01 vs. 02).
- Claude Code headless `claude -p --output-format json --bare` ist
  strukturiert und stabil dokumentiert.
- Codex-Adapter kommt in v1.x oder v2 als zweiter Adapter, sobald das
  `ExecutionAdapter`-Interface stabil ist.

**Aktion:** Spec-Patch in §5.4 und §8.5. Codex-Integration dokumentiert als
„vorbereitet, nicht V1-Default".

### Befund 10 — Policy als Querschnitt nicht ausführbar (Mittel)

**Position:** Teilweise zugestimmt.

**Reasoning:** Policy als Querschnitt ist richtig. Aber für V1 braucht es
mindestens ein minimales Policy-Modell — sonst wissen wir nicht, welche Tools
erlaubt sind oder wann Approval nötig ist.

**Nuance:** Das volle Modell (`ToolRisk`, `AutonomyTier`, `PolicyDecision`,
`BindingResolution`) kann stufenweise entstehen. V1 braucht:
- `ToolRisk`: statisches Inventar (YAML/TOML) von erlaubten Tools pro
  Work-Item-Typ.
- `PolicyDecision` als Record (Teil der Runtime Records aus ADR-0011).
- Fail-closed-Default: nicht inventarisierte Tools werden denied.

`AutonomyTier` und `BindingResolution` kommen mit v2 (Portfolio) bzw. v3
(Governance).

**Aktion:** Neuer ADR `policy-evaluator-v1.md` (entweder als 0015 oder
eingebettet in ADR-0011 Runtime-Audit). Spec-Patch in §8 („Querschnittliche
Konzepte").

### Befund 11 — Secrets und Identity verharmlost (Mittel)

**Position:** Vollständig zugestimmt.

**Reasoning:** „~50-Zeilen-Teil" im Interaction-Modul unterschätzt die
Sicherheitswirkung.

**Aktion:** Secret-Vertrag in ADR-0010 (Execution Harness Contract) oder
dediziert. Inhalt: Secret-Quelle, erlaubte Scopes, Injection-Mechanismus,
Masking-Regeln, Rotation, Verbot globaler Env-Vererbung, Trennung
interaktiver Nutzer-Logins von Agent-Service-Credentials.

### Befund 12 — Observability zu knapp (Mittel)

**Position:** Vollständig zugestimmt.

**Aktion:** Spec-Patch in §8.4 mit normativem Minimum:
- SQLite-Audit-Tabellen für Domain-Zustandsänderungen (ADR-0011).
- JSONL-Runlog pro Attempt.
- JSONL-Budgetledger pro Tag.
- CLI-Commands `agentctl status`, `agentctl costs today`,
  `agentctl runs inspect`.
- Retention-Policy (angelehnt an Git-Retention für Knowledge).

### Befund 13 — Backup ohne Restore-Drill (Mittel)

**Position:** Vollständig zugestimmt.

**Aktion:** Akzeptanzkriterium in §10 ergänzen:
- Quartalsweiser Restore-Drill.
- Dokumentierter Restore-Befehl.
- Test: Restore auf frischem Host zeigt konsistente Lage.
- Nach Restore: laufende Runs werden `needs_reconciliation` markiert
  (zusätzlicher Run-Zustand).

### Befund 14 — Standards-Promotion Materialisierung (Mittel)

**Position:** Bewusste Verschiebung — nicht Ablehnung.

**Reasoning:** Der Befund ist inhaltlich korrekt (Binding-Compiler nötig, um
`bound` Standards in Agent-Verhalten zu übersetzen). Aber: Standards werden
erst in v3 aktiviert (Brief 15). In v1 gibt es nichts zu materialisieren.
Wenn das Modell jetzt gebaut wird, bauen wir Vorratshaltung.

**Aktion:** ADR-0005 bekommt einen `Follow-ups`-Abschnitt mit Verweis auf
„Binding-Compiler-Spec bei v3-Start". Kein neuer ADR jetzt.

### Befund 15 — Test- und Verifikationsstrategie fehlt (Mittel)

**Position:** Teilweise zugestimmt.

**Reasoning:** Ein vollständiger Teststrategie-Plan ist in einem
Dokumentations-Only-Repo ohne Code Vorratshaltung. Gleichzeitig ist die
Testmatrix für Budget, Sandbox, HITL, Retry, Restore genau richtig — sie
gehört als Akzeptanzkriterium **in die Release-Dokumentation** (v1a, v1b),
nicht in die allgemeine Spec.

**Aktion:** Spec-Patch in §10.3 („Akzeptanzkriterien") mit einer kompakten
V1-Testmatrix. Umfang wie von Codex vorgeschlagen:
- Unit: Policy- und Budget-Entscheidungen.
- Integration: Worktree-Isolation, Egress-Blocking.
- Crash: Prozess stirbt vor Post-Flight.
- Retry: externer Effekt nicht doppelt registriert.
- HITL: Approval überlebt Restart.
- Restore: frischer Host, konsistente Lage.

Keine eigene Teststrategie-ADR.

### Befund 16 — ADR-Status zu final (Niedrig–Mittel)

**Position:** Teilweise zugestimmt.

**Reasoning:** MADR-Tradition erlaubt `accepted` mit Follow-ups — der Status
bezieht sich auf die Richtung, nicht auf implementierungsvollständige
Verträge. Gleichzeitig stimme ich zu, dass der aktuelle Inhalt einiger ADRs
zu wenig Fülle hat und die Lücke offener Verträge verbergen könnte.

**Aktion:** Keine Status-Änderung, aber `Follow-ups`-Abschnitt in den ADRs
0003, 0004, 0006, 0007, 0005 (wo jeweils ein zukünftiger ADR bekannt ist).
Keine neuen ADR-Stati wie `provisional`; MADR definiert Standard-Stati, und
`proposed / accepted / deprecated / superseded` reicht.

## Änderungsplan

In der Reihenfolge, in der ich sie umsetzen würde:

### Phase A — Kritische und hohe Befunde (vor jeder Implementierung)

1. **ADR-0010** `execution-harness-contract.md` (Befund 4 + 11).
2. **ADR-0011** `runtime-audit-and-run-attempts.md` (Befund 3 + 7 + 10).
3. **ADR-0012** `hitl-timeout-semantics.md` (Befund 2).
4. **ADR-0013** `v1-deployment-mode.md` (Befund 1).
5. **Spec-Patch §5.7** — `stage`-Spalte + „Runtime Records"-Unterabschnitt
   (Befund 7 + 8).
6. **Spec-Patch §6.2** — HITL-Zustände und Kriterien (Befund 2).
7. **Spec-Patch §7** — Betriebsmodi klar getrennt (Befund 1).
8. **Spec-Patch §8.2** — Verweis auf ADR-0010 für Harness-Vertrag (Befund 4).
9. **Spec-Patch §8.3** — Budget-Caps unabhängig (Befund 5).
10. **Spec-Patch §8.4** — Observability-Minimum normativ (Befund 12).
11. **Spec-Patch §8.5** — Claude Code als primärer Adapter, Codex Mode
    entschieden (Befund 6 + 9).
12. **Spec-Patch §10** — Akzeptanzkriterien inkl. Restore-Drill (Befund 13 +
    15).
13. **Spec-Patch Appendix A** — Trennung Zielarchitektur / Staging (Befund 8).
14. **`Follow-ups`-Abschnitte** in ADRs 0003, 0004, 0005, 0006, 0007
    (Befund 16 + 14).
15. **CHANGELOG** `v0.1.1` mit Einträgen.

### Phase B — Bewusst verschoben (nicht in diesem Patch)

- Multi-Projekt-Dependencies bleiben v2.
- Zweiter Agent-Adapter bleibt v1.x / v2.
- Standards-Binding-Compiler bleibt v3.
- Messenger/Mail bleibt nach v1-Deployment-Entscheidung.
- Vollständige Teststrategie bleibt, bis Code existiert.

### Phase C — Optional später

- `docs/releases/v0.md`, `v1a.md`, `v1b.md`, `v2.md`, `v3.md` anlegen, sobald
  die jeweilige Stufe Substanz hat. Heute wäre das Vorratshaltung.

## Meta: Was dieser Gegenreview *nicht* ist

- Keine Ablehnung des Codex-Reviews. Das ist kein „aber…"-Dokument.
- Keine defensive Interpretation. Wo ich falsch lag, ist das dokumentiert.
- Keine Autorität — der Spec-Patch wartet auf dein Go.

## Anfrage an dich

Nach Freigabe dieses Counter-Reviews setze ich Phase A um (4 neue ADRs +
Spec-Patches + Follow-ups + CHANGELOG). Phase B und C bleiben bewusst offen
und werden nicht angefasst, bis sie eigene Substanz bekommen.
