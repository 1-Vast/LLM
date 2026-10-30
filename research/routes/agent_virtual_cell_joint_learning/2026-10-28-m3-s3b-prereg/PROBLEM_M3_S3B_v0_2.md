# PROBLEM_M3_S3B_v0_2 —— R204-M3-S3B.1 seed 计数 201/7 arms 可判字段（不运行候选）

2026-10-28。对象：R204-M3-S3b 高 regret 固定反馈 learner 比较预注册。本文件修正 v0.1（[PROBLEM_M3_S3B.md](PROBLEM_M3_S3B.md)，保留不改），落实 M3-S3B-C1 必改：**`all_exec_seeds_count` 181→201**（补齐 headroom 20），并写入 **n_arms=7 / n_arm_seeds=140 / n_exec_seeds=201** 可判字段；**不训练/不拟合候选、不运行效果**。依据：Stage3 no_increment（C218）、C220/C221 纠正、NEXT_EXPERIMENT、M3 Stage1/C209、Stage2/C213。
**状态：预注册修订草案 v0.2；仅设计期 headroom（合成、机制账）；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。执行须另立独立挑战+Lead 批准。**

## 0. M3-S3B-C1 必改落实

| # | 矛盾 | v0.2 修正 |
|---|---|---|
| ① **seed 计数 181 vs 201** | v0.1 `all_exec_seeds_count=181`；但 7 arms×20=140 → 应为 env1+headroom20+feedback20+eval20+arm140=**201**；181 与 7 arms/140 seeds/family=6 不一致 | **`EXEC_SEEDS` 补入 headroom 20 seeds**：env 20262200 + headroom 20262201–20 + feedback 20262221–40 + eval 20262241–60 + arms 20262261–2400（7×20）= **201**；`all_exec_seeds_count=201`；**保留 7 arms**，family=6 不变；不采用删 arm 方案 |
| ② **schema/JSON 可判字段** | — | 新增 **`n_arms=7`、`n_arm_seeds=140`、`n_exec_seeds=201`**；`all_exec_seeds_count` 由 blocks 程序化生成（len(EXEC_SEEDS)）；`seed_block_counts` = {env1,headroom20,feedback20,evaluation20,arms140}；schema/report/record 同步；`unique=true`、`overlap=[]` 保持 |
| ③ 保持 | — | 分离/纠正；高 regret 环境（H3/A3/Y binary、p=[.3,.4,.3]、π2' .82/.09、H=π2/w、H_max=18.91778<C_H 无 clipping）；DR gap=0<1e-10；headroom **P_empirical_mean/P_standard_DR_TMLE .14841667 CI [.10382916,.19300417]**；learner 合同（真实 ε NLL/L-BFGS/score<1e-6；standard same m no ε；禁假变换）；六比较/Holm6/δ=.05/单侧下尾/raw-paired/CI R=20/等价审计；seeds env 20262200/headroom 20262201–20/feedback 20262221–40/eval 20262241–60/arms 20262261–2400；两跑/caps 1800 s/2 h/8 GB/0 wells/schema/13 失败/停止/边界 |

## 1. 分离/纠正（不变）

- M3 Stage3 **`no_increment` 冻结保留**；C220 原“合格 M3/TMLE 比较”解释**不成立**；S3b 是新预注册、非重跑旧 Stage3；旧判定/阈值/输出不改；一步投影仍撤（C208）。
- 仅合成机制账；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码。

## 2. 高 regret 环境/headroom（不变）

- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b 沿用 Stage2；m_wrong=.5；C_H=20；b_min=1e-6；**π2' 对角 .82/非对角 .09**；Q 公式；`w=Q/ΣQ`；反馈按实际 w；`H=π2/w`；H_max=18.9178<C_H（无 clipping）；support/positivity 通过。
- 设计期 headroom（R=20 seeds 20262201–20；300 feedback/rep；300 eval；known truth）：
  | baseline | mean | 95% CI(t₁₉) |
  |---|---|---|
  | P_empirical_mean | **.14841667** | **[.10382916,.19300417]** |
  | P_standard_DR_TMLE（same m，analytic DR no ε） | **.14841667** | **[.10382916,.19300417]** |
- 均≥2δ=.10 → **executable**；未重设环境；设计期实测、不用候选结果反选；若未来<.10→重设/冻结或 unreachable_gate；不降 δ/不换 seed/环境。
- DR 恒等：m=μ、H=π2/w，correction expectation=0；exact gap **0.0<1e-10**；H 用实际 w、不用旧 b。

## 3. Learner 合同（不变）

- Candidate：per-cell **weighted Bernoulli NLL**（offset logit(m_hat)、weights H=π2/w）拟合真实 logit-fluctuation ε；**L-BFGS**；score residual `<1e-6`；收敛；`m_ε=σ(logit m_hat+ε)`。
- Standard：same m、analytic DR/TMLE、**no ε**；`V_std=m_hat+H·mean(Y−m_hat)`。
- **禁止** `0.5+0.5*score`、`sigmoid(2*score)`、无 NLL/优化器的 sigmoid、用缩放/λ/类名制造差异；不得用旧 b 作 H 分母。
- 分离：truth/feedback/validation/final evaluator 隔离；raw R 与 paired D 分存。

## 4. 六比较/等价/统计（不变）

- Family=6 planned：primary candidate vs **P_standard_DR_TMLE**；secondary P_empirical_mean、P_importance_weighting、P_full_history_retrain、P_DR_targeting、P_value_aware。
- D=regret_cand−regret_base<0；δ=.05；**Holm family=6、单侧下尾**；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；CI R=20 cluster=replicate t(df=19)；不用 planning MDE 当功效；不换端点。
- 等价审计：candidate vs 各 baseline 策略/单调/正仿射/解析覆盖→equivalence、合并等价类、停止增量；候选≡standard→no_increment；不得用实现差异制造独立成功。

## 5. 执行/seeds/两跑/caps/schema/失败/停止

- **独立 seeds（20262200+）**：
  | block | seeds | count |
  |---|---|---|
  | env | 20262200 | 1 |
  | headroom | 20262201–20262220 | 20 |
  | feedback | 20262221–20262240 | 20 |
  | evaluation | 20262241–20262260 | 20 |
  | arms | 20262261–20262400（20262261+20a+r；a=0..6，r=0..19） | 140 |
  | **total** | — | **201** |
- forbidden ranges 见 JSON；**overlap=[]、unique=true**；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独；caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **13 失败类别**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/chain_mismatch/unreachable_gate/precision_insufficient/no_increment/inconclusive。
- **停止**：headroom<.10→重设/冻结或 unreachable_gate；等价→no_increment；DR gap≥1e-10→design_invalid: propensity/calibration；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务**不训练/不运行候选**。

## 6. 边界

仅合成机制账；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/容差；Stage3 no_increment 保留；S3b 不重跑旧 Stage3；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。
