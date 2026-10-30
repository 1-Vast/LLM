# Lead 接受：R204-M1 Stage2 设计（不执行；机制账；compute-only；0 wells）

2026-10-28。依据：R204-M1-S2.1-C1（i003）判 **approve_stage2_design_v0_2_to_lead**；reward 有界语义、唯一 Pθ 生成器、C-MDN/H1–H3 容差、保留项/自检/两跑/pilot、边界均 PASS。

## 接受范围
- **仅接受 M1 Stage2 设计**；**不执行 Stage2/3**、不训练、不读真实数据；机制账 only；compute-only；0 wells；不批效果/真实决策/药理/迁移/机制/新颖性。
- 冻结 v0.2 链：PROBLEM_M1_STAGE2_v0_2 `63C0C228…`、DESIGN_M1_STAGE2_v0_2 `642C3108…`、stage2_m1_plan_v0_2.py `482E254F…`、json `73B8C025…`、schema `9C4DF027…`、timing `488C8EF6…`、report `BCE5DE11…`、record `CBA86C88…`。
- 冻结定位：Stage1 B2 等价（`rename_maxent_detected=true`、`m1_increment_claimed=false`）；**一步投影主算法主张撤回**；Stage2 只研究高维/未知随机核/受限给药程序下条件药效保持+同预算规划/校准。
- 高维设置：X d=64/A=4/Y d=4；Y **compact box [-2,2]^4**；唯一 **Pθ=3 分量截断 GMM/对角协方差/条件异方差/无 Student-t**（c~N(0,.5²)(4,3,4)、M~N(0,.1²)(4,3,4,64)、d~N(0,.1²)(4,3,64)；μ=c+Mx；σ=.1+.4sigmoid(d^Tx)；截断 Z/Pθ；param_seed 20261201/train 20261202(N4096)/eval 20261203(N2048)）。
- reward `r=w^Ty−λ||y||²`、w=[.4,.3,.2,.1]、λ=.2、**r∈[−5.2,.375]**；τ∈{.5,1}；π0 full/constrained；train4096/eval2048。
- 候选 **C-MDN**（K=3 logits+mean4+log-scale4；hidden128/2 ReLU；NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；采样规划4096/action；不称一步投影）；G1/G2/G4/G5/G6；G3/H1/H2/H3（H1 d∈{8,16,32,64}×N∈{512,1024,2048,4096}、256-bin TV、容差表 d8 .12–.07…d64 .18–.12、超→`projection`；H2 log-domain Sinkhorn ε∈{.1,.25,.5,1,2}/maxiter2000/marginal 1e-8/至少一 ε 收敛；H3 small-case d2/A2/Y2 exact oracle GL128/dim、候选 target-action TV≤.05、仅诊断）；B1–B5 等预算；Stage3 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z/data_unavailable；caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry。

## 非阻塞执行备注
- H1 容差数组顺序写死为 N grid {512,1024,2048,4096}（schema/执行协议）；
- H3 是 small-case oracle，**不得当高维 exact oracle**；高维误差由 H1 判；
- 内存估计需执行前用实际分配器复核（Q_g GL64/dim、H3 GL128/dim）；
- Stage2 训练/执行另立预注册+独立挑战+Lead 批准；Stage3 需合格真实功能数据（当前 data_unavailable C203/C205）。

## 不批准
- Stage2/3 执行、训练、真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；把一步投影/B2 等价写成 M1 增量；H1–H3 当效果；把 H3 当高维 oracle；改公式/阈值/端点救结果；代码晋升；改旧判定/门槛；恢复已停止实验。
