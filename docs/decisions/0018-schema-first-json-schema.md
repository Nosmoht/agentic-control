# ADR-0018: Schema-First mit JSON Schema für Daten-Boundaries

* Status: accepted
* Date: 2026-04-27
* Context: `docs/spec/SPECIFICATION.md §5.7`, ADR-0011, ADR-0016,
  ADR-0017, F0008

## Kontext und Problemstellung

Das System trägt eine Reihe von **Daten-Verträgen**, die heute als
Markdown-Tabellen in Spec/ADRs/Features formuliert sind:

- **Runtime Records (ADR-0011):** `RunAttempt`, `AuditEvent`,
  `ApprovalRequest`, `BudgetLedgerEntry`, `ToolCallRecord`,
  `PolicyDecision`, `SandboxViolation`.
- **V1 Domain Schema (F0008):** `Run`, `Artifact`, `Evidence`.
- **Konfig-YAMLs (ADR-0016 Write Contract):** `model-inventory.yaml`,
  `routing-pins.yaml`, `tool-risk-inventory.yaml`,
  `benchmark-task-mapping.yaml`, plus zukünftige Defaults.
- **Spec §5.7 Kernobjekte:** Work Item, Decision, Plan, Project,
  Source, Standard, RunAttempt, AuditEvent, …

Diese Schemas leben heute in Prosa-Tabellen. Konsequenzen:

- Drift zwischen Doku und Implementierung wird erst zur Laufzeit
  sichtbar.
- Konfig-YAMLs werden nicht hart gegen Schema validiert
  (ADR-0016 schreibt `Optimistic Conflict Check` über `version` +
  `content-hash`, aber kein **Strukturkontrakt**).
- Der Implementierer muss die Tabellen manuell in Pydantic/Structs/Zod
  übersetzen — Übersetzungsfehler sind unsichtbar.

Vor dem v0-Implementierungsstart muss entschieden werden, in welcher
Form die Daten-Verträge formalisiert werden. Die Frage ist nicht „ob",
sondern „mit welchem Werkzeug und an welchen Boundaries".

## Entscheidungstreiber

1. **Sprach-Neutralität** — entkoppelt von ADR-0017. Wenn die Sprache
   wechselt, soll der Schema-Bestand erhalten bleiben.
2. **Werkzeug-Last proportional zu n=1** — kein gRPC-/protoc-/buf-
   Stack, wenn die Boundaries das nicht hergeben.
3. **Boundary-Realität in v1a** — keine RPC, kein REST, ein Prozess.
4. **Forward-Kompatibilität zu v2+** — wenn Messenger-Bridge oder
   externer Daemon dazu kommen, soll der Wechsel zu Protobuf/OpenAPI
   möglich sein, ohne die Schemas neu zu schreiben.
5. **Validierungs-Punkte konkret** — ADR-0016 Config Write Contract
   braucht hard-validation; Runtime-Records brauchen Insert-Validation;
   Adapter-Outputs (JSONL von Claude Code / Codex CLI) brauchen Parse-
   Validation.
6. **Single-Source-of-Truth** — Doku, Code, Validierung sollen
   nicht divergieren.

## Erwogene Optionen

### Option 1 — Status quo (Markdown-Tabellen, keine Maschinen-Schemas)

**Pro**
- Null Werkzeug-Last.
- Niedrige Eintrittsbarriere für Doku-Änderungen.

**Contra**
- Drift unsichtbar.
- Konfig-YAMLs (ADR-0016) nicht hart validierbar.
- Implementierer muss raten/übersetzen — Fehlerklasse, die ADR-0011
  Idempotenz-Disziplin gerade ausschließen will.

### Option 2 — Pydantic-only (Single-Source = Code)

**Pro**
- Wenn Python (ADR-0017 Option 1) gewählt wird: maximaler Komfort.
- `model_json_schema()` liefert JSON Schema bei Bedarf.
- Validation und Typing in einem.

**Contra**
- An Sprache gebunden — bei Sprach-Wechsel (ADR-0017 Wahl) wertlos.
- Externe Tools (yq, JSON-Schema-CLI) müssen erst vom Code abgeleitete
  Schemas konsumieren.
- Markdown-Doku muss separat aktuell gehalten werden — keine
  Single-Source.

### Option 3 — JSON Schema (Draft 2020-12) als kanonische Form

**Pro**
- RFC 8259 + IETF-Draft, sprach-neutral.
- Reife Validatoren in Python (`jsonschema`), Go (`gojsonschema`,
  `santhosh-tekuri/jsonschema`), TS (`ajv`), Rust (`jsonschema`).
