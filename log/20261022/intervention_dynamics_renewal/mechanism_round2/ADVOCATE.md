# 第二轮独立倡议：用守恒谱系质量给“仅选择”解释设可观测界限

2026-10-22，mechanism_advocate。依 parent 新任务独立形成；**未读取本轮其他 agent 的机制结论，不联网，不读取新数据 body，不实现架构**。仅复用上一轮已经审查的 AP-1／ADCC 文献设计及既往失败边界。

**交叉后判断：只保留一次有界资产／近邻理论资格，不晋升核心机制创新；当前无新算法或 RSI 已成立。** 标准 missing-outcome／共同母群支配条件可用作特定生物 null 的审查。经有限样本校准后违反它，只排除固定 endpoint 响应类型的任意选择解释；普通世代数依赖的自发切换、损伤或残药等仍可解释。未违反也不证明现实无记忆。交叉前原稿另存 `ADVOCATE_INDEPENDENT.md`，实际往来见 `CROSS_ADVOCATE.md`。

## 1. 应用与仅有的一个候选

应用限定：癌细胞经历一个 conditioning drug／低剂量适应、明确 washout、同环境再挑战后，判断功能变化是否可完全由预存响应类型的选择解释。AP-1 的 trametinib 分阶段适应／live reporter 可作设计动机；ADCC 则说明 effector 状态会混入功能读数，若采用该体系必须先另控制 effector。**不拼接两篇论文的数据，也不假设现在有完整谱系。**

候选的具体操作是：

1. 在 conditioning 开始前给每个 founder cell 质量 1，随机分配历史 h（例如 conditioning→washout）或 c（vehicle→相同 washout）。
2. 完整观察每次二分裂：母细胞的质量各半分给两个女儿。死亡／脱落／失踪分支的质量计入 missing mass，绝不把它从分母删除。这样细胞数可增长，但同一 founder 的全部潜在谱系质量仍为 1。
3. washout 后测 live single-cell state；再施加共同 rechallenge B。对 B 期间也沿树分质量，测活着的 descendant mass。函数终点不是仅对 survivor 重新归一化的表达均值。
4. 用 conditioning 阶段丢失质量给“选择可造成多少差异”设最坏情况界限；只有超出界限，才将反馈作为反对 selection-only 的证据。

这是一个具体的**经验识别条件**。谱系重加权、missing-data bounds 和共同支配 subprobability measure 是已知数学工具；在所给宽泛选择 null 下，本式正是这些标准界限，不宣称新理论或核心算法。将其用于真实 washout→functional rechallenge 是否有尚未回答的生物价值，需一次有界近邻一手理论／资产核验；当前不能称 first-of-kind。

## 2. 它究竟排除什么

明确 null `H_sel`：conditioning 历史只改变预存、沿谱系固定的响应类型的分裂／死亡／移除概率；共同 washout／rechallenge 下，随机选择一个女儿继续的 lineage path 的 B 响应潜能不因 h/c 而改变。允许任意类型异质性，允许选择与 B 响应任意相关，允许 conditioning 导致差异增殖；**不假设选择与功能独立**。

随机化保证在 conditioning 前两臂有同分布的 latent B 响应潜能。沿每次 division 对半分权，消除某类型仅因繁殖更多而被额外加权；conditioning 死亡仍可能产生 survivor bias，因此保留其全部质量作为未知。

null 不包含 conditioning 改变分裂次数后真实改变了女儿的功能类型、遗传突变、细胞周期状态、残留药物、损伤或可持久的表观状态。这些都是不同的谱系内变化候选。**拒绝 H_sel 只证明“固定 endpoint 响应类型的选择”不够，不唯一证明 epigenetic memory。** 更强反例：每 division 以处理无关的固定概率 q 自发 0→1，conditioning 仅改变世代数 d，则即使 δ=0，响应率 `1-(1-q)^d` 也可不同；无需 treatment-specific transition 或新增隐记忆。普通 generation-aware dynamics 必须保留为强替代解释。共同环境、药物清除、细胞周期／损伤和独立重复仍是更强机制归因所需条件；不能把所有违反都归给 AP-1。

## 3. 最小过识别限制及推导

下列均指随机分配前共同母群的**期望／概率量**，不是两个有限经验样本必定满足的逐样本等式。每个臂按起始 founder 质量取平均，记：

- `L_h`：rechallenge 开始时仍在观察中的 live lineage mass；`δ_h=1-L_h` 是 conditioning／washout 阶段丢失的质量。
- `z_h(B)`：共同 B 后**已知存活**的 lineage mass，仍以 conditioning 前的 founder mass 为分母。
- `u_h(B)`：B 期间直到终点仍未知／censored 的 lineage mass；B 的已知死亡质量 `d_h` 不列入 u。完整 frontier 应满足 `z_h+u_h+d_h=L_h`，不能同时计母细胞与女儿。
- `μ_B`：若未被 conditioning 选择移除，原始 founder 分布在共同 B 下的平均功能潜能。H_sel 要求 h/c 共享这一量。

