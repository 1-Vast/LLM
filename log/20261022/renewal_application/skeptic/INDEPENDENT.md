# 独立反方：撤掉普遍禁令，测试分子响应能否决定功能反馈的迁移

2026-10-22。总体目标 ACTIVE / NOT_ACHIEVED。本稿不拟合、不读新 raw response、不改任何已冻结阶段；新 GET=0。本稿在阅读本轮 peer 全稿和 root 新取得的两份全文前保存。写作期间收到 root 关于 lineage/rare-tail 的备选摘要，以及 advocate 关于 RNA source/sink 的摘要；这两项概要暴露在此披露，未用于改成本稿候选，故不宣称完全盲审。本文复用既有 LCD XML，是 root 本轮新增来源之外的历史原文件。

## 一、研究程序确有可能自设过强阻碍

用户要求世界状态/功能模型、实验反馈、可继承研究程序及改进策略的再改进；没有要求第一阶段就同时解决同细胞连续轨迹、独立 raw repeats、动态可重置环境和疗效终点。应保留精确合同，但避免把某一合同的失败升级为普遍准入门。

| 必须保留的局部门 | 不应推成的普遍禁令 |
|---|---|
| 分清 published-normalized catalog 与前瞻独立湿实验；披露 shared ComBat、既有暴露与选择历史 | 任何经过归一化或已暴露数据都不能做探索性预测、程序学习或改进策略比较 |
| 没有同细胞连续观测，不能声称识别真实单细胞时间轨迹或 washout 机制 | 破坏性 snapshots、静态干预后的条件分布都不能构成有用 world state |
| RNA/形态不是校准 viability，不能用捕获细胞数假称生存率 | 早期分子响应不能作为药物功能预测的辅助状态；功能必须与状态来自同一物理培养或同一文件 |
| RNA 与功能若未配对，不能从边缘分布恢复个体条件关系 | 处理条件对齐的跨 assay 均值不能用于条件平均响应预测；不能作这种较窄任务 |
| PRISM 特定 80%/70%/七板门失败，准确 bulk-profile 配置停止 | 任何稀疏局部面板、不同任务都必须满足同一批阈值 |
| 针对某个新操作的精确同信息、同预算构造归约可否定该操作的新算法主张 | 只说“可以写成 meta-learning / Bayesian design / contextual bandit”就宣布某具体生物结构或有限样本贡献不存在 |
| C4 比较必须固定 later-task 起点、信息权限和预算，并实际改变 improver | improver 必须修改自己的源码、必须无限加速，或只有真实在线湿实验才允许计算性 C4 试验 |

最重要的改法是把三个问题顺序分开：**观测是否足以定义一个窄应用；具体结构是否在强基线下有收益；其研究策略是否能被改进并迁移。** 不必在第一问通过前造完整框架，也不应在没有实证前要求独有算法定理才能检查第二问。

历史负结果仍有约束：O'Neil 程序/规则修订没有胜过固定 refit，PTV-1 ppODE 没有胜过强 direct，STACK 额外历史只有小幅且未过实用门，AZ effect-coordinate 与 PRISM 两池 bulk 合同停止。这要求换一个有具体未决结构的假设，而非再加模块、再写 LLM editor、搬动同一 exposed test 或降低原阈值。

## 二、只推荐一个候选：功能误差按干预后的分子响应结构迁移

**候选可证伪结构：在未见化学组的新药物中，少量已查询条件所揭示的功能误差，能按干预诱导的分子响应方向迁移到未查询条件；这种迁移优于化学相似性、剂量邻近、整体 offset 与普通全量重拟合。**

这不是宣布一个新 optimizer。核心未知是一个生物统计结构：解释药物之间“谁的反馈能帮助谁”的变量，究竟是早期响应程序，还是普通化学/剂量/批次邻近已足够。即使机制预测器、kernel regression 和 meta-learning 都能表达它，有限标签下是否稳定存在、是否可用，仍须实际比较。若普通 state-kernel 已解释全部，则不得包装新的更新算法；但一个可靠的跨化学 functional-transfer 结构仍可能是实证贡献，需进一步文献核查与外源复验。

最小 world 只包含两个受监督对象：

1. 在固定细胞培养范围内，`(control state, drug, dose) → early molecular response`。
2. `early response → later scoped functional readout`，并允许少量反馈修正有限的共享方向。

