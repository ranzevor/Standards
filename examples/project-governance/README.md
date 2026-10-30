# 合成离线CSV项目 / Synthetic offline CSV project

把UTF-8 CSV的 `name,id` 列顺序转成 `id,name`；原输入保持原字节，坏行整批拒绝，已有输出绝不覆盖。这个小项目展示从立项、需求与工作项，到实际执行、证据和本地候选准备的一条可跟随路径。

Convert UTF-8 CSV columns from `name,id` to `id,name`. Keep the input unchanged, reject malformed batches without partial output, and never replace an existing target. This example links project records to actual local execution.

## 三步跟跑 / Three steps

在源码根目录使用Python 3.12及以上版本和标准库。Git工作区运行需要可执行的Git，以捕获包含未提交修改的候选tree；正式Source或Agent Skill包解压后，运行器使用随包完整性清单，可在没有Git的环境离线执行：

```sh
python -B examples/project-governance/project_example.py --validate-only
python -B examples/project-governance/project_example.py
python -B -m unittest tests.test_project_governance_example -v
```

1. 第一条核[填妥记录](project-record.json)与[有限schema](../../registry/schemas/governance-project.schema.json)，应得到 `contracts-defined` 与 `check_aggregate: not-run`。这是预设合同，不是静态“pass报告”。
2. 第二条在独占临时合成目录创建夹具，启动真实Python子进程转换，保存输入输出摘要和stdout/stderr，再调用有限治理模型比较结果。退出0要求全部预设合同为pass；故意的业务拒绝进程退出2仍可符合负例合同。
3. 第三条检验解析、记录语义、坏例、合法邻例、错误变异、竞争和恢复；方法数不等于场景数，更不等于真实项目或平台覆盖。

The first command validates a planned record, not execution. The second executes all predeclared contracts in a private temporary directory and prints a fresh report. The third runs direct and mutation tests. Python uses only the standard library. A Git worktree requires an executable Git to capture the candidate tree, including uncommitted changes; the runner in an extracted official Source or Agent Skill bundle uses the included integrity manifest and can run offline without Git.

运行器不读取用户数据、凭据或环境秘密，也不创建远端对象。临时输入由记录内字符串生成；转换完成或拒绝后，先提取必要观察、关闭句柄并释放活动引用，再回收临时目录。记录文件不会被结果回写。若需要保留本次报告，可将stdout保存到一个**尚不存在**的本地文件，并保留独立stderr及外层命令退出码。

The runner uses only embedded synthetic data. It captures observations and releases references before cleaning its own temporary directory. It never rewrites the planned record. Preserve stdout, stderr and the outer process exit separately when retaining evidence.

## 实际业务合同 / Actual conversion contract

| 项目 / Property | 合同 / Contract |
|---|---|
| 编码 / Encoding | UTF-8严格解码，无BOM；非法字节拒绝 / Strict UTF-8, no BOM; reject invalid bytes |
| 输入 / Input | 表头必须为name,id，顺序准确，每行恰好两列 / Exact header and two fields per row |
| 输出 / Output | id,name，UTF-8、LF；不裁剪合法字段值 / UTF-8, LF, exact values preserved |
| ID | 正十进制整数，无前导零，文件内唯一 / Positive decimal, no leading zeros, unique per file |
| name | 非空白，不含NUL；允许引号、逗号、内嵌换行 / Nonblank, no NUL; quoted commas/newlines allowed |
| 空数据 / Empty data | 只有合法表头的CSV合法，输出仅规范表头 / Header-only CSV is a legal neighbor |
| 大小 / Size | 最多1048576输入字节；先做有界读取 / At most 1 MiB, bounded read first |
| 失败 / Failure | 全量解析和预期输出身份核对后才提交；坏行不产生部分文件 / Parse and verify before committing |
| 已有文件 / Existing files | 同路径、符号链接、已有目标或提交竞争均不覆盖 / No overwrite on aliases, existing targets or races |

