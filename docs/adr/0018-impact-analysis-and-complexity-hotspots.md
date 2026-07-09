# ADR-0018: Impact Analysis & Complexity Hotspots

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

User asked what other Health-type information is worth adding, based on industry best practice. Research across three domains (CodeScene for code health, Gartner/Atlan for data governance maturity, GitLab Orbit/Endor Labs for impact analysis) was filtered against strict criteria: (1) derivable from existing knowledge graph, (2) answers a high-frequency real question, (3) actionable, (4) sinan's unique advantage. Three candidates were rejected (Bus Factor — needs person attribution excluded by ADR-0003; governance maturity model — needs manual assessment; runtime anomaly detection — sinan is static, ADR-0002). Two were accepted.

## Decision

### 1. Impact / Blast Radius analysis — universal action on all views

**Question**: "If I change this component/data source/validation rule, what will be affected?"

**Industry basis**: [GitLab Orbit pre-merge blast radius](https://medium.com/@poojabhavani19/pre-merge-blast-radius-analysis-with-the-gitlab-orbit-knowledge-graph-f49f3e181e89), [Endor Labs vulnerability blast radius](https://endorlabs.com/learn/vulnerability-blast-radius-how-to-measure-and-reduce-impact), [Augment Code microservice impact](https://augmentcode.com/tools/microservices-impact-analysis). All require a dependency graph — which sinan already has.

**Implementation**: select any node in any view → "Show impact" → graph traversal of all downstream dependents (follow `calls`/`references`/`sources_from`/consumer edges in the dependency direction) → render the impact subgraph with affected nodes highlighted.

**Why sinan does this better than pure code-graph tools**: sinan's graph is cross-source. Changing a SQL table affects not only the code that queries it, but also the reports that display it, the validation rules that check it, and the documents that describe it. Pure code-graph tools show only code-level impact; sinan shows **business-level impact**.

**This is a universal action**, like drilldown and Ask AI (ADR-0016). It becomes the third standard action on every node across all 12 views.

**Impact subgraph content**:
- Affected code symbols (downstream callers)
- Affected reports/dashboards (cells/fields that depend on this)
- Affected data assets (downstream datasets)
- Affected validations (rules that validate downstream of this)
- Affected documents (sections that describe downstream of this)
- Count summary: "This change impacts N code symbols, M report fields, K datasets"

### 2. Complexity Hotspots — visual encoding in Architecture + Module Dependency views

**Question**: "Where is this project most complex, hardest to understand, and should be prioritized for understanding?"

**Industry basis**: [CodeScene Code Health / hotspots](https://codescene.com/use-cases/sonarqube-vs-codescene). CodeScene combines complexity × change-frequency; sinan has no change history (ADR-0002), so uses **pure structural complexity**.

**Implementation**: for each `CodeSymbol`/`Module`, compute a complexity score from graph structure:
- **Fan-in**: how many nodes depend on this (in-degree)
- **Fan-out**: how many nodes this depends on (out-degree)
- **Call-chain depth**: longest path from an entry point to this node
- **Downstream reach**: number of reachable nodes below this

Composite score = weighted combination. Visualized in Architecture (C4) and Module Dependency views via node size (proportional to complexity) and color (red = high complexity hotspot, yellow = medium, green = low).

**Use case**: a new developer or business owner opening the project sees immediately which components are the complex hubs that need attention first — directly serving requirement #6 (top-down understanding) and #10 (help quickly understand the project).

**Integration with Findings (ADR-0017)**: top-N highest-complexity nodes are listed as "Complexity hotspots" findings (severity: info/warning based on threshold).

## Rejected candidates (with rationale)

| Candidate | Why rejected |
|---|---|
| Bus Factor (key-person risk) | Requires git author history + Person nodes. ADR-0003 explicitly excluded people attribution. Would need a contradictory decision. |
| Data governance maturity model (1-5 level score) | Requires manual questionnaire + process audit. sinan's graph cannot auto-compute an organizational maturity level. Project Overview health card (ADR-0016) already covers auto-computable governance metrics. |
| Runtime data quality anomaly detection | Requires connecting to live data pipelines and monitoring value changes over time. sinan is a static analysis tool (ADR-0002: current-state snapshot). Different product category. |

## Consequences

- **+** Impact/Blast Radius is the highest-value graph-derived capability — answers "what happens if I change X" with business-level precision no pure code tool can match.
- **+** Complexity hotspots guide understanding priority — directly serves the "help quickly understand the project" mission.
- **+** Both are graph-derived — no new data sources or heavy engines.
- **+** Impact analysis as a universal action adds consistency (every node in every view can be impact-analyzed).
- **−** Impact traversal on large graphs may be slow. Mitigation: cap traversal depth (default 5 hops, configurable); cache impact results per node until graph changes.
- **−** Complexity score weights are subjective. Mitigation: weights configurable; the score is relative (for ranking/prioritization), not absolute.
- **Open question**: whether to add a dedicated "path exploration" natural-language input ("trace from X to Y") as a separate entry, or let Ask AI cover it. Deferred to user decision.
