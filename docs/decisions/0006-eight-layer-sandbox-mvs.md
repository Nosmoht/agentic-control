# ADR-0006: 8-Schichten-Minimum-Viable-Sandbox pro Agent-Run

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §8.2`

## Kontext und Problemstellung

Agent-Runs (Claude Code, Codex CLI) führen arbiträren Code aus. Die nativen
Sandbox-Mechanismen der Tools (bubblewrap/seatbelt/Landlock) sind
Defense-in-Depth, aber keine Sicherheitsgrenze: Pfad-Tricks,
Token-Budget-Bypass und `.claude/`/`.codex/`-RCE-Vektoren (CVE-2025-59536,
CVE-2026-21852) sind dokumentiert. Unser System muss **über** der nativen
Sandbox eine eigene Isolation bauen.

## Entscheidungstreiber

- OWASP LLM Top 10, NIST AI RMF, NVIDIA Agentic-Guidance fordern
  Network-Egress-Control, Workspace-Bounded Writes und Config-Protection
  als „mandatory foundation layer".
- Produktivbewährung: Anthropic Claude Code Cloud und OpenAI Codex Cloud
  implementieren produktiv Container + Egress-Proxy.
- Schwelle zu Firecracker-MicroVMs rechnet sich nur bei Multi-Tenant.

## Erwogene Optionen

1. **Keine eigene Sandbox** — auf Native-Sandbox allein verlassen.
2. **Nur Worktree** — Isolation via Git-Branch.
3. **Worktree + Container** — Standard-Container (Docker/Podman), Default-Flags.
4. **Worktree + Container + volle 8-Schichten-MVS** (Empfehlung Brief 07).
5. **Firecracker-MicroVM pro Run** — VM-Isolation.

## Entscheidung

Gewählt: **Option 4 — 8-Schichten-MVS**.

### Die 8 Schichten

1. Git-Worktree pro Run.
2. Container oder Bubblewrap/Seatbelt, CWD rw, Rest ro.
3. Non-Root + `--cap-drop=ALL` + `no-new-privileges`.
4. Read-Only-Root-FS + tmpfs für `/tmp`.
5. Egress-Proxy mit Domain-Allowlist (Registries, Git, Modell-Endpoint);
   Block auf 169.254.169.254.
6. Config-Write-Schutz für `.mcp.json`, `~/.ssh`, Shell-RCs, `.claude/`,
   `.codex/`.
7. cgroup-Ressourcen- und Token-Budget-Limits.
8. Secret-Injection pro Run, keine Env-Vererbung.

### Konsequenzen

**Positiv**
- Alle drei genannten Tier-1-Referenzen (Anthropic, OpenAI, NVIDIA) sind
  abgedeckt.
- Egress-Proxy schließt die große Exfiltrations-Klasse ab.
- Secret-Injection pro Run verhindert unabsichtliche Env-Vererbung.

**Negativ**
- Initialer Setup-Aufwand: Container-Image, Egress-Proxy-Konfig,
  Worktree-Automation.
- Performance-Overhead pro Run (Container-Start, Proxy-Latenz).
- Nicht VM-Isolation — bei fortgeschrittenem Kernel-Exploit weiterhin
  durchbrechbar.

## Pro und Contra der Optionen

| Option | Isolation | Aufwand | Deckung der Tier-1-Anforderungen |
|---|---|---|---|
| Keine | minimal | 0 | keine |
| Nur Worktree | schwach | niedrig | teilweise |
| Container (Default) | moderat | mittel | teilweise |
| 8-Schichten-MVS | hoch | mittel-hoch | vollständig |
| Firecracker | sehr hoch | hoch | vollständig, aber unproportional |

## Referenzen

- `docs/research/07-trust-sandboxing.md` — OWASP/NIST/NVIDIA Cross-Validation
- `docs/research/01-claude-code.md` — CVE-Klasse und Bypass-Muster
- `docs/research/02-codex-cli.md` — Codex-Sandbox-Mechanik
- OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/
