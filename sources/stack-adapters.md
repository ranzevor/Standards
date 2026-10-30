# 十类语言与技术栈适配来源

引用日期：2026-10-23。下表记录十类语言与技术栈的来源版本、章节、技术命题和适用边界。项目按选用的工具链版本消费对应接口，并结合L4技术规范确定验收条件。

| ID | 官方/原始对象与所读章节 | 支持的有限技术命题、版本与边界 |
| --- | --- | --- |
| JS-01 | TC39，[ECMAScript 2025 §13表达式](https://tc39.es/ecma262/2025/multipage/ecmascript-language-expressions.html)，Await；语言类型与Number相关定义 | 语言求值/await与宿主、远端事务是不同层；不是浏览器/Node全部API的规范。采用TC39固定2025多页正文 |
| JS-02 | Node.js，[v24.19.0 Packages](https://nodejs.org/download/release/v24.19.0/docs/api/packages.html)，Determining module system / Package entry points | type、文件扩展与exports参与模块解析；锁文件不自动证明权利或构建无副作用。采用固定release正文 |
| JS-03 | TypeScript，[Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)，Type Assertions；滚动Handbook | 类型断言在编译时移除，不执行运行时检查；实际编译器/strict选项仍由项目固定 |
| JS-04 | WHATWG，[Fetch Living Standard](https://fetch.spec.whatwg.org/#abort-fetch)，fetch method / abort fetch，所见更新2026-10-19 | 中止操作作用于客户端Promise/请求与响应体；不是远端事务撤销。HTTP错误响应与network error不同。DOM的AbortSignal接口要求API主动消费signal；已完成操作可忽略取消信号，取消不提供任意CPU或远端操作的强停保证 |
| PY-01 | Python，[3.12 asyncio Tasks](https://docs.python.org/3.12/library/asyncio-task.html)，Task Cancellation / Task Groups / Timeouts | 任务取消、清理及异常传播按asyncio契约；引用文档为3.12.15，项目固定所用解释器及实现版本 |
| PY-02 | Python，[3.12 venv](https://docs.python.org/3.12/library/venv.html)，介绍与环境性质 | 虚拟环境用于包环境，应可重建而非可搬运安全沙箱；不证明来源可信 |
| PY-03 | Python，[3.12 typing](https://docs.python.org/3.12/library/typing.html) Note；[3.12 decimal](https://docs.python.org/3.12/library/decimal.html) 介绍 | 运行时不强制类型注解；十进制表示与二进制float不同。具体业务范围、舍入和未知结果由项目合同规定 |
| JVM-01 | Oracle，[Java SE21 JLS §17](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html) §17.4.5；[javac21](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javac.html) --release | JMM的happens-before与线程同步；编译语言/API目标和实际运行时分开 |
| JVM-02 | Oracle，[Java21 BigDecimal](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html)，表示、equals/compareTo | 数值与scale、比较合同不同；不提供统一财税/金额业务规则 |
| JVM-03 | Oracle，[Java21 AutoCloseable](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/AutoCloseable.html)，接口描述/close | try-with-resources调用close；close不必像Closeable那样幂等。释放不证明事务或远端效果 |
| JVM-04 | Kotlin kotlinx.coroutines，[固定commit 7e0d1b3…的 coroutines-cancellation.md](https://github.com/Kotlin/kotlinx.coroutines/blob/7e0d1b3e9ca83652427ae00dda7d1673f058a743/docs/topics/coroutines-cancellation.md)，Make coroutines react to cancellation；blob `251212df40b6bdfd548facccdc351ba9d8b3d784` | 取消是合作式，需挂起或明确检查 |
| GO-01 | Go，[Modules Reference](https://go.dev/ref/mod)，Modules/packages/versions、go.mod/go.sum | 模块路径、版本和校验信息有不同作用；本体系额外要求固定实际解析与工具身份 |
| GO-02 | Go，[Memory Model](https://go.dev/ref/mem)，2022-06-06模型；Data races / Synchronization | 无数据竞争的顺序保证与实际同步关系；不证明持久事务或对象权限 |
| GO-03 | Go标准库，[context](https://pkg.go.dev/context)，Overview / WithCancel / Done | 取消通过上下文信号传递，调用方仍需按操作合同响应/结束；滚动pkg页须与目标工具链对照 |
| RS-01 | Rust，[Cargo build](https://doc.rust-lang.org/cargo/commands/cargo-build.html)，Manifest Options --locked/--offline/--frozen | 锁现有解析和离线是不同开关，frozen组合二者；无安全或字节可复现自动认证 |
| RS-02 | Rust Reference，[Behavior considered undefined](https://doc.rust-lang.org/reference/behavior-considered-undefined.html)，undefined.intro / soundness | unsafe也不得触发UB，安全抽象需对所有合法安全调用者sound；此滚动清单本身明确并非穷尽正式模型 |
| CC-01 | ISO C委员会，[N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)，2011-04-12委员会草案 §5.1.2.4、§6.7.3 | C数据竞争/volatile与原子同步分开。引用对象为C11委员会草案；项目按L6固定具体采用版本 |
| CC-02 | C++工作草案，[intro.races](https://eel.is/c++draft/intro.races)，2026-10-23所见条款 | 竞争、同步、原子与UB的规则；滚动工作草案不是固定ISO C++20文本 |
| NET-01 | Microsoft，[Cancellation in managed threads](https://learn.microsoft.com/en-us/dotnet/standard/threading/cancellation-in-managed-threads)，合作式取消/请求与响应/Dispose | 取消是通知，监听者决定如何结束；Dispose不同于发出取消。实际TFM/SDK/资源清理另验 |
| NET-02 | Microsoft，[Nullable reference types](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/null-safety/nullable-reference-types)，静态分析与null-state | nullable是编译分析/诊断，不等于运行时外部数据验证；反射/AOT/序列化需要按实际交付验证 |
| GD-01 | Godot，[4.6 GDScript Reference](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/gdscript_basics.html)，Awaiting signals / Assert keyword | await让出并等待信号；release导出忽略assert及其表达式。不是保证实际游戏确定性/恢复/设备支持 |
| GD-02 | Godot，[4.6 Thread-safe APIs](https://docs.godotengine.org/en/4.6/tutorials/performance/thread_safe_apis.html)，Scene tree | 活动场景树并非线程安全；延迟调用等消费路径仍需有效对象/世代，不自动提供业务原子性 |
| SQL-01 | PostgreSQL，[18 §4.2 Value Expressions](https://www.postgresql.org/docs/18/sql-expressions.html)、[18 §9.2 Comparison](https://www.postgresql.org/docs/18/functions-comparison.html) | 表达式与NULL比较有具体语义，不能凭同名SQL语法假定所有引擎一致；持久与并发契约交具体数据库L4 |
| SQL-02 | SQLite，[Quirks](https://www.sqlite.org/quirks.html)，Flexible typing / Foreign Key Enforcement / NULL等 | 实现差异及外键设置必须真实核对；滚动官方实现说明，不外推PostgreSQL或文件掉电耐久 |
| SH-01 | GNU Bash5.2.37实际内置帮助：`help printf; help read; help trap; help set`；[官方手册入口](https://www.gnu.org/software/bash/manual/html_node/Quoting.html) | Bash5.2内置帮助规定格式、read -r、trap与set的语义；argv保真以子进程实际收到的参数为判据 |
| SH-02 | Microsoft，[PowerShell7.4 about_Quoting_Rules](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules?view=powershell-7.4)，Long description / 引用规则 | 表达式/参数模式和含空格参数的引用；不能把Bash转义算法直接套PowerShell |

## 验收与来源边界

每个 `STK-NN` 条款结合所选L4机制、语言规格及工具版本确定输入、动作和验收判据。项目运行记录应包含实际工具版本、执行命令和观察结果。
