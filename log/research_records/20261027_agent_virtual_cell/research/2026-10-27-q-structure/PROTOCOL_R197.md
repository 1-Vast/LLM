# PROTOCOL_R197 —— Q 结构可预测性重审（v1 **FROZEN**，2026-10-27，任何 R197 效果/推断统计之前）

> 依据：R197 BRIEF（`research/2026-10-27-innovation-round-r197/BRIEF.md`）、独立重审（`research/2026-10-27-cross-domain-directions/{report.md, late_results_audit.md}`）、ERRATA_Q2/ERRATA_A3（`research/2026-10-27-conditional-shift/`）、PROTOCOL_Q2 与 q2.py/q2.json、A1/A2 记录（`report_q1.md`, `report_q2.md`, `record_q2.md`）。
>
> **本文件在运行任何 R197 推断/预测统计之前冻结；冻结后不改。** 任何实现选择/偏离在 `report_r197.md §偏离` 与 `record_r197.md` 披露。
>
> **边界（写死）**：R197 **不是** A1/A2 的通过或复活，不做跨 screen 复验，不启动反馈/Agent/acquisition/元学习/RSI，不把旧 1.43% 当"可迁移规律总量"，也不把 Q2 的 `condition_structure_present` 或可靠性 0.868 当作已认证结论（重校准见 A0）。条件偏移 ≠ 机制；条件级结构 ≠ 可迁移。

## 0. 数据与重建（冻结）

- **Q 数据**：由 A2/q2 的同一输入重建：Jaaks Original fitted（`1188968C…`）、`matched_conditions.csv`（`73FD5085…`）；A0 有效行规则、barcode 均值聚合、`controlled_anchor` 主分层、condition-pair 按 library_id 升序定向、端点 `SYNERGY_DELTA_EMAX`。**不重读 Validation**（R197 不用 Validation）。
- 结构断言（必须与 q2.json 一致，否则 `inconclusive` 停）：`n_obs=92,039`、`n_condition_pairs=229`、`n_cell_pairs=1,501`、`n_cells=96`、`n_conditions=291`、`n_matched_keys=9,154`、`unique(i,j)=92,039`；每 condition-pair 的 cell-pair 数 78–595（中位 435），每 cell-pair 的 condition-pair 数 6–134（中位 58）。
- 观测矩阵 `Q ∈ R^{229×1501}`，缺失=缺失（不插补、不按 Q 值挑层、不剔除极端值）；观测掩码 `M`。
- 辅助结构：cell-pair 列 j ↔ 两个细胞（规范化名）；condition-pair 行 i ↔ 两条条件（anchor_id, library_id, anchor_conc, library_conc）；barcode 计数（来自 Original）用于噪声标定复核。
- 输入 SHA256：Original `1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278`、matched_conditions `73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF`、q2.json `…`（完整记录于 r197.json）；脚本 SHA256 写入 r197.json。

## 1. 种子与确定性（冻结）

| 用途 | seed |
|---|---|
| A0 修正式对照（legacy 双向 cluster） | 20261103 |
| A0 依赖感知 bootstrap（cell/condition/node） | 20261102 |
| A0 graph-aware 置换零分布 | 20261104 |
| A0 分半可靠性（cell 分半） | 20261105 |
| B0/A0 无随机（确定性拟合） | — |
| B 外层折分配 | 20261106 |
| B 聚类 bootstrap CI | 20261107 |
| B 置换零分布 | 20261108 |
| B 内层 CV / 秩选择 / λ 选择 | 20261109 |
| B 完整规则 type-I 模拟 | 20261110 |
| B4 随机森林/GBM | 20261111 |
| 主随机流（若需） | 20261101 |

- JSON 键排序、无时间戳、`allow_nan=False`；固定 `PYTHONHASHSEED=0`（集合/字典迭代顺序不得影响结果）；连续两次运行 `r197.json` 与 `r197_rows.csv` 逐字节相同（验收）。

## 2. A0：Q2 推断重校准（必做；先于 B）

### 2.1 修正式加权矩估计（冻结代数）

