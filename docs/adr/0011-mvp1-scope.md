# ADR-0011: MVP-1 Scope

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

MVP-1 is positioned as a **generic, extensible framework with Web UI**, not a feature-complete product. The framework must be built so subsequent MVPs add language packs, document types, and framework support without architectural changes. However, MVP-1 must also prove sinan's core differentiation value: multi-source fusion, Excel data provenance, and LLM cross-source association.

## Decision

### MVP-1 guiding principle
**Build the extensible framework first; ship enough real capability to prove the core value.** Every interface (language pack, framework pack, source ingestor, storage repository) is fully defined and has at least one reference implementation. Subsequent MVPs add implementations, not architecture.

### MVP-1 includes

#### Framework & infrastructure (the "generic, extensible" core)
- Language pack interface (tree-sitter grammar + `.scm` query files + auto-detection)
- Framework pack interface (DI/route/lineage detection patterns)
- Source ingestor interface (per source type)
- Storage repository interface (ArcadeDB implementation, swappable)
- Query/RAG layer (graph-first + vector-supplement hybrid)
- MCP endpoint
- Web UI (project management, source management, graph browser with drilldown, AI chat)
- Incremental build (source-level + file-level, manual trigger)
- Environment isolation (ArcadeDB multi-database: DEV/QA/UAT/PROD)

#### Language packs (reference implementations)
- **TypeScript/TSX** — frontend + Node backend
- **Python** — backend + AI projects
- **Java** — enterprise backend (Spring ecosystem)
- **C#** — .NET backend
- **SQL (generic)** — data lineage (critical for provenance chain)

#### Framework packs (data lineage — core value)
- **dbt** — model dependency graph via `ref()`
- **Spark** — DataFrame API lineage (`read`→`transform`→`write`)

#### Data sources
- **GitHub repository URL** (Git source, default/main/master branch + explicit override)
- **Excel (.xlsx)** — FULL OOXML analysis (formulas, Range as first-class node, PivotTable + PivotCache lineage, PivotField, Table, Chart, DefinedName, SharedFormula, DataValidation) — top priority (重中之重)
- **Word (.docx)** — section-aware parsing
- **Email (.eml/.msg)** — headers + body + reply chain
- **Markdown (.md)** — header-based section chunking
- **Plain text (.txt)** — fixed-size chunking

#### Core capabilities
- LLM cross-source `related_to` association (code↔doc↔data linking)
- Bounded data provenance (report→API→SQL→table from user-provided sources)
- Evidence chain (every answer traces to original source + location)
- Progressive disclosure (graph → document → code/data slice)
- AI chat via LLM SDK
- Vectors for semantic fuzzy matching (supplement to graph traversal)

### MVP-1 explicitly excludes (subsequent MVPs)
- Remaining 25+ language packs (Go, Kotlin, Swift, Rust, Ruby, PHP, Scala, etc.)
- Stash/Bitbucket Server source (MVP-2)
- DI/injection framework packs (Spring, NestJS, .NET DI) (MVP-2)
- Route registration + UI→API call chain packs (Express, FastAPI, ASP.NET, etc.) (MVP-2)
- ORM packs (SQLAlchemy, Hibernate, Prisma, GORM, EF) (MVP-2)
- gRPC, GraphQL, WebSocket, Kafka framework packs (MVP-2)
- Pandas, Airflow framework packs (MVP-2)
- SQL dialect variants (BigQuery, SQLite) (MVP-2)
- Jira/Rally ALM integration (MVP-3+)
- Temporal/historical tracking (ADR-0002 — out of v1)

### Engineering scale acknowledgment
MVP-1 is large: 5 language packs + 2 framework packs + 6 source types (including full Excel OOXML) + framework + Web UI + MCP + RAG layer. This reflects the user's consistent priority that Excel analysis, data lineage, and multi-source fusion are core value that must be proven in MVP-1. The framework-first principle ensures that even if some packs ship incomplete in MVP-1, the architecture supports completing them in MVP-2 without rework.

## Consequences

- **+** Framework-first means every subsequent MVP is additive — no architectural rework.
- **+** Core value (multi-source fusion + Excel provenance + data lineage + LLM association) is proven in MVP-1.
- **+** SQL + dbt + Spark in MVP-1 means the report→API→SQL→table provenance chain is demonstrable end-to-end.
- **−** Large engineering surface for an MVP. Mitigation: the framework interfaces are defined first and locked; packs are implemented in parallel against stable interfaces.
- **−** Full Excel OOXML parsing is a significant standalone effort. Mitigation: it is explicitly top priority and resourced accordingly.
- **−** Without DI/route/UI-call packs in MVP-1, the injection detection and UI→API chain capabilities are not yet demonstrable. This is accepted — they are MVP-2.
