# 跨平台与离线消费者验收

发行制品以 UTF-8 保存文本，规范正文和生成索引采用 LF。根目录的
[Git 属性](../.gitattributes)固定文本检出换行；规范登记中的 SHA-256 对应原始字节，
不能通过自动转换正文或重新计算摘要掩盖检出差异。

维护者的目标基线为 Python 3.12。Windows 与 Linux 分别执行原生验证；一个系统上的
通过记录不能代替另一个系统的结果。当前验收范围不包含 macOS、网络共享、全部文件
系统、任意长路径或用户个人 Skill 安装。

## 编码与路径契约

- 离线 lookup CLI 的标准输出和标准错误采用 UTF-8，重定向到文件或管道仍保留中文
  标题与路径。`find()` 函数被导入时不调整调用方的标准流。
- 规范内、登记中和 ZIP 中使用相对 POSIX 路径。原生命令行接受当前操作系统的目录
  路径，工具使用参数数组调用子进程，支持路径中的空格与中文。
- 发行路径拒绝绝对路径、父级穿越、反斜杠、冒号、控制字符、Windows 禁用字符、
  末尾点或空格及设备保留名。目录组件同样受约束。
- 全路径和目录前缀不能存在大小写或 Unicode NFC 规范化后的别名；验证器拒绝冲突，
  不重命名文件。正常的中文、内部空格、`COM10.md`、`con-file.txt` 等邻近名称保留有效。
- 索引生成器显式读写 UTF-8/LF。`INDEX.md` 和来源目录索引的 `--check` 会拒绝 CRLF
  漂移；规范正文的字节变化由登记摘要拒绝。

这些路径限制依据 [Microsoft 文件命名规则](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)，
并增加保守的别名冲突检查。[Python UTF-8 模式](https://docs.python.org/3.12/using/windows.html#utf-8-mode)
与[标准流编码](https://docs.python.org/3.12/library/sys.html#sys.stdout)说明了解释器模式和
重定向流的区别。模拟旧编码或换行默认值的回归测试只验证相应边界，不计作 Windows
原生执行证据。

## 同一发行的 Source 与 Agent Skill

从正式发行入口取得同一版本的 Source、Agent Skill 与摘要清单后，在可信源码目录运行
[消费者检查](../tools/check_offline_consumers.py)。将下面参数换成实际绝对路径；命令本身
同时适用于 POSIX shell 与 PowerShell：

```sh
python -X utf8 -B tools/check_offline_consumers.py --source-archive "/absolute/path/Standards-v0.1.1-source.zip" --skill-archive "/absolute/path/Standards-v0.1.1-agent-skill.zip" --evidence-dir "/absolute/path/new-consumer-evidence"
```

Windows 路径示例可以使用 `C:/StandardsAssets/Standards-v0.1.1-source.zip`。版本号只是
命令示例，必须替换为输入制品的准确版本。证据目录必须尚不存在且位于源码树之外；
失败后的重试使用新目录，保留原始失败记录。

检查先验证两个 ZIP 的全部清单、文件字节与规范身份，再确认版本、规范快照和 Source
快照相同。随后解压到含中文与空格的独立路径，从无关工作目录执行两个独立验证器、
Source 登记与索引检查、Source 合同检查以及两种包内的条款查询。查询故意在 ASCII
重定向环境执行，并验证输出是 UTF-8 JSON、条款身份正确且返回路径指向实际文件。
执行使用 Python 标准库，不依赖原仓库的 `.git`、个人 Skill 目录或第三方 Python 包。
检查结束再次核对两个解包目录，发现内容改动或未登记缓存即失败。

该检查不请求网络操作；它没有隔离操作系统网络，也不把校验和当作发行者身份认证。
它不会安装、启用、复制到个人 Skill 目录或发布任何包。

## 执行记录与 Windows 交接

`execution.json` 记录实际 OS、Python、准确输入制品摘要、每条命令、工作目录、开始和
结束时间、退出码及原始 stdout/stderr 的位置和摘要。受阻、进程失败、错误编码和
完整性失败都会保留失败状态；其他平台固定为 `not-run`，不能由本次成功改成通过。

[平台工作流](../.github/workflows/platform.yml)由维护者手动触发，分别使用
`ubuntu-latest` 和 `windows-latest`。它固定 Actions 提交、只申请 `contents: read`，
检出不保留凭据，不执行发布或个人安装。工作流在准确候选提交上运行源检查、跨平台
回归和两个独立消费者，并保留分平台证据。

仓库质量与发行工作流使用 GitHub 托管的 Ubuntu Runner。此平台工作流使用
GitHub 托管的 Ubuntu 和 Windows Runner。维护者确认对应
Runner 可用后再触发；没有原生运行结果时记录为 `not-run`，也可按上述命令本地验收。

本地没有 Windows runner 时，交接应记录准确候选 commit、两个 ZIP 的 SHA-256、上述
命令和证据目录。Windows 环境运行后，核对 `environment.system` 确为 `Windows`、
所有命令退出码为零、输入身份与待验收发行一致，以及执行后的包完整性通过。提供
工作流 run URL 与日志或交回完整证据目录后，才能把该 Windows 目标从 `not-run` 改为
通过。不要把 YAML 已存在或模拟测试通过写成 Windows 已验证。
