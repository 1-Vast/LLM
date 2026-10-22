# 独立机制支持稿：当前没有可晋级的新操作

2026-10-22，Asia/Shanghai。角色 `/root/mechanism_advocate`。本稿先于读取本轮反方稿完成；未读其未来提案、未开HTTP、未读取新的响应或图、未建代码、未跑训练/API。遵照有界任务最多审查两个构造，不以新模块补足新颖性。

**结论：`NONE_SURVIVES_AS_CORE_INNOVATION`。** 当前最有生物意义的方向是用单基因干预screen约束真实进化谱系的状态—功能关系，但尚未给出区别于同信息核条件更新或常规突变—选择模型的新操作。以下两项是被审查并未晋级的构造，不是两个获准实现的候选。来源资格继续有独立价值；不应为本结论下载FASTQ或启动完整Agent。

## 依据与暴露边界

读取本source `REPORT.md`、本人上一轮state-split `CROSS_ADVOCATE.md`、TG时钟 `DECISION.md`、20261021 `autonomous_rsi_round1/NOVELTY_ADVOCATE.md`、`rsi_next_qualification/DECISION.md`，以及 `research/REPORT.md` 头部和 `log/archive/HISTORY.md` 的可见关键段。批量长输出有截断，未声称逐行读完全部历史。没有读取本轮skeptic稿。

历史已排除把timewarp、history predicate split、残差核、普通refit/混合、固定seed知识库和可编辑程序/元程序本身当独有贡献。Beat AML支持过真实功能反馈，但同信息ridge/offset可解释；PTV轨迹、PRISM提案/更新和若干程序继承没有显示所求增量。Hyperagents/AIDE²/SpecRSI/MetaShare的既存核验见20261021独立稿：任务程序与改进程序可编辑、从历史继承、共同起点测后继改进本身已有先例。本文未新检索这些论文，也不扩大其原有全文/摘要访问层级。

本source已认证：3,904mutants×40drugs的筛选后静态s-score来源；23drug/12lineage实验进化及70/634选择后pair的功能验证方法；Zenodo文件名只有Tetracycline的12lineages×day3/5/7及WT。真实谱系状态与药敏逐样本join仍未认证。不能从Methods中几个已曝光的功能assay/基因名字构造事后“新发现”。

## 审查构造一：把支持药敏残差写回遗传干预坐标

应用设想：新进化谱系已有WGS/遗传状态，购买少量真实药敏反馈后，重新排序尚未测量的伴随抗生素，避免将当前已耐药的药物误列为有效partner。遗传screen的作用是为跨药传播提供干预特征，而不是给药敏标签改名。

最小操作可明确写出。令 `S[:,a]` 是仅用允许训练部分形成的基因删除—药物效应向量；对谱系当前预测参数 `u`，已购支持药集合Q的残差为r。执行一次带正则的最小改动：

    Δu = S_Q (S_Qᵀ S_Q + λI)⁻¹ r
    Δŷ_a = S_aᵀ Δu

若带先验协方差C，则只把内积换为 `S_aᵀ C S_b`。这确实是可执行更新，也允许生物上透明的gene坐标；它不会因为不是全量重训就成为新算法。

**具体等价基线**：定义 `K(a,b)=S_aᵀS_b`，则 `Δŷ_a=K(a,Q)(K(Q,Q)+λI)⁻¹r`，与相同遗传特征的kernel ridge/线性Gaussian posterior conditioning完全相同。gene空间的稀疏化是sparse regression；只允许更新少数gene block是结构化regularization；低秩压缩是常规factor model。这是构造性的相同诱导行为，不是以“NN可以拟合任何函数”泛泛否定归纳偏置。

如果另加 `ŷ_a=f(g_t,a)` 或多任务头，强直接模型得到同样S、g_t、history和辅助监督即可；本操作没有状态转移。它可能改进药物排序，但那只证明遗传特征/功能反馈和有限参数族有用。与原论文OCDM不同之处是引入了目标谱系支持残差，而非单纯计算两drug chemical-genetics profile相似性；该差别被上述普通条件核基线完整覆盖。

继承S、C、λ或稀疏gene集分别是共享先验/权重、hyperparameter transfer或feature selection。继承“何时用哪一种更新”是普通meta-learning/selector。让LLM改这些对象，或从未来任务损失学其选择，不额外产生不同于等预算程序搜索的操作。**新颖核心：拒绝。**

## 审查构造二：用遗传干预锚定药物选择下的突变群体转移

应用设想：已知早期进化群体的遗传状态，预测继续某抗生素选择后哪些未测partner仍保留敏感性，或提名能阻断特定耐药路线的adjuvant target。真正待证的是：explicit evolutionary rollout是否比同信息直接预测未来药敏更省反馈，而不是“会模拟所以是世界模型”。

