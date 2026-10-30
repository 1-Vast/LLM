# DESIGN_M1_S2D —— R204-M1-S2d 错配/背景漂移规划价值执行设计（先 headroom；不运行候选）

2026-10-28。依据：[PROBLEM_M1_S2D.md](PROBLEM_M1_S2D.md)、`headroom_design_m1_s2d.json`、`schema_m1_s2d.json`、S2c/C223、H1b/C222、C216/C217、C208、C220/C221、M1 Stage2 v0.2。
**状态：预注册设计草案；仅设计期 headroom（冻结源/目标真值）；未训练 C-MDN/未运行候选规划/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 分离/前置（不变）

- S2c 正结果仅合成 known-truth；不称真实数据/药理/真实决策/迁移/机制/新颖性；S2d 不修改 S2c。
- C216 旧 H1 0/16、`design_invalid: projection`、C217 归因、H1b 16/16 密度-only、一步投影撤（C208）**全部不变**；旧容差/判定不改。
- 本任务仅设计期 headroom；不训练 C-MDN/不运行候选规划/不报效果。

## 1. 源/目标环境

- **源训练 Pθ**：c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；Y∈[-2,2]^4；K=3/[.5,.3,.2]；param/train/eval seeds 20261301/02/03；X~N(0,I_64)；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；S=4096/动作。
- **目标 Pθ'（预注册）**：
  | id | 漂移 | 参数/种子 |
  |---|---|---|
  | T1_scale_drift（主） | 尺度 | c'~N(0,1.0²)，M/d 同源；X~N(0,I)；π0' full；target c seed **20262001** |
  | T2_slope_drift | 斜率/协方差 | M'~N(0,.2²)，c/d 同源；X~N(0,I)；π0' full；target M seed **20262002** |
  | T3_background_drift | 背景 X | θ 同源；X'~N(0,1.5²I)；π0' full |
- **候选 C-MDN 仅源训练**；**目标数据不得用于训练/调参**；目标数据只用于评价与 target-adapted baseline 的 512/动作标定（该 baseline 明确定义；候选不共享）。
- known-truth 用目标 Pθ' 的解析截断正态矩（高精度，独立于训练/验证）。

## 2. 设计期 headroom（已算；先于候选）

- baseline = P_empirical_mean_source：每动作 **N_train=4096 源样本**的动作级经验平均 reward（忽略 x）；目标 Pθ' 独立 eval X=4096；R=20（20262011–30）；真值目标解析。
- **结果**：

| target | mean baseline regret | 95% CI(t₁₉) | headroom_ok |
|---|---|---|---|
| **T1_scale_drift（主）** | **0.51107412** | **[0.46843293, 0.55371531]** | true |
| T2_slope_drift | **0.56758207** | **[0.56039835, 0.57476580]** | true |
| T3_background_drift | **0.39007047** | **[0.38530525, 0.39483569]** | true |

- **要求每个目标 mean baseline regret≥2δ=.10**；三目标均满足 → **executable**；**未重设环境**；**headroom 设计期实测（候选未见前）**；若未来任一目标<.10，在候选结果前重设/冻结或 `design_invalid: unreachable_gate` 停止；**不降 δ/不换 seed/不换环境救结果**。

## 3. 六比较族（每个 target 内；主 target=T1）

| id | 比较 | 角色 |
|---|---|---|
| primary | candidate（源训练）vs **P_empirical_mean_source** | 标准 source empirical mean |
| secondary_target_adapted | candidate vs **P_empirical_mean_target_adapted** | 同预算 3584 源+512 目标/动作；少量标定/重加权 |
| secondary_max_entropy | candidate vs P_max_entropy | 最大熵 |
| secondary_conditional_density_MC | candidate vs P_conditional_density_MC | 共用 C-MDN，预计 D=0，不称独立 |
| secondary_random | candidate vs P_random | 随机 |
| secondary_softmax_expected_reward | candidate vs P_softmax_expected_reward | softmax 期望 |

- **D_j=regret_candidate−regret_baseline_j**；改善 D<0；δ=**0.05**；**统一 Holm（family=6）、单侧下尾**；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05。
- **raw regret 与 paired D 分开保存**；CI 按独立 replicate（R≥20，cluster=replicate）；不用规划 MDE 当功效。
- T2/T3 为预注册次级/泛化目标：同六比较、每 target 内 Holm；不合并 target/pool；主成功仅 T1。
- **等价审计**：candidate 与 P_empirical_mean_source/P_max_entropy/P_conditional_density_MC 逐点动作/单调/解析覆盖→equivalence、停止增量；不得用目标数据训练/调参制造差异。

## 4. 执行/seeds/两跑/预算/schema/失败/停止

- **seeds**：headroom 20262011–30；执行 data **20262031**、target eval **20262032**、cell seeds **20262041–20262088**（48）；与 S2c/H1b/C216/C217/旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **失败类别 11**：projection/calibration/leakage/unreachable_gate/equivalence/precision_insufficient/two_run_mismatch/chain_mismatch/compute_budget_exceeded/no_increment/inconclusive。
- **停止**：headroom<.10（任一 target）→未见候选前重设/冻结或 unreachable_gate 停止；等价→no increment；CI 无法排除 0 或 −δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务不训练 C-MDN/不运行候选规划/不报效果。

## 5. 边界/批准清单

- 机制账 only；合成 compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 分离/旧状态不变；② 源/目标 Pθ'（3 目标）；③ 设计期 headroom 表（T1 .51107/T2 .56758/T3 .39007，均≥.10，未重设）；④ 六比较/Holm/δ/raw-vs-paired/CI/目标分层；⑤ 候选仅源训练/目标禁用训练调参；⑥ 独立 seeds/两跑/caps/schema/11 失败/停止；⑦ 边界。执行须另立独立挑战+Lead 批准。
