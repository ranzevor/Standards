# 项目治理执行指南

本指南把[项目治理专项](../standards/project-governance/README.md)落实为可填写步骤；必要规则以准确规范条款为准。示例项目LocalTableConverter是合成离线CSV工具，没有账号、云部署或真实交易。

## 1. 定义交付

填写记录的`project.problem`、`project.audiences`、`project.scope`、`project.resources`、`project.success_criteria`及`project.lifecycle.entry_condition`、`project.lifecycle.next_condition`。例：输入UTF-8 CSV，输出固定列顺序的CSV；不修改原输入，非法列数拒绝且无半成品。不以“写完若干文件”代替用户可观察结果。尚无测量的条件保持unknown。

在`requirements`中分别记录REQ-01列顺序、REQ-02输入保持与失败拒绝、REQ-03必要检查/范围/依赖、REQ-04材料保留，再用`acceptance_ids`连接预设合同。转换器在目标目录写完整临时文件，flush/fsync并复核输入摘要，以`os.link`原子创建此前不存在的目标；目标已存在或竞争出现时拒绝，不替换已有文件，最后清理未提交临时名字。接口固定编码、列集合、错误及权威输出路径。

## 2. 锁定条款并分配记录

使用[字段说明](../templates/project-governance/README.md)填写准确文档 ID、0.1.0 版本、路径、SHA256及条款。项目只填适用、配置、操作和必要例外，不复制通用正文。无部署不适用PGU的真实部署动作，但范围、Git、测试、证据及维护说明仍有用途。合成选择保持technical-reference；没有真实采用决定时不填批准人或生效时间。

## 3. 改动与本地操作

先读status/diff并保护非本次变化，再逐路径暂存；暂存后再次修改会形成索引与工作区两份差异，必须分别检查。选择独立分支或worktree时不让两个工作树同时检出同一分支。同步前fetch并观察提交图，再选择ff-only、明确merge或未共享分支的rebase，不能把pull默认策略当作项目规则。

```sh
python examples/project-governance/git_scenarios.py --scenario index_snapshot
python examples/project-governance/git_scenarios.py --scenario merge_conflict
python examples/project-governance/git_scenarios.py --scenario rebase_conflict
```

场景名以脚本`--help`实际列项为准。冲突发生后检查未合并索引；可明确解决、暂存并continue，也可abort回到预定状态。revert以新增提交恢复内容并保留已共享历史；标签核附注对象和剥离提交，不从名称推导发行完成。

## 4. 验证正常和失败路径

```sh
python examples/project-governance/project_example.py
python checks/project_governance.py --project examples/project-governance/project-record.json
python -m unittest tests.test_governance_models tests.test_project_git_scenarios tests.test_project_readme -v
```

正常转换核列顺序、输出内容和输入摘要；非法行核预定错误、原输入保持、输出不替换且无残留半成品。治理模型另外核陈旧revision、缺必要依赖、部分缺陷闭合、过期例外、未核外部效果和材料活动引用，不把模型状态当真实业务事实。

把实际对象、环境、argv、退出码、预期/实际和原始输出列入证据。Git工作区以包含待测修改的实际tree及基线commit绑定结果，离线发行包以经验证的构建清单绑定结果；运行前后核对同一身份。反例测试的预期非零退出可以通过该测试；未启动的浏览器、超时未知、跳过和真实环境未验分别记录，不能合成全部通过。

## 5. 审查、交付与恢复

提案列准确基线/候选、差异、来源/许可、风险、兼容、验证和未完成项。独审实际检查内容及关键反例；作者修复后按新对象复核全部原判据。合并前重新核目标HEAD和最终集成对象，旧绿色或旧hash不覆盖新提交。

示例没有正式发行和部署。若以后选择发行，先补真实许可/分发决定、维护范围和必要门禁，再创建准确标签与制品清单；发布响应未知先查目标事实，不能盲目重试。需要数据迁移时先验证恢复点和旧新读写矩阵，只有备份文件存在不足以证明回滚安全。

## 6. 维护和材料回收

记录实际支持范围、渠道和责任，个人项目可以不承诺SLA。新问题保留原失败并进入相应工作项。退役分别核消费者、导出、保留与撤权；归档不等于删除。

按目录和材料类型设置保留规则，单独记录实际需要保留、回收或例外处理的对象。保留源码、正式成果和不可替代证据；缓存/依赖/构建物先核可重建方法、活动引用、保留hold及实际占用。回收模型只给dry-run计划，不在检查中删除真实文件。当前候选由Git tree或发行清单定位，最小必要证据索引与原始结果放在独立运行目录或授权证据存储。
