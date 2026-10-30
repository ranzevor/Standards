# 离线分发与使用

发行集合版本由项目元数据固定；162 份已采用规范逐份保留准确版本。正文位于 `standards/`，[规范登记](../registry/standards.json)提供稳定 ID、版本、路径和 SHA-256，[条款索引](../registry/requirements.json)提供条款位置。

## 制品

| 制品 | 内容 | 解包入口 |
| --- | --- | --- |
| `Standards-v0.1.0-source.zip` | 规范、指南、索引、模板、检查工具与测试 | `Standards-v0.1.0/source/` |
| `Standards-v0.1.0-agent-skill.zip` | Agent Skill、规范引用与离线检索脚本 | 包内根目录的 Skill 说明文件 |
| `BUILD-REPORT.json` | 来源提交、源码集合身份与两类包的验证结果 | 与发行附件一起获取 |
| `SHA256SUMS.txt` | 两个 ZIP 与 BUILD-REPORT 的 SHA-256 | 与发行附件一起获取 |

## 从公开发行入口首次使用

前置条件为 Python 3.12。Source 包只使用 Python 标准库，不需要安装第三方依赖，也不读取账号、凭据或环境变量。浏览器可代替下列下载命令；文件仍应来自同一 [Standards v0.1.0 Release](https://github.com/ranzevor/Standards/releases/tag/v0.1.0)。

### Windows PowerShell

在一个新的空目录中运行：

```powershell
$version = '0.1.0'
$base = "https://github.com/ranzevor/Standards/releases/download/v$version"
Invoke-WebRequest "$base/Standards-v$version-source.zip" -OutFile "Standards-v$version-source.zip"
Invoke-WebRequest "$base/SHA256SUMS.txt" -OutFile 'SHA256SUMS.txt'

$archive = "Standards-v$version-source.zip"
$line = Get-Content .\SHA256SUMS.txt | Where-Object { $_.EndsWith("  $archive") }
if (-not $line) { throw "SHA256SUMS.txt 中没有 $archive" }
$expected = ($line -split '\s+')[0].ToLowerInvariant()
$actual = (Get-FileHash ".\$archive" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "SHA-256 不匹配" }

Expand-Archive -LiteralPath ".\$archive" -DestinationPath .
Set-Location "Standards-v$version"
python -X utf8 -B verify.py
Set-Location source
python -X utf8 -B tools/skill_lookup.py --document-id STD-PG-005 --clause-id PGE-05
```

### Ubuntu

在一个新的空目录中运行：

```sh
version='0.1.0'
base="https://github.com/ranzevor/Standards/releases/download/v${version}"
curl -fL "$base/Standards-v${version}-source.zip" -o "Standards-v${version}-source.zip"
curl -fL "$base/SHA256SUMS.txt" -o SHA256SUMS.txt
grep "  Standards-v${version}-source.zip$" SHA256SUMS.txt | sha256sum -c -
unzip "Standards-v${version}-source.zip"
cd "Standards-v${version}"
python3 -X utf8 -B verify.py
cd source
python3 -X utf8 -B tools/skill_lookup.py --document-id STD-PG-005 --clause-id PGE-05
```

摘要检查、`verify.py` 和最小查询都应以退出码 0 结束。查询输出应包含文档 `STD-PG-005`、条款 `PGE-05`、版本、路径与正文行段。摘要不一致或校验失败时，不继续使用当前副本；删除已下载文件，从同一 Release 重新取得并再次核对。

## 检查与构建

在完整源码根目录使用 Python 3.12 标准库，以非优化模式运行：

```sh
python -X utf8 -B checks/generate_registry.py --check
python -X utf8 -B checks/generate_index.py --check
python -X utf8 -B checks/validate_all.py
python -X utf8 -B -m unittest discover -s tests -v
python -X utf8 -B tools/build_release_bundle.py --output ../Standards-release-assets --source-commit "$(git rev-parse HEAD)"
python -X utf8 -B tools/verify_release_bundle.py ../Standards-release-assets/Standards-v0.1.0-source.zip
python -X utf8 -B tools/verify_release_bundle.py ../Standards-release-assets/Standards-v0.1.0-agent-skill.zip
```

上面的包名以 0.1.0 为示例，使用其他发行版本时替换为项目元数据中的准确版本。构建命令采用 POSIX shell；PowerShell 可先以 `git rev-parse HEAD` 取得提交，再把完整值传入 `--source-commit`。

构建输出必须位于源码目录之外。构建过程验证全部正文身份，生成两个确定性 ZIP 以及摘要清单。`BUILD-REPORT.json` 记录本次构建与文件验证结果。

Source 包解压后，在 `Standards-v0.1.0/` 执行 `python verify.py`，再进入 `source/` 执行源码检查。

## Agent Skill

Skill 包解压后，在 `ranzevor-standards/` 执行：

```sh
python -X utf8 -B scripts/verify_bundle.py
python -X utf8 -B scripts/lookup.py --query "Agent"
python -X utf8 -B scripts/lookup.py --document-id STD-L0-001 --clause-id ARC-01
```

检索可使用 `--query`、`--document-id`、`--clause-id`、`--domain` 和 `--limit`。结果提供文档身份、路径与条款行段；按任务读取适用条件、具体要求和必要依赖。源码中可直接使用 `python tools/skill_lookup.py`。

本地构建不发布；受审查的发行配置合入 `main` 后，工作流可在验证通过后创建 Tag 和 Release，具体条件见[发行治理](../governance/RELEASE.md)。自动发布环境不可用时，维护者按同一份准确提交与制品清单手动发布。从正式发行入口取得制品，并核对同一版本的 SHA-256 清单。发现文件、清单或摘要不一致时，重新取得完整制品。

## 许可

规范、文档和数据按 CC BY 4.0 分配，软件与检查工具按 Apache-2.0 分配。Source 与 Agent Skill 包的公开再分发和商业使用遵循根 [LICENSE](../LICENSE) 及各材料的具体条件。

## 原生平台消费者

需要核对编码、中文与空格路径、解包及独立工作目录消费时，使用[跨平台验收](CROSS-PLATFORM.md)与[消费者检查入口](../tools/check_offline_consumers.py)。按准确输入制品分别记录平台结果；Windows 状态以实际 Windows 执行记录为准。
