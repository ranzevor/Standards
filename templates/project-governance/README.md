# 项目治理记录模板 / Project governance record template

本模板把项目自身的范围、需求、验收和保留办法落到一份记录；通用技术义务仍引用唯一规范正文。先填写事实，再运行检查。**模板不是已验收项目，也不是批准书。**

This template records project-specific facts and references the canonical standards. A filled form is neither acceptance nor an authorization.

## 开始填写 / Start here

1. 复制[起点JSON](project-record.template.json)，保留 `record_state: starter`，先填范围、问题、受众、成功条件和实际责任接口。
2. 从准确登记选择文档和条款，补齐需求、实现位置、工作项与执行前已确定的验收合同。不要从一次实际输出反填预期。
3. 补齐全部必要引用后改为 `planned`；此词仅表示合同已定义。运行 `--validate-only` 核记录，再运行[合成实例](../../examples/project-governance/README.md)验证实际行为。
4. 保存执行报告中的候选/环境/输入输出身份、原始stdout/stderr和结果。实质审查、真实采用、发行与部署各自保持自己的状态。

Copy the starter, fill factual scope and responsibilities, bind exact standards and requirements, predeclare expectations, then mark it planned. Validate the record before execution. Keep execution, independent review, adoption, release and deployment separate.

```sh
python -B examples/project-governance/project_example.py --validate-only --record templates/project-governance/project-record.template.json
python -B examples/project-governance/project_example.py --validate-only --record examples/project-governance/project-record.json
```

第一条应返回 `readiness: not-ready`，第二条应返回 `contracts-defined`、`check_aggregate: not-run`。两者均不表示运行通过。`run_example`不回写这两份JSON；实际结果只在本次报告中。

The starter is deliberately not ready. The filled record defines contracts but remains not-run. Runtime reports do not silently rewrite either file.

## 有限接口与必填规则 / Finite profile and required fields

[schema](../../registry/schemas/governance-project.schema.json)及校验器使用以下有限关键词：`type`、`required`、`additionalProperties`、`properties`、`enum`、`items`、`minLength`、`minItems`、`maxItems`、`pattern`。`maxItems` 检查数组长度上界，规范登记用它限制集合数量。校验器不是完整JSON Schema实现，没有 `$ref`、条件分支、format或数值上下界关键字。数字范围、跨字段引用、时间与状态由下述实际API承担。

The validator supports the ten listed keywords. `maxItems` limits array length, including the normative registry's document count. The executable adapter owns the implemented cross-field checks.

- 根对象及全部列出的容器均必填。表中“必填”表示父对象/数组行存在时必填；数组可在 `starter` 中为空，但 `planned` 必须有范围、成功条件、需求、合同、工作项和准确规范选择。
- “可选”不是随意丢弃事实：决定非 `not-decided` 时必须有 `actor/at/reference`；`date_kind != unset` 时必须有date；维护active时必须有实际owner。未决决定不得出现actor、时间和reference。
- ID在自己的集合内唯一；引用必须指向同份记录的准确ID。规范身份是 `document_id + version + path + sha256 + clause id`，路径不是版本，名称相同不是内容相同。
- 该运行器只有离线CSV合同，没有真实部署、公开发行或SLA实现。schema保留有限状态，而不假造完整生产治理系统；其他项目应建立对应合同及验证实现，不能只改状态骗过本示例。

All named containers are required. A required row field is mandatory whenever that row exists. Empty starter arrays do not satisfy planned readiness. Decisions and committed dates require real attribution. IDs resolve locally; standard references bind exact version, bytes and clauses. This executable profile does not implement production release, deployment or SLA management.

## 未知与失败处置 / Unknowns and failure handling

- **F0 形状或必填缺失 / Shape or missing facts：** 保留starter或原记录；补实际值后再验。没有准确摘要时不要填全零摘要，未准备的对象先不创建该行；不能把未填模板改planned。
- **F1 引用或身份失败 / Reference or identity drift：** 保留旧选择与失败，核原始对象和迁移映射；不得用latest、同名文件或事后实测摘要替代原先期望。
- **F2 结果/状态失败 / Result or state failure：** 未执行用not-run；已开始但效果未核实用unknown；只有确无触发才not-applicable。失败保留为fail，不删required项，不把partial聚合为pass；修复后另建结果。
- **F3 修订/时间冲突 / Revision or time conflict：** 重读当前对象与revision，比较差异并取得适用决定；旧历史不改写。到期例外不能自动续期。
- **F4 材料/配置失败 / Material or configuration failure：** 引用、hold、重建能力不清时保留；先核边界再计划回收。配置错误拒绝运行，不静默降级。原始不可替代失败不回收。

Unknown scalars must not be fabricated: use the enclosing explicit state, omit conditionally absent attribution, and keep the record a starter until required facts exist. F0–F4 are the recovery rules referenced below.

## 逐字段说明 / Field-by-field reference

合法值来自有限schema，语义与条件还须符合上述规则及对象专节。`string+`为非空字符串，`SHA256`为64位小写十六进制；`integer`在修订、字节和退出码处还要求非负精确整数，布尔不是整数。`[]`表示数组元素。

Values below describe the finite shape; semantic conditions still apply. `string+` means a nonempty string, SHA256 means 64 lowercase hexadecimal characters, and boolean is not integer.


### `schema_version`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `schema_version` | 记录格式版本 / Record format version | 必填 / required；`"standards-governance-project/1"` | F0 |

### `id`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `id` | 本记录稳定ID / Stable record ID | 必填 / required；`string+` | F0 |

### `record_state`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `record_state` | 填写阶段；starter不可执行，planned仍不是通过 / Filling stage, not acceptance | 必填 / required；`"starter"` / `"planned"` | F2 |

### `example_only`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `example_only` | 是否仅为合成示例 / Whether the record is synthetic-only | 必填 / required；`boolean` | F0 |

### `operation_authorized`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `operation_authorized` | 固定false；记录不产生操作授权 / Always false; no authority is granted | 必填 / required；`false` | F0 |

