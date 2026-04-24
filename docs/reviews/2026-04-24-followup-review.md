---
title: Follow-up-System-Review — Personal Agentic Control System V0.2.0-draft
date: 2026-04-24
status: draft
reviewer: Codex
scope: V0.2.0-draft (Spec, ADRs 0010-0014, Features, Plan, Dispatch-Konfiguration, Meta-Dokumente)
supersedes: null
amends: null
responds_to:
  - docs/reviews/2026-04-23-critical-system-review.md
  - docs/reviews/2026-04-23-counter-review.md
  - Plans/option-3-ich-m-chte-serialized-oasis.md
  - docs/spec/SPECIFICATION.md
  - docs/decisions/0010-execution-harness-contract.md
  - docs/decisions/0011-runtime-audit-and-run-attempts.md
  - docs/decisions/0012-hitl-timeout-semantics.md
  - docs/decisions/0013-v1-deployment-mode.md
  - docs/decisions/0014-peer-adapters-and-cost-aware-routing.md
  - docs/features/README.md
  - docs/features/F0001-sqlite-schema-core-objects.md
  - docs/features/F0002-work-add-cli.md
  - docs/features/F0003-cost-aware-routing-stub.md
  - docs/features/F0004-benchmark-awareness-manual-pull.md
  - docs/plans/project-plan.md
  - config/dispatch/model-inventory.yaml
  - config/dispatch/routing-pins.yaml
  - CHANGELOG.md
  - GLOSSARY.md
  - AGENTS.md
  - .claude/agents/spec-reviewer.md
---

# Follow-up-System-Review — Personal Agentic Control System V0.2.0-draft

## Executive Summary

V0.2.0-draft ist ein echter Fortschritt gegenüber V0.1.0-draft. Die neue Spec
ist deutlich klarer, die drei stärksten neuen Dokumente (`ADR-0010`,
`ADR-0011`, `ADR-0013`) adressieren reale Architektur- und
Betriebswidersprüche, und der Schritt von einer impliziten Zielarchitektur zu
einer dokumentierten Stage-Logik ist substanziell. Die Architektur ist damit
nicht mehr an denselben acht Stellen blockiert wie gestern.

Trotzdem schließt V0.2 meine acht priorisierten Alt-Befunde **nicht**
vollständig. Mein Urteil für Achse A lautet:

- **geschlossen:** 2 von 8
- **teilweise geschlossen:** 6 von 8
- **offen:** 0 von 8

Die stärkste Verbesserung liegt in der Operationalisierung: Sandbox,
Deployment-Modi und Runtime-Records sind jetzt als Verträge formuliert. Die
schwächste Stelle ist die Konsistenz zwischen den neuen Dokumenten und den
alten, weiterhin `accepted` markierten ADRs. Mehrere Vollschließungen, die der
Counter-Review angekündigt hat, sind im Repo **nicht** als saubere
Normkonsistenz gelandet.

Zu Option 3: Die Entscheidung für Claude Code und Codex CLI als Peer-Adapter
ist als Dokumentationsentscheidung vertretbar. Das eigentliche Problem ist
nicht, dass das `ExecutionAdapter`-Interface inline in ADR-0014 lebt; das ist
für zwei Adapter noch tragfähig. Das Problem ist, dass ADR-0014 gleichzeitig
vier Dinge bündelt: Peer-Stance, Interface, Routing-Policy und
Codex-Approval-Mode. Dazu kommt eine inhaltliche Schieflage: formal sind beide
Peers, operativ ist Claude Code im `pinned`-Default weiterhin die faktische
Primärroute.

Die empirische Symbiose-Pivot ist **richtungsmäßig** plausibel. Die Abkehr von
Task-Class-Specializer und Cross-Model-Review ist besser begründet als der
ursprüngliche Entwurf. Aber die stärksten quantitativen Sprünge in Appendix A
stützen sich an entscheidenden Stellen auf Tier-2-/Sekundärquellen und auf
einen blogbasierten Harness-Vergleich. Das reicht, um überkomplexe
„Symbiose“-Mechaniken zu verwerfen. Es reicht **nicht**, um eine automatische
Umschaltung in `cost-aware` nach „5 Pins oder 4 Wochen“ als empirisch solide
zu behaupten.

Der Minimal-Scope ist insgesamt näher an einer proportionalen Single-User-V1
als V0.1, aber an einer Stelle unterdimensioniert: F0003 und F0004 setzen
Runtime- und Schema-Artefakte voraus, für die im aktuellen Feature-Set kein
klarer Liefer-Slice existiert. V0.2 ist also architektonisch besser, aber noch
nicht dokumentationsseitig „scharf genug“, um die hohen Befunde als erledigt zu
verbuchen.

Kurzurteil:

- **Architekturqualität:** klar verbessert
- **Vollständigkeit der Reparatur:** unvollständig
- **Option-3-Umsetzung:** tragfähig, aber nicht sauber genug getrennt
- **Empirische Pivot:** vernünftig im Trend, überpointiert in der Sicherheit
- **V1-Proportionalität:** deutlich besser, aber mit zu dünnem Runtime-Slice

## Quellenbasis

Der Review basiert primär auf lokalen Dokumenten. Gelesen wurden:

- die 12 vom Nutzer vorgegebenen Artefaktgruppen
- zusätzlich zur Konsistenzprüfung: `docs/decisions/0004-headless-agents-pydantic-ai.md`
- zusätzlich zur Konsistenzprüfung: `docs/decisions/0006-eight-layer-sandbox-mvs.md`
- zusätzlich zur Konsistenzprüfung: `docs/decisions/0007-inbox-hitl-cascade.md`
- zusätzlich zur Konsistenzprüfung: `docs/decisions/0008-four-scope-budget-gate.md`
- zusätzlich zur Konsistenzprüfung: relevante Stellen aus
  `docs/research/02-codex-cli.md`

