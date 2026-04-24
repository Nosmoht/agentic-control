# ADR-0013: V1 Deployment Mode

* Status: accepted
* Date: 2026-04-24
* Context: `docs/spec/SPECIFICATION.md §7`; klärt Widerspruch aus Counter-Review.

## Kontext und Problemstellung

Die V1-Spec §7 beschreibt zwei Betriebsmodi:
- Laptop-only: SQLite + DBOS embedded.
- Laptop + VPS: SQLite + Litestream + „spiegelnde Instanz, Messenger-Bridge".

ADR-0003 sagt: „Postgres wird Pflicht, sobald > 1 Prozess gleichberechtigt
schreibt." Eine spiegelnde Instanz ist **genau dieser Fall**, wenn sie
schreiben soll.

Der Counter-Review (Befund 1) hat diesen Widerspruch als kritisch markiert.

## Entscheidungstreiber

- Klarheit für den Implementierer, welcher Modus wann gilt.
- Minimaler Operations-Aufwand für n=1.
- Klarer Upgrade-Pfad ohne Datenmigration bei Wechsel.
- Keine stillen Write-Konflikte (Dual-Write-Fehlerklasse).

## Erwogene Optionen

1. Nur lokal-only in V1; VPS verschieben.
2. SQLite + Litestream mit „spiegelnder VPS-Instanz" read-only belassen
   (unklar in Spec).
3. **Drei klar getrennte Stages: v1a lokal-only, v1b read-only Bridge, v2+
   Postgres.**
4. Von Anfang an Postgres — zu viel Overhead für n=1.

## Entscheidung

Gewählt: **Option 3**.

### Drei Deployment-Stages

**v1a — Lokal-only**
- Ein Prozess, SQLite WAL + Litestream → Object Storage (Hetzner Object
  Storage oder S3-kompatibel).
- DBOS in-process. Keine zweite Schreibrolle.
- Claude Code + Codex CLI als lokale Subprozesse.
- Control Surface: CLI (`agentctl`).
- Backup: Litestream continuous.
- Exit-Kriterium: 5+ Work Items durchgezogen, 0 Runaway-Vorfälle.

**v1b — Lokal + read-only Bridge** (optional)
- v1a + zusätzliche Prozess-Instanz auf VPS (Hetzner CX22 ~5 USD/Monat) oder
  lokaler Zweitprozess.
- Die Zweit-Instanz ist **strikt read-only**: sie liest aus Litestream-
  Restore, schreibt **nicht** in die SQLite-DB.
- Zweck: Messenger/Mail-Adapter kann Inbox-Cards ausliefern, ohne
  Schreibzugriff zu brauchen.
- Wenn der Nutzer Approve/Reject via Messenger schickt, wird die Antwort
  **lokal** in die primäre SQLite geschrieben, nicht auf dem VPS.
- Exit-Kriterium: Bridge-Latenz < 5 min, keine Write-Konflikte.

**v2+ — Postgres**
- Ausgelöst **nicht** durch Datenvolumen, sondern durch zweiten schreibenden
  Prozess oder Host.
- Triggers:
  - Messenger-Bridge soll durable reagieren und schreiben (nicht nur
    Inbox-Read).
  - Zweiter lokaler Prozess will paralleles Write-Locking umgehen.
  - Sustained Writes > 50/s (praktisch nie für n=1, dokumentiert aus
    Vollständigkeit).
- Migration: einmaliger `pg_dump`-Import aus SQLite. DBOS-Schema portabel.
- Exit: Postgres läuft, Migration erfolgreich, keine SQLite-Rückstände.

### Entscheidungsregel

| Szenario | Modus |
|---|---|
| Laptop, ein User, alles lokal | v1a |
| Laptop + Messenger-Adapter, aber Nutzer antwortet nur am Laptop | v1a + optional v1b |
| Zweite schreibende Rolle (Messenger-Daemon, Webhook-Empfänger, paralleler Agent-Host) | v2+ (Postgres) |

### Konsequenzen

**Positiv**
- Widerspruch in Spec §7 geschlossen.
- Nutzer kann v1a nutzen, ohne VPS zu mieten.
- Read-only Bridge ist legitime Zwischenstufe ohne Postgres-Zwang.
- Upgrade-Pfad zu Postgres ist expliziter Event, nicht Geröllfläche.

**Negativ**
- v1b erfordert Litestream-Restore-Latenz-Toleranz (typisch Minuten).
- Nutzer muss sich ggf. bewusst für v2+ entscheiden — kein automatischer
  Upgrade.

### Follow-ups

- Benchmark der Litestream-Restore-Latenz für typische DB-Größen (offen in
  ADR-0003).
- Falls v1b tatsächlich gewünscht wird: eigenes Feature-File.

## Referenzen

- Spec §7 (Verteilungssicht)
- ADR-0003 — SQLite + Litestream + Postgres-Upgrade-Pfad
- ADR-0002 — DBOS
- `docs/research/12-persistence.md` — Stack-Kosten, Litestream-Eigenschaften
- Counter-Review (2026-04-23) Befund 1
