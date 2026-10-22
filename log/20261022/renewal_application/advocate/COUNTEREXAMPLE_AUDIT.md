# Selection/transport 反例独立复核

2026-10-22，`mechanism_advocate`。只读 skeptic 已封存 protocol/code/test/result/execution 与 root RAW_TOKEN_WARNING。未改 skeptic 或既有独立稿/CROSS；无生物值、HTTP或拟合。新增独立代码 `research/renewal_application_20261022/advocate_counterexample_check.py` 从手写400 founder逐个展开后代，不import/call skeptic函数；精确有理数检查结果与运行receipt在本目录 COUNTEREXAMPLE_CHECK/EXECUTION.json。

**裁决：反例成立，独立13 checks PASS；它证明给定 endpoint/global 观测不足普遍识别 selection 与 state change，不证明实际 Watermelon 无法识别任何结构，也不否定 conditional prediction。**

## 按既定六项清单核对

### 1. 隐状态、观测与零

初态均为200个A、200个B founder。每个founder为不分裂存活（1后代）、一次二分裂（2后代）或死亡（0后代）。state change 模型允许一个A-origin founder的两个分裂后代成为B；selection-only不允许状态改变。

允许观测为初始state计数、最终state×理想H2B-generation联合计数、终点总数、总体division/death数。它没有逐origin的生死/分裂事件、origin→destination配对、barcode或中间时点state。这是明确模型类，不将真实缺捕获当成零。合成中的A|1=0是真实手写零；不能套用到Watermelon缺sampletuple/未捕获barcode。

### 2. 每个事件及计数合法

| 模型 | A-origin founders | B-origin founders |
|---|---|---|
| S selection-only | 198不分裂A；2死亡 | 198不分裂B；2各分裂成2个B |
| T state-change | 198不分裂A；1分裂成2个B；1死亡 | 198不分裂B；1分裂成2个B；1死亡 |

每个模型各400 founders，所有事件数非负，生成的后代数与generation一致。T有一个A→B变化事件；其A→B**后代细胞数**为2。不能混用transition-event count与descendant count。

S的2次division都来自B，2个死亡来自A；T在A/B各有一次division与一次死亡。总体相同但origin-resolved事件不同，正是未观测信息。若把origin-resolved division/death列为观测，此反例不再等价，不得省略这一条件。

### 3. 完整允许 endpoint joint 与全局量相同

两模型均有 `A|0=198, A|1=0, B|0=198, B|1=4`，故端点A198/B202，总数400，generation1后代4，cycling tail=4/400=1%。初态400+两次二分裂的净新增2−死亡2=400。

理想reporter按后代generation精确读0/1次分裂，此处不依赖measurement noise或FACS gate偏差。即使reporter无噪声、已知全局总量，缺失origin联合关系仍可非识别。这比仅匹配totalRNA均值的反例强，但未覆盖全部可能的lineage观测。

术语小限定：skeptic `birth_events_total` 是 `founders*(descendants−1)`，在本例等于division events/净新增细胞数2。若把birth定义为产生的daughter cells，则为4，两个模型仍同为4；死亡2不变。宜把摘要写成“2次分裂、2个死亡事件”，不把不同birth记账约定混为生物差异。

### 4. 隐藏 flow 与普通复现

S后代flow为A→A198、A→B0、B→A0、B→B202；T为A→A198、A→B2、B→A0、B→B200。A-origin最终后代总数也从198变为200。独立展开与保存result逐项相同，冻结protocol/code/tests哈希均匹配。

普通饱和表可设 `P(A)=99/200, P(B)=101/200`，`P(generation1|A)=0, P(generation1|B)=2/101`。相乘回到四个联合计数，均为精确整数；独立检查没有依赖原实现的`int(Fraction)`，排除本例截断造成假匹配。

这张表的参数来自同一个endpoint，因此只是观测likelihood/分布的精确复现，不是留出预测结果、样本效率优势、跨culture泛化或world性能失败；不能拿一个饱和表要求动态模型胜过已见endpoint本身。

### 5. Sampling/gate 与lineage条件

反例本身在完整population endpoint上成立，等价不依赖未知gate sampling。若两模型再经过同一个仅依赖state/generation的观测核，包括相同gate/capture机制，它们仍等价。若观测核额外依赖origin、提供有效origin配对或不同机制的额外测量，则必须重检；不能无条件称“加任何lineage也无用”。

真实Watermelon有clone barcode与多个时点，不可自动等同本例的“无origin配对”。若initial-state与founder真的绑定且后代可完整追踪，它可能已提供区分两模型的联合量；若clone内初态异质，clone标记不是每个founder的state label，仍不能直接当这种联合观测。两种情况都应从实际身份规则确定。

root RAW_TOKEN_WARNING使这一边界更具体：逗号分隔多barcode annotation是token而非已认证单clone；跨sample重复10x cell barcode不能直接全球join。任何后续分析须先固定sample_id+barcode/已认证row键，以及single30nt保守规则。多barcode串的精确token支持不得称lineage支持，不能拆串制造独立cell/lineage。该格式警告不是生物选择/转移阴性。

### 6. 最少额外反馈及结论强度

一个精确的origin-A→late-B后代数能区分这对模型（0 vs2）；它并不保证一般系统的唯一机制辨识，也没有有限噪声样本的功效证明。若仅给clone而不知clone内origin-state，额外量未必可获得。

即使确认A-origin→B发生，也只排除本S，不能唯一归因于drug诱导、而非自发转换/其他过程；drug-induced主张还须相应对照。哪一种额外measurement打破哪个等价应明确，不能将“一个量能区分一对构造”升级为“一标量普遍识别”。

## 对实际 Watermelon 和总目标不能作的推论

- 不意味着实际source满足本反例的全部假设；它不是该数据的拟合、检验或机制裁决。
- 不否定earlyRNA在未见culture/lineage下预测reporter-conditioned fate，也不要求先识别完整selection/transport才允许条件预测。
- 不证明任何world/agent/继承/联合/RSI性能阴性，更不制造新RSI机制。
- 不把总体birth/death、reporter、barcode当必然无用；本例说明缺少特定joint时仍有歧义，附加实测结构可以改变识别。
- 不使普通fate分类自动成为新core；反例揭示的非识别性与一个具体结构的预测/更新效用是不同命题，后者需独立合同和同信息强比较。

## 实际 cross

已向skeptic发送独立13check结论及四项最强保留：birth计数约定、未含origin-resolved/完整lineage观测、饱和表不是heldout预测、一个额外量不是普遍识别且drug-induced仍需对照。

对方实际回复：全部接受，尤其birth字段命名易混；冻结code/results不改，在interpretation明确2次division/net新增与4个daughter births的约定。确认观测没有origin-resolved events或完整Watermelonbarcode，不能外推source无信息；static表只复现endpointlikelihood，无heldoutforecast胜利；A→B标量只区分构造pair，drug-induced非spontaneous需对照。双方结论边界一致。没有变更peer模型以救结果。
