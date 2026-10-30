# L4 事务、隔离、MVCC 与锁竞争技术规范

**文档ID：** STD-L4-DATABASE-004　**版本：** 0.1.0　**状态：** adopted　**生效日期：** 2026-10-30

## 一、定位、实际适用范围与分层权威

本专项为数据库与数据工程领域第 03 项具体技术规范，聚焦**所选存储引擎内部事务、隔离可见性、MVCC 版本、行/表/范围锁、死锁、锁等待与可验证的并发一致性**。按真实选择 PostgreSQL、MySQL InnoDB、SQLite、SQL Server 或其他引擎启用相应机制，不强制跨项目统一数据库、隔离等级、锁实现或分布式架构。

**相邻规范边界：** 相应 L4 领域基线和[数据模型/Schema](013-数据模型、键与-Schema-兼容技术规范--v0.1.0.md)决定对象/字段约束，[SQL 查询与数据访问](002-SQL-方言、查询语义与数据访问技术规范--v0.1.0.md)决定选择/过滤及数据访问合同；后端业务幂等与分布式工作流决定跨系统副作用和客户权利。本专项只深入**具体数据库并发控制和事务生命周期**，不重写行业引擎算法，也不批准生产数据操作。物理索引、WAL/崩溃恢复、复制/高可用、DDL/回填及备份/PITR分别由[领域目录](README.md)中的对应独立技术规范承担。L5 确认驱动/引擎及配置版本，L6 定义真实业务不变量、身份、测试环境和验收证据。

## 二、官方技术来源与规范性质（2026-10-15 核对）

