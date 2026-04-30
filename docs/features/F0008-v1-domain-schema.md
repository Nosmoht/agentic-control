---
id: F0008
title: V1 Domain Schema (Run, Artifact, Evidence)
stage: v1a
status: in_progress
spec_refs: [§5.7]
adr_refs: [ADR-0001, ADR-0003, ADR-0016]
---

# F0008 · V1 Domain Schema (Run, Artifact, Evidence)

## Context

F0001 liefert das v0-Domain-Schema mit vier Tabellen (`project`,
`work_item`, `observation`, `decision`). `Run`, `Artifact` und
`Evidence` sind in Spec §5.7 als Stage v1 markiert und in F0001
ausdrücklich aus dem Scope ausgeschlossen, weil sie erst mit
v1a-Lifecycle-Automation Sinn ergeben. F0006 setzt aber bereits einen
Foreign-Key auf `run` voraus, um `RunAttempt`-Records persistieren zu
können (Counter-Counter-Counter-Review-2026-04-26 Befund 1, Hoch).
F0008 schließt diese Schema-Lücke als minimal additiver
v1a-Domain-Slice **vor** F0006. Plan-Reihenfolge wird damit
F0001 → F0008 → F0006 → [F0003, F0004, F0007] → F0005.

## Scope

- Migration `0001b_v1_domain_schema.sql` auf die F0001-DB (additiv,
  kein Drop von v0-Tabellen):
  - Tabelle `run` mit FK auf `work_item`, Lifecycle-State als
    TEXT-Enum gemäß Spec §5.7 Run-Lifecycle (`created`, `running`,
    `paused`, `waiting`, `retrying`, `needs_reconciliation`,
    `completed`, `failed`, `aborted`).
  - Tabelle `artifact` mit FK auf `run` (`origin_run_ref`),
    Pflichtfelder gemäß Spec §5.7 (`id`, `kind`, `path|ref`,
    `provenance`, `state`).
  - Tabelle `evidence` mit polymorpher `subject_ref`-Spalte (Format
    `<typ>:<id>`, z. B. `run:abc`, `artifact:xy`, `decision:42`),
    Pflichtfeld `kind`, optionales `jsonl_blob_ref`.
- Subtypen-Markierungen via TEXT-Enum (`kind`-Spalte):
  - `evidence.kind` mindestens `benchmark`, `decision_evidence` (Spec
    §5.5); Erweiterung pro Bedarf.
  - `artifact.kind` mindestens `benchmark_raw`, `file_diff`,
    `commit_hash`, `run_log`; Erweiterung pro Bedarf.
- Migration ist idempotent (zweite Ausführung schlägt nicht fehl).

## Out of Scope

- **Runtime-Records-Tabellen** (`run_attempt`, `audit_event` etc.) —
  liefert F0006.
- **`Standard`-Tabelle** — kommt in v3.
- **`Dependency`-Tabelle** — kommt in v2.
- **CRUD-CLI-Befehle** (`agentctl runs new`, `artifacts add`,
  `evidence import`) — eigene Folgefeatures pro Bedarf.
- **Migration-Tool selbst** — nutzt das bestehende Forward-Only-
  Migrations-Skelett aus F0001.

## Acceptance Criteria

1. Migration läuft auf einer F0001-DB ohne Fehler; `sqlite3 .schema`
   zeigt `run`, `artifact`, `evidence` zusätzlich zu den vier
   v0-Tabellen.
2. FK-Constraint auf `work_item` ist aktiv: Insert eines `run` mit
   nicht-existentem `work_item_ref` schlägt fehl.
3. CHECK-Constraint auf `run.state` ist aktiv: Insert mit
   `state='bogus'` schlägt fehl; alle neun Lifecycle-States aus Spec
   §5.7 (inkl. `needs_reconciliation`) sind gültig.
4. FK auf `artifact.origin_run_ref` ist aktiv: Insert mit
   nicht-existentem Run schlägt fehl.
5. CHECK-Constraint auf `artifact.state` ist aktiv: Insert mit
   `state='bogus'` schlägt fehl; alle Lifecycle-States aus Spec
   §6.1 (`registered`, `available`, `consumed`, `superseded`,
   `archived`) sind gültig
   (Counter-Counter-Counter-Counter-Review-2026-04-26 Befund 4).
6. Polymorphe `evidence.subject_ref` akzeptiert mindestens
   `work_item:<id>`, `run:<id>`, `artifact:<id>`, `decision:<id>`;
   `kind`-Werte `benchmark` und `decision_evidence` sind erlaubt.
