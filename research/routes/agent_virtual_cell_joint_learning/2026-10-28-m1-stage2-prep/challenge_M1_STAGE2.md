# R204-M1 Stage2 设计独立挑战（task-164）：高维近似

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M1、不运行效果/不训练/不读真实数据）。对象：[PROBLEM_M1_STAGE2.md](PROBLEM_M1_STAGE2.md)（SHA `344E69A3…`）、[DESIGN_M1_STAGE2.md](DESIGN_M1_STAGE2.md)（`E8EBE3F5…`）、[stage2_m1_plan.py](stage2_m1_plan.py)（`FC5A9664…`）、[stage2_m1_plan.json](stage2_m1_plan.json)（`CD15CF33…`）、[stage2_m1_schema.json](stage2_m1_schema.json)（`EB9F71CF…`）、[report_m1_stage2_prep.md](report_m1_stage2_prep.md)（`1F8E08A7…`）、[record_m1_stage2_prep.md](record_m1_stage2_prep.md)（`7C6F0C28…`）、M1 v0.2/Stage1 C208、R203 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_stage2_design_to_lead；也不是 stop）。**

定位正确、Stage1 撤一步投影、G1/G2/G4/G5/G6 保留、H1–H3/B1–B5/Stage3 data_unavailable/预算/边界基本写清；但高维设计有三处会阻断 Stage2 执行/复现：
1. **reward 有界性与设定矛盾**：PROBLEM/DESIGN 写 `r_g(y)` 有界，但 `r_g(y)=w^T y−λ||y||²` 在 `Y∈R^4`、Pθ 为 GMM/Student-t(5)（无界支撑）时 **不是有界函数**（二次项使 `||y||→∞` 时 `r→−∞`；仅在 λ>0 时上有界）。target `Q_g∝exp(r_g/τ)` 的可归一化/期望存在、G1/H3 的“有界奖励”前提都需要明确 **compact/truncated Y** 或 **bounded/clipped reward**；不能同时写“r 有界”和该二次形式。
2. **Pθ 生成器未冻结**：`3 分量 Gaussian mixture + 条件异方差 + Student-t(5) 重尾选项` 中 **“选项”未选**，也没有分量均值/协方差/自由度/尺度/截断/target Q 归一化；Stage2 是“已知真值”诊断，生成器不唯一则 H1/H2/H3/条件核检查不可复现。
3. **Stage2 候选/近似方法未定义**：设计列出 G3/H1/H2/H3 与 B1–B5，但没有写 Stage2 实际要实现的 **高维近似/投影/规划方法**（候选算法、近似族、求解器、H1 的 d/N 子采样与容差、H3 的 exact small-case oracle 构造）；H1 容差还写“在 Stage2 执行协议中冻结”，当前设计无法判定“通过”。
4. 其余：B1–B5 等预算规格、Stage3 data_unavailable、caps/两跑/pilot/边界基本正确。

**结论：先修 §2 的 1–3，再提交 Lead 接受 M1 Stage2 设计（不执行）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 定位/一步投影撤 | **PASS** | Stage1 B2 等价（rename_maxent_detected=true、m1_increment_claimed=false）；一步投影主算法主张撤回；Stage2 只研究高维/未知核/受限程序下条件药效保持+同预算规划/校准；不写一步投影增量 ✓。 |
| ② | 高维设置/生成器 | **FAIL（reward 有界/Pθ 未冻结）** | X d64/A4/Y4；Pθ 3 分量 GMM+条件异方差+Student-t(5) **“选项”未选**；seed 20261201；`r=w^Ty−λ||y||²`；τ∈{.5,1}；π0 full/constrained；train4096/eval2048；seeds；target 不作标签/Doob 非药物 ✓。**但 r 写“有界”却用无界 Y 的二次形式；Pθ 未冻结**。 |
| ③ | 保留/新增检查 | **PASS（H1 容差待冻结）** | 保留 G1/G2/G4/G5/G6；新增 G3、H1 d∈{8,16,32,64}/N∈{512,1024,2048,4096}、H2 Sinkhorn marginal≤1e-8、H3 planning vs exact small-case oracle；H1–H3 只诊断、不替代 Stage3；条件核校准≠细胞动力学 ✓。H1 容差留到执行协议，设计阶段不可判（见 §2-3）。 |
| ④ | 等预算对照 | **PASS** | B1 random MPC/B2 max-entropy/B3 cond density+MC/B4 constrained SB/B5 same-info DF；同数据/物理反馈/信息集/cap/调参≤20/合法实验包；target 不作标签；标准控制等预算复制/超过/解析等价→rename_maxent/撤；不得只比错误目标条件化 ✓。 |
| ⑤ | Stage3 主端点/数据 | **PASS** | 独立功能决策效用/后悔 δ=.05；headroom/MDE 先检；cluster=独立培养/背景/任务；6,282/1,573 仅 Fisher-z；data_unavailable（C203/C205）；不得合成/RNA 替代；Stage3 另立预注册+挑战+Lead ✓。 |
| ⑥ | 失败/停止/预算 | **PASS** | 失败类别含 projection/support/calibration/leakage/compute_budget_exceeded/rename_maxent/two_run_mismatch/chain_mismatch、unreachable_gate/precision_insufficient/no_increment/inconclusive；caps 1800s/2h/8GB/0 wells；两跑/JSON 无 telemetry；失败只写类别 ✓。 |
| ⑦ | 骨架/单测/计时 | **PASS** | 仅规划/结构单测/计时；单测 PASS（shape/finite/support/seed/Sinkhorn/内存）；两跑 plan.json CD15CF33 逐字节；pilot 2.9322e-04s/rep、projected .002932s、wall .051557s；caps ✓。 |
| ⑧ | 边界 | **PASS** | 机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage2 执行另立预注册+挑战+Lead；一步投影已撤；M1 不与 M2/M3 混同；N1 no_increment 不作 M1 Stage2 证据 ✓。 |
| ⑨ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5，Lead 接受设计前）