最小操作：状态为真实haplotype频率q，而非把不同gene的边际变异频率假定为独立细胞。设 `Fθ(h,a)` 是drug a下haplotype h的繁殖fitness，M为mutation transition。一次固定暴露步为

    q⁺ = M [q ⊙ exp(τ Fθ(:,a))] / 1ᵀ[q ⊙ exp(τ Fθ(:,a))]

再由相同群体的药敏readout `Hφ(q⁺, b, assay)` 预测partner b的功能。删除screen可以约束 `Fθ(h_KO(g),a)-Fθ(h_WT,a)` 或H中的相应效应，但不能直接令 `F=S`。

**具体等价基线**：这是常规replicator/mutation–selection transition与genotype–phenotype readout。取additive gene effects即可得到普通加性突变选择模型；加入pairwise epistasis是普通epistatic fitness model；估计F/M/H是常规系统辨识/particle filtering或重训。有限动作的lookahead/MPC、posterior sampling或稳健控制可使用完全相同模型和screen先验。当前没有给出新的selection算子、识别条件、计算性质或样本保证。它与已停的timewarp/state-split不是同一个模型，但“不同于上一候选”不等于已有可辩护的新颖性。

更关键的是此处需要的生物映射尚不存在：

- 单基因删除≠进化point mutation/调控变异/部分功能缺失；删除效应可以与真实allele相反。若把未知allele统一映射成loss-of-function，就是本方法核心假设，不能假装是观测。
- s-score相对mutant跨条件median的modified t-statistic，不是每代fitness，也不是IC90。任意直接指数化s-score没有量纲/测量依据；需要允许数据中的校准或原始growth与assay映射，所有基线共享。
- 群体WGS通常给边际variant frequency，未必给haplotype。两个不同haplotype混合可有相同边际频率但不同多基因fitness；不能靠将它写成世界模型解除不可识别性。
- 本实验每天从最高生长浓度选择并转移，action依赖过去OD。只有day3/5/7与固定selection protocol的状态不能任意识别所有drug-switch转移，更不能模拟未测switch后把模拟值当真实反馈。
- 当前WGS文件名只覆盖Tetracycline。12lineages与3timepoints不是36个独立跨药研究任务，不能支撑从一种选择药推断广泛任务继承或递归改善。

这些问题不会由加一个gene-language encoder、元智能体、记忆库或“可编辑动力学”解决。若校准/allele映射/状态join日后成立，这个常规模型可能有应用价值，并值得与直接预测严谨比较；**当前新颖核心：拒绝，动态可识别性：未资格。**

## 哪些可证伪研究问题仍诚实存在

这不是批准实验。若根代理出于独立应用理由继续，先只回答source身份和上述假设资格，不能因它们通过就重开新颖性。所有后续比较使用同一实际反馈菜单，用户的WM、Agent、继承、联合、RSI目标分别裁决：

| 待证增益 | 可证伪主张与必需强对照 |
|---|---|
| 信息/遗传锚定 | 在未查询partner、完整lineage单元上，S与真实状态增加预冻药敏决策效用；对比原论文OCDM、drug identity/MoA、same-S线性/核/boosting与强非线性direct。增加训练或目标测量不算结构独有收益。 |
| WM转移 | 固定相同支持反馈与输入，显式mutation–selection rollout的未来功能决策超过同状态/history/direct多任务、普通动态系统、纯终点与简单混合；再与同一普通selection算子比较。若只胜过无WGS模型，仅证明测量信息有用。 |
| Agent | 在同模型、同真实功能菜单、同预算下，候选研究程序超出固定SOP、exploit-first、AL/model-discrimination、MPC和等proposal/evaluation/compute程序搜索。当前未提出一个预期能做到的独有操作。 |
| 继承 | 从共同task程序/model/history起点，移植具体程序的净收益超过restart、先验/权重移植、案例检索、蒸馏与同历史常规拟合。目标药标签记忆或更强初始模型不算程序收益。 |
| 联合 | direct/world × ordinary/agent的2×2，最终联合臂超过最强普通系统，且不是仅有交互项或更多观察。 |
| RSI | m0/m1从同一model/task程序/history，等k提案、评估、真实query形成后继，在更后未优化任务比较改进—成本曲线；m1/m2另比，并计形成meta的成本。这是必要实验要求，本文不把共同起点设计当新算法。 |

具体应用终点应是固定真实assay预算下，未查询partner在未参与更新的真实谱系上经药敏确认的效用，或在合法trajectory菜单下未来功能预测引发的选择效用；不把已购支持测量计为传播命中。真正独立任务不足时只报告有限development，而不从技术重复制造transfer/RSI样本量。若只有静态终点菜单，仍可做跨实验研究反馈；不要求相同colony分支，但不能额外声称drug-switch control已认证。

