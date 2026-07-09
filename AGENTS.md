# AGENTS.md — sinan

> LLM-powered multi-source project analysis. Build cross-system knowledge graphs (code + docs + Excel + data lineage), query with evidence-backed answers, drill down from architecture to a single line of code.

```
Data Sources → Ingestion Pipeline → ArcadeDB Knowledge Graph → Query Layer → Web UI / MCP
(GitHub/Excel/   (8 stages, Celery)   (graph + vectors,         (graph-first +     (Angular +
 Word/Email/MD)                       multi-DB env isolation)   vector-supplement)  Cytoscape /
                                                                LiteLLM gateway)    MCP endpoint)
```

**Tech stack:** Python 3.12 · FastAPI · Pydantic · ArcadeDB · Celery/Redis · LiteLLM · tree-sitter · Angular/Cytoscape
**Dev prereqs:** `uv`, Python ≥3.12
**Startup:** TBD (reserved — backend/frontend launch commands added when wired)

## 目录与架构

```
src/sinan/
├── core/          # 铁律层: types.py (node/edge names), models.py (shapes), interfaces.py (pack ABCs)
├── packs/         # 可扩展层: language/ framework/ source/ — 实现核心接口,禁止反向依赖
│   ├── language/  #   tree-sitter 语言包 (TS/Python/Java/C#/SQL — ADR-0007)
│   ├── framework/ #   框架包 (dbt/Spark 数据血缘 — ADR-0007)
│   └── source/    #   数据源 ingestor (GitHub/Excel/Word/Email/MD/Txt — ADR-0004)
├── storage/       # ArcadeDB 仓储层 (ADR-0008) — packs 禁止导入
├── llm/           # LiteLLM 集成 (ADR-0012) — packs 禁止导入
├── query/         # RAG 混合检索层 (ADR-0014) — packs 禁止导入
└── api/           # FastAPI + MCP (ADR-0013) — packs 禁止导入
```

**依赖方向（铁律）:** `packs → core` 单向。packs 只能 import `sinan.core.*`。
禁止 `packs` import `sinan.storage|llm|api|query`。由 `test_packs_do_not_import_internals` 强制。

## 验证命令

| 范围 | 命令 | 何时用 |
|---|---|---|
| 文件级（快） | `uv run ruff check <file>` · `uv run ruff format <file>` | 改单个文件后 |
| 全量 pre-commit | `uv run ruff check src/ && uv run ruff format --check src/` | 提交前 |
| 全量类型 | `uv run mypy src/sinan` | 推送前（pre-push hook） |
| 全量门测试 | `uv run pytest tests/types/ -v` | 推送前（pre-push hook） |
| 全量测试 | `uv run pytest tests/ -v -m "not network"` | CI |

## 自动化检查（三层纵深防御）

| 层 | 触发 | 耗时 | 内容 |
|---|---|---|---|
| pre-commit | `git commit` | <2s | ruff check + ruff format（Python） |
| pre-push | `git push` | ~15s | mypy src/sinan + pytest tests/types/ |
| **CI** | push/PR | 完整 | **权威关卡** — ruff + mypy + pytest + pip-audit，branch protection 强制 |

> CI 是不可绕过的权威关卡。`--no-verify` 绕过本地 hook，**绕不过 CI**。
> Branch protection 要求 `check` job 通过才能合并。

## AI 行为原则（ADR-0019）

**优先级: 质量 > 维护性 > 成本。** 成本优化在质量约束内追求，绝不牺牲质量省成本。

1. **Think-before-do** — 先读 ADR 和相关代码，理解约束再动手。
2. **Precise-minimal** — 最小精确改动，不顺手重构无关代码。
3. **Simplicity-first** — 资深工程师会说"过度设计"吗？会就不做。
4. **Honest-unknowns** — 信息不足时标注"未知"，绝不猜测冒充确定。

