# 独立倡议稿：用选择性 effector 重置辨识可继承的肿瘤响应

2026-10-22；**独立初稿已先写入，再向 skeptic 发问**。本稿未阅读反方本轮独立稿，不读取任何新响应数据。本轮只提出这一项最小操作。当前结论是：它有明确的生物学可证伪条件，但**尚不足成为新算法／RSI 核心，且当前来源不支持离线验证**。

## 具体应用和假设

应用限定为 cetuximab–NK-CD16 对结直肠癌细胞的 ADCC。研究目标是判断撤药后再挑战的恢复，哪些属于肿瘤响应状态，哪些属于 effector 功能状态，从而避免把 effector 变化继承进肿瘤转移规律。原论文已含可逆 S/R 切换以及 NK 作用随时间衰减，因此“两个部分都重要”并非新结论。

新增的实际操作是**交叉重配两种肿瘤历史与两种 NK 历史**：肿瘤 i=0（naive）或 i=1（ADCC-adapted；后续可另预登记 withdrawn）；NK j=0（fresh）或 j=1（有标准化先前挑战历史）。共同起点、相同 cetuximab 浓度、相同 live E:T、固定 24h 终点。NK 历史必须独立制备，清除残余旧肿瘤与药物；不能将同时改变 effector 数量当作纯状态重置。

原研究每轮加入 NK、挑战后洗掉，不等于认证了这个 reciprocal aged-NK × naive/adapted-tumor 2×2；也不能声称原研究从未使用 fresh-NK 控制。

## 最小数学主张

用肿瘤特异计数与匹配 tumor-only growth control 得到 V_ij。CTG 如被采用，需分别验证每种 NK 背景和肿瘤特异计数的一致性。仅在 V 位于预先可定量且 `0<V<1` 的范围内定义 `H_ij=-log(V_ij)`；它是**操作性有效杀伤分数**，不是自动成立的真实死亡 hazard。

假设该固定终点存在可迁移的乘法分离：

`H_ij = r_i e_j`，其中 r 为肿瘤 susceptibility，e 为该实验条件下 NK competence。

以 H00 固定非零 anchor 后，前三个配对可预测第四个：

`H11_hat = H10 * H01 / H00`。

可证伪限制是 `log H11 - log H10 - log H01 + log H00 = 0`。这个限制比“有路径依赖”强：它要求一种实测 compartment reset 支持跨配对迁移。但它只辨识相对 r/e，存在全局尺度 gauge；并未由终点分离辨识肿瘤 on/off 转移速率或单细胞机制。

交叉期间边界补充：通过这个检验也不能证明 e 不受肿瘤 ligand、接触或分泌状态影响，或 r 就是肿瘤内在 epigenetic memory；它只在指定动作、时间和读数下支持操作性分离。真正的 compartment-specific causal explanation 仍需额外识别控制。

在更大的已实现交叉菜单中，最小主动选择可严格限定为：用同一 rank-one 模型的 posterior predictive variance 除以真实实验成本，选择最大者；并预留互为交叉的复合历史作盲测。更新只拟合 r/e，重置 effector 时保留 r。**2×2 的最便宜杀伤试验不需要主动学习模块**。没有理由先加入 LLM 程序改写或复杂世界模型。

## 与已有方法的实质差异和精确归约

相对所审原论文，实质实验差异是 reciprocal compartment-history crossover 和 held-out cross-pair prediction，原论文公开方法未认证这项设计。这个实验是否已有其他先例，本轮窄搜索不能判定；因此不声称 first-of-kind。

算法上，普通对照可以逐步完全复制：

1. 直接以 `(tumor-history, NK-history)` 为输入拟合受 rank-one 约束的矩阵响应模型，固定同一 gauge 和同一 likelihood/prior。
2. 以同一参数 posterior 的 predictive variance/cost 选取同一 action，使用同一随机 tie break。
3. 观察同一响应，使用同一拟合／posterior 更新；fresh-NK 操作只改变相应列，保留行参数。
4. 用同一公式预测 held-out 组合，传递同一 r 参数及不确定性。

这不是因为它属于“主动学习”就判无新意，而是这个普通 **factorized predictor + 同一设计准则 + 同一更新** 已逐项重现全部操作。强直接预测器不应被禁止用相同 reset 信息；这个模型本身就应作为强简单基线。

仍可能有价值的贡献是：某个独立组织化的 ADCC 操作条件下，这个分离假设确实成立，且能节省新配对实验，并在新肿瘤历史／NK histories 上可靠转移。这是尚未测试的**生物识别与样本效率贡献**。仅“能表示为普通模型”不消灭该经验主张。当前没有证据支持超越这个范围的新方法优势。