- Code-Gen optional: `datamodel-code-generator` → Pydantic;
  `go-jsonschema` → Go-Structs; `json-schema-to-zod` → TS.
- Integriert sauber in ADR-0016 Write Contract: vor jedem Konfig-Write
  ein `validate(content, schema)`-Schritt, atomisch zusammen mit Lock
  + Conflict-Check.
- YAML-Configs werden über `yaml.safe_load` → JSON-Schema-Validate
  geprüft.
- Markdown-Tabellen können automatisch aus den Schemas generiert
  werden (z. B. `json-schema-for-humans`).
- Forward-Path zu OpenAPI: OpenAPI 3.1 verwendet JSON Schema 2020-12
  als Body-Schema-Sprache. Migration ist syntaktisch lokal.

**Contra**
- Kein Wire-Format (irrelevant für v1a).
- Schema-Files erzeugen ein zusätzliches Verzeichnis (`schemas/`).
- Editor-Tooling (LSP für JSON Schema in YAML-Configs) muss eingerichtet
  werden — geringe Hürde.

### Option 4 — Protobuf

**Pro**
- Wire-Format effizient.
- Strenges Schema-Evolution-Modell (Field-Numbers, Reserved).
- Code-Gen für alle relevanten Sprachen.

**Contra**
- v1a hat **keine** RPC- oder Wire-Format-Boundary in eigener Hand.
- `protoc`/`buf` als Build-Schritt — neue Werkzeug-Pflicht.
- Protobuf-Maps, Optional-Semantik, Default-Werte sind in jeder
  Sprache leicht anders gelagert.
- YAML-Configs sind kein Protobuf-Use-Case.
- Erst ab v2+ (Messenger-Bridge ↔ Daemon) sinnvoll.

### Option 5 — OpenAPI

**Pro**
- HTTP-API-Vertrag, Doku-Generation, Cross-Language-Clients.
- 3.1 nutzt JSON Schema 2020-12 — Schemas wären portabel.

**Contra**
- Kein HTTP-API in v1a (CLI-Daemon, kein Service).
- Erst sinnvoll, wenn `agentctl` über Netz auf Daemon zugreift oder
  Audit-Export für Drittsysteme exponiert wird.

## Entscheidung

Gewählt: **Option 2 — Pydantic-Models als kanonische Single-Source,
JSON Schema als abgeleitetes Export-Artefakt** (nicht Option 3 wie in
der `proposed`-Fassung empfohlen).

Die ursprüngliche Fassung dieses ADR (V0.3.3-draft, `proposed`)
hatte Option 3 (Standalone-JSON-Schema-Files) empfohlen, mit dem
Argument der Sprach-Neutralität. Mit ADR-0017 fixiert auf Python ist
dieses Argument schwächer geworden — und die adversarielle Review hat
einen realen Failure-Mode benannt: **15 Standalone-Schema-Files
neben dem Code produzieren doppelte Drift**, weil weder Prosa noch
JSON-Files normativ sind und beide gleich schnell veralten.

### Gewähltes Muster

- **Pydantic-Models** in `src/<package>/contracts/` sind die
  **einzige Quelle** der Daten-Verträge.
- `model_json_schema()` exportiert bei Build oder Pre-Commit nach
  `schemas/`. Diese Files sind Build-Artefakte, kein handgepflegter
  Bestand — `schemas/` wird im Repo gehalten, damit Reviewer und
  Tooling (z. B. YAML-LSP für Konfig-Editing) sie sehen, aber per
  Convention nicht von Hand editiert.
- **ADR-0016 Config Write Contract** lädt das exportierte JSON-Schema
  für jede Konfig-YAML und validiert vor `acquire_lock`. Das
  geforderte Strukturkontrakt-Verhalten ist damit erfüllt, ohne dass
  zwei Quellen synchron gehalten werden müssten.
- **Markdown-Tabellen in Spec/ADRs** werden mittelfristig aus den
  Pydantic-Models per Doku-Gen aktualisiert — nicht handgepflegt.
  Bis dahin trägt der Pydantic-Model den normativen Vertrag und die
  Tabelle ist informativ.
- **Protobuf/OpenAPI bleiben defer bis v2+.** OpenAPI 3.1 nutzt JSON
  Schema 2020-12; das Export-Artefakt ist also forward-kompatibel zur
  späteren HTTP-Boundary. Protobuf-Migration bei v2+-RPC-Bedarf ist
  syntaktisch lokal aus den exportierten Schemas.

