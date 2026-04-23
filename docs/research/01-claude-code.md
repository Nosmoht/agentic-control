---
topic: claude-code
tier: A
date: 2026-04-23
status: draft
---

# Brief 01: Claude Code — aktueller Stand (Anfang 2026)

## Forschungsfrage
Wie sehen Architektur, Permission-Modell und Feature-Oberfläche von Claude
Code (CLI/IDE/Web) Anfang 2026 aus? Was lebt lokal, was in der Cloud? Wie
funktionieren Hooks, Skills, Subagents, MCP, Sandboxing, Sessions, Headless-
Modus? Kann Claude Code die Rolle "Execution & Verification" übernehmen —
und welches Harness muss darum herum gebaut werden?

## Methodik
Acht Sub-Queries (Architektur, Permissions, Hooks, Skills, Subagents, MCP,
Sandbox, Headless/Sessions), je 1–2 WebSearches plus gezielter Fetch via
Jina Reader. Primär: `code.claude.com/docs`, `platform.claude.com/docs`,
Anthropic-Engineering-Blog, Check-Point-Advisory. Sekundär: GitHub-Issues
im Claude-Code-Repo, Security-Research (Ona, Adversa). Verworfen: Tutorials
ohne Belege, Marketing.

## Befunde

### Architektur
Claude Code ist ein einheitlicher Agent über fünf Surfaces: Terminal-CLI,
VS-Code- und JetBrains-Extension, Desktop-App, Web (`claude.ai/code`)[^1].
`CLAUDE.md`, `settings.json` und MCP-Server werden über alle Surfaces
synchronisiert[^1]. Kern: Single-Binary-CLI mit React+Ink für das TUI[^2];
IDE-Extensions starten lokal einen MCP-Server `ide`, mit dem sich die CLI
automatisch verbindet[^2]. Web/Desktop bieten Remote Control lokaler
Sessions und verteilte Weiterführung — dadurch landet Session-State
zwangsläufig in Anthropics Cloud[^1]. Für ein lokal-souveränes System
bleiben CLI + IDE-Extension die kontrollierbaren Surfaces.

### Permission-Modell
Settings-Hierarchie (niedrig → hoch): User (`~/.claude/settings.json`) →
Shared-Project (`.claude/settings.json`) → Local-Project
(`.claude/settings.local.json`) → CLI-Flags → Managed-Settings (MDM)[^3].
Modi: `default`, `acceptEdits`, `plan`, `auto` (Preview), `dontAsk`,
`bypassPermissions` (überspringt Prompts außer für `.git`, `.claude`,
`.vscode`, `.idea`, `.husky`)[^3]. Regeln `allow`/`ask`/`deny`, Format
`Tool(specifier)` mit Wildcards (`Bash(npm *)`, `Read(./.env)`,
`WebFetch(domain:...)`, `Agent(...)`). Auswertungsreihenfolge: **deny →
ask → allow**, erste Übereinstimmung gewinnt[^3]. Managed-Settings können
`allowManagedPermissionRulesOnly`, `disableBypassPermissionsMode`,
`allowManagedMcpServersOnly` erzwingen[^3]. **Dokumentierte Leaks**: Deny
wird bei Commands mit >~50 Sub-Commands aus Token-Gründen stillschweigend
übersprungen[^4]; Pfad-/Symlink-Tricks (`/proc/self/root/...`) umgehen
Pattern-Deny[^5]. Das Modell ist eine **Hinweiskonvention mit Leaks**,
kein Sicherheits-Perimeter.

### Hooks
User-definierte Shell-Commands, HTTP-Endpoints, Prompts oder Subagents an
Lifecycle-Events der CLI[^6]. Offizielle Referenz listet ~28 Events, u.a.
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
`PermissionRequest`, `SubagentStart/Stop`, `Stop`, `PreCompact`,
`FileChanged`, `CwdChanged`[^6]. Vier Handler-Typen: `command`, `http`,
`prompt`, `agent`. `PreToolUse` antwortet mit
`permissionDecision ∈ {allow, deny, ask, defer}` und kann Inputs via
`updatedInput` modifizieren; andere Events nutzen `decision: "block"`
oder Exit-Code 2[^6]. Default-Timeouts: Command 600 s, Prompt 30 s, Agent
60 s, SessionEnd 1.5 s[^6]. **Sicherheitsrelevant**: Hooks führen
beliebigen Code mit User-Rechten aus. CVE-2025-59536 (RCE via
SessionStart-Hook, Patch 2025-08-26) und CVE-2026-21852
(API-Key-Exfil via `ANTHROPIC_BASE_URL`, Patch 2025-12-28)
dokumentieren die Klasse[^7]. Warn-Dialoge und verzögerte Netz-Ops wurden
gehärtet; die Grund-Angriffsfläche — eingecheckte `.claude/`-Dateien mit
Ausführungssemantik — bleibt bestehen[^7].

