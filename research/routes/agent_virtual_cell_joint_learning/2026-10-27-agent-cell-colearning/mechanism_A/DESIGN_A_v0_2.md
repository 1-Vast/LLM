# DESIGN_A_v0_2 —— R201-A.1 P0/P1 预注册执行协议（仅 P0/P1；不执行 P2/S1/S2/H_A2）

2026-10-28。本文件修订 [DESIGN_A.md](DESIGN_A.md)（v0.1，SHA `D1D02A4B…`，保留不改），落实 [challenge_A.md](challenge_A.md) 的 5 必改（appr​ove_to_lead_mvp：**仅 P0/P1**）。形式化定义见 [PROBLEM_A_v0_2.md](PROBLEM_A_v0_2.md)；数据资格数字见 [qualify_A_v0_2.json](qualify_A_v0_2.json)。
**只做设计/预注册：不运行效果、不拟合预测、不读 O'Neil 响应值做统计；不称新颖性/机制/迁移/决策收益。**

## 0. 范围（写死）

- **批准范围 = 仅 P0/P1 最小实验**（开发性形式/存在性）。**P2/S2/H_A2 不执行**（未批准；P1 后另立预注册 + 独立挑战）；S1 决策终点不执行（若未来跑也只能 `evaluation_cannot_distinguish`，仅描述性）。
- **只用已有 O'Neil 数据/结构：不新增 wells/plate/轮次**；若执行中需要任何新测量 → 立即停，另立协议（`data_unavailable` 或 `if_needs_new_measurement: separate_protocol`）。
- 执行前本文件 + PROBLEM_A_v0_2 + qualify_A_v0_2 冻结（SHA 入 JSON）；冻结后不得改 y 聚合、τ/σ_pair、U 宇宙、F_crit、N_perm、seed、BH q、失败模板、预算；**不得看结果改阈值**。

## 1. 数据、人群与观测（冻结）

| 项 | 冻结值 |
|---|---|
| 资源 | O'Neil combination workbook（`data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`；OOXML；368,832 数据行） |
| 人群 | **batch1 且 complete-case**（viability1–4 全非空）的 pair-cell 行；**target30 细胞**（on1.json `cells.target_nonoverlap`，9 个 Jaaks 重叠细胞排除）；**702 个 15 行 pair-cell 与 315 个 0 行 pair-cell 排除**；不插值/不外推 |
| 计划（plan） | P-dose = 4×4 网格的一行 `(d_a,d_b)`（4 个技术重复为列）；P-replace = 同成员/角色/剂量在不同伙伴上下文 |
| **y 聚合（主）** | **`y_row = mean(viability1..4)`**（每行 4 重复均值；**primary 冻结**）；`X/X0` 仅作敏感性（不进 P1 主统计）；`mu/muMax` 不使用 |
| 噪声/重复 | 技术重复 = 4 列；**技术重复 ≠ 独立培养**（披露）；k=1 行不参与标定；不假设 MCAR/MAR |
| 端点/拼接 | 仅 viability（不得与 Jaaks ΔEMAX 拼接）；单药工作簿**不读数值** |

## 2. P0 门（先于 P1；全部通过才允许 P1 统计）

