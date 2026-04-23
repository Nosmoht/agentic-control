---
topic: agent-repo-prep
tier: E
date: 2026-04-23
status: draft
---

# Brief 17: Agent-Repo-Preparation fuer Claude Code und Codex CLI

## Forschungsfrage
Welche Dateien, Konfigurationen und Konventionen braucht ein Repo 2025–2026,
damit Claude Code und Codex CLI die enthaltene Dokumentation effektiv
konsumieren und dabei projektspezifische Konventionen einhalten? Speziell:
Was ist Tier-1-Konvention, wo divergieren die beiden Tools, was ist
Anti-Pattern, und wie wird der vorhandene Spec-Bestand ohne Token-Bloat
exponiert?

## Methodik
Basis: Briefs 01 und 02 — Tier-1-Belege zu Claude-Code-/Codex-Internals
bereits validiert, werden nicht redupliziert. Drei Such-Zyklen zu Lücken:
AGENTS.md-Konvention, CLAUDE.md-Token-Budget, Symlink-Pattern,
MCP-Auswahl, reale Beispiele. Primär: `code.claude.com/docs`,
`developers.openai.com/codex`, `github.com/anthropics/skills`,
`github.com/openai/codex`. Sekundär: Tessl/Augment/SSW-Rules, Builder.io-
und Desktop-Commander-Blogs. Cutoff 2025-10-23, Ausnahme offizielle Docs.

## Befunde

### Claude Code — Artefakte im Repo
- **`CLAUDE.md`** (Projekt-Root, optional `.claude/CLAUDE.md`): wird bei
  jedem Session-Start in den System-Prompt geladen — kostet Tokens ab
  Turn 1. Zielgroesse laut offiziellen Best Practices und Community-
  Konsens: **< 200 Zeilen / ≤ ~500 Tokens** fuer den Core; darueber hinaus
  via `@pfad/zu/datei.md`-Imports in Skills/Referenzen auslagern[^1][^2].
  Inhalt: Tech-Stack, Repo-Layout, Befehle (build/test/lint), Hard-
  Konventionen, Verweise auf die Spec. **Nicht hierein**: Prozedur-
  Wissen (→ Skill), externe API-Semantik (→ MCP-Server-Doku).
- **`.claude/skills/<name>/SKILL.md`**: YAML-Frontmatter (`name`,
  `description`/`when_to_use` ≤ 1 536 Zeichen, `allowed-tools`) + Body.
  Body wird erst beim Invoke geladen (progressive disclosure, ~30–50
  Tokens Startup-Overhead pro Skill)[^3][^2]. Fuer alles Prozedurale,
  das reproduzierbar ausgefuehrt werden soll.
- **`.claude/commands/<name>.md`**: Slash-Command; 2026 mit Skills
  vereinheitlicht (dieselbe Datei in beiden Ordnern erzeugt `/name`).
  Commands fuer User-getriggerte Kurz-Workflows, Skills fuer alles mit
  Scripts/Assets[^3][^4].
- **`.claude/agents/<name>.md`**: Subagent-Definition (eigenes Kontext-
  Fenster, eigene Tool-Rechte, kein weiterer Spawn). Nutzen: Reviewer,
  Red-Team, Verifier — Isolation schuetzt den Haupt-Thread[^4].
- **`.claude/settings.json`** (eingecheckt) vs. `.claude/settings.local.json`
  (gitignored, persoenliche Overrides): Permission-Regeln
  (`allow`/`ask`/`deny`, Format `Tool(specifier)`), `permissionMode`,
  Hooks, Env-Flags. Evaluierung: deny → ask → allow[^4].
