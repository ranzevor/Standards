# 桌面与移动来源命题

引用日期：2026-10-23。以下条目记录桌面与移动规范采用的官方来源、章节、技术命题和适用边界。具体项目在适配画像中固定SDK及工具版本。

<a id="dm01"></a>

## DM01 · Known Folders

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/shell/known-folders)。
- 身份/章节：动态 Win32 指南；页面更新 2026-07-17；Known Folders advantages。
- 有限命题：标准用户目录可被重定向，包括网络位置；目录名不能代替实际解析结果。
- 不支持：不据此统一其他 OS 的目录，也不推导所有 Known Folder 调用的实现前提。
- 绑定条款：D05、S01、S11。

<a id="dm02"></a>

## DM02 · XDG Base Directory Specification

- 发布者/入口：freedesktop.org，[官方正文](https://specifications.freedesktop.org/basedir/0.8/)。
- 身份/章节：固定 0.8，2021-05-08；§2 Basics；§3 Environment variables。
- 有限命题：数据、配置、状态、缓存、运行目录分工不同；环境目录须为绝对路径，运行目录不能跨完整注销或重启保留。
- 不支持：仅采用 XDG 的实现；不提供网络文件系统持久性保证。
- 绑定条款：D05、S01、S20。

<a id="dm03"></a>

## DM03 · GetFileInformationByHandleEx

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex)。
- 身份/章节：动态 Win32 API；实际 SDK 由采用方锁定；Syntax；Parameters；Remarks。
- 有限命题：接口以实际文件句柄和信息类取得对象资料；对象检查不能只看路径字符串。
- 不支持：文件 ID 不因此永久稳定，也不是业务访问授权；信息类支持依目标核实。
- 绑定条款：D06、I06、S03、S04。

<a id="dm04"></a>

## DM04 · fsync(2)

- 发布者/入口：Linux man-pages project，[官方正文](https://man7.org/linux/man-pages/man2/fsync.2.html)。
- 身份/章节：动态 Linux man-pages；核读日版本所见；STANDARDS 标 POSIX.1-2024；DESCRIPTION；RETURN VALUE；ERRORS。
- 有限命题：文件同步与包含它的目录项同步不同；同步可能报错，文件 rename 可见性不是全部掉电持久性。
- 不支持：不是全平台持久算法或真实硬件断电证明。
- 绑定条款：D07、S06、S13。

<a id="dm05"></a>

## DM05 · FlushFileBuffers

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)。
- 身份/章节：动态 Win32 API；页面更新 2021-10-13；Parameters；Return value；Remarks。
- 有限命题：flush 的对象种类、写权限和返回失败各有条件，不能只凭写操作结束确认持久。
- 不支持：不要求普通应用管理员全卷 flush；不保证任意硬件真实断电行为。
- 绑定条款：D07、S06、S13。

<a id="dm06"></a>

## DM06 · ReplaceFileW

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)。
- 身份/章节：动态 Win32 API；SDK/OS 按项目锁定；dwReplaceFlags；Return value。
- 有限命题：1176、1177 等失败可留下不同路径状态；忽略 ACL 合并错误可能丢失保护。
- 不支持：失败回读要求是组织补充，不提供未经目标实验的替换算法。
- 绑定条款：S07。

<a id="dm07"></a>

## DM07 · QSaveFile

- 发布者/入口：Qt Project，[官方正文](https://doc.qt.io/qt-6/qsavefile.html)。
- 身份/章节：qt-6 滚动文档；页面标识 Qt 6.12.0；引用日期 2026-10-23；Detailed Description；cancelWriting；commit。
- 有限命题：临时文件提交与 direct-write fallback 的取消保护不同；实际直写时 cancelWriting 不能恢复原内容。
- 不支持：只在采用该 API 时激活；页面版本标签不证明发布状态或任意文件系统掉电保证。
- 绑定条款：S05、S08。

<a id="dm08"></a>

## DM08 · The Role of File Coordinators and Presenters

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileCoordinators/FileCoordinators.html)。
- 身份/章节：官方 Documentation Archive；macOS 10.7+ 机制说明；开篇；Using NSDocument and UIDocument。
- 有限命题：协调者、呈现者以及文档对象协作处理共享文件的变更。
- 不支持：不保证拦截所有不参与协议的外部写者；现代 API availability 不由档案决定。
- 绑定条款：D08、S09、S10。