### Skills
Seit 2026 ein vereinheitlichtes System mit Slash-Commands: Eine Datei
`.claude/commands/foo.md` und ein Skill `.claude/skills/foo/SKILL.md`
erzeugen beide `/foo`[^8]. Skills sind empfohlen: Directory für
Support-Files, YAML-Frontmatter, optional auto-invoked durch das Modell[^8].
Frontmatter: `name`, `description`/`when_to_use` (≤ 1 536 Zeichen),
`allowed-tools`, `context: fork` (Subagent-Isolation),
`disable-model-invocation` (nur User), `user-invocable: false` (nur
Modell)[^8]. **Lade-Semantik**: Skill-Body wird erst beim Invoken geladen
und bleibt danach für den Rest der Session im Kontext[^8]. Reihenfolge:
Enterprise → User → Project → Plugin[^8]. Primäres Werkzeug für
wiederverwendbare Prozeduren ohne `CLAUDE.md`-Bloat.

### Subagents
Jeder Subagent läuft in eigenem Kontext-Fenster mit eigenem System-Prompt,
eigenen Tool-Rechten, eigenem Permission-Mode; erbt Working-Dir, gibt nur
eine Zusammenfassung zurück[^9]. YAML-Frontmatter + Markdown-Body (`name`,
`description`, `tools`/`disallowedTools`, `model`, `permissionMode`,
`hooks`, `mcpServers`, `isolation`, `maxTurns`, `color`). Invokation:
automatisch, per `@"name (agent)"`, via natürlicher Sprache oder
`claude --agent <name>` als Haupt-Thread[^9]. Parallelismus: mehrere
unabhängige Subagents gleichzeitig; harte Obergrenze nicht offiziell
beziffert. **Hartes Limit**: Subagents können selbst keine weiteren
Subagents spawnen — ein zentrales Design-Constraint[^9].

### MCP
Drei Scopes: Local (`~/.claude.json`, pro-Projekt), Project (`.mcp.json`,
eingecheckt), User (`~/.claude.json`, global); Präzedenz Local > Project >
User > Plugin > Claude.ai-Connectors[^10]. Transporte: `stdio` (lokal),
`http` (empfohlen), `sse`. Env-Expansion via `${VAR}` und `${VAR:-default}`
in `command`, `args`, `env`, `url`, `headers`[^10]. **Tool-Search** (ab
Sonnet/Opus 4+) lädt default nur Tool-Namen, Schemas on-demand;
`ENABLE_TOOL_SEARCH=auto:5` steuert[^10]. Output-Limits: Warn-Schwelle
10 000 Tokens, Default-Max 25 000 (`MAX_MCP_OUTPUT_TOKENS`). Verwaltung:
`claude mcp add|list|get|remove`, `/mcp`-Slash. HTTP/SSE haben
Auto-Reconnect mit 5 Versuchen, exponentieller Backoff[^10].

### Sandboxing
Native Sandbox mit OS-Primitiven: `bubblewrap` (Linux/WSL2), `seatbelt`
(macOS); WSL1 unsupported, Windows nativ angekündigt[^11]. FS-Isolation:
Schreibrechte nur im CWD + Subdirs, systemweites Lesen (außer Deny-Pfade);
steuerbar via `sandbox.filesystem.allowWrite/denyWrite/denyRead/allowRead`.
Netz-Isolation: Outbound nur über Unix-Socket-Proxy mit Domain-Whitelist[^11].
Anthropic misst **84 % weniger Permission-Prompts** im internen Einsatz[^12].
**Gaps**: Read-/Edit-Tools und Computer-Use sind nicht abgedeckt;
Netz-Filter inspiziert nur Domains, kein Content; keine CPU/Memory-Limits[^11][^12].
Zusätzlich dokumentierte Bypässe der Deny-List (Pfad-Tricks,
Token-Budget)[^4][^5]. Fazit: Die Sandbox ist wertvolle
Defense-in-Depth, aber **keine ausreichende Execution-Isolation** —
Container/VM/Worktree-Schicht muss darüber liegen.

### Session-Modell & Headless
Sessions werden automatisch auf Platte geschrieben und via
`claude --continue` (letzte) oder `--resume <id>` wieder aufnehmbar[^13].
Session-Memory (2026) schreibt strukturierte Cross-Session-Summaries[^13].
Issue #43696 (April 2026) meldet, dass `--continue`/`--resume` den Kontext
nicht verlässlich restauriert[^14] — **Session-Resume ist nicht
produktionsreif** als Zustandsfundament. **Headless**: `-p`/`--print`
liefert Response an stdout; Formate `text`, `json`, `stream-json`
(NDJSON)[^15]. Tool-Auth via `--allowedTools "Bash,Read,Edit"`. `--bare`
überspringt Auto-Discovery von Hooks, Plugins und MCP-Servern — empfohlen
für CI und deterministische Skripts[^15]. Das Anthropic Agent SDK
(Python/TS) liefert die gleiche Funktionalität programmatisch und ist die
saubere Integrationsschicht für einen Orchestrator[^15].

## Quellenbewertung
- **Tier 1**: 9 (Anthropic Docs, Engineering-Blog, GitHub-Issue,
  Check-Point-Advisory als CVE-Autorität)
