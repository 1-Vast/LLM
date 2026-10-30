# Lead 批准：R204-M1-S2d 错配/背景漂移规划比较执行（机制账；compute-only；0 wells）

2026-10-28。依据：R204-M1-S2D.2-C1（i003）判 **approve_exec_v0_3_to_lead**；T3 重划、forbidden 10 ranges/533 去重/overlap=[]/disjoint、60 cells/R20、schema 五字段、T2 4093、headroom/六比较/δ/Holm/等价审计/边界均 PASS。

## 批准范围（仅 M1-S2d 执行一次）
- 批准 M1-S2d **错配/背景漂移规划比较执行**（机制账、compute-only、0 wells）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
- 冻结旧状态：S2c 不改；C216 旧 H1 0/16 `design_invalid: projection`、C217 归因、H1b 16/16 仅密度、C208 一步投影撤——全部不变。
- 冻结 v0.3 链：PROBLEM_M1_S2D_v0_3 `33EE4312…`、DESIGN `58E26FB0…`、headroom.py `34B92436…`、json `B4C99ADD…`、schema `5C6D95D9…`、report `85EBB593…`、record `A6882D76…`；执行前重核链，不匹配→`design_invalid: chain_mismatch`。
- 冻结环境：源 Pθ 同 H1b/S2c；目标 T1 c'~N(0,1.0²) seed20262001（主）、T2 M'~N(0,.2²) seed20262002、T3 X'~N(0,1.5²I)；X d=64/A=4/r=wᵀy−λ||y||²/π0 按预注册、S=4096/动作；**候选仅在源 Pθ 训练，目标数据禁用训练/调参**（目标只评价 + adapted baseline 512/动作标定）；known-truth 用目标 Pθ' 解析。
- headroom 2δ 门槛：T1 **.51107412 CI [.46843293,.55371531]**、T2 **.56758207 CI [.56039835,.57476580]**、T3 **.39007047 CI [.38530525,.39483569]**，均≥2δ=.10；执行时按同规则核对；**任一 target headroom<2δ=.10 → 未见候选前 redesign/freeze 或 `design_invalid: unreachable_gate` 停止，不执行**；不得降 δ/换 seed/换环境救结果。
- 执行 cells：T1 20262041–60、T2 20262061–80、T3 20262141–60（每 target R=20、共 60）；**20262100 不用**、M2 Stage3 20262100–39 保留；10 forbidden ranges/533 去重/overlap=[]；headroom 20262011–30、data 20262031、eval 20262032。
- 六比较：primary candidate vs P_empirical_mean_source；secondary target-adapted empirical mean（3584 源+512 目标/动作，同预算）、P_max_entropy、P_conditional_density_MC（共用 C-MDN，D=0 不称独立）、P_random、P_softmax_expected_reward；D=regret_candidate−regret_baseline<0；δ=.05；统一 Holm family=6；单侧下尾；成功 mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw regret 与 paired D 分开保存；CI 按每 target 独立 replicate R=20、cluster=replicate；T2/T3 每 target 内 Holm、不合并/pool、主成功仅 T1；不用规划 MDE 当已证功效。
- 等价审计：candidate 与 empirical-mean/max-entropy/conditional-density 逐点/单调/解析等价→`equivalence`、停止增量；不得用目标数据训练/调参制造差异。
- 两跑同 seeds 独立进程逐字节、telemetry 单独；caps 1800s/2h/8GB/0 wells；执行前 final-implementation pilot 实测冻结 canonical；schema 先写；11 失败类别；JSON 无 telemetry；**T2 valid_eval_rows=4093 冻结，不按 4096 报**；不输出真实数据/效果/真实决策/药理/迁移/机制/新颖性。

## 不批准
- 真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；用目标数据训练/调参；用 20262100（M2 Stage3 保留区）；T2/T3 次级豁免 CI；改旧判定/容差；代码晋升；恢复已停止实验。
