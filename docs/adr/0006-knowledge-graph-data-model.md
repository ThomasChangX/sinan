# ADR-0006: Knowledge Graph Data Model

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

The data model is the foundation of sinan. It determines what ingestors extract, what the AI can answer, and how evidence chains are built. This ADR consolidates decisions from the grilling, with two areas given **highest priority (重中之重)**: full tree-sitter leverage, and full Excel analysis. It also enforces framework-aware injection detection and complete UI→API call-chain capture.

## Decision

### 1. Node types

#### System
| Node | Description |
|---|---|
| `Project` | Analysis project; primary isolation boundary |
| `Source` | A registered data source (Git repo@branch, Excel file, etc.) |

#### Code (extracted via tree-sitter — see §3)
| Node | Description |
|---|---|
| `Module`/`Package` | Namespace / directory hierarchy layer |
| `File` | A source file |
| `CodeSymbol` | Function / Class / Method / Interface / Enum / Type / Variable (sub-typed) |
| `ApiEndpoint` | An HTTP endpoint (detected via framework route-registration patterns) |
| `Configuration` | Declarative config (Spring XML/YAML, DI module, annotation-based config) |
| `TestCase` | A test function/method — `describes`/`validates` the feature under test |
| `CodeChunk` | A line range slice of a file, for precise display in progressive disclosure |
| `Import` | An import statement (feeds cross-file name resolution + module dependency graph) |
| `Decorator`/`Annotation` | `@Inject`, `@RestController`, etc. — feeds DI detection + route detection |

#### Documents (three-layer granularity + LLM entity extraction)
| Node | Description |
|---|---|
| `Document` | Whole file (Word, Markdown, Txt, Email-as-doc) |
| `DocumentSection` | Structural section (Markdown heading, Word paragraph block, Email body block) |
| `DocumentChunk` | Semantic chunk (fixed token window) — **the embedding/retrieval unit** |
| `Concept`/`Feature`/`Component` | Domain entities LLM extracts from docs+code — **the cross-source linking bridge** |

#### Excel (full OOXML analysis — see §2, highest priority)
| Node | Description |
|---|---|
| `Workbook` | The .xlsx file (= a `Document`) |
| `Worksheet` | A sheet |
| `Cell` | A non-empty cell (formula or value); empty cells not indexed |
| `Range` | **First-class node** (not expanded into cells by default) — per TACO/HyperFormula model |
| `Table` | Excel Table / ListObject — structured, named-column range; formulas reference `Table[Col]` |
| `PivotTable` | A pivot table |
| `PivotField` | A pivot row/col/data/filter field |
| `PivotCache` | **Independent node** — defines the pivot's data source (the pivot→source chain) |
| `Chart` | A chart — `visualizes` a Range/PivotTable |
| `DefinedName` | Workbook-level named range; resolution anchor for `=Revenue`-style formulas |
| `SharedFormula` | OOXML shared-formula group (master + slaves via `si` index) |
| `DataValidation` | `<dataValidations>` — answers "is there validation, what are allowed values" |
| `Formula` | A formula as an addressable object (supports "what is the formula for this cell") |
| `ConditionalFormatting` | Low priority in v1; model reserves the node type |

#### Email
| Node | Description |
|---|---|
| `EmailMessage` | An email; `reply_to` structural edge via `In-Reply-To`/`References` headers |

#### Cross-cutting
| Node | Description |
|---|---|
| `ValidationRule` | Generic validation (from code, docs, or Excel) |

### 2. Excel analysis — highest priority (重中之重)

sinan must parse **all** relevant OOXML parts, not just cell text. Concretely v1 must extract:

- `xl/workbook.xml` → `Workbook`, `Worksheet` list, `DefinedName`s
- `xl/worksheets/sheetN.xml` → `Cell`s, `Formula`s, `Range`s, `DataValidation`s, `ConditionalFormatting`
- `xl/tables/tableN.xml` → `Table` (ListObject with named columns)
- `xl/pivotTables/pivotTableN.xml` → `PivotTable` + `PivotField`s
- `xl/pivotCache/pivotCacheDefinitionN.xml` → `PivotCache` (the source definition)
- `xl/pivotCache/pivotCacheRecordsN.xml` → cache records (evidence for pivot cell values)
- `xl/charts/chartN.xml` → `Chart` + its referenced ranges
- Shared formulas (`t="shared"`, `si` index) → `SharedFormula` master/slave links

