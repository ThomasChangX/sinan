# ADR-0008: Storage Architecture

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

sinan must store three categories of data: (1) the property graph (nodes + edges + properties), (2) vector embeddings (for semantic retrieval / RAG), and (3) metadata (projects, sources, ingestion state, user data). A hard constraint from ADR-0001 is self-hosting simplicity — minimize the number of independent services to operate.

The RAG query pattern is: vector search for semantically relevant chunks → graph traversal for relationships and evidence chains. This favors storing vectors and graph in the same engine to avoid cross-database joins.

## Decision

### Single multi-model engine: ArcadeDB

Use **ArcadeDB** as the sole storage engine for all three data categories:

- **Graph** — native property graph storage (index-free adjacency), Cypher (97.8% TCK compliant).
- **Vectors** — built-in vector search, co-located with graph nodes. No separate vector DB.
- **Metadata** — document model in the same engine (projects, sources, ingestion logs).

### Why ArcadeDB (over alternatives)

| Requirement | ArcadeDB | Neo4j Community | Postgres+AGE+pgvector | Memgraph | FalkorDB |
|---|---|---|---|---|---|
| Single engine (graph+vector+meta) | ✅ | ✅ (v5+) | ✅ | ❌ (no vectors) | ✅ |
| Self-host simplicity (1 service) | ✅ | ✅ | ✅ | ❌ (2-3 services) | ❌ (2 services) |
| License | Apache 2.0 | GPLv3 (limited) | Apache 2.0 | BSL 1.1 (not OSS) | Source-available |
| Multi-database (env isolation) | ✅ composite DBs | ❌ (Community) | ✅ (schemas) | ❌ | ❌ |
| Built-in MCP server | ✅ | ❌ | ❌ | ❌ | ❌ |
| Graph traversal performance | Native, strong | Native, strong | Table-join bounded | In-memory, fast | GraphBLAS |
| Data caps | None | None | None | RAM-bound | RAM-bound |

Key reasons:
1. **Self-host simplicity**: one engine, one process, one backup. Aligns with ADR-0001.
2. **Vectors in-graph**: the RAG query pattern (vector → graph traversal) executes without cross-database latency.
3. **Apache 2.0**: no BSL/source-available restrictions; aligns with "generic solution freely deployable".
4. **Multi-database**: supports DEV/QA/UAT/PROD logical isolation within one instance (see §Environment Isolation).
5. **Built-in MCP**: aligns with the MCP-first access model (ADR-0001).

### Why not Postgres+AGE+pgvector (the strongest alternative)

This would be the pick for a Postgres-centric team. Two technical concerns:
1. AGE implements an **openCypher subset**, not full Cypher — complex graph queries may be unsupported.
2. AGE stores graph data as `agtype` (JSONB-based); multi-hop traversals compile to table joins. The TACO paper (arXiv:2302.05482) showed real spreadsheet formula graphs can reach 200k-edge paths — this depth risks poor performance under the table-join model.

ArcadeDB's native graph engine does not have this limitation.

### Why not Neo4j Community

- Community Edition is GPLv3, single-instance, no RBAC, no clustering, no multi-database. The DEV/QA/UAT/PROD isolation requirement (need #9) likely needs multi-database or RBAC, which Community lacks.
- Enterprise is commercial; introduces licensing cost and complexity for a "generic solution".

### Environment isolation (DEV/QA/UAT/PROD)

Use **ArcadeDB composite databases** (logical isolation, same instance):
- Each environment gets its own database within the ArcadeDB instance: `sinan_dev`, `sinan_qa`, `sinan_uat`, `sinan_prod`.
- Projects live within an environment's database. Project-level isolation (ADR-0001) is enforced by scoping all graph queries to a project ID.
- Migration between environments = export from one database + import into another (ArcadeDB supports database export/import). This satisfies the "data isolation and migration" requirement (need #9).

If physical isolation is later required (e.g. PROD on separate hardware), ArcadeDB instances can be deployed per-environment — the architecture supports this without code changes, only deployment topology changes.

## Consequences

- **+** One storage engine to install, operate, back up, and monitor. Minimal ops surface.
- **+** Vectors co-located with graph — RAG queries are single-engine, no cross-DB latency.
- **+** Apache 2.0 with no data caps — no licensing surprises.
- **+** Multi-database for environment isolation; migration via export/import.
- **+** Built-in MCP server aligns with the agent access model.
- **−** Smaller ecosystem than Neo4j (no APOC utility library, no GDS graph algorithms). Mitigation: sinan needs graph traversal, not graph analytics algorithms (PageRank, community detection, etc.), so GDS is not required. APOC utilities can be replaced with Cypher.
- **−** ArcadeDB is less battle-tested than Neo4j at very large scale. Mitigation: sinan's graph size per project is bounded by the source codebase size (typical: 10k-100k nodes), well within ArcadeDB's comfort zone.
- **−** Team must learn ArcadeDB operations (vs. more familiar Postgres). Acceptable trade-off given the multi-model and licensing benefits.
