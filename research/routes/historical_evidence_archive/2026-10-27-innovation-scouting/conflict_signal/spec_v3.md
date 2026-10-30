# R198-A1v3 机制规格：跨 tissue 池化的关系冲突信号（修订版）

2026-10-27。本文件按 R198-A1v2 复审 [challenge_A1_v2.md](challenge_A1_v2.md)（revise，≤5 必改）与 **Lead 已决事项（写死，不再开选项）** 修订 [spec_v2.md](spec_v2.md)；v1/v2 文件保留不改。**只做设计；本轮不运行效果/relations_check/体检/MDE 预检，不读 S/U 响应，不声称新颖性。**

## 0. Lead 已决（写死）

1. **Context 定义 = 跨 tissue 池化（pooled across tissue）**：关系上下文不再按 tissue 切分，tissue 作为 **nuisance**（细胞/组织随机效应或固定效应）进入模型；主关系族 = pooled。**Breast/Colon 限制版仅作敏感性**并披露外部有效性限制；per-tissue 关系一律 exploratory，不参与主判定。
2. `n_ctx_min=12`、`alpha_per_relation=0.01` **保持不放宽**。
3. **S=24 可行**（24≥12）；P0a 增加 **S 侧 Cond_r 覆盖 ≥12（metadata-only）预检**。
4. **P0a 验收只用区间宽度 2.0σ_r**；效用范围移到 **P0d**（δ_min 定义后），P0a 不依赖 utility。
5. **覆盖分母冻结为关系网格 229 → 通过关系 ≥115**（写死）。
6. **MDE 标注**：MDE(80%, n=12) = **p1≈0.9307**；**p1≥0.95 为保守设计目标**（power 0.882，不是 MDE）；补 n–p1 表（§3.3）。
7. **P0b/P0c 用依赖生成模型**（cell/tissue/batch 随机效应）校准 type-I/功效，报 **ρ/κ 敏感性**；primary 家族/BH 写死。
8. **M_setup 正式概率模型 + 共享预测似然**；惩罚拟合准则/权重/δ_fit/CV 写死；J 候选族生成写死；κ 用 nuisance-only/留出半/置换估计；退出上限给 operational 分母。
9. **统一 64/16 与 84/24/17**：Stage 0/Stage 1 统一为 **reference 84 (A42/B42) / S 24 / U 17**；64/16 不再作为可选配置（登记为已废弃口径）。
10. **P0b 独立生成器**（iid + 依赖两版，不得注入参考违反结构）；**P0c** ±0.05/模拟次数/n_eff 写死；**P0a–P0d 流程清单化**；保留 A4/A5 接口、Stage 1 三类、(iii) 仅 proxy、措辞模板。
11. **关系集算术写死**（§2.1 可行性表）：tissue-specific 不可行 → 由跨 tissue 池化解决；若池化后仍不可行 → `data_unavailable`/`design_invalid` 停，不降 n_ctx/不放宽 α。
12. 不变：不声称新颖性；C141/C154/C160/C167/C171/C172/C174/C175/C176/C177 边界；不换端点/不换聚合；只排组合不排细胞。

## 1. 关系与 context 定义（v3 冻结）

- 关系单位（同 v2）：`d_c(p,q) = y(c,p) − y(c,q)`，p=(anchor a, library l1)、q=(a,l2)，**同方向**（anchor→library）、同 `ANCHOR_CONC`、同 `LIBRARY_CONC`、同端点；细胞级对比。
- 关系 `r = (Cond_r, a_r, l_r, u_r)`：
  - **`Cond_r`（v3）=（direction=anchor→library, ANCHOR_CONC, LIBRARY_CONC, endpoint, cell-pool）= pooled**；**tissue 不进 Cond_r**，而是进入 nuisance（§1.2）。
  - `a_r`：nuisance-正交的受控对比（同 anchor/两浓度下的 library 差异；对细胞主效应、药对/方向主效应、剂量主效应、tissue 主效应、batch 主效应正交）。
- **context（v3 冻结）= 一个独立细胞**（S 细胞；每个细胞在 Cond_r 内对每个关系贡献一个符号）。细胞间共享药对/板/批的依赖由 §3.2 的依赖零分布/P0b/P0c 处理，不再用"cell-pair 组"当 context（删除 v2 的冲突定义）。

