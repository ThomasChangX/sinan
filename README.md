<div align="center">

# 司南 · sinan

**基于 LLM 的多源项目分析引擎 —— 构建跨系统知识图谱，带证据链理解你的整个项目**

*司南（sinan），中国古代的指南针。在纷繁的代码、文档、数据中，为你指引理解的方向。*

</div>

---

<div align="center">

[![CI](https://github.com/ThomasChangX/sinan/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ThomasChangX/sinan/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-261230.svg?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

<!-- ==================== 中文 ==================== -->

## 📖 项目简介

`sinan`（司南）是一个**自托管的、基于 LLM 的项目分析解决方案**。

你创建一个「分析项目」，把各种数据源（GitHub 仓库、Excel 报表、Word 文档、邮件、Markdown）导入进来，sinan 会：

1. **增量构建知识图谱** —— 用 tree-sitter 解析代码、完整解析 Excel（公式 / 透视表 / 校验规则）、结构化解析文档，把它们统一成一个跨系统关联的图。
2. **智能建立跨源关联** —— LLM 推断代码符号、文档概念、数据资产之间的语义关联，让分散在所有系统中的信息连成一张网。
3. **有界数据溯源** —— 从一个报表单元格，追溯到它的计算公式、允许值、校验规则，一直到最原始的数据来源，每一步都有证据链。
4. **渐进式展示** —— 图表 → 文档章节 → 代码 / 数据切片，从顶层架构一路 drill-down 到具体某一行代码。
5. **AI 问答** —— 通过 Web UI 或 MCP 端点（供 ZCode / Codex / Claude / Copilot 等 AI 开发工具调用），用自然语言提问，获得有证据支撑的完整答案。

> **核心理念：** 在一个项目的代码、文档、数据散落在 Git、Confluence、Excel、Jira 各处时，sinan 帮开发者和业务负责人快速建立**完整且可追溯**的理解。每一个分析结论都能倒查到做出这个分析的最原始文档和代码。

---

## ✨ 核心特性

| 特性 | 说明 |
|---|---|
| 🔗 **多源融合** | 代码 + 文档 + Excel + 邮件，在一个知识图谱里统一关联 |
| 📊 **全量 Excel 分析** | 公式依赖图、透视表血缘、PivotCache、数据校验——完整 OOXML 解析（[ADR-0006](docs/adr/0006-knowledge-graph-data-model.md)） |
| 🌲 **tree-sitter 深度利用** | 七层能力：CST / 符号 / 装饰器 / 调用 / import / 代码切片 / 路由检测（30+ 语言） |
| 🎯 **有界数据溯源** | report → API → SQL → 表，基于用户提供的源构建完整逻辑链 |
| 🤖 **LLM 跨源关联** | 代码符号 ↔ 文档概念 ↔ 数据资产的 `related_to` 语义边（带置信度） |
| 🖼️ **11 个默认视图** | C4 架构图、数据血缘 DAG、报表目录、校验覆盖、发现与健康检查等 |
| 🔍 **四个通用操作** | 每个节点：Drill-down / Ask AI / 影响分析 / 路径追踪 |
| 🧩 **可扩展框架** | 语言包 / 框架包 / 数据源 ingestor 全部接口化，后续 MVP 即插即用 |
| 🏠 **自托管** | Docker Compose 一键部署，或 Linux 命令行直接启动 |

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户访问层                               │
│   Web UI (Angular + Cytoscape)          MCP Endpoint             │
│   项目/源管理 · 图浏览器 · AI Chat       (ZCode/Codex/Claude…)    │
└───────────┬───────────────────────────────────┬─────────────────┘
            │           共享查询层                │
┌───────────▼───────────────────────────────────▼─────────────────┐
│              Query Layer (FastAPI · 混合检索)                     │
│   图优先(结构化问题 → Cypher 遍历) + 向量辅助(语义模糊匹配)        │
│   → 全局证据排序 → Orchestrator 合成渐进式答案                    │
└───────┬───────────────────────────────┬─────────────────────────┘
        │                               │
┌───────▼───────────┐       ┌──────────▼──────────────────────────┐
│  LiteLLM 网关      │       │   ArcadeDB (单一多模型引擎)          │
│  100+ provider    │       │   属性图 + 向量索引 + 元数据          │
│  按角色配置模型    │       │   多数据库 (DEV/QA/UAT/PROD 隔离)    │
└───────────────────┘       └─────────────────────────────────────┘
            ▲
┌───────────┴──────────────────────────────────────────────────── ┐
│   Ingestion Pipeline (Celery · 8 阶段后台任务)                    │
│   Fetch → Parse → Extract → NameResolve → SQLInject              │
│   → Embed → LLM-associate → Persist                              │
│                                                                   │
│   ┌──────────┐  ┌─────────┐  ┌────────┐  ┌────────┐            │
│   │Language  │  │Framework│  │Source  │  │  core  │            │
│   │Packs     │  │Packs    │  │Ingestor│  │ types/ │            │
│   │TS Py Java│  │dbt Spark│  │GH Excel│  │ models │            │
│   │C# SQL…   │  │…        │  │Word…   │  │ interf.│            │
│   └──────────┘  └─────────┘  └────────┘  └────────┘            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

> ⚠️ sinan 目前处于**设计 + 框架搭建阶段**（MVP-1 进行中）。以下为规划中的使用方式。

### 环境要求

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/)（包管理）
- Node.js ≥ 20（前端，待搭建）
- ArcadeDB（图数据库，待搭建）

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/ThomasChangX/sinan.git
cd sinan

# 安装依赖
uv sync --extra dev

# 运行测试
uv run pytest tests/ -v

# 安装 git hooks（pre-commit + pre-push）
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

---

## 📐 设计文档

所有架构决策记录在 ADR 中（[`docs/adr/`](docs/adr/)）：

| 范畴 | ADR |
|---|---|
| **范围与模型** | [0001](docs/adr/0001-deployment-and-access-model.md) 部署 · [0002](docs/adr/0002-v1-scope-current-state-only.md) 范围 · [0003](docs/adr/0003-v1-scope-and-data-lineage.md) 数据血缘 · [0006](docs/adr/0006-knowledge-graph-data-model.md) 数据模型 |
| **数据源** | [0004](docs/adr/0004-v1-data-sources.md) 数据源 · [0005](docs/adr/0005-credential-and-file-source-model.md) 凭证模型 |
| **技术与存储** | [0007](docs/adr/0007-language-and-framework-pack-scope.md) 语言/框架 · [0008](docs/adr/0008-storage-architecture.md) 存储 · [0012](docs/adr/0012-llm-integration-model.md) LLM · [0013](docs/adr/0013-deployment-and-ui-tech-stack.md) 技术栈 |
| **管线与查询** | [0009](docs/adr/0009-incremental-build.md) 增量构建 · [0014](docs/adr/0014-ingestion-pipeline-and-query-layer.md) 摄取与查询 |
| **UI 与分析** | [0016](docs/adr/0016-default-web-ui-views.md) 视图 · [0017](docs/adr/0017-findings-and-health-inspection.md) 发现 · [0018](docs/adr/0018-impact-analysis-and-complexity-hotspots.md) 影响分析 · [0019](docs/adr/0019-path-explorer-and-engineering-priorities.md) 路径探索 |
| **工程治理** | [0015](docs/adr/0015-quality-and-consistency-maintenance.md) 质量 · [0020](docs/adr/0020-governance-and-consistency-system.md) 治理体系 · [0010](docs/adr/0010-reference-implementations-analysis.md) 参考实现 · [0011](docs/adr/0011-mvp1-scope.md) MVP-1 范围 |

---

## 🤝 贡献

- 架构规则、铁律、验证命令见 [`AGENTS.md`](AGENTS.md)
- PR review 流程见 [`docs/agent/pr-review-protocol.md`](docs/agent/pr-review-protocol.md)
- 工程优先级：**质量 > 维护性 > 成本**（[ADR-0019](docs/adr/0019-path-explorer-and-engineering-priorities.md)）

---

## 📄 许可证

[MIT](LICENSE)

---

<!-- ==================== English ==================== -->

<div align="center">

# sinan

**An LLM-powered multi-source project analysis engine — build cross-system knowledge graphs to understand your entire project, with evidence.**

*司南 (sinan) — the ancient Chinese compass. In a sea of scattered code, docs, and data, it points you toward understanding.*

</div>

---

## 📖 Overview

`sinan` is a **self-hosted, LLM-powered project analysis solution**.

You create an "analysis project," feed it data sources (GitHub repos, Excel reports, Word docs, emails, Markdown), and sinan:

1. **Incrementally builds a knowledge graph** — parses code with tree-sitter, fully parses Excel (formulas / pivot tables / validation rules), structurally parses documents, unifying them into one cross-system graph.
2. **Intelligently links sources** — an LLM infers semantic associations between code symbols, document concepts, and data assets, connecting information scattered across all your systems.
3. **Provides bounded data provenance** — from a report cell, trace its formula, allowed values, validation rules, all the way to the original data source — every step backed by an evidence chain.
4. **Progressive disclosure** — graph → document sections → code/data slices, drill down from top-level architecture to a specific line of code.
5. **AI Q&A** — via Web UI or MCP endpoint (for AI dev tools like ZCode / Codex / Claude / Copilot), ask questions in natural language and get evidence-backed answers.

> **Core idea:** When a project's code, docs, and data are scattered across Git, Confluence, Excel, and Jira, sinan helps developers and business owners build a **complete and traceable** understanding. Every analysis conclusion can be traced back to the original document and code it was derived from.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔗 **Multi-source fusion** | Code + docs + Excel + email, unified in one knowledge graph |
| 📊 **Full Excel analysis** | Formula dependency graphs, pivot-table lineage, PivotCache, data validation — complete OOXML parsing ([ADR-0006](docs/adr/0006-knowledge-graph-data-model.md)) |
| 🌲 **Deep tree-sitter leverage** | Seven layers: CST / symbols / decorators / calls / imports / code slices / route detection (30+ languages) |
| 🎯 **Bounded data provenance** | report → API → SQL → table, a complete logical chain built from user-provided sources |
| 🤖 **LLM cross-source association** | `related_to` semantic edges between code symbols ↔ doc concepts ↔ data assets (with confidence) |
| 🖼️ **11 default views** | C4 architecture, data lineage DAG, report catalog, validation coverage, findings & health inspection, and more |
| 🔍 **Four universal actions** | Every node: Drill-down / Ask AI / Impact analysis / Path tracing |
| 🧩 **Extensible framework** | Language packs / framework packs / source ingestors are all interface-based — future MVPs plug in without architectural changes |
| 🏠 **Self-hosted** | One-command Docker Compose deploy, or direct Linux CLI launch |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Access Layer                             │
│   Web UI (Angular + Cytoscape)          MCP Endpoint             │
│   Project/source mgmt · Graph browser   (ZCode/Codex/Claude…)    │
│              · AI Chat                                           │
└───────────┬───────────────────────────────────┬─────────────────┘
            │          Shared Query Layer         │
┌───────────▼───────────────────────────────────▼─────────────────┐
│              Query Layer (FastAPI · Hybrid Retrieval)            │
│   Graph-first (structural → Cypher traversal) +                  │
│   Vector-supplement (semantic fuzzy matching)                    │
│   → Global evidence ranking → Orchestrator synthesizes           │
│     progressive-disclosure answer                                │
└───────┬───────────────────────────────┬─────────────────────────┘
        │                               │
┌───────▼───────────┐       ┌──────────▼──────────────────────────┐
│  LiteLLM Gateway   │       │   ArcadeDB (single multi-model)     │
│  100+ providers    │       │   Property graph + vector index     │
│  Per-role config   │       │   + metadata · Multi-DB             │
│                    │       │   (DEV/QA/UAT/PROD isolation)       │
└───────────────────┘       └─────────────────────────────────────┘
            ▲
┌───────────┴──────────────────────────────────────────────────── ┐
│   Ingestion Pipeline (Celery · 8-stage background job)           │
│   Fetch → Parse → Extract → NameResolve → SQLInject              │
│   → Embed → LLM-associate → Persist                              │
│                                                                   │
│   ┌──────────┐  ┌─────────┐  ┌────────┐  ┌────────┐            │
│   │Language  │  │Framework│  │Source  │  │  core  │            │
│   │Packs     │  │Packs    │  │Ingestor│  │ types/ │            │
│   │TS Py Java│  │dbt Spark│  │GH Excel│  │ models │            │
│   │C# SQL…   │  │…        │  │Word…   │  │ interf.│            │
│   └──────────┘  └─────────┘  └────────┘  └────────┘            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

> ⚠️ sinan is currently in the **design + scaffolding phase** (MVP-1 in progress). The usage below reflects the planned experience.

### Prerequisites

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) (package manager)
- Node.js ≥ 20 (frontend, pending scaffold)
- ArcadeDB (graph database, pending setup)

