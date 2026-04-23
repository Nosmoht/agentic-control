---
topic: codex-cli
tier: A
date: 2026-04-23
status: draft
---

# Brief 02: Codex CLI — aktueller Stand (Anfang 2026)

## Forschungsfrage
Wie ist Codex CLI (plus Codex Cloud) Anfang 2026 architektonisch aufgebaut, welches Permission-/Sandbox-Modell bietet es, und eignet es sich als gebundener "Execution & Verification"-Kontext innerhalb eines übergeordneten Multi-Projekt-Agentensystems — oder ist die Vertrauensgrenze für diese Rolle unzureichend definiert?

## Methodik
Primärquellen: `developers.openai.com/codex/*` (Dokumentation, CLI-Referenz, Security-Seite, MCP-Seite, Subagents-Seite, Sandboxing-Konzept, Cloud-Environments, Non-interactive Mode, Changelog)[^1][^2][^3][^4][^5][^6][^7][^8]. Ergänzend OpenAI Help Center (Rate Card)[^9] und ausgewählte Sekundärquellen für Kontext und Cross-Validation[^10][^11][^12]. Iterative WebSearch-Zyklen (4), dann gezieltes Fetching der relevanten Tier-1-Dokseiten über Jina Reader. Cutoff für Quellenalter: 2025-10-23, Ausnahme offizielle Docs ohne neuere Revision.

## Befunde

### Architektur (lokal vs. Cloud)
Codex existiert Anfang 2026 in zwei operativen Formen, die denselben Markennamen, aber unterschiedliche Trust-Modelle tragen.

- **Codex CLI (lokal):** Rust-basiertes Terminal-Tool, das Modell-APIs aufruft, aber Datei- und Befehls-Execution **auf der lokalen Maschine** durchführt. State liegt unter `CODEX_HOME` (Default `~/.codex`): `config.toml`, `auth.json` bzw. OS-Keychain, optional `history.jsonl`, SQLite-State-DB für resumable Runs[^2][^6].
- **Codex Cloud / Web:** Task läuft in einem **isolierten Container** auf OpenAI-Infrastruktur, Repo-Checkout erfolgt aus GitHub; das Universal-Image wird mit Setup-/Maintenance-Scripts customisiert[^5]. Container-Cache hält bis zu 12h, wird invalidiert bei Änderung von Setup-Script, Env-Variablen oder Secrets[^5]. **Alle Outbound-Requests laufen durch einen HTTP/HTTPS-Proxy**[^5].
- **State-Aufteilung:** Lokal liegt sämtlicher Session-State auf dem Entwickler-Host; Cloud-Environments persistieren Env-Vars/Secrets und einen zeitlich begrenzten Container-Cache, aber keinen Conversation-State über das Task-Ende hinaus (Setup-only Secrets werden vor der Agent-Phase entfernt[^5]).

### Permission-Modi & Approval
Zwei orthogonale Achsen, die explizit getrennt sind[^3][^8]:

**Approval Policies** (wann das Modell menschliche Freigabe braucht):
- `on-request` — **Default in versionierten Verzeichnissen**. Codex fragt, bevor es Dateien ausserhalb des Workspace editiert oder Commands mit Netzzugriff ausführt[^3].
- `untrusted` — nur bekannte Read-Only-Commands laufen ohne Prompt; alles Mutierende oder extern Ausführende erfordert Freigabe[^3].
- `never` — keine Prompts; Codex bleibt durch Sandbox begrenzt, nicht durch Human-in-the-Loop[^3].
- `granular` — selektive Kategorien (Sandbox-Approvals, Rule-Prompts, MCP-Prompts, Permission-Requests, Skill-Scripts)[^3].

**Sandbox Modes** (was technisch erlaubt ist, unabhängig von Approval):
- `read-only` — **Default in nicht-versionierten Verzeichnissen** und **Default für `codex exec`**[^8][^4].
- `workspace-write` — Read/Write innerhalb Workspace; `.git`, `.agents`, `.codex` bleiben unabhängig vom Modus schreibgeschützt[^3][^8].
- `danger-full-access` / `--yolo` — keine Sandbox[^3][^8].

