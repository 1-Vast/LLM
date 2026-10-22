# 独立反方：先区别静态遗传敏感性、演化状态预测与研究策略改进

2026-10-22，Asia/Shanghai。只读取本轮source资格报告/方法投影和项目历史报告，未读`ADVOCATE.md`，无HTTP、未授权响应、FASTQ或实验。本稿独立形成。**这是一项有真实genetic intervention与evolution/function线索的公开资产；最窄生物预测可能成立，具体state→function join尚未认证。没有具体新算子可供晋级，也没有理由先搭世界模型/Agent。**

## 当前事实和最窄应用

已认证静态层为3,904single-gene knockouts×40antibiotics的筛选后chemical-genetics矩阵；这个遗传干预响应图本身是有价值的静态功能资产，不是细胞沿药物作用后演化的state transition。作者OCDM及此前correlation/tree基线正是利用该图预测XR/CS；任何把删除效应重新组合、给gene×drug相似度换latent名称的操作，都应首先作为静态conditional prediction比较，不能凭中间变量称world model。

演化层为23药各12lineages的响应依赖最高生长浓度传代，以及70/634 predicted interactions的真实susceptibility复核。WGS公开文件明确只有Tetracycline 12lineages×days3/5/7及WT。**不能把40静态drug、23 evolution drugs、70selected pairs、36stage genomes合并成40/23/70个完整动态任务。** 实验身份和监督可分别有价值，不相同的覆盖范围不得拼接归因。

可先保留三类不同窄应用，按实际join资格分别裁决：

1. **静态遗传状态→功能/药对相互作用。** 使用真实删除株screen为新的有向药对或遗传背景预测susceptibility/XR/CS；若只有这一层，按chemical-genetics方法报告。可用作下一项复核实验优先级，但不称演化模拟。
2. **选药后endpoint genotype→同条件IC90。** 若evolved clone/population和功能单位可关联，可研究条件于该evolution regime的genotype-conditioned phenotype prediction，比较同一drug pair内不同lineage差异。它本身可能有应用价值；endpoint genotype解释endpoint IC90不是预测未来转移，也不是genome在决策前免费可用。
3. **前缀状态/历史→后来功能。** 若TET day3/5 genotype或已测susceptibility可与同lineage后来day/挑战药IC90准确关联，可研究在固定TET适应流程中预测未来cross-susceptibility或挑选需复核lineages。这个任务不需首先取得所有备选药序/RSI，但需真实时间cut和功能对应；当前文件名笛卡尔积不足以证明它。

具体应用宜限于**体外E.coli耐药演化后的抗生素功能复核/实验分配**，不外推患者疗法或PHH。未测的564预测pair不能当negative或真实模拟回报；作者复核70pair的选择机制要共享并限定适用菜单。

## 最强普通解释，按缺口逐一比较

| 看起来像新机制的结果 | 最强直接解释/基线 | 真正未回答的区别 |
|---|---|---|
| 删除screen预测后续XR/CS | 原论文OCDM、相似度/6features/tree、同数据regularized pair predictor | 是否只是复现原文静态关系，而非新操作。 |
| genotype使同药对的不同lineage预测更准 | genotype+drug直接条件模型、gene/allele lookup、mutation burden或gene/pathway特征 | 真实状态信息有用≠显式transition结构必要。原文已提出相同pair随耐药机制可有不同XR/CS。 |
| knockout效应帮助解释evolved mutations | weighted/additive static chemical-genetic score、kernel/多任务transfer、gene-levelL2模型 | 删除不等于实际evolved allele；gain-of-function、copy-number与epistasis是否需要新算子。 |
| 几个early measurements能更新later IC90 | last-IC90 persistence、day/actualdose/drug-history、普通offset/ridge/kernel条件更新、ordinaryrefit | 增益是否来自付费反馈或多拿history，而非world。 |
| 预测下一genotype或drug-response trajectory | 普通Markov/state-space/evolution model、直接multi-horizon/multitask predictor | 固定同history和辅助监督下显式可组合transition有无未测功能/决策增益。 |
| 选择下一药或复核实验 | 固定SOP、OCDM优先、exploit-first、uncertainty/标准AL/KG/model-discrimination | 是否比同模型/菜单/预算的常规采集更好。 |
| 保存突变解释、更新规则或选药程序 | 普通retraining/continual、retrieval、规则蒸馏/元学习、等预算程序搜索 | 是否真有可执行程序迁移的独立收益及更会改进的meta策略。 |

不要用过强popgen模型作为唯一“普通演化”对照，让简单直接baseline缺席。先用gene/drug/history条件ridge/树/kernel与Markov/transition table，再按真实数据量选择RNN或population-genetics模型。相反，也不能因通用direct模型理论上可表达一切而否定有限数据/有限计算的结构归纳偏置；需同信息实测。

单基因删除screen到evolved allele的桥接是假设，不是天然因果相等：许多耐药变异可能是调控/功能增强，多个突变可epistatic，日传代选择的群体与测序单clone可不同。若功能IC90来自population、genome来自一个clone，即使lineage/day号一样也不自动是足够state；需要明确代表性/取样假设，不应把无解释误差自动叫world-model失败或神秘memory。若只适用于可认证loss-of-function mutation子集，应在开值前定义，不按结果挑获胜类别。