### 1.2 tissue 进 nuisance 的检验口径（写死）

- 主模型：`d_c ~ μ_r + u_{tissue(c)} + v_{batch(c)} + ε_c`（u、v 为随机效应；tissue/batch 从元数据预注册）。关系检验用 **tissue/batch 调整后的 μ_r**（REML/BLUP 或固定效应），区间由按细胞 cluster bootstrap 给出。
- 主关系族（pooled）：只要 μ_r 方向在 S 的 ≥12 个细胞上一致，且通过 α=0.01/BH q≤0.10。
- **敏感性（仅报告、不改主判定）**：Breast/Colon 限制版（去掉 Pancreas 关系）；per-tissue 关系 exploratory；tissue×contrast 异质性检验（Cochran Q/I²）；若 tissue 交互显著且方向反转 → 主关系降级为"跨组织平均"并在报告披露；**不得**在看到结果后改成 per-tissue 主族。
- 外部有效性：主族是跨 tissue 平均，报告明确"不保证每个 tissue 都成立"；Breast/Colon 敏感性用于披露样本构成限制（Pancreas 仅 28 matched 细胞）。

## 2. 关系集资格（Stage 0 / P0a）

### 2.1 细胞可行性算术（写死；复核 challenge_A1_v2 §0/§1）

| 口径 | Breast | Colon | Pancreas | 合计 | 可行性 |
|---|---|---|---|---|---|
| Original 125 细胞 | 51 | 45 | **29** | 125 | tissue-specific 需 reference A/B 各≥12（24）+ S 每 tissue≥12（12）= 36 > 29 → **不可行** |
| matched 96 细胞 | 33 | 35 | **28** | 96 | 同上 36 > 28 → **不可行** |
| S=24 按 tissue 分层 | ~8.25 | ~8.75 | ~7.0 | 24 | 每 tissue < n_ctx_min=12 → tissue 内 X_flip 不可行 |

**结论**：tissue-specific Cond_r 下 X_flip 结构性不可行（不是风险）；Lead 决定 **pooled context** 解决：reference 84（A42/B42，⊆ matched 96，按 tissue 分层比例）**跨 tissue 池化**；S 24 从剩余 41 细胞（12 matched 余 + 29 unmatched Original）抽取；U 17。S 侧 Cond_r 覆盖预检：每个候选关系必须在 S 的元数据上满足 Cond_r 且存在 ≥12 个 S 细胞（metadata-only，不读 y）；不满足的关系不进 Stage 0 候选集。
- **候选关系网格 = 229 条**（A0 matched 96 上 pooled 池化的同 anchor/两浓度受控 library 对比）；A42/B42 切分下预计 A/B 均≥12 的候选供给 ≈ **154** 条（Breast 86/Colon 37/Pancreas 31；用于可行性核算，不作为结果）；覆盖要求 **≥115/229 通过**（冻结），供给 154 对 115 留有 39 条余量（披露）。
- 若 S 侧预检后候选 <115，或 Stage 0 通过关系 <115 或 <R_min=20 → **`data_unavailable`**（不降 n_ctx、不放宽 α、不合并 tissue 之外的口径）。若关系构造出现协议/算法冲突 → `design_invalid`。

### 2.2 R_old 验收（v3）

- `R_old ∈ [20, 200]`；每关系独立 context（S 或 reference B 的细胞数）≥ **12**；A/B 半分离 + 半交换（方向一致率 ≥0.90）；`|μ_r| ≥ 0.5 σ_r`。
- **区间宽度：仅 `w_r ≤ 2.0 σ_r`（P0a）**；效用相关宽度检查移到 **P0d**（δ_min/utility 冻结后，Stage 1 前）。
- 多重比较（写死）：每关系精确单侧符号检验 **α=0.01**；**primary 关系族 ≤10**（预注册排序：stability_A > |μ|/σ > 较小 p > relation_id）；primary 族内 **BH q≤0.10**；exploratory 关系单独 BH q≤0.10（只报告，不参与判类/主判定）。
- 覆盖：通过关系 ≥ **115**（分母 229 冻结）；`R_old` 输出 SHA 冻结在接触 S/U 响应前。

