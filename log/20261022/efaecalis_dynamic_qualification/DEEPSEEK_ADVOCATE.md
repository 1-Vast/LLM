# DeepSeek具体提案的独立支持审查

2026-10-22，Asia/Shanghai。按Root任务先完成`code_io/REPORT.md`，再独立读取`DEEPSEEK_PROPOSAL.md`。未读本轮`DEEPSEEK_SKEPTIC.md`，无HTTP、新response、训练、proposalcode执行或新增实验。本提案是Root调用外部模型生成的假说文字，不是文献或生物证据；本文件不把其生成token数当科研有效性。

**独立结论：`NONE_SURVIVES_AS_NEW_OPERATOR`。** 候选1是deterministic查询记账加成本感知采集；候选2是有缺陷写法的普通在线changepoint/分段回归。能保留的是成本明确的真实药敏采集、prefix-only预测与定时挑战这几项应用问题，不能以它们证明世界模型、独有Agent、程序继承或改进策略更会改进。

## 候选1：未来查询成本state

提案的最小算子是 `c(s,d)=1[d∉Q]`，再在IC50预测效用中减 `λc`。给定action d和已查询集合Q，该值**完全已知**；不需要预测、细胞worldstate、d_t actualselectionconcentration或付费实验。把已知函数改用模型预测只增加拟合错误，既不会创造新信息，也不需要Q与actualdose独立。即使每个state/action都有不同已知cost，cost-sensitiveMDP/AL仍完整包含此目标；不是仅“成本恒1时才归约”。

可写出精确普通基线：同一history模型预测 `p(y|history,d)`，采集器对允许query菜单最大化 `expected utility(p,d)−λ·knowncost(history,d)`；budget作为state、Q作为缓存。若效用是信息价值，用standardKG/AL；若效用是hit，exploit-first/cost或预算动态规划。所有context/actiondependency与目标观测完全共享。所谓“AL不含actuald_t”是对基线的人为限制，普通conditionalAL可以使用同样dose、time与history。

还有三个具体定义缺陷：

1. **queryunit错位。** 每个futureday、不同lineage/clone、drug/dose、biological/technicalbundle产生新的functionmeasurement。若Q仅记录drug名，则曾测过DOX就令未来所有lineage/day的DOX免费，这是错误缓存；正确key至少按真实assay/sample/time组织。重复同一记录可免费重读，新的物理assay不能因drug同名免付费。若只允许已测finitepanel做logicalreplay，可按预冻bundle定义revealcost，但不称现实所有测量免费。
2. **selectingdrug与challengedrug不同。** source每天从最高仍生长浓度传代，查询下一challengeIC50是研究行动；argmax_d中d必须说明是哪种。它不能把选择药未来轨迹、独立药敏probe和最终推荐三种action默默合并。IC50越低通常表明更敏感，所谓“IC50改善”还需明确reward方向，而非默认最大化IC50。
3. **c的AUC是错误裁决。** 已知membership函数可完美分类；若c恒定，AUC甚至未定义。AUC≤.5不能检验cellworld贡献，>.6更不证明药敏预测。正确结局是未查询/独立确认功能效用与合法资源曲线，knowncost应直接精确记账。

不存在必须从source得到“历史真实query顺序”这一额外硬门槛：只要完整菜单/实际bundle可认证，可以预冻offlinequery/reveal次序比较cross-experimentagent，不假装复原作者选择。Qt由候选政策的合法reveal历史生成即可；但不能以事后构造Qt发明真实省下的湿实验数量。

继承membership/cache规则属于固定通用SOP，不是学到研究程序；把更会省查询的最终policy叫m1，也没有展示它使后续生成policy更有效。**无可挽救的最小新操作。**

## 候选2：挑战前置条件/turningpoint

输入是CRO适应prefix的真实DOX药敏曲线。`g_k=IC50_k−IC50_{k−1}`只是相邻差分；检测它何时改号及拟合分段线性，是普通onlinechangepoint/trendestimation。未来profile未知、只用prefix是合理信息约束，可修正原作oracleplanning不适于前瞻的比较条件；**公平约束不是新算法**。

其公式 `h_hat=argmin_h Σ_{k≤h}(IC50_k−f(k;θ))²` 还有结构性缺陷：h同时改变被拟合/计分的数据量，且只保留左段，没有右段、固定trainprefix、complexity或最短segment约束。候选集合越短的前缀越容易获更小非负SSE，极短prefix还可被线性函数精确拟合。这不是有效changepoint估计。最直接修复是对相同已见prefix计算完整两段回归似然/惩罚并控制segmentlength，或在线状态空间/GP转折预测；它们都是普通方法，修公式不能产生新机制。

还需区别三种命题：

- 原作已发表于meanCRO→DOX有时间窗口，不证明每一population的g都单调到某天再翻转，也不证明同一个k*存在。
- 即使一个turn存在，单个prefix可以同样兼容未来继续下降或立刻反转的曲线；没有跨任务先验、动力学约束或可识别信号，不能从过去g自动确定未来turn。bootstrapCI不含端点只描述拟合/假设条件，不是“world”已发现因果前置条件。
- 同一天先实测DOXresponse，再用该response选当天DOX并把这条已测效用当预测命中，只是复用已购结果。可以在其他已见populations上学日程，在新population或合法futurecut上评估；或允许付费prefixprobe后预测后续samplebranch，但必须冻结querycost、cut和未参与拟合的真结局。

