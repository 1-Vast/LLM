# 独立反方：更新价值机会、可靠性与普通等价

2026-10-22。先读本phase PROTOCOL、冻结AZ DECISION、latest-literature DECISION及历史EG-RPT PROTOCOL/POSITIONING/NOISE_HEADROOM，再写本稿。**未读本阶段其他新评审稿、根历史audit数值输出或三份待审历史records**；未接触raw/reserve、未新fit、未调用provider。根代理在独立写作期间告知旧records已有两套synthetic-probe-noise结果，拟先冻结posthoc审计；我的方法意见已实际回传，但没有先看其结果。随后根通知审计已执行并另行授权我在本稿封存后独立重算，本稿仍不含其数值结论。

**裁决：GO最便宜的已exposed历史输出资格审计；尚不能GO新生物拟合，更不能GO新RSI核心。** 最小问题值得问，但“任务不同→更新价值不同→学选择器”的机制本身已被algorithm selection/contextual meta-learning/learned optimization占据。先证明可用异质性，再证明合法信息可预测性，最后才问特殊功能表示是否提供贡献；这三步不能互相代替。

## 1. 对已完成阴性和未执行旧稿的约束

AZ当前effect残差压缩在完整96MASTER覆盖下输给strongdirect，两个主门都失败；停止该配置的agent/RSI扩展。effectvsdose的较小归纳偏置收益可保留，但不能变成本阶段更新策略机会的证据。固定episode offset不改固定base的actionrank。原413reserve数值不打开。

历史EG-RPT已经明确提出split-noise rank agreement和cross-draw oracle-minus-fixed门；该想法不是本次首创，也没有因写过protocol而变成执行证据。旧33.5best-of excess等于绝对差总和的一半，不识别真实可选收益；与matched-Gaussian的相似也不是“全部为噪声”的统计证明。13历史study记录/4依赖组/6不兼容单位不是足够的策略训练panel。旧稿把syntheticnoise分支叫两独立probe-noise draws最多表示模拟扰动条件独立，绝不等于两独立技术replicates。

## 2. 精确一手前驱和实质差异

本轮恰4GET，两个arXiv Atom metadata响应、两篇完整primary HTML。URL/status/body/hash见HTTP_RECEIPTS/SOURCE_MANIFEST；完整body与有限定位excerpts均保存。新全文核读是针对method/assumptions，不声称重现论文实验；下表严格区分全文与abstract证据。

| 前驱 | 实际核到的机制 | 对当前候选的约束/差异 |
|---|---|---|
| SATzilla: Portfolio-based Algorithm Selection for SAT，arXiv1111.2249v1（primary Atom abstract） | 按instance特征预测solver表现并构建优化指定目标的portfolio | 已有per-task选择operator；换成细胞task/update不自动新。未读全文，不引用细节或理论保证。 |
| Meta-Learning for Contextual Bandit Exploration / MELEE，arXiv1901.08159v1（primary Atom abstract） | 在可模拟离线task上用imitation学探索policy，再移到真实contextualbandit；强调rich features | “在旧任务学更有效探索/表示帮助探索”已有直接先例；全信息update-table训练先是supervisedalgorithmselection，只有部分反馈才是bandit问题。 |
| Automated Dynamic Algorithm Configuration，arXiv2205.13881v1（primary Atom abstract） | 把运行中的动态参数适配形式化并作evolution/planning/ML实证 | 连续反馈下切换更新参数并非新RSIoperator；不能仅以动态controller命名区别。 |
| **Reliable Algorithm Selection for Machine Learning-Guided Design**，Fannjiang/Park，arXiv2503.20767v2，2025-07-02版（新全文） | 对有限design-config菜单，用heldoutlabel纠正设计预测偏误、density-ratio加权prediction-powered inference、multiplehypothesis/FWER选择满足successcriterion的算法，允许空集；GB1/RNA模拟设计 | 生物设计算法“可靠选择/失败则拒绝”已有直接近邻；其known-density-ratio保证不能移植到未知celltaskshift。本文不是学跨latercelltask更新value，仍需说明具体不同，而不是宣称第一种reliabilitygate。定位fragments190/192/196/216/1280/1292/1425。 |
| **Decision-Focused Sequential Experimental Design: A Directional Uncertainty-Guided Approach**，Wan/Liu/Grigas/Shen，arXiv2602.05340v1，2026-02-05（新全文） | contextual stochastic linear optimization中按归一化predictiondirection而非scale uncertainty选择labels；finitehypothesis/结构margin/optimalitygap条件下风险与stoppingtime结果 | “纠正predictionloss与决策价值错位”“只表示决策相关方向”均非新。固定cardinality topk也有scale/constant不改rank的普通几何；不能据此宣称细胞新充分状态。该文假设/任务不同，不能直接拿保证给细胞。定位fragments160/170/176/917/1972/2705/3266。 |
| Bayesian Algorithm Execution / InfoBAX，arXiv2104.09460v2（primary Atom abstract） | 有prior的昂贵blackbox下，选最大化algorithmoutput互信息的query，所求可为levelset/路径/局部最优等 | 按最终科研algorithmoutput的价值选实验已有明确原型；未读全文，不把abstract“up to500×”作本项目预算先验。 |
| Lightweight and Versatile Learned Optimization by Recombination of Gradient History，arXiv2610.09604v1（复用既存全文及前次独立核读） | 小网络重组不同时间跨度gradienthistory，跨unseentask继承update能力，无须改代码 | 更新方法可普通learnedoptimization实现；same-step不等compute，defaultAdam/SGD对照有限，较强language结果含hybridrouting，不能免费借论文transfer外推细胞。 |

