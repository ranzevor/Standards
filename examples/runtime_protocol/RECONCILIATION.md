# SQLite有限夹具：操作结论与旧尝试闭合

`DurableFixture` 演示单个 SQLite 文件中的有限事务。生产协议、权限验证和目标权威查询分别由采用项目实现。`resolve_local_operation` 的输入是夹具设定的可信操作级观察；观察来源、权限、业务状态和接收窗口由调用方提供准确记录。

## 前提与状态

同一逻辑意图`k`固定payload指纹，每次传输尝试有不同标签。只有当前完整尝试集合均被覆盖、且该集合不再可能被接收时，操作级终局结论才可进入夹具。重复覆盖标签、漏尝试、未知操作、非布尔标志或未关闭接收边界被拒绝；集合顺序不影响身份。

- `applied=False`：在同一`BEGIN IMMEDIATE`事务中写入`reconciliation_events`、将已覆盖尝试置为`not_applied`、把操作置为`failed_known`。
- 新合法尝试进入`in_flight`后，操作可为`dispatching`；新尝试确实未知时仍为`unknown`。旧尝试被闭合不能抹除新未知。
- `applied=True`：记录操作已成功的观察，但不凭操作成功虚构“哪一个尝试应用”。后到的尝试失败不回退已知操作成功；相反终局结论被拒绝。

## 审计与失败

每次接受的操作级调和保存原操作状态、原尝试状态、准确覆盖集合和 UTC 观察记录时刻。该 API 只追加记录，不删除旧 attempt；此前的 `unknown` 观察仍保留在事件中。写入者防篡改和观察新鲜性由独立机制验证，时间戳只记录观察时刻。

事件、尝试和操作状态原子提交；SQL故障应回退整体，自动回退时不再用第二次ROLLBACK覆盖原始错误。重开同一文件后，已记录闭合不得因再次聚合复活旧未知。依据[SQLite事务文档](https://www.sqlite.org/lang_transaction.html)的事务与单写者边界，夹具使用本地事务；已跑正常关闭/重开、SQL触发器故障及有限双连接并发，不宣称断电、复制、远端权威或所有调度已验。

旧夹具若只留下`failed_known`标签、却没有尝试闭合证据，不自动补造事件或认定旧未知已消解。须重新取得完整且当前有效的操作级观察，再调用此接口；这是一种保守兼容路径，不是对真实业务历史的追认。

## 可运行回归

```sh
python -m unittest discover -s tests -p 'test_runtime_reconciliation.py' -v
python -m unittest discover -s tests -p 'test_runtime_examples.py' -v
```

回归包括终局未应用→新尝试→明确未应用、真实本地目标提交、重开、旧迟到/新未知、跨意图隔离、SQL回退和并发新增尝试。真实产品另须实现观察的权限、作用域、新鲜性、接收窗和全尝试覆盖证据，不能复制本夹具的oracle标志代替这些机制。
