# PROTOCOL_Q2（R194-A2：Q 的条件级结构可估性）——v1 **FROZEN**（2026-10-27，任何 Q2 效果估计之前）

> 依据：R194 BRIEF、R193-A1 `inconclusive`（C171；[q1.json](q1.json)、[report_q1.md](report_q1.md)、[PROTOCOL_Q.md](PROTOCOL_Q.md)）、A0（`matching_qualified`）+ [ERRATA_A0.md](ERRATA_A0.md) + [challenge_A0.md](challenge_A0.md)、R193 记录。**本文件在跑 `q2.py` 之前冻结；冻结后不改，偏离写 AMENDMENT 并在报告中披露。**
>
> **这是与 A1 不同的信息对象问题，不是 A1 换聚合复活**：A1 问"Q 能否跨 screen 复验"（cell-pair 级设计，判定 inconclusive 因为 96 细胞→n_eff≈189）；A2 问"**Q 是否存在可估的 condition-pair 级结构，而非被 cell-pair 交互/测量噪声淹没**"（condition-pair × cell-pair 的交叉随机效应设计）。**A2 不把 A1 判为通过，不做跨 screen 复验**（Validation 只作探索性样本外条件级一致性，不参与主判定），**不启动 B/C/acquisition**，不换端点/分层/δ，不按 Q 大小挑层，不用 Q 结果反推模型选择。

## 0. 问题与假设

- Q 定义（与 R193 一致）：`Q = (y[c,p] − y[c,q]) − (y[c',p] − y[c',q])`；主分层 **controlled_anchor**（同 `anchor_id`、同 `ANCHOR_CONC`、同 `LIBRARY_CONC`，仅 library 不同）；端点主 `SYNERGY_DELTA_EMAX`；原始重复板按 **barcode 均值** 聚合；条件为**有向** `(ANCHOR_ID→LIBRARY_ID, ANCHOR_CONC, LIBRARY_CONC)`，condition-pair (p,q) 按 **library_id 升序**定向（Q 符号一致）。
- **H194a（主）**：交叉随机效应 `Q_ij = μ + a_i(condition-pair) + b_j(cell-pair) + c_ij(交互) + ε_ij(测量噪声)` 中，**condition-pair 方差分量 σ²_cond > 0 且条件级 Q 的可靠性 ≥ 0.50（预注册阈值）**。
- **H194b（诊断）**：报告 σ²_cond 与 σ²_cellpair 的相对份额；若 condition 级份额可忽略（**<10%**），记录"条件结构主要是细胞特异的"边界含义（B/R194 BRIEF）。
- 宇宙：**Original screen 为主**（barcode 重复提供噪声标定）；Validation 只作探索性交叉检查。
- 明确不做：不把本分析当作 A1 通过/不通过；不做跨 screen 复验；不启动 B/C/acquisition；不换端点/分层/δ；不按 Q 大小挑层/挑 condition-pair；不用 Q 结果反推模型或阈值。

## 1. 数据、单元与边界处理（冻结）

- 输入：Jaaks Original/Validation fitted 表（SHA 见 A0 report：Original `1188968C…`、Validation `DCBD4C31…`）、A0 `matched_conditions.csv`（`73FD5085…`，9,154 键）、`a0.json`（`72BBAF6D…`）、[PROTOCOL_A0.md](PROTOCOL_A0.md)、[PROTOCOL_Q.md](PROTOCOL_Q.md)、[q1.json](q1.json)、[ERRATA_A0.md](ERRATA_A0.md)、[challenge_A0.md](challenge_A0.md)、R194 BRIEF。
- 有效行 = A0 规则（非 composite、细胞归一名、端点有值、ID/剂量存在）；按 (screen, cell, condition) 做 barcode 均值聚合。
- 观测单元 = **(condition-pair i, cell-pair j) 唯一格**（每个主分层四元组恰好对应一格；A2 probe 验证 `unique 92,039 / 92,039`）。
- 结构（A2 结构 probe，仅元数据）：**229 个 realized condition-pair**（universe 230）；**1,501 个 cell-pair**；**92,039 个观测**；每 condition-pair 的 cell-pair 数 78–595（中位 435）；每 cell-pair 的 condition-pair 数 6–134（中位 58）；二部图 3 个连通分量（sizes 134/58/37）。
- 边界：缺失格 = 缺失（**不插补、不按 Q 选层**）；同一格无重复观测；Q 用双差，cell/condition 加性主效应精确消去；不剔除极端 Q（全量入分析；极端值影响由 bootstrap/敏感性报告）。
- **跨 screen**：Validation 只算"条件级均值"的探索性一致性；不进入 H194a/H194b 判定。

## 2. 方差分量：冻结的矩估计（ANOVA 型）

对观测单元的 `Q_ij`：