**Range as first-class node** is mandatory. A formula `=SUM(A1:A100)` produces ONE `computes_from` edge to a `Range` node, not 100 cell→cell edges. This follows the [TACO model (arXiv:2302.05482)](https://arxiv.org/pdf/2302.05482) and [HyperFormula](https://hyperformula.handsontable.com/docs/guide/dependency-graph.html), which show real spreadsheets can have 300k dependents and 200k-edge paths if ranges are naively expanded.

**Pivot lineage chain must be complete:** `PivotCell` → `PivotTable` → `PivotCache` → source `Range`/external query. This is the only way to answer "how is this pivot number computed".

### 3. tree-sitter — highest priority (重中之重), seven-layer leverage

tree-sitter is not just "a symbol extractor". v1 must use all seven layers:

| Layer | tree-sitter capability | sinan use |
|---|---|---|
| 1. CST build | Full-fidelity, error-tolerant, keeps every token | Evidence-chain positions: every node carries exact `(start_row,col)-(end_row,col)` |
| 2. Symbol extraction (Query DSL) | Per-language `.scm` query patterns | Build `CodeSymbol` nodes (sub-typed) |
| 3. Decorator/annotation extraction | Query patterns for `@Inject`/`@RestController`/`@Service` | Feed `Configuration`/`Decorator` nodes → DI `binds` edges, `ApiEndpoint` detection |
| 4. Call-site extraction | Query patterns for call expressions | Build `calls` edges (**name-level**, see §5) |
| 5. Import extraction | Query patterns for import statements | `Module` dependency graph + name-resolution scopes |
| 6. Code-slice rendering | CST node positions → precise line ranges | Progressive-disclosure code slices |
| 7. Route-registration detection (ast-grep-style patterns) | Structural patterns like `app.get("/x",h)`, `@GetMapping` | `ApiEndpoint` nodes + `invokes` edge matching (UI→API) |

### 4. Framework-aware injection (DI) — per language/framework

**Hard rule:** DI detection is NOT one generic algorithm. It is framework-aware. Each framework contributes its own detection patterns via a **framework pack**:

| Framework | DI mechanism | Detection source |
|---|---|---|
| Spring (Java) | XML `<bean>`, `@Autowired`/`@Inject` on fields/ctors, `@Configuration`+`@Bean` | annotations + XML config |
| Guice (Java) | `bind(Interface).to(Impl)` in modules | code patterns in Module classes |
| .NET DI | `services.AddScoped<IFoo,Foo>()` in Startup/Program | code patterns |
| NestJS (TS) | providers array + `@Injectable()` | decorator + module metadata |
| Django (Py) | settings injection / service locators | code patterns |
| (others) | per-framework | per-framework pack |

`binds` edge (Interface → Implementation) is only created when a framework pack's pattern matches. If no pack matches, no `binds` edge is created — sinan does not guess.

### 5. Honest boundary: v1 edges are name-level, not semantic-level

tree-sitter is **syntactic only** ([HN discussion](https://news.ycombinator.com/item?id=46719899); multiple sources). It does NOT do type checking, cross-file reference resolution, or scope analysis. Therefore:

- `calls` edges in v1 are **name-level + name-resolution** (match call-site name to a definition in the same file/module, or via resolved imports). Marked `resolved: name-based` with a confidence score.
- Overloads, polymorphism, dynamic dispatch → edge may be unresolved or ambiguous. Marked honestly; never silently guessed.
- LSP integration (true semantic resolution) is a **future enhancement**, explicitly NOT v1.
- Dynamic dispatch (reflection, runtime strategy selection) → LLM may infer `related_to` with confidence, but this is never a `calls` edge.

### 6. UI→API call chains — must not be missed

A complete UI→API→function chain must be captured:

1. **Frontend call site:** `fetch("/api/users")`, `axios.get("/users")`, `HttpClient.get(...)`, framework-specific (e.g. React query hooks). Extract via tree-sitter patterns → produces an `invokes` edge candidate carrying the URL pattern.
2. **Backend route registration:** `app.get("/users/:id", handler)`, `@GetMapping("/users/{id}")`, `@app.get(...)`, `[HttpGet("users/{id}")]`. Extract via framework-pack patterns → produces an `ApiEndpoint` node carrying the normalized URL pattern.
3. **Matching:** a URL-pattern normalizer reconciles `/api/users/:id` vs `/users/{id}` vs `/users/{userId}` (strip prefixes, normalize param syntax). Match → `invokes` edge (frontend symbol → `ApiEndpoint`).
4. **Continue into backend:** `ApiEndpoint` `defines`/is-handled-by a `CodeSymbol` (the handler function). That handler's `calls` edges continue the chain into business logic.

Edges involved: `invokes` (UI symbol → ApiEndpoint, matched by URL pattern), `handles`/`defined_by` (ApiEndpoint → handler CodeSymbol), `calls` (handler → deeper logic).

**Honest limit:** if the URL is a runtime-computed variable (not a string literal), tree-sitter cannot extract it. Mark unresolved; LLM may infer `related_to`.

### 7. Edge type catalog

| Edge | Meaning | Type |
|---|---|---|
| `contains` | Containment | static |
| `defines` | Defines | static |
| `calls` | Calls (**name-level + name-resolution**) | static + name-resolution |
| `references` | References (incl. `Table[Col]`/`DefinedName` resolution) | static + name-resolution |
| `implements` | Implements interface | static |
| `binds` | DI binding (Interface→Impl, framework-pack detected) | static |
| `invokes` | UI/API client → ApiEndpoint (URL-pattern matched) | static + URL-normalization |
| `handles`/`defined_by` | ApiEndpoint → handler CodeSymbol | static |
| `computes_from` | Excel formula dependency (Formula/Cell → Range) | static |
| `sources_from` | Pivot/data source chain (PivotTable→PivotCache→source Range) | static |
| `visualizes` | Chart → data source | static |
| `validates` | Validates | static |
| `describes` | Describes | static / LLM |
| `reply_to` | Email reply | static |
| `shared_with` | Excel shared formula (slave→master) | static |
| `related_to` | Semantic association | **LLM-inferred, with confidence** |

## Consequences

- **+** Excel model is complete and evidence-backed (OOXML parts + academic graph model).
- **+** tree-sitter is used to its full capability across 7 layers, not just symbol extraction.
- **+** Framework packs make injection + route detection extensible without core changes.
- **+** UI→API→function chains are first-class, answering "this dropdown shows these options because…".
- **+** Honest boundaries (name-level calls, runtime-URL gaps) prevent over-claiming.
- **−** High engineering cost: per-language query files + per-framework packs + full OOXML parser. These two areas are explicitly the top priority per user direction.
- **−** Name-level `calls` means cross-file/polymorphic call graphs are imperfect in v1. Must be surfaced to users as "name-based resolution" confidence.
- **−** Framework pack coverage determines DI/route/UI-call quality. v1 ships with a fixed set of packs (next ADR); frameworks without a pack get symbol-level only.
