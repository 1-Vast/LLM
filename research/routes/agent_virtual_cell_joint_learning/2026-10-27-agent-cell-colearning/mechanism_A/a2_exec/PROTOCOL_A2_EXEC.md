# PROTOCOL_A2_EXEC —— R201-A.2 执行协议（Lead 批准后、运行前冻结）

2026-10-28。依据：`DECISION_R201_A2_EXEC.md`（Lead 批准仅 A.2 data-only P1 重跑）、`PROBLEM_A2_v0_2.md`（`3B49A8AB…`）、`DESIGN_A2_v0_2.md`（`3AB5A663…`）、`null_design_A2_v0_2.json`（`96AE014D…`）。
**本文件在 `run_a2_exec.py` 运行前冻结；运行后不得改阈值/族/N_perm/legal 规则/null/σ。**
**范围**：A.2 data-only P1 重跑（0 新 wells；不进入 P2/S2/H_A2；不重判 A.1；不做生物学/机制/迁移/决策收益/新颖性主张）。non-blind/peeked 继承 ON3 披露。

## 1. 输入与冻结常量

| 项 | 值/路径 |
|---|---|
| O'Neil workbook | `data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`（SHA 见 JSON） |
| target30 | `research/2026-10-27-core-module-design/oneil_dev/on1.json → cells.target_nonoverlap` |
| |U| | **340,088**（固定；A.2 不改变 U） |
| σ_w_hat | `sqrt(mean_over_batch1_complete_rows((hA1−hA2)²))`，hA1=mean(viability1,2)，hA2=mean(viability3,4) |
| σ_obs_A2 | `σ_w_hat/2`（行均值噪声 SD） |
| S1 | `σ_w_hat²/8` |
| **σ_pair²_A2** | **`0.5 × mean_{plan,context} ||P⊥(f_A1−f_A2)||²/(K−1)`**（S2_raw/2；预期 ≈0.00107924） |
| F_self_check | 每 (plan-cell, context)：两套半拆 A={1,2}/{3,4}、B={1,3}/{2,4}（同组 4 wells）；`d_avg=(d_A+d_B)/2`；`F=||P⊥d_avg||²/(K−1)/σ_pair²_A2` |
| A.2 legal | `RMS ≤ 1.96·σ_obs_A2`（预期阈值 0.0910607）；`n_legal_A2 ≥ 17,004.4`（5%|U|）否则 coverage |
| F_crit | 2.60（仅 D2+D3 通过时保留；不缩放 observed F、不改阈值） |
| N_perm | **500**（seed=**20261029**；N0 与 N1 同 seed，确定性） |
| BH | q=0.05（30 细胞） |
| 族 | S-add（role-stratified） |
| 预算 | wall≤900 s、CPU≤2 h、内存≤8 GB；≈2,500 模拟；两跑逐字节；结果 JSON 无 telemetry |

## 2. 数据与结构（同 A.1）

- batch1 complete-case（viability1–4 全非空）；target30；完整 4×4 网格 plan-cell（16 行、4 distinct concA、4 distinct concB、16 combos）；702/315 pair-cell 排除；不插值；不读单药工作簿；不拼 ΔEMAX。
- 每 plan-cell 建 5 个 4×4 矩阵：`Y`（4 reps 均值）、`MA1/MA2`（半拆 A：{1,2}/{3,4} 的 2-rep 均值）、`MB1/MB2`（半拆 B：{1,3}/{2,4}）；行=concA 升序、列=concB 升序。
- 上下文 profile：role A → 行均值（4 剂量）；role B → 列均值；每 plan-cell 的 A/B 两个上下文。
- 计划对：同 cell、共享 1 个 (drug,role) 上下文；**|U| 必须=340,088**（与 A.1 同一构造）。

## 3. D1–D7 诊断门（先于 P1；按序判定）

