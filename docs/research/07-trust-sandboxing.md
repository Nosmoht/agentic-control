---
topic: trust-sandboxing
tier: B
date: 2026-04-23
status: draft
---

# Brief 07: Trust-Zonen und Sandboxing für codeausführende LLM-Agenten

## Forschungsfrage

Welche verteidigbaren, quellenbelegten Standards gibt es 2025–2026 für Trust-
Zonen und Sandboxing codeausführender LLM-Agenten, welcher Minimum Viable
Sandbox folgt daraus für ein Ein-Personen-System (Laptop + kleiner VPS), und
trägt unser 5-Zonen-Trust-Modell gegen die Literatur?

## Methodik

Drei Rechercheschleifen entlang OWASP, NIST, akademisch, Industrie, MVS,
Taxonomien. Priorität Tier 1 (OWASP, NIST, arXiv, Anthropic, NVIDIA) vor
Tier 2 (Engineering-Posts) vor Tier 3 (Blogs). Jede substanzielle Aussage
≥2-fach belegt oder als unverifiziert markiert. Primärquellen tief gefetcht:
Anthropic Engineering, CaMeL-Paper, CSA Agentic NIST Profil, NVIDIA Blog,
MAESTRO Playbook.

## Befunde

### OWASP LLM Top 10 (aktueller Stand)

Aktiv ist **OWASP Top 10 for LLM Applications v2025** (Nov 2024), seit Dez 2025
ergänzt durch **OWASP Top 10 for Agentic Applications 2026** — explizit für
autonome, tool-nutzende Agenten[^1][^2]. Agenten-relevant:

- **LLM06 Excessive Agency**: drei Wurzelursachen — *excessive functionality*
  (Tools außerhalb Task-Scope), *excessive permissions* (überbreite Rechte),
  *excessive autonomy* (High-Impact ohne HITL)[^1]. Controls: Least-Privilege
  pro Task, Autorisierung **außerhalb** des LLM, Extensions im User-Security-
  Kontext (nicht Service-Identität), Human-Approval für konsequenzreiche
  Aktionen[^1].
- **LLM05 Improper Output Handling** / **LLM02 Sensitive Info Disclosure**:
  Agent-Output ist nie trusted — Downstream muss validieren, Secrets maskieren,
  egress filtern[^2].
- **LLM10 Unbounded Consumption**: Ressourcen-/Zeit-/Kostenlimits sind
  Sicherheits-, nicht nur Kosten-Controls[^2].
- **Agentic Top 10 2026** führt Tool-Poisoning, Delegation-Chain-Exploits,
  Memory-Poisoning als eigene Kategorien[^2].

### NIST AI RMF — Agent-Controls

**NIST AI 600-1 (GenAI-Profil, Juli 2024)** operationalisiert den AI RMF in
zwölf Risikobereichen (u.a. Information Security, Human-AI Configuration,
Value Chain Integration)[^3]. Das Profil adressiert jedoch, was das System
*produziert*, nicht was es *tut* — Delegation und Tool-Autoritäts-Scope in
Sub-Agent-Ketten sind nicht abgedeckt[^3].

Die **CSA Agentic AI RMF Profil v1** (2025) schließt die Lücke[^4]:

- **Autonomy Tiering** (GOVERN): 4-Stufen-Klassifikation, proportional
  Oversight.
- **Delegation Accountability** (GOVERN): Agent-Accountability-Register,
  dokumentierte Autorisierungs-Grenzen.
- **Tool-Use Risk Inventory** (MAP): Tools klassifiziert nach Consequence
  Scope, Reversibilität, Auth-Bedarf, kompositorischem Risiko.
- **Action-Consequence-Graphen** (MAP), **Runtime Behavioral Telemetry**
  (MEASURE): Action-Velocity, Permission-Escalations, Delegation-Tiefe.

### Akademische Forschung 2025–2026

- **CaMeL — Defeating Prompt Injections by Design** (arXiv:2503.18813)[^5]:
  Capability-Schicht um das LLM. Trennt Control-Flow (trusted Query) von
  Data-Flow (untrusted Tool-Output); Untrusted-Daten können Programmfluss
  nicht beeinflussen; Capabilities verhindern Exfiltration. 77% Task-Erfolg
  mit beweisbarer Sicherheit vs. 84% ungeschützt (AgentDojo) — moderate
  Kosten.
- **Design Patterns for Securing LLM Agents** (arXiv:2506.08837)[^6]:
  Action-Selector, Plan-Then-Execute, Dual-LLM, Code-Then-Execute, Context-
  Minimization mit Utility/Security-Trade-offs.
- **Protocol Exploits Survey** (arXiv:2506.23260)[^7]: 30+ Angriffstechniken
  über Host-Tool- und Agent-Agent-Kanäle.
- **Breaking the Protocol — MCP** (arXiv:2601.17549)[^8]: drei fundamentale
  MCP-Schwächen — fehlende Capability-Attestation, Sampling ohne Origin-Auth,
  implizite Trust-Propagation.
