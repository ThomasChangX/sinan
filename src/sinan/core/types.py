"""Graph type names — the single source of truth (铁律 #1).

This module is the ONLY place where NodeType and EdgeType may be defined.
Packs must use ``NodeType.CODE_SYMBOL`` / ``EdgeType.CALLS`` members, never raw
strings. The architecture-gate test ``test_node_edge_types_defined_only_in_core``
enforces that no StrEnum subclass named NodeType/EdgeType exists outside this
file. See ADR-0006 (data model) and ADR-0020 (governance).

Slash-variant names in ADR-0006 are resolved here with rationale:
- MODULE covers "Module/Package" — same graph role (namespace layer); the
  ``subsystem`` property on the node distinguishes depth if needed.
- DECORATOR covers "Decorator/Annotation" — both are tree-sitter-extracted
  metadata markers feeding DI/route detection.
- CONCEPT covers "Concept/Feature/Component" — all are LLM-extracted domain
  entities of one nature; the ``entity_kind`` property distinguishes them.
- HANDLED_BY is directional (ApiEndpoint → handler CodeSymbol), replacing the
  loose "handles/defined_by" wording in ADR-0006.
"""

from __future__ import annotations

from enum import StrEnum


class NodeType(StrEnum):
    """All node types in the sinan knowledge graph (ADR-0006 §1)."""

    # --- System ---
    PROJECT = "Project"
    SOURCE = "Source"

    # --- Code (tree-sitter extracted) ---
    MODULE = "Module"
    FILE = "File"
    CODE_SYMBOL = "CodeSymbol"
    API_ENDPOINT = "ApiEndpoint"
    CONFIGURATION = "Configuration"
    TEST_CASE = "TestCase"
    CODE_CHUNK = "CodeChunk"
    IMPORT = "Import"
    DECORATOR = "Decorator"

    # --- Documents (three-layer granularity + LLM entity extraction) ---
    DOCUMENT = "Document"
    DOCUMENT_SECTION = "DocumentSection"
    DOCUMENT_CHUNK = "DocumentChunk"
    CONCEPT = "Concept"

    # --- Excel (full OOXML analysis, ADR-0006 §2 — top priority 重中之重) ---
    WORKBOOK = "Workbook"
    WORKSHEET = "Worksheet"
    CELL = "Cell"
    RANGE = "Range"
    TABLE = "Table"
    PIVOT_TABLE = "PivotTable"
    PIVOT_FIELD = "PivotField"
    PIVOT_CACHE = "PivotCache"
    CHART = "Chart"
    DEFINED_NAME = "DefinedName"
    SHARED_FORMULA = "SharedFormula"
    DATA_VALIDATION = "DataValidation"
    FORMULA = "Formula"
    CONDITIONAL_FORMATTING = "ConditionalFormatting"

    # --- Email ---
    EMAIL_MESSAGE = "EmailMessage"

    # --- Cross-cutting ---
    VALIDATION_RULE = "ValidationRule"


class EdgeType(StrEnum):
    """All edge types in the sinan knowledge graph (ADR-0006 §7)."""

    CONTAINS = "contains"
    DEFINES = "defines"
    CALLS = "calls"  # name-level + name-resolution (ADR-0006 §5)
    REFERENCES = "references"
    IMPLEMENTS = "implements"
    BINDS = "binds"  # DI binding, framework-pack detected
    INVOKES = "invokes"  # UI/API client → ApiEndpoint, URL-pattern matched
    HANDLED_BY = "handled_by"  # ApiEndpoint → handler CodeSymbol (directional)
    COMPUTES_FROM = "computes_from"  # Excel formula dependency
    SOURCES_FROM = "sources_from"  # pivot/data source chain
    VISUALIZES = "visualizes"
    VALIDATES = "validates"
    DESCRIBES = "describes"
    REPLY_TO = "reply_to"
    SHARED_WITH = "shared_with"  # Excel shared formula (slave→master)
    RELATED_TO = "related_to"  # LLM-inferred, carries confidence


# --- Registries (completeness is asserted by test_all_types_registered) ---
# Every enum member MUST appear here. New members require a registry entry.

