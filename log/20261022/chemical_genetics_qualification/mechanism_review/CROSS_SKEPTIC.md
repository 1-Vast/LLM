# 正式反方交叉：两构造关闭，窄时序信息问题可以保留

2026-10-22，Asia/Shanghai。已实际读支持方`ADVOCATE.md`（含其独立初稿及读文献后追加）、root `LITERATURE_SCOPE.md`、`NARRATIVE_LITERATURE.json`相关Results/Discussion/Fig5与ED5叙述、`KERNEL_AUDIT_PROTOCOL.md`和`KERNEL_AUDIT_RESULT.json`。长叙述第一次工具输出截断，随后从同一JSON定向读含population/hldE/waaF/gain-of-function/epistasis的完整段；不声称完整全文逐行阅读。全部原作文字/数字是design-exposed literature，不是本项目验证；无HTTP、工作簿响应、FASTQ、拟合。

## 原作已做到哪里，未证明哪里

比初始Methods-only稿更强的事实现在明确：Fig5标题本身就是chemical genetics recapitulate dynamics；作者追踪12条TET-evolved lineages的TET/AZI IC90，图注列day2/3/5/7/10，Results另说各passage都有测。day3/5/7测序被Results/Fig5/ED5描述为population mutation frequencies；作者解释hldE/waaD强CS路线被waaF/marR等替代，并以deletionIC90、uptake等验证部分机制。因此“静态screen可解释进化谱系的时间改变”“同药对机制不同导致XR/CS不同”不能作为项目新生物发现。

但原作的叙述解释、按day5相互作用分组的展示和gene机制验证，**不自动认证从一个合法early-cut预测later IC90时，在过去IC90/day/实际选择浓度/mutation burden之上的独立增量**，更不自动证明前向模型胜过same-information direct。这个窄问题尚可有应用价值；不需反方证明它永远无效。它是否值得投入由exactjoin、12lineages的有效任务量和实际复核用途决定，不由“原文已讲动态”一票否定。

原始Methods说“a clone ... from populations”测序，而Results/Fig5说population/frequency，两者表述不同，**本轮不替作者抹平**。需要以样本制备/具体数据格式认证到底是isolated clone、bulk population还是其他方案，不能仅凭图写frequency就假定得到完整haplotypes。Fig4是class汇总；纵向资格对象是SourceDataFig5/MOESM9，仍未开数值。

## 构造一：核等价的准确范围

支持方的线性Gaussian遗传坐标残差写回，在共同feature `S`、prior mean/covariance `C`、观测集Q与noise `R`下，

`Δu = C S_Q (S_Qᵀ C S_Q + R)⁻¹ r`

诱导的任意drug预测为

`Δŷ_a = S_aᵀ C S_Q (S_Qᵀ C S_Q + R)⁻¹ r`。

这正是`K(a,b)=S_aᵀ C S_b`的posterior/正则核条件预测。它不是“directNN普遍能拟合”的弱反驳，而是相同输入、同反馈、同不确定性下的确切函数等价。若两种程序用该相同posterior作相同query objective，也可产生相同下一实验；gene坐标可提供解释/审计实现，但不独占决策能力。

root审计覆盖4feature/covariance情形×3positive noise，共12batch cases及24个顺序检查，最大差6.4437e-13；省去非identityC的negativecontrol差1.9276。正确sequential mean与covariance同时更新、同反馈不重复计数时匹配batch。这个结果是**预定synthetic algebra/实现核验**，无biology、generalization、sample efficiency、drug utility或RSI。它没有测试zero-noise特殊逆、非Gaussianlikelihood、受约束sparse/nonnegative编辑、学得非线性feature或自适应改变S/C的全部算法；不能把它扩大成“所有遗传锚定组合都无用”。

不过，未来改变S/C、稀疏度、nonlinearfeature或观察likelihood仍必须说明具体新算子、可识别假设/成本性质，并与同样可学习这些对象的普通kernel/representation/结构搜索比较。仅离开本公式不等于取得新颖性；目前构造一没有该新增步骤，支持关闭。

## 构造二：常规模型确实可实现，生物状态仍有缺口

`q⁺ ∝ M[q⊙exp(τF(:,a))]`在M为保总量的mutation transition、F为该暴露下可校准growth fitness时，是普通selection→mutation离散步。若M列和为1，支持方分母可归一化；这不意味着它精确等于任意连续mutation-selection过程：mutation/selection的顺序、τ、dailybottleneck、响应依赖浓度选择和geneticdrift要与实际protocol一致。普通模型可实现该假设族，不能把加入这条方程本身称新增机制。

进一步，当前biology不能由方程符号补齐：

