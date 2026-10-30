# 云域失败谓词与合法邻例

本例提供二十类观察函数，检查内容身份、执行阶段、撤权、恢复、资源退出等局部不变量。输入为合成字节和给定观察值；真实云接口、审批身份及目标环境的验证入口见[云基础设施规范](../../standards/L4/cloud/README.md)和[目标画像](target_profiles.md)。

```sh
python -B -m unittest discover -s tests -p 'test_cloud_case_predicates.py' -v
```

[函数实现](case_predicates.py)和[测试](../../tests/test_cloud_case_predicates.py)列出正常输入、直接失败输入与合法邻例。下表说明每个接口的观察值和拒绝条件。

| 函数与条款 | 可观察不变量 | 必须拒绝 | 应当保留的邻例 |
| --- | --- | --- | --- |
| `content-identity`：BL-09、SUP-09 | 对每份UTF-8合成输出实际计算SHA-256，分别比对其登记值 | 两份不同字节仍沿用同一个内容摘要 | 同一源码或频道产生多个不同且分别登记的输出 |
| `approved-content`：SUP-14 | 实际消费字节的摘要等于被选择的准确批准摘要 | Tag改变后用旧批准消费不同字节 | 频道可变，新发行按其新的准确批准消费 |
| `classified-change`：BL-16、IAC-31 | 当前计划摘要、被批准计划摘要、不可逆分类及所需保护分别成立 | 未分类的不可逆动作、错误计划批准或缺少保护 | 已分类、准确批准且满足保护的受控自动化替换 |
| `outage-promise`：BL-28 | 同单位故障时间不超已提供的停机上限，健康报告与观察一致 | 超承诺停机，或不可用却报告健康 | 已接受单点、承诺范围内且诚实报告的停机 |
| `revocation-window`：IAM-18、IAM-38、SEC-30 | 在同一观察时基固定截止；到达截止即不得继续写入，提前完成声明也须有拒绝观察 | 截止时或之后仍写入；窗口内仍能写却宣称已撤权 | 窗口内诚实记录传播中，或提前实际阻断 |
| `dns-recovery`：NET-14 | 全部恢复声明不得超过实际观察的用户路径 | 仅权威记录创建就宣称所有用户恢复，而负缓存下的路径仍失败 | TTL内旧负缓存与恢复中状态如实共存 |
| `rootfs-write`：ISO-25 | 区分运行时根只读承诺、真实根写入和另挂的授权可写卷 | 承诺只读的实际根仍接受未授权写入 | 镜像不可变而实例Overlay可写；只读根另挂有界tmpfs |
| `completion-report`：ISO-37、IAC-39 | 所报完成不能越过已观察的实际阶段 | Pod被拒却报交付完成；异步受理就报业务端点完成 | 正确Admission拒绝或异步受理，交付仍未完成 |
| `proof-consumption`：SUP-17 | 要求证明的消费只有在实际证明已验证时才放行；发现路径明确 | API不支持且兼容发现也未取得证明仍放行 | 无Referrers API但兼容索引已取得证明；缺证据时诚实阻断 |
| `withdrawal-consumption`：SUP-43 | 实际字节摘要落入已提供拒绝范围时不能继续获准消费 | 忽略撤回范围继续消费旧Digest | 按保留策略继续存储或拉取旧内容，但受信消费执行拒绝 |
| `secret-refresh`：SEC-21 | 已发布、已投影及实际消费者版本分别登记，按所承诺期限刷新 | env仍旧却报刷新成功，或超过本合同刷新截止仍未收敛 | 投影文件已新而env旧，在窗口内如实等待重启 |
| `rotation-stage`：SEC-25、SEC-26、SEC-28 | 通知、候选、源服务设置/测试、CURRENT、消费者与旧值退出是不同事实 | 通知/候选冒充全量完成，或未设置测试即提升CURRENT | 通知或候选阶段、未泄露旧值的有界迁移仍如实待完成 |
| `scoped-completion`：REL-14、REL-18、DR-33 | 每个命名范围独立记录完成/待定/未知，声明只覆盖实际完成范围 | HTTP/DNS配置完成就把队列、在途副作用或缓存客户端也报完成 | 单独HTTP回退可完成，独立队列或TTL路径仍明确待定 |
| `incident-facts`：OBS-16 | 通知可静默，观察到的故障仍有事故记录且不能虚报解决 | 静默后抹除或无恢复事实就关闭事故 | 限时静默、事故继续处理且来源事实保留 |
| `backup-scope`：DR-07 | 声称备份的集合不得超出实际备份集合，本合同必要对象不能遗漏 | 只有YAML却声称同时包含PV数据，或漏掉所选合同必要对象 | 准确命名的配置备份只覆盖其配置范围 |
| `retirement-resources`：COST-34、COST-35、COST-36 | 真实对象是否存在、当前Owner、同口径持续费用及删除声明分别核对 | 父对象删除/Finalizer处理中/脱离State就报对象全删或费用归零 | 合法保留或移交的资源仍有Owner、用途及准确持续费用 |
| `external-exit`：COST-39 | 在用集成有当前授权和Owner；全部外部下线声明须与实际活动范围一致 | 迁移回调仍活动就报全部下线，或活动回调无当前授权/归属 | 前端已退役，有权迁移回调继续活动，退出范围准确记录 |

