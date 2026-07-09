# ADR-0002: v1 Scope — Current-State Only (No Temporal Tracking)

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

Initial brainstorming surfaced a requirement to answer questions like "this feature broke, it used to work differently — what changed?" (Q5). This implies temporal knowledge-graph capabilities: reconstructing past graph states, diffing across time, bi-temporal edges.

## Decision

**v1 represents only the current state of all sources.** No temporal tracking, no historical graph reconstruction, no "what changed since X" queries.

Each node/edge still carries **provenance** (the source file + line range / document section / ticket that produced it) — this is required by the evidence-chain requirement and is independent of temporal tracking. But there is no version history of the graph itself, and a re-ingest overwrites the previous state for a given source.

## Consequences

- **+** Dramatically simpler storage model: no bi-temporal metadata, no snapshot management, no diff computation.
- **+** Incremental ingestion stays simple: re-ingest a source → replace its nodes/edges with the latest.
- **+** Provenance (evidence chain) is preserved — we can still trace any claim to its original source.
- **−** Cannot answer "what changed" / "this used to be different" questions. If this becomes important later, it will require a follow-up ADR to add snapshotting or event-sourcing on top of the current-state graph.
- **Architectural note:** Design ingestion as timestamped *events* internally, so that historical reconstruction could be layered on later without re-architecting — but do not build the query surface for it in v1.