Preset-Shortcuts: `--full-auto` = `workspace-write` + `on-request`; voll autonom ohne Sandbox = `danger-full-access` + `never`[^8][^10]. 2026 hinzugekommen: Deny-Read-Glob-Policies, Managed-Network-Profile, Platform-Sandbox-Enforcement, isolierte `codex exec`-Runs, die User-Config ignorieren[^1].

### Sandbox & Workspace-Isolation
Plattformspezifisch — das ist sicherheitsrelevant[^7]:
- **macOS:** native **Seatbelt** (`sandbox-exec -p`). Keine Zusatzinstallation[^7][^10].
- **Linux / WSL2:** **bubblewrap (bwrap)** über unprivilegierte User-Namespaces; auf älteren Ubuntu ggf. `bwrap-userns-restrict` nötig. Manche Docs erwähnen zusätzlich Landlock-Rulesets für Fine-Grained-Policies[^7][^10].
- **Windows (PowerShell):** **Windows Sandbox** nativ; in WSL2 wird die Linux-Implementation genutzt[^1][^7].
- **Codex Cloud:** isolierter Container plus verpflichtender HTTP/HTTPS-Egress-Proxy, Internet für Agent-Phase per Default **aus**[^5].

Wichtig: Lokale Sandboxes bieten **Prozess-/Dateisystem-Isolation, keine VM-Isolation**. Compromise-Szenarien (z.B. fremde Deps, Prompt-Injection, Ausbruch über signierte Binaries) sind weiter möglich — OpenAI warnt explizit vor `danger-full-access` ausserhalb einer dedizierten Sandbox-VM[^10].

### Session-Modell
Sessions sind **langlebig und wiederaufnehmbar**[^6][^4]:
- `codex resume` öffnet Picker; `--last` nimmt letzte Session des cwd; `--all` ignoriert cwd-Filter; `<SESSION_ID>` zielt spezifisch.
- Auch `codex exec resume --last` bzw. `resume <SESSION_ID>` existiert für Headless-Runs[^4].
- State-DB: SQLite unter `sqlite_home` bzw. `CODEX_SQLITE_HOME`; Default fällt auf Temp-Dir bei WorkspaceWrite-Sessions, sonst `CODEX_HOME`[^6].
- Flag `--ephemeral` verhindert Persistenz[^4].
- Cloud-Tasks sind demgegenüber pro Task containerisiert; Conversation-State über Tasks hinweg wird nicht garantiert persistiert.

### Multi-Agent / Subagents
Seit Anfang 2026 nativ[^11]:
- Drei Built-ins: `default`, `worker` (execution), `explorer` (read-heavy). Custom-Agents als TOML in `~/.codex/agents/` oder `.codex/agents/`[^11].
- Parallelismus-Limits (Defaults): `agents.max_threads = 6`, `agents.max_depth = 1` (keine rekursive Delegation), `agents.job_max_runtime_seconds = 1800`[^11].
- **Subagents erben die Sandbox-Policy und Runtime-Overrides des Parents** (inkl. `--yolo`)[^11].
- Trigger ist explizit: "Codex only spawns a new agent when you explicitly ask it to do so"[^11].
- Kosten: "subagent workflows consume more tokens than comparable single-agent runs"[^11].
- `/agent`-Command im TUI zum Wechseln/Inspizieren aktiver Threads[^11].

### MCP / Extensibility
Codex CLI unterstützt MCP als Haupt-Extensibility-Layer[^2]:
- Zwei Transports: **STDIO** (lokaler Prozess) und **Streamable HTTP**[^2].
- Config in `~/.codex/config.toml` global, `.codex/config.toml` pro Projekt (nur in "trusted projects")[^2][^6].
- Verwaltung: CLI (`codex mcp add`), TOML direkt, TUI (`/mcp`)[^2].
- Pro Server: Timeouts (`startup_timeout_sec` 10s, `tool_timeout_sec` 60s), Auth (Bearer/OAuth mit `mcp_oauth_callback_port`), Tool-Filter (`enabled_tools`/`disabled_tools`)[^2].
- 2026-Updates: namespaced MCP-Registration, Parallel-Call-Opt-in, Sandbox-State-Metadata für MCP-Server, MCP-Apps-Tool-Calls[^1].