- **Hooks** (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`,
  `SessionStart`, `PreCompact` u.a.): projektsinnvoll sind i.d.R.
  `PreToolUse`-Guards (z.B. Format/Lint vor Write) und `Stop`-Hooks fuer
  Artefakt-Generierung. Eingecheckte Hooks sind aber **Code-Execution-
  Primitiv mit User-Rechten**; CVE-2025-59536 und CVE-2026-21852 sind
  konkrete RCE/Exfil-Klassen[^4]. Faustregel: nur Hooks einchecken, die
  man auch als Build-Script einchecken wuerde.
- **`.mcp.json`** (Projekt-Scope, eingecheckt): `mcpServers`-Map mit
  `command`/`args`/`env` (stdio) oder `url`/`headers` (http/sse).
  `${VAR}`-Expansion. Precedence Local > Project > User > Plugin[^4].
  Projekt-Scope nur fuer Server, die **das Team** braucht — pro-Entwickler-
  Tools gehoeren in User-Scope.

### Codex CLI — Artefakte im Repo
- **`AGENTS.md`** (Repo-Root, zusaetzlich in Unterordnern moeglich): offizielle,
  werkzeuguebergreifende Konvention[^5][^6]. Discovery-Kette: `~/.codex/
  AGENTS.override.md` → `~/.codex/AGENTS.md` → Repo-Root → naechstliegendes
  Unterverzeichnis. Codex zitiert die geladenen Items sichtbar, bevor es
  arbeitet[^5]. Inhaltslinie (belegt durch `openai/codex/AGENTS.md` selbst:
  ~213 Zeilen, enforcement-fokussiert[^7]): Build-/Test-Commands,
  Code-Style, Ordnerstruktur, explizite "do/don't"-Regeln. Keine Narrative.
- **`.codex/config.toml`**: laedt **nur bei "trusted projects"**; Trust-
  State aktuell in `~/.codex/config.toml` als
  `[projects."<abs-path>"].trust_level` (Issue #14601/#15433 adressieren
  VCS-Unsauberkeit)[^8]. Inhalt: Profile (`[profiles.<name>]`), MCP-
  Server, Sandbox-/Approval-Defaults.
- **`.codex/agents/<name>.toml`**: Custom-Subagent; Built-ins
  `default`/`worker`/`explorer`. Subagents erben Sandbox/Runtime des
  Parents; Default-Limits 6 Threads, Tiefe 1, 1 800 s[^9].
- **`.codex/` ist Protected Path** wie `.git` — Config-Tampering durch
  Agent-Run ausgeschlossen[^9].
- **Kein Settings-JSON-Aequivalent**: Permissions/Sandbox via CLI-Flags
  oder Profile-Eintraege.

### Cross-Cutting
**Shared vs. divergent.** `AGENTS.md` deckt den gemeinsamen Teil ab:
Projekt-Fakten, Commands, Konventionen. Claude Code liest `AGENTS.md`
nicht automatisch, kann aber **`CLAUDE.md` als Symlink auf `AGENTS.md`**
setzen — Git-nativ, funktioniert auf macOS/Linux/WSL[^10][^11]. Reiner
Claude-Content (`@imports`, `.claude/skills/`, `.claude/settings.json`,
`.claude/agents/`) bleibt Claude-exklusiv. Reiner Codex-Content
(`.codex/config.toml`, `.codex/agents/`, TOML-Profile) bleibt
Codex-exklusiv. **Nicht den ganzen `.claude/`-Ordner symlinken** — nur
`CLAUDE.md` bzw. einzelne geteilte Skills[^10].

**MCP-Server fuer docs-heavy Repo.** Konsens 2026 (Tier-1 + 2 aus
Builder.io, Fastio, Desktop-Commander):
- **Filesystem-MCP** (official `@modelcontextprotocol/server-filesystem`)
  als sichere Default-Lesebasis mit Directory-Whitelist[^12].
- **Git-MCP** (official) fuer Repo-History ohne Shell-Escape;
  read-only Default verhindert Force-Push[^12].
- **GitHub-MCP** fuer Issue-/PR-/Code-Search jenseits des lokalen
  Working-Trees (Brief-17-Kontext: GitHub ist laut User-CLAUDE.md einziger
  aktiver Tracker).
- **Obsidian-MCP** (`cyanheads/obsidian-mcp-server` oder
  `Piotr1215/mcp-obsidian` ohne App-Abhaengigkeit) **nur wenn** die Spec
  wirklich in einem Obsidian-Vault lebt[^13] — sonst ueberdimensioniert.
- **Vermeiden**: generische Fetch-Server mit uneingeschraenktem Netz,
  Google-Drive-Connector im selben Projektscope wie Secrets-lesende Tools,
  jede MCP-Gruppe > 20 k Tokens Tool-Definitionen — das kollabiert den
  effektiven Kontext[^2].

### Anti-Pattern
- **CLAUDE.md-Bloat** (> 500 Zeilen / > 2 k Tokens): Claude ignoriert
  nachweislich Teile, wenn die Datei zu lang wird[^2]. Fix: Ruthless
  Pruning, Move nach Skills, `@imports` statt Inline-Prose.
- **Duplicate Rules** in `CLAUDE.md` + `AGENTS.md` + Skill + Command:
  Jede Regel gehoert an genau eine Stelle. Symlink aufloest das fuer
  Claude/Codex; Skills aufloesen das fuer Prozedurales.
- **Ungescopte MCP-Server im Project-Scope** (`.mcp.json` bloatet Tool-
  Definitions fuer alle Entwickler — Kosten vor erster Nachricht)[^2].
- **Eingecheckte `.claude/settings.json` mit `bypassPermissions`**:
  Angriffsflaeche fuer RCE-Klasse (siehe Brief 01, CVE-Kette).
- **Stale `AGENTS.md`** mit Commands, die nicht mehr existieren: Codex
  zitiert sie sichtbar — der Agent macht Falsches und laesst es zitieren.
- **`NOS-*`/Linear-Referenzen** oder andere tote Tracker-Zeiger in Docs
  (CLAUDE.md-Globalregel des Users): Agent chased Links ins Nichts.
- **"Infinite exploration"**: Agent ohne scoped Brief auf grosses Doku-
  Set loslassen — Kontext brennt aus, ohne dass V1 geschrieben wird.

### Beispiele aus der Wildbahn
- **`openai/codex/AGENTS.md`** ~213 Zeilen, rein enforcement-orientiert
  (Code-Style, Crate-Konventionen, Test-Patterns, RPC-Naming). Kein
  Narrativ[^7].
- **`anthropics/skills`**: Public-Index mit `SKILL.md`-Template (YAML
  `name`/`description`, Sections Examples/Guidelines)[^3][^14].
- **`kedro-org/kedro` Issue #5408**: Spike zu `AGENTS.md` + Symlink
  `CLAUDE.md` ueber alle Ecosystem-Repos — Symlink als Mainstream[^10].
- Reife Projekte (Datasette, DBOS-Docs, Desktop-Commander) konvergieren
  2026 auf `AGENTS.md`-Root + tool-spezifische `.<tool>/`-Ordner.

## Quellenbewertung
- Tier 1: 7 (Anthropic-Docs, OpenAI-Developer-Docs, `openai/codex`-Repo,
  `anthropics/skills`-Repo, kedro-Issue)
- Tier 2: 3 (Tessl, Augment, SSW-Rules — Engineering-Artikel mit
  konkreten Code-Beispielen)
- Tier 3: 2 (Medium-Guide, Desktop-Commander-Blog — ergaenzend, nicht
  tragend)
- Cross-Validation: jede nicht-triviale Aussage (AGENTS.md-Discovery,
  CLAUDE.md-Budget, Symlink-Pattern, MCP-Auswahl) steht auf ≥ 1 Tier-1
  plus ≥ 1 unabhaengiger Quelle. Brief 01/02 liefern die tieferen
  Tier-1-Belege fuer Claude-Code-/Codex-Internals.

## Implikationen fuer unser Repo

**Minimum-viable Dateiliste fuer V1 (genau diese, nicht mehr):**
1. `AGENTS.md` (Root, ~100–150 Zeilen): Zweck des Repos, Spec-Einstieg
   (`99-synthesis.md`), Commands (`lint`/`test`/falls vorhanden),
   Konventionen (Scoped Conventional Commits, Englisch in Artefakten),
   Pointer zu `research/` als Tier-B-Material.
2. `CLAUDE.md` → Symlink auf `AGENTS.md` (`ln -s AGENTS.md CLAUDE.md`).
3. `.claude/settings.json`: Permission-Allowlist fuer sichere Read-/
   Search-Tools, Deny fuer `.env`/`credentials*`; kein Hook in V1.
4. `.mcp.json`: **nur** Filesystem-MCP + GitHub-MCP im Projekt-Scope.
   Obsidian-MCP, falls Vault-Integration gewollt, in User-Scope.
5. `.claude/skills/spec-navigator/SKILL.md`: beschreibt, wie die Spec-
   Dokumentation zu lesen ist (V1 = `99-synthesis.md`; `00–11` legacy;
   `research/*` Tier-B-Evidenz; `REVIEW.md` Gaps). Body ~60 Zeilen.
6. `.claude/agents/spec-reviewer.md`: Subagent mit Read-Only-Tools
   gegen Spec-Konsistenz — nutzt Kontextisolation (siehe Brief 01).
7. `.codex/config.toml` (minimal): Profil `spec-work` mit
   `sandbox = "workspace-write"`, `approval = "on-request"`, gleiche
   MCP-Server wie in `.mcp.json`. **Nicht** `danger-full-access`.
8. `.gitignore`: `.claude/settings.local.json`, `.codex/auth.json`,
   `.codex/history.jsonl`.

**Spec ohne Legacy-Noise exponieren.** In `AGENTS.md` ein 5-Zeilen-
Abschnitt "How to read this repo":
- Source of truth = `research/99-synthesis.md`.
- `00-README.md`..`11-glossary.md` = legacy, haben Quellenwert, aber
  widersprechen stellenweise `99`.
- `research/01..15` = Tier-A/B-Evidenz fuer einzelne Bausteine.
- `REVIEW.md` = offene Gaps; Aenderungen der Spec gehen durch Review.
- Dieselbe Navigation als `spec-navigator`-Skill fuer Claude; Codex
  liest sie direkt aus `AGENTS.md`.

**Token-Bloat-Prophylaxe.** `AGENTS.md` unter 200 Zeilen halten. Alle
Prozeduren in Skills. Keine Research-Briefs in `AGENTS.md` einbetten —
nur relative Links. MCP-Server-Count im Projektscope auf 2 begrenzen.

**Empfohlene Hooks fuer V1: keine.** Der Nutzen (Format-on-Save,
Auto-Lint) ist fuer ein Docs-Repo gering; die Angriffsflaeche (eingecheckte
Hooks = RCE-Primitiv) ist real. Wenn spaeter Code in diesem Repo landet,
ein einziger `PreToolUse`-Hook fuer `prettier`/`markdownlint` — und das
als Shell-Script, das auch ausserhalb des Agents lauffaehig ist
(Deterministic Hierarchy: CODE vor SKILL).

**Reproduzierbare Agent-Aufrufe.**
- Claude Code: `claude -p --output-format json --bare --allowedTools
  "Read,Grep,Glob" --agent spec-reviewer "<prompt>"` (Brief 01, §
  Headless).
- Codex CLI: `codex exec --json --sandbox read-only --profile spec-work
  --output-schema schemas/spec-review.json "<prompt>"` (Brief 02,
  § Headless). Beide Aufrufe im `AGENTS.md` unter "Reproducible agent
  invocations" dokumentieren.

## Offene Unsicherheiten
- Ob Claude Code 2026 neben `CLAUDE.md` zusaetzlich `AGENTS.md` nativ
  einliest — die Docs sagen nein, einzelne Community-Berichte behaupten
  experimentelle Unterstuetzung. Symlink bleibt der sichere Weg.
- Wie sich die Skill-Progressive-Disclosure mit `AGENTS.md`-Inhalten
  verhaelt, wenn dieselbe Regel in beiden Plaetzen steht (Duplicate-
  Penalty nicht empirisch gemessen).
- Codex-Trust-Profile-Split (`.codex/config.toml` vs. Trust-State in
  `~/.codex/`) wird laut Issue #15433/#14601 geaendert — exaktes Schema
  fuer 2026-H2 offen.
- Kein oeffentlicher Benchmark fuer "MCP-Tool-Definitions-Budget" — die
  20-k-Token-Faustregel ist Community-Konsens, nicht Tier-1-Zahl.
- Ob ein einziger Repo-Skill (`spec-navigator`) ausreicht oder pro
  Brief ein kleiner Retrieval-Skill sinnvoller ist (Modellierung offen,
  Messung empfohlen).

## Quellen
[^1]: https://code.claude.com/docs/en/best-practices — Tier 1, 2026, CLAUDE.md-Groesse, Import-Syntax, Session-Start-Laden.
[^2]: https://www.mindstudio.ai/blog/claude-code-token-management-hacks und https://buildtolaunch.substack.com/p/claude-code-token-optimization — Tier 2, 2026-04, konkrete Token-Messungen (MCP > 20 k toxisch, CLAUDE.md > 500 Tokens teurer pro Turn).
[^3]: https://code.claude.com/docs/en/skills und https://github.com/anthropics/skills/blob/main/README.md — Tier 1, 2026, SKILL.md-Template, Frontmatter, Progressive Disclosure (30–50 Tokens Overhead pro Skill).
[^4]: Brief 01 (research/01-claude-code.md) — Tier 1 aggregiert: Subagents, Settings-Hierarchie, Hooks-Events, MCP-Scopes, CVE-Kette.
[^5]: https://developers.openai.com/codex/guides/agents-md — Tier 1, 2026, AGENTS.md-Discovery-Kette, Override-Datei, Codex zitiert Items sichtbar.
[^6]: https://agents.md/ — Tier 2, 2026, Open-Standard-Beschreibung mit Cross-Tool-Positionierung.
[^7]: https://github.com/openai/codex/blob/main/AGENTS.md — Tier 1, 2026, reales Beispiel (~213 Zeilen, enforcement-fokussiert, Rust/TUI/Tests/API-Sektionen).
[^8]: https://developers.openai.com/codex/config-advanced, https://github.com/openai/codex/issues/14601, https://github.com/openai/codex/issues/15433 — Tier 1, 2026, Trust-State-Pfad, Profile-Struktur, offene VCS-Sauberkeit.
[^9]: Brief 02 (research/02-codex-cli.md) — Tier 1 aggregiert: Sandbox-Modi, Subagent-Limits, Protected Paths `.codex`, Headless-JSONL.
[^10]: https://github.com/kedro-org/kedro/issues/5408 und https://www.ssw.com.au/rules/symlink-agents-to-claude — Tier 1 + 2, 2026, Symlink-Pattern im OSS-Ecosystem und expliziter Rule.
[^11]: https://kau.sh/blog/agents-md/ und https://tessl.io/blog/the-rise-of-agents-md-an-open-standard-and-single-source-of-truth-for-ai-coding-agents/ — Tier 2, 2026, Single-Source-of-Truth-Argumentation und Multi-Tool-Sync.
[^12]: https://www.builder.io/blog/best-mcp-servers-2026 — Tier 2, 2026, Filesystem-/Git-MCP als "secure default", Read-only-Git.
[^13]: https://github.com/cyanheads/obsidian-mcp-server, https://github.com/Piotr1215/mcp-obsidian, https://desktopcommander.app/blog/best-mcp-servers-for-knowledge-bases-in-2026/ — Tier 1/2, 2026, Obsidian-MCP-Optionen mit/ohne App-Dependenz.
[^14]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf — Tier 1, 2026, Anthropic-Guide mit Skill-Template, progressive disclosure, Startup-Overhead-Zahlen.
