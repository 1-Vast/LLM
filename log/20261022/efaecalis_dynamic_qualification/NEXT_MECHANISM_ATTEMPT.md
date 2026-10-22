# 一次窄再设计：不猜相位，能否直接判定药物排序

2026-10-22，Asia/Shanghai。独立初稿；只据此前已读来源资格、代码I/O与机制关闭记录和Root本次列出的资产范围。本次不读取任何新响应、即将产生的E.faecalis pilot结果、未来评审或未授权文件；无HTTP、DeepSeek、训练、作者代码执行或新研究代码。此文件不修改任何历史STOP。

**结论：`NONE_AS_NEW_CORE_OPERATOR`。** 最强严肃尝试是绕开单条haplotype猜测：把所有与已测边际变异频率相容的真实群体都纳入，只有它们对第二药的功能排序一致时才作选择。它不同于前次被撤回的点估计selection rollout，但其确切推断归约为普通Fréchet/moment约束下的partial identification与稳健优化；现资产又缺少使边界非空泛的克隆功能校准。没有新的识别或样本性质可支撑晋级，不加Agent层救它。

## 唯一尝试的操作

应用限定为体外抗生素功能复核：一个进化群体只有unphased variant frequency时，是否无需猜测哪些突变位于同一细胞，就能可靠决定该优先复核哪一个challenge drug。不是声称患者疗法或任意多轮换药。

设有限候选haplotype为h∈{0,1}^G，未知群体比例为q_h，测得每个variant的边际频率p_i。以真实可认证的频率误差区间[ℓ_i,u_i]形成

    Q(p) = {q ≥ 0 : Σ_h q_h = 1,
                    ℓ_i ≤ Σ_h h_i q_h ≤ u_i for each i}.

若有独立校准的、固定选择暴露a下每种haplotype增长倍数w_a(h)>0，以及challenge drug b在浓度z下的克隆功能g_b(h,z)，且该assay允许由clone比例线性汇总，则选择后群体的challenge读出为

    Y_b(q,z) = [Σ_h q_h w_a(h) g_b(h,z)] / [Σ_h q_h w_a(h)].

**操作只有一次求界**：对所有q∈Q，求 `min/max Y_b(q,z)`，或者直接求两个候选药物效用差的最坏界；仅当 `min_q[U_b(q)−U_c(q)]>0` 时称b对c的排序已被当前信息确定。若不确定，则保留未决，而不输出一个伪精确haplotype轨迹。比较不同challenge浓度或IC90时，必须先有匹配的dose–response/归一化与单调性定义，不能把一个gene s-score直接代入这个Y。

这个操作消除了前次q-forward中无根据的linkage-equilibrium closure，也不需要预测所有中间state才作功能判断。条件上可能存在实际价值：haplotype不完全可识别，但药物排序仍可能在所有可行coupling中相同。这是一种可以失败的**决策可识别性问题**，不是提出一个有新名字的潜state。

## 最接近普通方法的确切归约

在不继续选择、直接测当前群体时，Y对q线性；求上下界就是带marginal/moment约束的普通linear program。上式有相同正分母，是普通linear-fractional program；令 `t=1/(Σq_hw_a(h))`、`v_h=tq_h` 即得到线性目标与约束，属于标准分式优化变换。若w/g也不确定，在其允许集合上再取界就是普通稳健partial identification，不自动产生新算法。

此处不以“万能NN能表示一切”否定结构，而是逐项写出ordinary solver可产生相同上下界、同排序certificate。若把下一次实验选为最缩小界宽/减少最坏regret的项，就是普通active model discrimination/稳健实验设计；继承约束集或校准分布是普通constraint/prior transfer。LLM搜这些规则与Hyperagents类元程序搜索的区别仍未出现。

能成立的覆盖性质也只是条件性的普通性质：真实q在Q、真实w/g在校准集合、assay组合假设成立，则真实功能落在所求界内。若频率区间有jointcoverage，以上可随之得到coverage；这不提供一个新有限样本定理，更不保证界窄或query省钱。尚未给出新的求解复杂度、紧性识别条件或超出普通优化的样本性质。

**为何比口头说“相位有影响”更明确：** 两位点的任意克隆表型都可写为

    g(h1,h2)=α+β1 h1+β2 h2+γ h1h2.

由边际p1,p2只能得到 `E[g]=α+β1p1+β2p2+γq11`，其中

    max(0,p1+p2−1) ≤ q11 ≤ min(p1,p2).

若γ已知，sharpuncertaintywidth为 `|γ|·[min(p1,p2)−max(0,p1+p2−1)]`。若γ=0，当前meanphenotype对phase不敏感；若γ≠0且marginal允许多种coupling，一般不能由marginals点识别。该简单推导是标准moment/Fréchet结构，不是本项目新定理、运行结果或生物证据。加入选择后的ratio还可能让原先加性的challenge在未知phase下产生不同未来结果；不能以当前additive就默认未来可识别。

