# 编制与文件约定

## 结构与命名

正文使用 UTF-8 Markdown，中文语言标识为 zh-Hans；正式品牌和 MCP/API/SDK/CLI 等缩写按实际拼写。仓库标识采用 PascalCase，中文文档文件名使用 `NNN-标题--v<major>.<minor>.<patch>.md`，版本与声明一致。`standards/`保存唯一正式正文；草案修改通过分支和 Pull Request 提交。

[L0](../standards/L0/001-体系架构与规范编制准则--v0.1.0.md)定义层级/领域/专题边界。[规范模板](../templates/SPECIFICATION.md)给最小完整结构和具体例子。独立技术对象需有独立失败机制和验收入口；已有正文充分承担则给准确映射，不为数量机械拆文。

## 逐条合同与来源

每条保留稳定ID、触发/主体、输入/输出/状态权威、必要动作与不变量、失败/并发/超时/未知/恢复、兼容、可查工件和可观察判据、正确/直接失败/合法邻例、真实官方来源版本章节及有限命题、L4/L5/L6消费接口。必须、建议、示例分开；没有外部标准的组织要求写必要性和理由，不虚构出处。

已有PG、CE、D/I/S、M、AUT、§等ID保留；新前缀按文档画像唯一。局部ID以文档ID限定为全局身份。章节要求与对应核验合同共同绑定，索引覆盖该章节的全部适用义务。来源/范围/附录也参与全文身份和人工覆盖；未识别技术段不能静默漏掉。

## 登记与生成

[唯一登记](../registry/standards.json)是唯一身份源。先核输入、差异和来源；更新文档后写准确版本/摘要和必要迁移，再运行：

```sh
python checks/generate_registry.py
python checks/generate_index.py
python checks/generate_registry.py --check
python checks/generate_index.py --check
python -m unittest discover -s tests -v
python checks/validate_all.py
```

生成器只生成结构/绑定，不批准语义或运行。必须人工核逐条机制、合法邻例、来源、依赖和实际验收合同；独审与作者自查分别绑定准确对象。详细接口、schema有限关键词和非目标见[验证政策](../governance/VALIDATION.md)。

## 变更与维护

移动或更名重写相对链接/锚点/来源/别名并重算摘要，保留旧→新身份及义务变化。修复后重验受影响与完整门禁，保留失败和修复记录。读者内容、技术诊断和专门约束各归其位；规范不装入无关项目材料、凭据或内部调度说明。
