# 云身份、审计、发布与挂载目标画像

本指南实例化云领域的T4/T8及发布、IaC、挂载验收接口。它不另建规范权威；要求仍按准确采用的条款解释。目标账户、工具/SDK版本、只读测试对象、执行者、费用及允许副作用由项目画像固定。云命令只有在相应真实目标已具备权限时执行；离线HCL及Linux名字空间实验不能证明云端权限、真实事故或Kubernetes运行时已经通过。

<a id="identity"></a>
## 1. 身份交换按机制选择输入

每次验证先固定：`mechanism`、源身份、目标账户/Region/租户、资源/动作、配置修订、操作ID、期限及一个允许和一个应拒绝的只读目标。选择下列实际分支，不要求所有分支同时存在。

| 分支 | 必须固定的输入与权威 | 实际API/动作 | 必须观察与失败/合法邻例 |
|---|---|---|---|
| AWS已认证主体的`AssumeRole` | 源AWS Principal及其实际认证会话、RoleArn、RoleSessionName、角色Trust和调用方授权；ExternalId、MFA、SourceIdentity、Tags及会话策略仅按实际信任条件选择 | 用受信SDK作SigV4签名调用STS`AssumeRole`；请求含RoleArn/RoleSessionName及已选条件。将临时凭据只交给内存中的目标SDK会话，执行固定只读请求 | 保留AssumedRoleUser、Expiration、RequestId及目标请求结果，不记录凭据。错误Principal或不满足已要求ExternalId/MFA时必须拒绝。合法非OIDC主体不需Issuer/JWKS；取得STS会话但被资源策略拒绝是合法邻例，不算目标动作通过 |
| AWS `AssumeRoleWithWebIdentity`，选用OIDC | 支持的IdP、精确RoleArn/RoleSessionName、Token来源、Issuer/Audience/Subject、签名键/算法、期限、角色Trust条件及可选会话策略 | STS`AssumeRoleWithWebIdentity`携带WebIdentityToken；该分支不要求先有AWS凭据。Token只在受权流程内存中使用 | 核Provider/Audience/Subject与AssumedRoleUser/期限；错误发行者、受众、过期或不允许Subject须被实际STS/目标拒绝。JWT解码成功不证明签名/信任通过。API支持的非OIDC提供者使用其ProviderId/Token合同，不伪填OIDC字段 |
| GCP Workload Identity Federation | 精确Pool/Provider、属性映射/条件、目标资源、`subjectTokenType`及其机制来源 | `POST https://sts.googleapis.com/v1/token`，固定grantType、audience、scope、requestedTokenType、subjectToken和subjectTokenType；此STS请求不发送Authorization头 | OIDC分支消费Issuer/JWKS/Audience/Subject和期限；SAML消费所选Provider的签名证书/断言/受众；AWS凭据分支消费签名的GetCallerIdentity令牌及AWS账户/ARN映射，不要求OIDC发行者。错误Provider/属性/受众应拒；合法直接访问可不经过服务账号冒用 |
| GCP服务账号冒用 | 已认证源身份、准确服务账号`projects/-/serviceAccounts/{EMAIL_OR_ID}`、`iam.serviceAccounts.getAccessToken`权限、scope、lifetime；存在委派链时逐跳角色授权 | `POST https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{EMAIL_OR_ID}:generateAccessToken`，body为scope及适用delegates/lifetime；再以返回Token调用固定资源 | 核expireTime、目标服务账号与目标资源结果。无冒用权或错目标应拒；直接请求不强加delegates，也不强加外部OIDC/JWKS。源身份来自WIF时，先分别保存交换与冒用的关联 |
| Azure VM Managed Identity | 已启用并分配身份的具体VM、系统分配或用户分配身份、目标resource及RBAC/资源权限；多用户分配身份明确选择client_id/object_id/msi_res_id之一 | VM内向`http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource={ENCODED_RESOURCE}`作GET，`Metadata: true`，必要时加身份选择器；Token只在内存传给目标SDK | 核resource、expires_on、身份绑定与只读资源结果。未分配身份、错误选择器或目标授权拒绝不能算通过。`az identity show`仅查配置，不取得Token也不证明访问；同一VM中可取得已分配身份的代码共享此资源边界，不假定进程间秘密隔离 |
| GitHub OIDC作为来源 | 准确仓库/工作流/事件/Ref/Environment、调用权限、请求Audience、可信JWT字段与云端Trust修订 | 仅由具备相应权限的受权工作流取得Token，再进入实际AWS/GCP/Azure联合身份分支 | 分别核可信来源、云端交换和资源拒绝。Fork/错误Ref或Audience不得因能解码JWT而获权；合法可信工作流不需要长期云密钥 |

