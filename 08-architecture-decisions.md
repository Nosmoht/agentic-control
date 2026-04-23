# Architecture Decisions

## AD-01 — Das System ist ein persönliches Multi-Projekt-Steuerungssystem
Kein Chatbot, keine reine Session-Bridge, sondern ein persönliches Agentic Portfolio System.

## AD-02 — Messenger ist nur Control Surface
Messenger oder andere Kontrollkanäle sind reine Interaktionsadapter und nie Source of Truth.

## AD-03 — Die Architektur ist capability-first
Die Architektur wird aus erforderlichen Fähigkeiten abgeleitet, nicht aus Tool-Denkmodellen.

## AD-04 — Portfolio-Struktur und Prozesssteuerung bleiben getrennt
Portfolio besitzt Projekt- und Dependency-Struktur, Workflow besitzt Ablaufzustände.

## AD-05 — Work Item und Workflow sind unterschiedliche Objekte
Work Item = fachliches Arbeitsobjekt, Workflow = prozessuale Steuerinstanz.

## AD-06 — Planung ist eine eigene Domäne
Planning liegt zwischen Intake und Workflow.

## AD-07 — Policy & Governance sind getrennt von Knowledge
Knowledge hält Beobachtungen, Entscheidungen, Standards, Evidenz und Kontext.
Policy & Governance entscheidet über Verbindlichkeit.

## AD-08 — Nur Policy & Governance darf Verbindlichkeit herstellen
Keine andere Domäne darf Bindung oder globale Regelgeltung erzeugen.

## AD-09 — Execution ist bounded und nie selbst Systemsteuerung
Execution arbeitet nur auf expliziten Auftrag, in explizitem Scope und mit expliziten Grenzen.

## AD-10 — Externe Modelle werden immer übersetzt
Provider-, Messenger- und Tool-Semantik darf das Kernmodell nicht ungefiltert prägen.

## AD-11 — Event Fabric ist nie Business Authority
Events transportieren Änderungen und Signale, sind aber keine fachliche Wahrheit.

## AD-12 — Jeder relevante Zustand hat genau einen Primärbesitzer
Source of Truth wird hart entlang der Domänengrenzen zugewiesen.

## AD-13 — Human escalation ist Ausnahme, nicht Standard
Vor Eskalation werden Clarify, Retry, Wait, Replan oder Reject geprüft.

## AD-14 — Cross-Project-Abhängigkeiten müssen explizit und evidenzgebunden sein
Keine informellen Dependencies aus Chatverlauf oder Agent-Memory.

## AD-15 — Lernen verändert das System nur über kontrollierte Promotion
Learning läuft über Beobachtung, Klassifikation, Evidenz, Kandidat, Review, optionalen Standard und optionale Bindung.

## AD-16 — Vertrauen wird zonenbasiert modelliert
Die Architektur unterscheidet untrusted input, interpreted control, decision core, restricted execution und trusted retention/audit.

## AD-17 — Reference geht vor Replikation
Kontextübergreifende Zusammenarbeit erfolgt bevorzugt über stabile Identitäten statt über breite lokale Kopien.
