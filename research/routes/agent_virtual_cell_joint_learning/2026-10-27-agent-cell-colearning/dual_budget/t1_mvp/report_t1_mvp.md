# report_t1_mvp —— R201-B T1 合成模拟器实现 + 资格门报告（**仅资格门，未跑主结果**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 Lead `DECISION_R201_T1_MVP.md`（approve_mvp_to_lead：仅 T1 实现+资格门）。**本报告只报告实现与资格门；未运行 T1 主 500 replicate 结果、未运行 T2/T3、未读 O'Neil/Validation 真实响应、无湿实验；不称新颖性/机制/迁移/决策收益/独立确认。**

## 0. 判定

**T1 模拟器实现完成；资格门全部 PASS；`verdict = qualification_pass`。**
- 资格门（9 项）全 PASS：oracle 可恢复、null FP、EV 离散参考一致性、18 格全臂成本账、filler 不进学习器、无泄漏、10 arms、menu hash、schema、wall。
- **pilot 仅计时**：10 replicate×10 arms=100 arm-runs，wall **6.97 s**；外推 primary 5,000 arm-runs ≈ **5.81 min**（≤45min），两跑 ≤90min；满足 wall 门。
- **两跑 `t1_qualify.json` 逐字节一致**：SHA256 **`A50A1E96797A247618EFFF89B232461E2F5749F368E817DCCCF31418A0BA9203`**。
- **未跑主 500 replicate 结果**；是否具备执行主 T1 的条件仅作建议，需 Lead 另批。

## 1. 交付

| 文件 | SHA256 |
|---|---|
| `t1_sim.py`（模拟器实现；无真实响应读取） | `A09CAE8923AD98FB8DFDFDFAFBA1C8BB82B6084041CC4E12F6C729DE00372930` |
| `t1_qualification.py`（资格门脚本） | `A7202348C0AD83D6E3B6D1C6B46F73A32A225A2986C842AE5FA0DCE6FBE54381` |
| `t1_qualify.json`（资格门输出；两跑一致） | `A50A1E96797A247618EFFF89B232461E2F5749F368E817DCCCF31418A0BA9203` |
| `timing_pilot.json`（pilot 计时） | `41EA27D464D9734F2A3260AC316BB7DF5E3CFE8DAA56F434CB3EE1218F08A856` |
| `schema_t1_qualify.json` | 本 schema；见文件 |
| `report_t1_mvp.md` / `record_t1_mvp.md` / `usage_t1_mvp.json` | 见各文件 |

## 2. 实现范围（按 v0.4 冻结，未改旋钮）

- 40-plan 宇宙；x1/x2/dose 表按 v0.4 公式；O=20、M=10、reserve=10；菜单 hash=SHA256(canonical metadata)。
- θ 固定 `[0.5,0.3,0.2,0.1,−0.1]`；γ 5 点/组（值 `{-0.4,−0.2,0,0.2,0.4}`，权重 `[0.054488685,0.244201342,0.402619947,0.244201342,0.054488685]`；3 组→125 worlds）；σ=0.10 五点噪声网格。
- 证书阶梯 `[0.40,0.20,0.10,0.05,0.025]`、每 step 120s、min unit 120s；R_max=5；实验动作 anchored key 363.6 CU；EV **有限离散近似**（非精确；125 gamma worlds + 5 点噪声参考）。
- **10 arms**：`π_dual`、C0–C6、C7_compute_only、C7_experiment_only；同 learner/update/信息/调参/seed；C7 两臂分别输出。
- 成本：合成总成本 `T_seconds=B_C+κ·B_E_CU`、`T_CU=B_E_CU+B_C/κ`；整数 key + **1 CU/blank/QC well** filler（合成价格假设；非物理 A5 5.3–10.7 CU/well；若用 A5 价会超 T，须重算，未用）。
- Filler 无信息：blank/QC/已知标准品不进学习器/训练/模型更新/证书；compute filler 不产证书；单测断言模型状态 hash 不变。

## 3. 资格门结果（逐项）

| 门 | 结果 |
|---|---|
| **oracle 可恢复** | **PASS**：20 个测试世界；无噪声 all-40-plan latent learner（无限计算/数据极限）恢复 latent oracle top-1；仅评估用。注：clipped 响应的 top 可能有并列，门用 latent 真值；不用于结果。 |
| **null FP** | **PASS**：100 个 null 世界（γ=0），π_dual vs C7 两臂；H_B 未被支持（`H_B_false_positive=false`；p1=p2=0.5，mean diff=0）；只作 gate，不报主结果。 |
| **EV 近似门** | **PASS**：5 个动作；approx（零噪声）vs 5 点噪声参考的 max |Δ| = **1.998e-15 ≤0.02**；**声明为"离散参考一致性门"，非连续真误差、非 EV exact**。 |
| **成本账（18 格全臂）** | **PASS**：18 格 negative filler=0、outside tolerance=0；all 10 arms spend diff≤1；primary 例 residual 109.2/filler 110 wells/diff 0.8；filler 不改变 learner state hash=true。 |
| **无泄漏** | **PASS**：特征 5 列（无 γ/响应）；训练仅 O；M 不在训练；oracle 仅评估；10 arms 同信息。 |
| **10 arms** | **PASS**：10 arms 唯一、同 learner/update；无 arm-specific 数据/模型/调参。 |
| **menu hash/seed** | **PASS**：menu hash 两次一致；seed 表可复现。 |
| **schema** | **PASS**：required keys 完整；schema 文件 `schema_t1_qualify.json`；无 forbidden result keys。 |
| **wall** | **PASS**：pilot 100 arm-runs wall 6.97 s；外推 primary≈5.81min ≤45min；两跑 ≤90min；pilot 只看时间、不读结果。 |

## 4. 两跑/确定性

- `t1_qualify.json` 两次运行 **逐字节一致**（SHA `A50A1E96…`）；无时间戳；wall 只在 `timing_pilot.json`（两跑计时不同属预期）。
- 两次运行均 `qualification_pass`；未运行主 500 replicate 结果。

## 5. 实现备注/限制

- **filler 价格假设**：现在按合成 1 CU/blank/QC well 计价；Lead 备注要求标注。物理 A5 assay well≈5.3–10.7 CU/well 会使 experiment-only 超 T；本实现**未采用** A5 价，仅合成 planning；若改用 A5 价须重算并披露。
- **EV 门**：是有限离散参考一致性门（approx zero-noise vs 5-point noise-grid），**不是连续真误差/不是 EV exact**；更高分辨率/解析参考未做。
- **σ**：primary σ=0.10 五点网格；敏感性 σ=0.05 的对应五点网格未在本次资格门中运行（敏感性只作描述，不用于 H_B）。
- 资格门通过≠执行主 T1；主 500 replicate、H_B、决策收益等**未运行**；T2/T3 未运行；真实响应未读；不称新颖性/机制/迁移/决策收益/独立确认。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；技术重复≠独立培养；O'Neil 限制不变。

## 6. 建议

- **T1 实现+资格门通过**；若 Lead 决定执行主 T1（500 replicate、10 arms、H_B AND），需另批；当前实现/门可复用，wall 预计 primary≈5.8min、两跑≤90min（pilot 外推，非承诺）。
- 不申请 T2/T3 执行；不申请任何结果解释。
