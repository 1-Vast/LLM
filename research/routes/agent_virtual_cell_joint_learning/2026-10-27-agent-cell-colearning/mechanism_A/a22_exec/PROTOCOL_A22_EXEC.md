# PROTOCOL_A22_EXEC —— R201-A.2.2 执行协议（Lead 批准后、运行前冻结）

2026-10-28。依据：`DECISION_R201_A22_EXEC.md`（Lead 批准仅 A.2.2 data-only P1 重跑）、`PROBLEM_A22.md`（`69605BBC…`）、`DESIGN_A22.md`（`EAC8EA10…`）、`sigma_robust_A22.json`（`12DC9855…`）。
**本文件在 `run_a22_exec.py` 运行前冻结；运行后不得改阈值/族/N_perm/legal 规则/σ/null/诊断门。**

## 1. 冻结常量

| 项 | 值 |
|---|---|
| 数据 | O'Neil batch1 complete-case、target30、完整 4×4 网格；702/315 pair-cell 排除；0 新 wells |
| |U| | **340,088** |
| A.2 legal（不变） | `RMS ≤ 1.96·σ_obs_A2`，`σ_obs_A2=σ_w_hat/2`（σ_w_hat=sqrt(mean((hA1−hA2)²))）；预期阈值≈0.0910607；n_legal_A2≥**17,004.4** 否则 coverage |
| **R4 σ** | 每 context c=(cell,drug,role)：`σ²_R4(c)=mean_{plan pairs in c}[ ||P⊥(f_a−f_b)||²/(K−1) ]`（f=full 4-rep profile：role A 行均值/role B 列均值） |
| **F_pair** | `[||P⊥(f_p−f_q)||²/(K−1)] / σ²_R4(shared context)` |
| **F_self**（D2/D3 用；精确公式） | `F_self(p,q)=[||P⊥(f_p−f_q)||²/(K−1)]/σ²_R4(c)`（与 F_pair 同式；pair 级 full profile；D2/D3 按 legal pair 计算） |
| F_crit | 2.60（仅 D2+D3 PASS 保留） |
| N_perm / BH / 阳性 | 500（seed=20261029）/ q=0.05（30 细胞）/ 三条件同 A.1 |
| 预算 | wall≤900 s、CPU≤2 h、内存≤8 GB；≈2,500 模拟；两跑逐字节；结果 JSON 无 telemetry |

## 2. 数据结构

- plan-cell 矩阵：`Y`（4 reps 均值，4×4）、`MA1/MA2`（半拆 A={1,2}/{3,4}）——半拆仅用于**描述性**诊断（A.2 的 F_self_check 指标），不参与 D2/D3 判定（D2/D3 用 §1 的 pair-level F_self）。
- 每 plan 两个 context：A=(cell,drugA,'A')、B=(cell,drugB,'B')；context profile：A→行均值、B→列均值；每 context 的 plans 列表。
- 计划对：同 cell、共享 **1 个** context（U 必须=340,088）；每 pair 记录 shared context key 与该 context 内两个 plan 的局部索引。
- **R4 前置门**：每 context 需 ≥2 plans 且 σ²_R4(c) 有限、>1e-12；invalid context 的 pair 不进入 F 推断；**排除 pair 比例 = #invalid-context pairs / U ≤5%**，否则 `design_invalid: coverage`。
- **resubstitution 披露**：σ²_R4(c) 的均值**包含被检验 pair**（finite-sample/resubstitution 校准，不称"独立尺度"）；另报 leave-one-pair-out 敏感性（描述性，不作判定）：对 context 内 n_pairs≥2 的 pair，`σ²_LOO=(sum_ss−ss_pair)/((n_pairs−1)(K−1))`，`F_LOO=ss_pair/((K−1)σ²_LOO)`，报 F_LOO/F 的中位/分位。

## 3. D1–D7（先于 P1；按序）