NODE_TYPE_REGISTRY: dict[NodeType, str] = {
    NodeType.PROJECT: "Analysis project; primary isolation boundary",
    NodeType.SOURCE: "A registered data source (Git repo@branch, Excel file, etc.)",
    NodeType.MODULE: "Namespace / directory hierarchy layer (covers Module & Package)",
    NodeType.FILE: "A source file",
    NodeType.CODE_SYMBOL: "Function/Class/Method/Interface/Enum/Type/Variable (sub-typed)",
    NodeType.API_ENDPOINT: "An HTTP endpoint (framework route-registration detected)",
    NodeType.CONFIGURATION: "Declarative config (Spring XML/YAML, DI module, annotations)",
    NodeType.TEST_CASE: "A test function/method — describes/validates the feature under test",
    NodeType.CODE_CHUNK: "A line-range slice of a file, for precise display",
    NodeType.IMPORT: "An import statement (feeds cross-file name resolution)",
    NodeType.DECORATOR: "Decorator/Annotation (@Inject, @RestController, etc.)",
    NodeType.DOCUMENT: "Whole file (Word, Markdown, Txt, Email-as-doc)",
    NodeType.DOCUMENT_SECTION: "Structural section (Markdown heading, Word paragraph block)",
    NodeType.DOCUMENT_CHUNK: "Semantic chunk (fixed token window) — the embedding/retrieval unit",
    NodeType.CONCEPT: "LLM-extracted domain entity (Concept/Feature/Component)",
    NodeType.WORKBOOK: "The .xlsx file (= a Document)",
    NodeType.WORKSHEET: "A sheet",
    NodeType.CELL: "A non-empty cell (formula or value); empty cells not indexed",
    NodeType.RANGE: "First-class node (not expanded into cells by default) — TACO/HyperFormula model",
    NodeType.TABLE: "Excel Table / ListObject — structured, named-column range",
    NodeType.PIVOT_TABLE: "A pivot table",
    NodeType.PIVOT_FIELD: "A pivot row/col/data/filter field",
    NodeType.PIVOT_CACHE: "Independent node — defines the pivot's data source",
    NodeType.CHART: "A chart — visualizes a Range/PivotTable",
    NodeType.DEFINED_NAME: "Workbook-level named range; formula resolution anchor",
    NodeType.SHARED_FORMULA: "OOXML shared-formula group (master + slaves via si index)",
    NodeType.DATA_VALIDATION: "<dataValidations> — allowed values / constraints",
    NodeType.FORMULA: "A formula as an addressable object",
    NodeType.CONDITIONAL_FORMATTING: "Conditional formatting (low priority in v1)",
    NodeType.EMAIL_MESSAGE: "An email; reply_to structural edge via In-Reply-To/References",
    NodeType.VALIDATION_RULE: "Generic validation (from code, docs, or Excel)",
}

EDGE_TYPE_REGISTRY: dict[EdgeType, str] = {
    EdgeType.CONTAINS: "Containment",
    EdgeType.DEFINES: "Defines",
    EdgeType.CALLS: "Calls (name-level + name-resolution, ADR-0006 §5)",
    EdgeType.REFERENCES: "References (incl. Table[Col]/DefinedName resolution)",
    EdgeType.IMPLEMENTS: "Implements interface",
    EdgeType.BINDS: "DI binding (Interface→Impl, framework-pack detected)",
    EdgeType.INVOKES: "UI/API client → ApiEndpoint (URL-pattern matched)",
    EdgeType.HANDLED_BY: "ApiEndpoint → handler CodeSymbol (directional)",
    EdgeType.COMPUTES_FROM: "Excel formula dependency (Formula/Cell → Range)",
    EdgeType.SOURCES_FROM: "Pivot/data source chain (PivotTable→PivotCache→source Range)",
    EdgeType.VISUALIZES: "Chart → data source",
    EdgeType.VALIDATES: "Validates",
    EdgeType.DESCRIBES: "Describes (static or LLM)",
    EdgeType.REPLY_TO: "Email reply",
    EdgeType.SHARED_WITH: "Excel shared formula (slave→master)",
    EdgeType.RELATED_TO: "Semantic association (LLM-inferred, carries confidence)",
}
