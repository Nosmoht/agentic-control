# Agent Conventions

Diese Datei ist die **einzige Quelle** für Instruktionen an Agent-Tools
(Claude Code, Codex CLI). `CLAUDE.md` ist ein Symlink auf diese Datei.

## Was dieses Repo ist

Ein **Dokumentations-Repo** — keine Implementierung. Es spezifiziert V1 eines
persönlichen agentischen Steuerungssystems. Die V1-Spec ist in
[`docs/spec/SPECIFICATION.md`](docs/spec/SPECIFICATION.md).

Stand: **V0.1.0-draft**, 2026-04-23. Noch kein Code.

## Sprache

- Alle Dokumente sind in **Deutsch** verfasst.
- Technische Kennungen (Code, Pfade, CLI-Flags, API-Namen) bleiben original.
- Zitate fremder Quellen bleiben in Originalsprache.
- Commit-Messages auf Englisch (Conventional Commits, z. B. `docs(spec): …`).

## Verbindliche Konventionen

### Architektur-Entscheidungen

- Jede neue fachliche Entscheidung, die Verhalten ändert, bekommt ein
  MADR-Dokument in `docs/decisions/` (NNNN-titel.md, fortlaufend).
- Vor der Entscheidung: lies existierende ADRs; widersprich nicht, ohne zu
  begründen oder superseden.
- MADR-Format: Status, Context, Drivers, Options, Decision, Consequences,
  References.

### Spezifikation pflegen

- `docs/spec/SPECIFICATION.md` ist **normativ**.
- Änderungen der Spec brauchen einen CHANGELOG-Eintrag (`CHANGELOG.md`).
- Neue Aussagen, die nicht trivial sind, müssen auf Research-Briefs
  (`docs/research/NN-*.md`) verweisen oder explizit als **Eigenentscheidung**
  markiert werden.

### Legacy nicht wiederbeleben

- `archive/legacy-notes/` (alte Notizen 00–11) und `archive/REVIEW.md` sind
  **nicht mehr normativ**. Nicht als Quelle für neue Spec-Entscheidungen
  nehmen.
- Wenn ein Konzept aus Legacy doch auftauchen muss: über die Synthese
  (`docs/research/99-synthesis.md`) zitieren, nicht direkt.

### Commit-Disziplin

- Scoped Conventional Commits: `docs(spec): …`, `docs(adr): …`,
  `docs(research): …`, `chore: …`.
- Keine Issue-Tracker-Referenzen im Commit-Body (siehe User-Konvention).
- Commit-Messages sind self-contained.

### Permissions und Sicherheit

- Nie auto-push ohne explizite Nutzer-Freigabe.
- Nie `.env`, `credentials*`, `~/.ssh`-Inhalte lesen oder loggen.
- Niemals Hooks in `.claude/settings.json` anlegen (RCE-Klasse aus
  CVE-2025-59536; siehe ADR-0006).

## Typische Aufgaben

### Spec erweitern

1. Research-Evidenz zu `docs/research/NN-thema.md` ergänzen.
2. Entscheidung als ADR in `docs/decisions/NNNN-thema.md` festhalten.
3. Spec aktualisieren, auf ADR verweisen.
4. `CHANGELOG.md` ergänzen.

### Research-Brief hinzufügen

- Format: YAML-Frontmatter (`topic`, `tier`, `date`, `status`) + arc42-artige
  Abschnitte (Forschungsfrage, Methodik, Befunde, Quellenbewertung,
  Implikationen, Offene Unsicherheiten, Quellen).
- Sprache: Deutsch. Quellen: Deutsch oder Englisch (original).
- Quellenregel: ≥ 2 unabhängige, ≥ 1 Tier-1/2.

### ADR schreiben

- MADR-Template (siehe bestehende ADRs 0001–0009 für Muster).
- Status: `accepted` wenn Entscheidung getroffen; sonst `proposed`.
- Konsequenzen ehrlich beschreiben (positiv, negativ, neutral).
- Auf Research-Briefs als Evidenz verweisen.

### Legacy-Notiz löschen

- Nicht löschen. Zurück ins Archiv verschieben, wenn versehentlich außerhalb.

## Progressive Disclosure

Wenn du nicht alles laden willst: nutze den
[`spec-navigator`](.claude/skills/spec-navigator/SKILL.md)-Skill (Claude Code),
der gezielt Sektionen der Spec oder ADRs zieht, statt alles zu laden.

## Fragen, die ich beantworten kann (ohne Verweis auf externe Quellen)

- „Welche Module gibt es?" → ARCHITECTURE.md oder SPECIFICATION.md §5
- „Welches Tool für Durable Execution?" → ADR-0002 (DBOS)
- „Wie ist die Sandbox?" → ADR-0006 (8 Schichten)
- „Wie läuft HITL?" → ADR-0007

## Fragen, bei denen ich auf Research verweise

- Kostenanker, Pricing-Details → `docs/research/13-cost.md`
- Framework-Vergleich (Temporal/Restate/DBOS) → `docs/research/03-durable-execution.md`
- Sandbox-Details & CVEs → `docs/research/07-trust-sandboxing.md`

## Bekannte Lücken

Siehe `docs/spec/SPECIFICATION.md §11.3` (Offene Entscheidungen) und
`archive/12-open-questions.md` (historisch, ggf. überholt).
