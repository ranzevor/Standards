# AI/Agent 控制契约运行入口

从仓库根目录运行：

```sh
python -m unittest discover -s tests/ai_agent -v
python checks/ai_code_mutations.py
python checks/ai_target_contract.py examples/ai-agent/target-contract.json
```

`checks/ai_agent_model.py` 使用同进程锁、整数预算、合成目标账本、局部权限表、HMAC 测试状态和本地检查点文件，覆盖预算预留与结算、票据原子消费、目标 epoch 和版本接受、旧 attempt 事件隔离、删除 tombstone、输出前撤权、压缩关键字段保真、证据依赖失效及 MCP/A2A 数据分支。Agent、SDK、网络协议、分布式存储、OS 或浏览器沙箱及收费服务由对应目标适配器验收。

记忆更正、当前删除、根预算和控制终态的恢复条件、冲突处置与合法邻例见[有限恢复合同](RESTORATION.md)；不能只给旧检查点换一个新epoch便沿用旧支出或旧事实。

`Target` 的授权与写入在同一进程锁内原子，幂等记录不会到期；目标适配器另行验证原子接受点、幂等作用域和期限，以及权威查询的最终性。`Checkpoints` 测试本地文件写入与原子替换；目录 fsync、主机掉电持久性及分布式唯一恢复者分别验收。`archive_members` 执行有界归档输入准入且不解压文件；文件打开时的路径竞态隔离由目标文件处理流程验证。统计函数计算已说明 IID 二项假设下的数学值，采样假设和模型稳定性另行验证。

L5 适配器在 `target-contract.json` 填入模块、命令、端点、准确版本、主体来源、输入输出、权威查询、幂等窗口、接受栅栏、预算和取消合同，并分别保存实际结果。空字段保持未配置；合同字段检查与目标运行分别记录。服务拒绝、未知或未运行按实际状态报告。

每个条款的专用正例、直接失败例、合法邻例见 [AI/Agent 规范目录](../../standards/L4/ai-agent/README.md)。文本场景与已执行测试数分别记录；文本变异覆盖少量关键句，全文语义和独立技术审查使用各自的审查记录。

`StreamAssembler`接收适配器附加了请求/attempt/epoch与逐item序号的合成事件封套，不直接解析任何厂商SSE。网络FIN不能晋升完成；tool参数需完整序列和结束标记，所得仍只是未授权提议。`RemoteTaskTracker`按A2A任务独立生命周期保留断流后的运行状态，与MCP请求流取消分开。`Inbox`只给出事件先到、匹配和幂等消费的有限模型，实际持久事务与崩溃恢复须由L5适配器验证。

查看尚未配置的真实目标合同：

```sh
python checks/ai_target_contract.py examples/ai-agent/target-contract.json
```

该命令检查合同字段，不执行命令、不建立网络连接，也不读取凭据。配置完成后，分别保存各运行层的结果。

有限模型、恢复、目标合同与代码变异测试分别覆盖各自接口。目标合同的完整合成示例、字段类型与必需场景见[真实目标验收接口](TARGET-CONTRACT.md)；采用项目据此配置目标，并记录实际权限和执行结果。

## 可选行为配置

输出表达、授权内执行和交付质量的使用方法见[行为指南](../../guides/AI-BEHAVIOR.md)，案例入口见[场景与验证](behavior/README.md)。项目选用后固定其身份，场景合同检查与模型运行结果分别记录。
