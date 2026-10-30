# PROBLEM_B_v0_4 —— 双预算决策形式化 v0.4（R201-B.3；T1 冻结修复；不执行）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：v0.3 文件、`challenge_B_v0_3.md`（R201-B.3-C1，revise 5 必改，SHA `9B6F4438…`）、R201 BRIEF、A5/ON2-EX/ON3/PEEK/C187/C190。**仅设计/算术；未运行 T1/T2/T3、未拟合、未读响应、无湿实验；不称新颖性/机制/迁移/决策收益。**

## 0. v0.4 的 5 项修复

| challenge 必改 | v0.4 处理 |
|---|---|
| ① filler 单位/公式 | 改为 **`blank_QC_filler_CU=(B_E_CU+B_C/κ)−n0×363.6`**（不是 `T_seconds−keys_CU`）；18 格全部重算；`residual_CU∈[0,363.6)`；无负 filler；primary 109.2 CU 保持；filler 用整数 blank/QC wells=`ceil(residual_CU)`，`spend_diff≤1 CU`。 |
| ② arm-run 计数 | T1 **10 arms/replicate**：`π_dual + C0–C6(7) + C7_compute_only + C7_experiment_only`；primary 500×10=**5,000**；sensitivity 17×50×10=**8,500**；total **13,500**；pilot=10×10=100 arm-runs；wall/45/90min/fallback 按此重算。 |
| ③ x1/x2 + EV 网格 | 40-plan 表：`cell_u=p//10, j=p%10, x1=(j%3)−1, x2=((j//3)%3)−1, dose=0.5 if j<5 else 1.0`，split O/M/reserve；θ 固定 `[0.5,0.3,0.2,0.1,−0.1]`；EV 用 **125 gamma worlds**（3 gamma groups×5-point normal grid，τ=0.20，权重 `[0.0545,0.2442,0.4026,0.2442,0.0545]`）+ 噪声近似；预注册误差门 **≤0.02 selection accuracy**，超过→`design_invalid: EV_approximation_error`；不再称"精确枚举"。 |
| ④ 全臂 spend 校验 | 18 格 × 各臂 `|spend−T_CU|≤1 well-equivalent`；JSON 给出每格 residual/filler wells/spend_diff；无负 filler；compute-only 秒精确；dual filler 补 T；主例 residual 109.2 CU/filler 110 wells/diff 0.8 CU；κ=0.1 例 residual 91.2 CU/filler 92 wells/diff 0.8。 |
| ⑤ 边界同步 | wall JSON/报告统一为 10 arms；T2 描述+PEEK `B4CAD955…`；T3 `data_unavailable/cost_uncalibrated`；r primary=5；T1 批准仅实现+资格门、不批结果/T2/T3；资格门先于结果、失败只 `design_invalid`、不报 selection accuracy/top-k/regret。 |

## 1. 决策状态/成本（形式化）

- 状态 = (P, M_t, B_C [实测 CPU-second], B_E [整数 keys/wells/plates/rounds + A5 planning CU], A_compute∪A_experiment, π)。
- **合成总成本**：`T_seconds=B_C+κ·B_E_CU`；**实验侧 CU 等价**：`T_CU=B_E_CU+B_C/κ`；T2/T3 无报价→`cost_uncalibrated`，不作成本结论。
- **primary**：`B_C=1200s, B_E=16 integer keys, κ=1, σ=0.10`；`T_seconds=T_CU=7017.6`；experiment-only `n0=19 keys=6908.4 CU` + residual **109.2 CU** filler（110 blank/QC wells）；spend 7018.4 CU，diff 0.8≤1；compute-only `B_C_eff=7017.6s`；dual 1200s+5817.6 CU + filler 到 T。
- **decision unit**：独立 held-out cell/fold 菜单；primary 500 replicate=500 decision units；technical wells/keys 不是 unit。
- **T3**：r primary=5；393×5×363.6=**714,474.0 CU**；T3 仍 data_unavailable/cost_uncalibrated。

## 2. 判据/H_B/Primary（与 v0.3 一致，冻结）

- 唯一判定树：无证书/效用→`certificate_unavailable/blocked`；`g_C>1` 且 B_C 足→计算；**B_C 耗尽→`compute_budget_exceeded`（不买实验/不静默停）**；`g_C≤1` 决策唯一→`compute_sufficient`；evidence-limited：headroom 未知→`oracle_unknown`；MDE>δ/power<0.8/headroom<Δ→`evaluation_cannot_distinguish`；否则买 EV/CU 最大实验；轮次耗尽→`unresolved`；T2/T3 冻结前不下结论。
- Primary = top-1 selection accuracy（[0,1]）；primary 500 units 的 MDE=`2.801585×sqrt(0.5/500)=` **0.088594 ≤0.10 PASS**；δ=0.10 为操作阈值；blocked 仅 secondary；
- H_B 成立 iff 两主对比（dual vs C7_compute_only、dual vs C7_experiment_only）**Holm 后均正且显著、且两点估计均≥δ=0.10**；只赢一个→`partial_decision_benefit`；无→`no_decision_benefit`；显著但低于 δ→`below_delta`；主检验仅 primary；敏感性只描述。

## 3. 与 AL/BOED/COPEx/边界

一般概念已被覆盖（decision AL/BOED/EVSI/ENBS/COPEx/约束生成/计算决策/GP）；不主张新算法/首次双预算/预测分歧采样；差别仅限定具体共享对象与更新运算；同信息同预算普通方法等效→撤新意。T1 仅计算证据；T2 描述+PEEK；T3 data_unavailable/cost_uncalibrated；不称新颖性/机制/迁移/决策收益/独立确认；D1/D3/A1/C187 不重复；冻结≠资源足够/关系成立/Stage 1/效果。
