# Web 与后端合同验收入口

## 1. 输入与证据记录

每个项目固定提供者/消费者构建摘要、真实 OS/浏览器/辅助技术或引擎/SDK/Broker 版本、角色与租户、协议配置、测试数据、初态、故障触发屏障、时限及权威查询入口。逐章 `P` 是正例，`F` 是直接破坏机制的变异，`N` 是合法邻例。从 [Web 规范目录](../../standards/L4/web/README.md)和[后端规范目录](../../standards/L4/backend/README.md)选择适用正文，按条款固定输入、三类场景与观察量。相同章节的多个子规则分别记录，不能只运行最容易的一个。

每份结果至少包含 `case_id / original_rule_id / input / action / expected / actual / authoritative_before / authoritative_after / versions / timing / raw_evidence / status`。状态区分 `pass`、`fail`、`not-run`、`blocked`；预期失败变异被检出，不等于错误实现通过。客户端 ACK、日志、Span、监测导出、Pod Ready 均不得替代领域收据。组织设计约束与官方协议支持的有限命题见 [来源映射](../../sources/web-backend/claims.json)。

## 2. 可重复的局部实现

以下命令从仓库根目录运行。Python 示例只使用标准库；浏览器夹具需已有 Playwright Python 包和真实 Chromium。

```sh
python -m unittest discover -s tests -p test_web_backend_local_contracts.py -v
STANDARDS_RUN_BROWSER_TARGETS=1 python -m unittest discover -s tests -p test_web_backend_browser_contracts.py -v
```

`local_contracts.py` 的 SQLite 数据仅含合成租户、订单及整数分金额。局部测试使用实际进程退出、双进程争用、数据库事务、多连接、线程及 loopback HTTP；逐次命令、退出码和数据库观察保存到每次运行的独立结果目录。退出后重新打开数据库文件查询提交状态，不从退出事件本身推断。保存前崩溃、保存后丢响应、同键异参、相同金额不同表示、独立租户、去重缓存清理、Inbox 的独立消费范围、目标世代拒旧均有具体断言。

新的局部测试运行默认在系统临时目录 `StandardsWebLocalContracts/<UTC-run-id>/` 保存各测试的 SQLite 文件与 `results.json`，不改写规范仓库。可用 `STANDARDS_WEB_LOCAL_EVIDENCE_DIR` 指定独立输出根目录；每次运行仍生成唯一子目录。每份结果绑定实际执行的输入版本和环境；不能用另一对象的旧结果替代。

错误变异包括业务先提交但 Outbox 缺失、Inbox 先提交抑制未发生业务、缺少目标栅栏、读时暂缺却另建意图导致双写。SQLite WAL 场景要求捕获对应交错下的 `SQLITE_BUSY_SNAPSHOT` 并核事务结果；这不是 PostgreSQL/MySQL 的隔离实测，也不证明掉电耐久、实际鉴权、真实支付或 Broker 的端到端效果。

浏览器夹具 `browser_contracts.html` 和 10 项测试覆盖原生 required、键盘默认 submitter、`requestSubmit` 与 `submit`、successful controls、事件传播与默认动作、原生模态焦点、History 和可控异步落地顺序。错误变异直接触发空值绕过提交、禁用后字段消失、换账号后旧内容重新可见；合法邻例包括 readonly 值继续提交、当前账号/最新查询可落地。该夹具使用 Promise 屏障；实际网络取消、系统 IME 和真实 AT 按下列目标合同分别验证。

浏览器初始化或必要系统能力失败时，保存实际错误、命令及版本，相关场景记录 **blocked / not-run**；没有进入目标断言不能报告浏览器通过。恢复目标环境后重新运行受影响场景，原失败记录保留。

## 3. Web 的真实执行动作

