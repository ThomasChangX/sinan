# ADR-0010: Reference Implementations Analysis

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

Before building sinan, analyze three relevant existing implementations to extract lessons learned — what to adopt, what to avoid. This informed the decision that no existing solution meets sinan's requirements (ADR-0010 complement), and shaped the MVP-1 scoping (ADR-0011).

## Conclusion: No existing solution covers sinan's needs

All three are **pure code-graph tools**. sinan's core differentiators — multi-source fusion (code + documents + Excel + data lineage), bounded data provenance, LLM cross-source association, framework-aware injection — exist in none of them. Self-building sinan is justified.

## Reference 1: Code-Graph-RAG (vitali87/code-graph-rag)

The closest open-source project. A CLI tool that parses multi-language codebases with tree-sitter, builds a knowledge graph in Memgraph, and answers natural-language queries via LLM→Cypher.

### Architecture
- **Parser**: tree-sitter (per-language grammar submodules)
- **Graph store**: Memgraph (in-memory property graph)
- **Vector store**: Qdrant (optional `semantic` extra)
- **LLM**: pluggable — Google Gemini / OpenAI / Ollama (local)
- **Two-model split**: Orchestrator (reasoning) + Cypher (NL→Cypher query gen)
- **MCP server**: exposes graph query tools to Claude Code / MCP clients

### Strengths to adopt
1. **Per-language tree-sitter grammar as submodules** — clean extensibility model. `cgr language add-grammar <name>` auto-detects node types (function/class/module/call) from `tree-sitter.json`. sinan should adopt this auto-detection approach for its language packs.
2. **Two-model split (Orchestrator + Cypher)** — separates reasoning from query generation. Allows using a cheap/fast model for Cypher gen and a strong model for reasoning. sinan's MCP/chat layer should consider this split.
3. **MCP server with well-scoped tools** — `list_projects`, `query_code_graph`, `get_code_snippet`, `semantic_search`, `ask_agent`. Good tool granularity for AI agents. sinan should design similar MCP tools but extend to multi-source.
4. **Workspace (multi-project) isolation** — `cgr workspace` bundles multiple repos, queries scoped to listed projects. Validates sinan's project-isolation model (ADR-0001).
5. **Real-time file watch + incremental graph update** — `realtime_updater.py` watches files, updates graph on change. Proves file-level incremental is feasible (ADR-0009).
6. **`.cgrignore` (gitignore-syntax exclusions)** — practical necessity for excluding `node_modules`, `vendor`, generated code. sinan must have equivalent.

