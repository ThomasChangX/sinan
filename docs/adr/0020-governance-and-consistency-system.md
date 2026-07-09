# ADR-0020: Governance and Consistency System

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

The user requires that sinan never suffer path or data-structure inconsistency as it grows (30+ language packs, 25+ framework packs, multiple source ingestors, multiple contributors + AI agents). ADR-0015 established the principles (architecture tests, pack conformance, linting, ADR-driven dev); this ADR defines the concrete governance system that implements them, adapted from the proven pattern in a sibling project (`a-stock-assistant`).

## Decision

### 1. Three-layer defense in depth

| Layer | Trigger | Latency | Contents |
|---|---|---|---|
| pre-commit | `git commit` | <2s | ruff check + format (Python) |
| pre-push | `git push` | ~15s | mypy + architecture/doc gate tests |
| CI | push/PR | full | authoritative gate — ruff + mypy + pytest + pip-audit; `check` job + branch protection |

CI is the non-bypassable gate. `--no-verify` bypasses local hooks but not CI. This mirrors the reference project's proven model.

### 2. Dual single-source-of-truth (铁律)

The reference project uses an enum iron-law (type names) + Pydantic models (type shapes) + a cross-check test. Sinan adopts the same dual structure:

- **铁律 #1 — Type names:** `src/sinan/core/types.py` is the ONLY place `NodeType`/`EdgeType` may be defined. `test_node_edge_types_defined_only_in_core` (AST, scoped to StrEnum subclass *definitions*) enforces this. Member access (`NodeType.X`) is never flagged — it's the correct usage.
- **铁律 #2 — Type shapes:** `src/sinan/core/models.py` defines `NodeModel`/`EdgeModel` (Pydantic). Packs construct instances, never raw dicts — enforced by interface return-type signatures + Pydantic's runtime validation. `test_every_node_type_has_model` cross-checks that every NodeType has a registered model.
- **铁律 #3 — ADR↔code:** ADR-referenced paths/identifiers must stay valid. `test_doc_consistency.py` lints this.

### 3. Architecture-gate tests (`tests/types/test_architecture_gates.py`)

Seven tests, each precisely scoped (see file docstrings):
1. Type definitions only in core/types.py.
2. All enum members registered.
3. Every NodeType has a model (cross-check).
4. Registered packs implement correct base (explicit PACK_REGISTRY, not name-guessing).
5. Packs don't import storage/llm/api/query (layer rule).
6. All modules import cleanly (circular-import smoke, non-exhaustive).
7. Pydantic rejects missing fields (runtime boundary sanity).

### 4. pip-audit supply-chain scanning (v4 optimization)

CI `audit` job runs `pip-audit` against `uv.lock`. Per [Defense in Depth Python supply-chain guidance](https://bernat.tech/posts/securing-python-supply-chain/), this scans the lockfile (which exists from day 1) and grows in coverage as dependencies are added. Low cost, high value, aligned with Quality > Cost principle (ADR-0019).

### 5. ADR↔code consistency lint (v4 optimization)

`tests/types/test_doc_consistency.py` — minimal docs-as-code check (VeriContext-inspired, no SHA hashing). Asserts backtick-wrapped paths and `NodeType.X`/`EdgeType.X` identifiers in ADRs resolve. Catches the most common doc drift (renamed files/classes).

## Deferred (considered, not forgotten)

Each was evaluated and explicitly deferred with rationale:

| Item | Rationale for deferral |
|---|---|
| **Schemathesis / Hypothesis** contract testing | Requires a running API + OpenAPI schema. None exists yet. Add when API layer is built — high value then. |
| **Semgrep** custom architecture rules | AST gate tests already cover core needs (layer rules, interface compliance, type SoT). Semgrep adds value when packs proliferate and security rule breadth matters. |
| **Dependabot** config file | GitHub-native; no config file needed to enable. pip-audit covers CI scanning. PR-update behavior optional, enable on demand. |
| **commitlint / commit-msg hook** | Conventional Commits enforced via AGENTS.md + PR review. commit-msg hook conflicts with squash-merge workflows. |
| **Full SHA doc-code hashing** (VeriContext-style) | Over-engineering for now. The path/identifier lint catches the common drift case cheaply. |

## Consequences

- **+** Type-name drift impossible (enum + AST test + member-only usage).
- **+** Type-shape drift impossible (Pydantic construction + cross-check).
- **+** Path/import drift impossible (layer test + circular smoke + monorepo scan).
- **+** Doc drift caught early (ADR↔code lint).
- **+** Supply-chain risk caught in CI (pip-audit).
- **+** All guardrails are deterministic, fast, and CI-enforced — no reliance on reviewer memory.
- **−** Seven architecture tests + two doc tests = maintenance surface. Mitigation: each is small, single-purpose, and the patterns are proven in the reference project.
- **−** mypy not globally strict — some type errors slip through. Mitigation: incremental tightening via module overrides as code stabilizes; `check_untyped_defs` + `warn_unreachable` catch the high-signal subset.