- **Tier 2**: 2 (Ona, Adversa — Security-Research mit konkreten Exploits)
- **Tier 3**: 0
- **Cross-Validation erfüllt**: ja. Jede nicht-triviale Aussage ist
  entweder durch offizielle Anthropic-Docs mit konkreten Konfigurations-
  Details (Tier 1) belegt oder durch zwei unabhängige Quellen
  (Docs + Security-Research) abgesichert. CVEs sind formale Autoritäten.

## Implikationen für unser System
**Kann Claude Code "Execution & Verification" sein?** Ja, unter Harness:
1. Immer Headless (`-p --output-format json --bare --allowedTools ...`);
   interaktive Sessions sind nicht nutzbar, weil Resume unzuverlässig.
2. Niemals `bypassPermissions`; `plan` für Verification, `acceptEdits` für
   scoped Execution in einem vorgegebenen Worktree.
3. Native Sandbox aktiv als Defense-in-Depth, **zusätzlich** Worktree-/
   Container-Isolation pro Run — Deny-List-Bypässe sind dokumentiert.
4. `.mcp.json` und `.claude/settings.json` nie aus untrusted Quellen
   akzeptieren (Hook-RCE-Klasse); via `allowManagedHooksOnly` härten.
5. Subagents für Verification nutzen (Kontextisolation).

**Native Features, die unser Trust-Zonen-Modell abbilden kann**:
- Permission-Modi ≈ Execution-Policy pro Zone.
- Subagent-Kontext ≈ Prozess-Scope pro Task.
- Sandbox (FS/Netz) ≈ Outer Fence.
- Hooks = Policy-Enforcement (selbst aber Angriffsfläche).

**Was das umgebende System bauen muss**:
- State-Persistenz außerhalb von Claude Code (Resume unzuverlässig).
- Externer Scheduler, der Headless-Runs triggert — Claude Code triggert
  sich selbst nicht.
- Worktree-/Container-Wrapper pro Run, nicht allein auf bubblewrap/Deny
  verlassen.
- Unabhängige Audit-Spur außerhalb der Hook-Schicht.
- Versionierter Permission-Rule-Generator pro Rolle/Zone.

## Offene Unsicherheiten
- Harte Parallelitäts-Obergrenze für Subagents nicht offiziell beziffert.
- Cloud-State-Umfang bei Web/Desktop (welche Artefakte genau?) unklar.
- Verhalten von `ENABLE_TOOL_SEARCH=auto:5` bei kleinen Contexts nicht
  durch Benchmark validiert.
- `SessionEnd`-Timeout (1.5 s) vs. langläufige Hooks im Headless-Modus.
- Windows-nativer Sandbox-Support: "planned", kein ETA.

## Quellen
[^1]: https://code.claude.com/docs/en/overview — Tier 1, 2026, offizielle Architektur-Übersicht, Surface-Matrix, Cross-Device-Sessions.
[^2]: https://claude.com/product/claude-code — Tier 1, 2026, Produktseite mit CLI/IDE-Architektur (React+Ink, `ide`-MCP-Server).
[^3]: https://code.claude.com/docs/en/permissions — Tier 1, 2026, Permission-Modi, Evaluierungsreihenfolge, Managed-Settings.
[^4]: https://adversa.ai/blog/claude-code-security-bypass-deny-rules-disabled/ — Tier 2, 2026, Deny-Rule-Bypass bei >50 Sub-Commands.
[^5]: https://ona.com/stories/how-claude-code-escapes-its-own-denylist-and-sandbox — Tier 2, 2026-03, Pfad-/Symlink-Deny-Bypass.
[^6]: https://code.claude.com/docs/en/hooks — Tier 1, 2026, vollständige Event- und Handler-Referenz, Timeouts, Decision-Patterns.
[^7]: https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/ — Tier 1/2, 2026-01, CVE-2025-59536 + CVE-2026-21852 mit Patch-Timeline.
[^8]: https://code.claude.com/docs/en/skills — Tier 1, 2026, Skills/Slash-Commands-Vereinigung, SKILL.md, Frontmatter, Lade-Semantik.
[^9]: https://code.claude.com/docs/en/sub-agents — Tier 1, 2026, Kontextisolation, Tool-Allow/Deny, Invokation, No-Spawn-Limit.
[^10]: https://code.claude.com/docs/en/mcp — Tier 1, 2026, Scopes, Transporte, Tool-Search, Output-Limits.
[^11]: https://code.claude.com/docs/en/sandboxing — Tier 1, 2026, bubblewrap/seatbelt, FS-/Netz-Isolation, Plattform-Matrix.
[^12]: https://www.anthropic.com/engineering/claude-code-sandboxing — Tier 1, 2025, 84-%-Prompt-Reduktion, Bedrohungsmodell.
[^13]: https://code.claude.com/docs/en/agent-sdk/sessions — Tier 1, 2026, Session-Persistenz, `--continue`/`--resume`, Session-Memory.
[^14]: https://github.com/anthropics/claude-code/issues/43696 — Tier 1 (Issue-Tracker), 2026-04, Context-Restore-Bug.
[^15]: https://code.claude.com/docs/en/headless — Tier 1, 2026, `-p`, Output-Formate, `--allowedTools`, `--bare`, Agent-SDK.
