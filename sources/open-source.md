# 开源项目与公共生态来源

下表固定来源版本、章节、支持命题及适用条件。滚动资料采用记录日期为2026-10-23。

| ID | 发布者、准确身份与入口 | 引用章节/技术命题 | 不支持的结论 |
| --- | --- | --- | --- |
| O01 | SemVer；[Semantic Versioning2.0.0](https://semver.org/spec/v2.0.0.html) | Specification条款1/3—11；声明公共API；同发行版本内容不可改；兼容/破坏按所选SemVer规则编号，build metadata不排序。 | 只约束明确采用者，不证明实际兼容或强制所有项目采用。 |
| O02 | SLSA/The Linux Foundation；[SLSA v1.2 approved；Build Provenance predicate v1](https://slsa.dev/spec/v1.2/build-provenance) | Model/Parsing rules；verifying-artifacts行58—61/103—133；证明绑定subject、builder与构建输入；一般未知扩展字段忽略，而非预期externalParameters按验证期望处置；依赖枚举不保证闭包。 | 存在证明/签名不证明等级；本包不执行真签名、SLSA等级评估或完整依赖验证。 |
| O03 | SPDX/The Linux Foundation；[SPDX Specification2.3.1；语法字段SPDX-2.3](https://spdx.github.io/spdx-spec/v2.3.1/) | §6.1/6.5、§7.2/7.5/7.7/7.13—15、§11.1；document行6—27/144—157；package行40—54/160—170/714—848；relationships行6—18/65—73；文档版本/namespace、元素身份和关系应准确；NOASSERTION与NONE有不同语义，不可自动互换。 | 只读表列部分，不声明全SPDX语义/许可法律结论或完整SBOM符合。 |
| O04 | The Linux Foundation；[Developer Certificate of Origin1.1](https://developercertificate.org/) | (a)—(d)，页面行11—33；DCO列贡献来源/提交权和公开记录的自述条件；它不是提交签名自动证明所有材料权利。 | 不复制/改写证书，不强制所有项目采用，也不作法律充足性判断。 |
| S4 | NIST；[SP800-218 SSDF v1.1 final，2022-02](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf) | 表1 PW.1.1/1.2，印刷p11；RV.1.1—1.3/RV.2.2，p16—18；PDF页19/24—26；风险建模/决定记录、可信漏洞报告调查及风险处置/修复沟通是SSDF所列活动。 | 指南活动不是全法域义务，不强制企业PSIRT；不证明真实补丁或下游已采用。 |

## 组织合成与适用边界

对应规范将状态、不变量、故障恢复和验收场景作为项目工程要求，条款中说明其适用条件、观察对象和来源接口。

