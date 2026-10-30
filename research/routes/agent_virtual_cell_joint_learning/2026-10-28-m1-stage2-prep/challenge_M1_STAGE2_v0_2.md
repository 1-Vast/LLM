# R204-M1 Stage2.1 轻量复核（task-166）：v0.2 高维近似设计

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M1、不运行效果/训练/不读真实数据）。对象：[PROBLEM_M1_STAGE2_v0_2.md](PROBLEM_M1_STAGE2_v0_2.md)（SHA `63C0C228…`）、[DESIGN_M1_STAGE2_v0_2.md](DESIGN_M1_STAGE2_v0_2.md)（`642C3108…`）、[stage2_m1_plan_v0_2.py](stage2_m1_plan_v0_2.py)（`482E254F…`）、[stage2_m1_plan_v0_2.json](stage2_m1_plan_v0_2.json)（`73B8C025…`）、[stage2_m1_schema_v0_2.json](stage2_m1_schema_v0_2.json)（`9C4DF027…`）、report/record/usage v0.2、M1/Stage1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_stage2_design_v0_2_to_lead（仅接受 M1 Stage2 设计；不执行 Stage2/3、不训练、不读真实数据；机制账 only；compute-only；0 wells；不批效果/真实决策/药理/迁移/机制/新颖性）。**

v0.2 已修掉 v0.1 的三项阻断：
- **reward 有界**：`Y` 冻结 compact box `[-2,2]^4`；`r=w^Ty−λ||y||²`、`w=[.4,.3,.2,.1]`、`λ=.2`；box 上连续 → `r_max=.375`（y=w/(2λ)=[1,.75,.5,.25]）、`r_min=−5.2`（box 顶点 [-2,-2,-2,-2]）；`Q_g∝π0Pθ exp(r/τ)` 归一化有限/期望存在；τ∈{.5,1}；G1/H3 bounded-reward 前提成立；不 clip/不把无界 GMM/Student-t 当有界 ✓。
- **唯一 Pθ 生成器**：3 分量截断 GMM、对角协方差、条件异方差、无 Student-t；`X~N(0,I64)`/A4/Y∈[-2,2]^4；K=3、权重 [.5,.3,.2]；c~N(0,.5²)(4,3,4)、M~N(0,.1²)(4,3,4,64)、d~N(0,.1²)(4,3,64)；μ=c+Mx；σ=.1+.4·sigmoid(d^Tx)；截断 Z、Pθ=ΣwN/Z；param_seed 20261201/train 20261202(N4096)/eval 20261203(N2048)；H1/H2/H3 同一生成器 ✓。
- **候选/近似/容差**：C-MDN（K=3 logits+均值4+log-scale4；hidden128/2 ReLU；NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；采样规划4096/动作；不称一步投影）；H1 d∈{8,16,32,64}×N∈{512,1024,2048,4096}、256-bin TV、容差表 d8 .12/.10/.08/.07、d16 .14/.11/.09/.08、d32 .16/.13/.11/.10、d64 .18/.15/.13/.12、超→projection；H2 log-domain Sinkhorn ε∈{.1,.25,.5,1,2}/maxiter2000/marginal1e-8/至少一 ε 收敛；H3 小例 d2/A2/Y2、exact oracle GL128/dim、候选 target-action TV≤.05（仅诊断）✓。
- **保留/自检**：一步投影撤（B2 rename_maxent=true/m1_increment_claimed=false）；G1/G2/G4/G5/G6；B1–B5 等预算；Stage3 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z/data_unavailable；caps 1800s/2h/8GB/0 wells；两跑/无 telemetry；失败类别/边界；单测全 PASS；两跑 plan.json `73B8C025…` 逐字节；pilot 1.35687e-03s/rep、projected .013569s、wall .046166s；all_pass=true/failure_category=null；未输出 effect ✓。

