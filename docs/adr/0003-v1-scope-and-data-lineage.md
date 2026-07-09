# ADR-0003: v1 Scope — Information Graph, No People Attribution; Bounded Data Lineage

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

Two scope refinements from the grilling:

1. The user dropped people attribution / responsibility tracking entirely (no "who knows this", "who built this"). The graph is about *information and its relationships*, not *people and information*.

2. Data lineage is bounded to **what is observable in user-provided sources**, not independently reconstructed by sinan.

## Decision

### 1. No people attribution in v1 (and likely ever)
The knowledge graph contains no Person nodes, no commit-author activity graphs, no "who knows / who built" attribution. Git/ALM ingestion extracts *content* (commits as change-events that explain design intent via their messages, PR discussions as design rationale) but **not** author identity as a first-class graph dimension. Author names may be retained as raw provenance metadata on a node, but are not queryable graph structure.

> Rationale: keeps the graph focused and avoids the heavy ingest pipeline (activity aggregation, reviewer graphs, expertise scoring) that attribution requires.

### 2. Data lineage is bounded to user-provided sources
sinan does **not** perform independent static analysis to reconstruct data lineage (no SQL-lineage extraction from arbitrary datasets, no UI→API static taint analysis). Instead, lineage is surfaced by **linking what the user-provided sources already expose**:

- If a document describes "report X calls API Y, which runs SQL Z against tables T1, T2" → sinan links report→API→SQL→tables as graph edges, with the document as evidence.
- If an Excel file contains formulas → sinan extracts the formula and links the cell to its referenced ranges.
- If API code contains validation rules → sinan links the API endpoint node to its validation definitions.

The lineage chain is only as complete as the user's sources make it. sinan connects the dots; it does not invent dots.

### 3. Lineage answer shape is fixed
Answers to lineage questions (e.g. "why is this cell this value?") must return:
- The **formula / computation** behind the value.
- The **allowed values** (if any constraint is defined).
- Whether **validation** exists, and what it is.
- The **complete logical chain** from the queried artifact back to its root inputs, each step with evidence.

### 4. Progressive disclosure display
Information presentation is layered, simple → detailed:
1. **Graph/chart** — high-level relationships (the lineage chain as a diagram).
2. **Document** — relevant document sections (natural-language explanation).
3. **Code slice / data slice** — the exact lines/cells/formulas.

Users drill down through these layers. This applies to *all* answers, not just lineage.

## Consequences

- **+** Focused, shippable v1: information graph + evidence chain + progressive display.
- **+** Lineage ingest is bounded — no need to build general-purpose SQL/UI static analysis engines.
- **+** "Bounded by user sources" is an honest contract: sinan connects what's there; gaps are visible as gaps in the chain, not silently filled.
- **−** Cannot answer lineage questions where the user's sources don't contain the connecting information. Must surface "incomplete chain" honestly rather than guess.
- **−** Dropping people attribution means Q1/Q2 ("who knows this", "who built this") are permanently out of scope — confirm this is acceptable long-term, not just for v1.
- **Architectural:** The graph needs node types for: CodeSymbol, File, DocumentSection, Ticket, ApiEndpoint, DataAsset (table/cell/range), ValidationRule, plus edges: calls, references, defines, validates, computes-from, describes, implements, related-to. To be detailed in a data-model ADR.
