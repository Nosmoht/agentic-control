# Referenzarchitektur 1.0

## Zweck
Diese Referenzarchitektur beschreibt ein persönliches System zur kontrollierten Steuerung
agentischer Arbeit über viele parallele Projekte hinweg.

Das System soll:
- neue Ideen in Projekte überführen,
- bestehende Projekte bearbeiten,
- projektübergreifende Abhängigkeiten explizit verwalten,
- autonome Arbeit kontrolliert zulassen,
- Learnings in das System zurückführen,
- und dabei Beherrschbarkeit, Nachvollziehbarkeit und Governance erhalten.

Das System ist **kein Chatbot**, **keine reine Messenger-zu-CLI-Bridge** und
**kein monolithischer Agent mit etwas Memory**.
Es ist ein **Steuerungs-, Koordinations- und Lernsystem**.

## Architekturprinzipien
1. Control is not execution.
2. Semantics precede action.
3. Intake precedes planning.
4. Planning precedes orchestration.
5. Structure and process are different truths.
6. Execution is bounded and subordinate.
7. Knowledge informs, governance binds.
8. Observation is not authority.
9. One owner per primary state.
10. Prefer reference over replication.
11. External semantics must be translated.
12. Events inform, domains decide.
13. Escalate late, not early.
14. Cross-project effects require explicit structure.
15. Trust is explicit, not ambient.
16. Technical capability is not business legitimacy.
17. Systems must fail in a controlled way.

## Capability-Familien
- Steuerung
- Verstehen und Arbeitsaufnahme
- Planung und Koordination
- Portfolio und Projektanlage
- Ausführung
- Wissen und Lernen
- Governance und Vertrauen
- Integration und Betrieb

## Architekturkontexte
- Interaction Management
- Identity, Trust & Access
- Intent Resolution
- Work Intake & Triage
- Work Design & Planning
- Policy & Governance
- Workflow Coordination
- Portfolio Context
- Project Provisioning & Provider Integration
- Execution & Verification
- Knowledge, Context & Evidence
- Event Fabric
- Observability & Audit

## Kernlogik
- Interaction steuert, führt aber nie direkt aus.
- Intent Resolution erkennt Bedeutung, nimmt aber keine Arbeit auf.
- Intake priorisiert und nimmt Arbeit auf.
- Planning entwirft Arbeit.
- Workflow steuert Arbeit über Zeit.
- Portfolio hält Struktur und Dependencies.
- Execution arbeitet nur im expliziten Scope.
- Knowledge liefert Kontext und Wiederverwendung.
- Policy & Governance setzt Verbindlichkeit.
- Event Fabric transportiert Signale.
- Observability beschreibt das System.
