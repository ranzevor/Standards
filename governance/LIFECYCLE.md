# 规范状态与项目记录

## 规范生命周期

| 状态 | 含义与进入条件 |
| --- | --- |
| draft | 正在编写的变更，已有明确范围和内容身份 |
| review | 变更进入技术审查 |
| adopted | 规范维护方已经采用的准确版本与范围 |
| deprecated | 已公布替代方案和迁移要求 |
| withdrawn | 已撤回，并说明受影响版本及原因 |

Standards v0.1.1 的 162 份现行规范均为 adopted。规范的正式身份和状态由[规范登记](../registry/standards.json)统一记录；规范目录、译文和发行工具使用同一登记。

## 审查、项目采用与实现验收

技术审查绑定被审内容及范围。作者自查与独立审查分别保留；变更后的结论应说明有效范围及必要补验。

项目采用记录项目选择的文档、版本、条款、参数、依赖和例外。已有有效决定覆盖当前项目时，沿用该决定及其范围。

实现验收记录实际目标、输入、操作和观察，使用 pass、fail、not-run、partial、unknown 或有范围依据的 not-applicable。规范已经 adopted 与项目实际实现通过分别由各自记录说明。

项目记录的字段和操作接口见[项目治理指南](../guides/PROJECT-GOVERNANCE.md)与[字段说明](../templates/project-governance/README.md)。
