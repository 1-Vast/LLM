# 独立反方：反例驱动的历史状态细分尚无操作级新意

2026-10-22，Asia/Shanghai。依据根代理的新候选描述形成独立初始立场，未读取支持方本轮提案/源码审计。本阶段无HTTP、真实响应、训练或合成胜利；具体生物资产的可用菜单仍需另行资格。**建议STOP当前候选作为新颖核心；保留“观测状态是否遗漏可迁移的干预相关历史信息”这个合法数据问题。**

## 操作级对应关系

令历史`H_t=(o_0,a_0,...,o_t)`，当前表示`s_t=e(o_t)`，付费实验产生未来功能`Y_{t+k}`。候选寻找同/近似`s_t`下某个可执行`a`满足`P(Y|s,H1,a)≠P(Y|s,H2,a)`，然后把状态改成`s'=(s,selected_history_feature)`。这个信息检验有明确意义，但目前每一步都有直接已有操作解释：

| 候选步骤 | 直接方法学对应 | 仍需独有的内容 |
|---|---|---|
| 按未来受控响应区分两段历史 | controlled predictive/causal-state equivalence；PSR用action-observation tests的预测定义state | 哪个新的可实施更新或保证超越这些预测状态学习 |
| 用反例增加最小历史记忆 | counterexample-guided automata/Mealy-machine learning；variable-order Markov/state splitting；MDL结构选择 | 新的split操作、可验证样本/成本优势或真实约束下必要保证 |
| 只为实际动作保留相关维度 | action-conditioned conditional prediction/feature selection/sufficiency testing | 不等于因为输出含action就新增机制 |
| 选择最能暴露下一次aliasing的实验 | active model discrimination、information gain、experimental design/active automata learning | 同菜单/假设族/历史/评估预算下额外改进效率 |
| 继承历史细分规则 | 普通跨任务feature/meta-model transfer、检索、规则蒸馏 | 从共同状态/程序起点迁移的可执行程序净收益 |
| 再改寻找反例的策略 | active meta-learning/learned optimizer；本项目已核验的通用RSI先例 | 共同起点的后继改进收益，不是保存更好的state/权重 |

经典相关方向包括Littman/Sutton/Singh的Predictive State Representations、Angluin的Learning Regular Sets from Queries and Counterexamples、Shalizi/Klinkner的CSSR、输入输出causal-state/ε-transducer。它们的假设不同（有限确定自动机、随机离散过程、受控系统等），不能说它们已经解决连续菌落生物学或本项目成本约束；也不能把这些假设差异本身当新算法。本轮仅离线理论对照，未重新取其一手全文，不提供未经核验的DOI/性能数字。若支持方提出具体不等价操作，再有针对性核一手算法。

**核心缺口：** 目前候选只规定“什么现象说明状态不够”和“应以最小记忆纠正”，没有给出超出经典受控状态细分/条件特征选择的具体算子。可证伪性强或名为world model不补足新颖性。

## 最小构造：证明遗漏信息，同时推翻独有收益的推断

构造两类独立细菌培养历史：`H_A`先经历A再恢复，`H_B`先经历B再恢复。在决策时都观测`o=(current_size=1,current_growth_rate=0)`。未来给予药C时令功能抑制`Y=1`对`H_A`，`Y=0`对`H_B`；给予D时反过来。两历史各占一半、观测无噪声，且C/D都在两种历史后的真实可用菜单中。

- 只用当前o的最优MSE预测对C为0.5，误差0.25；加一bit`last_prior_drug=A/B`可零误差。它严格证明这个观测表示不具controlled predictive sufficiency。
- 一个普通direct条件表`Y=f(last_prior_drug,next_drug)`、深度1/2树或one-hot ridge交互得到完全相同结果，**不需要世界模型、代理、递归细分或RSI**。候选即使在该例获胜，也只战胜故意漏history的基线。
- 若当前o另含准确resistance marker，则一bit已可从o得到，历史不应增加收益；若数据中从未对`H_B`施C，无法靠观察`H_A→C`与`H_B→D`断言aliasing；若H_A/B与不同run/nutrient绑死，差异不能归为history。

这是解析信息例，不是运行合成实验，不对应任何真实药/抑制数值。扩成多step后用最后两药或suffix trie即可处理有限记忆；只有实际数据表明更长/潜在历史必要才考虑更复杂状态。若需要完整历史，强RNN/Transformer和predictive-state learners必须拿同样history、辅助监督和计算预算，不可只给候选过去动作。

