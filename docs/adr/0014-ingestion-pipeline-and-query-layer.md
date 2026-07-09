# ADR-0014: Ingestion Pipeline and Query Layer

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

With data model (ADR-0006), storage (ADR-0008), LLM integration (ADR-0012), and tech stack (ADR-0013) decided, this ADR defines: (1) the ingestion pipeline stages, and (2) the query/RAG retrieval strategy. These are the two core runtime flows.

## Decision

### 1. Ingestion pipeline

Ingestion runs as a Celery background job (ADR-0013). Stages, in order:

```
Source registered →
  [Stage 1: Fetch]        Git clone / file load / URL fetch
  [Stage 2: Parse]        tree-sitter (code) / OOXML parser (Excel) / doc parser (Word/MD/Txt) / email parser
  [Stage 3: Extract]      Build nodes (symbols, cells, sections, chunks) + structural edges (contains/defines/calls/computes_from/...)
  [Stage 4: Name-resolve] Resolve name-level edges across files (calls/references via import resolution)
  [Stage 5: SQL-inject]   Inject SQL grammar into string literals → parse embedded SQL → extract table refs → data-lineage edges
  [Stage 6: Embed]        Vectorize document chunks + code symbol summaries (embedding model)
  [Stage 7: LLM-associate] Run cross_source_association model → infer related_to edges; run document_entity_extraction → Concept/Feature/Component nodes
  [Stage 8: Persist]      Write all nodes/edges/vectors to ArcadeDB (scoped by source_id + project_id)
```

Each stage is a discrete function with a typed input/output. Stages 1-6 are deterministic; Stage 7 is LLM-driven. This separation means deterministic stages can be re-run without LLM cost if they fail, and the LLM stage can be re-run independently when models improve.

**Incremental (ADR-0009):** on source refresh, stages 1-6 run only on changed files (Git diff for code; full replace for static files); Stage 7 re-runs for affected nodes (delete-and-rebuild of related_to edges touching the source).

**Progress visibility:** each stage reports progress to Celery → Web UI shows per-stage status (fetching / parsing / extracting / associating / done).

### 2. Query layer — hybrid retrieval (graph-first, vector-supplement)

Per the Sourcegraph lesson (ADR-0010): vectors supplement, they do not replace, structural graph search. The query flow:

```
User question (NL) →
  [Intent classification]   tree-sitter-free NLP classification: is this a structural query
                            (callers/callees/dependencies/lineage) or a semantic query
                            (concept/"how does X work"/fuzzy)?
        │
        ├── Structural → [Cypher generation]     cypher_generator model (or structured template fallback)
        │                 → [Graph traversal]    ArcadeDB Cypher query → subgraph result
        │                 → [Evidence gather]    fetch code slices / doc sections / cell values from node provenance
        │
        ├── Semantic → [Vector search]           embedding model → ArcadeDB vector index → top-K chunks
        │             → [Graph expand]           expand from vector-matched nodes via 1-2 hop graph traversal
        │             → [Evidence gather]        fetch provenance for expanded nodes
        │
        └── Mixed → run both, merge & rank

  [Global evidence ranking]  rank all retrieved evidence (graph + vector) by relevance
                             → take top-N (budget-aware, token-efficient)
  [Answer synthesis]         orchestrator model assembles progressive-disclosure answer:
                               1. Graph summary (the relationship/lineage chain)
                               2. Relevant document sections
                               3. Code/data slices (exact lines/cells/formulas)
                             Each layer cites provenance (source + location)
```

**Key principles:**
- **Graph-first for structural questions.** "Who calls X?" / "What does this API depend on?" / "Trace this cell's formula" → direct Cypher graph traversal. No vector search needed; exact structural answer.
- **Vector-supplement for semantic questions.** "How does authentication work?" / "Find code about fraud detection" → vector search finds semantically relevant chunks, then graph expansion pulls in related structural context.
- **Evidence always attached.** Every node in a result carries provenance (file + line range / document section / cell address). The orchestrator assembles the answer with inline citations.
- **Token efficiency.** Global ranking takes top-N evidence before sending to orchestrator. This pre-digests context for the calling AI agent (requirement #10: "save tokens").

### 3. Progressive disclosure answer format

Answers are structured in three layers (ADR-0003 §4), and the Web UI + MCP both return this structure:

```json
{
  "summary": "Short natural-language answer",
  "graph": { "nodes": [...], "edges": [...] },  // layer 1: relationship/lineage visualization
  "documents": [                                 // layer 2: relevant doc sections
    { "source": "...", "section": "...", "text": "..." }
  ],
  "slices": [                                    // layer 3: exact code/data slices
    { "source": "...", "location": "file.go:42-58", "content": "..." }
  ],
  "evidence_chain": [                            // full provenance trace
    { "claim": "...", "source": "...", "location": "..." }
  ]
}
```

The Web UI renders this as: graph (Cytoscape) → clickable document sections → clickable code slices. The MCP endpoint returns the same JSON for AI agents to consume.

## Consequences

- **+** Pipeline stages are discrete and independently re-runnable.
- **+** Hybrid query (graph-first + vector-supplement) gives both exact structural answers and fuzzy semantic matching.
- **+** Progressive disclosure format is consistent across Web UI and MCP — one answer structure, two consumers.
- **+** Token efficiency via global evidence ranking before LLM synthesis.
- **+** Evidence chain is first-class in every answer (requirement #10).
- **−** Pipeline has 8 stages — complexity. Mitigation: each stage is a pure function; stage orchestration is a simple sequential pipeline with clear failure points.
- **−** Intent classification adds a step. Mitigation: lightweight (can be a simple heuristic or a fast model call); misclassification just means running both paths (correctness preserved, slight cost).
- **−** SQL injection (Stage 5) is fiddly per embedding pattern. Mitigation: start with common cases (Python/Java string literals, Jinja templates); expand incrementally.