对观测单元 `(i,j)` 给权重 `w_ij`。记组 `g`（condition-pair 行 i 或 cell-pair 列 j）内：
`W_g=Σw`、`S_g=Σwy`、`S2_g=Σw²y`、`T2_g=Σw²y²`、`W2_g=Σw²`；全局 `μ=Σwy/Σw`。
组内**不同观测对**的加权残差积和：
`A_g = ½(S_g² − T2_g)`；`B_g = W_g·S_g − S2_g`；`C_g = ½(W_g² − W2_g)`；
`num_g = A_g − μ·B_g + μ²·C_g`；`den_g = C_g`。
- `σ²_cond = Σ_i num_i / Σ_i den_i`；`σ²_cellpair` 对称（按列）；`σ²_total = Σ w(y−μ)²/(Σw−1)`；`σ²_resid = σ²_total − σ²_cond − σ²_cellpair`。
- **旧式（q2.py）公式**（仅对照，不改点估计）：`num_g^legacy = ½[(S_g−μW_g)² − (Σw y² − 2μS_g + μ²W2_g)]`，其余同上。
- **自检（冻结，必须通过）**：(i) ERRATA_Q2 例：`y=(1,3), w=(2,1), μ=5/3` → 正确不同原始观测对加权残差积 `−8/9`；旧式 `−37/18`。(ii) `w≡1` 时修正式与旧式**代数恒等**；用原 Q 数据计算 `w≡1` 点估计必须与 q2.json 一致（`σ²_cond=0.000371`、`σ²_cellpair=0.001023`、`σ²_total=0.025944`、`σ²_resid=0.024551`；容差 1e-6）。

### 2.2 dyadic 对比方差原型测试（冻结，必须复现）

n∈{4,10,30} 个细胞、全部词典定向对比 `Q_ab=z_a−z_b`（a<b），`z_c` 独立同方差 σ²=1：
- 系数 `c_i=(n−1−2i)/C(n,2)`（i=0..n−1），真实均值方差 `Σc_i²`，闭式 `4(n+1)/(3n(n−1))`；
- 独立边近似 `2/C(n,2)`；
- 要求：n=30 时真实/近似 = **10.33 ± 0.01**（复现 ERRATA 的 10.33×），且 2,000 次蒙特卡洛（seed 20261102）与闭式差 ≤3 个 MC-SE；n=4/10 同法报告。
- 同时纳入 `Q=[[1,−1],[−1,1]]` 秩 1 反例：行/列加性均值均为 0 但结构完全共享 → 用于报告 §A0-1.43% 读法的**数学反例**（不用于本数据估计）。

### 2.3 依赖感知推断（冻结）

对 `σ²_cond, σ²_cellpair, share_cond, σ²_resid, ρ_cond`（定义见 2.5）计算 `B=1,000` 次 bootstrap 的 2.5/97.5 百分位 CI：

- **V1 legacy 双向 cluster**（q2 口径的修正代数版）：重采样 229 condition-pair 与 1,501 cell-pair，`w_ij=m_i·m_j`。
- **V2 cell-node**：重采样 **96 个细胞**（有放回）；cell-pair j=(a,b) 权重 `w=m_a·m_b`（共享细胞结构被保留）；行不重采样。
- **V3 condition-node**：重采样 **291 条条件**（有放回）；condition-pair i=(p,q) 权重 `w=m_p·m_q`；列不重采样。
- **V4 cell+condition node（主）**：`w_ij = m_p·m_q·m_a·m_b`。
- 每个 replicate 用 §2.1 修正式重算全部统计量。主口径 = **V4**；V1–V3 全部报告。权重和为 0 / 分母≤0 的 replicate 记 NaN 并报告有限比例（<95% → A0 `inconclusive`）。