## 3. 判据统计（v2 修正）

### 3.1 X_flip（v3 context=细胞；n/α/BH 写死）

- n_ctx_min=12（S 细胞；pooled Cond_r）；每关系精确单侧符号检验 α=0.01。
- **MDE 与 n–p1 表（写死；精确二项，单侧；α 为该 (n,k) 的最小的可拒绝水平）**：

| 真实一致翻转率 p1 | 需要 n / k | 实际 α（exact） | 80% 功效? 实际 power |
|---|---|---|---|
| p1≈0.9307 | **n=12 / k=11** | 0.003174 | **=0.7998 ≈ MDE 点**（故 MDE(80%,n=12)=p1≈0.9307） |
| p1=0.95 | n=12 / k=11 | 0.003174 | 0.8816（**保守设计目标**，非 MDE） |
| p1=0.95 | n=11 / k=10 | 0.005859 | 0.8981 |
| p1=0.93 | n=11 / k=10 | 0.005859 | 0.8228 |
| p1=0.90 | n=14 / k=12 | 0.006470 | 0.8416 |
| p1=0.85 | n=19 / k=15 | 0.009605 | 0.8556 |
| p1=0.98 | n=7 / k=7 | 0.007812 | 0.8681 |

- **规则**：预注册 MDE = "n=12 下 p1≈0.9307 时约 80% 功效"；若预期 p1<0.9307 则必须按上表增大 n（或 pre-registered 提高 context 质量），**不得事后放宽 α 或改 n**；若可用 context < 表中所需 → `insufficient_precision` 停。
- **依赖**：细胞共享药对/板/批 → exact sign test 只作主判统计量；同时必须报告 **cluster（细胞/药对/批次）bootstrap/置换** 的 p 与 MDE，若两者结论不一致 → `ambiguous_conflict`；P0b/P0c 用依赖生成模型校准 type-I/功效并报 ρ/κ 敏感性（§4）。

### 3.2 四类解释与 M_setup 正式模型（v3）

- 候选解释：`E = {M_i, M_ii(J), M_setup}`（(iii) 只 `proxy_only`）。
- **M_setup 概率模型（写死）**：
  `y_i = φ_i^Tθ + u_{tissue(i)} + v_{batch(i)} + ε_i`，`u~N(0,τ_t²)`, `v~N(0,τ_b²)`, `ε_i~N(0,σ_i²·γ²)`；
  - 参数：`θ`（nuisance）、`τ_t,τ_b`（批次/组织）、`γ`（区间/噪声尺度校准；参考值 γ=1）；
  - **共享预测似然**：所有解释用同一观测模型/同一噪声+批次结构，只通过 (a) 是否释放关系约束、(b) 是否估计 γ/τ 来区分；M_i 固定 γ=1, τ_b=0（或参考值），M_setup 估计 γ,τ_t,τ_b。
  - 拟合：REML/贝叶斯后验；留出预测对数似然（K 折按细胞分组，K=5，折内不共享细胞）。
- **惩罚拟合准则（写死）**：`score(E) = −2·loglik_heldout(E) + λ_k · k_E · log(n_eff)`，`λ_k=1` 主（BIC 型），`λ_k∈{0.5,1,2}` 敏感性；`n_eff = n_ctx/(1+(n_ctx−1)ρ̂)`（设计效应，ρ̂ 由参考/留出半估计）；`k_E` = 自由参数个数（M_i < M_setup < M_ii(J)）。
- **δ_fit（写死）**：`δ_fit = 2.0`（AIC 尺度：score 差 ≤2.0 视作不可区分）；若 top-2 的 score 差 ≤δ_fit，或两解释对 U 的 Δ_pred 不同 → `ambiguous_conflict`；不得用"释放集更小"作 tie-break。
- **J 候选族生成（写死）**：对每个越界关系，J 候选 = {单例释放} ∪ {按 `C_conf` 下降的贪心前向释放（最多 5 步）} ∪ {预注册结构族：按 tissue/剂量布局分类的整族释放}；总候选 ≤200；`J_min` = 最小代价可行 J；若多解并列或 60 s 内无认证 → `ambiguous_conflict`；`J_max=min(5,ceil(0.10|R_old|))`。
- **κ 估计（写死，三法）**：(a) nuisance-only 残差（不含关系拟合残差）；(b) 留出参考半 B；(c) 置换零分布。报告 `[κ_lo,κ_hi]`；χ²/σ 分类必须在 κ 带内一致，否则 `ambiguous_conflict`；若 (a) 被关系违反污染（诊断：残差与关系对比相关）→ 以 (b)/(c) 为主并披露。
- **σ 传播**：`σ∈[σ_lo,σ_hi]` 网格；分类在全带一致，否则 ambiguous。

