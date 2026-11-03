# 本地提交与 PR 元数据检查

本仓库的提交消息采用 `type(scope): 简体中文具体变更主题`。涉及功能和缺陷的提交必须有实质性正文，破坏性变更说明对应的契约和迁移影响。

执行 `git config --local core.hooksPath .githooks` 后，Git 的 `commit-msg` 阶段会调用仓库内的消息校验器。新克隆仓库需要单独启用钩子，`--no-verify` 可以绕过本地检查，因此它不是远端保护。

在创建 PR 前准备包含 `pull_request`、`commits` 和 `files` 字段的真实 JSON 快照，执行 `node .github/scripts/governance_gate.cjs preflight-json <文件路径>`。此检查不能替代检查重复 PR、实际 Diff 语义、完整测试、权限和来源的创建前核验。

GitHub 的 `governance-metadata` 检查读取当前 PR 的真实元数据和全部 API 分页结果，失败时阻断该检查通过；只有管理员在远端规则中设置为必需检查并核实其来源后，才会阻断合并。

独立技术审查、语义一致性与治理配置自身的防篡改需要独立于此元数据检查进行验证。
GitHub 将于 2026-12-02 对公开仓库默认禁止 `pull_request_target` 事件，部署本门禁之前必须在适用的 Actions event policy 中明确允许此工作流，并完成 GitHub 实际事件执行与阻断验收。不能为了让检查变绿改用可由未合并 PR 自行改写执行内容的弱化入口。参见 [GitHub 官方变更说明](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)。