| 门 | 断言/阈值（冻结） | 失败处置 |
|---|---|---|
| **G1 覆盖** | target30 细胞 = **30/30** 有完整 4×4 网格 pair-cells；每细胞完整网格 pair-cells ≥ 200（v0.1 资格 median 565，min 494）；合格计划对宇宙 `|U|` ≥ 预注册下限 **100,000**（由 qualify_A_v0_2 精确计数，见 JSON） | `design_invalid: coverage` |
| **G2 可识别** | per-cell 加性设计 `rank` = 参数数 − gauge（v0.1：rank 中位 295）；**over-id = #obs − rank ≥ 16**（v0.1 median 8,745）；共享 (drug,role) 上下文中剂量集对齐比例 ≥90%（v0.1 96.9%） | `design_invalid: identifiability` |
| **G3 噪声** | `σ_obs` 由 batch1 技术重复**分半**（每行 4→2+2，固定列索引 {1,2}/{3,4}，禁按值排序）标定：`σ_obs = sqrt(mean_over_rows(half1−half2)²/2)`；要求 `1e-6 ≤ σ_obs ≤ 1.0`；`σ_pair² = σ_obs²/2`；`F_crit=2.60`；**半拆分 FPR 门**：在 H0（技术半拆替身）下 P1 检测 FPR ≤0.10 | `design_invalid: noise_calibration` |
| **G4 泄漏/隔离** | batch1 only（batch2 只披露、batch3 无 complete 行）；target30 ∩ Jaaks = 0；无 ΔEMAX/单药数值；P1 不做选择（全 U 计算）；原始 wells 不重复计数（4 重复只作行均值）；P2/S1 留出规则仅冻结不执行 | `design_invalid: leakage` |
| **G5 边界/lineage 断言** | 代码在**任何统计前**断言并写入 JSON：① target30 细胞名（归一）∩ Jaaks 125 细胞 = ∅；② 端点列仅 `viability1..4`（无 ΔEMAX）；③ 仅 batch1；④ 702/315 pair-cell 已排除；⑤ 无新 wells（data-only）；⑥ peek 披露已打印（non-blind/peeked 继承 ON3） | `design_invalid: boundary` |

## 3. P1 统计（精确冻结；形式定义见 PROBLEM_A_v0_2 §5）

### 3.1 检验宇宙 U（不做事后选择）
`U = {(p,q)}`：同一 target30 细胞；两 pair-cell 均 batch1 complete-case 完整 4×4 网格；两计划共享 ≥1 个 `(drug,role)` 上下文且**共同剂量水平 ≥2**。**|U| 由 `qualify_A_v0_2.py` 在数据上精确计数**（只数结构，不读响应）；P1 对 **U 中全部对**计算，不按任何响应量筛选。随机计划对/主动选择**只属未来 H_A2**（本协议不执行）。

### 3.2 单计划合法（separate legality）
`Y_p`（K×M 行均值矩阵，行=成员剂量、列=伙伴剂量）；加性分解 `R_p = Y_p − r_p1^T − 1c_p^T + grand`；`s_p² = ||R_p||²/((K−1)(M−1))`；**单独合法 ⇔ `sqrt(s_p²) ≤ 1.96·σ_obs/2`**（行均值噪声 SD = σ_obs/2）。仅"两计划都合法"的对进入 P1 的 per-cell max。
**若合格对中"两计划都合法"的比例 <5%** → `design_invalid: family_misspecification`（S-add 族不适合；不得改族重跑；P1 停，需另立 S-r1 协议）。

### 3.3 统计量与阈值
- 共享剂量集 D（K=共同剂量水平数，P1 要求 ≥2，预期 4）：`d = f_p|D − f_q|D`（行均值按剂量值对齐）；`d_⊥ = d − mean(d)`；**`F_pair = [||d_⊥||²/(K−1)] / σ_pair²`**。
- **δ_J（pair 级）**：`F_crit = F_{0.95, K−1, ∞} = 2.60`（K−1=3 时；K<4 时按冻结公式 `scipy.stats.f.ppf(0.95, K−1, np.inf)` 计算）。
- **per-cell**：`T_c = max F_pair over c`（仅合法对）。**置换零分布**：每 plan-cell 内把 16 行做**行置换**（保持 4 列结构；不加额外噪声），重算 row means 与所有 F，得 `T_c^{(b)}`；**N_perm=500、seed=20261029**。
- **per-cell p 值**：`p_c=(1 + #{b: T_c^{(b)} ≥ T_c})/(1+N_perm)`；**BH-FDR q=0.05**（30 细胞）。
- **P1 阳性（冻结，三条件全满足）**：① BH 拒绝细胞数 **≥5**；② pooled 合格对中 `F_pair ≥ F_crit` 的比例 ≥ **置换零分布 pooled 比例的 Q95**（同一 N_perm）；③ G1–G5 全 PASS。
- **P1 阴性（冻结）**：不满足 ①/② → verdict `no_joint_contradiction`；**只写"本资源/本族/本设计下未检出联合矛盾"，不写"矛盾不存在"、不写结构/机制/迁移/决策**。