成功条件必须在任何数值前由可达误差/实验成本决定 `δ_use` 与任务级精度，冻结强比较者和效用；区间下界超过δ且联合臂绝对获胜才支持相应层级。当前不知道独立task数量和query单位，不编造一个数字门槛或声称此资产已经有能力检验它。

停止条件具体为：删除→allele/fitness校准不成立则停该运输假设；状态—功能join失败则停该source的WM实验；普通核更新复现构造一的全部输出则停止其独有贡献；普通selection model复现构造二则按常规模型应用报告；预冻同信息对比上界低于δ_use则无实用增益，宽区间为INCONCLUSIVE；没有足够未来独立任务则继承/RSI保持NOT_TESTABLE，不用更多程序编辑替代。

## 本轮决策与交叉评审问题

当前没有可交给程序搜索的“可信最小新操作”。建议先保留source metadata/identity核验，拒绝为上述构造搭建Agent或下载WGS。也不要求反方证明所有未来方法都无新意：本次拒绝只因为两个具体构造都已有明确普通实现，且缺少新的识别/成本性质。

向反方的可裁决挑战是：是否存在一个**不能被上述确切kernel update或同先验mutation–selection基线实现的最小步骤**，并说明它需要哪项真实观测来证伪？若回答仅为更好的gene映射、更灵活epistasis、学更好的experiment selector或继承元策略，则须分别对齐普通representation learning、fitness inference、amortized design、meta-program search，不能以组合名称作为差异。

本稿不把科学谨慎变成对全部应用的否定，也不把来源完整当方法新颖性证据。后续若出现真正不同的操作，再审查它；两个被拒构造的数值阳性不会自动改变本轮核心裁决。

## 独立稿完成后：读原论文叙述的资格补充

上文独立初稿已保存并通知根代理后，收到其新增明确授权，继而读取 `LITERATURE_SCOPE.md` 与 `NARRATIVE_LITERATURE.json`。首次长JSON输出截断，随后只从相同本地JSON定向完整读取Results段15/16/18/19及Discussion相关段。无新HTTP、源表、FASTQ、数值数组或代码文件。此新增阅读包括已发表性能与生物结果，明确全部为 **published/design-exposed**，不是本项目盲实验；不把作者结果当本项目证据。

读源前，两个构造已因具体普通方法归约而被拒；readout exactjoin未认证。读源后，**新颖性拒绝加强，来源叙述资格改善**：

1. 原论文本身的Fig5标题已是“Chemical genetics recapitulate the dynamics and explain the mechanisms of non-monochromatic interactions”。12条TET进化谱系的TET/AZI药敏按Fig5a图注展示day2/3/5/7/10；Results另称每个passage测定，不能把其文字和图中五时点当成已认证的十时点完整源表。群体测序覆盖同12条谱系的day3/5/7。作者明确解释hldE/waaD强CS路线随后由waaF或marR等弱CS/XR路线取代，target mutation与混合群体也能产生neutral phenotype，并做删除株IC90和tetracycline uptake机制验证。**“删除screen揭示进化选择路线、状态改变解释未来药敏”不是本项目新生物机制。**
2. 原论文OCDM的concordance优先规则已经以异质群体在第二药下XR菌群可压过CS菌群作解释。把它改称population-aware world state不能声明新颖。本文构造二的explicit forward transition并非原文已给出的定量算子；我不声称原文做过相同公式/预测评估。但新增的公式属于普通mutation–selection模型，所以仍无独有贡献。
3. 作者Discussion已明言single nonessential loss-of-function screen不能覆盖gain-of-function、essential target mutation和epistasis，并提出相应扩展。仅把这些限制改成一个可编辑模块、增加多基因项或“发现KO与真实allele差异”也不能作为新问题独占。需要新的可验证识别或高效推断步骤。
4. 更准确的最低成本纵向源表为 **Source Data Fig5 / `41564_2024_1857_MOESM9_ESM.xlsx`**；Fig4是class汇总。原source报告中的MOESM7仍适于70pair终点菜单，但不能把它说成真正纵向状态—功能表。这个源对象修正并未打开工作簿，gene/lineage/time/assay的数值层exactjoin仍待schema认证。

因此本稿不是“因不知道有纵向数据所以说无机制”。已发表的纵向机制现在明确存在；缺少的是一项区别于原作者生物解释、普通选择动态和同信息条件学习的最小新操作。**最终结论维持 `NONE_SURVIVES_AS_CORE_INNOVATION`，不为以上两构造启动新模型/Agent或数值搜索。** 可以按独立应用目的核验Fig5 schema；其通过不会自动重启新颖性主张。未读本轮反方稿，尚未开展本轮交叉辩论，不能把此独立结论写成多方共识。
