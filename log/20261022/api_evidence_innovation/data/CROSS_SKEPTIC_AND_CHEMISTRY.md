# 对两反馈修复候选的最强挑战与最小来源方案

2026-10-22。data独立稿seal后，收到skeptic已seal通知并读其INDEPENDENT.md。root已选择该候选优先，以下提出可实际推翻它的挑战，不以礼貌同意替代独立判断。未开新数值/结局。

**一、你的结构可能就是受限制的ordinary joint conditioning。** 对source的`uM,uH,vM,vH`建同信息联合协方差，标准条件均值已经允许两种创新量修复后续。若你的Bx只让uM影响uH、By只让vM影响vH，是特定blockcrosscovariance限制；强joint模型还允许vM帮助state、uM帮助剩余function。必须把该限制说成有限样本bias/variance假说，非已证生物模块解耦。若ordinaryjoint相同约束与计算精确复制，合并同一方法；若更一般joint更好，两阶段必要性失败。不要要求候选胜自己的copy。

**二、先以最简单2×2feedback实验测真实增量。** 固定M支持、同一完整history，比较无反馈、uM、vM、uM+vM；再比较joint/full-history与顺序factor。所有arms得同source辅助RNA、RNAQC、chemical+dose及实际M读数。差别是更新结构，不能是信息权限。uH和vH为source训练targets，所有表示、g和创新量需chemicalgroup外预测；尤其不能用同药H训练过的g生成看似组外vM。不能在先看laterH再选表示、rank或误差定义。

**三、v残差是否真是功能创新不自动成立。** `vM=yM−g(actualxM)`仍包括g误设、测量误差、normalization、lot混杂；不是已识别RNA外生物功能。x为高维RNA分布/均值，nonlinearg(E[xH])不等于E[g(xH)]；两步误差下降可能只是校准Jensen偏差。应把这些作为普通解释，首关用小维source-only表征、明确同目标scale，不加新机制模块救结果。重复RNA/功能来自不同payload且无同培养映射，condition-mean预测合法，individualmediation不合法。

**四、跨剂量继承容易被剂量预筛与plate/实验效果伪装。** L/M/H是每药不同绝对浓度，1:5:25仅inprinciple。Bx可只学习dose-ratio/potency或批次共同偏移。保留化学和logdose/ratio、perexperimentcontrol归一化的ordinarydirect；sourcecrossfit以解析chemicalgroup为单位，不能仅药内leave-doseout。H按80–90%survival/solubility预筛，有真实信息先验，constant或Mfunctionbaseline先做headroom的决定是必要的；若无实用空间不下载RNA。47label下3dose不能计141独立任务。

**五、RSI中程序字典较小时K若覆盖全集，scheduler只能省中间步。** 这不是否定有限C4，但指标必须固定sameK最终值/曲线面积，history、calibrationbank与候选失败预算全部匹配。不能让newimprover看到更多完整H伪episode而old只看摘要。普通metaselector/retrieval也给全history；若它匹配，保留普通学习结果，不包装递归新机制。

## 已保存源化学身份的最小可靠方案

读取官方已保存README§2.2，compoundlist声明的字段是COMPOUND_NAME、COMPOUND_ABBREVIATION、COMPOUND_NO及各物种CEL链接；已保存CELmetadata同样含这三字段。sample/function身份表仅name。**这些已查资产没有CAS/SMILES/InChI字段**；没打开SupplementTableS1，故不声称所有source全球无CAS。

47safe菜单先以EXP_ID+exactname连接CELmetadata，确认name→COMPOUND_NO一对一与全部Low/Middle/High一致。这提供sourcecatalogentity，不提供material结构/盐型/批号真值。若用PubChemname解析，结果须标candidateproxystructure：保存exactquery、全部CID候选、去歧义理由、isomericSMILES/InChIKey和访问receipt；不把数据库检索首条当源试剂认证。优先用sourceCAS/明确salt名称若后续查到；否则保留ambiguity，不凭熟悉药名猜。

在开值前冻结parent标准化/tautomer/盐规则并保留raw结构；同parent并组，有环Murcko才用于scaffold并组。无环空Murcko不能把所有acyclic药并成一组，应按parent个别组。未知/mixture/polymer/不适合结构的小分子身份例外按预注册保留为unresolved、排除或另列探索，不能用未知填共同假结构，也不能结果后选最有利组法。若可靠resolvedgroups不足，报告小目录探索或停此分区，不宣称47labels已充分化学隔离。

尚未执行PubChem/新metadata下载、原raw函数读取或任何fit。root可按此最小方案继续；我不会并行重复其化学实现。