| 门 | 内容 | 失败类别 |
|---|---|---|
| D1 | σ_w_hat、σ_pair²_A2 有限、1e-6<σ_w<1、1e-12<σ_pair²<1 | `design_invalid: scale_mismatch` |
| D2 | F_self_check 均值/中位∈[0.5,2]；ratio `σ_pair²_A2/S1∈[0.5,2]` | `design_invalid: scale_mismatch` |
| D3 | F_self_check `FPR@F_crit≤0.10`（D2+D3 通过才保留 F_crit=2.60） | `design_invalid: noise_calibration` |
| D4 | primary null（N0）pooled 比例中位∈[0.02,0.15]（N0 计算后判定） | `design_invalid: null_calibration` |
| D5 | `median(T_null)/median(T_obs)∈[0.2,3]`（N1 计算后判定） | `design_invalid: null_calibration` |
| D6 | pilot 预算投影 ≤ caps（执行前） | `design_invalid: compute_budget_exceeded` |
| D7 | G1–G5（覆盖/可识别/泄漏/边界断言，A.1 定义）+ peek 披露 | A.1 既有类别 |

任一失败：写 `failure_category` 与 `verdict=design_invalid`，**不进入 P1 判定**。

## 4. P1（A.2 冻结流程）

1. 计算 A.2 legal 集（§1 规则）→ n_legal_A2；≥17,004.4 否则 coverage fail。
2. `F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²_A2`（K=4；f 为 full profile：role A 行均值、role B 列均值）。
3. per-cell `T_c=max F_pair`（A.2 legal pair 集）；pooled `#{legal pairs: F≥F_crit}/n_legal_A2`。
4. **primary null N0**（pooled）：seed 20261029，500 次，每次生成 `n_legal_A2` 个 iid `χ²₃/3`，得 pooled 比例 null；Q95 与中位。
5. **N1 per-cell null**：seed 20261029，500 次；每次：对每 (cell, context-A group) `f_hat^A = mean` 行 profile；每 plan `g_hat^B = colmeans(Y−f_hat^A)`；生成 `Y* = f_hat^A[:,None] + g_hat^B[None,:] + N(0,σ_y²)`，`σ_y=sqrt(2σ_pair²_A2)`；重算 F/T_c（legal pair 集固定为 A.2 observed legal 集）；得 `T_null[cell,b]`。
6. `p_c=(1+#{T_null≥T_obs})/(1+500)`；BH q=0.05（30 细胞）；D4/D5 判定。
7. **阳性三条件**：① BH 拒绝≥5；② pooled_obs ≥ Q95_N0；③ D1–D7 全 PASS。阳性→`p1_positive`（仅"本资源/本族/本设计下存在联合矛盾（开发性）"）；否则→`p1_negative`（仅 `no_joint_contradiction`，**不写"矛盾不存在"**）。

## 5. 预算 pilot（执行前）

- 测 2 次 N1 单次模拟、2 次 N0 抽样、observed 统计的耗时（wall/CPU/内存）；投影 total = observed + 500·t_N1 + 500·t_N0，×1.2 overhead；与 caps 比较；超限→`design_invalid: compute_budget_exceeded`（**不减 N_perm**）。
- telemetry（pilot 实测/投影/最终 wall/CPU/内存）只写 `a2_exec_diagnostics.json` 与 usage；结果 JSON 确定性、无 telemetry。

## 6. 输出/确定性/边界

- 输出：`a2_exec.json`（判定/统计/门/失败类别）、`a2_exec_rows.csv`（逐细胞）、`a2_exec_diagnostics.json`（σ/F_self/legal/pilot/预算/零模型诊断/BH/阳性条件/peek 披露）、report/record/usage。
- 两跑逐字节一致（JSON 键排序/无时间戳/allow_nan=False）。
- 禁止：P2/S2/H_A2；新测量/新 wells；改冻结阈值/族/N_perm/legal 规则；用 observed 选规则；用 A.1 结果改 null/σ/阈值；把 positive 写机制/生物学/迁移/决策收益。
- 边界：0 新 wells；non-blind/peeked；pair 级仅描述性；技术重复≠独立培养；不拼 ΔEMAX。
