# ADR-0016: Default Web UI Views

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

Before a user opens AI chat, the Web UI must present default views that help users and IT quickly understand a project. These views are the first impression and must be auto-generated from the knowledge graph (not hand-drawn). This ADR defines the default view set, based on industry best practices: C4 model (hierarchical architecture), Backstage (developer portal overview), and OpenLineage/Marquez (data lineage DAG).

## Design principles

1. **Every view answers a specific, high-frequency question** — no vanity dashboards.
2. **Every view is auto-generated from the knowledge graph** — no manual diagram authoring.
3. **Every view supports drilldown** — aligns with progressive disclosure (ADR-0003 §4) and the C4 zoom-level philosophy ([c4model.com](https://c4model.com/)).
4. **Every node links to provenance** — click any node to see its source (file+lines / document section / cell address).
5. **Every view has "Ask AI about this"** — select nodes/subgraph → jump to AI chat with context.

## Decision: 8 default views

### Group 1: Project Overview (landing)

#### View 1: Project Overview (项目仪表盘)
- **Question**: What is this project? What sources does it contain? How large? Health?
- **Content**: project metadata, source list (Git repos / Excel / docs, with counts), graph statistics (symbol count, doc sections, sheets), ingestion status per source (indexed / failed / stale), environment label (DEV/QA/UAT/PROD).
- **Reference**: Backstage entity Overview.
- **Graph source**: `Project`/`Source` nodes + ingestion metadata.

#### View 2: Architecture (C4 hierarchical, drilldown)

The core architecture view, adopting the [C4 model](https://c4model.com/introduction) zoom levels:

| Level | Shows | Answers | Graph query |
|---|---|---|---|
| **Context (C1)** | System/project boundary + external dependencies (external APIs, databases, message queues) | "What does this system interact with?" | Top-level `Module` + `related_to` to external dependency nodes |
| **Container (C2)** | Major subsystems/services (web frontend / API / data pipeline / database) | "What major blocks is it composed of?" | `Module` hierarchy aggregation, grouped by directory/namespace |
| **Component (C3)** | Core components within a module (Service classes, Controllers, data models) | "What's the internal structure of each block?" | `CodeSymbol` (Class/Interface) + `implements`/`calls` edges |
| **Code (C4)** | Symbol-level (class methods, call relationships) | "How is this component implemented?" | `CodeSymbol` + `calls`/`references` edges |

Each level drills into the next (click a C2 container → expand to C3). This directly implements requirements #6 (top-down to bottom-up understanding) and #11 (chart drilldown).

### Group 2: Data Perspective

#### View 3: Data Lineage (数据血缘 DAG)
- **Question**: Where does data come from, what transforms it, where does it go?
- **Content**: DAG — source datasets (tables/files) → transformations (SQL/Spark/dbt/Pandas) → downstream datasets → consumers (reports/Excel/API). Per [OpenLineage/Marquez](https://openlineage.io/) default DAG pattern.
- **Graph source**: `computes_from`/`sources_from` edges + SQL/Spark/dbt framework-pack-extracted lineage.
- **Key**: Core visualization for the data provenance requirement (ADR-0003). Click a dataset node → see upstream chain + downstream impact.

#### View 4: Data Assets (数据资产清单)
- **Question**: What data assets does the project involve? What validation rules exist?
- **Content**: Table of all `DataCell`/`Range`/`Table`/`PivotTable`/SQL tables, with columns: type, owning sheet/query, formula/computation summary, has `ValidationRule` (Y/N).
- **Graph source**: Excel + SQL parsed nodes.
- **Use**: Business users quickly find "this cell in this report."

### Group 3: Code Perspective

#### View 5: Module Dependency Graph (模块依赖图)
- **Question**: Which modules depend on which? Circular dependencies? Hub modules?
- **Content**: Directed graph — `Module` nodes, `IMPORTS`/`DEPENDS_ON` edges. Highlight high-in-degree nodes (hubs). Per [dependency-graph best practice](https://understandlegacycode.com/blog/safely-restructure-codebase-with-dependency-graphs/).
- **Graph source**: tree-sitter import extraction + `Module` nodes.

#### View 6: Tech Stack (技术栈清单)
- **Question**: What languages, frameworks, libraries does the project use?
- **Content**: Grouped by language, lists detected frameworks (framework-pack identified), external dependencies (`ExternalPackage` nodes), versions.
- **Reference**: Backstage Tech Radar concept.
- **Graph source**: `ExternalPackage`/`Module` nodes + import analysis.

### Group 4: Knowledge

#### View 7: Knowledge Map (知识地图)
- **Question**: What documentation exists? What concepts do they describe? Which code do those concepts link to?
- **Content**: `Document` node list + LLM-extracted `Concept`/`Feature`/`Component` + their `describes`/`related_to` connections to code symbols. Visualizes sinan's cross-source intelligent association (ADR-0006 `related_to`).
- **Use**: Lets users see "the 'authentication service' mentioned in docs corresponds to which class in code."

#### View 8: Search & Explore (全局搜索)
- **Question**: I want to find X.
- **Content**: Global semantic search (vector) + structural search (filter by symbol name / file / type). Results carry provenance, clickable to drilldown into any view.

## Navigation model

```
Project Overview (default landing page)
    │
    ├── Architecture (C4 drilldown: Context→Container→Component→Code)
    ├── Data Lineage (data lineage DAG)
    ├── Data Assets (data asset inventory)
    ├── Module Dependency (module dependency graph)
    ├── Tech Stack (technology stack)
    ├── Knowledge Map (doc↔code association)
    └── Search & Explore (global search)

[All views] → click node → drilldown → Code/Data Slice detail
[All views] → select → "Ask AI about this" → AI Chat (with selected context)
```

Two universal actions on every view:
- **Drilldown**: click any node → expand next layer (progressive disclosure, ADR-0003 §4).
- **Ask AI about this**: select node/subgraph → jump to AI chat with the selection as context.

## Consequences

- **+** Every view answers a real question; no vanity dashboards.
- **+** C4 model gives a proven drilldown hierarchy for architecture — directly implements requirements #6/#11.
- **+** Data Lineage DAG and Data Assets make the data provenance value (ADR-0003) immediately visible without needing to ask AI.
- **+** Knowledge Map visualizes the cross-source association — sinan's core differentiation.
- **+** All views are graph-generated; no manual maintenance.
- **−** 8 views is a substantial frontend effort. Mitigation: Views 1/5/6/8 are relatively simple (tables/lists/basic graphs); Views 2/3/7 are the complex ones (C4 drilldown, lineage DAG, association map). Prioritize 1/2/3 for MVP-1; 4/5/6/7/8 can follow.
- **−** C4 level detection (what counts as a "container" vs "component") requires heuristics (directory depth, naming conventions, framework-pack hints). May need tuning per project. Mitigation: heuristics are configurable; LLM can assist classification.
