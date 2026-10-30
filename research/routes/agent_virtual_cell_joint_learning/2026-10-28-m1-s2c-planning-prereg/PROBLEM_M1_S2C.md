# PROBLEM_M1_S2C —— R204-M1-S2c H1b 近似的规划价值检验预注册（先 headroom；不运行候选）

2026-10-28。对象：R204-M1 规划价值检验（M1-S2c）。依据：C208（一步投影撤）、C216（旧 H1 0/16）、C217（floor 归因）、C222（H1b 16/16 密度近似可分辨）、C220/C221 合同纠正、M1 Stage2 v0.2、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C208/C209/C213/C215/C216/C217/C220/C221/C222。
**状态：预注册草案；仅设计期 headroom 分析（冻结真值）；未训练 C-MDN、未运行候选规划、未报效果、未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。执行须另立独立挑战+Lead 批准。**

## 0. 分离（写死）

| 项 | 状态 |
|---|---|
| C216 旧 H1 | **0/16 FAIL、`design_invalid: projection` 不变** |
| C217 归因 | **oracle 有限样本 floor 归因不变** |
| H1b（C222） | **16/16 PASS 仅表示密度近似可分辨**；**不是旧 H1 通过**，不改 C216/C217 |
| 一步投影 | **仍撤（C208）**；本实验不写 M1 增量/机制/迁移/真实决策/药理/新颖性 |
| 旧容差/判定 | 不改；任何结果不改变旧判定 |

## 1. 冻结环境（与 H1b 一致）

- **Pθ**：3 分量截断 GMM；c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4·sigmoid(dᵀx)；K=3/[.5,.3,.2]；Y∈[-2,2]^4；param/train/eval seeds **20261301/20261302/20261303**。
- **X~N(0,I_d)**；主 **d=64**（预注册次级 d=16）；**A=4**。
- **reward**：r(y)=wᵀy−λ||y||²，w=[.4,.3,.2,.1]、λ=.2、**r∈[−5.2,.375]**；**τ=1**。
- **π0**：**full** = 4 动作均匀；**constrained** = 仅 {0,1} 合法（动作 2/3 无支持）。
- **规划**：每动作模型采样 **S=4096**；known-truth 用**独立解析高精度**（截断正态矩，解析），不复用训练/验证样本。
- target 样本不作标签；Doob 非可执行药物。

## 2. 设计期 headroom（先于候选结果）

- **baseline planner = P_empirical_mean**：每个合法动作从 **N_train=4096** 合成样本估计**动作级经验平均 reward**（忽略 x，标准朴素规划器）；在 **独立 eval X（N_eval=4096）** 上评价；R=**20** 独立 replicate（20261901–20）。
- **baseline regret** = 每 eval x 的真最优合法动作期望 reward − 所选动作真期望 reward，再对 eval X 平均；真值用解析截断正态矩（高精度）。
- **headroom 结果（设计期，先于候选）**：
  | π0 | mean baseline regret | 95% CI(t₁₉) | chosen actions |
  |---|---|---|---|
  | **full** | **0.22625306** | **[0.22094996, 0.23155615]** | {1,3} |
  | constrained | **0.15141651** | **[0.15007466, 0.15275836]** | {1} |
- **要求**：mean baseline regret ≥ **2δ=0.10** 才可执行。**两种 π0 均满足**；**主协议 = full**，constrained 为预注册敏感性；**未重设环境**（无需 redesign）；decision=**executable**。
- **不降 δ/不换 seed/不换环境救结果**；若未来独立复核认为 headroom 不足，则按规则重设并冻结或 `unreachable_gate` 停止。

## 3. 比较族（6；写死）

- **Primary**：candidate（H1b 通过的条件密度近似 C-MDN）vs **P_empirical_mean**。
- **Secondary**：P_max_entropy、P_conditional_density_MC、P_constrained_SB、P_random、P_softmax_expected_reward。
- **D_j = regret_candidate − regret_baseline_j**；**改善方向 D<0**；δ=**0.05**。
- **统一 Holm**（family=6），**单侧下尾**；primary 必须满足 `mean D ≤ −δ` ∧ 95% CI upper<0 ∧ Holm p<.05。
- **raw regret 与 paired D 分开保存**；CI 按**独立 replicate（≥20，cluster=replicate）**；**不用规划 MDE 当已证功效**。
- 规划 4096/动作（模型）；known-truth 独立高精度；不把 target 样本作标签。

## 4. 等价审计

- 若 candidate 的规划动作与 **P_empirical_mean 或 P_max_entropy** 等价（策略逐点相同/单调变换/解析覆盖）→ 登记 **equivalence**、停止增量主张；不得以不同实现制造差异。
- 标准方法等预算复制/超过→`no_increment`/撤；不称分配/规划新颖性。

## 5. 执行/预算/失败/停止

- **独立 seeds**：headroom 20261901–20；执行数据 **20261921**、eval **20261922**、cell seeds **20261931–20261954**（24 个）；与 H1b/C216/C217/旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- **caps** 1800 s/2 h/8 GB/0 wells；执行前**最终实现 pilot 实测并冻结 canonical timing**；schema/失败模板先写；JSON 无 telemetry。
- **失败类别**：`design_invalid: projection|calibration|leakage|unreachable_gate|equivalence|precision_insufficient|two_run_mismatch|chain_mismatch|compute_budget_exceeded`、`no_increment`、`inconclusive`。
- **停止**：headroom<δ→不运行；等价→no increment；CI 无法排除 0 或 −δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 不输出真实决策/药理/机制/迁移/新颖性；H1b/本实验不写成旧 H1 通过。

## 6. 边界

机制账 only；合成 compute-only、0 wells；不训练 C-MDN/不运行候选规划/不报效果（本任务）；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。