### `project`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `project.id` | 项目稳定ID / Stable project ID | 必填 / required；`string+` | F0 |
| `project.kind` | 合成或真实项目类别 / Synthetic or real-project category | 必填 / required；`"synthetic"` / `"real-project"` | F0 |
| `project.name` | 面向读者的项目名 / Reader-facing project name | 必填 / required；`string+` | F0 |
| `project.problem` | 受众当前可观察问题 / Observable audience problem | 必填 / required；`string+` | F0 |
| `project.audiences` | 目标受众，不是虚构成员 / Intended audiences, not invented team members | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `project.baseline.state` | 未测基线为unknown / Unmeasured baseline is unknown | 必填 / required；`"unknown"` / `"measured"` | F2 |
| `project.baseline.observation` | 已知基线或取得基线的方法 / Known baseline or how to obtain it | 必填 / required；`string+` | F0 |
| `project.outcome` | 用户可观察的业务终点 / Observable user outcome | 必填 / required；`string+` | F0 |
| `project.success_criteria[].id` | 成功条件稳定ID，供需求引用 / Success criterion ID referenced by requirements | 必填 / required；`string+` | F2 |
| `project.success_criteria[].measurement` | 判定方法和观察来源 / Measurement and observation method | 必填 / required；`string+` | F2 |
| `project.success_criteria[].window` | 实际观察窗口 / Observation window | 必填 / required；`string+` | F2 |
| `project.success_criteria[].acceptance_ids` | 证明该条件的合同ID集合 / Contract IDs for this criterion | 必填 / required；`array`（元素见schema / see schema） | F2 |
| `project.success_criteria[].state` | 当前结果；未执行为not-run / Current result; not-run before execution | 必填 / required；`"not-run"` / `"pass"` / `"fail"` / `"partial"` / `"unknown"` / `"not-applicable"` | F2 |
| `project.scope.revision` | 已知范围修订号，从0开始 / Known scope revision, initially zero | 必填 / required；`integer` | F3 |
| `project.scope.in_scope` | 范围内的稳定能力ID / In-scope capability IDs | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `project.scope.out_of_scope` | 明确排除的能力ID，不得与范围内重叠 / Disjoint excluded capability IDs | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `project.scope.history` | 模型原生旧新集合与intent记录 / Native before/after and intent history | 必填 / required；`array`（元素见schema / see schema） | F3 |
| `project.resources[].id` | 资源稳定ID / Stable resource ID | 必填 / required；`string+` | F1 |
| `project.resources[].provider` | 实际提供方或unassigned / Actual provider or unassigned | 必填 / required；`string+` | F1 |
| `project.resources[].state` | 实际可用性；未确定为unknown / Availability; unknown if unestablished | 必填 / required；`"available"` / `"unknown"` / `"unavailable"` | F2 |
| `project.resources[].allowed_use` | 该资源的具体用途 / Specific permitted resource use | 必填 / required；`string+` | F1 |
| `project.resources[].missing_impact` | 缺失时阻断的具体活动 / Activities blocked if unavailable | 必填 / required；`string+` | F1 |
| `project.roles.decision_owner` | 真实范围决定者，未分配用unassigned / Actual decision owner or unassigned | 必填 / required；`string+` | F0 |
| `project.roles.executor` | 执行接口；示例为local-example-runner / Executor interface, not approval | 必填 / required；`string+` | F0 |
| `project.roles.reviewer` | 实际审查者，未分配用unassigned / Actual reviewer or unassigned | 必填 / required；`string+` | F2 |
| `project.roles.maintainer` | 实际维护者，未分配用unassigned / Actual maintainer or unassigned | 必填 / required；`string+` | F0 |
| `project.lifecycle.state` | 阶段；accepted需必要成果已验证 / Stage; accepted requires verified necessary work | 必填 / required；`"discovery"` / `"active"` / `"blocked"` / `"accepted"` / `"retired"` | F2 |
| `project.lifecycle.entry_condition` | 当前阶段进入依据 / Current stage entry basis | 必填 / required；`string+` | F0 |
| `project.lifecycle.next_condition` | 下一阶段尚需的条件 / Conditions for the next stage | 必填 / required；`string+` | F0 |
| `project.lifecycle.unresolved` | 未决问题；空数组只表示未列未决项 / Unresolved questions, not implicit success | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `project.io_contract.encoding` | 本运行器明确支持UTF-8，不接受BOM / Runner encoding: UTF-8 without BOM | 必填 / required；`"utf-8"` | F0 |
| `project.io_contract.input_columns` | 输入准确表头与顺序 / Exact input column names and order | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `project.io_contract.output_columns` | 输出准确表头与顺序 / Exact output column names and order | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `project.io_contract.line_ending` | 输出LF；合法输入CRLF被规范化 / LF output; input CRLF is normalized | 必填 / required；`"LF"` | F0 |
| `project.io_contract.id_rule` | ID格式和唯一性规则 / ID format and uniqueness rule | 必填 / required；`string+` | F0 |
| `project.io_contract.name_rule` | name字段值约束 / Name-field value constraints | 必填 / required；`string+` | F0 |
| `project.io_contract.error_policy` | 拒绝、保留与不覆盖合同 / Rejection, preservation and no-overwrite contract | 必填 / required；`string+` | F0 |
| `project.io_contract.max_input_bytes` | 输入最大字节数，不是字符数 / Maximum input bytes, not characters | 必填 / required；`integer` | F0 |
| `project.fixtures[].id` | 合成夹具ID / Synthetic fixture ID | 必填 / required；`string+` | F0 |
| `project.fixtures[].input_text` | 逐字UTF-8合成输入 / Exact synthetic input encoded as UTF-8 | 必填 / required；`string`（可空 / may be empty） | F0 |
| `project.fixtures[].expected_output_text` | 执行前确定的逐字输出；拒绝夹具可为空 / Predeclared output; empty for rejection fixture | 必填 / required；`string`（可空 / may be empty） | F2 |

