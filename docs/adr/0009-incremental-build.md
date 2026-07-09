# ADR-0009: Incremental Build

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

Requirement #1 mandates incremental knowledge base construction. When a user adds or updates a source, sinan must not rebuild the entire project graph — it must process only what changed.

## Decision

### 1. Incremental granularity: source-level + file-level

**Source-level (all source types):**
- Every node/edge carries a `source_id` property.
- Adding a new source: ingest the source, create its nodes/edges, run LLM cross-source `related_to` inference for the new nodes.
- Updating an existing source: delete all nodes/edges with that `source_id`, re-ingest, rebuild.
- This is the baseline for all source types (Git, Excel, Word, Email, Markdown, Txt).

**File-level (Git sources only):**
- When a Git source is refreshed (manual trigger), sinan runs `git pull` and computes a file-level diff (changed/added/deleted files).
- Only changed files are re-parsed by tree-sitter; unchanged files' nodes/edges are retained.
- For each changed file: delete its old nodes/edges (scoped by `source_id` + `file_path`), re-parse, rebuild.
- Cross-file edges (calls/references that point into a changed file) are re-resolved via name resolution after the file is rebuilt.

**Symbol-level incremental: explicitly out of v1.**
- tree-sitter supports incremental AST parsing (re-parse only changed subtrees), but incrementally updating graph edges (which calls-edges point to a changed symbol) is too complex for v1. Deferred.

### 2. Git update trigger: manual only

- The user clicks a "Refresh" button in the Web UI for a Git source.
- sinan performs `git pull`, computes file diff, runs file-level incremental ingestion.
- No automatic polling in v1.
- No webhook support in v1.
- Rationale: manual trigger is simple, user-controlled, and avoids resource consumption from polling or network configuration for webhooks. Polling and webhook can be added later as opt-in features.

### 3. Static file update: source-level

- Static files (Excel, Word, Email, Markdown, Txt) have no inter-file references like code.
- Update = replace: delete the source's nodes/edges, re-ingest the new file.
- No file-level diff needed for static files.

### 4. LLM-inferred `related_to` edges: delete-and-rebuild

- When a source is re-ingested (source-level or file-level), all `related_to` edges touching that source's nodes are deleted.
- LLM cross-source association inference is re-run for the affected (new/changed) nodes.
- Rationale: accuracy over speed. Stale `related_to` edges could mislead users. The cost is LLM API calls, which is acceptable for a manual-trigger update flow (not real-time).
- Future optimization: a retention strategy (keep old edges, only infer for new nodes) can be layered on if LLM cost becomes a problem.

## Consequences

- **+** Source-level incremental is simple and reliable — a clear `source_id` scoping makes delete+rebuild atomic and safe.
- **+** File-level incremental for Git avoids re-parsing an entire repo on every refresh — only changed files are processed.
- **+** Manual trigger keeps the user in control; no surprise background resource usage.
- **+** LLM edge delete-and-rebuild guarantees accuracy of cross-source associations.
- **−** Symbol-level changes (e.g. editing one function) trigger file-level re-parse of the whole file — coarser than ideal, but acceptable given tree-sitter's parsing speed.
- **−** Manual trigger means the graph can be stale until the user refreshes. This is acceptable given v1's current-state-only scope (ADR-0002) — there is no real-time requirement.
- **−** LLM edge rebuild on every refresh could be costly for large projects. Mitigation: only re-run inference for changed nodes, not the entire project.
