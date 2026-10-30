# PROBLEM_M1_S2D_v0_2 —— R204-M1-S2D.1 错配/背景漂移规划价值预注册（每 target R≥20/共 60 cells；不运行候选）

2026-10-28。对象：R204-M1-S2d 错配/背景漂移规划价值检验预注册。本文件修正 v0.1（[PROBLEM_M1_S2D.md](PROBLEM_M1_S2D.md)，保留不改），落实 M1-S2D-C1 必改：**执行 cells 48→每 target 独立 R≥20、共 60**，并补 schema/JSON 可判字段与 T2 有效行数记录；**不训练 C-MDN、不运行候选规划、不报效果**。依据：S2c/C223、H1b/C222、C216/C217、C208、C220/C221、M1 Stage2 v0.2。
**状态：预注册修订草案 v0.2；仅设计期 headroom（冻结源/目标真值）；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不修改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。执行须另立独立挑战+Lead 批准。**

## 0. M1-S2D-C1 必改落实

| # | 挑战问题 | v0.2 修正 |
|---|---|---|
| ① **执行 cells 不足** | v0.1 `execution_cell_seeds` 20262041–88（48）÷3 targets=16 <20；但要求每 target R≥20、cluster=replicate | **每 target 独立 R=20 seed 块、共 60 cells**：**T1 20262041–20262060、T2 20262061–20262080、T3 20262081–20262100**；与 S2c/H1b/C216/C217/旧集 disjoint；**48 不再使用**；头段/执行 R 分开 |
| ② **schema/JSON 可判字段** | — | 新增 **`R_execution_per_target=20`、`n_targets=3`、`n_cells=60`、`cluster="replicate"`、`CI_method="95% t interval across independent replicates (df=R-1); cluster=replicate"`**；`multiple_testing.CI` 与实际 60 cells 一致；**T2/T3 每 target Holm 也按 R=20**，不得以次级豁免 |
| ③ **T2 有效行数** | v0.1 JSON 仅 `valid_eval_rows_min=4093` | 执行前冻结：**T2 target eval 有效行数=4093**（3 个极端解析下溢行被剔除；nominal 4096）；schema/JSON 记录 4093+原因，**不按 4096 谎报**；T1/T3=4096 |
| ④ 保持 | — | 目标 Pθ'（T1 c'~N(0,1.0²) seed 20262001 主 / T2 M'~N(0,.2²) seed 20262002 / T3 X'~N(0,1.5²I)）；headroom 值 T1 .51107412 CI [.46843293,.55371531]、T2 .56758207 CI [.56039835,.57476580]、T3 .39007047 CI [.38530525,.39483569]；候选仅源训练/目标禁用训练调参；六比较/Holm family=6/δ=.05/单侧下尾/raw-paired/**每 target CI R≥20**/T2/T3 不合并/主成功仅 T1；等价审计；headroom seeds 20262011–30、data 20262031、eval 20262032；两跑/caps 1800 s/2 h/8 GB/0 wells/schema/11 失败/停止/边界 |

## 1. 分离（不变）

- S2c 正结果仅**合成 known-truth**；不称真实数据/药理/真实决策/迁移/机制/新颖性；S2d 不修改 S2c。
- C216 旧 H1 0/16/`design_invalid: projection`、C217 归因、H1b 16/16 密度-only、一步投影撤（C208）**全部不变**；旧容差/判定不改。

## 2. 源/目标环境（不变）

- 源 Pθ 同 H1b/S2c：c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；Y∈[-2,2]^4；K=3/[.5,.3,.2]；param/train/eval seeds 20261301/02/03；X~N(0,I_64)；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；S=4096/动作。
- 目标 Pθ'（3 种）：**T1_scale_drift（主）** c'~N(0,1.0²)（M,d 同源；target c seed 20262001；X~N(0,I)；π0' full）；T2_slope_drift M'~N(0,.2²)（c,d 同源；seed 20262002）；T3_background_drift θ 同源、X'~N(0,1.5²I)。
- **候选 C-MDN 仅源训练；目标数据禁用训练/调参**；known-truth 用目标 Pθ' 解析截断正态矩。

## 3. 设计期 headroom（不变；先于候选）

- baseline=P_empirical_mean_source（N_train=4096 源样本/动作、动作级经验均值、忽略 x）；目标独立 eval X=4096；R=20（20262011–30）；真值目标解析。
- **结果**：T1 **.51107412** CI **[.46843293,.55371531]**；T2 **.56758207** CI **[.56039835,.57476580]**；T3 **.39007047** CI **[.38530525,.39483569]**；均≥2δ=.10 → executable；未重设环境。
- **headroom R=20 仅是设计期**，**不得冒充执行 R=20**；执行每 target 独立 R=20（见下）。

## 4. 六比较族/执行设计（每 target R=20）

- Primary（主 target T1）：candidate（源训练）vs **P_empirical_mean_source**；secondary P_empirical_mean_target_adapted（同预算 3584 源+512 目标/动作）、P_max_entropy、P_conditional_density_MC（共用 C-MDN、预计 D=0、不称独立）、P_random、P_softmax_expected_reward。
- **D_j=regret_candidate−regret_baseline_j**；改善 D<0；δ=**0.05**；**统一 Holm（family=6）、单侧下尾**；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；**每 target 独立 R=20、cluster=replicate、95% t 区间（df=19）**；不用规划 MDE 当功效。
- **T2/T3 每 target 同六比较、同 Holm（family=6，R=20）**；不合并/pool；主成功仅 T1；T2/T3 不得以次级豁免 CI。
- **执行 cells**：**T1 20262041–60、T2 20262061–80、T3 20262081–100**（每 target 20，共 60）；与旧集 disjoint；**执行 data 20262031/eval 20262032**。
- **等价审计**：candidate 与 P_empirical_mean_source/P_max_entropy/P_conditional_density_MC 逐点动作/单调/解析覆盖→equivalence、停止增量；不得用目标数据训练/调参制造差异。
- **T2 有效行数冻结**：目标 eval nominal 4096，T2 有效 **4093**（3 个极端解析下溢行剔除）；T1/T3 4096；执行/报告按实际有效行记录，不写成 4096。

## 5. 执行/seeds/两跑/caps/schema/失败/停止（不变）

- **seeds**：headroom 20262011–30；data **20262031**、target eval **20262032**；执行 cells 按 §4 三块；overlap=[]；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **失败类别 11**：projection/calibration/leakage/unreachable_gate/equivalence/precision_insufficient/two_run_mismatch/chain_mismatch/compute_budget_exceeded/no_increment/inconclusive。
- **停止**：headroom<.10（任一 target）→未见候选前重设/冻结或 `unreachable_gate` 停止；等价→no increment；CI 无法排除 0 或 −δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务**不训练 C-MDN/不运行候选规划/不报效果**。

## 6. 边界

机制账 only；合成 compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。
