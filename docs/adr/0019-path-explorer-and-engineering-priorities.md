# ADR-0019: Path Explorer & Engineering Priorities

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

ADR-0018 left an open question: whether to build a dedicated "path exploration" entry (option B) or let Ask AI cover it (option A). The user chose (B), establishing a project-wide engineering priority principle in the process.

## Decision

### 1. Path Explorer — dedicated natural-language path-query entry

**Question**: relational exploration — "trace from X to Y", "what path does data take from login to order creation", "where does this report number ultimately originate".

**Why a dedicated entry over Ask AI coverage**: The user's engineering priority principle (§2 below) places quality above maintainability cost. A dedicated Path Explorer produces **more precise path queries** than a general-purpose chat that may generate suboptimal Cypher. The quality of path exploration — shortest path, all paths, annotated with edge semantics — justifies the separate component.

**Implementation**:
- A dedicated UI entry (available from any view, alongside drilldown / Ask AI / Show impact).
- User selects a **start node** and an **end node** (or a target description like "the source database table").
- System computes paths via graph traversal:
  - **Shortest path** (fewest hops).
  - **All simple paths** up to a depth cap (default configurable).
  - Each path annotated with edge semantics (e.g. "calls → calls → sources_from → computes_from").
- Result rendered as a **highlighted path subgraph** in Cytoscape, with each hop labeled by its relationship type and provenance.
- "Ask AI about this path" — sends the path as context to chat for explanation.

**Graph traversal basis**: standard shortest-path (BFS) + bounded DFS for all-paths. Edge direction matters: paths follow the semantic direction of relationships (e.g. data flows source→consumer; calls flow caller→callee).

**Industry basis**: [Neo4j adversarial risk path analysis](https://neo4j.com/videos/25-adversarial-risk-analysis-using-knowledge-graphs/), and the general knowledge-graph pattern of "explain the connection between X and Y."

This becomes the **fourth universal action** on every node across all views: drilldown → Ask AI → Show impact → **Trace path**.

### 2. Engineering priority principle: Quality > Maintainability > Cost

This is now a **project-wide decision-making principle** recorded as a first-class ADR. It governs all engineering trade-off decisions in sinan:

- **Quality (质量)** — correctness, precision, evidence-backed results, honest labeling, robustness. Highest priority.
- **Maintainability (维护性)** — code clarity, extensibility, pack architecture, ADR-driven consistency. Second priority.
- **Cost (成本)** — development time, compute cost, LLM token cost, engineering effort. Lowest priority.

**Concrete applications**:
- When a choice trades result quality for implementation cost (e.g. dedicated Path Explorer vs relying on general chat), **choose quality**.
- When a choice trades correctness for speed (e.g. name-resolution confidence vs skipping unresolved edges), **choose correctness** — surface honest "unresolved" rather than guess for speed.
- When a choice trades honest "unknown" labeling for simpler implementation, **choose honest labeling**.
- Cost optimizations (token efficiency, incremental builds, caching) are pursued **only after** quality and maintainability are satisfied — not by sacrificing them.

**What this does NOT mean**: cost is ignored. The query layer's global evidence ranking (ADR-0014) pre-digests context for token efficiency; incremental builds (ADR-0009) avoid redundant work; these are valid cost optimizations that don't sacrifice quality. The principle forbids cutting corners on quality/maintainability *to save cost*, not all cost-conscious design.

## Consequences

- **+** Path Explorer gives precise relational exploration that general chat cannot reliably produce.
- **+** "Trace path" as a universal action completes the exploration toolkit (drilldown / ask / impact / trace).
- **+** The engineering priority principle gives a clear tie-breaker for all future design decisions — no more ambiguity on quality-vs-cost trade-offs.
- **+** Aligns with the project's core mission: accurate, evidence-backed project understanding. Quality is the product.
- **−** Path Explorer is a 4th universal action → more frontend work. Accepted per the priority principle.
- **−** "Quality > cost" may mean higher LLM token usage (stronger models, more context). Accepted — the user has explicitly endorsed this trade-off. Token efficiency is pursued within the quality constraint, not by violating it.
- **−** Future contributors must respect the priority order. Mitigation: this ADR is the reference; the AGENTS.md (ADR-0015) must cite it.
