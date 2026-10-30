# R204-M1-P1 独立挑战（task-154）：可执行生成式药理规划预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M1、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M1.md](PROBLEM_M1.md)（SHA `03A8D388…`）、[DESIGN_M1.md](DESIGN_M1.md)（`7CA08616…`）、[formalism_M1.py](formalism_M1.py)（`210CACA4…`）、[formalism_M1.json](formalism_M1.json)（`A38A6239…`）、[report_M1.md](report_M1.md)（`DA8ACEF8…`）、[record_M1.md](record_M1.md)（`C8D2633A…`）、R204 BRIEF/report、ERRATA C197/C199/C201/C207、R203-P1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_m1_stage1_to_lead（仅批准 M1 Stage 1 合成实现：机制账、compute-only、0 wells；不批效果/真实决策/药理/迁移/新颖性）。**

M1 的形式化与算术核验通过：
- **形式化**：`Pθ(y|X,a)`；目标联合提案 `Q_g∝π0 Pθ exp(r_g/τ)`；可执行族 `Rπ=πPθ`；反向 KL 投影 `π*∝π0 exp(E_{Pθ}[r_g|X,a]/τ)`；**先期望后动作**；目标样本不作标签、仅真实给药更新 Pθ；有限时程保留物理条件核、Doob 路径核不可执行 ✓。
- **反例算术正确**：A 10%得10/90%得0 E=1；B 稳定2 E=2；target Q `P(action=A)=.99665795`/B `.00334205`；可执行投影 `π*_A=.26894142`/`π*_B=.73105858`；只证目标条件化风险、不证候选优于标准控制 ✓。
- **投影/校准正确**：`KL(Rπ*||Q_g)=.24038053 < KL(uniform||Q_g)=.45067680`；条件核互差 `1.11e-16`；target joint within-action y tilt `.43647017` 标为不可执行 proposal；support 例 π0_3=0→π*_3=0；Doob 边界保留 ✓。
- **等预算对照**：随机 MPC、最大熵控制、条件密度+MC、受约束 SB、同信息 Diffusion Forcing；同数据/物理反馈/计算/调参；只比正确随机控制目标；标准控制等效→`rename_maxent`/撤 ✓。
- **三阶段/主端点**：Stage1 已知随机核离散检查不报效果；Stage2 高维近似/校准边界；Stage3 真实独立功能记录，主端点决策效用/后悔 δ=.05、headroom/MDE/cluster、6,282 仅 Fisher-z、次端点 secondary；当前 data_unavailable ✓。
- **校准/失败/停止**：G1 条件药效保持、G2 支持/程序、G3 投影/近似、G4 无泄漏、G5 两跑/schema/预算；失败类别/停止写清 ✓。
- **预算/两跑**：pilot 5.0e-6 s/rep、projection arithmetic .0052 s、caps 1800s/2h/8GB/0 wells；formalism JSON 两跑逐字节；telemetry 分开 ✓。
- **边界**：机制账 only；一步投影=最大熵控制/SB 近邻、公式不称创新；候选新意仅在高维/未知随机核/受限程序下保持条件药效+同预算规划校准（未验证）；N1 `no_increment` 不作 M1 证据；M2 不混同；不称药理/真实决策/迁移/机制/新颖性；不晋升代码/不改旧判定；M1 执行另立预注册+挑战+Lead 批准 ✓。

