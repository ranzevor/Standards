# 验证政策

## 规范与索引

[规范登记](../registry/standards.json)固定 162 份 adopted 正文的 ID、版本、路径和 SHA-256。[条款索引](../registry/requirements.json)绑定准确文档和正文行段；来源、跨领域依赖和译文保留各自的语义关系与输入身份。

仓库文件版本及变更差异由 Git commit、tree 和 diff 管理。验证使用实际待测工作区生成的候选 tree，并关联基线 commit；未提交修改纳入候选身份。执行前后核对同一候选，确认结果对应被测内容。

常规离线入口：

```sh
python checks/generate_registry.py --check
python checks/generate_index.py --check
python checks/validate_all.py
python -m unittest discover -s tests -v
```

检查覆盖文档身份、结构、链接、Schema、依赖关系、接口合同及可运行示例。技术审查另外核对要求的适用条件、机制、并发、失败恢复、合法邻例与来源支持范围。

## 软件仓库 profile

从 Standards 源码根目录检查采用项目的软件仓库 profile：

```sh
python checks/software_repository.py --root <project-root> --profile <project-relative-profile.json>
```

该入口使用当前发行自带的有限 schema，核可见性、分发、协作、维护和发行状态之间的必要关系，检查 profile 所列文件、全部 GitHub 工作流的远程 Action 固定，以及实施证据目录是否已加入 `.gitignore`。目标目录为 Git 工作区时，同时拒绝已被跟踪的证据排除路径。

检查不读取平台规则集、安全功能、环境权限或发行对象，也不执行快速开始命令。平台状态、独立审查、实际发布和首次使用结果按[软件仓库采用指南](../guides/SOFTWARE-REPOSITORY-ADOPTION.md)分别验收。

## 发行包

`tools/build_release_bundle.py` 构建 Source 和 Agent Skill 包，在构建时生成完整文件集合、长度和 SHA-256 清单并随包交付；`tools/verify_release_bundle.py` 验证 ZIP 或解包目录的清单和规范登记。验证拒绝不安全路径、大小写冲突、文件目录冲突、符号链接、特殊文件、未列出的文件和身份不一致的正文。离线发行包使用经验证的发行清单固定候选身份。

## 结果记录

记录准确对象、环境、输入、命令、开始和结束时间、退出码、原始输出及检查范围。原始结果及必要证据索引保存到源码目录外的运行目录或授权证据存储，通过准确位置与摘要取得。pass、fail、not-run、partial、unknown 与 not-applicable 分别表达实际状态；失败与修复后的执行结果分别保留。

有限模型的结论对应其输入和假设。浏览器、设备、硬件、远端服务及生产操作按采用项目的真实验收合同验证，项目的实现验收使用该目标的实际观察。