- **ATFAA** (arXiv:2504.19956): STRIDE-Erweiterung für Agenten — PDF nicht
  extrahierbar, Details unverifiziert.

### Industrie-Praxis

| Plattform | Isolation | Quelle |
|---|---|---|
| Claude Code (lokal) | Bubblewrap (Linux/WSL2), Seatbelt (macOS); FS nur CWD, Netz via Unix-Socket-Proxy + Domain-Allowlist | [^9][^10] |
| OpenAI Codex CLI (lokal) | Landlock + seccomp, per Default aktiv | [^10] |
| GitHub Copilot Cloud Agent | GitHub-Actions-Runner; optional Docker-Sandbox im MicroVM mit HTTP/HTTPS-Filterproxy ("smart deny-all"), blockt Metadata-Endpoints | [^11] |
| OpenAI Codex Cloud | isolierte Cloud-Umgebung, Details nicht öffentlich | [^11] |
| Cursor Background Agents | bis 20 parallele Agenten auf dedizierten AWS-VMs | [^12] |
| Sourcegraph Cody / Amp | Enterprise-Self-Host möglich; keine dokumentierte kernelnahe Sandbox | [^12] |
| E2B / Northflank / Vercel Sandbox | Firecracker-MicroVMs bzw. Kata+gVisor; Northflank >2 Mio. Workloads/Monat | [^13][^14] |

Konsens: **MicroVMs (Firecracker, Kata) = Goldstandard** für untrusted
Agent-Code (eigener Kernel); **gVisor** als Syscall-Interception-Kompromiss;
**reine Container unzureichend** für arbiträren Code[^13][^14]. NVIDIA
explizit: "within a fully virtualized environment isolated from the host
kernel at all times"; gVisor biete "potentially weaker security
guarantees"[^14].

### Minimum Viable Sandbox (Single-User)

Schnittmenge aus Anthropic-, NVIDIA- und DevContainer-Praxis[^9][^14][^15]:

1. **Worktree pro Task** (Git-Worktree, ein Pfad pro Agent-Run).
2. **Container oder Bubblewrap/Seatbelt** um den Agent-Prozess; CWD rw, Rest
   read-only oder nicht gemountet.
3. **Non-Root** (UID 1000), `--cap-drop=ALL`,
   `--security-opt=no-new-privileges`.
4. **Read-Only-Root-FS**; `/workspace` + `/tmp` (tmpfs) writable.
5. **Egress-Proxy mit Domain-Allowlist** (Package-Registries, Git-Host,
   Modell-Endpoint); Block auf 169.254.169.254 und interne Netze.
6. **Config-Write-Schutz**: `.mcp.json`, `~/.ssh`, `~/.aws`, Shell-RCs
   außerhalb des Mounts.
7. **Ressourcenlimits** (cgroups CPU/Mem, Wall-Clock, Token-Budget) —
   adressiert LLM10.
8. **Secret-Injection pro Task** (keine globale Env-Vererbung).

Darunter fällt man nicht belegbar hinter OWASP-LLM06 und NVIDIA-Empfehlungen.
Voll-MicroVM wäre sauberer, für Laptop+VPS aber Overkill[^14].

### Trust-Zonen-Modelle in der Literatur

Dominante publizierte Taxonomien:

- **MAESTRO** (OWASP-nah, 2025)[^16]: 7 Layer — *Foundation Model*, *Data
  Operations*, *Agent Frameworks*, *Deployment Infrastructure*,
  *Evaluation & Observability*, *Security & Compliance*, *Agent Ecosystem*.
  Phase 4 definiert Trust-Zonen mit Boundary-Crossings und Controls pro
  Boundary.
- **STRIDE + Trust-Boundaries** (klassisch)[^17]: Grenzen zwischen
  Privilegstufen; Data-Flows über Boundaries sind primäres Analyseobjekt.

Unser 5-Zonen-Modell (External Untrusted / Interpreted Human Control /
Decision Core / Integration & Identity / Restricted Execution / Trusted
Knowledge & Audit) ist **keine 1:1-Kopie**, deckt sich aber sinngemäß mit
MAESTRO: External Untrusted ↔ L7 Agent Ecosystem + L2 Data Ops, Decision Core
↔ L3 Agent Frameworks, Restricted Execution ↔ L4 Deployment Infrastructure,
Trusted Knowledge & Audit ↔ L5 Evaluation & Observability, Integration &
Identity ↔ L6 Security & Compliance. Also DDD-orientierte Re-Projektion
derselben Schnitte, kein Eigenbau im negativen Sinn.

## Quellenbewertung

Tier 1: OWASP[^1][^2], NIST[^3], Anthropic[^9], NVIDIA[^14], arXiv[^5][^6][^7][^8].
Tier 2: CSA[^4], MAESTRO[^16], Northflank[^13]. Tier 3 nur zur Kreuzvalidierung
von Claude-Code-Details[^10][^15]. Verworfen: Vendor-Marketing, Blogs ohne
technische Details. Kreuzvalidiert: Claude-Code-Sandbox (Anthropic + 3
Reviews), MicroVM-Konsens (NVIDIA + Northflank), MAESTRO-Layer (offizielles
Playbook).

