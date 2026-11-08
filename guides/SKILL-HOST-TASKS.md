# Skill 真实宿主任务验收

先按[安装指南](SKILL-INSTALLATION.md)安装准确的 Skill 包，再用[现有行为评测工具](ai-behavior/EVALUATION.md)准备试验。案例位于 [skill-host-tasks.json](../examples/ai-agent/behavior/cases/skill-host-tasks.json)，输入都是隔离的合成工程，不连接真实仓库或发布服务。输入可以是合成的，输出必须由实际宿主中的 Agent 产生。

## 任务和观察

| 案例 | 交付 | 必须实际观察 |
| --- | --- | --- |
| `HOST-001` 差异审查 | `review.md` | 加载 Skill、检索适用规范、读取原文、定位退出码回归，源码不改 |
| `HOST-002` 小型修复 | 修正的代码、测试及 `result.md` | 首次测试失败、最小修复、修后真实子进程测试通过 |
| `HOST-003` 发行判断 | `decision.json`、`decision.md` | 识别未执行的必需目标，保留已有通过结果，不执行发布 |

Codex CLI 与 Claude Code 各做这三个任务。每个任务分别在新会话执行显式调用和不提技能名称的自然任务，共十二次；不得在自然触发失败后于同一次试验补上技能名称，再改记为自然触发通过。修复后另建试验，不覆盖首次结果。

## 准备宿主与范围

记录实际 `codex --version` 或 `claude --version`、操作系统、配置选定的模型及可观察模型标识。使用项目批准的已登录环境和预算，不在仓库、案例或截图中保存凭据。实际无凭据或宿主无法启动时，记录对应错误，其他可执行目标继续进行。

使用独立临时 Git 项目。将完整 Skill 安装在工作区之外的受控个人目录或隔离项目父目录，让宿主能发现它；执行配置的 `tool_configuration` 记录其准确绝对路径及只读使用权限。不要把整个规范包复制进每次捕获的 `workspace/`。执行配置的 `project_instructions` 明确允许只读该路径和在本次 workspace 内完成案例；不得指向真实业务项目。

为两个宿主、两种调用方式分别建立执行配置和运行目录。显式调用的项目指令要求使用 `ranzevor-standards`；在 Codex 中以 `$ranzevor-standards`、Claude Code 中以 `/ranzevor-standards` 附加准备后的原始任务。自然模式只提供原始任务与授权路径，不指定要调用哪个技能、不预先注入技能正文。

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
