---
topic: docs-structure
tier: E
date: 2026-04-23
status: draft
---

# Brief 16: Dokumentations-Struktur fuer Architektur-Specs (2025–2026)

## Forschungsfrage

Wie strukturiert man Architektur-/Spezifikations-Doku Stand 2025–2026 fuer ein
Single-User-Repo, das RESEARCH (Briefs), SPEC (Synthese) und LEGACY haelt und
fuer Mensch + agentische Tools (Claude Code, Codex CLI) lesbar bleibt?

## Methodik

Fuenf Sub-Queries: Frameworks (arc42/C4/Diataxis), ADR-Praxis (Nygard/MADR),
Docs-as-Code, OSS-Repo-Layout, Diagramme+Discoverability. Tier 1–2 bevorzugt,
≥2 unabhaengige Quellen pro nicht-trivialer Aussage, Fetches via `r.jina.ai`.
Direkt gelesen: arc42 Overview, Diataxis, MADR, matklad ARCHITECTURE.md.

## Befunde

### Etablierte Frameworks

**arc42 — strukturelle Schablone, nicht Methode.**[^arc42] 12 feste Abschnitte:
1 Ziele, 2 Randbedingungen, 3 Kontext, 4 Loesungsstrategie, 5 Bausteinsicht,
6 Laufzeit, 7 Deployment, 8 Querschnitt, 9 Entscheidungen, 10 Qualitaet,
11 Risiken, 12 Glossar. Gliederung fix, Tiefe frei. arc42 nennt keine
load-bearing-Teilmenge; Praxis fuellt 1/3/4/5/9 dicht, 7/10/11 duenn.
Abschnitt 9 ist explizit ADR-Container.[^arc42ex] v8.2 seit 01/2023,
keine Breaking Changes.

**C4 — Diagrammhierarchie, kein Doku-Framework.**[^c4] Context (L1), Container
(L2), Component (L3), Code (L4). L1+L2 liefern empirisch den meisten
Wert, L3 selektiv, L4 meist ueberfluessig.[^c4practice] Begriffe load-bearing:
Container = deploybar, Component = nicht-deploybar innerhalb eines Containers;
"Subkomponenten" sind Antipattern.[^c4misuse] C4 fuellt arc42-§3 und -§5.

**Diataxis — Ausrichtung nach Nutzerbeduerfnis.**[^diataxis] 2×2 aus
praktisch/theoretisch × Erwerb/Anwendung → Tutorial, How-to, Reference,
Explanation. Kernforderung: **Trennung der Modi**, ein Dokument = ein Modus.
Fuer Architektur-Specs nur partiell anwendbar (Specs sind Reference+Explanation);
als Linse nuetzlich, nicht als Ordnerachse.

### ADRs in der Praxis

Nygard 2011: Title/Status/Context/Decision/Consequences, eine kurze MD-Datei
pro Entscheidung.[^nygard] MADR 4.0 (09/2024) erweitert um Decision Drivers,
Considered Options, optional Confirmation/Pros-Cons/More-Information.[^madr]
Konvention: `NNNN-title-with-dashes.md` (4-stellig), Ablage `docs/decisions/`
oder `docs/adr/`, Lebenszyklus `proposed → accepted → deprecated | superseded
by ADR-NNNN`.[^madr] Nummerierung ist hier sinnvoll: ADRs sind unveraenderliche
Ereignisse, `ADR-0007` bleibt stabil.

### Docs-as-Code

Konsens der Generatoren (MkDocs, Docusaurus, Starlight):[^docsascode]
Markdown/MDX-Quelle, Git-Versionierung, CI-Build, statisches Hosting.
Docusaurus + Starlight versionieren nativ, MkDocs via `mike`. Trend 2025:
Migration Docusaurus → Starlight (Astro). **Produktwahl fuer unser Repo
irrelevant**; wichtig sind die Lehren: Markdown-Quelle, flache Ordner,
relative Cross-Links, kein Binaer-Kram.

### Repo-Layout — Konventionen 2025-2026

Root-Files reifer OSS-Projekte:[^matklad][^agents] `README.md`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `LICENSE`. `ARCHITECTURE.md`
seit matklad (2021) etabliert — kurz, codemap-orientiert.[^matklad] `AGENTS.md`
seit 08/2025 de-facto-Standard (>60k Repos Ende 2025, Linux-Foundation-
unterstuetzt), maschinen-lesbarer Companion zum README fuer Coding-Agents.[^agents]
`ROADMAP.md`, `docs/adr/`, `GLOSSARY.md` verbreitet, aber nicht kanonisch.