### Weaknesses / lessons to avoid
1. **Incremental update recalculates ALL CALLS edges on every file change** — the README admits this: "recalculates all CALLS relationships on every file change to ensure consistency... may impact performance on very large codebases." This is the naive approach. sinan's ADR-0009 scopes edge re-resolution to changed files only, avoiding this.
2. **Name-level CALLS edges, not semantic** — same limitation sinan accepts (ADR-0006 §5), but Code-Graph-RAG doesn't surface this honestly to users. sinan must label `resolved: name-based` confidence.
3. **Small local LLMs produce poor Cypher** — the [gdotv analysis](https://gdotv.com/blog/codebase-rag-knowledge-graph-analysis-part-1/) found llama3.2/codellama "unable to adequately answer" even example questions. Lesson: sinan's Cypher-gen model must be capable (GPT-4 class), or fall back to structured query templates instead of freeform NL→Cypher.
4. **No documents, no Excel, no data lineage** — single-source (code only). This is sinan's primary differentiation opportunity.
5. **Memgraph license (BSL 1.1)** — not open source. sinan chose ArcadeDB (Apache 2.0) partly for this reason (ADR-0008).
6. **Graph schema is code-only** — node types are Project/Package/File/Module/Class/Function/Method/Interface/Enum/Type. No Document, no DataAsset, no Concept. sinan's schema (ADR-0006) is much richer.

### What sinan borrows
- Language pack auto-detection from `tree-sitter.json`
- Two-model LLM split concept
- MCP tool granularity
- Workspace/project isolation
- `.sinanignore` exclusion mechanism

---

## Reference 2: FalkorDB CodeGraph

Vendor (FalkorDB) tool that maps Git repos into a FalkorDB knowledge graph, queryable via Cypher and natural language.

### Architecture
- **Parser**: AST-based static analysis
- **Graph store**: FalkorDB (GraphBLAS, Redis-derived)
- **LLM**: GPT-4o / Llama 3-70B for NL→Cypher
- **UI**: web-based graph browser (zoom/pan/query)

### Strengths to adopt
1. **NL→Cypher with strong models** — uses GPT-4o / Llama 3-70B (not small local models), producing reliable Cypher. Confirms Code-Graph-RAG's weakness lesson: use capable models for query gen.
2. **Interactive graph browser** — zoom, pan, drill into nodes. This is exactly sinan's progressive-disclosure requirement (#11). The UI pattern (enter a repo URL → see the graph → query in natural language) is a proven UX.
3. **Structured-query examples** — the blog shows concrete Cypher patterns (impact analysis, dead-code detection, inheritance chains, hub detection). These are reusable query templates for sinan's graph layer.
4. **"Graph beats vector for code" argument** — FalkorDB argues structured relationships (CALLS/INHERITS/DEPENDS_ON) beat embedding similarity for code questions. sinan's hybrid (graph + vector) takes the best of both: graph for structural, vector for semantic fuzzy search.

### Weaknesses / lessons to avoid
1. **Source-available license (SSPL-adjacent)** — not open source. Conflicts with sinan's generic-solution goal.
2. **Single-threaded Redis heritage** — write-heavy concurrent ingestion may bottleneck. ArcadeDB avoids this.
3. **Graph-only, no vectors initially** — added HNSW vectors later as a bolt-on. sinan designs vectors-in-graph from the start (ADR-0008).
4. **No multi-model** — graph only. No document/Excel/data support. Same gap as Code-Graph-RAG.
5. **Vendor lock-in** — tightly coupled to FalkorDB. sinan's storage choice (ArcadeDB) should be abstracted behind a repository interface so the engine is swappable.

### What sinan borrows
- Graph browser UX pattern (zoom/pan/drill/NL-query)
- Cypher query templates for impact/dead-code/hub analysis
- Confirmation that capable LLMs are needed for NL→Cypher

---

## Reference 3: Sourcegraph Cody

Enterprise AI coding assistant built on Sourcegraph's code intelligence platform.

### Architecture
- **Retrieval**: BM25 search over indexed repos (NOT embeddings — they moved away from embeddings)
- **Parser**: tree-sitter (for autocomplete intent detection)
- **Context**: local IDE context + remote Sourcegraph search, globally ranked
- **Scale**: 100 to 100,000+ repos

### Strengths to adopt
1. **Abandoned embeddings for search** — a major architectural decision. Sourcegraph found embeddings require sending code to 3rd parties, are complex to maintain at scale, and vector DBs struggle at 100k+ repos. They replaced with BM25 keyword search + learned ranking signals. **Lesson for sinan**: vectors are for semantic fuzzy matching (doc concepts, "find code about authentication"), NOT the primary code-search mechanism. Code search should use graph traversal + name matching; vectors supplement.
2. **Tree-sitter for intent detection (autocomplete)** — Cody uses tree-sitter to detect what the user is doing (filling a function body, writing a docstring, implementing a call) to pick the right context. sinan's MCP layer can use similar intent detection to choose query strategy (structural graph query vs semantic vector search).
3. **Global context ranking** — combines local + remote context sources, ranks globally, takes top-N. sinan's query layer should similarly rank evidence from multiple sources (graph traversal results + vector matches + doc sections) before presenting to LLM.
4. **Future vision: wikis, docs, tickets as context** — Cody's blog explicitly says they want to expand to "wikis, docs, and engineering tickets." This is exactly sinan's multi-source premise — sinan starts where Cody wants to go.

### Weaknesses / lessons to avoid
1. **Proprietary, not self-hostable as generic solution** — Cody Enterprise requires a Sourcegraph instance. Not an open generic framework.
2. **BM25-only loses semantic matching** — by dropping embeddings entirely, Cody loses fuzzy semantic search ("find code that does X" without exact keywords). sinan keeps vectors for this (hybrid approach).
3. **Code-only** — no documents, Excel, data lineage. Same gap.
4. **Scale-first, not fusion-first** — optimized for searching across many repos, not for deep multi-source understanding within one project's context.

### What sinan borrows
- Vectors as supplement, not primary code search (graph + name matching first)
- Tree-sitter intent detection concept for query strategy selection
- Global evidence ranking across multiple retrieval sources
- Validation that "code + docs + tickets fusion" is an unmet need (sinan's opportunity)

---

## Cross-cutting lessons (applied to sinan)

| Lesson | Source | sinan application |
|---|---|---|
| Per-language tree-sitter grammar as swappable packs | CG-RAG | Language pack architecture (ADR-0006/0007) |
| Two-model LLM split (reason + query-gen) | CG-RAG | MCP/chat layer design |
| MCP tools with clear granularity | CG-RAG | MCP endpoint design |
| Use capable LLMs for NL→Cypher, not small local models | CG-RAG weakness, FalkorDB strength | Default to strong models; offer structured templates as fallback |
| Graph browser UX (zoom/pan/drill/NL-query) | FalkorDB | Web UI progressive disclosure (#11) |
| Cypher query templates (impact/dead-code/hubs) | FalkorDB | Reusable query library |
| Vectors supplement, don't replace, structural search | Sourcegraph | Hybrid: graph-first, vector-supplement |
| Global ranking of evidence from multiple sources | Sourcegraph | Query result aggregation |
| Recalculate only changed-file edges, not all | CG-RAG weakness | ADR-0009 file-level incremental |
| Honest labeling of name-level resolution confidence | CG-RAG weakness | ADR-0006 §5 |
| Abstract storage behind repository interface | FalkorDB lock-in concern | Storage swappability |
| Multi-source fusion (code+docs+data) is the unmet need | All three lack it | sinan's core differentiation |

## sinan's differentiation summary

No existing tool provides:
1. Multi-source fusion (code + documents + Excel + email in one graph)
2. Full Excel OOXML analysis (formulas, pivot lineage, validation)
3. Bounded data provenance (report→API→SQL→table from user sources)
4. LLM cross-source association (code↔doc↔data `related_to` edges)
5. Framework-aware injection + UI→API call chains
6. Self-hostable, Apache-licensed, multi-environment generic framework

sinan builds where these tools stop.
