# 本地提交与 PR 元数据检查

本仓库的提交消息采用 `type(scope): 简体中文具体变更主题`。涉及功能和缺陷的提交必须有实质性正文，破坏性变更说明对应的契约和迁移影响。

在已审查的可信分支中执行 `node governance/install_commit_hook.cjs`。安装器先将提交消息校验器及 CommonMark 依赖写入尚未启用的 Git 私有目录，再安装受管理的 `commit-msg` 钩子。对于默认或已位于 Git 私有目录的钩子路径，保持原有路径，原有 `pre-commit`、`pre-push` 等钩子继续生效；独立的 `commit-msg` 不会被覆盖。重装失败不会修改正在使用的校验器。

如果生效的 `core.hooksPath` 指向工作树且存在钩子，安装器拒绝自动复制或停用它们。应先审查现有钩子及其调用的脚本，将需要保留的检查迁移到由 `git rev-parse --git-path hooks` 定位的 Git 私有钩子目录，处理 `commit-msg` 冲突，并取消旧的工作树钩子路径配置后重新安装。没有既有钩子的工作树路径会改为 Git 私有版本目录；启用 `extensions.worktreeConfig` 时使用工作树级配置，安装后核对实际生效的 `core.hooksPath`。

安装完成后检出其他分支时，受管理的钩子不从工作树加载可执行脚本。仅在审查并接受新版检查器后重新安装；新克隆需单独安装。本地钩子仍可通过 `--no-verify` 绕过，远端保护由独立的必需检查承担。

创建 PR 前应对当前 Git 分支的实际提交、相对于目标分支的差异、拟使用的标题和正文进行检查，并填写当前 PR 模板。本地 `commit-msg` 钩子仅约束提交消息；本仓库未提供直接绑定 Git 候选的自动 PR 创建前门禁，不使用脱离真实变更的 JSON 快照代替预检。

GitHub 的 `governance-metadata` 检查读取当前 PR 的真实元数据和全部 API 分页结果，失败时阻断该检查通过；只有管理员在远端规则中设置为必需检查并核实其来源后，才会阻断合并。

独立技术审查、语义一致性与治理配置自身的防篡改需要独立于此元数据检查进行验证。
GitHub 将于 2026-12-02 对公开仓库默认禁止 `pull_request_target` 事件，部署本门禁之前必须在适用的 Actions event policy 中明确允许此工作流，并完成 GitHub 实际事件执行与阻断验收。不能为了让检查变绿改用可由未合并 PR 自行改写执行内容的弱化入口。参见 [GitHub 官方变更说明](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)。
