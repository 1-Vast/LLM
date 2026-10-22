# 第二轮独立倡议：用守恒谱系质量给“仅选择”解释设可观测界限

2026-10-22，mechanism_advocate。依 parent 新任务独立形成；**未读取本轮其他 agent 的机制结论，不联网，不读取新数据 body，不实现架构**。仅复用上一轮已经审查的 AP-1／ADCC 文献设计及既往失败边界。

**判断：保留一个值得证伪的最小经验识别候选；当前无新算法或 RSI 已成立。** 其贡献候选不是“又一个带记忆的网络”，而是在一组明确的谱系观测条件下，给出“任何仅靠既有类型的差异生长和死亡都必须满足”的可观测限制。若限制被独立响应违反，世界模型必须允许谱系内功能状态改变；若限制未被违反，不能把人口组成变化标成细胞内记忆。

## 1. 应用与仅有的一个候选

应用限定：癌细胞经历一个 conditioning drug／低剂量适应、明确 washout、同环境再挑战后，判断功能变化是否可完全由预存响应类型的选择解释。AP-1 的 trametinib 分阶段适应／live reporter 可作设计动机；ADCC 则说明 effector 状态会混入功能读数，若采用该体系必须先另控制 effector。**不拼接两篇论文的数据，也不假设现在有完整谱系。**

候选的具体操作是：

1. 在 conditioning 开始前给每个 founder cell 质量 1，随机分配历史 h（例如 conditioning→washout）或 c（vehicle→相同 washout）。
2. 完整观察每次二分裂：母细胞的质量各半分给两个女儿。死亡／脱落／失踪分支的质量计入 missing mass，绝不把它从分母删除。这样细胞数可增长，但同一 founder 的全部潜在谱系质量仍为 1。
3. washout 后测 live single-cell state；再施加共同 rechallenge B。对 B 期间也沿树分质量，测活着的 descendant mass。函数终点不是仅对 survivor 重新归一化的表达均值。
4. 用 conditioning 阶段丢失质量给“选择可造成多少差异”设最坏情况界限；只有超出界限，才将反馈作为反对 selection-only 的证据。

这是一个具体的**经验识别条件**。谱系重加权和 missing-data bounds 是已知数学工具，本稿不宣称其代数是新理论；相对本项目的实质变化是将它们用于真实 washout→functional rechallenge 的可否证 null，并要求世界模型同时解释质量、状态和功能。全领域是否已有同一实验与限制仍未查明，不能称 first-of-kind。

## 2. 它究竟排除什么

明确 null `H_sel`：conditioning 历史只改变预存、沿谱系固定的响应类型的分裂／死亡／移除概率；共同 washout／rechallenge 下，随机选择一个女儿继续的 lineage path 的 B 响应潜能不因 h/c 而改变。允许任意类型异质性，允许选择与 B 响应任意相关，允许 conditioning 导致差异增殖；**不假设选择与功能独立**。

随机化保证在 conditioning 前两臂有同分布的 latent B 响应潜能。沿每次 division 对半分权，消除某类型仅因繁殖更多而被额外加权；conditioning 死亡仍可能产生 survivor bias，因此保留其全部质量作为未知。

null 不包含 conditioning 改变分裂次数后真实改变了女儿的功能类型、遗传突变、细胞周期状态、残留药物、损伤或可持久的表观状态。这些都是不同的谱系内变化候选。**拒绝 H_sel 只证明“仅预存类型选择”不够，不唯一证明 epigenetic memory。** 细胞内功能历史效应还必须经共同环境、药物清除、细胞周期／损伤和独立重复等检查；不能把所有违反都归给 AP-1。

## 3. 最小过识别限制及推导

每个臂按起始 founder 质量取平均，记：

- `L_h`：rechallenge 开始时仍在观察中的 live lineage mass；`δ_h=1-L_h` 是 conditioning／washout 阶段丢失的质量。
- `Z_h(B)`：共同 B 后存活的 lineage mass，仍以 conditioning 前的 founder mass 为分母。因此 `0≤Z_h≤L_h`。
- `μ_B`：若未被 conditioning 选择移除，原始 founder 分布在共同 B 下的平均功能潜能。H_sel 要求 h/c 共享这一量。

conditioning 中已丢失的每单位质量在 B 下最多贡献 1、最少贡献 0，因此 H_sel 必须满足：

`Z_h(B) ≤ μ_B ≤ Z_h(B)+δ_h`。

对多个随机历史，**所有区间必须有共同交集**：

`max_h Z_h(B) ≤ min_h [Z_h(B)+δ_h]`。

对两臂等价地，若 `Z_h > Z_c+δ_c` 或 `Z_c > Z_h+δ_h`，即使允许 conditioning 按隐藏类型任意选择，也无法解释观察。该条件不是拿直接预测器的表达能力作限制，而是该生物 null 在已知 mass accounting 下的可观测必要条件。

零丢失 `δ_h=δ_c=0` 时，H_sel 要求 `Z_h=Z_c`，任意增殖速率差异已被 lineage weights 抵消。这提供最便宜、最有力的 conditioning-window 资格目标；不必先造复杂模型。

注意这是必要条件，非充分条件：区间相交不能证明没有 memory，可能只是损失太多、界限太宽。有限样本还需按独立 biological run／batch 估计不确定性，founder/cell 不自动等于独立重复。未测到／难跟踪的分支应增加 δ 或 measurement-error slack，不能默认为存活或剔除。

## 4. 单细胞状态提供第二个可核查限制，而非替代功能

若有同一完整 lineage 上可重复测量的 live state（例如经过验证的 reporter），可在共同终点定义预先固定的状态分区 `S_k`，记各臂中 alive lineage submass `q_h(k)`，其和为 L_h。更强的 selection-only null 假定 conditioning 不改变该测量状态的 path-level 潜能，只删去某些路径；于是存在同一未选择的概率分布 `π(k)` 满足 `q_h(k)≤π(k)`。