这也显示为何只测单KO不足：g00、g10、g01即便都在相同功能单位测到，g11/γ仍未知。若不限制γ、w或群体相互作用，很多看似精细的频率约束仍会留下几乎整个功能范围。给未知γ任意小先验会缩窄区间，但那是额外假设，不是source信息。

## 现有三资产能否否证它

| 已有资格资产 | 真正可能提供什么 | 此尝试缺什么，不能默补什么 |
|---|---|---|
| chemicalgenetics与TET12lineages/day3/5/7 genomic图 | 遗传干预效应、populationmarginalfrequency与对应TET/AZI功能的潜在join；原作已有演替解释 | 实际allele≠单基因KO；s-score≠每代w或cloneOD；多突变g/epistasis、远变异phase、knownmixture的readoutadditivity未认证。图上同号lineage不解除这些缺口。 |
| TG-GATEs人肝48药/144完整条件、2/8/24hRNA及功能身份 | 相同暴露菜单内earlymeasuredstate→laterfunction的有限预测资产 | RNA不是已知细胞组成/clonefraction；没有以RNA分解为真实componentq的身份与purecomponent功能。把latentRNAfactor当q会变为自由factor model，失去上述可识别约束。不能把人肝与E.coli基因干预合成一个干预calibration集。 |
| E.faecalis phenotypicprefix→laterchallenge | 多药/时间的功能history，适合正在准备的smallridge资格 | 没有已认证genomicmarginalq/phase或纯clonew/g。原作additiveprofiletransport并不提供这些量。把预测collateralvector当q会回到普通多输出预测与原MDP。 |

本操作的最直接反证本来应是：用独立校准的w/g与真实marginal构造Q后，未参与拟合的同群体真实challenge落在界外，或certificate排序与功能确认相反。这会否定校准/组合/运输假设至少一项；若能逐一分开测，可定位哪项失败。但**当前资产不能建立这种已校准的预测集合**，所以不能先画一个任意窄界，再把某几个点落入当验证。

即使化学遗传学数据将来逐样本join成功，它最多先允许检验一个具体受限additive/LOFphenotype模型；没有所有haplotype真值时，多个宽界都包含观察也不证明上式机制正确。要估计sampleefficiency，必须有实用query/确认单位与可达到的界宽；当前不知道，不编造一个数字收益门槛。

因此此尝试不是“因缺phase就一律禁止任何预测”。marginalfrequency/phenotypehistory的强direct模型仍可做有用途的窄预测，不需识别q；被拒的是以未校准Q/w/g声称有一个新机制与distribution-freedecisioncertificate。

## World、Agent、继承与improver仍缺哪些实验

如果以上输入日后真实可获得，普通LP/分式优化就是同信息主比较者；一个候选只有给出不同的新限制/推断性质才有新机制可比。可检验world结构的角色是约束真实futurefunction：固定相同prefix、state测量、辅助监督与query，超过directmulti-horizon、普通动态/refit/continual、普通robustbounds与simpleblend；宽而无排序的界不能当高质量world。

Agent必须在同一model/Q/w/g和真实feedback菜单上超出固定design、cost-awareAL/robustdesign及等proposal/evaluation/compute程序搜索。certificate本身由解优化直接得到，不必先加Agent；保存一个优化结果也不等于学会研究程序。

继承至少需多个独立适用背景中可运输的已验证约束/实验程序，并在共同model/program/history起点胜restart、sharedprior/weights、retrieval与蒸馏。单TET的12lineages或CRO/DOX的20populations不能自动供多层元改进任务，更多timepoints也不是更多独立研究。

改进策略本身需明确I0→I1编辑了如何产生/验证以后更新；冻结I0/I1从同一起点、同k修改/评估/query生成后继，再更后未优化任务比较改进—成本，I2/I1另比，计形成成本。当前连一个不同于普通robustdesign的I都没有，更没有这些任务；最终bound变窄或policy更好不代替improver更会改进。

## Go/stop

**停止此尝试作为新核心，不为其开新response、源下载或架构。** 它是对已知partialidentification/robustoptimization的一次有明确生物对象的应用构造，且目前连有效校准和可否证输入都缺。把“只在所有phase一致时行动”当新口号不能补足贡献；添加epistasisnetwork、LLM与metamemory也不能补。

此次最强留下的科学问题是：在真实unphased群体中，phase未识别是否仍允许功能排序识别？它可能有价值，但问法与LP界本身已有普通统计解释；本稿没有新的识别或样本定理，也没有现资产可独立否证其必要生物假设的办法。因此最终 **NONE**，不建议在等待smallridgegate时开启另一组数值搜索。正在准备的E.faecalis信息/持久性门槛可以按其独立协议继续，不能借本尝试阳性叙述引导其结果或重开已停机制。