## 不交换性不能作为替代证据

普通两状态线性动力学中，令 on-kill `A=diag(-d_S,-d_R)`，off-reversion `W=[[0,r],[0,-r]]`。交换子 `[A,W]` 的右上元素为 `r(d_R-d_S)`，通常非零。因此固定普通 Markov 模型也能出现 on/off 顺序差异；观察顺序效应不证明模型学会新隐状态、更新程序、继承或 RSI。这里不需运行代码。

## 最低数据和最便宜 kill test

本轮来源只有 P/R/W 肿瘤历史及 endpoint molecular 数据；**未认证 aged-NK factorial 响应、匹配 live E:T、绝对靶细胞计数及其控制**。GSE255674、PRJNA1076459 和仓库模拟 CSV 均不能补成这张表。

最便宜的真实 kill test 是一组 2×2 reciprocal crossover 加各自 tumor-only/NK-only 控制，采用独立制备的生物重复、同 batch 随机化。先锁定 H00/H10/H01 的分析，用前三格拟合后盲测 H11；不能在看到 H11 后挑时间点或删除不合分离的历史。

开做前需用独立 assay calibration 固定 V 的可定量区间、最小 H00、重复方差及实用误差界限。可预登记一个具体实用标准：预测 H11 对应的 V11 绝对误差 ≤0.05，且跨重复的 95% 误差区间完全在 ±0.05 内；不显著偏离 0 不能代替等价性证据。pilot 若噪声使 ±0.05 根本不可判，先停止，不能边看正式结果边放宽阈值。

交叉后精化：该区间须共同传播前三格、共用 control、H00 分母以及第四格的生物重复不确定性，不能只用第四格的标准误。不得观察正式 held-out V 后再删除 V>1 或接近 1 的条件；若它们落在先前锁定的定量域之外，则按已登记 assay/假设失败处理。相同 endpoint H 也不识别过程：`h_A(t)=r_i e_j/T` 与前 T/2 为 `2r_i e_j/T`、后 T/2 为 0 的 `h_B(t)`，给出完全相同 4 个终点，却对中途撤药和 reset 的预测不同；这是解析反例，不是本来源的响应数据。

**停止条件：** 无可操纵／可复现的 NK history；清除过程同时改变未知 tumor state；V 不在可定量范围；相互作用超过预定实用界限；或只有 source simulations。即使通过这个低成本检验，也只支持该条件下的分离限制，不能建立动态世界模型或 RSI。

**继续条件：** 独立数据证明交叉限制和新历史预测成立，且相同信息、成本与任务顺序下比无分离强预测器、普通重训练、持续学习、主动学习、简单混合至少一个有预设实用收益，并不劣于显式 rank-one 基线。先有该结果，才值得考虑连续 withdrawal durations、tumor transition identification 和更多 biological tasks。

## 世界模型、智能体、继承与 RSI 分账

- 世界模型：当前只是固定终点交叉响应约束，尚未观察到完整连续转移；不可直接称虚拟细胞世界模型已验证。
- 智能体：2×2 kill test 无需智能体。大菜单的 variance/cost 选择等价普通 AL；需要额外对同菜单 random/fixed/AL 公平比较，不能把新控制设计的收益全归给 agent。
- 继承：保留 r 只指 **endpoint-row transfer**，不是动态 operator 继承或已证明收益。应在新肿瘤历史×独立 NK 制备中，与从零、pooling、普通 fine-tuning、同 rank-one 的 warm start 比；不共用未见标签。
- 联合：需分别打开／关闭实测 reset 信息、选择策略和可继承参数；现有材料不足以跑此析因。
- RSI：此处没有更新“改进策略本身”的新操作。参数变准、选择更好或 transfer 更好均不够。后续如引入 selector/update-rule 编辑，必须在新的未见研究任务上与冻结旧 improver、普通累积数据及等预算程序搜索比较每单位未来改进成本的收益；目前不应加入这一模块。

独立结论：**NONE（当前算法／RSI 核心）；保留一个有明确 2×2 kill test 的经验识别候选，但当前公共路径缺少所需真实干预数据，不应开始模型性能实验或声称联合收益。**

交叉后行动进一步限定：先寻找并资格已有公开 crossed-history 功能资产；不因这份概念稿启动新架构、训练或湿实验。无该资产则暂停本线，不能拿作者 simulations 补真值。