这要求 `sum_k max_h q_h(k)≤1`。超过 1 表明不存在一个仅被不同删去的共同状态分布。它明确使用绝对谱系质量，而不是 normalized survivor proportions。

这项状态限制只是同一候选的另一读数，并非另一个算法。它比功能 null 更强：reporter 可以变化却不改变未来 B 响应；因此仅拒绝状态 null 不足以宣布药物功能记忆。必须分别报告状态和真实功能两项结果，不能用状态变化代替 Z。

如果状态来自破坏性 scRNA 终点且与再挑战细胞无 lineage/sample 联结，最多做各自 marginal 的 null 检验；**不能凭同一细胞系把 state 与 function 硬 join，不能据此定位中介状态或训练 state→function transition**。若要由可观察状态预测 B，最低需要同一活细胞／同一可追踪 lineage 的 pre-B state 与 post-B function 配对；live reporter 也不自动是完整 state。

## 5. 为什么 count + snapshots 本身不够

只有总人口 N 和 scstate proportions p 时，n_k=Np_k 的变化可由状态转移、差异增殖和死亡的多种组合产生；没有分支去向或可信 birth/death 上界，不足排除选择。barcode clone count 也未必解决，因为 clone 内仍可选择。

普通 cell counts 不能替代本候选的 founder-mass accounting。每轮只测总数、或仅追踪最终幸存细胞，都缺少 δ 和 division weights。现有 AP-1 的 46 tracks 不等于已认证所有 attempt、全部死分支及 rechallenge；ADCC 的 P/R/W snapshots 也不提供这些量。当前无可直接执行此限制的认证公共表。

## 6. 若真实数据可得，世界模型贡献怎样测

模型的对象必须是带出生／死亡质量的状态转移与明确 control schedule，分别预测：原始细胞数 N(t)、可观察 state 的 submass／distribution、以及未来真实 B 下的 Z(B)。在同一完整验证 run 上同时对照 mass accounting；不能只提高 survivor RNA 分布相似度。

最小训练／验证分工：只用若干 conditioning／washout 的完整短分支及共同 B 校准反馈；封存独立 batch、未用于更新的 washout duration 或真实再挑战时间分支，测试绝对存活数和 founder-weighted Z。不能从连续药物内插就称跨撤药世界模型。所有 test schedules 必须确实实施，模拟 rollout 不是 ground truth。

公平比较必须给强 direct history predictor **相同** lineage features、counts、state、完整 schedule 和标签预算，并包括简单 state mixture、普通 refit/CL、同菜单 AL、显式 birth-death＋state-transition 模型。对 direct predictor 施加相同 mass/null 信息也应作为基线；不能靠藏掉谱系信息制造优势。

世界模型的正贡献候选是：这些真实转移约束能否在独立 schedule 外推上以更少反馈改善绝对功能误差，并正确定位 selection-only 可解释／不可解释的分支。它必须比同信息最简单约束模型有预登记的实用收益，否则只保留识别实验本身，不立新架构。

本轮没有新 Uψ。用上述界限决定是否拒绝 null／保留多解释是普通推断，不能包装成 RSI；程序搜索完全能包含同一规则。后续只有明确改动 improver、冻结版本、在独立未来更新机会上同数据同预算比较，才讨论改进策略本身的继承。

## 7. 最便宜 kill、成功与停止

**先做资产资格，当前不训练：** 需要已公开或本来可用的完整 founder→division/death/loss 树、处理／洗脱／再挑战时间、live count、pre-B live state 与 post-B functional fate 的键、所有 attempts 及独立 batch。只取 manifest/schema 即能先判断是否具备；没有则停止该资产，不把不完整 tracks 拼成闭环。

**若未来已有合格实验条件：** 先选一个低 death／低 tracking-loss conditioning 窗口，随机 h/c，充分 washout，共同 B，完整记录所有 founder。最便宜的主检验只需 Z 与 δ，不要求大组学。state 用于进一步定位并测试 predictive sufficiency。

可在新的正式协议中锁定实用 margin `ε=0.05` founder mass（必须先经独立 calibration 判断可分辨性），用按 batch 的同时置信界检验：`lower95(Z_h) > upper95(Z_c+δ_c)+ε` 或反向成立。measurement error／树重建误差必须计入 slack；不能看结果后删除大δ条件或放宽 ε。

成功分层：先拒绝仅选择 null；再要求 washout 后的功能效应在独立 batch／新真实时间分支复现；最后才比较动态模型是否以同预算更好预测真实 endpoint。只成功第一步不等于预测性能、agent、inheritance 或联合收益。

停止条件：完整树缺失且无法给 tight loss bound；δ／测量 slack 大到不能越过实用 margin；没有真正洗脱／共同 B；状态－功能无法联结却要求中介建模；质量加权后的差异落在选择可解释范围；或模型未优于同信息简单 birth-death/mixture/direct baselines。前几项是不可识别／资产失败，不能记录为生物 memory 阴性。

## 8. 当前结论与最小缺失条件

**候选保留：一个有显式 selection-only 区间限制的 washout→rechallenge 经验识别条件。不是新网络，不以已知组件组合自动宣称新颖，也不因 universal predictor 能表示就否定其科学价值。** 新颖性查证与真实可用性仍未完成。

最小缺失不是更多模型参数或 DeepSeek 调用，而是**包含丢失／死亡分支的完整 lineage mass、真正 washout 后共同 rechallenge 的配对功能读数，以及独立实验 run**。若只有当前已审 snapshots／不完整 tracks，本轮结论为：没有可执行的新模型／RSI 核心；不以此宣称完成总目标。
