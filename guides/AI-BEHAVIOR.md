# AI 行为与交付指南

这里提供现有 Standards 条款的使用指南和可选行为场景配置。项目选择适用条款、配置和案例后，将其登记到已有采用记录；本入口不建立第二套规范正文，也不使新配置自动约束旧采用项目。

## 选择和固定

1. 识别任务的成果、读者、权限和完成条件，选取下列相关专题。
2. 从[规范登记](../registry/standards.json)取得文档 ID、版本、路径和 SHA-256，结合[条款索引](../registry/requirements.json)定位准确要求。
3. 在项目已有采用记录中保存选定条款、配置/场景身份、参数、例外和验收方式。按[项目采用指南](ADOPTION.md)处理适用性和升级。
4. 运行前固定案例、模型/宿主、指令和工具配置。模板与正反例只作为实施输入；实际观察另行记录。

## 按任务选读

| 专题 | 内容 | 案例 |
| --- | --- | --- |
| [声明与表达质量](ai-behavior/EXPRESSION.md) | 对应现有条款的执行方法、失败例与合法邻例 | [expression](../examples/ai-agent/behavior/cases/expression.json) |
| [授权内推进与必要确认](ai-behavior/AUTONOMY.md) | 对应现有条款的执行方法、失败例与合法邻例 | [autonomy](../examples/ai-agent/behavior/cases/autonomy.json) |
| [产物用途与完整性](ai-behavior/DELIVERABLES.md) | 对应现有条款的执行方法、失败例与合法邻例 | [artifacts](../examples/ai-agent/behavior/cases/artifacts.json) |
| [完成状态与证据](ai-behavior/EVIDENCE.md) | 对应现有条款的执行方法、失败例与合法邻例 | [evidence](../examples/ai-agent/behavior/cases/evidence.json) |
| [按需加载与宿主适配](ai-behavior/PROFILES.md) | 对应现有条款的执行方法、失败例与合法邻例 | [context](../examples/ai-agent/behavior/cases/context.json) |
| [真实行为评测操作](ai-behavior/EVALUATION.md) | 对应现有条款的执行方法、失败例与合法邻例 | [evaluation](../examples/ai-agent/behavior/cases/evaluation.json) |

## 核对场景合同

```sh
python -m checks.behavior_cases
```

该入口检查场景结构和当前规范引用，不执行模型，也不批准项目采用。实际行为检查应同时观察产物、可见执行记录和独立语义判据。

常见任务可从[任务速查](ai-behavior/QUICKSTART.md)开始。模型与宿主适配只保存有复现依据的差异，并设复审和移除条件。

[评测操作指南](ai-behavior/EVALUATION.md)提供冻结、捕获、独立审查、汇总和成对比较命令。真实执行证据保存在源码树外，规范仓仅保存安全场景和工具。

## 采用、升级与反馈

用[采用与升级流程](ai-behavior/ADOPTION.md)将实际问题、选定配置、运行证据和升级决定连起来。缺陷或模型偏差使用[反馈模板](../examples/ai-agent/behavior/FEEDBACK.template.md)，附原始失败和相邻合法例；没有复现证据的型号专属补丁保持停用。
