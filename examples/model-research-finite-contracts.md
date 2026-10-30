# 研究有限谓词的输入与判据

这些接口位于 [`checks/model_research_finite.py`](../checks/model_research_finite.py)。输入为合成的可信比较记录，执行范围限于明确建模的谓词，不读取项目数据、不训练模型、不消耗云资源，也不处理材料授权。科研、隐私和准入状态按各自的来源、观察范围、权利及实现记录填写。

## 时间划分：训练截止与每次预测

`check_split(records, claim, cutoff=None, fit_roles=('train',))`区分跨主体、同主体未来及已声明传导式主张。记录的`role`明确为`train/test`；同主体未来不强制主体互斥。

对于`same-subject-future`，每项训练的事件、可获取、标签成熟时点均不晚于训练信息截止`cutoff`，并对**每项**评价检查`cutoff <= prediction_at`及`available_at <= prediction_at`。这里端点相等表示协议允许预测瞬间已可得的信息；更严格的预测前封闭窗应由项目协议另行约束。数值时标可以是有限整数、浮点或精确分数，布尔、未知、非有限值不当作时点。

可选`target_at`若提供须不早于预测；未提供时本函数不证明标签窗、真实目标事件或更新时点已经核验。`event_at`与`available_at`的真实语义、时区和来源证据仍由[数据专题§16](../standards/L4/model-research/009-训练数据与数据集治理技术规范--v0.1.0.md)及项目协议确定，不凭文件mtime推断。

正例是训练信息截止10、预测13；直接失败是截止10的信息用于预测5；合法邻例是同一主体、截止与预测都为10且协议允许该端点。训练标签回填11、预测后才可得的特征仍分别拒绝。传导式允许已声明的未标注评价输入拟合，但不称独立未见测试，评价标签反馈仍拒绝。

## 隐私组合：非负参数不是可退款支出

`visible_privacy_ledger(entries, observer)`只汇总给定观察者可见机制的元数据。每项实际计入的机制必须有有限、非负的`epsilon`，以`Fraction`精确求和；推荐用整数、十进制字符串或分数字符串表达精确意图。有限浮点按其实际表示值转换，不把二进制近似冒称原十进制精确值。负数、NaN、无穷、未知或错误类型直接使元数据无效，不是“负预算退款”；0与正分数合法。

同一既有输出的再次分发须引用已知机制且没有新私密访问，不能仅换ID规避组合。可信边界内状态若影响可见结果而没有完整机制证明覆盖，记入`assumption_gaps`；已证明覆盖的受信内部状态不机械另算一次可见机制。空账本的0不证明任何真实系统具有零隐私泄漏。

来源补核为Dwork与Roth，2014，[*The Algorithmic Foundations of Differential Privacy*](https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf)，Definition 2.4、Proposition 2.1、Corollary 3.15及Theorem 3.16（PDF页21—23、47，页码从1计）。这里只使用定义、后处理前提和基本组合；有符号的隐私损失随机变量可能为负，不等于把机制保证参数ε设为负。该模型不验证实际机制、抽样、δ、会计器、相关随机性或任何法律结论；更精细的会计器必须按对应理论和实现另核。

## 材料准入：状态和用途共同限定

`check_admission(expected_bundle, actual_bundle, state, permitted_use, current_use)`先核完整组合身份，再使用以下有限正向词汇，不靠拒绝名单接受所有其他字符串：

| 状态 | 可列入的用途 | 不产生的升级 |
| --- | --- | --- |
| `limited-static-check` | `inspect` | 不自动训练、评价或发布 |
| `limited-research` | `inspect/train/evaluate` | 不自动发布 |
| `limited-publication` | `inspect/publish` | 不自动训练 |

用途清单必须是非空、无重复、与状态相容的显式列表，当前用途还必须在该列表内。未知、`not-run/pending/rejected/withdrawn`等非活动状态默认拒绝；后续增加词汇须显式修订接口与测试，不悄悄把未知解释成可用。正例是已给定限定研究记录的`train`；直接失败是静态扫描“无发现”被用于训练；合法邻例是限定静态检查只做`inspect`。函数不认证记录签发者、效期、环境或真实执行权，这些仍是[研究安全§03](../standards/L4/model-research/007-研究安全、隐私与模型材料风险技术规范--v0.1.0.md)的消费前提。

## 执行

```sh
python -B -m unittest tests.test_model_research_finite -v
```

测试检查时间窗口、精确隐私参数、材料状态与用途组合的正常、失败和合法邻例。实际框架、真实训练与科学结论按采用项目的研究协议验证。
