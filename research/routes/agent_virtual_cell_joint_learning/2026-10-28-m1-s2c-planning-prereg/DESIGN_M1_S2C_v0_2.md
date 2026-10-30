# DESIGN_M1_S2C_v0_2 —— R204-M1-S2C.1 规划价值执行设计（headroom 阈值 .10；不运行候选）

2026-10-28。依据：[PROBLEM_M1_S2C_v0_2.md](PROBLEM_M1_S2C_v0_2.md)、`headroom_design_m1_s2c_v0_2.json`、`schema_m1_s2c_v0_2.json`、H1b/C222、C216/C217、C220/C221、M1 Stage2 v0.2。
**状态：预注册修订设计 v0.2；仅设计期 headroom（冻结真值）；未训练 C-MDN/未运行候选规划/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 分离/前置（不变）

- C216 旧 H1 0/16、`design_invalid: projection`、C217 归因、旧容差/判定**不变**；H1b 16/16 仅密度可分辨、不是旧 H1 通过；一步投影仍撤（C208）。
- 本任务仅 design-time headroom；不训练 C-MDN/不运行候选规划/不报效果。
- 冻结环境同 H1b：Pθ（c .5²/M .1²/d .1²、σ、box[-2,2]^4、K=3/[.5,.3,.2]、seeds 20261301/02/03）；X~N(0,I_d)，主 d=64（次级 d=16）；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；π0 full/constrained；规划 S=4096/动作；known-truth 解析截断正态矩（高精度）。

## 1. headroom 阈值（统一 .10）

- **baseline planner = P_empirical_mean**：每合法动作 N_train=4096 合成样本的动作级经验平均 reward（忽略 x）；独立 eval X=4096；R=20（20261901–20）；真值解析。
- **结果**：full **0.22625306** CI **[0.22094996,0.23155615]**；constrained **0.15141651** CI **[0.15007466,0.15275836]**；均 **≥0.10** → **executable**；**未重设环境**。
- **写死字段**：`headroom_required=0.10`、`headroom_decision_rule="execute only if mean baseline regret >=0.10 (2δ); <0.10 → redesign/freeze before candidate or design_invalid: unreachable_gate stop"`、`headroom_stop_category="design_invalid: unreachable_gate"`；执行器按 .10 判，**不按 .05**。
- **headroom 设计期实测（候选未见前）**；若未来重设，必须在候选结果前记录并冻结新环境；**不得用候选结果反选**。
- **停止条件[0]**：headroom<2δ=.10 → 重设并冻结环境或 `design_invalid: unreachable_gate` 停止，不执行；不得降 .10 为 .05。

## 2. 执行时设计（本次不运行）

- Candidate C-MDN 结构/训练按 M1 Stage2 v0.2 冻结；规划 4096/动作；合法动作按 π0。
- 六比较族：primary candidate vs P_empirical_mean；secondary P_max_entropy/P_conditional_density_MC/P_constrained_SB/P_random/P_softmax_expected_reward；D=regret_cand−regret_base<0；δ=.05；Holm family=6、单侧下尾；raw regret 与 paired D 分存；CI 独立 replicate（R≥20，cluster=replicate）；不用规划 MDE 当功效。
- 等价审计：candidate 与 empirical-mean/max-entropy 逐点/单调/解析覆盖→equivalence/no increment；标准方法等预算复制/超过→no_increment/撤；不得实现差异制造增量。

## 3. seeds/两跑/预算/schema

- headroom 20261901–20；执行数据 **20261921**、eval **20261922**、cells **20261931–54**；与旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- 失败类别 11（projection/calibration/leakage/unreachable_gate/equivalence/precision_insufficient/two_run_mismatch/chain_mismatch/compute_budget_exceeded/no_increment/inconclusive）。
- 停止：headroom<.10（2δ）不执行/重设或 unreachable_gate；等价 no increment；CI 无法排除 0/−δ inconclusive；标准方法复制/超过 no_increment/撤；超 caps compute_budget_exceeded；任何失败不改旧判定。

## 4. 边界/批准清单

- 机制账 only；合成 compute-only、0 wells；不训练 C-MDN/不运行候选规划/不报效果（本任务）；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 旧/新分离；② 冻结环境；③ **headroom 阈值统一 .10**、字段/停止类别；④ headroom 值 full .22625/CI、constrained .15142/CI、未重设；⑤ 六比较/Holm/δ/raw-paired/CI/等价；⑥ seeds/两跑/caps/schema/11 失败/停止；⑦ 边界。执行须另立独立挑战+Lead 批准。