### 3.4 FPR/多重性论证（441,867 全宇宙；写死）
- v0.1 资格在 **39 细胞**上给出 441,867 个合格计划对；**target30 的 |U| 由 qualify_A_v0_2 精确计数**（预计 <441,867）。**pair 级计数只作描述性**：若 P1 用 pair 级计数作证据，在 H0 下每个 pair 以 5% 误报 → 44 万对期望 ~2.2 万假阳性，**故 pair 计数永不单独作为存在性证据**。
- P1 推断统计量 = **per-cell max**：cell 内 ~10^4 对的多重性被 max 统计量 + 500 次行置换零分布吸收；30 细胞再用 **BH q=0.05** 控制跨细胞 FDR；P1 阳性还要求 pooled 比例超零分布 Q95（双保险）。**不得**用 pair 级 p 值或按结果挑细胞。
- **零模型门（P0 后、P1 前）**：① 技术半拆 FPR ≤0.10（每行 4→2+2 独立半拆，行均值替身零分布）；② 算子打乱（(drug,role) 标签在细胞内的计划间随机置换、保支撑）下 P1 检测率 ≤0.10；③ 行置换零分布 PASS（N_perm=500 自身即零模型）。任一失败 → `design_invalid: null_calibration`。
- **随机计划对**：P1 无选择，故随机 vs 全 U 无差异；随机对照只属 H_A2（未批），本协议不执行。

### 3.5 种子/确定性
| 用途 | 值 |
|---|---|
| 折分配（30 细胞 → 5×6） | seed **20261028** |
| P1 行置换零分布 | seed **20261029**，N_perm=**500** |
| 技术半拆分半索引 | 固定列索引 {1,2}/{3,4}（禁按值排序） |
| 算子打乱零模型 | seed **20261031**，N_perm=500 |
| JSON 键排序/无时间戳/allow_nan=False；同脚本两跑逐字节一致 | 必需 |

## 4. 切分/折清单/防泄漏

- **P1 无训练/测试切分**：P1 是**全数据存在性/拟合检验**，不预测、不学习跨细胞；因此不做留出（留出只用于未来 P2/S1）。**写死**：P1 的合法性由置换零分布（行置换）校准，而不是留出。
- **折清单（仅报告一致性，不参与 P1 推断）**：30 个 target 细胞按归一名排序，seed 20261028 随机置换后 `fold = index % 5` → **5 折 × 6 细胞**；每折报告 P1 描述性计数（不作 per-fold 推断、不换折）。
- **防泄漏（写死）**：4 个技术重复只作行均值（不把 wells 当独立 n）；batch1 only；target30 ∩ Jaaks = 0；不读单药工作簿数值；不拼 ΔEMAX；P2/S1 的"整 pair-cell/剂量行留出"规则冻结（P2 若执行：留出整个 pair-cell 或整个剂量行，不得留出单个 well），本协议不执行。
- **P1 不得**按响应/残差选择计划对、细胞或阈值；不得用 702/315 pair-cell 或 batch2/3 补数。

## 5. 两跑、schema、失败模板、G5 断言

