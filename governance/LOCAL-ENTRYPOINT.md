# 本地提交与 PR 元数据检查

本仓库的提交消息采用 `type(scope): 简体中文具体变更主题`。涉及功能和缺陷的提交必须有实质性正文，破坏性变更说明对应的契约和迁移影响。

在已审查的可信分支中执行 `node governance/install_commit_hook.cjs`，安装程序会把提交消息校验器、CommonMark 依赖及钩子复制到 Git 私有目录并启用本地 `core.hooksPath`。安装后检出其他分支时，钩子不从工作树加载可执行脚本。只有审查并接受新版本的检查器后才重新运行安装命令；曾配置 `core.hooksPath .githooks` 的本地克隆也必须改用此安装方式。新克隆仓库需要单独安装，`--no-verify` 仍可绕过本地钩子，因此远端保护由独立的必需检查承担。

创建 PR 前应对当前 Git 分支的实际提交、相对于目标分支的差异、拟使用的标题和正文进行检查，并填写当前 PR 模板。本地 `commit-msg` 钩子仅约束提交消息；本仓库未提供直接绑定 Git 候选的自动 PR 创建前门禁，不使用脱离真实变更的 JSON 快照代替预检。

GitHub 的 `governance-metadata` 检查读取当前 PR 的真实元数据和全部 API 分页结果，失败时阻断该检查通过；只有管理员在远端规则中设置为必需检查并核实其来源后，才会阻断合并。

独立技术审查、语义一致性与治理配置自身的防篡改需要独立于此元数据检查进行验证。
GitHub 将于 2026-12-02 对公开仓库默认禁止 `pull_request_target` 事件，部署本门禁之前必须在适用的 Actions event policy 中明确允许此工作流，并完成 GitHub 实际事件执行与阻断验收。不能为了让检查变绿改用可由未合并 PR 自行改写执行内容的弱化入口。参见 [GitHub 官方变更说明](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)。