## 什么实测差异支持状态/转移贡献

第一层是**state信息增量**：同selecting drug/actualdose/day/previousIC90/context下，真实genotype或所提state改善独立lineage/function预测，超过实用δ；不能由mutation-count、当前growth或简单history解释。它不要求存在可执行adaptivebranch，也不自动证明transition。

第二层才是**transition结构增量**：从同一决策cut、相同paidstate/历史/辅助监督出发，显式model预测later state并经功能读出得到的未查询IC90/功能决策，胜过强direct multi-horizon/multitask以及普通transition/refit、简单blend。关键是same-information功能效用，而不是late-genotype reconstruction相关更漂亮。只对去掉全部辅助标签的弱direct赢，没有归因价值。

若声称跨干预可组合，应在真实测过的相同starting-state/context条件下，对未用于fit的后续action/duration预测有效；若当前只TET持续适应时间菜单，结论只能是该regime下的temporal prediction，不是任意换药模拟。没有全actioncrossing不禁止该窄任务；它限制反事实范围。

最便宜的反证构造是**静态解释已足够**：真实state加入后全部收益由same-genotype direct model复现，或者固定last-IC90+day更新匹配。此时保留state或feedback应用价值，停止“world transition独有贡献”。另一反证是早state与late同号但不是同culture/clone ancestry，或分区混入同lineage未来值；此时是任务未资格而非模型性能阴性。

## Agent、继承及改进策略要观察什么差异

**Agent：** 可把完整的已测70pair/lineage菜单当跨实验query/update replay，只要source表确有允许query的全部attempt/反馈和成本；不要求同colony有所有分支。先固定获胜模型/更新族，仅改变实验选择，比较相同初始信息/预算的fixed coverage、作者/OCDM策略、AL/KG及等预算search。query应按真实测量bundle计费，12lineages和2technical replicates不拆作免费重复选择；已查询结果不算未查询target命中。更强same-lineage根据state换药policy另外需要真实可替代continuations/分配/positivity，不能用一个simulation补缺并自评。

**继承：** 先定义真正source/后续任务（drug family、strain/selection regime或独立cohort），而不是把TET day3、day5、day7当三个新研究任务。分别开关权重与程序；从共同model/program起点，程序移植须胜过同history普通refit、continual、case retrieval、蒸馏及元学习。只有drug-specific系数或更好initialgenotypeencoder，不算研究程序继承。

**联合：** world/direct×adaptive/conventional 2×2；联合系统须胜最强常规完整系统，不能仅凭正interaction晋级。与SOP或ordinaryAL相同则保留正常采集应用，不宣布Agent特异收益。

**改进策略/RSI：** 真实保存的m1应改变如何提出/选择/检验以后更新，而不是只是多看过结果或多了状态。冻结m0/m1，从同p0/model/history给同k次proposal/evaluation/真实query，在更后未参与优化任务比较净改进曲线；再形成m2并同样比较m2/m1。强retrieval/固定MDL/普通search得到同源失败历史和总预算。更准的初始模型或更多成功编辑不能代替这个差异；形成meta的历史成本另计。

这些分层是**分别何种结论需要何种证据**，不是要求一个窄endpoint预测先做全RSI才准运行。若仅TET12lineages足以做有限state/function预测但不足source/meta拆分，应运行或停止该窄任务依实际用途判断，诚实把继承/RSI保持未测，不虚增任务数。

## 最小资格与具体停止条件

数值前至少锁定：精确drug方向/浓度、evolution day、lineage/founder、clone/population、technicalreplicate、ancestor/control与IC90/genome join；相同lineage全部stage同partition，drug pair共享药物和筛选的依赖要按外推目标处理。MIC IC90的response-dependent passage浓度是既有反馈，全部baseline必须可见并计成本，不能当randomizedaction。祖先/对照normalization、数据筛选和原作者OCDM训练曝光要区分；最终矩阵随机split不会把全条件s-score标准化、作者cutoff选择或已发布结果变盲。

如果只能认证静态drugpair终点表，保留静态预测/实验选择资产；如果能认证genotype与endpoint但无earlierfunction，保留endpoint条件预测；如果earlier/later精确join才进入temporal任务。按各层实际范围停止，不把一个join失败扩大成“没有publicfunction”或所有世界模型无用。

在结果前定义真实功能loss/utility、实用δ、预算和interval规则；上界<δ判无实用增量，宽区间判未决，禁止结果后换endpoint续命。若candidate操作与OCDM/staticgenetics、ordinaryevolution/refit或同预算程序搜索等价，停止新增机制主张；无需先昂贵下载15.99GB FASTQ证明一个操作命名没有新意。

## 独立初始建议

继续root正在进行的identity/header资格；它可能开启合法窄预测，尚不批准架构。支持方应先给出一个确切操作、适用数据和可被强普通解释推翻的预测，而非把静态screen、evolution和LLM组合叫创新。历史项目多次被ridge/offset、固定design、simpleblend和等预算搜索解释；此次必须主动把这些解释放进主比较，而不是失败后补。

当前没有读取支持方提案，**未判其未知具体操作新颖或失败**，也未执行性能实验。真正交叉辩论将另行读取并记录实际问答；本稿不是代理共识。
