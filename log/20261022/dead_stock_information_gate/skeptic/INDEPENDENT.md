# 独立反方：早期 dead stock 的条件信息价值

2026-10-22。先读本阶段 ROOT_PROTOCOL、复用已保留 BESTDR 原文，再做四次有界 GET。本稿落盘前没有读本阶段 advocate/auditor 稿、数值 CSV 或拟合结果。写稿期间收到根代理拟用 DoseResponse-only、24→72 relativeh、8-fold concentration holdout 的方案，以及支持方提出 context holdout 的两问；这两项消息是已知设计信息，不假称完全盲法。独立问题范围先保存在 `PROTOCOL.md`。

**结论：值得先资格后执行一次窄的真实信息 gate；当前算法新颖性 NONE，也没有已成立的新生物经验性质。** 已测 live prefix 后，dead stock 能否改善后来 LIVE counts，是必要且具体的条件预测问题。即使阳性，首先支持多一个 readout 的信息价值；它不自动支持新世界模型、真实 birth/death识别、agent、程序继承或 RSI。不能将已停止的 scalar alpha 简单换成两 κ 救结果。

## 科学上究竟还剩什么可测

主张应是：在固定、相同的 live prefix、实际时间、剂量及 recorded context 下，加入 early dead-stock prefix，使未用于本次训练/选择的 later LIVE-count loss 降低到预定实用幅度。可写作预锁分组上的 `Loss(f_L)−Loss(f_LD)>=δ`，并报告各剂量/context的异质性。f_L 与 f_LD 必须得到相同标签、split、候选族、调参预算和合法历史。

固定且已知 `L'=rL, D'=dL−cD` 时，未来 L 不依赖 D。**但不能把这点扩大成“常率模型中 dead 永远无信息”。** r 若未知、live count 有测量误差，或 b/d/r 先验相关，D 可以通过普通联合参数推断改善 r 的后验。该收益无须 D 因果影响 L，更无须一个新生物记忆状态。BESTDR 正是该解释的强近邻。

还可能存在 phase/damage/turnover 等共同潜变量，使同样早期净 live growth 对应不同后期响应；这可作为动机，但本 readout 本身不能唯一识别它。D 在相同 L 下的差异也可能来自清除、染色延迟、分割或 assay/context校准。若 `live=total−dead`，同帧 L/D 的代数共享与相关误差尤其重要。跨时间相关的计数误差也能产生真实 readout forecast gain；不能把它直接命名为真实细胞死亡机制。

比较 full D history 与 D0-only、latest-prefix D snapshot-only 是必要的简化：若一个 snapshot 已有同样收益，应报告死细胞快照价值，而非“死亡动力学必要”；若 D0 即足够，解释可能是起始培养/检测校准。超越这两者的动态增量仍需对普通多变量 forecast、时间变参数/多状态及含 clearance 的联合模型比较后，才值得研究其生物原因。

## 最贴近的一手操作与未被直接回答的问题

1. **BESTDR, Cancer Research2026，DOI10.1158/0008-5472.CAN-25-1181**：沿用此前保存并已全文核对的一手原文，不重复 GET。它联合使用 live/dead stock 与 clearance，使用多类型分支过程均值/协方差近似似然，另设测量误差，后验估计浓度依赖 birth/death/transition率，并有层级跨细胞系共享。其 live-only/live-dead 对比主要检验模拟速率恢复与 clearance 稳健性；真实 HCT116 比较计数推断与另一个谱系实验的时间尺度。**这覆盖本题的大量操作，但在已读正文没有直接完成“完整相同 early live prefix+metadata，加入D，heldout later LIVE”的严格条件 contrast。** 不把同方法操作误当经验问题已回答，也不把有限阅读当全部文献不存在此检验。

