"""Pack interface contracts (ADR-0006, ADR-0014, ADR-0015).

Abstract base classes that every language pack, framework pack, and source
ingestor must implement. Method signatures return ``NodeModel`` / ``EdgeModel``
instances — this makes the Pydantic models the runtime boundary: a pack cannot
return a malformed dict, it must construct a validated model.

Layer rule (ADR-0015 §1, enforced by ``test_packs_do_not_import_internals``):
packs may import from ``sinan.core`` only. They must NOT import
``sinan.storage``, ``sinan.llm``, ``sinan.api``, or ``sinan.query``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from sinan.core.models import EdgeModel, NodeModel


class BaseSourceIngestor(ABC):
    """Fetches and parses a data source into graph nodes/edges.

    One ingestor per source type (GitHubRepoIngestor, ExcelIngestor, ...).
    See ADR-0004 (data sources), ADR-0014 pipeline stages 1-3.
    """

    @abstractmethod
    def fetch(self, source_ref: str, dest_dir: Path) -> Path:
        """Stage 1: fetch the source (git clone / file copy / URL download).

        Returns the local path to the fetched content.
        """

    @abstractmethod
    def parse(self, fetched_path: Path) -> list[NodeModel]:
        """Stages 2-3: parse fetched content and extract structural nodes.

        Returns nodes (Files, Worksheets, Documents, etc.).
        """

    @abstractmethod
    def extract_edges(self, nodes: list[NodeModel]) -> list[EdgeModel]:
        """Stage 3 (edges): extract structural edges (contains, defines, ...)."""

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Identifier for this ingestor's source type (e.g. 'github', 'excel')."""


class BaseLanguagePack(ABC):
    """Tree-sitter-based code analysis for one language (ADR-0006 §3).

    Provides the seven tree-sitter layers: CST build, symbol extraction,
    decorator extraction, call-site extraction, import extraction, code-slice
    rendering, route-registration detection. See ADR-0007 for language scope.
    """

    @abstractmethod
    def parse_file(self, file_path: Path) -> list[NodeModel]:
        """Extract CodeSymbol/File/Import/Decorator nodes from one source file."""

    @abstractmethod
    def extract_calls(self, nodes: list[NodeModel]) -> list[EdgeModel]:
        """Build calls edges (name-level + name-resolution, ADR-0006 §5)."""

    @abstractmethod
    def extract_imports(self, nodes: list[NodeModel]) -> list[EdgeModel]:
        """Build module dependency edges from import statements."""

    @abstractmethod
    def extract_decorators(self, nodes: list[NodeModel]) -> list[NodeModel]:
        """Extract Decorator/Annotation nodes feeding DI/route detection."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Language identifier (e.g. 'typescript', 'python', 'java')."""

    @property
    @abstractmethod
    def file_extensions(self) -> tuple[str, ...]:
        """File extensions this pack handles (e.g. ('.ts', '.tsx'))."""


class BaseFrameworkPack(ABC):
    """Framework-specific detection patterns (ADR-0006 §4, ADR-0007).

    Detects DI bindings, route registration, UI→API calls, and data lineage
    for one framework (Spring, NestJS, dbt, Spark, ...). Without a matching
    framework pack, sinan falls back to symbol-level only — it never guesses.
    """

    @abstractmethod
    def detect(self, nodes: list[NodeModel], edges: list[EdgeModel]) -> list[EdgeModel]:
        """Detect framework-specific edges (binds, invokes, sources_from, ...).

        Operates on the structural graph produced by language packs + ingestors.
        """

    @property
    @abstractmethod
    def framework(self) -> str:
        """Framework identifier (e.g. 'spring', 'dbt', 'spark')."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Language this framework uses (e.g. 'java' for Spring)."""


# --- Pack registry (explicit, not name-guessing) ---
# Packs register themselves here on import. ``test_registered_packs_implement_base``
# asserts every entry subclasses the correct base, and every Base subclass under
# src/sinan/packs/ is registered. Empty initially — populated as packs are built.
PACK_REGISTRY: dict[str, type[Any]] = {}