**三个非阻塞问题**（不影响批准，但执行前应补）：
1. **G 编号/范围不一致**：PROBLEM/DESIGN 用 **G1–G5**（G5=两跑/schema/预算），JSON `gates` 用 **G1–G6**（G5=两跑，G6=预算）；统一为 G1–G5 或 G1–G6 并同步 schema/失败模板。
2. **等预算基线的实现规格未冻结**：随机 MPC/最大熵/条件密度+MC/SB/DF 的**目标函数、调参预算、计算预算、信息集、停止准则**未逐项写死；Stage1 若只做“检查性比较”而不冻结这些，容易只比错误目标条件化/不可复现。建议在 Stage1 执行预注册中写每基线接口/目标/预算/等价审计。
3. **Stage1 生成器/容差**：有限 X/A/Y、Pθ 生成方式、seed、r/τ/π0、full/constrained 两版本、KL/采样/条件核容差需写死（现有 DESIGN 只写“合成 generator/seed 预注册”）；否则 S1-a–e 的“通过标准”不可判定。

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | 形式化/期望先于动作/Doob | **PASS** | Q_g/Rπ/π* 公式正确；反向 KL 推导先 E_{Pθ}[r] 后动作；目标样本不作标签；仅真实给药更新 Pθ；Doob 路径核不可执行、保留 Pθ 条件核 ✓。 |
| ② | 反例算术 | **PASS** | A E=1/B E=2；target A=.99665795/B=.00334205；π*_A=.26894142/B=.73105858；只证风险 ✓。 |
| ③ | 投影/条件核/不可执行 proposal/支持 | **PASS** | KL .24038053<.45067680；条件核差1.11e-16；target y tilt .43647017；π0_3=0→π*_3=0；Doob 边界 ✓。 |
| ④ | 等预算对照 | **PASS（需实现规格）** | 基线列表/同预算/正确目标/ `rename_maxent` 写清；实现目标/调参/计算/信息集需在 Stage1 预注册冻结（§0 非阻塞2）。 |
| ⑤ | 三阶段/主端点/防选择性 | **PASS** | Stage1 不报效果；Stage2 近似/校准；Stage3 独立功能主端点 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z；data_unavailable；先留出/不用于 guidance/model selection ✓。 |
| ⑥ | 校准门/失败/停止 | **PASS（G 编号需统一）** | G1–G5 条件药效/支持/投影/泄漏/两跑预算；失败类别/停止写清；JSON G6 预算需统一（§0 非阻塞1）✓。 |
| ⑦ | 预算/两跑/timing | **PASS** | pilot 5e-6s/rep、projection .0052s、caps 1800/2h/8GB/0 wells；formalism JSON 两跑一致；JSON 无 telemetry ✓。 |
| ⑧ | 边界诚实 | **PASS** | 机制账 only；公式不称创新；候选新意未验证；N1 no_increment 不作 M1 证据；M2 不混同；不称药理/真实决策/迁移/机制/新颖性；不晋升代码/不改旧判定；执行另立预注册+挑战+Lead 批准 ✓。 |
| ⑨ | 总判决 | **approve_m1_stage1_to_lead** | 仅 Stage1 合成实现；不批效果/真实决策/药理。 |

## 2. 修完后建议的 Lead Stage1 批准文本（仅合成机制账/compute-only/0 wells）

> **批准范围**：批准 R204-M1 **Stage 1 合成实现**（仅机制账、compute-only、0 new wells）；不批准效果/真实决策/药理/迁移/机制/新颖性；不批准 Stage2/3 真实数据执行；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：`Pθ(y|X,a)`；`Q_g∝π0Pθexp(r_g/τ)`；可执行 `Rπ=πPθ`；反向 KL 投影 `π*∝π0exp(E_{Pθ}[r_g|X,a]/τ)`；先期望后动作；目标样本不作标签、仅真实给药更新 Pθ；Doob 路径核不可执行；π0 支持/受限程序；反例 A/B 数值；KL/条件核/within-action y tilt/support 检查；Stage1 有限离散 generator/seed/X/A/Y/Pθ/r/τ/π0/容差；等预算基线（random MPC/最大熵/条件密度+MC/SB/DF）目标/信息/调参/计算/等价审计；G1–G5（统一编号）条件药效保持/支持/投影/无泄漏/两跑/schema/预算；失败类别/停止；caps 1800s/2h/8GB/0 wells；两跑逐字节、JSON 无 telemetry。
>
> **禁止**：效果/真实决策/药理/迁移/新颖性；Stage2/3 真实数据/湿实验；把 target 生成样本当标签；用 Doob 路径核/目标条件化 y 替代 Pθ；只比错误目标条件化；标准控制等预算等效仍称增量；改公式/阈值/端点救结果；晋升代码；不改旧判定；不恢复停止实验。

## 3. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 M1 预注册/formalism JSON/DESIGN/report 与 R204/R203 链；只写本文件与 `tmp/`；未改 M1 产物。
- **总判决：approve_m1_stage1_to_lead**。形式化/反例/投影/条件核/支持/Doob/等预算/三阶段/主端点/校准门/预算/边界均核验通过；仅 G1–G5 vs G6 编号、等预算实现规格、Stage1 生成器/容差三个非阻塞项需在执行前补齐。仅批准 Stage1 合成实现（机制账/compute-only/0 wells）；不批效果/真实决策/药理。

**一句话：M1 的 Q_g/Rπ/反向 KL π* 公式、A/B 反例（target A .996658 vs π*_A .268941）、KL .24038<.45068、条件核 1.11e-16、within-action y tilt .43647、π0_3=0→π*_3=0、Doob 边界、等预算/三阶段/校准门/边界都正确；仅 G 编号、等预算基线实现规格、Stage1 generator/容差三个非阻塞项需补——判 approve_m1_stage1_to_lead（仅 Stage1 合成实现：机制账/compute-only/0 wells；不批效果/真实决策/药理/迁移/新颖性）。**
