# L4 Schema 迁移、回填与兼容收缩技术规范

**文档ID：** STD-L4-DATABASE-003　**版本：** 0.1.0　**状态：** adopted　**生效日期：** 2026-10-30

## 一、技术定位、适用条件与相邻规范的职责

本专项属于 L4「数据库与数据工程」第 08 项具体技术专题，专门规定**真实 Schema/数据结构迁移、DDL 锁及重写、旧新版本兼容窗口、历史数据回填、并发写入、约束分阶段验证与安全收缩**。它不强制项目增加 Migration Service、复制节点或额外收费工具；可按实际单机/云端数据库的风险调整发布批次。

现行相应数据模型与 Schema 兼容专项定义字段/键/数据语义，SQL 查询专项负责读写查询结果，事务/MVCC 及 WAL 专项分别管理事务和持久化，索引/执行计划专项负责计划成本，复制/高可用负责副本与切换，后端跨版本发布专项负责系统整体部署；本专项只增补**数据库 DDL 与数据回填过程的安全性、进度及收缩条件**。备份/PITR、CDC/流批和数据质量专题分别负责相应机制。L5 锁定具体数据库/工具/驱动版本，L6 依据真实授权、数据权利、成本预算和项目用户任务作出验收。

## 二、官方实现依据、版本与效力（2026-10-15）