- 全局均值 `μ̂`（无权重=全体观测均值）。
- **σ²_cond**：同 condition-pair、不同 cell-pair 的观测对的协方差（共享 a_i，其余分量独立）
  `σ̂²_cond = Σ_i Σ_{j<j'∈obs(i)} (Q_ij−μ̂)(Q_ij'−μ̂) / Σ_i C(n_i,2)`，用 `Σ_{j<j'} x_j x_{j'} = ½[(Σx)²−Σx²]` 计算。
- **σ²_cellpair**：对称地按 cell-pair 聚合。
- **σ̂²_total**：`Σ (Q_ij−μ̂)² / (N−1)`（无偏样本方差）。
- **σ̂²_resid = σ̂²_total − σ̂²_cond − σ̂²_cellpair**（= 交互 + 测量噪声；可负，保留原值并报告截断值）。
- **噪声标定（σ²_single）**：仅用 Original 内**四个 key 都有 ≥2 barcode** 的四元组；每键按 barcode 排序分半（first ⌈b/2⌉ vs rest），
  `diff = Q_half1 − Q_half2`，`denom = Σ_{4 keys}(1/b_h1 + 1/b_h2)`，
  `σ̂²_single = Σ diff² / Σ denom`（矩估计；单 barcode 键的单药读数误差方差）。
  每观测的噪声方差 `σ²_noise,ij = σ̂²_single · Σ_{4 keys} 1/b_k`；`σ²_noise_avg` = 全部观测的均值。
- **交互**：`σ̂²_int = max(0, σ̂²_resid − σ²_noise_avg)`（原值同时报告）。
- **份额**：`share_cond = σ̂²_cond/σ̂²_total`，`share_cell = σ̂²_cellpair/σ̂²_total`，`share_int = σ̂²_int/σ̂²_total`，`share_noise = σ²_noise_avg/σ̂²_total`（截断后口径；未截断口径同报）。
- 负估计处理：σ̂²_cond、σ̂²_cellpair 保留原值；份额按 `max(σ̂²,0)/σ̂²_total` 报告并注明；判定用原值（不因截断改变显著性）。

## 3. 条件级 Q 与可靠性（公式先冻结）

- 条件级 Q：`Q̄_i = mean_{j ∈ obs(i)} Q_ij`（每个 condition-pair 的 cell-pair 均值；全部 229 个都 ≥78 个 cp）。
- **条件级 Q 可靠性（主定义）**：
  `rel_i = σ̂²_cond / (σ̂²_cond + σ²_est,i)`，其中 `σ²_est,i = (σ̂²_int + σ²_noise_avg) / n_i`（n_i = 该 condition-pair 的 cell-pair 数；barcode 数已进入 σ²_noise_avg）。
  **headline reliability** = 在 **median(n_i)** 处的 `rel`（本数据 median n_i = 435），阈值 **≥ 0.50**（BRIEF 建议值，先冻结）。
- 另报（只作敏感性，不替换主定义）：`rel_noise_only = σ²_cond/(σ²_cond + σ²_noise_avg/n_i)`；`rel_with_cellpair_sampling = σ²_cond/(σ²_cond + (σ̂²_cellpair + σ̂²_int + σ²_noise_avg)/n_i)`；每个 condition-pair 的 rel_i 分布。
- 说明（写死）：由于每个 condition-pair 有 ~435 个 cell-pair，`rel` 对 σ²_cond 的**显著性**不敏感；它衡量的是"条件级均值相对（交互+测量噪声）的稳定性"，不是"σ²_cond 占 Q 总方差的比例"——后者由 share/H194b 报告。

## 4. 推断：聚类 bootstrap 与置换零分布（冻结）

