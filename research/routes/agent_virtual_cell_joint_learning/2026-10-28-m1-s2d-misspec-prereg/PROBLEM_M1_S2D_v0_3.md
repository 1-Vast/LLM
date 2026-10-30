# PROBLEM_M1_S2D_v0_3 —— R204-M1-S2D.2 错配/背景漂移规划价值预注册（T3 避开 M2 Stage3；forbidden 补全；不运行候选）

2026-10-28。对象：R204-M1-S2d 错配/背景漂移规划价值检验预注册。本文件修正 v0.2（[PROBLEM_M1_S2D_v0_2.md](PROBLEM_M1_S2D_v0_2.md)，保留不改），落实 M1-S2D.1-C1 必改：**T3 block 20262081–20262100 与 M2 Stage3 保留区 20262100–20262139 重叠**、**forbidden 集不完整**。**不训练 C-MDN、不运行候选规划、不报效果**。依据：S2c/C223、H1b/C222、C216/C217、C208、C220/C221、M1 Stage2 v0.2、M1 Stage2 exec seed 清单。
**状态：预注册修订草案 v0.3；仅设计期 headroom（冻结源/目标真值）；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不修改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。执行须另立独立挑战+Lead 批准。**

## 0. M1-S2D.1-C1 必改落实

| # | 矛盾 | v0.3 修正 |
|---|---|---|
| ① **T3 seed 与 M2 Stage3 重叠** | v0.2 T3 **20262081–20262100**，末 seed **20262100** 落在 **M2 Stage3 保留区 20262100–20262139** | **T3 重划为 20262141–20262160**（20 seeds）；T1 20262041–60、T2 20262061–80 不变；每 target R=20、共 60；**20262100 不再使用**；M2 Stage3 保留区不解除 |
| ② **forbidden 集不完整** | v0.2 `forbidden_old_seeds` 未列 M2 Stage3 20262100–39，`overlap=[]` 不完整 | **补全 forbidden ranges**：M1 Stage1/C208 20261112–13；M1 v0.2 20261201–03；**M2 Stage2 20261200–39**；M1 Stage2 exec 20261300–49；**M3 Stage2 20261400–99**；**M3 20261500–99**；**M3 Stage3 20261600–90**；H1b 20261800–49；S2c 20261900–59；**M2 Stage3 20262100–39**；重算 **overlap_with_forbidden=[]、cell_blocks_disjoint=true**；`forbidden_old_seeds_count=533`（唯一 seed 去重） |
| ③ 保持 | — | 60 cells/R20；schema 五字段；T2 valid_eval_rows=4093（nominal 4096、不谎报）；headroom 值 T1 .51107412 CI [.46843293,.55371531]、T2 .56758207 CI [.56039835,.57476580]、T3 .39007047 CI [.38530525,.39483569]；目标 θ'；候选仅源训练/目标禁用训练调参；六比较/Holm6/δ=.05/单侧下尾/raw-paired/T2T3 不合并/主成功仅 T1/等价审计；headroom seeds 20262011–30/data 20262031/eval 20262032；两跑/caps/schema/11 失败/停止/边界 |

## 1. 分离（不变）

- S2c 正结果仅**合成 known-truth**；不称真实数据/药理/真实决策/迁移/机制/新颖性；S2d 不修改 S2c。
- C216 旧 H1 0/16/`design_invalid: projection`、C217 归因、H1b 16/16 密度-only、一步投影撤（C208）**全部不变**；旧容差/判定不改。

## 2. 源/目标环境（不变）

- 源 Pθ 同 H1b/S2c：c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；Y∈[-2,2]^4；K=3/[.5,.3,.2]；param/train/eval seeds 20261301/02/03；X~N(0,I_64)；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；S=4096/动作。
- 目标 Pθ'：**T1_scale_drift（主）** c'~N(0,1.0²)（seed 20262001；M/d 同源；X~N(0,I)；π0' full）；T2_slope_drift M'~N(0,.2²)（seed 20262002）；T3_background_drift θ 同源、X'~N(0,1.5²I)。
- **候选 C-MDN 仅源训练；目标数据禁用训练/调参**；known-truth 用目标 Pθ' 解析截断正态矩。

## 3. 设计期 headroom（不变；先于候选）

- baseline=P_empirical_mean_source（N_train=4096 源样本/动作、动作级经验均值、忽略 x）；目标独立 eval X=4096；R=20（20262011–30）；真值目标解析。
- **结果**：T1 **.51107412** CI **[.46843293,.55371531]**；T2 **.56758207** CI **[.56039835,.57476580]**；T3 **.39007047** CI **[.38530525,.39483569]**；均≥2δ=.10 → executable；未重设环境。
- **headroom R=20 仅设计期**，不冒充执行 R；执行每 target 独立 R=20。

## 4. 执行 cells / forbidden（关键修正）

| target | 执行 cell seeds | R |
|---|---|---|
| T1_scale_drift | **20262041–20262060** | 20 |
| T2_slope_drift | **20262061–20262080** | 20 |
| T3_background_drift | **20262141–20262160** | 20 |
| **合计** | — | **60** |

- **forbidden ranges（旧保留区，不得占用）**：M1 Stage1/C208 20261112–13；M1 v0.2 20261201–03；**M2 Stage2 20261200–39**；M1 Stage2 exec 20261300–49；**M3 Stage2 20261400–99**；**M3 20261500–99**；**M3 Stage3 20261600–90**；H1b 20261800–49；S2c 20261900–59；**M2 Stage3 20262100–39**。
- **overlap_with_forbidden=[]**（执行 seeds + data/eval 与上述全集交集为空）；**cell_blocks_disjoint=true**；`forbidden_old_seeds_count=533`（唯一值）。
- headroom seeds 20262011–30、data 20262031、eval 20262032；执行 cells 三块；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。

## 5. 六比较/Holm/分析（不变）

- 主 target T1：primary candidate（源训练）vs P_empirical_mean_source；secondary P_empirical_mean_target_adapted（同预算 3584 源+512 目标/动作）、P_max_entropy、P_conditional_density_MC（共用 C-MDN、预计 D=0、不称独立）、P_random、P_softmax_expected_reward。
- D=regret_cand−regret_base<0；δ=.05；Holm family=6、单侧下尾；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；每 target R=20、cluster=replicate、95% t（df=19）；不用规划 MDE 当功效。
- T2/T3 每 target 同六比较、同 Holm（R=20）；不合并/pool；主成功仅 T1；不得次级豁免 CI。
- 等价审计：candidate 与 P_empirical_mean_source/P_max_entropy/P_conditional_density_MC 逐点动作/单调/解析覆盖→equivalence、停止增量；不得目标训练/调参制造差异。
- **T2 有效行数**：nominal 4096，T2 valid **4093**（3 极端解析下溢行剔除）；T1/T3=4096；不按 4096 谎报。

## 6. 执行/预算/失败/停止（保持）

- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry；本任务不训练/不运行候选。
- 失败类别 11：projection/calibration/leakage/unreachable_gate/equivalence/precision_insufficient/two_run_mismatch/chain_mismatch/compute_budget_exceeded/no_increment/inconclusive。
- 停止：headroom<.10（任一 target）→未见候选前重设/冻结或 unreachable_gate 停止；等价→no increment；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 边界：机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。
