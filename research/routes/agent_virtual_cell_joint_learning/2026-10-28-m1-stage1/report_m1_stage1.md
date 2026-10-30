# report_m1_stage1 —— R204-M1 Stage 1 合成检查报告（机制账；不报效果）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者（endpoint-auditor）。
**状态：Stage 1 合成检查完成；仅机制账、compute-only、0 wells；不报效果/增益/方法比较；Stage2/3 未执行；不称药理/真实决策/迁移/机制/新颖性。**

依据：Lead `DECISION_R204_M1_STAGE1.md`；冻结 v0.2 链 `PROBLEM_M1_v0_2` `18A7FC9F…`、`DESIGN_M1_v0_2` `11FACB26…`、`formalism_M1_v0_2.py` `5B843FA9…`、`formalism_M1_v0_2.json` `B7298653…`、`stage1_m1_schema_v0_2` `8FF66514…`、timing `72870EF9…`。

## 1. 链核验

- 执行前逐一实算 v0.2 链 SHA：**全部 match**；`chain_ok=True`；无 `design_invalid: chain_mismatch`。
- 本实现只读引用 `formalism_M1_v0_2.py` 中反例/投影/支持/Doob 算术；**未改 M1 预注册/M2/N1/A-B-D/旧门槛/旧判定/代码**。

## 2. 生成器/形式化实现

- 冻结生成器：X=4（0..3）、A=3、Y=4（0..3）；每个 (x,a) `logits~Normal(0,.6²)`，softmax；generator seed **20261112**；eval seed **20261113**；`r(y)=y`；τ=1；π0 full `[1/3,1/3,1/3]`、constrained `[.5,.5,0]`。
- 实现 `Pθ`、`Q_g∝π0 Pθ exp(r/τ)`、`Rπ=πPθ`、`π*∝π0 exp(E_P[r]/τ)`；先期望后动作；目标样本不作标签；Doob 不可执行。
- 检查性诊断复现：
  - 反例 A/B：target Q 动作 A **0.99665795**、B **0.00334205**；E_A=1<E_B=2；π*_B **0.73105858**；仅证风险。
  - 投影：`KL(Rπ*||Q_g)=0.24038053 < KL(uniform)=0.45067680`；可执行条件核差 **1.11e-16**；target joint within-action tilt **0.43647** 标为**不可执行 proposal**。
  - 支持：π0_3=0 → π*=0；Doob 核非药物。

## 3. S1-a–e（PASS）

| 检查 | 结果 | 阈值 |
|---|---|---|
| S1-a target 动作 TV（full/constrained） | **0.00545039 / 0.00156330** | ≤.02（20k/x） PASS |
| S1-b max TV 条件核（Pθ） | **0.00902615** | ≤.02（20k/condition） PASS |
| S1-c 可执行条件核差 / 标签 | **0.0** / target 样本不作标签 | ≤1e-12 PASS |
| S1-d 支持 | full 全支持；constrained action2 π*=0 | exact PASS |
| S1-e π* KL gap（解析最优；grid 诊断） | **0.0 / 0.0**；π*<legal-uniform | ≤1e-8 PASS |

**S1-e 说明**：grid step .001 为诊断；以**解析闭式 π*** 作为精确最优参照（任务允许“提高 grid/解析最优”），未放宽阈值；全/constrained 均 π*<legal-uniform。**S1-a/b 采样误差在预注册容差内。**

## 4. B1–B5 规格复核（仅检查性；不报效果/方法差异）

| 项 | 检查结果 |
|---|---|
| **B1 random MPC** | 0 configs、20,000 actions、uniform legal；规格 PASS |
| **B2 max-entropy** | `max_abs_diff_vs_pi_star=0.0`；**`rename_maxent_detected=true`**；**不写 M1 增量** |
| **B3 conditional MC** | N=20k/动作；max SE **0.00836378**≤.02；TV to π* **0.00358422**≤.02；规格 PASS |
| **B4 constrained SB** | one-step entropic OT/Sinkhorn；row marginal error max **1.54e-13**；target outcome error max **1.11e-16**；constraints PASS |
| **B5 same-info DF** | ≤20 configs、同 cap/生成量；仅规格登记，**未执行方法比较** |

**B2 结论**：解析等价于 π*，属 `rename_maxent` 检出；**Stage1 不写 M1 算法增量**，不将等价写成效果。

## 5. G1–G6（Stage1 门）

| 门 | 状态 | 说明/失败类别 |
|---|---|---|
| **G1** 条件药效保持 | **PASS** | 条件核差 0；target 样本不作标签；失败=calibration |
| **G2** 支持/程序 | **PASS** | full/constrained support exact；失败=support |
| **G3** 投影/近似 | **PASS** | π* KL gap 0；S1-a/b 在容差内；失败=projection |
| **G4** 无泄漏 | **PASS** | target 样本/plan 不作标签；无 holdout/未来时点泄漏；失败=leakage |
| **G5** 两跑 | **PASS（外部核验）** | 两个独立进程 result JSON 逐字节；失败=two_run_mismatch |
| **G6** schema/预算 | **PASS** | schema 先写；full wall 21.323 s≤1800；0 wells；失败=compute_budget_exceeded |

**无 `design_invalid`；无失败门。**

## 6. 两跑/预算/timing

- 两独立进程（run1/run2）：`m1_stage1.json` **逐字节一致 `EF701C66BFEF12E518D40F1D897C4045EBB0B76FFAE9FE24375052B1382EEAFF`**；rows/diagnostics/schema 亦一致；timing 单独。
- pilot：10 reps **2.1e-05 s/rep**；projection arithmetic projected **0.0209 s**；full Stage1 wall **21.323 s**；caps **1800 s/2 h/8 GB**；**0 wells**；实际远低。
- schema/failure template 先写（`schema_m1_stage1.json`）；JSON 无 telemetry；未输出 decision utility/regret/方法比较/top-k。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `m1_stage1.json`（两跑一致） | `EF701C66BFEF12E518D40F1D897C4045EBB0B76FFAE9FE24375052B1382EEAFF` |
| `m1_stage1_rows.csv` | `3A6536F50DD5BE6971EEF83B9445D8D168BE308CD1797981BEDB5D3464AA2728` |
| `m1_stage1_diagnostics.json` | `998406D10D8F34E13FCDCA03FBE32F7BCE9DF4D92414325C22402510639E7B10` |
| `schema_m1_stage1.json` | `D5B84C483B185677D1E0F7D3A5BB30ACA9247DA9C96993AE85DBE0DD44036F3C` |
| `timing_m1_stage1.json` | 见文件；result SHA `EF701C66…` |
| `run_m1_stage1.py` / report / record / usage | 见 usage |

## 8. Stage2 建议/边界

- **Stage1 合成检查通过**；仅机制账/检查性，不构成效果/药理/真实决策/迁移/新颖性证据。
- **Stage2 设计条件（仅建议）**：可开始准备高维近似设计；但真实功能数据当前 **data_unavailable（C203）**，Stage2/3 不执行；需另立预注册+独立挑战+Lead 批准；不得用合成/RNA/预测替代独立功能决策。
- B2 等价已检出 `rename_maxent`；任何后续算法主张必须与 B1–B5 等预算比较，且不能把 B2 等价写成 M1 增量。
- 边界：不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养；N1 `no_increment` 仅其 own primary，不作 M1 证据。