<a id="dm09"></a>

## DM09 · Write-Ahead Logging

- 发布者/入口：SQLite，[官方正文](https://www.sqlite.org/wal.html)。
- 身份/章节：官方滚动引擎文档；机制始于 SQLite 3.7.0，实际引擎另锁；§1；§2；§4。
- 有限命题：WAL 中可包含已提交而尚未回主文件的数据；WAL 的共享内存前提不适合跨主机网络文件系统。
- 不支持：不把单复制主 db 当活跃引擎完整备份；不采用页面未核的版本漏洞结论。
- 绑定条款：D09、D19、DT6-02、DT6-05、S11、S12、S14、S15、S16、S17、S18、S19、S20。

<a id="dm10"></a>

## DM10 · Named Pipe Security and Access Rights

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights)。
- 身份/章节：动态 Win32 指南；页面更新 2021-01-07；默认 security descriptor；access checks；logon SID。
- 有限命题：默认命名管道 DACL 不等于私有；客户端和服务端访问均受实际安全描述符控制。
- 不支持：管道名或自报 PID 不构成业务授权；跨会话策略由具体合同决定。
- 绑定条款：D02、D03、D11、DT3-03、I03、I04、I06、I07、I15。

<a id="dm11"></a>

## DM11 · Security

- 发布者/入口：Electron Project / OpenJS，[官方正文](https://www.electronjs.org/docs/latest/tutorial/security)。
- 身份/章节：滚动 latest 指南，核读 2026-10-23；实际 Electron 版本另锁；§17 Validate the sender of all IPC messages；§20。
- 有限命题：IPC 来自帧与子窗口，需以可信发送上下文限制原生能力；URL 外观不足以证明文档控制者。
- 不支持：示例不是跨平台身份协议；不据页面承诺当前框架已无漏洞。
- 绑定条款：D02、D12、I01、I02、I11、I12、I13、MB5-06。

<a id="dm12"></a>

## DM12 · Develop secure WebView2 apps

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security)。
- 身份/章节：动态 WebView2 指南；运行时版本另锁；Web content and host isolation；source validation。
- 有限命题：WebView 宿主具有浏览器之外的原生资源，宿主与网页隔离和最小桥面是独立边界。
- 不支持：每次回包绑定文档/账号代际是组织补充；不是保证所有 WebView 同一 API。
- 绑定条款：D02、D12、I01、I07、I11、I12、I14、MB5-06、MB5-07。

<a id="dm13"></a>

## DM13 · D-Bus Specification