**非阻塞实现备注**（不阻止批准）：
1. **H1 容差表需标注 N 顺序**：`tolerance_table_TV_max` 的四个值对应 N∈{512,1024,2048,4096}（当前 JSON 只给数组）；schema/执行协议应写死“顺序=N grid”，避免执行时按反序/错配。
2. **H3 oracle 是 small-case（d2/A2/Y2）**：不能把 TV≤.05 当高维 exact oracle；只作规划诊断；H1 高维误差仍由 H1 表判。
3. **内存估计**：`memory_bytes_estimate≈6.68MB` 只覆盖当前实例；`Q_g` tensor GL64/dim（64^4≈1.68e7）与 H3 GL128/dim 下实际内存更高（仍应<8GB，但执行前用实际分配器复核）。
4. **Pθ 参数种子/训练/评估拆分**写死；H1/H2/H3 同一生成器；target 样本不作标签、Doob 不可执行；Stage2 不训练/不执行。

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | reward 有界/Q 归一化 | **PASS** | Y compact box [-2,2]^4；r_max .375、r_min −5.2；unit reward_max_observed .3663≤.375、min −5.2；Q_g 有限归一化；τ∈{.5,1}；G1/H3 前提成立；不 clip/无 Student-t ✓。 |
| ② | 唯一 Pθ 生成器 | **PASS** | 3 分量截断 GMM/对角协方差/条件异方差/无 Student-t；c/M/d 形状与分布；σ 形式；Z/Pθ；param/train/eval seeds；H1/H2/H3 同生成器；truncation mass positive；shapes/seed unit tests ✓。 |
| ③ | C-MDN/H1/H2/H3 | **PASS** | C-MDN 架构/训练/planner；H1 d/N grid + 256-bin TV + 容差表；H2 log-domain Sinkhorn ε grid/maxiter2000/1e-8/at least one；H3 small-case GL128 oracle + TV≤.05 diagnostic ✓。 |
| ④ | 保留/自检 | **PASS** | 一步投影撤；B2 rename；G1/G2/G4/G5/G6；B1–B5；Stage3 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z/data_unavailable；caps/两跑/pilot；单测 all_pass；plan SHA 73B8C025；无 effect ✓。 |
| ⑤ | 边界 | **PASS** | 机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage2 执行另立预注册+挑战+Lead；一步投影已撤；M1 不与 M2/M3 混同；N1 不作 M1 Stage2 证据 ✓。 |
| ⑥ | 总判决 | **approve_stage2_design_v0_2_to_lead** | 仅接受设计；不执行。 |

## 2. Lead 接受 M1 Stage2 设计文本（不执行）

> **批准范围**：接受 R204-M1 Stage2 的**设计**（不执行 Stage2/3、不训练、不读真实数据；机制账 only；compute-only；0 wells；不批效果/真实决策/药理/迁移/机制/新颖性）。
>
> **冻结**：定位（Stage1 B2 等价、一步投影撤、m1_increment_claimed=false；Stage2 只研究高维/未知核/受限程序下条件药效保持+同预算规划/校准）；高维 X d64/A4/Y4；**Y compact [-2,2]^4**；**唯一 Pθ=3 分量截断 GMM/对角协方差/条件异方差/无 Student-t**（c/M/d 分布、σ、Z、param/train/eval seeds）；**r=w^Ty−λ||y||²、w=[.4,.3,.2,.1]、λ=.2、r∈[−5.2,.375]**；τ∈{.5,1}；π0 full/constrained；train4096/eval2048；**C-MDN 架构/训练/planner**；G1/G2/G4/G5/G6；G3/H1/H2/H3（H1 d/N + 容差表、H2 Sinkhorn ε/marginal≤1e-8、H3 small-case oracle TV≤.05，仅诊断）；B1–B5 等预算；Stage3 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z/data_unavailable；失败/停止/caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry。
>
> **禁止**：Stage2/3 执行、真实数据/湿实验、效果/真实决策/药理/迁移/机制/新颖性；把一步投影/B2 等价写成 M1 增量；H1–H3 当效果；把 H3 small-case oracle 当高维 oracle；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验。

## 3. 声明

- **本轮不运行效果/不训练/不读真实数据**：只读 M1 Stage2 v0.2 设计/JSON/schema/Stage1 链；只写本文件与 `tmp/`；未改 Stage2 产物。
- **总判决：approve_stage2_design_v0_2_to_lead**。reward 有界/Q 归一化、唯一 Pθ 生成器、C-MDN/H1–H3、保留项/等预算/Stage3/caps/两跑/pilot/边界均核验通过；仅 H1 N 顺序、H3 small-case、内存复核三个非阻塞执行备注。仅接受设计；不执行；机制账/compute-only/0 wells；不批效果/真实决策/药理/Stage2–3。

**一句话：v0.2 已把 Y 冻结 compact box [-2,2]^4（r∈[−5.2,.375]）、唯一截断 GMM Pθ、C-MDN 与 H1/H2/H3 容差写死；两跑/单测/pilot/caps 通过——判 approve_stage2_design_v0_2_to_lead（仅接受 M1 Stage2 设计，不执行；机制账/compute-only/0 wells；不批效果/真实决策/药理/迁移/机制/新颖性）。**