### `requirements[]`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `requirements[].id` | 需求稳定ID / Stable requirement ID | 必填 / required；`string+` | F0 |
| `requirements[].success_criterion_id` | 必须解析到成功条件ID / Reference to a success criterion ID | 必填 / required；`string+` | F1 |
| `requirements[].statement` | 可分别判断的必要行为 / Independently decidable required behavior | 必填 / required；`string+` | F2 |
| `requirements[].state` | 未决为proposed；实现不等于verified / Proposed if undecided; implemented is not verified | 必填 / required；`"proposed"` / `"accepted"` / `"implemented"` / `"verified"` / `"rejected"` / `"deferred"` | F2 |
| `requirements[].source` | 需求来源或原问题定位 / Requirement origin or problem locator | 必填 / required；`string+` | F1 |
| `requirements[].scope_id` | 必须属于project.scope.in_scope / Must belong to the project scope | 必填 / required；`string+` | F1 |
| `requirements[].design` | 本项目方案、取舍和失败责任 / Project-specific design, trade-offs and failure responsibility | 必填 / required；`string+` | F0 |
| `requirements[].implementation_path` | 仓库内实际实现相对路径 / Existing repository-relative implementation path | 必填 / required；`string+` | F1 |
| `requirements[].implementation_symbol` | 该Python文件实际顶层函数或类 / Actual top-level Python function or class | 必填 / required；`string+` | F1 |
| `requirements[].acceptance_ids` | 本需求合同ID，双向回指一致 / Contract IDs with matching reverse references | 必填 / required；`array`（元素见schema / see schema） | F1 |
| `requirements[].work_item_ids` | 承载本需求的工作项ID / Work item IDs delivering this requirement | 必填 / required；`array`（元素见schema / see schema） | F1 |

### `acceptance[]`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `acceptance[].id` | 验收合同稳定ID / Stable acceptance contract ID | 必填 / required；`string+` | F0 |
| `acceptance[].requirement_id` | 被证明需求ID；不能指向不存在项 / Requirement ID proved by this contract | 必填 / required；`string+` | F1 |
| `acceptance[].scenario` | 运行器场景名；新增场景须实现观察路径 / Runner scenario name; new scenarios need implementation | 必填 / required；`string+` | F0 |
| `acceptance[].layer` | 隔离进程与有限模型严格分层 / Isolated-runtime or finite-model evidence layer | 必填 / required；`"isolated-runtime"` / `"finite-model"` | F0 |
| `acceptance[].command` | 从仓库根执行的入口 / Reproduction command from repository root | 必填 / required；`string+` | F0 |
| `acceptance[].expectation_origin` | 独立期望依据，不得由actual反填 / Independent expectation origin, never copied from actual | 必填 / required；`"requirement"` / `"protocol"` / `"pre-registered-hypothesis"` | F0 |
| `acceptance[].expected_exit` | 预期进程退出码或有限模型适配结果码 / Expected process exit or finite-model adapter code | 必填 / required；`integer` | F2 |
| `acceptance[].expected_value` | 有限JSON对象，执行前固定且完整相等比较 / Predeclared finite JSON object, compared in full | 必填 / required；`object`（有限JSON / finite JSON） | F2 |
| `acceptance[].failure_reason` | 违反合同时的直接原因 / Direct cause when the contract is violated | 必填 / required；`string+` | F0 |
| `acceptance[].recovery` | 具体保全、修复与重跑步骤 / Preservation, correction and rerun steps | 必填 / required；`string+` | F0 |

### `work_items[]`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `work_items[].id` | 工作项稳定ID / Stable work item ID | 必填 / required；`string+` | F0 |
| `work_items[].type` | 实际工作分类 / Actual work category | 必填 / required；`"feature"` / `"defect"` / `"research"` / `"documentation"` / `"maintenance"` / `"security"` | F0 |
| `work_items[].owner` | 实际执行接口或unassigned / Executor interface or unassigned | 必填 / required；`string+` | F0 |
| `work_items[].revision` | 已知工作项修订号 / Known work item revision | 必填 / required；`integer` | F3 |
| `work_items[].state` | 当前状态，不因合并而自动关闭 / Current state; merging does not imply closure | 必填 / required；`"open"` / `"triaged"` / `"in-progress"` / `"blocked"` / `"verification"` / `"closed"` | F2 |
| `work_items[].resolution` | 未关闭为null；关闭理由不全表示已验证 / Null before closure; not all resolutions mean verified | 必填 / required；`null` / `"verified-fix"` / `"verified-delivery"` / `"not-reproducible"` / `"rejected"` / `"duplicate"` | F2 |
| `work_items[].acceptance_ids` | 精确当前接受条件ID / Exact current acceptance IDs | 必填 / required；`array`（元素见schema / see schema） | F1 |
| `work_items[].dependencies` | 必要工作项依赖ID，不是导航链接 / Required work item dependencies, not navigation | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `work_items[].history[].from` | 前一工作状态 / Previous work state | 必填 / required；`string+` | F3 |
| `work_items[].history[].to` | 本次新工作状态 / New work state | 必填 / required；`string+` | F3 |
| `work_items[].history[].revision` | 本次连续修订号 / Sequential revision for this transition | 必填 / required；`integer` | F3 |
| `work_items[].history[].reason` | 非验证关闭或恢复的具体理由 / Reason for nonverified closure or recovery | 条件可选 / conditional；`string+` | F3 |

### `milestone`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `milestone.id` | 里程碑稳定ID / Stable milestone ID | 必填 / required；`string+` | F0 |
| `milestone.goal` | 必要成果与可观察终点 / Necessary deliverables and observable endpoint | 必填 / required；`string+` | F0 |
| `milestone.required_ids` | 必要根工作项；判定包含传递闭包 / Required roots including their transitive closure | 必填 / required；`array`（元素见schema / see schema） | F1 |
| `milestone.date_kind` | 未设、估计或真实承诺 / Unset, estimated or actually committed date | 必填 / required；`"unset"` / `"estimate"` / `"committed"` | F0 |
| `milestone.date` | 仅非unset时填写实际日期/窗口 / Date or window only when date_kind is not unset | 条件可选 / conditional；`string+` | F0 |
| `milestone.state` | 当前结果，不以百分比替代必要闭包 / State, not a percentage replacing required closure | 必填 / required；`"not-run"` / `"partial"` / `"pass"` / `"blocked"` | F2 |

