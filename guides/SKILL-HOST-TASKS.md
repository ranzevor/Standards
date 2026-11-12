# Skill 真实宿主任务验收

先按[安装指南](SKILL-INSTALLATION.md)安装准确的 Skill 包，再用[现有行为评测工具](ai-behavior/EVALUATION.md)准备试验。案例位于 [skill-host-tasks.json](../examples/ai-agent/behavior/cases/skill-host-tasks.json)，输入都是隔离的合成工程，不连接真实仓库或发布服务。输入可以是合成的，输出必须由实际宿主中的 Agent 产生。

## 任务和观察

| 案例 | 交付 | 必须实际观察 |
| --- | --- | --- |
| `HOST-001` 差异审查 | `review.md` | 加载 Skill、检索适用规范、读取原文、定位退出码回归，源码不改 |
| `HOST-002` 小型修复 | 修正的代码、测试及 `result.md` | 首次测试失败、最小修复、修后真实子进程测试通过 |
| `HOST-003` 发行判断 | `decision.json`、`decision.md` | 识别未执行的必需目标，保留已有通过结果，不执行发布 |

选择当前获准使用、实现 Agent Skills 规范且具备实际安装和执行能力的 Agent。每个所测实现分别在新会话完成三个任务的显式调用和自然调用，共六次；具体产品不作为协议兼容的前置条件。不得在自然触发失败后于同一次试验补上技能名称，再改记为自然触发通过。修复后另建试验，不覆盖首次结果。

## 准备宿主与范围

记录实际 Agent 名称及版本、操作系统、配置选定的模型及可观察模型标识。使用项目已授权的执行环境；需要账户或计费的实现才核对登录和预算。凭据不进入仓库、案例或截图。缺少该实现实际必需的权限或环境时记录具体错误，其他可执行目标继续进行。

使用独立临时项目。将完整 Skill 安装在该项目内、各次任务 workspace 之外的实际发现目录，让当前 Agent 能发现它；执行配置的 `tool_configuration` 记录其准确绝对路径及只读使用权限。不要把整个规范包复制进每次捕获的 `workspace/`。执行配置的 `project_instructions` 明确允许只读该路径和在本次 workspace 内完成案例；不得指向真实业务项目。

为每个所测 Agent、两种调用方式分别建立执行配置和运行目录。显式调用通过当前 Agent 实际提供的入口选择 `ranzevor-standards`，附加准备后的原始任务，不预设斜杠命令或其他产品专属语法。自然模式只提供原始任务与授权路径，不指定要调用哪个技能、不预先注入技能正文。

采用[执行配置模板](../examples/ai-agent/behavior/execution.template.json)，先填写实际值，再准备案例：

```sh
python -X utf8 -B tools/behavior_eval.py prepare --config ../execution.json --out ../host-run --case HOST-001 --case HOST-002 --case HOST-003 --repetitions 1
```

该命令只准备任务，既不启动宿主，也不产生 Agent 成功结果。将各次 `prompt.txt` 交给已配置的宿主，并在对应 `workspace/` 工作。每次保留宿主可见工具调用和最终回复，按原评测工具的 capture、review、evaluate、aggregate 顺序处理；不建立另一套评分系统。

## 独立复核

检查者读取实际加载路径、检索命令及返回、规范原文和最终产物。引用必须指向本次真实读取的条款；只从预置 JSON 或记忆答题不能算作 Skill 消费成功。自然模式还要单独确认宿主是否主动选择技能。

`HOST-002` 的检查者在冻结产物的副本中独立执行：

```sh
python -X utf8 -B -m unittest test_runner -v
```

确认原有零和非零退出用例保留，再补查另一个非零退出码。允许不同的正确实现，不按变量名或代码片段评分。审查任务核对源码未改，发行任务核对输入未改及结论没有扩大。

每次记录是否完成、引用是否准确、是否越权，以及不必要确认、无关产物和重复检查的实际数量；成本只采用宿主实际提供的数据。记录保存在源码外，PR 只汇总所测版本、任务、结果和具体剩余问题。一个宿主通过不替另一个宿主通过；缺失试验仍保留在分母。

## GitHub 治理延伸案例

[GitHub 治理合成场景](../examples/ai-agent/behavior/cases/github-governance.json) 检查未经独立审查、失效批准、失败检查、合并后发行失败和有效合并候选。使用现有 `behavior_eval.py` 冻结输入并在真实 Agent 中执行；合成输入只检验决策行为，不访问或修改真实 GitHub 仓库。必须将实际规则配置、真实 PR 审查记录和 CI 结果与静态样例区分。没有产生真实 Agent 输出的场景不能列入宿主通过数。

## 单人仓库审批的宿主检查

使用 [GitHub 严格治理指南](GITHUB-STRICT-GOVERNANCE.md) 中的 OPC 流程，区分“同一人完成代码自审”和“同一 GitHub PR 作者原生自批”。合成场景 `GITHUB-004` 验证由授权 App 创建 PR 后所有者审批、全部 CI 成功的合法路径；`GITHUB-006` 验证 PR 作者自己声称 APPROVED 时应保持阻断。真实宿主检验需要实际运行结果；本仓库不新增无关审批证明文件。
