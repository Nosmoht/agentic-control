# ADR-0010: Execution Harness Contract

* Status: accepted
* Date: 2026-04-24
* Context: `docs/spec/SPECIFICATION.md §8.2, §5.4`; erweitert ADR-0006 um operativen Vertrag.

## Kontext und Problemstellung

ADR-0006 definiert eine 8-Schichten-Minimum-Viable-Sandbox für Agent-Runs.
Offen blieb, **wie der Agent-Prozess konkret in dieser Sandbox sitzt**:
- Läuft die Agent-CLI selbst im Container?
- Wo liegen `~/.claude`/`~/.codex`/Auth-Tokens?
- Wie wird Netzwerk-Egress erzwungen?
- Wie werden Secrets injiziert?
- Welches Exit-Vertrags-Format liefert der Harness an den Orchestrator?

Der Counter-Review (2026-04-23, Befund 4) hat diese Lücke als kritisch
markiert: eine Sandbox, die nur im Dokument existiert, schützt nicht.

## Entscheidungstreiber

- Adapter-neutral — der Vertrag muss für Claude Code *und* Codex CLI gelten.
- Reproduzierbar — zwei Runs mit gleicher Eingabe ergeben dieselbe
  Sandbox-Konfiguration.
- Defense-in-Depth — mehrere unabhängige Kontrollen (nicht nur eine).
- Auditierbar — Post-Flight-Exit liefert strukturierte Artefakte.
- Kein Host-Credential-Leak — der Agent darf keine interaktiven
  Nutzer-Credentials erben.

## Erwogene Optionen

1. Alle Host-Config kopieren — Agent läuft mit vollem Zugriff, einfach.
2. **Harness-Vertrag mit explizit geführten Isolationsschichten.**
3. Firecracker-MicroVM pro Run — maximale Isolation, unproportional für n=1.

## Entscheidung

Gewählt: **Option 2** — ein normativer Harness-Vertrag.

### Der Vertrag

**Prozessbaum.** Ein Run = ein Container/Bubblewrap-Sandbox. Die Agent-CLI
(Claude Code oder Codex CLI) läuft *innerhalb* der Sandbox, nicht vor ihr.
Alle Kind-Prozesse (Tool-Calls, Shells, Compiler) erben die Sandbox.

**Mount-Tabelle (pro Run):**
| Pfad | Mount | Zweck |
|---|---|---|
| `/workspace` (= Git-Worktree) | `rw` | Arbeitsbaum |
| `/tmp` | `rw` (tmpfs) | Scratch |
| `/var/cache/apt`, `/var/cache/pip` | `ro` | Read-only Cache |
| `/usr`, `/etc`, `/bin`, `/sbin`, `/lib*` | `ro` | System |
| `~/.claude`, `~/.codex`, `~/.ssh`, `~/.netrc` | `masked` (nicht gemountet) | verhindert Host-Credential-Erbung |
| `.mcp.json` aus Host | `masked` | kein impliziter MCP-Server-Load |
| `/var/run/secrets/<run-id>/` | `ro` (tmpfs) | Per-Run-Credentials |

**Credentials.**
- Keine Env-Vererbung vom Host. Der Harness startet mit minimalem Env
  (`PATH`, `HOME=/home/agent`, `SHELL=/bin/sh`, `RUN_ID`).
- Secrets pro Run werden als Dateien in `/var/run/secrets/<run-id>/`
  gemountet, vom Orchestrator-Prozess erzeugt, nach Run gelöscht.
- Agent liest Credentials per `CREDENTIALS_PATH=/var/run/secrets/<run-id>`-
  Env-Var; keine Env-Variablen mit Secret-Wert direkt.

**Netzwerk.**
- Default: **kein** Netzwerk (`--network=none` bzw. Namespace ohne Default-
  Route).
- Opt-in pro Run: Egress-Proxy auf Loopback mit Domain-Allowlist.
  Allowlist-Default: Modell-Endpoint (Anthropic/OpenAI), Paket-Registries
  (crates.io, pypi.org, npmjs.org), Git-Hosts (github.com).
- Block auf 169.254.169.254 (Metadata-Endpoint) hart.
- Agent kennt nur den Proxy, nicht die Zieldomains direkt (`HTTP_PROXY`,
  `HTTPS_PROXY` gesetzt, direkte DNS-Auflösung nicht konfiguriert).

**Config-Write-Schutz.**
Folgende Pfade sind innerhalb der Sandbox write-protected:
`.mcp.json`, `.claude/`, `.codex/`, `~/.ssh/`, `~/.aws/`, Shell-Profile
(`.bashrc`, `.zshrc`, `.profile`), `/etc`.

**Ressourcen-Limits (cgroup v2).**
- Speicher: default 4 GiB (konfigurierbar pro Run-Type).
- CPU: 2 Kerne.
- PIDs: 1024.
- Wall-Clock: 15 min hart (matches ADR-0008 Task-Cap).
- Token-Budget: pro ADR-0008, harter Stop.

**Exit-Vertrag (Post-Flight-Artefakte).**
Der Harness gibt nach Run-Ende an den Orchestrator zurück:
- `exit_code` (int)
- `stdout_jsonl` (Pfad, append-only, strukturierte Events)
- `cost_receipt` (JSON: Tokens in/out, geschätzte Kosten, Cache-Hits)
- `tool_calls` (JSONL: Tool-Name, Inputs-Hash, Outputs-Ref, Duration, Exit)
- `artifacts_manifest` (JSON: erzeugte/veränderte Dateien im Worktree,
  SHA256, Größe)
- `sandbox_violations` (JSONL: verweigerte Egress-Versuche, Config-
  Write-Versuche, cgroup-Limits)
- `idempotency_keys` (JSON: Keys für externe Effekte, siehe ADR-0011)

Der Orchestrator persistiert diese Artefakte als `RunAttempt`-Records
(ADR-0011).

### Konsequenzen

**Positiv**
- Einheitlicher Vertrag für beide Adapter (ADR-0014).
- Sandbox ist kein Lippenbekenntnis mehr — Reihenfolge der Schichten,
  Mount-Tabelle, Egress-Policy explizit.
- Credential-Leak-Klasse geschlossen (masked statt gemountet).
- Audit-Trail ist strukturiert (strukturierte Exit-Artefakte).

**Negativ**
- Setup-Komplexität erhöht (Container-Image, Egress-Proxy-Konfig,
  Secrets-Injection-Helper).
- Performance-Overhead pro Run: Container-Start + Proxy-Latenz. Messung
  im v1a-Exit-Kriterium.
- Kernel-Exploit-Klasse weiterhin möglich (keine VM-Isolation).

## Referenzen

- ADR-0006 — 8-Schichten-MVS (Verträge lebten dort auf Prinzip-Ebene)
- ADR-0011 — Runtime Audit Records (konsumiert Exit-Artefakte)
- ADR-0014 — Peer-Adapters (konsumieren diesen Vertrag)
- `docs/research/07-trust-sandboxing.md` — OWASP/NIST/NVIDIA Cross-Validation
- `docs/research/01-claude-code.md`, `docs/research/02-codex-cli.md` — CLI-Eigenheiten
- Counter-Review (2026-04-23) Befund 4
