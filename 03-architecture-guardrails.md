# Architecture Guardrails

## Zweck
Dieses Dokument verdichtet die Referenzarchitektur in prüfbare Leitplanken.

## Muss-Regeln
1. Interaktion darf nie direkt Ausführung auslösen.
2. Jeder fachlich relevante Zustand hat genau einen Primärbesitzer.
3. Projektstruktur und Prozesszustand bleiben getrennt.
4. Work Item und Workflow bleiben getrennte Objekte.
5. Planung bleibt von Orchestrierung getrennt.
6. Nur Policy & Governance darf Verbindlichkeit herstellen.
7. Ausführung bleibt bounded.
8. Externe Semantik wird immer übersetzt.
9. Events sind Signale, keine Fachwahrheit.
10. Projektübergreifende Wirkung braucht explizite Struktur.
11. Beobachtung ist keine Regel.
12. Technischer Zugriff ist nicht fachliche Erlaubnis.
13. Menschliche Eskalation ist Ausnahme, nicht Default.
14. Reference geht vor Replikation.
15. Execution liefert lokale Resultate, aber keine globale Wahrheit.

## Darf-nicht-Regeln
- Interaction darf keine Projektzustände setzen.
- Intent Resolution darf keine operative Arbeit starten.
- Intake darf keine Detailplanung übernehmen.
- Planning darf keine Prozesssteuerung übernehmen.
- Workflow darf keine Projektstruktur besitzen.
- Portfolio darf keine Workflowhistorie besitzen.
- Knowledge darf keine Verbindlichkeit herstellen.
- Execution darf keine projektübergreifende Wirkung stillschweigend erzeugen.
- Observability darf keine operative Fachentscheidung ersetzen.
- Event Fabric darf nie Source of Truth für Fachzustand sein.

## Nicht verhandelbare Invarianten
- Kein Direktpfad von Control Surface zu Execution
- Kein zweiter Primärbesitzer für denselben Zustand
- Keine implizite Cross-Project-Kopplung
- Keine Bindung ohne Governance
- Kein Event als Ersatz für Domänenwahrheit
- Keine Ausführung ohne expliziten Scope
- Keine stille Standardisierung aus erfolgreicher Praxis
- Keine Vermischung von Struktur- und Prozesswahrheit