### 3.3 退出上限的 operational 分母（v3）

- 分母 = **eligible S 单元**：S 中满足 Cond_r 且四键（c,p),(c,q),(c',p),(c',q) 在 S/参考中按设计可用的 cell×relation 单元数（由 P0a 输出冻结）。
- 上限来自 **P0b 依赖零分布**：在 M0（iid）与 M1（依赖）两版零生成下各 ≥1,000 次，记录 `exit_rate_not_identifiable`、`exit_rate_ambiguous` 的 95% 分位；
  - 冻结上限 = `max(0.15, P95_notid)` 与 `max(0.10, P95_ambig)`（**只能抬高上限，不能降低**）；
  - 若 P95 超过硬天花板（notid>0.15 或 ambig>0.10）→ 说明设计不可判 → `design_invalid`（不放宽）。
- 运行时若超过冻结上限 → `design_invalid` 停，并报逐单元退出原因。

## 4. P0b/P0c 依赖生成模型（写死）

### 4.1 P0b：独立生成器（iid + 依赖两版；不得注入参考违反结构）

- **独立生成器**：只用 **(a) 参考数据估计的方差/相关性参数**（σ、τ_t、τ_b、ρ）与 (b) 合成类标签生成 y，**不得**把参考中的具体关系违反/方向拷贝进合成数据；两个实现（iid 版：ρ=0,τ=0；依赖版：ρ∈{0.2,0.4,0.6}, κ∈{1,3,10}）由**独立脚本**实现，与 Stage 1 更新器解耦。
- 注入类别：每个单元按预注册规则注入 (i) nuisance-only 偏移、(ii) 关系方向在 ≥12 contexts 中系统性翻转、(setup) γ≠1/τ_b>0；每类 ≥30 单元，效应量 ≥ MDE；
- 通过：每类 recall≥0.80、precision≥0.80；置换零 type-I≤0.10；退出率≤§3.3 上限；**失败 → `design_invalid`**，不得改阈值继续。
- 若两版生成器（iid/依赖）给出矛盾校准（如 iid 通过而依赖不通过）→ 以依赖版为准（更保守），并在报告披露。

### 4.2 P0c：MDE/功效预检（写死）

- 模拟：依赖生成模型（ρ∈{0.0,0.2,0.4,0.6} × κ∈{1,3,10}），每格 **≥1,000 批**；`n_eff = n_ctx/(1+(n_ctx−1)ρ̂)`；
- 目标：在 δ_min 上 **80% 功效 ±0.05**、type-I：点估计 ≤0.05 且 **exact 95% CP 上界 ≤0.10**（若 0/20 类不足，按预注册追加 sims 到 ≥40 或 47 全 0/≤1 的 CP 规则）；
- 报告每格 power/MDE/type-I/CP；**任一格 80% 目标不满足 → `insufficient_precision`** 停（不换聚合/不放宽 α）；
- 本轮不运行 P0c；数值/模拟次数/CP 规则写死，下一轮执行。

## 5. P0a–P0d 流程清单（写死；短路按序）

