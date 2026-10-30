# R201-B.3 最终确认（task-113）：v0.4 T1 预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 B、不运行效果/不拟合/不读响应）。对象：[PROBLEM_B_v0_4.md](PROBLEM_B_v0_4.md)（SHA `D6B37E70…`）、[DESIGN_B_v0_4.md](DESIGN_B_v0_4.md)（`9112EDDC…`）、[design_B_v0_4.json](design_B_v0_4.json)（`A2D0CC1A…`）、[report_B_v0_4.md](report_B_v0_4.md)（`31F17B5E…`）、[record_B_v0_4.md](record_B_v0_4.md)（`7A3F3A23…`）、v0.3 [challenge_B_v0_3.md](challenge_B_v0_3.md)、R201 BRIEF、A5/ON2-EX/ON3/PEEK/C187/C190。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_mvp_to_lead（仅 T1 合成模拟器实现 + 资格门；不批结果/T2/T3/真实响应/湿实验）。**

v0.4 已修掉 v0.3 的两个可复核算术错误（filler 公式/18 格重算、8→10 arms wall 计数）并把 x1/x2、EV 网格、全臂 spend 冻结；核验项如下（均 PASS）：
- **filler**：`blank_QC_filler_CU=(B_E_CU+B_C/κ)−n0×363.6`；18 格 `negative_filler_rows=0`/`rows_outside_tolerance=0`/`all_pass=true`；primary residual **109.2 CU**、filler **110 wells**、spend diff **0.8≤1**；κ=0.1 例 **91.2/92/0.8**；旧 `−3917.76` 已消除；filler 不进学习器/更新/证书、无信息、单测断言。
- **10 arms/wall**：`π_dual + C0–C6(7) + C7_compute_only + C7_experiment_only` = **10 arms/replicate**；primary **5,000**、sensitivity **8,500**、total **13,500**、pilot **100**；单次≤45min/两跑≤90min；fallback 已同步（pilot primary>45→design_invalid: compute_budget_exceeded；total>45 但 primary≤45→只跑 primary 跳过敏感性；不减 500/10/configs）。
- **x1/x2+EV**：40-plan 宇宙全表冻结（`cell_u=p//10, j=p%10, x1=(j%3)−1, x2=((j//3)%3)−1, dose=0.5 if j<5 else 1.0`；split O/M/reserve）；θ 固定、τ=0.20、γ 5 点/组权重、125 γ worlds、σ=0.10 五点噪声网格；EV 明确为有限离散**近似**（不称精确），误差门≤0.02 selection accuracy、超→`design_invalid: EV_approximation_error`。
- **全臂 spend**：18 格逐格 compute-only 精确秒/experiment-only 整数 keys+filler/dual 残余 filler；JSON `spend_validation` 全 pass；primary/κ=0.1 例通过。
- **H_B**：两主对比（dual vs C7_compute_only / C7_experiment_only）Holm α=0.05；H_B 成立 iff 两者均正且 Holm 显著且点估计均≥δ_min=0.10；只赢一个→partial；无→no_decision_benefit；显著低于 δ→below_delta；主检验仅 primary；best-single 仅 inner validation；测试集不 max。
- **T2/T3/边界**：T2 描述+PEEK `B4CAD955…`、n=6/30 不作主检验；T3 data_unavailable/cost_uncalibrated、r primary=5（714,474 CU）、不执行；T1 仅计算证据；不称新颖性/机制/迁移/决策收益/独立确认；D1/D3/A1/C187 不重复。
- **SHA/算术**：v0.4 六份 SHA 与 report 一致；primary MDE 0.088594≤0.10；T3 r 成本 714,474.0 CU；18 格表格/arm 数/13,500 与 JSON 一致。

**结论：可提交 Lead 批准"T1 模拟器实现 + 资格门"，但不批准任何结果解释、T2/T3 执行、真实响应读取。**

## 1. 非阻塞实现备注（写入执行实现，不改变批准范围）