## Implikationen für unser System

**Konkreter MVS für V1** (Execution-Kontext): Git-Worktree pro Task;
Container Non-Root, Cap-Drop, No-New-Privs, Read-Only-Root-FS, tmpfs;
Egress-Proxy mit Allowlist (z.B. mitmproxy oder squid); cgroup-Limits + Token-
Budget; Secret-Injection pro Task; Config-Write-Schutz.

**OWASP/NIST-Pflichten für V1**:

- LLM06: Tool-Scope pro Task, Human-Approval für irreversible Aktionen, Auth
  außerhalb des LLM (Policy & Governance-Kontext übernimmt das).
- LLM10: harte Kosten-/Zeit-/Token-Budgets pro Run.
- CSA Autonomy Tiering: explizite Stufen je Workflow, dokumentierte
  Eskalationstrigger — passt zu unserem Escalate-late-Prinzip.
- CSA Tool-Use Risk Inventory: **neue Artefakt-Pflicht** — jedes Tool nach
  Reversibilität und Scope klassifiziert.

**Trust-Zonen-Modell**: trägt. Literatur-Support über MAESTRO und STRIDE-
Boundaries; unser Modell ist DDD-spezifische Zerschneidung derselben Grenzen.
"Interpreted Human Control" ist eigenständig benannt, inhaltlich Kombination
aus MAESTRO L7 + L6.

## Offene Unsicherheiten

- Codex-Cloud- und Cursor-Hintergrundagent-Interna nur grob belegt.
- Reale Kosten/Latenz eines Egress-Proxys mit Deep-Inspection im Single-User-
  Kontext nicht benchmark-validiert.
- ATFAA-Details unverifiziert (PDF-Extraktion fehlgeschlagen).
- CaMeL: nur auf AgentDojo validiert — Transfer auf realen Code-Execution-
  Agent offen.
- MAESTRO-Adoption 2026 noch nicht breit belegt.
- Firecracker-vs-Bubblewrap-Schwelle für Ein-Personen-Scope nicht quantitativ
  studiert.

## Quellen

[^1]: OWASP, "LLM06 Excessive Agency", v2025.
  https://owasp.org/www-project-top-10-for-large-language-model-applications/
[^2]: OWASP, "Top 10 for Agentic Applications 2026", Dez 2025.
  https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
[^3]: NIST, "AI 600-1 Generative AI Profile", Juli 2024.
  https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
[^4]: Cloud Security Alliance, "Agentic NIST AI RMF Profile v1", 2025.
  https://labs.cloudsecurityalliance.org/agentic/agentic-nist-ai-rmf-profile-v1/
[^5]: Debenedetti et al., "CaMeL: Defeating Prompt Injections by Design",
  arXiv:2503.18813, 2025.
[^6]: "Design Patterns for Securing LLM Agents", arXiv:2506.08837, 2025.
[^7]: "From Prompt Injections to Protocol Exploits", arXiv:2506.23260, 2025.
[^8]: "Breaking the Protocol: MCP Security Analysis", arXiv:2601.17549, 2026.
[^9]: Anthropic Engineering, "Making Claude Code More Secure and Autonomous",
  Okt 2025. https://www.anthropic.com/engineering/claude-code-sandboxing
[^10]: Truefoundry, "Claude Code Sandboxing", 2026.
  https://www.truefoundry.com/blog/claude-code-sandboxing
[^11]: Microsoft Azure DevBlogs, "GitHub Copilot + MicroVMs via Docker
  Sandbox", 2025.
  https://devblogs.microsoft.com/all-things-azure/best-of-both-worlds-for-agentic-refactoring-github-copilot-microvms-via-docker-sandbox/
[^12]: SitePoint, "AI IDE Comparison 2026: Cursor vs Claude Code vs Cody".
  https://www.sitepoint.com/ai-ides-compared-cursor-claude-code-cody-2026/
[^13]: Northflank, "How to sandbox AI agents in 2026".
  https://northflank.com/blog/how-to-sandbox-ai-agents
[^14]: NVIDIA Developer Blog, "Practical Security Guidance for Sandboxing
  Agentic Workflows", 2026.
  https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/
[^15]: INNOQ, "I sandboxed my coding agents. Now I control their network",
  März 2026. https://www.innoq.com/en/blog/2026/03/dev-sandbox-network/
[^16]: OWASP MAESTRO Playbook, "Seven Architectural Layers", 2025.
  https://agentic-threat-modeling.github.io/MAESTRO/playbook/01-layers.html
[^17]: OWASP Threat Modeling Cheat Sheet.
  https://owasp.deteact.com/cheat/cheatsheets/Threat_Modeling_Cheat_Sheet.html
