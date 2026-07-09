"""ADR↔code consistency lint (ADR-0020, v4 optimization).

Lightweight docs-as-code check (VeriContext-inspired minimal version — no SHA
hashing, just "does the referenced thing still exist"). Catches the most common
doc drift: an ADR references a file path or enum identifier that was renamed
or deleted.

Scans docs/adr/*.md for:
- Backtick-wrapped paths like `` `src/sinan/core/types.py` `` → assert the path
  exists in the repo.
- ``NodeType.XXX`` / ``EdgeType.XXX`` identifiers → assert XXX is a real member.
"""

from __future__ import annotations

import re
from pathlib import Path

from sinan.core.types import EdgeType, NodeType

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = REPO_ROOT / "docs" / "adr"

# Matches `path/like/this` containing a slash and a dot (file-ish), excluding URLs.
BACKTICK_PATH = re.compile(r"`([a-zA-Z0-9_./-]+\.[a-zA-Z]{1,5})`")
# Matches NodeType.MEMBER or EdgeType.MEMBER where MEMBER is a real-looking
# identifier (2+ chars, not the placeholder "X").
TYPE_MEMBER = re.compile(r"\b(NodeType|EdgeType)\.([A-Z][A-Z0-9_]{1,})\b")

# Only treat backtick paths as repo-relative if they look like repo paths.
# Exclude obvious non-files (e.g. `pyproject.toml` is fine, `http://...` won't match dot-ext rule).
PATH_PREFIXES = ("src/", "tests/", "docs/", ".github/", ".pre-commit", "pyproject")


def _collect_adr_files() -> list[Path]:
    if not ADR_DIR.is_dir():
        return []
    return sorted(ADR_DIR.glob("*.md"))


def test_adr_referenced_paths_exist() -> None:
    """Every backtick-wrapped repo path in an ADR must exist."""
    missing: list[str] = []
    for adr in _collect_adr_files():
        text = adr.read_text(encoding="utf-8")
        for match in BACKTICK_PATH.finditer(text):
            candidate = match.group(1)
            if not candidate.startswith(PATH_PREFIXES):
                continue
            if not (REPO_ROOT / candidate).exists():
                missing.append(f"{adr.name}: `{candidate}` does not exist")
    assert not missing, "ADR references non-existent paths:\n" + "\n".join(missing)


def test_adr_type_identifiers_are_valid() -> None:
    """Every NodeType.X / EdgeType.X in ADR prose must be a real member."""
    valid_node = {m.name for m in NodeType}
    valid_edge = {m.name for m in EdgeType}
    invalid: list[str] = []

    for adr in _collect_adr_files():
        text = adr.read_text(encoding="utf-8")
        for match in TYPE_MEMBER.finditer(text):
            kind, member = match.group(1), match.group(2)
            valid_set = valid_node if kind == "NodeType" else valid_edge
            if member not in valid_set:
                invalid.append(f"{adr.name}: {kind}.{member} is not a valid member")

    assert not invalid, "ADR references invalid type members:\n" + "\n".join(invalid)
