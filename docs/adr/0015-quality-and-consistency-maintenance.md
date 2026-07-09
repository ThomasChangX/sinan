# ADR-0015: Quality and Consistency Maintenance

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

sinan is an extensible framework where multiple language packs, framework packs, and source ingestors are added over time. Without guardrails, the codebase will drift: packs will diverge in interface compliance, architecture layers will blur, and inconsistencies will accumulate. The user explicitly requires quality review and consistency maintenance as a first-class concern.

## Decision

### 1. Architecture tests (guardrails, enforced in CI)

Inspired by ArchUnit-style architecture testing and the [automated architectural governance practice](https://www.linkedin.com/pulse/from-gates-guardrails-automating-architectural-governance-khan-jkyoc):

- **Layer dependency rules** — enforce that packs depend only on the core interfaces, never on each other or on storage/LLM internals. Tests assert: `ingestor` layer may import `core.interfaces` but not `storage` or `llm`.
- **Interface compliance** — every language pack, framework pack, and source ingestor must implement its declared interface. A test scans the `packs/` directory and asserts each pack class implements the correct ABC/Protocol.
- **Naming conventions** — packs follow `LanguagePack`, `FrameworkPack`, `SourceIngestor` naming; query files under `.scm`; config keys match the interface contract.
- **No circular imports** — automated check across modules.

These run as unit tests in CI on every PR. A pack that violates the architecture cannot merge.

### 2. Pack conformance test suite

Every pack type has a **conformance test fixture**: a small sample input (a code snippet, an Excel file, a document) with expected node/edge output. Each new pack must pass the conformance test for its type. This ensures all language packs produce structurally equivalent graphs — a Java function and a Python function produce the same `CodeSymbol` node shape, so cross-language queries work.

- `tests/conformance/language_pack/` — sample repos per language, expected graph assertions.
- `tests/conformance/framework_pack/` — sample DI/route/lineage patterns, expected edges.
- `tests/conformance/source_ingestor/` — sample files per type, expected nodes.

### 3. Linting and static analysis (CI-enforced)

| Tool | Scope | Purpose |
|---|---|---|
| **Ruff** | Python (backend) | Lint + format (replaces flake8/isort/black) |
| **ESLint + Prettier** | Angular (frontend) | Lint + format |
| **mypy** | Python | Type checking — critical for interface contracts |
| **Semgrep** | All | Security + custom architecture rules (e.g., "no pack imports storage") |

All run in pre-commit hooks and CI. No merge without clean lint/types.

### 4. ADR-driven development

- Every architectural decision is recorded as an ADR (this practice, ongoing).
- Code changes that contradict an ADR must either update the ADR (with rationale) or be rejected in review.
- The ADRs live in `docs/adr/` and are the source of truth for architecture. The [AI guardrails practice](https://paddo.dev/blog/guardrails-by-default/) of encoding decisions as checkable rules is applied: where an ADR implies a testable rule, a corresponding architecture test exists.

### 5. AGENTS.md / contribution guardrails

- A root `AGENTS.md` documents the architecture rules, pack interfaces, and conformance requirements — so that AI coding agents (ZCode, Codex, etc.) that help build packs follow the same constraints as human contributors.
- Pack authoring guide (`docs/pack-authoring.md`) with a template and checklist for adding a new language/framework pack.

### 6. Continuous consistency checks

- **Graph schema consistency** — a test that ingests a reference multi-source project and asserts the resulting graph matches the schema in ADR-0006 (correct node types, no orphan nodes except expected, provenance present on all nodes).
- **Query layer smoke tests** — a set of canonical questions with expected answer structure (progressive disclosure layers present, evidence chain populated).

## Consequences

- **+** Architecture cannot drift — CI enforces layer rules and interface compliance.
- **+** Packs are structurally consistent — conformance tests guarantee cross-language/cross-source uniformity.
- **+** AI agents and humans follow the same guardrails via AGENTS.md.
- **+** ADRs are living enforcement, not just documentation.
- **−** Upfront test infrastructure investment. Mitigation: conformance fixtures are small; the framework is built once and every subsequent pack benefits.
- **−** Some overhead for pack authors (must pass conformance tests). Mitigation: clear authoring guide + template reduces friction; the conformance test IS the spec.
