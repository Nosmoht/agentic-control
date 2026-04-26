# Fifth Codex Follow-up Review — Prompt

Repo: `agentic-control-docs-final` (cwd beim Start auf den Repo-Root setzen).

## Aufgabe

Schreibe ein **fünftes** Review der V1-Spec. Du hast vier Vorgänger-Reviews verfasst:

- `docs/reviews/2026-04-23-critical-system-review.md`
- `docs/reviews/2026-04-24-followup-review.md`
- `docs/reviews/2026-04-26-followup-review-2.md`
- `docs/reviews/2026-04-26-followup-review-3.md`

Dazwischen liegt eine Counter-Review von Claude:

- `docs/reviews/2026-04-23-counter-review.md`

Seit deinem vierten Review (auch 04-26) ist **V0.3.1-draft** gelandet — ein Konsistenz-Patch, der die zehn Befunde aus 04-26-followup-review-3 adressieren soll.

Was V0.3.1-draft konkret tut:

- **Neues Feature F0008** (V1 Domain Schema: `run`, `artifact`, `evidence`) — schließt den FK-Anker, den F0006 von F0001 erwartete, ohne dass F0001 ihn liefert.
- **F0006-Korrekturen:** AC 3 hat jetzt zwei UNIQUE-Constraints (`(run_attempt_id, tool_call_ordinal)` + `(run_attempt_id, idempotency_key)`); ACs 11–13 für `DispatchDecision`, `PolicyDecision` (mit Fünf-Tag-CHECK), `SandboxViolation` ergänzt; `depends_on: [F0001, F0008]`.
- **F0007-Rebase auf PolicyDecision-Historie:** primäre Datenquelle ist `policy_decision(policy=tool_risk_match)` aus F0006, nicht eine Re-Klassifikation gegen das aktuelle Inventory. `tools propose` hat normierte Einfügepositions-Regeln + Dry-Run-Match + Rollback. Digest-Card-ID deterministisch aus `sha256(period_start + sorted_unmatched + threshold_kind)`. `adr_refs` += ADR-0016, `depends_on: [F0006]`.
- **F0003 wired:** `dispatch pin` schreibt jetzt explizit über ADR-0016-Vertrag; `adr_refs` += ADR-0016.
- **ADR-0016 Conflict-Check** zusätzlich auf Inhalts-Hash (`sha256(file_content)` als `before_hash` beim initialen Read, Re-Check vor `rename`); manuelle Editor-Edits ohne Versions-Bump werden damit erkannt.
- **Spec §8.5 ADR-Reservierung** korrigiert: Harness-Profile-ADRs sind jetzt 0017/0018 (ADR-0016 ist Config-Write).
- **Spec Appendix A v1a** erweitert: F0005, F0006, F0007, F0008 + ADR-0016 namentlich, mit explizit dokumentierter Reihenfolge `F0001 → F0008 → F0006 → [F0003, F0004, F0007] → F0005`.
- **Index, Plan, Meta** auf V0.3.1-draft.

Dein Review prüft: **Sind die zehn Befunde aus 04-26-followup-review-3 substanziell geschlossen — oder wieder nur teilweise? Hat V0.3.1-draft neue Probleme eingeführt, insbesondere durch F0008 als zusätzliches Schema-Feature und die Rebase-Operation an F0007?**

Du darfst eigene frühere Befunde revidieren. Du darfst deine eigene Logik aus 04-26 in Frage stellen, falls V0.3.1 sie überholt hat.

## Lese-Reihenfolge

1. Vier Vorgänger-Reviews + Counter-Review (Kontext).
2. `CHANGELOG.md` Einträge `[0.3.1-draft]`, `[0.3.0-draft]`, `[0.2.4-draft]`.
3. **Neue/geänderte Features:** F0008 (neu), F0006 (AC-Korrekturen + Scope), F0007 (Scope-Rebase + AC 4 + propose-Regeln), F0003 (ADR-0016-Wiring).
4. **Geänderter ADR:** ADR-0016 (Conflict-Check + Inhalts-Hash).
5. **Spec-Sektionen:** §8.5 (ADR-Reservierung), Appendix A v1a (Reihenfolge), §9 (ADR-Tabelle), §5.7 (Lifecycle-Konsistenz mit F0008-Migration), Frontmatter.
6. **Index/Plan:** `docs/features/README.md`, `docs/plans/project-plan.md` (Dependency-Graph).
7. Configs ungeändert (`model-inventory.yaml` v3, `tool-risk-inventory.yaml` v2, `benchmark-task-mapping.yaml` v1).

## Bewertungsachsen

**A · Schließen V0.3.1-Patches die zehn Befunde aus 04-26-followup-review-3?**

- N1 Hoch: F0008 als FK-Anker für F0006.
- N2 Hoch: F0006-ACs für alle acht Runtime Records.
- N3 Hoch: Idempotency-Key-UNIQUE-Constraint korrekt.
- N4 Mittel-Hoch: F0007 misst über `PolicyDecision`-Historie.
- N5 Mittel: Pattern-Matcher-Dependency entkoppelt.
- N6 Mittel: `tools propose`-Einfügeposition normiert.
- N7 Mittel: ADR-0016-Conflict-Check auf Inhalts-Hash.
- N8 Mittel: ADR-0016-Adoption (F0007/F0003-Frontmatter, Index, Plan).
- §8.5-Drift: ADR-Nummern.
- N9 Mittel: Appendix A.
- N10 Niedrig-Mittel: F0007 Digest-Card-Idempotenz.

**B · Hat V0.3.1 neue Widersprüche eingeführt?**