| 文档 | 具体输入、工具与动作 | 观察和失败判据 |
|---|---|---|
| W01 通用基线 | 选一条完整读路径、一条带权限的写路径、一条可合法简化的纯静态路径；真实浏览器 DevTools Network/Accessibility/Performance 联同服务端收据 | 从用户目标至权威终态逐项核对；静态路径不被强制安装 PWA/状态库；未知写入不能显示成功 |
| W02 DOM/交互 | 实际页面以 Tab/Shift+Tab/Enter/Space/Escape 操作；记录 `activeElement`、`composedPath()`、cancelable/defaultPrevented、submitter、`new FormData(form, submitter)`；同时检查服务端收到的字段 | 原生 disabled/readonly/未选字段分别判定；停止传播不冒充取消默认动作；移除组件后无遗留监听/节点写入；Shadow 关系与焦点真实成立 |
| W03 CSS | 最长内容、缺字/慢字体、RTL、200%/400% 缩放、窄视口、强制颜色、减少动效和打印；DevTools Computed/Layout 及实际截图/打印输出 | 控件、焦点、错误和重要信息不被剪掉；普通/important 的层顺序分开；软键盘覆盖不得仅凭 `dvh` 宣称解决；允许合法布局差异而非逐像素强求一致 |
| W04 渲染/路由 | 直接深链、刷新、Back/Forward、重复 URL 参数、导航 A→B 后倒序完成请求、冻结恢复；在 SSR 首字节/已发副作用/接管前分别断流 | 地址、焦点、滚动、DOM、身份世代与有效导航一致；错误接管可恢复且不复制业务动作；hydration mismatch 不靠自动重载未知提交掩盖 |
| W05 状态/表单 | A/B 账号、双标签、旧版本 ETag、提交已持久化后断响应、IndexedDB blocked 升级、配额耗尽；Network/Application 面板与权威操作查询 | 草稿/显示缓存/服务器事实分离；旧身份回调不能重新落地；IME 候选确认不误提交；request success 不等于事务 complete，更不等于设备掉电不丢 |
| W06 浏览器安全 | 测试身份直接调用隐藏接口，异源表单/CORS 请求、同源旧窗口 postMessage、错 origin/source/challenge、伪造字段和会话恢复 | 服务端对象/租户/字段权限和副作用计数为 oracle；CORS 可读限制不是防 CSRF；相同 origin 不足以接受旧窗口消息；Trusted Types 直通策略不能算净化 |
| W07 PWA | 双标签分别保持旧页面；更新 Worker，记录 installing/waiting/active/controller；离线后动态 import、队列重放、Schema 升级及账号切换；Application/Network 面板 | skipWaiting/claim 不更新运行中页面 JS；旧资源依赖闭包仍可取；离线受理不等于服务端完成；持久请求被拒、配额回收和无后台唤醒均有前台恢复 |
| W08 可访问性 | 固定真实浏览器+OS+AT 版本，例如目标 Windows/NVDA 或 macOS/Safari/VoiceOver；读出 role/name/state/relations，再以键盘和 AT 从进入、编辑、错误、提交至完成；中文系统 IME 在候选打开时用 Enter/方向键，再确认候选 | 保留原始操作/朗读及焦点轨迹，不以 Accessibility Tree 或自动扫描替代用户任务；aria-activedescendant 的活动项与 DOM 焦点分开；Dialog/Popover/Combobox 按实际合法模式判定 |
| W09 性能 | 固定设备/网络/冷暖缓存/身份分段，PerformanceObserver 原始条目、Performance 轨迹和有权 RUM；慢第三方、长任务、隐藏恢复与缺失指标分别记录 | p75/尾延迟从原样本复算，缺失不填零；LCP/INP/CLS 与完整业务正确性同时过关；单次 Lab 不能代表真实人群分位 |
| W10 兼容 | 锁定 Playwright/WebDriver 及二进制；分别执行承诺品牌浏览器、真机/WebView、输入法和 AT 矩阵；使用特性检测关闭可选能力并重跑必要路径 | 补丁 WebKit 不代表 iOS Safari；UA 字符串不代表实际能力；无可选 API 时仍可合法退化；布局容差不掩盖语义/交易差异 |
| W11 发行 | 用真实构建清单请求每个入口/Chunk/Worker 与摘要；旧标签冻结后在新版发行再 import；旧客户端/新 API、反向组合、离线恢复和回滚分别执行 | 不可变 URL 字节不被覆盖，旧资源闭包可获得；HTML/CDN/Worker/Schema/API 版本分别记录；代码回滚不等于已发业务或数据回滚 |

