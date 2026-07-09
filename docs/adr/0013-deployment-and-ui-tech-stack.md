# ADR-0013: Deployment and UI Tech Stack

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

User requirements: (1) support both Docker and direct Linux CLI launch; (2) Web UI in Angular. Remaining stack choices need industry-best-practice recommendations.

## Decision

### 1. Deployment: dual-mode (Docker Compose + direct CLI)

**Mode A: Docker Compose (primary)**
- A `docker-compose.yml` bundles all sinan components: backend API, ArcadeDB, Web UI (served as static files), background ingestion workers.
- One command to start: `docker compose up`.
- Industry consensus ([ServerFault](https://serverfault.com/questions/1152947/install-services-with-a-script-or-use-docker-compose), [Dev.to self-hosting guide](https://dev.to/jhot/is-this-the-ultimate-self-hosting-setup-i-think-so-15on)) favors Compose for multi-service stacks: declarative, reproducible, handles volumes/networking/dependencies.
- Integrates with systemd for production ([Glukhov.org guide](https://www.glukhov.org/developer-tools/containers/docker-compose-as-systemd-service/)).

**Mode B: Direct Linux CLI**
- A single entrypoint script/binary (`sinan serve`) starts the backend + serves the UI + connects to a separately-running ArcadeDB.
- For environments without Docker. Requires ArcadeDB installed locally (or accessible remotely).
- systemd unit file provided for running as a service.
- Same config file (`sinan.yaml`) drives both modes.

Both modes share identical config and code paths; only the process orchestration differs.

### 2. Backend: Python (FastAPI)

- **Python** because: tree-sitter Python bindings are mature, ArcadeDB has a Python client, LiteLLM is Python-native, and the entire ML/LLM ecosystem is Python-first.
- **FastAPI** for the REST API: async, type-safe (Pydantic), auto-generated OpenAPI docs, industry standard for Python web services.
- The backend serves both the REST API (for Web UI) and the MCP endpoint (for AI dev IDEs). They share the same query layer.

### 3. Frontend: Angular (user-specified)

- Angular (latest) for the Web UI.
- Graph visualization: **Cytoscape.js** with the **cytoscape-dagre** layout extension.
  - Rationale: [2026 comparison](https://www.pkgpulse.com/guides/cytoscape-vs-vis-network-vs-sigma-graph-visualization-2026) shows Cytoscape.js is the richest all-in-one graph toolkit with excellent large-graph performance. dagre provides directed-graph layout (ideal for call graphs, dependency graphs, lineage chains). vis-network is faster to start but sluggish at scale; Cytoscape handles sinan's potentially large graphs (10k-100k nodes) better.
  - Angular integration via a thin wrapper component around Cytoscape core (no heavyweight third-party wrapper needed).
- Progressive disclosure UI: graph view → document section view → code/data slice view, each layer drilldown-able.

### 4. Background ingestion: task queue (Celery + Redis)

- Ingestion (tree-sitter parsing, Excel OOXML parsing, LLM association) is long-running and must be async — the Web UI cannot block on it.
- **Celery** (Python task queue) + **Redis** (broker) for background ingestion jobs.
- Rationale: industry standard for Python async task processing; supports progress tracking (user sees ingestion status in Web UI), retries, and job priority.
- ArcadeDB remains the sole data store (graph + vectors + metadata); Redis is only a transient task broker, not a data store.

## Component inventory (MVP-1)

| Component | Technology | Docker service | Purpose |
|---|---|---|---|
| Backend API + MCP | Python + FastAPI | `sinan-api` | REST API, MCP endpoint, query layer |
| Web UI | Angular + Cytoscape.js | `sinan-ui` (served by API) | Project/source management, graph browser, chat |
| Ingestion workers | Python + Celery | `sinan-worker` | Background parsing, LLM association |
| Task broker | Redis | `sinan-redis` | Celery broker (transient) |
| Storage | ArcadeDB | `sinan-db` | Graph + vectors + metadata |
| LLM gateway | LiteLLM (SDK, in-process) | (embedded in api/worker) | Universal model access |

## Consequences

- **+** Docker Compose = one-command deploy; direct CLI = no-Docker environments. Both covered.
- **+** Python backend aligns with tree-sitter/ArcadeDB/LiteLLM/ML ecosystem.
- **+** Cytoscape.js + dagre handles large directed graphs with drilldown (matches progressive-disclosure requirement).
- **+** Celery async ingestion keeps Web UI responsive; progress visible to users.
- **−** 4 Docker services (api, worker, redis, db) — more than a single binary, but each is independently scalable and debuggable. Direct CLI mode collapses to 2 (sinan + ArcadeDB).
- **−** Redis as an additional component. Justified: Celery needs a broker; Redis is lightweight and standard. Not a data store — only transient task state.