现可承认的潜在差异仅是：**某个具体、可验证的干预响应结构是否改善跨细胞context的update-value预测/样本效率**。目前没有给出该结构，更没有排除普通taskembedding、容量、源label、regularization或knownmeta-learning的解释。普通bandit/controller不抹去真实representation贡献，但也不会因此变成新RSIalgorithm。新颖性裁决仍NOT_ESTABLISHED，以上boundedreview不是全领域首创认证。

## 3. 最小可证伪定义

固定task t、共同起始artifact W0、合法已付history O_t、预算B和有限普通update菜单A。以同一审计功能终点定义 V_t(a)=U_t(update_a(W0,O_t))−U_t(W0)。所有a共享O_t/权限/预算起点；执行新的生物观测另收费。反复fit同O_t是计算，不是新反馈。两paidwitness+sealedtarget不能虚构多轮audit反馈。

先只需2个有实际不同作用的ordinaryupdates，例如固定完整重训练与固定regularizedlocaladaptation；identity/W0同时作固定锚。具体名称只有取得source/起始模型/真实feedback合同后才可执行，当前不注册新fit。不能用函数等价、仅episode常数或几乎相同的输出菜单制造智能体选择空间。

必须分开三问：

1. **可用heterogeneity**：同任务上不同update的value差异是否能在另一次评价/扰动中保持，使按第一次选法在第二次真正优于强fixed？单个hindsightmax−mean不是证据，rankcorrelation也不能替代净utility。
2. **合法可预测性**：只看动作前可得O_t/metadata的冻结selector，能否在未来完整taskgroup上胜由source训练选出的fixedpolicy？即使firstquestion有机会，descriptor未必含足够信号。
3. **特殊功能表示贡献**：与同原始信息的充分优化普通selector比较，functionalrepresentation是否仍有样本效率/transport增益？“只拿worldembedding的bandit”不等于排除“所有raw信息的strongselector”。

## 4. 最便宜现在可做：历史cross-synthetic-noise审计

根告知 `feedback_propagation` 的fold2/3/4旧exportrecords已有 A_B3和C_noise_seed2，含ridge/R1的unmeasuredcampaignhits/compounds/family/index。按根拟冻结合同先做schema/hash/共同key/complete64campaignjoin；不读raw、不生成新noise、不重新fit。不得通过discard表现差task或改变completecase规则扩大机会。

令U_r(t,a)为drawr在完整64compoundcampaign内的hitcount（单位events/64，数值不再除64）。第一次draw按最大U_1逐task选a_1(t)，exacttie固定ridgefirst；评价G_1→2=mean[U_2(t,a_1(t))−U_2(t,a_fixed,trainingfolds)]。反向另算G_2→1，再报对称均值。fixed在另fold/leave-one-fold、仅从选择方向的训练draw确定；此外分别列alwaysridge/alwaysR1两固定法，另标全测试hindsightbestfixed为描述性anchor而非可部署训练选择。不能把test2全局maxfixed伪作source-selectedbaseline。

**关键资格限缩**：a_1(t)读了该task隐藏终点U_1，是不可部署hindsightselector。它只审计相同Y/设计下syntheticprobe扰动的稳定选择机会；既不是legalfeatureselector，也不是实测measurement重复。它也不是真oraclevalue的严格上界：噪声argmax可能比知道真实ranking的合法descriptorselector更差。因此失败支持“本预算下没有继续训练这个菜单的证据”的局部资源决策，不是数学证明任何selector不可能。