**graph-aware 置换零分布（冻结）**：
- σ²_cond 的零分布：对每个 cell-pair 列 j，把该列观测值在其**已观测行集合内**随机置换（保持稀疏型与列值多重集，破坏 condition-pair 对齐）；B=1,000（seed 20261104）；报告 null mean/sd/q95/p=(1+#{null≥obs})/(B+1)。
- σ²_cellpair 的零分布：对每个 condition-pair 行 i，在**已观测列集合内**置换该行观测值；B=1,000。
- 说明：逐观测打乱 condition-pair 标签（q2 做法）破坏布局/缺失/共享键结构，**不作为 R197 的零分布**；仅作对照记录。

### 2.4 条件级可靠性重校准（冻结）

噪声沿用 q2 口径重算并核对：只用 Original 内四键都有 ≥2 barcode 的四元组、每键 barcode 排序 first ⌈b/2⌉ vs rest 分半，`σ²_single = Σdiff²/ΣΣ_k(1/b_h1+1/b_h2)`，每观测 `σ²_noise,ij=σ²_single·Σ_k 1/b_k`，`σ²_noise_avg` 为均值；`σ²_int=max(0, σ²_resid−σ²_noise_avg)`。要求与 q2.json 一致（σ²_single=0.003351、noise_avg=0.011968；容差 1e-6）。

- **R_old**（q2 主定义，重算核对）：`σ²_cond/(σ²_cond+(σ²_int+σ²_noise_avg)/n_i)` 在 median `n_i=435` 处。
- **R_formula_dep**（依赖感知解析式）：`rel_i = σ²_cond/(σ²_cond + V_i)`，其中 `V_i` = 在 **V2 cell-node bootstrap** 下该 condition-pair 加权均值 `Q̄_i` 的跨 replicate 方差（对每个 i 计算，取 `V̄=mean_i V_i`）；headline 用 `median_i` 处的 rel 与 `mean` 两口径同报。CI：对 V2 bootstrap 的每个 replicate 重算 rel（分母用同 replicate 的 V̄），取百分位。
- **R_split**（经验分半可靠性，**认证主用**）：把 96 个细胞随机分为两半（每半 ≥40 细胞；seed 20261105；重复 20 个随机分半，`cell-split` 无细胞跨半）；对每个分半，仅在**两细胞都在同一半**的 cell-pair 上计算 `Q̄_i^half`（要求每半该 condition-pair ≥10 cell-pair，否则该 i 在该 split 不参与）；跨 condition-pair 计算两半均值的 Spearman `r`，Spearman–Brown `rel=2r/(1+r)`。报告 20 次 split 的 median、min、max、2.5/97.5 百分位。**R_split median ≥0.50 视为条件级可靠性认证成立**（沿用 q2 冻结阈值 0.50）。
- **A0 重校准状态（冻结）**：
  - `q2_inference_robust`：V4 的 σ²_cond CI 下界 > 0 **且** R_split median ≥ 0.50 **且** 置换 p<0.05；
  - `q2_inference_not_robust_under_dependence`：V4 CI 下界 ≤0 **或** R_split median < 0.50 **或** 置换 p≥0.05；
  - `q2_recalibration_inconclusive`：自检/结构/有限比例失败。
- **报告纪律（写死）**：`share_cond` 仅命名为 **"加性 condition 主效应份额"**；**不得**写成"可迁移规律只有 1.43%"或"不应以条件级共享规律为前提"（秩 1 反例见 §2.2）；`σ²_int/σ²_noise` 分割是该误差模型下的分割，不是已测生物机制比例。

## 3. B：Q 结构留出预测（主实验）

### 3.1 数据与目标

- 同一 Q 矩阵（229×1501，92,039 观测条目）。**不引入新数据**；不读 Validation；特征来自已授权元数据/单药列（见 3.2）。
- 目标：预测**留出**观测条目的 Q；主对比 `Δ = Spearman(主模型) − Spearman(B0)`；另报 B1/B4 与全部模型。

### 3.2 预注册特征（只用元数据与同 screen 单药列）

- 细胞元数据：`Tissue`（Breast/Colon/Pancreas）两细胞 one-hot（3+3）、`same_tissue`（1）。
- 单药列（Jaaks 同 screen 单药拟合，非 Q）：对 library id l、细胞 c 取 `mono_emax(c,l)=mean(LIBRARY_EMAX)`、`mono_auc(c,l)=mean(LIBRARY_AUC)`（按行聚合；缺失用**同 library 在 96 个匹配细胞上的中位数**填补并记录缺失率）。特征：`dA_emax=mono_emax(a,p)−mono_emax(a,q)`、`dB_emax`（同 b）、`d_emax=dA_emax−dB_emax`，AUC 同构 3 个（共 6）。**不使用任何组合 Q 响应**。
- condition-pair 元数据：`ANCHOR_PATHWAY` one-hot（该 condition-pair 的 anchor 通路）、`ANCHOR_DRUG_TYPE`（targeted=1）、library p/q 的 `LIBRARY_PATHWAY` one-hot、`LIBRARY_DRUG_TYPE` 两个 0/1、`same_library_pathway`、`anchor_conc`、`library_conc`（numeric）。
- **B1 特征矩阵** = 上三块拼接（约 78 维）。
- **B3 特征矩阵** = B1 + 交互块：细胞侧 `C=[tissue a one-hot(3), tissue b one-hot(3), same_tissue, dA_emax, dB_emax, d_emax, dA_auc, dB_auc, d_auc]`（13）× 条件侧 `G=[library_p_type, library_q_type, same_library_pathway, ANCHOR_PATHWAY one-hot(≤17)]`（≤20）的逐对乘积（≤260 维）。**交互块只用元数据/单药列**。
- 标准化只用训练条目（均值/方差），测试条目只 transform；特征在拟合前一次构建。

### 3.3 预注册模型（全部冻结；测试集不调参）

- **B0 加性**：`Q_ij ≈ μ + a_i + b_j`，在训练条目上用交替均值中心化拟合（tol 1e-9, ≤200 迭代）；未见到的行/列效应置 0（中心化后）。
- **B1 元数据/单药线性**：岭回归（截距）于 B1 特征；λ 从固定网格 `{0.1, 1, 10, 100, 1000}` 用**训练条目内** 5 折内层 CV（seed 20261109）选 MSE 最小者。
- **B2 低秩**：`Q_ij ≈ μ + a_i + b_j + (U V^T)_ij`，rank `r∈{1,2,3,5}`；ALS（λ_lr=0.1 固定，25 次迭代，缺失只进观测掩码损失，初始化固定 seed）；r 用**训练条目内**内层 CV（1 个 80/20 内层划分，seed 20261109）按 MSE 选择，随后在外层训练条目上重拟合；未见到的行/列因子与主效应置 0。**注意（已预注册）**：在 H197a（留出 cell-pair 的细胞全部不在训练集）下，留出列的 `V_j` 不可辨识 → B2 预测退化到 B0；该退化由代码断言与报告确认，H197a 主模型因此取 **B3**（B2 仍报告）。
- **B3 层级/交互**：岭回归（截距）于 B3 特征；λ 网格/内层 CV 同 B1。
- **B4 容量对照**：`HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=20, l2_regularization=1.0, random_state=20261111)`，输入 = B3 特征 + B0 的 OOF/训练拟合预测作为一列；**不做超参搜索**（容量对照）。
- 所有模型只在训练条目上拟合；**测试条目/测试标签不参与 λ、r、早停或任何选择**。

### 3.4 预注册留出设计（5 折外层；折分配 seed 20261106）

- **H197a（主）留出 cell-pair（按细胞分组防同细胞跨折）**：96 细胞按规范化名排序，`fold=index%5`（19/19/19/19/20 细胞）。对折 f：**测试条目** = 观测条目中其 cell-pair 的两细胞均在折 f；**训练条目** = 观测条目中两细胞均**不在**折 f（跨折细胞对既不入训练也不入测试，计数并报告）。→ 测试细胞的任何键均不出现在训练，无细胞泄漏。
- **H197b（次）留出 condition-pair**：229 行按 `(anchor_id, library_p, library_q)` 排序后 `fold=index%5`（46/46/46/46/45）。测试 = 该折行的全部条目；训练 = 其余行。
- **H197c（次）随机留出条目**：92,039 个观测条目按 `(row, col)` 排序后 `fold=index%5`；测试 = 该折条目；训练 = 其余。
- 每折收集所有模型对测试条目的预测（OOF 汇总）。

### 3.5 指标、主对比与推断（冻结）

- 模型指标：**OOF Spearman**（汇合全部测试条目：`pred` vs 观测 `Q`）、每折 Spearman（5 个）与 **OOF R²**（`1−SSE/Σ(y−ȳ_test)²`）。
- **主对比**：H197a `Δ=B3−B0`；H197b `Δ=B2−B0`；H197c `Δ=B2−B0`（预注册；其他模型−B0 全部报告）。
- **CI**：聚类 bootstrap（B=1,000，seed 20261107）：H197a 重采样 **细胞**、H197b 重采样 **condition-pair 行**、H197c 重采样**细胞与行**；把对应单元多重性>0 的 OOF 条目按多重性复制后重算 Spearman 与 Δ；取 2.5/97.5 百分位。
- **MDE80**：`MDE80 = 2.802·SD_boot(Δ)`（双侧 α=0.05、80% 功效；与 R190-A0/R196 同口径）。**设计门槛：MDE80 ≤ δ_min=0.05**。
- **置换零分布**：保持测试条目集合与预测不变，随机置换测试条目的观测 Q（B=1,000，seed 20261108）；`Δ_null=Spearman(pred_primary,y_perm)−Spearman(pred_B0,y_perm)`；报告 null mean/sd/q95/q5、单侧 p=(1+#{Δ_null≥Δ_obs})/(B+1)。
- **完整规则 type-I 模拟**（设计门槛 ≤0.10）：把 92,039 个观测 Q 值整体随机置换生成零数据（每 sim 一个 seed=20261110+sim），**完整重跑**该设计的冻结规则（5 折、B0/B1/B2/B3/B4 按正确设置重拟合、内层选择、聚类 CI B=200、Δ/δ_min/容量对照/置换 p 全规则）统计"判 present"的比例。模拟次数：H197a **20**、H197b **10**、H197c **10**（B2 秩选择为成本限制；报告精确二项 95% 上界与有限精度，不隐瞒）。
- **δ_min=0.05（冻结 operational 理由）**：Q 的 OOF 噪声标度 `sqrt(mean σ²_noise,ij)≈0.109`；0.05 Spearman 增量对应可解释秩方差 <0.3%（数量级），低于此值的"结构增量"不足以支持后续"固定反馈比较更新器/选药"实验的决策价值；且与 A1 的 δ_min_latent=0.10 在观测层折半一致。此值**不据 R197 结果调整**。

### 3.6 B 设计体检（任一项失败 → `inconclusive` 停，不做"present/absent"判定）

- **B-D1 覆盖**：每设计汇合测试条目 ≥10,000 且每折 ≥1,000；各模型 OOF 预测有限比例 ≥99%。
- **B-D2 无泄漏**：H197a 每折测试细胞 ∩ 训练细胞 = ∅（断言）；H197b 每折测试行 ∩ 训练行 = ∅；H197c 同；内层选择只用训练条目（断言/代码路径）。
- **B-D3 零分布校准**：三个设计的置换零分布均值 |mean|≤0.02、SD 有限；完整规则 type-I（3.5）≤0.10。
- **B-D4 检定力**：H197a 主对比 MDE80 ≤0.05（δ_min）；H197b/H197c 各自主对比 MDE80 记录（若 >δ_min 记为次级不可分辨，不影响主判定）。
- **B-D5 退化披露**：H197a 下 B2 的留出列因子范数应为 0（与 B0 预测全等的比例报告）；不作为失败，但 H197a 主模型固定为 B3。
- **B-D6 输入/确定性**：SHA 断言、双跑一致。

### 3.7 判定规则（冻结）

- **`predictive_structure_present`**：B 设计体检全部通过 **且** 各设计的主对比（见 AMENDMENT-R197-001）`Δ` 点估计 **≥0.05** **且** 其 95% CI 下界 **>0** **且** 置换单侧 p<0.05 **且** 主模型的 held-out Spearman **≥ Spearman(B1)** 且 **≥ Spearman(B4)**（容量对照不劣于主模型；两项均需满足）。
- **`no_stable_increment`**：体检通过但 present 条件不成立 → **停止该资源上的"条件规律"研究**（按 BRIEF）；次级 H197b/c 结果只作描述，**不得**用来把主判定换切分复活；若次级出现增量，记录为"仅条件行/随机条目切分有增量、冷细胞对无 → 不可迁移到新细胞"。
- **`inconclusive`**：任一体检失败（MDE>δ_min、type-I>0.10、覆盖/泄漏/零分布/确定性失败）→ 停，记录设计边界与解冻条件。
- 输出措辞：不得写"Q 没有结构/条件规律不存在"；只能写"在本资源/本端点/本标定与预注册规则下，留出**冷细胞对**上未检出可复用增量"等限定语句。

## 4. 交付、确定性与纪律

- 交付（`research/2026-10-27-q-structure/` 新建）：本协议、`r197.py`、`r197.json`、`r197_rows.csv`、`report_r197.md`、`record_r197.md`、`usage_r197.json`。
- `r197_rows.csv`：每 condition-pair 一行（id、anchor_id、library_p/q、concs、n_cell_pairs、q_mean、q_sd、`reliability_old_formula`、`reliability_dep_formula`、`reliability_split_half`、B 相关留出预测均值/残差概要）。
- `r197.json`：inputs/script/环境 SHA、结构断言、A0 全表（修正式 vs 旧式、V1–V4、置换、dyadic 原型、可靠性旧/新、状态）、B 设计体检、各设计×模型指标、Δ+CI、MDE、零分布、type-I、判定、偏离、边界声明。
- 只写本目录与 `tmp/`；不改 A0/A1/A2/A3/Q1/Q2 产物、其它目录、INDEX、git。
- 单条命令 ≤20 min；CPU-only；不联网；不晋升代码；阴性完整记录。

## 5. 明确不做

- 不把 R197 写成 A1/A2 通过、不写跨 screen 复验、不启动反馈/Agent/RSI/acquisition、不做机制/临床主张、不按 Q 值挑层或挑 condition-pair、不换端点/分层/δ、不用测试集调参、不因结果调整门槛。
- 不把 `share_cond=1.43%` 解释为可迁移规律总量；不把本轮任何阴性读成"结构不存在"。

## AMENDMENT-R197-001（2026-10-27 18:0x，**任何 R197 推断/留出预测运行之前**；结构可辨识性触发）

- **事由**：Q 矩阵的行/列是 condition-pair / cell-pair。若某个留出设计的**整行或整列**在训练集中完全无观测（H197a 留出 cell-pair 列：其两细胞均不入训练；H197b 留出 condition-pair 行：整行不入训练），则 B2 低秩模型中该行/列的主效应与潜因子**不可辨识**（训练损失不含其任何观测），其预测在代数上**退化为 B0 的预测**（未见到效应置 0 后二者相同）。此时以 B2−B0 作主对比将结构性得到 0，不能检验"结构是否可预测"。
- **修订（仅主对比模型标签；门槛/δ/规则不变）**：主对比按设计取**可辨识的预注册结构化模型**：
  - **H197a（主，留出 cell-pair 冷细胞）**：`Δ = Spearman(B3) − Spearman(B0)`；
  - **H197b（次，留出 condition-pair）**：`Δ = Spearman(B3) − Spearman(B0)`；
  - **H197c（次，随机留出条目）**：`Δ = Spearman(B2) − Spearman(B0)`。
  B0/B1/B2/B3/B4 的留出指标与各自 −B0 的 Δ 仍全部报告；B2 在 H197a/H197b 的退化由代码断言确认（与 B0 预测范数差 ≈0 的比例 ≥0.99），并作为披露项（B-D5），**不**据此判失败。判定规则 §3.7 的"主模型"指本修订给出的该设计主模型。
- **为什么不是事后调参**：本修订只依据"整行/整列在训练集不可观测 ⇒ 因子不可辨识"的代数事实，发生在任何 R197 模型拟合、预测、指标或推断计算之前；修订方向不是挑选更有利的模型（B3 与 B2 均为预注册模型；H197c 仍用 B2），且 B2 的所有结果仍完整报告。旧文本保留如上，不作删除。
