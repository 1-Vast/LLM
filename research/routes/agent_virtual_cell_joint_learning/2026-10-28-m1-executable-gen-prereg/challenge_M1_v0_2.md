# R204-M1.1 轻量复核（task-156）：v0.2 G1–G6/等预算/Stage1

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M1、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M1_v0_2.md](PROBLEM_M1_v0_2.md)（SHA `18A7FC9F…`）、[DESIGN_M1_v0_2.md](DESIGN_M1_v0_2.md)（`11FACB26…`）、[formalism_M1_v0_2.py](formalism_M1_v0_2.py)（`5B843FA9…`）、[formalism_M1_v0_2.json](formalism_M1_v0_2.json)（`B7298653…`）、[stage1_m1_schema_v0_2.json](stage1_m1_schema_v0_2.json)（`8FF66514…`）、[timing_M1_pilot_v0_2.json](timing_M1_pilot_v0_2.json)、report/record/usage v0.2、ERRATA C197/C199/C201/C207。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_m1_stage1_v0_2_to_lead（仅批准 M1 Stage 1 合成实现：机制账、compute-only、0 wells；不批效果/真实决策/药理/Stage2–3）。**

v0.2 已落实 v0.1 的三项必补：
- **G1–G6 统一**：G1 条件药效保持→calibration；G2 支持/程序→support；G3 投影/近似（KL gap≤1e-8、TV≤.02）→projection；G4 无泄漏→leakage；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded；PROBLEM/DESIGN/JSON/schema/失败模板/report 同步 ✓。
- **B1–B5 等预算规格**：共同合同（同数据/物理反馈/信息集/目标样本不作标签/无额外 holdout/同 cap/调参≤20/seeds 20261112·20261113/只比正确随机控制目标/标准控制等效→rename_maxent）；B1 random MPC（0 configs、20k actions）、B2 max-entropy（闭式、τ=1、0 configs，与 π* 解析等价）、B3 cond-density+MC（20k/动作、SE>0.02→precision、TV≤.02）、B4 constrained SB（one-step entropic OT、≤5 ε、Sinkhorn≤1800s）、B5 same-info DF（≤20 configs、同 cap）✓。
- **Stage1 生成器/容差**：X4/A3/Y4；r(y)=y；τ=1；Pθ logits~N(0,.6²)+softmax；gen seed 20261112/eval 20261113；π0 full/constrained；S1-a TV≤.02、S1-b maxTV≤.02、S1-c ≤1e-12、S1-d exact、S1-e KL gap≤1e-8 且 π*<uniform ✓。
- **保留项**：反例 A target .99665795/B .00334205、E_A=1<E_B=2、π*_B=.73105858；KL star .24038053<uniform .45067680；条件核差 1.11e-16；within-action tilt .43647 不可执行 proposal；无支持 π*=0；Doob 非药物；两跑 formalism JSON 逐字节；pilot 5e-6s/rep、projected .0053s、caps 1800s/2h/8GB/0 wells；JSON 无 telemetry ✓。
- **边界**：机制账 only；Stage1 不报效果；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage1 执行另立预注册+挑战+Lead 批准；Stage2/3 data_unavailable ✓。

**三个非阻塞实现备注**（不阻止批准）：
1. **B2 与候选 π* 解析等价**：`π_ME∝π0exp(E_P[r]/τ)` 就是 M1 一步投影；**Stage1 会检出 `rename_maxent`**。这符合“公式不称创新”的边界；Stage1 报告只能写“检查到等价/撤主算法”，不能把 B2 等价写成 M1 增量。候选新意只在 Stage2/3 高维/未知核/受限程序，未验证。
2. **S1-e 的 grid 容差**：simplex grid 步长 .001、KL gap≤1e-8 是紧的（π*≈[.268941,.731059] 时 step .001 的 KL gap≈8.7e-9）；执行前应精确计算；若超过 1e-8，**提高 grid 分辨率/用解析最优**，不得放宽阈值。S1-a/b 的 20k/x 采样 TV≤.02 足够宽。
3. **B4 constrained SB 规格**：需明确 target outcome marginal 由 `Q_g` 的精确 y 边际、action marginal=π0、Sinkhorn ε 网格/停止/约束投影；当前表已写方向，执行时按 frozen schema 固化；不得把“约束 SB”实现成另一个错误目标条件化。

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | G1–G6 统一 | **PASS** | G1 calibration、G2 support、G3 projection、G4 leakage、G5 two_run_mismatch、G6 compute_budget_exceeded；PROBLEM/DESIGN/JSON/schema/失败模板/report 同步；旧 G1–G5 合并删除 ✓。 |
| ② | B1–B5 等预算规格 | **PASS** | 共同合同/调参≤20/同 seeds/只比正确目标；B1 0 configs 20k actions；B2 闭式 τ=1；B3 20k/动作 SE>0.02→precision；B4 ≤5 ε/Sinkhorn≤1800；B5 ≤20 configs 同 cap；等效→rename_maxent ✓。 |
| ③ | Stage1 生成器/容差 | **PASS（S1-e 紧）** | X4/A3/Y4/r=y/τ=1/Pθ logits N(0,.6²)+softmax/seed 20261112/eval 20261113/π0 full+constrained；S1-a TV≤.02、S1-b maxTV≤.02、S1-c≤1e-12、S1-d exact、S1-e KL gap≤1e-8 且 π*<uniform ✓。S1-e grid .001 的 gap 紧，执行前精确核（非阻塞1/2）。 |
| ④ | 保留项 | **PASS** | 反例 A .99665795/B .00334205、E1<E2、π*_B .73105858；KL .24038053<.45067680；条件核 1.11e-16；within-action tilt .43647；无支持 π*=0；Doob；两跑；pilot 5e-6/.0053；caps/0 wells；无 telemetry ✓。 |
| ⑤ | 边界 | **PASS** | 机制账 only；Stage1 不报效果；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage1 执行另立预注册+挑战+Lead 批准；Stage2/3 data_unavailable ✓。 |
| ⑥ | 总判决 | **approve_m1_stage1_v0_2_to_lead** | 仅 Stage1 合成实现；不批效果/真实决策/药理/Stage2–3。 |

