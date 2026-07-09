"""Graph type shapes — the single source of truth (铁律 #2).

Pydantic models defining the *shape* of graph nodes/edges. Together with
``types.py`` (which defines the *names*), this forms the dual single-source-of-
truth enforced by ADR-0020. Packs construct ``NodeModel`` / ``EdgeModel``
instances (or registered subclasses) — never raw dicts — so a missing or
wrong-typed field fails at construction time, before reaching storage.

The cross-check ``test_every_node_type_has_model`` asserts every NodeType maps
to a model in NODE_MODEL_REGISTRY, mirroring the a-stock-assistant precedent
(test_config_yaml_covers_all_model_fields).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from sinan.core.types import EdgeType, NodeType


class Provenance(BaseModel):
    """Evidence-chain anchor — where this node/edge came from.

    Required by ADR-0003: every claim must trace back to its original source.
    """

    source_ref: str = Field(description="Identifier of the originating Source node")
    location: str = Field(
        description=(
            "Human-readable location: 'path/to/file.go:42-58', 'sheet!B5', 'doc §3.2', 'msg <id>'"
        )
    )
    start_line: int | None = Field(default=None, description="Start line (code/data files)")
    end_line: int | None = Field(default=None, description="End line (code/data files)")
    start_byte: int | None = Field(default=None, description="Start byte offset (documents)")
    end_byte: int | None = Field(default=None, description="End byte offset (documents)")


class NodeModel(BaseModel):
    """A node in the knowledge graph.

    Specific node kinds (CodeSymbol, PivotTable, etc.) MAY define richer
    subclasses registered in NODE_MODEL_REGISTRY. The base shape is always
    valid — type-specific fields live in ``properties`` or a subclass.
    """

    id: str
    project_id: str
    source_id: str
    node_type: NodeType
    properties: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance


class EdgeModel(BaseModel):
    """A directed edge in the knowledge graph.

    ``confidence`` is None for deterministic edges (calls/contains/...) and a
    float in [0,1] for LLM-inferred edges (RELATED_TO) — ADR-0006 §5 / §7.
    """

    id: str
    project_id: str
    source_id: str
    edge_type: EdgeType
    from_node: str = Field(description="ID of the source node")
    to_node: str = Field(description="ID of the target node")
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(
        default=None,
        description="None for deterministic edges; [0,1] for LLM-inferred RELATED_TO",
    )


# --- Model registry (completeness asserted by test_every_node_type_has_model) ---
# Initially every NodeType maps to the base NodeModel — sufficient because all
# nodes share the base shape and carry kind-specific data in `properties`.
# As packs need richer typed fields, they register subclasses here, e.g.:
#   NODE_MODEL_REGISTRY[NodeType.CODE_SYMBOL] = CodeSymbolModel
# Subclasses are added WITH the using-pack, not preemptively (avoid over-design).
NODE_MODEL_REGISTRY: dict[NodeType, type[NodeModel]] = dict.fromkeys(NodeType, NodeModel)
