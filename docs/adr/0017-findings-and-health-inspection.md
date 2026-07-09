# ADR-0017: Findings & Health Inspection View

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

The user requested a section showing errors and optimization opportunities discovered during system scanning. Industry analysis confirms this is a standard practice across three product domains: code quality (SonarQube Issues), architecture analysis (CodeScene/Arcan anti-patterns), and data observability (Monte Carlo anomalies). The key design principle: sinan's findings should derive from **knowledge-graph structural analysis**, not from a general-purpose static analysis engine (which is out of scope). This is sinan's unique advantage — it already has the graph.

Reference: [Drexel architecture anti-patterns research](https://www.cs.drexel.edu/~yhpc/2019/tse2019.pdf) confirms many architecture anti-patterns are "automatically detectable by analyzing structural relationships" — exactly what a knowledge graph enables.

## Design principle

**Graph-derived findings only.** sinan detects issues by analyzing the structure of its knowledge graph (cycles, orphans, disconnected lineage, missing validation, conflicts). It does NOT run a separate static-analysis engine (no AST-level code-smell rules, no security taint analysis). This keeps sinan focused on "understanding" + "graph-derived risk surfacing," not on becoming SonarQube.

Every finding:
1. Is computed from a graph query (deterministic, repeatable).
2. Cites the specific nodes/edges that triggered it (evidence-backed, traceable — per ADR-0003 evidence-chain principle).
3. Is categorized by domain (architecture / data / documentation / code-resolution).
4. Has a severity (critical / warning / info) and an actionable description.
5. Links to the relevant view for drilldown + "Ask AI about this."

## Decision

### Add View 12: Findings & Health Inspection (发现与优化建议)

A dedicated view showing all graph-derived issues and optimization opportunities, grouped by domain.

#### Finding categories (MVP-1)

**Architecture findings:**
| Finding | Detection (graph query) | Severity |
|---|---|---|
| Circular dependency | Strongly Connected Components in `IMPORTS`/`DEPENDS_ON`/`calls` graph | Critical |
| God component (over-coupling) | `CodeSymbol`/`Module` with in-degree or out-degree above threshold | Warning |
| Dead code (orphan symbol) | `CodeSymbol` with no incoming `calls`/`references` and not an entry point (no route/decorator/main) | Info |
| Deeply nested call chain | Path length in `calls` graph exceeding threshold (complexity hotspot) | Warning |

**Data findings:**
| Finding | Detection | Severity |
|---|---|---|
| Broken lineage | `DataAsset` has consumer (`sources_from` in-edge) but upstream chain terminates without reaching a source dataset | Critical |
| Orphaned data asset | `DataAsset` with no consumer and no producer (isolated node) | Warning |
| Unvalidated critical data | `DataAsset` referenced by a report/dashboard but has no `validates` edge | Warning |
| Metric definition conflict | Same-named `Concept`/metric has multiple differing `Formula` definitions | Critical |

**Documentation findings:**
| Finding | Detection | Severity |
|---|---|---|
| Undocumented core component | High-centrality `CodeSymbol` (hub) with no `describes`/`related_to` doc edge | Info |
| Stale doc reference | `DocumentSection` `describes` a symbol that no longer exists in code (name-resolution miss) | Warning |

**Resolution findings:**
| Finding | Detection | Severity |
|---|---|---|
| Unresolved call | `calls` edge marked `resolved: name-based` with low confidence or unmatched target | Info |
| Ambiguous reference | A name resolves to multiple definitions (overload ambiguity) | Info |

### View layout

```
Findings & Health Inspection
├── Summary scorecard: total findings by severity (critical/warning/info)
├── Architecture findings (grouped)
│   ├── [Critical] 2 circular dependencies detected
│   │   └── ModuleA → ModuleB → ModuleA  [drilldown → Module Dependency view]
│   └── [Warning] 3 god components detected
├── Data findings (grouped)
│   ├── [Critical] 1 broken lineage chain
│   │   └── Report "Q3 Revenue" cell B5 → ... → (terminates, no source)  [drilldown → Data Lineage]
│   └── [Warning] 4 unvalidated critical data assets
├── Documentation findings (grouped)
└── Resolution findings (grouped)

[Each finding] → click → drilldown to relevant view + Ask AI about this
```

### Integration with other views

- **Project Overview** health card (ADR-0016) pulls aggregate counts from Findings (critical count shown on landing).
- **Each finding cross-links** to the relevant view: circular dependency → Module Dependency; broken lineage → Data Lineage; unvalidated data → Validation Rules + Reports.
- **Finding → Ask AI**: "Explain this circular dependency and suggest how to break it" — the finding's evidence (the nodes/edges) becomes chat context.

### MVP-1 scope for findings

Start with the **highest-value, lowest-complexity** detectors:
- Circular dependency (SCC — standard graph algorithm)
- Dead code / orphan symbol (in-degree zero check)
- Broken lineage (reachable-set doesn't hit a source)
- Unvalidated critical data (join report-referenced assets with missing validation)
- Metric conflict (name-grouping + definition-diff check)

Defer for MVP-2: God component threshold tuning, deep-chain analysis, stale-doc-reference detection (requires change tracking, partly temporal — ADR-0002 excluded temporal).

## Consequences

- **+** Surfaces actionable risks the user didn't know to ask about — proactive value beyond reactive Q&A.
- **+** All findings are graph-derived — no heavy static-analysis engine needed; leverages sinan's existing graph.
- **+** Every finding is evidence-backed (cites the triggering nodes/edges) — consistent with the evidence-chain principle.
- **+** Cross-links to other views + Ask AI → findings are actionable, not just noise.
- **+** Validates industry best practice (SonarQube/CodeScene/Monte Carlo all have this).
- **−** Threshold-based findings (God component, deep chain) need calibration per project. Mitigation: thresholds are configurable; defaults are conservative; findings are labeled as heuristic.
- **−** "Unvalidated critical data" depends on sinan correctly identifying report-referenced assets — if lineage is incomplete, this finding may be noisy. Mitigation: honest "unknown" labeling (ADR-0016); only flag assets with confirmed report references.
- **−** Adds a 12th view and a finding-detection subsystem. Mitigation: detectors are simple graph queries; the subsystem is a batch job run after ingestion, not a real-time engine.