报告两个方向及每fold收益、每task差值、ties、正负反转、exactsignagreement、相对两固定及hindsightfixed、同64分母和所有排除原因。统一outcome尺度，不把querymeasurement误加成auditlabels。campaign含混合family且fold/lineage共享，不能按36campaign普通bootstrap或把两方向当两独立重复提供CI。先不报这种伪CI，列descriptives/支持范围即可。

历史δ*=0.1875events/64可作为沿用的有用尺度，须明确是历史内部尺度而非新source的实测噪声/药效门。建议预算停止：若两个方向任一≤0或对称净gain≤δ*，不训练这个2update菜单的selector；若超过只记CONDITIONAL_OPPORTUNITY，仍需下节合法featuresheldouttask检验，不能宣称实测重复/可泛化improver。本稿阈值建议须由根审定登记，不能事后选择方向/threshold；根已执行合同以其事前冻结规则为准，不能据本稿修改已冻分析。

## 5. 新source上的最小可靠性与普通等价门（尚未注册/执行）

sourcequalified后优先固定已有support，分别在**同条件独立audit技术/生物重复**评价同两个更新输出，识别scoremeasurement可靠性；若也要检验supportnoise，再另分支用重复support更新，明确随机性来源。drughalves、不同gene集合、不同dose或donor不是同干预条件的技术replicates；可合法叫intervention-panel泛化/空间迁移，但不能说测量重现。若没有真实重复，就只能作有限split-generalization和syntheticstress，不伪造已测noise分布。

最小价值门不必硬加“rankaccuracy>70%”这类无单位阈值。冻结一个application-unit实际有用margin δ_app，主要条件为跨独立audit的**净utilitygain≥δ_app且合法cluster95%lower>0**；sign/rank/reversal只是诊断。δ_app须由新任务实际用途/测量/费用确定，不能把AZ.02或历史.1875移植给RNA/morphology。样本量以真正独立taskgroup计算，例如80%power的保守规划 N≈[(1.96+0.84)σ_group/δ_app]^2，用独立development估计σ，不能用无数cells或drughalves代替N；若group不足或CI覆盖δ_app，结论不足以继续昂贵扩展，而不是把零显著性当零效应。

有可靠机会后，仅训练一个小的ordinaryselector（regularizedvalue-regression或nearest-taskretrieval，不先加LLM）。来源训练的全信息updatevalue-table和其全部fit/label费用同供对照。冻结后在未见完整cell/donor/plate/sourcegroup上检验，至少比较：bestsourcefixed、random、简单predeclaredcontext规则、raw全信息regularizedselector/检索、强directpredictor、普通重训练/CL（若确有sequence）、AL（若确有带费query）、simplemixture、all-in equal-budgetfiniteprogramsearch。要测试哪个update好，不应让selector免费试尽所有targetupdate再只计最终一次成本。

保持world有无×policy有无和初始/继承solver×old/newpolicy的swaps，另报真实jointproducts。C4要求在后续task从同artifact/初始history/权限/总预算比较old/newimprover，source策略训练与继承payload明示并给普通meta方法同权限；之后history因action可分叉。静态action-conditionedworld合法，C4不要求无限加速，joint不要求superadditive。若onlyworldrepresentation有用，保留representation贡献；若sameinformation普通selector解释全部收益，停止“新RSIoperator”主张但保留真实ordinaryC4。

## 6. 明确停止条件

- 无legalfeedback与protectedaudit分离、taskjoin不明、伪replicate/伪task独立、预算漏计：资格STOP，不把其包装为性能阴性。
- 已冻结历史crossdraw门不支持有用选择：STOP该二update菜单的selector投入，不打开AZreserve或重新选择噪声种子救结果。
- 可靠value异质性存在但合法featuresselector不胜fixed/普通retrieval：STOP“可学策略机会”，不能以hindsightheadroom补证。
- 只有同raw信息普通bandit/meta/learnedoptimizer即可复现：STOP新algorithm核心，保留限定结构/普通能力结果。
- 新sourceprotectedtasks未过δ_app及clusterlower门，或独立taskpower不足：停止此配置扩展，记录全部失败，不增加agent模块救exposedtest。

截至本稿，无新机制或可继承improver能力已建立。最小nextaction是根已冻结且完成的历史输出审计的独立核验；随后实际cross与根决定，不提前开新数值任务。
