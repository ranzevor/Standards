# L4 云基础设施与 DevOps 领域通用基线

**文档ID：** STD-L4-CLOUD-003　**版本：** 0.1.0　**状态：** adopted　**生效日期：** 2026-10-30

## 一、目标、适用与非目标

**目标：** 使运行环境、交付链、恢复和费用的共同断言可追溯到真实资源及客户结果。

**适用：** 凡采用服务器、VM、容器、云/边缘、CI、IaC或远程发布的项目；按实际采用组件激活机制。

**非目标：** 不强制多云/Kubernetes/商业产品，不接管应用协议、数据库事务、客户合同或付款权。

本 L4 领域通用基线适用于实际采用自建服务器、虚拟机、容器、边缘节点、Serverless、托管云、持续集成、基础设施声明或远程部署的项目。以真实业务权利、用户规模、环境风险、可维护性、成本与恢复要求选择技术；不强制单人项目采购多云、Kubernetes、Service Mesh、商业安全或 FinOps 产品。

L1—L3 管理组织授权、通用工程质量与协作；相应 L4 后端、数据库与 Web 专题保留其应用协议、数据合法性、业务状态、缓存、事务和客户结果的职责。本基线只界定运行环境、云资源、身份、构建链、基础设施状态、发布、恢复与费用的共同工程条件。网络协议、安全工程、自动化和具体云产品由相应 L4 专题及 L5 具体化；L6 由实际项目有权主体确认生产环境、收费和真实业务验收。

### 用语、强度与权威状态

环境身份=账户/项目不可变ID+地域+Principal+数据集；制品身份=实际字节Digest+平台；完成=明确层次的目标事实。

OPC指单人组织/单人公司画像；真实有权自然人可兼任多个职责，不因此虚构额外审批者或由工具角色取代业务授权。

“必须/不得”为本规范适用条件成立时的强制要求；“应/优先”为需给出可复核理由方可偏离的建议；“可”为许可选项。原有机制句及其验收为规范性合同，直接失败与合法邻例约束解释范围。外部来源的MUST/SHOULD保留其原强度，本规范自行加强的门禁不得倒称外部原文要求。

**共同不变量：** 标签/期望配置不产生有效权限；受理、资源就绪、业务完成、费用结清是不同状态。

**状态词：** 未开始、已受理、执行中、成功、失败、取消请求、结果未知分别记录；Timeout/取消请求不自动证明目标未执行。输出至少绑定对象不可变ID/版本、实际主体、目标环境、操作ID、观察时点及所见范围，秘密值不进入共享证据。

**兼容原则：** IAM、NET、ISO、IAC、CI、SUP、SEC、REL、CAP、OBS、DR、COST分别按实际独立失效机制实施；小型单进程项目可合并实现但不可删除相同适用义务。

## 二、官方来源、准确身份与有限命题

下表将官方章节支持的技术命题绑定到对应合同；工程要求以各条机制、适用条件与验收为准。动态页面按所示访问日期定位，L5 须记录实际工具、服务版本及功能条件；版本变化时重新核对受影响命题。