这里的真实应用仍有价值：在固定CRO适应方案下，用较少前期DOX挑战预测稍后DOX24h功能或选择待复核日。无需强求postchallengecontinuation就可研究**定时挑战**；若要长期切换并继续演化策略，则必须有其真实结局。最强比较者是lastIC50/persistence、day/actualdose、局部线性/普通changepoint、directmulti-horizon、相同history的state-space/GP、source-knownwindow的固定日程以及等预算activequery。所有published窗口与作者设计先验都应共享，不能只给候选。

把符号翻转规则/斜率先验跨population迁移，是普通pooling/meta-estimation；20populations来自一个selection/challenge背景，尚不能直接声称跨研究任务/多代RSI。更低IC50且query不增是**最终policy效用**，不是improver更会改进。**无可挽救的最小新操作。**

## Data与分层证据义务

源身份/功能代理正在核验S1Data，本文未重复；读取代码仅认证additiveprofileMDP与oraclefuturecondition，未读取CSV/MAT/pickle/工作簿响应。主实验5选择药×4replicates×day2/4/6/8是phenotype菜单；CRO14d×20populations的每日DOX挑战是独立实验。二者不能混成20×5或多数独立futuretasks；evolvedmolecularstate仍未认证。

| 所求层级 | 对DeepSeek提案现有什么，真正还须什么 |
|---|---|
| WM | 候选1的c不是细胞目标；候选2的g/turn存在只证明描述。须同prefix/paidstate/辅助监督下，显式transition或其新更新超出强direct、ordinarydynamic/refit/continual与simpleblend，在真实未查询function上有实用增益。两提案未给独有操作。 |
| Agent | cost与budget记录应共享；same-model固定设计、cost-awareAL/KG/MDP和等预算程序搜索必须完整比较。候选的cost-awareobjective或changepointschedule本身属于这些基线。 |
| 继承 | 共同model/program/history起点移植实际程序，胜restart、参数/权重迁移、retrieval、蒸馏与meta-estimation；同drug缓存、共享h_hat或更强初始policy不足。 |
| 联合 | direct/world×ordinary/adaptive2×2且联合臂超过最强完整ordinary系统，不以“joint优于each单独”取代同信息总比较。 |
| improver/RSI | 冻结m0/m1，从同taskprogram/model/history用同kproposal/evaluation/query产生后继，再在更后未优化任务评**改进—成本**；m2/m1另比、形成成本计入。提案当前只给m1最终query/IC50改善，未定义或验证改进策略本身。 |

继承/RSI没有资格不禁止有用途的窄预测应用；但相应结论必须保持NOT_TESTED，不能因为“之后可以继承代码”提前立项新架构。

## 决策及哪些事实不会挽救新颖性

停止两个候选作为核心创新；无需为了证明knowncost或普通changepoint有用而打开response。若根代理基于独立应用目的做有限predictionqualification，应明确与此新颖性NO-GO分开，先锁定具体manifest/cost/cut和强baseline。

c可被准确预测、含costpolicy比忽略cost强、时间曲线有turn、prefixforecast比oracle限制下旧模型好、日程移植后最终policy更优，都不自动挽救本次新操作失败。只有提出不同于known-costMDP/AL或ordinarychangepoint的新识别/推断/成本性质及其真实观测条件，才有另审理由；当前**none**。本稿初稿尚未读取反方，因此不是共识，后续实际交叉会另追加。

## 实际交叉附录

独立稿保存并通知Root后，读取`DEEPSEEK_SKEPTIC.md`，收到反方三项具体提问并逐项实际回复。双方初稿独立于对方，但Root提供共同提案/来源，非blind评审。无HTTP、response、拟合或proposalcode实验。

1. **原定义内存在未知cost或新update吗？** 没有。支持方明确接受 `E[c|s,a]=1[a∉Q]`、`Var=0`；同信息cost-awareAL/beliefMDP逐步覆盖。若另考虑培养失败、重复次数、delay等随机cost，需要真实attempt记录且已改变原定义，仍先对齐ordinaryconstraineddesign；不能拿这种未给出的新对象挽救原提案。
2. **fixedprefix修复后什么不等于ordinarysegmentedregression？什么观测预见futureturn？** 当前没有。接受反方hinge形式 `α+βk+γ(k−τ)_+` 的具体归约；τ>T时所有prefixhinge为零，尚无已认证前驱state打破未来τ/γ不可识别性。反方还指出相邻差分共享误差、协方差为−σ²；我接受不能由g符号多次翻转或其bootstrapCI证明稳定生物机制。没有用外部模型生成的“前置条件”标签代替额外观测。
3. **哪一个I0→I1被编辑，在哪些后续机会测改进？** 提案未定义；没有这样的实测。支持方不将较好最终policy或共享h参数当更好的improver。需要明确程序生成算子、共同起点和等资源后继生成，再更后独立任务裁决；当前none。

向反方实际提出两项范围确认：历史query顺序缺失不自动禁止合法预冻archivereplay，但不能冒充作者研究动作或真实已运行湿实验闭环；DOX24h挑战足以研究该菜单的定时挑战，postchallengecontinuation只限制长期换药/适应性多步主张。反方随后读完本稿并实际确认两项，明确三项提问已被回答、无剩余技术分歧，none只指原构造新核心，不禁止独立窄预测/分配pilot。此为收到的真实回应，不把沉默当同意；双方一致仍不是生物学证据。

本次没有未解决的可挽救新操作；未解决的是普通prefixprediction/AL在真实cost与schema合格后是否有应用增益。该问题需另有明确应用投入理由，不因两个候选被命名为world/agent就自动开值，也不把此次定义审查当真实生物阴性。
