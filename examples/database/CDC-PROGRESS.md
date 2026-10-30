# 本地SQLite的CDC投递进度夹具

## 适用范围和权威边界

入口为[`checks.database_examples.apply_event`](../../checks/database_examples.py)。它在一份隔离SQLite数据库内提交合成源事件、Inbox、目标行和**调用者提供**的消费游标链，示范[CDC专题](../../standards/L4/database/001-CDC、流批时序与幂等水位技术规范--v0.1.0.md)§19—22、§37—38的部分不变量。它不连接实际Broker，不验证外部源事件完整性，不执行付款，不证明真实连接器Exactly-Once、掉电耐久或其他引擎正确。

## 三个独立身份

1. 源事件身份是`source/generation/transaction/record/table/tenant/key`。相同LSN可以有多条合法记录。源内容包括源版本、操作、值和其他提供的JSON源字段；身份不变但内容变了是冲突。
2. `epoch`是调用者声明的当前Worker控制代次，不是不可变源内容。每次调用在事务内先查`lease`，包括重复事件；过期Worker不能因命中Inbox绕过隔离。模型不认证谁有权改变租约。
3. 投递位置是`stream/predecessor/next_cursor`，与源事件身份分开。游标是有限整数、必须前进，可以不连续；`stream`包含调用者选择的流世代。同源事件可能在同流新位置或另一流再次投递。

## 状态和返回值

`init_store(connection)`只初始化新夹具，创建`lease/inbox/target/delivery_progress/outbox`。调用者设置租约初始代次/游标。`apply_event(connection,event,stream,predecessor,next_cursor,fail_at=None)`要求调用者没有未提交事务，输入为有限JSON；失败不擅自提交调用者事务。

- 未知源事件：验证当前位置等于`predecessor`，插入Inbox，按源对象版本更新目标，登记投递回执并CAS推进租约游标；一次事务提交，返回`applied`。
- 已知且源内容相同：**不再次写目标**。若是当前位置上的新投递，仍须登记这次回执、推进游标，返回`duplicate`。该返回值只表示源作用已去重，不表示游标没有变化。
- 已提交的准确投递回执重放：范围和源身份必须完全相同，且现行游标不能落在该回执后方；返回`duplicate`而不倒退。它可以发生在后续进度已提交之后。
- 无回执的旧范围、跳过当前前驱、同位置换事件/范围、源身份内容冲突、旧代次及未知流：拒绝且事务不产生部分变化。仅有Inbox命中不足以证明旧投递位置。

同键旧对象版本不会覆盖新值/删除；同版本不同值保留冲突。模型中的单调对象版本仅在给定源世代及对象范围比较，不为不同真实源构造全序。

## 故障、并发与恢复

`fail_at`支持`after-inbox/after-target/before-commit/after-commit`。前三项抛错时Inbox、目标、投递回执和游标一并回退。最后一项模拟提交后客户端确认丢失：不能假定未发生；使用准确投递范围重开查询/重放，已提交回执使其无二次作用。当前Worker接管只改变控制代次，合法重放原源内容不会制造“不同载荷”。

实际双连接测试使用SQLite事务锁和唯一投递回执串行化重复消费，不模拟分布式锁服务。旧版本数据库缺少`delivery_progress`时不能从Inbox推测历史消费范围；应保留旧数据库，使用新的隔离夹具，或由真实项目提供可核验的显式迁移/重放边界。本文不自动补造历史回执。

## 可复跑验收

仓库根目录执行：

```sh
python -B -m unittest tests.test_database_cdc_progress tests.test_database_cdc_mutations tests.test_database_examples -v
python -B checks/run_database_checks.py --evidence-dir /tmp/StandardsDatabaseChecks
```

16个新投递方法核读实际SQLite行、游标、投递回执及目标触发器观察；正例是首条作用提交，直接失败是旧事件命中就提前返回而不消费新位置，合法邻例是新代次或新位置的同源内容重放。另测提交前后故障、双连接、缺口/回绑、非连续游标、源内容冲突及调用者事务。4处真实守卫/状态变异应失败，注释邻例应通过。命令通过仅建立这些有限谓词，不替代真实项目验收。
