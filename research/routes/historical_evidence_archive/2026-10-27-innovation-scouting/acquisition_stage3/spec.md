# R198-A5 规格：取证策略（acquisition）的等合法预算比较设计

2026-10-27。角色：独立设计/执行审计员。**本文件只做设计、成本模型与先例核验，不运行 acquisition、不训练模型、不模拟/报告任何 acquisition 收益。** 文中所有数字是**规划算术**（physical wells / planning cost units），不是货币实测、不是效果证据。

- 输入（只读）：[R192/R193/R194/R195 记录与 SYNTHESIS](../../SYNTHESIS.md)（C136/C144/C154/C155/C156/C167/C171/C172）、[跨领域方向报告](../../2026-10-27-cross-domain-directions/report.md)（第 3 步与 H3）、[方法先例审计](../../2026-10-27-handoff-method-audit/report.md)、R2 整板/KG 回放（[report](../../2026-10-26-agent-cell-evidence-r2/report.md)/[PROTOCOL](../../2026-10-26-agent-cell-evidence-r2/PROTOCOL.md)）、R187 药对主动学习（[report](../../2026-10-27-agent-cell-identifiability-r187/report.md)）、R189-I003 先例核验（[evidence](../../2026-10-27-detectability-acquisition/evidence.md)）、R198-A1 冲突信号规格（[spec](../conflict_signal/spec.md)，只读引用其更新器 M1 与 DPG 接口，不评价其机制）。
- 配套文件：[cost_model.md](cost_model.md)（成本模型与等成本算术）、[prior_art.md](prior_art.md)（先例覆盖）、[protocol_draft.md](protocol_draft.md)（若冻结须写死的项）、[record.md](record.md)、[usage.json](usage.json)。
- 确定性算术：[tmp/a5_cost_arithmetic.py](../../../tmp/a5_cost_arithmetic.py) → [tmp/a5_cost_arithmetic.json](../../../tmp/a5_cost_arithmetic.json)（离线、固定算法、可重跑；本文件引用其键值）。

## 0. 范围、前置条件与谱系

- **任务位置**：新主线第 3 步——"**修订能迁移后，再比较如何取证**"（跨领域方向报告 §7 第三步、H3）。因此本设计**只有在第 2 步（固定反馈的更新比较）显示可迁移修订后**才允许冻结执行；本轮不运行、不排名策略、不产生效果数字。
- **与 A1/A2 的关系（写死）**：A1（`inconclusive`，C171）与 A2（`condition_structure_present` 但 `share=1.43%`，C172）**都不构成本阶段的准入**；A5 不是 A1/A2 的复活或换聚合，也不把 1.43% 当"规律总量"。A1 的 M1（PRU-CC 更新器）与 M2（DPG，决策精度门控购买）只作为**候选接口**引用：M1 可当固定更新器候选，M2 可当候选 acquisition 策略；**A5 不评价其机制收益**（那是 A1 的 P4/P5）。
- **不做**：不运行 acquisition/训练/回放、不模拟收益、不下载新数据、不做机制/临床主张、不晋升代码、不启动 B/C/RSI；不改其它目录、INDEX、SYNTHESIS、git；不按 Q 大小挑层/挑单位，不用 Q 结果反推模型/阈值。

## 1. 决策任务定义（冻结前须由 Lead 确认的"任务对象"）

