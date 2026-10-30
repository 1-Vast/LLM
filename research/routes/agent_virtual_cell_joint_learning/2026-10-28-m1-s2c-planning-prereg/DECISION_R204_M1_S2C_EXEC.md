# Lead 批准：R204-M1-S2c 候选规划比较执行（机制账；compute-only；0 wells）

2026-10-28。依据：R204-M1-S2C.1-C1（i003）判 **approve_exec_v0_2_to_lead**；v0.2 阈值统一、schema 可判字段、headroom 语义、六比较/Holm/δ/CI/等价审计/seeds/caps/schema/边界均 PASS。

## 批准范围（仅 M1-S2c 候选规划比较一次）
- 批准 M1-S2c 候选规划比较执行（机制账、compute-only、0 wells）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
- 冻结旧状态：C216 旧 H1 0/16 `design_invalid: projection`、C217 归因、H1b 16/16 仅密度、C208 一步投影撤——全部不变。
- 冻结 v0.2 链：PROBLEM_M1_S2C_v0_2 `2692C4FB…`、DESIGN `FFC3A13C…`、headroom.py `40F44DD4…`、json `89C3586B…`、schema `4DCFE96B…`、report `A6472DC6…`、record `2C6273EA…`；执行前重核链，不匹配→`design_invalid: chain_mismatch`。
- 冻结环境/合同：Pθ 同 H1b（c .5²/M .1²/d .1²、σ=.1+.4sigmoid(dᵀx)、box[-2,2]^4、K=3/[.5,.3,.2]、seeds 20261301/02/03）；X d=64 主/d=16 次；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2、τ=1）；π0 full/constrained；S=4096/动作；known-truth 独立解析。
- **headroom 2δ 门槛**：设计期 full .22625306 CI [.22094996,.23155615]、constrained .15141651 CI [.15007466,.15275836]，均≥2δ=.10；执行时按同一规则重算/核对；**headroom<2δ=.10 → 未见候选前 redesign/freeze 或 `design_invalid: unreachable_gate` 停止，不执行**；不得降 δ/换 seed/换环境救结果；不得用候选结果反选 headroom。
- 六比较：primary candidate vs P_empirical_mean；secondary P_max_entropy/P_conditional_density_MC/P_constrained_SB/P_random/P_softmax_expected_reward；D=regret_candidate−regret_baseline<0；δ=.05；统一 Holm family=6；单侧下尾；成功 mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw regret 与 paired D 分开保存；CI 按独立 replicate R≥20、cluster=replicate；不用规划 MDE 当已证功效。
- 等价审计：candidate 与 P_empirical_mean/P_max_entropy 动作逐点相同/单调/解析覆盖→`equivalence`、停止增量主张；标准等预算复制/超过→`no_increment`/撤。
- seeds：headroom 20261901–20、data 20261921、eval 20261922、cells 20261931–54；两跑同 seeds 独立进程逐字节、telemetry 单独；不得改 seed。
- caps 1800s/2h/8GB/0 wells；执行前 final-implementation pilot 实测冻结 canonical；schema 先写；11 失败类别；JSON 无 telemetry；不输出真实数据/效果/真实决策/药理/迁移/机制/新颖性。
- 非阻塞执行备注：顶层 headroom 语义字段可能为 null，执行器读 `headroom_design.*` 或 schema；六比较/Holm6/raw-paired/CI R≥20 保持；不把 H1b 密度通过写成旧 H1 通过、不把 C208 写成 M1 增量。

## 不批准
- 真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；改旧判定/容差；把 headroom .10 降为 .05；候选结果后重设 headroom；代码晋升；恢复已停止实验。