### Headless & Automation
`codex exec` ist für Orchestration explizit ausgelegt[^4]:
- **Default: read-only**; `--full-auto` oder `--sandbox workspace-write` für Schreibrechte nötig[^4].
- `--json` erzeugt **JSONL-Event-Stream** auf stdout: `thread.started`, `turn.started/completed/failed`, `item.*` (Messages, Reasoning, Commands, File Changes, MCP-Calls, Web-Searches), `error`[^4].
- `--output-schema` für strukturierte Final-Response gegen JSON-Schema[^4].
- Auth: `CODEX_API_KEY` als CI-Secret (nur für `exec` gültig)[^4].
- Piping-Patterns: Stdin als Kontext (`npm test | codex exec "..."`), voller Prompt aus Stdin (`codex exec -`)[^4].
- Fortschritt geht nach **stderr**, finale Message nach stdout — sauber pipebar[^4].
- `--ephemeral`, `-o <path>`, `--skip-git-repo-check` als Feintuning[^4].

### Kosten & Token-Tracking
- Abrechnung seit 2026-04-02 **tokenbasiert** (Input / Cached Input / Output), gekauft werden Credits[^9][^12].
- Codex ist in ChatGPT-Plänen (Free/Go/Plus/Pro/Business/Enterprise) mit Plan-spezifischen 5h-Limits enthalten; API-Nutzung via `CODEX_API_KEY` läuft separat[^9][^12].
- Tracking sichtbar im Workspace-Settings-Panel ("Usage"); feingranulares Per-Session-Tracking in der CLI existiert laut Community-Quellen, wird aber in offiziellen Docs nur summarisch dokumentiert[^12].
- Subagents erhöhen Tokenverbrauch deutlich[^11].

## Quellenbewertung
- Tier 1: 8 (OpenAI Developer Docs + Help Center)
- Tier 2: 1 (Simon Willison Beobachtungsbericht zu Subagents)
- Tier 3: 3 (Community-Blogs zu Flags, Pricing, Deep-Dive)
- Cross-Validation erfüllt: **ja** — jede zentrale Behauptung (Sandbox-Tech, Approval-Modi, exec-Defaults, Subagent-Limits, MCP-Transports) steht in mindestens einer Tier-1-Quelle mit konkretem Spezifitätsgrad.

## Implikationen für unser System

### Kann Codex CLI als "Execution & Verification"-Kontext dienen?
**Ja, mit Einschränkungen.** `codex exec --json --sandbox read-only` (bzw. `workspace-write` für Fix-Runs) mit `--output-schema` liefert deterministisch parsebaren Output und ein explizites Sandbox-/Approval-Modell — das passt strukturell zur Rolle eines gebundenen Ausführungskontexts. `--ephemeral` erlaubt zustandslose Runs, was unser Modell bevorzugt.

### Lokale vs. Cloud trust-theoretisch
- **Lokal:** Vertrauensgrenze ist die OS-Sandbox (Seatbelt / bwrap / Windows Sandbox). Das ist **Prozess-Isolation, nicht VM-Isolation** — Host-Compromise möglich, sobald `danger-full-access` aktiv ist. `--yolo` ohne externe VM ist inakzeptabel für unseren Controller.
- **Cloud:** echter Container + Egress-Proxy + Internet-off-by-default liefert stärkere Isolation, aber dafür laufen Code und Secrets **auf OpenAI-Infra**. Für Execution-Tasks auf öffentlichen Repos akzeptabel; für Secrets/private Daten Policy-Entscheidung.

### Welcher Harness wäre nötig?
1. **Wrapper-Script**, das ausschliesslich `codex exec --json --output-schema <path> --sandbox workspace-write --ask-for-approval on-request` aufruft — nie `--yolo`, nie `danger-bypass-approvals-and-sandbox`.
2. **JSONL-Event-Konsument**, der `turn.failed`/`error` in unser Work-Item-Modell übersetzt und Abbruch erzwingt.
3. **Budget-Gate** vor Invocation: Token-Limit pro Run, hartes Timeout, max. Subagent-Threads (default 6 ok, evtl. runter auf 2).
4. **Schreibbereichs-Constraint**: Codex nur in Worktree-Clone-Verzeichnisse loslassen, niemals im Haupt-Workspace; protected paths (`.git`, `.codex`) sind built-in readonly, aber das ersetzt keinen externen Sandbox-Layer.
5. **Getrennte Credentials**: dedizierter `CODEX_API_KEY` pro Kontext, nicht der interaktive Login.
6. **MCP-Whitelist**: Subset unserer MCP-Tools exponieren, insbesondere keine Github-Write-Tools in Verifikationsläufen.

