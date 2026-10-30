# Lead 批准：R204-M3-S3b 候选 learner 比较执行（机制账；compute-only；0 wells）

2026-10-28。依据：R204-M3-S3B.1-C1（i003）判 **approve_exec_v0_2_to_lead**；seed blocks 201、schema 可判字段、高 regret/headroom、DR 恒等、learner 合同、六比较/Holm/δ/CI/等价审计/边界均 PASS。

## 批准范围（仅 M3-S3b 执行一次）
- 批准 M3-S3b **候选 learner 比较执行**（机制账、compute-only、0 wells）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
- 冻结旧状态：C218 Stage3 `no_increment` 保留；C220“合格 M3/TMLE 比较”解释不成立；S3b 新预注册、不是重跑旧 Stage3；C208 一步投影撤；旧判定/阈值/输出不变。
- 冻结 v0.2 链：PROBLEM_M3_S3B_v0_2 `5EAB7A51…`、DESIGN `73245C43…`、headroom.py `F63135BD…`、json `E7D9EC3D…`、schema `CBD748B7…`、report `C25D1E0C…`、record `78D239A7…`；执行前重核链，不匹配→`design_invalid: chain_mismatch`。
- 环境：H=3/A=3/Y∈{0,1}；p=[.3,.4,.3]；μ/b 按 Stage2；m_wrong=.5；C_H=20；b_min=1e-6；π2' 对角 .82/非对角 .09；Q 公式与 w=Q/ΣQ；反馈按实际 w，**H=π2/w**；H_max=18.91777778<C_H 无 clipping；执行时断言 H≤C_H、不得改 π2/w 后仍用旧 H。
- headroom 2δ 门槛：P_empirical_mean 与 P_standard_DR_TMLE 的 baseline regret **.14841667 CI [.10382916,.19300417]**，≥2δ=.10；执行时按同规则核对；<.10 → 未见候选前 redesign/freeze 或 `unreachable_gate` 停止；不得降 δ/换 seed/换环境。
- learner 合同：candidate 真实 logit-fluctuation ε（per-cell weighted Bernoulli NLL、offset logit(m_hat)、weights H=π2/w、L-BFGS、score 残差<1e-6、收敛）；standard=同一 m 的解析 DR/TMLE（无 ε 更新）；**禁止 0.5+0.5*score、sigmoid(2*score)、无 NLL 变换、缩放/λ/类名制造差异**。
- 执行前 DR 恒等检查：m=μ、H=π2/w 时 exact gap=0.0<1e-10；否则 `design_invalid: propensity/calibration`。
- 六比较（family=6）：primary candidate vs P_standard_DR_TMLE；secondary P_empirical_mean/P_importance_weighting/P_full_history_retrain/P_DR_targeting/P_value_aware；D=regret_candidate−regret_baseline<0；δ=.05；统一 Holm family=6；单侧下尾；成功 mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw regret 与 paired D 分开；CI 按独立 replicate R=20（cluster=replicate，t df=19）；不用 planning MDE 当已证功效。
- 等价审计：候选与 standard/任何基线策略/单调/正仿射/解析覆盖→`equivalence`、合并/`no_increment`；候选≡standard→`no_increment`；不得用实现差异制造独立成功。
- seeds：env 20262200(1)+headroom 20262201–20(20)+feedback 20262221–40(20)+eval 20262241–60(20)+arms 20262261–2400(140)=**201**；unique/overlap=[]；不得用 181 口径；两跑同 seeds 独立进程逐字节、telemetry 单独。
- caps 1800s/2h/8GB/0 wells；执行前 final-implementation pilot 实测冻结 canonical；schema 先写；13 失败类别；JSON 无 telemetry；不输出真实数据/效果/真实决策/药理/迁移/机制/新颖性。
- 非阻塞执行备注：`all_exec_seeds_count/seed_block_counts` 在 `execution_seeds` 块（顶层同名键 null），执行器读 nested/schema；执行时程序化校验 len(EXEC_SEEDS)=201；H_max 接近 C_H 但要断言不 clipping。

## 不批准
- 真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；把 181 口径配 7 arms；把旧 Stage3 `no_increment` 改写；改 learner 合同/缩放/λ/类名；改旧判定/阈值；代码晋升；恢复已停止实验。