输入法验证必须实际启用目标系统输入法；Playwright `fill`、`insert_text` 或构造 CompositionEvent 只能证明相应脚本路径。屏幕阅读器验证需实际朗读与操作证据，自动工具提示不等于符合性结论。系统 IME、AT、品牌/真机矩阵没有相应证据时保持 `not-run`。

## 4. 后端的真实执行动作

| 文档 | 具体输入、工具与故障屏障 | 权威观察与合格判据 |
|---|---|---|
| B01 通用基线 | 完整 API→持久提交→事件→消费者→业务终点；每阶段保留独立身份和受理/耐久/履约证据；慢依赖、撤权、重启和回滚 | 不因 HTTP/RPC 成功、Confirm、ACK、Trace 或 Ready 跨阶段推定终态；合法单体无需强拆 |
| B02 领域 | 有权需求样例、金额/单位/时间边界、同字不同上下文、实体重建、非法状态转换；属性测试与所有真实入口/持久/导出逐字段对比 | 守恒、身份、精度和必要关联不变量完整；CQRS/聚合/服务拆分须有实际价值，允许合法简单实现 |
| B03 HTTP | `curl -i` 或固定 SDK 经实际代理执行协商、条件读写、重复键/冲突、分页变更、Range、PATCH 整体失败、202 后续查询 | 保存真实状态/头/正文和权威副作用；失败前置条件无写入，旧 ETag 不被内存检查后并发穿透；2xx/202 不能冒充异步履约 |
| B04 RPC/流 | 锁定生成 SDK 的 unary/客户端流/服务端流/双向流，慢读、半关闭、写不读、压缩/大小、deadline、断开后回读；grpcurl 仅覆盖它实际能表达的路径 | 消息及最终 trailers/status 分别核对，write 完成不等于出网/业务提交；应用派生工作停止和外部结果独立确认 |
| B05 服务权限 | 低权/跨租户/撤销身份直接走 API、RPC、订阅、任务、导出；错 alg/issuer/aud/typ、过期/未知密钥、旧授权和批量混合对象 | 每个对象/字段/阶段按当前合法权利，无权限数据不出现在错误、缓存或外效；DPoP 方法/URI/密钥/时间证明不能替代领域授权 |
| B06 事务 | 固定真实引擎版本/隔离/索引，用两个连接按屏障交错；先查后写、范围缺失、跨行写偏斜、死锁、序列化失败、提交断响应 | 原始 SQL、连接状态、行数/错误码、提交前后全不变量及永久领域身份；重试完整事务，不把 SQLite 结果外推到其他引擎 |
| B07 消息 | 实际 Broker、队列类型/复制/ACK/事务配置；在 Outbox 提交前后、发布 Confirm 前后、Inbox 事务前后和 ACK 前后杀进程；倒序、重复、毒消息、DLQ 修复及历史回放 | 源业务/Outbox/Broker/Inbox/目标效果分阶段对账；分区 checkpoint 只越过已耐久连续前缀；不可交换增量缺版不得静默丢弃 |
| B08 工作流 | 固定引擎/SDK、历史与版本，主方法前合法 Signal、Worker 崩溃/重放、旧租约迟到、未知外效、补偿失败/并发他者更新 | 合法早到消息可持久缓冲，错相关/越权拒绝；旧执行者在目标边界被 fence；补偿按当前业务权利不直接覆盖旧快照；待履约始终可查 |
| B09 缓存 | 真实源库/缓存/CDC/索引；用屏障暂停旧读→新写失效→新值填入→旧读恢复；再逐出版本墓碑、失效断线、旧备份回灌 | 源版本下界/水位和权限为 oracle；不得只因 TTL、缓存为空、通知曾发出声称最新；非安全陈旧读依合同可合法接受 |
| B10 流量 | 固定根意图预算及各层重试，真实代理/服务施加 arrival-rate、慢消费者、热租户、外部限额、摘流/恢复与 hedging | 记录根业务数、真实尝试/队列年龄、已受理义务、未知外效和共享依赖上限；本地限流不冒充全局配额；资源熔断不冒充统一状态机 |
| B11 可观测性 | 固定已知完整业务事件集复算 SLI、delta/cumulative/reset/缺失和直方图；真实 OTLP receiver 返回填充 partial_success、断流和重试；开放/封闭负载分别记录到达/完成 | 填充 partial_success 不整体重试；接受不等于耐久/可查询；P99 不可平均；监测故障不能让未知或缺失变成零/成功 |
| B12 发布恢复 | 部署只读版本清单，真实引擎扩展/回填/收缩和隔离恢复；旧 Writer、DLQ、离线客户端、备份程序与新 Schema 交叉 | Pod template 回滚不能代表数据/外效撤销；恢复须跨源/投影/消息/外部收据对账；删旧依赖前证明支持窗和恢复闭包结束 |
| B13 合同/E2E | 从独立需求 oracle 生成消费者和真实提供方反例；同数据跨入口、真实代理、实际 SDK/Broker/引擎；分别注入拒绝、丢失、重复、乱序、未知与恢复 | 测试不从被测输出抄 expected；Mock/Schema/CI 不冒充实际服务；错误变异必须使断言失败，合法邻例不得误拒；外部最终收讫独立核验 |

