# DESIGN_M1_S2C —— R204-M1-S2c 规划价值执行设计（先 headroom；不运行候选）

2026-10-28。依据：[PROBLEM_M1_S2C.md](PROBLEM_M1_S2C.md)、`headroom_design_m1_s2c.json`、`schema_m1_s2c.json`、H1b/C222、C216/C217、C220/C221 合同纠正、M1 Stage2 v0.2。
**状态：预注册设计草案；仅设计期 headroom（冻结真值）；未训练 C-MDN/未运行候选规划/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 分离/前置

- C216 旧 H1 0/16、C217 归因、旧容差/判定**不变**；H1b 16/16 **仅密度可分辨**，不是旧 H1 通过；**一步投影仍撤（C208）**。
- 本任务只做 **design-time headroom**；不训练 C-MDN、不运行候选规划、不报效果。
- 冻结环境同 H1b：Pθ（c .5²/M .1²/d .1²、σ=.1+.4sigmoid(dᵀx)、box[-2,2]^4、K=3/[.5,.3,.2]）；X~N(0,I_d)；主 d=64；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；π0 full（4 动作均匀）/constrained（仅 {0,1}）；规划 MC S=4096/动作；known-truth 独立解析截断正态矩（高精度）。

## 1. headroom 设计（已计算；先于候选）

- **P_empirical_mean baseline**：每个合法动作从 **N_train=4096** 合成样本估计动作级经验平均 reward（忽略 x，标准朴素规划器）；独立 **eval X（N_eval=4096）** 上评价；R=**20** replicate（20261901–20）；真值解析高精度；regret=真最优合法动作期望 reward − 所选动作真期望 reward，对 eval X 平均。
- **结果**：
  | π0 | mean baseline regret | 95% CI(t₁₉) | chosen actions |
  |---|---|---|---|
  | **full（主）** | **0.22625306** | **[0.22094996, 0.23155615]** | {1,3} |
  | constrained（敏感性） | **0.15141651** | **[0.15007466, 0.15275836]** | {1} |
- **gate**：mean baseline regret ≥ **2δ=0.10**；两 π0 均满足 → **executable**，未重设环境；**不降 δ/不换 seed/不换环境救结果**。
- **若未来 headroom<0.10**：在未见候选结果前重设并冻结环境（记录全部选择）或 `unreachable_gate` 停止；不得事后降 δ/换 seed。

## 2. 执行时设计（本次不运行）

### 2.1 Candidate

- C-MDN 结构/训练按 M1 Stage2 v0.2 冻结：K=3 logits+mean4+diag log-scale4；hidden128、2 ReLU；NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；H1b 通过的近似版本；**不称一步投影**。
- 规划：对每个 eval x，候选核采样 **S=4096/动作**，估计每动作期望 reward，选最大；合法动作按 π0（full/constrained）。

### 2.2 六比较族

| id | 角色 | 规划器 |
|---|---|---|
| primary | 候选 vs P_empirical_mean | 动作级经验平均 reward（N_train=4096/动作；忽略 x） |
| secondary_1 | P_max_entropy | 最大熵/闭式倾斜标准规划 |
| secondary_2 | P_conditional_density_MC | 条件密度 + MC |
| secondary_3 | P_constrained_SB | constrained Schrödinger bridge |
| secondary_4 | P_random | 随机合法动作 |
| secondary_5 | P_softmax_expected_reward | softmax 期望 reward |

- **D_j=regret_candidate−regret_baseline_j**；改善 D<0；δ=**0.05**；统一 **Holm family=6**、**单侧下尾**；primary 成功=mean D≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05。
- **raw regret 与 paired D 分开保存**；CI 按独立 replicate（R≥20，cluster=replicate）；**不用规划 MDE 当已证功效**。
- 每 planner 同成本/合法动作集/信息；target 样本不作标签；不把 H1b 密度通过当规划价值。

### 2.3 等价审计

- candidate 与 P_empirical_mean/P_max_entropy 动作逐点相同/单调/解析覆盖→登记 **equivalence**、停止增量主张；标准方法等预算复制/超过→`no_increment`/撤；不得用不同实现制造差异。

## 3. 执行 seeds/两跑/预算

- **headroom seeds**：20261901–20（已用；设计期）。
- **执行 seeds**：数据 **20261921**、eval **20261922**、cell seeds **20261931–20261954**（24 个）；与 H1b/C216/C217/旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前**最终实现 pilot 实测并冻结 canonical timing**；schema/失败模板先写；JSON 无 telemetry。
- 结果 schema：per-cell（replicate/planner/raw_regret/D_vs_baseline/pass）、raw 与 paired 分存、run_shas、failure_category。

## 4. 失败/停止

- 失败类别：`design_invalid: projection|calibration|leakage|unreachable_gate|equivalence|precision_insufficient|two_run_mismatch|chain_mismatch|compute_budget_exceeded`、`no_increment`、`inconclusive`。
- 停止：headroom<0.10→不运行；等价→no increment；CI 无法排除 0 或 −δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 不输出真实决策/药理/机制/迁移/新颖性；不把 H1b/本实验写成旧 H1 通过。

## 5. 边界/批准清单

- 机制账 only；合成 compute-only、0 wells；不训练 C-MDN/不运行候选规划/不报效果（本任务）；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 旧/新分离；② 冻结环境；③ headroom 结果（full .22625/CI、constrained .15142/CI，均≥.10，未重设）；④ 六比较族/Holm/δ/raw-vs-paired/CI；⑤ 等价审计；⑥ 独立 seeds/两跑/caps/schema/failure/stop；⑦ 边界。执行须另立独立挑战+Lead 批准。
