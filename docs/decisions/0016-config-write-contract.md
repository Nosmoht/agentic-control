# ADR-0016: Config Write Contract for Dispatch and Execution

* Status: accepted
* Date: 2026-04-26
* Context: `docs/spec/SPECIFICATION.md §5.7 (Runtime Records), §8
  (Querschnittliche Konzepte)`; F0005, F0006, F0007.

## Kontext und Problemstellung

V0.2.0 ff. haben mehrere normative YAML-Konfigurationsdateien als
Schnittstelle zwischen Tooling und Runtime etabliert:
`routing-pins.yaml`, `model-inventory.yaml`, `tool-risk-inventory.yaml`,
`benchmark-task-mapping.yaml` und (in F0005) `pending-proposals.yaml`.
F0005 schreibt aktiv in `routing-pins.yaml` und `model-inventory.yaml`;
F0006 und F0007 werden weitere Lese-/Schreib-Pfade hinzufügen.

Der dritte Codex-Follow-up-Review-2026-04-26 hat als Befund 3 (Hoch)
festgehalten, dass F0005 Config-Writes ohne Vertrag durchführt:

- kein Atomic-Write (Crash zwischen `open`/`write`/`close` erzeugt
  halbe Dateien).
- kein File-Lock (parallele Writes oder Read-during-Write können
  inkonsistente Zustände erzeugen).
- kein Diff-/Hash-Audit (schwer rückzuverfolgen, was sich wann
  änderte).
- keine Conflict-Detection (User editiert manuell + F0005 schreibt
  → Last-Write-Wins-Verlust).

Ohne expliziten Vertrag werden diese Fehlerklassen sich vervielfachen,
sobald F0005/F0006/F0007 implementiert sind.

## Entscheidungstreiber

- Reproduzierbarkeit von Config-Änderungen über Git-History.
- Sicherheits- und Audit-Anforderung: jeder Config-Write muss als
  `AuditEvent` (ADR-0011) erscheinen.
- n=1: Single-Writer-Annahme reicht für V1, aber Last-Write-Wins ist
  zu fragil für gleichzeitige CLI- + Editor-Sessions.
- Forward-Kompatibilität: bei späteren Multi-Writer-Szenarien (v2+)
  soll der Vertrag erweiterbar sein.

## Erwogene Optionen

1. **Inline in F0005** als Acceptance Criterion — bündelt nur den
   F0005-Schreibpfad.
2. **Eigener ADR mit Vertrag für alle Config-Schreiber** (gewählt) —
   kohärent, von F0005/F0006/F0007 zitierbar.
3. **SQLite statt YAML** für alle Configs — würde Atomic-Writes durch
   die DB lösen, aber CLI-Edit + Git-Diff gingen verloren.
4. **Externe Lockfile-Bibliothek ohne eigenes Schema** — partial;
   Conflict-Detection und Audit fehlen weiterhin.

## Entscheidung

Gewählt: **Option 2** — eigener Vertrag mit vier Garantien.

### Vier Garantien

1. **Atomic Write.** Schreibvorgang läuft als read-into-memory →
   modify in-memory → serialize-to-tmp-file (`<file>.tmp.<pid>`) →
   `fsync` → `rename`. Crash während Phase 1–4 hinterlässt nur die
   tmp-Datei (ignorierbar, beim nächsten Start wird sie aufgeräumt);
   Crash nach `rename` lässt die Datei konsistent.