- F0008-Schema vs. Spec §5.7 Lifecycle-States: deckungsgleich (alle neun Run-States, inkl. `needs_reconciliation`)?
- F0006 `depends_on: [F0001, F0008]` vs. project-plan-Graph: konsistent?
- F0007 Frontmatter `depends_on: [F0006]` vs. F0006 das nur F0001+F0008 voraussetzt — gibt es einen impliziten Pattern-Matcher-Dependency, der jetzt unsichtbar ist?
- Idempotency-Key-NULL-Erlaubnis (für Tool-Calls ohne externen Effekt): kollidiert mit `(run_attempt_id, idempotency_key)`-UNIQUE? SQLite-Semantik: NULL ist nicht eindeutig, also funktioniert UNIQUE bei NULL. Trotzdem: ist das im Schema klar dokumentiert?
- ADR-0016-Inhalts-Hash-Check vs. F0005 `accept`-Diff-Anzeige: konsistent (zeigt der angezeigte Diff gegen den initialen `before_hash` oder gegen die aktuelle Datei)?

**C · F0008-Bewertung**

- ACs vollständig genug für ein Schema-Feature (FK-Tests, CHECK-Tests, polymorphe Ref-Tests, Idempotenz, Integrationstest mit F0001+F0006)?
- Migration-Tool-Wiederverwendung: ist die F0001-Forward-Only-Skelett-Annahme realistisch (V0.3.1 spec'd kein Migration-Tool, nur die Konvention)?
- Sind `evidence.kind` und `artifact.kind` als Open-Enum (mit Mindest-Set) ausreichend, oder braucht es einen ADR?

**D · F0006-Korrekturen-Bewertung**

- Doppelte UNIQUE-Constraints (`(run_attempt_id, tool_call_ordinal)` + `(run_attempt_id, idempotency_key)`): orthogonal nutzbar, oder kann ein Tool-Call mit NULL-Idempotency-Key beide Constraints verletzen?
- ACs 11–13 (DispatchDecision, PolicyDecision, SandboxViolation): konkret genug für Implementierungs-Tests?
- Stub-Alert-Hook in AC 13: ausreichend definiert?

**E · F0007-Rebase-Bewertung**

- Tatsächliche Datenquelle umgestellt von `tool_call_record + Live-Matcher` auf `policy_decision(policy=tool_risk_match)` — sauber durchgezogen oder Rest-Zitat des Live-Matchers?
- Re-Match-Fallback für Alt-Daten (vor F0006): ausreichend gewarnt?
- Digest-Card-ID-Formel mit `threshold_kind`: was sind die zwei Kinds, sind beide klar?
- `tools propose`-Einfügeposition + Dry-Run-Match: deckt das Glob-Catch-all-Familien-Reihenfolge ab oder gibt es Edge Cases?

**F · ADR-0016-Erweiterung**

- Inhalts-Hash-Check zusätzlich zu Versions-Check: Performance-Implikation bei großen Configs (in V1 klein, aber langfristig)?
- Was passiert, wenn der `before_hash` selbst gespeichert werden muss zwischen Lock-Acquire und Schreibvorgang? Muss er persistent sein oder lebt er im Prozess?

**G · Lieferbarkeitsblick V0.3.1**

- v0-Pfad (F0001 + F0002): unverändert sauber?
- v1a-Pfad (F0001 → F0008 → F0006 → [F0003, F0004, F0007] → F0005): ist das jetzt **vollständig** start-tauglich, oder gibt es weitere implizite Voraussetzungen (z. B. Pattern-Matcher in ADR-0010-Implementation, die noch kein Feature hat)?
- Welche ADRs (0010, 0012, 0013) brauchen noch Implementations-Features bevor v1a-Exit erreichbar ist?

## Ausgabe

Schreibe genau eine neue Datei. Pfadname mit dem heutigen Datum aus deiner Systemuhr:

**Pfad:** `docs/reviews/<YYYY-MM-DD>-followup-review-4.md`

**Format:** YAML-Frontmatter (`title`, `date: <YYYY-MM-DD>`, `status: draft`, `reviewer: Codex`, `scope`, `responds_to`-Liste mit Pfaden) + Markdown-Sections analog zum 04-26-followup-review-3:

- Executive Summary mit Kurzurteil pro Achse.
- Quellenbasis (welche lokalen Dokumente du gelesen hast; **kein** externer Web-Check).
- Bewertungsmaßstab.
- Was V0.3.1 stark macht.
- Bewertung der zehn Befunde aus 04-26-followup-review-3 (Status: geschlossen / teilweise / offen, mit Zeilen-Belegen).
- Neue Befunde aus Achsen B / C / D / E / F / G (Begründung, Belege, Empfehlung).
- Perspektivenreview (Architektur / Sicherheit / Betrieb / Daten / Kosten / Implementierung — je 3–5 Sätze).
- Priorisierte Empfehlungen (Sofort / Danach / Verschoben).
- Schlussurteil — insbesondere: ist V0.3.1 jetzt **implementierungsbereit** für v1a, oder braucht es einen weiteren Patch?

Sprache: Deutsch. Belege mit `pfad:zeile`-Referenzen. Konkrete Quellen-Zitate für jede Behauptung.

## Was du NICHT tust

- Keine anderen Dateien schreiben oder editieren.
- Keine Git-Commits, keine Pushes.
- **Kein** externer Web-Check als Bewertungsgrundlage (lokal-only).
- Keine Implementierungs-Vorschläge in Code; nur Design/Spec-Ebene.

## Nach Ende

`git status` zeigt genau eine neue Datei (`docs/reviews/<YYYY-MM-DD>-followup-review-4.md`). Du gibst einen 2–3-Satz-Status zurück: wie viele Befunde fully closed / partial / neu, plus dein Kernurteil zur v1a-Implementierungsreife. Mehr nicht.