- 发布者/入口：freedesktop.org，[官方正文](https://dbus.freedesktop.org/doc/dbus-specification.html)。
- 身份/章节：页面标 Version 0.43，revision 2024-10-29；滚动末后修改另核；GetConnectionCredentials；NameOwnerChanged。
- 有限命题：凭证字段可因不可得而省略；总线名称所有者会改变，缺失字段不能当匹配。
- 不支持：使用真实连接身份的动作授权是组织补充；不把总线名字当永续主体。
- 绑定条款：D11、DT3-03、DT3-06、I03、I04、I05、I08、I15。

<a id="dm14"></a>

## DM14 · Sandbox Permissions

- 发布者/入口：Flatpak Project，[官方正文](https://docs.flatpak.org/en/latest/sandbox-permissions.html)。
- 身份/章节：滚动 latest 指南；实际 Flatpak/runtime 另锁；Portals；Permissions guidelines；D-Bus access。
- 有限命题：静态 finish-args 与 portal 选择资源不同；广泛总线/主目录权限会扩大有效能力。
- 不支持：仅 Flatpak 实现；不把某一包模式套到全部 Linux 桌面。
- 绑定条款：D04、D06、I09、I10。

<a id="dm15"></a>

## DM15 · Handle file activation in a Windows app

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/apps/develop/launch/handle-file-activation)。
- 身份/章节：动态 Windows Apps 文档；页面更新 2026-09-26；In this article；Step 1；Step 3；Remarks。
- 有限命题：文件关联需用户选择，清单与运行激活入口分开；来自激活的文件仍可不可信。
- 不支持：不是所有桌面应用必须用 UWP/WinUI 清单；不决定业务去重规则。
- 绑定条款：D10、D13、D23、DT3-01、DT3-02、DT3-04、DT3-05、DT3-07、DT5-06。

<a id="dm16"></a>

## DM16 · Desktop Entry Specification

- 发布者/入口：freedesktop.org，[官方正文](https://specifications.freedesktop.org/desktop-entry/1.5/exec-variables.html)。
- 身份/章节：固定 1.5；§7 The Exec key。
- 有限命题：Exec 引用、字段码和单参数/多参数展开有明确规则；空格、非 ASCII 不得被拆坏。
- 不支持：不是 shell 命令语言；不推广到全部桌面会话或平台。
- 绑定条款：D10、DT3-01、DT3-02、DT3-04。

<a id="dm17"></a>

## DM17 · WM_IME_COMPOSITION

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/intl/wm-ime-composition)。
- 身份/章节：动态 Win32 API；页面更新 2021-01-07；Parameters；Remarks。
- 有限命题：组合串、结果串与取消标记不同，自绘输入须处理或正确转交 IME 消息。
- 不支持：不把每个按键认定已确认文本；TSF/现代框架适配另按实际 API。
- 绑定条款：D14、DT4-03。

<a id="dm18"></a>

## DM18 · UI Automation Providers Overview

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-providersoverview)。
- 身份/章节：动态 UI Automation 指南；采用方锁 SDK；In this article。
- 有限命题：UIA provider 暴露控件信息与操作；标准控件有平台 provider，自绘需确保实际语义。
- 不支持：树存在不等于整条读屏任务通过；不是要求所有平台实现 UIA。
- 绑定条款：D14、DT4-01、DT4-02、DT4-04、DT4-07。

<a id="dm19"></a>

## DM19 · High DPI desktop application development on Windows

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows)。
- 身份/章节：动态指南；页面更新 2026-09-10；PMv2 自 Windows 10 1703；Per Monitor DPI Awareness；Testing Your Changes；Common Pitfalls。
- 有限命题：DPI awareness、坐标空间和重排职责不同；多屏动态变化需要真实混合 DPI 验证。
- 不支持：框架历史支持表不是当前全部框架的支持断言；不统一像素阈值。
- 绑定条款：D14、DT4-05、DT7-03、DT7-07。

<a id="dm20"></a>

## DM20 · Sign an MSIX package

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview)。
- 身份/章节：动态 MSIX 指南；页面更新 2026-04-15；开篇；Timestamping；Package Integrity Enforcement。
- 有限命题：MSIX 签名与设备信任链不同；时间戳/证书过期与安装后的继续运行需分别解释。
- 不支持：不泛化全部 EXE；不将签名变为功能正确或平台全部完整性保护的证明。
- 绑定条款：D03、D16、D17、DT5-01、DT5-02、DT5-03、DT5-04、DT5-05、DT5-06、DT5-07、DT6-01、DT6-03、DT6-04、DT6-07。

<a id="dm21"></a>

## DM21 · Gatekeeper and runtime protection in macOS

- 发布者/入口：Apple，[官方正文](https://support.apple.com/guide/security/gatekeeper-and-runtime-protection-sec5599b66df/web)。
- 身份/章节：Apple Platform Security；发布 2024-12-19；Gatekeeper；Runtime protection。
- 有限命题：外部分发的开发者身份、公证、完整性检查与 App Store 沙箱/审核不是相同事实。
- 不支持：不据公证推断无未知恶意或无漏洞；不把系统允许的绕过作为正常安装验收。
- 绑定条款：D17、DT5-01、DT5-02、DT5-05、DT5-07、DT8-05、I09。

<a id="dm22"></a>

## DM22 · Configure update settings in the App Installer file

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/msix/app-installer/update-settings)。
- 身份/章节：动态 App Installer 指南；页面更新 2021-12-30；UpdateSettings 表；OnLaunch；ForceUpdateFromAnyVersion。
- 有限命题：更新选项有最低系统版本和组合前提；允许降级的包设置不证明数据兼容。
- 不支持：未规定设备管理策略优先级；有效策略应由目标观测，不凭此表虚构优先顺序。
- 绑定条款：D18、D19、D26、D28、DT6-01、DT6-02、DT6-03、DT6-04、DT6-05、DT6-06、DT6-07、S19。