## Offene Unsicherheiten
- Genauer Zustand der Landlock-Integration auf Linux vs. reiner bwrap-Mechanik — Docs nennen beides, Cross-Validation unvollständig.
- Stabilität der `--output-schema`-Compliance (Anteil Runs, bei denen Schema eingehalten wird) — offiziell versprochen, empirische Messung fehlt.
- Ob `codex exec resume` in JSONL-Mode dieselben Event-Typen wie Fresh-Runs liefert (vermutet, nicht verifiziert).
- Persistenz von Subagent-Custom-Definitionen bei Parallel-Runs in CI — `.codex/agents/` als Repo-Artefakt plausibel, aber Sicherheitsimplikationen ungeklärt.
- Konkreter Preis pro Million Input/Output-Tokens nach dem 2026-04-02-Modell nicht aus einer Tier-1-Quelle extrahiert (Rate Card-Seite erwähnt nur Struktur).

## Quellen
[^1]: https://developers.openai.com/codex/changelog — Tier 1, 2026, Changelog erwähnt Deny-Read-Globs, Managed-Network-Profiles, Platform-Sandbox-Enforcement, isolierte `codex exec`-Runs, namespaced MCP-Registration, Parallel-Call-Opt-in, MCP-Apps.
[^2]: https://developers.openai.com/codex/mcp — Tier 1, 2026, MCP-Transports (STDIO + HTTP), Config-Pfade, Auth-Optionen, Tool-Filter.
[^3]: https://developers.openai.com/codex/agent-approvals-security — Tier 1, 2026, Approval-Modi (`on-request`/`untrusted`/`never`/`granular`), Sandbox-Modi (`read-only`/`workspace-write`/`danger-full-access`), Protected Paths.
[^4]: https://developers.openai.com/codex/noninteractive — Tier 1, 2026, `codex exec`-Verhalten, JSONL-Events, `--output-schema`, `CODEX_API_KEY`, Resume-Support, Stdin-Piping.
[^5]: https://developers.openai.com/codex/cloud/environments — Tier 1, 2026, Container-Isolation, HTTP/HTTPS-Proxy, 12h-Cache, Setup-/Maintenance-Scripts, Internet-off-by-default.
[^6]: https://developers.openai.com/codex/config-reference sowie github.com/openai/codex docs/config.md — Tier 1, 2026, `CODEX_HOME`, `sqlite_home`, `config.toml`-Schlüssel, Precedence.
[^7]: https://developers.openai.com/codex/concepts/sandboxing — Tier 1, 2026, Seatbelt (macOS), bubblewrap (Linux/WSL2), Windows Sandbox (PowerShell), Default-Modi, Protected Paths.
[^8]: https://developers.openai.com/codex/cli/reference — Tier 1, 2026, Command-Line-Options, `--full-auto`, `--workspace-write`, `--sandbox`, `--ask-for-approval`.
[^9]: https://help.openai.com/en/articles/20001106-codex-rate-card — Tier 1, 2026, Rate-Card-Struktur, Credit-basierte Abrechnung, Plan-Einbindung.
[^10]: https://www.vincentschmalbach.com/how-codex-cli-flags-actually-work-full-auto-sandbox-and-bypass/ — Tier 3, 2026, Flag-Semantik-Deep-Dive mit konkreten Beispielen (Warnung vor `--dangerously-bypass-approvals-and-sandbox`).
[^11]: https://developers.openai.com/codex/subagents und https://simonwillison.net/2026/Mar/16/codex-subagents/ — Tier 1 + Tier 2, 2026, Built-in-Agents, Parallelismus-Limits (6/1/1800s), Sandbox-Vererbung, Token-Kosten.
[^12]: https://amanhimself.dev/blog/codex-tokens-usage/ — Tier 3, 2026, Community-Bericht zu Token-Tracking und Usage-Panel.