| 官方技术资料 | 发布性质与版本 | 本专项实际采用的范围 |
| --- | --- | --- |
| [PostgreSQL 18 ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html) | 固定版本官方数据库文档 | 锁/表重写、USING、NOT VALID、VALIDATE 与 NOT NULL 验证 |
| [PostgreSQL 18 CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html) | 固定版本官方数据库文档 | CONCURRENTLY、无效索引、不能置于事务块 |
| [PostgreSQL 18 Modifying Tables](https://www.postgresql.org/docs/18/ddl-alter.html) | 固定版本官方数据库文档 | 添加/修改列和默认值的 SQL 合同 |
| [PostgreSQL 18 ALTER TYPE](https://www.postgresql.org/docs/18/sql-altertype.html) | 固定版本官方数据库文档 | ENUM/复合类型及现有使用者变更边界 |
| [PostgreSQL 18 Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html) | 固定版本官方数据库文档 | DDL、读写和长事务的锁冲突级别 |
| [MySQL 8.4 Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html) | 固定版本官方数据库文档 | ALGORITHM INSTANT/INPLACE/COPY 的分类及列/索引限制 |
| [MySQL 8.4 Online DDL Limitations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-limitations.html) | 固定版本官方数据库文档 | Metadata Lock、长事务、并发 DML、复制滞后 |
| [MySQL 8.4 Atomic DDL](https://dev.mysql.com/doc/refman/8.4/en/atomic-ddl.html) | 固定版本官方数据库文档 | 单语句原子性与跨 DDL/DML 事务边界差异 |
| [MySQL 8.4 InnoDB and Online DDL](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl.html) | 固定版本官方数据库文档 | 重构、算法选择、锁/IO/空间与失败场景 |
| [MySQL 8.4 Metadata Locking](https://dev.mysql.com/doc/refman/8.4/en/metadata-locking.html) | 固定版本官方数据库文档 | 表元数据锁及连接事务生命周期 |
| [SQLite ALTER TABLE](https://www.sqlite.org/lang_altertable.html) | SQLite 官方动态实现文档 | 受支持 ALTER、Schema SQL 重写及安全 12 步重建 |
| [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html) | SQLite 官方动态实现文档 | FK 开关、延迟引用及 foreign_key_check |
| [SQLite Backup API](https://www.sqlite.org/backup.html) | SQLite 官方动态实现文档 | 数据库文件/在线一致复制与回退快照边界 |
| [SQL Server Online Index Guidelines](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/guidelines-for-online-index-operations?view=sql-server-ver16) | Microsoft 固定目标版本文档 | ONLINE、SCH-M、Edition/功能及 Resumable 条件 |
| [SQL Server Online Index Operations](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/perform-index-operations-online?view=sql-server-ver16) | Microsoft 固定目标版本文档 | 并发索引创建/重建及资源/锁边界 |
| [MongoDB 8.0 Validation Level](https://www.mongodb.com/docs/v8.0/core/schema-validation/specify-validation-level/) | MongoDB 固定目标版本官方文档 | strict/moderate 的旧数据处理和写入验证 |
| [MongoDB 8.0 collMod](https://www.mongodb.com/docs/v8.0/reference/command/collmod/) | MongoDB 固定目标版本官方文档 | 集合校验器和动态元数据更改 |
| [MongoDB Schema Validation (latest)](https://www.mongodb.com/docs/manual/core/schema-validation/specify-validation-level/) | MongoDB 官方动态文档 | 9.0 才新增 constraint 的版本差异，不能用于 MongoDB 8.0 |
| [CockroachDB Online Schema Changes](https://www.cockroachlabs.com/docs/v26.2/online-schema-changes) | CockroachDB v26.2 官方版本文档 | 分阶段 Schema Change Job 与同步/异步完成语义 |
| [Redgate Flyway Versioned Migrations](https://documentation.red-gate.com/fd/versioned-migrations-273973333.html) | 迁移工具官方产品文档 | 版本迁移不可随意重写，Checksum 与 Forward Fix |
| [Redgate Flyway Schema History](https://documentation.red-gate.com/flyway/flyway-concepts/migrations/flyway-schema-history-table) | 迁移工具官方产品文档 | 历史账本、Applied/Pending/Failed 及校验 |
| [Redgate Flyway Repeatable Migrations](https://documentation.red-gate.com/fd/repeatable-migrations-273973335.html) | 迁移工具官方产品文档 | 重复变更的 Checksum 重跑与真实幂等责任 |

这里的版本化 PostgreSQL/MySQL/SQL Server/MongoDB/CockroachDB 与 SQLite 动态产品说明只对其实际支持环境成立。Flyway 为可选迁移工具的官方历史/Checksum 机制示例，不作为所有项目的指定依赖。MongoDB 最新文档中 9.0 新增的 constraint 验证级别不能当作 MongoDB 8.0 功能。

## 三、48 项迁移与回填技术机制

各条的验收语义指向获授权的真实项目测试输入，不能用静态审查声称数据库已执行迁移。

### §01 变更对象与权威数据范围
**机制：** 先明确每次 DDL/回填触及的业务实体、租户、数据权利、已有读写/历史文件和恢复义务；数据库列修改不自动获得更改订单、资金或隐私语义的权利。

**验收：** 每项变更具有受影响对象清单、真实业务前后条件及合法审批主体。

**核验合同与来源：** [migration-R01](#migration-R01)；本条对应的失败输入见下文验证矩阵。

### §02 迁移范围与发布责任
**机制：** 区分数据库 Schema 结构、约束校验、存量数据变换、事件/API 合同及生产部署步骤；本专项规定数据库内操作的正确性门禁，跨系统版本发布仍由现行 L4 负责。

**验收：** 一次变更可以明确划分 DDL、应用版本、存量回填、切流及最终业务验收。

**核验合同与来源：** [migration-R01](#migration-R01)；本条对应的失败输入见下文验证矩阵。

### §03 原始基线与风险盘点
**机制：** 变更前检查现有 Schema、字段数值/空值/数据大小、索引/约束、长事务、资源和各类消费者，不能只从 ORM 实体类推断真实数据库状态。

**验收：** 原始结构及数据异常、现存不兼容和容量预算均可独立复核。

**核验合同与来源：** [migration-R01](#migration-R01)；本条对应的失败输入见下文验证矩阵。

### §04 Expand—Migrate—Contract 阶段门禁
**机制：** 先扩展兼容读取/写入能力，再分批迁移数据，最后在没有活跃旧消费者和回放依赖后收缩旧字段；这些阶段可按小项目实际简化，不强制引入新工具或服务。

**验收：** 各阶段都有独立准入条件、退出证据和不允许越级的不可逆操作清单。

**核验合同与来源：** [migration-R01](#migration-R01)；本条对应的失败输入见下文验证矩阵。

### §05 多版本 Writer/Reader 兼容矩阵
**机制：** 记录当前、新版本和仍在线/离线客户端、后台任务、CDC、历史事件/备份在混合发布期间哪些版本合法同时读写，Schema 可解析不等于业务含义与授权不变。

**验收：** 受支持的旧写新读、新写旧读和回放组合全部产生批准结果或明确拒绝。

**核验合同与来源：** [migration-R01](#migration-R01)；本条对应的失败输入见下文验证矩阵。

### §06 旧新字段权威与双写职责
**机制：** 拆分字段/表、双写或事件镜像时必须明确唯一的权威值、写入顺序、冲突优先级与何时停止旧写路径，不能让两套字段彼此覆盖或循环回写。

**验收：** 并发写入和部分失败之后可以通过稳定业务键判明权威、差异和补偿动作。

**核验合同与来源：** [migration-R01](#migration-R01)；本条对应的失败输入见下文验证矩阵。

### §07 迁移版本账本与不可变历史
**机制：** 使用迁移版本、审查来源、Checksum、适用环境及执行结果登记历史；已执行的正式迁移不可悄然编辑覆盖，应以新修订/前滚迁移维护审计和复现性。

**验收：** 现行 Schema、已执行脚本与历史记录可用唯一版本/Hash 对应，漂移被检出。

**核验合同与来源：** [migration-R02](#migration-R02)；本条对应的失败输入见下文验证矩阵。

### §08 环境漂移与部分成功治理
**机制：** 检测手工热修、旧环境缺步骤、跨区域不同版本及上次失败残余，不能依 IF EXISTS 让环境静默跳过不正确对象或错误约束。

**验收：** 同样版本下每个实例的结构/关键数据契约一致，否则提供可审计的修复路径。

**核验合同与来源：** [migration-R02](#migration-R02)；本条对应的失败输入见下文验证矩阵。

### §09 DDL 原子性与事务边界
**机制：** 区分支持事务性 DDL、单语句 Atomic DDL、隐式 COMMIT 和不可事务执行的特殊命令；多个 DDL 与回填 DML 不可假定总能作为一个原子操作回滚。

**验收：** 任一步中断时保存真实已生效范围，并只执行该引擎允许的回退/前滚。

**核验合同与来源：** [migration-R02](#migration-R02)；本条对应的失败输入见下文验证矩阵。

### §10 DDL 锁等级与长事务冲突
**机制：** 每个 DDL 操作需按目标引擎及版本确定元数据/表锁、获取/释放时点、应用连接和长事务阻塞；宣称 ONLINE/CONCURRENTLY 不意味着零锁。

**验收：** 长读、长写、读写峰值及超时场景能识别真实阻塞半径和止损阈值。

**核验合同与来源：** [migration-R02](#migration-R02)；本条对应的失败输入见下文验证矩阵。

### §11 表扫描、重写及磁盘/日志预算
**机制：** 类型更改、建索引和约束验证可能触发全表扫描、表数据 COPY、生成临时对象及 WAL/Redo/复制积压；要按真实数据规模测算空间、IO、持续时间和恢复余量。

**验收：** 在预估资源超限时不启动或安全终止，未改变数据正确性及保留范围。

**核验合同与来源：** [migration-R02](#migration-R02)；本条对应的失败输入见下文验证矩阵。

### §12 迁移工单与执行时序
**机制：** 每次操作应有前置依赖、请求所有权、操作对象、超时/暂停/失败处置和可观测的结果，变更顺序不可仅依据文件名或单台实例执行完成来推定。

**验收：** 恢复或重复执行不会乱序执行结构/回填收缩，生产写入与发布门禁仍受真实授权。

**核验合同与来源：** [migration-R02](#migration-R02)；本条对应的失败输入见下文验证矩阵。

### §13 PG 18 ALTER TABLE 锁与改型
**机制：** PostgreSQL 18 ALTER TABLE 的不同子命令使用不同锁，一般未另行标示时为 ACCESS EXCLUSIVE；SET DATA TYPE 可要求 USING 表达式并可能重写大量数据/更新统计。

**验收：** 真实子命令、类型转换及旧新数据/索引范围有官方对应与可复测锁成本。

**核验合同与来源：** [migration-R03](#migration-R03)；本条对应的失败输入见下文验证矩阵。

### §14 PG 18 NOT VALID 到 VALIDATE
**机制：** PostgreSQL 18 支持对 FK、CHECK 和 NOT NULL 的合适 NOT VALID/VALIDATE 流程，新 DML 可先受约束而存量仍需扫描验证；不能把 NOT VALID 套用到 UNIQUE/PK 或宣称存量已全部合法。

**验收：** 历史非法数据被识别及修复，VALIDATE 成功后才标记存量约束完全成立。

**核验合同与来源：** [migration-R03](#migration-R03)；本条对应的失败输入见下文验证矩阵。

### §15 PG 并发索引与无效残留
**机制：** CREATE INDEX CONCURRENTLY 不能放进普通事务块，构建可能因冲突/数据违规留下 INVALID 索引，其仍可能带来维护成本甚至 UNIQUE 提前生效影响；失败需单独核实清理。

**验收：** 实际索引在 Catalog 中为 Valid 且查询和唯一性契约无误，失败残余有批准处置。

**核验合同与来源：** [migration-R03](#migration-R03)；本条对应的失败输入见下文验证矩阵。

### §16 PG 字段默认与存量回填
**机制：** 改变 DEFAULT 只决定后续写入行为，不自动改写已存数据；常量默认新增列的快速路径依目标 PG 版本及表达式条件，不能将常量、volatile 默认和真实历史回填混为一谈。

**验收：** 旧 NULL/缺字段与新增默认均按各自语义读取，只有要求回填的历史行被有界处理。

**核验合同与来源：** [migration-R03](#migration-R03)；本条对应的失败输入见下文验证矩阵。

### §17 PG 类型、ENUM 与依赖对象
**机制：** PG ALTER TYPE/ENUM、列类型变换可能影响表达式、索引、视图、存储过程及旧客户端解码；不能通过临时强制 CAST 或 CASCADE 毫无审查地抹掉依赖。

**验收：** 实际新旧枚举/时间/精度样本及全部活跃对象在 DDL 前后保持合法含义。

**核验合同与来源：** [migration-R03](#migration-R03)；本条对应的失败输入见下文验证矩阵。

### §18 PG 事务 DDL 与进度证据
**机制：** 普通 PG DDL 可按具体子命令参与事务，但 CREATE INDEX CONCURRENTLY 有独立事务限制；pg_catalog/pg_stat_progress 等诊断随版本变化，不能用请求返回即证明所有异步消费者已接受变更。

**验收：** 结构/索引/锁/应用连接与历史迁移账本的最终状态一致，未宣称外部业务完成。

**核验合同与来源：** [migration-R03](#migration-R03)；本条对应的失败输入见下文验证矩阵。

### §19 MySQL 8.4 INSTANT/INPLACE/COPY 选型
**机制：** InnoDB 8.4 DDL 的 INSTANT、INPLACE、COPY 有不同能力、并发 DML 和重建范围；使用默认算法不等于所有操作都 Instant，应按具体字段、索引/行格式限制强制校验。

**验收：** ALTER 通过时回读实际算法可用性、锁、是否重建、数据结果及资源成本。

**核验合同与来源：** [migration-R04](#migration-R04)；本条对应的失败输入见下文验证矩阵。

### §20 MySQL Metadata Lock 与在线 DDL
**机制：** MySQL 在线 ALTER 可在准备/提交阶段需要排他 Metadata Lock，长事务可能使变更等待或阻塞业务；LOCK=NONE 在部分约束/操作下不可用，不能保证连续服务零等待。

**验收：** 混合长 SELECT、DML、DDL 的锁等待/超时及客户端中断均有可诊断结论。

**核验合同与来源：** [migration-R04](#migration-R04)；本条对应的失败输入见下文验证矩阵。

### §21 MySQL INSTANT 行版本及限制
**机制：** MySQL 8.4 INSTANT ADD/DROP COLUMN 有 Row Version、行数/字段/表属性等限制，版本过多会拒绝继续 INSTANT；不应静默降级到大表 COPY。

**验收：** 达到真实阈值或不适用表结构时安全拒绝，另行审查建表/重建成本。

**核验合同与来源：** [migration-R04](#migration-R04)；本条对应的失败输入见下文验证矩阵。

### §22 MySQL 类型调整/重建与精度
**机制：** MySQL 8.4 某些列类型变化必须 COPY，延长 VARCHAR 也受字节存储边界约束；数据库能 CAST 不证明金额、时区、Unicode 与历史值无损。

**验收：** 非法值、溢出、排序规则和编码极值在变更后保持批准的业务语义。

**核验合同与来源：** [migration-R04](#migration-R04)；本条对应的失败输入见下文验证矩阵。

### §23 MySQL Atomic DDL 与隐式提交
**机制：** MySQL 8.4 的 Atomic DDL 是受支持 InnoDB 单 DDL 与数据字典/Binlog 协调，不等于用户可把任意 DDL/DML 套进一个事务统一撤销，DDL 可能隐式提交既有事务。

**验收：** 异常/崩溃时操作实际生效状态与历史账本一致，不能声称应用事务也被原子回退。

**核验合同与来源：** [migration-R04](#migration-R04)；本条对应的失败输入见下文验证矩阵。

### §24 MySQL 在线 DDL 复制延迟与空间
**机制：** 在线 ALTER 即使允许源库并发 DML，也可能引起副本 DDL 应用滞后、额外在线日志、临时空间/回滚耗时；关键客户端不能在副本未追上时误判新字段不存在。

**验收：** 在目标真实副本拓扑测量延迟、空间、旧新 schema 混用和合法拒绝条件。

**核验合同与来源：** [migration-R04](#migration-R04)；本条对应的失败输入见下文验证矩阵。

### §25 SQLite 原生 ALTER 支持边界
**机制：** SQLite 对 RENAME/ADD/DROP 等 ALTER 操作支持范围随版本变化，不能把 MySQL/PostgreSQL 改列类型的语法直接用于其文件结构，简单改动与必须重建表的操作分开选择。

**验收：** 按目标 SQLite 版本检查可用语法以及旧新 Schema 和磁盘结构的实际差异。

**核验合同与来源：** [migration-R05](#migration-R05)；本条对应的失败输入见下文验证矩阵。

### §26 SQLite 12 步安全重建方案
**机制：** 涉及改列类型、PK/FK/UNIQUE/CHECK 的较复杂变更应依据 SQLite 官方安全表重建过程，不能先 RENAME 原表后新建导致 Trigger/View/FK 引用自动被错改。

**验收：** 重建前后行数、键和依赖 SQL 均相同或满足明确转换合同。

**核验合同与来源：** [migration-R05](#migration-R05)；本条对应的失败输入见下文验证矩阵。

### §27 SQLite FK、Trigger 与视图依赖
**机制：** SQLite Foreign Key 启用受连接设置与实际版本约束；重建和校验要包含 Trigger、Index、View、外键/SQL Schema 及旧数据，不能用 PRAGMA foreign_keys=OFF 视为已达完整性。

**验收：** 重建后 foreign_key_check 和实际合法父子操作正常，触发器/视图语义无遗漏。

**核验合同与来源：** [migration-R05](#migration-R05)；本条对应的失败输入见下文验证矩阵。

### §28 SQLite WAL 文件组及事务确认
**机制：** 单 SQLite 数据库的结构重建、WAL/-shm、读连接和备份快照有一致性要求；复制单独 .db 文件、强删 WAL 或直接编辑 sqlite_schema 不能替代官方安全流程。

**验收：** 正在读写及中断恢复时每个业务对象均存在受支持的一致视图。

**核验合同与来源：** [migration-R05](#migration-R05)；本条对应的失败输入见下文验证矩阵。

### §29 SQL Server ONLINE 索引与 Edition 限制
**机制：** SQL Server ONLINE CREATE/REBUILD/DROP INDEX 与列/唯一约束的支持依目标 SQL Server Edition/版本及具体索引类型；ONLINE 不表示从头到尾无需 Schema 锁或不会影响大量并发写入。

**验收：** 操作的 Edition、模式、锁、临时空间和实际读写阻塞被隔离验证。

**核验合同与来源：** [migration-R06](#migration-R06)；本条对应的失败输入见下文验证矩阵。

### §30 SQL Server RESUMABLE 与残余进度
**机制：** 支持的 RESUMABLE CREATE/REBUILD INDEX 可暂停/恢复，必须同时满足 ONLINE 与其他约束；Pause 不是 Cancel，不等于可删除运行状态或无资源占用。

**验收：** 故障/暂停/恢复后最终 Index State 正确且没有无界资源/业务等待。

**核验合同与来源：** [migration-R06](#migration-R06)；本条对应的失败输入见下文验证矩阵。

### §31 SQL Server DDL 的一致性及性能证据
**机制：** DDL/索引操作期间行版本、锁、tempdb 和执行计划可能变化；减少单次索引维护停机不能推断任意列类型更改都可无阻塞在线完成。

**验收：** 在真实 SQL Server 目标版本中记录完整执行、资源及业务结果，原索引/权限保持。

**核验合同与来源：** [migration-R06](#migration-R06)；本条对应的失败输入见下文验证矩阵。

### §32 SQL Server 超时回滚和异步业务边界
**机制：** DDL 被取消/超时后应检查实际对象状态及正在使用的事务/应用连接；即使 DDL 可回退，外部缓存、消息和已发生的客户业务事件不能自动回滚。

**验收：** 失败状态与客户完成、外部服务和真实数据库结构分别回读。

**核验合同与来源：** [migration-R06](#migration-R06)；本条对应的失败输入见下文验证矩阵。

### §33 MongoDB 8.0 Validator 与 collMod
**机制：** MongoDB 8.0 可用 collMod 更改 Schema Validator 和 validationLevel，`strict` 与 `moderate` 对已存在不合规文档的后续更新有不同要求；更改并不自动回填旧数据。

**验收：** 旧无效/旧有效/新增文档的插入和更新路径按指定 Validator 合法处理。

**核验合同与来源：** [migration-R07](#migration-R07)；本条对应的失败输入见下文验证矩阵。

### §34 MongoDB 历史文档及修复水位
**机制：** 升级 MongoDB 8.0 校验规则后存量非法文档仍可能留存，必须先枚举、修复及保留无法自动修正的业务证据；正常插入成功不能作为存量全部通过的证明。

**验收：** 历史扫描总量、例外、更新失败和再次修复样本有对应清单。

**核验合同与来源：** [migration-R07](#migration-R07)；本条对应的失败输入见下文验证矩阵。

### §35 MongoDB 9.0 Constraint 级别前置
**机制：** MongoDB 9.0 新增 validationLevel:"constraint"，不能用于 8.0。升级前按实际 9.0 文档完成 prepareConstraintValidationLevel:true，使用 validationAction:"error" 或 "errorAndLog" 并确认全部存量文档满足；设置过程扫描现有文档且可能失败，不能与同一次 validator 修改合并。strict 对未来写验证并不证明历史存量全合法，旧实例需独立扫描/修复。

**验收：** 以一条非法旧文档、合法存量及未准备/不合适 validationAction 分别调用目标实例 collMod；非法存量或前置不满足必须拒绝，合法准备后升级及后续非法写入行为分别核对。未运行 MongoDB 9.0 目标实例只记录合同，不报约束已采用。

**核验合同与来源：** [migration-R07](#migration-R07)；本条对应的失败输入见下文验证矩阵。

### §36 文档 Schema 与字段缺省合同
**机制：** MongoDB/BSON Validation、JSON Schema required/null/default、客户端 DTO、旧数据缺失是不同层级；自动从 API Schema 生成校验器时仍须独立判断缺失值与业务写入权限。

**验收：** 旧客户端写入、显式 null/缺失及非法字段不会被未经批准的默认值掩盖。

**核验合同与来源：** [migration-R07](#migration-R07)；本条对应的失败输入见下文验证矩阵。

### §37 分布式在线 Schema Job 状态
**机制：** CockroachDB 26.2 或 TiDB 等分布式引擎中 Schema 变更可能经历多个描述符/Job 阶段和后台 Backfill；DDL 请求返回、Job 完成与所有节点旧连接可读新版本是不同状态。

**验收：** 模拟 DDL Job 部分执行及拓扑变化时，写入/查询只使用受支持结构且有明确状态。

**核验合同与来源：** [migration-R08](#migration-R08)；本条对应的失败输入见下文验证矩阵。

### §38 分布式 Schema 版本同步窗口
**机制：** 数据库集群内旧新 Schema Descriptor 共存/租约及多节点缓存刷新期间，旧 SQL Writer 可能仍运行；必须基于目标版本的发布/兼容规则设计扩展与清理时点。

**验收：** 旧节点、慢请求和新节点更新期间业务键与字段语义稳定或明确拒绝。

**核验合同与来源：** [migration-R08](#migration-R08)；本条对应的失败输入见下文验证矩阵。

### §39 迁移工具版本历史与变更校验
**机制：** 采用 Flyway 等工具时版本迁移要保存 immutable Script/Checksum、目标环境 Schema History、成功/失败和发布操作者，不能修改已经下发的历史脚本来悄然绕过检测。

**验收：** 各环境执行相同版本在数据与 Schema 合同上可复现，未经审查的漂移触发门禁。

**核验合同与来源：** [migration-R08](#migration-R08)；本条对应的失败输入见下文验证矩阵。

### §40 Repeatable 迁移与真实幂等
**机制：** Flyway Repeatable Migration 等工具会按 Checksum 变化重新执行；`CREATE OR REPLACE`、参考数据 Upsert、DDL IF EXISTS 并非对任意用户数据无条件幂等。

**验收：** 变更脚本可证明重复运行无非法数据变更，失败重试具可诊断恢复路径。

**核验合同与来源：** [migration-R08](#migration-R08)；本条对应的失败输入见下文验证矩阵。

### §41 回填范围、稳定键和游标
**机制：** 历史记录回填按稳定的对象 Key/租户/主键顺序分批推进，避免深 OFFSET、无 ORDER BY 和分区内单独游标导致漏行/重复；每批记录上下限与源事实版本。

**验收：** 中途重启、删除/插入或跨分区迁移后不会漏掉合法旧记录。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

### §42 并发写入水位、增量追赶和业务源权威
**机制：** 回填过程新旧客户端仍可能更新原字段，必须建立可靠源版本/Change Watermark/触发器或 CDC 补偿，界定快照切点和后续增量，不能以回填 100% 即宣称数据已追平。

**验收：** 与回填同时更新同一业务 Key 的最新授权写入不会被旧快照覆盖。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

### §43 幂等回填、比较交换和冲突治理
**机制：** 批量回填应依据 Key、版本/乐观锁或 CAS、业务前置条件实现重复无害；禁止使用盲目 REPLACE/UPSERT 抹掉后来已确认的数据及权限字段。 回填提交使用源版本比较交换（例如 UPDATE ... WHERE id=? AND version=?），比较失败必须重读/归并，不可用无条件覆盖修复；同批重试和并发 Worker 均保留稳定批次/业务身份。

**验收：** 故障后重复执行及多个 Worker 竞争时只有合法的一次语义更新。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

### §44 批次限流、资源上限和失败处置
**机制：** Backfill Batch 大小、并发、事务时间、Lock、Replica Lag、WAL/Redo、温度及资金/用户请求阈值共同决定节流和暂停；不能强制全表一次 UPDATE 造成业务不可用。

**验收：** 负载升高、磁盘空间不足、死锁和超时时任务可靠暂停，恢复后成本有界。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

### §45 数据转换语义与非法存量
**机制：** 货币 Scale/Unit、时间/时区、编码 Collation、NULL/缺失/枚举及外部 ID 变更可能无损、需人工修复或必须拒绝；成功 CAST 不等于业务数据正确。

**验收：** 旧/新值逐 Key 样本与全量计数/校验可核对，非法数据列出修复与回滚边界。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

### §46 读写 Cutover、验证门禁与契约收缩
**机制：** 切换到新字段/表之前确认所有活跃 Reader/Writer、回填最终水位、来源/目标数量/Hash、权限和复制延迟；收缩旧列只在明确回放/备份/离线客户端窗口结束后执行。 收缩前还要覆盖离线客户端、低频导出、定时任务、历史消息及恢复后的旧备份读写器；已离线不等于永不回来，应有可拒绝的最低兼容版本或经证实的迁移完成证据。

**验收：** 旧写入真正停止，独立 Query/事件/导出没有继续依赖被删除字段。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

### §47 前滚修复、回退及不可逆变更
**机制：** 把可回退 Schema 变更、需要数据前滚恢复及不可逆字段/历史删除分开；执行 DROP/类型截断之后不能宣称仅回退应用包就可恢复数据和已外发业务结果。 DROP 列、单位有损转换和物理清理不会因回滚应用版本恢复被删除信息；退路须依赖可用的原始数据、兼容窗口或经验证恢复点，不能以 reverse SQL 文本存在证明可逆。

**验收：** 失败时权威数据库、历史脚本、快照、合法备份及已履约客户状态都有各自恢复目标。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

### §48 可复现的阶段性与 L6 最终验收
**机制：** 为变更保存数据库/SDK 版本、Schema/脚本 Hash、锁/扫描/回填进度、存量异常、写入水位、校验结果、事务/副本、授权身份及真实业务终点；静态文本、隔离测试、CI、生产运行分级。

**验收：** 仅对已实际执行的 DDL/回填和真实客户业务声明通过，未执行的故障和外部动作保持未验收。

**核验合同与来源：** [migration-R09](#migration-R09)；本条对应的失败输入见下文验证矩阵。

## 四、60 项静态失败输入及 L6 预期检查

下列为静态失败输入和项目级检查设计，不代表执行了真实生产数据库 DDL、数据回填或外部业务操作。

### 场景组 1：范围、兼容矩阵及变更账本
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 未经批准把客户账单金额单位从分改成元并直接覆盖历史记录 | §01 | 业务对象/合同及数据权限先行 |
| 数据库已改新字段而旧 API 仍把相同字段名当旧语义 | §02 | 数据库/API/消息的发布阶段独立 |
| 只按 ORM 模型生成 ALTER，遗漏真实数据库已存在的租户索引 | §03 | 源 DDL/数据样本及依赖清单完整 |
| 先 DROP 旧列，再部署仍在写旧列的离线客户端 | §04 | Expand-Migrate-Contract 阶段门禁正确 |
| 只测新写新读，旧客户端写入后新版 Consumer 无法解释 | §05 | 混合 Writer/Reader 矩阵真实兼容 |
| 双写两列无权威主次，失败回放把已更新的客户状态回退 | §06 | 唯一源权威和冲突修复可追溯 |

### 场景组 2：迁移历史、DDL 事务及锁资源
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 直接改写上个月已应用的 Flyway 迁移脚本，Checksum 与生产历史不符 | §07 | 历史迁移固定并以前滚脚本修正 |
| 测试环境手工添加了不同类型字段，IF NOT EXISTS 令错误漂移静默通过 | §08 | 真实 Schema 和版本账本一致 |
| 把 MySQL DDL 和账本 UPDATE 包进用户事务，错误以为失败能一起回滚 | §09 | 实际 DDL 原子/事务范围正确 |
| 上线前有空闲长事务持有 Metadata Lock，DDL 长时间阻塞读写 | §10 | 目标数据库锁/期限及业务影响明确 |
| 大表类型转换触发表重写，WAL 和磁盘临时空间不足 | §11 | 扫描/重写成本与安全余量满足 |
| 前一个 DDL 只成功一半，重新启动发布时把中间状态当全部完成 | §12 | 工单依赖和阶段进度真实回读 |

### 场景组 3：PostgreSQL 类型、约束及索引
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| PG 18 类型更改未定义 USING，非无损 CAST 导致历史金额变更 | §13 | 真实类型值域、USING/锁和结果无损 |
| PG 使用 NOT VALID 增加约束后便宣称旧百万行已全部满足条件 | §14 | 新写和历史 VALIDATE 分开 |
| PG CREATE INDEX CONCURRENTLY 失败留下 INVALID UNIQUE，仍被当成有效索引 | §15 | 实际索引 Valid/残留维护和唯一影响复核 |
| PG 只改 DEFAULT，误称已为所有历史 NULL 行实际补值 | §16 | 默认只影响后写，存量回填另验证 |
| PG ENUM 类型新增值后旧客户端硬编码状态拒绝或误认为成功 | §17 | 依赖/旧读写与枚举版本兼容 |
| 把 CREATE INDEX CONCURRENTLY 放进统一事务迁移脚本导致无法执行 | §18 | 该操作非普通事务块，计划及历史状态正确 |

### 场景组 4：MySQL 算法、Metadata Lock、复制延迟
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| MySQL 8.4 列类型改变却强制 INSTANT，结果自动失败但发布仍视作成功 | §19 | 算法支持和行/索引约束核查 |
| MySQL 在线 ALTER 末尾申请排他 Metadata Lock，耗尽服务可用连接 | §20 | 阶段性锁与长事务冲突可诊断 |
| INSTANT ADD/DROP 已用满 8.4 Row Versions，却默默退化为重建整表 | §21 | 达到行版本限制时明确拒绝或专门审批 |
| latin1 VARCHAR(255) 到 VARCHAR(256) 跨最大字节长度 255/256 边界，被误作无需重建的 Inplace | §22 | 字段值/行格式/重建成本正确 |
| MySQL Atomic DDL 因隐式提交提前提交客户资金相关 DML | §23 | Atomic DDL 不与外部事务混同 |
| MySQL Source 在线 DDL 已完成，但 Replica DDL 滞后且旧读取器仍被路由到副本 | §24 | 复制滞后和 Schema Readiness 并行验收 |

### 场景组 5：SQLite 重建及 SQL Server 维护
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| SQLite 直接用 PG ALTER COLUMN TYPE 语法修改现有列，变更失败 | §25 | 实际 SQLite 版本/支持语法匹配 |
| SQLite 先重命名旧表导致外键/视图引用被错误重写后复制新表 | §26 | 官方安全 12 步重建过程与依赖验证 |
| SQLite 重建期间关闭 FK 检查并忘记恢复，孤儿记录被持久接受 | §27 | foreign_key_check 与连接级校验有效 |
| SQLite 在线 WAL 活跃时单独复制 .db，恢复遗漏已提交订单 | §28 | 含 WAL 的受支持一致备份路径 |
| SQL Server 使用 ONLINE 建索引却目标 Edition/索引类型不支持而阻断发布 | §29 | Edition、锁与 Index 类型限制正确 |
| SQL Server RESUMABLE Index 暂停后被标成功并删除进度状态 | §30 | Resumable 作业实际恢复至完工且资源有界 |

### 场景组 6：SQL Server、MongoDB Validator 与文档差异
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| SQL Server Online Index 完成但 Version Store 失控使应用读写超时 | §31 | 实际在线索引的资源与客户查询正确 |
| SQL Server DDL 取消之后认为应用/外部通知已同时回滚 | §32 | 实际物理结构和外部客户义务分别确认 |
| MongoDB collMod strict 后历史非法文档没修，更新时突然持续报错 | §33 | 严格/温和校验和旧数据差异准确 |
| MongoDB 8.0 新文档验证器阻断新非法写入，就宣称老数据全量合法 | §34 | 全量旧数据扫描与新增校验分层 |
| MongoDB 8.0 按新 9.0 `constraint` 说明配置集合，实际 8.0 不支持 | §35 | 特性版本、存量保证的前置条件核实 |
| Mongo BSON 缺失字段被 JSON Schema default 注解默默替换为空角色 | §36 | 缺失、null、业务默认和权限字段分开 |

### 场景组 7：分布式 Schema Job 与迁移账本
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 分布式数据库 ALTER 发起后后台 Job 尚未 Public 就开放新客户端 | §37 | 真实 Job Phase 和可用 Schema 版本对应 |
| 一台旧节点保留 Schema Descriptor，切换后继续写已废弃列 | §38 | 租约/版本/旧写者兼容期有保证 |
| 已执行 Flyway Versioned Migration 被覆盖以修复 Bug，环境校验失败 | §39 | 前滚修订、版本 Hash 与历史记录一致 |
| Repeatable Migration 改了 Checksum 后重新执行带副作用的初始化脚本，重复扣费 | §40 | 可重复脚本真正幂等而非仅看名称 |
| 回填按 OFFSET 无稳定排序，期间删除记录导致下一页遗漏 | §41 | 稳定 Key 和范围水位覆盖全部源记录 |
| 回填 100% 后有旧 Writer 又改源列，新列数值已过期 | §42 | 增量追赶的真实水位与权威读写可见 |

### 场景组 8：幂等写入、资源、收缩和业务验收
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 回填 Worker 重试无 CAS 覆盖新提交客户状态 | §43 | 幂等版本与冲突规则保护新事实 |
| 每批历史更新锁住全部大表，复制积压且应用超时 | §44 | 批量/速率和提交日志有资源上限 |
| 金额 DECIMAL→FLOAT 成功转换却造成合法对账误差 | §45 | 实际单位/时间/精度和异常项单独确认 |
| 未等待旧离线客户端退役就删除旧字段，历史请求永久失败 | §46 | 所有 Reader/Writer 和回放窗口完成再收缩 |
| DROP 之后只回滚应用二进制文件便声称所有删除数据已恢复 | §47 | 不可逆历史删除和数据库业务权威真正修复 |
| CI Schema Validator 绿色却真实用户订单和敏感角色权限错误 | §48 | 静态/隔离/业务 L6 分级验收 |

### 场景组 9：混合版本、实例和故障叠加
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| PG NOT VALID 约束和 Mongo moderate 被误当作相同的历史存量保证 | §14、§33、§34 | 各数据库旧数据保证、强制条件独立 |
| MySQL INSTANT DDL Row Versions 用尽且 Replica 落后，同时应用直接读新列 | §20、§21、§24、§38 | 算法、元数据版本和复制一致性分层 |
| PG Concurrent Index 留下 INVALID 约束 + 新版本读写不兼容 | §05、§15、§39 | 索引真实状态、混合客户端、迁移账本一致 |
| SQLite 安全重建途中断电并被强制恢复旧裸文件复制 | §26、§27、§28、§47 | 真正数据库/WAL/FK 与恢复权限检查 |
| 分布式 Schema Descriptor 未同步，旧 Writer 继续更改正在回填字段 | §06、§37、§38、§42、§43 | 最新合法值不会被旧版本回填覆盖 |
| SQL Server Resumable Index 作业未完 + 复制延迟异常使查询重放旧计划 | §29、§30、§31、§44 | 索引/副本/读语义分别验收 |

### 场景组 10：存量、权限与不可逆组合故障
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 新增索引为了性能触发 PII 复制到外部临时测试系统 | §01、§11、§31、§48 | 数据边界、镜像权限与业务收益可证明 |
| 订单状态枚举收窄与旧客户端回放共同导致自动退款重复触发 | §05、§17、§36、§46 | 版本兼容和客户交易幂等并行保护 |
| 热表迁移超时后运维直接改 Schema History 为 Success | §07、§08、§12、§39 | 历史账本只能反映真正完成的 DDL |
| 历史日期时区转换与双写无源权威造成账单跨月少计 | §06、§41、§42、§45 | 时间窗口和数据权威按 Key 对账 |
| 反复重试回填到达磁盘/日志上限，管理员提前删旧分区保留文件 | §10、§11、§44、§47 | 容量止损、法律保留和恢复链正确 |
| Schema 切流成功但外部客户导出接口仍依赖老列并泄漏已撤权数据 | §02、§05、§46、§48 | 读写器/权限/导出及最终业务验收完整 |

## 五、组织批准、正式版本和 L5/L6 项目验收

1. 本规范 共 **48 项独立技术机制及 60 项静态失败场景**，10 组输入对全部 §01—§48 有直接或组合覆盖，技术来源用于追溯，项目实施时核对适用版本及职责。L5 与 L6 实际生产数据库变更、数据权限和业务验收仍独立执行。
静态场景、迁移脚本写好或 CI 通过都不等于真实生产 DDL、合法用户数据转换及客户业务验收。
3. L5 采用实际 PostgreSQL/MySQL/SQLite/SQL Server/MongoDB/CockroachDB/迁移工具版本与能力，L6 自行按授权判断真实租户、数据读取/写入权限、业务合同、停机/IO/日志预算、审批/费用和事故处置。未经许可不运行生产 Schema Migration、历史数据写入、敏感复制、外部支付或 DDL 强制回滚。
4. 相应数据库领域基线、数据模型/Schema 语义、SQL 查询、MVCC、WAL/故障恢复、分片、复制 HA 与备份/PITR、CDC 和数据质量专题各自保持职责。本版只约束数据库 DDL 执行、数据回填、旧新版本共存与 Contract 收缩的可靠性。

## 核验合同附录

各合同按条款范围列出输入、判据、合法邻例与恢复要求。来源版本及支持命题见[数据库来源表](../../../sources/database-sources.json)。

<a id="migration-R01"></a>

### migration-R01

**条款范围：** §01、§02、§03、§04、§05、§06

**目标工具/输入：** old/new Writer/Reader四象限与离线客户端准入。新写旧读失败、双写无权威、先drop旧列、旧消费者延迟回归

**判据：** expand/migrate/contract顺序及每个兼容方向明确，不靠新版本全绿

**合法邻例：** 无破坏新增可选字段与无旧读者的单实体部署可合法简化

**恢复：** 保留旧权威源，暂停收缩并fence真正不兼容的旧入口

**来源：** [PG-D](https://www.postgresql.org/docs/18/sql-altertable.html)、[JS-V](https://json-schema.org/draft/2020-12/json-schema-validation)、[PB-3](https://protobuf.dev/programming-guides/proto3/)、[AV-S](https://avro.apache.org/docs/1.12.0/specification/)。关系：implementation-and-organisation-synthesis

<a id="migration-R02"></a>

### migration-R02

**条款范围：** §07、§08、§09、§10、§11、§12

**目标工具/输入：** 迁移history checksum、实际Catalog、锁和空间/日志预算。已执行脚本改hash、DDL部分成功、长事务阻锁、磁盘不足

**判据：** history和真实数据库状态对照；语句原子性不等于部署整体原子

**合法邻例：** 幂等确认现有目标正确可无操作，不能仅因重复执行就拒绝

**恢复：** 记录每阶段已生效对象，前滚修复或验证恢复，不任意repair清历史

**来源：** [FW-H](https://documentation.red-gate.com/flyway/flyway-concepts/migrations/flyway-schema-history-table)、[PG-D](https://www.postgresql.org/docs/18/sql-altertable.html)、[MY-D](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html)。关系：implementation-and-organisation-synthesis

<a id="migration-R03"></a>

### migration-R03

**条款范围：** §13、§14、§15、§16、§17、§18

**目标工具/输入：** ALTER TABLE NOT VALID/VALIDATE；CREATE INDEX CONCURRENTLY；pg_constraint/pg_index。非法旧行、新非法写、无效残余索引、volatile DEFAULT/重写

**判据：** PG18 FK/CHECK/not-null存量与新写规则分别验证；Valid状态独立

**合法邻例：** 合法旧数据修复后VALIDATE及常量默认快路径可接受，不硬要求重写

**恢复：** 保留失败索引/约束身份，受控清残余或继续验证；有损改型需源数据退路

**来源：** [PG-D](https://www.postgresql.org/docs/18/sql-altertable.html)、[PG-X](https://www.postgresql.org/docs/18/sql-explain.html)。关系：implementation-and-organisation-synthesis

<a id="migration-R04"></a>

### migration-R04

**条款范围：** §19、§20、§21、§22、§23、§24

**目标工具/输入：** ALTER TABLE ALGORITHM/LOCK；INFORMATION_SCHEMA INNODB_TABLES TOTAL_ROW_VERSIONS。超行版本、metadata lock、latin1 255→256及复制追赶

**判据：** 实际8.4算法/字节边界、隐式提交、锁/IO/复制成本正确

**合法邻例：** 同一字节长度区间扩VARCHAR可合法inplace，不能按字符数统一拒绝

**恢复：** 按真实残余状态前滚/重新建表；保留binlog/基线及旧读写兼容

**来源：** [MY-D](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html)、[MY-W](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html)。关系：implementation-and-organisation-synthesis

<a id="migration-R05"></a>

### migration-R05

**条款范围：** §25、§26、§27、§28

**目标工具/输入：** SQLite受支持ALTER或12步重建；foreign_key_check/integrity_check/backup。先改名旧表污染引用、漏trigger/view/FK、活跃WAL只复制db

**判据：** 原生能力按实际sqlite_version；重建完整Schema与数据/引用

**合法邻例：** 事务内合法DDL回滚、小型离线迁移不要求商业迁移平台

**恢复：** 事务失败回滚或从一致Backup API恢复；重开连接读回FK配置

**来源：** [SQ-D](https://www.sqlite.org/lang_altertable.html)、[SQ-F](https://www.sqlite.org/foreignkeys.html)、[SQ-B](https://www.sqlite.org/backup.html)、[SQ-W](https://www.sqlite.org/wal.html)。关系：implementation-and-organisation-synthesis

<a id="migration-R06"></a>

### migration-R06

**条款范围：** §29、§30、§31、§32

**目标工具/输入：** SQL Server目标版本/edition与online/resumable实际Catalog。把ONLINE当无SCH-M锁、暂停任务当完成、超时后旧worker继续

**判据：** 真实支持、异步/残余进度、锁/资源和业务切流分阶段确认

**合法邻例：** 所选edition不支持时用获批离线窗口是合法替代，不伪称在线

**恢复：** 按实际任务状态resume/abort并校验对象，不把应用回退当DDL数据回退

**来源：** [SS-D](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/guidelines-for-online-index-operations?view=sql-server-ver16)、[SS-I](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver16)。关系：implementation-and-organisation-synthesis

<a id="migration-R07"></a>

### migration-R07

**条款范围：** §33、§34、§35、§36

**目标工具/输入：** 目标Mongo collMod validator/validationLevel/action及准备命令。8.0套9.0 constraint、strict未扫旧数据、同命令改validator+升级constraint

**判据：** 版本和prepareConstraintValidationLevel/error action/全量扫描前置分别成立

**合法邻例：** 8.0 strict/moderate配合独立旧数据治理可合法，不强迫升级9.0

**恢复：** 隔离非法存量，按原Schema权威修复后验证，不把校验器更新当已回填

**来源：** [MO-V](https://www.mongodb.com/docs/manual/core/schema-validation/specify-validation-level/)、[JS-V](https://json-schema.org/draft/2020-12/json-schema-validation)。关系：implementation-and-organisation-synthesis

<a id="migration-R08"></a>

### migration-R08

**条款范围：** §37、§38、§39、§40

**目标工具/输入：** SHOW JOBS/实际Schema；Flyway validate/history及repeatable checksum。SQL响应后job未完、重复迁移重发副作用、repair掩真实漂移

**判据：** 异步job、Schema传播、不可变history与真实幂等独立

**合法邻例：** 重复迁移合法无操作/安全replace可以接受，不要求每次都有行变化

**恢复：** 核对真实已提交阶段，按工具支持前滚/resume；不可逆旧数据另恢复

**来源：** [CR-D](https://docs.cockroachlabs.com/docs/v26.2/online-schema-changes)、[FW-H](https://documentation.red-gate.com/flyway/flyway-concepts/migrations/flyway-schema-history-table)。关系：implementation-and-organisation-synthesis

<a id="migration-R09"></a>

### migration-R09

**条款范围：** §41、§42、§43、§44、§45、§46、§47、§48

**目标工具/输入：** 稳定keyset回填、UPDATE WHERE version=? CAS、cutover admission matrix。旧snapshot覆盖在线新值、count100%未追增量、离线旧读者回归、drop后假可逆

**判据：** 源版本/增量追赶/新旧读写/收缩及原始退路均有实证

**合法邻例：** 无并发的一次性离线迁移可省CDC；旧读者被有效fence后可收缩

**恢复：** CAS失败重读归并、重放未追增量，收缩前保留完整恢复点/源映射

**来源：** [PG-D](https://www.postgresql.org/docs/18/sql-altertable.html)、[KA-C](https://kafka.apache.org/41/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html)、[JS-V](https://json-schema.org/draft/2020-12/json-schema-validation)。关系：implementation-and-organisation-synthesis
