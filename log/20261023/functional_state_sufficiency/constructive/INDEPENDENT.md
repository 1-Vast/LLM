# 功能反馈修订状态充分性：一个精确定义的尝试，当前不提名拟合

2026-10-23。本角色在读取本阶段其他角色报告之前完成此原稿。上一阶段CD14预冻结STOP不变；不按它的467个反号pair、marker/cut/seed重开搜索。本次结论 **NO_SUPPORTED_NEW_CORE / NO_FIT_NOMINATION**，不是要求任何候选必须使用全新数学原语，也不否定低反馈状态修订的可能价值。

## 已核对的历史范围

- `log/20261022/antibiotic_state_refinement_review/DECISION.md`：基于历史反例的最小predicate/state split，在固定字典、惩罚、local refit与选择规则后由普通MDL细分完全实现。真实历史信息有用不等于世界模型独立贡献；这个有限菜单等价不否定所有连续/噪声状态构造。
- `log/20261023/observation_law_search/DECISION.md`：未归一化人口测度、transport/growth/capture分离及已知capture重加权已有明确常规实现；snapshot不足以一般识别干预动力学。其STOP是“裸observer作为新核心”，不是所有population模型或不使用lineage的功能预测都禁止。
- `log/20261023/function_update_renewal/DECISION.md`：固定线性功能读出下共享线性状态编辑可折叠普通scalar regression；同时编辑组合算子有有限交叉项，不能把所有非线性更新宣布线性等价。付费状态信息须同样给direct并计成本。
- `log/20261023/decision_probe_mechanism/DECISION.md`：terminal功能类压缩若只保留每probe边缘，会丢联合观测信息；正确普通joint-law planning可修复，不独证世界模型必要。
- `log/20261023/update_strategy_renewal/DECISION.md`：CD16A一手研究已说明first-kill不保证serial-killing，contact/release及effector survival有意义；缺所需公开individual event轨迹，普通多状态hazard/refit也没有新机制。不能把该生物叙事重新命名本轮创新。
- `log/20261023/mixed_feedback_estimator/DECISION.md`及`intervention_constraint/DECISION.md`相关前段：对角mixed-law已在源上失败，target-conjugate接口不能仅据RNA名字认证。不能在已曝73-pair响应上换copula/高阶头救旧规律。
- `log/20261023/feedback_sufficiency_renewal/DECISION.md`：完整轨迹direct是强对照；MAE固定路径的特定magnitude碰撞不是所有适配失败，更不能以换MSE作为新机制。

这些历史中有些只读了决策前段；未读它们原始数值表或本轮同行稿。目录内关键词搜索仅用于定位具体范围，不能证明全局新颖性。

## 唯一认真审查的操作：只修订单细胞联合结构，保留已观测边缘

科学问题可以精确区分：两种干预产生相近pseudobulk均值乃至相近各基因边缘分布，却有不同的同细胞共表达/共激活组合，因而在某个联合阈值型功能上不同。仅把均值向量当“细胞状态”可能混淆这两种群体。与追加通用embedding不同，一个可写出完整操作的尝试是**功能反馈约束下的联合分布重加权**。

设干预a的模型群体包含z_i，初始权重w0_ai，源期固定一个单细胞功能witness ψ(z)。对已支付的同条件功能反馈y_a，调整权重：

    minimize_w  sum_i w_i log(w_i/w0_ai)
    subject to w_i>=0, sum_i w_i=1,
               sum_i w_i b_gk(z_i)=m_a,gk for declared marginal bins,
               sum_i w_i ψ(z_i)=y_a.

bin约束若只用基因均值，仅保留均值而非全部边缘；必须诚实区分。这个操作可能改变联合分布而不改已约束边缘。拉格朗日形式是w_i proportional to w0_ai exp(λψ(z_i)+sum_gk ν_gk b_gk(z_i))。函数witness与边缘约束在源期确定，不能从目标query筛选；若y不在满足边缘约束的可行功能范围，必须报告infeasible，而不是加latent cell救分。

**我不提名它进入拟合。** 这恰是标准minimum-KL/I-projection或maximum-entropy moment calibration，并未给出新的求解/继承操作。若之后把λ跨药物传播，则必须有独立共享规律；“同一个患者”或“同一通路”本身不提供该规律。固定ψ时，功能值就是权重对ψ的普通期望；同信息的普通moment/copula conditional predictor获得同样边缘、联合样本、功能反馈与先验，不能故意只给它pseudobulk均值。