- **单位**：`u=(c, pair, design)`：c=细胞背景；pair=有序组合条件（anchor→library，含方向）或无序药对（须写死一种）；design=冻结的剂量布局（如 anchor 浓度 / library 剂量集）。端点 y=冻结的功能读数（候选：`SYNERGY_DELTA_EMAX`，须先冻结可比性与端点协议；**换端点即换问题，不许在 acquisition 过程中换**）。
- **动作（可购买决策）** `b ∈ B(U)`：购买一个**合法测量批次**（见 §2 菜单），付全成本，得到该批次全部结果（含失败孔与对照），再更新后验。
- **未查询菜单** `U`：候选组合/条件集合（固定在看到任何反馈之前；菜单必须可枚举、可定价、且每个动作的"购买批次"唯一）。
- **效用** `U(a)`：单动作的决策效用，冻结为**功能读数**的函数（例：top-k 命中次数的净收益，或 `−Viability`/ΔEMAX 的 top-k 均值）。**明确不用相关系数替代**（跨领域报告 H3；R187 的教训：相关增量 ≠ 决策收益）。
- **oracle / 菜单头空间**：`U_oracle = max_{可买全菜单} 效用`；`U_static = 现有最强静态预测（不买任何新数据）`；`headroom = U_oracle − U_static`。**headroom 是菜单属性，与 acquisition 策略、成本都无关**；若 headroom 小于决策指标的 MDE，则该菜单**不可检验 acquisition**（见 §5 与 §7）。
- **损失/后悔**：`loss = U_oracle − U(决策)`；`regret = U_oracle − U(策略所购后决策)`。
- **净收益**：`NB = 效用增益(购买后 − 购买前) − λ · 成本`，λ 为预注册的成本→效用换算（须由 Lead 认可；不许在结果后调整；报告 λ 敏感性，只报"每成本单位"曲线，不用单一 λ 制造赢家）。

## 2. 合法菜单与可购买动作（来自现有资源，冻结前须逐项确认）

**物理锚点**（均有出处，见 [cost_model.md](cost_model.md) §1）：GDSC/Jaaks 组合屏为 **1,536-well** 板；每个 (cell, anchor-library) 组合块 = **2 anchor 浓度 × 7 library 剂量 = 14 个 combo well**，每板含 5 份 anchor-alone（两浓度）、4 份 library-alone（全 dose response）、阴性 DMSO/阳性（MG-132/staurosporine）/blank 对照，单份 combo 重复（primary screen）；BATCHIE PAIR 公开屏为 **384-well** 板，我们 R2 的每个合法动作 = **2 张物理板 / 766 条原始 well 记录**（含控制与失败孔）。

| # | 动作 | 单位 | 物理内容（wells） | 可否单独购买 |
|---|---|---|---|---|
| A1 | **整板（plate）** | 一张物理板 | 384-well 或 1,536-well 全板（含对照/参照/空孔） | 是（最小物理单位） |
| A2 | **组合行（row / anchored key）** | 一个 (cell, pair) 的 anchored 2×7 | 14 combo + 12–38 单药参照 + 8–16 对照 ≈ **34–68 wells/key** | 否（须占板；可与其他行拼板） |
| A3 | **药对×剂量网格（dose grid）** | 一个 (cell, pair) 的 n×n 网格 | 6×6: 36 combo + 12–24 refs + 8–16 ctrl ≈ 56–76；10×10: ≈128–156 | 否（须占板） |
| A4 | **单剂量孔（single-dose key）** | 一个 (cell, pair, 单剂量) | 1 combo well（+ 0–2 对照）；参照可复用已有 fitted 单药数据（0 新 wells）或买新参照（14 wells/key） | 否（须占板） |
| A5 | **单药参照包（mono reference）** | 一个 (cell, drug) 的 7 点单药曲线 | 7 wells + 2–4 对照（BeatAML 风格 7×1） | 是（可复用历史数据，见 A4） |
| A6 | **重复（replicate）** | 上述动作的重复份 | 技术重复 ×1/×2/×3；独立生物重复（不同日/培养）另计 | 是（按倍数乘 wells） |
| A7 | **新细胞（new cell line）** | 一条细胞系 | 播种密度优化 1,344 wells（GDSC：6 密度 ×224 wells on 1,536 板）+ day=1 无药对照板 1,536 wells | 是（固定成本块，与买多少测量无关） |
| A8 | **批次（batch）** | 一次培养/上机运行 | 固定成本；本设计冻结"每批 ≤10 板"的打包规则 | 是（通过动作组合隐式购买） |