<a id="dm23"></a>

## DM23 · How emulation works on Arm

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation)。
- 身份/章节：动态 Windows 指南；页面更新 2025-11-07；开篇；How emulation works；Detecting emulation。
- 有限命题：Windows 10/11 Arm 的用户态仿真范围不同；内核驱动需匹配 Arm64，宿主和进程架构应分开。
- 不支持：不证明某应用或驱动已兼容；不自动要求 ARM 发行。
- 绑定条款：D01、D15、D27、DT5-03、DT5-07、DT7-01、DT7-02、DT7-03、DT7-07。

<a id="dm24"></a>

## DM24 · Symbols and Symbol Files

- 发布者/入口：Microsoft，[官方正文](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbols-and-symbol-files)。
- 身份/章节：动态 Debugger 指南；页面更新 2021-12-15；开篇；Windows Symbols。
- 有限命题：调试现场或转储需匹配被测二进制/系统构建的符号。
- 不支持：有函数名不等于符号正确；不要求上传私有源代码或全内存。
- 绑定条款：D24、D25、DT8-01、DT8-02、DT8-03、DT8-04、DT8-05、DT8-06、DT8-07、MB7-06。

<a id="dm25"></a>

## DM25 · Debugging Information in Separate Files

- 发布者/入口：GNU GDB Project，[官方正文](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Separate-Debug-Files.html)。
- 身份/章节：滚动 current 手册；实际 GDB/Binutils 版本另锁；§18.3。
- 有限命题：独立调试文件可通过 debuglink/CRC 或 build ID 关联构建，不能只按产品版本字符串选符号。
- 不支持：该身份链不是发行签名或权限证据；未启用下载也可离线符号化。
- 绑定条款：D24、D25、DT7-02、DT8-01、DT8-02、DT8-06、DT8-07、MB7-06。

<a id="dm26"></a>

## DM26 · Processes and app lifecycle

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/guide/components/activities/process-lifecycle)。
- 身份/章节：滚动 Android 指南；实际 API level/targetSdk 另锁；进程重要性与回收。
- 有限命题：系统可回收进程，组件/线程内存不能作为跨进程死亡保存承诺。
- 不支持：不把 force-stop、普通回收、重启或取消视为等价。
- 绑定条款：M01、M02、MB1-01、MB1-05。

<a id="dm27"></a>

## DM27 · Save UI states

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/topic/libraries/architecture/saving-states)。
- 身份/章节：滚动 Android 架构指南；具体库另锁；Options for preserving UI state；saved state。
- 有限命题：ViewModel、saved state、持久存储的恢复范围不同；大业务数据不应依赖 UI snapshot。
- 不支持：具体 Compose 新增 API 不写为统一要求；saved state 不承诺所有退出方式均保留。
- 绑定条款：M02、M03、M14、MB1-02、MB1-03、MB1-04、MB1-05、MB1-07、MB5-05、MB7-01、MB7-05。

<a id="dm28"></a>

## DM28 · Introducing Multiple Windows on iPad

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/videos/play/wwdc2019/212/)。
- 身份/章节：WWDC19 session 212；iOS/iPadOS 13 引入机制的官方演讲；Transcript：UIWindowScene / SceneSession；state restoration。
- 有限命题：scene 可与 session 断接，界面状态与应用进程状态不同；恢复应绑定对应会话而非全局当前窗口。
- 不支持：不以 2019 演讲决定当前 SDK availability 或强制多窗口；恢复正确性要求是组织补充。
- 绑定条款：M02、MB1-01、MB1-02、MB5-03。

<a id="dm29"></a>

## DM29 · Task scheduling

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/develop/background-work/background-tasks/persistent)。
- 身份/章节：滚动指南；页面更新 2026-02-26；实际 WorkManager 另锁；Work constraints；Robust scheduling；Use WorkManager for reliable work。
- 有限命题：WorkManager 有约束和持久调度，非全部即时工作通用机制，排队不等于业务结果。
- 不支持：不承诺强停后即时运行或精确时刻；应用的操作账与 OS 作业 ID 分离是组织补充。
- 绑定条款：M04、MB2-01、MB2-02、MB2-03、MB2-04、MB2-05、MB2-06、MB2-07、MB4-02。