## 2. Lead M1 Stage1 合成实现批准文本（建议）

> **批准范围**：批准 R204-M1 **Stage 1 合成实现**（仅机制账、compute-only、0 new wells）；不批准效果/真实决策/药理/迁移/机制/新颖性；不批准 Stage2/3 真实数据/湿实验；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：`Pθ(y|X,a)`；`Q_g∝π0Pθexp(r_g/τ)`；可执行 `Rπ=πPθ`；反向 KL `π*∝π0exp(E_{Pθ}[r_g|X,a]/τ)`；先期望后动作；目标样本不作标签、仅真实给药更新 Pθ；Doob 路径核不可执行；π0 支持/受限程序；反例 A/B 数值；KL/条件核/within-action tilt/support/Doob 边界；**Stage1 生成器 X4/A3/Y4、r=y、τ=1、Pθ logits N(0,.6²)+softmax、seed 20261112、eval 20261113、π0 full/constrained、S1-a–e 容差**；**B1–B5 等预算规格**（B1 random MPC 0 configs/20k actions；B2 max-entropy 闭式 τ=1；B3 cond-density+MC 20k/动作 SE>0.02→precision；B4 constrained SB ≤5 ε/Sinkhorn≤1800；B5 same-info DF ≤20 configs）；**G1–G6**（G1 calibration/G2 support/G3 projection/G4 leakage/G5 two_run_mismatch/G6 compute_budget_exceeded）；失败类别/停止；caps 1800s/2h/8GB/0 wells；两跑逐字节、JSON 无 telemetry；Stage1 只做检查、不报效果/增益。
>
> **禁止**：Stage2/3 真实数据/湿实验；效果/真实决策/药理/迁移/新颖性；target 生成样本作标签；Doob/目标条件化 y 替代 Pθ；只比错误目标条件化；B2 等价仍称 M1 增量（应 `rename_maxent`/撤）；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验。

## 3. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 M1 v0.2 预注册/formalism JSON/schema/timing/report 与 ERRATA/R203 链；只写本文件与 `tmp/`；未改 M1 产物。
- **总判决：approve_m1_stage1_v0_2_to_lead**。G1–G6 统一、B1–B5 规格、Stage1 生成器/容差、保留项/两跑/pilot/边界均核验通过；仅 B2 与 π* 解析等价（Stage1 会 `rename_maxent`）、S1-e grid 容差紧、B4 实现细节三个非阻塞备注需执行记录。仅批准 Stage1 合成实现（机制账/compute-only/0 wells）；不批效果/真实决策/药理/Stage2–3。

**一句话：v0.2 已统一 G1–G6、冻结 B1–B5 等预算规格与 Stage1 生成器 X4/A3/Y4/r=y/τ=1/Pθ seed20261112/eval20261113/π0 full+constrained/S1-a–e 容差；反例/投影/条件核/Doob/两跑/pilot/边界正确。B2 与 π* 解析等价意味着 Stage1 会 rename_maxent（符合“公式不称创新”），候选增量只能留给 Stage2/3 未验证——判 approve_m1_stage1_v0_2_to_lead（仅 Stage1 合成实现：机制账/compute-only/0 wells；不批效果/真实决策/药理/Stage2–3）。**
