# PROBLEM_N1_EXEC —— R203-N1 效果执行预注册草案（机制账；不运行效果）

2026-10-28。对象：R203-N1 效果执行（M vs B1–B6 的 held-out decision regret 比较）。依据：`DECISION_R203_N1_PREREG.md`（仅批准执行预注册，不批效果执行）、C204（`2026-10-28-n1-implementation/`，`qualification_pass`）、N1 v0.4 预注册链、R203-P1 链、ERRATA（C197/C199/C201/C203）。
**状态：预注册草案；未运行任何效果比较、未报告方法差异、未读真实/响应数据；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；0 wells/compute-only。任何效果执行须另立独立挑战 + Lead 批准。**

## 0. 执行前必核（任何不匹配 → stop）

**已完成本地核验**（`exec_plan.py`，结果在 `exec_plan.json → pre_execution_chain`，chain_pass=true / full_pass=true）：

| 链 | 文件/SHA |
|---|---|
| N1 v0.4 | PROBLEM `5C513D94…FA0649A`；DESIGN `94BAB805…7C029C`；generator py `AA5D454A…EDCC97`；generator json `35E41136…D610263`；V4_validation `254BEBAB…DC8E2ECF`；pilot `A4C7E0F6…5586C7`；DECISION_R203_N1_PREREG `930F1567…C174AD` |
| C204 实现/资格 | run_n1_gates.py `D2AA831F…B276D7B8`；n1_gates.json **`529C1D2E…6CBA0E0`**（G5 两跑一致）；rows `78457E1F…B587F6EB`；timing_n1_gates.json `5A52E42F…7F75AC`；schema `F2D561D9…C5AB1D`；report `38CFD34C…E682CAF5`；record `DA21E2D9…CDCA7680`；usage `F795C15D…322B4DD7` |
| **V4_MODEL_SPEC** | SHA **`A69B845D…BF3289`**（static ridge 21 特征 λ=1e-2；nonstatic 33 特征、soft responsibilities、weighted ridge λ=1.0、forward posterior、init 1/S、无调参、T_hold=2） |
| 资格门数值 | V1 Δ_f/σ **11.6554**/power 1；V2 KL **0.61703**；V3 E_h **0.50891**/power 1；V4 独立 seed **20261062**/n=200：**503.04246827 / 64.42138097 / [376.77888173, 629.30605481]**（唯一 gate）；G1 k=**976/20000**、point **0.0488≤.05**、Wilson **0.05187354≤.075**；G2 **1.000/1.000/1.000**；G3 full **143/600/140/3**；G7 pilot **0.0455 s/rep、20.48 s main、0.04 GB**、B2 audit PASS |

**执行前清单**：① 重算 v0.4/C204 SHA 链，全部匹配；② V4_validation `model_spec_sha256` 匹配；③ G1–G7 数值匹配且 PASS；④ B2 等价审计 PASS；⑤ G7 pilot 复核 ≤caps；⑥ 任一不匹配 → `design_invalid: chain_mismatch`，停止、不报效果。

## 1. 执行种子/样本（独立，不复用 gate seeds）

- **禁止复用** gate/开发 seeds **{20261030, 20261061, 20261062, 20261063}**。
- **执行 replicate 数据集 seed**：`20261070 + r`，r=0..**49**（共 50 个：20261070–20261119）；同一 replicate 的 menus/初始数据/GT 由该 seed 生成；**执行时不得改 seed**。
- **方法随机性 seed**（B5/B6/初始化等）：`20262000 + r*10 + method_index`，method_index 0..6（M/B1/B2/B3/B4/B5/B6 固定顺序）；两跑同一 seed。
- **headroom 预检 seeds**：`20261130 + r`，r=0..19（20 个；独立于执行/gate seeds）；用于 B2 vs oracle 的 headroom 预检（不用于效果主检验）。
- **两跑**：run1/run2 使用**完全相同 seeds**的独立进程；结果 JSON（无 telemetry）逐字节一致；不一致 → `design_invalid: two_run_mismatch`。seed 表 SHA 与禁止 seeds 重叠检查由 `exec_plan.py` 记录（overlap=[]、unique=true）。

## 2. 方法/等预算（M vs B1–B6）

- **M（N1 method）**：状态后验 + 一次反馈统一修订（soft state responsibilities/weighted ridge，按 v0.4 冻结）。
- **基线**：B1 full retrain（静态 S-add 全历史）、**B2 static S-add（关键强基线；同特征/同 prior/同初始化/同 feedback/同 query/同调参/同 seed）**、B3 hierarchical/EB、B4 GP、B5 random plan-pair、B6 decision AL。
- **统一预算**：T=**6** 轮（fit 4 / held-out 2）、每轮 **1** 次反馈；query 数相同；特征信息相同；prior/初始数据相同；调参 ≤**20** 配置且不针对单个方法额外调参；同 wall/CPU/内存 cap。
- **B2 等价审计**（执行时以最终 effect runner 再次确认）：same initial-data hash、menus/round、query count=6、prior、tuning=20、shared dataset seed；审计失败 → `design_invalid: leakage`/`generator_misspecified`。
- **冻结代码只读**：执行时只读导入 `generator_n1_v0_4.py`（SHA `AA5D454A…`）；不得复制/修改冻结 generator/λ/特征/初始化。

## 3. Primary 与多重性

