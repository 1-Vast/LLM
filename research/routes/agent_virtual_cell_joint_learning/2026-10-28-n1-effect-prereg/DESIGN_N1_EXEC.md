# DESIGN_N1_EXEC —— R203-N1 效果执行设计（预注册草案；不运行效果）

2026-10-28。依据：[PROBLEM_N1_EXEC.md](PROBLEM_N1_EXEC.md)、`exec_plan.json`、C204（`qualification_pass`）、N1 v0.4 冻结链、R203-P1 链。
**状态：设计/预注册草案；未运行效果；任何效果执行须独立挑战 + Lead 批准；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells/compute-only。**

## 0. 前置条件（全部通过才允许执行；失败 → stop）

1. **SHA 链核验**（`exec_plan.py` 已核验通过，执行时重跑）：v0.4 链（PROBLEM/DESIGN/generator/py/json/V4_validation/pilot/DECISION）与 C204 链（run_n1_gates.py、n1_gates.json `529C1D2E…`、timing、schema、report/record/usage）SHA 全部匹配；不匹配 → `design_invalid: chain_mismatch`。
2. **V4_MODEL_SPEC SHA** `A69B845D…` 匹配；V4 唯一 gate = 独立 seed 20261062（dev 20261061 post-hoc、oracle 20261063 fallback **不得替代**）。
3. **G1–G7 数值**匹配且 PASS（G1 .0488/.05187；G2 1.000；G3 143/600/140/3；G7 .0455 s/20.48 s/.04 GB；B2 audit PASS）。
4. **headroom 预检**（在执行前、独立 headroom seeds 20261130+r, 20 reps×300 units）：`U0(B2)`、`U_max=1`；若 `headroom=1−U0 < δ=.05` → `unreachable_gate`（停止；不解释为算法失败；若 B2 近满分，另立 budget-to-target，不静默换端点）。
5. **G7 复核**：用最终 effect runner 跑 2-replicate pilot；若 wall/CPU/内存投影 >caps（1800 s/7200 s/8 GB）→ `design_invalid: compute_budget_exceeded`（不得减 n_units/R/methods）。

## 1. 实现计划（执行时新建；不修改冻结代码）

- **effect runner**：新文件（如 `run_n1_effect.py`），**只读导入** `research/2026-10-28-n1-synthetic-prereg/generator_n1_v0_4.py`（SHA `AA5D454A…`）与七方法类；不得复制/修改 generator/λ/特征/初始化/V4 spec；不重用 A/B 线代码。
- **数据生成**：每 replicate r 用 dataset seed `20261070+r` 生成 GT（S=3 隐藏状态/state-specific 转移/共享动态核/f,g,h/σ=.15）、menus、初始数据；所有方法共享同一 replicate 数据（same menus/initial/feedback 流）。
- **协议**：每 unit T=6 轮；fit 轮 1–4：方法每轮选 1 个 plan、获得 1 次反馈并更新；**held-out 轮 5–6：不更新**，按方法当前模型在菜单 m=5 上选择；记录 held-out regret/U/chosen/oracle、query/feedback/tuning/成本计数。
- **方法**：M 与 B1–B6 均由冻结模块提供；统一 prior/初始数据/feedback/query T=6/调参≤20/特征信息/seed；B5/B6 随机性用 method seed `20262000+r*10+idx`；**B2 等价审计**（initial-data hash/menus/query count/prior/tuning/seed）。
- **held-out regret 定义**：`r_t = max_{p∈M_t} U(p) − U(â_t)`，`U∈[0,1]`（control/floor 归一化，冻结 generator 的 GT oracle 用于 U）；`R_i = mean_{t∈T_hold} r_t`；`D_i = R_i(M) − R_i(B2)`。
- **成本账**：per method/replicate 记录 queries、feedback 数、fits/updates、tuning 配置数；wall/CPU/内存只进 telemetry。**不得**用成本差异替代效果判定。

## 2. 执行顺序（冻结）

