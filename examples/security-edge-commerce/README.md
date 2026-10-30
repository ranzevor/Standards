# 有限合成合同模型

`models.py`仅使用Python标准库。运行：

```sh
python3 -m unittest discover -s tests -p 'test_sec_edge_commerce_models.py' -v
```

在仓库根目录运行；测试按文件定位模型，不依赖工作目录导入隐式包。参数循环、逐字节tear及线程争用分别检验局部不变量；样本数不是独立真实场景数。实际结果以对应准确源码与运行记录为准。

| 模型/实际执行类型 | 局部条款映射 | 已证明的有限性质 | 未证明 |
| --- | --- | --- | --- |
| Money/allocate；整数/Decimal/Fraction范围 | COM-L01/L02 | 精确量化、币种/单位拒绝、符号对称余数与稳定tie-break、总和守恒 | 真实币种目录/渠道单位例外、税费规则、实际账单 |
| Attempts/RefundBook/Stock；内存锁与真实线程屏障 | COM-Q02/Q03、COM-S04 | 旧未知不能被新未应用关闭、未知退款占用、原子最后名额/退款准入 | 分布式锁、数据库隔离/耐久、支付渠道迟到保证 |
| Ledger/Usage；纯内存 | COM-L03、COM-S02 | 来源唯一/参数漂移拒绝、同币平衡与固定账户类型、原记录保留、计量ID去重 | 完整会计政策、并发数据库、真实采集/丢失、更正/账期全流程 |
| ResourceGate/CredentialRoll；纯内存 | SEC-P05/P06 | issuer命名空间、对象/动作、已安装目标代际拒旧；消费者和目标拒旧均需闭合 | 真令牌/证书/密码、撤销传播耐久、真实权限、离线消费者可信发现 |
| record/recover；合成字节+实际临时文件写/重开 | EDG-F01 | 在既定格式/CRC/旧槽保留假设下逐字节截断恢复旧或新；同代际冲突拒绝 | Flash擦写原子、欠压、磨损、fsync/掉电、恶意篡改认证 |
| FirmwareDevice/Manifest；有限内存状态 | EDG-F02/F03/F04 | 错硬件/摘要/大小/序列/安全下限拒绝，新序列旧展示版本合法，同清单续传不重置尝试，启动非健康 | 真实签名/SUIT/MCUboot、可信高水位存储、全引导/恢复过程 |
| Buffer/elapsed_u8；状态/模算术 | EDG-H02/H03 | 抽象所有权拒绝早读/早释放，已定小区间内计时回绕 | 编译器/CPU屏障、cache/DMA、真实最坏时延/功耗/物理输出 |
| material_scope/verify_provenance/validate_graph；元数据 | OSS-B01/B04/B05 | 根许可不填未知/覆盖异授，制品与信任期望绑定，未知扩展与未知外参分开，关系/未知语义 | 法律权利、真签名、SLSA等级、SPDX全格式、真实包/安装态完整性 |

## 必须保持的模型假设

- 互斥锁仅保护一个进程，权威观察由测试输入给定，不模拟跨系统可信查询；`never-applies`是假设权威证明，包括不会未来执行，不是not-found。
- CRC只用于合成tear检测；`authenticated_by_test_authority`与`proof.signed_by`是输入断言，不执行密码学，不可作为生产信任位。
- 记录模型假定至少旧槽保留且字节读取准确；文件重开只证明实际文件API读回，不证明磁盘/Flash掉电耐久。
- 固件状态机不模拟全部物理故障、真实存储顺序或独立恢复分区；序列/健康/尝试的局部不变量不能替代真实引导器验收。
- 账本仅有合成capture/reversal账户映射，不提供会计/财税意见；争议敞口与业务政策未在模型中实现。
- SBOM函数只验证本模型的三类关系/ID与所选语法字段，不是SPDX schema/全语义验证器。

模型以外的订阅日历/DST、真实签名/认证、全渠道异步状态、台架期限/能量/总线/磨损、真实包构建安装/消费者/网络等均未执行。具体目标命令、输入与权威观察合同在各专题末尾，缺真实目标参数时保持not-run。

## 离线命令有限接口

`QueuedCommand`固定意图、主体/对象/动作、epoch、原始有效区间和payload摘要。`OfflineCommandQueue`在可信时间区间完整有效、对象授权及适用离线租约/重连同步条件成立后才调用进程内ResourceGate；准确重放返回历史回执，未知ACK不重做。`install_control`只安装不倒退的控制观察，未观察的新撤销不被登记为已传播。它仅保存RAM状态，不替代设备持久执行账或真实时钟/签名验证。正反及合法邻例入口为`python -m unittest tests.test_offline_edge_commands -v`；采用接口见[合成边缘记录](../adoption-contracts/edge-command.json)。