<a id="dm30"></a>

## DM30 · Advances in App Background Execution

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/videos/play/wwdc2019/707/)。
- 身份/章节：WWDC19 session 707；iOS 13 BGTask 机制的官方演讲；Transcript：expiration / completion；earliest begin；debug launch。
- 有限命题：有限执行机会要求处理到期与完成回报；最早时间非必达承诺，调试触发不能替代自然调度。
- 不支持：不固定当前配额、后台时限或照抄私有调试选择子；采用方锁定当前 SDK 机制。
- 绑定条款：M04、M12、MB2-01、MB2-02、MB2-04、MB2-05、MB2-06、MB2-07、MB5-04、MB7-04。

<a id="dm31"></a>

## DM31 · Request runtime permissions

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/training/permissions/requesting)。
- 身份/章节：滚动指南；危险权限流程适用于 Android 6/API23+；特殊权限分立；Basic principles；Workflow。
- 有限命题：上下文请求、每次受保护操作前检查、拒绝后相关功能降级；权限组不是稳定授权单元。
- 不支持：不证明特定权限所有版本行为；账号、scene、对象授权仍独立。
- 绑定条款：M05、M06、M12、MB2-05、MB3-01、MB3-02、MB3-03、MB3-04、MB3-07、MB4-04、MB5-04。

<a id="dm32"></a>

## DM32 · Minimize your permission requests

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/privacy-and-security/minimize-permission-requests)。
- 身份/章节：滚动隐私指南，核读 2026-10-23；开篇；alternative ways。
- 有限命题：选择器、较低精度和免权限代理可缩小访问面。
- 不支持：不禁止真实功能必需且获准的广泛访问。
- 绑定条款：M05、MB3-01、MB3-03。

<a id="dm33"></a>

## DM33 · Build an offline-first app

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/topic/architecture/data-layer/offline-first)。
- 身份/章节：滚动架构实施指南；非跨平台强制框架；Design；local/network data source；Error handling。
- 有限命题：本地可见数据与远端状态可暂时不同；离线读写、重试和冲突需要明确数据层合同。
- 不支持：不强制所有应用 offline-first；远端效果权威、去重与原账号绑定由后端合同和组织补充。
- 绑定条款：D20、M09、M10、M19、MB4-01、MB4-02、MB4-03、MB4-04、MB4-05、MB4-06、MB4-07。

<a id="dm34"></a>

## DM34 · Keychain data protection

- 发布者/入口：Apple，[官方正文](https://support.apple.com/guide/security/keychain-data-protection-secb0694df1a/web)。
- 身份/章节：Apple Platform Security 滚动页面，核读 2026-10-23；Overview；accessibility classes / This device only。
- 有限命题：密钥链访问组、锁定可用性和迁移保护类有不同边界。
- 不支持：macOS 与移动 Data Protection 机制不同；不统一选择某一类，不承诺解锁等于服务授权。
- 绑定条款：D21、DT8-03、I10、I14、M07、M08、MB1-03、MB1-06、MB2-05、MB3-05、MB3-07、MB5-05、MB6-06、S02。

<a id="dm35"></a>

## DM35 · Android Keystore system

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/privacy-and-security/keystore)。
- 身份/章节：滚动指南；KeyInfo 查询依目标 SDK 分支；Extraction prevention；StrongBox；Key use authorizations。
- 有限命题：非导出密钥仍可能被受攻陷应用调用；硬件支持依设备、算法和配置确认。
- 不支持：不要求所有设备 StrongBox；不声明密钥不可用即可清空业务数据。
- 绑定条款：D21、M08、MB3-05、MB3-07。

<a id="dm36"></a>

## DM36 · Verify App Links

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/training/app-links/verify-applinks)。
- 身份/章节：滚动指南；手动域验证流程 Android 12+；Auto verification；Manual verification；Review results。
- 有限命题：域关联状态可验证，none/verified/approved 等不同；域关联不是业务对象授权。
- 不支持：不将测试强制 approved 冒称域名验证；不统一所有系统的深链规则。
- 绑定条款：M11、MB5-01、MB5-02、MB5-03。

<a id="dm37"></a>

