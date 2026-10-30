# 语言与技术栈有限可运行示例

在仓库根目录运行：

```sh
report_dir="$(mktemp -d)"
python examples/stacks/run_local.py --report "$report_dir/StandardsStackReport.json"
```

脚本只调用已安装的本地运行时，不安装依赖、不访问服务，构建和引擎缓存写入临时目录。报告记录命令、起止时间、退出状态、两个输出流、夹具摘要、未执行项和检查范围。各技术栈及产品验收按下表的覆盖范围分别执行。

每个子命令默认限时 40 秒，可用正的有限值 `--timeout-seconds` 调整。完成、超时和启动失败分别记录；超时或启动失败的 `exit_code=null`。超时保留已捕获的部分 stdout/stderr、此前完成记录，并输出失败报告。外部效果、后代进程状态和未观察到的输出保持未确定。两个流同时保留原始字节的 base64、SHA-256 和 UTF-8 替换解码视图。

报告路径必须在夹具源仓库之外且尚不存在，旧记录不会被覆盖。退出 0 表示本次已执行夹具的判据成立，退出 1 表示夹具或命令失败，退出 2 表示参数或报告发布失败。报告写入失败时仍向 stdout 输出已装配记录。标准库行为依据[Python 3.12 subprocess 文档](https://docs.python.org/3.12/library/subprocess.html)：`run(timeout=...)` 的直接子进程处理与 `Popen.communicate` 不同，`TimeoutExpired` 捕获流可能为 bytes 或 `None`；产品进程树终止由目标环境另行验证。

| 示例 | 实际机制 | 未覆盖 |
| --- | --- | --- |
| JavaScript | 运行时整数边界、旧世代拒绝、合法多对象 | TS编译、浏览器/DOM、服务幂等 |
| Python | bool与int区别、合法0、实际asyncio取消传播和本地清理 | 杀线程、撤回远端效果 |
| SQLite | 实际参数绑定、NULL比较、外键和事务回滚 | 其他引擎、文件持久性、断电恢复 |
| C / C++ | 实际编译与运行、合法边界/零长度、超界拒绝 | 全部内存/并发正确、硬件/ABI全支持 |
| Bash | 含空格/分号/Unicode值的真实argv/输出及错误退出 | POSIX全兼容、PowerShell、信号/网络效果 |
| Godot | 实际4.6脚本Variant验证、旧世代和合法对象 | GUI输入、AT、物理回放、release导出或设备支持 |

## 其余真实目标的执行合同

- **TypeScript：** 已锁定编译器及tsconfig后，`tsc --strict --noEmit`检查合法与错误消费例；再从实际发行包运行JS消费者。期望错误类型输入被编译/运行时按各自边界拒绝；不能仅改类型断言让错误通过。
- **Java/Kotlin：** 固定JDK/Kotlin/依赖，分别编译旧新消费者并在承诺JVM运行；注入interrupt/协程取消和清理失败，观察资源/原始异常/权威业务结果。该有限夹具不编译JVM消费者；未运行所选工具链时不报告编译通过。
- **Go：** 先用真实Go工具链 `go version`、`go env`固定身份，再执行 `go test ./...`和适用`go test -race ./...`。同名可执行文件不能替代工具链身份核验；该有限夹具未执行Go目标。
- **Rust：** 固定rustc/cargo/target/feature和依赖，`cargo test --locked --offline`及发行消费者；unsafe/FFI按支持工具执行Miri或相应检查。未执行所选工具链为not-run，不由名称或文件存在推断通过。
- **.NET：** 固定SDK/TFM/RID和解析输入，按项目入口`dotnet build`、`dotnet test`并从发行包消费；取消和反射/AOT对实际产物执行。未执行所选SDK目标保持not-run。
- **PowerShell：** 固定pwsh/OS后`pwsh -NoProfile -File`运行参数保真、非终止错误、原生命令退出及取消夹具；逐个核stdout/stderr/exit和子进程，不复用Bash引用算法。未执行所选PowerShell目标保持not-run。

目标项目还必须按L4与L6加入真实状态、权限、并发、迁移、恢复与发行路径；没有这些环境的有限示例不能代替它们。