提交步骤：在目标目录写完整临时文件，flush/fsync，复核输入未改变，再用 `os.link` 原子创建一个此前不存在的目标，最后移除临时名字。没有“先删旧目标再写”的窗口，也没有覆盖性rename。文件系统不支持硬链接时明确返回 `commit-unavailable`，保留输入与既有文件。

The writer stages complete bytes, flushes/fsyncs, rechecks the input, then creates the target with an atomic no-replace hard link. Unsupported commits fail explicitly. This is not a crash-durability guarantee for a whole filesystem, nor a lock against arbitrary external writers; the supplied runtime owns its temporary directory. Process crashes, network filesystems, power loss and Windows execution have not been established by this example.

## 立项到结果 / From project initiation to results

| 记录位置 / Selector | 本例事实与动作 / Facts and action |
|---|---|
| project | 基线效率unknown，目标为正确转换/明确拒绝，非目标为云同步、生产部署、公开发行和外部交易 / Measurable conversion outcome, no invented efficiency improvement |
| requirements | REQ-01格式、REQ-02保留/拒绝、REQ-03门禁与依赖、REQ-04材料保留；各自映射文件、符号、合同和工作项 / Four separately traceable requirements |
| acceptance | 执行前固定输入、完整期望、层级和恢复 / Predeclared complete expectations and recovery |
| work_items / milestone | 从open进入triaged、in-progress、verification，仅准确必要合同都pass才verified-delivery；闭包包括依赖 / Actual in-memory transition sequence after observed checks |
| change | 一个准确本地候选；作者检查与独审分开，未创建PR或合并 / Local candidate, no invented independent review or merge |
| checks | 静态results为空；本次实际值在报告observations/checks / Empty planned result slots, fresh runtime observations |
| dependencies / configuration | 准确规范版本/摘要；实际Python版本逐次观察；无第三方包或秘密 / Exact standard bytes, observed interpreter, no third-party packages |
| materials | 活动引用时回收计划拒绝；提取观察并释放引用后仅回收独占临时数据 / Retain active data, clean only owned released temporary data |
| version | 最多形成ready-for-review，许可与分发决定仍not-decided / Ready for review is not release approval |
| adoption | technical-reference，不作真实采用；exceptions为空且有不触发理由 / Technical reference only, no adopted status or fabricated exception |
| maintenance / deployment | 不承诺SLA，无真实部署环境 / No SLA or deployment target |

未分配的实际决定者、审查者和维护者写unassigned，不能把示例运行器名字当真实批准人。四条需求的静态状态implemented仅说明仓库有实现位置；不把未运行的目标改成verified。

Unassigned roles remain unassigned. Static implemented requirements describe existing code, not executed or independently reviewed acceptance.

## 预设检查与恢复 / Predeclared checks and recovery

“隔离进程”具有实际argv、cwd、stdout/stderr和进程退出码。“有限模型”是在同一Python进程中对合成记录调用既有API；其中结果码只表示适配器返回/拒绝，不冒称外部程序、平台或现实权限。

Isolated-runtime checks spawn real processes. Finite-model checks call APIs on synthetic records; their adapter codes do not represent external systems or real authority.