1. **冻结 reward 的有界性语义**：二选一——(a) 限制 `Y` 到 compact/truncated 支撑（如 GMM 截断/有界变换），并给出 `r_g` 的上下界；或 (b) 明写 `r_g` 仅上有界/可将 `r_g` clip 到预注册区间，并说明 target `Q_g` 归一化、期望存在、G1/H3 前提；不能继续写“r_g 有界”又用无界二次形式。同步 PROBLEM/DESIGN/JSON/schema。
2. **冻结唯一 Pθ 生成器**：明确 GMM 还是 Student-t(5)、分量数/均值/协方差/自由度/尺度、条件异方差的 `h(X)` 形式、是否截断、target Q 的可归一化条件、H1/H2/H3 使用的同一生成器；seed/训练/评估拆分写死。当前“重尾选项”不可执行。
3. **定义 Stage2 候选/近似方法**：写明高维近似/投影/规划的实际算法族（例如低秩/核/神经/采样）、求解器与复杂度、H1 的 d/N 子采样与容差、H2 Sinkhorn 迭代/ε 网格、H3 exact small-case oracle 的构造与“planning quality”指标；H1 容差必须在 Stage2 执行预注册前冻结，不能留到执行时自由选。
4. **保持其余**：G1/G2/G4/G5/G6、B1–B5 等预算、Stage3 data_unavailable/主端点/6,282 仅 Fisher-z、caps/两跑/pilot/失败/边界不变；Stage2 不执行、不报效果；一步投影已撤。
5. 数据/安全：不读真实数据；target 样本不作标签；Doob 不可执行；不称药理/真实决策/迁移/机制/新颖性；M1 不与 M2/M3 混同；N1 no_increment 不作 M1 Stage2 证据。

## 3. 修完后建议的 Lead 接受 M1 Stage2 设计文本（不执行）

> **批准范围**：在必改 1–3 完成并复核后，**接受** R204-M1 Stage2 的**设计**（不执行 Stage2/3、不训练、不读真实数据；机制账 only；compute-only；0 wells；不批效果/真实决策/药理/迁移/机制/新颖性）。
>
> **冻结**：定位（Stage1 B2 等价、一步投影撤、m1_increment_claimed=false；Stage2 只研究高维/未知核/受限程序下条件药效保持+同预算规划校准）；高维 X d64/A4/Y4、**唯一 Pθ 生成器（GMM/Student-t、分量/协方差/自由度/条件异方差/截断）**、**reward 有界/截断语义**、τ∈{.5,1}、π0 full/constrained、train4096/eval2048、seeds；G1 条件药效/G2 支持/G4 无泄漏/G5 两跑/G6 schema·预算；G3/H1/H2/H3（H1 d/N 容差、H2 marginal≤1e-8、H3 small-case oracle，仅诊断）；B1–B5 等预算；Stage3 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z/data_unavailable；失败/停止/caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry。
>
> **禁止**：Stage2/3 执行、真实数据/湿实验、效果/真实决策/药理/迁移/机制/新颖性；把一步投影/B2 等价写成 M1 增量；把 H1–H3 合成诊断当效果；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验。

## 4. 声明

- **本轮不运行效果/不训练/不读真实数据**：只读 M1 Stage2 设计/JSON/schema/Stage1 链；只写本文件与 `tmp/`；未改 Stage2 产物。
- **总判决：revise**。定位/等预算/Stage3/预算/边界基本正确；但 **reward 二次形式与“有界”声明矛盾、Pθ 生成器仍是“选项”未冻结、Stage2 候选/近似方法与 H1 容差未定义**。修完 1–3 后可接受 M1 Stage2 设计（不执行；机制账/compute-only/0 wells；不批效果/真实决策/药理）。

**一句话：Stage1 B2 等价/一步投影撤回、Stage2 高维设置、G1–G6/H1–H3、B1–B5、Stage3 data_unavailable、caps/两跑/pilot/边界都写清了；但 `r=w^Ty−λ||y||²` 在无界 Y 上不是“有界奖励”、Pθ 的“Student-t 重尾选项”未冻结、Stage2 实际近似/规划方法与 H1 容差未定义——判 revise：先冻结 reward 有界语义/唯一生成器/候选近似方法与容差，再提交 Lead 接受 M1 Stage2 设计（不执行）。**
