# report_B_v0_3 —— R201-B.2 修订报告（T1 冻结候选；**未运行**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。针对 `challenge_B_v0_2.md`（R201-B.2-C1，revise 5 必改，SHA `4D3A3AB5…`）提交 v0.3。**仅设计/算术；未运行 T1/T2/T3、未拟合、未读响应、无湿实验；不称新颖性/机制/迁移/决策收益。**

## 0. 交付

| 文件 | SHA256 |
|---|---|
| `PROBLEM_B_v0_3.md` | `753B9CF8BEA1CC8B2963F7F67D5622C710CE1F85D0631F035C777B6403C5F900` |
| `DESIGN_B_v0_3.md` | `183BE5DEA3FBCCE2B95C551C1D99B80FF25A75ADA29A28B9EC102B3A06AFF22C` |
| `design_B_revision_v0_3.py`（仅算术） | `AA49E4C8E3565FC59D7F8B732D59DFEBADACF4C618E4BC70C807172824A66D1C` |
| `design_B_v0_3.json` | `50E6EE30959CACD9894F799276BE907388189BCFF9B225DC7E6C68611E8A27D9` |
| `report_B_v0_3.md` / `record_B_v0_3.md` / `usage_B_v0_3.json` | 见各文件 |

## 1. 5 必改落实

### ① primary 配置与 500 replicate 归属（写死）
- **primary 配置**：`(B_C=1200s, B_E=16 integer keys), κ=1.0 s/CU, σ=0.10`。
- **primary 500 独立 replicate = 500 decision units**；seed=`20261130+replicate_id(0..499)`；**MDE=0.088594 ≤δ_min=0.10 PASS**；主 H_B 只用这 500。
- **敏感性**：其余 **17 格**（3 固定预算对 ×3κ×2σ=18 格减 primary），每格 **50 replicate**（共 850），seed=`20261131+cell_index*1000+r`；仅描述/`cost_sensitive`，不得用于 H_B/Holm。
- **网格统一**：固定预算对 `(300,4)/(1200,16)/(3600,64)`；κ∈{0.1,1,10}；σ∈{0.05,0.10}；不再有 B_C 网格不一致。

### ② 整数 key + 无信息 filler（可执行）
- 实验 key 必须**整数**；experiment-only：`n0=B_E+floor((B_C/κ)/363.6)` keys + `filler_CU=T−n0×363.6` 用 **blank/QC/已知标准品**填充（不进学习器/不更新模型/不产目标信息）；`|spend−T|≤1 well-equivalent`。
- compute-only：`B_C_eff=T`；compute filler=无信息随机计算步骤（不产证书/不更新模型）。
- dual 残余同法补齐；所有臂账本逐项报 compute s/key 数/CU/wells/plates/rounds/filler。
- **primary 例**：`T=7017.6s`；experiment-only **19 keys=6908.4 CU + blank/QC filler 109.2 CU**；compute-only 7017.6s；dual 1200s+5817.6 CU；无分数 key。
- **无泄漏断言**：filler 不进学习器/训练/模型更新/证书；blank/QC 不产目标 plan 响应；compute filler 不产证书；单测断言模型状态不变。

### ③ H_B 判定（AND；仅 primary）
- 两主对比：`Δ1=dual−compute-only-filler`、`Δ2=dual−experiment-only-filler`；Holm α=0.05；配对 bootstrap CI。
- **H_B 成立 iff Δ1、Δ2 均正且 Holm 显著，且两点估计均 ≥δ_min=0.10**。
- 只赢一个 → `partial_decision_benefit`；都不成立 → `no_decision_benefit`；显著但低于 δ → `below_delta`；敏感性配置只 `cost_sensitive`/描述，不得声称 H_B。
- best-single inner validation 选；测试集不 max；max 仅描述（同时 CI）。

### ④ T1 旋钮全冻结
- plan 宇宙 40；O=20；M=10；菜单 hash=SHA256(canonical metadata)，运行前冻结。
- σ primary 0.10、敏感性 0.05；`γ~N(0,τ²), τ=0.20`；`f=θ0+θ1x1+θ2x2+θ3x1x2+θ4dose`，θ 固定 `[0.5,0.3,0.2,0.1,-0.1]`。
- 证书阶梯：宽度 `[0.40,0.20,0.10,0.05,0.025]`，初始 0.40，每 step 成本 120s，min unit 120s；`Δ_utility=0.10`。
- 实验动作：每动作一个 anchored key（363.6 CU；34–68 wells；测一个 plan 响应）；EV 在固定离散世界网格精确枚举；`R_max=5`。
- seed：primary `20261130+r`；sensitivity `20261131+cell_index*1000+r`；两跑 JSON 逐字节一致；schema 每 replicate×arm 含 selection_accuracy/topk_hit/regret/chosen/oracle/成本账/compute_steps/experiments/filler/failure_class。
- 结果前**资格门**：oracle 可恢复/null FP≤α/成本账整数+filler/无泄漏/C0–C7 等价/两跑/schema/wall/菜单 hash/seed 复现；任一 fail→`design_invalid`，不报结果。

### ⑤ 边界一致
- **T1 批准仅限模拟器实现 + 资格门**；不批结果/T2/T3。
- T2 描述+PEEK `B4CAD955…`（ON3 non-blind/peeked）；n=6/30 不作主检验。
- T3 `data_unavailable/cost_uncalibrated`；**r primary=5**（T3 393 units×5 keys×363.6=**714,474.0 CU**），r=1/10 仅敏感性；不执行。
- 不称新颖性/机制/迁移/决策收益/资源足够/独立确认；D1/D3/A1/C187 不重复；冻结≠资源足够/关系成立/Stage 1/效果。

## 2. T1 Wall/预算（冻结规则）

- primary arm-runs **500×8=4,000**；sensitivity **17×50×8=6,800**；总 **10,800** arm-runs。
- pilot：先跑 10 个 primary replicate 只计时（不读结果）外推；**单次 T1 ≤45 min、两跑 ≤90 min**（CPU-only）。
- **fallback 写死**：pilot 外推 primary-only >45min → `design_invalid: compute_budget_exceeded`，不报结果；若总计 >45min 但 primary ≤45min → 只跑 primary、跳过敏感性（不报敏感性结论）；**不得减少 primary 500/configs**。

## 3. 建议

- 可提交 **approve_mvp_to_lead（仅 T1 模拟器实现+资格门）**；建议先由独立挑战者做一次只读确认（primary 配置/500、整数 key/filler、H_B AND、冻结旋钮/wall、T2/T3 边界），再由 Lead 批准实现+资格门；**不批准 T2/T3 执行、不批准任何结果/决策收益/迁移/机制/新颖性主张**。
- T1 只作计算证据；若资格门失败→`design_invalid`，不报 selection accuracy/top-k/regret。
