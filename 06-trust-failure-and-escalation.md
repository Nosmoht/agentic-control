# Trust, Failure and Escalation

## Trust-Zonen
- External Untrusted Input
- Interpreted Human Control
- Decision Core
- Integration & Identity Control
- Restricted Execution
- Trusted Knowledge & Audit

## Kritische Trust Boundaries
- externer Input → Interaction / Intent
- externer Provider / Tool / Resource → Integration / Knowledge
- Interaction / Intent → Decision Core
- Decision Core → Execution
- Execution → Knowledge / Portfolio / Workflow
- Knowledge → Policy
- Identity / Access → Provisioning / Execution
- Event Fabric → Fachkontexte

## Sicherheitsregeln
- kein direkter Pfad von untrusted input zu Execution
- externe Semantik wird immer übersetzt
- Execution erhält nur minimalen Scope
- technischer Zugriff ist nicht fachliche Erlaubnis
- Beobachtung ist keine Autorität
- Audit ist nicht Governance

## Fehlerklassen
- Interaction Failure
- Identity & Access Failure
- Semantic Failure
- Intake Failure
- Planning Failure
- Policy / Governance Failure
- Workflow Failure
- Portfolio / Dependency Failure
- Provisioning / Provider Failure
- Execution Failure
- Knowledge / Evidence Failure
- Event Failure
- Observability Failure

## Standardreaktionen
- Reject
- Clarify
- Wait
- Retry
- Replan
- Escalate

## Eskalationsprinzipien
- Human escalation ist nie Default-Reaktion auf technische Unsicherheit
- Retry nur für plausible transiente Fehler
- Replan statt Retry bei Entwurfsfehlern
- Pause statt Abort, wenn legitime spätere Auflösung erwartbar ist
- Abort statt Wait, wenn keine realistische Auflösungsperspektive besteht
- Eskalation an den Menschen muss priorisiert, gebündelt und begründet sein
