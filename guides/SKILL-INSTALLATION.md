# 安装 Skill 并完成第一个任务

本指南使用正式发行中的完整 `ranzevor-standards/` 目录。先安装并登录所选的 Codex CLI 或 Claude Code；检索脚本使用 Python 3.12。安装只增加可选技能，不修改项目已采用的规范或宿主工具权限。

## 取得和放置

从 [GitHub Releases](https://github.com/ranzevor/Standards/releases) 选择需要的准确版本，取得 `Standards-v<version>-agent-skill.zip`，按[离线说明](OFFLINE.md)核对同版下载文件。在新的暂存目录解压，得到：

```text
ranzevor-standards/
├── SKILL.md
├── BUNDLE-MANIFEST.json
├── scripts/
│   ├── lookup.py
│   └── verify_bundle.py
└── references/
```

复制整个目录，不要只复制 `SKILL.md`，也不要形成两层 `ranzevor-standards/ranzevor-standards/`。

| 宿主 | 当前项目 | 当前用户的所有项目 |
| --- | --- | --- |
| Codex CLI | `<项目根目录>/.agents/skills/ranzevor-standards/` | `<用户主目录>/.agents/skills/ranzevor-standards/` |
| Claude Code | `<项目根目录>/.claude/skills/ranzevor-standards/` | `<用户主目录>/.claude/skills/ranzevor-standards/` |

选择一个宿主、一个作用域。首次建议在临时项目使用项目级目录；不要同时安装多个同名副本。Codex 可能在选择器中显示两个同名技能；Claude Code 的个人技能可以覆盖项目级同名技能。启动目录应在目标 Git 项目内。

将以下代码存为源码目录外的临时 Python 文件，在目标项目根目录运行。把 `source` 改为已解压目录的绝对路径，`host` 选择 `codex` 或 `claude-code`，`scope` 选择 `project` 或 `user`。脚本先校验完整包，成功才复制；目标存在时拒绝覆盖。

```python
from pathlib import Path
import shutil
import subprocess
import sys

source = Path('/absolute/path/ranzevor-standards')
host = 'codex'
scope = 'project'
parent = {'project': Path.cwd(), 'user': Path.home()}[scope]
folder = {'codex': '.agents', 'claude-code': '.claude'}[host]
target = parent / folder / 'skills' / 'ranzevor-standards'
subprocess.run([sys.executable, '-X', 'utf8', '-B',
                str(source / 'scripts/verify_bundle.py'), str(source)], check=True)
shutil.copytree(source, target)
print(target)
```

Windows 路径可写成 `Path('C:/Users/name/Downloads/ranzevor-standards')`。项目级安装是否纳入该项目版本控制，由项目自己决定；不要把下载 ZIP、暂存副本或运行记录一起提交。

## 确认发现与显式调用

在目标项目根目录启动新会话，避免旧会话残留的技能内容影响首次验证。

**Codex CLI：** 运行 `codex`，在 `/skills` 中确认 `ranzevor-standards` 可见，然后输入：

```text
$ranzevor-standards 查询 STD-PG-005 的 PGE-05 条款，读取原文，并说明它对当前项目快速开始的具体要求。只读，不修改项目。
```

**Claude Code：** 运行 `claude`，输入 `/ranzevor-standards` 并附上同一任务：

```text
/ranzevor-standards 查询 STD-PG-005 的 PGE-05 条款，读取原文，并说明它对当前项目快速开始的具体要求。只读，不修改项目。
```

检查实际加载的 `SKILL.md` 位置、脚本调用和原文读取，不把回复中出现技能名称当作加载证明。脚本应从该文件所在目录定位，使用绝对路径运行；项目工作目录不需要切换。返回的 `references/...` 相对于 Skill 根目录，Source 包的 `standards/...` 相对于 `source/`。

技能未显示时，先检查目录层级、`SKILL.md` 名称、同名个人副本及宿主禁用设置；重新启动会话后再查。不要通过复制多个同名目录掩盖发现问题。

## 自然任务与最小交付

再开一个新会话，不提 Skill 名称，给出实际任务，例如：

```text
依据本项目已经采用的工程规范，审查当前差异中的命令退出与失败处理。读取相关原文，给出可定位的问题和最小修复建议；只读，不创建治理文件或修改采用范围。
```

确认宿主是否选择技能、读取适用条款，并完成任务。没有自动选择时，保留这次结果，再另开显式调用任务排查；不能把显式调用成功记作自然触发成功。

工程任务还应核对最终差异、必要测试、错误定位和是否增加无关工作。可复用[真实宿主任务](SKILL-HOST-TASKS.md)的审查、修复和发行判断案例。

## 升级、恢复与移除

先在扫描目录外解压并验证新版本，比较真正采用的文档和条款；发行集合升版不代表每份规范正文变化。停止使用该技能的会话，再将原技能目录移到扫描目录之外，按首次安装步骤复制新目录。不要覆盖合并两个版本的文件，否则已删除文件可能残留。

新版本无法使用时，移出新目录并将原目录放回同一安装位置，重新启动会话。保留项目采用决定和已完成工作，不用切换技能包改写它们。确认新版本满足项目任务后，再按自己的保留策略处理旧包。

移除时，只移出或删除本次安装的完整 `ranzevor-standards/` 目录，不删除 `.agents`、`.claude`、宿主配置或其他技能。启动新会话，确认技能不再可选；历史对话中已加载的内容不会因删目录而从记录中消失。

## 宿主依据

安装路径、发现方式和显式调用入口以 [OpenAI 技能文档](https://learn.chatgpt.com/docs/build-skills) 与 [Claude Code 技能文档](https://code.claude.com/docs/en/skills) 为依据。实际宿主版本可分别用 `codex --version` 和 `claude --version` 取得；具体行为验收应记录运行版本，而不是仅引用文档。
