# GitHub 仓库治理：PR 自审、必需 CI 与合并后验证

适用于已采用此配置的独立开发者、OPC 和使用 Standards Skill 执行 GitHub 治理任务的 Agent。具体要求沿用[变更提案审查与合并规范](../standards/project-governance/009-变更提案审查与合并规范--v0.1.0.md)、[测试质量门禁与证据规范](../standards/project-governance/011-测试质量门禁与证据规范--v0.1.0.md)及[版本发行规范](../standards/project-governance/015-版本标签与发行规范--v0.1.0.md)。其他仓库已实际采用的更严格规则不会因本配置自动降低。

## 1. OPC 基线：本人创建 PR、本人与 Agent 审查、CI 全部通过

1. 在非受保护分支完成变更，使用本人现有 GitHub 账号或已获授权的 Agent 创建 PR；无需另设 GitHub App、Actions Bot 或第二个维护者。
2. 对当前 PR 的 **Files changed**、提交、测试覆盖、兼容性、权限和发布影响进行实际自审。发现问题就修改，修改后重新审查受影响范围。已采用的规范另外要求实质独立技术审查时，由未参与实现的独立审查者或审查 Agent 针对当前候选完成复核；这一技术审查不等于 GitHub 平台的 APPROVED，也不要求另设账号。现有 PR 正文按仓库模板填写真实审查和验证内容，不生成无关证明文件。
3. 主分支强制经 PR 集成，禁止删除和 force push，保持线性历史和目标分支同步；必须解决全部审查线程、阻止失败/跳过的必需 CI，且不设置宽泛 bypass。
4. 当前策略允许开发者**自审并自行决定合并**。GitHub Ruleset 的 `required_approving_review_count=0`，含义仅为**不强制其他账号提交 APPROVED**；不是跳过审查、CI 或合并授权。PR 作者不能使用 GitHub 原生 APPROVE 审批自己的 PR，但可以审阅 Diff、讨论修改并在门禁满足后执行合并。
5. 若某仓库已经采用原生一票或多人审批，保持原设置，除非所有者针对准确仓库明确批准改变。Agent 不因开发者人数、效率、额度或 CI 失败而自行降低任何实际采用的保护。

## 2. 配置并核实真正生效的 GitHub Ruleset

必须核实目标仓库和主分支的远端 Ruleset，而不是凭文档、历史会话、PR 文本推断已启用。对本模式的 `main`：

- Active：Require pull request before merging，Required approving reviews **0**，Require conversation resolution；保持 dismiss stale reviews on push 等已采用的设置。
- 禁止删除、force push，要求线性历史；要求更新目标分支后重新检查。只允许已采用的 squash 合并方式。
- Required status checks：`validate`、`verify`、`governance-metadata`，绑定正确且可信的检查来源。
- 不新增能跳过检查或直接推送到主分支的 bypass；如远端 Ruleset 高于本模式，要先取得仓库所有者针对该对象的明确调整决定。

GitHub 可将 `neutral` 或 `skipped` 结论视为满足原生 Required status check；关键作业必须用始终执行的汇总检查验证所有必要依赖均为实际 `success`。该汇总检查的名称须与 Ruleset 要求相符。没有发生的工作流不是通过；不要因路径过滤或身份条件漏跑必需任务。

审查失败、待解决的线程、CI 未完成、取消或缺失时禁止合并。使用真实 PR 核验失败时有阻断、修复后能恢复，避免错误门禁永久阻断合法变更。若 `pull_request_target` 在仓库策略中被禁止，应修复受信工作流事件配置；不要取消必需的 `governance-metadata`。

## 3. 从 PR 到 main 的交付

合并前重新读取 PR head、base、全部文件和审查线程，确认本次自审覆盖准确候选；`validate` 必须同时汇总 Linux 合同检查与 Ubuntu/Windows 原生消费测试，`verify` 和 `governance-metadata` 也须成功。缺少其他 GitHub 账号的原生 APPROVED 不是本模式的阻断条件；已采用的独立技术复核必须对当前候选完整通过，未审阅实际 Diff、独立复核未完成或未获合并授权均须阻断。

目标分支变化后重新检查。批准合并时使用当前 HEAD 并校验最终 squash 消息，不强推或通过管理员绕过。合并后检查真实 `main` 提交上的 `push` CI、产物及实际发行结果。PR 绿色不是集成后发行成功的证明。

### 合并后发行失败处理

若发行工作流已经创建草稿并上传附件，却因草稿回读 API 返回 HTTP 404，准确结果是“草稿及附件部分创建成功，发行检查失败”。先按 Release ID 检查既有草稿和附件，定位错误；通过新的修复 PR 或受控回退恢复，按相同门禁复核后继续发行。禁止把已经合并的提交当成未合并，也不重建尚未检查的草稿、重写已共享历史或隐瞒失败。

## 4. Agent 与宿主

操作前读取当前远端状态、准确采用决定及权限。将**审查完成**、**必需检查通过**、**已合并**、**主分支集成检查成功**、**已发行**视为不同事实。不允许因为“只有一个开发者”虚构第二名批准者，也不允许为了严格而强加未采用的一票审批。实际合并、发布或修改 Ruleset 仍按各自授权执行。

Agent 可按[Skill 选读流程](SKILL-CONSUMPTION.md)寻找准确条款，使用[GitHub 治理行为案例](../examples/ai-agent/behavior/cases/github-governance.json)核对阻断与合法邻例。此处的行为测试不替代真实 GitHub 上的生效检查。
