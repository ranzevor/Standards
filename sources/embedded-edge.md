# 嵌入式与边缘计算来源

下表固定来源版本、章节、支持命题及适用条件。滚动资料采用记录日期为2026-10-23；具体设备按所用实现版本验证对应机制。

| ID | 发布者、准确身份与入口 | 引用章节/技术命题 | 不支持的结论 |
| --- | --- | --- | --- |
| E01 | IETF；[RFC9019，Informational，2021-04](https://www.rfc-editor.org/rfc/rfc9019.html) | §2.2角色、§3架构、§4/4.1引导、§6清单；清单与传输独立，固件/清单真实性及引导更新角色分别考虑。 | 架构资料，不实现SUIT、不证明引导器或所有掉电模式。 |
| E02 | IETF；[RFC9124，Informational，2022-01](https://www.rfc-editor.org/rfc/rfc9124.html) | §3.2—3.4、§3.13—3.15；§4.3.1/4.3.4—10/4.3.17—18；清单序列不回绕且不同于展示版本；新序列可授权旧版本。适配类、payload摘要/大小、真实性与授权各有职责。 | 同序列幂等续传、安全下限和持久耦合为组织合成；不证明真实硬件信任根。 |
| E03 | NIST；[NISTIR8259A final，2020-05](https://nvlpubs.nist.gov/nistpubs/ir/2020/NIST.IR.8259A.pdf) | Table1 Device Identification，印刷p5/PDF页10；IoT设备网络安全能力基线包含逻辑/物理设备识别能力。 | 仅能力背景，未引入表中全部控制，不证明安全擦除/功能安全。 |
| E04 | GCC；[Using GCC在线手册，2026-10-23所见滚动页；真实编译器版由L5固定](https://gcc.gnu.org/onlinedocs/gcc/Volatiles.html) | §6.10 When is a Volatile Object Accessed；GCC的volatile访问不提供对非volatile写的一般内存屏障/顺序保证。 | 只说明该编译器规则，不声称编译器屏障独立完成DMA/cache/多核同步。 |
| E05 | Arm；[CMSIS6 latest/Core Cortex-M D-Cache动态API页，所见2026-10-23](https://arm-software.github.io/CMSIS_6/latest/Core/group__Dcache__functions__m7.html) | SCB_CleanDCache_by_Addr/Invalidate；所读按地址D-Cache维护API要求32字节对齐地址，长度按字节。 | API文档非真实CPU/DMA一致性实验；不能推广所有CPU/cache行。 |

## 组织合成与适用边界

对应规范将状态、不变量、故障恢复和验收场景作为项目工程要求，条款中说明其适用条件、观察对象和来源接口。