**不可购买项（写死）**：
1. **设计外剂量点/未公开的完整剂量布局**：DrugComb/Jaaks 只发布设计列层面的浓度；未公开的 library 完整浓度点集不可购买（只能按已认证设计列重测）。
2. **独立培养/独立生物重复的"历史等价物"**：barcode 不相交不等于独立培养；没有培养/传代/接种批次记录时只能买新批次（另计成本），不能把旧数据当免费重复。
3. **靶点占据/机制读数**：现有组合功能屏没有配套 engagement/mechanism 端点；不能把 ΔEMAX 读数当靶点参与。
4. **未见药物的化学身份/合成**：菜单只能使用已购化合物库/已有实体；未在库的药物无法通过"购买测量"得到。
5. **跨 study/跨来源的"补测"**：只能购买新实验批次；不能购买历史未测点的"回填"。
6. **QC/失败孔的免费信息**：失败孔仍收费（R2 已冻结"支付全部 well，含失败"），且 QC 只在评分端揭示、不进入 acquisition 特征。
7. **计算/LLM 成本不可隐藏**：若策略用 LLM/额外算力，按预注册单位计入总成本（R2/跨领域报告要求）。

## 3. 成本与统计检定力必须分开（本任务的核心纪律）

- **成本模型（[cost_model.md](cost_model.md)）回答"买多少物理测量/花多少 planning cost units"**：wells、plates、batches、cells、replicates、failed wells、controls、single-agent refs。成本算术见 cost_model §2–§5（例：C136 的 1,600 keys 在 central 场景、125 细胞下约 **4.0×10^5–6.2×10^5 CU**（cell setup 计入）或 **7.7×10^3–2.2×10^5 CU**（setup 视为 sunk）；同一预算 100,000 CU 可买 ~46 个 R2 式整板动作或 ~21,000 个单剂量 key——形状完全不同）。
- **统计模型回答"这些测量能检定多大效应"**：有效独立单元不是 wells/keys，而是**细胞、cell×pair、批次**层面的独立单位；C136 已给"约 **1,600 个 cell×pair 测量**才达到 80% 检定力（200 个时 power≈0.46）"；C144 给"分配近乎中性，总量才是关键"；C154/R187 给"补 50 对 ≈1,835 行只让估计动 ±0.003 → 估计已饱和，主动学习无法救压平的曲线"；C156 给"'测量行数多'≠'可留药单元多'"；C171 给"96 细胞 → n_eff≈189，MDE 远大于 δ_min"。
- **两条线在比较中的用法（写死）**：
  1. 所有策略在**同一 total cost units（预算 B_CU）**下比较（不是同行数、同 wells、同 keys）；
  2. 同时报告**有效独立单元数**（cells/pairs/batches/keys）与该预算下的 **MDE_decision**；
  3. **预注册 δ_min**：δ_min 必须由"决策有用差异"定义（不是旧 CI 反推），且必须满足 `headroom > MDE_decision(计划预算)`；若不满足 → 该菜单/预算对 acquisition 不可检验，停止（见 §7）。
- **菜单接近 oracle 的风险（R2 的实证）**：R2 的 5 细胞冻结菜单上，静态预测效用 −0.005547、oracle −0.001205，**剩余 regret 仅 0.004343**；同一轮 KG−random 的 95% 区间 [−0.0811,+0.0636]（宽 ~0.145）≫ headroom。**即：在那个菜单上，任何 acquisition 比较的 MDE 都大于菜单头空间——菜单本身饱和，测试不可检验**（这是菜单属性，不是方法失败）。A5 要求每个候选菜单先算 `headroom`，并按下面规则判定（§7 S2）。

## 4. 固定更新器契约（先固定更新比较，再比较采样）

冻结前必须写死，执行时**所有策略共用同一个更新器**（R2/PROTOCOL 与跨领域报告 §7 第二步的要求）：

