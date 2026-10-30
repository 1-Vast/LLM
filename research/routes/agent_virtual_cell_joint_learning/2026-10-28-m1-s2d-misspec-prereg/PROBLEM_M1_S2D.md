# PROBLEM_M1_S2D —— R204-M1-S2d 错配/背景漂移下规划价值检验预注册（先 headroom；不运行候选）

2026-10-28。对象：R204-M1-S2d 错配/背景漂移规划价值检验预注册。依据：S2c（C223 `planning_comparison_pass`，primary mean D −.055231 CI [−.068569,−.041892]、Holm 4.83e-16；仅合成 known-truth）、H1b/C222、C216/C217、C208、C220/C221 合同纠正、M1 Stage2 v0.2。
**状态：预注册草案；仅设计期 headroom（冻结源/目标真值）；未训练 C-MDN、未运行候选规划、未报效果、未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不修改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。执行须另立独立挑战+Lead 批准。**

## 0. 分离（写死）

| 项 | 状态 |
|---|---|
| S2c 正结果（C223） | **仅合成 known-truth**；不称药理/真实决策/迁移/机制/新颖性；不改 S2c |
| C216 旧 H1 | 0/16 FAIL、`design_invalid: projection` 不变 |
| C217 归因 | 不变 |
| H1b（C222） | 16/16 仅密度近似可分辨；不是旧 H1 通过 |
| 一步投影 | 仍撤（C208）；S2d 不写 M1 增量 |
| 旧容差/判定 | 不改 |

## 1. 源训练环境（同 H1b/S2c）

- Pθ：K=3 截断 GMM；c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；Y∈[-2,2]^4；K=3/[.5,.3,.2]；param/train/eval seeds **20261301/02/03**。
- X~N(0,I_64)；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；规划 S=4096/动作；known-truth 解析。
- **候选 C-MDN 仅源训练**；**禁用目标数据训练/调参**（目标数据只用于评价与 target-adapted baseline 的少量标定）。

## 2. 目标 Pθ'（至少 2 种，预先写死；本预注册 3 种）

| id | 漂移 | 参数 |
|---|---|---|
| **T1_scale_drift（主目标）** | 尺度漂移 | **c'~N(0,1.0²)**（M,d 同源）；X~N(0,I)；π0' full |
| T2_slope_drift | 协方差/斜率漂移 | **M'~N(0,.2²)**（c,d 同源）；X~N(0,I)；π0' full |
| T3_background_drift | 背景/协变量漂移 | θ 同源；**X'~N(0,1.5² I)**；π0' full |

- target param seeds：T1 **20262001**、T2 **20262002**、T3 复用源 θ；known-truth 用 **Pθ' 解析截断正态矩**（独立高精度）。
- 目标数据只用于评价；候选不得用目标数据训练/调参；若等价审计发现候选与标准方法等价→equivalence/no increment。

## 3. 设计期 headroom（先于候选；目标 Pθ' 上 P_empirical_mean_source baseline regret）

- baseline = **P_empirical_mean_source**：每动作 N_train=4096 **源**样本的动作级经验平均 reward（忽略 x）；在目标 Pθ' 独立 eval X=4096 上评价；R=20（20262011–30）；真值用目标 Pθ' 解析。
- **要求每个目标 mean baseline regret ≥ 2δ=0.10** 才可执行；任一目标 <0.10 → **未见候选前**重设/冻结该目标，或 `design_invalid: unreachable_gate` 停止；**不降 δ/不换 seed/不换环境救结果**。
- **结果（设计期实测，候选未见前）**：

| target | mean baseline regret | 95% CI(t₁₉) | headroom_ok |
|---|---|---|---|
| **T1_scale_drift** | **0.51107412** | **[0.46843293, 0.55371531]** | **true** |
| T2_slope_drift | **0.56758207** | **[0.56039835, 0.57476580]** | **true** |
| T3_background_drift | **0.39007047** | **[0.38530525, 0.39483569]** | **true** |

- **三目标均 ≥.10 → executable**；**未重设环境**；**未用候选结果反选 headroom**。

## 4. 六比较族/Holm/分析

- **Primary（主目标 T1）**：candidate（源训练）vs **P_empirical_mean_source**。
- **Secondary**：P_empirical_mean_target_adapted（**同预算**：每动作 3584 源 + 512 目标样本；目标少量标定/重加权）、P_max_entropy、P_conditional_density_MC（共用 C-MDN，预计 D=0，不称独立）、P_random、P_softmax_expected_reward。
- **D_j=regret_candidate−regret_baseline_j**；改善 D<0；δ=**0.05**；**统一 Holm（family=6）、单侧下尾**；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05。
- **raw regret 与 paired D 分开保存**；CI 按独立 replicate（R≥20，cluster=replicate）；**不用规划 MDE 当已证功效**。
- **T2/T3 为预注册次级/泛化目标**：同六比较、同 Holm（每个 target 内 family=6）；不合并 target、不 pool；主成功判定仅 T1；T2/T3 报告泛化/错配敏感性。
- **等价审计**：candidate 与 P_empirical_mean_source/P_max_entropy/P_conditional_density_MC 逐点动作/单调/解析覆盖→equivalence、停止增量；不得用目标训练/调参制造差异。

## 5. 执行/seeds/两跑/caps/schema/失败/停止

- **独立 seeds**：headroom **20262011–20262030**；执行 data **20262031**、target eval **20262032**、cell seeds **20262041–20262088**（48）；与 S2c/H1b/C216/C217/旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **失败类别 11**：`design_invalid: projection|calibration|leakage|unreachable_gate|equivalence|precision_insufficient|two_run_mismatch|chain_mismatch|compute_budget_exceeded`、`no_increment`、`inconclusive`。
- **停止**：headroom<.10（任一 target）→未见候选前重设/冻结或 `unreachable_gate` 停止；等价→no increment；CI 无法排除 0 或 −δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务**不训练 C-MDN/不运行候选规划/不报效果**。

## 6. 边界

机制账 only；合成 compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。
