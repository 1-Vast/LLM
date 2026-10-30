# PROTOCOL_P0P1_EXEC —— R201-A P0/P1 执行协议（Lead 批准后、运行前冻结）

2026-10-28。依据：`DECISION_R201_A_P0P1.md`（Lead 批准仅 P0/P1）、`DESIGN_A_v0_2.md`（`486272B2…`）、`PROBLEM_A_v0_2.md`（`61EC2FC9…`）、`qualify_A_v0_2.json`（`D6AE3506…`）。
**本文件在 `run_a_p0p1.py` 运行前冻结**；实现选择在此写死，运行后不得改阈值/族/置换数/折清单。
**范围**：P0 资格门 + 预算预检 + P1 联合矛盾存在性（开发性）。**不执行 P2/S1/S2/H_A2；0 新 wells/plate/轮次；data-only。**

## 1. 输入与冻结常量

| 项 | 值 |
|---|---|
| O'Neil combination workbook | `data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`（SHA 见输出 JSON） |
| target30 | `on1.json → cells.target_nonoverlap`（30 细胞；9 个 Jaaks 重叠排除） |
| y | `y_row = mean(viability1..4)`（**primary 冻结**）；`X/X0` 不进 P1 |
| 人群 | batch1 且 complete-case（viability1–4 全非空）；702 个 15 行/315 个 0 行 pair-cell 排除；不插值 |
| 噪声 | 固定半拆 `{1,2}/{3,4}`：`half1=mean(viability1,2)`、`half2=mean(viability3,4)`；`σ_obs=sqrt(mean_over_batch1_rows((half1−half2)²)/2)`（**冻结公式字面**）；`σ_pair²=σ_obs²/2` |
| 门限 | `F_crit=2.60`（F_{0.95,3,∞}）；`|U|=340,088`（target30，由 v0.2 冻结）；`N_perm=500`（seed=**20261029**）；BH `q=0.05`（30 细胞）；`δ_min=0.05`（不用于 P1） |
| 预算 | wall≤**900 s**、CPU≤**2 h**、内存≤**8 GB**；F 计算量 ≈3.40×10⁸；0 新 wells |
| 算子族 | **S-add（role-stratified）**：`y(pair(a,b))=f_{a,roleA}(d_a)+g_{b,roleB}(d_b)`；S-r1/role-agnostic 不进 P1 |

## 2. 数据结构与公式（实现冻结）

- **plan-cell**：target30 内 batch1 complete-case 的 (cell, unordered pair)，要求 16 行、4 个 distinct `drugA Conc`、4 个 distinct `drugB Conc`、16 个 distinct `(concA,concB)`；矩阵 `Y`（4×4，行=concA 升序、列=concB 升序，元素=4 重复均值）。不满足者排除并计数。
- **上下文**：`(drug, role)`；role A = drugA slot（行方向剂量集），role B = drugB slot（列方向剂量集）。
- **profile**：role A → 行均值（4 剂量）；role B → 列均值。计划对共享 1 个上下文且剂量集相同（4 个共同剂量）→ 对齐后用 `f_p−f_q`。
- **单计划合法**：加性残差 `R=Y−r1^T−1c^T+grand`，`s²=||R||²/((K−1)(M−1))=||R||²/9`；合法 ⇔ `sqrt(s²) ≤ 1.96·σ_obs/2`。
- **F_pair**：`d=f_p|D−f_q|D`；`d⊥=d−mean(d)`；`F=[||d⊥||²/(K−1)]/σ_pair²`（K=4）。
- **per-cell T_c**：`max F_pair` 于**观测合法** pair 集（legal 由观测数据判定，permutation 时固定该集合）；无合法 pair 的细胞 p=1 且不拒绝。
- **半拆分 FPR**：每个 (plan-cell, context) 用 `Y_h1`/`Y_h2` 的 profile 差：`F_self=[||P⊥(f_h1−f_h2)||²/3]/σ_pair²`（半均值差的行均值方差与 σ_pair² 同阶）；`FPR = #{F_self>F_crit}/total`；门 ≤0.10。
- **16 行可交换性断言**：每 plan-cell 行恰为 16 个唯一剂量组合；workbook 无 plate/date/行序元数据列（列清单断言）；行置换保持 4×4 结构 → 可交换。失败 → `design_invalid: null_calibration`。
- **行置换零分布**：每次 replicate 对**每个 plan-cell** 独立随机置换其 16 个矩阵元素（reshape 回 4×4），重算 row/col means 与全部 F_pair（合法 pair 集固定），得 `T_c^{(b)}`、pooled 比例^{(b)}；`N_perm=500、seed=20261029`。
- **算子打乱零模型（操作化，冻结）**：因 F 只依赖数值 profile，标签置换在保支撑下等价于对 plan-cell 数值重排；**实现为独立行置换，seed=20261031、N=500**；检测率 = `#{T_c^{(b,op)} ≥ Q95_行置换_null(c)}` / (30×500)；门 ≤0.10。
- **检验结构**：per-cell `p_c=(1+#{b:T_c^{(b)}≥T_c})/(1+N_perm)`；**BH q=0.05**（30 细胞）。**P1 阳性三条件**（全满足）：① BH 拒绝细胞数 ≥5；② `pooled_obs = #{legal pairs: F≥F_crit}/n_legal_pairs` ≥ `Q95_perm(pooled^{(b)})`；③ G1–G5 全 PASS。**阴性** → `no_joint_contradiction`（不得写"矛盾不存在"）。
- **族错设门**：`frac_legal_pairs = n_legal_pairs/|U|`；<0.05 → `design_invalid: family_misspecification`（不跑 P1）。
- **预算预检（先于 500×2 次置换）**：测 1 次完整行置换 + observed 全 F 的 wall；投影 `t_obs + N_perm·(t_perm_row + t_perm_op)`；与 wall 900 s / CPU 7200 s / 内存 8 GB 比较；超限 → `design_invalid: compute_budget_exceeded`（**不得**减 N_perm/换便宜分析）。
- **G5 六断言（运行前）**：① target30∩Jaaks=∅；② 端点列仅 viability1–4（无 EMAX/SYNERGY）；③ batch1 only；④ 702/315 pair-cell 已排除；⑤ 无新 wells（data-only）；⑥ peek 披露打印（non-blind/peeked 继承 ON3 `39868CE4…`）。
- **失败模板**：`failure_category ∈ {design_invalid:coverage|identifiability|noise_calibration|leakage|boundary|null_calibration|family_misspecification|compute_budget_exceeded, no_joint_contradiction}`；verdict ∈ {p0p1_positive, p0p1_negative, design_invalid, data_unavailable}。

## 3. 两跑/输出/边界

- 同脚本两跑：`a_p0p1.json` 与 `a_p0p1_rows.csv` **逐字节一致**（JSON 键排序/无时间戳/allow_nan=False；telemetry wall/CPU/内存写 `usage_a_p0p1.json`，不进结果 JSON）。
- 输出：`a_p0p1.json`（gates、σ、F_crit、per-cell T/p/BH、pooled、positive 三条件、failure）、`a_p0p1_rows.csv`（逐细胞）、`budget_precheck.json`、report/record/usage。
- 解释边界：阳性只写"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`；pair 级仅描述性；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked；不执行 P2/S1/S2/H_A2；不追加新测量。