- **双向 cluster bootstrap（主 CI）**：每个 replicate 分别有放回重采样 229 个 condition-pair **和** 1,501 个 cell-pair；观测权重 `w_ij = m_i × m_j`；用 §2 的加权矩估计重算 σ²_cond、σ²_cellpair、share、rel。`B = 1000`，seed `20261028`。CI = 2.5/97.5 百分位。
- **置换零分布**：
  - **(i) condition-pair 标签打乱**（保持 cell-pair 结构）：把 92,039 个观测的 condition-pair 标签整体随机置换，重算 σ̂²_cond；`B = 1000`，seed `20261029`；报告 95 分位与 p = (1+#{null ≥ obs})/(B+1)。
  - **(ii) cell-pair 标签打乱**：对称，seed `20261030`；用于 σ̂²_cellpair 的零分布。
- 判定不使用参数正态近似，用 (i) 的置换零分布 95 分位 + 双向 bootstrap CI。

## 5. 设计体检（**先于任何 H194a 判定**；任一不过 → `inconclusive` 停，不救）

- **D1 结构**：N=92,039 ≥ 10,000；cell-pair 1,501 ≥ 200；realized condition-pair 229 ≥ 50；每 condition-pair n_i ≥ 10；每 cell-pair m_j ≥ 5；`unique(i,j)=N`。
- **D2 噪声覆盖率与稳定性**：barcode 标定四元组 ≥ **300**（all-4-keys-≥2-barcode）；σ̂²_single 有限且 >0；**分半稳定性**：把标定四元组按 (condition-pair id 奇偶) 与 (cell-pair id 奇偶) 各分两半，四个 half 估计两两比值落在 **[0.5, 2]**（每个 half ≥100 四元组）；噪声份额 `share_noise` 有限。
- **D3 可辨识性**：σ̂²_cond、σ̂²_cellpair 有限；**pilot 双向 bootstrap（B=200）** 中 SE 有限比例 ≥95%；condition-pair 数 ≥50；二部图连通分量 ≤5（结构已报告）。
- **D4 功效/type-I（先于效果判定）**：在**观测到的 (i,j) 格型**上模拟
  `Q_ij = a_i + b_j + e_ij`，`σ²_total=1`，`σ²_cond = s²`（s∈{0.2,0.4}），`σ²_cellpair = 0.4(1−s²)`、`σ²_resid = 0.6(1−s²)`（冻结的备择分割；另报分割敏感性）；检验 = 双向 bootstrap（B=100）z 统计量 `σ̂²_cond/SE > 1.645`（单侧 5%）；`N_SIM=200`，固定 seed `20261031`；
  要求 **power(s=0.4) ≥ 0.80**，**type-I（s=0）≤ 0.10**。
- 另报：power(s=0.2)、备择分割 ρR∈{0.2,0.6} 的敏感性。

## 6. 判定规则（冻结）

- **`condition_structure_present`**：设计体检通过 **且** σ̂²_cond > 0 **且** 双向 bootstrap 95% CI 下界 > 0 **且** σ̂²_cond > 置换零分布 95 分位 **且** `rel(median n_i) ≥ 0.50`。
- **`condition_structure_absent`**：设计体检通过但 present 的条件不成立。措辞（写死）：**"在本资源/本分层/本标定精度上，condition-pair 方差分量不可估或可忽略；这是'不可估/可忽略'的证据，不是'条件级结构普遍不存在'，也不构成 A1 的通过/不通过。"** 若同时 `share_cond < 10%` → 记"H194b：条件级份额可忽略，条件结构主要是细胞特异的"。
- **`inconclusive`**：设计体检（D1–D4）任一不过 → 停，不进行 H194a 判定；记录设计边界与后续解冻条件。
- 分支（写死）：absent → 条件结构线停止（不启动 B/C/Agent；接受"现有资源只能支持静态/平均效应"的边界）；present → 下一轮只在**更大独立资源**上做条件级跨 screen 复验的资格审计（**不是**用同一 96 细胞再换聚合）；inconclusive → 记录设计边界。

## 7. 探索性 Validation 交叉检查（不参与主判定）

- 用 Validation 的同 92,039 个匹配四元组计算 `Q^B_ij` 与条件级均值 `Q̄_i^B`；
- 报告 `Spearman(Q̄_i^A, Q̄_i^B)` 跨 229 个 condition-pair + 按 condition-pair 聚类的 bootstrap CI；
- 报告 Validation 的 σ̂²_cond^B / share 作探索性对照；
- 措辞：**仅探索性样本外一致性，不进入 H194a/H194b 判定，不构成跨 screen 复验**。

## 8. 实现、确定性与交付

- `q2.py` 顺序：加载/断言输入 SHA → 结构 → **设计体检 D1–D4** → 若通过 → 主估计（方差分量/份额/可靠性/零分布）→ Validation 探索 → 输出。**设计体检未过禁止进入 H194a 判定**；写盘前断言 `main_effects_computed=False`。
- 确定性：固定种子（§4/§5）、JSON 键排序、无时间戳、输入/脚本 SHA256；单命令 ≤45 min。
- 交付（`research/2026-10-27-conditional-shift/`，只新增）：`PROTOCOL_Q2.md`、`q2.py`、`q2.json`、`q2_rows.csv`（每 condition-pair 一行：n_cp、Q̄_i、rel_i、份额等）、`report_q2.md`、`record_q2.md`、`usage_q2.json`。
- 不晋升代码；阴性/不可估同样完整记录。

## 9. 明确不做 / 边界

- 不是 A1 复活或换聚合；不做跨 screen 复验；不启动反馈/Agent/元学习/RSI；不做机制/临床主张；不换端点/分层/δ（本分析无 δ_min；可靠性阈值 0.50 已冻结）；不按 Q 大小挑层或挑 condition-pair。
- 条件偏移 ≠ 机制；condition 级结构 ≠ 可迁移；本分析只描述"在 matched 子集与该端点/标定精度上条件级方差是否可估"。
