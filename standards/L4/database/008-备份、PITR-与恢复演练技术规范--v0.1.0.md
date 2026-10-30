# L4 备份、PITR 与恢复演练技术规范

**文档ID：** STD-L4-DATABASE-008　**版本：** 0.1.0　**状态：** adopted　**生效日期：** 2026-10-30

## 一、技术范围、真实业务条件与分层职责

本专项为 L4 数据库与数据工程领域第 09 项独立技术规范，约束实际选用的数据库备份资产、恢复链、受支持的时点恢复、离线/在线一致快照、独立恢复演练及客户业务数据权利。**不强制小型系统上多副本、商业备份服务或增加常驻服务器。** 适用条款按真实数据库、备份机制、数据权利与已批准 RPO/RTO 选择。

相应领域通用基线、数据模型/Schema、SQL、事务/MVCC、索引、物理 WAL/Crash Recovery、分区/分片、复制/HA、Schema 迁移与回填各保持原有权威。本专项仅对**备份保留链、可选择恢复点、真实恢复步骤/验证和恢复演练**提出完整机制。复制 ACK 不能代替备份；物理 Crash Recovery 不能自动支持 PITR；云服务 PITR 与客户实际履约也不是同一结果。数据安全/CDC/元数据等相邻专题及现行后端业务事务与消息工作流继续独立负责外部客户权利。L5 记录所选引擎/服务/工具版本与许可，L6 决定生产访问、区域、密钥、故障注入、费用、业务合同及真实验收。

## 二、官方技术依据与版本条件（2026-10-15）

