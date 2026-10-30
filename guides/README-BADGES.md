# README 徽章的对象与依据

README 使用标准 [Shields.io静态徽章](https://shields.io/badges/static-badge)，分为项目身份、材料许可、技术与发行形态、有限范围参考。点击徽章可到达对应项目说明；URL、可见文字、目标与本地数据来源登记在 [README 合同](../sources/project-governance/documentation-rights.json)。

| 徽章 | 表达范围 | 依据 |
| --- | --- | --- |
| Documents / 162 adopted | 当前登记规范集合的采用数量与状态 | [规范登记](../registry/standards.json)；单份规范版本分别登记 |
| Version | 当前源码及消费包的发行集合版本 | [项目元数据](../project.json)与对应发行说明；实际已发布对象见 [Releases](https://github.com/ranzevor/Standards/releases) |
| Docs & data / CC BY 4.0 | 项目自有文档、规范、数据等材料的许可分配 | [根 LICENSE](../LICENSE)及文件级例外 |
| Software / Apache-2.0 | 工具、测试、自动化和软件 Schema 的许可分配 | [根 LICENSE](../LICENSE)及文件级例外 |
| Python / 3.12 | 离线工具与质量工作流采用的 Python 基线 | [质量工作流](../.github/workflows/quality.yml)、[兼容指南](COMPATIBILITY.md) |
| Documents / Markdown | 规范与指南的编制格式 | [编制指南](AUTHORING.md) |
| Contracts / JSON Schema | 登记使用 JSON 与软件 Schema | [Schema](../registry/schemas/standards.schema.json)、[有限验证范围](../governance/VALIDATION.md) |
| Distribution / Agent Skill | 发行提供 Agent Skill 消费包 | [离线指南](OFFLINE.md)；支持范围以实际目标验收为准 |
| References / RFC 2119 / RFC 8174 | 规范性用语的有限参考 | [CG-01、CG-02](../sources/common-governance.md)；中文词义由本体系定义 |
| References / SSDF 1.1 | 所选安全开发实践的参考 | [CG-03](../sources/common-governance.md)；限定到已列命题 |

两类许可按材料分配，不表示每份材料都可任选两种许可。技术格式徽章不扩张为完整标准实现保证；参考徽章不表示获得外部认证。

## 维护与验证

合同必填`badge_protocol: shields-static/1`；删除或改变该字段不能停用Shields.io要求。集合采用状态使用`readme_contract.badge`，其他徽章使用`additional_badges`；每项登记稳定ID、类型、对象、主张、官方URL、颜色、目标与本地数据来源，并同步两个语言入口。`images`仅登记封面等本地图像。

标准静态URL为 `https://img.shields.io/badge/<标签>-<消息>-<颜色>`。空格使用`%20`，文字中的连字符使用`--`，下划线使用`__`，其他特殊字符按URL编码处理。显示文字由URL中的标签和消息确定；替代文字保持相同含义，外层Markdown链接指向状态或许可的准确依据。

`python -m checks.project_readme` 离线核对标准URL、替代文字、目标，以及当前规范数量/状态、版本字段、Python基线和文本参考。检查不下载远程SVG，不依赖徽章文件或其摘要；本地封面仍按实际文件身份验证。完整语义、许可分配和来源支持范围按STD-PG-005的PGE-03/PGE-08核对。

发行版本变化后更新版本徽章的URL、文字与发行说明目标；规范集合变动后重新核对数量和状态。图片服务不可达时，正文和替代文字仍提供关键信息。窄屏时徽章自然换行，静态徽章保持其已登记含义。
