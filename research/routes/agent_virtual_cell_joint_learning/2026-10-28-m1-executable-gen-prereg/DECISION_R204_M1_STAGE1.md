# Lead 批准：R204-M1 Stage 1 合成实现（仅机制账；compute-only；0 wells）

2026-10-28。依据：R204-M1.1-C1（i003）判 **approve_m1_stage1_v0_2_to_lead**；G1–G6 统一、B1–B5 等预算规格、Stage1 生成器/容差、保留项/边界均 PASS。

## 批准范围（仅 Stage1 合成实现/检查性门）
- **仅 Stage1**：实现冻结形式化与未知随机核离散系统，跑 G1–G6 检查与 B1–B5 规格复核；**不报效果/增益/方法比较结论**；不批 Stage2/3、真实数据/湿实验/药理/真实决策/迁移/新颖性。
- 冻结 v0.2 链：PROBLEM_M1_v0_2 `18A7FC9F…`、DESIGN_M1_v0_2 `11FACB26…`、formalism_M1_v0_2.py `5B843FA9…`、formalism_M1_v0_2.json `B7298653…`、stage1_m1_schema_v0_2.json `8FF66514…`、timing `72870EF9…`、report `4BF3C490…`、record `205AA995…`。
- 冻结：Pθ/Q_g/Rπ/π* 公式、先期望后动作、目标样本不作标签、Doob 不可执行、π0 支持/受限程序、反例 A/B 数值、KL/条件核/within-action tilt/support/Doob 边界；Stage1 生成器 X=4/A=3/Y=4、r(y)=y、τ=1、Pθ logits~N(0,.6²)+softmax、seed 20261112/eval 20261113、π0 full/constrained；S1-a TV≤.02、S1-b maxTV≤.02、S1-c≤1e-12、S1-d exact、S1-e KL gap≤1e-8 且 π*<uniform（执行前精确计算；超则提高 grid/用解析最优，**不得放宽阈值**）。
- B1–B5 等预算规格：B1 random MPC（0 configs、20k actions）；B2 max-entropy（闭式 τ=1、0 configs；**与 π* 解析等价→Stage1 检出 `rename_maxent`、撤主算法，不写成 M1 增量**）；B3 cond-density+MC（20k/动作、SE>0.02→precision、TV≤.02 等价）；B4 constrained SB（one-step entropic OT、action marginal=π0、target outcome marginal=Q_g 的 y 边际、≤5 ε、Sinkhorn≤1800s；不得实现成另一个错误目标条件化）；B5 same-info DF（≤20 configs、同 cap/生成量）。
- G1–G6：G1 条件药效保持（calibration）/G2 支持程序（support）/G3 投影近似（projection）/G4 无泄漏（leakage）/G5 两跑逐字节（two_run_mismatch）/G6 schema/预算（compute_budget_exceeded）；caps 1800s/2h/8GB/0 wells；两跑逐字节、JSON 无 telemetry；失败只写 design_invalid 不报结果。
- 非阻塞备注：B2 解析等价预期；S1-e 容差紧需精确计算；B4 规格固化；Stage1 仅检查性比较、不报增益。

## 不批准
- Stage2/3 真实数据/湿实验；效果/真实决策/药理/迁移/新颖性；代码晋升；改旧判定/门槛；恢复已停止实验；把 B2 等价写成 M1 增量；用 target 样本作标签；Doob/目标条件化 y 替代 Pθ；改公式/阈值救结果。
