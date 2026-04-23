# ADR-0009: AGENTS.md als Quelle, CLAUDE.md als Symlink

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §8.5`, `AGENTS.md`

## Kontext und Problemstellung

Das Projekt soll sowohl von **Claude Code** (liest `CLAUDE.md`) als auch von
**Codex CLI** (liest `AGENTS.md` nativ) produktiv genutzt werden. Die
Pflege zweier paralleler Instruktions-Dateien erzeugt Drift-Risiko; eine
einzige Instruktionsquelle ist klar vorzuziehen.

## Entscheidungstreiber

- 2025–2026-Konvergenz auf `AGENTS.md` als Cross-Tool-Standard.
- Claude Code folgt Symlinks — `ln -s AGENTS.md CLAUDE.md` macht Claude Code
  die Datei verfügbar, ohne sie zu duplizieren.
- Git-nativer Symlink; kein Tooling-Special-Case.
- Tool-spezifische Ergänzungen bleiben in `.claude/` bzw. `.codex/`
  — keine Fusion tool-spezifischer Details in die geteilte Quelle.

## Erwogene Optionen

1. **Nur `CLAUDE.md`**, Codex CLI ignoriert.
2. **Nur `AGENTS.md`**, Claude Code ignoriert.
3. **Beide getrennte Dateien mit kopiertem Inhalt** — manuell synchron halten.
4. **`AGENTS.md` als Quelle, `CLAUDE.md` als Symlink**.
5. **Template-Generator** produziert beide aus einem gemeinsamen YAML.

## Entscheidung

Gewählt: **Option 4 — AGENTS.md + Symlink**.

### Konsequenzen

**Positiv**
- Single Source of Truth, Drift ausgeschlossen.
- Git behandelt Symlinks nativ.
- Funktioniert auf Unix-Derivaten ohne Sondertooling.
- Tool-spezifische Details (Skills, Commands, Permission-Modell, Hooks,
  Codex-Profile) bleiben in `.claude/` bzw. `.codex/`.

**Negativ**
- Windows-native Git-Repos ohne Symlink-Unterstützung benötigen Workaround
  (für dieses Projekt nicht relevant — Zielplattform macOS/Linux).
- Konvention ist jung; möglicherweise Änderungen in H2/2026.

## Pro und Contra der Optionen

| Option | Drift-Risiko | Tooling-Aufwand | Future-Proofness |
|---|---|---|---|
| Nur CLAUDE.md | kein Codex | null | claude-only |
| Nur AGENTS.md | Claude liest nicht | null | codex-first |
| Beide manuell | hoch | manuell | fragil |
| AGENTS.md + Symlink | null | git-nativ | gut |
| Template-Gen | keins | Buildschritt | komplex |

## Scope-Grenze

- **In AGENTS.md** gehören: Repo-Zweck, Spec-Einstiegspfad, harte
  Konventionen, erlaubte/verbotene Aktionen, Commit-Stil, Sprache.
- **Nicht in AGENTS.md**: Tool-Konfiguration (gehört in `.claude/settings.json`
  bzw. `.codex/config.toml`), komplette Specs (gehören nach `docs/spec/`),
  Quellensammlungen (gehören nach `docs/research/`).

## Referenzen

- `docs/research/17-agent-repo-prep.md` — Agent-Repo-Konventionen
- Kedro Issue #5408 — Referenzbeleg für AGENTS.md-Pattern
- Anthropic Docs — CLAUDE.md-Konventionen