| ID / 层级 | 场景 / Scenario | 直接失败原因与恢复 / Cause and recovery |
|---|---|---|
| `CSV-01` / `isolated-runtime` | `normal` — normal conversion | 输出列顺序、UTF-8或字节不符；保留输入；修转换器后在新目标路径复验。 |
| `CSV-02` / `isolated-runtime` | `bad-row` — malformed late row | 坏行列数不是2，必须在输出提交前拒绝；修正合成输入的坏行，在新文件另存并按新摘要重跑。 |
| `CSV-03` / `isolated-runtime` | `wrong-input-identity` — wrong preselected input | 实际输入与预先选择摘要不同；重读来源和原始选择；不得仅更新摘要跳过审查。 |
| `CSV-04` / `isolated-runtime` | `wrong-output-identity` — wrong expected output | 完整转换字节与预设输出不符；比较需求期望与完整输出；修实现或经审查修合同后复验。 |
| `CSV-05` / `isolated-runtime` | `existing-output` — existing target | 目标已存在，不得覆盖；保留现有文件，选择新的空目标名称。 |
| `CSV-06` / `isolated-runtime` | `quoted-neighbor` — legal quoted/CRLF neighbor | 合法引号、逗号、内嵌换行或CRLF被误拒；修复CSV解析而非禁止合法字段。 |
| `GOV-01` / `finite-model` | `missing-check` — required check missing | 必要检查缺失不能聚合通过；按原required集合补运行缺项；不删必要ID。 |
| `GOV-02` / `finite-model` | `failed-check` — failed child check | 失败子项不能被通过子项覆盖；保留失败并修复后生成新结果。 |
| `GOV-03` / `finite-model` | `unknown-check` — unknown child check | 已发起但未核实效果不能视为通过；先核实际终点，再决定恢复或重试。 |
| `GOV-04` / `finite-model` | `stale-revision` — stale scope revision | 旧revision不能覆盖新范围；重新读取范围、比较差异并取得对应决定后再试。 |
| `GOV-05` / `finite-model` | `wrong-adoption-scope` — wrong adoption scope | 采用范围含本项目显式排除项；恢复正确范围；真实扩张另行形成范围和采用决定。 |
| `GOV-06` / `finite-model` | `unresolved-dependency` — unresolved required dependency | 必要依赖不存在；补齐依赖及其验收，不能降为参考绕过。 |
| `GOV-07` / `finite-model` | `active-material` — active transitive material reference | 仍由活动成果传递引用的材料不可回收；结束使用并更新引用revision，再重新计划。 |
| `GOV-08` / `finite-model` | `recovery` — new observation after an unknown result | 未知旧结果不得被覆盖或自动改成通过；保留旧事件；核终点后另建当前完成事件。 |
| `GOV-09` / `finite-model` | `maintenance-boundary` — 维护承诺 / maintenance commitment | 没有真实渠道/责任却承诺响应时限。保持undecided或无SLA的limited；取得真实能力与决定后再改承诺。 |
| `GOV-10` / `finite-model` | `work-state-boundary` — 工作项关闭 / work closure | 未知验收关闭为verified，或重复关闭被算作交付。保留旧事件，重新进入verification并核准确接受条件。 |
| `GOV-11` / `finite-model` | `configuration-boundary` — 配置优先级与类型 / configuration | 配置优先级错误、布尔冒充整数或未知键被放行。保持旧有效配置；修覆盖顺序/类型/边界后复验。 |
| `GOV-12` / `finite-model` | `reference-boundary` — 准确规范引用 / reference identity | 同名规范的错误摘要仍被使用。保留原锁定并核准确登记与正文；不静默换latest。 |
| `GOV-13` / `finite-model` | `traceability-boundary` — 需求双向追溯 / traceability | 合同反向引用不是所证明的需求。修准确需求/合同关联并复核受影响运行。 |
| `GOV-14` / `finite-model` | `four-axis-boundary` — 四轴分离 / four axes | 用文档/独审状态替代采用或实现结果。分别恢复四轴；只依真实对象与证据更新对应轴。 |
| `GOV-15` / `finite-model` | `milestone-boundary` — 必要成果闭包 / milestone closure | 未验或duplicate依赖被计入已验证里程碑。保留必要闭包及关闭理由，复验实际必要成果。 |
| `GOV-16` / `finite-model` | `dependency-lock-boundary` — 依赖内容锁定 / dependency lock | 解析对象不同于锁定内容或版本。保持旧有效锁定，核来源和取得对象再运行。 |
| `GOV-17` / `finite-model` | `release-boundary` — 分发准备阻断 / release blockers | 陈旧/未知检查或未决许可被当作可分发。保留实际未决状态；重新绑定候选及必要检查，不触发发布。 |
| `GOV-18` / `finite-model` | `capacity-boundary` — 空间预算边界 / capacity | 预算忽略待写峰值或最低余量。重新观察可用字节和增量；核闲置可重建项后再规划。 |
| `GOV-19` / `finite-model` | `standard-closure-boundary` — 必要规范提供方 / standard closure | 适用消费接口缺少准确提供方条款。恢复所需规范选择、条件判断及相应验收合同。 |