### 请求与恢复记录

1. 对照已选API逐字段核请求；SDK认证来源和角色Trust是不同对象。只保存必要不可重放的身份/会话关联、摘要、操作ID和错误分类。
2. 对允许源执行固定只读请求；再分别换成错误Principal、错误ExternalId或错误OIDC受众等**适用于该分支**的失败输入。非OIDC分支没有Issuer不是失败。
3. 取得会话但目标资源拒绝时，记录“交换成功、资源调用拒绝”，不可聚合成全部成功。时效或Trust修订变化使旧观察失效。
4. 换票响应丢失时按实际审计/会话范围核事实；不能把取得新Token当成原业务动作没有发生。业务动作若非只读，另消费操作查询、幂等与未知结果合同。

官方定位：[AWS AssumeRole](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)、[WebIdentity](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html)、[GCP STS请求](https://docs.cloud.google.com/iam/docs/reference/sts/rest/v1/TopLevel/token)、[AWS/Azure来源分支](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-other-clouds)、[GenerateAccessToken](https://docs.cloud.google.com/iam/docs/reference/credentials/rest/v1/projects.serviceAccounts/generateAccessToken)、[Azure VM Token接口](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token)。这些来源支持各自产品接口，不规定所有云采用同一种身份机制。

<a id="audit"></a>
## 2. 管理操作与数据访问使用不同审计源

查询前形成覆盖记录：操作类别及API名、账户/Region/租户/资源、身份链/请求ID、时间窗、采集器与选择器修订、实际启用时间、目标日志库/表、保留期限、投递延迟、读取权限和分页完成状态。当前已启用不证明历史已经采集；空查询结果不单独证明访问未发生。

| 分支 | 前置和实际入口 | 判据 |
|---|---|---|
| AWS管理/Insights | `CloudTrail LookupEvents`仅支持所选Region最近90天的管理事件及已启用的Insights；固定StartTime/EndTime及受支持LookupAttribute，遍历NextToken且保持相同参数 | 在覆盖时间内关联角色/会话及事件。超过保留期、错Region、未启用Insights或未遍历分页分别记录缺口，不用它查S3 GetObject数据事件 |
| AWS数据事件，如S3 GetObject | 事件发生时已有适用Trail或Event Data Store，选择器包含相应资源/API/读事件，日志仍保留且可读。先核`GetEventSelectors`/适用高级选择器和投递配置历史；Trail日志可从已授权S3日志位置读其`Records`，或使用项目已配置且有预算的查询入口 | 关联eventTime、eventSource/eventName、userIdentity、requestID、resources/对象范围、result/error；记录事件时间与投递时间区别。Data Events默认不采集，启用/查询可能计费，新增配置不能补回过去未采集的事件 |
| Azure控制面 | `az monitor activity-log list --resource-id "$RESOURCE_ID" --start-time "$FROM" --end-time "$TO" --output json`；核订阅/CorrelationId/保留范围，默认保留90天 | 能核资源创建、权限策略修改等管理操作；不能证明Key Vault SecretGet或数据库请求。该日志不典型记录读取，不将管理事件缺失推广为所有操作未发生 |
| Azure资源数据面，如SecretGet | 事件发生时已有正确Diagnostic Setting、AuditEvent类别及目的地；核资源/配置历史、保留和采集延迟。使用实际已选Log Analytics表或Storage/Event Hub接收方，不假定所有目的地都有相同表 | 资源特定表AZKVAuditLogs按TimeGenerated/_ResourceId/OperationName及CorrelationId、Identity、ResultType等实际字段关联；legacy AzureDiagnostics按其实际Schema映射。无采集/已过期须记录无法恢复的历史缺口，不能用Activity Log替代 |
| GCP | 按实际服务/操作核Admin Activity、Data Access、System Event或Policy Denied；明确logName、resource、protoPayload.methodName、身份、时间窗和目标Bucket/View权限 | Admin Activity持续产生；Data Access除BigQuery外通常须显式启用，还须核服务支持、排除/路由、保留与读取权限。不能把所有云数据读取都当同一种事件或都默认可见 |

对已经采用AZKVAuditLogs目的地的Key Vault，以下是可绑定的KQL形状；先把四个值固定到已授权画像，并核实际SDK/CLI查询权限。它不创建日志库、启用采集或授予访问。

```kusto
AZKVAuditLogs
| where TimeGenerated between (datetime(2026-01-01T00:00:00Z) .. datetime(2026-01-01T00:05:00Z))
| where _ResourceId =~ "/subscriptions/SYNTHETIC/resourceGroups/Fixture/providers/Microsoft.KeyVault/vaults/Fixture"
| where OperationName == "SecretGet"
| project TimeGenerated, OperationName, CorrelationId, Identity, ResultType, RequestUri
```

正常场景：在有授权且采集已覆盖的隔离目标进行一次只读数据请求，以客户端请求ID/身份链和相应数据日志双向关联。失败场景：同一数据请求只查询管理日志，必须报告所选日志类别不能回答该问题；或者事件发生时未启用数据采集，报告历史证据缺口。合法邻例：仅核一次受支持管理操作时可用管理日志，无需为此强制购买数据日志。查询失败、延迟、权限不足和缺少采集保持Unknown；已证实无采集的过去窗口不能因未来启用而改成已验证。

官方定位：[LookupEvents](https://docs.aws.amazon.com/awscloudtrail/latest/APIReference/API_LookupEvents.html)、[CloudTrail数据事件](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html)、[Trail日志格式](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-examples.html)、[Azure Activity Log](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/activity-log)、[Key Vault日志](https://learn.microsoft.com/en-us/azure/key-vault/general/logging)、[AZKVAuditLogs字段](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/azkvauditlogs)、[GCP审计类型](https://cloud.google.com/logging/docs/audit)。

<a id="initial-release"></a>
## 3. 首发与升级的恢复目标

| 模式 | 准入输入 | 失败后的具体目标与观察 |
|---|---|---|
| 已有服务升级 | 精确旧稳定Code/Config/Secret/Schema/流量元组、保留制品、兼容窗口、已验证回退或前向恢复步骤，以及新候选和阶段批准 | 停止继续放量；条件化撤销未结束Promote，回读路由和在途消费者；按兼容策略恢复旧元组或批准的前向修复。数据与外部效果仍独立对账，旧代码健康不证明它们恢复 |
| 首次上线 | `initial`模式、准确候选及首次资源清单、已知未部署/无流量或安全停服基线、依赖/监控/绝对阈值、可撤入口、在途请求与数据/外部效果处理人；不能虚造旧稳定版本 | 撤新路由并确认不再接新流量，停止/排空新工作负载和消费者，逐操作查询在途副作用；只回收确认由本次创建且无保留/共享依赖的新资源。已有数据、外部交易、日志与恢复材料不得随“首发失败”删除。该结果称撤回/停服，不称回退到不存在的旧版本 |

首发没有旧稳定样本时，不伪造A/B比较；使用预先固定的绝对SLO/安全/兼容判据和足够样本。确需比较但无有效基线时结果为Inconclusive并暂停，不填零或放宽阈值。正常首发、首发失败撤路由/停新工作负载、升级失败恢复旧版本及未知外部效果分别产生版本/路由、资源所有权和副作用回执。停止发布任务本身不是远端发布已撤销。

<a id="ignore-changes"></a>
## 4. 合法ignore_changes与独立安全判据

Terraform的`ignore_changes = all`是合法特殊值，影响更新计划，不保证隐藏所有已知状态；裸`*`是无效配置，不能用它的语法失败证明漂移控制。允许其他控制器管理某一属性时，只忽略约定属性，仍从实际刷新/资源读回核安全约束。

可在全新临时目录、Terraform 1.17.0及仅内置provider画像下使用以下无云资源配置。它演示Core对已知本地状态的更新规划；实际安全组还需所选provider及隔离账户读回。

```hcl
terraform { required_version = "= 1.17.0" }
resource "terraform_data" "example" {
  input = { cidr = "10.0.0.0/24", tags = { owner = "service" } }
  lifecycle { ignore_changes = [input.tags] }
}
```

```sh
terraform init -backend=false -input=false
terraform validate -json
terraform plan -refresh=false -out=local.tfplan
terraform show -json local.tfplan
```

[完整Core实验](terraform_ignore_probe.py)固定官方Terraform 1.17.0 linux_amd64的可执行摘要，使用仅内置terraform_data的已审本地计划，分别注入合成标签/CIDR状态并读取完整show-json；它不执行云provider刷新。将对应官方工具路径和全新仓库外输出目录传入：`python -B examples/cloud_contracts/terraform_ignore_probe.py --terraform /path/to/terraform --output /tmp/StandardsTerraformIgnoreResult`。工具归档与发布SHA256由[官方1.17.0目录](https://releases.hashicorp.com/terraform/1.17.0/)核对；不把本例平台/版本限制推广为通用规范。

语义失败输入必须是**合法**`all`配置、危险CIDR已经进入已知刷新/读回、独立安全门禁却只检查“没有更新动作”便放行。它应被CIDR/授权策略拒绝；不能说所有输出都不可见。合法邻例是已批准的标签共管变更，`[input.tags]`可不给标签更新，危险CIDR仍触发更新或独立安全拒绝。语法失败、Core计划、实际provider刷新和真实安全策略验收分别记录。[官方lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle#ignore_changes)说明`all`和属性地址的准确含义。

<a id="propagation"></a>
## 5. 挂载事件方向不同于共享文件写入

在项目已授权的隔离Linux目标内，固定Volume类型、Runtime/内核、源挂载、传播标志及两个名字空间。使用`findmnt -R -o TARGET,PROPAGATION`读取实际挂载表，分别从模拟宿主和容器侧创建/卸载一次测试子挂载，再检查对侧的**挂载点**；不要用同一文件内容的可见性冒称挂载传播。

| 所选方向 | 接收来源挂载事件 | 容器产生挂载事件向来源回传 | 普通共享可写文件 |
|---|---|---|---|
| None/rprivate | 否 | 否 | 仍受同一底层文件和RW权限影响 |
| HostToContainer/rslave | 是；也可收到同源其他Bidirectional发布者的事件 | 否 | 同左，不由传播方向单独禁止 |
| Bidirectional/rshared | 是 | 是 | 同左；向外传播必须另有明确权限与隔离 |

实际Runtime可能对不适用rprivate的场景采取其已文档化回退，必须核实而不是只看Pod声明。`None`也不等于文件只读；`HostToContainer`接收传播不等于它能向宿主回传。按[官方Mount propagation](https://kubernetes.io/docs/concepts/storage/volumes/#mount-propagation)核特定Volume和Runtime支持，Kubernetes的Bidirectional另有特权和终止清理要求。

本仓[Linux名字空间实验](mount_direction_probe.py)只在新建非特权user/mount名字空间内创建tmpfs/bind，比较三种方向和普通文件写入。以新目录保存stdout/stderr/命令及结果：

```sh
python -B examples/cloud_contracts/mount_direction_probe.py --output /tmp/StandardsMountDirectionResult
```

目录已存在时拒绝覆盖。没有unshare/mount能力、权限不足或运行失败保留原错误，不退回真实宿主或降低安全设置；该实验不认证Kubernetes/CSI或真实宿主隔离。目标验收仍须在所选Runtime核传播方向、允许的共享写入、不相关宿主/租户拒绝及异常终止后清理。
