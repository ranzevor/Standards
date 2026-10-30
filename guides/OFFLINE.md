# 离线分发与使用

发行集合版本由项目元数据固定；162 份已采用规范逐份保留准确版本。正文位于 `standards/`，[规范登记](../registry/standards.json)提供稳定 ID、版本、路径和 SHA-256，[条款索引](../registry/requirements.json)提供条款位置。

## 制品

| 制品 | 内容 | 解包入口 |
| --- | --- | --- |
| `Standards-v0.1.0-source.zip` | 规范、指南、索引、模板、检查工具与测试 | `Standards-v0.1.0/source/` |
| `Standards-v0.1.0-agent-skill.zip` | Agent Skill、规范引用与离线检索脚本 | 包内根目录的 Skill 说明文件 |
| `BUILD-REPORT.json` | 来源提交、源码集合身份与两类包的验证结果 | 与发行附件一起获取 |
| `SHA256SUMS.txt` | 两个 ZIP 与 BUILD-REPORT 的 SHA-256 | 与发行附件一起获取 |

## 检查与构建

在完整源码根目录使用 Python 3.12 标准库，以非优化模式运行：

```sh
python checks/generate_registry.py --check
python checks/generate_index.py --check
python checks/validate_all.py
python -m unittest discover -s tests -v
python tools/build_release_bundle.py --output ../Standards-release-assets --source-commit "$(git rev-parse HEAD)"
python tools/verify_release_bundle.py ../Standards-release-assets/Standards-v0.1.0-source.zip
python tools/verify_release_bundle.py ../Standards-release-assets/Standards-v0.1.0-agent-skill.zip
```

上面的包名以 0.1.0 为示例，使用其他发行版本时替换为项目元数据中的准确版本。构建命令采用 POSIX shell；PowerShell 可先以 `git rev-parse HEAD` 取得提交，再把完整值传入 `--source-commit`。

构建输出必须位于源码目录之外。构建过程验证全部正文身份，生成两个确定性 ZIP 以及摘要清单。`BUILD-REPORT.json` 记录本次构建与文件验证结果。

Source 包解压后，在 `Standards-v0.1.0/` 执行 `python verify.py`，再进入 `source/` 执行源码检查。

## Agent Skill

Skill 包解压后，在 `ranzevor-standards/` 执行：

```sh
python scripts/verify_bundle.py
python scripts/lookup.py --query "Agent"
python scripts/lookup.py --document-id STD-L0-001 --clause-id ARC-01
```

检索可使用 `--query`、`--document-id`、`--clause-id`、`--domain` 和 `--limit`。结果提供文档身份、路径与条款行段；按任务读取适用条件、具体要求和必要依赖。源码中可直接使用 `python tools/skill_lookup.py`。

本地构建不发布；受审查的发行配置合入 `main` 后，工作流可在验证通过后创建 Tag 和 Release，具体条件见[发行治理](../governance/RELEASE.md)。自动发布环境不可用时，维护者按同一份准确提交与制品清单手动发布。从正式发行入口取得制品，并核对同一版本的 SHA-256 清单。发现文件、清单或摘要不一致时，重新取得完整制品。

## 许可

规范、文档和数据按 CC BY 4.0 分配，软件与检查工具按 Apache-2.0 分配。Source 与 Agent Skill 包的公开再分发和商业使用遵循根 [LICENSE](../LICENSE) 及各材料的具体条件。

## 原生平台消费者

需要核对编码、中文与空格路径、解包及独立工作目录消费时，使用[跨平台验收](CROSS-PLATFORM.md)与[消费者检查入口](../tools/check_offline_consumers.py)。按准确输入制品分别记录平台结果；Windows 状态以实际 Windows 执行记录为准。