### Development

```bash
# Clone
git clone https://github.com/ThomasChangX/sinan.git
cd sinan

# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Install git hooks (pre-commit + pre-push)
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

---

## 📐 Design Documentation

All architectural decisions are recorded as ADRs ([`docs/adr/`](docs/adr/)):

| Area | ADRs |
|---|---|
| **Scope & Model** | [0001](docs/adr/0001-deployment-and-access-model.md) Deployment · [0002](docs/adr/0002-v1-scope-current-state-only.md) Scope · [0003](docs/adr/0003-v1-scope-and-data-lineage.md) Data lineage · [0006](docs/adr/0006-knowledge-graph-data-model.md) Data model |
| **Data Sources** | [0004](docs/adr/0004-v1-data-sources.md) Sources · [0005](docs/adr/0005-credential-and-file-source-model.md) Credentials |
| **Tech & Storage** | [0007](docs/adr/0007-language-and-framework-pack-scope.md) Langs/frameworks · [0008](docs/adr/0008-storage-architecture.md) Storage · [0012](docs/adr/0012-llm-integration-model.md) LLM · [0013](docs/adr/0013-deployment-and-ui-tech-stack.md) Tech stack |
| **Pipeline & Query** | [0009](docs/adr/0009-incremental-build.md) Incremental · [0014](docs/adr/0014-ingestion-pipeline-and-query-layer.md) Ingestion & query |
| **UI & Analysis** | [0016](docs/adr/0016-default-web-ui-views.md) Views · [0017](docs/adr/0017-findings-and-health-inspection.md) Findings · [0018](docs/adr/0018-impact-analysis-and-complexity-hotspots.md) Impact · [0019](docs/adr/0019-path-explorer-and-engineering-priorities.md) Path explorer |
| **Engineering** | [0015](docs/adr/0015-quality-and-consistency-maintenance.md) Quality · [0020](docs/adr/0020-governance-and-consistency-system.md) Governance · [0010](docs/adr/0010-reference-implementations-analysis.md) Ref. analysis · [0011](docs/adr/0011-mvp1-scope.md) MVP-1 scope |

---

## 🤝 Contributing

- Architecture rules, iron-laws, and verification commands: [`AGENTS.md`](AGENTS.md)
- PR review protocol: [`docs/agent/pr-review-protocol.md`](docs/agent/pr-review-protocol.md)
- Engineering priority: **Quality > Maintainability > Cost** ([ADR-0019](docs/adr/0019-path-explorer-and-engineering-priorities.md))

---

## 📄 License

[MIT](LICENSE)
