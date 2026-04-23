# Changelog

Alle signifikanten Änderungen an der Spezifikation werden hier dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versionen folgen [Semantic Versioning](https://semver.org/) für Specs
(Major = Breaking Change im Datenmodell oder in Modul-Grenzen,
Minor = additiv, Patch = Klarstellungen/Fixes).

## [0.1.0-draft] — 2026-04-23

### Added
- `docs/spec/SPECIFICATION.md` — V1-Spec in arc42-Struktur.
- `docs/decisions/0001-0009` — 9 MADR-Architekturentscheidungen.
- `docs/research/01-15` — 15 Research-Briefs (Tier A–D).
- `docs/research/16-17` — 2 Research-Briefs zu Doku-Struktur und
  Agent-Repo-Preparation (Tier E).
- `docs/research/99-synthesis.md` — Synthese der Research-Briefs als Brücke
  zur Spec.
- `AGENTS.md` als Single-Source-of-Truth für Agent-Instruktionen,
  `CLAUDE.md` als Symlink darauf.
- `.claude/` und `.codex/` Projekt-Konfigurationen für Claude Code bzw.
  Codex CLI.
- `.mcp.json` mit Filesystem- und GitHub-MCP-Servern.
- `.claude/skills/spec-navigator/` als Progressive-Disclosure-Skill.
- `.claude/agents/spec-reviewer.md` als read-only Subagent für
  Konsistenz-Checks.
- `GLOSSARY.md` als zentrales Glossar.
- `README.md`, `ARCHITECTURE.md` als Einstiegspunkte.
- `archive/` mit den ursprünglichen 12 Brainstorm-Notizen, `REVIEW.md` und
  `12-open-questions.md` (nicht mehr normativ).

### Changed
- Modul-Schnitt: 13 Bounded Contexts → **5 Module** (Interaction, Work,
  Execution, Knowledge, Portfolio).
- Kernobjekte: 12 → **9**. Entfallen: `Approval` (Flag am Work Item),
  `Context Bundle` (Funktion in Knowledge), `Provider Binding` (Property
  an Run). `Workflow` umbenannt zu `Run`.
- Standards-Lifecycle: 6 → **4 Stufen**.
- Trust-Zonen: 6 → **4 Zonen**.

### Removed
- Legacy-Status für `archive/legacy-notes/` — nicht löschen, nicht mehr
  normativ.
- `Evidence.trust_class` (Kategorienfehler).
- Eigenständige Kontexte: Identity/Trust/Access, Intent Resolution,
  Event Fabric, Observability/Audit, Project Provisioning/Provider
  Integration (alle als Querschnitt oder Property integriert).