1. **输入**：已购数据 `D_bought`（含失败/QC 由评分端处理）、冻结的特征映射 φ、源数据（训练用）；**不得**读未购/terminal 结果。
2. **输出接口**：对全部未查询动作 `a ∈ U` 给出 `(预测均值, 不确定性/后验样本或方差, 可选决策相关量)`；acquisition 策略只能使用该接口与设计特征（R2：枚举全部真实动作、不拆免费 label）。
3. **候选更新器（冻结时选一，不得按结果择优）**：
   - **U1（首选，若 A1 冻结）**：A1 的 M1 PRU-CC（`θ_new = argmin ||W_S(Φ_Sθ−y_S)||² + λ||θ−θ_old||² s.t. 关系约束`；λ 由内层药物分组 CV 选；冲突证书可输出）——见 [../conflict_signal/spec.md](../conflict_signal/spec.md) §5；
   - **U2（普通强基线）**：按细胞/药对分组的层级经验贝叶斯（或全量重训/少样本适配），超参数同网格；
   - **U3**：多输出 GP（RBF/冻结核参数，noise 由源数据/重复标定）——用于 GP-KG/PDBAL 类策略。
   **所有策略与所有基线共用同一更新器与同一算力上限**（报告 wall-time/CPU，不隐藏）；基线也可正常更新，不得人为冻结其结构/后验（R2 已犯过"冻结基线"风险的教训）。
4. **禁止**：策略自带更新器、策略调自己的超参数、更新器用策略分数选参数、acquisition 读 QC/terminal（见 §8）。

## 5. 比较器（冻结菜单、预算、更新器后）

| ID | 策略 | 定义（冻结） | 作用 |
|---|---|---|---|
| S0 | **static / no-buy** | 不购买；用源数据最强静态预测选动作 | 下界与"成本是否值得"的基线 |
| S1 | **固定配对采集** | 预注册的 13 对 × 125 细胞（C136 规模）式固定设计，按预算买满整行/整板 | 最省的"非自适应"设计；测"自适应是否值得" |
| S2 | **随机整板** | 在合法整板动作上均匀随机（R2 的精确均匀期望；多 seed 或全枚举） | 主随机对照 |
| S3 | **贪心 exploit** | 每轮买"预测 top-3 效用最高"的动作（整板/行） | 强简单基线（GDSC2 类基准上常胜，见 prior_art F10） |
| S4 | **GP-KG（batch）** | 知识梯度（Gaussian fantasy，R2 用 16 fantasy；batch KG 按整板联合观测） | 经典贝叶斯优化 acquisition |
| S5 | **决策 AL / VOI** | 选择"最大化未查询动作决策损失下降"的合法测量（决策聚焦；可含 A1 的 DPG 若冻结为候选） | 决策导向 acquisition |
| S6 | **PDBAL / BATCHIE 式** | 后验样本距离（BATCHIE 的 PDBAL）批量选板 | 组合筛选领域最强已发表近邻 |
| S7 | **oracle（事后）** | 事后枚举全菜单最优 | 只用于 headroom/regret，**不作为可执行策略** |

**公平性写死**：同一菜单、同一更新器、同一 total CU、同一随机 seed 集、同一信息（特征/参考/单药/批次元数据/支持标签）与同一计算预算；每策略在同一预算下独立执行；随机策略用全动作均匀期望（可枚举时）或预注册 seed 集合。

## 6. 指标（主/次与口径）

- **主指标**：**每成本单位的未查询决策净收益**（`NB per CU`），在**配对预算**下比较策略 S vs S0/S2/S1：`ΔNB = NB_策略 − NB_对照`，按细胞/药对/批次聚类 bootstrap 报告 95% CI 与 MDE。
- **次指标（预注册，只报告不改判定）**：决策损失/regret（未查询动作上的 top-k 效用或损失）、命中率/hit@k、购买批次数/板数/keys、成本分解、oracle 差距。
- **单位与聚类**：决策单元是 (cell, pair) 或菜单动作；独立单位按细胞（96/125 上限）、药对、批次聚类；**不得**把 wells 或 1,536 板内孔当独立样本（R2/R187 教训）；报告 n_eff 与 ICC。
- **MDE/δ_min（与成本分开）**：MDE_decision 由**预注册的效应量、聚类结构、预算/keys** 计算（C136 式：1,600 keys→80% power；200 keys→0.46 为规划锚点）；δ_min 由"决策有用差异"定义（例如 top-k 净收益的最小业务意义），且必须 `MDE_decision ≤ δ_min ≤ headroom`；否则 §7 停止。**禁止**用旧 CI 下界反推 δ_min（R193 教训）。
- **不替代**：支持反馈命中率、训练误差、全局 Spearman/相关系数均不能替代未查询决策指标（R187/C154 教训）。