### Warum nicht Option 3 (Standalone JSON Schema first)

- Sprach-Neutralität ist ab ADR-0017 (Python fixiert) keine offene
  Anforderung mehr.
- Standalone-Schema-Files vor Code-Zeile 1 erzeugen Pflege-Last für
  einen Vertrag, der noch keinen Konsumenten hat.
- Pydantic 2 erzeugt JSON Schema Draft 2020-12 nativ — der erwartete
  Code-Gen-Schritt (`datamodel-code-generator`) entfällt.
- Single-Source vermeidet die „Markdown vs. JSON Schema vs.
  Pydantic"-Drei-Quellen-Drift, die der Adversarial-Review als
  konkretes Failure-Pattern für n=1-Doku-First-Setups benannt hat.

### Warum nicht Option 1 (Status quo, nur Markdown)

- ADR-0016 Write Contract bekommt ohne maschinenlesbares Schema
  keinen Strukturkontrakt; das ist ein konkreter Lücken-Befund aus
  ADR-0016, der nicht offen bleiben darf.
- Drift wird unsichtbar; ADR-0011-Idempotenz-Disziplin verlangt
  hartes Insert-Validation.

### Konkrete Vertrags-Inventur (v0 + v1a Scope)

Zu schreibende Pydantic-Models in `src/<package>/contracts/` mit
JSON-Schema-Export nach `schemas/`:

| Pydantic-Model | Export-Pfad | Quelle | Validierungs-Punkt |
|---|---|---|---|
| `RunAttempt` | `schemas/runtime-records/run-attempt.json` | ADR-0011 | DB-Insert |
| `AuditEvent` | `schemas/runtime-records/audit-event.json` | ADR-0011 | DB-Insert |
| `ApprovalRequest` | `schemas/runtime-records/approval-request.json` | ADR-0011 | DB-Insert |
| `BudgetLedgerEntry` | `schemas/runtime-records/budget-ledger-entry.json` | ADR-0011 | DB-Insert |
| `ToolCallRecord` | `schemas/runtime-records/tool-call-record.json` | ADR-0011 | DB-Insert |
| `PolicyDecision` | `schemas/runtime-records/policy-decision.json` | ADR-0011, F0007 | DB-Insert |
| `SandboxViolation` | `schemas/runtime-records/sandbox-violation.json` | ADR-0011 | DB-Insert |
| `Run` | `schemas/domain/run.json` | F0008 | DB-Insert |
| `Artifact` | `schemas/domain/artifact.json` | F0008 | DB-Insert |
| `Evidence` | `schemas/domain/evidence.json` | F0008 | DB-Insert |
| `ModelInventory` | `schemas/config/model-inventory.json` | ADR-0014, F0005 | ADR-0016 Write |
| `RoutingPins` | `schemas/config/routing-pins.json` | ADR-0014 | ADR-0016 Write |
| `ToolRiskInventory` | `schemas/config/tool-risk-inventory.json` | ADR-0015, F0007 | ADR-0016 Write |
| `BenchmarkTaskMapping` | `schemas/config/benchmark-task-mapping.json` | F0005 | ADR-0016 Write |
| `DispatchDefaults` | `schemas/config/dispatch-defaults.json` | ADR-0014 | ADR-0016 Write |

(15 Modelle; Spec-Kernobjekte aus §5.7 sind Untermenge der
Domain-/Runtime-Records. Die Pydantic-Models sind die Quelle, die
JSON-Schema-Files sind das Export-Artefakt.)

### Layout

```
src/<package>/contracts/
├── runtime_records.py        # 7 Models
├── domain.py                 # 3 Models
└── config.py                 # 5 Models

schemas/                      # exportiert via `model_json_schema()`
├── runtime-records/
│   ├── run-attempt.json
│   ├── audit-event.json
│   └── …
├── domain/
│   ├── run.json
│   ├── artifact.json
│   └── evidence.json
└── config/
    ├── model-inventory.json
    ├── routing-pins.json
    └── …
```

`$schema`-Header verweist auf JSON Schema Draft 2020-12 (Pydantic 2
Default). `$id` ist ein lokaler Pfad
(`https://agentic-control.local/schemas/…`), kein Internet-URL.

Export erfolgt automatisiert per `agentctl schemas export` (oder
äquivalentem `make schemas`-Target). Pre-Commit-Hook prüft, dass
`schemas/` im Sync zu `src/<package>/contracts/` ist (nicht bei
`docs-only`-Phase, wo es noch keinen Code gibt — eingeführt mit dem
v0-Implementierungsstart).

