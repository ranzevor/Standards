# 安全工程与身份系统来源

下表固定来源版本、章节、支持命题及适用条件。滚动资料采用记录日期为2026-10-23；具体项目选择对应保证级别和实现版本。

| ID | 发布者、准确身份与入口 | 引用章节/技术命题 | 不支持的结论 |
| --- | --- | --- | --- |
| S1 | OWASP；[Threat Modeling；2026-10-23所见动态社区方法页](https://community.owasp.org/Threat_Modeling) | Overview、Objectives、Across the Lifecycle；页面行19—46；模型可记录对象、假设、威胁、措施与验证，并随变化更新。 | 方法参考，不强制STRIDE或统一模板，不证明控制有效。 |
| S2 | NIST；[SP800-63B-4 final，2025-07；在线正文所见时间2025-08-26](https://pages.nist.gov/800-63-4/sp800-63b.html) | §3.1.1.2、§3.2.2、§4.1/4.2/4.6、§5；正文行248—257/451—463；events行7—16/67—85/109—152；session行55—57；采用相应要求时遵守口令最小长度/完整验证、认证器作用域失败上限及禁用再绑定；绑定/恢复按所选保证，IdP/RP会话各自管理。 | 不是全AAL符合声明；不覆盖所有认证器、同步fabric/生物识别或真实验证器。 |
| S3 | NIST；[SP800-63C-4 final，2025-07](https://pages.nist.gov/800-63-4/sp800-63c.html) | §3.13 Assertion Protection/§4.9 Assertion Contents；RP验证预期IdP、签名、时效、受众、适用nonce与重放；subject处于issuer命名空间。 | 认证/联合断言不等于资源授权；不声明完整FAL符合。 |
| S4 | NIST；[SP800-218 SSDF v1.1 final，2022-02](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf) | 表1 PW.1.1/1.2，印刷p11；RV.1.1—1.3/RV.2.2，p16—18；PDF页19/24—26；风险建模/决定记录、可信漏洞报告调查及风险处置/修复沟通是SSDF所列活动。 | 指南活动不是全法域义务，不强制企业PSIRT；不证明真实补丁或下游已采用。 |
| S5 | IETF；[RFC9700，BCP240，2025-01](https://www.rfc-editor.org/rfc/rfc9700.html) | §2.1.1、§2.2.2；§4.14；采用该BCP的公有授权码客户端使用PKCE；公有客户端刷新令牌须发送者约束或轮换。 | 不强制未采用OAuth项目使用OAuth，不证明业务批准或对象权限。 |
| S6 | NIST；[SP800-61r3 final，2025-04](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf) | §3 CSF Profile；RS.AN-06/07，印刷p29；RC.RP-03/05，p34；PDF页36/41；调查动作/记录及事件材料来源完整性应保护；恢复前检查恢复资产，恢复后核状态。 | 风险管理建议，不凭本指南授予事件处置权限或保证取证法律效力。 |
| S7 | OWASP；[ASVS5.0.0，2025-05-30稳定版](https://asvs.owasp.org/) | Overview/ASVS5.0.0/How To Reference；ASVS定位为Web应用/服务验证框架；引用编号应带准确版本。 | 用于定位框架与版本；具体控制按采用的ASVS版本逐项选择。 |
| S8 | IETF；[RFC9325，BCP195，2022-11](https://www.rfc-editor.org/rfc/rfc9325.html) | §3.1.1、§4.1、§7.1；行165—190/297—315及Hostname Validation；采用该BCP时不能协商废弃SSL/TLS版本；TLS支持/套件/验证条件按原文，不自定较弱最低值。 | 非未来协议通用结论，不证明某端实际配置/协商。 |
| S9 | IETF；[RFC5116，Standards Track，2008-01](https://www.rfc-editor.org/rfc/rfc5116.txt) | §2.1/2.2、§3.1/3.3；对使用非空nonce的相应算法同密钥调用保持nonce唯一；AEAD输出明文或失败，AAD拼接需无二义。 | 不是抗重放或访问控制协议；不将零长nonce接口选项误用于AES-GCM。 |
| S10 | OpenSSL；[openssl-s_client，3.5版本文档](https://docs.openssl.org/3.5/man1/openssl-s_client/) | SYNOPSIS；-verify_return_error，行183/287—292/700；s_client默认可在验证错误后继续；验收命令需显式使验证错误失败并核目标名称。 | 命令文档不证明本机已安装该版或目标TLS已验。 |

## 组织合成与适用边界

对应规范将状态、不变量、故障恢复和验收场景作为项目工程要求，条款中说明其适用条件、观察对象和来源接口。

## 规范接口别名

以下别名关联现行v0.1.0规范。文档的稳定标识、路径与摘要见[规范登记](../registry/standards.json)，跨域提供与消费条件见[必要技术接口](../registry/technical-dependencies.json)。

| 别名 | v0.1.0 规范 |
| --- | --- |
| G0 | [001-体系架构与规范编制准则--v0.1.0.md](../standards/L0/001-体系架构与规范编制准则--v0.1.0.md) |
| G1 | [001-全局治理补充规范--v0.1.0.md](../standards/L1/001-全局治理补充规范--v0.1.0.md) |
| G2 | [001-人类与-Agent-团队组织协作规范--v0.1.0.md](../standards/L2/001-人类与-Agent-团队组织协作规范--v0.1.0.md) |
| G3 | [001-通用工程规范--v0.1.0.md](../standards/L3/001-通用工程规范--v0.1.0.md) |
| B | [009-服务身份、对象授权与-API-安全技术规范--v0.1.0.md](../standards/L4/backend/009-服务身份、对象授权与-API-安全技术规范--v0.1.0.md) |
| W | [008-浏览器身份与应用安全技术规范--v0.1.0.md](../standards/L4/web/008-浏览器身份与应用安全技术规范--v0.1.0.md) |
| C | [005-云账户、身份与资源授权技术规范--v0.1.0.md](../standards/L4/cloud/005-云账户、身份与资源授权技术规范--v0.1.0.md) |
| K | [013-配置、秘密管理与密钥生命周期技术规范--v0.1.0.md](../standards/L4/cloud/013-配置、秘密管理与密钥生命周期技术规范--v0.1.0.md) |
| SUP | [011-软件供应链、制品身份与发行技术规范--v0.1.0.md](../standards/L4/cloud/011-软件供应链、制品身份与发行技术规范--v0.1.0.md) |
| R | [012-运行观察、事件响应与自动恢复技术规范--v0.1.0.md](../standards/L4/cloud/012-运行观察、事件响应与自动恢复技术规范--v0.1.0.md) |
| D | [011-数据安全、访问控制、保留与导出技术规范--v0.1.0.md](../standards/L4/database/011-数据安全、访问控制、保留与导出技术规范--v0.1.0.md) |
| RES | [007-研究安全、隐私与模型材料风险技术规范--v0.1.0.md](../standards/L4/model-research/007-研究安全、隐私与模型材料风险技术规范--v0.1.0.md) |
