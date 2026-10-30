# 文档与源译记录

用于[文档编制规范](../standards/project-governance/006-文档编制与国际化规范--v0.1.0.md) PGD-01—08 的项目侧配置及译文维护。通用规范仍由准确中文源提供权威；译文不是第二份独立规范。

## 填写字段

| 字段 | 必填条件与含义 |
| --- | --- |
| `document_id` / `source_version` | 每条记录必填；准确稳定源文档 ID 和版本，不凭文件名猜测 |
| `source_path` / `source_sha256` / `source_bytes` | 必填；源文件及其完整字节身份，正文增删后重新计算 |
| `target_path` / `target_sha256` / `target_bytes` | 有实际译文时必填；完整译文文件及其字节身份 |
| `source_language` / `target_language` | 使用明确语言标记；当前机器记录取`zh-Hans`、`en`，不据语言标记推断地区法律适用性 |
| `authority` | `source-only`；语义冲突先停用受影响译句并修正，不让译文静默改义务 |
| `coverage` | 实际全文为`full`；没有译文在可用性记录写`unavailable`，不得创建空页面冒充全文 |
| `clause_ids` | 源与译同序稳定条款 ID 的完整数组；附录、前言、表格和代码也必须全文逐段核读 |
| `target_version_marker` | 译文实际版本字段名称；未指定使用工具约定，不兼容字段不能靠子串命中 |
| `terminology` | 每个专业词的中文、英文、含义、适用边界；同形异义词分别说明，例如下载镜像站与镜像制品 |
| `semantic_review` | 区分作者逐句实读、独立审阅及未决差异；机械摘要和ID检查不生成语义等价结论 |

本仓可运行格式以 [translations.json](../registry/translations.json) 为准；字段扩展需同时更新检查器、测试及使用指南。

## 正常实例

清单中的 `STD-PG-006` 对应本规范与 [英文全文](../translations/en/project-governance/documentation-i18n.md)。ID PGD-01—08、标题层级、步骤、失败恢复、表格及限制逐段对应；技术词保留必要英文。修改前先保存旧源/译身份，完成双语同一条款修改，再重算两份文件身份，运行 `python checks/translations.py`，最后按逐句判据人工实读差异。

## 失败与恢复实例

中文把“可发布”改成“必须先验证恢复”，英文仍为旧许可句：即使ID数量一致也属于未同步。将该译文标为需要更新，不能声明当前全文等价；对照具体条款补译必要动作及失败分支，更新准确身份，再复核被修改段落与交叉引用。目标语言缺少界面词时使用记录的源语言回退，不以空字符串掩盖；文档翻译可用并不证明产品界面已国际化。