| 官方资料 | 发布性质 | 本专项采用范围 |
| --- | --- | --- |
| [PostgreSQL 18 Backup and Restore](https://www.postgresql.org/docs/18/backup.html) | 固定版本官方文档 | 逻辑备份、文件系统备份及连续归档是不同恢复机制 |
| [PostgreSQL 18 Continuous Archiving and PITR](https://www.postgresql.org/docs/18/continuous-archiving.html) | 固定版本官方文档 | Base Backup、WAL 归档和 PITR 恢复连续性、Timeline |
| [PostgreSQL 18 pg_basebackup](https://www.postgresql.org/docs/18/app-pgbasebackup.html) | 固定版本官方命令 | 全量与基于先前 Manifest 的增量备份能力 |
| [PostgreSQL 18 pg_verifybackup](https://www.postgresql.org/docs/18/app-pgverifybackup.html) | 固定版本官方命令 | Manifest/文件及 WAL 范围校验不是实际恢复证明 |
| [PostgreSQL 18 pg_combinebackup](https://www.postgresql.org/docs/18/app-pgcombinebackup.html) | 固定版本官方命令 | 合成完整备份依赖所有之前的备份 |
| [PostgreSQL 18 Backup Manifest Format](https://www.postgresql.org/docs/18/backup-manifest-format.html) | 固定版本官方格式 | Backup Manifest 的文件、Checksum、WAL-Ranges 和系统标识 |
| [PostgreSQL 18 WAL Recovery Targets](https://www.postgresql.org/docs/18/runtime-config-wal.html) | 固定版本官方配置 | Recovery Target LSN/Time、Inclusive 与 Timeline |
| [MySQL 8.4 Backup and Recovery](https://dev.mysql.com/doc/refman/8.4/en/backup-and-recovery.html) | 固定版本官方文档 | 备份方法及恢复目标 |
| [MySQL 8.4 mysqldump](https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html) | 固定版本官方命令 | --single-transaction 的 InnoDB 快照与非事务表限制 |
| [MySQL 8.4 PITR using Binary Logs](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html) | 固定版本官方文档 | 完整备份后的 Binlog Replay 和恢复边界 |
| [MySQL 8.4 PITR Overview](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery.html) | 固定版本官方文档 | Binlog 文件及时间点/事务位置恢复的适用前提 |
| [SQLite Online Backup API](https://www.sqlite.org/backup.html) | SQLite 官方动态接口文档 | 并发访问下受支持的一致性数据库复制 |
| [SQLite VACUUM INTO](https://www.sqlite.org/lang_vacuum.html) | SQLite 官方动态 SQL 文档 | 一致副本和目标文件/设备的实际要求 |
| [SQLite WAL](https://www.sqlite.org/wal.html) | SQLite 官方动态实现文档 | 活跃 WAL 数据库主文件与 -wal/-shm 的协调 |
| [SQL Server Recovery Models](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/recovery-models-sql-server?view=sql-server-ver16) | Microsoft 固定目标版本文档 | Simple、Full、Bulk-Logged 决定备份及 PITR 能力 |
| [SQL Server Differential Backups](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/differential-backups-sql-server?view=sql-server-ver17) | Microsoft 官方版本化文档 | Differential Base 对全量备份的依赖 |
| [SQL Server Restore Sequences](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/plan-and-perform-restore-sequences-full-recovery-model) | Microsoft 官方文档 | 完整/差异/日志与 Restore Sequence 顺序 |
| [SQL Server Apply Transaction Log Backups](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/apply-transaction-log-backups-sql-server?view=sql-server-ver15) | Microsoft 官方文档 | 日志序列、NORECOVERY 与目标时间恢复 |
| [SQL Server Tail Log Backups](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/tail-log-backups-sql-server?view=sql-server-ver16) | Microsoft 官方文档 | 适用时保留尚未备份的事务日志尾部 |
| [MongoDB 8.0 Self-managed Backups](https://www.mongodb.com/docs/v8.0/core/backups/) | 固定目标版本官方文档 | 文件快照、Dump 及管理型连续备份支持差异 |
| [MongoDB 8.0 mongodump and mongorestore](https://www.mongodb.com/docs/v8.0/tutorial/backup-and-restore-tools/) | 固定目标版本官方文档 | Replica Set --oplog、恢复与性能影响 |
| [MongoDB 8.0 Sharded Backup and Restore](https://www.mongodb.com/docs/v8.0/administration/backup-sharded-clusters/) | 固定目标版本官方文档 | 跨 Shard 协调一致备份要求 |
| [DynamoDB Point-in-time Recovery](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html) | AWS 动态托管服务文档 | 1–35 日 Recovery Window、表级恢复及费用 |
| [Spanner PITR Overview](https://docs.cloud.google.com/spanner/docs/pitr) | Google Cloud 动态托管服务文档 | earliest_version_time、1 小时到 7 日的版本窗口 |
| [Spanner Use PITR](https://docs.cloud.google.com/spanner/docs/use-pitr) | Google Cloud 动态操作指南 | Version Retention 不自动补齐过去历史、恢复到新数据库 |

固定版本文档只适用于对应数据库/工具，SQLite 文档和 DynamoDB/Spanner 云服务说明按 L5 实际采用时核对配置、权限和费用。备份工具功能不构成所有项目的强制依赖；对企业专属或托管备份能力，应单独确认许可和真实可用性。不得用文件存在、备份目录大小或静态命令输出代替实际恢复。

## 三、48 项独立备份、PITR 与恢复机制

### §01 备份资产与业务权威范围
**机制：** 为真实项目列出数据库集群、表空间、租户、对象附件、凭据关联和应用依赖，划分必须恢复的权威状态与可重建缓存；不能只备份主表而称已完成用户业务恢复。

**验收：** 每份恢复计划可映射独立业务对象、必要文件/密钥/Schema 以及实际授权主体。

**核验合同与来源：** [backup-R01](#backup-R01)；本条对应的失败输入见下文验证矩阵。

### §02 故障等级、RPO、RTO 与恢复验收
**机制：** 分别定义误删、逻辑污染、实例宕机、整区不可用和备份库遭破坏等故障模型及可接受数据丢失与恢复时间，不将一个备份成功通知当成 RPO/RTO 实测。

**验收：** 为每种故障保存恢复起点、目标时间、可用性、已确认业务键和未满足承诺。

**核验合同与来源：** [backup-R01](#backup-R01)；本条对应的失败输入见下文验证矩阵。

### §03 备份、复制、缓存与 Crash Recovery 分离
**机制：** 实时副本可复制误删，WAL Crash Recovery 需要原数据文件，缓存可能过期，备份则应维持独立的历史恢复副本；不同机制不互相替代。

**验收：** 单独注入节点损坏与合法业务误删，分别证明采用的正确恢复路径。

**核验合同与来源：** [backup-R01](#backup-R01)；本条对应的失败输入见下文验证矩阵。

### §04 单引擎恢复与跨系统客户结果
**机制：** 数据库达到事务一致状态不自动恢复对象存储、支付商、邮件、消息队列及授权令牌；应确定彼此引用的最后共同一致点与补偿责任。

**验收：** 数据库和外部业务的已完成、未知、待履约状态可用稳定操作键对账。

**核验合同与来源：** [backup-R01](#backup-R01)；本条对应的失败输入见下文验证矩阵。

### §05 完整备份资产清单与依赖
**机制：** 列明 Schema、用户/角色、扩展、Tablespace、Data Files、事务日志、恢复脚本、加密钥匙、配置及网络凭据的实际包含/排除范围，避免数据完好却无法启动或访问。 恢复 Manifest 还要包含引擎/工具精确版本、数据/日志/增量父链、表空间与对象附件、密钥版本、恢复账号/权限、配置和可选恢复点；每个依赖有内容身份与可用性，不以压缩包文件名代替。

**验收：** 从全新隔离环境使用备份内和获授权的外部依赖恢复实际完整业务对象。

**核验合同与来源：** [backup-R01](#backup-R01)；本条对应的失败输入见下文验证矩阵。

### §06 快照一致性与跨对象时间点
**机制：** 物理快照、事务快照、逻辑 Dump 与跨 Shard 协同备份对写入并发和一致性点的保证不同；未经验证不应将多个时间不同的文件拼接成全局一致备份。

**验收：** 保留快照水位/Commit LSN/时间及锁或事务前置，验证多表关联与外部键。

**核验合同与来源：** [backup-R01](#backup-R01)；本条对应的失败输入见下文验证矩阵。

### §07 Full、Incremental、Differential、Log Chain 区别
**机制：** 全量、增量、差异、WAL/Redo/Binlog/事务日志备份采用不同依赖图；某次增量备份成功不意味着旧基线文件可以安全删除。

**验收：** 指定恢复时间点能找到完整且版本相容的所有基线和日志节点。

**核验合同与来源：** [backup-R02](#backup-R02)；本条对应的失败输入见下文验证矩阵。

### §08 恢复链 Manifest 与身份校验
**机制：** 给每份备份分配不复用的标识、源 System ID/Cluster ID、版本、文件清单、依赖 LSN/时间线、Checksum 和存储位置，避免错用其他集群同名文件。

**验收：** 备份 Manifest 的原始身份、依赖、文件 Hash 与恢复源一一对应。

**核验合同与来源：** [backup-R02](#backup-R02)；本条对应的失败输入见下文验证矩阵。

### §09 恢复目标时间与包含性
**机制：** 业务目标应由经过授权的 UTC 时间/LSN/事务标记给出，明确恢复时点前、时点上及之后事务的包含关系和合法观测时间差。

**验收：** 边界点两侧交易及跨时区/夏令时数据能按批准的时点精确复算。

**核验合同与来源：** [backup-R02](#backup-R02)；本条对应的失败输入见下文验证矩阵。

### §10 跨数据库恢复时间和全局时钟
**机制：** 各引擎 LSN/GTID/TimeLine、客户端 Wall Clock、对象存储事件版本不是一个通用全局时钟；跨服务 PITR 需单独设计可验证的共同业务水位。

**验收：** 多系统各恢复点与外部交易同一操作键对账，不能靠同一分钟戳默认一致。

**核验合同与来源：** [backup-R02](#backup-R02)；本条对应的失败输入见下文验证矩阵。

### §11 备份不可变、访问控制与隔离
**机制：** 备份历史需防被主业务账号误删、覆盖、加密勒索或篡改；保留与日志归档的授权角色与生产主账号适度隔离，不因备份无需数据库写权限便对外公开。

**验收：** 模拟普通业务账号越权修改备份时必须拒绝，合法恢复凭据独立可用。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §12 机房及地域独立性
**机制：** 备份与源数据库位于同一故障域、账号或云区域时可能同步损毁；异地保存应同时遵守实际数据驻留与复制许可，不能只凭不同 Bucket 名称宣布灾备。

**验收：** 测试隔离源节点/账号/区域后的备份独立可访问性以及合规边界。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §13 加密、密钥生命周期和复原权利
**机制：** 备份加密密钥、KMS 配额/授权、密钥版本和恢复所需证书应与备份保留期匹配；删除旧密钥会让文件仍在但永不可解密。

**验收：** 在批准的隔离账户及灾难恢复身份下实际解密并读取敏感业务数据，非法角色拒绝。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §14 隐私、保留和法律删除冲突
**机制：** 长期 PITR、不可变归档和客户合法删除/保留要求需要按具体法律和合同治理，不能以备份存在为由永久保存敏感数据或为恢复而公开所有历史版本。

**验收：** 能解释到期清理、Legal Hold、恢复后删除重放与数据权利的适用范围。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §15 备份依赖 DAG 与安全清理
**机制：** 清理策略应保留所有被后续增量/差异或日志恢复链引用的前置备份，不能只按文件创建日期删除；不可达文件识别另有授权与校验。 删除判定必须从所有保留恢复点及被保护 Snapshot/Tag 求依赖传递闭包；包括密钥、配置、增量基线和日志区间。先计算候选再在原子/受控窗口复核新引用，无法证明不可达时保守保留；清理后重新验证承诺的最早/最新恢复点。

**验收：** 清理后对最早、最新和随机目标时点仍能完成受支持的恢复链求解。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §16 恢复容量、传输和成本预算
**机制：** 结合备份总字节、压缩比、解密、增量合并、WAL Replay、跨区传输和冷存储取回估算真实 RTO/费用，不凭单文件下载时长预测整库完成。

**验收：** 代表性数据规模下恢复步骤耗时与费用满足已批准阈值，资源不足时安全拒绝。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §17 备份频率、快照重叠及节流
**机制：** 调度备份与业务热点、DDL、大规模回填、索引维护、压缩、复制积压冲突时需避免异常资源叠加和未完成备份相互覆盖。

**验收：** 多个并发备份/流控/取消场景不会损坏已成功备份和当前业务写入。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §18 在线备份对读写和资源影响
**机制：** 逻辑 Dump、跨 Shard 扫描和物理备份可能造成 IO、内存、锁和缓存污染；自动备份成功不证明用户请求未受影响。

**验收：** 测量备份期间写入延迟、读资源、CPU/IO/网络、复制延迟和合法数据可见性。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §19 备份健康与归档滞后监测
**机制：** 区分计划创建、实际启动、远端 ACK、Manifest 完整、日志归档、水位/Retention 与恢复测试成功；监测断流不是零错误。

**验收：** 某一步失败、过期或未完成时不能把下次定时计划视作已有可用的恢复点。

**核验合同与来源：** [backup-R03](#backup-R03)；本条对应的失败输入见下文验证矩阵。

### §20 PostgreSQL 逻辑备份与 PITR 的区别
**机制：** PostgreSQL 18 pg_dump/pg_dumpall 为逻辑数据与 SQL 对象导出，不包含可从 Dump 继续 WAL Replay 的物理基础，不能用 pg_dump 文件直接声称可做 WAL 连续恢复。

**验收：** 实际 Dump 可被恢复成合法数据，但仅物理基线与适配 WAL 才构成对应 PITR。

**核验合同与来源：** [backup-R04](#backup-R04)；本条对应的失败输入见下文验证矩阵。

### §21 PostgreSQL pg_basebackup 与 Cluster Scope
**机制：** PostgreSQL 18 pg_basebackup 及低层 Base Backup 依真实权限、Tablespace、WAL 保留和相同 Cluster ID；不能把单表 Dump 或缺失外置文件的复制当成完整 Base Backup。

**验收：** 对数据目录、Tablespace、Backup Label 与支持的 WAL Range 形成一致可恢复基线。

**核验合同与来源：** [backup-R04](#backup-R04)；本条对应的失败输入见下文验证矩阵。

### §22 PostgreSQL 连续 WAL 归档与缺口
**机制：** 归档要从基线开始覆盖连续 WAL，Archive Command 返回成功必须代表真正持久成功；误报零退出码会丢失必要 WAL，Timeline 分叉也不能仅按文件名字数字排序。

**验收：** 故障时可审计 Archive Success、WAL 文件完整性、起始 LSN 和 Timeline History。

**核验合同与来源：** [backup-R04](#backup-R04)；本条对应的失败输入见下文验证矩阵。

### §23 PostgreSQL pg_verifybackup 的能力边界
**机制：** pg_verifybackup 可根据 Manifest 检查文件、Checksum 和必要 WAL；某些格式需跳过 WAL Parse，工具本身不能检验数据库启动与业务逻辑可用性。

**验收：** 先检查 Manifest/WAL 后在隔离实例实际启动并运行授权业务查询。

**核验合同与来源：** [backup-R04](#backup-R04)；本条对应的失败输入见下文验证矩阵。

### §24 PostgreSQL 增量与 pg_combinebackup 链
**机制：** PG 18 Incremental 依上一次 Manifest 与 WAL Summary，恢复需要所有依赖备份并由 pg_combinebackup 合成，备份工具不负责保留依赖 DAG。

**验收：** 删除任一被依赖基线时静态校验失败；合法合并后完整启动恢复成功。

**核验合同与来源：** [backup-R04](#backup-R04)；本条对应的失败输入见下文验证矩阵。

### §25 PostgreSQL PITR 目标与 Timeline
**机制：** recovery_target_time/lsn/xid 与 recovery_target_inclusive、recovery_target_timeline 的语义须按目标版本与重放日志确定，停止点后历史分叉不宜随意覆盖。

**验收：** 目标时点之前/之后和边界恰好提交的业务记录按约定保留或排除。

**核验合同与来源：** [backup-R04](#backup-R04)；本条对应的失败输入见下文验证矩阵。

### §26 PostgreSQL 参数与外部配置完整性
**机制：** PG WAL 归档不自动恢复手工更改的 postgresql.conf、pg_hba.conf、证书和外部密钥；恢复受目标 PG/OS/扩展及 Tablespace 兼容限制。

**验收：** 独立恢复后的配置、授权角色、扩展与业务账户可用且不越权。

**核验合同与来源：** [backup-R04](#backup-R04)；本条对应的失败输入见下文验证矩阵。

### §27 MySQL 一致逻辑快照的引擎边界
**机制：** MySQL 8.4 mysqldump --single-transaction 的一致快照适用于 InnoDB 等事务表，MyISAM/MEMORY 可能在 Dump 期间改变，且 DDL 竞态会影响备份；不能仅依参数名当全库一致。

**验收：** 在含不同存储引擎、并行 DDL/写入的测试库证明实际一致范围或受控停写。

**核验合同与来源：** [backup-R05](#backup-R05)；本条对应的失败输入见下文验证矩阵。

### §28 MySQL Binary Log PITR 开启与位置
**机制：** MySQL 8.4 使用完整备份加随后连续 Binlog 进行时点恢复；恢复要保存 Binlog 文件、事件位置、GTID/Server 身份，不能以 Relay Log 收到 ACK 替代完整可用链。

**验收：** 针对选择的时间点能定位完整日志序列及业务事务的启动/停止位置。

**核验合同与来源：** [backup-R05](#backup-R05)；本条对应的失败输入见下文验证矩阵。

### §29 MySQL mysqlbinlog 回放与双重执行风险
**机制：** 重放 Binlog 需按正确顺序/位置或允许目标过滤事件，恢复实例若已有该事务会导致重复 DML/外部副作用；跨数据库业务不由日志文件自动保持一致。

**验收：** 隔离恢复环境中精确回放并按业务操作键核对，不向生产/支付服务发出真实动作。

**核验合同与来源：** [backup-R05](#backup-R05)；本条对应的失败输入见下文验证矩阵。

### §30 MySQL 物理/逻辑备份及工具支持
**机制：** InnoDB 物理备份、官方备份工具与 mysqldump 逻辑备份的版本、许可、Redo/Undo/恢复步骤和一致性承诺不同；不可把某个商业专属功能当免费版本默认具备。

**验收：** 记录所选备份工具、实际许可、引擎及恢复过程，不依赖未安装功能。

**核验合同与来源：** [backup-R05](#backup-R05)；本条对应的失败输入见下文验证矩阵。

### §31 MySQL 从库备份与故障位置
**机制：** 在 Replica 上获取备份可减轻 Source 负载，但必须保存 Replica 已执行 GTID、复制延迟、Source Binlog 连续性和合法恢复目标；只复制 Relay Log 未必构成可恢复备份。

**验收：** 切主前后确认数据基线与实际日志来源一致、无缺失和跨账号风险。

**核验合同与来源：** [backup-R05](#backup-R05)；本条对应的失败输入见下文验证矩阵。

### §32 SQLite Backup API 一致性快照
**机制：** SQLite 在线 Backup API 有受支持的一致复制语义；大数据库 Step/Busy 及源写入并发影响完成时间，不能用普通文件复制替代实际 Backup API。

**验收：** 在 WAL 持续写入期间复制到独立新文件后能读取和通过外键/业务校验。

**核验合同与来源：** [backup-R06](#backup-R06)；本条对应的失败输入见下文验证矩阵。

### §33 SQLite WAL 文件组和备份边界
**机制：** SQLite WAL 模式下主 .db 与 -wal、-shm 状态相关，活跃库仅复制主文件可能丢失未 Checkpoint 的已确认提交；正确做法依 Backup API 或可证明静态一致快照。

**验收：** 恢复时看到同一事务完整数据，缺必要 WAL 的备份明确失效。

**核验合同与来源：** [backup-R06](#backup-R06)；本条对应的失败输入见下文验证矩阵。

### §34 SQLite VACUUM INTO 与设备持久性
**机制：** VACUUM INTO 可导出一致紧凑副本，但其耗时、额外磁盘、输出文件权限和故障后持久等级另需确认，不能以文件存在即认定最终写入已耐久。

**验收：** 中止/满盘/恢复后副本可验证、未被公开，并与业务数据快照一致。

**核验合同与来源：** [backup-R06](#backup-R06)；本条对应的失败输入见下文验证矩阵。

### §35 SQL Server 恢复模型与 PITR 能力
**机制：** SQL Server Simple、Full、Bulk-Logged 恢复模型决定日志备份及可支持的 PITR；含 Bulk-Logged 操作的日志备份可能无法在该段中途任意时间恢复。

**验收：** 在所选 Recovery Model 和日志窗口内可执行目标恢复，超出能力明确报告。

**核验合同与来源：** [backup-R07](#backup-R07)；本条对应的失败输入见下文验证矩阵。

### §36 SQL Server 完整与差异备份基线
**机制：** SQL Server Differential 以先前合法 Full Backup 为基线，不能任意配对不同的 Full/Copy-Only/文件组或备份 Media Set；时间最近不自动意味着同一基线。

**验收：** 可根据 BackupSet/LSN 等标识追踪差异依赖并拒绝错配。

**核验合同与来源：** [backup-R07](#backup-R07)；本条对应的失败输入见下文验证矩阵。

### §37 SQL Server Log Chain、Tail-Log 与 NORECOVERY
**机制：** 在 Full/Bulk-Logged Recovery Model 下需要正确顺序应用事务日志备份，并在适用情境保存 Tail-Log；RESTORE WITH NORECOVERY 保持继续重放能力，过早 WITH RECOVERY 会终止当前日志序列。

**验收：** 从合法基线+差异+日志链恢复到批准事务时间点，未发生未声明数据截断。

**核验合同与来源：** [backup-R07](#backup-R07)；本条对应的失败输入见下文验证矩阵。

### §38 SQL Server Restore 检查与实际恢复区别
**机制：** Backup Checksum、RESTORE VERIFYONLY 和 Header 信息只能发现部分损坏，无法证明所有表、权限、登录名、外部应用依赖和客户业务均可恢复。

**验收：** 必须在隔离目标数据库完成实际 RESTORE、DBCC/业务查询及授权测试。

**核验合同与来源：** [backup-R07](#backup-R07)；本条对应的失败输入见下文验证矩阵。

### §39 MongoDB Replica Set mongodump 和 --oplog
**机制：** MongoDB 8.0 使用 mongodump/restore 对小规模部署和 Replica Set 可用，活跃写入时需要 --oplog 或受控停止写以获得适用一致性，扫描本身可能带来缓存压力。

**验收：** 在真实 Replica Set 写入交错和 Oplog Replay 下验证多集合相关对象一致。

**核验合同与来源：** [backup-R07](#backup-R07)；本条对应的失败输入见下文验证矩阵。

### §40 MongoDB Shard 一致备份与 Atlas/Ops Manager
**机制：** MongoDB 8.0 分片集群不是逐个独立 mongodump 后拼接就能保证全局事务一致；协调快照/Atlas/Ops Manager 等支持方式具有部署和商业前置条件。

**验收：** Shard/Config Metadata/Balancer/跨分片事务在恢复后保持同一合法全局视图。

**核验合同与来源：** [backup-R07](#backup-R07)；本条对应的失败输入见下文验证矩阵。

### §41 DynamoDB PITR Window 与新表恢复
**机制：** DynamoDB PITR 的受支持恢复时间窗口为1–35天，时间精度秒，具体 API 与 Table/LSI/GSI、Stream/权限及新目标表语义不同；不开启或尚无历史时不能声称可恢复到任意更早时间。

**验收：** 检查 EarliestRestorableDateTime、LatestRestorableDateTime 及新表相关依赖，评估费用。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

### §42 Spanner 版本保留与最早恢复时间
**机制：** Spanner PITR 默认版本保留1小时、最多7天，延长保留不回溯填充已经过期的旧版本；earliest_version_time 是当前能恢复的下界，变化需按服务 API 核对。

**验收：** 请求早于 earliest_version_time 时明确拒绝并给出真实可选恢复范围。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

### §43 对象附件及外部服务一致恢复
**机制：** 数据库行引用对象存储文件、外部账本或消息 Broker 时，应确保所有关联版本、密钥与业务权利在恢复点上合法；只恢复关系库可能产生孤儿文件或付款状态错配。

**验收：** 跨系统稳定业务键及版本检查覆盖已交付、未知和待补偿记录。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

### §44 隔离恢复环境、权限与网络出口
**机制：** 恢复演练不应覆盖唯一原库或连接真实外部支付、邮件等有副作用接口，应使用批准的隔离目标/网络和最小权限；恢复测试环境中的机密记录仍遵守数据使用权。

**验收：** 恢复操作无法外发敏感数据或误执行真实客户资金，原库状态保持不变。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

### §45 业务级校验、对账与恢复准入
**机制：** 恢复后不只核对表行数/Checksum，还要验证主外键、租户隔离、已确认事务、授权、历史变更、索引及外部业务操作键；恢复正确与允许重新接流量是不同门禁。 从旧备份恢复会重现后来已撤权/删除的数据；对外发布前重放有效删除/保留例外及权限变更账本，核对传播截止和法律保全冲突，恢复成功不自动恢复历史访问权。

**验收：** 为每个核心业务测试提供失败/成功原始对照和人工/自动恢复准入责任。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

### §46 恢复切流、客户端重试及旧主 Fencing
**机制：** 重启新数据库/切流时旧节点、缓存、连接池、读副本和重试可能指向旧 Timeline/备份版本，必须保证唯一写入权、幂等请求和正确的客户端连接更新。

**验收：** 故障与恢复后没有双主写入、重复付款和未经授权读历史数据。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

### §47 可重放 Runbook、演练频率和 L6 证据
**机制：** 备份计划、Manifest、日志连续性、解密权限、Restore Steps、校验脚本、RPO/RTO 测量、失败处理、收费成本与合法数据保留证据按版本固化；静态审查/CI 不等于真实恢复演练。

**验收：** 每次受权演练保存环境、目标时间、实际数据、日志、耗时与客户业务结论，未测试等级明确留空。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

### §48 恢复演练证据等级与最终业务确认
**机制：** 区分文件存在、完整性验证、可启动隔离库、跨区域故障注入与客户实际业务恢复的各级证据；未执行的类别不得根据绿色指标推断通过，需独立保留批准时点和恢复事实。

**验收：** 只对真实已执行的故障等级、用户权限、交易核查和客户业务结果声明相应验收结论。

**核验合同与来源：** [backup-R08](#backup-R08)；本条对应的失败输入见下文验证矩阵。

## 四、60 项静态失效场景与 L6 预期检查

### 场景组 1：数据资产与恢复承诺
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 只备份订单表，不备份授权键和附件，恢复后订单无法打开 | §01 | 恢复资产清单含全部必要对象 |
| 可用性探针健康便宣布达成误删事故的 RPO/RTO | §02 | 故障级别、实际恢复时间和缺失键分别测量 |
| 副本立即复制了错误删除，却被当作 PITR 历史备份 | §03 | 能够恢复删除前版本或明确不可恢复 |
| 数据库表恢复成功，但第三方支付已执行而本地交易缺失 | §04 | 稳定交易操作键跨系统对账 |
| 数据页齐全但丢失扩展/证书/角色，恢复环境不可用 | §05 | 业务依赖和恢复凭据完整 |
| 跨两分片不同时间点拼装表文件，客户余额不一致 | §06 | 跨对象一致点有明确证明 |

### 场景组 2：备份链与数据权利
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 增量备份成功后删除仍被依赖的全量基线 | §07 | 完整备份依赖链可计算 |
| 把另一个集群同名 WAL/Manifest 纳入当前备份 | §08 | System ID 与 Backup Chain 身份一致 |
| 用 JST 本地时间表示 PITR 边界，但恢复进程按 UTC 排除交易 | §09 | 恢复目标时区和边界包含性准确 |
| 直接比较 MySQL GTID 与 PostgreSQL LSN 判定全局同一时间 | §10 | 跨系统合法业务水位独立定义 |
| 生产应用账号可以删除或覆盖所有历史备份 | §11 | 备份写入、删除与恢复最小权分离 |
| 数据库和备份都放同一区域同一卷而宣称区域故障可恢复 | §12 | 独立故障域与驻留权利可证明 |

### 场景组 3：调度、成本和 PostgreSQL 基线
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 密钥轮换后删除唯一解密旧备份的密钥版本 | §13 | 隔离角色实际解密成功 |
| 永久保存已合法删除的私人数据在所有恢复集里且无治理 | §14 | 法律保留和删除重放规则清晰 |
| 按时间清掉增量备份的祖先，最近备份无法恢复 | §15 | 依赖 DAG 下的清理门禁有效 |
| 仅测压缩备份大小便宣称整库恢复 5 分钟 | §16 | 传输、解密、合并、重放和校验总时间实测 |
| 两次备份互相覆盖同名目标文件导致恢复链断裂 | §17 | 调度及路径身份隔离 |
| 大型 mongodump 淘汰业务热数据缓存造成线上查询激增超时 | §18 | 备份与业务资源共验 |

### 场景组 4：PostgreSQL WAL/PITR 和 MySQL
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 归档任务调度正常但实际连续三天失败，监控仍绿色 | §19 | 远端真正存储和可恢复水位验证 |
| 只保存 pg_dump.sql 就宣布可重放 PostgreSQL 物理 WAL 做 PITR | §20 | 区分逻辑导出与物理基线 |
| pg_basebackup 遗漏外部 Tablespace，恢复后丢失核心表 | §21 | 基线与关联表空间完整 |
| archive_command 未正确持久却返回零，原 PG WAL 被回收 | §22 | 真实 WAL 归档闭环校验 |
| pg_verifybackup 成功，真实 PostgreSQL 实例启动后业务索引损坏 | §23 | 文件校验和实际恢复测试分离 |
| pg_combinebackup 需要的老增量链已被生命周期任务删除 | §24 | 所需全量/增量和 WAL 连续保持 |

### 场景组 5：MySQL、SQLite 与备份一致性
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| recovery_target_inclusive 选择错误，恢复时点上的退款被多执行 | §25 | 目标时刻前/后/等于边界事务正确 |
| PG 数据文件恢复成功但 pg_hba.conf/证书丢失导致业务全断 | §26 | 服务器配置与恢复权限完整 |
| MySQL --single-transaction 包含 MyISAM 表仍被当作一致快照 | §27 | 非事务表和并行 DDL 另设前置 |
| Binlog 关闭期间生成的交易仍被当作可进行任意 PITR | §28 | 可用连续 Binlog 覆盖目标窗口 |
| mysqlbinlog 重放已提交事务两次，恢复时向外部账户重复付款 | §29 | Replay 幂等/隔离对账 |
| 免费版本运行未安装的付费物理备份接口而声称已备份 | §30 | 真实许可、工具与备份结果匹配 |

### 场景组 6：SQL Server 日志恢复与 MongoDB
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 从库落后 GTID 仍用源库最新日志起点，漏掉 Replica 基线缺口 | §31 | 副本快照水位和日志链完整 |
| SQLite 主库写入期间裸复制主 .db 文件，事务分两半 | §32 | 采用受支持 Online Backup API |
| WAL 中有已确认订单，只拷贝 SQLite .db 导致最近数据丢失 | §33 | 活跃 WAL 文件/备份 API 一致 |
| VACUUM INTO 产物尚未持久就删掉原始数据库 | §34 | 目标文件可启动并包含正确事务 |
| SQL Server Simple Recovery Model 被当作能够恢复到任意交易秒 | §35 | Recovery Model 的 PITR 能力按实际验证 |
| 把差异备份应用到错误 Full Base，恢复失败 | §36 | 备份基线与 LSN 依赖正确 |

### 场景组 7：托管 PITR 与跨系统数据恢复
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| SQL Server 过早 RESTORE WITH RECOVERY，后续 Log 无法按当前链应用 | §37 | 完整日志和 Tail Log 按顺序应用 |
| RESTORE VERIFYONLY 成功却客户主外键/登陆权限损坏 | §38 | 隔离恢复和领域断言通过 |
| MongoDB Replica Set 活跃写入做 mongodump 未启用 --oplog | §39 | 实际一致快照与 Oplog Replay |
| MongoDB 分片各节点不同时间备份，跨片转账缺一边 | §40 | 协调跨 Shard 原子快照 |
| DynamoDB PITR 未启用却请求 30 天前恢复 | §41 | Earliest/Latest 可用时间与服务配置核对 |
| Spanner 扩保留到 7 天后立即尝试恢复 6 天前数据 | §42 | earliest_version_time 有实际旧版本支持 |

### 场景组 8：安全恢复、切流和审计证据
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 关系库恢复后对象附件新版本丢失导致已交付合同文件打不开 | §43 | 跨存储文件与业务键版本核对 |
| 恢复测试连真实支付接口，重放订单造成额外扣款 | §44 | 网络出口及生产资金动作隔离 |
| 恢复行数一致但租户数据混用、已撤销权限恢复为允许 | §45 | 租户/角色/核心业务不变量独立验证 |
| 新恢复主库上线后旧 Primary 仍能写入导致两份权威账本 | §46 | 客户端切流与旧主撤权门禁 |
| 恢复测试报告不保存版本/日志和真实异常记录，无法复盘 | §47 | 运行手册和原始证据齐备 |
| 只做备份文件静态验签就宣布完成生产区域级灾难演练 | §48 | 仅按真实演练的故障等级报告成功 |

### 场景组 9：跨技术的备份链失效
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| PG 增量和 SQL Server 差异备份误互换，删除两者所需基线 | §07、§24、§36 | 产品依赖链逐项保持完整 |
| PostgreSQL PITR 与 MySQL Binlog 的时间戳不一致造成退款再执行 | §09、§25、§28、§29 | 跨产品业务操作键校验最终状态 |
| SQLite 在线写入与 MongoDB 分片快照未经协调就拼出一个账本 | §06、§32、§33、§40 | 存储间一致点独立证明 |
| 备份加密钥匙和 DynamoDB PITR 恢复角色均已被删除 | §11、§13、§41 | 密钥、权限及服务恢复能力共同检查 |
| Spanner 保留时间和 SQL Server Tail Log 混同，用户被承诺同一 RPO | §02、§37、§42 | 实际服务恢复窗口分别核算 |
| SQL Server Bulk-Logged 日志中段试图停止至任意秒，恢复过多交易 | §09、§35、§37 | 恢复模型和 Point-in-Time 能力核实 |

### 场景组 10：组合故障和客户恢复结果
| 失败输入 | 关联机制 | L6 预期检查 |
| --- | --- | --- |
| 误删扩展后使用备份恢复但 Pg HBA、对象存储附件与外部账本不匹配 | §05、§26、§43 | 必要依赖与已完成交易范围对齐 |
| 将备份和所有日志放同云账号后被同一勒索事件删除 | §11、§12、§15 | 多故障域备份保留和恢复授权 |
| 恢复期间执行用户支付回调，客户端重试与旧主继续接单 | §04、§29、§44、§46 | 支付、Fencing 和幂等同时成立 |
| 旧敏感数据从历史归档恢复后直接向新租户公开 | §01、§14、§44、§45 | 历史恢复与现行数据权利一致 |
| 为缩短恢复时间丢弃必要 WAL/增量基线，导致可恢复窗口变短 | §07、§15、§16、§22、§24 | 容量优化不降低已批准恢复承诺 |
| 演练只验文件 CRC、实际业务核心订单状态与已收款不一致 | §08、§23、§38、§45、§48 | 校验、可启动及客户业务结果分级验收 |

## 五、版本、审批与实际恢复验收

1. 本版包含 **48 项独立技术机制、60 项静态失效场景**，10 组失败输入覆盖 §01—§48，来源需按实际版本、适用条件和证据范围复核。L5/L6 真实备份、PITR 恢复、生产权限与客户业务验收仍须独立执行。
静态文档、CI、备份文件校验、数据库实际启动、业务正确性和生产灾难恢复演练属于不同证据等级，不能互相替代。
4. 具体备份部署脚本和版本归 L5，项目数据库/外部系统的权利及最终业务恢复归 L6；安全、元数据及流批专题分别独立审核，本版不自行修改它们。

## 核验合同附录

各合同按条款范围列出输入、判据、合法邻例与恢复要求。来源版本及支持命题见[数据库来源表](../../../sources/database-sources.json)。

<a id="backup-R01"></a>

### backup-R01

**条款范围：** §01、§02、§03、§04、§05、§06

**目标工具/输入：** 恢复Manifest：引擎/工具/基线/日志/密钥/账号/对象附件/目标点。副本当备份、只备数据漏配置/keys、多系统时点不一致

**判据：** 可启动、可解密、数据完整及客户结果为独立条件，scope明确

**合法邻例：** 单机离线备份可满足实际RPO，无需求不强制多区域收费服务

**恢复：** 保护原件并从依赖闭包隔离恢复，外部权威资金/消息独立对账

**来源：** [PG-B](https://www.postgresql.org/docs/18/continuous-archiving.html)、[SQ-B](https://www.sqlite.org/backup.html)、[NI-K](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf)。关系：implementation-and-organisation-synthesis

<a id="backup-R02"></a>

### backup-R02

**条款范围：** §07、§08、§09、§10

**目标工具/输入：** Full/增量/差异/日志DAG；恢复目标时区/inclusive/timeline。缺早期基线、断WAL、跨时间线、目标边界交易包含性错

**判据：** 每个保留点有完整合法链和精确边界；链校验不同于内容校验

**合法邻例：** 仅支持全量恢复的小工具可不提供PITR，但不能宣称任意时间可恢复

**恢复：** 选择最近满足目标的完整合法链；缺点明确报不可恢复不自动移到最新

**来源：** [PG-B](https://www.postgresql.org/docs/18/continuous-archiving.html)、[PG-CB](https://www.postgresql.org/docs/18/app-pgcombinebackup.html)、[AW-B](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html)、[GO-B](https://docs.cloud.google.com/spanner/docs/pitr)。关系：implementation-and-organisation-synthesis

<a id="backup-R03"></a>

### backup-R03

**条款范围：** §11、§12、§13、§14、§15、§16、§17、§18、§19

**目标工具/输入：** 密钥版本/恢复账号、地域、保留锁、容量/归档lag清单。保留法律例外冲突、删key断恢复、清前置增量、预算不足

**判据：** 所有仍承诺恢复点的依赖闭包受保护，保留与删除例外可审查

**合法邻例：** 法律保全中的旧备份暂保留可合法，不能为追求清理率删除

**恢复：** 按保留根重新计算闭包，隔离不合法公开路径并保留合法恢复材料

**来源：** [NI-K](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf)、[S3-L](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)、[GC-L](https://docs.cloud.google.com/storage/docs/bucket-lock)、[PG-B](https://www.postgresql.org/docs/18/continuous-archiving.html)。关系：implementation-and-organisation-synthesis

<a id="backup-R04"></a>

### backup-R04

**条款范围：** §20、§21、§22、§23、§24、§25、§26

**目标工具/输入：** pg_basebackup/pg_verifybackup/pg_combinebackup；recovery_target与config。pg_dump当物理PITR、verify绿但库不可启动、漏tablespace/外部配置

**判据：** PG18链/manifest/system ID/WAL/timeline配置与实际隔离恢复数据分别核验

**合法邻例：** 纯逻辑对象恢复可合法不用PITR；verify输出并非无用只是不充分

**恢复：** 先合成全部依赖并核完整，按目标timeline恢复至隔离库再查询业务键

**来源：** [PG-B](https://www.postgresql.org/docs/18/continuous-archiving.html)、[PG-VB](https://www.postgresql.org/docs/18/app-pgverifybackup.html)、[PG-CB](https://www.postgresql.org/docs/18/app-pgcombinebackup.html)。关系：implementation-and-organisation-synthesis

<a id="backup-R05"></a>

### backup-R05

**条款范围：** §27、§28、§29、§30、§31

**目标工具/输入：** mysqldump --single-transaction；binlog起止位置/GTID；mysqlbinlog实际版本。非事务表假一致、DDL并发、缺binlog段、回放重复付款

**判据：** 一致逻辑快照依storage engine；完整备份位置与binlog链及幂等关联

**合法邻例：** 不包含非事务表/并发DDL的隔离InnoDB快照可合法简化

**恢复：** 从明确基线重放合法区间，读权威业务键和重复操作账本确认

**来源：** [MY-B](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html)、[MY-W](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html)、[MY-HA](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html)。关系：implementation-and-organisation-synthesis

<a id="backup-R06"></a>

### backup-R06

**条款范围：** §32、§33、§34

**目标工具/输入：** Connection.backup/restore；VACUUM INTO实际版本；integrity_check。只copy db漏WAL、目标存在/不完整、文件存在误当设备持久

**判据：** 恢复包含预期已提交行、原库无破坏、输出完整性检查独立

**合法邻例：** 无账号单机备份及一致关闭连接后受支持拷贝是合法邻例

**恢复：** 以Backup API重建隔离副本并核对键值，未测掉电仍保留not-run

**来源：** [SQ-B](https://www.sqlite.org/backup.html)、[SQ-W](https://www.sqlite.org/wal.html)、[SQ-P](https://www.sqlite.org/pragma.html#pragma_synchronous)。关系：implementation-and-organisation-synthesis

<a id="backup-R07"></a>

### backup-R07

**条款范围：** §35、§36、§37、§38、§39、§40

**目标工具/输入：** SQL Server backup/restore header/verify/full-diff-log；Mongo版本/拓扑与oplog。恢复模型不支持目标点、差异基线错、过早RECOVERY、shard非同时快照

**判据：** 真实工具目标版本/拓扑、链和支持的恢复范围全部匹配

**合法邻例：** 无PITR承诺的合法Simple恢复模型和离线一致快照可接受

**恢复：** 保留尾日志与一致基线，按实际拓扑恢复；verify不替代启动/业务查询

**来源：** [SS-B](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/apply-transaction-log-backups-sql-server?view=sql-server-ver15)、[SS-W](https://learn.microsoft.com/en-us/sql/relational-databases/logs/control-transaction-durability?view=sql-server-ver16)、[MO-B](https://www.mongodb.com/docs/v8.0/administration/backup-sharded-clusters/)、[MO-R](https://www.mongodb.com/docs/v8.0/reference/read-concern-majority/)。关系：implementation-and-organisation-synthesis

<a id="backup-R08"></a>

### backup-R08

**条款范围：** §41、§42、§43、§44、§45、§46、§47、§48

**目标工具/输入：** DescribeContinuousBackups/earliest_version_time；隔离恢复与删除覆盖账本。扩大retention假补过去、旧备份复活已删除数据、恢复连真实外部副作用

**判据：** 托管可恢复窗以实际API为准；发布前套当前权限/删除/保全政策

**合法邻例：** 本地单库、无账号公开数据无须开云服务，依法保留例外明确不误拒

**恢复：** 恢复到独立目标，阻断外部动作、重放当前删除/权限覆盖并对账后准入

**来源：** [AW-B](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html)、[GO-B](https://docs.cloud.google.com/spanner/docs/pitr)、[EU-R](https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en)、[NI-K](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf)。关系：implementation-and-organisation-synthesis