Es wurde **kein externer Web-Check** als Bewertungsgrundlage durchgeführt.
Zeitabhängige Aussagen in Plan-Appendix A, `model-inventory.yaml` und den
Benchmark-Ankern sind daher in diesem Review nur gegen die lokalen Dokumente
geprüft, nicht gegen aktuelle Primärquellen revalidiert.

## Bewertungsmaßstab

- **Kritisch:** kann zu falscher Implementierungsrichtung, doppelten externen
  Effekten, Sicherheitsbruch, Kosten-Runaway oder einem falschen V1-Scope
  führen.
- **Hoch:** gefährdet Kernziele von V1 oder erzeugt eine normative
  Mehrdeutigkeit, die vor Implementierung geklärt sein sollte.
- **Mittel:** erhöht Reibung, Drift, Wartungskosten oder Fehldeutung bei
  späterer Umsetzung.
- **Niedrig:** Klarheits- oder Dokuqualitätsthema ohne direkte
  Architekturblockade.

## Was V0.2 stark macht

### 1. Die Spec ist nicht mehr bloß ein schönes Zielbild

V0.1 hatte gute Architekturintuition, aber zu viele weiche Stellen. V0.2
landet mit `ADR-0010`, `ADR-0011`, `ADR-0012` und `ADR-0013` genau die
Vertragsflächen, die vorher nur behauptet waren:

- operativer Sandbox-Vertrag
- Runtime-Records für Audit und Retries
- saubere HITL-Timeout-Semantik
- explizite Deployment-Modi

Das ist der richtige Reparaturvektor.

### 2. Die SQLite/VPS/Postgres-Frage ist jetzt dokumentierbar entscheidbar

`docs/spec/SPECIFICATION.md:357-381` und
`docs/decisions/0013-v1-deployment-mode.md:39-79` trennen lokal-only,
read-only Bridge und Postgres-Schwelle klar. Das beseitigt den schärfsten
Betriebswiderspruch aus V0.1.

### 3. Die Symbiose-Pivot hat unnötige Komplexität abgeschnitten

Appendix A verwirft Task-Class-Specializer, Kendall-τ-Disagreement und
Cross-Model-Review. Das ist architektonisch gesund. Selbst wenn einzelne
quantitative Claims noch nachzuschärfen sind, ist die qualitative Bewegung
richtig: weniger Dispatch-Mathematik, mehr bewusst begrenzte Policy.

### 4. Das Feature-File-Pattern ist für Solo-V1 grundsätzlich proportional

`docs/features/README.md:16-54` hält Frontmatter und Lifecycle klein. Die
Regel „`done` nur durch den Nutzer“ ist diszipliniert, ohne in
Prozessbürokratie zu kippen. Für ein Single-User-Dokumentationsrepo ist das
vernünftiger als ein umfassendes Ticket-System.

### 5. Die neue Spec trennt Zielarchitektur und Release-Stages explizit

`docs/spec/SPECIFICATION.md:17-19` und `:635-682` machen die vorher fehlende
Trennung sichtbar. Sie ist noch nicht repo-weit sauber durchgezogen, aber der
richtige Strukturentscheid ist jetzt da.

## Bewertung der 8 Befunde aus Achse A

### Befund 1 — Kritisch: V1-Betriebsmodus widerspricht sich bei SQLite, DBOS und VPS

**Status: geschlossen.**

Der Kernwiderspruch aus V0.1 ist in V0.2 aufgelöst. Die Spec trennt nun
explizit:

- `v1a` lokal-only (`docs/spec/SPECIFICATION.md:357-365`)
- `v1b` lokal + read-only Bridge (`docs/spec/SPECIFICATION.md:366-374`)
- `v2+` Postgres bei zweiter schreibender Rolle
  (`docs/spec/SPECIFICATION.md:375-381`)

ADR-0013 verdoppelt genau diese Grenze normativ und liefert zusätzlich eine
Entscheidungsregel pro Szenario
(`docs/decisions/0013-v1-deployment-mode.md:39-79`).

Das ist konsistent mit dem, was der Counter-Review angekündigt hat
(`docs/reviews/2026-04-23-counter-review.md:51-59`). An dieser Stelle wurde
die angekündigte Reparatur tatsächlich umgesetzt.

### Befund 2 — Kritisch: HITL-Timeout-Semantik ist widersprüchlich und potenziell unsicher

**Status: teilweise geschlossen.**

Die **gefährliche Kernsemantik** ist repariert:

- vier Zustände statt pauschalem 72h-Abandon
  (`docs/decisions/0012-hitl-timeout-semantics.md:41-49`)
- disjunktive Eskalationskriterien statt „kumulativ“
  (`docs/decisions/0012-hitl-timeout-semantics.md:50-66`)
- kein Default-Auto-Abandon mehr in der Spec
  (`docs/spec/SPECIFICATION.md:328-339`)

Damit ist der kritische Fehlanreiz aus V0.1 weitgehend beseitigt.

Nicht sauber geschlossen ist der Befund trotzdem aus zwei Gründen:

Erstens bleibt die Zustandsmodellierung inkonsistent. Die Flow-Beschreibung
arbeitet mit `waiting_for_approval`, `stale_waiting` und
`timed_out_rejected` (`docs/spec/SPECIFICATION.md:332-339`), die
Lifecycle-Tabelle modelliert das Work Item aber weiterhin nur als
`... → waiting/blocked → completed/abandoned`
(`docs/spec/SPECIFICATION.md:295-299`). Die Zustände existieren also im
Hauptfluss, aber nicht im Lebenszyklusmodell.

Zweitens ist der alte Widerspruch in ADR-0007 dokumentarisch nicht sauber
entwertet. ADR-0007 steht weiterhin als `accepted` mit
`72 h -> auto-abandoned` und „Kumulativ“
(`docs/decisions/0007-inbox-hitl-cascade.md:37-52`). Die Spec markiert zwar,
dass ADR-0012 präzisiert (`docs/spec/SPECIFICATION.md:527`), aber der
Counter-Review hatte explizit einen Follow-up-Verweis in ADR-0007 angekündigt
(`docs/reviews/2026-04-23-counter-review.md:81-89`). Dieser Verweis ist im
Repo nicht gelandet.