### Validierungs-Punkte

1. **ADR-0016 Config Write Contract:** vor `atomic_write`, nach
   `lock_acquired`, **vor** `version+hash-conflict-check`. Jede
   Konfig-YAML wird als JSON-Schema validiert.
2. **DB-Insert für Runtime-Records:** Application-Layer-Validation
   (Pydantic/Struct/Zod) vor `INSERT`.
3. **Adapter-Output (JSONL aus Claude Code / Codex CLI):** Parse-
   Validation pro Line; ungültige Lines landen im `audit_event` mit
   `kind=adapter_parse_error`.
4. **F0007 Tool-Risk-Drift-Detection:** schon heute `default_hit_pct`
   per Convention; Schema macht den Vertrag explizit.

## Konsequenzen

**Positiv**
- Ein **kanonischer Vertrag pro Datentyp**, sprach-neutral.
- ADR-0016 Write Contract bekommt seinen Strukturkontrakt zurück.
- Sprach-Wechsel (ADR-0017) bleibt günstig — Schemas sind portabel.
- Code-Gen erzeugt typisierte Modelle in der gewählten Sprache.
- Forward-Path zu Protobuf (v2+ RPC) und OpenAPI (v2+ HTTP) ist
  syntaktisch lokal.

**Negativ**
- Zusätzliches Verzeichnis `schemas/` mit 15 Files (initial).
- Doppelte Repräsentation, bis Markdown-Tabellen aus Schemas
  generiert werden (Mittelfrist-Aufgabe; nicht Blocker für v0).
- Validierungs-Schritt in ADR-0016 Write-Pfad fügt einen Calls-Hop
  hinzu (Mikrosekunden, vernachlässigbar).

**Neutral**
- Schema-Versionierung erfolgt über Datei-Pfad (z. B.
  `runtime-records/v1/run-attempt.json` bei späteren Migrationen);
  Forward-Only-Migrationen (siehe v0-/v1a-Eigenentscheidung in
  F0008) bleiben gültig.

## Verhältnis zu ADR-0016

ADR-0016 definiert **wie** geschrieben wird (atomic + lock +
optimistic conflict + audit). ADR-0018 definiert, **was eine gültige
Inhaltsstruktur ist**. Die Pipeline wird:

```
load_yaml → validate_against_schema → check_version_and_hash →
  acquire_lock → atomic_write → audit_event
```

Schema-Validation ist **vor** Lock — eine ungültige Konfig wird
zurückgewiesen, ohne Lock-Kosten.

## Follow-ups

- F0006 Acceptance-Kriterien um Pydantic-Validation pro Runtime-Record
  ergänzen, sobald der v0-Implementierungsstart erfolgt.
- F0005, F0007 explizit auf die jeweiligen Pydantic-Models und
  exportierten JSON-Schemas verweisen.
- Eigenes Feature-File für `agentctl schemas export` und
  Pre-Commit-Hook (Schema-Sync-Check), wenn der Code-Pfad steht.
- Mittelfrist: Markdown-Tabellen aus den Pydantic-Models generieren
  (eigenes Feature-File, nicht Blocker).
- v2+: ADR „RPC-Boundary auf Protobuf" oder „HTTP-Boundary auf
  OpenAPI 3.1" — beide bauen auf den hier exportierten JSON-Schemas
  auf, nicht auf Pydantic-Models direkt.

## Referenzen

- ADR-0011 — Runtime Records and Idempotency Reconciliation
- ADR-0014 — Peer Adapters and Cost-Aware Routing (Konfig-Quellen)
- ADR-0015 — Tool-Risk-Inventory and Approval-Routing
- ADR-0016 — Config Write Contract
- ADR-0017 — Implementation Language (Code-Gen-Pfad)
- F0005 — Benchmark Curated Pin Refresh
- F0006 — Runtime Records and Reconcile-CLI
- F0007 — Tool-Risk-Drift-Detection
- F0008 — V1 Domain Schema
- JSON Schema Draft 2020-12: <https://json-schema.org/draft/2020-12>
- OpenAPI 3.1 Specification:
  <https://spec.openapis.org/oas/v3.1.0> (Body-Schemas = JSON Schema)
- Code-Gen: <https://github.com/koxudaxi/datamodel-code-generator>
  (Python), <https://github.com/omissis/go-jsonschema> (Go),
  <https://github.com/StefanTerdell/json-schema-to-zod> (TS)