### `change`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `change.id` | 变更稳定ID / Stable change ID | 必填 / required；`string+` | F0 |
| `change.type` | 按行为风险分类，不按行数 / Behavior-based risk category, not line count | 必填 / required；`"behavior"` / `"editorial"` / `"interface"` / `"security"` | F0 |
| `change.reason` | 改动原因与所解决问题 / Reason for the change and addressed problem | 必填 / required；`string+` | F0 |
| `change.base_identity` | 准确旧对象或明确无旧发行 / Exact baseline or explicitly no prior release | 必填 / required；`string+` | F1 |
| `change.candidate_identity_state` | 执行时捕获摘要或尚未解析 / Identity captured at execution or unresolved | 必填 / required；`"capture-at-execution"` / `"unresolved"` | F2 |
| `change.author_review` | 作者自查结果，不冒充独审 / Author self-review result, not independent review | 必填 / required；`"not-run"` / `"pass"` / `"fail"` / `"partial"` / `"unknown"` / `"not-applicable"` | F2 |
| `change.independent_review` | 独立审查结果；合成记录固定not-run / Independent review result; synthetic profile is not-run | 必填 / required；`"not-run"` / `"pass"` / `"fail"` / `"partial"` / `"unknown"` / `"not-applicable"` | F2 |
| `change.review_units` | 应审技术范围单元ID / Technical units requiring review | 必填 / required；`array`（元素见schema / see schema） | F2 |
| `change.findings[].id` | 发现稳定ID / Stable finding ID | 必填 / required；`string+` | F0 |
| `change.findings[].state` | 未修、部分修复或完整关闭 / Open, partial or closed finding | 必填 / required；`"open"` / `"partial"` / `"closed"` | F2 |
| `change.findings[].criteria` | 预先列出的全部修复判据ID / Complete predeclared closure criteria | 必填 / required；`array`（元素见schema / see schema） | F2 |
| `change.findings[].closed_criteria` | 实际已核判据的子集 / Actually rechecked subset of closure criteria | 必填 / required；`array`（元素见schema / see schema） | F2 |
| `change.findings[].blocking` | 该发现是否阻断进入下一阶段 / Whether the finding blocks the next stage | 必填 / required；`boolean` | F2 |
| `change.merge_state` | 合并实际状态，本例not-applicable / Actual merge state; not applicable here | 必填 / required；`"not-run"` / `"not-applicable"` / `"unknown"` | F2 |
| `change.recovery` | 保留旧候选/失败并复验的路径 / Preserve baseline/failure and revalidate | 必填 / required；`string+` | F0 |

### `checks`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `checks.required_ids` | 全部必要合同ID；本profile须与acceptance完全一致 / Exact necessary contract set | 必填 / required；`array`（元素见schema / see schema） | F1 |
| `checks.results[].id` | 对应验收合同ID / Acceptance contract ID | 必填 / required；`string+` | F0 |
| `checks.results[].state` | 观察状态；失败、未知、缺失不可抹除 / Observed state; do not erase failures or unknowns | 必填 / required；`"not-run"` / `"pass"` / `"fail"` / `"partial"` / `"unknown"` / `"not-applicable"` | F2 |
| `checks.results[].candidate_sha256` | 被测 source_identity 的canonical SHA256 / Canonical digest of the tested source_identity | 必填 / required；`SHA256` | F1 |
| `checks.results[].evidence` | 原始观察定位集合，不是pass字符串 / Raw observation locators, not a pass label | 必填 / required；`array`（元素见schema / see schema） | F0 |

### `dependencies`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `dependencies.tools[].name` | 实际工具名称 / Actual tool name | 必填 / required；`string+` | F0 |
| `dependencies.tools[].version_rule` | 支持/匹配策略，不假称上游锁定 / Version policy, not an invented upstream lock | 必填 / required；`string+` | F0 |
| `dependencies.tools[].resolution_state` | 运行前not-run，观察后observed / Not-run before observation, observed afterwards | 必填 / required；`"not-run"` / `"observed"` | F2 |
| `dependencies.tools[].source` | 取得入口与信任边界 / Acquisition source and trust boundary | 必填 / required；`string+` | F1 |
| `dependencies.records[].id` | 已选规范的document_id / Selected standard document ID | 必填 / required；`string+` | F0 |
| `dependencies.records[].kind` | 依赖类别；本profile实际解析standard / Dependency kind; this adapter resolves standards | 必填 / required；`"runtime"` / `"development"` / `"optional"` / `"service"` / `"standard"` | F0 |
| `dependencies.records[].purpose` | 必要消费用途 / Required consumption purpose | 必填 / required；`string+` | F0 |
| `dependencies.records[].source` | 准确来源坐标，不是latest / Exact source coordinate, never latest | 必填 / required；`string+` | F1 |
| `dependencies.records[].path` | 实际本地依赖文件路径 / Existing local dependency path | 必填 / required；`string+` | F1 |
| `dependencies.records[].locked_version` | 预先选定版本；与登记解析值比较 / Preselected version compared with registry resolution | 必填 / required；`string+` | F0 |
| `dependencies.records[].expected_sha256` | 预先选定完整内容摘要 / Preselected complete-content digest | 必填 / required；`SHA256` | F2 |
| `dependencies.package_dependencies` | 额外包依赖；本例为空且不安装包 / Extra packages; empty in this standard-library example | 必填 / required；`array`（元素见schema / see schema） | F0 |