Urteil: Die operative Gefahr ist weitgehend entschärft. Die normative
Eindeutigkeit ist es noch nicht.

### Befund 3 — Kritisch: Durable Execution wird zu stark als gelöst dargestellt

**Status: teilweise geschlossen.**

V0.2 hat den Befund substanziell bearbeitet:

- `RunAttempt`, `AuditEvent`, `ApprovalRequest`, `BudgetLedgerEntry`,
  `ToolCallRecord`, `PolicyDecision`, `SandboxViolation` stehen jetzt als
  Runtime-Records in der Spec (`docs/spec/SPECIFICATION.md:273-289`)
- ADR-0011 beschreibt Persistenz, Beziehungen und Idempotency-Keys
  (`docs/decisions/0011-runtime-audit-and-run-attempts.md:41-94`)
- die Testmatrix fordert explizit Retry- und Restore-Verhalten
  (`docs/spec/SPECIFICATION.md:569-581`)

Das ist ein großer Fortschritt gegenüber V0.1.

Vollständig geschlossen ist der Befund trotzdem nicht. Der verbleibende
Kernfehler liegt im Idempotenzmodell selbst. ADR-0011 sagt:

- vor Ausführung prüft der Orchestrator, ob ein `ToolCallRecord` mit demselben
  `idempotency_key` existiert
  (`docs/decisions/0011-runtime-audit-and-run-attempts.md:85-87`)
- danach seien Dual-Write-Fehler konstruktiv ausgeschlossen, weil Checkpoints
  und Runtime-Record-Writes in derselben DB-Transaktion liegen
  (`docs/decisions/0011-runtime-audit-and-run-attempts.md:89-94`)

Das schließt aber **nicht** die Crash-Lücke „externer Effekt passiert, Prozess
stirbt vor Persistierung des `ToolCallRecord`“. Genau in diesem Fenster hilft
ein lokal gespeicherter Key nicht, wenn der Effekt bereits bei GitHub, Slack
oder Mail ausgelöst wurde. Für natürliche Idempotenzfälle wie
Datei-Write/Commit ist das weniger schlimm; für `create comment`-ähnliche
Side-Effects bleibt die Duplikationsklasse bestehen.

Zusätzlich ist die Recovery-Semantik noch nicht rund modelliert. Die Testmatrix
erwartet nach Restore den Zustand `needs_reconciliation`
(`docs/spec/SPECIFICATION.md:579-580`), der im Run-Lifecycle gar nicht
existiert (`docs/spec/SPECIFICATION.md:297`).

Der Counter-Review hat hier Vollschließung behauptet
(`docs/reviews/2026-04-23-counter-review.md:91-109`). Das halte ich für zu
stark. V0.2 liefert die **richtige Richtung und das richtige Objektmodell**,
aber noch keinen vollständig belastbaren Vertrag für externe Effekte.

### Befund 4 — Kritisch: Sandbox-Grenze ist konzeptionell richtig, aber operativ unklar

**Status: geschlossen.**

ADR-0010 liefert genau den fehlenden operativen Vertrag:

- Agent-CLI läuft **innerhalb** der Sandbox
  (`docs/decisions/0010-execution-harness-contract.md:42-45`)
- explizite Mount-Tabelle
  (`docs/decisions/0010-execution-harness-contract.md:46-56`)
- keine Env-Vererbung, filebasierte Secret-Injection
  (`docs/decisions/0010-execution-harness-contract.md:57-64`)
- Netzwerk-Default `none`, opt-in Proxy-Allowlist
  (`docs/decisions/0010-execution-harness-contract.md:65-74`)
- strukturierter Exit-Vertrag
  (`docs/decisions/0010-execution-harness-contract.md:87-100`)

Die Spec verweist an der richtigen Stelle auf diesen Vertrag
(`docs/spec/SPECIFICATION.md:394-409`). Genau diese Punkte hatte der
Vor-Review als fehlend benannt. Auf Dokumentationsebene ist der Befund damit
geschlossen.

### Befund 5 — Hoch: Budget-Caps haben missverständliche `AND`-Semantik

**Status: teilweise geschlossen.**

Die Spec ist korrigiert:

- `Task (Run) | $2 oder 25 Turns oder 15 min`
  (`docs/spec/SPECIFICATION.md:413-421`)

Das Problem ist die Normkonsistenz. ADR-0008 steht weiterhin unverändert auf

- `Task (Run) | $2 AND 25 Turns AND 15 min Wall-Clock`
  (`docs/decisions/0008-four-scope-budget-gate.md:35-40`)

Das ist nicht bloß ein Schönheitsfehler. Der Counter-Review hatte ausdrücklich
angekündigt, **Spec und ADR-0008** zu patchen
(`docs/reviews/2026-04-23-counter-review.md:141-145`). Im Repo ist aber nur
die Spec korrigiert, nicht die alte ADR.

Urteil: Die fachlich richtige Semantik ist jetzt sichtbar, aber die alte,
weiterhin `accepted` markierte ADR widerspricht ihr weiterhin. Das ist keine
Vollschließung.

### Befund 6 — Hoch: Codex-Approval-Policy widerspricht dem Research-Harness

**Status: teilweise geschlossen.**

Die positive Seite zuerst: V0.2 trifft jetzt tatsächlich eine Entscheidung.
ADR-0014 legt `approval=never` für Codex CLI fest
(`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:161-174`).
Damit ist die frühere Schwebe „`never` oder `on-request`?“ beendet.

Teilweise bleibt der Befund aber offen, weil die gewählte Architektur ihre
eigene Sicherheitsvoraussetzung noch nicht normativ liefert. ADR-0014 sagt
selbst:

- HITL-Gates werden orchestrator-seitig über ein Tool-Risk-Inventar gezogen
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:168-170`)
- das Tool-Risk-Inventar muss präzise sein
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:203-204`)

Im aktuellen Repo gibt es dafür aber **kein** entsprechendes normatives
Artefakt. Es gibt `PolicyDecision` als Runtime-Record
(`docs/spec/SPECIFICATION.md:284`), aber weder ein Tool-Risk-Schema noch eine
fail-closed Policy-Definition, noch eine konkrete Konfigurationsquelle
vergleichbar zu `model-inventory.yaml` oder `routing-pins.yaml`.

Der Counter-Review hat hier Vollschließung angekündigt
(`docs/reviews/2026-04-23-counter-review.md:146-166`). Mein Urteil ist
strenger: Die Richtungsentscheidung ist gefallen, der Sicherheitsunterbau
dahinter ist noch zu implizit.

### Befund 7 — Hoch: Nachvollziehbarkeit ist Ziel, aber kein vollständiger Datenvertrag

**Status: teilweise geschlossen.**

Hier ist V0.2 klar besser:

- Runtime-Records sind jetzt als eigener Layer normativ
  (`docs/spec/SPECIFICATION.md:273-289`)
- Observability nennt SQLite-Audit, JSONL-Runlog und JSONL-Budgetledger
  (`docs/spec/SPECIFICATION.md:431-443`)
- ADR-0011 trennt Technik-Querschnitt von Domain-Objekten
  (`docs/decisions/0011-runtime-audit-and-run-attempts.md:21-39`)

Trotzdem ist der Datenvertrag noch nicht vollständig sauber.

Erstens fällt `DispatchDecision` aus dem Raster. Die Spec führt es als
Runtime-Record (`docs/spec/SPECIFICATION.md:286`), ADR-0014 baut Routing und
Retries darauf auf (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:157-159`),
aber ADR-0011 listet es **nicht** in der Tabelle „Neue Runtime-Record-Typen“
(`docs/decisions/0011-runtime-audit-and-run-attempts.md:43-51`). Es taucht nur
im Beziehungsblock auf (`docs/decisions/0011-runtime-audit-and-run-attempts.md:68-69`).
Genau dort bleibt also ein technisches Objekt halb beschrieben.

Zweitens ist die Frage „welcher Record ist final, welcher vorläufig?“ nicht
durchgängig geklärt. Das sieht man besonders bei `DispatchDecision`, wenn das
Budget-Gate den Kandidaten noch einmal umbiegt
(`docs/spec/SPECIFICATION.md:318-320`, `:423-426`, `:501-503`).

Drittens ist Portabilität noch Follow-up, nicht Vertrag:
`docs/decisions/0011-runtime-audit-and-run-attempts.md:110-115`.

Ich widerspreche daher der Vollschließungsformel aus dem Counter-Review
(`docs/reviews/2026-04-23-counter-review.md:168-181`). Der fehlende
Datenvertrag ist nicht mehr grob, aber er ist auch noch nicht rund.

### Befund 8 — Hoch: V1-Zielarchitektur und Release-Staging sind vermischt

**Status: teilweise geschlossen.**

Die Verbesserung ist sichtbar:

- die Spec trennt Zielarchitektur und Release-Stages explizit
  (`docs/spec/SPECIFICATION.md:17-19`)
- Appendix A beschreibt `v0`, `v1a`, `v1b`, `v2`, `v3`
  (`docs/spec/SPECIFICATION.md:640-677`)
- die Kernobjekte tragen eine `Stage`-Spalte
  (`docs/spec/SPECIFICATION.md:254-271`)

Das reicht aber noch nicht für repo-weite Staging-Klarheit.

Das Hauptproblem: Die Stage-Taxonomie ist zwischen den Artefakten nicht
kohärent.

- die Spec benutzt `v1a`, `v1b` und zusätzlich einen separaten
  Aktivierungsschritt für `cost-aware`
  (`docs/spec/SPECIFICATION.md:649-667`)
- der Project Plan benutzt ebenfalls `v1a` und `v1b`
  (`docs/plans/project-plan.md:19-25`)
- Feature-Frontmatter erlaubt aber nur `v0 | v1 | v2 | v3`
  (`docs/features/README.md:18-26`)
- F0003 und F0004 tragen deshalb nur `stage: v1`
  (`docs/features/F0003-cost-aware-routing-stub.md:2-7`,
  `docs/features/F0004-benchmark-awareness-manual-pull.md:2-7`)

Damit ist zwar klarer **dass** es Stages gibt, aber nicht mehr sauber
codierbar, **welche** v1-Unterstufe ein Feature tatsächlich bedient.

Der Counter-Review meinte, `stage`-Spalte plus Appendix A reichten vermutlich
(`docs/reviews/2026-04-23-counter-review.md:191-195`). Ich halte das für nur
teilweise richtig: in der Spec ja, repo-weit nein.

## Zentrale neue Befunde aus Achsen B-F

### Neuer Befund 1 — Hoch: Peer-Adapter-Stance ist formal symmetrisch, operativ aber asymmetrisch

ADR-0014 behauptet explizit:

- „Kein Vorrang, keine `Primary`-Rolle“
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:52-57`)

Im selben ADR wird für den V1-Default im `pinned`-Modus aber festgelegt:

- globaler Default `adapter=claude-code`
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:126-130`)

Die Spec übernimmt diese Logik:

- `pinned`-Mode ist V1-Default
  (`docs/spec/SPECIFICATION.md:489-490`, `:649-653`)

Das ist ein echter Architekturwiderspruch, nicht bloß eine Präferenzfrage.
Wenn der Cold-Start-Traffic ohne Pin immer zu Claude Code geht, dann existiert
operativ sehr wohl eine Primärrolle.

**Warum das relevant ist**

- Option 3 sollte gerade die frühere Primary-Entscheidung überschreiben.
- Messungen zum „Adapter-Mix“ werden verzerrt, wenn einer der beiden Peers
  schon im Default bevorzugt wird.
- „Peers“ wäre dann eher eine Interface-Eigenschaft als eine reale
  Betriebsentscheidung.

**Empfehlung**

- Entweder offen dokumentieren: „Peers im Vertrag, Claude Code als
  V1-Default im `pinned`-Mode“.
- Oder den Default von einem expliziten Nutzer-Setting abhängig machen.
- Oder `pinned` so definieren, dass immer **ein expliziter** globaler Default
  im Config-File gesetzt wird, nicht hartcodiert im ADR.

### Neuer Befund 2 — Hoch: `DispatchDecision` friert zu früh oder zu unklar

Die Spec beschreibt diesen Ablauf:

- Schritt 2: Dispatcher erzeugt `DispatchDecision`
  (`docs/spec/SPECIFICATION.md:311-317`)
- Schritt 3: Budget-Gate kann den Dispatcher zwingen, einen günstigeren
  Kandidaten zu wählen (`docs/spec/SPECIFICATION.md:423-426`)
- später heißt es: `DispatchDecision` sei pro RunAttempt `frozen`
  (`docs/spec/SPECIFICATION.md:501-503`)

ADR-0014 beschreibt dasselbe Muster:

- Dispatch entscheidet zuerst (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:121-146`)
- dann Gate-Check mit möglicher Rewahl
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:148-155`)
- gleichzeitig soll `DispatchDecision` frozen sein
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:157-159`)

Unklar bleibt damit:

- friert der erste Router-Kandidat ein?
- oder erst der budgetbereinigte Endkandidat?
- gibt es einen vorläufigen und einen finalen Dispatch-Record?

**Warum das relevant ist**

- Audit und Retry-Semantik hängen daran.
- Sonst ist unklar, ob ein Retry denselben Kandidaten oder den
  budgetkorrigierten Kandidaten wiederholen muss.
- Die Auswertung „Pin vs. Cost-Aware vs. Gate Override“ bleibt unscharf.

**Empfehlung**

- Zwei Begriffe einführen: `DispatchCandidate` und `DispatchDecisionFinal`.
- Nur der finale, gate-geprüfte Kandidat wird pro RunAttempt `frozen`.
- Gate-induzierte Rewahl muss als eigener `PolicyDecision`-Record sichtbar
  werden.

### Neuer Befund 3 — Hoch: ADR-0011 übertreibt die Stärke seines Idempotenzversprechens

ADR-0011 ist der richtige Schritt, formuliert seine Tragweite aber zu stark.
Der Text suggeriert:

- Idempotency-Key-Check vor Ausführung
  (`docs/decisions/0011-runtime-audit-and-run-attempts.md:74-87`)
- Checkpoints und Writes in einer Transaktion
  (`docs/decisions/0011-runtime-audit-and-run-attempts.md:89-94`)

Das löst jedoch nicht die Lücke „Side-Effect erfolgreich, Persistierung des
ToolCallRecord scheitert“. Genau dort entsteht die klassische
at-least-once-Duplikationsklasse.

**Warum das relevant ist**

- GitHub-Kommentare, PR-Create, Slack/Mail haben ohne providerseitigen
  Idempotency-Support keine lokale Exactly-Once-Garantie.
- Die ADR liest sich stärker gelöst, als sie es technisch ist.
- Daraus kann eine zu optimistische Implementierung folgen.

**Empfehlung**

- Im ADR explizit zwischen drei Effektklassen unterscheiden:
  natürliche Idempotenz, providerseitige Idempotenz, nur lokale
  De-Duplizierung.
- Für die dritte Klasse einen Reconciliation-Mechanismus definieren.
- Den Satz „Dual-Write-Fehler konstruktiv ausgeschlossen“ auf DB- und
  Post-Flight-Writes begrenzen, nicht auf externe APIs verallgemeinern.

### Neuer Befund 4 — Hoch: Stage- und Lifecycle-Taxonomie ist über Repo-Grenzen hinweg inkonsistent

Die Inkonsistenz betrifft nicht nur Stages, sondern auch State-Machines.

Bei HITL:

- Work Item Lifecycle kennt `waiting/blocked`
  (`docs/spec/SPECIFICATION.md:295-299`)
- Flow nutzt `waiting_for_approval`, `stale_waiting`,
  `timed_out_rejected` (`docs/spec/SPECIFICATION.md:328-339`)

Bei Recovery:

- Testmatrix verlangt `needs_reconciliation`
  (`docs/spec/SPECIFICATION.md:579-580`)
- Run Lifecycle kennt diesen Zustand nicht
  (`docs/spec/SPECIFICATION.md:297`)

Bei Stages:

- Spec/Plan arbeiten mit `v1a`, `v1b`, `cost-aware`-Aktivierung
  (`docs/spec/SPECIFICATION.md:649-667`,
  `docs/plans/project-plan.md:19-25`, `:76-79`)
- Feature-System kennt nur `v1`
  (`docs/features/README.md:18-26`)

**Warum das relevant ist**

- State-Machines sind Implementierungsverträge.
- Feature-Frontmatter soll genau das Release-Staging operationalisieren.
- Wenn beide Taxonomien auseinanderlaufen, droht inkonsistente Umsetzung bei
  CLI, DB-Schema und Tests.

**Empfehlung**

- Eine einzige State-Liste pro Domain-Objekt normativ machen.
- `needs_reconciliation` entweder in den Run-Lifecycle aufnehmen oder in der
  Testmatrix anders benennen.
- Entweder Feature-Stages auf `v1a`/`v1b` erweitern oder die Spec auf
  `v1`-Oberstufen zurückfalten und Unterstufen nur im Plan führen.

### Neuer Befund 5 — Mittel bis Hoch: Der Minimal-Scope ist an der Runtime-Basis unterdimensioniert

Der Plan hält den Scope klein. Das ist gut. Gleichzeitig setzen F0003 und
F0004 bereits Infrastruktur voraus, die im aktuellen Feature-Set nicht als
lieferbarer Slice auftaucht.