conditioning／washout 中已死或丢失的质量，其反事实 B 潜能未知；B 中未知 fate 也可贡献 0–1。因此 H_sel 必须满足：

`z_h(B) ≤ μ_B ≤ z_h(B)+u_h(B)+δ_h = 1-d_h`。

对多个随机历史，**所有区间必须有共同交集**：

`max_h z_h(B) ≤ min_h [z_h(B)+u_h(B)+δ_h]`。

无 B 删失时令 `Z_h=z_h`、u=0，恢复 `[Z_h,Z_h+δ_h]`。若允许各历史对任意隐藏固定类型作任意选择，这些 scalar marginal summaries 的共同区间相交是 **null 可行性的充要条件**。构造：任选交集内 p，令共同母群中 type1 质量 p、type0 质量 1-p；历史 h 保留 type1 质量 Z_h 与 type0 质量 L_h-Z_h。可行条件正是 Z_h≤p≤Z_h+δ_h。边界 p=0/1 取退化群体。有 B 删失时可将其未知 fate 在区间内分配，形成相同存在性论证。

这项充分性仅针对这些未联结汇总边际，不覆盖完整 paired tree、共有早期 branch、整数 cohort 或 time trajectory 的额外限制；更不证明实际世界无记忆。它不是拿直接预测器的表达能力作限制。

零丢失且 B 无删失时，H_sel 要求母群 `E[Z_h]=E[Z_c]`，任意 fixed-type 增殖速率差异被 chronological random-daughter lineage weights 抵消。**不要求有限样本 Z_h=Z_c**：四 founders 含两个固定 responders，随机 2:2 分组有 2/6 的分组给经验 Z=1 与0；或者两个同 r=.5 的细胞一次独立挑战也可一活一死。随机化只保证母群同分布，challenge probability 不是确定 fate。未经推断的 plug-in 不交不能直接拒绝 null。

区间相交说明宽泛母群 marginal null 可行，不能证明没有 memory，可能只是损失太多、界限太宽。有限样本需对母群期望构造与实际 randomization、biological run／batch 及 challenge 随机性一致的 simultaneous confidence region；founder/cell 不自动等于独立重复。未测到／难跟踪分支应增加 δ、u 或 measurement-error slack，不能默认为存活或剔除。只用单个历史终点或 survivor 独立 SE 的做法不成立。

## 4. 单细胞状态提供第二个可核查限制，而非替代功能

若有同一完整 lineage 上可重复测量的 live state（例如经过验证的 reporter），可在共同终点定义预先固定的状态分区 `S_k`，记各臂中 alive lineage submass `q_h(k)`，其和为 L_h。更强的 selection-only null 假定 conditioning 不改变该测量状态的 path-level 潜能，只删去某些路径；于是存在同一未选择的概率分布 `π(k)` 满足 `q_h(k)≤π(k)`。

这要求 `sum_k max_h q_h(k)≤1`，对未联结 categorical 母群边际也是充要可行性条件：取 π(k)=max_h q_h(k)，剩余质量任意分配。超过 1 表明不存在一个仅被不同删去的共同状态分布；有限经验分布仍需推断。它使用绝对谱系质量，不是 normalized survivor proportions。binary response 的 q1=Z、q0=L-Z 形式与 scalar interval 同一条件，不能算两份独立确认。

这项状态限制只是同一候选的另一读数，并非另一个算法。它比功能 null 更强：reporter 可以变化却不改变未来 B 响应；因此仅拒绝状态 null 不足以宣布药物功能记忆。若测量是同一非负 kernel K，且 retained latent measures a_h≤p、q_h=Ka_h，则 q_h≤Kp 保留共同母群支配；需确保 selection 后同一 conditional kernel 仍成立。仅 baseline assay 相同不够，history-specific measurement drift 也可制造 q 违反。高维逐细胞 empirical support 几乎天然分离，不能当无推断的证明。

如果状态来自破坏性 scRNA 终点且与再挑战细胞无 lineage/sample 联结，**不能凭同一细胞系把 state 与 function 硬 join，不能据此定位中介状态或训练 paired state→function transition**。P(S=1)=P(Y=1)=.5 的边际同时兼容 Y=S 和 Y=1-S。两类 marginal bounds 分别通过也不保证存在同一个 fixed joint null；反方给出的跨历史 capacity 反例见 CROSS_ADVOCATE.md。因此不能误称无 pairing 就无法检验任何 joint restriction；能否检验须按实际 marginal capacities 明确推导。即便有 pairing 也首先给关联，causal mediator 仍需干预／额外假设。

## 5. 为什么 count + snapshots 本身不够

只有总人口 N 和 scstate proportions p 时，n_k=Np_k 的变化可由状态转移、差异增殖和死亡的多种组合产生；没有分支去向或可信 birth/death 上界，不足排除选择。barcode clone count 也未必解决，因为 clone 内仍可选择。