- **Primary endpoint**：paired held-out decision regret `D_i = R_i(M) − R_i(B2)`（**lower better**）；`R_i = mean_{t∈T_hold} r_t`，`r_t = max_{p∈M_t} U(p) − U(â)`，`U∈[0,1]` normalized；held-out 轮**不更新**。
- **δ = 0.05 normalized utility**（由决策相关性预注册，不得事后降 δ）。
- **成功判据（全部满足）**：① `mean ΔR ≤ −δ`；② 95% CI **upper < 0**；③ **Holm 校正后 p < 0.05**。
- **多重性**：预注册 family = **6** 个 planned comparisons（M vs B1、**M vs B2=primary**、M vs B3、M vs B4、M vs B5、M vs B6）；**Holm**（α=.05）在同一 family；primary 必须在 Holm 校正后显著。secondary 为其余 5 个，同一 Holm family；primary 失败时 secondary 仅描述性方向，不作算法主张。
- **不得换端点**：primary 必须保持 held-out decision regret；不得换成预测指标/预算指标/top-k；若 B2 接近最优 → `unreachable_gate`/另立 budget-to-target（E5），不静默换端点/降 δ。
- **headroom 预检**：在 headroom seeds 的 20 reps×300 units 上估 `U0(B2)`、`U_max=1`；`headroom=1−U0`；若 `headroom<δ` → `unreachable_gate`（停止，不解释为算法失败）。

## 4. 分析/单位/MDE

- **执行规模**：**n_units=300**（每 replicate）× **R=50 replicates** × **7 methods** × T=6。
- **分析单位**：replicate 内的**决策单元** i（300/rep；共 R·n_units=15,000 paired units）；`D_i` 配对；**cluster-robust SE 按 replicate（G=50）**，报告 mean ΔR、95% CI、Holm p、每个基线。
- **保守 MDE**：单 replicate 口径 `n_units=300`、deff=1+(m−1)ICC=**2.2**（m=5, ICC=.30）→ n_eff=**136.36**；SD(D) 保守 **.20** → **MDE80=0.04798≤.05**；n_req(cluster)=**278≤300**。因实际分析用 50 replicates（cluster 层级计），真实精度**不差于**该保守值；执行报告同时给保守 MDE 与 cluster-robust SE。
- 若实际 cluster-robust SD 使 MDE>δ → `precision_insufficient`（停/扩资源，不是算法失败）；不得事后加 n/降 δ。

## 5. 预算/资源

- **main**：300 units × 50 reps × 7 methods；**wall≤1800 s/run、CPU≤2 h、内存≤8 GB**；**0 wells/compute-only**；不使用 A/B 资源。
- **pilot/G7 复核**：引用 C204 实测（**per-rep 0.0455 s、main 20.48 s、memory 0.04 GB**、B2 audit PASS）；执行前用最终 effect runner 重跑 2-replicate pilot；若投影 >caps → `design_invalid: compute_budget_exceeded`（**不得减 n_units/R/methods**）。
- **两跑**：每跑独立进程，结果 JSON 无 telemetry；wall/CPU/内存只写 `timing_n1_effect.json`；两跑结果逐字节一致（否则 two_run_mismatch）。
- **成本账**：per-method/replicate 记录 queries、feedback 数、fits/updates、tuning configs（计数）；wall 时间只进 telemetry。

## 6. Schema/输出（冻结）

- **top keys**：`task_id, status, frozen_chain, seeds, design, per_replicate, summary, headroom, cost_ledger, run_shas, failure_category, verdict`。
- **per_replicate/per_method**：`replicate_id, dataset_seed, method_seeds, method, n_units, heldout_regret_mean, heldout_selected_U_mean, oracle_U_mean, n_queries, n_feedback, tuning_configs`。
- **summary**：`primary_mean_DeltaR, primary_CI95, primary_holm_p, secondary_effects, secondary_holm_p, n_units_total, n_replicates`。
- **禁列**：`prediction_accuracy/topk_hit/budget_to_target_effect/exploratory_endpoint` 及任何药理/真实决策/迁移/机制/新颖性字段；不得含未预注册终点。
- **失败输出**：只写 `failure_category`/`design_invalid`，**不报方法差异**。

## 7. 失败类别/停止

`design_invalid: chain_mismatch / schema_mismatch / two_run_mismatch / leakage / compute_budget_exceeded / generator_misspecified / calibration_failed / nonidentifiable`；`unreachable_gate`（headroom<δ）；`precision_insufficient`（MDE>δ/n 不足）；`no_increment`（primary CI 排除 −δ 的非改善侧且无 secondary 支持）；`inconclusive`（CI 同时覆盖 0 与 −δ、未达成功）。`design_invalid` 停且不报效果；`unreachable_gate`/`precision_insufficient` 不是算法失败；`no_increment`/`inconclusive` 撤回/不宣称算法增量。

## 8. 边界

- 机制账 only：合成 generator、已知 ground-truth、compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；技术重复≠独立培养；不拼 ΔEMAX；不使用 A/B 线资源。
- 不晋升代码；不改旧门槛/旧判定；不恢复已停止实验；**效果执行须另立独立挑战 + Lead 批准**；本文件不运行效果、不报告方法差异。

## 9. 产物

`PROBLEM_N1_EXEC.md`（本文）、`DESIGN_N1_EXEC.md`、`exec_plan.py`（规划/种子/SHA 校验，不跑效果）、`exec_plan.json`、report/record/usage。
