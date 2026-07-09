# ADR-0012: LLM Integration Model

- **Status:** Accepted
- **Date:** 2026-07-10

## Context

sinan needs LLMs for two distinct task categories, and the user requires: (1) universal support for all models, (2) per-task model configuration. Additionally, Code-Graph-RAG's two-model split (orchestrator + Cypher) is confirmed for adoption.

## Decision

### 1. Universal model support via LiteLLM

Use **LiteLLM** as the universal LLM abstraction layer. LiteLLM is the leading open-source AI gateway supporting **100+ providers** (OpenAI, Anthropic, Google Gemini, AWS Bedrock, Azure, Ollama/local, and more) through a single OpenAI-compatible interface.

- **Python SDK** for in-process integration with sinan's Python backend.
- **OpenAI-compatible API** — all models called with the same interface, no provider-specific code.
- **Provider routing, fallbacks, cost tracking** built in.

Rationale: LiteLLM is the most widely adopted open-source LLM proxy ([github.com/BerriAI/litellm](https://github.com/BerriAI/litellm)). It eliminates vendor lock-in and lets users point sinan at any model — cloud (GPT-4o, Claude, Gemini) or local (Ollama, vLLM). This directly satisfies the "universal support for all models" requirement.

### 2. Per-task model configuration (config-driven)

sinan's config assigns models to **task roles**, not to hardcoded model names. Each role is independently configurable:

```yaml
llm:
  # Ingest-time tasks
  cross_source_association:        # LLM cross-source related_to inference
    model: "gpt-4o"
    provider: "openai"
  document_entity_extraction:      # Concept/Feature/Component extraction from docs
    model: "gpt-4o-mini"
    provider: "openai"

  # Query-time tasks (two-model split, per Code-Graph-RAG lesson)
  orchestrator:                    # Reasoning, answer synthesis, evidence assembly
    model: "gpt-4o"
    provider: "openai"
  cypher_generator:                # NL→Cypher query generation
    model: "gpt-4o-mini"
    provider: "openai"

  # Embedding model (for vectors)
  embedding:
    model: "text-embedding-3-small"
    provider: "openai"
```

Each role maps to a LiteLLM model identifier. Users can mix providers (e.g., orchestrator on Claude, cypher on GPT-4o-mini, embedding on local Ollama). Any role can point to any LiteLLM-supported model.

### 3. Task roles (fixed set)

| Role | Phase | Purpose |
|---|---|---|
| `cross_source_association` | Ingest | Infer `related_to` edges across code/doc/data sources |
| `document_entity_extraction` | Ingest | Extract Concept/Feature/Component nodes from documents |
| `orchestrator` | Query | Reason over retrieved evidence, synthesize progressive-disclosure answers |
| `cypher_generator` | Query | Generate Cypher graph queries from natural language |
| `embedding` | Ingest + Query | Vectorize document chunks + queries for semantic search |

### 4. Two-model split (adopted from Code-Graph-RAG)

Confirmed. The query path uses a separate orchestrator model (strong reasoning) and cypher_generator model (can be cheaper/faster). This allows cost optimization: pay for strong reasoning only where needed, use cheaper models for mechanical Cypher generation.

### 5. Structured query template fallback

Per the Code-Graph-RAG lesson (small models produce poor Cypher), if `cypher_generator` fails or returns invalid Cypher, sinan falls back to a **structured query template library** (predefined Cypher patterns for common query types: impact analysis, dependency tracing, provenance chain, find-callers, etc.). The orchestrator selects a template + fills parameters rather than generating freeform Cypher. This ensures the system degrades gracefully with weaker models.

## Consequences

- **+** Universal model support — any LLM provider via LiteLLM, no vendor lock-in.
- **+** Per-task config — optimize cost/capability per role; mix providers.
- **+** Two-model split enables cost optimization without sacrificing reasoning quality.
- **+** Structured fallback ensures graceful degradation with weak models.
- **−** Adds LiteLLM as a dependency. Mitigation: it's mature, widely adopted, MIT-licensed, and can run as either in-process SDK or external proxy.
- **−** Config complexity — users must configure 5 roles. Mitigation: sensible defaults (all-OpenAI or all-Ollama) out of the box; advanced users customize per-role.
