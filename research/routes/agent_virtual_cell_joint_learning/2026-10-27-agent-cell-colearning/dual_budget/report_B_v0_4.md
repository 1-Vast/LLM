# report_B_v0_4 —— R201-B.3 修订报告（T1 冻结候选；**未运行**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。针对 `challenge_B_v0_3.md`（R201-B.3-C1，revise 5 必改，SHA `9B6F4438…`）提交 v0.4。**仅设计/算术；未运行 T1/T2/T3、未拟合、未读响应、无湿实验；不称新颖性/机制/迁移/决策收益。**

## 0. 交付

| 文件 | SHA256 |
|---|---|
| `PROBLEM_B_v0_4.md` | `D6B37E704DE141FE481A73D4BDDC0FFA6CBB0BA7FA6A686004D568415E6C5C99` |
| `DESIGN_B_v0_4.md` | `9112EDDC3180BA6101DF76CB34282BE84E7E9DF0EBD3EC714C4999388E7D01CD` |
| `design_B_revision_v0_4.py`（仅算术） | `E4968C701DB031BF246767D821A31DC5B8EF9AB50D3A0694462E023F661A3A5E` |
| `design_B_v0_4.json` | `A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1` |
| `report_B_v0_4.md` / `record_B_v0_4.md` / `usage_B_v0_4.json` | 见各文件 |

## 1. 5 必改落实

### ① filler 单位/公式（已修）
- 正确公式：**`blank_QC_filler_CU = (B_E_CU + B_C/κ) − n0×363.6`**（不是 `T_seconds−keys_CU`）；filler 用整数 blank/QC wells=`ceil(residual_CU)`。
- **18 格全部重算**（3 预算对×3κ×2σ）：`residual_CU∈[0,363.6)`；**negative filler=0**；`rows_outside_tolerance=0`；`all_pass=true`。
- primary 例：T_CU=7017.6；n0=19 keys=6908.4 CU；**residual 109.2 CU**；filler 110 wells；spend 7018.4；diff **0.8 CU≤1**。
- κ=0.1 例（300s,4 keys）：T_CU=4454.4；n0=12 keys=4363.2；**residual 91.2 CU**（v0.3 曾误为 −3917.76）；filler 92 wells；diff 0.8。
- blank/QC/已知标准品 filler 不进入学习器/训练/模型更新/证书；compute filler 不产证书；无泄漏单测断言模型状态不变。

### ② arm-run 计数（已修）
- T1 **10 arms/replicate**：`π_dual` + C0–C6（7）+ **C7_compute_only** + **C7_experiment_only**；同 update/信息/调参/seed，C7 两臂分别输出。
- primary **500×10=5,000** arm-runs；sensitivity **17×50×10=8,500**；total **13,500**；pilot **10×10=100** arm-runs（只计时）。
- wall：单次≤45min、两跑≤90min；fallback：pilot 外推 primary >45min→`design_invalid: compute_budget_exceeded`；总计 >45min 但 primary ≤45min→只跑 primary、跳过敏感性；不得减少 primary 500/10 arms/configs。
- report/JSON `wall_budget` 已同步（不再用 8 arms）。

### ③ x1/x2 + EV 网格（已冻结）
- 40-plan 宇宙：`cell_u=p//10`；`j=p%10`；`x1=(j%3)−1`；`x2=((j//3)%3)−1`；`dose=0.5 if j<5 else 1.0`；split：p<20 O、20≤p<30 M、p≥30 reserve；完整 40 行表在 JSON `x_mapping.plan_table`；菜单 M hash=SHA256(canonical metadata)。
- θ 固定 `[0.5,0.3,0.2,0.1,−0.1]`；`f=θ0+θ1x1+θ2x2+θ3x1x2+θ4·dose`；γ_g~N(0,τ²), τ=0.20（x2 groups 3）。
- **EV 有限离散近似（不再称精确）**：γ 网格 5 点/组 `{-0.4,−0.2,0,0.2,0.4}`，权重 `[0.054488685,0.244201342,0.402619947,0.244201342,0.054488685]`，3 组→**125 worlds**；噪声网格 σ=0.10 五点；EV 在 125 worlds 上按权重期望，动作排序用零均值期望效用，观测加 Gaussian ε。
- **误差门**：EV_approx vs 5-point noise-grid EV 的 max selection-accuracy difference **≤0.02**；超过→`design_invalid: EV_approximation_error`，不报结果。

### ④ 全臂 spend 校验
- 18 格每格：compute-only `spend_seconds=T_seconds` 精确；experiment-only 整数 keys + filler 后 `|spend_CU−T_CU|≤1`；dual 残余 filler 补 T；表见 JSON `equal_cost.rows` / `spend_validation`。
- primary：residual 109.2 CU / filler 110 wells / diff 0.8；κ=0.1：91.2 / 92 / 0.8；全部 18 格 pass；无负 filler。

### ⑤ 边界同步
- T1 批准仅限 **模拟器实现+资格门**；不批结果/T2/T3。
- T2 描述+PEEK `B4CAD955…`（ON3 non-blind/peeked）；T3 `data_unavailable/cost_uncalibrated`；**r primary=5**（T3 393×5×363.6=714,474.0 CU）。
- H_B AND（两 Holm 对比均正且显著且≥δ=0.10；只赢一个=partial；无=no_decision_benefit；显著低于 δ=below_delta）；主检验仅 primary；best-single 仅 inner validation；测试集不 max。
- 不称新颖性/机制/迁移/决策收益/资源足够/独立确认；D1/D3/A1/C187 不重复；冻结≠资源足够/关系成立/Stage 1/效果。

## 2. 建议

- 可提交 **approve_mvp_to_lead（仅 T1 模拟器实现+资格门）**；建议先由独立挑战者做一次只读确认（filler 18 行、10 arms/wall、x1x2/EV 网格、全臂 spend、T2/T3 边界），再由 Lead 批准实现+资格门。
- 资格门先于结果；失败只 `design_invalid`，不报 selection accuracy/top-k/regret；T1 仅计算证据，不外推真实决策收益。
