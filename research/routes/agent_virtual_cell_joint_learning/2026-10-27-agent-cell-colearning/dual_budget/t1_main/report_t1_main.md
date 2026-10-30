# report_t1_main —— R201-B 主 T1 合成模拟器执行报告（**仅计算证据**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 Lead `DECISION_R201_T1_MAIN.md`（SHA `19719E25…`；批准主 T1 执行一次，仅计算证据）。**本报告只报告合成模拟器结果；未读 O'Neil/Validation 真实响应、未运行 T2/T3、无湿实验；不称新颖性/机制/迁移/决策收益/独立确认；不得外推生物/药物决策；冻结≠资源足够/关系成立/Stage 1/效果。**

## 0. 判定（一屏）

- **主 T1 一次执行完成；H_B 判定 = `partial_decision_benefit`（未支持 H_B）。**
- 两主对比（primary 500 decision units，paired；Holm α=0.05）：
  - `dual vs C7_compute_only`：点估计 **+0.022**，CI95 **[0.006, 0.040]**，Holm p=**0.01117**（显著为正，但 **<δ_min=0.10**）。
  - `dual vs C7_experiment_only`：点估计 **+0.010**，CI95 **[−0.006, 0.026]**，Holm p=**0.11252**（不显著）。
  - 两 Holm 对比并非都为正且显著；两点估计均未达 δ=0.10 → **`partial_decision_benefit`**（按预注册：只赢一个/未达 δ 的分类；**不写"双预算无效"**）。
- 两跑 `t1_main.json` **逐字节一致** SHA256 **`58E290A7935472F9B34B856CE832BC2B822E24B37431F9E55843E654B95ADB05`**。
- 实测 wall：run1 **974.96 s**、run2 **956.73 s**（约 16.25/15.95 min；≤45min；两跑合计 ≤90min）。
- 资格门快检：与 T1-MVP 一致，**全部 PASS**、无偏差；主执行未改冻结旋钮。

## 1. 执行事实（冻结 primary）

- primary：`(B_C=1200s, B_E=16 integer keys), κ=1.0, σ=0.10`；500 独立 replicate=500 decision units。
- 10 arms：`π_dual`、C0–C6、C7_compute_only、C7_experiment_only；同 learner/update/信息/调参/seed。
- primary arm-runs 5,000；敏感性 17 格×50 replicate×10 arms=8,500（仅描述/cost_sensitive）；总 13,500。
- 未读真实响应；未运行 T2/T3；未做湿实验。

## 2. H_B 统计（预注册 AND 规则）

| 对比 | n | 点估计 | 95% CI | Holm p | 显著正 | ≥δ=0.10 |
|---|---|---|---|---|---|---|
| dual − C7_compute_only | 500 | **+0.022** | [0.006, 0.040] | **0.01117** | 是 | 否 |
| dual − C7_experiment_only | 500 | **+0.010** | [−0.006, 0.026] | 0.11252 | 否 | 否 |

- H_B 成立条件（预注册）：两对比均正且 Holm 显著且两点估计均≥δ=0.10；**未满足**（一显著但<δ，一不显著）→ `partial_decision_benefit`。
- 只作合成计算证据；不将 `partial` 解释为结构/药物决策结论。

## 3. Per-arm 描述（primary，500 units）

| arm | mean selection accuracy |
|---|---:|
| π_dual | **0.912** |
| C0 | 0.906 |
| C1 | 0.906 |
| C2 | 0.890 |
| C3 | 0.878 |
| C4 | 0.878 |
| C5 | 0.878 |
| C6 | 0.888 |
| C7_compute_only | 0.890 |
| C7_experiment_only | 0.902 |

- 仅描述；未对非主对比做显著性/选择；不选最佳 arm/不换主终点。
- per-replicate 行见 `t1_main_rows.csv`（5,000 行：selection_accuracy/topk_hit/normalized_regret/chosen/oracle/cost ledger/compute_steps/experiments/filler/failure_class）。

## 4. 敏感性（17 格×50，仅描述/cost_sensitive）

- 17 个非 primary 配置（3 预算对×3κ×2σ）：每格 50 replicate；**不用于 H_B/Holm**；仅描述表在 `t1_main.json.sensitivity`。
- `dual−C7_compute_only` 每格均值范围 **−0.04…+0.04**；`dual−C7_experiment_only` 同范围 **−0.04…+0.04**；配置间差异仅描述，不作主推断、不选赢家。
- 若 wall 不允许则按 fallback 跳过；本次 wall 允许（总 wall ~16min≤45min），已执行敏感性。

## 5. 资格门快检/墙/两跑

- 资格门快检（与 T1-MVP 一致）：oracle/null FP/EV 近似/成本账/无泄漏/10 arms/menu hash 全 PASS；无偏差。
- wall：run1 974.96s（qual gates quick 70.65s + primary 348.46s + sensitivity 555.67s）；run2 956.73s（68.39+337.90+550.25）；均≤45min；两跑≤90min；未触发 fallback。
- **两跑 `t1_main.json` 逐字节一致**；`t1_main_rows.csv` 亦逐字节一致；timing 文件因 wall 不同属预期。

## 6. 产出 SHA

| 文件 | SHA256 |
|---|---|
| `run_t1_main.py` | `F805AA3EDD5CE8C07978D437DBB020F757FC2C2D50AE19579E84CC1E75A351F7` |
| `t1_main.json`（两跑一致） | `58E290A7935472F9B34B856CE832BC2B822E24B37431F9E55843E654B95ADB05` |
| `t1_main_rows.csv` | `2A227AB0EFE97603D4AB9A0DB003DCCF73067C7B82DC6862C5A90A41D267369F` |
| `timing_main.json`（run2 最后写入；run1 wall 见 report/record） | `A5A816FBB9E2AA25F0CE9566DEC166D7628E3D17BB04FB3C8A347C6958A6232C` |
| `report_t1_main.md` / `record_t1_main.md` / `usage_t1_main.json` | 见各文件 |

## 7. 边界（随报告引用）

- **仅合成计算证据**；不称新颖性/机制/迁移/决策收益/独立确认；不得外推 O'Neil/生物/药物决策；T2/T3 未执行；真实响应未读；湿实验未做。
- H_B 不成立按预注册写 `partial_decision_benefit`；**不写"双预算无效"**；不写结构成立/不存在。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；技术重复≠独立培养。
