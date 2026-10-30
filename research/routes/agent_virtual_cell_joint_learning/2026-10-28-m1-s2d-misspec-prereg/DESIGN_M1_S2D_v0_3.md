# DESIGN_M1_S2D_v0_3 —— R204-M1-S2D.2 错配/背景漂移规划价值执行设计（T3 避开 M2 Stage3；不运行候选）

2026-10-28。依据：[PROBLEM_M1_S2D_v0_3.md](PROBLEM_M1_S2D_v0_3.md)、`headroom_design_m1_s2d_v0_3.json`、`schema_m1_s2d_v0_3.json`、S2c/C223、H1b/C222、C216/C217、C208、C220/C221、M1 Stage2 v0.2、M1 Stage2 exec seed 清单。
**状态：预注册修订设计 v0.3；仅设计期 headroom（冻结源/目标真值）；未训练 C-MDN/未运行候选规划/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 分离/前置（不变）

- S2c 正结果仅合成 known-truth；S2d 不修改 S2c；C216 旧 H1 0/16、C217 归因、H1b 密度-only、一步投影撤（C208）全部不变；旧容差/判定不改。
- 本任务仅设计期 headroom；不训练 C-MDN/不运行候选规划/不报效果。

## 1. 源/目标环境（不变）

- 源 Pθ：c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；Y∈[-2,2]^4；K=3/[.5,.3,.2]；seeds 20261301/02/03；X~N(0,I_64)；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；S=4096/动作。
- 目标 Pθ'：**T1_scale_drift（主）** c'~N(0,1.0²)（seed 20262001；M/d 同源；X~N(0,I)；π0' full）；T2_slope_drift M'~N(0,.2²)（seed 20262002）；T3_background_drift θ 同源、X'~N(0,1.5²I)。
- 候选 C-MDN 仅源训练；目标数据禁用训练/调参；known-truth 目标解析截断正态矩。

## 2. 设计期 headroom（不变）

- baseline=P_empirical_mean_source（N_train=4096 源样本/动作、动作级经验均值、忽略 x）；目标独立 eval X=4096；R=20（20262011–30）；真值目标解析。
- 结果：T1 **.51107412** CI **[.46843293,.55371531]**；T2 **.56758207** CI **[.56039835,.57476580]**；T3 **.39007047** CI **[.38530525,.39483569]**；均≥.10 → executable；未重设环境；headroom 设计期实测（候选未见前），不冒充执行 R。

## 3. 执行 cells / forbidden（必改 1–2）

| target | 执行 cell seeds | R |
|---|---|---|
| T1_scale_drift | **20262041–20262060** | 20 |
| T2_slope_drift | **20262061–20262080** | 20 |
| T3_background_drift | **20262141–20262160** | 20 |
| **合计** | — | **60** |

- **T3 旧 block 20262081–20262100 作废**（20262100 属 M2 Stage3 保留区，未解除）；T3 新块 20262141–60。
- **forbidden ranges（旧保留区）**：M1 Stage1/C208 20261112–13；M1 v0.2 20261201–03；**M2 Stage2 20261200–39**；M1 Stage2 exec 20261300–49；**M3 Stage2 20261400–99**；**M3 20261500–99**；**M3 Stage3 20261600–90**；H1b 20261800–49；S2c 20261900–59；**M2 Stage3 20262100–39**。
- `forbidden_old_seeds` = 上述并集去重（count=533）；`forbidden_ranges` 写死；`overlap_with_forbidden=[]`；`cell_blocks_disjoint=true`；执行 cells/data/eval 与全集无交集。
- schema/JSON 五字段保持：`R_execution_per_target=20`、`n_targets=3`、`n_cells=60`、`cluster="replicate"`、`CI_method="95% t interval across independent replicates (df=R-1); cluster=replicate"`；T2/T3 每 target Holm R=20。

## 4. T2 有效行数（保持）

- nominal 4096；**T2 valid_eval_rows=4093**（3 极端解析下溢行剔除）；T1/T3=4096；schema/JSON `valid_eval_rows_frozen` + note；**不按 4096 谎报**。

## 5. 六比较/Holm/分析（保持）

- 主 target T1：primary candidate（源训练）vs P_empirical_mean_source；secondary P_empirical_mean_target_adapted（3584 源+512 目标/动作同预算）、P_max_entropy、P_conditional_density_MC（共用 C-MDN、预计 D=0、不称独立）、P_random、P_softmax_expected_reward。
- D=regret_cand−regret_base<0；δ=.05；Holm family=6、单侧下尾；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；每 target R=20、cluster=replicate、95% t(df=19)；不用规划 MDE 当功效；T2/T3 不合并、主成功仅 T1；等价审计（candidate 与 empirical-mean/max-entropy/conditional-density 等价→equivalence/no increment；不得目标训练/调参制造差异）。

## 6. 两跑/caps/schema/失败/停止/边界（保持）

- 两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独；caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- 失败类别 11：projection/calibration/leakage/unreachable_gate/equivalence/precision_insufficient/two_run_mismatch/chain_mismatch/compute_budget_exceeded/no_increment/inconclusive。
- 停止：headroom<.10（任一 target）→重设/冻结或 unreachable_gate；等价→no increment；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 7. 批准清单

① 分离/旧状态不变；② T3 新块 20262141–60 + 完整 forbidden/overlap=[]/cell_blocks_disjoint；③ 60 cells/R20 与 schema 五字段；④ T2 4093 冻结不谎报；⑤ headroom 值/六比较/δ/Holm/raw-paired/每 target CI/等价审计；⑥ 候选仅源训练/目标禁用训练调参；⑦ 两跑/caps/schema/11 失败/停止/边界。执行须另立独立挑战+Lead 批准。
