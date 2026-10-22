# 完整measured protocol：反方预数值审查

2026-10-22。读 `MEASURED_PROTOCOL.md`，未读本phase peer新稿、真实input/ZIP rows/targets、未GET或fit，也未运行准备/训练代码。本稿先于实际交叉问答；后续答复另存cross，不回写独立稿。ROOT已获实时问题消息。

**条件支持有界普通pilot；在以下接口问题明确前不宜开数值。** 13个querypairs与12个targetpairs全局不交、按MASTER分role、每episode共同checkpoint和独立两bundle、所有paid字段给direct、先seal后testtarget，均实质改进了公平性。无需继续无穷资格；最终科学身份仍是源内静态功能表面/推荐proxy的普通结构机会试验。

## 必须预先明确

**1. Utility的目标missingness与action必须相容。** 当前允许episode至少5个finite targetrows，但未说明top5是在所有nominal rows中preseal选定，还是目标开后只在finite rows里重选。后一方式用未来目标可用性改变行动；前一方式可能选到无y点而无法评分。推荐明确：先seal所有nominal forecasts及top5索引；recommendation主panel只用整matrix target complete的共同episode，并单独锁定≥95%episode/targetrow覆盖。或者明说只做target-finite-menu的回顾诊断、降低可执行utility解释；不能混用。无论何解，target值不能参与选索引，不能按各arm selected-missingness形成不同panel。

**2. 单位必须是接口定义，不是从.02猜。** 明确source `inhibition`、`lib1_y`、`lib2_y`到Y/u/v的固定转换，保证`B=u+v−uv`与2个百分点margin含义一致。若源本来0–1则写identity；若百分值则写固定除100。保留finite越界，不clip，不用观察分布决定缩放或资格；此点可以由既有glossary/实现合同解决，不需先探索数值。

**3. 推荐比较者的选择范围。** 四臂12configs均按MAE选model，随后在这些arm中按val U选comparator，合法但仅是“forecast-optimized registered policies里的U最优者”，不是所购12config验证结果中的U最优。较强且不增加selection fits的方案是：从已保存全部ordinary config的val预测按U锁定推荐比较者；若其baseconfig不同，额外refit要前置计费、双方同规则，不假称原4refits。也可保留原较窄规则但准确限定claim。建议前者，因为本门明确要求decision-oriented headroom，而selection预算已经支付。

**4. 零贡献MASTER的处理。** ≥95%episode/row覆盖不保证每个预分配MASTER都有可评分episode。须报告各role预分配与contributing cell数；预定零贡献时是qualification abort还是条件评分。bootstrap应遵照同一预定cell estimand，不能默默把96改成事后剩下的cell数并仍称“all preassigned contexts”。forecast和utility的common panel可不同但必须各自固定规则、所有臂一致，coverage分母仍全部nominal。

## Co-primary及ordinary comparator的结论边界

forecast与U分别val锁比较者、test用配对cell CI，双主门均需通过，是intersection规则；不会因设置两个终点就自动产生“任一成功”的多重性漏洞。两项point margin+95%lower>0的门是前瞻实用筛选规则，不能将其解读为CI下界已超过.02。CI仍条件于一次fit、源内样本/模型/标签，不涵盖训练seed、独立培养、来源重叠或试验噪声。

effect、ridge/RBF、local offset、blend与validation枚举本身都是ordinary方法。预选比较者列表应理解为**不含effect结构的已注册比较者**；不能把候选因为单独命名就说成唯一非ordinary模型。mixture包含effect端点，enumerator能选择effect，匹配是预期事实；即便effect胜其它非effect臂，也只能支持有限预算下结构归纳偏置，不证明击败普通程序搜索或新算法。完整报告mixture/enumerator可防止误述，不能因其复制effect就抹掉真实结构实证。

direct与combo_direct都获得paidcombo，前者额外获得mono，信息差归因明确。direct中不用MASTER ID避免偷认cell；固定mask/padding和querydrug identity使其可消费完整两bundle。普通local offset提供有限而真实的source-context适配，至少强于只摆一个不更新direct；它不是所有refit/CL的穷尽对照。本门不主张全面胜CL/AL/RSI，故不需要此时堆更多算法。

## 权重、coverage与两个“平台/支持”问题

每episode训练总重1、episode→MASTER评价是合法预定选择，但**训练不是cell-balanced**：episode多的cell在拟合中权重更大。所有臂共享可避免直接预算不公；仍建议若目标是cell宏泛化，改成每cell总重1、cell内episode等权的固定weight，或明确坚持episode-balanced而不称cell-balanced。不要开test后因某臂弱而换weight。

一个targetpair/master只保留一个metadata选targetmatrix，已避免重复plate直接改变评价pair权重。witness重复值的平均规则、不同pair witness mono噪声和完整paidcombo可用性均须所有臂一致。episode common abstention与target common scorable status应分开记；不能把额外D/mono失败行只给某个direct恢复，不能换witness救覆盖。targetfinite规则只能执行先定的无值筛选，不能解释为全库无条件性能。

**Baseline regret≤.02的near-ceiling停止**在该released utility benchmark内合理：连噪声oracle可改善空间都不足注册用途量级，便不扩展推荐。高regret则不证明真实可达空间，因oracle挑的是带噪标签。forecast可仍完整报告，但双主门不能通过，也不能换指标宣布框架成功。

**Mono plateau诊断**建议精确定义为同episode nominal两点的`max(|Δu|,|Δv|)≤.02`且至少一轴`|Δlog10dose|≥1`，明确absolute distance、是否existential flag和坐标方向。它证明条件压缩有碰撞/近碰撞，不单凭此证明功能不可预测；需要target residual差才谈经验破坏，且不能用诊断筛test。pair训练rectangle只是范围盒，不是joint support或可识别性证明；明确train→val、train+val→test所用盒子来源，不能借test目标改善支持判断。

## Paid-reference excess U的科学解释

`U=Y−max(u,v)`接口可以合法成立：给定预购两bundle导出的observed mono参照，评价hidden AB在同dose的exported inhibition相对参照的增量。它不是source HSA、同一次独立mono实验的HSA、因果synergy或临床效益。finite out-of-range或参考测量噪声可能影响排序，全部方法共享这些输入，不能clip到有利范围。目标AB附带mono不用于纠正U，即使其看起来更干净也不行。

这一utility避免仅比较最大inhibition，但并不保证固定最大dose anchor必差；应完整报告固定合法5点选择的anchor。若“maximumdosecorner”只选1点，而其它policy选5点，应标成不同输出大小的描述锚，或者先定义同样5个design-only点的固定policy，不能当同动作5点对照。主比较者仍由已声明val规则锁定。

结论：上述单位、missing-target action、比较者与零贡献cell接口写清并落实代码后可GO一次普通pilot；没有原始独立归一化谱系不自动阻此限定回顾试验。不得把实用代理门通过变成新world/agent/继承/RSI贡献，亦不得把本门失败扩大为所有功能结构无用。
