"""Architecture rule: only the persistence package may import from ``sqlalchemy.orm``.

ADR-0020 keeps SQLAlchemy as a connection/type layer only. ORM features
(declarative_base, sessionmaker, relationship, ...) are forbidden in
contracts/cli code to preserve Pydantic-First (ADR-0018).
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent / "src" / "agentic_control"
ALLOWED_DIR = SRC / "persistence"
PATTERN = re.compile(r"^\s*(from\s+sqlalchemy\.orm|import\s+sqlalchemy\.orm)", re.MULTILINE)


def test_no_sqlalchemy_orm_imports_outside_persistence() -> None:
    offenders: list[Path] = []
    for py in SRC.rglob("*.py"):
        if ALLOWED_DIR in py.parents or py == ALLOWED_DIR:
            continue
        if PATTERN.search(py.read_text()):
            offenders.append(py)
    assert not offenders, (
        "sqlalchemy.orm imports forbidden outside persistence package; "
        f"offenders: {offenders}"
    )