| 门 | 内容 | 失败类别 |
|---|---|---|
| D1 | 全部 included context 的 σ²_R4(c) 有限、>1e-12、非退化；σ_w_hat 有限 | `design_invalid: scale_mismatch` |
| D2 | ① per-context F_self 中位 ∈[0.5,2] 的 context 比例 **≥0.85**；② 全局 F_self 中位∈[0.5,1.5]；③ overall F_self FPR@F_crit≤0.10；④ ratio 诊断（p95/p05）仅报告 | `design_invalid: scale_mismatch` |
| D3 | ① overall FPR@F_crit≤0.10；② **worst-context FPR≤0.25**；③ **context-FPR p95≤0.20**（context FPR = F_self>F_crit 比例，按 legal pair） | `design_invalid: noise_calibration` |
| D4 | primary null（N0-strat）pooled 比例中位∈[0.02,0.15]（null 后） | `design_invalid: null_calibration` |
| D5 | `median(T_null)/median(T_obs)∈[0.2,3]`（null 后） | `design_invalid: null_calibration` |
| D6 | pilot 预算投影 ≤caps（执行前） | `design_invalid: compute_budget_exceeded` |
| D7 | G1–G5（A.1 定义）+ peek 披露 | A.1/A.2 既有类别 |

任一失败：写 failure_category 与 verdict=design_invalid，不进入 P1 判定。F_crit 仅在 D2+D3 PASS 时保留。

## 4. P1（A.2.2 冻结流程）

1. A.2 legal 集（阈值≈0.0910607）、n_legal_A2；≥17,004.4 否则 coverage。
2. 有效 pair 集 = legal pairs 且 shared context valid（R4 前置门）；n_legal_infer；排除比例门已在 D7/coverage。
3. 观测：F_pair（§1）、per-cell `T_c=max F_pair`（cell 内 legal valid pairs）、pooled_obs=`#{F_pair≥F_crit}/n_legal_infer`。
4. **N0-strat**（primary pooled null）：seed=20261029；500 次，每次对每个 legal-valid pair 抽 `F*~χ²₃/3`，pooled*=mean(F*≥F_crit)；Q95/中位；D4。
5. **N1-R4 per-cell null**：seed=20261029；500 次；每 replicate：每 included context c 取 `f_hat(c)=mean full profile`；每 plan 生成 `f*_p ~ N(f_hat(c), σ²_R4(c)/2)`（per dose）；重算各 legal-valid pair 的 `F*`（用 σ²_R4(c)）与 per-cell `T_c*`；`p_c=(1+#{T_c*≥T_c})/(1+500)`；BH q=0.05（30 细胞）；D5。
6. **阳性三条件**（同 A.1）：① BH 拒绝≥5；② pooled_obs ≥ Q95_N0；③ D1–D7 全 PASS。阳性→`p1_positive`（仅"本资源/本族/本设计下存在联合矛盾（开发性）"）；否则→`p1_negative`（仅 `no_joint_contradiction`，**不写"矛盾不存在"**）。

## 5. 预算/输出/边界

- **pilot**：测 1 次 N1-R4 replicate + 1 次 N0 replicate 耗时，投影 `t_obs + 500·t_N1 + 500·t_N0`（×1.2 overhead）；caps 900 s/7200 s/8 GB；超→compute_budget_exceeded（不减 N_perm）。
- 输出：`a22_exec.json`（确定性判定/统计/门）、`a22_exec_rows.csv`（逐细胞）、`a22_exec_diagnostics.json`（σ/coverage/LOO/pilot/telemetry/null/BH/positive/peek）；report/record/usage；两跑逐字节。
- **披露**：候选选择/校准只用合成（A.2.2 预注册）；C194 仅用于问题诊断与预设阈值，**不用于 A.2.2 observed 选择**；R4 σ 为 resubstitution；LOO 仅描述；non-blind/peeked（ON3 继承）；pair 级仅描述性；不称机制/生物学/迁移/决策收益；0 新 wells；不进 P2/S2/H_A2；A.1/A.2 不重判。