- 若source只有gene/variant边际频率，不能唯一确定多位点haplotype distribution q。single-end122bp不会自动phase远距变异；相同marginals可以对应不同连锁/epistasis和未来选择。因此“真实q已知”的输入条件尚未认证。
- s-score是跨conditions标准化的modified t-statistic，不是每代F；IC90也是population dose-response assay，不是可直接指数化的growthrate。populationIC90可能由小耐药子群主导，不能未经校准当cloneIC90的线性平均。F、M、H都从同一稀疏IC90后验解释出来时，可发生参数不可识别和循环拟合。
- KO→point/regulatorymutation并不等价，原作者Discussion已点明gain-of-function/essentialtarget/epistasis；仅提出这些模块不新。但若未来有实测运输校准，可成为独立生物/统计贡献，而非因组成部分已知就逻辑禁止研究。

我已向支持方提出具体可回答质疑：**若最终只取得marginal mutation frequencies、没有haplotype/clone–population身份，是否撤回当前q-forward构造并保留direct-frequency窄预测，还是有一个事先可检验的closure假设？F/H最少需要哪项独立测量或校准，才能避免从同IC90目标自循环识别？** 这些问题要求当前构造说明适用条件，不要求所有窄预测先解决全群体机制。

## 关于“已知部分组成新系统”的边界

我接受支持方的两个范围主张：确切核等价只关构造一当前版本；经典mutation–selection也不先验排除某种组合在真实有限数据/计算下产生技术贡献。组合若解决一个先前方法不能处理的实际识别/计算问题，或提出新约束并有新保证/同信息实用增量，可以认真评审。

当前两个构造却没有新增的coupling、识别条件、优化操作或可验证成本性质；遗传residual坐标与普通核完整等价，forward式与普通selection模型完整对应，Agent/继承外壳也没有独有策略。故**STOP是针对已写出的两个构造**，不是从“部件已有”推导所有可能组合无创新。支持方自己没有声称已经找到那项缺失操作，反方无需凭空替其发明。

## 若只做窄实用评估，什么结果仍值得保留

可保留的一个预注册问题是：在TET固定适应protocol内，从某earlycut已知的pastIC90、day、实际selectiondose、growth/technicalcovariates与mutationburden出发，新增早期allele frequencies/其变化是否改善未用于fit的后来AZIIC90功能预测，且胜过lastIC90、ordinaryhistory/directgenotype、chemicalgeneticstaticfeatures和标准动态/refit，达到实际复核有用δ。所有same-lineage时点同fold；没有预先知道的未来day5分组/authorXRCS标签进入输入。only12lineages可能只能给宽区间development，不能以3days×12扩成36独立任务。

若这项增量成立，即使ordinarydirectfrequency模型匹配显式rollout，也可报告**earlygenetic information的有限功能预测/实验复核价值**；不叫transition必要、Agent、继承或RSI。若普通kernelconditioning用chemicalgeneticfeatures在同反馈预算下省样本，也可报告一个清楚的常规数据整合应用，而不是新kernel算法。若仅重建原文hldE→waaF解释，则是复现/机制描述，不能叫发现。

没有数值开值授权或可达成本/power依据时，不为了展示正数字启动该pilot。sourceidentity/header资格有独立价值，不因两构造关闭而停止；也不因为source通过就自动重开新颖性。

## 当前建议与实际交换状态

**两构造均不晋级新颖核心，不启动完整Agent/FASTQcampaign。** 可继续已独立授权的exactidentity/schema资格；如果出现真实低成本、可改变后续资源决定的窄state/function预测任务，再单独预注册。

支持方已实际发送问题，询问我是否承认nonlinear/finitesample边界及上述earlyfrequency条件增量问题。我已回复两者均可保留，但须满足cut/join/context/power并分类贡献；同时发出haplotypeclosure与F/H校准质疑。收到其正式cross后将在下方只追加简短回应，不以未回复当共识。

## 已收到支持方正式cross后的简短回应

已实际读取`CROSS_ADVOCATE.md`。它回答了具体质疑：若只认证marginalfrequency则撤回当前q-forward，无可辩护closure；用纯加性fitness下`.5(00)+.5(11)`与`.5(01)+.5(10)`同marginal却产生不同selection后marginal的解析例说明缺口。这是正确的非充分性例，非生物验证。它将F/H独立观测校准列为最直接方案，并接受我补充的边界：可证明的jointidentifiability加独立heldout功能检验也可另评，不是所有普通预测都必须追加两项wetlab。

双方也确认early-frequency条件增量已由两稿覆盖，不是第三个新候选或“未覆盖新假设”。当前没有新增可信操作；两构造关闭，窄应用价值与source身份资格可分别保留。没有剩余关于这两个构造的新颖性分歧；真实join、统计power与实用效用仍未决，不将共识当作实验或生物否定。