普通 cell counts 不能替代本候选的 founder-mass accounting。每轮只测总数、或仅追踪最终幸存细胞，都缺少 δ 和 division weights。现有 AP-1 的 46 tracks 不等于已认证所有 attempt、全部死分支及 rechallenge；ADCC 的 P/R/W snapshots 也不提供这些量。当前无可直接执行此限制的认证公共表。

## 6. 若真实数据可得，世界模型贡献怎样测

模型的对象必须是带出生／死亡质量的状态转移与明确 control schedule，分别预测：原始细胞数 N(t)、可观察 state 的 submass／distribution、以及未来真实 B 下的 Z(B)。Z 是 random-daughter path estimand，不是细胞数或物理 biomass。抗药细胞指数增殖但无死时 Z 可不变，实际肿瘤负荷却恶化；应用 utility 必须分报 N／绝对功能，不能只优化 Z。对同一完整验证 run 同时对照 mass accounting，不能只提高 survivor RNA 分布相似度。

最小训练／验证分工：只用若干 conditioning／washout 的完整短分支及共同 B 校准反馈；封存独立 batch、未用于更新的 washout duration 或真实再挑战时间分支，测试绝对存活数和 founder-weighted Z。不能从连续药物内插就称跨撤药世界模型。所有 test schedules 必须确实实施，模拟 rollout 不是 ground truth。

公平比较必须给强 direct history predictor **相同** lineage features、counts、state、完整 schedule 和标签预算，并包括简单 state mixture、普通 refit/CL、同菜单 AL、显式 birth-death＋state-transition 模型。对 direct predictor 施加相同 mass/null 信息也应作为基线；不能靠藏掉谱系信息制造优势。

世界模型的正贡献候选是：这些真实转移约束能否在独立 schedule 外推上以更少反馈改善绝对功能误差，并正确定位 selection-only 可解释／不可解释的分支。它必须比同信息最简单约束模型有预登记的实用收益，否则只保留识别实验本身，不立新架构。

本轮没有新 Uψ。用上述界限决定是否拒绝 null／保留多解释是普通推断，不能包装成 RSI；程序搜索完全能包含同一规则。后续只有明确改动 improver、冻结版本、在独立未来更新机会上同数据同预算比较，才讨论改进策略本身的继承。

## 7. 最便宜 kill、成功与停止

**先做资产资格，当前不训练：** 需要已公开或本来可用的完整 founder→division/death/loss 树、处理／洗脱／再挑战时间、live count、pre-B live state 与 post-B functional fate 的键、所有 attempts 及独立 batch。只取 manifest/schema 即能先判断是否具备；没有则停止该资产，不把不完整 tracks 拼成闭环。

**若未来已有合格实验条件：** 先选一个低 death／低 tracking-loss conditioning 窗口，随机 h/c，充分 washout，共同 B，完整记录所有 founder。最便宜的主检验只需 Z 与 δ，不要求大组学。state 用于进一步定位并测试 predictive sufficiency。

可在新的正式协议中锁定实用 margin `ε=0.05` founder mass（先经独立 calibration 判断可分辨性），对母群期望与已知 randomization／batch dependence／challenge stochasticity构建同时置信界，例如 `lower95(z_h) > upper95(z_c+u_c+δ_c)+ε` 或反向成立。这是拟议校准需求，不是已实现的有效检验。measurement error／树重建误差必须计入 slack；不能看结果后删除大δ/u条件或放宽 ε。

成功分层：先拒绝仅选择 null；再要求 washout 后的功能效应在独立 batch／新真实时间分支复现；最后才比较动态模型是否以同预算更好预测真实 endpoint。只成功第一步不等于预测性能、agent、inheritance 或联合收益。

停止条件：完整树缺失且无法给 tight loss bound；δ／测量 slack 大到不能越过实用 margin；没有真正洗脱／共同 B；状态－功能无法联结却要求中介建模；质量加权后的差异落在选择可解释范围；或模型未优于同信息简单 birth-death/mixture/direct baselines。前几项是不可识别／资产失败，不能记录为生物 memory 阴性。

## 8. 当前结论与最小缺失条件

**只保留一次有界 source／近邻理论资格；当前不晋升核心机制。** 本式在该条件下是已知 missing-outcome／dominating-subprobability 界，world、agent、inheritance、joint gain、RSI 均未验证。不因 universal predictor 可表达而否定未来具体生物观察的价值；但没有新观察、合格资产或额外配对／时间识别限制时，不能把标准检验升级为创新。

最小缺失不是更多模型参数或 DeepSeek 调用，而是**包含丢失／死亡分支的完整 lineage mass、真正 washout 后共同 rechallenge 的配对功能读数，以及独立实验 run**。若只有当前已审 snapshots／不完整 tracks，本轮结论为：没有可执行的新模型／RSI 核心；不以此宣称完成总目标。