## DM37 · What's new in Universal Links

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/videos/play/wwdc2020/10098/)。
- 身份/章节：WWDC20 session 10098；2020 机制说明；Transcript：two-way association。
- 有限命题：应用 entitlement 与网站关联文件共同建立域关联，验证链接的交付入口。
- 不支持：不证明链接对象当前有权或所有当前平台路径规则；缓存传播按采用版本核实。
- 绑定条款：M11、MB5-01、MB5-02、MB5-03。

<a id="dm38"></a>

## DM38 · WebView – Native bridges

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges)。
- 身份/章节：滚动安全指南；风险文档非跨平台 API 标准；Overview；Mitigations。
- 有限命题：addJavascriptInterface 向所有帧暴露对象且不能验证调用帧 origin；消息通道亦需正确来源边界。
- 不支持：不能写出平台不可能提供的可信帧验证；无法验证时须隔离内容/取消敏感桥而非自报 URL。
- 绑定条款：M13、MB5-06、MB5-07。

<a id="dm39"></a>

## DM39 · Sign your app

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/studio/publish/app-signing)。
- 身份/章节：滚动签名指南，核读 2026-10-23；Play App Signing；Keystores；key upgrade。
- 有限命题：Play 上传密钥与设备 APK 应用签名密钥职责不同；AAB 上传物与渠道派生 APK 不是同一字节对象。
- 不支持：密钥轮换条件依 OS/渠道核；不把相同 key 绝对化，也不提供密钥操作授权。
- 绑定条款：M17、M18、MB6-01、MB6-02、MB6-03、MB6-04、MB6-05、MB6-06。

<a id="dm40"></a>

## DM40 · apksigner

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/tools/apksigner)。
- 身份/章节：SDK Build Tools 接口；页面更新 2026-03-05；实际工具另锁；Verify command。
- 有限命题：verify 与 print-certs 可检查 APK 签名与证书，API范围须与支持合同一致。
- 不支持：不能代替渠道资格、对象授权或真机安装；不读取私钥。
- 绑定条款：M17、MB6-01、MB6-02。

<a id="dm41"></a>

## DM41 · Choose a build to submit

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/help/app-store-connect/manage-builds/choose-a-build-to-submit)。
- 身份/章节：滚动 App Store Connect Help，核读 2026-10-23；Choose a build to submit。
- 有限命题：上传构建、版本选择和提交审核是不同步骤/状态。
- 不支持：不据此认定真实账号具资格或端上安装成功；其他渠道规则另按采用路径核。
- 绑定条款：M17、M21、MB6-01、MB6-02、MB6-05、MB6-07。

<a id="dm42"></a>

## DM42 · Back up user data with Auto Backup

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/identity/data/autobackup)。
- 身份/章节：滚动 Android 指南；有效规则须按 OS/targetSdk/厂商固定；Files that are backed up；Backup/Restore schedule。
- 有限命题：缓存/代码缓存/no-backup 与业务数据的备份范围不同；系统恢复与账号/密钥恢复需分别核。
- 不支持：不统一全部厂商迁移行为，不许诺每夜成功或所有数据已备份。
- 绑定条款：M07、M18、M21、MB1-03、MB1-06、MB1-07、MB6-04、MB6-06、MB6-07、MB7-05。

<a id="dm43"></a>

## DM43 · Test your app's accessibility

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/guide/topics/ui/accessibility/testing)。
- 身份/章节：滚动指南，当前页面含 Compose/Views 分流；Testing approaches；Manual testing；TalkBack。
- 有限命题：真实辅助技术任务与自动化/扫描是互补层；检查可达元素、播报和核心工作流。
- 不支持：不把标签或扫描结果等同等级符合；不强制采用 Compose。
- 绑定条款：D27、DT4-01、DT4-06、DT4-07、M14、M15、M22、MB7-01、MB7-02、MB7-07。

<a id="dm44"></a>

## DM44 · Perform accessibility audits for your app

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/videos/play/wwdc2023/10035/)。
- 身份/章节：WWDC23 session 10035；Xcode 15 时代演示；Discover audits；Considerations；identifier/label。
- 有限命题：Inspector/XCTest 审计检查当前视图常见问题；测试 identifier 与给用户的 label 用途不同。
- 不支持：不证明整条任务或全部 AT 通过；具体 API availability 由实际 SDK 决定。
- 绑定条款：DT4-01、DT4-02、DT4-06、DT4-07、M15、M22、MB7-02、MB7-07。

