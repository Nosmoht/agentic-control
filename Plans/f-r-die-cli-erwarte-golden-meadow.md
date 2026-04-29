# Plan: v0-MVP-Implementierung (F0001 + F0002, Python)

**Stand:** 2026-04-29 · **Branch-Ziel:** `feat/v0-schema-and-cli`

## Context

Der Nutzer will den ersten MVP des agentic-control-Systems implementieren
lassen. v0-Scope laut `docs/plans/project-plan.md`:

> **v0 — Handbetrieb mit Schema**: SQLite-Schema + `work add`/`work next`
> laufen, 5+ Work Items manuell durchgezogen.

Vor dieser Plan-Sitzung waren F0001/F0002 nicht ready-to-implement (R3-
Gate aus `~/.claude/CLAUDE.md` verletzt). Commit `d68fccc`
(2026-04-29, „docs(spec+adr+features): make v0 ready to implement")
schließt alle R3-Lücken via ADR-0019 (UUIDv7), ADR-0020 (Alembic),
Spec-Patches (§5.7 Spaltentypen, §6.1 Decision-Lifecycle) und
vollständig überarbeitete F0001/F0002. Eine zwischenzeitlich erwogene
Variante mit Go-CLI wurde verworfen — wir bleiben bei Python wie in
ADR-0017 entschieden.

Dieser Plan ist die Ausführungs-Roadmap für die zwei Features. Es geht
um Code, nicht um Spec-Arbeit.

## Approach

Sequenziell, weil F0002 auf F0001 aufbaut. Ein einziger Topic-Branch
`feat/v0-schema-and-cli`, zwei Commits (einer pro Feature), kein
Direkt-Push auf `main`.

### Schritt 1: Repo-Hygiene (Vorbedingung)

1. `.mcp.json`-Löschung im Working Tree klären (commit oder revert) —
   nicht Teil dieses Plans, aber blocker für saubere Branch-Erzeugung.
2. `git fetch origin && git pull origin main --ff-only` (per
   CLAUDE.md-Branch-Hygiene-Regel).
3. Topic-Branch anlegen.

### Schritt 2: Projekt-Scaffold

- `pyproject.toml` (Python ≥ 3.13, `uv`-Workflow).
- `uv init` + initiale Dependencies: `pydantic`, `sqlalchemy`,
  `alembic`, `typer`, `uuid-utils`, `xdg-base-dirs` (oder Eigenbau für
  XDG-State-Pfad).
- Dev-Dependencies: `pytest`, `ruff`, `mypy`, `import-linter`.
- Verzeichnis-Layout per ADR-0018 + F0001:
  ```
  src/agentic_control/
    contracts/        # Pydantic-Models (Single-Source)
    persistence/      # SQLAlchemy Connection-Layer (kein ORM)
    cli/              # Typer-App
  migrations/
    versions/         # Alembic
    env.py
    alembic.ini       # im Repo-Root
  schemas/            # JSON-Schema-Export-Artefakte (ADR-0018)
  tests/
    unit/
    integration/
    fixtures/
  ```
- `import-linter`-Konfiguration: `sqlalchemy.orm`-Imports nur in
  `src/agentic_control/persistence/` erlaubt (F0001 AC 10).

### Schritt 3: F0001 — Schema + Migrations

Implementierungs-Reihenfolge innerhalb des Features:

1. **Pydantic-Contracts** in `src/agentic_control/contracts/`:
   - `Project`, `WorkItem`, `Observation`, `Decision`.
   - `id: UUID7`-Felder (Pydantic v2 nativer Typ).
   - State-Enums als `Literal[...]` exakt aus Spec §6.1.
   - JSON-Schema-Export-Test in `tests/unit/test_contracts.py`.
2. **Alembic-Setup**: `alembic init migrations`, `env.py` so anpassen
   dass DB-URL aus `AGENTIC_CONTROL_DB_URL`-Env-Var kommt (Default
   `sqlite:///$HOME/.agentic-control/state.db`), DB-Verzeichnis wird
   bei Bedarf erstellt.
3. **Migration `0001_initial_core_objects.py`** — manuell geschrieben
   (kein `--autogenerate`, ADR-0020):
   - `project`, `work_item`, `observation`, `decision`-Tabellen.
   - PKs als `TEXT(36) NOT NULL PRIMARY KEY CHECK(LENGTH(id) = 36)`.
   - FKs mit `ON DELETE RESTRICT`.
   - State-CHECK-Constraints exakt aus F0001-Scope.
   - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`.
4. **Connection-Layer** in `src/agentic_control/persistence/`:
   - `engine.py`: SQLAlchemy-Engine mit `PRAGMA foreign_keys = ON`-
     Hook bei jedem Connect.
   - `repository.py`: Kleine CRUD-Funktionen pro Entity (Pydantic-In,
     Pydantic-Out, SQL-Core dazwischen — kein ORM).
   - UUIDv7-Generator-Wrapper: `from uuid_utils import uuid7` mit
     Kommentar zum 3.14-Import-Swap.
5. **Tests** (alle 10 ACs):
   - Migration auf leerer DB (AC 1, 7).
   - Schema-Vollständigkeit (AC 2).
   - FK-Enforcement (AC 3).
   - State-CHECK-Enforcement (AC 4).
   - UUIDv7-Längen-CHECK (AC 5).
   - Pydantic-Validation vor SQL-Send (AC 6).
   - Schema-Dump-Stabilität gegen Fixture (AC 8).
   - Pydantic↔Schema-Drift-Check (AC 9).
   - `import-linter`-CI-Stage (AC 10).

Commit nach grünen Tests: `feat(v0): SQLite schema with UUIDv7 + Alembic`

### Schritt 4: F0002 — CLI

1. **Typer-App-Skelett** in `src/agentic_control/cli/`:
   - `main.py` mit `app = typer.Typer()`, `work = typer.Typer()`,
     `app.add_typer(work, name="work")`.
   - `pyproject.toml` Entry-Point: `agentctl = "agentic_control.cli.main:app"`.
2. **Sub-Commands** in eigenen Modulen:
   - `add.py`: `work add --title`, `--observation`, `--decision`.
   - `next.py`: `work next`.
   - `show.py`: `work show <id-or-prefix>`.
   - `transition.py`: `work transition <id> <state>`.
3. **ID-Präfix-Resolver** in `src/agentic_control/persistence/prefix.py`:
   - Eingabe-Validierung (≥ 4 Zeichen oder volle UUID).
   - `WHERE id LIKE '<prefix>%'` mit Eindeutigkeits-Prüfung.
   - Mehrdeutigkeits-Fehler mit Kandidaten-Liste + minimal-eindeutiger
     Präfix-Länge.
4. **Lifecycle-Transition-Validator**: Matrix aus F0002 als
   `dict[str, set[str]]` in `src/agentic_control/contracts/lifecycle.py`.
5. **Multiline-Input für `--decision`** (4-Modi-Hybrid):
   - Modus-Dispatch in der Reihenfolge `--from-file` → drei Einzelflags
     → `click.edit()` (Default) → stdin (wenn nicht-TTY).
   - `click.edit()` mit `extension=".md"`, `require_save=True`,
     Markdown-Template aus F0002-Scope.
   - MD-Section-Parser: regex auf `## Context`, `## Decision`,
     `## Consequence`. `#`-Kommentar-Zeilen strippen.
6. **Draft-Recovery**:
   - Pfad: `xdg.StateHome() / "agentic-control" / f"decision-{subject}.draft.md"`.
   - Vor Editor-Launch: Template oder existierender Draft als Seed.
   - Bei DB-Validation-Fehler (Exit 3): Draft bleibt liegen.
   - Bei Erfolg: `draft_path.unlink()`.
7. **Output-Format**: stdout standardmäßig human-readable mit
   8-Zeichen-UUID-Präfixen; `--output json` schreibt vollständige UUIDs
   und maschinenlesbares JSON.
8. **Exit-Codes** (0/2/3/4) per Typer-Custom-Exception-Handler.
9. **Tests** (alle 11 ACs):
   - Typer `CliRunner` für jedes Sub-Command.
   - Editor-Modus mit Mock-Editor (`EDITOR=/bin/true`, `EDITOR=cat`,
     eigenes Skript für Validation-Fehler-Pfad).
   - Headless-Test ohne TTY (`stdin=PIPE`).
   - Präfix-Resolution mit künstlich kollidierenden UUIDs.
10. **Manuelle Verifikation** (v0-Exit-Kriterium):
    - 5+ Work Items real durchziehen (Scaffold-Aufgaben für v1a-Features
      eignen sich als Test-Vehikel).
    - Mindestens eine Decision via `$EDITOR`-Modus, eine via
      `--from-file`.
    - Lifecycle einmal vollständig durchlaufen
      (`proposed → accepted → planned → ready → in_progress → completed`).

Commit nach grünen Tests: `feat(v0): work CLI with Typer and editor-driven decisions`

### Schritt 5: PR-Vorbereitung

- Branch pushen, PR gegen `main` öffnen mit Test-Plan-Checkliste aus
  beiden Feature-Files.
- v0-Exit erst nach 5+ realen Work Items durch den Nutzer markiert
  (Feature-Status `proposed → in_progress` per Code-Push, `done` nur
  durch Nutzer-Commit nach Vokabular-Test).

## Critical Files

**Bestehend (Spec-Quellen, nur lesen):**
- `docs/spec/SPECIFICATION.md` §5.7, §6.1 (normativ für Schema +
  Lifecycles)
- `docs/decisions/0017-implementation-language.md` (Python ≥ 3.13)
- `docs/decisions/0018-schema-first-json-schema.md` (Pydantic-First)
- `docs/decisions/0019-primary-key-strategy.md` (UUIDv7 + uuid-utils)
- `docs/decisions/0020-migrations-tool.md` (Alembic ohne autogenerate)
- `docs/features/F0001-sqlite-schema-core-objects.md` (10 ACs)
- `docs/features/F0002-work-add-cli.md` (11 ACs)

**Neu anzulegen:**
- `pyproject.toml`, `uv.lock`
- `alembic.ini`, `migrations/env.py`, `migrations/versions/0001_initial_core_objects.py`
- `src/agentic_control/__init__.py`
- `src/agentic_control/contracts/{__init__,project,work_item,observation,decision,lifecycle}.py`
- `src/agentic_control/persistence/{__init__,engine,repository,prefix}.py`
- `src/agentic_control/cli/{__init__,main,add,next,show,transition,_editor,_draft}.py`
- `tests/unit/`, `tests/integration/`, `tests/fixtures/schema-0001.sql`
- `.importlinter` (Connection-Layer-Regel)
- `.github/workflows/ci.yml` (uv sync → ruff → mypy → import-linter →
  pytest → schema-drift-check)

## Reused Patterns

- **Pydantic v2 `UUID7`-Typ** (nativ, `from pydantic import UUID7`) —
  laut ADR-0019.
- **`click.edit()`** via Typer (Typer reicht Click 1:1 durch) — laut
  F0002-Decision.
- **`uuid_utils.uuid7()`** als Generator bis Python-3.14-Upgrade.
- **SQLAlchemy `Uuid(as_uuid=True)`** als Spalten-Typ-Wrapper.
- **`xdg-base-dirs`** für `XDG_STATE_HOME`-Resolution
  (Cross-Platform).

## Verification

**Lokal nach jedem Feature:**
```bash
uv sync
uv run ruff check
uv run mypy src/
uv run lint-imports
uv run pytest
```

**Manuell für v0-Exit (Nutzer-Aufgabe):**
```bash
uv pip install -e .
agentctl --help
alembic upgrade head
agentctl work add --title "Implement F0008"
agentctl work add --title "Wire F0006 reconcile-CLI"
agentctl work add --title "Bench-pull MVP"
agentctl work add --title "Routing-pin file validation"
agentctl work add --title "HITL inbox draft"
agentctl work next
agentctl work transition <prefix> accepted
agentctl work transition <prefix> planned
agentctl work transition <prefix> ready
agentctl work transition <prefix> in_progress
agentctl work transition <prefix> completed
agentctl work add --decision --subject <prefix>   # öffnet $EDITOR
agentctl work show <prefix>                        # rendert WI + Decision
```

Exit-Kriterium erfüllt, wenn 5+ Items mind. einmal Lifecycle durchlaufen
und Nutzer schriftlich bestätigt: „Vokabular trägt" oder „R3-Lücken sind
hier: …" (in `docs/reviews/v0-exit.md`).

## Risks / Open

1. **`.mcp.json`-Löschung** im Working Tree ist offene Hygiene-Frage —
   muss vor Branch-Anlage entschieden werden.
2. **9 Commits ungepusht auf `main`** (Stand vor Plan-Anlage) — sollte
   gepusht werden, bevor Topic-Branch anhängt.
3. **`uv-Lockfile-Reproduzierbarkeit`**: bei Erst-`uv sync` kann
   `pydantic-core`-Wheel auf macOS-arm64 abweichen von Linux-CI. ADR-0017
   nennt diese Risiko-Klasse explizit; quartalsweiser Restore-Drill
   (Spec §10.4) ist Mitigation.
4. **`uuid-utils`-Maintenance-Risiko**: Single-Maintainer-Projekt. Bei
   Stillstand vor Python-3.14-Upgrade: Fallback `uuid6`-Library.
5. **Typer + `click.edit()` auf Windows**: VSCode ohne `code --wait`
   kehrt sofort mit leerem Buffer zurück. Doku im `--help`-Text
   erwähnen.