## 7. 停止规则（冻结）

- **S1 成本抵消**：`ΔNB = NB_策略 − NB_static` 的 95% CI 上界 < δ_min（成本无法被收益覆盖）→ 该策略分支停止，不发展。
- **S2 菜单接近 oracle**：`headroom < MDE_decision`（或 headroom < δ_min）→ 该菜单不可检验 acquisition，停止；**换一个真正有 headroom 的菜单需要独立理由**（R2 教训）。
- **S3 无稳定增量**：在预注册的两个独立执行轮次/seed 集合上，`ΔNB` 的 CI 均包含 0 或点估计 < δ_min，且没有一致排序 → 判无稳定增量，停止该策略分支。
- **S4 饱和**：若增加测量对更新的改变（|Δ预测|/ΔNB）低于预注册饱和阈值（C154/C144 的现象），停止"再加数据"路线。
- **S5 预算耗尽/泄漏**：预算达到上限即停；任何策略被证明使用了未购/QC/terminal 信息 → 该策略作废（`leakage`），整轮判失败类别，不救。

## 8. 泄漏与公平防护（写死）

1. **数据可见性**：acquisition 只看源数据、已购数据、设计特征；未购/terminal/QC 仅在支付并揭示后可入更新与评分；QC 只在共同评分端使用（R2 首版 bug 的教训：不能用 QC 过滤后的池选板）。
2. **菜单冻结**：`U` 与 `B(U)`（可购动作）在第一次购买前枚举并哈希；不得事后增删动作或按结果挑层。
3. **随机性**：随机策略的全动作枚举优先；必须抽样时用预注册 seed 集合，且所有策略共享同一 seed 用于共同随机项。
4. **等成本核查**：见 [cost_model.md](cost_model.md) §6（不是等行数；必须逐策略验证 total CU 与物理量）。
5. **不隐藏成本**：LLM/算力/人工成本入账；批量固定成本按冻结打包规则分摊。
6. **不换端点/分层/δ**：端点、菜单、效用、δ_min、更新器在第一次购买前全部冻结；执行中不得改（改即新轮）。
7. **独立评估者**：terminal/评分由未参与策略设计的独立 runner 持有；策略实现者看不到 terminal（阶段 2/3 的 R2 做法沿用）。

## 9. 与既有边界的对齐

- 不把 A1 的 `inconclusive` 写成阴性；不把 A2 的 1.43% 当"条件规律总量"；不声称条件级共享规律成立（C171/C172）。
- 不用 acquisition 结果反推交互族/机制/新算法；B/C/RSI 未启动；不做机制/临床主张。
- 本阶段只在"第 2 步显示可迁移修订后"启动；第 2 步失败/不可判 → 本设计冻结但不执行（记录为条件未满足）。

## 10. 交付与下一轮接口

- 本轮交付：[spec.md](spec.md)（本文件）、[cost_model.md](cost_model.md)、[prior_art.md](prior_art.md)、[protocol_draft.md](protocol_draft.md)、[record.md](record.md)、[usage.json](usage.json)；算术在 `tmp/a5_cost_arithmetic.py/json`。
- 若 Lead 下一轮冻结：`protocol_draft.md` 的「冻结清单」需全部落数（成本系数由真实报价/LOI 替换、菜单由实际资源确定、δ_min/MDE 由 pilot 与决策效用确定），并由独立挑战者审过才可执行；执行时按 §8 的可见性与等成本核查。
- **本文件不构成效果证据**：所有成本/容量/headroom 数字是规划算术或他人已发表描述；没有运行 acquisition、没有训练、没有新的生物效果。
