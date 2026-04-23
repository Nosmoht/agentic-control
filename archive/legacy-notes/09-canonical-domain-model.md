# Canonical Domain Model

## Zweck
Das Canonical Domain Model definiert die kanonischen Kernobjekte des Systems.
Es ist kein Datenbankschema und kein API-Schema, sondern das fachliche Referenzmodell.

## Modellierungsprinzipien
1. Jedes Kernobjekt hat eine eigenständige fachliche Identität.
2. Kanonische Objekte werden nicht aus Tool- oder Provider-Modellen abgeleitet.
3. Objekte folgen den Context Boundaries.
4. Referenzen gehen vor eingebetteter Fremdstruktur.
5. Zustand, Entscheidung und Evidenz bleiben unterscheidbar.
6. Lokale Resultate sind keine globalen Objekte ohne Promotion.

## Kernobjekte
### Project
Pflichtattribute:
- project_id
- title
- project_type
- lifecycle_state
- portfolio_scope
- created_from
- current_focus_class
- owning_portfolio_context_ref

### Work Item
Pflichtattribute:
- work_item_id
- title
- project_ref
- work_item_type
- lifecycle_state
- origin_ref
- priority_class
- current_plan_ref
- current_blockage_ref

### Workflow
Pflichtattribute:
- workflow_id
- work_item_ref
- workflow_type
- lifecycle_state
- current_step_ref
- start_condition_ref

### Dependency
Pflichtattribute:
- dependency_id
- dependency_type
- source_ref
- target_ref
- lifecycle_state
- satisfaction_basis
- scope

### Approval
Pflichtattribute:
- approval_id
- approval_type
- required_for_ref
- lifecycle_state
- request_reason
- decision_scope
- decision_owner_ref

### Standard
Pflichtattribute:
- standard_id
- title
- standard_type
- lifecycle_state
- applicability_scope
- source_basis
- current_binding_state

### Observation
Pflichtattribute:
- observation_id
- observation_type
- source_ref
- lifecycle_state
- captured_context_ref
- classification

### Decision
Pflichtattribute:
- decision_id
- decision_type
- decision_scope
- subject_ref
- lifecycle_state
- decision_basis
- decision_owner_context

### Artifact
Pflichtattribute:
- artifact_id
- artifact_type
- origin_ref
- lifecycle_state
- provenance_ref
- current_validity_state

### Evidence
Pflichtattribute:
- evidence_id
- evidence_type
- subject_ref
- origin_ref
- trust_class
- integrity_state

### Context Bundle
Pflichtattribute:
- context_bundle_id
- bundle_purpose
- subject_ref
- scope
- included_context_refs
- assembly_basis

### Provider Binding
Pflichtattribute:
- provider_binding_id
- internal_subject_ref
- provider_type
- external_reference
- binding_state

## Verbotene Modellverkürzungen
- Project = Repository
- Work Item = Workflow
- Observation = Standard
- Decision = Binding
- Artifact = Datei
- Approval = boolesches Flag
- Dependency = Event
- Context Bundle = beliebiger Context Dump
- Provider Binding = internes Fachobjekt
- Execution Result = globale Wahrheit
