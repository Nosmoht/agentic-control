# Features

Dieses Verzeichnis enthält einzelne Feature-Dateien. Jedes Feature ist ein
eigenständiger Lieferumfang, der proposed → in_progress → done läuft und
unabhängig von anderen Features abgenommen werden kann.

Die Spec (`docs/spec/SPECIFICATION.md`) sagt *was das System ist*.
Die ADRs (`docs/decisions/`) sagen *warum es so gebaut ist*.
Die Features hier sagen *welche Slices als Nächstes geliefert werden*.

## Naming

`FNNNN-kebab-name.md`. 4-stellig. Monoton. Nie wiederverwendet.
Beispiel: `F0003-cost-aware-routing-stub.md`.

## Frontmatter (6 Pflichtfelder)

```yaml
---
id: F0001
title: SQLite Schema for Core Objects
stage: v0                    # v0 | v1 | v1a | v1b | v2 | v3
status: proposed             # proposed | in_progress | done | rejected | superseded
spec_refs: [§5.7]
adr_refs: [ADR-0001]
---
```

Keine weiteren Felder. `owner`, `created`, `updated`, `depends_on`,
`signed_off_*`, `research_refs` fallen weg — sind aus Git-Log oder
ADR/Spec-Refs ableitbar.

## Body (feste Reihenfolge)

1. **Context** — ≤ 6 Sätze. Warum dieses Feature existiert.
2. **Scope** — Bullet-Liste: was ist drin.
3. **Out of Scope** — Bullet-Liste: was explizit nicht drin; Verweis auf
   Nachfolge-Feature-ID wenn möglich.
4. **Acceptance Criteria** — nummerierte, testbare Aussagen.
5. **Test Plan** — wie jedes Kriterium geprüft wird.
6. **Rollback** — was „Undo" bedeutet für dieses Feature.

**Risks & Mitigations** ist optional, nur bei nicht-trivialen Features.

## Lifecycle (3 Zustände)

| Zustand | Bedeutung | Wer darf transitionieren |
|---|---|---|
| `proposed` | Datei existiert, Scope drafted | Agent oder Nutzer |
| `in_progress` | Arbeit läuft auf Branch | Agent oder Nutzer |
| `done` | In main gemerged, Akzeptanzkriterien erfüllt | **Nur Nutzer** |
| `rejected` / `superseded` | Terminal | **Nur Nutzer** |

Der einzige harte Gate: `done` setzt der Nutzer per Commit. Alles andere
ist frei.

## Anti-Redundanz: Wo gehört dieser Satz hin?

Eine Cheat-Sheet für Grenzfälle:

| Satztyp | Gehört in |
|---|---|
| „Wir entscheiden X statt Y, weil Z." | **ADR** (`docs/decisions/`) |
| „Das System hat einen X-Zustand mit Übergängen Y → Z." | **Spec** (`docs/spec/SPECIFICATION.md`) |
| „Feature F0003 liefert die CLI-Implementierung von X, verifiziert durch Test T1." | **Feature** (hier) |
| „Hintergrund: X funktioniert empirisch besser als Y (Quelle Z)." | **Research** (`docs/research/`) |
| „Nutzer-Anforderung: wir müssen X regelmäßig tun." | **Plan** (`docs/plans/project-plan.md`) oder **Spec §11.3** |

Wenn ein Feature-Text „Decision/Entscheidung/Options considered" enthält, ist
das ein Signal: der Inhalt gehört in einen ADR. Feature bleibt slank und
verweist.

## Index

Manuell gepflegt. Bei Änderung an Frontmatter bitte hier aktualisieren.

| ID | Titel | Stage | Status | ADR | Spec |
|---|---|---|---|---|---|
| F0001 | SQLite Schema for Core Objects | v0 | proposed | ADR-0001, ADR-0003 | §5.7 |
| F0002 | `work add` / `work next` CLI | v0 | proposed | ADR-0001 | §5.3 |
| F0003 | Cost-Aware Routing Stub | v1a | proposed | ADR-0014 | §5.3, §8.6 |
| F0004 | Benchmark Awareness (Manual Pull) | v1a | proposed | ADR-0014 | §5.5, §8.6 |
| F0005 | Benchmark-Curated Pin Refresh | v1a | proposed | ADR-0014, ADR-0011, ADR-0016 | §5.3, §6.2, §8.6 |
| F0006 | Runtime Records SQLite Schema and Reconcile CLI | v1a | proposed | ADR-0011, ADR-0016 | §5.7, §6.2, §8.4, §10.4 |
| F0007 | Tool-Risk-Drift Detection | v1a | proposed | ADR-0015, ADR-0011, ADR-0016 | §5.4, §8 |
| F0008 | V1 Domain Schema (Run, Artifact, Evidence) | v1a | proposed | ADR-0001, ADR-0003, ADR-0016 | §5.7 |

## Verweise

- [`../plans/project-plan.md`](../plans/project-plan.md) — Master-Plan mit
  Milestones und Stage-Rahmen.
- [`../spec/SPECIFICATION.md`](../spec/SPECIFICATION.md) — normative V1-Spec.
- [`../decisions/`](../decisions/) — Architekturentscheidungen.
- [`../research/`](../research/) — empirische Belege.