Recovery in English: retain the original input and failed event; correct malformed input into a new file, reread a mismatched identity instead of silently changing the expected digest, choose a new target instead of overwriting, restore the necessary check/dependency set, reread current revisions before retrying, keep adoption within scope, and release current material references before replanning reclamation. An unknown event remains in history when a new completed observation is added.

## 精确输入与输出 / Exact fixture identities

以下是执行前夹具和独立期望的字节身份，不是已执行结果。实际运行报告重新读文件并给出其观察摘要；拒绝场景应没有输出，不能把空串摘要误当已创建空文件。

These are predeclared fixture/expectation identities. Execution reports separately observe actual files. A rejection has no output file; the empty-string digest is not a created artifact.

| 夹具 / Fixture | 输入字节 / Input bytes | 输入SHA256 / Input digest | 预期输出字节 / Expected bytes | 预期SHA256 / Expected digest |
|---|---:|---|---:|---|
| `normal` | 19 | `f6b4306c60b3d57222edf6c98f7852838ec7a2c137e4a49bf3cc0d5673a15b25` | 19 | `b702d8de49af5b07dd75d4dc9ea12da58cf360d26cba89ff1567b33c46e4e264` |
| `bad-row` | 21 | `603b8f2e449e2bf5d7ee76c86c0f796884040252c67fcb0ef069028b9901aa22` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `quoted-neighbor` | 38 | `79e30ee206a0f26a4948ff14109a649dc650deffc6b4cf4d10ab9dc6a9456dbb` | 35 | `a18741ef253cd6d1245c545576bf49cdadd82b652d32609683f135fc7c77e686` |

## 如何读取报告 / Read the report

- `source_identity`固定实际源码身份。Git工作区记录 `kind: git`、`object_format`、`base_commit` 和包含待测修改的实际 `tree`；新仓尚无提交时 `base_commit`为null。离线发行包经完整性校验后记录 `kind: release-bundle`、`bundle_kind`、`version`、`source_tree_sha256` 和 `manifest_sha256`。
- `candidate_sha256`是 `source_identity`的canonical SHA256；`source_unchanged`比较执行前后重新取得的来源身份。未提交修改可作为合法候选，捕获身份时保持真实Git索引和HEAD。`record_canonical_sha256`另行绑定实际传入的记录对象，报告的 `cwd`为实际源码根目录。
- `tool_versions`固定本次解释器、实现与平台；每项合同绑定环境摘要和输入摘要。
- `observations[].contract`是执行前期望；`.event.actual`来自实际文件观察或模型返回。CSV项的`file_identities.stdout/stderr/process_exit_code`保留真实子进程输出。外层退出0表示全部预期符合，不表示所有被测业务进程都退出0。
- `aggregate`不得把fail/unknown/not-run变绿；`milestone_ready_in_model`只属于合成工作记录。`release_preparation`最多ready-for-review，`actual_project_acceptance`与`independent_review`仍not-run。
- `requirement_results`与`success_results`从各自准确acceptance_ids重新聚合，给出需求和成功条件的本次合成结果，不覆写静态需求状态。
- `materials.active_plan`保留引用中的对象，`released_plan`仅为dry-run计划；实际临时目录回收由`temporary_directory_exists_after`读回，计划里的files_deleted不伪写为已删除数量。