2. **File Lock.** Während des gesamten read-modify-write-Vorgangs
   wird ein POSIX-File-Lock (`fcntl(LOCK_EX)`) auf der Zieldatei
   gehalten. Andere CLI-Sessions blockieren oder fehlschlagen mit
   `EWOULDBLOCK` und einer `agentctl`-Fehlermeldung („Locked by PID
   X — wait or retry").
3. **Optimistic Version Check.** Jede normative Config-Datei trägt
   ein `version: int` und/oder `updated: ISO-8601`-Feld in der
   YAML-Wurzel. Vor dem `rename`-Schritt wird die Datei erneut
   gelesen; wenn `version` oder `updated` sich seit dem ersten Read
   geändert haben → `ConflictDetected`-Fehler, kein Write, keine
   teilweise modifizierten Daten. Nutzer muss erneut anstoßen
   (typisch `agentctl dispatch review` + `accept`).
4. **Audit Event.** Jeder erfolgreiche Write erzeugt einen
   `AuditEvent`-Record (ADR-0011) mit den Pflichtfeldern:
   - `subject_ref`: Pfad zur Config-Datei.
   - `before_hash`: SHA-256 des Inhalts vor Modifikation.
   - `after_hash`: SHA-256 des Inhalts nach Modifikation.
   - `actor`: CLI-Befehl (z. B. `agentctl dispatch accept p-12`).
   - `reason`: optional Freitext (z. B. „F0005 accept proposal X").

### Geltungsbereich

Der Vertrag gilt für jede Konfigurations-/State-Datei, die als
normativ zitiert wird:

- `config/dispatch/routing-pins.yaml`
- `config/dispatch/model-inventory.yaml`
- `config/dispatch/benchmark-task-mapping.yaml`
- `config/dispatch/pending-proposals.yaml` (F0005)
- `config/execution/tool-risk-inventory.yaml`

**Nicht im Vertrag:**

- `state.db` (SQLite-WAL-Mode löst Atomic-Writes selbst, ADR-0003).
- JSONL-Logs (append-only, Atomic-Append durch `O_APPEND`).
- Markdown-Dokumente (manuelle Pflege via Git, kein
  Maschinen-Schreibpfad).

### YAML-Wurzel-Konvention

Alle normativen Configs tragen pro V0.3.0-draft mindestens **ein** der
folgenden Felder in der Wurzel:

```yaml
version: 1          # Integer, monoton, bei jedem Schreibvorgang +1
updated: 2026-04-26 # ISO-8601-Datum oder -Timestamp
```

Bestehende Configs:
- `model-inventory.yaml` hat `version: 2` ✓ (V0.2.3-draft).
- `tool-risk-inventory.yaml` hat `version: 1`, `updated: 2026-04-25` ✓
  (V0.2.3-draft).
- `benchmark-task-mapping.yaml` hat `version: 1`, `updated: 2026-04-26`
  ✓ (V0.2.4-draft).
- `routing-pins.yaml` hatte initial keine Version — bei der ersten
  F0005-Implementierung wird der Header ergänzt (Best-Effort-Migration
  in F0005).

### Konsequenzen

**Positiv**

- F0005, F0006, F0007 zitieren den Vertrag statt jeweils eigene
  Schreibsemantik zu definieren.
- AuditEvent-Spur deckt alle Config-Änderungen ab.
- Forward-Pfad zu Multi-Writer-Szenarien existiert (Lock-Semantik
  identisch).

**Negativ**

- File-Locks unter Windows verhalten sich anders (V1 ist Linux/macOS,
  Windows-Support nur Best-Effort).
- Der Vertrag erzeugt kleinen Lese-Overhead (Re-Read vor `rename` für
  Conflict-Check).
- Bei sehr großen Config-Dateien wäre der parse-modify-serialize-
  Loop teuer — V1-Configs sind klein (~100–500 Zeilen).

### Follow-ups

- Concurrency-Mehrleser-Tests, sobald F0005/F0006 implementiert sind.
- Optionaler Schemaversion-Migration-Pfad bei Schema-Änderungen
  (Best-Effort jetzt: `version`-Bump im YAML-Wurzel + Schema-
  Validator pro Datei).
- Windows-File-Lock-Semantik dokumentieren, sobald V1 dort getestet
  wird.

## Referenzen

- ADR-0003 — SQLite + Litestream (state.db ist außerhalb dieses
  Vertrags)
- ADR-0011 — Runtime Records (`AuditEvent`)
- ADR-0014 — Peer Adapters (`model-inventory.yaml` lebt unter diesem
  Vertrag)
- ADR-0015 — Tool-Risk-Inventory (`tool-risk-inventory.yaml` lebt
  unter diesem Vertrag)
- F0005, F0006, F0007 — Konsumenten
- Counter-Counter-Review-2026-04-26 — Befund 3 (Hoch, F0005-Config-
  Writes ohne Vertrag)