无需 ODE、真实轨迹、全细胞模拟或 causal mediation 承诺。重点不是模块名字，而是**经过干预后的状态是否使反馈迁移比输出邻近更有效**。功能反馈不能反向伪造 molecular truth。

## 三、具体应用与已可获得资产

优先复用已认证但未做本候选数值试验的 **TG-GATEs 人原代肝细胞持续暴露菜单**，应用为体外毒性确认的剂量外推：用一份较低剂量的条件级早期表达及功能反馈，预测同药较高剂量的24h功能响应；随后在未见化学组药物上重复。它是安全性筛查辅助，不是疗效或临床用药推荐。

已有元数据证据来自 tggates_functional_qualification：2→24h 有156个 LDH 身份可用条件/52药，8→24h有385条件/152标签，严格三时点条件为144条件/48药。它们是不同菜单，不能混用。高剂量源自80–90% relative-survival 预筛或溶解度限制，故只支持这个已筛选菜单。非 control dose=0、μg/kg 例外、化学别名/结构必须先按设计解决，但无须凭空要求 donor holdout 或同一物理培养轨迹。

官方把 LDH(%) 和 DNA(%) 都定义为 relative survival；本候选不把 LDH(%) 当原始泄漏率，不推断 birth/death。早期 RNA 与晚期功能按 treatment/dose/time 对齐的 assay 平均，不声称同细胞配对、因果中介或新 donor 转移。分子值尚未因本候选下载/转换，后续需明确 CEL 成本和预处理。已认证 asset 是一个现实起点，不是本稿发现的新数据集。

最小任务菜单建议先只用**身份认证的、同药至少三个有效正剂量的2h→24h条件**。原始最高有效剂量固定为目标，较低两剂量是可买支持菜单；若该菜单数量不够，应报告这个设计不够，而非事后改成任意 dose/time。化合物 parent/scaffold 分组贯穿 source/dev/later-test；药内剂量和 RNA 技术重复不增加独立 task N。

一份支持是预先列明的条件级 assay bundle：所需早期表达重复及24h两个功能 assay 的发布读数，按实际不同培养/assay payload 分列。它不是“一次便宜标量查询”。目标剂量的早期 treated RNA 和晚期功能都不可作为免费输入；world 必须预测未买目标的状态。若把目标 RNA 预先给所有方法，那是另一个有用应用，却不能用来验证 world 的状态预测贡献。

## 四、一个真正能改变决策的最小实验

先做固定支持、同历史比较，暂不加 LLM。用 source/dev 固定状态表示与最多一个共享低秩修正；不要让目标一条反馈辨认任意高维机制。模型不必可识别所有生物参数，只需给出可审计的预测及其不确定性；任何参数生物学解释另列待证。

必须同信息/同 source 标签/同搜索预算运行：

- 强 chemical+dose direct（含非线性树模型与适当 neural/multitask 基线）；direct 的 source 训练必须也允许同样的辅助表达标签，不能把额外数据优势算 world 优势。
- 同反馈 direct，输入完整已付表达、两个功能读数与缺失 mask；不能只给均值或只给化学特征。
- 固定 no-update、普通 offset、剂量曲线/shape refit、全量普通重训练及强正则 few-shot 更新。
- 简单 chemical/dose covariance 或 kNN 与**真实分子响应 kernel/低秩回归**，以及普通 learned metric/shrinkage。这组能直接击穿“分子局部更新就是新算法”的包装。
- 简单混合；程序预算允许的等数量预定更新/表示选择。所有 source 状态构建、伪 episode、超参和失败都计入搜索/CPU账。

关键消融不是只去掉模型的一层：把 source 分子响应在化学组内/跨组适当置乱，保留批次、剂量和表达尺度；替换成已发表 EGR1/ATF3/GDF15/FGF21 四基因 stress signature；去掉已付分子反馈但保留全部功能反馈；给 direct 同样的预测状态特征。若置乱仍有等大增益或简单 stress/offset 已足够，候选的响应几何解释不成立。

