# 安装 Skill 并完成第一个任务

将提示词交给当前使用的 Agent 执行。`ranzevor-standards` 使用 [Agent Skills 开放规范](https://agentskills.io/specification)；安装位置与发现入口由当前 Agent 的实际实现决定，不限定产品或额外安装服务。

## 中文安装提示词

```text
请在我当前使用的 Agent 环境中，为当前项目安装 Ranzevor Standards 的 ranzevor-standards Skill。仓库：https://github.com/ranzevor/Standards 。从该仓库 GitHub Releases 获取最新正式发布的完整 Agent Skill 包，不使用未发布的 PR、分支源码或 SKILL.md.in 模板。按 Agent Skills 开放规范（https://agentskills.io/specification）处理 SKILL.md 和随附资源，并根据当前 Agent 实际支持的发现与安装机制选择当前项目范围的安装位置；不要把某个 Agent 专属目录、命令、插件或服务当作协议要求。

安装前校验发行包，保留完整技能目录。不得覆盖已有同名 Skill，不得经符号链接、junction 等重定向写出项目范围；先在项目范围内、技能发现目录外暂存并验证，成功后再放入正式位置，失败不得留下可被发现的不完整技能。完成后确认当前 Agent 能发现并加载技能，使用随包检索脚本完成一次只读条款查询，并报告安装版本、实际位置和验证结果。不要修改业务源码、现有项目采用决定、其他 Skill 或全局配置。当前 Agent 不支持项目级安装或缺少实际权限时，说明具体缺失，不改为全局安装，也不以安装说明冒充安装成功。
```

## English installation prompt

```text
Install the ranzevor-standards Skill from Ranzevor Standards for the current project in the Agent environment I am using. Repository: https://github.com/ranzevor/Standards . Obtain the complete Agent Skill archive from the latest official GitHub Release in that repository, not an unpublished PR, branch checkout, or SKILL.md.in template. Handle SKILL.md and its bundled resources according to the Agent Skills specification (https://agentskills.io/specification). Select a project-scoped installation location using this Agent's actual discovery and installation mechanism; do not treat any Agent-specific directory, command, plugin, or service as a protocol requirement.

Verify the release archive before installing and retain the complete Skill directory. Do not overwrite an existing Skill with the same name or follow symlinks, junctions, or other redirects outside the project scope. Stage and verify inside the project scope but outside Skill discovery directories, then place the complete directory at its final location; failures must not leave a discoverable partial Skill. Confirm that this Agent can discover and load it, run one read-only clause lookup with its bundled script, and report the installed version, actual location, and verification results. Do not modify business source, existing adoption decisions, other Skills, or global configuration. If this Agent lacks project-scoped installation support or the necessary permissions, report the specific missing capability; do not switch to a global installation or present instructions as a successful installation.
```

## 获取与安装流程

1. **确认范围。** 确定当前项目根目录、Agent 实际的 Skill 发现方式及安装权限。项目范围不受支持时报告该限制，不自动改成用户级或全局安装。先检查当前发现范围内的同名 Skill，包括其他目录中的同名副本；已有安装保持不动。
2. **选定发行。** 从仓库 [GitHub Releases](https://github.com/ranzevor/Standards/releases/latest) 选择最新正式发行，固定该次返回的版本与附件。取得对应的完整 `Standards-v<version>-agent-skill.zip` 和同版完整性材料；不要混用不同发行、预发布、草稿、PR 或分支文件。下载与暂存也放在项目授权范围内。
3. **验证完整包。** 按[离线使用说明](OFFLINE.md)完成下载校验。解压位置必须在实际 Skill 发现目录之外；包根目录应为 `ranzevor-standards/`，包含 `SKILL.md`、`scripts/` 和 `references/`。保留所有随附资源，执行包内校验器。格式检查使用官方 `skills-ref validate`；它不替代包完整性和实际消费检查。
4. **完整安装。** 使用当前 Agent 的项目级安装机制。文件系统安装先检查目标父目录的实际归属，拒绝符号链接或 junction 重定向；在发现目录外完成复制与校验，再以不可覆盖的目录移动放入最终位置。复制、校验或移动失败时清理本次暂存，不删除原有安装或其他技能。
5. **实际消费。** 刷新当前 Agent 的技能目录或开启新会话，通过其实际入口发现并加载该技能。根据实际加载的 `SKILL.md` 位置找到脚本，执行一次只读查询，读取对应原文。报告准确版本、位置、发现／加载和查询结果。

[客户端实现指南](https://agentskills.io/client-implementation/adding-skills-support)说明了本地目录、远端 API 和预置资源等发现方式。格式规范不统一规定安装路径、调用命令或权限。安装到目录只完成了文件放置，发现与加载必须在实际 Agent 中检查。

## 本地目录安装工具

已校验的 Source 包提供 `tools/install_skill.py`，Skill 包内的同一工具位于 `references/tools/install_skill.py`。该工具用于 Windows 和 Linux 的本地目录安装，不连接账户或安装宿主，也不改变 Agent Skills 格式。原有发行未携带该工具时，由 Agent 使用自身可用的安装机制，不从未发布分支补装脚本。

先从实际 Agent 配置取得项目内的发现目录，以相对于项目根目录的路径传入 `--skills-dir`。暂存父目录必须位于同一项目、同一卷，并且在所有实际 Skill 发现目录之外；默认项目根目录 `.` 只有满足这些条件时才能使用。以下命令中的路径应替换为实际位置：

```sh
python -X utf8 -B tools/install_skill.py --source "/project/downloads/ranzevor-standards" --scope-root "/project" --skills-dir "actual-skill-directory" --staging-parent "."
```

工具先验证源包，再创建本次独有的暂存目录，复制并复验完整内容，最后执行不可覆盖的目录移动。目标即使是空目录也不会被替换；链接和 Windows 重解析目录会被拒绝。阶段失败不创建正式技能，普通异常或中断会清理本次暂存。进程被强制终止时，残留仅位于发现目录外，下一次安装使用新的暂存目录；确认没有安装进程使用旧暂存后，只清理该次残留。跨卷或平台不支持不可覆盖移动时停止，不退回直接复制到正式目录。

工具输出安装版本和实际位置；Agent 继续完成发现、加载与只读查询。它不自动登记全局配置，也不将其他宿主的目录约定当作默认值。

## 首次查询与工程任务

从本次实际加载的 `SKILL.md` 所在目录定位 `scripts/lookup.py`。在项目工作目录运行脚本绝对路径，不必切换工作目录：

```sh
python -X utf8 -B "/project/actual-skill-directory/ranzevor-standards/scripts/lookup.py" --document-id STD-PG-005 --clause-id PGE-05
```

查询成功后读取返回路径中的原文；`references/...` 相对于 Skill 根目录。确认返回的是 `STD-PG-005`、`PGE-05` 及其实际文档版本，而非仅在回复中提到 Skill 名称。

再开一个新会话，不指定技能名称，执行一个实际任务，例如审查当前差异的退出码和失败处理。观察 Agent 是否选择技能、检索适用条款并完成任务。没有自动选择时保留该结果，另做显式调用排查。审查、修复与发行判断案例见[真实宿主任务](SKILL-HOST-TASKS.md)。

## 升级、恢复与移除

升级是单独操作，不作为遇到同名安装时的自动回退。先验证新包，比较项目真正采用的文档与条款；发行集合升版不会自动改变项目采用。经授权升级时结束相关会话，将旧目录移到发现范围之外，再安装完整新目录，避免覆盖合并导致旧文件残留。

新版本不能使用时，将其移出发现范围，把保留的旧目录恢复到原位置，再重新加载。移除时只处理本次安装的 `ranzevor-standards/`，不删除宿主配置、父目录或其他技能。发现入口中的启用、禁用和移除动作遵循当前 Agent 的实际实现。
