# 共性编制、治理与协作来源

引用日期：2026-10-23。下表记录通用治理规范引用的来源及其支持命题。

| 来源ID | 发布者、准确对象与性质 | 实读章节与支持命题 | 不支持的推论 |
| --- | --- | --- | --- |
| CG-01 | IETF，[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html)，1997，BCP 14 | §1–6：区分必要、建议、可选；强制要求需有互操作或避免危害等理由 | 不规定中文词汇、不决定本体系采用权，也不要求所有工程采用相同方法 |
| CG-02 | IETF，[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html)，2017，更新 RFC 2119 | §2：其专门关键词含义仅适用于所列全大写英文用法；没有这些词的文本仍可具有规范性 | 中文“必须/应/可”是本仓明确约定，不冒称 IETF 正式译文 |
| CG-03 | NIST，[SP 800-218 / SSDF 1.1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf)，2022-02，建议框架 | Table 1：PO.2.1 维护职责；PO.4.1–2 定义检查准则并保存支持信息；PS.1.1 限制代码访问 | 不是通用组织法、不是特定人员已获权限或产品安全认证；表中示例不全部强制化 |
| CG-04 | GitHub，[About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)，滚动平台文档，2026-10-23 所见 | About branch protection rules / Require status checks：保护规则及必需检查是平台配置，检查名存在不能证明已启用规则 | 不说明本仓保护已配置，也不授予操作权限；套餐及具体设置必须以目标实际状态为准 |

## 组织设计要求的依据

L0 的 ARC-01–06 是为避免层级越权、缺文、权威混淆、词典提供身份漂移及证据外推而制定的体系设计；L1 的 GG-01–08 是版本、适用、真实权利与例外生命周期的组织契约；L2 的 ORG-01–15 是委派、并行、交接、实质独审和任务终态的协作契约。它们不声称由上述来源逐字规定。具体反例及合法邻例说明要求所保护的不变量；下游可据实际对象选择适用条款，不得把这种可组合性用作隐藏已有承诺的理由。

项目治理领域以PGF-01–06定义单一权威、职责与组合接口，专项PGI/PGT/PGR/PGE/PGD/PGW/PGB/PGC/PGK/PGQ/PGS/PGP/PGL/PGV/PGU/PGM/PGA/PGX/PGN分别定义项目流程和可检查产物；准确条款范围以[领域目录](../standards/project-governance/README.md)为准。L1负责跨项目治理决定，L2负责协作过程，L3负责工程实现行为；同一主题分别消费决定、任务、实现与证据接口，不建立第二规范权威。

## 审查接口

逐条核对：触发对象是否存在、机制能否实现、未知与失败是否可区分、恢复是否重复副作用、合法路径是否误拒、来源是否支持实际命题。记录准确正文摘要、条款ID、理由、证据层级、未执行目标和修订影响。机器结构通过不填写人工技术判定，也不替代实际采用决定。
