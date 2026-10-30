# 贡献指南

贡献从具体条款、工具行为或使用问题开始。通过 [Issue](https://github.com/ranzevor/Standards/issues) 描述对象、预期行为、实际结果和可复现条件；敏感问题使用[安全报告邮箱](SECURITY.md)。

1. 从[规范登记](registry/standards.json)确定文档 ID、版本和路径。新要求说明适用对象、触发条件、必要动作、不变量、失败恢复、合法邻例和验收方式。
2. 正式正文保存在 `standards/`。修改以分支和 Pull Request 提出；同一版本的发布快照保持可定位，后续实质修订按[版本与发行政策](governance/RELEASE.md)确定版本。
3. 修改正文时同步来源、依赖、示例、译文和检查，重新生成受影响索引并运行 README 中的检查命令。提交实际检查结果和影响范围。
4. Pull Request 说明变更原因、差异、兼容影响及验证结果。作者负责自查；独立审查者核对具体技术内容、反例和修复。
5. 贡献按根 [LICENSE](LICENSE) 的材料类型映射进入对应许可证。第三方材料同时保留来源、适用许可和必要通知；贡献者应拥有相应贡献权限。

文件格式和版本约定见[编制指南](guides/AUTHORING.md)，仓库标识见[命名政策](governance/REPOSITORY-NAMING.md)。协作遵循[行为准则](CODE_OF_CONDUCT.md)。

新维护者提交、PR 标题及 squash 消息遵循[提交与独立审查约定](governance/BRANCHES-AND-REVIEW.md)：英文 `type(scope)`，简体中文主题和正文。AI 行为缺陷可使用[反馈模板](examples/ai-agent/behavior/FEEDBACK.template.md)，具体采用与升级见[操作指南](guides/ai-behavior/ADOPTION.md)。