| 命题 ID / 官方来源与身份 | 已读章节 / 有限支持命题 | 不支持的推论 |
| --- | --- | --- |
| CAP-CLOUDRUN：[来源](https://docs.cloud.google.com/run/docs/configuring/max-instances)；Cloud Run maximum instances; rolling page observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | Service/revision max; exceeding max; tags；流量突发时实例数可能短时超过配置Max；Service/Revision级与Tagged Revision计数条件不同。 | 不是绝对DB连接/费用硬上限，需要并发接纳与在途余量。 |
| CAP-LAMBDA：[来源](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)；AWS Lambda concurrency; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Reserved concurrency; provisioned concurrency；Reserved保留并限制并发但不预初始化；Provisioned预初始化且另计费，准备/Reset仍可出现冷路径，溢出依Reserved等配置。 | 并发不是RPS，不可因配置预置而保证零冷启动或零费用超支。 |
| CI-GITLAB：[来源](https://docs.gitlab.com/runner/security/)；GitLab Runner security; rolling page observed 2026-10-23；发布者：GitLab；性质：vendor product documentation | Shell executor; privileged containers; cached images; shared environments；Shell/Privileged与非临时Runner扩大宿主及跨Job污染；if-not-present可复用未授权用户缓存私有镜像，fetch可继承共享工作区污染。 | 不从Executor名字证明安全隔离；当前凭据Helper默认策略不代表历史Runner或宿主配置同样安全。 |
| CI-NIST204D：[来源](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204D.pdf)；NIST SP800-204D final February2024；发布者：NIST；性质：published final guidance; not automatic universal legal mandate | §5/5.1; AppendixA；CI/CD Driver比被执行的Build Steps拥有更高信任和控制权，构建链需按实际信任分区集成安全实践。 | 指南不是全项目法律强制或使用任一工具即达成供应链等级的证明。 |
| CI-RESOURCEGROUP：[来源](https://docs.gitlab.com/ci/resource_groups/)；GitLab CI resource groups; rolling page observed 2026-10-23；发布者：GitLab；性质：vendor product documentation | Process modes；提供unordered/oldest_first/newest_first/newest_ready_first等调度模式，更新优先模式要求Job适合幂等执行。 | 只串行指定资源组，不代替云State锁、目标栅栏或外部业务事务。 |
| COST-ALERT：[来源](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets)；Azure Cost Management budgets; rolling page observed 2026-10-23；发布者：Microsoft；性质：vendor product implementation documentation | Introduction; cost-data delays; action groups；预算阈值通知本身不影响资源或停止消耗；费用通常延迟8–24小时且按日求值，Action Group需另配并验证。 | 不能把邮件收到当硬额度已执行；具体账单币种/Scope及自动动作权限各自限定。 |
| COST-AWS-ACTION：[来源](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)；AWS Budgets actions; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Action types; automatic/manual; account restrictions；预算可自动或人工批准IAM/SCP或特定EC2/RDS动作；跨账号目标存在具体限制。 | 通知/Action接受不保证所有资源停费，在途、固定合同和其他SKU仍需算入。 |
| COST-AZ-LOCK：[来源](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/lock-resources)；Azure Resource Manager locks; rolling page observed 2026-10-23；发布者：Microsoft；性质：vendor product implementation documentation | Control plane/data plane; ReadOnly; CanNotDelete; considerations；Lock作用控制面而非数据面；ReadOnly可阻某些POST/ListKeys/角色动作，CanNotDelete可影响备份/Autoscale；不阻订阅取消。 | 不是所有数据删除保护或不可移除WORM，解除Lock不产生销毁权。 |
| COST-CAP：[来源](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps)；Google Cloud Budgets Spend caps; rolling page observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | Eligibility; limitations; permissions; enforced/lifted states；当前Cap限单Project单支持服务的月度第一方费用；仅列举支持服务，执行非即时且超额仍可计费，成本估算依据依服务不同。 | 不是全账号/所有SKU/固定承诺硬停费，更不能把Configured当Enforced；执行权限需另核。 |
| COST-CUR：[来源](https://docs.aws.amazon.com/cur/latest/userguide/Lineitem-columns.html)；AWS CUR line-item columns; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | ResourceId; NetUnblendedCost; UsageStartDate/EndDate；ResourceId可选且部分费用为空；Net字段有条件出现，Usage区间按UTC开始含/结束不含，部分费用用量0。 | 缺ResourceID或Usage0不等免费，CUR字段也不自动等同FOCUS同名口径。 |
| COST-DELETE：[来源](https://docs.cloud.google.com/resource-manager/docs/delete-restore-projects)；Google Cloud project delete/restore; rolling page observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | Effects of shutting down; restore; billing；项目一般30天恢复窗但部分资源更早永久删除，恢复耗时/账单重新关联另有条件；费用可能滞后且长期承诺责任仍在。 | 不能声称30天内所有服务完整可恢复、删除即零账单或Project ID可复用。 |
| COST-DORA：[来源](https://dora.dev/guides/dora-metrics/)；DORA metrics guide; updated2026-01-05；发布者：DORA；性质：research/practice metric guidance | Software delivery performance metrics; interpretation；当前五指标含Change lead time、Deployment frequency、Failed deployment recovery time、Change fail rate、Deployment rework rate，需服务上下文与共同质量解释。 | 不是强制所有项目高频生产部署的配额，不以CI重跑次数充发布量或以单指标排名。 |
| COST-FOCUS：[来源](https://focus.finops.org/docs/specification/v1-4/datasets/cost-and-usage/)；FOCUS v1.4 Cost and Usage dataset；发布者：FinOps Foundation FOCUS project；性质：versioned cost-and-usage data specification | §3.1; column requirement table；字段区分Mandatory/Conditional/Recommended，ResourceID等依条件，费用/覆盖关系需使用同一所选Schema。 | 并非每账单行都有ResourceID，合Schema不证明账单完整或全部供应商已支持1.4。 |
| GH-CONCURRENCY：[来源](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)；GitHub Actions concurrency; rolling page observed 2026-10-23；发布者：GitHub；性质：vendor product documentation | Concurrency behavior; queue:max; ordering；默认一运行一等待且新等待替换旧等待；queue:max可排至100个等待且不能与cancel-in-progress:true组合；分组不区分大小写，FIFO按开始等待而非派发顺序。 | 不是数据库事务锁，也不保证所有工作流全局顺序、取消已回滚或跨仓库互斥。 |
| GH-OIDC：[来源](https://docs.github.com/en/actions/reference/security/oidc)；GitHub Actions OIDC; rolling page observed 2026-10-23；发布者：GitHub；性质：vendor product documentation | Understanding OIDC claims; audience; immutable subject identifiers；Issuer、Audience、Subject及工作流上下文须与目标Trust匹配；Audience默认值可定制，不可变ID格式并非所有GHES均支持。 | id-token权限仅允许请求OIDC Token，不自动授予云写权；其他发行者不必具有GitHub字段。 |
| GH-SECURE：[来源](https://docs.github.com/en/actions/reference/security/secure-use)；GitHub Actions secure use; rolling page observed 2026-10-23；发布者：GitHub；性质：vendor product documentation | Hardening self-hosted runners; JIT runners；自托管Runner即使私有仓库也可能被不可信工作流持久污染；环境批准不隔离宿主，单作业JIT不等于底层硬件清洁。 | 不由私有仓库、PR作者或一次清理脚本证明可安全暴露生产Secret。 |
| IAC-CFN-CHANGE：[来源](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html)；AWS CloudFormation change sets; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Executing change sets；Change Set生成不更新实际Stack，须执行并验证；执行会使该Stack其他Change Sets失效。 | 预览不证明运行时配额、Custom Resource或实际业务恢复。 |
| IAC-CFN-DRIFT：[来源](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-drift.html)；AWS CloudFormation drift detection; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Considerations; supported properties/resources; nested stacks；只比较受支持资源及显式属性，不自动检查Nested Stack；没有受支持资源也可能IN_SYNC，未检查项保持NOT_CHECKED。 | IN_SYNC不证明所有云资源/密钥/运行配置无漂移。 |
| IAC-CFN-FAIL：[来源](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stack-failure-options.html)；AWS CloudFormation preserve successful resources; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Preserve successfully provisioned resources; conditions；可选保留成功对象时独立路径继续，失败可留下混合结果；恢复受Stack状态/最后稳定状态及不可变更新限制。 | 失败不总是全量回滚，也不承诺持久业务数据恢复。 |
| IAC-PULUMI：[来源](https://www.pulumi.com/docs/iac/cli/commands/pulumi_refresh/)；Pulumi CLI generated docs v3.272.0；发布者：Pulumi；性质：generated versioned CLI documentation | refresh description; --preview-only; --expect-no-changes；refresh将真实资源状态采纳进Stack而不修改程序；--preview-only只预览；--expect-no-changes在Refresh应用后再检查有无变化。 | Refresh不是只读巡检的同义词，也不自动协调代码与实况；不同版本要核支持参数。 |
| IAC-TF-LOCK：[来源](https://developer.hashicorp.com/terraform/language/state/locking)；Terraform docs v1.17.x navigation; rolling page observed 2026-10-23；发布者：HashiCorp；性质：vendor tool implementation documentation | State Locking; Force Unlock；锁能力依Backend；自动加锁失败时不继续，-lock=false危险，强解仅用于自己未成功自动释放的锁。 | 没有内建通用活跃持有者/业务权限证明，且State锁不阻止云控制台或其他State写同对象。 |
| IAC-TF-PLAN：[来源](https://developer.hashicorp.com/terraform/cli/commands/plan)；Terraform CLI plan; v1.17.x navigation observed 2026-10-23；发布者：HashiCorp；性质：vendor tool implementation documentation | -out; -lock-timeout; saved plan contents；Saved Plan包含完整配置、计划值、选项及输入变量，敏感值可能明文存在；锁等待与退出需按真实Backend处理。 | UI隐藏不加密Plan，Plan成功不承诺Apply成功、云权限不变或对象未被外部修改。 |
| IAC-TOFU-BACKEND：[来源](https://opentofu.org/docs/language/state/backends/)；OpenTofu rolling docs; banner1.13.0 observed2026-10-23；发布者：OpenTofu project；性质：versioned/rolling tool implementation documentation | State Storage; Manual State Pull/Push；非本地Backend写State不可恢复失败时可落本地防丢；pull输出敏感State，push检查Lineage/较高Serial但-force可绕过，需事前备份。 | 不是后端永不丢失或强推自动安全；本地异常State与目标云局部效果须共同核对。 |
| IAC-TOFU-LOCK：[来源](https://opentofu.org/docs/language/state/locking/)；OpenTofu State Locking; rolling page observed 2026-10-23；发布者：OpenTofu project；性质：versioned/rolling tool implementation documentation | State locking; Force Unlock；支持锁的Backend对可能写State的操作加锁；失败不继续；force-unlock唯一ID针对该锁，错误解锁可能双写。 | 不是所有Backend支持锁；锁ID不是旧进程已停止或解锁者有业务授权的证明。 |
| IAM-AWS-EVAL：[来源](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html)；AWS IAM User Guide; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Determining whether a request is allowed or denied; resource-based policies; role session principals；显式拒绝优先；同账号直接授予Role Session与授予Role ARN对隐式Boundary/Session限制有不同结果，跨账号、KMS与Trust另有条件。 | 不是所有供应商/所有Principal都能化简成同一个集合交集；模拟器不能证明真实服务调用已允许。 |
| IAM-AWS-SCP：[来源](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)；AWS Organizations SCP; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | SCP effects on permissions; tasks/entities not restricted；SCP限制成员账号可用权限但不授予权限；不约束管理账号及部分服务关联角色；外部Principal不因资源所属账号SCP而自动受限。 | 组织层标签、SCP存在或Owner名称均不自证实际访问；RCP与资源策略另核。 |
| IAM-AZ-DENY：[来源](https://learn.microsoft.com/en-us/azure/role-based-access-control/deny-assignments)；Azure RBAC deny assignments; rolling page observed 2026-10-23；发布者：Microsoft；性质：vendor product implementation documentation | How deny assignments are created; properties; permissions；Deny Assignment由Azure创建管理，含Scope、子范围继承和例外；读取需denyAssignments/read。 | 不能建议用户直接创建普通自定义Deny Assignment；列表无结果也需确认读取权限和作用域。 |
| IAM-AZ-IDENTITY：[来源](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)；Microsoft Entra managed identities; rolling page observed 2026-10-23；发布者：Microsoft；性质：vendor product implementation documentation | Types of managed identities；System-assigned随父资源生命周期；User-assigned为独立可共享身份，删除父资源不自动删除它。 | 生命周期规则不证明已签发Token即时失效或业务权限自动最小化。 |
| IAM-AZ-ROLE：[来源](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions)；Azure RBAC role definitions; page updated 2025-03-30；发布者：Microsoft；性质：vendor product implementation documentation | Actions; NotActions; DataActions; NotDataActions；NotActions是从该角色Allow中减去而非显式Deny，其他角色仍可允许；控制面与数据面动作分开。 | 控制面Reader/Owner不等同业务数据权；可取账户Key的控制面权限可能另开数据访问路径。 |
| IAM-GCP-DENY：[来源](https://docs.cloud.google.com/iam/docs/deny-overview)；Google Cloud IAM Deny; rolling page observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | Denial conditions; inheritance; supported permissions；Deny条件为真或不能求值时拒绝，条件为假仍需有效Allow；只覆盖支持的权限且变更有传播时间。 | 不能将自定义任意权限都写入Deny，不能从控制面写入回执推断各入口即时生效。 |
| IAM-GCP-WIF：[来源](https://docs.cloud.google.com/iam/docs/best-practices-for-using-workload-identity-federation)；Google Cloud WIF best practices; rolling page observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | Use immutable attributes; avoid subject collisions; audiences; protect mappings；共享Issuer仍须限制可信主体；可变/复用属性与映射碰撞会混淆主体，Audience和映射管理权限需独立保护。 | 外部Token签名有效不产生目标资源权限，也不证明任意云都识别GitHub同名Claim。 |
| ISO-ROOTLESS：[来源](https://docs.docker.com/engine/security/rootless/)；Docker Engine rootless; rolling docs observed 2026-10-23；发布者：Docker；性质：vendor tool implementation documentation | How it works; prerequisites；Rootless让Daemon与容器在非root用户的User Namespace中运行，需uidmap与适当subuid/subgid。 | 不是所有宿主威胁的证明，不能将仅userns-remap冒称Daemon也非root。 |
| ISO-USERNS：[来源](https://docs.docker.com/engine/security/userns-remap/)；Docker userns-remap; rolling docs observed 2026-10-23；发布者：Docker；性质：vendor tool implementation documentation | Remapping; limitations；Remap时Daemon仍为root，容器ID映射宿主高UID；Bind Mount权限需预安排，共享Host PID/NET等有不兼容条件。 | 映射不自动隔离宿主Socket、设备或所有共享Namespace。 |
| ISO-WINDOWS：[来源](https://learn.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/container-security)；Windows containers security; 2025-01-23; Server2016–2025；发布者：Microsoft；性质：vendor product implementation documentation | Process isolation; Hyper-V isolation；进程隔离共享宿主Kernel，不被微软视为强敌对多租户边界；Hyper-V提供不同的隔离边界。 | 不从这一供应商文档推论所有Hypervisor绝对安全，Linux能力设置不直接适用于Windows。 |
| K8S-NETPOL：[来源](https://kubernetes.io/docs/concepts/services-networking/network-policies/)；Kubernetes rolling docs observed 2026-10-23；发布者：Kubernetes project；性质：rolling official implementation documentation | Network policy isolation; propagation; hostNetwork; existing connections；需实现策略的CNI；策略异步生效且API不指示精确数据面应用时点；hostNetwork、重写地址及已有连接行为有实现差异。 | YAML存在不证明隔离，不能许诺新Pod绝无传播空窗或全部旧连接立即关闭。 |
| K8S-RBAC：[来源](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)；Kubernetes RBAC; rolling page observed2026-10-23；发布者：Kubernetes project；性质：rolling official implementation documentation | RoleBinding/ClusterRoleBinding; role/binding escalation restrictions；RoleBinding可将ClusterRole限制到单Namespace，ClusterRoleBinding为全局；创建角色/绑定需已有所授权限或明确escalate/bind许可。 | Role名字不证明作用域或最小权限，RBAC不能单独证明应用客户对象授权。 |
| K8S-SECURITY：[来源](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)；Kubernetes security context; rolling docs observed 2026-10-23；发布者：Kubernetes project；性质：rolling official implementation documentation | allowPrivilegeEscalation; capabilities; Pod/container settings；allowPrivilegeEscalation对应no_new_privs控制；当前文档不允许false与privileged/CAP_SYS_ADMIN组合；Pod与Container字段/覆盖需区分。 | 不以提交SecurityContext代替真实进程UID、Mount、Seccomp、LSM与可达宿主资源验证。 |
| KERNEL-CGROUP：[来源](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)；Linux cgroup v2 kernel latest page observed 2026-10-23；发布者：Linux kernel project；性质：kernel implementation documentation; target version must be bound | Memory: memory.high; memory.max; hierarchy；memory.high触发节流/回收而非本身OOM且可越过；memory.max回收失败可OOM，也有短时越界/特殊分配路径，祖先限制同样有效。 | 不能把high当绝对内存硬墙，不能未经目标Kernel画像宣称所有版本同样行为。 |
| NET-AWS-NACL：[来源](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html)；AWS VPC network ACL; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Rules; statelessness; limitations；按规则号首匹配、入出方向独立且无状态；响应需相应允许，不过滤同子网全部流及若干平台特殊流。 | 不能将SG的状态语义移植到NACL。 |
| NET-AWS-SG：[来源](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)；AWS VPC security groups; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Statefulness; traffic not filtered；SG连接跟踪允许获准流的响应不受反向规则限制；部分平台特殊流量不被SG过滤。 | SG不是所有链路完整隔离证据；实际关联、路由和新旧连接均须测。 |
| NET-AWS-SG-RULES：[来源](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)；AWS SG rules; rolling page observed2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Security group rule basics；SG仅Allow无Deny；多SG规则聚合，新增组默认无入站而初始出站全允许，规则变更效果受连接跟踪影响。 | 无Deny不是默认所有流都允许，另有NACL/路由/平台特殊流量边界。 |
| NET-AZ-NSG：[来源](https://learn.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview)；Azure NSG; rolling page observed 2026-10-23；发布者：Microsoft；性质：vendor product implementation documentation | Security rules; existing connections; security admin rules；NSG有状态，更新规则影响新连接而旧连接可继续；先行安全管理规则的AlwaysAllow/Deny可终止后续求值。 | 规则保存不保证旧连接被撤断；平台保留流量另核。 |
| NET-GCP-FW：[来源](https://docs.cloud.google.com/firewall/docs/firewall-policies-rule-eval-order)；Google Cloud firewall policy evaluation; rolling page observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | BEFORE_CLASSIC_FIREWALL; AFTER_CLASSIC_FIREWALL; goto_next；层级/区域系统策略与网络/经典规则顺序受实际配置影响；goto_next继续到后层不是直接Allow，最终默认依流量类别不同。 | 不能只按一个数字Priority比较不同策略层，也不能把VM默认推广到所有代理。 |
| OBS-ALERTMANAGER：[来源](https://prometheus.io/docs/alerting/latest/alertmanager/)；Prometheus Alertmanager; rolling page observed 2026-10-23；发布者：Prometheus project；性质：upstream implementation/statistical guidance | Silences; inhibition; routing；Silence按匹配器/时间窗静默通知，Inhibition可按其他Alert抑制通知，路由与接收另有状态。 | 通知静默不等故障恢复或所有租户风险已消除。 |
| OBS-CLOUDWATCH：[来源](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html)；AWS CloudWatch missing data; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Treating missing data；missing、notBreaching、breaching、ignore有不同求值语义，稀疏错误指标与持续心跳需分别选。 | 不能把所有NoData一律Healthy或一律故障，也不由无Alarm证明完整业务健康。 |
| OBS-PROMRULE：[来源](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)；Prometheus alerting rules; rolling page observed 2026-10-23；发布者：Prometheus project；性质：upstream implementation/statistical guidance | Defining rules; for; keep_firing_for; inspecting alerts；for需连续求值满足才从Pending到Firing；keep_firing_for在条件最后满足后继续保持指定时长，通知由另一层处理。 | 告警状态不是实际接收/ACK或事故恢复，缺数策略必须显式。 |
| OBS-PROMTOOL：[来源](https://prometheus.io/docs/prometheus/latest/command-line/promtool/)；Prometheus promtool; rolling command manual observed2026-10-23；发布者：Prometheus project；性质：upstream implementation/statistical guidance | promtool check rules; syntax/lint flags；check rules检查规则文件，Lint与未知字段等选项会改变检查范围；未知字段被检查工具忽略并不表示服务端严格加载会接受。 | 规则静态检查不证明Alert已加载/持续触发、通知抵达或客户故障恢复。 |
| OCI-DESCRIPTOR：[来源](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md)；OCI Image Specification v1.1.1; blob1d53762d21377c21a0ffc845c3bc46842a1f0f17；发布者：Open Container Initiative；性质：versioned upstream specification/schema or tool reference; selected file identity retained | Descriptor digest; size; verification；Descriptor要求Digest/Size等字段；规范建议验证内容摘要，大小不符不应信任；重处理前先核内容。 | 本规范可将消费侧验证提升为必须，但不能冒称OCI原文所有SHOULD均为MUST。 |
| OCI-IMAGE：[来源](https://github.com/opencontainers/image-spec/blob/v1.1.1/manifest.md)；OCI Image Specification v1.1.1; blob16a601708c73786596166a3d74134982efac6af7；发布者：Open Container Initiative；性质：versioned upstream specification/schema or tool reference; selected file identity retained | Image manifest: config; layers; artifactType; subject；Manifest配置与Layer按Descriptor引用；未知artifactType不必阻止存储复制；subject只是到另一Manifest的弱关联。 | 格式可解析与subject引用不产生签名信任、构建来源或运行隔离保证。 |
| OCI-INDEX：[来源](https://github.com/opencontainers/image-spec/blob/v1.1.1/image-index.md)；OCI Image Index v1.1.1; blob94799418bbb551f13b4639a5cb5eb9f211a46757；发布者：Open Container Initiative；性质：versioned upstream specification/schema or tool reference; selected file identity retained | Index properties; manifests; platform; variants；Index可含零Manifest，platform整体可选而存在时os/architecture必需；特定平台应带最小运行要求，多匹配时建议首个，未知mediaType不应导致通用格式错误。 | 合法格式不保证含当前平台或实际ABI可运行，组织支持矩阵可更严格但应明确区别。 |
| OCI-RUNTIME：[来源](https://github.com/opencontainers/runtime-spec/blob/v1.3.0/config-linux.md)；OCI Runtime Specification v1.3.0; blobc71757494ca743fd90692c25e4897bf74cf00388；发布者：Open Container Initiative；性质：versioned upstream specification/schema or tool reference; selected file identity retained | Linux namespaces; cgroupsPath; seccomp；配置定义Namespace、cgroup路径与可选Seccomp；相对/绝对cgroup路径有不同解释，是否配置不是运行时已强制执行证据。 | 只支持已读Linux配置范围，镜像格式正确不证明Bundle、目标Kernel或跨OS兼容安全。 |
| OTEL-COLLECTOR：[来源](https://opentelemetry.io/docs/collector/resiliency/)；OpenTelemetry Collector resiliency; rolling page observed 2026-10-23；发布者：OpenTelemetry project；性质：signal protocol/specification or Collector implementation guidance | Sending queue; retry; persistent storage；内存队列/重试有限会丢弃；file_storage WAL可跨重启但磁盘满/损坏及重试期限仍可丢数。 | 本地WAL不产生任意故障下分布式耐久与Exactly-once承诺。 |
| OTEL-LOGS：[来源](https://opentelemetry.io/docs/specs/otel/logs/data-model/)；OpenTelemetry logs data model; rolling spec observed 2026-10-23；发布者：OpenTelemetry project；性质：signal protocol/specification or Collector implementation guidance | Timestamp; ObservedTimestamp; TraceId/SpanId；Timestamp是原事件时间，ObservedTimestamp是采集观察时间；Trace/Span关联字段可选。 | 跨主机时间先后不单独证明因果或业务提交，日志缺失不证明动作未发生。 |
| OTEL-OTLP：[来源](https://opentelemetry.io/docs/specs/otlp/)；OTLP specification1.11.1; observed 2026-10-23；发布者：OpenTelemetry project；性质：signal protocol/specification or Collector implementation guidance | Partial success; retries; transport acknowledgements；partial_success填充后不得整请求重试，即使仅警告拒收数0；HTTP200可部分成功，确认是每跳而非后端耐久承诺；可重试码受协议限制。 | 接收ACK不是业务事务或永久存储成功，也不能对任意失败无界重试。 |
| REC-CSI：[来源](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)；Kubernetes VolumeSnapshots; modified2026-07-30；发布者：Kubernetes project；性质：rolling official implementation documentation | CSI/controller prerequisites; binding; Delete/Retain; topology；Snapshot为CRD且需实现快照的CSI及Controller/Sidecar；Delete/Retain影响实际存储快照；部分拓扑只在原区可恢复，新拓扑功能为Alpha。 | YAML复制不移动卷数据，不证明数据库应用一致或跨Region已备份。 |
| REC-D1：[来源](https://developers.cloudflare.com/d1/reference/time-travel/)；Cloudflare D1 Time Travel; rolling page observed 2026-10-23；发布者：Cloudflare；性质：vendor product implementation documentation | Availability; restore; limitations；生产D1恢复需适用Wrangler版本，按当前套餐7/30天窗口；就地覆盖会取消在途请求，恢复前Bookmark可用于再恢复。 | 不是任意历史保留或分叉新库功能，代码部署不回滚D1数据。 |
| REC-ETCD：[来源](https://etcd.io/docs/v3.6/op-guide/recovery/)；etcd v3.6 disaster recovery；发布者：etcd project；性质：versioned database recovery implementation documentation | Snapshotting; status; restoring; revision bump/membership；etcdctl snapshot save与直接拷db文件有不同完整性/WAL边界；etcdutl恢复创建新逻辑集群；Kubernetes/Watch消费者恢复旧Revision应考虑bump及mark-compacted失效缓存。 | 快照状态命令不证明全Kubernetes资源/证书/外部卷恢复；bump幅度需按真实变更速率与窗口确定，不照抄示例数。 |
| REC-OBJECT-LOCK：[来源](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)；Amazon S3 Object Lock; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Version protection; delete markers; governance bypass; legal hold；保护指定对象Version，仍可创建新版本/删除标记；简单DELETE可200建标记，指定受保Version删除被拒；Governance绕过需权限及Header。 | 对象不可变不等不可撤读取权限或整个Bucket永不改变；LegalHold与Retention独立。 |
| REC-OBJECTIVES：[来源](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html)；AWS DR workloads whitepaper; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Backup and restore; pilot light; warm standby；备份频率/恢复点、复制延迟和启用/扩容步骤影响RPO/RTO；Pilot Light与Warm Standby的可服务前置动作不同，需定期实测。 | 厂商典型延迟不是项目SLA或任何灾害下供应/数据零损失保证。 |
| REC-PG：[来源](https://www.postgresql.org/docs/18/continuous-archiving.html)；PostgreSQL18 manual；发布者：PostgreSQL Global Development Group；性质：versioned database implementation manual | §25.3 Continuous Archiving and PITR；物理PITR需兼容Base Backup及从起点起连续WAL链；pg_dump不是物理Base/WAL恢复输入。 | 备份成功不证明无缺段或任意跨大版本物理恢复；恢复后新Timeline/业务完整性另验。 |
| REC-REGION：[来源](https://learn.microsoft.com/en-gb/azure/reliability/regions-paired)；Azure region pairs; rolling page observed 2026-10-23；发布者：Microsoft；性质：vendor product implementation documentation | Region pairs and disaster recovery；Region Pair不自动提供HA/DR或Failover；微软发起的灾难Failover不是应用主要恢复策略。 | 区域名称/配对不证明数据、Key、身份、网络、配额与恢复授权完整。 |
| REC-VAULT：[来源](https://developer.hashicorp.com/vault/docs/sysadmin/snapshots/restore)；Vault snapshot restore; rolling docs observed 2026-10-23；发布者：HashiCorp；性质：vendor tool implementation documentation | External plugin artifacts; asynchronous restore completion；Raft快照不包含外部Plugin二进制，仅目录元数据；命令受理后后台恢复/解封完成及真实服务仍须观察。 | 单快照不包含所有引导材料，命令退出不等全部服务恢复。 |
| REC-VELERO：[来源](https://velero.io/docs/v1.17/restore-reference/)；[关联已读章节](https://velero.io/docs/v1.17/backup-reference/)；Velero v1.17 restore plus backup reference；发布者：Velero project；性质：versioned backup/restore implementation documentation | Existing resources; update policy; backup immutability compatibility；默认跳过已有对象（部分特例），Update为Best-effort且不据此覆盖PV数据；备份元数据阶段更新与不同对象锁实现兼容需独立核。 | Completed不证明所有已存在对象/卷被还原，Backup CR被删不等对象存储已清理。 |
| REL-CLOUDRUN：[来源](https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration)；Google Cloud Run traffic migration; rolling docs observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | Traffic splitting; migration behavior；路由变更非即时，正在处理请求继续，过渡请求可到旧/新Revision；现有Split可延续后续部署。 | 切0%不停止所有在途/后台/Tagged入口，也不撤回数据库变更。 |
| REL-ECS：[来源](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)；AWS ECS deployment circuit breaker; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | Rollback eligibility; deployment states；仅ECS滚动Controller适用；回滚需最近COMPLETED版本，无候选可停滞；回滚中的目标变IN_PROGRESS不再立即符合候选条件。 | 不能说任意ECS Controller或任意失败都自动业务回滚。 |
| REL-K8S：[来源](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)；Kubernetes Deployment; rolling docs observed 2026-10-23；发布者：Kubernetes project；性质：rolling official implementation documentation | Progress deadline; failed deployment; rollback；超过进度期限只报告ProgressDeadlineExceeded，本身不自动采取回滚；暂停不计该期限，其他编排器可另行处理。 | Rollout状态不证明客户入口或持久数据已恢复。 |
| REL-WORKERS：[来源](https://developers.cloudflare.com/workers/versions-and-deployments/)；Cloudflare Workers versions/deployments; updated 2026-09-22；发布者：Cloudflare；性质：vendor product implementation documentation | Version; Deployment; resource changes；Version包括代码/Assets/Bindings/兼容配置，不包含KV/R2/DO/D1持久内容；Deployment激活一或两Version，wrangler deploy默认创建并100%发布。 | 代码版本回退不回滚上述持久数据，也不自动取消外部效果。 |
| SECRET-AWS-ROTATE：[来源](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda-functions.html)；AWS Secrets Manager Lambda rotation; rolling page observed 2026-10-23；发布者：Amazon Web Services；性质：vendor product implementation documentation | createSecret; setSecret; testSecret; finishSecret；RequestToken使步骤幂等，AWSPENDING/Current/Previous分阶段；须更新真实服务并测试后切Current，验证目标避免Confused Deputy。 | 写Secret新值不等于旧凭据在数据库/缓存/会话中已撤销。 |
| SECRET-GCP-ROTATE：[来源](https://docs.cloud.google.com/secret-manager/docs/secret-rotation)；Google Cloud Secret Manager rotation; rolling page observed 2026-10-23；发布者：Google Cloud；性质：vendor product implementation documentation | Rotation schedules; Pub/Sub; delivery retries；轮换计划发SECRET_ROTATE通知，实际更新需订阅者实现；在途投递/重试最多七天等条件可推迟/跳过后续通知。 | 通知送达不是实际密码更换或消费者切换完成。 |
| SECRET-VAULT-LEASE：[来源](https://developer.hashicorp.com/vault/docs/concepts/lease)；Vault rolling docs v2.x navigation observed 2026-10-23；发布者：HashiCorp；性质：vendor tool implementation documentation | Lease; renewal; revocation；动态Secret/Service Token可有Lease，KV数据不属于Lease；续期增量由当前时间算且后端可忽略请求，必须检查返回TTL。 | TTL配置/撤销请求不证明目标服务或既有会话已实际失效。 |
| SUP-DSSE：[来源](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md)；DSSE v1.0.2 May10 2024; blob75dfb56e2437ca698003d6dde6f53b422e614fd1；发布者：Secure Systems Lab / DSSE；性质：versioned upstream specification/schema or tool reference; selected file identity retained | Envelope; PAE；签名认证PAE中的UTF8 payloadType与Payload字节，长度按字节计；keyid不被认证，仅可作查Key提示。 | keyid/文件名不产生Signer信任，解析出Envelope不等于验证签名。 |
| SUP-INTOTO：[来源](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)；in-toto Statement v1; blob630f773cb530fe5989fe2dbc30e7f73239cd943a；发布者：in-toto project；性质：versioned upstream specification/schema or tool reference; selected file identity retained | Statement fields; subject; predicateType；Statement用Type URI、Subject摘要与PredicateType区分语义；Subject身份靠摘要，name可选，Predicate字段也可能省略。 | 字段齐全不证明签名/内容真实或目标消费者已执行策略。 |
| SUP-PROVENANCE：[来源](https://slsa.dev/spec/v1.2/build-provenance)；SLSA v1.2 provenance v1；发布者：SLSA project；性质：versioned community specification; selected Track/Level conditional | BuildDefinition; RunDetails; builder.id; resolvedDependencies；Builder身份代表信任闭包/运行模式；消费者必须限定可接受Signer–Builder组合；依赖完整性要求依等级/字段不同。 | 签名有效不自动批准Builder、Source、参数或目标制品，不能声称所有依赖都已完整可复现。 |
| SUP-SLSA：[来源](https://slsa.dev/spec/v1.2/build-track-basics)；[关联已读章节](https://slsa.dev/spec/v1.2/build-requirements)；SLSA v1.2 Build Track；发布者：SLSA project；性质：versioned community specification; selected Track/Level conditional | Build levels L0–L3; requirements overview；L1有Provenance但可未签或不完整；L2要求受托管平台生成且可认证；L3增加运行隔离及用户构建步骤不可访问Provenance签名Key。 | Build/Source Track与等级分开，不从使用某CI或有SBOM推定达到L2/L3。 |
| SUP-SOURCE：[来源](https://slsa.dev/spec/v1.2/source-requirements)；SLSA v1.2 Source Track requirements；发布者：SLSA project；性质：versioned community specification; selected Track/Level conditional | Levels1–4; continuity; Source Provenance; two-party review；Source等级与Build独立；控制连续性中断需从新Revision重建，SourceL4要求最终上下文两可信人审查并有规范定义的TrustedRobot例外。 | 不能凭当前开关、两个同人账号或BuildL3声称历史SourceL4；不要求所有项目选L4或必须Git。 |
| BL-AWS-SHARED：[来源](https://aws.amazon.com/compliance/shared-responsibility-model/)；AWS Shared Responsibility Model; rolling page read 2026-10-23；发布者：Amazon Web Services；性质：供应商责任模型说明 | Overview; Understanding the AWS Shared Responsibility Model; Customer responsibility; Applying the model in practice；AWS说明其管理基础设施层，而客户责任随所选服务变化；EC2客户需管理来宾OS/应用及安全组，S3等抽象服务仍要求客户管理数据分类与权限。 | 不是所有供应商的合同，也不证明客户数据权利、业务承诺、真实角色已获授权或审计结论。 |

## 三、技术机制与逐条可观察合同

### §01 领域启用与最小基础设施
<a id="CLD-BL-01"></a>

**稳定条款：** `CLD-BL-01`（保留 `§01`）。

**机制：** 按真实服务可用性、数据权利、交付渠道及使用负载决定云/本地/托管/Serverless 等运行方式，不强制引入 Kubernetes、独立集群、Service Mesh 或付费工具。

**验收：** 每种平台组件能关联实际业务负载、权限和成本边界；无用组件可移除且不损害核心交付。

**主体、前置与输入：** 本条针对“领域启用与最小基础设施”；执行者必须具有目标范围的实际权限，消费 `CLD-BL-T1` 的固定输入：固定业务画像、峰值/持续负载、延迟/可用性/恢复目标、数据处理允许范围、维护能力、当前部署及成本上限；每个组件关联所需能力，包含不采用某组件的理由。

**权威状态与输出：** 有权服务负责人确认的业务负载/数据权利/可用性与恢复目标，实际运行时与资产清单；费用权威仅负责费用，不代替平台选择决定。输出本条验收的原始观察及 `CLD-BL-T1` 产物：组件—业务能力—负载—权限—成本—恢复映射、候选运行方式的取舍、代表负载原始结果和移除冗余组件后的回归；不得因未采购Kubernetes/多云而失败。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 负载/权利/目标变化时重新评估受影响组件；比较期间固定版本与负载，单次探针超时保留未知；移除失败先恢复已验证配置和数据，再依据业务探针确认恢复，不能仅重启进程结案。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，可保留单站点/托管部署方案，不强制无关平台成本；本条具体可观察验收仍为“每种平台组件能关联实际业务负载、权限和成本边界；无用组件可移除且不损害核心交付。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 公开静态页面被要求采购完整 Kubernetes 集群。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 既有单机满足负载和恢复目标，可不采用容器。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-BL-T1` ](#CLD-BL-T1)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`COST-FOCUS`；只支持第二节所列命题，不为整条实施结果背书。

**专属验收分界：** 单机或托管静态站点在固定负载与恢复目标下满足输出且成本可解释，允许保留简单架构；直接失败：没有业务能力或负载依据，单因平台偏好强制购买完整集群，或用健康HTTP200代替恢复测试，判失败；合法邻例：业务实际需要集群的隔离/调度能力且存在负载与恢复证据时，允许采用集群；简单架构优先不等于禁止复杂架构。

### §02 共享责任与服务合同
<a id="CLD-BL-02"></a>

**稳定条款：** `CLD-BL-02`（保留 `§02`）。

**机制：** 区分开发者、云商、托管商、域名/CDN/证书提供者、运行 Agent、客户及发布者的实际权限；平台资源权限不自动产生数据使用权和服务对外承诺。

**验收：** 根据真实账户/合同模拟云商故障、客户请求和 Agent 操作，能指出谁负责处理、批准与验证。

**主体、前置与输入：** 本条针对“共享责任与服务合同”；执行者必须具有目标范围的实际权限，消费 `CLD-BL-T2` 的固定输入：固定服务类型与所用功能、合同/责任说明的标识和有效范围、实际开发者/平台/托管商/域名证书方/运行Agent/客户/发布者及可兼任职责；云商故障、客户数据请求、Agent高风险动作三个事件画像。

**权威状态与输出：** 具体服务/版本的责任说明与实际有效合同、有权数据决定者、真实账户主体及服务责任矩阵；本工具或IAM标签不产生合同或数据处理权限。输出本条验收的原始观察及 `CLD-BL-T2` 产物：三事件各自的处理者、授权者、执行Principal、验证者、升级渠道/时限与证据出处；区分基础设施恢复、客户数据决定和对外承诺，缺失真实负责人不得以虚构审批者填补。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 服务或合同版本变化先复核职责分界；角色兼任可保留但每项实际权限仍核实；责任争议/未知授权期间只执行已允许的保全动作并升级有权主体，不借平台管理员身份处理客户数据。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，云商资源操作权限不能代替客户数据与合同授权；本条具体可观察验收仍为“根据真实账户/合同模拟云商故障、客户请求和 Agent 操作，能指出谁负责处理、批准与验证。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 云商管理控制台有权限便直接宣称能够处理客户数据。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 托管商负责物理故障，应用方仍持有数据处理决定权。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-BL-T2` ](#CLD-BL-T2)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`BL-AWS-SHARED`；只支持第二节所列命题，不为整条实施结果背书。

**专属验收分界：** 平台方处理其基础设施故障，应用方对其客户数据和应用配置承担明确职责，Agent只在当前委派范围执行；直接失败：仅凭云控制台Owner权限便批准客户数据新用途，或将云商负责硬件扩张成供应商承担所有业务故障，判失败；合法邻例：单人真实主体兼任开发/发布/运维可接受，只要其对每项动作确有权限且责任/验证路径明确，不强制虚构多人审批。

### §03 环境、账户与秘密隔离
<a id="CLD-BL-03"></a>

**稳定条款：** `CLD-BL-03`（保留 `§03`）。

**机制：** 隔离开发、测试、验收、预发布、生产的账号、项目、租户、网络、数据集、出口、凭据、构建制品与通知目的端；不以默认参数造成跨环境写入。

**验收：** 测试标识、密钥或数据无法经默认部署模板或回退进入生产，生产变更需要明确目标环境。

**主体、前置与输入：** 本条针对“环境、账户与秘密隔离”；执行者必须具有目标范围的实际权限，消费 `CLD-IAM-T1` 的固定输入：当前账户/项目不可变ID、父级、Region、实际Principal、目标资源及合同作用域。

**权威状态与输出：** 云账户/目录与实际资源访问控制面；批准者与执行Principal分别记录。输出本条验收的原始观察及 `CLD-IAM-T1` 产物：主体-动作-资源-环境矩阵与实况清单；标签不产生有效权限。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 改名/删除重建/迁层级先重算绑定；换票或API超时不推定已授权，读回实际Principal及继承后再恢复。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**必要补充与不变量：** 环境标签是索引，不是隔离证据；进入变更前必须回读账户/项目不可变ID、Region、有效Principal与目标数据集，并对反环境资源执行拒绝测试。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，不同环境的凭据与通知目的端不得复用，跨环境外发被阻止；本条具体可观察验收仍为“测试标识、密钥或数据无法经默认部署模板或回退进入生产，生产变更需要明确目标环境。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 预发布配置默认指向生产密钥和真实用户通知地址。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 相同环境显示名可以存在于不同账号，但有效资源ID与身份不共享。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAM-T1` ](#CLD-IAM-T1)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAM-AWS-SCP`、`IAM-GCP-DENY`、`IAM-AZ-ROLE`；只支持第二节所列命题，不为整条实施结果背书。

### §04 地域、法域与网络出口
<a id="CLD-BL-04"></a>

**稳定条款：** `CLD-BL-04`（保留 `§04`）。

**机制：** 在实际选用的区域、可用区、VPC/私网、出口代理、CDN/镜像与备份链上核对数据所在位置、接收方、传输边界及容灾需求。

**验收：** 跨区域故障切换、镜像或外发不得绕过适用合同、数据驻留和网络访问控制。

**主体、前置与输入：** 本条针对“地域、法域与网络出口”；执行者必须具有目标范围的实际权限，消费 `CLD-NET-T1` 的固定输入：IPv4/IPv6源/目标、VPC/VNet/Region、接口、路由表、NAT/代理、允许接收方。

**权威状态与输出：** 实际云网络/路由器与权威DNS；网络编辑者不拥有业务数据权。输出本条验收的原始观察及 `CLD-NET-T1` 产物：选定源的实际下一跳/出口及可达性；环境和地址身份可追踪。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 更具体路由、NAT复用或路径失联时逐跳分层；未知路由不以临时全开放恢复。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，跨区域复制应受法域、合同和真实出入口条件限制；本条具体可观察验收仍为“跨区域故障切换、镜像或外发不得绕过适用合同、数据驻留和网络访问控制。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 故障切换将受限数据复制到未获授权区域。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 同一法域单区方案在已接受的恢复目标内合法。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-NET-T1` ](#CLD-NET-T1)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`NET-GCP-FW`、`NET-AZ-NSG`；只支持第二节所列命题，不为整条实施结果背书。

### §05 IAM 最小授权
<a id="CLD-BL-05"></a>

**稳定条款：** `CLD-BL-05`（保留 `§05`）。

**机制：** 把人员、服务、自动化、CI、生产维护、只读审计身份的操作权限和资源作用域分开；云角色、Kubernetes RBAC 与应用业务授权分别验证。

**验收：** 用正反权限矩阵验证普通部署身份不能修改资金、密钥和非目标环境的资源。

**主体、前置与输入：** 本条针对“IAM 最小授权”；执行者必须具有目标范围的实际权限，消费 `CLD-IAM-T2` 的固定输入：身份/资源Policy、SCP/RCP、Boundary、Session、GCP Deny、Azure全部Role/Deny及Principal种类。

**权威状态与输出：** 选用供应商的策略求值器与目标服务资源策略，而不是本地集合模型。输出本条验收的原始观察及 `CLD-IAM-T2` 产物：正向最小访问成功、跨资源/显式拒绝失败；策略求值过程和产品例外。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 策略传播中保持旧/新结果与时点；单侧模拟不确定先停高影响操作，读取实际服务拒绝/允许后确认。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，不在职责范围内的高权限操作应拒绝；本条具体可观察验收仍为“用正反权限矩阵验证普通部署身份不能修改资金、密钥和非目标环境的资源。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 应用部署角色意外持有全账号删除与计费权限。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 只读运维身份可查元数据，不因此拥有客户正文。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAM-T2` ](#CLD-IAM-T2)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAM-AWS-EVAL`、`IAM-AWS-SCP`、`IAM-GCP-DENY`、`IAM-AZ-ROLE`、`IAM-AZ-DENY`、`K8S-RBAC`；只支持第二节所列命题，不为整条实施结果背书。

### §06 短期工作负载身份
<a id="CLD-BL-06"></a>

**稳定条款：** `CLD-BL-06`（保留 `§06`）。

**机制：** 能使用联合身份与短期 Token 时优先避免长期静态云密钥；校验所选发行者的 Issuer、Subject、Audience、Token 有效期及目标信任条件；采用 GitHub 工作流时再绑定实际可用的仓库、分支、环境等 Claim，不向其他发行者强造同名字段。

**验收：** 伪造分支/PR、错误 Audience 或过期凭据无法访问生产云角色，合法工作流获得最小期限权限。

**主体、前置与输入：** 本条针对“短期工作负载身份”；执行者必须具有目标范围的实际权限，消费 `CLD-IAM-T4` 的固定输入：机制分支、目标资源/只读动作、策略修订和期限；AWS认证分支为源Principal、RoleArn、RoleSessionName及适用ExternalId/MFA/会话策略；OIDC分支为Issuer/Audience/Subject、签名键/算法和Trust；GCP另固定Provider/subjectTokenType及适用SA/Scope/委派链；Azure托管身份为宿主、身份选择器和目标resource。

**权威状态与输出：** 按实际机制分别由AWS认证主体和Role Trust、外部IdP与云端联合信任、GCP调用方/服务账号权限、或Azure已分配身份与Entra决定会话；目标服务另决定资源动作。输出本条验收的原始观察及 `CLD-IAM-T4` 产物：脱敏的实际源/会话/目标身份、期限、请求ID、交换和资源调用的分别结果；非OIDC分支不伪填Issuer/JWKS，错误Principal/适用ExternalId或OIDC发行者/受众不得取得越权结果。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 固定机制、Trust/Mapping/身份分配修订和期限；超时先核原交换/会话及操作身份，冲突或未知不借新Token重放业务副作用。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**必要补充与不变量：** 联合登录的主体命名空间由发行者与映射共同定义；验Token签名/时效不等于目标角色或业务对象授权成立。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，Federation 信任策略必须限制正确仓库、分支/环境和 Audience；本条具体可观察验收仍为“伪造分支/PR、错误 Audience 或过期凭据无法访问生产云角色，合法工作流获得最小期限权限。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 来自任意分支的 OIDC 身份取得生产部署令牌。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 非GitHub OIDC发行者无需GitHub仓库Claim，但必须有等效不可混淆主体绑定。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAM-T4` ](#CLD-IAM-T4)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAM-AWS-STS-AUTH`、`IAM-AWS-WEBIDENTITY`、`IAM-GCP-WIF`、`IAM-GCP-STS`、`IAM-GCP-IMPERSONATE`、`IAM-AZ-MANAGED-TOKEN`、`GH-OIDC`；仅支持[来源登记](../../../sources/cloud/source-claims.json)中的对应有限命题，不为整条实施结果背书。

### §07 秘密配置与轮换
<a id="CLD-BL-07"></a>

**稳定条款：** `CLD-BL-07`（保留 `§07`）。

**机制：** 区分公开配置、敏感配置、Kubernetes Secret、存储加密、外部密钥管理和日志脱敏；编码或 CI 隐藏不等于可靠加密和实际撤权。

**验收：** 恶意或低权工作负载无法读取其他环境秘密；轮换后旧凭据在确认窗口内失效且服务合法恢复。

**主体、前置与输入：** 本条针对“秘密配置与轮换”；执行者必须具有目标范围的实际权限，消费 `CLD-SEC-T5` 的固定输入：轮换事件/ClientRequestToken、候选版本、同一目标资源、测试与CURRENT、旧值退出。

**权威状态与输出：** 源数据库/API认证服务与Store Stage、消费者共同定义轮换完成。输出本条验收的原始观察及 `CLD-SEC-T5` 产物：准备/set/test/finish与实际失效分步结果；全消费者新值正例。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 重复通知按同一操作账恢复；未知set先查询目标；未泄露旧值可依批准回退，泄露值绝不可复活。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，低权不能从日志重放秘密，轮换后旧 Token 不可继续使用；本条具体可观察验收仍为“恶意或低权工作负载无法读取其他环境秘密；轮换后旧凭据在确认窗口内失效且服务合法恢复。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** Kubernetes Secret 明文暴露在 CI 日志且长期不轮换。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 公开配置可进入镜像，不将其与可重放Token等同。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-SEC-T5` ](#CLD-SEC-T5)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`SECRET-AWS-ROTATE`、`SECRET-GCP-ROTATE`、`SECRET-VAULT-LEASE`；只支持第二节所列命题，不为整条实施结果背书。

### §08 高影响操作与应急账户
<a id="CLD-BL-08"></a>

**稳定条款：** `CLD-BL-08`（保留 `§08`）。

**机制：** 删除资源、解锁 IaC State、提升生产角色、区域迁移、不可逆加密/保留设置和紧急访问分别要求适当权限、有效依据及可恢复路径。

**验收：** 越权操作者无法执行高影响动作，合法应急账户的使用时点、权限范围与后续复核均可查。

**主体、前置与输入：** 本条针对“高影响操作与应急账户”；执行者必须具有目标范围的实际权限，消费 `CLD-IAM-T3` 的固定输入：组/嵌套组、认证强度、临时角色起止、应急身份、委派来源。

**权威状态与输出：** 真实身份源与每次已签发会话；目录移除与目标授权各自权威。输出本条验收的原始观察及 `CLD-IAM-T3` 产物：高风险当前会话正例、普通/过期会话拒绝及实际撤权窗口。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 目录更新、Token缓存、下游委派并发时逐入口回读；不刷新为匿名管理员，不复活失效主体。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，操作因非持有者及缺少批准而拒绝并保留在途状态；本条具体可观察验收仍为“越权操作者无法执行高影响动作，合法应急账户的使用时点、权限范围与后续复核均可查。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** Agent 为修复错误直接解锁他人的 IaC State。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 有权人可按受控方案解除自己已终止作业的遗留锁。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAM-T3` ](#CLD-IAM-T3)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAM-GCP-DENY`、`IAM-AZ-IDENTITY`、`GH-OIDC`；只支持第二节所列命题，不为整条实施结果背书。

### §09 源码版本与构建对象身份
<a id="CLD-BL-09"></a>

**稳定条款：** `CLD-BL-09`（保留 `§09`）。

**机制：** 记录可重现定位的源提交、构建定义、外部依赖、输出平台/架构、制品摘要及运行入口；分清 Tag、Digest 和渠道上架版本。

**验收：** 从运行制品能核对源版本与内容 Digest；同名标签发生漂移时不自动视为等价制品。

**主体、前置与输入：** 本条针对“源码版本与构建对象身份”；执行者必须具有目标范围的实际权限，消费 `CLD-SUP-T2` 的固定输入：全文件集合、算法/字节范围、源码/构建配置、多架构Index及重打包身份。

**权威状态与输出：** 实际分发字节、发布清单与目标OS/ABI，而非Git Tag或CI名。输出本条验收的原始观察及 `CLD-SUP-T2` 产物：逐文件/平台摘要、可重现性范围与派生制品新身份。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 相同源码可多产物；单文件变化不能沿用旧签名，重建差异保持真实不夸SLSA等级。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，必须检测 Digest 漂移并标明真实提交和构建输入；本条具体可观察验收仍为“从运行制品能核对源版本与内容 Digest；同名标签发生漂移时不自动视为等价制品。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 相同 Docker tag 在两次构建中指向不同镜像，发布记录却未核对各自真实 Digest 而仍将两者视为同一已批准制品。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 一个源码提交可产生多个合法平台制品，逐个摘要分别记录；可变频道 Tag 合法移到新内容时仍保留每份 Digest、来源和批准范围。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-SUP-T2` ](#CLD-SUP-T2)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`OCI-IMAGE`、`OCI-INDEX`、`OCI-DESCRIPTOR`、`SUP-SLSA`；只支持第二节所列命题，不为整条实施结果背书。

### §10 构建环境与执行隔离
<a id="CLD-BL-10"></a>

**稳定条款：** `CLD-BL-10`（保留 `§10`）。

**机制：** 区分公共 PR、受信主分支、发行与生产部署工作流的权限、缓存、网络、Runner 生命周期和制品来源；禁止把未审代码作为高权构建输入。

**验收：** 在隔离测试下，外部 PR 不能读取生产秘密或污染受信发布缓存和工作目录。

**主体、前置与输入：** 本条针对“构建环境与执行隔离”；执行者必须具有目标范围的实际权限，消费 `CLD-CI-T3` 的固定输入：Runner ID/版本/OS、Label/Group、信任级、Socket/网络、JIT清理及工作目录。

**权威状态与输出：** 实际Runner宿主/Executor和Group允许来源，Label仅为选路。输出本条验收的原始观察及 `CLD-CI-T3` 产物：queued/实际执行/清洁完成分别记录，跨Job/跨租户负例拒绝。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** JIT注销不清宿主；清理或更新失败先隔离Runner；挂死/取消后核孤儿进程及凭据。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，不可信执行无法访问跨作业目录和生产秘密；本条具体可观察验收仍为“在隔离测试下，外部 PR 不能读取生产秘密或污染受信发布缓存和工作目录。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 外部 PR 可在持久 Runner 读取上次生产任务残留。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 无生产秘密的隔离Runner可执行未受信代码。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-CI-T3` ](#CLD-CI-T3)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`GH-SECURE`、`CI-GITLAB`、`CI-NIST204D`；只支持第二节所列命题，不为整条实施结果背书。

### §11 依赖清单与版本固定
<a id="CLD-BL-11"></a>

**稳定条款：** `CLD-BL-11`（保留 `§11`）。

**机制：** 依据真实软件栈管理依赖锁定、校验和、基础镜像及必要 SBOM/来源证据；避免不必要强制采购或所有项目统一工具。

**验收：** 重建时能核对相同输入依赖或明确发现漂移，过期镜像与高风险依赖能定位真实受影响制品。

**主体、前置与输入：** 本条针对“依赖清单与版本固定”；执行者必须具有目标范围的实际权限，消费 `CLD-SUP-T1` 的固定输入：直接/传递/可选依赖锁、包源/子模块Ref、基础Manifest、下载摘要及平台条件。

**权威状态与输出：** 实际依赖解析器/受信源与构建材料清单；名称不是内容身份。输出本条验收的原始观察及 `CLD-SUP-T1` 产物：解析后输入闭包与单字节/依赖混淆替换拒绝。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 上游Tag/分支/包响应变化需重绑受审输入；缓存只能加速，不把未核来源产物提升。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，能从锁定和摘要找出被替换依赖并拒绝未经审批制品；本条具体可观察验收仍为“重建时能核对相同输入依赖或明确发现漂移，过期镜像与高风险依赖能定位真实受影响制品。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 依赖管理只固定顶层版本而基础镜像可无声更新。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 不要求SBOM的内部低风险输出仍须记录实际输入版本。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-SUP-T1` ](#CLD-SUP-T1)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`OCI-IMAGE`、`SUP-SLSA`；只支持第二节所列命题，不为整条实施结果背书。

### §12 制品证明与发布门禁
<a id="CLD-BL-12"></a>

**稳定条款：** `CLD-BL-12`（保留 `§12`）。

**机制：** 按实际产品风险选择 SLSA Build/Source Track、来源声明、签名或 Attestation 级别；验签主体、Digest 和构建环境，CI 成功不自动等于具备 SLSA 等级。

**验收：** 制品内容或来源不匹配、证明无效及未经授权的替换被发行门禁拒绝。

**主体、前置与输入：** 本条针对“制品证明与发布门禁”；执行者必须具有目标范围的实际权限，消费 `CLD-SUP-T5` 的固定输入：in-toto Type URI、Subject Digest、DSSE原始payload/type、BuildDefinition/RunDetails与Track/Level。

**权威状态与输出：** 预设可信signer-builder与实际Subject/Predicate签名内容。输出本条验收的原始观察及 `CLD-SUP-T5` 产物：字节/类型/Builder来源绑定及每个选定等级完整要求证据。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** keyid未认证；Proof可来自错误Run/Subject，缺任何必需证据不补造；取消构建不代表签发未发生。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**必要补充与不变量：** 构建输入、Builder身份、签发者身份、消费策略与实际分发Digest必须闭合；Checksum、SBOM、签名与Provenance不得互相替代。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，发布门禁验证 Digest、Attestation 和有效签发主体；本条具体可观察验收仍为“制品内容或来源不匹配、证明无效及未经授权的替换被发行门禁拒绝。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 存在来源声明但实际部署镜像摘要与其主体不符。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 采用普通签名而未选择SLSA等级，不应被虚构等级门禁拒绝。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-SUP-T5` ](#CLD-SUP-T5)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`SUP-INTOTO`、`SUP-DSSE`、`SUP-PROVENANCE`、`SUP-SLSA`、`SUP-SOURCE`；只支持第二节所列命题，不为整条实施结果背书。

### §13 IaC 变更与实际对象归属
<a id="CLD-BL-13"></a>

**稳定条款：** `CLD-BL-13`（保留 `§13`）。

**机制：** 基础设施资源声明、远端状态、导入外部对象、人工紧急修改与资源删除应有源仓库/环境/执行身份；Plan 需确认实际作用范围。

**验收：** 同一变更在选定目标环境仅影响授权资源，意外删除或重建必须可识别。

**主体、前置与输入：** 本条针对“IaC 变更与实际对象归属”；执行者必须具有目标范围的实际权限，消费 `CLD-IAC-T1` 的固定输入：源提交、目标账号/Region、Provider Alias、Workspace/Stack/Backend与生命周期批准。

**权威状态与输出：** 云Resource ID与唯一声明/State负责人；工作区名字不产生权限。输出本条验收的原始观察及 `CLD-IAC-T1` 产物：对象ID/地址/受权范围映射，跨环境拒绝及预览影响。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 同名/重建/迁区必须重绑；未知实际归属先回读，不从空State推断云对象不存在。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，未经授权的目标资源变更应阻断；本条具体可观察验收仍为“同一变更在选定目标环境仅影响授权资源，意外删除或重建必须可识别。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** IaC Plan 预期仅改测试网络却包含生产网关删除。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 既有资源可合法导入；导入不应默默扩大资源权利。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAC-T1` ](#CLD-IAC-T1)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAC-TF-LOCK`、`IAM-AWS-EVAL`；只支持第二节所列命题，不为整条实施结果背书。

### §14 状态锁、并发与故障恢复
<a id="CLD-BL-14"></a>

**稳定条款：** `CLD-BL-14`（保留 `§14`）。

**机制：** IaC State 由实际选用 Backend 持有；不能假定所有后端支持锁；强制解锁前核验持有者、运行事务和当前版本/序列。

**验收：** 两次并发变更不得静默覆盖 State，错误 force-unlock 不得破坏合法在途变更。

**主体、前置与输入：** 本条针对“状态锁、并发与故障恢复”；执行者必须具有目标范围的实际权限，消费 `CLD-IAC-T4` 的固定输入：Lock ID/Key/持有Run、当前State、旧执行进程、恢复批准、Provider请求ID。

**权威状态与输出：** State锁Backend及覆盖全部写入口的交接门；云对象仍有实际执行权威。输出本条验收的原始观察及 `CLD-IAC-T4` 产物：同State最多一有效写者，遗留锁受控解锁、局部创建纳管结果。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 超时不证旧持有者已停；force-unlock是工具动作非活跃检测；先冻结/终止或栅栏旧写者，再核资源/State后重新规划。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**必要补充与不变量：** 锁ID只能定位锁，不证明其持有者已停止；解锁门须阻断新写入、确认全部旧执行路径停止或被目标侧栅栏拒绝，再在受保护State快照下处理。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，仍有合法执行者时不得并行写入 State 或静默解锁；本条具体可观察验收仍为“两次并发变更不得静默覆盖 State，错误 force-unlock 不得破坏合法在途变更。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** State 锁获取失败后操作员直接 force-unlock。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 无原生锁后端可采用经验证的外部唯一写入控制。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAC-T4` ](#CLD-IAC-T4)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAC-TF-LOCK`、`IAC-TOFU-LOCK`、`IAC-TOFU-BACKEND`；只支持第二节所列命题，不为整条实施结果背书。

### §15 实际漂移与声明差异
<a id="CLD-BL-15"></a>

**稳定条款：** `CLD-BL-15`（保留 `§15`）。

**机制：** 区分 Plan 检测的资源漂移、配置变更、Provider 非确定字段与合法的临时人工恢复；不以静态模板等同当前生产。

**验收：** 对真实对象、权限和 DNS 等执行只读比对，未审漂移在下一次 Apply 前被处理。

**主体、前置与输入：** 本条针对“实际漂移与声明差异”；执行者必须具有目标范围的实际权限，消费 `CLD-IAC-T8` 的固定输入：支持资源/显式属性、Nested Stack、手工变更、当前State、孤儿资源和账单。

**权威状态与输出：** 云实况与受权声明差异，State维护和最终费用/资源Owner。输出本条验收的原始观察及 `CLD-IAC-T8` 产物：漂移覆盖/NOT_CHECKED、状态修复审计、纳管/退役交接。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 只读采集不偷写State；IN_SYNC不证全覆盖；Pulumi refresh不改源码，下一up可能改回；遗留计费不结零账。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，发现实际对象与声明漂移并在 Apply 前处理；本条具体可观察验收仍为“对真实对象、权限和 DNS 等执行只读比对，未审漂移在下一次 Apply 前被处理。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 生产安全组已被手动改宽但仓库 Plan 未检查。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 授权救援造成的临时漂移可先保留，但须防下一Apply覆盖。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAC-T8` ](#CLD-IAC-T8)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAC-CFN-DRIFT`、`IAC-PULUMI`、`COST-FOCUS`；只支持第二节所列命题，不为整条实施结果背书。

### §16 不可逆变更与回退前提
<a id="CLD-BL-16"></a>

**稳定条款：** `CLD-BL-16`（保留 `§16`）。

**机制：** 主机/网络销毁、状态数据库丢失、加密密钥撤销、资源迁区、保留锁等变化要区分可回退、需数据迁移及真正不可逆动作。

**验收：** 在提交变更前能通过预演或证据识别不可逆副作用；未经有权人批准不得执行。

**主体、前置与输入：** 本条针对“不可逆变更与回退前提”；执行者必须具有目标范围的实际权限，消费 `CLD-IAC-T7` 的固定输入：Plan/State身份、当前权限、变更窗口、异步任务ID、重试/失败模式及业务不可逆性。

**权威状态与输出：** 执行API/异步任务与当前有效资源；批准绑定当前确定目标。输出本条验收的原始观察及 `CLD-IAC-T7` 产物：已接受/执行中/局部成功/完成/Unknown与实际资源状态分离。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** State未变不排除外部漂移；异步超时先查询；保留成功资源与回滚模式按产品核，不重放未知创建。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，必须提前分类和批准不可逆动作；未完成分类或有效批准不得执行，批准后的受控自动化不因此被禁止；本条具体可观察验收仍为“在提交变更前能通过预演或证据识别不可逆副作用；未经有权人批准不得执行。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 一条批量 Terraform Apply 包含不可逆密钥销毁，未识别该副作用或未取得绑定准确目标与计划的有权批准便执行。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 已识别且得到覆盖准确目标、计划及数据保护条件的有权批准时，可按受控方案执行不可逆变更；可重建无状态实例也可受控替换，不强求数据回滚。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-IAC-T7` ](#CLD-IAC-T7)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`IAC-TF-PLAN`、`IAC-CFN-FAIL`、`IAC-CFN-CHANGE`；只支持第二节所列命题，不为整条实施结果背书。

### §17 制品运行与架构匹配
<a id="CLD-BL-17"></a>

**稳定条款：** `CLD-BL-17`（保留 `§17`）。

**机制：** 实际使用容器时核对 OCI Image、Digest、操作系统/CPU 架构、入口、持久卷和不可变应用配置，不以镜像可拉取代表可运行或安全。

**验收：** 镜像架构不匹配、Tag 漂移、挂载错误都可在上线前被识别并拒绝。

**主体、前置与输入：** 本条针对“制品运行与架构匹配”；执行者必须具有目标范围的实际权限，消费 `CLD-ISO-T2` 的固定输入：Index/平台Digest、config.json、RootFS、Handler、PID1/入口和OS/ABI画像。

**权威状态与输出：** OCI目标Manifest/Bundle及实际CRI/Runtime/Kernel ABI。输出本条验收的原始观察及 `CLD-ISO-T2` 产物：真实目标启动与关键系统调用/信号/退出结果，不只拉取成功。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** Bundle或Handler不支持时明确拒绝；启动超时核真实进程/端口及容器ID，不重叠启动未知实例。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，运行前拒绝不兼容镜像和挂载；本条具体可观察验收仍为“镜像架构不匹配、Tag 漂移、挂载错误都可在上线前被识别并拒绝。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 镜像可拉取但实际架构与节点 CPU 不匹配。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 无容器项目按真实进程/安装包平台匹配验收。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-ISO-T2` ](#CLD-ISO-T2)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`OCI-IMAGE`、`OCI-INDEX`、`OCI-RUNTIME`、`ISO-WINDOWS`；只支持第二节所列命题，不为整条实施结果背书。

### §18 工作负载权限及隔离
<a id="CLD-BL-18"></a>

**稳定条款：** `CLD-BL-18`（保留 `§18`）。

**机制：** 选择运行用户、文件系统写入范围、Capability、Seccomp、主机挂载及 Pod Security 等能力时按真实容器引擎/宿主机版本检验。

**验收：** 普通应用不可因默认特权获取宿主机密钥或访问同机无关容器；合法服务仍可运行。

**主体、前置与输入：** 本条针对“工作负载权限及隔离”；执行者必须具有目标范围的实际权限，消费 `CLD-ISO-T3` 的固定输入：Pod/Container最终SecurityContext、uid_map/gid_map、PID/IPC/Network共享、必要能力。

**权威状态与输出：** 运行进程实际UID映射/Namespace/Capability/no_new_privs及宿主Socket权限。输出本条验收的原始观察及 `CLD-ISO-T3` 产物：允许业务成功而越权Host/跨租户操作被内核/Runtime拒绝。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** Pod与Container覆盖、Daemon Rootless与Remap分别核；撤能力后旧进程状态重新观察，不以新YAML代表旧进程。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，普通容器不得读取宿主机未授权路径和凭据；本条具体可观察验收仍为“普通应用不可因默认特权获取宿主机密钥或访问同机无关容器；合法服务仍可运行。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 容器默认特权运行并挂载宿主机秘密目录。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 经批准的专用管理容器可具必要能力，不能使普通负载继承。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-ISO-T3` ](#CLD-ISO-T3)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`ISO-ROOTLESS`、`ISO-USERNS`、`OCI-RUNTIME`、`K8S-SECURITY`；只支持第二节所列命题，不为整条实施结果背书。

### §19 入口/出口与网络执行能力
<a id="CLD-BL-19"></a>

**稳定条款：** `CLD-BL-19`（保留 `§19`）。

**机制：** 将 DNS、路由、TLS、WAF、Ingress、私网和网络策略与应用身份区别；Kubernetes NetworkPolicy 只在真实支持的 CNI 下发挥预期隔离。

**验收：** 跨租户测试请求不能访问隔离目标；无策略能力时必须采用有效替代控制，而非仅提交 YAML。

**主体、前置与输入：** 本条针对“入口/出口与网络执行能力”；执行者必须具有目标范围的实际权限，消费 `CLD-NET-T2` 的固定输入：规则版本/优先级/方向、ENI/NIC/Subnet关联、Pod选择器、CNI及既有连接。

**权威状态与输出：** 真正关联的SG/NACL/NSG/层级Firewall和具策略能力的CNI数据面。输出本条验收的原始观察及 `CLD-NET-T2` 产物：获准新流成功、跨租户/出口新流拒绝；旧流撤断与策略传播单列。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** Policy API成功不证数据面；传播空窗与hostNetwork/既有连接按实现测，无法确定先隔离高影响路径。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，测试仍可访问隔离 Pod 时必须判定策略无效；本条具体可观察验收仍为“跨租户测试请求不能访问隔离目标；无策略能力时必须采用有效替代控制，而非仅提交 YAML。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 提交了 NetworkPolicy 但当前 CNI 不实施策略。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 无NetworkPolicy能力时可采用实际有效的独立网络控制。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-NET-T2` ](#CLD-NET-T2)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`NET-AWS-SG`、`NET-AWS-SG-RULES`、`NET-AWS-NACL`、`NET-GCP-FW`、`NET-AZ-NSG`、`K8S-NETPOL`；只支持第二节所列命题，不为整条实施结果背书。

### §20 容量、调度与资源限制
<a id="CLD-BL-20"></a>

**稳定条款：** `CLD-BL-20`（保留 `§20`）。

**机制：** CPU/Memory Request、Limit、磁盘/IO、连接、队列和自动扩缩按实际峰值/成本优化；区分 OOM、调度失败和服务自身过载。

**验收：** 模拟峰值与 OOM，关键服务满足声明的容量边界，异常扩缩有停止或费用上限。

**主体、前置与输入：** 本条针对“容量、调度与资源限制”；执行者必须具有目标范围的实际权限，消费 `CLD-CAP-T5` 的固定输入：cpu.max/Memory/IO/PID/FD、Cloud Run service/revision max及连接池、Lambda并发类型。

**权威状态与输出：** 内核运行约束和Serverless真实实例/并发语义。输出本条验收的原始观察及 `CLD-CAP-T5` 产物：节流/OOM/磁盘/网络瓶颈与冷启动/上限实测，不以配置值冒称绝对费用硬限。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** Cloud Run max可短时超出；Lambda预置也有准备/重置及溢出；未知扩容先读实例而非重复申请。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，按项目资源阈值限制或隔离，关键服务不得被连带拖垮；本条具体可观察验收仍为“模拟峰值与 OOM，关键服务满足声明的容量边界，异常扩缩有停止或费用上限。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 工作负载没有资源上限导致节点持续 OOM。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 固定容量加有界接纳可满足目标，无需自动扩容。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-CAP-T5` ](#CLD-CAP-T5)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`KERNEL-CGROUP`、`CAP-CLOUDRUN`、`CAP-LAMBDA`；只支持第二节所列命题，不为整条实施结果背书。

### §21 CI 触发、权限及状态门禁
<a id="CLD-BL-21"></a>

**稳定条款：** `CLD-BL-21`（保留 `§21`）。

**机制：** 区分 PR 校验、受信发布、部署、手动重跑和定时任务；Job 与缓存来源、Actions 权限、并发互斥及目标环境必须正确绑定。

**验收：** PR 无法通过同名 Check/重跑伪造生产批准；必要 CI 未实际通过时阻止正式部署。

**主体、前置与输入：** 本条针对“CI 触发、权限及状态门禁”；执行者必须具有目标范围的实际权限，消费 `CLD-CI-T6` 的固定输入：needs/stage、矩阵必需性、Shell退出、Run Attempt、Concurrency/Resource Group及操作ID。

**权威状态与输出：** 必需DAG/Job结论、环境写入主权与目标操作账。输出本条验收的原始观察及 `CLD-CI-T6` 产物：必要失败阻断、同环境互斥、取消/重跑已发生效果核对。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** GitHub默认替换pending与queue:max按当前版；CI互斥不栅栏云端旧请求，Unknown先查询不盲重放。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，生产部署须绑定真正通过的受信检查与授权；本条具体可观察验收仍为“PR 无法通过同名 Check/重跑伪造生产批准；必要 CI 未实际通过时阻止正式部署。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 失败 PR 的检查被误判为正式发布成功。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 可选矩阵失败可不阻断，但不得抹去必需组合失败。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-CI-T6` ](#CLD-CI-T6)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`GH-CONCURRENCY`、`CI-RESOURCEGROUP`、`IAC-TF-LOCK`；只支持第二节所列命题，不为整条实施结果背书。

### §22 自托管 Runner 信任边界
<a id="CLD-BL-22"></a>

**稳定条款：** `CLD-BL-22`（保留 `§22`）。

**机制：** 持久 Runner、临时 JIT Runner、执行用户、注册 Token、共享工作目录及未受信代码执行面按真实风险隔离；临时注册不意味着复用宿主机安全。

**验收：** 恶意 PR 无法读到后继任务或生产凭据；Runner 释放后无可复用跨作业秘密。

**主体、前置与输入：** 本条针对“自托管 Runner 信任边界”；执行者必须具有目标范围的实际权限，消费 `CLD-CI-T3` 的固定输入：Runner ID/版本/OS、Label/Group、信任级、Socket/网络、JIT清理及工作目录。

**权威状态与输出：** 实际Runner宿主/Executor和Group允许来源，Label仅为选路。输出本条验收的原始观察及 `CLD-CI-T3` 产物：queued/实际执行/清洁完成分别记录，跨Job/跨租户负例拒绝。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** JIT注销不清宿主；清理或更新失败先隔离Runner；挂死/取消后核孤儿进程及凭据。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，隔离 Runner 和信任边界，后继作业不继承恶意状态；本条具体可观察验收仍为“恶意 PR 无法读到后继任务或生产凭据；Runner 释放后无可复用跨作业秘密。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 共享自托管 Runner 可被陌生 PR 持久化修改。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 单任务JIT运行在已清洁宿主才可重用硬件。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-CI-T3` ](#CLD-CI-T3)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`GH-SECURE`、`CI-GITLAB`、`CI-NIST204D`；只支持第二节所列命题，不为整条实施结果背书。

### §23 发布批次与兼容回退
<a id="CLD-BL-23"></a>

**稳定条款：** `CLD-BL-23`（保留 `§23`）。

**机制：** 区分发布制品、Schema/数据迁移、配置、Feature Flag、DNS/CDN 更新及客户端兼容窗口；Kubernetes Deployment 回滚不能撤回外部业务副作用。

**验收：** 旧新实例共存或失败回退时业务仍满足契约；不可逆数据迁移有独立恢复/补偿方案。

**主体、前置与输入：** 本条针对“发布批次与兼容回退”；执行者必须具有目标范围的实际权限，消费 `CLD-REL-T7` 的固定输入：Abort请求、可用旧Revision/Digest、数据Schema、在途连接/后台任务、业务副作用。

**权威状态与输出：** 当前真实流量/运行代码/持久状态与业务原始回执分别权威。输出本条验收的原始观察及 `CLD-REL-T7` 产物：实际冻结、独立流量/代码/数据恢复结果与再次放行证据。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 旧Revision可能GC；ECS无COMPLETED会stalled；未核旧请求/队列不能宣布全恢复；补偿是新授权操作。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**必要补充与不变量：** 分开记录新流量路由、实际运行代码、配置/Secret与持久数据四种恢复结果；一次控制面回退不把其他结果改为成功。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，回滚需独立验证 DB/客户端兼容或另行恢复；本条具体可观察验收仍为“旧新实例共存或失败回退时业务仍满足契约；不可逆数据迁移有独立恢复/补偿方案。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 旧镜像回滚却保留不兼容数据库结构。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 回退路由可独立完成，但数据修复仍保持未完成。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-REL-T7` ](#CLD-REL-T7)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`REL-ECS`、`REL-CLOUDRUN`、`REL-WORKERS`、`REC-PG`；只支持第二节所列命题，不为整条实施结果背书。

### §24 交付生效与流量验收
<a id="CLD-BL-24"></a>

**稳定条款：** `CLD-BL-24`（保留 `§24`）。

**机制：** 成功构建、推镜像、部署控制面接受、Pod Ready、真实入口可达、用户请求与业务履约必须分别验证；Readiness/Liveness/Startup 语义不能混淆。

**验收：** 通过外部真实入口及最小受控业务路径验证新版本，控制面成功但业务失败时不能结案。

**主体、前置与输入：** 本条针对“交付生效与流量验收”；执行者必须具有目标范围的实际权限，消费 `CLD-REL-T8` 的固定输入：版本/权重/时间/群组、低频任务、旧轨GC/账单、控制器失联与有权恢复路径。

**权威状态与输出：** 分阶段真实消费者、稳定观察窗、保留/成本与替代控制路径。输出本条验收的原始观察及 `CLD-REL-T8` 产物：用户群组业务结果、观察完成条件、旧资源清理及真实L5/L6结果。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 100%流量不结束低频观测；旧轨仅在恢复窗口结束后清理；失联冻结新变更不盲Promote。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，外部用户路径与业务结果不通过即阻止验收；本条具体可观察验收仍为“通过外部真实入口及最小受控业务路径验证新版本，控制面成功但业务失败时不能结案。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** Pod Ready 但真实域名返回错误租户数据。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 内部健康探针只声明其覆盖的内部路径，不冒称客户履约。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-REL-T8` ](#CLD-REL-T8)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`REL-K8S`、`REL-CLOUDRUN`、`COST-FOCUS`；只支持第二节所列命题，不为整条实施结果背书。

### §25 运行观察与业务指标
<a id="CLD-BL-25"></a>

**稳定条款：** `CLD-BL-25`（保留 `§25`）。

**机制：** 建立与关键服务关联的可用性、错误、延迟、资源和真实交付指标，明确采样、Trace/Metric/Log 版本和敏感字段范围；只监控确有价值的路径。

**验收：** 注入网络失败、资源耗尽和业务异常时能定位受影响服务，告警不泄漏 Token 或无关个人数据。

**主体、前置与输入：** 本条针对“运行观察与业务指标”；执行者必须具有目标范围的实际权限，消费 `CLD-OBS-T2` 的固定输入：OTLP版本/信号稳定度、批次拒收、队列/重试/磁盘、时间源、索引基数/采样。

**权威状态与输出：** 采集/Exporter/后端各跳确认与实际查询存储，不是stdout本身。输出本条验收的原始观察及 `CLD-OBS-T2` 产物：接收/拒收/丢数/可检索分层结果及有界成本。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** partial_success不整包重试；WAL也受磁盘与保留故障；缺Span不否定业务，跨主机时间不独证因果。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，观察点包含真实业务成功/失败，不以 CPU 空闲代替业务；本条具体可观察验收仍为“注入网络失败、资源耗尽和业务异常时能定位受影响服务，告警不泄漏 Token 或无关个人数据。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 服务指标看似正常但用户操作一直失败。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 低频服务可只保留有意义信号，但无数据不能虚构健康。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-OBS-T2` ](#CLD-OBS-T2)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`OTEL-OTLP`、`OTEL-COLLECTOR`、`OTEL-LOGS`；只支持第二节所列命题，不为整条实施结果背书。

### §26 告警处置与事故证据
<a id="CLD-BL-26"></a>

**稳定条款：** `CLD-BL-26`（保留 `§26`）。

**机制：** 区分告警触发、故障定位、恢复、客户通知、外部 SLA/合同责任及复盘；证据保留须按相应受众和权限控制。

**验收：** 模拟依赖超时和区域失败后能定位对象、影响和恢复步骤，不以告警静音等于恢复。

**主体、前置与输入：** 本条针对“告警处置与事故证据”；执行者必须具有目标范围的实际权限，消费 `CLD-OBS-T3` 的固定输入：指标窗/新鲜度/for、Missing策略、Silence/Inhibit、路由/失效接收端、独立故障域。

**权威状态与输出：** 规则求值、Alertmanager通知、实际接收/ACK分别权威。输出本条验收的原始观察及 `CLD-OBS-T3` 产物：告警状态、投递/接收/ACK与未确认升级各有回执。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** NoData不自动Healthy；静默只抑制通知，跨租户事故不能全局吞掉；迟到样本不授权当前修复。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，必须另行验证故障处置结果与受影响范围；本条具体可观察验收仍为“模拟依赖超时和区域失败后能定位对象、影响和恢复步骤，不以告警静音等于恢复。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 告警被关闭后事故未恢复却宣称服务正常。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 告警可限时静默，事故事实及影响仍保留。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-OBS-T3` ](#CLD-OBS-T3)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`OBS-ALERTMANAGER`、`OBS-CLOUDWATCH`、`OBS-PROMRULE`、`OBS-PROMTOOL`；只支持第二节所列命题，不为整条实施结果背书。

### §27 备份、恢复目标与演练
<a id="CLD-BL-27"></a>

**稳定条款：** `CLD-BL-27`（保留 `§27`）。

**机制：** 计算存储、配置、IaC State、Secrets、DNS/路由和数据库备份属于不同恢复资产；RPO/RTO 与加密密钥必须能在所选环境演练。

**验收：** 在隔离环境按清单恢复到声明窗口并重验权限、数据与入口；仅看到备份成功状态不通过。

**主体、前置与输入：** 本条针对“备份、恢复目标与演练”；执行者必须具有目标范围的实际权限，消费 `CLD-DR-T4` 的固定输入：IaC State/Provider、etcd版本/Key、CSI SnapshotHandle、Velero范围、Vault插件/解封、D1 bookmark。

**权威状态与输出：** 实际工具/Driver/目标Region及恢复引导材料。输出本条验收的原始观察及 `CLD-DR-T4` 产物：逐控制面/卷/数据库/秘密的实际恢复与代码-持久状态分离。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** Completed可跳过已有对象；Raft接受不等后台恢复完成；D1就地覆盖必须保护事故后写入，不把YAML复制当搬数据。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**必要补充与不变量：** 恢复闭包必须包含目标区可获得的材料、版本、网络、读取/解密/提升写主权限及可达信任根，不能只列资源名称。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，隔离恢复演练必须真实还原数据和访问权限；本条具体可观察验收仍为“在隔离环境按清单恢复到声明窗口并重验权限、数据与入口；仅看到备份成功状态不通过。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 备份文件存在但未含解密密钥导致无法恢复。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 低RTO要求以外可采用冷恢复，必须实测完整时间。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-DR-T4` ](#CLD-DR-T4)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`REC-ETCD`、`REC-CSI`、`REC-VELERO`、`REC-VAULT`、`REC-D1`；只支持第二节所列命题，不为整条实施结果背书。

### §28 依赖、故障域及降级路径
<a id="CLD-BL-28"></a>

**稳定条款：** `CLD-BL-28`（保留 `§28`）。

**机制：** 识别 DNS、CDN、外部网络、区域/可用区、KMS、仓库、构建平台和客户依赖的故障域，权衡单点、冗余和实际费用。

**验收：** 模拟最重要单点或区域故障时，按业务承诺进入明确降级、恢复或拒绝状态，不制造错误结果。

**主体、前置与输入：** 本条针对“依赖、故障域及降级路径”；执行者必须具有目标范围的实际权限，消费 `CLD-DR-T1` 的固定输入：业务恢复目标、持久/可重建资产、账户/KMS/DNS/第三方、故障假设和预算。

**权威状态与输出：** 已批准客户RPO/RTO与真实依赖/故障域，不是云区标签。输出本条验收的原始观察及 `CLD-DR-T1` 产物：技术恢复顺序、策略适用/缺口、完整RPO/RTO起止。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 依赖图既含材料又含权限/可达边；有节点无访问边不可恢复，原区故障不能仍依赖其唯一引导服务。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，按承诺执行降级/恢复，避免错误成功响应；本条具体可观察验收仍为“模拟最重要单点或区域故障时，按业务承诺进入明确降级、恢复或拒绝状态，不制造错误结果。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 单区域 DNS 或 KMS 故障让客户服务失效，超出已批准恢复/可用性承诺，或明知服务不可用却报告健康。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 已批准单点可接受明确停机，不虚称多区高可用。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-DR-T1` ](#CLD-DR-T1)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`REC-OBJECTIVES`、`REC-REGION`、`REC-VAULT`；只支持第二节所列命题，不为整条实施结果背书。

### §29 成本归属与资源清单
<a id="CLD-BL-29"></a>

**稳定条款：** `CLD-BL-29`（保留 `§29`）。

**机制：** 实例、磁盘、流量、存储版本、日志、CI Runner 和托管服务根据真实账单维度关联项目/环境与负责人；不为低价值项目强制 FinOps SaaS。

**验收：** 能够从资源清单定位异常收费项和责任主体，闲置/孤儿资源有可核实处置办法。

**主体、前置与输入：** 本条针对“成本归属与资源清单”；执行者必须具有目标范围的实际权限，消费 `CLD-COST-T1` 的固定输入：账号/Region/资源与无ID费用、SKU/Meter、共享/Idle、租户/发票主体和成功业务单位。

**权威状态与输出：** 供应商账单/实际资产与有权费用归属，不是标签自证。输出本条验收的原始观察及 `CLD-COST-T1` 产物：完整费用/Unallocated清单、隐私安全标签和可复核分母。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 父Compute消失不代附属资源/合同结束；标签滞后和失败业务成本不丢失；未知归属显式保留。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，计费资源必须有负责人及合理保留理由；本条具体可观察验收仍为“能够从资源清单定位异常收费项和责任主体，闲置/孤儿资源有可核实处置办法。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 停止的磁盘快照仍在计费却未被盘点。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 无Resource ID的用量可记为未分摊，不能从总额丢弃。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-COST-T1` ](#CLD-COST-T1)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`COST-FOCUS`、`COST-CUR`；只支持第二节所列命题，不为整条实施结果背书。

### §30 预算、上限与异常扩容
<a id="CLD-BL-30"></a>

**稳定条款：** `CLD-BL-30`（保留 `§30`）。

**机制：** 按现有收入和预算限制弹性资源、日志保留、第三方 API、构建并发、出口流量及临时资源生命周期；费用新增需实际有权人批准。

**验收：** 注入无限重试与增长流量时触发已声明的用量限幅与告警；若声明支出硬上界，则另验证实际执行范围、账单/在途延迟及预留裕量，普通告警不得充当硬停，未经批准不形成新增固定支出。

**主体、前置与输入：** 本条针对“预算、上限与异常扩容”；执行者必须具有目标范围的实际权限，消费 `CLD-COST-T3` 的固定输入：项目/期间/币种/SKU批准、AlertsOnly/Cap/Action范围、计费延迟、在途最坏用量与安全底线。

**权威状态与输出：** 真实预算授权与服务可执行限幅；邮件通知不是停费权威。输出本条验收的原始观察及 `CLD-COST-T3` 产物：告警投递/动作/实际拒新工作与剩余费用分别验证。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** Spend cap非即时且只限支持范围；预留在途/滞后/固定承诺，Unknown调用不退还预留后再次消费；不能为省费删唯一备份。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**必要补充与不变量：** 预算告警只是异步观测；服务级Spend cap也可能非即时且不覆盖所有SKU。严格预算须在业务接纳/资源申请前限幅，核在途、滞后、固定承诺与残留费用。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，超过额度触发明确定额、告警或批准条件；本条具体可观察验收仍为“注入无限重试与增长流量时触发已声明的用量限幅与告警；若声明支出硬上界，则另验证实际执行范围、账单/在途延迟及预留裕量，普通告警不得充当硬停，未经批准不形成新增固定支出。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 自动扩容不设预算让短时攻击产生高额账单。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 只有软告警的服务可使用预留裕量与本地用量限幅，不宣称绝对停费。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-COST-T3` ](#CLD-COST-T3)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`COST-CAP`、`COST-AWS-ACTION`、`COST-ALERT`；只支持第二节所列命题，不为整条实施结果背书。

### §31 退役、删除与历史依赖
<a id="CLD-BL-31"></a>

**稳定条款：** `CLD-BL-31`（保留 `§31`）。

**机制：** 服务退役时覆盖主机、快照、域名、证书、密钥、备份、自动化任务、监控、支付与数据保留义务；不能以关闭入口等同资源/数据清除。

**验收：** 退役复核能辨识合法保留和必须清理的各类资源，不破坏其他服务共享依赖。

**主体、前置与输入：** 本条针对“退役、删除与历史依赖”；执行者必须具有目标范围的实际权限，消费 `CLD-COST-T7` 的固定输入：保留期/LegalHold/WORM、旧Key/WAL、外部Webhook/DNS/身份、删除锁及长期合同。

**权威状态与输出：** 客户数据/恢复/合同处分权与真实服务生命周期、最终发票。输出本条验收的原始观察及 `CLD-COST-T7` 产物：有权退出/销毁与共享依赖保护；物理删除/撤读/最终结算独立结果。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 软删恢复窗不保证所有服务完整；解锁不产生销毁授权；项目关停仍可能滞后账单和长期费用，记结算待定。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，退役需同时处理对象、域名、密钥、历史副本和例外；本条具体可观察验收仍为“退役复核能辨识合法保留和必须清理的各类资源，不破坏其他服务共享依赖。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 删除应用入口后旧备份和 DNS 仍向外公开。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 合法保留的快照可以不删除，但剩余费用和访问权限独立登记。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-COST-T7` ](#CLD-COST-T7)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：`COST-AZ-LOCK`、`REC-OBJECT-LOCK`、`COST-DELETE`、`COST-FOCUS`；只支持第二节所列命题，不为整条实施结果背书。

### §32 L5/L6 独立适用和验收
<a id="CLD-BL-32"></a>

**稳定条款：** `CLD-BL-32`（保留 `§32`）。

**机制：** L4 仅确立跨平台运行工程条件，L5 决定真实云厂商、Kubernetes/Runner/OpenTofu 等版本和实现，L6 执行环境、客户权限、资金与业务验收。

**验收：** 每项生效门禁有真实项目的版本/角色/结果证据；单凭静态场景或 GitHub CI 不能认定生产业务完成。

**主体、前置与输入：** 本条针对“L5/L6 独立适用和验收”；执行者必须具有目标范围的实际权限，消费 `CLD-BL-T3` 的固定输入：实际项目适用矩阵、被选择L4条款、所消费L5供应商/引擎/Runner/IaC的准确版本与能力条件、L6授权范围、目标环境/数据/费用边界、每项真实验收的命令argv与预期产物。

**权威状态与输出：** 本仓已登记规范的准确版本/摘要与项目有权主体的适用决定、实际项目部署/工具/业务权威；静态基线和CI结果不产生生产采用或业务完成。输出本条验收的原始观察及 `CLD-BL-T3` 产物：每项门禁的文档/条款/版本/摘要—实际实现—角色—命令—目标结果证据闭环；独立登记文档状态、技术审查、项目采用和实现验收，未执行/未知/不适用项带具体理由。不能从期望配置/请求成功越级推断该输出。

**并发、超时、未知与恢复：** 规范/平台/项目版本变化先核依赖闭包与兼容迁移；真实结果未知时查询原操作权威，不能重跑副作用或把旧版本证据复制为新通过；回退须保留当前安全/撤权/数据与费用状态。记录本条对象版本与操作身份；冲突/部分成功/未观测项不并入成功，不以新请求覆盖原请求的未知结果。

**正例及判据：** 在上述明确目标/主体/版本和有效前置下，必须另行提供 L5 真实引擎及 L6 业务授权与结果；本条具体可观察验收仍为“每项生效门禁有真实项目的版本/角色/结果证据；单凭静态场景或 GitHub CI 不能认定生产业务完成。”。合法操作与应有拒绝均须由实际目标结果而非仅配置文本确认。

**直接失败：** 静态基线通过就宣称客户生产数据已全部验收。此时必须得到上述预期检查/失败诊断，不得登记本条整体通过。

**合法邻例与兼容：** 项目未采用某供应商不运行无关产品门禁，实际替代路径仍验。 与本条适用条件相容；不得为拒绝该合法情形而扩大外部规范或供应商限制。不同目标平台/版本的等效实现须保留同一输出不变量。

**真实检查入口：** 消费[ `CLD-BL-T3` ](#CLD-BL-T3)中的命令/API/项目入口，在同一隔离画像分别运行正例、上述失败输入和合法邻例；逐项比对本条验收，不以退出0单独替代资源、权限、业务或费用读回。有限来源命题：本条的L4/L5/L6采用接口为本仓工程要求，不主张外部厂商原文规定其采用流程；只支持第二节所列命题，不为整条实施结果背书。

**专属验收分界：** 实际项目仅激活已选择技术路径，逐项固定L5版本与L6目标证据；未跑产品门禁诚实登记not-run；直接失败：把本仓静态检查通过或无真实目标的CI成功写成生产客户业务通过，或同名新版本沿用旧摘要证据，判失败；合法邻例：未采用某供应商可不运行其专有门禁，但必须说明不适用条件并验证实际替代路径；不因没有无关供应商账号而拒绝项目。

## 四、42 项静态失败输入及预期检查

### 场景组 1：运行范围、权责与环境边界
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 公开静态页面被要求采购完整 Kubernetes 集群 | §01 | 可保留单站点/托管部署方案，不强制无关平台成本 |
| 云商管理控制台有权限便直接宣称能够处理客户数据 | §02 | 云商资源操作权限不能代替客户数据与合同授权 |
| 预发布配置默认指向生产密钥和真实用户通知地址 | §03 | 不同环境的凭据与通知目的端不得复用，跨环境外发被阻止 |
| 故障切换将受限数据复制到未获授权区域 | §04 | 跨区域复制应受法域、合同和真实出入口条件限制 |

### 场景组 2：身份、权限与秘密生命周期
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 应用部署角色意外持有全账号删除与计费权限 | §05 | 不在职责范围内的高权限操作应拒绝 |
| 来自任意分支的 OIDC 身份取得生产部署令牌 | §06 | Federation 信任策略必须限制正确仓库、分支/环境和 Audience |
| Kubernetes Secret 明文暴露在 CI 日志且长期不轮换 | §07 | 低权不能从日志重放秘密，轮换后旧 Token 不可继续使用 |
| Agent 为修复错误直接解锁他人的 IaC State | §08 | 操作因非持有者及缺少批准而拒绝并保留在途状态 |

### 场景组 3：源码、构建与制品来源
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 相同 Docker tag 在两次构建中指向不同镜像，发布记录却未核对各自真实 Digest 而仍将两者视为同一已批准制品 | §09 | 必须检测 Digest 漂移并标明真实提交和构建输入 |
| 外部 PR 可在持久 Runner 读取上次生产任务残留 | §10 | 不可信执行无法访问跨作业目录和生产秘密 |
| 依赖管理只固定顶层版本而基础镜像可无声更新 | §11 | 能从锁定和摘要找出被替换依赖并拒绝未经审批制品 |
| 存在来源声明但实际部署镜像摘要与其主体不符 | §12 | 发布门禁验证 Digest、Attestation 和有效签发主体 |

### 场景组 4：基础设施声明与状态演进
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| IaC Plan 预期仅改测试网络却包含生产网关删除 | §13 | 未经授权的目标资源变更应阻断 |
| State 锁获取失败后操作员直接 force-unlock | §14 | 仍有合法执行者时不得并行写入 State 或静默解锁 |
| 生产安全组已被手动改宽但仓库 Plan 未检查 | §15 | 发现实际对象与声明漂移并在 Apply 前处理 |
| 一条批量 Terraform Apply 包含不可逆密钥销毁，未识别该副作用或未取得绑定准确目标与计划的有权批准便执行 | §16 | 必须提前分类和批准不可逆动作；未完成分类或有效批准不得执行，批准后的受控自动化不因此被禁止 |

### 场景组 5：计算、容器与网络运行
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 镜像可拉取但实际架构与节点 CPU 不匹配 | §17 | 运行前拒绝不兼容镜像和挂载 |
| 容器默认特权运行并挂载宿主机秘密目录 | §18 | 普通容器不得读取宿主机未授权路径和凭据 |
| 提交了 NetworkPolicy 但当前 CNI 不实施策略 | §19 | 测试仍可访问隔离 Pod 时必须判定策略无效 |
| 工作负载没有资源上限导致节点持续 OOM | §20 | 按项目资源阈值限制或隔离，关键服务不得被连带拖垮 |

### 场景组 6：CI/CD 发布与版本回退
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 失败 PR 的检查被误判为正式发布成功 | §21 | 生产部署须绑定真正通过的受信检查与授权 |
| 共享自托管 Runner 可被陌生 PR 持久化修改 | §22 | 隔离 Runner 和信任边界，后继作业不继承恶意状态 |
| 旧镜像回滚却保留不兼容数据库结构 | §23 | 回滚需独立验证 DB/客户端兼容或另行恢复 |
| Pod Ready 但真实域名返回错误租户数据 | §24 | 外部用户路径与业务结果不通过即阻止验收 |

### 场景组 7：可观测、故障恢复与持续运营
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 服务指标看似正常但用户操作一直失败 | §25 | 观察点包含真实业务成功/失败，不以 CPU 空闲代替业务 |
| 告警被关闭后事故未恢复却宣称服务正常 | §26 | 必须另行验证故障处置结果与受影响范围 |
| 备份文件存在但未含解密密钥导致无法恢复 | §27 | 隔离恢复演练必须真实还原数据和访问权限 |
| 单区域 DNS 或 KMS 故障让客户服务失效，超出已批准恢复/可用性承诺，或明知服务不可用却报告健康 | §28 | 按承诺执行降级/恢复，避免错误成功响应 |

### 场景组 8：成本、资源生命周期与项目验收
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 停止的磁盘快照仍在计费却未被盘点 | §29 | 计费资源必须有负责人及合理保留理由 |
| 自动扩容不设预算让短时攻击产生高额账单 | §30 | 超过额度触发明确定额、告警或批准条件 |
| 删除应用入口后旧备份和 DNS 仍向外公开 | §31 | 退役需同时处理对象、域名、密钥、历史副本和例外 |
| 静态基线通过就宣称客户生产数据已全部验收 | §32 | 必须另行提供 L5 真实引擎及 L6 业务授权与结果 |

### 场景组 9：跨环境、供应链、状态与运行组合故障
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| 未知 PR 在复用 Runner 上植入凭据并触发 OIDC 生产部署 | §06、§10、§21、§22 | 双重校验执行来源、Runner 环境和云端信任条件 |
| 镜像 tag 被替换而 OCI Digest 与 SLSA Provenance 未核对 | §09、§11、§12、§17 | 锁定源版本、制品摘要及平台类型 |
| IaC State 锁丢失、人工漂移与生产资源销毁并发 | §13、§14、§15、§16 | 并发写入阻断、漂移确认与不可逆审批 |
| 发布旧版应用同时不可逆收缩 Schema 后发生故障 | §16、§23、§24 | 回退能力与数据库兼容性独立验证 |
| 业务读取跨境备份而灾备路由未审权利 | §02、§04、§27 | 故障切换与法域/合同/数据持有权限一并核查 |

### 场景组 10：容器、可用性、费用与退役组合故障
| 失败输入 | 关联机制 | 项目级预期检查 |
| --- | --- | --- |
| NetworkPolicy 不被 CNI 支持且容器拥有宿主高权限 | §17、§18、§19 | 实际网络隔离、运行权限和主机访问实测 |
| 自动扩缩与无限日志重试使预算用尽、重要服务被停止 | §20、§29、§30 | 资源容量、账单和重试上限联合验证 |
| 健康检查成功、关键业务失败却自动宣称恢复 | §24、§25、§26 | 入口、业务结果与故障恢复各自验收 |
| 加密密钥意外轮换而 PITR 备份未同步导致灾备不可恢复 | §07、§27、§28 | 密钥保留、恢复链和故障域联合演练 |
| 正式服务退役但历史快照、域名、凭据仍可由第三方使用 | §04、§07、§27、§31 | 来源授权、历史副本、出口和退役完整性 |

## 五、真实目标工具/API与验收产物合同

以下为按实际采用组件选择的目标入口，不是要求安装全部平台。命令中的变量必须在L5绑定为非秘密的确定对象ID与隔离测试资源，API名必须补齐所选SDK/CLI版本、完整参数及超时。项目专有入口须固定仓库路径、参数、数据夹具与预期退出/响应；缺少此绑定不得判该目标验收通过。Shell命令、HTTP/API名和故障注入动作分别标识，不将自然语言API列表当可直接复制的单条命令。

每个执行产物包括工具版本、目标账户/Region/集群/运行实例、实际Principal、输入/制品摘要、操作/请求ID、起止时点、退出/HTTP状态、资源/数据读回和覆盖边界。对每条至少保留正例/直接失败/合法邻例，不适用需给出不存在相应能力/承诺的理由。

### CLD-COST-T1
<a id="CLD-COST-T1"></a>

**权威与主体：** 供应商账单/实际资产与有权费用归属，不是标签自证。

**固定输入：** 账号/Region/资源与无ID费用、SKU/Meter、共享/Idle、租户/发票主体和成功业务单位。

**实际入口：** AWS CUR2/账单导出或Azure/GCP实际费用明细；云实际资产列表；按ResourceID/SKU/账期关联，缺ID保Unallocated。

**必须产物/观察：** 完整费用/Unallocated清单、隐私安全标签和可复核分母。

**故障恢复：** 父Compute消失不代附属资源/合同结束；标签滞后和失败业务成本不丢失；未知归属显式保留。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAM-T1
<a id="CLD-IAM-T1"></a>

**权威与主体：** 云账户/目录与实际资源访问控制面；批准者与执行Principal分别记录。

**固定输入：** 当前账户/项目不可变ID、父级、Region、实际Principal、目标资源及合同作用域。

**实际入口：** aws sts get-caller-identity；gcloud projects describe "$PROJECT" --format=json；az account show --output json。

**必须产物/观察：** 主体-动作-资源-环境矩阵与实况清单；标签不产生有效权限。

**故障恢复：** 改名/删除重建/迁层级先重算绑定；换票或API超时不推定已授权，读回实际Principal及继承后再恢复。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-NET-T1
<a id="CLD-NET-T1"></a>

**权威与主体：** 实际云网络/路由器与权威DNS；网络编辑者不拥有业务数据权。

**固定输入：** IPv4/IPv6源/目标、VPC/VNet/Region、接口、路由表、NAT/代理、允许接收方。

**实际入口：** ip route get "$IP"；dig "$FQDN" A；dig "$FQDN" AAAA；curl --fail-with-body --connect-timeout 5 --max-time 15 "$TEST_URL"；云有效路由API。

**必须产物/观察：** 选定源的实际下一跳/出口及可达性；环境和地址身份可追踪。

**故障恢复：** 更具体路由、NAT复用或路径失联时逐跳分层；未知路由不以临时全开放恢复。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAM-T2
<a id="CLD-IAM-T2"></a>

**权威与主体：** 选用供应商的策略求值器与目标服务资源策略，而不是本地集合模型。

**固定输入：** 身份/资源Policy、SCP/RCP、Boundary、Session、GCP Deny、Azure全部Role/Deny及Principal种类。

**实际入口：** aws iam simulate-principal-policy --policy-source-arn "$ROLE_ARN" --action-names s3:GetObject --resource-arns "$OBJECT_ARN"；az role assignment list --scope "$SCOPE" --include-inherited --output json；代表性S3 GetObject/Blob数据面隔离请求。

**必须产物/观察：** 正向最小访问成功、跨资源/显式拒绝失败；策略求值过程和产品例外。

**故障恢复：** 策略传播中保持旧/新结果与时点；单侧模拟不确定先停高影响操作，读取实际服务拒绝/允许后确认。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAM-T4
<a id="CLD-IAM-T4"></a>

**权威与主体：** 按实际机制分别由AWS认证主体和Role Trust、外部IdP与云端联合信任、GCP调用方/服务账号权限、或Azure已分配身份与Entra决定会话；目标服务另决定资源动作。

**固定输入：** 机制分支、目标资源/只读动作、策略修订和期限；AWS认证分支为源Principal、RoleArn、RoleSessionName及适用ExternalId/MFA/会话策略；OIDC分支为Issuer/Audience/Subject、签名键/算法和Trust；GCP另固定Provider/subjectTokenType及适用SA/Scope/委派链；Azure托管身份为宿主、身份选择器和目标resource。

**实际入口：** 按[身份目标画像](../../../examples/cloud_contracts/target_profiles.md#identity)选择AWS AssumeRole或WebIdentity、GCP STS交换或GenerateAccessToken、Azure VM IMDS Token及实际只读资源请求；az identity show只查配置；GitHub仅在受权工作流内取得来源Token。

**必须产物/观察：** 脱敏的实际源/会话/目标身份、期限、请求ID、交换和资源调用的分别结果；非OIDC分支不伪填Issuer/JWKS，错误Principal/适用ExternalId或OIDC发行者/受众不得取得越权结果。

**故障恢复：** 固定机制、Trust/Mapping/身份分配修订和期限；超时先核原交换/会话及操作身份，冲突或未知不借新Token重放业务副作用。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-SEC-T5
<a id="CLD-SEC-T5"></a>

**逐条失败与邻例判据：**
- `CLD-SEC-27`：失败条件为“单用户轮换造成服务失联，却没有满足约定可用性窗口的受控切换或恢复设计，或尚未恢复便报告切换完成”；邻例为“按实际后端与已批准可用性合同，可在有界停机窗口内受控轮换并如实记录恢复中；不强制双账号，也不假定单账号轮换必然断开既有连接。”

**逐条失败与邻例判据：**
- `CLD-SEC-25`：失败条件为“GCP SECRET_ROTATE 仅发送通知，数据库密码及消费者尚未变更却已登记轮换完成”；邻例为“轮换通知可以是合法起点，订阅者后续处理仍待完成；不得据通知签收目标密码已改。”
- `CLD-SEC-26`：失败条件为“AWSPENDING 已创建但目标服务未设置并验证新值，平台却提前提升 CURRENT 或报告目标轮换完成”；邻例为“准备阶段可先创建AWSPENDING而目标尚未改变，准确登记候选状态；成功后的AWSPENDING与AWSCURRENT也可指同一版本，标签本身不证后端完成。”
- `CLD-SEC-28`：失败条件为“轮换时半数实例仍用旧认证，另一半已用新值，平台却宣称全量消费者已完成轮换”；邻例为“声明过渡期内可并存两个未泄露值并准确登记未完成，但旧值退出期限和消费者确认必须成立；泄露值不得为等全量收敛而复活。”
- `CLD-SEC-30`：失败条件为“旧 API Key 在新版启用后仍能调用生产接口，但轮换任务已被关闭，或已超过固定的旧值撤权期限仍未阻断”；邻例为“旧连接可在已声明且获准的非泄露过渡窗口内保留会话，真实失效尚未完成时任务保持未完成；按目标认证/撤销机制核对截止。”

**权威与主体：** 源数据库/API认证服务与Store Stage、消费者共同定义轮换完成。

**固定输入：** 轮换事件/ClientRequestToken、候选版本、同一目标资源、测试与CURRENT、旧值退出。

**实际入口：** aws secretsmanager describe-secret --secret-id "$SECRET"；源数据库用受控service/passfile执行SELECT 1；GCP Pub/Sub SECRET_ROTATE处理后查询版本元数据/目标认证；旧新会话对照。

**必须产物/观察：** 准备/set/test/finish与实际失效分步结果；全消费者新值正例。

**故障恢复：** 重复通知按同一操作账恢复；未知set先查询目标；未泄露旧值可依批准回退，泄露值绝不可复活。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAM-T3
<a id="CLD-IAM-T3"></a>

**逐条失败与邻例判据：**
- `CLD-IAM-18`：失败条件为“用户已从目录删除，超过按实际服务能力和项目承诺固定的撤权截止后，旧 STS/客户端仍可写生产资源”；邻例为“撤权截止前仍有效的旧会话须如实报告为传播中，不能提前报告撤权完成；停止目录身份后保留只读历史审计不代表会话仍可调用。”

**权威与主体：** 真实身份源与每次已签发会话；目录移除与目标授权各自权威。

**固定输入：** 组/嵌套组、认证强度、临时角色起止、应急身份、委派来源。

**实际入口：** az role assignment list --assignee "$PRINCIPAL_ID" --all --output json；目标服务同一只读/写入隔离对象用旧新会话在窗口前后对照；保留HTTP状态与审计请求ID不保留Token。

**必须产物/观察：** 高风险当前会话正例、普通/过期会话拒绝及实际撤权窗口。

**故障恢复：** 目录更新、Token缓存、下游委派并发时逐入口回读；不刷新为匿名管理员，不复活失效主体。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-SUP-T2
<a id="CLD-SUP-T2"></a>

**逐条失败与邻例判据：**
- `CLD-BL-09`：失败条件为“相同 Docker tag 在两次构建中指向不同镜像，发布记录却未核对各自真实 Digest 而仍将两者视为同一已批准制品”；邻例为“一个源码提交可产生多个合法平台制品，逐个摘要分别记录；可变频道 Tag 合法移到新内容时仍保留每份 Digest、来源和批准范围。”
- `CLD-SUP-09`：失败条件为“源码标签一致但 CI 缓存不同产出两个 Wheel，发布记录未分别保存实际摘要和材料却将其标为同一制品”；邻例为“同一源码可有合法不同编译配置产物，须分别追踪。”

**权威与主体：** 实际分发字节、发布清单与目标OS/ABI，而非Git Tag或CI名。

**固定输入：** 全文件集合、算法/字节范围、源码/构建配置、多架构Index及重打包身份。

**实际入口：** sha256sum发行文件；OCI Manifest/Index读取；每声明平台真实安装/启动/ABI关键路径；独立重建后逐字节比较。

**必须产物/观察：** 逐文件/平台摘要、可重现性范围与派生制品新身份。

**故障恢复：** 相同源码可多产物；单文件变化不能沿用旧签名，重建差异保持真实不夸SLSA等级。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-CI-T3
<a id="CLD-CI-T3"></a>

**权威与主体：** 实际Runner宿主/Executor和Group允许来源，Label仅为选路。

**固定输入：** Runner ID/版本/OS、Label/Group、信任级、Socket/网络、JIT清理及工作目录。

**实际入口：** GitHub API 读取runner元数据与Job runner_id；宿主docker info/进程UID/工作区残留检查；GitLab Runner对应Executor隔离样本。

**必须产物/观察：** queued/实际执行/清洁完成分别记录，跨Job/跨租户负例拒绝。

**故障恢复：** JIT注销不清宿主；清理或更新失败先隔离Runner；挂死/取消后核孤儿进程及凭据。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-SUP-T1
<a id="CLD-SUP-T1"></a>

**权威与主体：** 实际依赖解析器/受信源与构建材料清单；名称不是内容身份。

**固定输入：** 直接/传递/可选依赖锁、包源/子模块Ref、基础Manifest、下载摘要及平台条件。

**实际入口：** 项目真实包管理器frozen/locked安装入口；sha256sum材料；docker buildx imagetools inspect "$IMAGE"；受控错误源/依赖替换对照。

**必须产物/观察：** 解析后输入闭包与单字节/依赖混淆替换拒绝。

**故障恢复：** 上游Tag/分支/包响应变化需重绑受审输入；缓存只能加速，不把未核来源产物提升。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-SUP-T5
<a id="CLD-SUP-T5"></a>

**权威与主体：** 预设可信signer-builder与实际Subject/Predicate签名内容。

**固定输入：** in-toto Type URI、Subject Digest、DSSE原始payload/type、BuildDefinition/RunDetails与Track/Level。

**实际入口：** cosign verify-attestation --certificate-identity "$IDENTITY" --certificate-oidc-issuer "$ISSUER" "$IMAGE_DIGEST"并核允许PredicateType；离线解析DSSE PAE/Statement；核Builder运行身份与SLSA要求清单。

**必须产物/观察：** 字节/类型/Builder来源绑定及每个选定等级完整要求证据。

**故障恢复：** keyid未认证；Proof可来自错误Run/Subject，缺任何必需证据不补造；取消构建不代表签发未发生。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAC-T1
<a id="CLD-IAC-T1"></a>

**权威与主体：** 云Resource ID与唯一声明/State负责人；工作区名字不产生权限。

**固定输入：** 源提交、目标账号/Region、Provider Alias、Workspace/Stack/Backend与生命周期批准。

**实际入口：** terraform version；terraform workspace show；terraform providers；terraform state list；云Describe目标ID。

**必须产物/观察：** 对象ID/地址/受权范围映射，跨环境拒绝及预览影响。

**故障恢复：** 同名/重建/迁区必须重绑；未知实际归属先回读，不从空State推断云对象不存在。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAC-T4
<a id="CLD-IAC-T4"></a>

**权威与主体：** State锁Backend及覆盖全部写入口的交接门；云对象仍有实际执行权威。

**固定输入：** Lock ID/Key/持有Run、当前State、旧执行进程、恢复批准、Provider请求ID。

**实际入口：** 两独立进程terraform plan -lock-timeout=5s -out="$PLAN"与terraform apply -lock-timeout=5s "$PLAN"（隔离资源）；terraform force-unlock "$LOCK_ID"仅经门禁；terraform state pull；云Describe请求/资源ID。

**必须产物/观察：** 同State最多一有效写者，遗留锁受控解锁、局部创建纳管结果。

**故障恢复：** 超时不证旧持有者已停；force-unlock是工具动作非活跃检测；先冻结/终止或栅栏旧写者，再核资源/State后重新规划。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAC-T8
<a id="CLD-IAC-T8"></a>

**权威与主体：** 云实况与受权声明差异，State维护和最终费用/资源Owner。

**固定输入：** 支持资源/显式属性、Nested Stack、手工变更、当前State、孤儿资源和账单。

**实际入口：** aws cloudformation detect-stack-drift --stack-name "$STACK"后以返回DetectionId调用DescribeStackDriftDetectionStatus（检测本身须获准）；aws cloudformation describe-stack-resource-drifts --stack-name "$STACK"；terraform plan -refresh-only；pulumi refresh --preview-only --diff；pulumi preview --diff；云资源及Billing读回。

**必须产物/观察：** 漂移覆盖/NOT_CHECKED、状态修复审计、纳管/退役交接。

**故障恢复：** 只读采集不偷写State；IN_SYNC不证全覆盖；Pulumi refresh不改源码，下一up可能改回；遗留计费不结零账。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-IAC-T7
<a id="CLD-IAC-T7"></a>

**逐条失败与邻例判据：**
- `CLD-BL-16`：失败条件为“一条批量 Terraform Apply 包含不可逆密钥销毁，未识别该副作用或未取得绑定准确目标与计划的有权批准便执行”；邻例为“已识别且得到覆盖准确目标、计划及数据保护条件的有权批准时，可按受控方案执行不可逆变更；可重建无状态实例也可受控替换，不强求数据回滚。”
- `CLD-IAC-39`：失败条件为“云服务创建 API 仅返回已受理且端点尚不可用，平台却据此报告业务部署成功”；邻例为“Provider返回异步任务ID可签收请求已受理，资源可用与用户路径仍待独立读回。”

**权威与主体：** 执行API/异步任务与当前有效资源；批准绑定当前确定目标。

**固定输入：** Plan/State身份、当前权限、变更窗口、异步任务ID、重试/失败模式及业务不可逆性。

**实际入口：** terraform apply "$PLAN"（隔离受权变更）；aws cloudformation describe-stacks --stack-name "$STACK"；aws cloudformation describe-stack-events --stack-name "$STACK"；Provider返回任务查询；必要入口只读验证。

**必须产物/观察：** 已接受/执行中/局部成功/完成/Unknown与实际资源状态分离。

**故障恢复：** State未变不排除外部漂移；异步超时先查询；保留成功资源与回滚模式按产品核，不重放未知创建。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-ISO-T2
<a id="CLD-ISO-T2"></a>

**权威与主体：** OCI目标Manifest/Bundle及实际CRI/Runtime/Kernel ABI。

**固定输入：** Index/平台Digest、config.json、RootFS、Handler、PID1/入口和OS/ABI画像。

**实际入口：** docker inspect "$CONTAINER"；crictl inspect "$CID"；runc state "$ID"；受控SIGTERM/崩溃后检查ExitCode及子进程；Windows docker inspect --format "{{.HostConfig.Isolation}}" "$CID"。

**必须产物/观察：** 真实目标启动与关键系统调用/信号/退出结果，不只拉取成功。

**故障恢复：** Bundle或Handler不支持时明确拒绝；启动超时核真实进程/端口及容器ID，不重叠启动未知实例。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-ISO-T3
<a id="CLD-ISO-T3"></a>

**权威与主体：** 运行进程实际UID映射/Namespace/Capability/no_new_privs及宿主Socket权限。

**固定输入：** Pod/Container最终SecurityContext、uid_map/gid_map、PID/IPC/Network共享、必要能力。

**实际入口：** docker inspect "$CID"；受权宿主读取/proc/$PID/{uid_map,gid_map,status,ns/*}元数据；kubectl get pod -n "$NS" "$POD" -o json；最小权限测试负载。

**必须产物/观察：** 允许业务成功而越权Host/跨租户操作被内核/Runtime拒绝。

**故障恢复：** Pod与Container覆盖、Daemon Rootless与Remap分别核；撤能力后旧进程状态重新观察，不以新YAML代表旧进程。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-NET-T2
<a id="CLD-NET-T2"></a>

**权威与主体：** 真正关联的SG/NACL/NSG/层级Firewall和具策略能力的CNI数据面。

**固定输入：** 规则版本/优先级/方向、ENI/NIC/Subnet关联、Pod选择器、CNI及既有连接。

**实际入口：** aws ec2 describe-security-groups --group-ids "$SG"；aws ec2 describe-network-acls --network-acl-ids "$ACL"；az network nic list-effective-nsg --ids "$NIC_ID"；kubectl get networkpolicy -n "$NS" -o json；从受权与无权源分别TCP/HTTP探测。

**必须产物/观察：** 获准新流成功、跨租户/出口新流拒绝；旧流撤断与策略传播单列。

**故障恢复：** Policy API成功不证数据面；传播空窗与hostNetwork/既有连接按实现测，无法确定先隔离高影响路径。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-CAP-T5
<a id="CLD-CAP-T5"></a>

**权威与主体：** 内核运行约束和Serverless真实实例/并发语义。

**固定输入：** cpu.max/Memory/IO/PID/FD、Cloud Run service/revision max及连接池、Lambda并发类型。

**实际入口：** cgroup cpu.stat/memory.events；kubectl describe pod "$POD" -n "$NS"；kubectl describe node "$NODE"；gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format=json；aws lambda get-function-concurrency --function-name "$FUNCTION"；aws lambda get-provisioned-concurrency-config --function-name "$FUNCTION" --qualifier "$QUALIFIER"。

**必须产物/观察：** 节流/OOM/磁盘/网络瓶颈与冷启动/上限实测，不以配置值冒称绝对费用硬限。

**故障恢复：** Cloud Run max可短时超出；Lambda预置也有准备/重置及溢出；未知扩容先读实例而非重复申请。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-CI-T6
<a id="CLD-CI-T6"></a>

**权威与主体：** 必需DAG/Job结论、环境写入主权与目标操作账。

**固定输入：** needs/stage、矩阵必需性、Shell退出、Run Attempt、Concurrency/Resource Group及操作ID。

**实际入口：** GitHub API Jobs/Check与Concurrency配置读回；GitLab Resource Group API；两隔离发布Run并发/取消后核目标版本与State锁；失败命令退出码对照。

**必须产物/观察：** 必要失败阻断、同环境互斥、取消/重跑已发生效果核对。

**故障恢复：** GitHub默认替换pending与queue:max按当前版；CI互斥不栅栏云端旧请求，Unknown先查询不盲重放。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-REL-T7
<a id="CLD-REL-T7"></a>

**权威与主体：** 当前真实流量/运行代码/持久状态与业务原始回执分别权威。

**固定输入：** Abort请求、可用旧Revision/Digest、数据Schema、在途连接/后台任务、业务副作用。

**实际入口：** kubectl argo rollouts abort "$ROLLOUT" -n "$NS"；kubectl argo rollouts status "$ROLLOUT" -n "$NS" --timeout=120s；需要回退时由当前批准调用undo "$ROLLOUT"；Cloud Run traffic/Workers Deployment读回；ECS DescribeServices；外部受控入口及业务账本/队列水位核对。

**必须产物/观察：** 实际冻结、独立流量/代码/数据恢复结果与再次放行证据。

**故障恢复：** 旧Revision可能GC；ECS无COMPLETED会stalled；未核旧请求/队列不能宣布全恢复；补偿是新授权操作。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-REL-T8
<a id="CLD-REL-T8"></a>

**权威与主体：** 分阶段真实消费者、稳定观察窗、保留/成本与替代控制路径。

**固定输入：** 版本/权重/时间/群组、低频任务、旧轨GC/账单、控制器失联与有权恢复路径。

**实际入口：** 实际入口带版本标识请求；kubectl/平台Revision与控制事件；指标按群组/窗口查询；资源/计费清理读回。

**必须产物/观察：** 用户群组业务结果、观察完成条件、旧资源清理及真实L5/L6结果。

**故障恢复：** 100%流量不结束低频观测；旧轨仅在恢复窗口结束后清理；失联冻结新变更不盲Promote。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-OBS-T2
<a id="CLD-OBS-T2"></a>

**权威与主体：** 采集/Exporter/后端各跳确认与实际查询存储，不是stdout本身。

**固定输入：** OTLP版本/信号稳定度、批次拒收、队列/重试/磁盘、时间源、索引基数/采样。

**实际入口：** OTLP Export受控返回partial_success/429/503；Collector内部queue/dropped指标与后端查询；合成高基数/时钟偏移/重启样本。

**必须产物/观察：** 接收/拒收/丢数/可检索分层结果及有界成本。

**故障恢复：** partial_success不整包重试；WAL也受磁盘与保留故障；缺Span不否定业务，跨主机时间不独证因果。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-OBS-T3
<a id="CLD-OBS-T3"></a>

**逐条失败与邻例判据：**
- `CLD-OBS-16`：失败条件为“Alertmanager Silence 抑制数据库通知后，客户仍无法登录，但系统删除事故事实或将事故登记已解决”；邻例为“限时Silence可暂停通知，同时保留来源、截止和仍在处理的客户事故；静默不删除告警与事故事实。”

**权威与主体：** 规则求值、Alertmanager通知、实际接收/ACK分别权威。

**固定输入：** 指标窗/新鲜度/for、Missing策略、Silence/Inhibit、路由/失效接收端、独立故障域。

**实际入口：** promtool check rules "$RULES"；amtool check-config "$AM_CONFIG"；Alertmanager /api/v2/alerts和/silences；CloudWatch DescribeAlarms；隔离通知接收端ACK记录。

**必须产物/观察：** 告警状态、投递/接收/ACK与未确认升级各有回执。

**故障恢复：** NoData不自动Healthy；静默只抑制通知，跨租户事故不能全局吞掉；迟到样本不授权当前修复。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-DR-T4
<a id="CLD-DR-T4"></a>

**权威与主体：** 实际工具/Driver/目标Region及恢复引导材料。

**固定输入：** IaC State/Provider、etcd版本/Key、CSI SnapshotHandle、Velero范围、Vault插件/解封、D1 bookmark。

**实际入口：** etcdutl snapshot status "$SNAP" -w table；隔离目标etcdutl snapshot restore "$SNAP" --bump-revision "$BUMP" --mark-compacted --data-dir "$RESTORE_DIR"（按实际Watch与Revision差距选BUMP）；kubectl get volumesnapshot,volumesnapshotcontent -A -o json；velero restore describe "$RESTORE" --details及restore logs；vault status；wrangler d1 time-travel info "$DATABASE"（读取目标Bookmark）。

**必须产物/观察：** 逐控制面/卷/数据库/秘密的实际恢复与代码-持久状态分离。

**故障恢复：** Completed可跳过已有对象；Raft接受不等后台恢复完成；D1就地覆盖必须保护事故后写入，不把YAML复制当搬数据。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-DR-T1
<a id="CLD-DR-T1"></a>

**逐条失败与邻例判据：**
- `CLD-BL-28`：失败条件为“单区域 DNS 或 KMS 故障让客户服务失效，超出已批准恢复/可用性承诺，或明知服务不可用却报告健康”；邻例为“已批准单点可接受明确停机，不虚称多区高可用。”

**权威与主体：** 已批准客户RPO/RTO与真实依赖/故障域，不是云区标签。

**固定输入：** 业务恢复目标、持久/可重建资产、账户/KMS/DNS/第三方、故障假设和预算。

**实际入口：** 云资源/备份/密钥/权限只读清单与依赖图；隔离按完整恢复顺序计时；外部业务可用点作为结束，不只命令耗时。

**必须产物/观察：** 技术恢复顺序、策略适用/缺口、完整RPO/RTO起止。

**故障恢复：** 依赖图既含材料又含权限/可达边；有节点无访问边不可恢复，原区故障不能仍依赖其唯一引导服务。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-COST-T3
<a id="CLD-COST-T3"></a>

**权威与主体：** 真实预算授权与服务可执行限幅；邮件通知不是停费权威。

**固定输入：** 项目/期间/币种/SKU批准、AlertsOnly/Cap/Action范围、计费延迟、在途最坏用量与安全底线。

**实际入口：** AWS Budgets DescribeBudget/DescribeBudgetActionsForBudget及Action执行状态；GCP Budgets Spend cap控制台/API元数据；Azure预算ActionGroup与隔离用量限幅/真实账单对照。

**必须产物/观察：** 告警投递/动作/实际拒新工作与剩余费用分别验证。

**故障恢复：** Spend cap非即时且只限支持范围；预留在途/滞后/固定承诺，Unknown调用不退还预留后再次消费；不能为省费删唯一备份。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-COST-T7
<a id="CLD-COST-T7"></a>

**逐条失败与邻例判据：**
- `CLD-COST-39`：失败条件为“前端已停用但旧Webhook仍接收付费回调，项目却宣称所有外部入口已下线，或该回调缺少当前有权归属与授权”；邻例为“服务前端停用后，Webhook可在明确迁移期由当前有权Owner处理获准回调并保留必要凭据；外部集成未结束时不宣称全部下线。”

**权威与主体：** 客户数据/恢复/合同处分权与真实服务生命周期、最终发票。

**固定输入：** 保留期/LegalHold/WORM、旧Key/WAL、外部Webhook/DNS/身份、删除锁及长期合同。

**实际入口：** Azure Lock读回；云对象/备份/Key/外部回调/DNS清单；GCP项目lifecycleState；供应商最终Invoice/长期承诺/席位结清对照。

**必须产物/观察：** 有权退出/销毁与共享依赖保护；物理删除/撤读/最终结算独立结果。

**故障恢复：** 软删恢复窗不保证所有服务完整；解锁不产生销毁授权；项目关停仍可能滞后账单和长期费用，记结算待定。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-COST-T8
<a id="CLD-COST-T8"></a>

**权威与主体：** 同负载同口径优化证据、安全/恢复底线与真实客户结果。

**固定输入：** 优化前后版本/币种/账期、季节负载、停机/错目标/并发恢复、替代平台合同。

**实际入口：** 固定账期费用/单位成本对照；隔离成本保护误目标/取消/恢复样本；真实替代平台入口/版本/数据与账单核对。

**必须产物/观察：** 实际费用收敛、可逆故障回归、未破SLO/RPO/认证与客户验收。

**故障恢复：** 对象删除但账单未最终出可只记技术退役；未清持续收费不结案；迁移后仍核真实入口/协议/Key。

**通过/失败判据：** 本组中每个条款的验收逐项满足，直接失败得到拒绝/诊断/正确恢复、合法邻例不被误拒；任何Unknown、未覆盖平台/权限或关键产物缺失分别保留，不允许从组内其他成功项外推。退出0、Accepted、配置已保存只证明其各自层次。

### CLD-BL-T1
<a id="CLD-BL-T1"></a>

**权威与主体：** 有权服务负责人确认的业务负载/数据权利/可用性与恢复目标，实际运行时与资产清单；费用权威仅负责费用，不代替平台选择决定。

**固定输入：** 固定业务画像、峰值/持续负载、延迟/可用性/恢复目标、数据处理允许范围、维护能力、当前部署及成本上限；每个组件关联所需能力，包含不采用某组件的理由。

**实际入口：** 按实际平台选择只读资产入口：aws resourcegroupstaggingapi get-resources --region "$REGION"（仅可标记资源，不声称完整资产）；gcloud asset search-all-resources --scope="projects/$PROJECT_NUMBER"；az resource list --subscription "$SUBSCRIPTION_ID" --output json；本地 uname -a。随后执行选定项目画像中固定argv的代表负载/恢复探针；HTTP隔离健康探针可用 curl --fail --max-time 10 "$HEALTH_URL"，但不能替代完整负载/恢复测试。人工逐项比对上述映射、测得结果和冗余移除回归。

**必须产物/观察：** 组件—业务能力—负载—权限—成本—恢复映射、候选运行方式的取舍、代表负载原始结果和移除冗余组件后的回归；不得因未采购Kubernetes/多云而失败。

**故障恢复：** 负载/权利/目标变化时重新评估受影响组件；比较期间固定版本与负载，单次探针超时保留未知；移除失败先恢复已验证配置和数据，再依据业务探针确认恢复，不能仅重启进程结案。

**成功场景：** 单机或托管静态站点在固定负载与恢复目标下满足输出且成本可解释，允许保留简单架构。

**直接失败判据：** 没有业务能力或负载依据，单因平台偏好强制购买完整集群，或用健康HTTP200代替恢复测试，判失败。

**相邻合法例：** 业务实际需要集群的隔离/调度能力且存在负载与恢复证据时，允许采用集群；简单架构优先不等于禁止复杂架构。

**验收与版本条件：** 固定实际服务/实现/合同版本并逐项核对；记录检查与人工演练、真实基础设施、真实业务分别登记，未知和缺证据不填通过。不同平台的等效路径须保持本组输出与失败边界。

### CLD-BL-T2
<a id="CLD-BL-T2"></a>

**权威与主体：** 具体服务/版本的责任说明与实际有效合同、有权数据决定者、真实账户主体及服务责任矩阵；本工具或IAM标签不产生合同或数据处理权限。

**固定输入：** 固定服务类型与所用功能、合同/责任说明的标识和有效范围、实际开发者/平台/托管商/域名证书方/运行Agent/客户/发布者及可兼任职责；云商故障、客户数据请求、Agent高风险动作三个事件画像。

**实际入口：** AWS身份可执行 aws sts get-caller-identity；Azure可执行 az account show --output json；读取所选服务官方责任说明及既有合同标识。由具备相应权限的参与者对三个固定事件做隔离桌面演练，逐项记录处理/批准/验证和拒绝边界；这是责任与权限人工验收，账户API退出0不能替代演练或专业法律判断。

**必须产物/观察：** 三事件各自的处理者、授权者、执行Principal、验证者、升级渠道/时限与证据出处；区分基础设施恢复、客户数据决定和对外承诺，缺失真实负责人不得以虚构审批者填补。

**故障恢复：** 服务或合同版本变化先复核职责分界；角色兼任可保留但每项实际权限仍核实；责任争议/未知授权期间只执行已允许的保全动作并升级有权主体，不借平台管理员身份处理客户数据。

**成功场景：** 平台方处理其基础设施故障，应用方对其客户数据和应用配置承担明确职责，Agent只在当前委派范围执行。

**直接失败判据：** 仅凭云控制台Owner权限便批准客户数据新用途，或将云商负责硬件扩张成供应商承担所有业务故障，判失败。

**相邻合法例：** 单人真实主体兼任开发/发布/运维可接受，只要其对每项动作确有权限且责任/验证路径明确，不强制虚构多人审批。

**验收与版本条件：** 固定实际服务/实现/合同版本并逐项核对；记录检查与人工演练、真实基础设施、真实业务分别登记，未知和缺证据不填通过。不同平台的等效路径须保持本组输出与失败边界。

### CLD-BL-T3
<a id="CLD-BL-T3"></a>

**权威与主体：** 本仓已登记规范的准确版本/摘要与项目有权主体的适用决定、实际项目部署/工具/业务权威；静态基线和CI结果不产生生产采用或业务完成。

**固定输入：** 实际项目适用矩阵、被选择L4条款、所消费L5供应商/引擎/Runner/IaC的准确版本与能力条件、L6授权范围、目标环境/数据/费用边界、每项真实验收的命令argv与预期产物。

**实际入口：** python -B checks/project_adoption.py --record "$PROJECT_ADOPTION_RECORD" 校验本仓格式、精确文档及依赖一致性；随后按记录中的每项check.command在已授权隔离目标执行并保存原始命令、版本、退出码和权威查询。记录检查不认证真实身份或批准权限，真实项目有权主体与技术审查者分别核验授权和逐项结果。

**必须产物/观察：** 每项门禁的文档/条款/版本/摘要—实际实现—角色—命令—目标结果证据闭环；独立登记文档状态、技术审查、项目采用和实现验收，未执行/未知/不适用项带具体理由。

**故障恢复：** 规范/平台/项目版本变化先核依赖闭包与兼容迁移；真实结果未知时查询原操作权威，不能重跑副作用或把旧版本证据复制为新通过；回退须保留当前安全/撤权/数据与费用状态。

**成功场景：** 实际项目仅激活已选择技术路径，逐项固定L5版本与L6目标证据；未跑产品门禁诚实登记not-run。

**直接失败判据：** 把本仓静态检查通过或无真实目标的CI成功写成生产客户业务通过，或同名新版本沿用旧摘要证据，判失败。

**相邻合法例：** 未采用某供应商可不运行其专有门禁，但必须说明不适用条件并验证实际替代路径；不因没有无关供应商账号而拒绝项目。

**验收与版本条件：** 固定实际服务/实现/合同版本并逐项核对；记录检查与人工演练、真实基础设施、真实业务分别登记，未知和缺证据不填通过。不同平台的等效路径须保持本组输出与失败边界。

## 六、跨域消费接口

**L3提供方：** [通用工程规范 v0.1.0](../../L3/001-通用工程规范--v0.1.0.md)，消费 `CE-01`、`CE-03`、`CE-09`、`CE-13`、`CE-14`、`CE-15`、`CE-16`、`CE-19`、`CE-20`、`CE-21` 的输入/权威状态、变化失效及可观察证据合同。L5把这些共性合同实例化到本专题的实际工具入口，不另造已生效或已验收推定。

**云专题接口：** 本基线将各条的真实目标合同绑定到上列独立云专题；各专题提供相应实际资源/主体/版本、输入输出、未知恢复和合法邻例。

**应用/数据/身份/协议消费：** 资源或发布动作涉及业务提交、对象授权、持久恢复、交易/补偿或消息水位时，必须消费对应L4提供方的明确提交点/操作查询、唯一写主、真实耐久、授权传播和保留合同；提供方正文、稳定定位、摘要及消费关系见[跨域接口登记](../../../registry/cloud-interfaces.json)。不得因基础设施成功重写这些权威业务事实。

**向L5/L6交付：** 输出适用矩阵、实际资源/主体/版本与命令绑定、各条正反/邻例结果、未执行/未知/不适用项及原因、保留原失败的修复回归、恢复和费用清单。技术实施、生产变更权、客户数据/合同、费用与业务结果各自验收；规范批准不产生这些权限，也不替代真实目标证据。