### `configuration`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `configuration.defaults.encoding` | 最低优先级编码默认 / Lowest-precedence encoding default | 条件可选 / conditional；`string+` | F4 |
| `configuration.defaults.max_input_bytes` | 最低优先级输入大小默认 / Lowest-precedence byte limit | 条件可选 / conditional；`integer` | F4 |
| `configuration.environment.encoding` | 显式传入的环境层编码覆盖，不读取秘密 / Explicit environment-layer override, no secret reads | 条件可选 / conditional；`string+` | F4 |
| `configuration.environment.max_input_bytes` | 环境层字节上限覆盖 / Environment-layer byte-limit override | 条件可选 / conditional；`integer` | F4 |
| `configuration.command_line.encoding` | 最高优先级编码覆盖 / Highest-precedence encoding override | 条件可选 / conditional；`string+` | F4 |
| `configuration.command_line.max_input_bytes` | 最高优先级字节上限 / Highest-precedence byte-limit override | 条件可选 / conditional；`integer` | F4 |
| `configuration.precedence` | 固定合并顺序 / Fixed configuration merge order | 必填 / required；`["default","environment","command-line"]` | F4 |
| `configuration.secret_state` | 本profile无秘密 / No secrets in this profile | 必填 / required；`"not-applicable"` | F4 |
| `configuration.reason` | 没有秘密/外部服务的业务原因 / Business reason for no secret or service configuration | 必填 / required；`string+` | F4 |

### `materials`

仅填写实际保留、回收或例外处理对象；目录和材料类型的通用规则由项目政策说明。文件版本由Git管理，发行完整文件清单在构建时生成。

Record only actual retention, reclamation or exception objects. Project policy defines general directory and material-type rules; Git manages file versions, and builds generate complete release manifests.

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `materials.revision` | 当前引用快照修订号 / Current reference snapshot revision | 必填 / required；`integer` | F4 |
| `materials.active_ids` | 活动材料根ID，保护传递依赖 / Active roots protecting transitive dependencies | 必填 / required；`array`（元素见schema / see schema） | F4 |
| `materials.records[].id` | 材料稳定ID / Stable material ID | 必填 / required；`string+` | F4 |
| `materials.records[].path` | 精确相对路径，不能绝对/逃逸 / Exact safe relative path | 必填 / required；`string+` | F4 |
| `materials.records[].kind` | 按实际用途分类，不按目录名 / Actual material class, not directory name | 必填 / required；`"source"` / `"formal-document"` / `"formal-delivery"` / `"irreplaceable-evidence"` / `"reproducible-build"` / `"dependency"` / `"cache"` / `"temporary"` | F4 |
| `materials.records[].bytes` | 实际完整字节数 / Actual full byte count | 必填 / required；`integer` | F4 |
| `materials.records[].sha256` | 实际完整字节SHA256 / Digest of the actual full bytes | 必填 / required；`SHA256` | F4 |
| `materials.records[].dependencies` | 必要材料ID边 / Required material dependency IDs | 必填 / required；`array`（元素见schema / see schema） | F4 |
| `materials.records[].holds` | 保留hold及调查原因 / Retention holds and investigation reasons | 必填 / required；`array`（元素见schema / see schema） | F4 |
| `materials.records[].rebuild_inputs_available` | 必要重建输入实际可得 / Whether necessary rebuild inputs are actually available | 必填 / required；`boolean` | F4 |
| `materials.records[].rebuild_command` | 已建立的重建入口；不可重建时可空 / Established rebuild command, empty if not reconstructable | 必填 / required；`string`（可空 / may be empty） | F4 |
| `materials.retention` | 源码、输入、正式成果和原始证据保留办法 / Source, input, deliverable and raw-evidence retention | 必填 / required；`string+` | F4 |
| `materials.cleanup_state` | 清理未执行或确实不适用 / Cleanup not-run or genuinely not applicable | 必填 / required；`"not-run"` / `"not-applicable"` | F4 |

### `version`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `version.candidate` | 本地候选版本标识，不是已发行事实 / Local candidate identifier, not a release fact | 必填 / required；`string+` | F0 |
| `version.scheme` | 版本标识对象及兼容语义 / Versioned object and compatibility scheme | 必填 / required；`string+` | F0 |
| `version.compatibility` | 实际格式/平台支持边界及未验范围 / Actual compatibility and untested scope | 必填 / required；`string+` | F0 |
| `version.preparation_state` | 未执行、可审或阻塞，不含ready-to-publish / Not-run, ready-for-review or blocked, never publish approval | 必填 / required；`"not-run"` / `"ready-for-review"` / `"blocked"` | F2 |
| `version.required_checks` | 发行准备必要检查，保持原必要集合 / Release-preparation checks preserving necessary scope | 必填 / required；`array`（元素见schema / see schema） | F0 |
| `version.publication_state` | 未执行、不适用或结果未知 / Not-run, not-applicable or unknown publication | 必填 / required；`"not-run"` / `"not-applicable"` / `"unknown"` | F2 |
| `version.distribution_state` | 真实分发决定未定或不适用 / Distribution undecided or not applicable | 必填 / required；`"not-decided"` / `"not-applicable"` | F2 |
| `version.license_state` | 实际许可范围未定或不适用 / License scope undecided or not applicable | 必填 / required；`"not-decided"` / `"not-applicable"` | F2 |
| `version.tag_state` | 真实标签操作未执行或不适用 / Tag operation not-run or not applicable | 必填 / required；`"not-run"` / `"not-applicable"` | F2 |
| `version.reason` | 本地候选和未分发的具体理由 / Reason for local candidate and no distribution | 必填 / required；`string+` | F0 |