### 4.1 HTTP 的可执行输入形状

在隔离的合成 API 上将 `BASE`、`TOKEN_A`、资源及接口名替换为已固定合同。令牌只经运行时秘密入口传入，证据删去凭据而保留身份角色。

```sh
curl -i -H "Authorization: Bearer $TOKEN_A" "$BASE/items/x"
curl -i -X PATCH -H "Authorization: Bearer $TOKEN_A" \
  -H 'If-Match: "version-1"' -H 'Content-Type: application/merge-patch+json' \
  --data '{"title":"new"}' "$BASE/items/x"
curl -i -X POST -H "Authorization: Bearer $TOKEN_A" \
  -H 'Idempotency-Key: intent-1' -H 'Content-Type: application/json' \
  --data '{"amount_minor":100,"currency":"CNY"}' "$BASE/orders"
```

重复最后一个请求使用同意图键和同指纹；异参复用需按目标合同拒绝。独立尝试标识另行记录。测试代理在服务器持久化后切断响应，再查询操作身份及永久订单唯一性；一次“查无”必须保持可能迟到，不另造意图扣第二次。没有目标幂等/栅栏保证时不把这些命令解释为无条件安全重试。

### 4.2 引擎双连接屏障

PostgreSQL 18 用 `psql "$TEST_DATABASE_URL" -X` 的两个会话：固定 `BEGIN ISOLATION LEVEL REPEATABLE READ` 或 `SERIALIZABLE`，读合成约束记录，屏障后分别改不同记录并提交；完整复算跨行约束，记录 40001 和整事务重试。序列变化及事务外通知另记。MySQL 8.4 用 `mysql` 两连接固定隔离：分别比较普通一致性 `SELECT` 与 `SELECT ... FOR UPDATE`/`UPDATE`，并固定唯一点查和范围索引。锁等待/范围边界不能从其他引擎报告继承。SQLite 局部脚本已有 WAL 真实交错；新增产品引擎测试的 SQL、驱动版本和实际输出必须另留证。