以下 3 条不改变 T1 预注册主体，但实现者应在代码/记录中写清，避免等成本/EV 门的语义漂移：
1. **filler well 计价**：当前 `filler wells=ceil(residual_CU)` 且 `spend_CU` 加 `ceil(residual_CU)`，等价于 **1 CU/blank/QC well**；请在实现/记录中明写该价格假设（blank/QC 非 A5 assay well）。若实现时把 filler 当作物理 A5 well（约 5.3–10.7 CU/well），则 spend 会超出 T；此时应改用 A5 per-well 价格重算或保持 1 CU/well 的合成价格并在账本中标注。主例 110 wells/109.2 CU 以 1 CU/well 为准。
2. **EV 门的参考**：`EV_approx` 与 `5-point noise-grid EV` 都是有限离散近似；误差门≤0.02 selection accuracy 是**两个离散近似之间**的差值，不是对连续真 EV 的误差上界。实现/记录中不得写"EV exact"；建议用更高分辨率参考（更细噪声网格/固定 seed 数值积分）复核，或明确该门是"离散参考一致性门"，仅作 T1 资格检查。T1 结果仍只作计算证据。
3. **σ=0.05 敏感性 EV 网格**：当前 `EV_grid.noise_grid_for_observation` 明确 σ=0.10；敏感性 configs 有 σ=0.05。实现必须为 σ=0.05 预注册对应五点网格（或按 fallback 跳过敏感性）；**不得**用 σ=0.10 的噪声网格跑 σ=0.05 的策略。另 EV 误差门的 calibration replicate 数/seed 需写入实现记录（当前设计只写"calibration replicate"）。

## 2. Lead T1 批准文本（建议，仅实现+资格门）

> **批准范围**：仅批准 R201-B.3 **T1 合成模拟器实现 + 资格门**。不批准 T1 结果解释/决策收益、不批准 T2/T3 执行、不批准 O'Neil/Validation 真实响应读取、不批准湿实验；T1 仅计算证据，不外推生物/真实决策收益。
>
> **冻结**：primary `(B_C=1200s,B_E=16 integer keys),κ=1,σ=0.10`；**500 独立 replicate=500 decision units**，MDE=0.088594≤0.10；敏感性 17×50 仅描述/cost_sensitive、不进主 H_B/Holm；**10 arms/replicate**（π_dual+C0–C6+C7_compute_only+C7_experiment_only）；primary 5,000/sensitivity 8,500/total 13,500/pilot 100 arm-runs；单次≤45min、两跑≤90min、fallback 按 v0.4；`T=B_C+κ·B_E_CU`、整数 key+filler（公式修正、18 格 all_pass、无负 filler、filler 不进学习器）；x1/x2/40-plan/θ/τ/γ 网格/EV 有限离散近似+误差门≤0.02/证书阶梯/R_max=5 按 v0.4 冻结；H_B AND（两 Holm 对比均正且显著且≥δ=0.10；只赢一个=partial；显著低于 δ=below_delta）；主检验仅 primary；best-single 仅 inner validation；测试集不 max。
>
> **资格门先于任何结果**：oracle 可恢复、null FP≤α、EV 近似误差≤0.02、成本账整数 key+filler+18 格 spend、无泄漏（filler 不进学习器）、10 arms 等价、两跑逐字节、schema、wall、菜单 hash/seed 复现；任一失败→`design_invalid`，不报 selection_accuracy/top-k/regret。
>
> **禁止**：T2/T3 执行；真实响应读取；把 T1 合成结果外推生物/真实决策收益/迁移/机制/新颖性；改 primary/δ/MDE/config 后救结果；把敏感性配置赢的某一格当 H_B；把 EV 离散参考一致性门写"精确 EV"。

## 3. 声明

- **本轮不运行效果/不拟合/不读响应/无湿实验**：只读 v0.4 与 v0.3 产物；只写本文件与 `tmp/`；未改 B 产物。
- **总判决：approve_mvp_to_lead**（仅 T1 模拟器实现+资格门；不批结果/T2/T3）。上述 3 条为非阻塞实现备注；T1 实现完成后，资格门结果仍需按原流程复核，T2/T3 不得执行。

**一句话：v0.4 已修复 v0.3 的 filler 公式/18 格（primary 109.2/110 wells/0.8；κ=0.1 91.2/92/0.8；无负 filler/全 pass）、10 arms wall（5,000/8,500/13,500/pilot 100）、x1/x2+EV 网格与全臂 spend；H_B AND、T2/T3/PEEK/边界一致；剩余 3 条（filler well=1 CU 假设、EV 门为离散参考一致性而非连续真误差、σ=0.05 敏感性 EV 网格）属实现/记录备注，不改变预注册主体——**approve_mvp_to_lead（仅 T1 实现+资格门，不批结果/T2/T3）**。**