2. **Gross et al., Analysis and modeling of cancer drug responses using cell cycle phase-specific rate effects, Nature Communications2023，DOI[10.1038/s41467-023-39122-z](https://doi.org/10.1038/s41467-023-39122-z)，[PMC10257663](https://pmc.ncbi.nlm.nih.gov/articles/PMC10257663/)**：新读原始 XML 的方法和相关结果/讨论，系比限定2024–26更早但更直接的近邻。该文不是仅加一个 ODE：将 G1、S-G2 按 gamma/Erlang驻留时间拆为8/20子阶段，用 linear-chain trick建 mean-field动态，分享非药物特异参数并同时拟合多药多剂量；有阶段特异死亡率与 drug-induced delay。其模型拟合平均的三重复、全部所用时点/浓度/药物，并用速率层组合预测实测组合药的 final cell numbers，与 endpoint Bliss比较。它证明“阶段/死亡动力学→功能细胞数”已有明确一手操作和实测用途；不等于已经测试本题 fixed-prefix conditional D增量。该文从死亡率积分得到 accumulated deaths，不能把这一模型输出当我们的 observed dead-stock CSV。

3. **A feedback loop between cell proliferation and ROS regulates ferroptosis sensitivity, Frontiers in Cell and Developmental Biology2026，DOI[10.3389/fcell.2026.1756238](https://doi.org/10.3389/fcell.2026.1756238)，[PMC13059718](https://pmc.ncbi.nlm.nih.gov/articles/PMC13059718/)**：新读原始方法与模型结果。其明确操作是 population n 与 lipid-ROS r 两变量耦合：logistic growth→ROS generation，ROS清除与正反馈，阈值触发 ferroptosis；加权最小二乘拟合时间曲线。不同初始密度/ROS可趋向不同 fate/稳态，作者用限制生长空间、GPX4与代谢干预作实测检验。它说明额外状态与生长/死亡耦合有生物近邻，但额外状态是 ROS，不是“死细胞数量导致未来活细胞变化”。不能从其成功运输到 HCT116/cisplatin，也不能把拟合全部曲线等同 early-prefix heldout forecast。

两次窄 TITLE_ABS 检索分别限2024–2026得到7/9条结果；未开展无限综述，未把摘要相似题材都当方法先例。所有作者结果为公开叙述暴露，非本项目复现。未见足以直接将本题升级为新核心的独有数学操作；合理增量目前只是严格限定条件下的测量信息检验。

## 同信息比较应怎样落地

先判断 **D信息价值**，再判断 **动力学结构价值**：

- L-only 与 L+D 的 direct 使用相同全部合法 L-prefix特征、time/dose/context、监督与候选预算；每一信息臂独立在训练/内验证选择配置。不能把 L+D 的强 nonlinear model 与 L-only 的固定线性模型相比。保留 persistence、局部/全 prefix slope、同信息多输出/多变量 regression/trees；简单混合不能省。
- 常规 multivariate kinetic/clearance 模型使用同 L/D测量与初始状态，普通 joint refit、层级共享或已知 prior 与候选共享。L-only/LD 情况下都允许估计未知 r；不能把最弱“固定已知 r且D完全旁观”的模型当唯一动力学控制，再说 kinetic 无法利用D。
- 若仅用两参数线性 stock模型，报告它在假设下的 posterior/regularized推断，不称真正的完整 BESTDR 实现。可用 ordinary time-varying/阶段型/多类型模型作为后续扩展的必要近邻；没有 cell-cycle/ROS测量时不要给候选独占这些真实标签。
- 对 D0-only、D24 snapshot-only、full D history 用同信息定义/预算；joint later D loss仅为次要，不能救主要 later LIVE loss失败。若原始 live 计数由 total−dead算出，额外的 total 可以由L/D代数恢复，应明确这也是新增信息，而非一个独立第四通道。

Agent/AL/CL/程序继承与 equal-budget program search 不在本信息 gate 自动得到验证；普通 hyperparameter tuning不是agent。若没有实际 query menu及成本，不能声称少做实验；本题可先是固定已测前缀的预测价值。

## 拟用 split 的具体审查

根代理拟用 DoseResponse-only，以避免另一Replicates文件可能复用0/12µM实验造成跨文件重复。赞同；不把同实验不同导出当外部验证。原始 image/well/seed/group/date 键须先认证或保留 opaque；同孔三images与时点一律不拆到不同集合。若图像区域重叠未知，可预定义同ROI尺度的均值readout，不必为了该预测强求绝对全孔细胞总数；不能随意求和后声称绝对cells。

**8 outer leave-one-concentration-out，剩7中固定 hash取1 validation/6train，再选配置并在7上refit**，可以检验此单药单细胞系内对未参与该次拟合的浓度预测。全context/well随该dose分组。它不是8个独立药物、8次独立研究改进，更不是跨context或跨生物run验证。不同dose的实验和模型高度依赖；总主分数可预定macro dose→context→well，逐dose/逐context列结果，**不把8fold/bootstrap当充分总体CI**。test0和边界高剂量包含浓度外推，其余可能是内插，应事前按设计注明，不在看结果后删边界。

这类交叉拟合的泄漏语言尤其要准：每个 outer target 的72h标签会在其他fold合法作train/inner-validation，因此不能声称所有 outer目标在整段实验中全局封存。应在第一次数值访问前冻结整个8fold代码、特征、预算、success rule；每fold明确禁止该dose的target进入训练、scaler、prior、调参；全部预测保存后统一评分，不能依据已跑fold结果修其他fold。写出每fold成员、选中模型、所见标签范围和hash，以便检查。每fold的预测算法未用该fold标签，与数据集所有目标从未被数值解析，是两个不同命题。

`concentration=0` 必须有预定有限编码，例如固定单位尺度的log1p和零指示，不能沿用log10(0)。opaque context不能当已认证连续接种密度/生物run；若用onehot，在此LOCO下各context通常在训练与测试均出现，因此该设计允许context校准，但不测试新context外推。context holdout则检验另一任务；只留1个context test时只能作单context描述，D帮助未知context校准也不能解释成生物机制。无需同时新开多个split挑最优。

## 数值开启前须锁的量化细节

建议主endpoint为每孔 image聚合后的 `log2(L72+1)`，配对比较 L-only 和 L+D 的同outerfold预测，先按已认证真实时间取得prefix/target，不使用future归一化、平滑或插值。relative24/72h可作为导出时钟的预测定义，不能未认证就称给药后24/72h。若“nearest72”有容差，应仅按时间/身份固定 tie和eligibility。L+D 的 D特征只来自同样<=24h前缀，D24意为该合法前缀末次实际读数，不能跨边界补端点。

根代理提出0.05log2与10%双条件作为此项独立问题的pragmatic门槛，可以在数值前冻结，但它不是 assay噪声估计：0.05精确是(N+1)约3.53%倍率，不是低计数N相对误差保证。该阈值不同于已停HTS001的0.10不等于事后挽救，因为本题readout/数据/假说不同；必须现在冻结，后续不改。只降次要D-loss、只胜弱基线、或未达到主live实用增量均停止此extra-channel应用的扩展。

调参预算需按arm×fold全计。例如若沿用14个direct配置，4信息臂×8fold就是448个首次拟合，另32个selected refit；这只是计费算式，不建议无条件加大配置。每臂预算、随机种子、macro scorer、平分规则和是否refit必须一致，普通kinetic的每个失败/不可识别拟合亦保留。数据太小不应靠扩搜索空间产生“最优D信息”阳性。

若主LIVE gain阳性：先确认不是D0/snapshot/共同计数噪声即可解释，并检验普通同信息模型是否足够；信息gate阳性不要求新算法，但不得据此声称新动力学机制。若阴性：停止这份具体early-D→later-LIVE条件信息配置，不据此否定所有death读数、其他时间/药物或虚拟细胞。若身份/目标/噪声无法支持判别，报告not-testable/inconclusive，不写生物阴性。世界模型独立收益、agent、继承、联合和RSI当前全未测试。

资源：4 GET，全部HTTP200，正文共420787 B；每请求UTC/status/bytes/SHA256已留存，无retry/redirect，单响应≤3MiB，timeout25s。无dataset payload、无API/训练、无生物实验。旧freeze未修改。一手投影和检索结果保留本目录；有限检索不保证穷尽newness clearance。
