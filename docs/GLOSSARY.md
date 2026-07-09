# sinan — Glossary

Working definitions for terms used in this project. Updated as the design solidifies.

## Core Concepts

- **Analysis Project (项目)** — The primary isolation boundary. A logical container holding a set of data sources and the knowledge base built from them. Projects are fully isolated from one another (no cross-project links unless explicitly configured). A project corresponds to one "thing being understood" — e.g. a product, a platform, or a collection of related repos.

- **Data Source (数据源)** — A raw input that feeds into an analysis project's knowledge base. Types include: Git repository (GitHub/Stash URL), ALM/ticket system (Jira/Jira Cloud/Rally), and static files (Excel, Docx, Email, Markdown, .txt).

- **Knowledge Base (知识库)** — The incrementally-built, cross-linked graph of information extracted from all data sources within a project. Includes code structure, documentation, tickets, and the relationships between them.

- **Evidence Chain (证据链)** — A traceable path from any AI-generated answer or analysis node back to the exact original source (file + line range, document section, ticket). Every claim the system makes must be backed by evidence.

## Framework Pack (语言/框架包)

- **Language pack** — A tree-sitter grammar + `.scm` query files for one language. Provides: symbol extraction, decorator extraction, call-site extraction, import extraction, code-slice rendering.
- **Framework pack** — Extends a language pack with framework-specific patterns: DI/injection detection (Spring XML/annotations, NestJS providers, .NET DI), route registration (Express/Spring/FastAPI/ASP.NET), UI call patterns (fetch/axios/HttpClient). A framework pack is what creates `binds` and `invokes` edges. Without a matching pack, sinan falls back to symbol-level only — it does not guess.

## v1 Priorities

- **Highest priority (重中之重):** (1) full tree-sitter leverage across all 7 layers; (2) full Excel OOXML analysis with Range as first-class node and complete pivot lineage.
- **Hard constraints:** injection detection is framework-aware (per framework pack); UI→API→function call chains must be captured end-to-end.
- **Honest boundary:** v1 `calls` edges are name-level + name-resolution, NOT semantic-level (no LSP). Overloads/polymorphism may be unresolved; always surfaced honestly.

## Storage

- **ArcadeDB** — The sole storage engine for sinan v1. A multi-model database (Apache 2.0) providing native property graph, vector search, and document storage in a single engine. Chosen for self-hosting simplicity (one service), vectors co-located with graph (RAG-friendly), Apache 2.0 licensing, and multi-database support for environment isolation.
- **Environment isolation** — DEV/QA/UAT/PROD are isolated as separate ArcadeDB databases (`sinan_dev`, `sinan_qa`, `sinan_uat`, `sinan_prod`) within one instance. Project-level isolation is enforced by scoping queries to a project ID within an environment database. Migration = export/import between databases.

## LLM Integration

- **LiteLLM** — Universal LLM abstraction layer (MIT-licensed, 100+ providers) used by sinan to call any model (OpenAI, Anthropic, Google, local Ollama, etc.) through one OpenAI-compatible interface. Eliminates vendor lock-in.
- **Task roles** — sinan assigns LLMs to fixed roles, each independently configurable: `cross_source_association` (ingest), `document_entity_extraction` (ingest), `orchestrator` (query reasoning), `cypher_generator` (NL→Cypher), `embedding` (vectorization).
- **Two-model split** — Query path uses a separate orchestrator model (strong reasoning) and cypher_generator model (can be cheaper). Enables cost optimization. Adopted from Code-Graph-RAG.
- **Structured query template fallback** — If cypher generation fails, the system falls back to predefined Cypher patterns (impact analysis, dependency tracing, etc.) instead of freeform NL→Cypher. Ensures graceful degradation with weak models.

## Pipeline & Query

- **Ingestion pipeline** — 8-stage background job: Fetch → Parse → Extract → Name-resolve → SQL-inject → Embed → LLM-associate → Persist. Stages 1-6 deterministic; Stage 7 LLM-driven. Each stage independently re-runnable.
- **Hybrid retrieval** — Query strategy: graph-first (structural questions answered by Cypher traversal) + vector-supplement (semantic questions answered by embedding search + graph expansion). Vectors supplement, never replace, structural search (Sourcegraph lesson).
- **Progressive disclosure answer** — Three-layer answer structure: graph (relationships) → document sections → code/data slices. Each layer cites provenance. Same structure returned by Web UI and MCP.

## Quality

- **Architecture tests** — CI-enforced rules asserting layer dependencies, interface compliance, no circular imports. Packs that violate architecture cannot merge. Inspired by ArchUnit.
- **Pack conformance suite** — Fixed test fixtures that every language/framework/source pack must pass, ensuring structural consistency (a Java function and a Python function produce equivalent graph nodes).

## Access

- **Web UI** — Hosted web interface for humans to create analysis projects, add data sources, explore the knowledge graph, and chat.

- **MCP / API endpoint** — The interface AI dev IDEs (ZCode, Codex, Claude, Copilot, Copilot-CLI, Amp, etc.) call to query the knowledge base and receive evidence-backed context. Saves tokens for the calling agent by pre-digesting the project.

## Scope

- **v1 scope — current-state only** — The v1 knowledge base represents the *current* state of all sources. No time-travel, no historical diffing, no "what changed since X" reconstruction. Each node/edge still carries provenance (which source + location it came from), but there is no version history of the graph itself. Historical/temporal queries are explicitly out of v1.

- **No people attribution** — The graph contains no Person nodes, no author/reviewer/expertise graphs. Author names may exist as raw provenance metadata but are not first-class queryable structure. "Who knows this / who built this" is out of scope.

- **Bounded data lineage** — sinan links lineage *observable in user-provided sources* (docs that describe report→API→SQL, Excel formulas, validation rules in code). sinan does **not** independently reconstruct lineage via static analysis of arbitrary datasets/UI. The chain is only as complete as the sources make it; gaps are surfaced honestly.

- **Progressive disclosure** — All answers are presented in layers, simple → detailed: (1) graph/chart of relationships, (2) relevant document sections, (3) code/data slices (exact lines/cells/formulas). Users drill down through layers.

## Lineage answer shape

When answering lineage questions ("why is this cell this value?"), the answer must include:
- The **formula / computation** behind the value.
- The **allowed values** (if any constraint is defined).
- Whether **validation** exists, and what it is.
- The **complete logical chain** from the queried artifact back to its root inputs, each step with evidence.

## Environments

- **Environment (DEV/QA/UAT/PROD)** — A deployment tier. Environment-level data isolation and migration paths need to be defined (open question: isolation per-project, per-environment, or both?).

## Users

- **AI dev tool user** — A developer using AI dev IDEs; consumes the knowledge base via MCP/API to get project context with token efficiency.
- **Knowledge builder** — Any user (developer, business owner) creating analysis projects and adding sources via the Web UI.
