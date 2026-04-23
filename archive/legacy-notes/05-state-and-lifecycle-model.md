# State and Lifecycle Model

## State Ownership
- Konversation → Interaction Management
- Zugriff/Identität → Identity, Trust & Access
- Semantik → Intent Resolution
- Arbeitsaufnahme → Work Intake & Triage
- Planstruktur → Work Design & Planning
- Verbindlichkeit → Policy & Governance
- Prozesszustand → Workflow Coordination
- Projekt- und Dependency-Struktur → Portfolio Context
- Provisioningzustand → Project Provisioning & Provider Integration
- Ausführungszustand → Execution & Verification
- Wissen, Evidenz, Standards, Artefakte → Knowledge, Context & Evidence
- Event-Korrelation → Event Fabric
- Telemetrie/Audit → Observability & Audit

## State Contracts
Beispiele:
- resolved_intent
- work_request
- priority_assignment
- work_plan
- action_authorized
- approval_required
- workflow_status_projection
- project_registry_entry
- dependency_record
- blockage_assessment
- execution_result
- verification_result
- observation_record
- standard_record
- artifact_record
- context_assembly

## Lifecycles
### Projekt
idea → candidate → provisioning → active → blocked/dormant → archived → retired

### Work Item
proposed → accepted → planned → ready → in_progress → waiting/blocked/under_review → completed/abandoned

### Workflow
created → running → paused/waiting/retrying/compensating → completed/failed/aborted

### Dependency
proposed → established → satisfied/violated → obsolete/removed

### Approval
required → requested → granted/rejected/expired/withdrawn

### Standard
observed_candidate → review_candidate → accepted_standard → bound_standard → deprecated → retired

### Artefakt
registered → available → consumed → superseded/invalidated → archived
