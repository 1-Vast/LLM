# Lead 批准：R201-B 主 T1 合成模拟器执行一次（仅计算证据）

2026-10-28。依据：T1-MVP（task-114）实现+资格门 **qualification_pass（9 项全 PASS）**：oracle 可恢复、null FP（100 null worlds，π_dual vs C7 两臂，p1=p2=0.5、mean diff=0）、EV 近似门（approx vs 5 点噪声参考 max|Δ|=1.998e-15≤0.02，**离散参考一致性门非连续真误差**）、成本账（18 格 negative filler=0/outside=0；10 arms spend≤1；primary residual 109.2/110 wells/0.8；filler 不改 learner state）、无泄漏、10 arms、menu hash、schema、wall；pilot 10×10=100 arm-runs wall **6.97s**，外推 primary 5,000 arm-runs≈**5.81min**≤45min、两跑≈**11.6min**≤90min；两跑 `t1_qualify.json` 逐字节一致（`A50A1E96…`）。

## 批准范围
- **主 T1 执行一次**：primary 配置 (1200s,16 integer keys,κ=1,σ=0.10)、500 独立 replicate=500 decision units、10 arms（π_dual+C0–C6+C7 两臂）、H_B AND（两 Holm 主对比均正且显著且点估计均≥δ_min=0.10；只赢一个→partial_decision_benefit；都不成立→no_decision_benefit；显著但低于 δ→below_delta）；主检验仅 primary；敏感性 17×50 仅描述/cost_sensitive（wall 允许时执行，否则 fallback 跳过）；两跑逐字节一致；实际 wall 报告。
- 冻结链：T1-MVP 资格门产物 + v0.4 设计；**不得改冻结旋钮**；仅合成模拟器，**不读 O'Neil/Validation 真实响应、不跑 T2/T3、不做湿实验**。
- 结果状态：**仅计算证据**（synthetic）；不称新颖性/机制/迁移/决策收益/独立确认；**不得外推到生物/药物决策**；冻结≠资源足够/关系成立/Stage1/效果。
- 失败/停止：资格门已过；若主执行出现实现偏差/预算超限→停并记录 `design_invalid`/`protocol_deviation`，不得改规则；若 H_B 不成立→按预注册写 `no_decision_benefit`/`partial`/`below_delta`，不写"双预算无效"。
