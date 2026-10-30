# report_n1_effect —— R203-N1 效果执行报告（合成机制账；**verdict = no_increment**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 Lead `DECISION_R203_N1_EXEC.md`（SHA `930F1567…`）与冻结执行预注册（PROBLEM/DESIGN `9993F0BA…`/`29F784E7…`、exec_plan `843DEC39…`/`BECEE7F8…`）。**仅合成机制账、compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；无 T2/T3/真实响应/湿实验。**

## 0. 判定（一屏）

- **执行完成；verdict = `no_increment`；failure_category = `no_increment`。**
- 预注册 primary `D=R(M)−R(B2)`（lower better；正值为不利）：mean **+0.00605165**，95% CI **[0.00328402, 0.00881927]**，Holm p **0.00017858**（显著，但方向为正/非改善）。
- 成功判据（mean≤−.05 ∧ CI upper<0 ∧ Holm p<.05）**未满足**：均值未达 −δ、CI upper>0 → 按预注册 `no_increment`（**不称"双预算/方法无效"**，只表示本预注册 primary 未显示增量）。
- headroom 预检：U0(B2)=**0.337630279**、headroom **0.662369721≥δ=.05**（PASS，非 ceiling）；actual cluster-robust MDE **0.00385839≤.05**（precision PASS）；保守 MDE .04798268 并列。
- **两跑 `n1_effect.json` 逐字节一致** SHA256 **`CAAC6718E002EA1C97D1F179B0B284BA0639479E8C3FA2FBFDEF3326E24D7044`**。
- 执行前链核验 PASS；pilot/G7 PASS；B2 等价审计 PASS；0 wells。

## 1. 执行事实

- 冻结：primary `D=R(M)−R(B2)`，δ=.05；family=6（M vs B1–B6）Holm α=.05；n_units=300 × R=50 = **15,000 paired decision units**；T=6（fit 4/hold 2）；每轮 1 feedback；M vs B1–B6；同 prior/初始/特征/query/调参≤20；只读导入冻结 generator `AA5D454A…`。
- 执行 seeds：dataset **20261070–20261119**；method seeds **20262000+r*10+idx**；未复用 gate seeds。
- 链核验：v0.4 7 文件 + C204 8 文件 SHA、V4 spec `A69B845D…`、V4 独立 gate 数字、G1/G2/G3/G7 数值均匹配（PASS）。
- pilot/G7（最终 effect runner，2 reps×20 units×7 methods）：per-rep **~0.69–0.76 s**、projected main **~313–342 s**、mem **~0.036 GB**；caps 1800 s/2 h/8 GB/0 wells PASS；B2 等价审计 PASS。
- headroom：20 reps×300 units（seeds 20261130–20261149），U0(B2)=**0.337630279**、U_max=1、headroom=**0.662369721≥δ**；`near_ceiling=false`；仅预检、不当效果端点。

## 2. Primary/Secondary 统计（pre-registered；no algorithm claim）

| comparison | mean ΔR（M−baseline；lower better） | 95% CI（cluster G=50, t₄₉） | Holm p |
|---|---:|---|---:|
| **M vs B2（primary）** | **+0.00605165** | **[0.00328402, 0.00881927]** | **0.00017858** |
| M vs B1_full_retrain | +0.00605165 | [0.00328402, 0.00881927] | 0.00017858 |
| M vs B3_hierarchical_EB | +0.00630875 | [0.00368340, 0.00893411] | 0.00005547 |
| M vs B4_GP | +0.00652235 | [0.00112936, 0.01191533] | 0.01878933 |
| M vs B5_random_plan_pair | +0.15819377 | [0.13803767, 0.17834987] | 0.0 |
| M vs B6_decision_AL | +0.16286624 | [0.13657104, 0.18916144] | 0.0 |

- Primary success=false；mean 未≤−δ、CI upper>0；按预注册 `no_increment`。**不据此宣称 M 有效/无效、不称双预算无效**。
- **实现备注（frozen generator）**：B1 `FullRetrain` 与 B2 `StaticAdd` 在冻结 generator 中共享同一静态 fit 实现（`FullRetrain(StaticAdd)` 未覆写 fit）；本执行**未修改冻结代码**，故两者估计相同；属冻结实现细节，不是执行时改动。
- 分析单位：15,000 paired units；cluster-robust SE 按 replicate（G=50）、t₄₉；primary mean/CI/Holm p 如上；secondary 仅预注册 family 报告，不作算法主张。

## 3. 两跑/预算/链核验

- **两跑**（同 seeds、独立进程）：`n1_effect.json` 逐字节一致 SHA **`CAAC6718E002EA1C97D1F179B0B284BA0639479E8C3FA2FBFDEF3326E24D7044`**；rows 亦一致；telemetry 只在 `timing_n1_effect.json`。
- wall（run1/run2）：pilot **0.97/1.03 s**、headroom **11.26/10.05 s**、main **440.38/418.57 s**、total **454.31/431.51 s**；CPU **433.5/413.6 s**；mem **0.09737/0.09733 GB**；caps 1800 s/2 h/8 GB PASS；无 `compute_budget_exceeded`。
- headroom PASS；actual MDE≤δ；无 `precision_insufficient`；无 `chain_mismatch`/`schema_mismatch`/`two_run_mismatch`/`leakage`/`generator_misspecified`/`calibration_failed`/`nonidentifiable`。

## 4. 失败类别/解释边界

- `failure_category = no_increment`（预注册分类）：primary CI 在非改善侧排除 −δ 且无 secondary 支持；**不表示算法/机制不存在**，不称"双预算/方法无效"；仅表示本合成机制账的预注册 primary 未显示增量。
- 仅合成机制证据（generator/GT/合成 regret）；**不外推药理、真实决策、迁移、机制、新颖性**；不晋升代码；不改旧门槛/判定；0 wells；未用 A/B 资源；T2/T3 未执行。

## 5. 产出 SHA

| 文件 | SHA256 |
|---|---|
| `run_n1_effect.py` | `4698E7452258D6BF51E003385BF37E02A8C1FC8A517735689F0AA9F79BC11B7B` |
| `n1_effect.json`（两跑一致） | `CAAC6718E002EA1C97D1F179B0B284BA0639479E8C3FA2FBFDEF3326E24D7044` |
| `n1_effect_rows.csv` | `60EA6BA7A227C3BEC7CFB75AA341ABD2BC1F36EC9233A2CAAF67E6DFF3D995FE` |
| `n1_effect_summary.json` | `342713DA9E7E6DE75DD43E5AB8CED4A8490BA11769C8B9E2BA7D6310507CA651` |
| `headroom_precheck.json` | `EC42006F3AA3990AA9C2D219A66888DDF4C70B7654FFBEAA38A951263551F7B2` |
| `timing_n1_effect.json` | `5089B4E9DB6320313CAFA5D495FF732713DD94671E18352EE7C22E4C891A55EF` |
| `schema_n1_effect.json` | 见文件 |
| `report_n1_effect.md` / `record_n1_effect.md` / `usage_n1_effect.json` | 见各文件 |

## 6. 结论边界（写死）

仅合成机制证据；**不称药理/真实决策/迁移/机制/新颖性**；`no_increment` 仅为本预注册 primary 的判定，不推广为"方法/双预算无效"；技术重复≠独立培养；冻结≠资源足够/关系成立/Stage 1/效果；N1 后续执行须另立预注册+独立挑战+Lead 批准。
