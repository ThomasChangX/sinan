# ADR-0001: Deployment and Access Model

- **Status:** Proposed
- **Date:** 2026-07-09

## Context

sinan must serve two user populations with different interaction modes:
1. Individual and enterprise developers using AI dev IDEs (ZCode, Codex, Claude, Copilot, Copilot-CLI, Amp), who need pre-digested, evidence-backed project context via an API/MCP endpoint to save tokens and improve agent accuracy.
2. Any user (developer, business owner) who wants to build cross-system knowledge graphs, via a hosted Web UI to create projects and add data sources.

The solution is inspired by GitHub's `code-graph` and must support self-hosting, multi-project isolation, and DEV/QA/UAT/PROD environments.

## Decision

Deploy as a **self-hosted multi-project platform on Linux** with two access surfaces:

1. **Web UI** — human-facing, for project creation, data source management, graph exploration, and chat.
2. **API / MCP endpoint** — agent-facing, for AI dev IDEs to query the knowledge base and receive evidence-backed context.

Both surfaces operate on the **same knowledge base** within a project. Projects are the primary isolation boundary (one project's data is not visible to another).

**Not** a multi-tenant SaaS billing product for v1. Multi-org isolation is deferred. Single self-hosted instance, multiple projects.

## Consequences

- **+** One codebase serves both humans and agents; no duplicated ingestion paths.
- **+** Self-hosting keeps enterprise data on-prem (important given Stash/Jira/Rally inputs).
- **+** MCP-first design aligns with the AI dev tool ecosystem the user targets.
- **−** Must design auth/access control that works for both interactive Web sessions and programmatic MCP clients.
- **−** Environment isolation (DEV/QA/UAT/PROD) adds operational complexity — see future ADR.
- **Open:** Whether "environment" isolation is per-deployment-instance or per-project-within-instance.