另一方面，不能从“属于I-projection”直接推出有限数据一定无益。一个生物学有效且可迁移的稀疏联合witness约束可能是有价值的结构贡献。现在缺的是：真实强控制的反复错误确实对应这种联合结构、功能witness如何合法识别、为什么有限反馈比直接联合矩估计更有效，以及跨干预重加权的共享语义。此处都没有新证据。

此外，该重加权无法产生初始支持外的新细胞状态；如果未来功能差异来自未观测dead/rare populations、邻居接触拓扑、绝对细胞质量或时间顺序，它会补偿错误对象。不能把静态同细胞copula当作immune contact graph或真实细胞过程。普通graph/survival与完整历史direct仍需同信息对照。

## 新的一手方法：避免自我标签的状态评分，不是本轮发明

本角色用了恰好2个公共GET，均200；原文/回执保存GET1/2。第一是arXiv作者feed，查询2025–2026 “state abstraction”，只看按新近排序前3项（共66条，非完整检索）。第二是选中原文：

Melih Kandemir、Mustafa Mert Çelikok，**What Information Buys in Active Inference**，arXiv2610.19046v1，2026-10-13，https://arxiv.org/html/2610.19046v1。

原文SHA256为721486a5b92ba5f83f8a103f5baf92dcf1ec32e42778219dac702078ce5b2177。完整HTML保存，但实际阅读限摘要、引言中固定/自适应goal与learned-abstraction段，以及§5 Assumption1、函数类、GOLF版本空间选择说明；没有逐条验证证明、运行代码或复现任何作者数值结果。

具体机制不是一句reward-aware embedding：它在候选abstraction集合Φ上构成可表达的value-function类，对每个候选函数计算**相对同一Bellman target最佳预测器的超额平方残差**，保留未超出半径的函数，再按最乐观候选贪婪行动。goal改变时，用已知新reward对旧transition重新标注并重建版本空间。作者明确这是GOLF（2021）的实例，而非本轮或该文发明一种细胞状态更新器。

重要假设：真实decoder在有限候选Φ中、block MDP中一个latent state的emission支持不交叠、reward可因子化为latent state/action函数，以及真实transition样本与episode结构。它指出predict own latent labels可能使错误粗状态自证，功能/价值的共同目标是更强对手；其平方根信息校准在固定reward下也不自动胜过普通confidence方法。

迁移边界：公开静态药物AUC并不自动给Bellman transition/可reset episode；一个H=1退化可用于共同实测功能target的普通表征风险比较，但此时本质是监督模型选择，不能借引用GOLF声称新动态世界或RSI。若功能目标本身从旧数据重新定义，更不能将它当独立新反馈。以上来源提供具体强对手和自证风险，不为copula尝试增加未有的新颖性。

## 若未来出现新证据，最低证伪与对手

数据角色由根另审；本报告不假定一个资产已经具备相匹配single-cell joint state、独立function和跨背景任务。需先确认实际观测来自同干预条件、功能不是由同一状态特征公式派生、时点/绝对数量/运行单位可审计。近似均值碰撞必须在结果前固定距离、噪声容忍和pairing，不能在功能标签后找最鲜明反例。

若有认证样本，最低实验应首先冻结一个联合witness及其传播限制，检验它能否改善未支付功能query/药物决策，而不是只改变state重建。强对手至少包括：同完整细胞样本的conditional direct/DeepSets、同ψ/bin的普通I-projection、普通联合矩/graph与非高斯EB、union refit；给全部方法相同源标签、当前state/function反馈与测量成本。若声称反馈节省，应比较不同反馈预算完整曲线，计入single-cell读出与源witness训练成本，不能只计λ拟合。

没有阈值证据时不预选任意5%实用门；必须基于具体function量纲/测量重复性在响应前约定。若普通同约束对手复现全部收益，或只有state差异没有功能/decision增量，停止新核心。即使约束有用，agent选择、跨任务继承、联合效应及G1更会改进G0仍需独立common-start/等总成本试验。不能把保存λ/ψ或模型选择称为RSI。

## 决策与真实成本

当前只保留“均值/边缘相似可能遗漏功能相关联合结构”这一可证伪科学问题；**不启动copula重加权拟合，不碰旧停止源，不把新原文改名为细胞算法**。2GET全部200，无重试；0API、0模型拟合、0模拟、0生物响应/保护值读取。两个抓取脚本只存取公共原文，未执行下载代码。原生模型身份/token/金额不可见，不编造。没有需要修复的抓取错误；一次广泛history rg输出过长被截断，随后仅使用明确读到的决策范围，不声称穷尽。