### `adoption`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `adoption.revision` | 采用选择当前revision / Current adoption-selection revision | 必填 / required；`integer` | F3 |
| `adoption.state` | 项目采用轴；与decision分别一致为not-decided/approved/rejected/withdrawn，不由检查推导 / Project adoption axis; decision must respectively be not-decided/approved/rejected/withdrawn, never inferred from checks | 必填 / required；`"not-decided"` / `"adopted"` / `"rejected"` / `"withdrawn"` | F2 |
| `adoption.scope_ids` | 采用能力范围，必须为in_scope非空子集 / Nonempty subset of project scope when planned | 必填 / required；`array`（元素见schema / see schema） | F1 |
| `adoption.decision.state` | 未决定不生成批准人和日期 / Undecided state must not invent attribution | 必填 / required；`"not-decided"` / `"approved"` / `"rejected"` / `"withdrawn"` | F2 |
| `adoption.decision.actor` | 有实际决定时的主体 / Actor only for an actual decision | 条件可选 / conditional；`string+` | F0 |
| `adoption.decision.at` | 实际决定的带时区ISO时间 / Actual timezone-aware decision timestamp | 条件可选 / conditional；`string+` | F3 |
| `adoption.decision.reference` | 可查的原始决定定位 / Traceable original decision reference | 条件可选 / conditional；`string+` | F0 |
| `adoption.selections[].document_id` | 唯一登记的规范ID / Unique registered standard ID | 必填 / required；`string+` | F1 |
| `adoption.selections[].version` | 准确版本，不接受latest / Exact version, never latest | 必填 / required；`string+` | F1 |
| `adoption.selections[].path` | 唯一正文当前相对路径 / Canonical document path | 必填 / required；`string+` | F1 |
| `adoption.selections[].sha256` | 该版本实际完整字节身份 / Full-byte identity of the selected object | 必填 / required；`SHA256` | F1 |
| `adoption.selections[].selection` | 参考、试用与真实采用分开 / Reference, trial and actual adoption are distinct | 必填 / required；`"technical-reference"` / `"trial"` / `"adopted"` | F1 |
| `adoption.selections[].clauses[].id` | 该文实际条款ID / Actual clause ID in that document | 必填 / required；`string+` | F1 |
| `adoption.selections[].clauses[].applicability` | 触发、未触发或事实未确定 / Applicable, not applicable or undetermined | 必填 / required；`"applicable"` / `"not-applicable"` / `"undetermined"` | F1 |
| `adoption.selections[].clauses[].reason` | 具体触发或缺失事实，不用未测冒充不适用 / Factual applicability reason, not lack of testing | 必填 / required；`string+` | F1 |
| `adoption.selections[].clauses[].acceptance_ids` | 有限自动合同ID；IDs=acceptance_ids、scope=automated_scope，实际条款/合同关联及人工状态由同一profile核验 / Finite automated contract IDs; IDs=acceptance_ids and scope=automated_scope; the same profile checks actual clause/contract relations and manual state | 必填数组；IDs为空时：IDs长度≥0、scope长度≤0；IDs非空时：IDs长度≥1、scope长度≥1；人工准则≥1且逐项非空 / Required array; when IDs are empty: IDs length≥0, scope length≤0; when IDs are nonempty: IDs length≥1, scope length≥1; at least 1 nonblank manual criterion | F1 |
| `adoption.exceptions[].id` | 例外稳定ID；没有例外则数组为空 / Stable exception ID; empty array when none | 必填 / required；`string+` | F0 |
| `adoption.exceptions[].requirement_id` | 准确项目需求ID / Exact project requirement ID | 必填 / required；`string+` | F1 |
| `adoption.exceptions[].document_sha256` | 被引用准确规范字节 / Exact selected standard digest | 必填 / required；`SHA256` | F1 |
| `adoption.exceptions[].scope` | 例外作用的范围ID / Scope ID affected by the exception | 必填 / required；`string+` | F0 |
| `adoption.exceptions[].reason` | 风险和不能满足原要求的原因 / Risk and reason for the deviation | 必填 / required；`string+` | F0 |
| `adoption.exceptions[].state` | 缺真实决定时为proposed / Proposed without an actual decision | 必填 / required；`"proposed"` / `"approved"` / `"rejected"` / `"expired"` / `"withdrawn"` | F2 |
| `adoption.exceptions[].starts_at` | 含时区起始时间 / Inclusive timezone-aware start | 必填 / required；`string+` | F3 |
| `adoption.exceptions[].expires_at` | 含时区到期时间，排他上界 / Exclusive timezone-aware expiry | 必填 / required；`string+` | F3 |
| `adoption.exceptions[].review_triggered` | 复核条件是否已触发 / Whether reassessment has been triggered | 必填 / required；`boolean` | F2 |
| `adoption.exceptions[].compensations[].id` | 补偿措施稳定ID / Stable compensating-control ID | 必填 / required；`string+` | F0 |
| `adoption.exceptions[].compensations[].state` | 补偿实测状态；未执行为not-run / Observed compensation result; not-run initially | 必填 / required；`"not-run"` / `"pass"` / `"fail"` / `"partial"` / `"unknown"` / `"not-applicable"` | F2 |
| `adoption.exceptions[].recovery` | 恢复原要求或重新决定的步骤 / Restore compliance or obtain a new decision | 必填 / required；`string+` | F0 |
| `adoption.exceptions[].decision.state` | 例外决定状态，与例外有效性区分 / Decision state, distinct from exception validity | 必填 / required；`"not-decided"` / `"approved"` / `"rejected"` / `"withdrawn"` | F2 |
| `adoption.exceptions[].decision.actor` | 实际决定主体 / Actual decision actor | 条件可选 / conditional；`string+` | F0 |
| `adoption.exceptions[].decision.at` | 实际决定时间 / Actual decision timestamp | 条件可选 / conditional；`string+` | F3 |
| `adoption.exceptions[].decision.reference` | 原始例外决定定位 / Original exception decision locator | 条件可选 / conditional；`string+` | F0 |
| `adoption.history` | 保留旧选择和升级原因，不覆写历史 / Retained prior selections and upgrade rationale | 必填 / required；`array`（元素见schema / see schema） | F3 |

