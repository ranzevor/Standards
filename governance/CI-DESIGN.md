# 离线门禁与 CI

## 运行入口

仓库提供 [quality.yml](../.github/workflows/quality.yml)，在 Pull Request 或手动触发时使用 Python 3.12 执行离线门禁。普通 main 推送不触发该工作流。

1. `python checks/generate_registry.py --check`：核对规范、条款和引用索引。
2. `python checks/generate_index.py --check`：核对规范目录。
3. `python checks/validate_all.py`：核对身份、链接、Schema、来源与接口合同。
4. `python -m unittest discover -s tests -v`：执行回归测试。

## 运行隔离

工作流采用只读仓库权限，检出时不保留凭据。第三方 Actions 固定到准确提交。外部贡献中的代码在隔离环境执行，生产秘密和持久发布权限不进入文档与工具检查作业。

技术栈、浏览器、设备、云服务及其他目标的验证按采用项目的实际环境与验收合同执行；各目标分别记录输入、环境、命令与结果。

## 私有仓库计算额度回退

Linux 作业默认使用 `ubuntu-latest`。私有仓库的 GitHub 托管计算额度耗尽后，在仓库 Actions Variables 中设置 `STANDARDS_PRIVATE_ACTIONS_EXHAUSTED=true`，随后启动新的工作流运行。额度恢复后删除该变量或改为 `false`。该变量记录维护者确认的额度状态；工作流不通过普通测试失败推断额度耗尽。

三个工作流的手动运行入口提供 `runner_mode`：

| 值 | Linux 作业的选择 |
| --- | --- |
| `auto`（默认） | 读取仓库变量；值为 `true` 时请求回退，否则使用 GitHub 托管运行器 |
| `github-hosted` | 本次运行使用 GitHub 托管运行器，覆盖仓库变量 |
| `mu-fallback` | 本次运行请求回退，不修改仓库变量 |

回退仅适用于私有仓库、由仓库所有者发起且由同一所有者执行重跑的运行；Pull Request 还要求源分支属于本仓库。不满足这些条件时使用 GitHub 托管运行器。仓库公开后自动使用托管运行器。

回退作业同时匹配以下三个标签：

```yaml
runs-on:
  - mu-fallback-linux-x64
  - mu-run-${{ github.run_id }}-${{ github.run_attempt }}
  - mu-job-validate
```

最后一个标签按作业固定：质量检查为 `mu-job-validate`，发行验证为 `mu-job-verify`，发行发布为 `mu-job-publish`，离线消费者的 Linux 成员为 `mu-job-offline-consumer`。运行器供给端须为对应运行、尝试次数和作业注册全部三个标签；重新运行时 `run_attempt` 递增，匹配标签也随之变化。`github.job` 在调度前不可用，因此作业标签使用明确的作业 ID。标签用于路由，运行器的访问范围与生命周期由供给端配置。

[离线消费者工作流](../.github/workflows/platform.yml) 保留 Linux / Windows 两个平台，只有 Linux 成员使用上述回退。Windows 成员仍在 `windows-latest` 上执行，其结果单独记录。

回退选择在作业调度前完成，不依赖先启动一个 GitHub 托管探测作业。配置变更后启动新运行以应用新选择；旧运行保留原有工作流提交及执行结果。发行验证和发布沿用[发行政策](RELEASE.md)的权限、来源及制品检查。回退改变计算运行器，附件存储仍使用 GitHub Actions 的存储服务。

运行器标签、表达式上下文和计费规则分别见 GitHub 的[自托管运行器路由](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow)、[上下文参考](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)及[Actions 计费说明](https://docs.github.com/en/billing/concepts/product-billing/github-actions)。

## 结果与维护

检查对应实际待集成提交。失败日志与后续修复结果分别保留，报告列出退出码、受影响对象和检查范围。生成物不一致时先修正输入或生成器，再重新生成并复核。

管理员配置必需检查与分支保护后，核对规则的生效分支、检查名称和权限例外；工作流检查结果与平台规则分别维护。