## 最强简单基线

首选直接对照是**同history的action-conditioned conditional predictor + 普通重训练**：输入当前size、最近growth slope、最近若干实际drug/dose/duration、恢复/洗脱与营养/基质/run信息，预测每个允许未来action下的功能；用regularized tree/boosted-tree或kernel ridge，并以同paid数据nested/prequential验证选择history长度/交互。固定同query序列先隔离更新增益。它无需声称学到了真实cell state即可使用全部历史信息。

更贴近候选、几乎相同的结构基线是**带复杂度惩罚的controlled variable-order state splitting**：只有在已有状态下history×action残差经独立验证可重复时增加最小split，保留unsplit作为回退。给它同history候选池、同假设检验/搜索预算和active-discrimination实验选择。若候选与它一致，不能将赢过无记忆模型当新意；若固定规则/ordinaryCV得到同等结果，停止程序继承特异主张。

两者不是要求永远不能使用新潜变量，而是避免“只给一臂历史/监督”的必胜设计。状态细分可降低方差、节省样本，是值得量化的实际归纳偏置；目前尚无新操作确保此增益。

## 数据与跨实验replay的必要条件

不要求同一菌落自适应分支才能进行**跨实验研究智能体**replay：完整静态schedule表足以让研究智能体逐轮挑选独立培养实验、收到结果后更新，再挑下一项。反之，若声称在**同培养轨迹内**看state再改下一药，必须有相应状态条件action分支/分配与positivity；两类应用不能混用。

要把观察到的差异叫action-conditioned collision，至少要：

1. 同/近似state的距离、tolerance及measurement uncertainty在结局前定义；两个连续浮点state从不恰好相同，不应事后挑看起来相似的极端响应。用current size+slope强状态先验，不能忽略显而易见的廉价观测制造aliasing。
2. H1/H2后有相同未来action/dose/timing的实测功能，分配单位、独立培养/lineage、run、环境和祖先依赖可追踪。只按不同动作观察两个不同结果不构成反例。足够的交叠可在跨培养随机分配获得，无需同colony测所有潜在结果。
3. 区分测量噪声、自然异质性、未来观测泄漏、diffusion/nutrient/geometry偏差与真正预测信息缺失。增长state与未来growth可同通道，但cut后帧/完整tracking/QC不能回填给cut前特征；按已知终点选genome不能伪装前瞻state。
4. split仅由paid support及允许训练历史产生；由独立heldout cultures/actions检验。发现一次大残差是筛查，不是新state已验证；多重搜索和selection噪声的成本计入，同历史的direct/MDL/CV基线得相同候选数。
5. 新history bit对未测后续时间/动作有可重复效用，且不只记住culture ID、drug名或当前已测标签。药物/菌株/环境的task分区预冻，shared ancestor/相同chamber不得跨fold冒充独立任务。

若只有一个strain、三药及固定loops，可能足够测试部分history信息，却未必有足够independent future tasks作weight/procedure/meta三阶段拆分。实际asset认证前不预支任务数量。

## 可证伪主张与停止标准

最窄可测数据主张是：在同current state+technical covariates+action条件下，预定history特征对独立未来功能有超过实用δ的增量。若强same-history direct模型也受益，它认证history信息；**不能据此证明显式world-state refinement必要**。若差异因run/geometry/当前slope/未来泄漏消失，停止该collision解释。

更新/Agent/继承/RSI的主张应逐项另测：固定支持集下的增益越过same-information direct与MDL splitting；同一模型下选择实验越过fixed/standardAL/model-discrimination/equal-budgetsearch；新任务共同model/program起点的程序移植越过ordinaryrefit/retrieval/distillation；最后冻结m0/m1从共同model/program/history和同k次修改预算看更后未选择任务净改进，再比较m1/m2。更多state维度、更多找到的反例、更多接受编辑均不是性能/RSI结果。

若候选无法给出超出上述baseline的最小操作，**现在就STOP其新颖核心，不为熟悉的state-splitting再堆LLM模块**。若仅存在history信息资格机会，可以保留为普通系统辨识/条件预测研究，并诚实命名；当前未批准数值开值或架构。尚待支持方独立源码审计后真实交叉辩论，不以本稿预告说已达成共识。
