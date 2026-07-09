# ADR-0016: Default Web UI Views

- **Status:** Accepted (revised — added Business Logic group + cross-navigation + health metrics)
- **Date:** 2026-07-10 (revised 2026-07-10)

## Context

Before a user opens AI chat, the Web UI must present default views that help users and IT quickly understand a project. These views are the first impression and must be auto-generated from the knowledge graph (not hand-drawn). Based on industry best practices: C4 model (hierarchical architecture), Backstage (developer portal overview), OpenLineage/Marquez (data lineage DAG), Monte Carlo / DataKitchen (data quality dashboards), and dbt Catalog / Semantic Layer (metrics governance).

## Design principles

1. **Every view answers a specific, high-frequency question** — no vanity dashboards.
2. **Every view is auto-generated from the knowledge graph** — no manual diagram authoring.
3. **Every view supports drilldown** — aligns with progressive disclosure (ADR-0003 §4) and the C4 zoom-level philosophy ([c4model.com](https://c4model.com/)).
4. **Every node links to provenance** — click any node to see its source (file+lines / document section / cell address).
5. **Every view has "Ask AI about this"** — select nodes/subgraph → jump to AI chat with context.
6. **Every view has cross-navigation** — nodes link to related views bidirectionally (e.g. a dataset in Lineage → "used by which reports?" → Reports view).
7. **Honest unknowns** — when source material is insufficient, label "unknown" not "none" (per ADR-0003 bounded lineage principle).

## Decision: 11 default views (5 groups)

### Group 1: Project Overview (landing)

#### View 1: Project Overview (项目仪表盘)
- **Question**: What is this project? What sources does it contain? How large? Health?
- **Content**: project metadata, source list (Git repos / Excel / docs, with counts), graph statistics (symbol count, doc sections, sheets), ingestion status per source (indexed / failed / stale), environment label (DEV/QA/UAT/PROD).
- **Data governance health card** (per [Monte Carlo 6 metrics](https://montecarlo.ai/blog-building-data-quality-dashboard) / [DataKitchen](https://datakitchen.io/blog/the-six-types-of-data-quality-dashboards/)):
  - Validation coverage: % of data assets with validation rules (vs unknown)
  - Lineage completeness: % of data assets with full upstream lineage
  - Documentation coverage: % of code symbols with doc `describes` links
  - These give IT an instant health snapshot on first open.
- **Reference**: Backstage entity Overview + data quality scorecard.
- **Graph source**: `Project`/`Source` nodes + ingestion metadata + aggregate counts from validation/lineage/doc edges.

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

### Group 5: Business Logic (业务逻辑层) — added per user feedback

These views cover the business-logic dimension that the original 8 views missed: reports, validation rules, and business metrics. They are neither pure architecture (code structure) nor pure data lineage (data flow) — they answer "what does this project do **business-wise**?"

#### View 9: Reports & Dashboards (报表/仪表盘目录 + 血缘)
- **Question**: What reports/dashboards exist? Where does each report field/cell get its data?
- **Content**: Report catalog (Excel reports, PivotTables, BI dashboards, report-serving API endpoints). Expand a report → field/cell list → per-field data lineage (trace back to SQL/dataset). This is the **consumer side** of Data Lineage — Lineage shows "how data flows"; this shows "how reports consume that data."
- **Graph source**: `PivotTable`/`Chart`/`ApiEndpoint` (report-type)/Excel report cells + `sources_from`/`computes_from` edges.
- **Reference**: [dbt Catalog](https://www.getdbt.com/product/dbt-catalog) resource inventory + lineage.

#### View 10: Validation Rules (校验规则目录 + 覆盖图)
- **Question**: What validation rules exist? Which fields/cells do they protect? Which data has no validation?
- **Content**: Validation rule catalog — rule name, type (range/enum/format/not-null/custom formula), applied-to (field/cell/API param). **Coverage heatmap**: which data assets have validation (green), which don't (red), which are **unknown** (grey — source material insufficient, per honest-unknowns principle).
- **Graph source**: `ValidationRule`/`DataValidation` nodes + `validates` edges.
- **Reference**: [Monte Carlo data quality dashboard](https://montecarlo.ai/blog-building-data-quality-dashboard) rule coverage + [Databricks expectations monitoring](https://medium.com/@hitesh09parab/part-2-data-quality-dashboard-a-visual-approach-to-monitoring-expectations-in-databricks-4c490fc25891).
- **Honest labeling**: "unknown" (source insufficient) vs "confirmed no validation" (explicitly absent in a complete source) vs "has validation" — never conflate unknown with none.

#### View 11: Business Metrics (业务指标/语义层)
- **Question**: What business metrics are defined? What's the formula? Are they consistent across reports?
- **Content**: Metric catalog — metric name, definition formula, computation source (which SQL/Excel formula/dbt metric), referenced by which reports. **Consistency conflict detection**: same-named metric defined differently in different places → highlighted.
- **Graph source**: LLM-extracted metric definitions from docs/SQL/Excel + `Concept`/`Formula` nodes + dbt semantic layer (if present in sources).
- **Reference**: [dbt Semantic Layer](https://www.getdbt.com/blog/build-centralize-and-deliver-consistent-metrics-with-the-dbt-semantic-layer) metric centralization concept.

## Navigation model (with cross-navigation)

```
Project Overview (default landing page)
    │
    ├── Architecture (C4 drilldown: Context→Container→Component→Code)
    ├── Data Lineage (data lineage DAG)
    ├── Data Assets (data asset inventory)
    ├── Module Dependency (module dependency graph)
    ├── Tech Stack (technology stack)
    ├── Knowledge Map (doc↔code association)
    ├── Reports & Dashboards (report catalog + per-field lineage)
    ├── Validation Rules (rule catalog + coverage heatmap)
    ├── Business Metrics (metric definitions + consistency check)
    └── Search & Explore (global search)
```

Three universal actions on every view:
- **Drilldown**: click any node → expand next layer (progressive disclosure, ADR-0003 §4).
- **Ask AI about this**: select node/subgraph → jump to AI chat with the selection as context.
- **Cross-navigate**: nodes offer contextual jumps to related views (bidirectional). Examples:
  - Dataset in Data Lineage → "used by which reports?" → Reports & Dashboards view
  - Report field in Reports → "what's the data lineage?" → Data Lineage view
  - Validation rule → "which fields it protects appear in which reports?" → Reports view
  - Metric → "which reports use this metric?" → Reports view; "what's the lineage?" → Data Lineage

## Consequences

- **+** Every view answers a real question; no vanity dashboards.
- **+** C4 model gives a proven drilldown hierarchy for architecture — directly implements requirements #6/#11.
- **+** Data Lineage DAG and Data Assets make the data provenance value (ADR-0003) immediately visible without needing to ask AI.
- **+** Knowledge Map visualizes the cross-source association — sinan's core differentiation.
- **+** Business Logic group (Reports/Validation/Metrics) covers the business dimension — what IT and business users care about most directly.
- **+** Validation coverage heatmap and honest "unknown" labeling prevent false confidence.
- **+** Cross-navigation connects views into a coherent exploration experience, not isolated pages.
- **+** Health metrics on Project Overview give instant governance snapshot.
- **+** All views are graph-generated; no manual maintenance.
- **−** 11 views is a large frontend effort. Mitigation / prioritization for MVP-1:
  - **Tier 1 (MVP-1 core)**: Project Overview, Architecture (C4), Data Lineage, Reports & Dashboards, Validation Rules — these prove the core value (architecture + data provenance + business logic).
  - **Tier 2 (MVP-1 follow)**: Search & Explore, Data Assets, Knowledge Map.
  - **Tier 3 (MVP-2)**: Module Dependency, Tech Stack, Business Metrics.
- **−** C4 level detection (what counts as a "container" vs "component") requires heuristics (directory depth, naming conventions, framework-pack hints). May need tuning per project. Mitigation: heuristics are configurable; LLM can assist classification.
- **−** Business Metrics consistency detection and metric extraction depend on LLM quality and source richness. May be incomplete for poorly-documented projects. Mitigation: honest "unknown" labeling; the view shows what's extractable, gaps are visible.
