# DESIGN_M3_S3B —— R204-M3-S3b 修正合同的高 regret 固定反馈 learner 比较执行设计（先 headroom；不运行候选）

2026-10-28。依据：[PROBLEM_M3_S3B.md](PROBLEM_M3_S3B.md)、`headroom_design_m3_s3b.json`、`schema_m3_s3b.json`、M3 Stage3 `no_increment`（C218）+ C220/C221 纠正、NEXT_EXPERIMENT、M3 Stage1/C209、Stage2/C213、M3 v0.2。
**状态：预注册设计草案；仅设计期 headroom（合成、机制账）；未训练/未运行候选、未报效果、未读真实数据；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 分离/纠正（写死）

- M3 Stage3 `no_increment`（C218）**冻结保留**；C220 原“合格 M3/TMLE 比较”解释**不成立**；S3b 是**新预注册**、不是重跑旧 Stage3；旧判定/阈值/输出不改；一步投影仍撤（C208）。
- 本任务仅设计期 headroom；不训练/不运行候选。

## 1. 高 regret 环境/headroom（已计算；先于候选）

- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b 沿用 Stage2；m_wrong=.5；C_H=20；b_min=1e-6。
- **π2' 对角 .82、非对角 .09**；`Q=p·π2'²·[Var+(μ−m_wrong)²]/b`；`w=Q/ΣQ`；反馈按 **实际 w** 采样；`H=π2'/w`；H_max=**18.9178**<C_H=20（无 clipping）；support b>0、b≥1e-6、Q finite、w>0。
- **设计期 headroom**（R=20 seeds 20262201–20；300 feedback/rep；300 eval contexts；known truth）：
  | baseline | mean | 95% CI(t₁₉) |
  |---|---|---|
  | P_empirical_mean | **.14841667** | **[.10382916,.19300417]** |
  | P_standard_DR_TMLE（same m，analytic DR no ε） | **.14841667** | **[.10382916,.19300417]** |
- 均≥2δ=.10 → **executable**；未重设环境；headroom 为设计期实测，不用候选结果反选；若未来<.10 → 未见候选前重设/冻结或 `unreachable_gate`；不降 δ/不换 seed/环境。
- **DR 恒等**：`V_target=Σ_h p_h Σ_a π2 μ`；m=μ、H=π2/w 时 correction expectation=0；exact gap **0.0<1e-10**；实测 w 不使用旧 b。

## 2. Learner 合同（执行时实现；写死）

- **m_hat**：cell mean Y，n=0 时 .5；candidate 与 standard 同 m。
- **Candidate**：per-cell weighted Bernoulli NLL with offset `logit(m_hat)`、weights `H=π2/w`；fit scalar ε by **L-BFGS**；`m_ε=σ(logit(m_hat)+ε)`；score residual `|Σ H(Y−σ(z+ε))|/ΣH <1e-6`；收敛判据不满足→`design_invalid: calibration`。
- **Standard**：same m，analytic DR/TMLE，**no ε**；`V_std(h,a)=m_hat(h,a)+H(h,a)·mean_{cell}(Y−m_hat(h,a))`（n=0→.5）。
- **禁止**：`0.5+0.5*score`、`sigmoid(2*score)`、无 NLL/优化器的 sigmoid、用 λ/缩放/类名制造差异；不得把实现差异当方法增量。
- 概率：feedback 按 actual w，H=π2/w；背景改变用 joint density ratio；**不得用旧 b 做分母**。
- 分离：truth/feedback/validation/final evaluator 隔离；raw R 与 paired D 分存。

## 3. 六比较/等价/统计

- **Family=6 planned**：
  1. primary：candidate vs **P_standard_DR_TMLE**（analytic DR/TMLE no ε）。
  2. P_empirical_mean（cell mean）。
  3. P_importance_weighting（H-weighted mean `ΣHY/ΣH`）。
  4. P_full_history_retrain（all-history cell mean；同 m；待等价审计）。
  5. P_DR_targeting（one-step analytic DR targeting no ε；待等价审计）。
  6. P_value_aware（m_hat shrink toward .5，affine；待等价审计）。
- `D_j=R_candidate−R_baseline_j`；D<0；δ=.05；**Holm family=6、单侧下尾**；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；CI R=20 cluster=replicate t(df=19)；不用 planning MDE 当功效；不换端点。
- **等价审计**：candidate vs each baseline 的策略/单调/正仿射/解析覆盖→equivalence、合并等价类、停止增量；候选≡standard→no_increment；不得用实现差异制造独立成功。等价类预注册：full-history≡empirical(mean)（同 m）；DR targeting≡standard（同解析 DR）；value-aware 正仿射→argmax 同；若合并，不增加独立成功主张，family 仍按 6 planned Holm（保守）。
- 六比较基线均同反馈/同预算/同合法动作/同评价；target 样本不作标签。

## 4. 执行/seeds/两跑/caps/schema/失败/停止

- seeds（20262200+）：env 20262200；headroom 20262201–20；feedback 20262221–40；evaluation 20262241–60；arms **20262261+20a+r**（a=0..6,r=0..19）；forbidden ranges 见 JSON；overlap=[]、unique=true。
- 两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独；caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **13 失败类别**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/chain_mismatch/unreachable_gate/precision_insufficient/no_increment/inconclusive。
- **停止**：headroom<.10→重设/冻结或 unreachable_gate；等价→no_increment；DR gap≥1e-10→design_invalid: propensity/calibration；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务不训练/不运行候选。

## 5. 边界/批准清单

- 合成机制账 only；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 no_increment 保留；不重跑旧 Stage3；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 分离/纠正；② 高 regret 环境 + headroom 值（P_empirical_mean/standard DR .14842 CI [.10383,.19300]）；③ DR identity gap 0.0<1e-10、H=π2/w 无用旧 b；④ learner 合同（真实 ε NLL/L-BFGS/score<1e-6；standard no ε；禁假变换）；⑤ 六比较/Holm/δ/raw-paired/CI；⑥ 等价审计；⑦ seeds/两跑/caps/schema/13 失败/停止；⑧ 边界。执行须另立独立挑战+Lead 批准。
