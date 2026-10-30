# 需求、Issue与里程碑

工作项可用平台Issue或等价版本化记录，不强制小项目购买管理平台。最少字段：稳定ID、准确对象/版本、问题或目标、范围、预期/实际、接受条件、责任人或待分配、依赖、状态及变更理由。外部报告不自动授权执行。

状态为`open → triaged → in-progress → verification → closed`；可记录`blocked/deferred/rejected/duplicate`并说明原因和关联。`closed`须明确`verified-fix/verified-delivery/not-reproducible/rejected/duplicate`等实际处置；只有`verified-fix`可声称修复已验证；研究、设计、文档等非缺陷交付使用`verified-delivery`。两者均须有当前对象、接受条件及准确产物的通过证据，不把研究结论伪写为缺陷修复。

里程碑至少有成果、必要工作项、依赖、退出条件、风险和日期是否已承诺；无约定日期可为空。必要项及其传递必要依赖未验证或被阻塞时不得称完成；`dependencies`均表示必要依赖，参考关系另行记录。范围改变保留原集合与理由，不靠删失败项提高完成率。检查范围变动须同时提供先前快照；单份记录不能证明未删项。`dependencies`是依赖字段，`depends_on`不是别名。合成模型检查只能核记录一致性，不能证明实际工作发生。