Ablage: kurzes im Root, umfangreiches in `/docs/` (Temporal, LangChain,
Kubernetes). Separates Doku-Repo nur bei eigener Deploy-Kadenz (LangChain
seit 2024 `langchain-ai/docs` separiert).[^lc] Temporal haelt Architektur in
`docs/architecture/` im Hauptrepo.[^temporal]

### Nummerierung und Reihenfolge

Prefix `00-/01-` gut fuer **sequenzielle Lesepfade** (Tutorials, Research-
Briefs)[^worldbank] und Antipattern fuer Referenz-Doku: Einfuegen erzwingt
Umnummerierung, Links brechen. Zettelkasten nutzt Nummern als *stabile ID*
ohne Ordnungsanspruch.[^zettel] ADRs: Nummerierung Pflicht. Spec-Doku:
sprechende Namen, keine Reihenfolge-Nummern.

### Versionierung

Konsens:[^doctave] Doku folgt Code-Releases. Status-Header im Frontmatter
(`status: draft | stable | deprecated | superseded`) + Datumsstempel sind
Standard. Fuer Architektur zusaetzlich Code-Tag, fuer das die Spec gilt.
Deprecated-Docs nicht loeschen, sondern markieren (Banner/Redirect).

### Atomic vs. Monolithic

Zwei Lager: matklad plaediert fuer **ein ARCHITECTURE.md** (kurz, kein
Link-Verfall, Symbol-Suche).[^matklad] arc42 erlaubt beides. Konsens:
**monolithisch bis ca. 1500 Zeilen**, danach splitten entlang arc42-Abschnitten.
Research-Briefs und ADRs sind per Definition atomic.

### Diagramme

**Mermaid** alternativlos fuer Markdown-Repos: nativ gerendert in GitHub
(seit 2022), GitLab, VS Code, Obsidian.[^mermaid] PlantUML hat reichere
Syntax, kein natives GitHub-Rendering (Action/Kroki noetig).[^diagramcompare]
D2: modernes Auto-Layout, aber kein GitHub-Native, kleines Oekosystem.
Excalidraw: Skizzen, nicht Spec (Binaer-JSON, diff-feindlich).
**Default: Mermaid**; PlantUML nur wenn Mermaid-Syntax nicht reicht.

### Discoverability

- **Index-Dateien** (`README.md` pro Ordner) = einfachster tool-unabhaengiger TOC.
- **Frontmatter-Tags** (`topic`, `tier`, `status`) → `ripgrep`- oder
  Dataview-Queries.
- **Graph-Navigation** (Obsidian-Backlinks) fuer Menschen nuetzlich, fuer Agenten
  irrelevant — Agenten brauchen Pfade, keine Graphen.
- **Map of Content (MOC)** aus Zettelkasten: eine Datei verlinkt verwandte
  Notizen.[^zettel]

## Quellenbewertung

Tier 1: arc42.org, diataxis.fr, c4model.com, adr.github.io/madr, Nygard
(Cognitect), GitHub Blog, Linux Foundation. Tier 2: matklad (rust-analyzer-
Autor), doctave, Temporal- und LangChain-Repos direkt. Cross-Validation
erfuellt ausser: Antipattern-Status der Nummerierung stuetzt sich auf
*einen* Tier-2-Beleg + Zettelkasten-Analogie — **Eigenentscheidung**.

## Implikationen für unser Repo

Empfohlene Zielstruktur (arc42 als Gliederungs-Referenz, nicht als
strikte Ordnung; C4 fuer Diagramme; Diataxis nur als Linse):

```text
/
├── README.md                 # Einstieg: Zweck, Status, Wegweiser
├── ARCHITECTURE.md           # Kurz, Codemap-Stil (matklad) — das V1-System
├── AGENTS.md                 # Agent-spezifische Instruktionen (Claude/Codex)
├── GLOSSARY.md               # Domain-Begriffe (aus 11-glossary.md)
├── CHANGELOG.md              # Versions-/Spec-Stand
├── docs/
│   ├── spec/                 # Die normative V1-Spezifikation
│   │   ├── 01-ziele.md       # arc42 §1
│   │   ├── 02-kontext.md     # arc42 §3
│   │   ├── 03-bausteine.md   # arc42 §5 + C4-L1/L2
│   │   ├── 04-laufzeit.md    # arc42 §6
│   │   ├── 05-konzepte.md    # arc42 §8 (Trust, State, Lifecycle)
│   │   ├── 06-qualitaet.md   # arc42 §10
│   │   └── 07-risiken.md     # arc42 §11
│   ├── decisions/            # ADRs, MADR-Format, NNNN-title.md
│   │   ├── 0001-control-execution-trennung.md
│   │   └── ...
│   └── research/             # Die 16 Briefs (bleiben als Evidenz)
│       ├── 00-research-plan.md
│       ├── 01-claude-code.md
│       ├── ...
│       └── 99-synthesis.md   # Bruecke von Research zu Spec
└── archive/                  # Ehemalige 00-11 + REVIEW.md, unveraendert
    ├── README.md             # Erklaert Status als historisch
    ├── 00-README.md
    ├── ...
    └── REVIEW.md
```