### 4.3 Broker、工作流、缓存与恢复

按项目锁定的官方客户端编写 publisher/consumer/worker 脚本，显式屏障在真实提交、Confirm、ACK 前后暂停，控制器只终止测试进程。消息身份记录 `tenant / consumer-scope / source / event-id / delivery / partition / offset`；业务意图与它们分别编号。生产者先落业务再单独存 Outbox、消费者先存 Inbox 再业务的错误版本必须分别复现缺事件/丢处理；合法独立来源及消费范围应均能处理。

缓存夹具在旧读结果取得后暂停，提交新源版本及失效，恢复旧读观察填充写入的版本判断，再清掉普通值仍保留必要版本 floor/墓碑。工作流导出历史后按引擎重放 API 验证旧历史与新代码；合法早到 Signal 的持久受理、处理器消费和下游履约为不同观察点。隔离恢复需同时对照基础备份/WAL、Outbox、消费水位、缓存/索引和外部操作收据，不只检查数据库能启动。

上述真实服务/引擎/AT 入口是验收合同，不是已执行结果。逐机制状态以相应原始证据为准；局部标准库通过不能覆盖整篇文档、整个真实产品或独立安全/符合性结论。


### 可选真实浏览器入口

默认离线回归不导入Playwright、不启动浏览器或HTTP夹具；10个真实浏览器用例明确报告skipped/not-run，不计为浏览器通过。只有在已核可用的目标环境显式设置`STANDARDS_RUN_BROWSER_TARGETS=1`才执行，保持Chromium沙箱开启；环境缺少必要能力时记录未运行，不关闭沙箱来改变测试前提。需安装与该环境相符的Playwright和Chromium版本，实际版本写入结果；这里不自动安装。原始运行结果输出到唯一的临时证据目录，可用`STANDARDS_BROWSER_EVIDENCE_DIR`选择有权保存位置，不覆盖旧证据，也不修改规范正文。IME、AT和跨浏览器仍需各自目标合同。


### 浏览器可执行文件 / Browser executable

浏览器目标显式启用后，默认可执行文件为`/usr/bin/chromium`；不同安装位置用`STANDARDS_BROWSER_EXECUTABLE`给出已核官方工具的准确绝对路径。运行记录保存该值与实际browser version；工具路径不是浏览器版本或来源证明。沙箱始终开启，缺驱动、路径、loopback能力或沙箱能力时保留失败原始输出，不改为跳过通过，也不关闭安全设置。

```sh
STANDARDS_RUN_BROWSER_TARGETS=1 STANDARDS_BROWSER_EXECUTABLE=/absolute/path/to/chromium python -B -m unittest tests.test_web_backend_browser_contracts -v
```

After explicitly enabling the browser target, select an already verified official executable by absolute path if it is not installed at the default location. The result records the path and observed version. Keep the sandbox enabled; missing prerequisites are failures or not-run facts, never browser passes.

### 合成金额入口 / Synthetic amount input

`local_contracts.canonical_amount`只为本SQLite夹具接受正的完整分值：十进制文本、整数、Decimal，或其实际二进制值恰可精确表示完整分值的原生float。`1`、`1.0`、`1.00`、`1.2300`的十进制写法合法；native `1.0`也合法，但二进制`0.1`不是准确分值输入，应使用文本`"0.10"`。非零多余小数位不因Decimal上下文精度而被舍去。输入表示最多1024字符，分值不超过SQLite有符号64位整数上限；超界拒绝，不截断、不自动转换币种或决定真实货币最小单位。

The fixture requires exact positive whole cents within SQLite signed-int64 range and a 1024-character input budget. Decimal spellings with trailing zeroes are legal. Native floats retain their exact binary value rather than a rounded string interpretation. These are fixture limits, not a universal currency policy.
