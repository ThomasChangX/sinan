# ADR-0004: v1 Data Sources

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

The user must be able to add raw data sources to an analysis project. Each source type requires a dedicated ingestor (connector + parser + extractor). Scope must be bounded for a shippable v1.

## Decision

### v1 supported sources (final)

| Source | Type | Notes |
|---|---|---|
| GitHub repository URL | Git | Clone + analyze. Default branch detection + explicit branch override. |
| Stash / Bitbucket Server URL | Git | Same pipeline as GitHub, with Bitbucket Server API auth. Default branch detection + explicit branch override. |
| Excel (.xlsx) | Static file | **Formula extraction is a v1-class requirement** (not optional) — enables cell-level lineage answers per ADR-0003. Extract: cell text, formulas, cell→cell references. |
| Word (.docx) | Static file | Section-aware parsing + chunking. |
| Email (.eml / .msg) | Static file | Headers + body + attachment references. |
| Markdown (.md) | Static file | Header-based section chunking. |
| Plain text (.txt) | Static file | Fixed-size chunking. |

### Explicitly out of v1
- Jira (Server + Cloud) — deferred.
- Jira Cloud — deferred.
- Rally — deferred.

These may return in a later version with their own ADR if demand materializes.

### Git branch handling

- **Default behavior:** clone the repository's default branch. Detect automatically: prefer `main`, fall back to `master`, fall back to whatever the remote reports as `HEAD`.
- **Override:** the user can specify an explicit branch when adding a Git source. When specified, that branch is cloned and analyzed; the default-branch detection is skipped.
- One source = one branch. To analyze multiple branches of the same repo, the user adds multiple Git sources (one per branch), each as a distinct source within the project. This keeps the ingest model simple and the graph unambiguous about which branch a code node belongs to.

## Consequences

- **+** Tight, shippable v1: 2 Git + 5 static-file sources.
- **+** Excel formula extraction is committed, so the lineage answer shape (ADR-0003) is fully supported for Excel-backed questions.
- **+** One-source-one-branch rule avoids multi-branch graph merge complexity.
- **−** No ALM integration in v1 — ticket↔code links cannot be auto-discovered. If the user wants ticket context, they must include it as a document (e.g. export Jira to CSV/Excel/Markdown and add as a static-file source). This is a workaround, not a first-class integration.
- **−** `.msg` (Outlook proprietary) parsing needs a dedicated library; `.eml` (RFC 822) is standard. Confirm both formats are needed, or `.eml`-only is acceptable.
- **Open:** Git auth model for private repos — see next ADR.