### `maintenance`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `maintenance.state` | 实际维护能力；未定为undecided / Actual maintenance capability; undecided if unknown | 必填 / required；`"active"` / `"limited"` / `"unmaintained"` / `"retired"` / `"undecided"` | F2 |
| `maintenance.response_hours` | 本有限profile只接受null，不承诺SLA / This finite profile accepts null only; no SLA | 必填 / required；`null` | F0 |
| `maintenance.channel_configured` | 渠道是否实际配置，不由文本推断 / Whether a channel is actually configured | 必填 / required；`boolean` | F0 |
| `maintenance.actual_owner` | active时必需的真实维护者 / Actual owner required for active maintenance | 条件可选 / conditional；`string+` | F0 |
| `maintenance.commitment_reference` | 有响应承诺才需真实依据；本profile不承诺 / Actual commitment reference when applicable | 条件可选 / conditional；`string+` | F0 |
| `maintenance.supported_versions` | 实际支持版本集合；未知时为空且状态undecided / Supported versions; empty when undecided | 必填 / required；`array`（元素见schema / see schema） | F0 |

### `deployment`

| 字段 / Field | 语义 / Meaning | 触发与合法值 / Required and values | 失败处置 / Recovery |
|---|---|---|---|
| `deployment.applicability` | 无运行环境可not-applicable；未确定用undetermined / Not applicable with no target, otherwise undetermined | 必填 / required；`"not-applicable"` / `"undetermined"` | F0 |
| `deployment.reason` | 无部署目标或缺失事实的具体原因 / Concrete reason for no target or unknown applicability | 必填 / required；`string+` | F0 |
| `deployment.execution_state` | 不适用与未执行分别表达 / Distinct not-applicable and not-run states | 必填 / required；`"not-run"` / `"not-applicable"` | F2 |

## 对象间合同与准确边界 / Cross-object contracts and precise limits

### 追溯与范围 / Traceability and scope

`validate_record(record, root=ROOT)`先用schema校形状，再核范围集合不重叠、需求⇄合同⇄工作项、成功条件覆盖、实现符号存在及必要工作闭包。`checks.required_ids`必须与acceptance全部ID完全一致；里程碑必要传递闭包必须覆盖记录内所有工作项。本有限profile不支持把必需工作静默转为可选。`adoption.scope_ids`可以是项目范围非空子集，但不能跨入排除项。正文内容是否充分、需求必要性和负责人是否真实仍须实读。

The adapter validates exact links, implementation symbols and necessary closure. Adoption may select a nonempty subset, never excluded scope. Semantic sufficiency and real responsibilities still need substantive review.

### 状态、历史与例外 / State, history and exceptions

`transition_item(item, target, expected_revision, **kwargs)`包装现有 `transition_work_item`，增加预期revision比较、连续revision和旧新状态记录。合法边为open→triaged→in-progress→verification→closed，in-progress↔blocked、verification→in-progress、closed→triaged。verified关闭必须从verification进入并具有准确全体条件的pass；not-reproducible不算已验证交付。`reason`用于非验证关闭；历史事件不能自动证明现实工作已发生。

`project.scope.history`的模型原生行是 `intent_id/intent_sha256/revision/before/after`，before和after各含in_scope/out_of_scope；`adoption.history`保留旧selection对象。schema只要求这两种history为对象数组，适配器不作完整事件溯源重放。范围更新用 `apply_scope_change`，采用升级用 `upgrade_adoption`；后者不检查项目采用范围，因此必须另外调用 `validate_adoption_scope`。二者的approved字段是有限记录条件，不认证真实决定。

例外缺决定时用proposed，不能靠 `exception_valid` 之外的文字宣称有效。该模型只核有限时间/状态/补偿；本适配器核引用与起止顺序，不自动判风险可豁免、不执行例外批准，也不把拟议补偿记pass。填妥实例没有例外，`exceptions: []`，PGN-04选择行记录不触发原因。

The work wrapper checks expected revisions and preserves transitions. Native scope/adoption histories remain finite object arrays, not fully replayed event logs. Adoption scope needs its own adapter because the upgrade model does not check it. Proposed exceptions are not approvals; no exception is needed in the bundled example.

### 检查、证据与发行 / Checks, evidence and release

静态记录results为空，表示尚未执行；执行报告给 `observations[].contract/event/state` 和 `checks[]`。CSV事件的exit_code是真实子进程退出码，有限模型事件则为本地函数的适配结果码；两层不能混称产品部署。`evaluate_observation`调用现有 `evaluate_check`，后者以 `finite_schema.json_equal` 比较完整JSON类型和值，拒绝0/false和1/true类型混同；`aggregate_checks`保留missing/fail/unknown区别。记录适配器核结果形状、必要集合、当前候选身份和非空证据定位，**不认证证据真伪、不读取任意外部证据、不以填写pass认证真实项目通过**。运行器捕获实际候选的 `source_identity` 和环境，并在执行后重新取得来源身份进行比较。

Git工作区的 `source_identity` 包含 `kind: git`、`object_format`、`base_commit` 和 `tree`；`tree`包含实际待测修改，`base_commit`在新仓尚无提交时为null。发行包包含 `kind: release-bundle`、`bundle_kind`、`version`、`source_tree_sha256` 和 `manifest_sha256`，由实际包校验取得。`candidate_sha256`是该身份描述的canonical SHA256；`record_canonical_sha256`另行绑定运行时输入记录。报告的 `cwd`是实际源码根目录。

For a Git worktree, source identity contains the actual candidate tree, object format and baseline commit, which is null for an unborn repository. For a verified release bundle, it contains bundle kind, version, source-tree digest and manifest digest. The canonical digest of this identity binds results; runtime record identity is separate. Uncommitted changes are valid candidates, and the report records the actual source root as cwd.

`change`记录实际自查和未审范围；本合成记录不得把独审改为pass。`version.preparation_state`最多ready-for-review；许可证/分发未定不会被运行通过替代。`release_ready`是另一个有明确发行前提的有限模型，本例没有这些真实事实；GOV-17仅在明确合成记录上检验正常及失败边界，不将其approved-scope输入写为项目的实际批准。

Static results are empty. Runtime reports bind actual subprocess exits or explicitly finite-model adapter codes to contracts and identities. The observation adapter delegates to the shared model’s type-sensitive JSON equality; 0 and false are distinct. Record consistency does not authenticate evidence. Ready-for-review is not ready-to-publish; no fictitious review, distribution or license approval is supplied.

### 配置、材料和模板适配 / Configuration, materials and adaptation