## 铁律 #1: 节点/边类型名（ADR-0006, ADR-0020）

`src/sinan/core/types.py` 是 `NodeType`/`EdgeType` 定义**唯一**位置。

- ✅ 用枚举成员: `NodeType.CODE_SYMBOL`、`EdgeType.CALLS`
- ❌ 禁止在 types.py 之外定义 `NodeType`/`EdgeType`(StrEnum 子类) — `test_node_edge_types_defined_only_in_core` 强制
- ❌ 禁止用裸字符串构造类型: `"CodeSymbol"`（拼写错误不会被捕获）— 用枚举成员
- ❌ 禁止添加枚举成员而不更新 `NODE_TYPE_REGISTRY`/`EDGE_TYPE_REGISTRY` — `test_all_node_types_registered` / `test_all_edge_types_registered` 强制

## 铁律 #2: 节点/边类型形状（ADR-0006, ADR-0020）

`src/sinan/core/models.py` 是 `NodeModel`/`EdgeModel` 形状定义**唯一**位置。

- ✅ packs 构造 `NodeModel(...)` / `EdgeModel(...)` 实例（或注册的子类）
- ❌ 禁止返回裸 dict — 接口签名要求 `list[NodeModel]`，mypy 会拒绝 dict
- 缺字段/类型错在构造瞬间 `ValidationError` 失败，到不了存储层
- 每个 `NodeType` 必须在 `NODE_MODEL_REGISTRY` 有对应模型 — `test_every_node_type_has_model` 强制
- 特化子模型（如 `CodeSymbolModel`）**随使用它的 pack 一起加**，不预先全建

## 铁律 #3: ADR↔代码一致性（ADR-0020）

ADR 引用的文件路径/类名/枚举标识符必须与代码同步。

- 变更 ADR 引用的路径 → 同步更新代码路径，反之亦然
- `test_adr_referenced_paths_exist` + `test_adr_type_identifiers_are_valid` 强制
- 违反记入历史教训（见下）

## Pack 编写规则（ADR-0015）

1. 在 `PACK_REGISTRY`（`core/interfaces.py`）注册你的 pack
2. 实现正确的 Base（`BaseLanguagePack`/`BaseFrameworkPack`/`BaseSourceIngestor`）
3. 发射 `NodeModel`/`EdgeModel` 实例，不是 dict
4. 通过 conformance 测试（fixture 随首 pack 建立）
5. 不 import `storage`/`llm`/`api`/`query`

## 历史教训

> 格式: `L{N}: 教训 → 根因 → 防护`。新增按 L{N} 续加。

*（尚无 — 随项目演进积累）*

## Git 与 PR

- **Conventional Commits** 带模块 scope: `feat(language-ts):`, `fix(query):`, `docs(adr):`, `test(types):`
- 从 `main` 开分支
- PR 必须通过 CI `check` 关卡
- **处理 PR review / CI 失败**: 遵循 [`docs/agent/pr-review-protocol.md`](docs/agent/pr-review-protocol.md)（先本地验证 → 批量收集 → 修复+回复+resolve → 先修阻断性基础设施）

## 预留（未启用）

以下能力在对应代码落地时启用，**现在不配置**（避免死配置/死文档）:

**配置类:**
- **前端 lint**（ESLint/Prettier）— Angular 脚手架建立后
- **生成产物漂移检查**（generated-schema drift）— MCP/OpenAPI schema 生成器建立后
- **Schemathesis 契约测试** — API 层建立后

**文档类（`docs/agent/` 下，随代码建立）:**
- `conventions.md` — 错误层级、API 路由约定、配置双层、数据源降级（代码建立后）
- `pack-authoring.md` — Pack 编写完整指南与模板（首 pack 建立时，ADR-0015 §5 已计划）

> 已覆盖、无需单独文档: 类型清单（NodeType/EdgeType 见 `core/types.py` + 铁律 #1/#2，非独立 enums.md）。
