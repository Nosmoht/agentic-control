# Personal Agentic Control System — Documentation

Dieses Repo enthält die Spezifikation und die Recherche-Grundlage für ein
persönliches, agenten-gestütztes Multi-Projekt-Steuerungssystem. Primärnutzer
sind der Repo-Besitzer sowie **Claude Code** und **Codex CLI**, die auf
Basis dieser Dokumentation Implementierungsarbeit ausführen sollen.

Stand: **V0.3.3-draft** (2026-04-27). Noch kein Code; das Repo enthält
ausschließlich Spezifikation und Forschung.

## Einstiegspfad

| Zweck | Datei |
|---|---|
| Überblick (du bist hier) | `README.md` |
| Architektur (arc42) | [`docs/spec/SPECIFICATION.md`](docs/spec/SPECIFICATION.md) |
| Architekturentscheidungen (MADR) | [`docs/decisions/`](docs/decisions/) |
| Research-Briefs (Evidenz) | [`docs/research/`](docs/research/) |
| Synthese (Research → Spec-Brücke) | [`docs/research/99-synthesis.md`](docs/research/99-synthesis.md) |
| Glossar | [`GLOSSARY.md`](GLOSSARY.md) |
| Agent-Konventionen | [`AGENTS.md`](AGENTS.md) (= `CLAUDE.md`) |
| Änderungshistorie | [`CHANGELOG.md`](CHANGELOG.md) |
| Historische Notizen | [`archive/`](archive/) |

## Schnellnavigation für Agenten

Claude Code / Codex CLI: erst [`AGENTS.md`](AGENTS.md) lesen. Für
spec-spezifische Aufgaben nutzt der
[`spec-navigator`](.claude/skills/spec-navigator/SKILL.md)-Skill die
Progressive-Disclosure-Regel.

## Status

Dieses Repo ist **reine Dokumentation**. Es enthält *keine* Implementierung.
Code entsteht in einem separaten Repo (oder Unterordner), sobald V0-MVP
begonnen wird — siehe `docs/spec/SPECIFICATION.md §Anhang A` (MVP-Staging).

## Sprache

Alle Dokumente sind in **Deutsch** verfasst. Zitate, Titel fremder Quellen
und technische Kennungen (Code-Identifier, CLI-Flags, Pfade) bleiben
original.

## Struktur

```
/
├── README.md                 # Einstieg (diese Datei)
├── ARCHITECTURE.md           # Architektur-Überblick, Pointer in docs/spec/
├── AGENTS.md                 # Agent-Konventionen (CLAUDE.md = Symlink)
├── CLAUDE.md                 # → AGENTS.md
├── GLOSSARY.md               # Zentrales Glossar
├── CHANGELOG.md              # Spec-Versionshistorie
│
├── docs/
│   ├── spec/                 # V1-Spezifikation (arc42)
│   ├── decisions/            # MADR Architektur-Entscheidungen
│   └── research/             # 17 Research-Briefs + Synthese
│
├── archive/                  # Historische Notizen, nicht mehr normativ
│
├── .claude/                  # Claude-Code-spezifische Konfiguration
├── .codex/                   # Codex-CLI-spezifische Konfiguration
└── .mcp.json                 # MCP-Server-Konfiguration (Projekt-Scope)
```