1. 链核验（v0.4+C204+V4 spec+G1–G7）→ 失败 stop。
2. headroom 预检（独立 seeds）→ `unreachable_gate` 若 headroom<δ。
3. G7 pilot 复核（最终 runner）→ `compute_budget_exceeded` 若超 caps。
4. **run1**（独立进程，执行 seeds）→ 写 result JSON（无 telemetry）+ timing1。
5. **run2**（独立进程，同 seeds）→ 写 result JSON（无 telemetry）+ timing2；比较 result SHA：不一致 → `design_invalid: two_run_mismatch`。
6. schema/G6 校验 → 失败 `design_invalid: schema_mismatch`。
7. 主分析 + Holm + headroom 记录 → verdict（success/no_increment/inconclusive/precision_insufficient 等）。
8. 失败时只写 failure_category，**不报方法差异**。

## 3. 统计分析（预注册）

- **主分析**：对全部 R×n_units=15,000 个 paired `D_i` 估计均值 ΔR；**cluster-robust SE（按 replicate，G=50）**；95% CI（t_{G−1} 或正态近似，写死为 t_{49}）；报告每个基线。
- **保守精度**：单 replicate 口径 n_units=300、deff=2.2、n_eff=136.36、SD(D) 保守 .20 → MDE80=.04798≤δ；n_req=278≤300；实际 cluster-robust SE 报告并与保守 MDE 对照。
- **多重性**：family=6（M vs B1,B2,B3,B4,B5,B6）；**Holm** α=.05；primary=M vs B2，需 mean ΔR≤−δ ∧ CI upper<0 ∧ Holm p<.05；secondary 同 family。
- **headroom**：记录 U_max/U0/headroom；`headroom<δ → unreachable_gate`；`U0` 近 1（ceiling）→ 另立 budget-to-target，不换 primary。
- **不静默换端点**：primary 固定为 held-out decision regret；不得事后换预测/预算/top-k 端点、不得降 δ、不得因结果加 n 或改 cluster。

## 4. 两跑/预算/telemetry

- **两跑**：run1/run2 独立进程、同 seeds、同代码；结果 JSON 无 wall/timestamps/telemetry；两跑逐字节一致（SHA 写 `run_shas`）；不一致 → two_run_mismatch。
- **预算**：main 300×50×7×T=6；wall≤1800 s/run、CPU≤2 h、内存≤8 GB；0 wells/compute-only；**C204 pilot 参考** .0455 s/rep、20.48 s main、.04 GB（执行时重跑 2-rep pilot 复核）。
- **telemetry**：wall/CPU/内存只写 `timing_n1_effect.json`，不进 result JSON。
- **失败/停止**：chain_mismatch/schema_mismatch/two_run_mismatch/leakage/compute_budget_exceeded/generator_misspecified/calibration_failed/nonidentifiable；unreachable_gate/precision_insufficient；no_increment/inconclusive 决策树按 PROBLEM §7。

## 5. Schema（冻结）

`exec_plan.json → schema`：top keys（task_id/status/frozen_chain/seeds/design/per_replicate/summary/headroom/cost_ledger/run_shas/failure_category/verdict）；per_replicate/per_method 字段（replicate_id/dataset_seed/method_seeds/method/n_units/heldout_regret_mean/heldout_selected_U_mean/oracle_U_mean/n_queries/n_feedback/tuning_configs）；summary（primary_mean_DeltaR/primary_CI95/primary_holm_p/secondary_effects/secondary_holm_p/n_units_total/n_replicates）；禁列见 PROBLEM §6。

## 6. 批准清单（供 Lead/挑战者核对）

1. 执行 seeds 独立于 gate/dev seeds（20261070–20261119；headroom 20261130–20261149；method 20262000 段）；两跑同 seeds 独立进程。
2. M vs B1–B6 等预算（T=6/每轮 1 feedback/调参≤20/特征/prior/初始数据/seed）；B2 强基线等价审计。
3. primary=held-out regret δ=.05；成功三项（mean≤−δ、CI upper<0、Holm p<.05）；family=6 Holm；不换端点；headroom 预检。
4. 分析单位/paired/cluster-robust；保守 MDE .04798/n_req278；报告 mean/CI/Holm p。
5. 预算 caps/两跑/schema/失败类别/边界；执行前链核验。
6. 机制账 only：不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells；效果执行另立独立挑战+Lead 批准。