Beispiele:

- F0003 erzeugt `DispatchDecision`
  (`docs/features/F0003-cost-aware-routing-stub.md:22-27`)
- F0003 erwartet Persistenz als Runtime Record oder JSONL
  (`docs/features/F0003-cost-aware-routing-stub.md:53-54`)
- F0004 erwartet `Evidence(kind=benchmark)` und
  `Artifact(kind=benchmark_raw)`
  (`docs/features/F0004-benchmark-awareness-manual-pull.md:33-37`,
  `:60-62`)
- der Project Plan sagt aber selbst, dass ADRs 0010–0013 erst später eigene
  Feature-Files bekommen (`docs/plans/project-plan.md:39-41`)

F0001 deckt nur vier v0-Tabellen ab
(`docs/features/F0001-sqlite-schema-core-objects.md:22-30`).

Das bedeutet: V1-Features hängen von einem v1-Schema- und Runtime-Slice ab,
der im aktuellen Minimal-Scope nicht als eigenes Feature sichtbar ist.

**Warum das relevant ist**

- Die Feature-Methode soll gerade lieferbare Slices explizit machen.
- Unsichtbare Infrastruktur-Slices unterlaufen diesen Anspruch.
- Daraus entstehen entweder implizite Zusatzarbeiten oder unklare
  Akzeptanzkriterien.

**Empfehlung**

- Entweder ein einziges Infrastruktur-Feature für `Run`, `Artifact`,
  `Evidence` und Runtime-Records ergänzen.
- Oder F0003/F0004 so zurückschneiden, dass sie nicht schon DB-Schema und
  Runtime-Persistenz voraussetzen.

### Neuer Befund 6 — Mittel: Cross-Ref- und Meta-Dokumente sind nicht auf V0.2 nachgezogen

V0.2 führt neue Feature- und Review-Disziplin ein. Ausgerechnet die
Meta-Dokumente ziehen aber noch V0.1-Schatten mit:

- `AGENTS.md` sagt weiterhin „Stand: V0.1.0-draft“
  (`AGENTS.md:12`)
- `.claude/agents/spec-reviewer.md` sagt weiterhin
  „wir sind in V0.1.0-draft ohne Code“
  (`.claude/agents/spec-reviewer.md:45-46`)
- derselbe Spec-Reviewer spricht von „alle 7 Invarianten“
  (`.claude/agents/spec-reviewer.md:50`), listet aber 8
  (`.claude/agents/spec-reviewer.md:13-29`)

Dazu kommen kleinere Cross-Ref-Drifts:

- F0001 verweist auf Runtime Records „(F0004-ff.)“
  (`docs/features/F0001-sqlite-schema-core-objects.md:17-18`), obwohl F0004
  Benchmark-Awareness ist
- Feature-Index und Frontmatter sind nicht überall deckungsgleich, etwa bei
  F0001s `adr_refs`
  (`docs/features/F0001-sqlite-schema-core-objects.md:2-7`,
  `docs/features/README.md:77-82`)

**Warum das relevant ist**

- Gerade Agent-Tools lesen `AGENTS.md` und Reviewer-Meta.
- Wenn diese Dokumente zurückhängen, tragen sie falsche Repo-Annahmen in
  spätere Arbeit.
- Das Feature-Pattern lebt oder stirbt an zuverlässiger Kleinkohärenz.

**Empfehlung**

- Meta-Dokumente als Teil des normativen V0.2-Patches behandeln.
- Kleine Cross-Ref-Fehler nicht als „später“ markieren; hier entsteht
  unnötige Drift am billigsten zu vermeidenden Ort.

### Neuer Befund 7 — Mittel: Die empirische Pivot stützt die Verwerfung von Überbau, aber nicht den Auto-Switch

Appendix A ist in seiner **qualitativen Stoßrichtung** plausibel:

- Task-Class-Specializer wird als zu spekulativ verworfen
  (`Plans/option-3-ich-m-chte-serialized-oasis.md:279`)
- Cross-Model-Review wird aus Bias-Gründen verworfen
  (`Plans/option-3-ich-m-chte-serialized-oasis.md:257-265`, `:280`)
- Cost-Aware-Routing wird als Minimalform empfohlen
  (`Plans/option-3-ich-m-chte-serialized-oasis.md:271-283`)

Aber die Beleglage ist für die stärkste operative Folgerung zu dünn:

- die wichtigsten Differenzierungszahlen kommen aus Sekundärquellen
  (`Plans/option-3-ich-m-chte-serialized-oasis.md:287-297`)
- der Harness-Delta-Claim `±16 pp` stützt sich auf eine einzelne Tier-2-Quelle
  (`Plans/option-3-ich-m-chte-serialized-oasis.md:253`, `:296`)
- die RouteLLM-Aussage bezieht sich auf Modellrouting auf MT Bench,
  nicht auf Headless-Agent-CLI-Routing zwischen Claude Code und Codex CLI
  (`Plans/option-3-ich-m-chte-serialized-oasis.md:273`, `:293`)
- trotzdem wird daraus eine automatische Aktivierung nach „5 Pins oder
  4 Wochen“ abgeleitet
  (`docs/spec/SPECIFICATION.md:491-499`, `:664-667`,
  `docs/plans/project-plan.md:76-79`)

**Warum das relevant ist**

- Hier springt das Repo von „empirisch gegen Overengineering“ zu
  „empirisch genug für Auto-Umschaltung“.
- Das erste ist gut gedeckt. Das zweite ist eine zusätzliche Inferenz.
- Ohne lokale Kalibrierung kann der Router in einen teureren oder nur formal
  anderen Modus wechseln, ohne dass sich Qualität verbessert.

**Empfehlung**

- `cost-aware` nicht zeit- oder pinbasiert automatisch aktivieren.
- Stattdessen: explizites Nutzer-Opt-in oder Aktivierung erst nach lokaler
  Qualitäts-/Kostenmessung.
