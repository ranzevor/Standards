# 运行、协议与集成领域来源命题

引用日期：2026-10-23。各条目记录来源版本、章节、支持命题及适用边界；条款编号关联具体消费方。

## RP01 · iCalendar

- 发布者：IETF/RFC Editor；版本/性质：RFC5545, September 2009 / Standards Track。
- 原始入口：[iCalendar](https://www.rfc-editor.org/rfc/rfc5545.html)；引用章节：§3.3.5、3.3.6、3.3.10、3.8.5.1–3。
- 支持命题：显式带TZID的重复DATE-TIME用第一次，不存在值用gap前偏移；RRULE生成的无效日期/不存在时刻忽略且不计数；包含集合去重后EXDATE优先，保留DTSTART关联身份。浮动时间、名义/精确持续时间分开。
- 不支持的推论：业务补跑、期限和日历更新策略由调度器合同规定；RRULE、时区组件及更新链按所选实现处理。
- 支持条款：AUT-TIME-02, AUT-TIME-03, AUT-TIME-04。

## RP02 · HTTP Semantics

- 发布者：IETF/RFC Editor；版本/性质：RFC9110/STD97, June 2022 / Internet Standard。
- 原始入口：[HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)；引用章节：§9.2.2、10.2.3、15.3.3。
- 支持命题：幂等关注重复请求预期作用，不要求相同响应；非幂等自动重试须有幂等语义或未应用依据；202表示已接受但处理未完成，Retry-After解释须按实际状态/服务。
- 不支持的推论：不定义业务幂等键TTL、操作级查询强度或跨系统恰好一次；这些是组织综合控制。
- 支持条款：G-STATE-05, SDK-API-05, AUT-SYNC-01, AUT-SYNC-04, AUT-EFFECT-04, AUT-EFFECT-05, AUT-EFFECT-06, AUT-RPA-02。

## RP03 · CronJob

- 发布者：Kubernetes；版本/性质：rolling page, version navigation v1.37 observed 2026-10-23 / Implementation documentation。
- 原始入口：[CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)；引用章节：Job creation; Schedule suspension; Time zones。
- 支持命题：官方说明调度近似，可能同一时间创建两个或不创建Job；suspend不影响已启动Job；时区使用timeZone字段而非schedule内TZ/CRON_TZ。
- 不支持的推论：不强制Kubernetes，不将当前滚动页面套到所有集群；Job创建不是业务完成或全局一次。
- 支持条款：AUT-TIME-01, AUT-TIME-04, AUT-TIME-05。

## RP04 · Validating webhook deliveries

- 发布者：GitHub；版本/性质：rolling 2026-10-23 / Product documentation。
- 原始入口：[Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)；引用章节：Validating webhook deliveries; Troubleshooting。
- 支持命题：GitHub HMAC-SHA256以原始payload字节计算并安全比较；先JSON重序列化会改变所签材料。
- 不支持的推论：该HMAC不自动签X-GitHub-Delivery/自定义时间头，不证明当前订阅权限或新鲜度。
- 支持条款：AUT-HOOK-01, AUT-HOOK-03。

## RP05 · Best practices for using webhooks

- 发布者：GitHub；版本/性质：rolling 2026-10-23 / Product guidance。
- 原始入口：[Best practices for using webhooks](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)；引用章节：Use X-GitHub-Delivery; Check event type and action; Respond within 10 seconds。
- 支持命题：重送保留原X-GitHub-Delivery；需检查事件/action并按产品接收时限及时响应。
- 不支持的推论：delivery头的命名不构成其被body HMAC认证的证明；10秒非所有Webhook通用常量，文档不提供业务效果恰好一次。
- 支持条款：AUT-HOOK-02, AUT-HOOK-03, AUT-HOOK-04, AUT-RPA-03。

## RP06 · AIP-158 Pagination

- 发布者：Google；版本/性质：Approved AIP158; page observed 2026-10-23 / API design guidance。
- 原始入口：[AIP-158 Pagination](https://google.aip.dev/158)；引用章节：Guidance; Opacity; Expiring page tokens。
- 支持命题：Google该契约允许非末页零结果；next_page_token控制终止，续页其他参数保持，page_size有明确例外；token不授予访问权限，可过期。
- 不支持的推论：不把Google字段、默认页数/期限或快照能力推广给全部服务；具体连接器仍消费提供方合同。
- 支持条款：SDK-API-06, AUT-SYNC-01, AUT-SYNC-02。

## RP07 · Atomic Commit In SQLite

- 发布者：SQLite；版本/性质：rolling technical explanation observed 2026-10-23 / Implementation design documentation。
- 原始入口：[Atomic Commit In SQLite](https://www.sqlite.org/atomiccommit.html)；引用章节：§2 Hardware assumptions; §3.7–3.11; §4; §9。
- 支持命题：事务原子性依日志/锁/flush顺序及硬件/OS假设；write返回可早于稳定存储，fsync和设备诚实性影响恢复保证。
- 不支持的推论：不把Python内存模型、单机进程重启或SQLite配置推广为真实断电/分布式耐久；不指定全部项目必须SQLite。
- 支持条款：G-STATE-04, AUT-HOOK-02, AUT-SYNC-02, AUT-SYNC-05, AUT-EFFECT-01, AUT-EFFECT-02, AUT-EFFECT-03, AUT-EFFECT-06。

## RP08 · os

- 发布者：Python Software Foundation；版本/性质：Python3.12 documentation; page3.12.15 observed / Runtime API documentation。
- 原始入口：[os](https://docs.python.org/3.12/library/os.html)；引用章节：os.replace; os.fsync; file descriptor paths。
- 支持命题：replace在成功条件下给POSIX原子重命名，可因跨文件系统失败；fsync与缓冲文件flush是不同接口层。
- 不支持的推论：原子可见不等于掉电耐久、跨多文件事务或所有网络FS相同语义；文件/目录持久依平台验证。
- 支持条款：G-STATE-04, CLI-PROC-02, CLI-PROC-05, CLI-PKG-04, CLI-EXT-01, CLI-EXT-02, AUT-SYNC-05, AUT-EFFECT-02。

## RP09 · zoneinfo

- 发布者：Python Software Foundation；版本/性质：Python3.12 documentation / Runtime API documentation。
- 原始入口：[zoneinfo](https://docs.python.org/3.12/library/zoneinfo.html)；引用章节：Using ZoneInfo; Data sources; fold example。
- 支持命题：使用系统IANA时区数据或first-party tzdata；fold区分偏移回拨产生的歧义时刻。
- 不支持的推论：直接给datetime附tzinfo不自动验证不存在时间，更不实现RFC5545；测试需绑定实际时区数据。
- 支持条款：G-SIM-01, AUT-TIME-02。

## RP10 · subprocess

- 发布者：Python Software Foundation；版本/性质：Python3.12 documentation / Runtime API documentation。
- 原始入口：[subprocess](https://docs.python.org/3.12/library/subprocess.html)；引用章节：Frequently Used Arguments; Security Considerations; Popen.wait/communicate; Windows notes。
- 支持命题：参数序列保留分词；stdout/stderr PIPE需持续排空以免死锁；communicate缓冲内存且超时不自动杀子进程，信号/返回码有平台差异。
- 不支持的推论：直接argv不消除被调工具选项注入；不认证任意CLI/PowerShell、RPA定位或分布式结果。
- 支持条款：CLI-PROC-01, CLI-PROC-03, CLI-PROC-04, CLI-PROC-05, CLI-EXT-03, AUT-RPA-01, AUT-RPA-04。

## RP11 · Coroutines and Tasks

- 发布者：Python Software Foundation；版本/性质：Python3.12 documentation / Runtime API documentation。
- 原始入口：[Coroutines and Tasks](https://docs.python.org/3.12/library/asyncio-task.html)；引用章节：Task cancellation; Task.cancel; Timeouts。
- 支持命题：cancel请求通过CancelledError注入，协程可清理/延迟甚至抑制；finally清理后通常传播，发cancel并不保证已取消。
- 不支持的推论：本地Task取消不提供远端撤销/事务回滚，不强制其他运行时同一异常API。
- 支持条款：CLI-PROC-05, SDK-API-02, SDK-API-03。

## RP12 · Semantic Versioning

- 发布者：SemVer project；版本/性质：SemVer2.0.0 / Versioning specification。
- 原始入口：[Semantic Versioning](https://semver.org/spec/v2.0.0.html)；引用章节：§1–3、6–8。
- 支持命题：采用SemVer者声明公开API，已发行版本内容不修改；主/次/补丁按公开API兼容含义变动。
- 不支持的推论：不是所有工具必须SemVer，不证明ABI/消费者行为；未发行草案修订不当成已发行制品替换。
- 支持条款：CLI-PKG-01, CLI-PKG-04。

## RP13 · JSON

- 发布者：IETF/RFC Editor；版本/性质：RFC8259/STD90, December2017 / Internet Standard。
- 原始入口：[JSON](https://www.rfc-editor.org/rfc/rfc8259.html)；引用章节：§4–8。
- 支持命题：对象名称唯一性是互操作建议；数组有序，大整数超常见binary64精确范围需独立合同，跨系统JSON使用UTF-8。
- 不支持的推论：语法合法不证明业务值/权限/精度；本包示例限制JSON输入是模型范围而非全部CLI强制格式。
- 支持条款：CLI-PROC-03, SDK-API-01, AUT-SYNC-03, AUT-EFFECT-01。

## RP14 · Language Server Protocol

- 发布者：Microsoft；版本/性质：LSP3.17 source commit baf2db31b5fb314a8f358f9a839d3c66e9d98734 / Protocol specification。
- 原始入口：[Language Server Protocol](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)；引用章节：Base protocol; Cancellation; initialize; didChange; shutdown; exit。
- 支持命题：Content-Length是UTF-8内容字节数，头ASCII；initialize先行，取消仍须响应；能力缺省不免除2.x强制基线；文档版本/顺序与位置编码协商；shutdown响应与exit不同。
- 不支持的推论：适用LSP 3.17及其固定源码；普通CLI仅在提供语言服务协议接口时消费本命题。
- 支持条款：CLI-EXT-04, CLI-EXT-05。

## RP15 · Platform compatibility tags

- 发布者：PyPA；版本/性质：rolling specification observed2026-10-23 / Packaging specification。
- 原始入口：[Platform compatibility tags](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)；引用章节：Overview; Python Tag; ABI Tag; Platform Tag。
- 支持命题：wheel兼容标签分别描述Python实现/版本、ABI、平台；none/any不代表带原生代码的任意平台包自然可用。
- 不支持的推论：只是Python画像，不认证实际包完整、许可或跨生态安装成功。
- 支持条款：CLI-PKG-02, CLI-PKG-03。

## RP16 · C API Stability

- 发布者：Python Software Foundation；版本/性质：Python3.12 documentation / Runtime ABI specification。
- 原始入口：[C API Stability](https://docs.python.org/3.12/c-api/stable.html)；引用章节：Stable ABI; Limited C API; Platform Considerations。
- 支持命题：Limited API/Stable ABI有明确边界；编译器、下层库、编译选项、OS/架构是平台条件；源码兼容不等二进制兼容。
- 不支持的推论：不表示任意FFI安全，不免除分配释放/异常边界或真实消费端测试。
- 支持条款：CLI-PKG-02。

## RP17 · Physics interpolation introduction

- 发布者：Godot；版本/性质：Godot4.5 / Engine implementation documentation。
- 原始入口：[Physics interpolation introduction](https://docs.godotengine.org/en/4.5/tutorials/physics/interpolation/physics_interpolation_introduction.html)；引用章节：Physics ticks and rendered frames。
- 支持命题：物理tick与渲染frame是不同频率，固定物理步长不保证呈现帧一致；插值用于呈现平滑。
- 不支持的推论：不提供所有游戏物理确定性、统一帧率或真实设备性能通过。
- 支持条款：G-SIM-01, G-SIM-02, G-SIM-04, G-DELIVERY-02, G-DELIVERY-03。

## RP18 · Random number generation

- 发布者：Godot；版本/性质：Godot4.5 / Engine implementation documentation。
- 原始入口：[Random number generation](https://docs.godotengine.org/en/4.5/tutorials/math/random_number_generation.html)；引用章节：Global scope versus RandomNumberGenerator; seed/state。
- 支持命题：RandomNumberGenerator可独立实例及seed/state，重设种子和恢复抽样状态不同。
- 不支持的推论：不承诺跨引擎/版本/并发顺序逐位复现；不能用随机教程证明完整应用确定性。
- 支持条款：G-SIM-03。

## RP19 · Simulation / FAQ determinism

- 发布者：Box2D；版本/性质：Simulation page3.2.0; FAQ page3.1.0 separately observed2026-10-23 / Engine documentation。
- 原始入口：[Simulation / FAQ determinism](https://box2d.org/documentation/md_simulation.html)；引用章节：Determinism; FAQ Is Box2D deterministic。
- 支持命题：Simulation把64位跨平台确定性联系到创建顺序、精确数学/禁浮点收缩和特定数学实现，并明确应用仍可能非确定；FAQ3.1.0说没有rollback determinism。
- 不支持的推论：两个页面版头不同，不混成同一版本认证；不把Box2D条件推广到全部Godot/Unity/3D物理，也不推断游戏回滚已验。
- 支持条款：G-SIM-02, G-SIM-05。

## RP20 · High-level multiplayer

- 发布者：Godot；版本/性质：Godot4.5 / Engine implementation documentation。
- 原始入口：[High-level multiplayer](https://docs.godotengine.org/en/4.5/tutorials/networking/high_level_multiplayer.html)；引用章节：High/low level API; RPC authority; Managing connections。
- 支持命题：高层API抽象不替代具体拓扑/权威和RPC权限选择，平台可用能力有差别。
- 不支持的推论：不采用页面概括TCP/UDP性能为普遍定律；不证明重连栅栏、耐久结算或真实网络已验。
- 支持条款：G-STATE-02, G-STATE-03。

## RP21 · Import process

- 发布者：Godot；版本/性质：Godot4.5 / Engine implementation documentation。
- 原始入口：[Import process](https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/import_process.html)；引用章节：Importing assets; Changing import parameters。
- 支持命题：导入派生藏于.godot/imported；导入资源按ResourceLoader加载，直接FileAccess在编辑器能读原件不代表导出包可读。
- 不支持的推论：不证明素材许可、目标GPU/媒体可用或缓存身份自动满足本规范。
- 支持条款：G-ASSET-01, G-ASSET-02, G-ASSET-05, G-DELIVERY-04。

## RP22 · Command line tutorial

- 发布者：Godot；版本/性质：Godot4.5 / Engine tool documentation。
- 原始入口：[Command line tutorial](https://docs.godotengine.org/en/4.5/tutorials/editor/command_line_tutorial.html)；引用章节：Exporting; Running a script; --import/--export-release。
- 支持命题：导出使用editor二进制及匹配导出模板；preset匹配export_presets.cfg，输出相对project.godot目录；headless避免窗口，脚本继承SceneTree/MainLoop。
- 不支持的推论：命令存在不证明任意项目可构建或发行运行；headless不能验证GUI/音画。旧错误export路径失败保留。
- 支持条款：G-DELIVERY-04。

## RP24 · XAG107 Input / Guidelines

- 发布者：Microsoft；版本/性质：XAG V3.2 index dated2023-06-08; rolling guideline read2026-10-23 / Accessibility best-practice guidance。
- 原始入口：[XAG107 Input / Guidelines](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/107)；引用章节：Goal; Input remapping; Guidelines introduction。
- 支持命题：输入方式可能排除玩家；建议重映射并在提示/教程反映新映射。索引明确XAG不是法律合规清单。
- 不支持的推论：不把指南建议自动当全部游戏同一强制选项，也不声明真实目标玩家任务或法律符合性已验。
- 支持条款：G-STATE-01, G-DELIVERY-01。

## RP25 · WCAG2.2

- 发布者：W3C；版本/性质：W3C Recommendation2024-12-12 / Recommendation。
- 原始入口：[WCAG2.2](https://www.w3.org/TR/2024/REC-WCAG22-20241212/)；引用章节：Abstract; §5 conformance scope。
- 支持命题：WCAG2.2针对Web内容的可测试成功准则，完整流程/范围影响符合性声明。
- 不支持的推论：不能把Web指南合规直接等同原生整款游戏符合性；本包未逐成功准则验收。
- 支持条款：G-DELIVERY-01。

## RP27 · Saving games

- 发布者：Godot；版本/性质：Godot4.5 / Engine tutorial。
- 原始入口：[Saving games](https://docs.godotengine.org/en/4.5/tutorials/io/saving_games.html)；引用章节：Identify persistent objects; Serializing。
- 支持命题：应识别跨会话保存对象及其数据，示例提供序列化/加载入口。
- 不支持的推论：教程示例不保证原子保存、断电耐久或完整物理求解器快照；这些需要项目独立设计/测试。
- 支持条款：G-STATE-04, G-ASSET-02。

## RP28 · Playing videos

- 发布者：Godot；版本/性质：Godot4.5 / Engine implementation documentation。
- 原始入口：[Playing videos](https://docs.godotengine.org/en/4.5/tutorials/animation/playing_videos.html)；引用章节：Supported playback formats; VideoStreamPlayer。
- 支持命题：该版核心VideoStreamPlayer只支持Ogg Theora及可选Vorbis，扩展可提供其他编码；扩展名本身不证明有视频。
- 不支持的推论：不把格式文档当目标解码/音画验收，不强制所有引擎Theora；版权/专利决定不由本包下结论。
- 支持条款：G-SIM-05, G-ASSET-03, G-DELIVERY-02。

## RP29 · glTF2.0 catalogue and registry

- 发布者：ISO/Khronos；版本/性质：ISO/IEC12113:2022 edition1,2022-07 / International Standard catalogue; registry。
- 原始入口：[glTF2.0 catalogue and registry](https://www.iso.org/standard/83990.html)；引用章节：Catalogue abstract/status; registry entry。
- 支持命题：官方目录确认glTF2.0是运行时3D资产交付格式；登记入口可定位格式规范。
- 不支持的推论：只核目录/入口，完整格式正文首次超时，未据此创制字段级要求或宣称glTF一致性；更不证明材料权利。
- 支持条款：G-ASSET-04。

## RP30 · OpenXR registry

- 发布者：Khronos；版本/性质：OpenXR1.1 family registry observed2026-10-23 / API registry。
- 原始入口：[OpenXR registry](https://registry.khronos.org/OpenXR/)；引用章节：Registry entries。
- 支持命题：XR API有独立规范/扩展/一致性入口，采用者须绑定实际版本与扩展。
- 不支持的推论：用作可选格式和API导航；采用方按所选格式版本确定具体算法和实现条件。
- 支持条款：G-ASSET-04。

## RP31 · TCP

- 发布者：IETF/RFC Editor；版本/性质：RFC9293/STD7,August2022 / Internet Standard。
- 原始入口：[TCP](https://www.rfc-editor.org/rfc/rfc9293.html)；引用章节：§2.2、3.6.1。
- 支持命题：TCP提供可靠有序字节流，不给应用消息边界；正常关闭按方向，接收EOF不意味不能返回最终响应。
- 不支持的推论：字节确认不提供持久业务提交或应用恰好一次；端点死亡可能使结果未知。
- 支持条款：G-STATE-02, G-STATE-05, SDK-API-05, NET-WIRE-01, NET-WIRE-03。

## RP32 · TLS1.3

- 发布者：IETF；版本/性质：RFC9846 Proposed Standard,July2026 / Standards Track。
- 原始入口：[TLS1.3](https://datatracker.ietf.org/doc/html/rfc9846)；引用章节：§1、2.2、6.1、8。
- 支持命题：正式9846废止8446；认证可含PSK但不能低熵口令；TLS写向关闭与应用完整分开；同一0-RTT握手每服务实例最多接受一次，跨实例及客户端重试仍有风险。
- 不支持的推论：不自动证明目标库实现该版要求或所有部署业务恰好一次；RFC Editor入口429，正式Datatracker正文成功。
- 支持条款：SDK-API-04, NET-WIRE-03, NET-WIRE-04。

## RP33 · Service Identity in TLS

- 发布者：IETF/RFC Editor；版本/性质：RFC9525,November2023 / Standards Track。
- 原始入口：[Service Identity in TLS](https://www.rfc-editor.org/rfc/rfc9525.html)；引用章节：§1.2–1.3、6。
- 支持命题：基于证书服务身份核预期参考身份与SAN呈现身份；叶证书名字匹配不替代完整路径验证。
- 不支持的推论：不要求合法PSK/指纹profile提供证书链，也不提供对象授权。
- 支持条款：SDK-API-04, NET-WIRE-04。

## RP34 · UDP Usage Guidelines

- 发布者：IETF/RFC Editor；版本/性质：RFC8085/BCP145,March2017 / Best Current Practice。
- 原始入口：[UDP Usage Guidelines](https://www.rfc-editor.org/rfc/rfc8085.html)；引用章节：§3.1–3.5。
- 支持命题：UDP无内建拥塞机制，应用需选择适当拥塞/聚合负载及消息尺寸/可靠性设计；避免超有效MTU导致脆弱分片。
- 不支持的推论：不同数据量/单播多播有差别，不把某示例速率/算法当全领域统一门槛。
- 支持条款：NET-WIRE-01, NET-WIRE-05, NET-FLOW-02。

## RP35 · WebSocket over HTTP2

- 发布者：IETF/RFC Editor；版本/性质：RFC8441,September2018 / Standards Track。
- 原始入口：[WebSocket over HTTP2](https://www.rfc-editor.org/rfc/rfc8441.html)；引用章节：§3–5、7。
- 支持命题：扩展CONNECT须SETTINGS_ENABLE_CONNECT_PROTOCOL启用，h1 Upgrade/101语义不能照搬h2。
- 不支持的推论：服务端配置一个协议不证明完整代理路径支持；不保证应用恢复。
- 支持条款：NET-WIRE-02。

## RP36 · WebSocket over HTTP3

- 发布者：IETF/RFC Editor；版本/性质：RFC9220,June2022 / Standards Track。
- 原始入口：[WebSocket over HTTP3](https://www.rfc-editor.org/rfc/rfc9220.html)；引用章节：§3、5。
- 支持命题：h3使用相应扩展CONNECT语义及独立注册设置，默认不启用；与h2的适配不是自动全端支持。
- 不支持的推论：不从启用QUIC推出所有WS客户端/代理兼容。
- 支持条款：NET-WIRE-02。

## RP37 · QUIC DATAGRAM

- 发布者：IETF/RFC Editor；版本/性质：RFC9221,March2022 / Standards Track。
- 原始入口：[QUIC DATAGRAM](https://www.rfc-editor.org/rfc/rfc9221.html)；引用章节：§3、5–5.4。
- 支持命题：扩展需协商，报文不丢失重传，无自身分片；ACK只证明接收端传输处理，不保证应用处理。
- 不支持的推论：不用于证明业务成功或任意大消息；仍受拥塞和路径尺寸约束。
- 支持条款：NET-WIRE-05, NET-FLOW-02。

## RP38 · QUIC Transport

- 发布者：IETF/RFC Editor；版本/性质：RFC9000,May2021 / Standards Track。
- 原始入口：[QUIC Transport](https://www.rfc-editor.org/rfc/rfc9000.html)；引用章节：§2、8.2、9。
- 支持命题：每流可靠有序但跨流不保证顺序；迁移/路径验证有握手/参数前提，NAT重绑定与主动迁移不同。
- 不支持的推论：对端丢连接状态不能靠迁移重建应用订阅；新路径不是新对象授权。
- 支持条款：NET-WIRE-05, NET-FLOW-05。

## RP39 · HTTP2

- 发布者：IETF/RFC Editor；版本/性质：RFC9113,June2022 / Standards Track。
- 原始入口：[HTTP2](https://www.rfc-editor.org/rfc/rfc9113.html)；引用章节：§5.2、5.2.2、6.9。
- 支持命题：流/连接窗口逐跳/有方向，只有DATA消耗本版流控窗口；端点及时读处理帧以免WINDOW_UPDATE被饿死。
- 不支持的推论：流控不自动约束所有代理/应用队列，也不等于拥塞控制。
- 支持条款：NET-FLOW-01。

## RP40 · QUIC Loss Detection

- 发布者：IETF/RFC Editor；版本/性质：RFC9002,May2021 / Standards Track。
- 原始入口：[QUIC Loss Detection](https://www.rfc-editor.org/rfc/rfc9002.html)；引用章节：§5–7。
- 支持命题：RTT估计、丢失检测、PTO及拥塞控制是传输对象，PTO退避有协议规则。
- 不支持的推论：不把PTO/丢包率当业务失败率，不重编协议常量。
- 支持条款：NET-FLOW-02。

## RP41 · WebSocket

- 发布者：IETF/RFC Editor；版本/性质：RFC6455,December2011 / Standards Track。
- 原始入口：[WebSocket](https://www.rfc-editor.org/rfc/rfc6455.html)；引用章节：§7.2.3、7.4.1。
- 支持命题：异常关闭后建议初始随机延迟及递增退避；1006用于本地异常表示，不得放Close帧。
- 不支持的推论：重连不保证历史已补，1006不证明对端业务拒绝；建议示例区间非全组织强制值。
- 支持条款：NET-FLOW-03, NET-FLOW-05。

## RP42 · HTML SSE

- 发布者：WHATWG；版本/性质：Living Standard updated2026-10-22 observed2026-10-23 / Living Standard; authoring notes informative。
- 原始入口：[HTML SSE](https://html.spec.whatwg.org/multipage/server-sent-events.html)；引用章节：§9.2.3–9.2.7。
- 支持命题：重连携带非空Last-Event-ID，空id可重置；尾事件缺空行不派发。编写提示涉及代理缓冲/空闲关闭。
- 不支持的推论：ID不证明日志保留或持久业务消费；作者提示不是普遍固定心跳阈值。
- 支持条款：NET-FLOW-04, NET-FLOW-05。

## RP43 · Deadlines

- 发布者：gRPC project；版本/性质：rolling guide2026-10-23 / Implementation guide。
- 原始入口：[Deadlines](https://grpc.io/docs/guides/deadlines/)；引用章节：Deadline Propagation; Cancellation。
- 支持命题：传播期限以扣除已耗时间的timeout避免跨机器墙钟偏差，不同语言默认支持不同。
- 不支持的推论：不是所有协议的wire格式，不证明截止时外部效果未提交或撤销。
- 支持条款：NET-FLOW-03, NET-MEDIA-05。

## RP44 · STUN

- 发布者：IETF/RFC Editor；版本/性质：RFC8489,February2020 / Standards Track。
- 原始入口：[STUN](https://www.rfc-editor.org/rfc/rfc8489.html)；引用章节：Abstract; §1–2。
- 支持命题：STUN可发现映射、检查连通、保持绑定，但本身不是完整NAT穿越方案。
- 不支持的推论：获取地址不证明对端可达、用户有权或媒体完成。
- 支持条款：NET-MEDIA-01。

## RP45 · ICE

- 发布者：IETF/RFC Editor；版本/性质：RFC8445,July2018 / Standards Track。
- 原始入口：[ICE](https://www.rfc-editor.org/rfc/rfc8445.html)；引用章节：§2、6–9、11。
- 支持命题：收集、检查、选对、restart分开；restart必须同时更换password与username fragment。
- 不支持的推论：不以候选收集完成判应用可用；实际适用更新需随profile核。
- 支持条款：NET-MEDIA-01, NET-MEDIA-03。

## RP46 · ICE PAC

- 发布者：IETF/RFC Editor；版本/性质：RFC8863,January2021 / Standards Track; updates8445/8838。
- 原始入口：[ICE PAC](https://www.rfc-editor.org/rfc/rfc8863.html)；引用章节：§3–5。
- 支持命题：没有候选对时仍须遵适用的最低等待，不能过早宣告ICE失败。
- 不支持的推论：不使所有路径可达，也不替代媒体/权限测试。
- 支持条款：NET-MEDIA-01。

## RP47 · TURN

- 发布者：IETF/RFC Editor；版本/性质：RFC8656,February2020 / Standards Track。
- 原始入口：[TURN](https://www.rfc-editor.org/rfc/rfc8656.html)；引用章节：§3、7–12。
- 支持命题：allocation、permission、channel独立；数据不刷新allocation，permission固定300秒并由相应请求刷新，按IP不是用户授权。
- 不支持的推论：不允许L6随意改协议常量；不证明具体中继权限/费用/真实可达。
- 支持条款：NET-MEDIA-02。

## RP48 · Consent Freshness

- 发布者：IETF/RFC Editor；版本/性质：RFC7675,October2015 / Standards Track。
- 原始入口：[Consent Freshness](https://www.rfc-editor.org/rfc/rfc7675.html)；引用章节：§5.1–5.2。
- 支持命题：30秒未有效响应须停相应发送；到期旧响应不重建consent；同ICE凭据不得再用于受影响5-tuple，须新session/restart；不发应用数据者的发送consent要求有区别。
- 不支持的推论：设备许可/业务授权/NAT保持都不是consent替代；不是统一心跳间隔。
- 支持条款：NET-MEDIA-03。

## RP49 · WebRTC Security Architecture

- 发布者：IETF/RFC Editor；版本/性质：RFC8827,January2021 / Standards Track。
- 原始入口：[WebRTC Security Architecture](https://www.rfc-editor.org/rfc/rfc8827.html)；引用章节：§4、6.2–6.5、7.4.1。
- 支持命题：设备权限、接收consent、信令信任及DTLS指纹绑定有不同作用；实际证书需匹配受信断言指纹。
- 不支持的推论：不从链路加密推出平台不可解密E2EE，不把文中历史算法直接当所有当今profile。
- 支持条款：NET-MEDIA-04。

## RP50 · WebRTC Data Channels

- 发布者：IETF/RFC Editor；版本/性质：RFC8831,January2021 / Standards Track。
- 原始入口：[WebRTC Data Channels](https://www.rfc-editor.org/rfc/rfc8831.html)；引用章节：§5–6.6。
- 支持命题：SCTP over DTLS支持有序/无序、可靠/部分可靠，通道/关联生命周期及消息约束独立。
- 不支持的推论：不保证业务恰好一次/任意文件完整；不从内部历史SCTP引用断言当前通用SCTP版本。
- 支持条款：NET-MEDIA-04。

## RP51 · WebRTC

- 发布者：W3C；版本/性质：Recommendation2025-03-13; candidate amendments distinguished / Recommendation。
- 原始入口：[WebRTC](https://www.w3.org/TR/2025/REC-webrtc-20250313/)；引用章节：RTCPeerConnection; RTCDataChannel。
- 支持命题：信令/ICE/连接状态不同；DataChannel的ordered、重传策略和bufferedAmount描述各自API语义，排队字节不含全部OS/网络缓冲。
- 不支持的推论：不把candidate amendments当全部已生效，不证明任意浏览器/中继/音画支持。
- 支持条款：NET-MEDIA-01, NET-MEDIA-04。

## RP52 · RTP

- 发布者：IETF/RFC Editor；版本/性质：RFC3550,July2003 / Standards Track。
- 原始入口：[RTP](https://www.rfc-editor.org/rfc/rfc3550.html)；引用章节：Abstract; §1。
- 支持命题：RTP不保证及时/可靠/有序交付或QoS，RTCP用于监测；实时预算需实际端到端证据。
- 不支持的推论：延迟和实时性取决于所选编解码、媒体profile、传输和目标环境。
- 支持条款：NET-MEDIA-05。

## RP53 · DTLS1.3

- 发布者：IETF/RFC Editor；版本/性质：RFC9147,April2022 / Standards Track。
- 原始入口：[DTLS1.3](https://www.rfc-editor.org/rfc/rfc9147.html)；引用章节：§3–4、8。
- 支持命题：DTLS保留报文语义，不提供应用可靠/有序；记录重放检测可选，与0-RTT重放或业务排重不同。
- 不支持的推论：不要求所有WebRTC立即采用DTLS1.3，也不把可选检测写成每实现已有。
- 支持条款：NET-WIRE-05。

## RP54 · High Resolution Time

- 发布者：W3C；版本/性质：Working Draft2026-09-01 / Working Draft。
- 原始入口：[High Resolution Time](https://www.w3.org/TR/2026/WD-hr-time-3-20260901/)；引用章节：§2.1–2.2、7。
- 支持命题：单调时钟不受系统时间调整且限定执行上下文；不能直接比较不同机器/执行的performance.now。
- 不支持的推论：草案不是全平台稳定标准；高精度不保证定时器准时或硬实时。
- 支持条款：NET-MEDIA-05。

## RP55 · GDScript reference

- 发布者：Godot；版本/性质：Godot4.6 / Engine implementation documentation。
- 原始入口：[GDScript reference](https://docs.godotengine.org/en/4.6/tutorials/scripting/gdscript/gdscript_basics.html)；引用章节：Assert keyword; Awaiting signals or coroutines。
- 支持命题：release导出忽略assert且不求值表达式；await信号/协程会交回控制并在完成后恢复。
- 不支持的推论：版本4.6与本包4.5画像分开；不把debug断言作为release输入门禁或调用await就当动作完成。
- 支持条款：standards/L4/game/004-游戏模拟时序、确定性与回放技术规范--v0.1.0.md#6。

## RP56 · The Profiler

- 发布者：Godot；版本/性质：Godot4.5 / Engine tooling documentation。
- 原始入口：[The Profiler](https://docs.godotengine.org/en/4.5/tutorials/scripting/debug/the_profiler.html)；引用章节：The measured data; Scope of measurement。
- 支持命题：Profiler区分frame/physics/idle及测量窗口，自身有开销且不同脚本语言支持有界。
- 不支持的推论：单工具读数不证明目标GPU/设备热态或所有发行版本；不把平均值当全帧预算。
- 支持条款：G-DELIVERY-03。

## RP23 · WebSockets API

- 发布者：WHATWG；版本/性质：Living Standard updated2026-10-19 observed2026-10-23 / Living Standard。
- 原始入口：[WebSockets API](https://websockets.spec.whatwg.org/)；引用章节：§3、5。
- 支持命题：bufferedAmount表示本地待发送应用数据，Ping/Pong不直接暴露给浏览器API。
- 不支持的推论：缓冲变化不是对端应用提交；原生socket能力不能套浏览器。
- 支持条款：E14。