配置按default < environment < command-line合并。本例环境层是JSON中的显式对象，不遍历系统环境变量。编码只支持utf-8；输入上限为1到1048576字节，配置最终值须与io_contract一致。Python精确版本在运行报告观察，不冒充经过上游签名核验的工具锁定；标准正文依赖则用先定版本/摘要与实际解析值比较。

材料计划使用 `reclaim_plan`，自身始终dry-run、files_deleted=0。合成运行器只在所有句柄关闭、必要观察已提取且活动引用release到新revision后，由临时目录所有者回收自己创建的数据；报告保留计划与实际目录不存在的读回。该行为不扩展到用户文件。schema允许材料分类，但分类真实性和重建可用性不能靠布尔自证。

模板沿用CSV演示profile的IO字段以便跟跑，不是给所有项目强加CSV、UTF-8或大小上限。换成其他类型项目时，应先定义它自己的合同、schema适配与运行器；不能把示例参数直接当通用规范。

Configuration is explicit and ordered. Dependency checks distinguish observed interpreter versions from preselected standard bytes. Reclamation models only plan; the example separately releases its own synthetic temporary directory after evidence extraction. Profile-specific CSV parameters are examples, not universal project requirements.

## 有限证明与必要规范接口字段 / Finite proof and required-standard fields

| 字段 / Field | 语义与必填触发 / Meaning and required condition | 合法值与失败处置 / Values and recovery |
|---|---|---|
| `acceptance[].proves` | 每个planned合同必填；运行场景实际检查的稳定有限谓词 / Required finite predicates actually exercised by the scenario | 非空唯一字符串数组；须匹配实现的scenario能力；错误映射先修合同，不改实际输出迎合期望 / Nonempty unique strings matching the implemented scenario |
| `adoption.selections[].clauses[].automated_scope` | 每条选择必填；本条实际被自动检查的有限部分 / Exact automated subset for each selected clause | 唯一字符串数组，可空；非空项须同时属于条款能力和所连合同的proves / Unique strings, possibly empty, supported by both clause and check |
| `adoption.selections[].clauses[].manual_criteria` | 每条选择必填；剩余技术充分性、真实事实及不适用理由的具体核读对象 / Concrete remaining manual criteria | 至少一项非空字符串；不能只写“人工确认完整” / One or more specific criteria |
| `adoption.selections[].clauses[].manual_state` | 每条选择必填；人工核读结果，与自动pass分开 / Separate manual result | not-run/pass/fail/unknown；合成实例只允许not-run / Synthetic examples retain not-run |
| `adoption.selections[].clauses[].manual_evidence` | 每条选择必填；原始人工核读对象定位 / Manual observation locators | 字符串数组；not-run必须为空，其他状态须实际非合成证据 / Empty when not-run; actual nonsynthetic evidence otherwise |
| `adoption.dependency_bindings[].from_document` | 每条必要消费边必填；当前选择的消费文档ID / Required consumer ID | 当前准确文档ID；缺边或多边拒绝 / Exact selected consumer |
| `adoption.dependency_bindings[].from_clause` | 消费条款局部ID / Consumer clause | 当前已选择条款；不把所有链接当必要边 / Exact selected clause |
| `adoption.dependency_bindings[].to_document` | 提供必要保证的规范ID / Provider document | 必须对应当前必要图端点 / Match the current required graph |
| `adoption.dependency_bindings[].to_clause` | 提供保证的准确条款 / Provider clause | applies时须已选择且applicable / Selected and applicable when triggered |
| `adoption.dependency_bindings[].interface` | 所消费的有限保证 / Named consumed guarantee | 与当前必要图逐字一致 / Exact declared interface |
| `adoption.dependency_bindings[].condition` | 何时需要此保证 / Trigger condition | 与当前必要图逐字一致；条件变化复核 / Exact current condition |
| `adoption.dependency_bindings[].applicability` | 当前条件判断 / Trigger classification | applies/not-triggered/undetermined；消费方不适用时not-triggered，未知时undetermined / Keep unresolved conditions unresolved |
| `adoption.dependency_bindings[].reason` | 本项目实际触发或未触发的对象与事实 / Project-specific factual reason | 非空具体文字；真实性人工审查，不由字符串存在认证 / Specific reason, reviewed rather than authenticated by presence |

没有自动能力的合法条款可以给空`acceptance_ids`与`automated_scope`，但必须有具体人工准则与未验状态；不能借任意一个已通过合同表示全条符合。对适用接口的提供方、逐条适用事实、完整自然语言义务及原始证据真实性的审查分别保存。

A legitimate manual-only clause has empty automated mappings, explicit criteria and a truthful pending result. Do not attach an unrelated passed test as a claim of complete compliance. Preserve exact provider identity, applicability reasoning, substantive review and original evidence separately.

## 条款证明字段条件 / Clause-proof field conditions

`acceptance_ids`、`automated_scope`和`manual_criteria`的数量条件来自同一可执行条件合同：[字段条件实现](../../checks/governance_field_conditions.py)。`IDs=[]`分支允许合法manual-only空映射；非空IDs分支要求明确scope，所有分支保留逐项非空人工准则。实际合同关联、条款允许范围及人工状态/证据继续由同一profile检查。

The cardinality conditions for these three sibling fields come from the same executable condition contract. The empty-IDs branch permits a valid manual-only mapping; mapped IDs require an explicit scope, and every branch retains nonblank manual criteria. The same profile separately validates actual contracts, allowed clause predicates and manual status/evidence.

`python -m checks.governance_field_conditions`比较这一个字段行与结构化条件的受控生成结果，不解析任意自然语言的充分性。语义回归把合法manual-only、缺人工准则、错合同和合法自动映射输入真实适配器；把manual-only最小ID数改为1的变异必须在合法输入的目标断言失败。

The command checks this generated row against structured conditions, not arbitrary prose meaning. Semantic regressions execute the real adapter on manual-only, missing-criteria, unrelated-check and mapped cases; a well-formed policy mutation requiring one manual-only ID must fail the legal-input assertion.