The report binds exact source, environment, contract and observations. Git source identity contains the actual candidate tree, including uncommitted changes, its object format and baseline commit; release-bundle identity comes from verified bundle metadata. candidate_sha256 is the canonical digest of source_identity, captured again after execution to detect drift. The real Git index and HEAD are preserved, and cwd identifies the actual source root. Expected rejection may pass a test while its child process exits 2. Model milestone readiness is not real-project acceptance. Cleanup plans and actual directory observations remain distinct.

## 测试证明了什么 / What the tests establish

专项测试直接进入CSV解析器和治理语义路径：坏行传入其真实摘要，因此不是被前置文件hash挡住；错误条款ID、范围、required集合和工作依赖先通过schema，再由目标语义规则拒绝。合法相邻输入包括表头-only、CRLF、逗号/换行/双引号、无结尾换行以及合法采用子范围。

有界实现变异把聚合器错误改成恒pass、把序列化输出错误改成输入字节；独立结果比较和预期输出合同捕获它们。另有JSON类型变异（0变false、true变1）；观察适配层调用共享模型的类型敏感JSON比较，拒绝Python相等语义可能放行的错误。故意错误的预期会生成fail、保持工作项verification并阻止里程碑完成，而不是自动调预期。竞争测试在提交点模拟另一个写入者抢先创建目标，验证赢家字节与原输入不变。

The tests exercise semantic paths, not merely whole-file integrity gates. Bounded mutations target false-green aggregation and incorrect serialization. They do not claim exhaustive mutation adequacy, real independent review, other operating systems, production durability, actual authorization, distribution rights or deployment.

完整字段、合法值、必填触发和未知表达见[模板说明](../../templates/project-governance/README.md)。记录一致性、隔离运行与实质审查结论分别报告，不从其中一层推导其他层通过。

See the field reference for exact shape and failure handling.

## 条款选择与证明边界 / Selected clauses and proof scopes

每条选择的`acceptance_ids`只连接实际检查的有限机制，`automated_scope`逐项给出其谓词。PGM-01连接维护承诺合同GOV-09，PGK-02连接状态/关闭合同GOV-10，PGS-03连接配置合同GOV-11；缺项聚合、未知事件和CSV输出不替代这些机制。全部选择另有具体`manual_criteria`；填妥合成记录的`manual_state`仍为not-run、`manual_evidence`为空。有限检查全部pass不把这些人工项或完整条款改为符合。

Each selected clause names the exact finite predicates its checks exercise. Maintenance, work closure and configuration use separate actual contracts, not generic green results. Concrete remaining manual criteria stay not-run in this synthetic record; finite test success does not establish full clause conformance.

`adoption.dependency_bindings`逐项对应当前所选消费条款的必要接口，锁定提供方条款、条件和具体触发理由；applies要求准确提供方已选择且适用。没有秘密、没有发行和没有部署分别记录条件未触发，不把“未测试”写成不适用。工具核完整集合和端点，条件理由由人工实读。静态记录不带当前执行结果；报告给出独立运行的观察。

Dependency bindings cover the selected consumers' required interfaces. Triggered guarantees need the selected applicable provider. A no-secret configuration is a legitimate non-triggered condition; an untested feature is not. The validator checks identity and closure, while the factual applicability reasons require review.

已有结果被读入时，每个`checks.results[].candidate_sha256`必须等于当前实际 `source_identity`的canonical摘要；混合或陈旧摘要拒绝。摘要和非空证据定位只是身份/形状条件，不认证证据真实性；人工审查应实际打开原始观察核执行、环境与预期。`record_canonical_sha256`另外绑定运行时输入记录，结果不会写回静态记录。

Imported results must consistently bind the canonical digest of the current source_identity. A digest and evidence locator do not authenticate actual execution: review the accessible original observations, environment and independent expectations. Runtime record identity is separate from source identity, and the planned record is not rewritten.