7. **Negative-Tests `evidence.subject_ref`:**
   - Insert ohne Präfix-Trennzeichen (`work_item42`) schlägt einer
     Format-Validierung fehl (CHECK-Regex
     `^(work_item|run|artifact|decision):[A-Za-z0-9_-]+$`).
   - Insert mit unbekanntem Präfix (`stranger:42`) schlägt fehl.
   - **Eigenentscheidung (V0.3.2-draft):** ID-Existenz wird
     **nicht** in SQLite erzwungen (polymorpher FK ist nicht trivial
     und wäre Overkill für n=1); F0006 prüft die Existenz beim
     Insert auf Anwendungsebene über einen kleinen Validierungs-
     Hook, der vor dem `INSERT` die Subject-Tabelle abfragt
     (Hook-Kontrakt siehe „Polymorpher-Ref-Validierungs-Hook" unten).
8. Migration ist idempotent: zweite Ausführung erzeugt keinen Fehler
   und keine Duplikate.
9. **Integrationstest mit F0001 + F0008 + F0006**: nacheinander
   ausgeführt, das Gesamtschema enthält 4 + 3 + 8 = 15 Tabellen, alle
   FK-Verbindungen funktionieren.
10. **Polymorpher-Ref-Validierungs-Hook** (V0.3.6-draft, Closure
    der R3-Lücke aus 2026-04-29 Audit):
    - Pydantic-Modell `EvidenceSubjectRef` in
      `src/agentic_control/contracts/evidence.py` als discriminated
      union über `kind: Literal["work_item","run","artifact","decision"]`
      + `id: UUIDv7`. `model_dump()` rendert das `<kind>:<id>`-Format
      für die SQL-Spalte; `model_validate()` parst es zurück.
    - Validierungs-Hook-Signatur in
      `src/agentic_control/persistence/evidence_validator.py`:
      `validate_subject_ref(engine: Engine, ref: EvidenceSubjectRef)
      -> None`. Wirft `RepositoryError` wenn die Subject-Row in der
      kind-zugeordneten Tabelle nicht existiert.
    - F0006-Repository ruft den Hook **vor** jedem `evidence`-Insert
      auf (gleiche Transaction).
    - Erweiterung um neue Subject-Typen ist eine atomare Änderung in
      drei Dateien: (a) Migrations-Skript erweitert die CHECK-Regex,
      (b) `EvidenceSubjectRef`-Union bekommt einen neuen Arm,
      (c) `validate_subject_ref` bekommt eine neue Tabellen-Branch.
      Alle drei Änderungen kommen in **einem** Commit; der Audit
      `tests/integration/test_evidence_polymorphic.py` schlägt fehl,
      wenn nur einer der drei Punkte gepatcht ist.

## Test Plan

- **Unit:** Migration auf leerer DB nach F0001; Schema-Dump vs.
  Expected-Fixture.
- **Integration:** Run + Artifact + Evidence-Roundtrips mit FKs;
  Sequence F0001 + F0008 + F0006.
- **Negative:** FK-Violation, CHECK-Violation, doppelte Migration.
- **Manuell:** sobald F0006-CLI vorhanden, manueller Run-Lifecycle:
  `work add` → `run new` (oder Äquivalent) → Run wird in DB sichtbar
  → Artifact wird registriert → Evidence wird angefügt.

## Rollback

**Eigenentscheidung (V0.3.2-draft):** v0 und v1a bleiben
**Forward-Only**, wie in F0001 etabliert. Down-Migration-Skripte sind
**nicht Teil von V1**. Rollback von F0008 erfolgt über:

1. Git-Restore auf den vorherigen Commit (`git checkout <pre-F0008>
   -- migrations/`).
2. Manuelles Drop der drei Tabellen (`DROP TABLE evidence; DROP TABLE
   artifact; DROP TABLE run;`) falls eine bereits migrierte DB im
   Live-Betrieb zurückgesetzt werden muss.
3. F0001-v0-Tabellen bleiben dabei unberührt.

Down-Migrations-Konvention für v2+ ist offen
(Counter-Counter-Counter-Counter-Review-2026-04-26 Befund 5);
falls ab v2 produktive Down-Migrationen nötig werden, entsteht
dafür ein eigener ADR.

F0006 wird ohne F0008 nicht funktionieren — ein Rollback von F0008
setzt v1a auf F0001+F0002 zurück.
