# PROBLEM_B_v0_3 —— 双预算决策形式化 v0.3（R201-B.2；T1 预注册冻结修复；不执行）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：v0.2 三件 + `challenge_B_v0_2.md`（R201-B.2-C1，revise 5 必改，SHA `4D3A3AB5…`）、R201 BRIEF、A5/ON2-EX/ON3/PEEK/C187/C190。**本文件只做形式化/预注册冻结修复；未运行 T1/T2/T3、未拟合、未读响应、无湿实验；不称新颖性/机制/迁移/决策收益。**

## 0. v0.3 的 5 项冻结修复

| challenge 必改 | v0.3 处理 |
|---|---|
| ① primary 配置与 500 replicate 归属 | **primary = `(B_C=1200s, B_E=16 keys), κ=1, σ=0.10`**；primary **500 独立 replicate = 500 decision units**；其余 17 配置（3 固定预算对 × 3κ × 2σ = 18 格）各 50 replicate，仅敏感性；主 H_B 只在 primary 做（Holm 两对比）；B_C 网格统一为固定预算对 `(300,4)/(1200,16)/(3600,64)`。 |
| ② 整数 key + 无信息 filler | 实验 key 必须**整数**；experiment-only 换算 `n0=B_E+floor((B_C/κ)/363.6)` + **blank/QC/已知标准品 filler**（不进学习器、不更新模型）；compute filler = 无信息随机计算步骤（不产证书/不更新）；`|花费−T|≤1 well-equivalent`；无泄漏单测断言 filler 不进训练。 |
| ③ H_B 判定 | **H_B 成立 = 两个 Holm 校正主对比都为正且显著，且两点估计均 ≥δ_min=0.10**（AND 规则）；只赢一个 → `partial_decision_benefit`；都不成立 → `no_decision_benefit`；显著但低于 δ → `below_delta`（不称 H_B）；**主检验只在 primary 配置**。 |
| ④ 冻结全部模拟器旋钮 | O=20/M=10/universe=40/hash；σ primary 0.10；γ~N(0,τ²), τ=0.20；f 线性+剂量交互；θ 固定；证书阶梯/每 step 120s/min unit 120s；实验动作 anchored key 363.6 CU/34–68 wells；EV 精确枚举；R_max=5；500 primary+17×50 sensitivity；wall pilot 规则/单次≤45min/两跑≤90min。 |
| ⑤ 边界 | T1 批准仅限模拟器实现+资格门；不批结果/T2/T3；T2 描述+PEEK `B4CAD955…`；T3 `data_unavailable/cost_uncalibrated`；r primary=5（1/10 仅敏感性）。 |

## 1. 决策状态与成本（形式化）

- 状态 = (P, M_t, B_C [实测 CPU-second], B_E [整数 keys/wells/plates/rounds + A5 planning CU], A_compute∪A_experiment, π)。
- **合成总成本** `T=B_C+κ·B_E_CU`（T1 合成 κ；T2/T3 无报价→`cost_uncalibrated`，不作成本结论）。
- **primary 配置**：`B_C=1200s, B_E=16 anchored keys, κ=1 s/CU, σ=0.10`；`T=7017.6s`；experiment-only `n0=16+floor(1200/363.6)=19 keys`（6908.4 CU）+ blank/QC filler 109.2 CU；compute-only `B_C_eff=7017.6s`；dual 1200s+5817.6 CU + filler；三臂等 T。
- **决策单元**：独立 held-out cell/fold 菜单（一个 top-1 选择/unit）；primary 500 replicates = 500 decision units；technical wells/keys 不是 unit。
- **T3 key→CU**：r primary=5（1/10 敏感性）；393 units × r keys × 363.6 CU；r=5 → **714,474.0 CU**；T3 仍 data_unavailable/cost_uncalibrated。

## 2. 判据（T1 合成；T2/T3 不可用）

- T1 合成真实效用 `u∈[0,1]`、证书区间 `[h_in,h_out]`、`Δ_utility=0.10`、`headroom=oracle−static`、EV 精确枚举；`g_C=(h_out−h_in)/Δ_utility`。
- 唯一判定树（详见 DESIGN v0.3 §6）：无证书/效用 → `certificate_unavailable/blocked`；`g_C>1` 且 B_C 足→计算；**B_C 耗尽且 g_C>1 → `compute_budget_exceeded`（不买实验/不静默停）**；`g_C≤1` 决策唯一→`compute_sufficient`；否则 evidence-limited：headroom 未知→`oracle_unknown`；MDE>δ/power<0.8/headroom<Δ→`evaluation_cannot_distinguish`；否则买 EV/CU 最大实验；轮次耗尽→`unresolved`。
- T1 判据/合成效用不可外推；T2/T3 在 utility/证书冻结前不得下结论；T2 仅描述+PEEK，T3 cost/data 不可得。

## 3. Primary/MDE/δ（统一）

- **Primary = top-1 selection accuracy**（[0,1]），primary 500 decision units → `MDE80 = 2.801585×sqrt(0.5/500) = 0.088594 ≤ δ_min=0.10`（PASS）。
- δ_min=0.10 为操作性统计阈值；`blocked_by_utility_definition` 仅用于 secondary regret/EV/headroom 与真实世界价值主张。
- Secondary：top-k hit（k=5）/normalized regret/预测辅助；top-k/regret null/MDE 只在 T1 模拟器校准，不作主推断。

## 4. H_B（AND 规则，写死）

- 主检验只在 primary 配置：两主对比 `dual vs compute-only-filler`、`dual vs experiment-only-filler`；两对比 **Holm α=0.05**；配对 bootstrap CI。
- **H_B 成立 iff 两对比均为正且 Holm 显著，且两点估计均 ≥δ_min=0.10**。
- 只赢一个 → `partial_decision_benefit`；都不成立 → `no_decision_benefit`；显著但低于 δ → `below_delta`；敏感性配置只 `cost_sensitive`/描述，不得声称 H_B。
- best-single 只在 inner validation 选；测试集不 max；max 仅描述（同时 CI）。

## 5. 与 AL/BOED/COPEx/边界

- 一般概念（决策 AL/BOED/EVSI/ENBS/COPEx/约束生成/计算决策/GP）已被覆盖；本设计不主张新算法/首次双预算/预测分歧采样；差别仅限定具体共享对象（跨计划共同反事实/约束算子+计算认证状态）与更新运算（计算证书收紧+真实反馈统一修订）；同信息同预算普通方法等效 → 撤新意。
- T1 仅计算证据；T2 描述+PEEK；T3 data_unavailable/cost_uncalibrated；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；D1/D3/A1/C187 不重复；冻结≠资源足够/关系成立/Stage 1/效果。