- **两跑**：同脚本、同输入、同 seeds → `outputs_A_v0_2.json` **逐字节一致**；单命令 wall 目标 ≤900 s、CPU ≤2 CPU-h、内存 ≤8 GB；超限 → `design_invalid: compute_budget_exceeded`（不得减 N_perm/换便宜分析）。
- **JSON schema（冻结字段）**：
  `{"protocol_sha256","script_sha256","inputs":{...},"peek_disclosure":{...},"y_aggregation","gates":{"G1":...,"G2":...,"G3":...,"G4":...,"G5":...},"p0":{"pass":bool,"details":{...}},"p1":{"universe_size","n_legal_pairs","T_c":{cell:...},"p_c":{...},"bh":{"q":0.05,"n_reject":...,"rejected_cells":[...]},"pooled_fraction","null_q95_pooled","F_crit","delta_J":...,"verdict":...},"null_checks":{"half_split_fpr":...,"operator_shuffle_rate":...},"failure_category":null_or_str,"notes":[...]}`
- **失败模板（冻结）**：`failure_category ∈ {data_unavailable, design_invalid:coverage|identifiability|noise_calibration|leakage|boundary|null_calibration|compute_budget_exceeded|family_misspecification, no_joint_contradiction}`；`verdict ∈ {p0_pass_p1_positive, p0_pass_p1_negative, p0_fail, design_invalid, data_unavailable}`；`notes` 必须含 peek 披露与非结论措辞。
- **G5 断言（代码级，先于统计）**：见 §2 G5 六条；断言结果写入 JSON `gates.G5.assertions`；任一失败即停（不产生 P1 数值）。

## 6. 预算（P0/P1；data-only）

| 项 | 冻结值 |
|---|---|
| 新 wells/plate/轮次 | **0**（只用已有 O'Neil 文件；无新测量） |
| 计算 cap | wall ≤**900 s**、CPU ≤**2 CPU-h**、内存 ≤**8 GB**（单跑）；两跑合计 ≤2× |
| 置换 | N_perm=**500**（行置换）+ N_perm=500（算子打乱，§3.4）；不增不减 |
| 实现估计 | target30 合格对 |U| 与 per-perm 全对 F 计算（qualify_A_v0_2.json 记录精确 |U|）；若实测超 cap → `design_invalid: compute_budget_exceeded` |
| 若需新测量 | 停 P0/P1，另立协议（记录所需测量），不得用已有数据替代新测量 |

## 7. 未批准项（写死延后）

- **P2/ΔW**：空集规则已冻结（PROBLEM_A_v0_2 §4）；**本协议不执行**；未来执行须另立预注册（含"非空对 ≥20% 才可估 P2"条件）。
- **S1 决策终点**：不执行；若未来跑仅描述性，MDE 0.7625 >δ_min → `evaluation_cannot_distinguish`，不得写决策收益。
- **S2/H_A2**：数值目标已冻结（PROBLEM_A_v0_2 §6：W*=0.05、δ_noninf=0.01、wells 差 ≥max(8 wells,25%)）；**不执行**；任何算法/决策/迁移主张均需 P1 通过后另立预注册 + 独立挑战 + Lead 批准。
- 先例：CoMap/LAWM/MDA/COPEx 仅背景，不得写成新意；不称新颖性/机制/迁移/决策收益。

## 8. Lead 批准清单（建议文本）

> 批准 **R201-A 仅进入 P0/P1 最小实验**（开发性形式/存在性；不进入 P2/S2/H_A2；S1 不执行）。
> 冻结：`PROBLEM_A_v0_2.md`、`qualify_A_v0_2.json`、`DESIGN_A_v0_2.md`（SHA 见 usage/report）；y=mean(viability1–4)、σ_pair=σ_obs/√2、F_crit=2.60、N_perm=500、seed 20261029、BH q=0.05、U 宇宙与 P0 门 G1–G5、失败模板、budget（data-only，0 新 wells）。
> **P1 解释边界**：只写"本资源/本族/本设计下存在联合矛盾"的开发性存在性；不写结构成立/生物机制/迁移/决策；不达 → `no_joint_contradiction`，不写"矛盾不存在"。
> 若执行需要任何新测量/新 wells → 停 P0/P1，另立协议。
