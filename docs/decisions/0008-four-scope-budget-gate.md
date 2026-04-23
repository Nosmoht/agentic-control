# ADR-0008: 4-Scope-Budget-Gate als Middleware

* Status: accepted
* Date: 2026-04-23
* Context: `docs/spec/SPECIFICATION.md §8.3`

## Kontext und Problemstellung

Agent-Loops haben dokumentierte Runaway-Muster (bis zu $300/Tag bei
unkontrollierten Schleifen). Weder Anthropic noch OpenAI bieten
serverseitige Tages-Hard-Caps pro API-Key; native Tool-Caps (Claude Code,
Codex CLI) greifen nur innerhalb eines Runs. Ein externer Gate ist Pflicht.

## Entscheidungstreiber

- Harter Kostendeckel muss an mehreren Granularitäten greifen.
- Gate muss **vor** dem LLM-Call sitzen (Pre-Cost-Projektion), nicht danach.
- Einzelner API-Call-Call-Point → eine Middleware-Schicht reicht.
- Muss mit Prompt-Caching kompatibel bleiben (sonst Kostenvorteil verloren).

## Erwogene Optionen

1. **Kein explizites Budget** — auf native Tool-Limits vertrauen.
2. **Nur Request-Level-Cap** — max_tokens + Preis-Schätzung.
3. **2 Scopes** — Request + Tag.
4. **4 Scopes** — Request + Task + Projekt-Tag + Global-Tag (Empfehlung).
5. **5+ Scopes** — zusätzlich Wochen-/Monats-Caps.

## Entscheidung

Gewählt: **Option 4 — 4 Scopes**.

### Caps (Defaults, kalibrierbar)

| Scope | Hard-Cap | Aktion bei Überschreitung |
|---|---|---|
| Request | max_tokens + Preis-Projektion < $0,50 | sofort `reject` |
| Task (Run) | $2 AND 25 Turns AND 15 min Wall-Clock | `abort` Run |
| Projekt/Tag | soft $5 / hard $15 | `pause` → HITL-Override |
| Global/Tag | $25 hard | `suspend` System |

### Empfohlene Optimierungen

- Anthropic Prompt-Caching mit stabilem Prefix: realistisch 90 % Rabatt auf
  gecachte Tokens, zählt nicht gegen ITPM.
- Modell-Routing: Haiku 4.5 für Klassifikation/Formatierung spart 20–25× vs.
  Opus 4.7 bei kaum messbarer Qualitätseinbuße.

### Konsequenzen

**Positiv**
- Runaway-Loops werden auf mehreren Ebenen gekappt.
- Pre-Cost-Projektion verhindert auch große Single-Request-Ausreißer.
- Caps sind transparent und nachvollziehbar — Nutzer sieht, wo gebremst wurde.

**Negativ**
- Eigener Middleware-Layer nötig (kein Off-the-Shelf).
- Caps brauchen 2-Wochen-Kalibrierung — initiale Defaults sind Startwerte,
  keine empirischen Konstanten.
- Hard-Cap auf Global-Tag kann legitime Arbeit blockieren (Feature, nicht Bug).

## Pro und Contra der Optionen

| Option | Schutzgrad | Fehlalarme | Implementierung |
|---|---|---|---|
| Keine | nicht verteidigbar | keine | trivial |
| Request-Only | gegen Ausreißer | wenige | einfach |
| 2 Scopes | moderat | wenige | einfach |
| 4 Scopes | vollständig | moderat | moderate Middleware |
| 5+ Scopes | redundant | viele | überkomplex |

## Referenzen

- `docs/research/13-cost.md` — Budget-Enforcement-Muster, Preisanker 2026
- `docs/research/04-agent-orchestration-libs.md` — LiteLLM-Middleware-Muster
- Anthropic Prompt-Caching: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
