# DESIGN_M3_S3B_v0_2 —— R204-M3-S3B.1 seed 计数 201/7 arms 执行设计（不运行候选）

2026-10-28。依据：[PROBLEM_M3_S3B_v0_2.md](PROBLEM_M3_S3B_v0_2.md)、`headroom_design_m3_s3b_v0_2.json`、`schema_m3_s3b_v0_2.json`、M3 Stage3 no_increment（C218）+ C220/C221、NEXT_EXPERIMENT、M3 Stage1/C209、Stage2/C213。
**状态：预注册修订设计 v0.2；仅设计期 headroom（合成、机制账）；未训练/未运行候选、未报效果、未读真实数据；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 分离/纠正（不变）

- M3 Stage3 **`no_increment` 冻结保留**；C220 原“合格 M3/TMLE 比较”解释**不成立**；S3b 新预注册、非重跑旧配置；旧判定/阈值/输出不改；一步投影仍撤（C208）。
- 本任务仅设计期 headroom；不训练/不运行候选。

## 1. 高 regret 环境/headroom（不变）

- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b 沿用 Stage2；m_wrong=.5；C_H=20；b_min=1e-6；π2' 对角 .82/非对角 .09；`Q=p·π2'²·[Var+(μ−m_wrong)²]/b`；`w=Q/ΣQ`；feedback 按实际 w；`H=π2'/w`；H_max=18.9178<C_H（无 clipping）；support/positivity 通过。
- 设计期 headroom（R=20 seeds 20262201–20；300 feedback；300 eval；known truth）：P_empirical_mean **.14841667 CI [.10382916,.19300417]**；P_standard_DR_TMLE **.14841667 同 CI**；均≥.10 → executable；未重设；设计期实测、不用候选结果反选；<.10→重设/冻结或 unreachable_gate；不降 δ/不换 seed/环境。
- DR identity：m=μ、H=π2/w 时 correction expectation=0；exact gap **0.0<1e-10**；不用旧 b。

## 2. Seed blocks / counts（必改 1–2）

| block | seeds | count |
|---|---|---|
| env | 20262200 | 1 |
| headroom | 20262201–20262220 | 20 |
| feedback | 20262221–20262240 | 20 |
| evaluation | 20262241–20262260 | 20 |
| arms | 20262261–20262400（20262261+20a+r；a=0..6，r=0..19） | 140 |
| **total** | — | **201** |

- **EXEC_SEEDS 由上述 blocks 组成**（env + headroom + feedback + eval + arms）；`all_exec_seeds_count=len(EXEC_SEEDS)=201`；**n_arms=7、n_arm_seeds=140、n_exec_seeds=201** 写入 JSON/schema/output；`seed_block_counts` 由 blocks 计算；`unique=true`、`overlap=[]`。
- 旧 v0.1 的 181 是**遗漏 headroom 20** 的错误计数，作废；不得同时保留 7 arms/140 seeds 与 181；不采用删 arm 方案；family=6 不变。
- forbidden ranges 见 JSON；与所有旧集 disjoint；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。

## 3. Learner 合同（不变）

- m_hat：cell mean Y（n=0→.5）；candidate 与 standard 同 m。
- Candidate：per-cell weighted Bernoulli NLL（offset logit(m_hat)、weights H=π2/w）拟合真实 logit-fluctuation ε；L-BFGS；score residual<1e-6；收敛；`m_ε=σ(logit m_hat+ε)`。
- Standard：same m、analytic DR/TMLE、no ε；`V_std=m_hat+H·mean(Y−m_hat)`。
- 禁止 `0.5+0.5*score`、`sigmoid(2*score)`、无 NLL/优化器的 sigmoid、用缩放/λ/类名制造差异；H 用实际 w，不用旧 b。

## 4. 六比较/等价/统计（不变）

- Family=6 planned：primary candidate vs P_standard_DR_TMLE；secondary P_empirical_mean/P_importance_weighting/P_full_history_retrain/P_DR_targeting/P_value_aware。
- D<0；δ=.05；Holm family=6、单侧下尾；success mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；CI R=20 cluster=replicate t(df=19)；不用 planning MDE 当功效；不换端点。
- 等价审计：candidate vs baseline 策略/单调/正仿射/解析覆盖→equivalence、合并等价类、停止增量；候选≡standard→no_increment；不得用实现差异制造独立成功。

## 5. 执行/预算/schema/失败/停止（不变）

- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- 13 失败类别：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/chain_mismatch/unreachable_gate/precision_insufficient/no_increment/inconclusive。
- 停止：headroom<.10→重设/冻结或 unreachable_gate；等价→no_increment；DR gap≥1e-10→design_invalid: propensity/calibration；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务不训练/不运行候选。

## 6. 边界/批准清单

- 合成机制账 only；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 no_increment 保留；不重跑旧 Stage3；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 分离/纠正；② seed blocks 201（env1+headroom20+feedback20+eval20+arms140）、n_arms/n_arm_seeds/n_exec_seeds、unique/overlap；③ 高 regret/headroom .14841667 CI [.10382916,.19300417]；④ DR gap 0.0/H=π2/w；⑤ learner 合同；⑥ 六比较/Holm/δ/raw-paired/CI；⑦ 等价审计；⑧ caps/schema/13 失败/停止/边界。执行须另立独立挑战+Lead 批准。