时间数值是同单位、非负的有限值，布尔字段必须为实际布尔值，未知函数或多余输入字段拒绝。撤权期限、审批身份和观察值由调用方提供；DNS 解析器、OCI 服务、挂载内核及实际云状态按各自目标画像验证。

费用例子的输入固定同一币种、计量口径、期间与资源范围，不是跨币种真实账单合并。为约束合成输入，十进制串至多200字符、128个数字位，指数为-12至12；超出此表示范围须拒绝，不能截断或静默舍入。这是此例的有限表示，不是所有币种或规范条款的数值限制。内部用准确有理数累加，不用二进制浮点或默认Decimal精度掩盖差额。

源码测试覆盖这些谓词的边界、异常和合法邻例。完整云验收按所选条款的目标入口、固定版本和实际结果执行。

来源版本、引用章节与具体支持范围见[云领域来源](../../sources/cloud/source-claims.json)。采用项目在合同中记录所选接口、运行权限与承诺。


## 中断、强制终止与写入体系

以下三个接口检查轮换中断、请求终止与写者准入；测试分别包含失败场景和允许的相邻场景。

- `rotation-interruption`：服务暂不可用时须有给定受控切换/恢复，遵守实际停机上限且不提前报切换完成；已授权有界计划中断可以合法。实际后端的连接行为独立核验，不假定单用户一定断连或强制双账号。
- `termination-accounting`：每个已接收请求有完成或持久恢复观察，待恢复不能叫干净完成；SIGKILL本身不等于丢数据。空的已接收集合可以强制停止，不伪造虚构请求。
- `writer-admission`：按给定作用域的`single-writer/coordinated-multiwriter`合同核有权写者；单写拒绝旧主，多写必须有产品支持及协调证据。集合参数不认证现实权限、冲突消解或数据库协议，不凭多个节点就推脑裂或推合法。

所有输入仍为合成观察和给定合同。Kubernetes的共享终止预算/超时强停、AWS单用户轮换的具体连接边界、Oracle RAC的协调共享存储与PostgreSQL不同复制方案，只支持各自限定命题，不能推广成统一供应商选型或许可。补核来源见[边界记录](../../sources/cloud/interruption-source-claims.json)。真实集群、轮换服务、共享存储和跨区业务仍not-run。


## 准确预算账与汇总入口

`contracts.Budget`及`contracts.totals`与上述`case_predicates`是两个有限接口，表示边界分别定义。预算账接口接受十进制字符串、整数或Decimal，不接受float/bool；输入文本最多1024字符、系数最多256位、十进制指数-128至128。超界明确拒绝。对所有接受值，预留准入、结算和billed/effective汇总按完整十进制系数与指数准确相加，不依赖调用者的Decimal精度或舍入模式。

例如上限1、固定占用1e-40时预留1必须拒绝；上限1e29、固定占用1时预留1e29也拒绝。合计1e28与1须保留低位1。普通100−1−99边界仍合法。结算保留实际超额，取消请求或未知结果不自动释放占用；接口不预测真实云价格、不证明实际渠道账单、币种换算或付款结果。

Budget/totals accepts bounded exact decimal text, integers or Decimal, never float/bool. It uses complete decimal coefficients rather than ambient Decimal precision for admission, settlement and totals. Its limits differ from the separate case-predicate API. Retain actual overruns and unknown reservations; this finite ledger does not authenticate cloud billing or payment.
