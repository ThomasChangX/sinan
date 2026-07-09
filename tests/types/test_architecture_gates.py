"""Architecture-gate tests — the consistency engine (ADR-0015, ADR-0020).

These are structural/AST-level tests that catch drift runtime tests miss.
Each test is scoped precisely (see docstrings) to avoid false positives.

Reference precedent: a-stock-assistant tests/types/test_architecture_gates.py
(enum iron-law + registry completeness + config↔model cross-check).
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest
from pydantic import ValidationError

import sinan
from sinan.core import models as models_mod
from sinan.core.interfaces import (
    PACK_REGISTRY,
    BaseFrameworkPack,
    BaseLanguagePack,
    BaseSourceIngestor,
)
from sinan.core.models import NODE_MODEL_REGISTRY, NodeModel
from sinan.core.types import EDGE_TYPE_REGISTRY, NODE_TYPE_REGISTRY, EdgeType, NodeType

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
PACKS_DIR = SRC_ROOT / "sinan" / "packs"
CORE_TYPES_PATH = SRC_ROOT / "sinan" / "core" / "types.py"

# Layer rule: packs must not import these internals (ADR-0015 §1).
FORBIDDEN_PACK_IMPORTS = {"sinan.storage", "sinan.llm", "sinan.api", "sinan.query"}


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


# ---------------------------------------------------------------------------
# Test 1: NodeType/EdgeType may be DEFINED only in core/types.py.
# Scoped to StrEnum subclass *definitions* — member access (NodeType.X) is
# never flagged, because member access is the correct, encouraged usage.
# ---------------------------------------------------------------------------
def test_node_edge_types_defined_only_in_core() -> None:
    offenders: list[str] = []

    for py_file in _iter_python_files(SRC_ROOT):
        if py_file == CORE_TYPES_PATH:
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name in ("NodeType", "EdgeType"):
                # Is it a StrEnum subclass? Use exact base-name match, not substring,
                # to avoid false positives on names like MyStrEnumMixin.
                bases = {ast.unparse(b) for b in node.bases}
                if "StrEnum" in bases:
                    offenders.append(f"{py_file}:{node.lineno} defines {node.name}(StrEnum)")

    assert not offenders, (
        "NodeType/EdgeType may only be defined in core/types.py (铁律 #1). "
        "Offenders:\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# Test 2: every enum member must appear in its registry (no orphans).
# ---------------------------------------------------------------------------
def test_all_node_types_registered() -> None:
    missing = set(NodeType) - set(NODE_TYPE_REGISTRY)
    assert not missing, f"NodeType members missing from NODE_TYPE_REGISTRY: {missing}"


def test_all_edge_types_registered() -> None:
    missing = set(EdgeType) - set(EDGE_TYPE_REGISTRY)
    assert not missing, f"EdgeType members missing from EDGE_TYPE_REGISTRY: {missing}"


# ---------------------------------------------------------------------------
# Test 3: cross-check — every NodeType must have a model (mirrors
# a-stock-assistant test_config_yaml_covers_all_model_fields).
# ---------------------------------------------------------------------------
def test_every_node_type_has_model() -> None:
    missing = set(NodeType) - set(NODE_MODEL_REGISTRY)
    assert not missing, f"NodeType members missing from NODE_MODEL_REGISTRY: {missing}"


# ---------------------------------------------------------------------------
# Test 4: pack interface compliance via explicit PACK_REGISTRY.
# Not name-suffix guessing — uses the registry packs opt into.
# ---------------------------------------------------------------------------
_BASE_CLASSES = {
    BaseLanguagePack,
    BaseFrameworkPack,
    BaseSourceIngestor,
}


def test_registered_packs_implement_base() -> None:
    """Every registered pack must subclass a recognized base."""
    for name, pack_cls in PACK_REGISTRY.items():
        if not any(issubclass(pack_cls, base) for base in _BASE_CLASSES):
            msg = (
                f"PACK_REGISTRY['{name}'] = {pack_cls} does not subclass "
                f"BaseLanguagePack/BaseFrameworkPack/BaseSourceIngestor"
            )
            raise AssertionError(msg)


def test_all_pack_subclasses_are_registered() -> None:
    """Every Base* subclass under src/sinan/packs/ must be in PACK_REGISTRY.

    PACK_REGISTRY keys are stable identifiers (e.g. "python", "dbt"), NOT class
    names — so we check the class appears as a registry *value*, not that its
    name is a key.
    """
    if not PACKS_DIR.is_dir():
        pytest.skip("packs/ directory does not exist yet")

    registered_classes = set(PACK_REGISTRY.values())

    for py_file in _iter_python_files(PACKS_DIR):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {ast.unparse(b) for b in node.bases}
            pack_bases = {
                "BaseLanguagePack",
                "BaseFrameworkPack",
                "BaseSourceIngestor",
            }
            if pack_bases & bases:
                # The class must be registered. We can't resolve the AST ClassDef
                # to a runtime object here, so we check by class name against the
                # registered classes' __name__. This is a heuristic but sufficient
                # for the gate; test_registered_packs_implement_base does the
                # precise runtime check.
                registered_names = {cls.__name__ for cls in registered_classes}
                if node.name not in registered_names:
                    msg = (
                        f"{py_file}:{node.lineno} class {node.name} subclasses a pack base "
                        f"but is not registered in PACK_REGISTRY"
                    )
                    raise AssertionError(msg)


# ---------------------------------------------------------------------------
# Test 5: layer rule — packs must not import internal modules.
# ---------------------------------------------------------------------------
def test_packs_do_not_import_internals() -> None:
    offenders: list[str] = []
    if not PACKS_DIR.is_dir():
        pytest.skip("packs/ directory does not exist yet")

    for py_file in _iter_python_files(PACKS_DIR):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(f) for f in FORBIDDEN_PACK_IMPORTS):
                        offenders.append(f"{py_file}:{node.lineno} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module.startswith(f) for f in FORBIDDEN_PACK_IMPORTS):
                    offenders.append(f"{py_file}:{node.lineno} imports from {node.module}")

    assert not offenders, (
        "Packs must not import storage/llm/api/query (ADR-0015 §1). "
        "Offenders:\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# Test 6: import every module — catches circular imports at import time.
# Non-exhaustive (grows with the codebase) but catches the common case.
# ---------------------------------------------------------------------------
def test_import_all_modules() -> None:
    failures: list[str] = []
    for module_info in pkgutil.walk_packages(sinan.__path__, prefix="sinan."):
        try:
            importlib.import_module(module_info.name)
        except Exception as exc:  # want to collect all failures, not abort
            failures.append(f"{module_info.name}: {exc!r}")

    assert not failures, "Circular/failed imports detected:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Test 7: Pydantic runtime boundary sanity — missing required field rejects.
# Proves the type-shape SoT (铁律 #2) is actually enforced at construction.
# ---------------------------------------------------------------------------
def test_node_model_rejects_missing_field() -> None:
    with pytest.raises(ValidationError):
        NodeModel(  # type: ignore[call-arg] — intentionally incomplete
            id="n1",
            source_id="s1",
            node_type=NodeType.CODE_SYMBOL,
            provenance=models_mod.Provenance(source_ref="s1", location="f:1"),
            # project_id intentionally omitted
        )