先注册一个主终点，不从 test 挑最好的 assay。建议以24h DNA relative-survival 的归一化 MAE 为主、LDH relative-survival 为完整次要结果；一个可讨论的工程目标是相对最强基线至少10%且绝对0.02 survival-unit 的下降。**这是未来合同的建议值、不是 assay 噪声/临床阈值，也不是已冻结门。** 应在任何候选新值打开前，根据真实筛查决策用途确定；不能用本阶段或原阶段 exposed test 调整。若 source/dev 的未查询目标 headroom 已不足实用门，停止该应用，不追加复杂 agent。

使我改变决定的结果是：在未参与选择的 later chemical groups 中，响应结构修正稳健超过最佳同信息 direct/refit/metric 方法，置乱及简单 stress signature 无法复现，并且对实际高剂量预测/确认有实用收益。这会支持深入，而不是自动证明新算法或分子因果机制。

停止条件明确：设计身份/可用性无法支持固定目标；普通方法已饱和；增益小于冻结实用门；state 置乱保留收益；效果只在一个板/批次或一个事后子组；或者额外表达/拟合成本吃掉净收益。停止本候选配置，保留正负分量，不外推 RNA 全无价值。

## 五、只有结构幸存后再验证 agent、继承及 RSI

- **world**：同一已付 history、相同 auxiliary source 标签下，显式干预状态构造相对强同反馈 direct 与普通 state-kernel 的额外价值。若无该值，不宣传 world 必要性。
- **agent**：在较低两个剂量支持菜单内固定买一 bundle 的预算，比较固定低剂量、固定中剂量、随机、普通 uncertainty/D-optimal、标准 active learning 与 learned query/update。目标最高剂量固定，避免改变评分目标来获得选择红利。
- **继承**：每个后续药物从同一个 source predictor/初始程序开始，只改变是否携带前药物学到的 query/update 策略；参数继承、普通重训练与 continual learning 另作对照。保留模型参数更好不等于策略变好。
- **联合**：world×agent×inheritance 的必要因子，分别列各自收益与总净收益；无需要求超加和。
- **RSI/C4**：早期和后期 frozen improver 从同一 later-task predictor、程序与初始 history 出发，拿同预算信息/搜索权限。后期 improver 必须让后续改进效率更高，而非只继承更强 predictor。与固定 improver、普通 meta-learning/AL、相同程序字典与等预算程序搜索直接比较；如果这些完全解释结果，停止新 RSI 机制主张。

此处的 later-task 是离线目录中未用于该策略选择的化学组。可用于有界计算试验，但不是新生物实验、独立原代 donor 数或前瞻确认。若最终需要药物发现高强度结论，再为外源或前瞻验证立合同，而非用这一要求禁止当前结构试验。

## 六、已有直接先例及新颖性边界

- Zhang 等，DOI10.1038/tpj.2013.39：TG-GATEs 早期 stress genes 预测后续毒性，四基因网络已有。**早 RNA→后毒性、stress 网络或“功能态”命名都不是本候选新颖性。** 本稿当前只重读作者摘要记录，历史阶段取得过全文，不冒称本轮全文重审。
- VCLMU，arXiv2610.04475v1：机制单位、action-conditioned latent state transitions、显式 transition supervision、perturbation-disjoint evaluation 都已有。复用已保存一手完整 HTML/正文投影。可作为机制状态方法邻居，不能以其表达力宣布具体功能反馈结构已被验证。
- LCD-CLIPR，PNAS2026-10-08，DOI10.1073/pnas.2602630123：snapshot、stationary causal diffusion、噪声分解、非加性组合预测与线性 drift 下识别已有。无需真实单细胞连续轨迹才允许受假设的机制模型；其定理也不能被扩成我们未配对 RNA/功能的中介识别。
- VCWorld，arXiv2512.00306v1：结构生物知识+LLM迭代机制推理和药物扰动预测已有，不能把 LLM 放进 loop 当新核心。
- 旧阶段 Hyperagents/SpecRSI 已明确 editable improver 和 common-start 控制；“会改自己的程序”或“携带策略状态”不是首创。本文没有新 GET 或穷尽新颖性保证。

**本稿判断：尚无新算法核心通过；推荐一个有具体生物统计未知、可被普通强基线直接否定的小实验。** 若该结构不幸存，反方会支持停止；若幸存，不能以一句泛 meta 等价消除其证据，必须在同信息/同预算下展示实际替代或精确归约，再裁定技术贡献。
