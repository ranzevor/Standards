# 本地提交与 PR 元数据检查

本仓库的提交消息采用 `type(scope): 简体中文具体变更主题`。涉及功能和缺陷的提交必须有实质性正文，破坏性变更说明对应的契约和迁移影响。

在已审查的可信分支中执行 `node governance/install_commit_hook.cjs`。安装器先将提交消息校验器及 CommonMark 依赖写入共同 Git 目录下尚未启用的版本目录，再安装受管理的 `commit-msg` 钩子。关联工作树被删除后，共享钩子仍可使用这些依赖。共享的 `core.hooksPath` 不得指向关联工作树专属的 Git 元数据目录；工作树级钩子配置只影响对应工作树。对于默认或已位于 Git 私有目录的钩子路径，保持原有路径，原有 `pre-commit`、`pre-push` 等钩子继续生效；独立的 `commit-msg` 不会被覆盖。重装失败不会修改正在使用的校验器；受管理钩子被添加额外检查或修改执行目标后，重装会拒绝覆盖，须先审查并整合。

如果生效的 `core.hooksPath` 指向工作树且存在钩子，安装器拒绝自动复制或停用它们。应先审查现有钩子及其调用的脚本，将需要保留的检查迁移到由 `git rev-parse --git-path hooks` 定位的 Git 私有钩子目录，处理 `commit-msg` 冲突，并取消旧的工作树钩子路径配置后重新安装。没有既有钩子的工作树路径会改为 Git 私有版本目录；启用 `extensions.worktreeConfig` 时使用工作树级配置，安装后核对实际生效的 `core.hooksPath`。

安装器拒绝通过符号链接父目录安装到可能被重定向的路径。安装完成后检出其他分支时，受管理的钩子不从工作树加载可执行脚本。仅在审查并接受新版检查器后重新安装；新克隆需单独安装。本地钩子仍可通过 `--no-verify` 绕过，远端保护由独立的必需检查承担。

创建 PR 前应对当前 Git 分支的实际提交、相对于目标分支的差异、拟使用的标题和正文进行检查，并填写当前 PR 模板。本地 `commit-msg` 钩子仅约束提交消息；本仓库提供了按准确候选分支创建草稿 PR 的可选 OPC 工作流；其标题、正文及实际 Git 变更仍由远端必需检查验证，不使用脱离真实变更的 JSON 快照代替预检。

## 远端检查接入

GitHub 的 `governance-metadata` 检查读取当前 PR 的真实元数据和全部 API 分页结果。管理员首次接入时按以下顺序配置：

1. 在 **Settings → Actions → Policies** 中，为 `.github/workflows/governance-metadata.yml` 明确允许 `pull_request_target` 事件，并按该工作流路径限定策略范围。公开仓库的默认事件限制见 [GitHub 官方变更说明](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)，配置入口见[工作流执行策略](https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution)。
2. 将工作流及校验器通过正常审查和现有必需检查合入默认分支。工作流从默认分支加载受信代码，首次真实运行安排在合入后。
3. 创建或更新目标为 `main` 的正常 PR，确认 `governance-metadata` 出现在该 PR 的检查结果中并成功完成。
4. 在 **Settings → Rulesets → Protect main** 中，保留现有 `validate`、`verify` 必需检查及分支同步要求，追加 `governance-metadata`，并为新增检查选择实际产生结果的 GitHub Actions 来源。
5. 在同一个 PR 中只编辑元数据：先将标题改为违规内容，等待 `edited` 事件触发的新检查失败并确认合并受阻；恢复标题后，单独删除正文中的必填项，再次等待检查失败并确认受阻。最后恢复合规正文，确认最新检查成功、对应阻断解除。

检查失败只有在它被列为必需检查后才会阻断合并。独立技术审查、语义一致性与治理配置自身的防篡改需要独立于此元数据检查进行验证。

## 最终 squash 消息

合并前，在已审查的可信分支中，将拟使用的完整提交消息写入仓库外的 UTF-8 文件，例如 `../squash-message.txt`。第一行为主题，其后用空行分隔正文，然后执行：

```sh
node .github/scripts/governance_gate.cjs message-file ../squash-message.txt
```

校验通过后，将同一标题和正文用于 squash 合并；通过 API 合并时，将同一标题和正文分别传入 `commit_title`、`commit_message`，将已审查 PR 的当前 HEAD 传入 `sha` 参数。消息修改后重新校验。

`PR_TITLE`、`PR_BODY` 提供默认合并文本，合并时仍可覆盖。元数据检查校验的是 PR 标题、正文和源提交；最终合并消息使用上述入口单独检查。参见 [GitHub 合并接口](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request)。

## OPC 内置令牌创建 PR

可选 [OPC 草稿 PR 工作流](../.github/workflows/opc-open-pr.yml) 由仓库所有者从默认分支手动运行，输入已推送的分支和真实标题。它仅请求 `contents: read` 与 `pull-requests: write`，从受信默认分支复制 PR 模板后以 GitHub Actions Bot 创建 Draft PR。仓库需在 **Settings → Actions → General → Workflow permissions** 单独启用 **Allow GitHub Actions to create and approve pull requests**；默认关闭时创建请求会被 GitHub 拒绝。工作流不自动审批 PR。

GitHub 当前允许使用 `GITHUB_TOKEN` 创建的 PR 触发 `pull_request` opened/synchronize/reopened 工作流，但执行需要仓库写入者批准；其余事件不必然触发。创建者须编辑完整正文、手动将 Draft 标为 Ready for review 以触发本仓库受信的 `pull_request_target` 检查、批准所需 CI 实际运行，再由不是 PR 作者的所有者以本人账户提交 APPROVE。PR、审核与检查三者都要绑定当前 HEAD，不能用设置开关或操作已发起代替实际门禁通过。