**LEGACY/SPEC/RESEARCH-Trennung:**

- **SPEC** (`docs/spec/` + Root): normativ, arc42-orientiert,
  `status: stable|draft` im Frontmatter.
- **RESEARCH** (`docs/research/`): evidenzsammelnd, `tier: A–E`,
  numerische Prefixe erlaubt (sequenzieller Lesepfad).
- **LEGACY** (`archive/`): nicht geloescht, per `archive/README.md` als
  "nicht verbindlich, ersetzt durch docs/spec" markiert.

**Naming**: Root `UPPERCASE.md`. `docs/spec/NN-kurzname.md` (2-stellig nur,
weil arc42-Abschnitte fest). ADRs `NNNN-title.md`. Briefs behalten Nummern.

**Diagramme**: Mermaid inline in allen MD-Dateien; keine Binaer-Diagramme.
C4-L1/L2 in `docs/spec/02-kontext.md` und `03-bausteine.md`.

**Frontmatter-Standard** (ausser Root): `topic`, `tier` (Research) oder
`arc42-section` (Spec), `date`, `status`, optional `supersedes`/`superseded-by`.

## Offene Unsicherheiten

- `AGENTS.md` Root vs. `.agents/` — Standard ist Root, bei grossen Instruktionen
  Auslagerung. Offen, welche Variante fuer uns trifft.
- ADR-Evidenz: Verweis auf die 16 Briefs via Citation-Keys oder eigener
  Evidenz-Block? Literatur schweigt — pragmatische Entscheidung.
- Versionierungs-Modell Single-User: SemVer ohne Release-Kadenz sinnlos;
  Datum (`2026-04`) vs. Spec-Revision (`v1`,`v2`) offen.
- Diataxis fuer Spec-Gliederung: reine Linse reicht, nicht als Ordnerachse
  — diese Einordnung nicht literaturgestuetzt.

## Quellen

[^arc42]: arc42 Template Overview, arc42.org/overview (Tier 1).
[^arc42ex]: arc42 Documentation, Beispiel "Use ADRs in Nygard format",
  docs.arc42.org/examples/decision-use-adrs/ (Tier 1).
[^c4]: c4model.com, Home (Tier 1).
[^c4practice]: "C4 Model Diagrams: Practical Tips for Every Level",
  revision.app/blog/practical-c4-modeling-tips (Tier 3).
[^c4misuse]: "Misuses and Mistakes of the C4 model", workingsoftware.dev
  (Tier 2, von Gernot Starke, arc42-Co-Autor).
[^diataxis]: diataxis.fr/ und /start-here/ (Tier 1, Daniele Procida).
[^nygard]: M. Nygard, "Documenting Architecture Decisions", cognitect.com,
  2011 (Tier 1).
[^madr]: MADR 4.0, adr.github.io/madr/ und GitHub adr/madr (Tier 1).
[^docsascode]: "Starlight vs. Docusaurus for building documentation",
  blog.logrocket.com; "MkDocs vs Docusaurus", blog.damavis.com (Tier 2/3).
[^matklad]: A. Kladov, "ARCHITECTURE.md", matklad.github.io, 2021 (Tier 2).
[^agents]: InfoQ, "AGENTS.md Emerges as Open Standard", 2025-08; Linux
  Foundation Press Release Agentic AI Foundation; agents.md (Tier 1).
[^lc]: LangChain Repository Structure, python.langchain.com und
  github.com/langchain-ai/docs (Tier 2).
[^temporal]: Temporal Repo, docs/architecture/README.md auf
  github.com/temporalio/temporal (Tier 2).
[^worldbank]: World Bank Template, "Folder Structure and Naming Conventions",
  worldbank.github.io/template (Tier 3).
[^zettel]: "The Zettelkasten Method in Obsidian", desktopcommander.app
  (Tier 3, als Sekundaerquelle fuer Luhmann-Praxis).
[^doctave]: "Documentation versioning best practices with docs-as-code",
  doctave.com (Tier 2).
[^mermaid]: GitHub Blog, "Include diagrams in your Markdown files with
  Mermaid" (Tier 1).
[^diagramcompare]: "Text to Diagram Tools Comparison 2025", text-to-diagram.com;
  Kroki.io Dokumentation (Tier 2/3).
