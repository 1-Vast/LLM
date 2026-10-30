# PROBLEM_M3_S3B —— R204-M3-S3b 修正合同的高 regret 固定反馈 learner 比较预注册（先 headroom；不运行候选）

2026-10-28。对象：R204-M3-S3b 高 regret 固定反馈 learner 比较预注册。依据：M3 Stage3 `no_increment`（C218）与 C220/C221 合同纠正、NEXT_EXPERIMENT、M3 Stage1/C209、Stage2/C213、M3 v0.2、R204 BRIEF/report。
**状态：预注册草案；仅设计期 headroom（合成、机制账）；未训练/未运行候选、未报效果、未读真实数据；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。执行须另立独立挑战+Lead 批准。**

## 0. 分离/纠正（写死）

| 项 | 状态 |
|---|---|
| M3 Stage3 冻结输出 | **`no_increment` 保留、不修改**（C218） |
| C220 解释 | 原“合格 M3/TMLE 算法比较”解释**不成立**；保留为 errata，不新增算法失败/成功结论 |
| S3b 定位 | **新预注册**，不是重跑旧 Stage3 配置；旧判定/阈值/输出**不变** |
| 一步投影 | 仍撤（C208）；不恢复；M3 不与 M1/M2 混同；N1 不作证据 |
| 声明边界 | 仅合成机制账；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码 |

## 1. 高 regret 环境（设计期；先于候选）

- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b 沿用 Stage2；m_wrong=.5；C_H=20；b_min=1e-6。
- **高 regret 目标/覆盖设计**：π2' 对角 **.82**、非对角 **.09**；shared-score allocation `Q=p·π2'²·[Var+(μ−m_wrong)²]/b`，`w=Q/Σ Q`；反馈按 **实际 w** 采样；`H=π2'/w`；**H_max=18.9178<C_H=20，无 clipping**；support b>0、b≥1e-6、Q finite、w>0。
- **高 regret 理由**：目标/覆盖集中在 diagonal 动作，而 μ-最优动作多为 off-diagonal；baseline 很少看到最优动作、缺省 m=.5 → baseline regret 高。
- **设计期 headroom（候选未见前）**：R=20（20262201–20262220）、300 feedback/rep、300 eval contexts；known-truth μ。
  | baseline | mean baseline regret | 95% CI(t₁₉) |
  |---|---|---|
  | **P_empirical_mean** | **0.14841667** | **[0.10382916, 0.19300417]** |
  | **P_standard_DR_TMLE**（same m, analytic DR no ε） | **0.14841667** | **[0.10382916, 0.19300417]** |
- **要求 mean baseline regret≥2δ=.10**；两者均满足 → **executable**；**未重设环境**；headroom 设计期实测、不得用候选结果反选；若未来 <.10 → 未见候选前重设/冻结或 `unreachable_gate`；**不降 δ/不换 seed/不换环境救结果**。
- **DR 恒等**：`V_target=Σ_h p_h Σ_a π2 μ`；m=μ、H=π2/w 时 `E[(π2/w)1{a}(Y−μ)]=0`，**exact gap=0.0<1e-10**；H 用实际 w，不用旧 b。

## 2. Learner 合同（写死）

- **m_hat**：cell empirical mean Y（n=0 时 .5）；candidate 与 standard **同一 m**。
- **Candidate**：真实 logit-fluctuation ε：对每 cell 用 **weighted Bernoulli NLL**（offset `logit(m_hat)`、权重 `H=π2/w`）拟合 ε；**L-BFGS**；**score residual `|Σ H(Y−σ(z+ε))|/ΣH <1e-6`**；收敛判据；`m_ε=σ(logit(m_hat)+ε)`；ε 未收敛→`design_invalid: calibration`。
- **Standard**：同一 m 的**解析 DR/TMLE，无 ε 更新**；`V_std=m_hat+H·mean(Y−m_hat)`（采样 cell）。
- **禁止**：`0.5+0.5*score`、`sigmoid(2*score)`、无 NLL/优化器的 sigmoid 变换、用类名/缩放/λ 制造差异；**不得把 candidate 与 standard 的差异归因于实现**。
- 概率：反馈按实际 w 采样，`H=π2/w`；背景改变用联合密度比；**不得用旧 b 作分母**。
- 分离：generator truth/training feedback/validation/final evaluator 隔离；raw R 与 paired D 分开保存。

## 3. 六比较/等价/统计

- **Family=6**（planned）：primary **candidate vs P_standard_DR_TMLE**；secondary P_empirical_mean、P_importance_weighting、P_full_history_retrain、P_DR_targeting、P_value_aware（公式见 DESIGN；等价类见下）。
- `D_j=R_candidate−R_baseline_j`；改善 **D<0**；δ=**0.05**；**统一 Holm family=6**、**单侧下尾**；primary 成功=mean D≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；**raw/paired 分存**；CI 按独立 replicate R=**20**（cluster=replicate，t df=19）；**不用 planning MDE 当已证功效**；不换端点。
- **等价审计**：candidate 与任何 baseline 策略/单调变换/正仿射/解析覆盖→**equivalence**、合并等价类、停止增量主张；不得用实现/缩放差异制造独立成功；候选≡standard→no_increment。
- 等价类预注册：P_empirical_mean vs P_full_history_retrain（同 m）；P_standard_DR_TMLE vs P_DR_targeting（同解析 DR）；P_empirical_mean vs P_importance_weighting（H 常数时）；P_value_aware 的仿射/argmax。等价合并**不增加独立成功**；family 仍按 6 个 planned 比较统一 Holm（保守）。

## 4. 执行/seeds/两跑/caps/schema/失败/停止

- **独立 seeds（20262200+）**：env **20262200**；headroom **20262201–20262220**；feedback **20262221–20262240**；evaluation **20262241–20262260**；arms **20262261+20a+r**（a=0..6，r=0..19）；与旧集 **overlap=[]**、unique=true（forbidden ranges 见 JSON）。
- 两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独；caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **13 失败类别**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/chain_mismatch/unreachable_gate/precision_insufficient/no_increment/inconclusive。
- **停止**：headroom<.10（任一 required baseline）→未见候选前重设/冻结或 `unreachable_gate`；等价→no_increment/停止增量；DR identity gap≥1e-10→design_invalid: propensity/calibration；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务**不训练/不运行候选**。

## 5. 边界

仅合成机制账；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/容差；Stage3 no_increment 保留；S3b 不重跑旧 Stage3；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。
