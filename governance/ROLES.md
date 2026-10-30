# 职责与维护入口

仓库维护者为 [Ranzevor](https://github.com/ranzevor)。一般问题通过 [Issue](https://github.com/ranzevor/Standards/issues) 提交；安全报告发送至 [ranzevor@gmail.com](mailto:ranzevor@gmail.com)。

| 职责 | 工作内容 | 产物或入口 |
| --- | --- | --- |
| 规范维护 | 维护正文、来源、依赖、版本和缺陷修复 | `standards/`、`sources/`、`registry/` |
| 工具维护 | 维护生成器、检查器、示例和回归测试 | `checks/`、`tools/`、`tests/` |
| 技术审查 | 审查准确变更、核心机制、失败恢复与合法邻例 | Pull Request 中的审查意见与复核结果 |
| 规范采用 | 确定规范版本、状态和生效范围 | `registry/standards.json`、[采用政策](ADOPTION.md) |
| 项目采用与验收 | 选择项目适用条款、参数、例外和实际验收方法 | 采用项目自己的记录 |
| 仓库平台管理 | 管理访问权限、分支规则、检查和发行入口 | GitHub 仓库设置与工作流 |
| 权属与许可 | 维护材料许可、第三方通知和贡献条件 | 根 [LICENSE](../LICENSE) 与[许可政策](LICENSING.md) |

同一维护者可以承担相容职责。要求独立审查的变更应由未参与该变更编写的审查者复核；作者自查和独立审查分别记录。

[CODEOWNERS](../.github/CODEOWNERS)指定审查路由；分支保护、必需检查和发行权限由仓库管理员在 GitHub 中配置并核对。维护范围见[维护政策](MAINTENANCE.md)。