- In Appendix A klar zwischen „gut belegt“ und „Architekturableitung“ trennen.

## Perspektivenreview

### Architekturperspektive

Stärken:

- V0.2 hat die richtige Reparaturreihenfolge gewählt: erst Verträge, dann
  Erweiterungen.
- `ADR-0010`, `ADR-0011` und `ADR-0013` machen aus Prinzipien operative
  Schnittstellen.
- Das Inline-`ExecutionAdapter`-Interface ist mit fünf Verben klein genug, um
  bei zwei Adaptern noch tragfähig zu sein
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:59-89`).

Risiken:

- ADR-0014 bündelt zu viele Entscheidungen an einer Stelle
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:24-27`,
  `:59-174`).
- Die Peer-Stance ist formal symmetrisch, operativ aber asymmetrisch.
- Dispatch, Budget und Retry greifen an einer Stelle ineinander, ohne dass die
  finalen Record-Grenzen ganz scharf wären.

Bewertung: **deutlich stärker als V0.1, aber ADR-0014 ist bereits an der Grenze
des noch gut haltbaren Zuschnitts.**

### Sicherheitsperspektive

Stärken:

- Der Harness-Vertrag ist die größte Sicherheitsverbesserung des gesamten
  Patches.
- Prozessgrenze, Masking von Host-Config, keine Env-Vererbung und
  Netzwerk-Default `none` sind richtig priorisiert
  (`docs/decisions/0010-execution-harness-contract.md:42-74`).
- Die Doku bleibt bei „native Sandbox ist nicht die Grenze“.

Risiken:

- `approval=never` ist nur so sicher wie das nicht sauber definierte
  Tool-Risk-Modell.
- Der geheimnisarme Satz in der Spec, Identität und Secrets seien ein
  „~50-Zeilen-Teil“, steht weiter im Repo
  (`docs/spec/SPECIFICATION.md:170-172`).
- Protected Paths und Orchestrator-Policy sind auf der Dokumentationsebene
  noch nicht dasselbe wie ein ausführbares Fail-Closed-Modell.

Bewertung: **die Sicherheitsarchitektur ist jetzt ernsthaft, aber nicht an
jeder Stelle bis zur letzten Policy-Kante durchgezogen.**

### Betriebsperspektive

Stärken:

- Die Verteilungssicht ist jetzt praktisch brauchbar.
- `v1a` als Default schützt vor voreiligem VPS-Overhead.
- Read-only Bridge ist als Zwischenstufe sauber markiert.

Risiken:

- Litestream-Restore-Latenz bleibt bewusst akzeptiert
  (`docs/decisions/0013-v1-deployment-mode.md:89-98`).
- Restore/Reconciliation ist im Test vorhanden, im Zustandsmodell aber noch
  nicht ganz angekommen.
- Mehrere Meta-Dokumente behaupten weiterhin V0.1.

Bewertung: **betriebsseitig viel klarer; Restore- und State-Drift sind die
offenen Reststellen.**

### Produkt- und UX-Perspektive

Stärken:

- Die neue HITL-Semantik ist deutlich nutzerverträglicher.
- Digest-Cards sind ein sinnvoller Kanal für System-Health ohne
  Work-Item-Blockade
  (`docs/decisions/0012-hitl-timeout-semantics.md:68-85`,
  `docs/spec/SPECIFICATION.md:348-351`).
- Das Feature-Pattern stärkt lieferbare Slices statt abstrakter Roadmap-Texte.

Risiken:

- Stage/State-Drift kann später in CLI und Inbox-UX sichtbar werden.
- Benchmark-Awareness kann in Benchmark-Obsession kippen; der Plan nennt das
  selbst als Risiko
  (`Plans/option-3-ich-m-chte-serialized-oasis.md:232-235`).
- Ein automatischer Wechsel in `cost-aware` nach Zeit oder Pin-Anzahl ist
  aus Nutzersicht erklärungsbedürftig.

Bewertung: **deutlich benutzerfreundlicher als V0.1, aber noch nicht ganz
erklärbar genug an den Dispatch- und State-Grenzen.**

### Daten- und Durability-Perspektive

Stärken:

- `RunAttempt` und Runtime-Records sind der richtige strukturelle Schritt.
- Audit, Budgetledger und Tool-Calls bekommen endlich einen Ort.
- JSONL plus SQLite ist für Single-User-V1 proportional.

Risiken:

- Exactly-Once für externe Effekte wird weiterhin zu optimistisch gelesen.
- `DispatchDecision` ist nicht auf allen Dokumentebenen gleich vollständig
  modelliert.
- `needs_reconciliation` ist gefordert, aber nicht als Zustand normiert.

Bewertung: **das Datenmodell ist jetzt deutlich professioneller, aber noch
nicht auf dem Niveau eines vollständig belastbaren Retry-/Reconcile-Vertrags.**

### Kostenperspektive

Stärken:

- Die `OR`-Semantik in der Spec ist richtig.
- Budget-Gate vor dem LLM-Call bleibt korrekt gesetzt.
- Cost-Aware-Routing ist als regelbasierte Policy vernünftiger als ein
  vorschneller Learned Router.

Risiken:

- Die alte ADR-0008 widerspricht weiterhin der korrigierten Spec.
- Die Haiku-Confidence-Probe kostet pro Work Item einen zusätzlichen Call
  (`docs/decisions/0014-peer-adapters-and-cost-aware-routing.md:201-202`).
- Die Aktivierungsregel für `cost-aware` ist nicht lokal kalibriert.

Bewertung: **richtig angelegt, aber das Regime ist noch inkonsistent zwischen
Spec, ADR und Aktivierungspolitik.**

### Implementierungsperspektive

Stärken:

- V0 ist mit F0001/F0002 klein genug.
- Das Feature-Pattern ist als Arbeitsoberfläche brauchbar.
- Die Architektur vermeidet weiterhin unnötige Service-Splits.

Risiken:

- F0003/F0004 greifen schon in Runtime- und Schema-Themen hinein, die der
  aktuelle Feature-Scope nicht explizit trägt.
- `spec-reviewer` und `AGENTS.md` hängen dokumentarisch hinterher.
- Die größte Komplexität sitzt jetzt nicht mehr in der Modulzahl, sondern in
  den Übergängen zwischen Routing, Budget, Retry und HITL.

Bewertung: **der Weg in eine echte v0/v1a-Umsetzung ist frei, aber nur, wenn
die Dokumente vor dem Start noch einmal auf Konsistenz gezogen werden.**

## Priorisierte Empfehlungen

### Sofort

1. **Normkonsistenz der Alt-ADRs herstellen.**
   ADR-0007 und ADR-0008 dürfen nicht weiter als `accepted` mit Semantiken
   stehen, die V0.2 bereits ersetzt oder korrigiert hat.

2. **Die State-Machines glätten.**
   `waiting_for_approval`, `stale_waiting`, `timed_out_rejected` und
   `needs_reconciliation` müssen entweder echte Zustände werden oder aus den
   Flows/Testkriterien verschwinden.

3. **Die Peer-Adapter-Asymmetrie offen entscheiden.**
   Entweder echte Symmetrie oder dokumentierter Claude-Default; das Dazwischen
   ist unklarer als beide ehrlichen Varianten.

4. **Das Tool-Risk-Modell explizit machen, bevor `approval=never`
   implementiert wird.**
   Ohne fail-closed Policy-Inventar ist der Approval-Entscheid noch kein
   sicherer Vertragszustand.

5. **Die Runtime-Basis als eigenes Liefer-Slice sichtbar machen.**
   F0003/F0004 sollten nicht auf impliziter Infrastruktur schweben.

6. **Appendix A zwischen Evidenz und Ableitung trennen.**
   „Diese Quellen stützen die Verwerfung von X“ und „deshalb auto-aktivieren
   wir Y“ sind zwei verschiedene Sätze.

### Danach

1. **ADR-0014 bei Beginn der Implementierung aufspalten, falls ein dritter
   unabhängiger Änderungswunsch auftritt.**
   Aktuell ist inline noch okay; bei Routing- oder Approval-Änderungen kippt
   das schnell.

2. **`DispatchDecision` und Gate-Reroute präzisieren.**
   Audit und Retry brauchen einen finalen, unverwechselbaren Record.

3. **Meta-Dokumente nachziehen.**
   `AGENTS.md`, `spec-reviewer.md`, Feature-Indizes und kleinere Cross-Refs
   sollten denselben Versions- und Invariantenstand tragen.

4. **Externe Effektklassen explizit typisieren.**
   Nicht jeder Side-Effect hat dieselbe Idempotenzqualität; das sollte der
   ADR-Text sagen.

5. **Den `cost-aware`-Mode lokal kalibrieren, nicht nur zeitbasiert
   aktivieren.**
   Ein Router sollte wegen Qualität/Kosten gewinnen, nicht wegen Kalenderzeit.

### Verschoben

1. **Learned Router / RouteLLM-Training** erst mit echter lokaler
   Dispatch-Historie.
2. **Automatischer Benchmark-Scheduler** erst, wenn der manuelle Pull
   überhaupt einen Nutzen zeigt.
3. **Dritter Adapter** erst nach stabiler Version des
   `ExecutionAdapter`-Vertrags.
4. **Cross-Model-Review** weiter explizit verworfen lassen, bis deutlich
   bessere Evidenz vorliegt.

## Schlussurteil

V0.2.0-draft ist **kein kosmetischer Patch**, sondern eine echte
Architekturreparatur. Das Repo ist heute deutlich näher an einer belastbaren
Single-User-v0/v1a-Basis als gestern. Besonders stark sind der
Execution-Harness-Vertrag, die Deployment-Klärung und die Einführung eines
technischen Runtime-Record-Layers.

Trotzdem trägt die Gegenreaktion von Claude an mehreren Stellen zu dick auf.
Mehrere als „vollständig geschlossen“ angekündigte Befunde sind im Repo nur
teilweise geschlossen:

- Befund 2 wegen HITL-State-Drift und ungelöschtem ADR-0007-Widerspruch
- Befund 3 wegen zu optimistischem Idempotenzversprechen
- Befund 5 wegen unverändert falscher ADR-0008
- Befund 6 wegen fehlendem Tool-Risk-Inventar
- Befund 7 wegen unvollständiger Runtime-Record-Kohärenz
- Befund 8 wegen unstimmiger Stage-Taxonomie

Zur Nutzerfrage nach „Symbiose“ ist mein Urteil klar:

- **Task-Class-Specializer:** nicht gut genug gestützt
- **Cross-Model-Review:** nicht gut genug gestützt
- **Peer-Adapter mit gemeinsamer Vertragsfläche:** gut vertretbar
- **Benchmarks als Awareness:** gut vertretbar
- **Automatischer `cost-aware`-Switch:** aktuell eher Architekturableitung als
  belasteter empirischer Schluss

Die beste Lesart von „Symbiose“ ist im jetzigen Stand **nicht**:
„das System entscheidet automatisch schlau zwischen zwei Frontiersystemen,
weil Benchmarks und Literatur das klar hergeben“.
Die empirisch sauberere Lesart wäre:
„beide Adapter teilen sich einen kleinen Vertrag, der Nutzer kann pinsen, das
System bleibt benchmark-aware, und teurere Automatik wird erst nach lokaler
Erfahrung eingeschaltet“.

Wenn diese zweite Lesart konsequent gezogen wird, ist V0.2 eine starke Basis.
Wenn ADR-0014 dagegen gleichzeitig Peer-Stance, de-facto-Claude-Default,
Auto-Aktivierung und implizite Approval-Sicherheit tragen soll, baut das Repo
sich an einer neuen Stelle wieder dieselbe Unschärfe ein, die V0.1 gerade erst
reparieren wollte.