1. **P0a-metadata 预检（metadata-only）**：细胞分配（reference 84 ⊆ matched 96；A42/B42；S 24/U 17；三元不交；seed 20261027）；**S 侧 Cond_r 覆盖≥12** 逐关系检查；候选网格 229 与 A/B≥12 供给；通过 → 关系构造。
2. **P0a relations_check**：A/B 半分离+交换；n_ctx≥12；α=0.01；primary≤10、BH q≤0.10；**宽度仅 2.0σ_r**；`R_old∈[20,200]`；覆盖 ≥115/229；`|μ|≥0.5σ`；输出 relations.csv/relations_check.json/relation_splits.json + SHA；失败 → `data_unavailable`（可修复则修 Stage 0 资源，不降标准）或 `design_invalid`。
3. **P0b constructive 体检**（依赖+独立生成器）：§4.1；失败 → `design_invalid`。
4. **P0c MDE/功效预检**：§4.2；失败 → `insufficient_precision`。
5. **P0d δ_min/成本/效用**：由任务成本/效用定义 δ_min（未定义 → `blocked_by_utility_definition`）；进行 Stage 1 前的效用宽度检查与预算；P0d 不过 → 不进入 Stage 1（Stage 0 关系表保留）。
- 短路规则：P0a-metadata 不过 → 不跑 P0a relations_check；P0a 不过 → 不跑 P0b/P0c；P0b 不过 → 不跑 P0c；P0d blocked → 只报告 Stage 0，不进入效果轮。
- 所有阶段输出 SHA、无时间戳、确定性；失败类别：`data_unavailable`/`design_invalid`/`insufficient_precision`/`blocked_by_utility_definition`。

## 6. 机制与判类（继承 v2 + v3 修正）

- M1 PRU-CC：区间约束 `l≤Aθ≤u` + 无释放时与投影核的关系仅等式/无激活时成立（v2 修正保留）；对照 (a) 等式投影核 (b) 同区间无释放 constrained ridge (c) soft-penalty (d) 尺寸匹配随机释放 + 全量重训/普通适配/层级/GP。
- M2 DPG：Stage 2 才启动；对照含 VOI/decision-focused（2602.05340、GoBOED 2605.26093、EVSI/ENBS）；无合法区分测量 → 拒绝购买/宣称。
- Stage 1 只判 (i)/(ii)/(setup)；**(iii) 仅 `proxy_only`**（与 A4 协调）。
- 判类仍用四解释惩罚拟合（§3.2），禁止顺序默认/释放廉价=证据/事后 tie-break。

## 7. Stage 0 实现同步清单（task-48 骨架 → v3；下一轮由实现者执行，仍不跑真实数据前须 Lead 批准）

`research/2026-10-27-innovation-scouting/conflict_signal/stage0/relations_check_config.json` 需改为：
- `candidate_enumeration.context_mode`: `"per_tissue"` → `"pooled_across_tissue"`；
- `statistics.interval_utility_check_enabled`: `true` → `false`；`utility.utility_gate_required_for_run`: `true` → `false`（P0a 不依赖 utility；P0d 单独 blocked）；
- `global_acceptance.coverage_denominator`: `null` → `229`（→ 目标 115）；
- `cell_allocation`: reference 84 ⊆ matched 96（需代码新增 matched-cell 限制与 S 侧 Cond_r 覆盖预检）、S24/U17；
- 新增 **P0a-metadata 预检步骤**（S 侧 Cond_r 覆盖≥12）与 **P0b/P0c** 独立脚本接口；
- 删除/废弃 64/16 配置（统一 84/24/17）。
以上为下一轮实现任务；本轮不修改 Stage 0 代码（避免半同步状态），不改 A1 v1/v2。

## 8. 措辞模板（写死）

- 判类："operational 归因：（i)/(ii)/(setup)，context=跨 tissue 池化"（不是生成原因）。
- 主族是**跨 tissue 平均**；不写"每个 tissue 成立"；Breast/Colon 只作敏感性披露。
- `not_identifiable`/`insufficient_precision`/`proxy_only`/`completed_null` 不写成阴性/不存在。
- 不写新颖算法/机制/迁移/决策收益；P2 只写"该参考/反馈/菜单/预算/context 下的更新比较"。
- 条件级 1.43% 只是加性主效应份额（C174）；A1v2/C176/C177 作废状态不复活。
- 与 A4/A5 接口保留：A4 决定 (iii) 能否升级；A5 成本/菜单接口在 A5 修订通过后才可用于 Stage 2。
