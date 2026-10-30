![Ranzevor Standards：工程与组织规范体系，文档和协作模块的连接插画](assets/cover.png)

[![Documents: 162 adopted](https://img.shields.io/badge/Documents-162%20adopted-brightgreen)](#status)
[![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-blue)](releases/v0.1.0.md)
[![Docs & data: CC BY 4.0](https://img.shields.io/badge/Docs%20%26%20data-CC%20BY%204.0-blue)](LICENSE)
[![Software: Apache-2.0](https://img.shields.io/badge/Software-Apache--2.0-blue)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-3776AB)](guides/COMPATIBILITY.md)
[![Documents: Markdown](https://img.shields.io/badge/Documents-Markdown-000000)](guides/AUTHORING.md)
[![Contracts: JSON Schema](https://img.shields.io/badge/Contracts-JSON%20Schema-blue)](governance/VALIDATION.md)
[![Distribution: Agent Skill](https://img.shields.io/badge/Distribution-Agent%20Skill-6E59A5)](guides/OFFLINE.md)

# Standards

[English](README.en.md) · [规范目录][catalog] · [快速开始](#quick-start) · [语言可用性][languages]

<a id="purpose"></a>
## 用途

Standards 是面向中文开发者、项目发起者、研究者、维护者与采用者的工程与组织规范体系，把适用条件、实施要求、失败恢复和验收接口连在一起，供人类、Agent及混合团队在研发、科研、产品、商业履约、开放协作和生产运营中选用。

项目治理覆盖仓库与维护过程；L0–L3组织体系、治理、协作和通用工程；L4提供十六技术领域；L5适配技术栈；L6把选定条款转成项目采用与实现验收合同。已有行业标准按准确版本和有限命题引用。

<a id="status"></a>
## 当前版本

**发行集合版本为 0.1.0，162 份现行规范全部已采用。** 单份规范的准确版本与摘要以登记为准。 从[规范目录][catalog]查看文档身份与适用领域，按[采用接口][adoption]选择项目需要的条款，使用[项目采用模板][adoptions]记录项目选择。正式发行记录见 [GitHub Releases](https://github.com/ranzevor/Standards/releases)。

<a id="quick-start"></a>
## 快速开始

运行工具需要 Python 3.12，仅使用标准库。在线阅读不需要安装；正式发行包解压即用，无需账号、凭据或环境变量。

### 从正式发行包开始

1. 从 [Standards v0.1.0](https://github.com/ranzevor/Standards/releases/tag/v0.1.0) 下载 [`Standards-v0.1.0-source.zip`](https://github.com/ranzevor/Standards/releases/download/v0.1.0/Standards-v0.1.0-source.zip) 和 [`SHA256SUMS.txt`](https://github.com/ranzevor/Standards/releases/download/v0.1.0/SHA256SUMS.txt)。
2. 按[离线使用说明](guides/OFFLINE.md#从公开发行入口首次使用)核对 SHA-256 并解压。
3. 在解压后的 `Standards-v0.1.0/` 运行包级校验，再进入源码目录执行一次最小查询：

```sh
python -X utf8 -B verify.py
cd source
python -X utf8 -B tools/skill_lookup.py --document-id STD-PG-005 --clause-id PGE-05
```

两条命令均应以退出码 0 结束；查询结果包含 `STD-PG-005`、`PGE-05`、准确版本、文件路径和正文行段。校验失败时不要使用该副本，重新从同一 Release 取得文件并核对摘要。

### 将规范用于项目

1. **找到任务。** 从下方领域或[项目治理总则][governance]选择相关内容，先读适用与不适用范围。
2. **固定要求。** 记录文档ID、准确版本、内容摘要与条款ID；按[采用接口][adoption]说明项目输入、责任人、判据和不适用理由。
3. **实施并留证。** 执行适用要求，分别记录通过、失败、未知和未执行；不要用文档检查代替目标系统验收。

维护仓库时，在仓库根目录使用 Python 3.12（非优化模式）检查当前文档、登记和工具：

```sh
python -X utf8 -B checks/validate_all.py
python -X utf8 -B -m unittest discover -s tests -v
```

第一条核对当前目录、链接、schema和合同绑定；第二条运行测试。各类目标、可选环境和结果说明见[验证指南](governance/VALIDATION.md)。


<a id="navigation"></a>
## 按任务找入口

- **理解体系：** [体系架构][architecture] · [完整目录][catalog]
- **建立项目治理：** [总则与职责接口][governance] · [软件仓库采用](guides/SOFTWARE-REPOSITORY-ADOPTION.md) · [README与品牌][readme-standard] · [文档与国际化][documentation-standard] · [权属与许可][rights-standard]
- **采用与适配：** [入门指南][getting-started] · [技术栈适配][stacks] · [项目采用接口][adoption]
- **编制与修改：** [编制指南][authoring] · [模板][templates] · [兼容与迁移][compatibility]
- **核对依据：** [官方来源与适用边界][sources] · [语言覆盖与翻译流程][languages]

- **AI 行为配置：** [可选行为指南](guides/AI-BEHAVIOR.md) · [场景与验证](examples/ai-agent/behavior/README.md)

- **原生平台验收：** [编码、路径与离线消费者](guides/CROSS-PLATFORM.md)

- **采用与维护 AI 行为配置：** [采用、升级与反馈](guides/ai-behavior/ADOPTION.md) · [缺陷反馈模板](examples/ai-agent/behavior/FEEDBACK.template.md)

<a id="domains"></a>
## 十六技术领域

项目按实际组成选择相应领域。

1. [Web前端与用户交互](standards/L4/web/README.md)
2. [后端与分布式系统](standards/L4/backend/README.md)
3. [数据库与数据工程](standards/L4/database/README.md)
4. [云基础设施与DevOps](standards/L4/cloud/README.md)
5. [AI应用与Agent系统](standards/L4/ai-agent/README.md)
6. [模型训练与AI科研](standards/L4/model-research/README.md)
7. [桌面与跨平台软件](standards/L4/desktop/README.md)
8. [移动应用](standards/L4/mobile/README.md)
9. [游戏开发与数字内容](standards/L4/game/README.md)
10. [CLI、SDK与开发工具](standards/L4/cli-sdk/README.md)
11. [网络与实时通信](standards/L4/network-realtime/README.md)
12. [安全工程与身份系统](standards/L4/security/README.md)
13. [自动化与系统集成](standards/L4/automation/README.md)
14. [嵌入式与边缘计算](standards/L4/embedded-edge/README.md)
15. [商业交易与计费系统](standards/L4/commerce-billing/README.md)
16. [开源项目与公共技术生态](standards/L4/open-source/README.md)

这些领域正文目前以中文提供；已具备英文全文的项目治理专项见[语言可用性][languages]。

## 技术与规范关系

工具采用 Python 3.12 标准库，规范以 Markdown 编制，登记与合同使用 JSON 和有限的 JSON Schema 校验。消费包提供 Source 与 Agent Skill 两种形态。

[![References: RFC 2119 / RFC 8174](https://img.shields.io/badge/References-RFC%202119%20%2F%20RFC%208174-gray)](sources/common-governance.md)
[![References: SSDF 1.1](https://img.shields.io/badge/References-SSDF%201.1-gray)](sources/common-governance.md)

RFC 与 SSDF 徽章表示[已说明范围的参考](sources/common-governance.md)。中文规范性用语由本体系定义，SSDF 仅引用选定实践。徽章的对象、证据与维护方式见[徽章说明](guides/README-BADGES.md)。

<a id="versions"></a>
## 版本与维护

[变更记录][changelog] · [离线使用](guides/OFFLINE.md) · [发行政策][release] · [维护支持][maintenance]

`standards/`是正式规范正文的唯一入口，`registry/`登记文档身份、条款和关系，`sources/`说明引用依据，`guides/`与`templates/`提供使用方法。采用时使用文档 ID、版本与内容摘要定位准确对象。

<a id="contributing"></a>
## 参与改进

从[贡献指南][contribution]开始，针对具体条款提出问题、机制或可复验案例。贡献授权与材料来源按实际条款确认，不以提交动作自动推定额外协议。[行为准则][conduct]说明协作边界。

<a id="security"></a>
## 安全问题

请按[安全报告说明][security]处理敏感缺陷，不在普通公开讨论中粘贴秘密。该页列报告字段、可用渠道与支持范围。

<a id="license"></a>
## 权属与许可

Standards 采用**双许可证分域**：项目自有的规范、文档、译文、模板、治理/规范数据与视觉资源主要采用 **CC BY 4.0**；校验器、工具、测试、自动化、可执行示例与软件型 Schema 主要采用 **Apache-2.0**。主仓及正式 Source/Agent Skill 消费包按对应许可授权公开再分发；第三方材料仍适用自身条件。见[根许可分配](LICENSE)、[许可状态][license]与[权属、第三方材料及贡献授权][licensing]。

[catalog]: INDEX.md
[languages]: guides/INTERNATIONALIZATION.md
[adoptions]: templates/project-governance/project-record.template.json
[governance]: standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md
[architecture]: standards/L0/001-体系架构与规范编制准则--v0.1.0.md
[adoption]: standards/L6/001-项目采用与实现验收接口规范--v0.1.0.md
[getting-started]: guides/GETTING-STARTED.md
[stacks]: guides/STACK-ADAPTERS.md
[authoring]: guides/AUTHORING.md
[templates]: templates/README.md
[compatibility]: guides/COMPATIBILITY.md
[sources]: sources/README.md
[readme-standard]: standards/project-governance/005-README品牌与徽章规范--v0.1.0.md
[documentation-standard]: standards/project-governance/006-文档编制与国际化规范--v0.1.0.md
[rights-standard]: standards/project-governance/014-权属许可与第三方材料规范--v0.1.0.md
[changelog]: CHANGELOG.md
[release]: governance/RELEASE.md
[maintenance]: governance/MAINTENANCE.md
[contribution]: CONTRIBUTING.md
[conduct]: CODE_OF_CONDUCT.md
[security]: SECURITY.md
[license]: LICENSE-NOTICE.md
[licensing]: governance/LICENSING.md