| 官方材料 | 发布性质 | 适用机制与限制 |
| --- | --- | --- |
| [ISO/IEC 9075-2:2023 SQL/Foundation](https://www.iso.org/standard/76584.html) | ISO/IEC 国际正式标准 | SQL 事务/隔离基础语义；各引擎行为仍按实现确认 |
| [PostgreSQL 18 13.2 Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) | 固定数据库版本官方文档 | Read Committed、Repeatable Read、Serializable 的可见性与并发异常 |
| [PostgreSQL 18 13.3 Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html) | 固定版本官方文档 | 行锁/表锁、deadlock、Advisory Lock 与冲突规则 |
| [PostgreSQL 18 13.5 Serialization Failure](https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html) | 固定版本官方文档 | SQLSTATE 40001、40P01、可条件重试及完整事务回放 |
| [MySQL 8.4 InnoDB Isolation](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html) | 固定版本官方文档 | 默认 Repeatable Read、读视图、locking read 与范围锁差异 |
| [MySQL 8.4 Consistent Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html) | 固定版本官方文档 | 普通 SELECT 与 DML/locking read 的不同快照语义 |
| [MySQL 8.4 InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html) | 固定版本官方文档 | record、gap、next-key、intention lock 的具体实现 |
| [MySQL 8.4 Deadlocks](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html) | 固定版本官方文档 | 死锁检测、牺牲者选择和事务级重试处理 |
| [SQLite Isolation](https://www.sqlite.org/isolation.html) | SQLite 官方实现文档 | WAL 快照、单写者与 SQLITE_BUSY_SNAPSHOT 的触发 |
| [SQLite Transactions](https://www.sqlite.org/lang_transaction.html) | SQLite 官方实现文档 | DEFERRED/IMMEDIATE/EXCLUSIVE、busy、显隐式事务的差异 |
| [SQLite Savepoints](https://www.sqlite.org/lang_savepoint.html) | SQLite 官方实现文档 | 内层 RELEASE 不等于持久 COMMIT，ROLLBACK TO 不取消外层事务 |
| [SQL Server Transaction Locking/Row Versioning](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver16) | Microsoft SQL Server 固定目标产品文档 | RCSI 与 SNAPSHOT 的数据库选项、版本存储和更新冲突 |
| [PostgreSQL 18 SQLSTATE](https://www.postgresql.org/docs/18/errcodes-appendix.html) | 固定版本官方文档 | 事务失败码与约束错误码分开 |

ISO SQL 标准、固定数据库版本实现文档、SQLite 持续更新实现说明与 Microsoft 特定产品版本指南分别具有不同效力；文档的语法说明不等于对所有引擎的统一实现承诺。会话默认、数据库选项、事务级隔离、锁定/非锁定读取、版本存储和 SDK 自动提交行为均以选定运行配置验证。

## 三、48 项独立事务与并发技术机制

每条要求只针对实际选用的存储能力和业务风险，不为小型单机系统制造虚假的多副本/分布式锁要求。

### §01 适用事务边界与权威确认
**机制：** 针对项目真实选用的关系型数据库或嵌入式存储，明确哪些数据更新必须原子提交、哪些业务回执属于数据库外部义务。事务成功、复制成功、HTTP 已受理与客户最终履约不应混同。

**验收：** 每一事务型路径明确数据库实例/版本、写入对象、提交点和最终业务验证依据。

**核验合同与来源：** [mvcc-R01](#mvcc-R01)；本条对应的失败输入见下文验证矩阵。

### §02 ACID 目标与实现差异
**机制：** 原子性、一致性、隔离与持久性属于需在所选数据库设置下满足的契约；隔离正确不自动保证数据文件可恢复或外部通知不重复，真实持久条件依据产品与部署配置核实。

**验收：** 事务失败/成功对账分别验证原子提交、逻辑不变量、可见性与持久结果。

**核验合同与来源：** [mvcc-R01](#mvcc-R01)；本条对应的失败输入见下文验证矩阵。

### §03 显式事务、自动提交与生效范围
**机制：** 区分应用开启事务、驱动 autocommit、数据库隐式事务、独立连接、会话状态及语句结束条件；事务范围不能因框架注解或同名连接配置而被推定真实生效。

**验收：** 同一组 SQL 在实际连接池/SDK 下按预定事务边界提交或回滚，不留孤立写入。

**核验合同与来源：** [mvcc-R01](#mvcc-R01)；本条对应的失败输入见下文验证矩阵。

### §04 COMMIT 确认与未知提交
**机制：** 连接在 COMMIT 后断开、响应丢失或切换节点时，客户端看到失败不等于数据库未提交；重试或补偿需要以稳定业务键查询真实权威结果，且保留 unknown 状态。 连接在 COMMIT 发送后断开不能直接认定已回滚；用稳定业务操作身份查权威结果，已提交不得再次扣款。

**验收：** 成功、明确失败、未知提交分别有确定恢复动作，无重复外部业务副作用。

**核验合同与来源：** [mvcc-R01](#mvcc-R01)；本条对应的失败输入见下文验证矩阵。

### §05 SQL 隔离等级的实现映射
**机制：** READ UNCOMMITTED/COMMITTED、REPEATABLE READ 与 SERIALIZABLE 的标签按标准与实际引擎分别解释；PostgreSQL、MySQL、SQLite 与 SQL Server 的默认值、底层锁与快照行为不能按同一名称自动等价。

**验收：** 项目声明隔离等级时附实现版本/数据库选项/会话设置及有代表性的并发验证。

**核验合同与来源：** [mvcc-R01](#mvcc-R01)；本条对应的失败输入见下文验证矩阵。

### §06 并发异常与可串行化目标
**机制：** 脏读、不可重复读、幻读、写偏斜与丢失更新是不同异常；以单一两连接现象通过并不证明多行或跨表业务不变量在实际隔离等级下全部安全。

**验收：** 隔离门禁对每个实际风险的不变量定义禁用异常或合法重试结果，而非仅使用隔离等级名称。

**核验合同与来源：** [mvcc-R01](#mvcc-R01)；本条对应的失败输入见下文验证矩阵。

### §07 PostgreSQL READ COMMITTED 语句快照
**机制：** PostgreSQL 18 READ COMMITTED 的普通查询在语句开始取得快照，同一事务重复语句可读到随后提交的修改；UPDATE/DELETE 在并发已改行上的重检行为按其章节另核实。

**验收：** 两个事务交错提交和读写后，各语句/操作都对应实际观察点，不误承诺全事务固定快照。

**核验合同与来源：** [mvcc-R02](#mvcc-R02)；本条对应的失败输入见下文验证矩阵。

### §08 PostgreSQL REPEATABLE READ 快照与限制
**机制：** PostgreSQL 18 的 Repeatable Read 使用事务级快照，不等同于 SQL Server RCSI 或 MySQL locking read；其快照隔离可能仍允许跨对象写偏斜，需要领域约束或 Serializable。

**验收：** 事务两次普通 SELECT 可见性和互不重叠对象并发修改分别运行针对性断言。

**核验合同与来源：** [mvcc-R02](#mvcc-R02)；本条对应的失败输入见下文验证矩阵。

### §09 PostgreSQL SERIALIZABLE 与 SSI
**机制：** PostgreSQL 18 的 Serializable Snapshot Isolation 监控读写依赖，不用阻塞性谓词锁代替范围锁。事务被判冲突时可能返回 SQLSTATE 40001，必须安全重放完整事务决定逻辑，不能只重跑最后一条写语句。

**验收：** write-skew 组合只允许一个合法结果或可恢复的序列化拒绝；40001 全事务重试无重复外部操作。

**核验合同与来源：** [mvcc-R02](#mvcc-R02)；本条对应的失败输入见下文验证矩阵。

### §10 MySQL InnoDB REPEATABLE READ 一致读
**机制：** MySQL 8.4 InnoDB 默认 REPEATABLE READ；一致性非锁定 SELECT 首次建立读视图，而 UPDATE/DELETE 或锁定读可能按当前行处理，不能由事务名推定全体语句均同视图。

**验收：** 同一事务混合普通 SELECT、FOR UPDATE 和 UPDATE 的结果符合真实引擎版本与域不变量。

**核验合同与来源：** [mvcc-R02](#mvcc-R02)；本条对应的失败输入见下文验证矩阵。

### §11 MySQL 锁定读与一致读边界
**机制：** MySQL 8.4 SELECT ... FOR UPDATE/FOR SHARE 与普通 SELECT 的锁和可见性语义不同，范围查询是否使用唯一索引可能改变 gap/next-key 锁；语句顺序与隔离等级均需验证。

**验收：** 没有在普通一致读后误认为已锁定记录，锁定读下竞争插入/更新有明确结果。

**核验合同与来源：** [mvcc-R02](#mvcc-R02)；本条对应的失败输入见下文验证矩阵。

### §12 SQL Server READ COMMITTED 与 RCSI
**机制：** SQL Server 目标版本中 READ_COMMITTED_SNAPSHOT 选项决定 READ COMMITTED 可使用语句级行版本视图，OFF 可使用共享锁机制；Azure SQL Database 与 SQL Server 默认设置可能不同，不能只看 isolation level。

**验收：** 记录并回读数据库选项和实际读者阻塞/读视图行为，不把 RCSI 当事务级 SNAPSHOT。

**核验合同与来源：** [mvcc-R02](#mvcc-R02)；本条对应的失败输入见下文验证矩阵。

### §13 SQL Server SNAPSHOT 与更新冲突
**机制：** SQL Server SNAPSHOT 需要允许此隔离的数据库选项；读取以事务快照为准，更新同一行可能发生冲突并终止事务；Version Store 存放位置与 ADR 等配置相关。

**验收：** 同一行并发变更导致合法更新或明确冲突，历史版本空间不足时有可观察错误和恢复路径。

**核验合同与来源：** [mvcc-R02](#mvcc-R02)；本条对应的失败输入见下文验证矩阵。

### §14 SQLite WAL 单写者与历史快照
**机制：** SQLite WAL 模式可在一个写事务同时允许多个读者，但仍只有一个 Writer；读者继续看旧快照，并不承诺每个新读语句都自动看到最新提交。

**验收：** 真实双连接读写可见性正确，单写者争用受界定而不产生双主写入。

**核验合同与来源：** [mvcc-R03](#mvcc-R03)；本条对应的失败输入见下文验证矩阵。

### §15 SQLite BEGIN DEFERRED/IMMEDIATE/EXCLUSIVE
**机制：** SQLite 默认 DEFERRED 的读事务升级可能失败，IMMEDIATE 提前申请写事务；WAL 模式 IMMEDIATE/EXCLUSIVE 对读者影响与其他 journaling 模式不同，不能把它们等价于跨数据库行级锁。

**验收：** 写竞争、读取及模式切换下 BEGIN、COMMIT、SQLITE_BUSY 的真实行为均被覆盖。

**核验合同与来源：** [mvcc-R03](#mvcc-R03)；本条对应的失败输入见下文验证矩阵。

### §16 同事务自身写入与快照例外
**机制：** 普通快照读通常看到已获批准的自身未提交写入，具体 UPDATE 的可见性/重新检查并不必然等同普通 SELECT；不能由读取到自身修改推导全局提交已生效。

**验收：** 混合自写、他人新提交和未提交事务时，权威数据库记录与外部报告分开判定。

**核验合同与来源：** [mvcc-R03](#mvcc-R03)；本条对应的失败输入见下文验证矩阵。

### §17 写偏斜与跨行不变量
**机制：** 两个事务读取相同约束前提、分别修改不同记录时可能各自提交且共同破坏领域不变量；仅对单行添加乐观版本或行锁不必然覆盖跨行约束。

**验收：** 双管理员轮班、名额限制或余额分摊等真实跨行前提，在并发下安全拒绝或保持约束。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §18 丢失更新与版本条件
**机制：** 读—改—写流程需要适用的行锁、条件 UPDATE、版本比较或 Serializable；无并发控制的客户端旧值不应覆盖更晚合法提交。

**验收：** 同一个业务对象并发更新不会丢失任一已确认合法变更，冲突可明确诊断。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §19 读取—修改—写入竞争与锁顺序
**机制：** 在余额、配额、库存等领域不变量确实依赖当前值时，确认在同一个有权限事务中完成判断及写入；所有参与者的锁定次序应一致，不能靠同步单个进程内 Mutex 保证跨实例正确。

**验收：** 多实例并发争用后既无负数非法余额也无双重权益，事务失败后状态可回查。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §20 幻读、范围冲突与谓词保护
**机制：** 先查不存在再插入、按范围计数再加入等条件不能仅靠一次普通 SELECT 保证；选择唯一约束、恰当范围锁或真实 Serializable 机制，PostgreSQL SSI 谓词锁不应误称阻塞性 gap 锁。

**验收：** 并发插入改变查询范围时，不产生重复业务主键、超配额或非法范围状态。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §21 并发唯一/外键/检查约束
**机制：** 数据库约束提交时可能与其他事务竞争；PostgreSQL Serializable 下可能仍出现 23505，需要按错误来源区分重试与真实业务冲突；FK 检查和级联锁的实际对象另按引擎验证。

**验收：** 重复键和外部键竞争不破坏权威关系，非瞬时冲突不被无限重试掩盖。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §22 MVCC 版本生命周期与内核实现边界
**机制：** MVCC 的可见版本、PostgreSQL VACUUM、InnoDB undo/Purge、SQL Server version store/ADR 与 SQLite WAL 是不同机制；不能以统一日志名、相同清理时机或共享默认阈值表达所有引擎。

**验收：** 项目识别活跃长快照对实际版本保留、存储占用及清理延迟的影响。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §23 删除、回滚与旧版本可见性
**机制：** 已删除对象可能在合法旧快照中仍可见，事务 ROLLBACK 对其私有修改应撤销，而客户端的权限撤销或 GDPR 删除对旧事务读者的要求需由更高业务/法律权威约束。

**验收：** 并发删除/回滚与跨会话读者的行为按真实权限、隔离、保留契约评估。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §24 跨表读视图、只读审计和时间戳
**机制：** 一组跨表报表是否需要同一一致时点由业务决定；SQL Server RCSI、PostgreSQL READ COMMITTED 等可能给每个语句不同视图，读者不能用 Wall Clock 时间代替事务快照权威。

**验收：** 跨表业务总额和子明细均可从一个受控一致视图复算，或明确标示允许的陈旧范围。

**核验合同与来源：** [mvcc-R04](#mvcc-R04)；本条对应的失败输入见下文验证矩阵。

### §25 行锁强度与实际冲突矩阵
**机制：** SELECT FOR UPDATE、FOR NO KEY UPDATE、FOR SHARE、FOR KEY SHARE 等锁模式仅在所选引擎/版本支持时适用；其行锁及意向表锁冲突不同，不得以一种锁名推断完全排他或禁止普通快照读取。

**验收：** 同一行/关联表的读写者根据真实冲突矩阵获锁、等待、拒绝或执行快照读取。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §26 锁定读取与更新资格
**机制：** `FOR UPDATE`/`FOR SHARE` 可用于在事务内锁定后续计划修改或检查的数据，但执行时作用的 WHERE/索引/隔离等级仍影响实际锁集合；事务提交前不得释放业务需要的保护条件。

**验收：** 不存在读后事务外更新或锁定对象与实际修改对象不一致的竞态。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §27 PostgreSQL 表锁与行锁区别
**机制：** PostgreSQL 的 ROW SHARE、ROW EXCLUSIVE 实际属于表级锁模式，不能因为名称包含 ROW 就称它们已锁定具体记录；SQL/DDL 会取得不同表锁且同一事务可持有多种模式。

**验收：** 行级争用与 DROP/ALTER/TRUNCATE 等表锁冲突分别有受控的排查和超时路径。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §28 MySQL Record/Gap/Next-Key 锁
**机制：** InnoDB 的行索引记录锁、Gap Lock 和 Next-Key Lock 根据索引、唯一等值搜索、范围条件与隔离等级变化；不能以 `SELECT FOR UPDATE` 推断只锁命中行或范围始终可并发插入。

**验收：** 真实范围查询及插入并发时，受锁行/间隙、幻读和误伤范围可复核。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §29 SQL Server 锁粒度与版本存储
**机制：** SQL Server 共享/更新/排他锁、锁升级、RCSI/SNAPSHOT 行版本以及可选优化锁行为按版本和数据库选项验证；版本存储空间不足也会造成读取或写入失败。

**验收：** 同一请求在版本选项/锁升级/空间压力下的真实阻塞和更新冲突被识别。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §30 NOWAIT、SKIP LOCKED 与公平性
**机制：** 支持 NOWAIT/SKIP LOCKED 的引擎可让竞争者拒绝等待或跳过锁定行，但它提供不完整的工作队列视图，不能将跳过视为记录不存在、最终不会遗漏或天然公平。

**验收：** 高争用、多 Worker、取消和重新可见时，未处理项不会永久遗忘，终态可对账。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §31 PostgreSQL Advisory Lock 所有权
**机制：** PG 会话级 advisory lock 与事务级 advisory lock 的释放时机不同，会话级锁不随普通事务回滚自动解除；锁键作用域及同连接/连接池的拥有关系必须明确。

**验收：** 事务中止、连接断开/回收及重复持锁测试可证明不会永久占用或错误跨租户复用。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §32 锁获取顺序与业务操作规范
**机制：** 跨多个表/行的事务需要一致的资源排序，并按真正需要的锁模式取得保护；锁升级或先共享后排他可能形成环路，不能只靠提高 lock_timeout 消除死锁。

**验收：** 相同两资源反向处理场景按统一顺序完成、受控等待或明确报死锁。

**核验合同与来源：** [mvcc-R05](#mvcc-R05)；本条对应的失败输入见下文验证矩阵。

### §33 死锁检测、受害事务与可观察性
**机制：** PostgreSQL、InnoDB 等引擎会选择受害事务并回滚，选择对象不由业务端预测；不同数据库是否使用超时后回滚以及检测配置需分别读取。

**验收：** 交错锁顺序构成环路后可以释放等待链，被中止的业务有明确恢复状态。

**核验合同与来源：** [mvcc-R06](#mvcc-R06)；本条对应的失败输入见下文验证矩阵。

### §34 序列化失败的完整事务重放
**机制：** PG 40001 必须重新计算完整事务判断和 SQL/值，40P01 死锁可以按风险选择重试；部分 23505/23P01 也可能源于并发，但不能无差别视为可重试。

**验收：** 重试后的选择、查询和后续写入基于新视图，无重复支付或客户通知。

**核验合同与来源：** [mvcc-R06](#mvcc-R06)；本条对应的失败输入见下文验证矩阵。

### §35 MySQL 死锁与锁等待超时的回滚界限
**机制：** InnoDB 检测到死锁一般回滚受害事务，但锁等待超时与事务是否整体回滚依服务器选项/错误路径；不能以任何 timeout 代表本事务所有语句都已撤销。

**验收：** 在 innodb_lock_wait_timeout 与 deadlock_detect 的实际组合下，可分辨事务仍活跃或已取消。

**核验合同与来源：** [mvcc-R06](#mvcc-R06)；本条对应的失败输入见下文验证矩阵。

### §36 SQLite SQLITE_BUSY 与 BUSY_SNAPSHOT 分级处理
**机制：** SQLite 写锁拥塞、BEGIN DEFERRED 读取后升级失败和 WAL stale snapshot 可能对应不同错误；BUSY_SNAPSHOT 不是简单 sleep 后在旧读快照上重试同一个 UPDATE。

**验收：** 读后他人已提交并升级写入时，丢弃旧快照、重新开始有效事务后才再次检查业务条件。

**核验合同与来源：** [mvcc-R06](#mvcc-R06)；本条对应的失败输入见下文验证矩阵。

### §37 锁等待超时与重试预算
**机制：** 锁等待时间、应用 Deadline、查询/事务超时、客户端取消及上游重试预算不自动一致；设定有界退避与可诊断的失败状态，重试风暴可能比原争用更严重。

**验收：** 过载或远端取消时连接、并发量和费用受限，未知提交能单独回查。

**核验合同与来源：** [mvcc-R06](#mvcc-R06)；本条对应的失败输入见下文验证矩阵。

### §38 唯一冲突与条件性重试边界
**机制：** 并发先读无键再写会触发唯一/排他约束异常，只有真正由竞争引起且可安全重算决策时才可重试，永久不合法的数据不得反复提交。

**验收：** 重复申请与同名键争用时，不发生重复插入、错误覆盖或无限循环。

**核验合同与来源：** [mvcc-R06](#mvcc-R06)；本条对应的失败输入见下文验证矩阵。

### §39 SAVEPOINT、局部回滚与外部副作用
**机制：** PostgreSQL/SQLite/Mysql 支持的 savepoint 语义及限制按产品核对；释放内层 SAVEPOINT 不等于外层提交，更不能撤销已发送的第三方邮件/付款。

**验收：** 嵌套逻辑失败后局部或全局回滚的数据库状态明确，外部不可撤销操作单独记账。

**核验合同与来源：** [mvcc-R06](#mvcc-R06)；本条对应的失败输入见下文验证矩阵。

### §40 长事务、版本积累与清理进度
**机制：** PG 老快照可能影响 VACUUM 清理，InnoDB 长视图影响 undo/purge，SQL Server RCSI/SNAPSHOT 影响 version store；不能用无记录的长事务等待用户输入或无限导出。

**验收：** 长读取器/闲置事务下版本积累、磁盘水位、业务延迟均能告警和回收。

**核验合同与来源：** [mvcc-R07](#mvcc-R07)；本条对应的失败输入见下文验证矩阵。

### §41 连接池、会话重置和并发上下文
**机制：** 锁、事务级设置、search_path、租户 role、autocommit、隔离等级和 driver cursor 状态与连接生命周期有关；连接归还不可给下一租户继承未结束事务或会话锁。

**验收：** 同一连接复用及异常取消后，另一身份不继承锁或不当权限，事务边界恢复可查。

**核验合同与来源：** [mvcc-R07](#mvcc-R07)；本条对应的失败输入见下文验证矩阵。

### §42 DDL 与元数据锁边界
**机制：** Schema 变更、索引建立、约束检查、TRUNCATE 等可能使用与普通 SELECT/UPDATE 不同的锁等级或元数据锁；DDL 具体迁移顺序归相邻规范，本专项控制竞争与一致性。

**验收：** 在线业务写入、长快照与 DDL 同时发生时明确阻塞/回滚/超时和允许的风险半径。

**核验合同与来源：** [mvcc-R07](#mvcc-R07)；本条对应的失败输入见下文验证矩阵。

### §43 工作队列行占用与欠履约
**机制：** 用数据库记录作为工作队列时需要事务级占有、稳定 Work ID、状态租约/续接、超时与扫描策略；SKIP LOCKED 只能避免部分等待，不代表消息去重和客户最终履约。

**验收：** Worker 崩溃/重启/迁移后全部合法业务对象被处理一次有效或仍作为待处理留存。

**核验合同与来源：** [mvcc-R07](#mvcc-R07)；本条对应的失败输入见下文验证矩阵。

### §44 热点记录、范围争用与公平性
**机制：** 账户总计、集中序列、单 Key 热点和范围锁会限制并发；分片/批处理应基于实际冲突集合及领域约束，不以静默放宽隔离换取表面 TPS。

**验收：** 代表性热点下吞吐、P95/P99、拒绝率、业务不变量和资金副作用均被同时验证。

**核验合同与来源：** [mvcc-R07](#mvcc-R07)；本条对应的失败输入见下文验证矩阵。

### §45 并发交错与冲突图验证
**机制：** 构造至少两个真实连接/会话和独立事务，固定 read/write/commit 顺序、障碍点、业务键、隔离选项；单个串行测试不能证明并发一致性，随机竞争结果要保存执行顺序。

**验收：** lost update、write skew、phantom、死锁和未知 COMMIT 均能重复注入并判定合法状态。

**核验合同与来源：** [mvcc-R08](#mvcc-R08)；本条对应的失败输入见下文验证矩阵。

### §46 锁等待诊断与源证据
**机制：** 在真实选用数据库下使用 pg_locks/pg_stat_activity、MySQL Performance Schema data_locks、SQL Server 监测或 SQLite 错误码进行诊断；锁视图具有瞬时性，不能被用来证明已提交业务完成。

**验收：** 原始待锁事务/SQL/资源及受影响业务对象可关联且对秘钥/个人数据做适当保护。

**核验合同与来源：** [mvcc-R08](#mvcc-R08)；本条对应的失败输入见下文验证矩阵。

### §47 跨引擎迁移和隔离假设回归
**机制：** 相同隔离等级文字在 PostgreSQL、MySQL、SQLite、SQL Server 的锁、快照和错误处理不同；升级/迁移时应重跑代表性的多事务组合，而非只对比标准 SQL 查询结果。

**验收：** 迁移前后读写可见性、锁冲突、错误码、事务边界和安全结果均在合同允许范围。

**核验合同与来源：** [mvcc-R08](#mvcc-R08)；本条对应的失败输入见下文验证矩阵。

### §48 工程门禁、证据和 L6 最终核定
**机制：** 静态规范引用、SQL 单测、离线双连接实验、隔离数据库并发测试、实际高负载和生产业务验收分级；每项失败保存实际引擎版本/会话配置/交错输入/原始错误与恢复。

**验收：** 受影响应用能独立证明权限、原子性、并发结果及真实客户义务，不将 CI 绿色等同真实履约。

**核验合同与来源：** [mvcc-R08](#mvcc-R08)；本条对应的失败输入见下文验证矩阵。

## 四、静态失效场景与项目级检查

以下是静态失败输入，不代表已执行真实数据库事务、死锁注入或生产数据测试。

### 场景组 1：事务责任、提交与隔离选择
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 数据库提交成功却将失败的第三方发送也记为完成 | §01 | 数据库与外部业务状态分别确认 |
| 事务读取一致但数据库断电后提交记录不可恢复 | §02 | 隔离与持久性两个维度分别验收 |
| 驱动启用 autocommit 导致订单两表写入只成功第一表 | §03 | 确认真实连接/事务边界及回滚 |
| COMMIT 已落库但响应丢失后直接重试扣费 | §04 | 未知提交按权威操作键回读 |
| 将 MySQL REPEATABLE READ 语义原样移植到 PostgreSQL | §05 | 按选中引擎及 session 配置对照 |
| 只测不可重复读便宣称没有 write-skew 或丢失更新 | §06 | 测试每个涉及的领域不变量 |

### 场景组 2：PG 可见性、SSI 与 MySQL 读视图
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| PG READ COMMITTED 事务内两次 SELECT 看到不同已提交值 | §07 | 语句快照的时点按真实产品判断 |
| PG Repeatable Read 跨行排班读取一致但两事务共同使无人值班 | §08 | 写偏斜不得被误判安全 |
| PG Serializable 报 40001 后只重放最后一次 UPDATE | §09 | 重试重新计算全事务决策 |
| MySQL 一致性普通 SELECT 仍读旧视图，却当最新数据扣款 | §10 | 一致读与业务权威时效分开 |
| MySQL 普通 SELECT 被认为已持有 FOR UPDATE 的记录锁 | §11 | 锁定读和非锁定读区别验证 |
| SQL Server RCSI 关闭却按行版本快照不阻塞的假设执行 | §12 | 实际数据库选项/锁冲突有证据 |

### 场景组 3：SQL Server、SQLite 与跨行竞争
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| SQL Server SNAPSHOT 未开启数据库选项却假设更新冲突已保护写入 | §13 | SNAPSHOT 实际开启/更新异常有记录 |
| SQLite WAL 两 Writer 同时改库却按多写者引擎设计并发 | §14 | 单写者竞争正常失败或重试 |
| SQLite DEFERRED 先读后升级写遇 BUSY_SNAPSHOT，原快照上继续操作 | §15 | 重开读写事务后再判断 |
| 同一事务能读到自己未提交写入便向客户宣称全球已完成 | §16 | 自写可见与实际持久提交分离 |
| 两事务分别修改不同行后多行业务约束失效 | §17 | 跨对象写偏斜安全拒绝 |
| 客户端旧状态无版本检查覆盖他人更晚合法变更 | §18 | 防止丢失更新 |

### 场景组 4：读改写、幻读、MVCC 与历史视图
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 跨实例只锁 JVM 内对象却让两个库存扣成负数 | §19 | 真实数据库事务及条件写保护 |
| 先 COUNT 名额再 INSERT 两事务各自成功使超配额 | §20 | 范围/谓词或唯一约束保证合法数量 |
| 并发同键插入触发 23505，却无限重试永久非法输入 | §21 | 区分瞬时竞争和真实业务违规 |
| 长快照阻止 VACUUM/undo 回收，WAL/版本占满空间 | §22 | 记录版本积累和回收上限 |
| 行被并发删除，旧快照仍看到其数据并错误扩大撤销权限 | §23 | 快照与当前合法授权分离 |
| 跨表报表在两次 READ COMMITTED 语句读到不同时间点而金额不等 | §24 | 明确一致读视图或允许差异 |

### 场景组 5：锁种类、间隙与队列公平性
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| SELECT FOR SHARE 被当独占行锁允许两业务同时分配同一库存 | §25 | 检查真实行锁冲突矩阵 |
| SELECT FOR UPDATE 写在另一个连接/事务内，主流程却认为已锁定 | §26 | 同事务写入资格被保护 |
| PostgreSQL ROW EXCLUSIVE 表级锁被误当已经锁住具体业务行 | §27 | 区分 PG 表/行锁 |
| MySQL 非唯一范围 FOR UPDATE 阻塞范围外新插入，误判资源可并发 | §28 | record/gap/next-key 锁影响范围可复核 |
| SQL Server 版本存储满后 SNAPSHOT 查询或 UPDATE 失败 | §29 | 监视 version store 并安全退出 |
| SKIP LOCKED 不返回忙碌订单后被误标为订单已全部完成 | §30 | 跳过对象保留待处理与后续回补 |

### 场景组 6：咨询锁、死锁、重试与 SQLite Busy
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| PG 会话级 advisory lock 在 ROLLBACK 后仍占锁，连接池持续泄漏 | §31 | 会话与事务锁释放正确 |
| 两个事务对账单和库存按相反顺序上锁造成环路 | §32 | 统一锁获取顺序 |
| 发生死锁后假设总是某业务请求被选作牺牲者 | §33 | 检测死锁并安全恢复任何受害事务 |
| PG 40001 重试只重新提交 UPDATE，没有重算之前的可变业务参数 | §34 | 完整事务从新读视图重算 |
| MySQL 锁超时后事务仍活跃，但客户端按已回滚处理 | §35 | 按实际配置确定超时回滚范围 |
| SQLite BUSY_SNAPSHOT 只 sleep 并在原 read txn 内反复 UPDATE | §36 | 释放旧快照并重启有效读写事务 |

### 场景组 7：超时、约束、局部回滚与环境
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 重试锁争用无次数/截止预算，雪崩导致更多死锁 | §37 | 重试、成本与并发上限有效 |
| 永久唯一约束冲突被当可重试死锁，最终造成资源耗尽 | §38 | 永久违规与瞬时冲突分离 |
| 内层 SAVEPOINT RELEASE 被当外层 COMMIT，外部邮件提前发送 | §39 | 局部/全局事务生效点独立 |
| 长期开着报表事务阻止版本清理和磁盘空间回收 | §40 | 限制活跃快照和保留链增长 |
| 连接归还后仍保持上一租户事务隔离级别和咨询锁 | §41 | 会话/事务/角色状态重置 |
| DDL 与长事务交错令在线查询一直等待强表锁 | §42 | 元数据与锁的风险半径可控 |

### 场景组 8：队列、热点、实际测试与证据
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 使用 SKIP LOCKED 工作队列后崩溃 Worker 领走的记录永久丢失 | §43 | 租约回收与欠履约状态能续接 |
| 优化单账户热点时降低隔离导致两个余额都被批准 | §44 | 吞吐增长不牺牲不变量 |
| 仅串行单连接测试，宣称不会发生 lost update 或 write skew | §45 | 至少两真实独立事务按时序验证 |
| pg_locks 的瞬时视图无锁就被当作账单已成功提交 | §46 | 锁诊断与实际业务持久事实分离 |
| 跨 PG 到 MySQL 迁移后原 Serializable 重试约定未更新 | §47 | 按真实引擎重跑冲突与重试 |
| CI 成功就宣称客户资金、复制与生产故障恢复已验收 | §48 | 运行证据与最终业务验收分离 |

### 场景组 9：跨数据库实现差异
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| SQL Server RCSI 语句快照被当作 PG Repeatable Read 事务快照 | §05、§08、§12、§47 | 实际隔离选项和快照寿命一致 |
| SQLite WAL 读后他人提交，再升级写导致 BUSY_SNAPSHOT | §14、§15、§36 | 原读视图作废后重新判断 |
| 把 PostgreSQL SSI 非阻塞谓词锁当 MySQL next-key 阻塞范围锁 | §09、§20、§28、§47 | 按引擎解释幻读/串行化失败 |
| PG advisory session lock 回滚仍存在，下一租户重用连接 | §31、§41 | 锁生命周期及租户键隔离 |
| SQL Server 版本存储膨胀导致长审计任务读失败 | §13、§29、§40 | 版本资源与审计证据安全恢复 |
| DDL 与锁升级交错造成写入停止，业务错误被当无数据 | §27、§32、§42、§46 | 锁等待、DDL 和空查询分离 |

### 场景组 10：复合故障与真实客户结果
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 支付提交 ACK 丢失，死锁重试又重新扣费 | §04、§34、§37、§38 | 权威账本按操作键只执行合法一次 |
| 两名值班者并发申请下线，不同锁顺序使全部离岗 | §17、§19、§25、§45 | 跨行值班不变量守恒 |
| SKIP LOCKED 任务崩溃后队列指标为零，却有欠交付订单 | §30、§43、§46、§48 | 锁扫描与履约终态分别核对 |
| 旧快照仍能看跨租户机密，权限撤销只更新最新写路径 | §23、§40、§41、§48 | 旧会话/副本访问按权利隔离 |
| MySQL 超时造成部分事务仍有效，外部退款先被视为已完成 | §35、§39、§48 | 数据库与真实外部退款分阶段对账 |
| 高并发压测缩短隔离提升 TPS，但真实资金账本产生重复记录 | §21、§44、§47、§48 | 吞吐、隔离、资金和恢复同时验收 |

## 五、版本、审批和真实项目验收

1. 本版包含 **48 项独立机制和 60 项静态失败场景**，10 组失败输入全部对应 §01—§48；项目应固定适用的官方来源和技术职责。L5/L6 项目的具体数据库测试及生产业务验收仍独立实施。
静态文本与 CI 验证不等于已执行实际数据库、生产故障注入、资金操作或客户业务验收。
3. 涉及 SQL/数据库时应由 L5 锁定引擎版本、驱动、WAL/隔离配置、数据库选项及异常码，L6 选择真实客户权利、负载、数据样本和各级验收阈值。事务重试须考虑外部副作用和未知提交，不授权任何生产环境操作。
4. 相应数据模型、SQL 查询、后端业务幂等/工作流规范保留原职责；物理存储/WAL、分区、高可用、DDL迁移和备份/PITR分别由[领域目录](README.md)中的对应独立规范承担；本专项的事务验证不替代这些技术对象的验收。

## 核验合同附录

各合同按条款范围列出输入、判据、合法邻例与恢复要求。来源版本及支持命题见[数据库来源表](../../../sources/database-sources.json)。

<a id="mvcc-R01"></a>

### mvcc-R01

**条款范围：** §01、§02、§03、§04、§05、§06

**目标工具/输入：** 双连接BEGIN/COMMIT脚本、isolation设置和SQLSTATE。自动提交边界错、COMMIT回执丢失、相同隔离名跨引擎套用

**判据：** 记录完整交错和实际提交/可见结果，业务不变量单独验证

**合法邻例：** 单写者/只读程序可无需最高隔离，但须满足真实不变量

**恢复：** 查权威业务身份；40001重放完整事务，不重复外部副作用

**来源：** [PG-I](https://www.postgresql.org/docs/18/transaction-iso.html)、[PG-R](https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html)、[MY-I](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)。关系：implementation-and-organisation-synthesis

<a id="mvcc-R02"></a>

### mvcc-R02

**条款范围：** §07、§08、§09、§10、§11、§12、§13

**目标工具/输入：** PG/Innodb/SQL Server双会话实际SQL和选项读回。普通读与锁定读混合、RCSI误当SNAPSHOT、写偏斜

**判据：** 语句/事务视图及并发更新冲突按对应引擎返回值判断

**合法邻例：** 业务允许的陈旧读合法，不能因非Serializable自动拒绝

**恢复：** 丢弃过时读视图重新读后决策；有界重试保留原交错

**来源：** [PG-I](https://www.postgresql.org/docs/18/transaction-iso.html)、[MY-I](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)、[SS-I](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver16)。关系：implementation-and-organisation-synthesis

<a id="mvcc-R03"></a>

### mvcc-R03

**条款范围：** §14、§15、§16

**目标工具/输入：** SQLite两连接WAL；BEGIN DEFERRED/IMMEDIATE。读快照后其他连接写入，本连接再升级写入

**判据：** 预期BUSY_SNAPSHOT与普通BUSY区分；本事务自身写可见

**合法邻例：** 无竞争单机、合法只读旧快照及BEGIN IMMEDIATE成功是正例

**恢复：** 回滚整个旧读事务并重开，不能只循环失败UPDATE

**来源：** [SQ-I](https://www.sqlite.org/isolation.html)、[SQ-W](https://www.sqlite.org/wal.html)。关系：implementation-and-organisation-synthesis

<a id="mvcc-R04"></a>

### mvcc-R04

**条款范围：** §17、§18、§19、§20、§21、§22、§23、§24

**目标工具/输入：** 写偏斜/丢更新/范围/唯一/FK并发交错SQL。两个医生均离岗、无版本覆盖、同键并发插入、旧版本误清

**判据：** 不变量与冲突图/约束返回码对应，MVCC不等于无业务冲突

**合法邻例：** 不需要跨行不变量的数据可用较低隔离；合法NULL引用可保留

**恢复：** 按版本CAS或支持的锁/串行化恢复整个决策，不通过抹除原记录修复

**来源：** [PG-I](https://www.postgresql.org/docs/18/transaction-iso.html)、[PG-C](https://www.postgresql.org/docs/18/ddl-constraints.html)、[MY-I](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)。关系：implementation-and-organisation-synthesis

<a id="mvcc-R05"></a>

### mvcc-R05

**条款范围：** §25、§26、§27、§28、§29、§30、§31、§32

**目标工具/输入：** 实际锁视图与行/表/next-key/advisory锁脚本。锁等级混淆、SKIP LOCKED遗漏、session锁被连接池转移

**判据：** 按真实锁冲突及所有权核验，不把SKIP LOCKED结果当完整集合

**合法邻例：** 队列允许跳过繁忙项可合法，但仍有重扫/欠履约追踪

**恢复：** 一致锁顺序、释放正确所有者和补扫未完成项，不能取消其他事务的锁

**来源：** [PG-I](https://www.postgresql.org/docs/18/transaction-iso.html)、[MY-I](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)、[SS-I](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver16)。关系：implementation-and-organisation-synthesis

<a id="mvcc-R06"></a>

### mvcc-R06

**条款范围：** §33、§34、§35、§36、§37、§38、§39

**目标工具/输入：** 死锁/锁等待/40001/BUSY脚本及SAVEPOINT。只重放最后语句、超时假定整事务回滚、RELEASE当最终提交

**判据：** 按SQLSTATE/引擎配置决定重试单元，已生效外部动作独立对账

**合法邻例：** 永久唯一冲突应拒绝而非盲重试；合法局部回滚保留外层事务

**恢复：** 完整事务回滚或协议定义单元后重试，业务幂等身份跨attempt稳定

**来源：** [PG-R](https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html)、[MY-W](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html)、[SQ-I](https://www.sqlite.org/isolation.html)。关系：implementation-and-organisation-synthesis

<a id="mvcc-R07"></a>

### mvcc-R07

**条款范围：** §40、§41、§42、§43、§44

**目标工具/输入：** 长事务/连接池/DDL/队列并发与资源快照。旧视图阻塞清理、角色遗留、DDL锁等待、热点饥饿

**判据：** 实际生命周期、资源上限、队列欠项及权限均可追踪

**合法邻例：** 小型短事务无需复杂队列，合法长只读需预算而非无条件拒绝

**恢复：** 结束失效会话、释放已授权锁、补扫欠项并核对更新权威

**来源：** [PG-I](https://www.postgresql.org/docs/18/transaction-iso.html)、[MY-I](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)、[SS-I](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver16)。关系：implementation-and-organisation-synthesis

<a id="mvcc-R08"></a>

### mvcc-R08

**条款范围：** §45、§46、§47、§48

**目标工具/输入：** 带barrier的并发脚本、SQLSTATE和实际版本记录。固定sleep偶然绿灯、缺隔离配置、CI当生产并发符合

**判据：** 可复现交错与业务状态证据完整，诊断与最终结果分层

**合法邻例：** 合法串行化/单写者实现可满足目标，不强制多节点压力

**恢复：** 保留失败交错与原输出，修复后在同一身份数据集和版本重放

**来源：** [PG-R](https://www.postgresql.org/docs/18/mvcc-serialization-failure-handling.html)、[SQ-I](https://www.sqlite.org/isolation.html)、[SS-I](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver16)。关系：implementation-and-organisation-synthesis