<a id="dm45"></a>

## DM45 · Profile battery usage with Batterystats and Battery Historian

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/topic/performance/power/setup-battery-historian)。
- 身份/章节：滚动指南；页面更新 2026-05-19；Warning；Gather data；View data。
- 有限命题：设备统计和轨迹用于能耗诊断；活动时间图不是组件耗电量，Battery Historian 已不积极维护。
- 不支持：不以模拟器/单次采样证明真机能耗；优先按实际目标选 system tracing/Power Profiler。
- 绑定条款：D22、DT7-04、DT7-05、DT7-06、DT7-07、M16、M22、MB7-03、MB7-04、MB7-05、MB7-07。

<a id="dm46"></a>

## DM46 · Third-party SDK requirements

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/support/third-party-SDK-requirements/)。
- 身份/章节：滚动渠道要求，核读 2026-10-23；名单不复制固化；Privacy Manifests；Signatures；SDK requirements。
- 有限命题：应用仍对 SDK 代码和数据实践负责；隐私清单、合并报告与 SDK 签名各证不同事实。
- 不支持：不把当前名单用于未选渠道或推断全面隐私合规。
- 绑定条款：M20、MB6-03、MB7-06。

<a id="dm47"></a>

## DM47 · Provide information for Data safety

- 发布者/入口：Google Play，[官方正文](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en)。
- 身份/章节：滚动 Play Console 政策说明，核读 2026-10-23；Overview。
- 有限命题：所选 Play 渠道触发的数据申报涵盖第三方 SDK 实际收集/处理。
- 不支持：适用例外与当前政策另核；不是全 Android 发行或法律合规结论。
- 绑定条款：M20、MB6-03。

<a id="dm48"></a>

## DM48 · Preventing Sensitive Information From Appearing In The Task Switcher

- 发布者/入口：Apple，[官方正文](https://developer.apple.com/library/archive/qa/qa1838/_index.html)。
- 身份/章节：官方 QA1838，2014-05-12；历史单窗口回调示例；Q/A；Note。
- 有限命题：任务切换快照会传播可见内容，应在对应生命周期边界保护敏感显示。
- 不支持：不把旧 app-delegate 示例直接用于全部 scene；不能撤回外部已捕获副本。
- 绑定条款：M20、MB3-06。

<a id="dm49"></a>

## DM49 · Secure Clipboard Handling

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/privacy-and-security/risks/secure-clipboard-handling)。
- 身份/章节：滚动指南，核读 2026-10-23；编译 API33 常量分支；Overview；Flag Sensitive Data。
- 有限命题：敏感标记遮蔽预览；剪贴板跨进程传播仍有权限与版本边界。
- 不支持：不把预览遮蔽等于全面阻止读取，也不要求按指南更改所有项目最低版本。
- 绑定条款：M20、MB3-06。

<a id="dm50"></a>

## DM50 · Secure sensitive activities

- 发布者/入口：Android Developers，[官方正文](https://developer.android.com/security/fraud-prevention/activities)。
- 身份/章节：滚动安全指南；页面更新 2026-03-06；FLAG_SECURE；Best practices。
- 有限命题：FLAG_SECURE 限制截图和非安全显示，但不能当成所有录屏/覆盖/物理拍摄的绝对防护。
- 不支持：按目标系统和真实任务测试，不泛化到全部平台。
- 绑定条款：M20、MB3-06。

<a id="dm51"></a>

## DM51 · Assessment and Certification

- 发布者/入口：OWASP MAS Project，[官方正文](https://mas.owasp.org/MASVS/04-Assessment_and_Certification/)。
- 身份/章节：滚动采用指南，核读 2026-10-23；未采纳某一 MASVS 控制版本；OWASP stance；Guidance for Certifying Mobile Apps。
- 有限命题：OWASP 不认证软件/评估者；移动客户端安全范围不包括全部远端接口，单工具不够证明评估。
- 不支持：仅作为评估边界；不是本包完成安全认证或逐控制符合审查。
- 绑定条款：M22、MB7-07。
