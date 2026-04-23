# Implementation Handoff for Codex CLI and Claude Code

## Zweck
Dieses Dokument gibt Codex CLI und Claude Code einen sauberen Startpunkt.

## Was zuerst zu respektieren ist
1. Das System ist kein Chatbot und keine Session-Bridge.
2. Messenger/Control Surface ist nur Adapter.
3. Portfolio-Struktur und Workflow-Prozess sind getrennt.
4. Work Item und Workflow sind getrennte Objekte.
5. Nur Policy & Governance darf Verbindlichkeit herstellen.
6. Execution ist bounded und nie Systemsteuerung.
7. Knowledge liefert Kontext, aber keine Bindung.
8. Jeder Primärzustand hat genau einen Besitzer.
9. Cross-Project-Wirkung braucht explizite Struktur.
10. Externe Modelle müssen übersetzt werden.

## Was nicht passieren darf
- Workflow wird zum Monolithen
- Knowledge wird zur Schatten-Policy
- Event Fabric wird zur Business-Wahrheit
- Provider-/Tool-Semantik prägt direkt das Kernmodell
- Execution bekommt stille projektübergreifende Autorität
- lokale Replikationen verdrängen Referenzen
