# ADR-0007: Language and Framework Pack Scope (v1)

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

ADR-0006 established that tree-sitter grammars provide language syntax parsing, while framework packs provide library/framework-specific pattern detection (DI, routes, UI calls, data lineage). This ADR defines the v1 scope of both. Grammar availability is verified against the [official tree-sitter parser list](https://github.com/tree-sitter/tree-sitter/wiki/List-of-parsers).

## Key conceptual distinction

- **Language grammar** (tree-sitter `.grammar` + `.scm` query files) = parses syntax of a language. Provides: symbols, calls, imports, decorators, code slices.
- **Framework pack** = framework-specific patterns layered on a language grammar. Provides: `binds` (DI), `invokes` (UI→API), route registration, data lineage, ORM model→table mapping, message topic dependencies.
- **Spark is NOT a language** — it is a framework. Spark projects are written in Scala/Python/Java/R + SQL, all of which have grammars. The Spark framework pack detects DataFrame API calls for lineage.

## Decision

### A. Language grammars (v1)

#### A1. General-purpose programming languages
TypeScript/TSX, JavaScript, Java, Python, Go, C#, Scala, Kotlin, Swift, Rust, Ruby, PHP, C, C++, Lua, Dart, Groovy, R, Bash, PowerShell, Perl, Elixir, Erlang, Haskell, Julia, OCaml, Objective-C, Fortran, F#, Clojure. (Zig: low priority, grammar exists.)

#### A2. Data/query languages (critical for data lineage)
- **SQL (generic)** — DerekStride/tree-sitter-sql — **critical**: parses SELECT/JOIN/FROM → table dependency edges.
- **SQL BigQuery**, **SQLite** — dialect variants.
- **GraphQL** — schema → resolver mapping + client queries.
- **Protobuf** — gRPC service definitions → code mapping.
- **PRQL** — pipeline query language.
- **Jinja2** — dbt templated SQL parsing.
- **HCL** — Terraform infrastructure.
- **PromQL** — monitoring queries.

#### A3. Configuration/infrastructure languages
YAML, JSON, TOML, XML, Dockerfile, INI, Properties.

#### A4. Markup/documentation languages
Markdown (+inline), HTML, CSS/SCSS, reStructuredText, AsciiDoc.

#### A5. Frontend template/UI languages (for UI→API call chain capture)
Vue, Svelte, Angular, Embedded Template (ERB/EJS), HTMLDjango, Twig, Pug, HEEx, Liquid, Razor.

### B. Framework packs (v1)

#### B1. DI / injection (per framework — ADR-0006 §4)
Spring (Java: XML + annotations), Guice (Java), .NET DI (C#), NestJS (TS), Django (Py).

#### B2. Web frameworks / route registration
Express/Fastify (TS/JS), NestJS (TS), Spring MVC (Java), FastAPI (Py), Django (Py), ASP.NET Core (C#), Gin (Go), Rails (Ruby), Laravel (PHP), Phoenix (Elixir), Flutter (Dart).

#### B3. Frontend UI→API call patterns
React (hooks: useEffect/useQuery + fetch/axios), Vue (axios/fetch), Angular (HttpClient), Svelte (fetch), native fetch/axios (generic).

#### B4. RPC / API protocols
- **gRPC** — proto definitions → service/method nodes; client stub call sites.
- **GraphQL** — schema → resolver mapping; client query extraction.
- **WebSocket** — **v1 requirement (not low priority)**: ws event registration (`ws.on('event', handler)`) and emission (`ws.emit('event', ...)`) → `publishes`/`subscribes` edges for async call chains.
- **tRPC** — low priority.

#### B5. Data processing / ETL (data lineage — critical)
- **Apache Spark** — DataFrame API lineage: `read.parquet/csv/jdbc` → `join/select/filter` → `write.parquet/csv/jdbc`. Extracts source→transformation→sink edges.
- **dbt** — model dependency graph via `ref('model_a')` → model-to-model lineage.
- **Airflow** — DAG task dependencies: `task_a >> task_b` → task dependency edges.
- **Pandas** — **v1 requirement (not low priority)**: DataFrame operation chain lineage: `read_csv/read_sql/read_parquet` → `merge/join/groupby/agg` → `to_csv/to_sql/to_parquet`. Extracts simplified source→transform→sink edges.

#### B6. ORM (SQL generation point detection)
SQLAlchemy (Py), Hibernate/JPA (Java), Prisma (TS), GORM (Go), Entity Framework (C#). Provides Model→Table mapping + query construction site detection. (ActiveRecord: low priority.)

#### B7. Messaging / event (async call chains)
- **Kafka** — producer/consumer topic dependencies.
- **RabbitMQ** — low priority.
- **Redis Pub/Sub** — low priority.

### C. SQL injection ruleset (critical engineering dependency)

SQL rarely exists as standalone files. It is embedded in:
- Python strings: `pd.read_sql("SELECT ...", conn)`, SQLAlchemy `text("...")`
- Java annotations: `@Query("SELECT ... FROM User")`, `@NamedQuery`
- Jinja templates: dbt `{{ config() }} SELECT ...`
- String concatenation (harder; LLM-assisted reconstruction)

tree-sitter injection mechanism: host language grammar identifies string literals → injects SQL grammar to parse the embedded SQL → extract table references. **An injection ruleset per embedding scenario is a v1 requirement for end-to-end data lineage.** Without it, SQL inside code is opaque text, and the report→API→SQL→table chain breaks at the SQL step.

## Consequences

- **+** Broad language coverage (30+ languages) verified against the official parser list — no guessing.
- **+** SQL + Spark + dbt + Pandas form a complete data-lineage detection stack for the report→API→SQL→table chain.
- **+** WebSocket + Kafka capture async call chains, not just synchronous request/response.
- **+** ORM packs detect SQL generation points, linking code models to database tables.
- **−** ~30 language grammars × query files + ~25 framework packs = the largest engineering surface in v1 after Excel.
- **−** SQL injection rulesets are fiddly per-language and per-embedding-pattern; incomplete rulesets mean some embedded SQL stays opaque.
- **−** Pandas lineage is approximate — DataFrame operations are dynamic (column names computed at runtime); lineage is best-effort from static API call patterns, not full dataflow analysis. Must be marked as approximate.
- **Mitigation:** The framework pack architecture (ADR-0006 §4) keeps this extensible — packs are additive, and missing packs degrade gracefully to symbol-level only.
