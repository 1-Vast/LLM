# report_M1 —— R204-M1-P1 可执行生成式药理规划预注册报告（设计；不运行效果）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者（endpoint-auditor）。
**状态：预注册设计完成；未运行效果比较/训练/真实数据/湿实验；机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性。**

依据：R204 BRIEF/report §3 M1；`DECISION`/M2/N1 边界；ERRATA C197/C199/C201；R203 decision/power scope。N1 `no_increment` 仅为其 own primary 判定，**不作 M1 证据**。

## 1. 结论

1. **形式化完成**：真实随机药效核 `Pθ(y|X,a)`；目标联合提案 `Q_g∝π0 Pθ exp(r_g/τ)`；可执行族 `Rπ=πPθ`；反向 KL 投影 `π*∝π0 exp(E_{Pθ}[r_g|X,a]/τ)`；**先对随机药效取期望，再优化动作**；目标样本不作标签，只有真实给药更新 Pθ；有限时程保留物理条件核。
2. **反例**：A 10% 得 10/其余 0 的期望 1 < B 稳定 2；目标联合提案 target 采样约 **99.67% 选 A**；可执行投影 π*_B≈**0.731**；只证明目标条件化风险，**不证明候选优于标准控制**。
3. **投影算术**：小 categorical 例中 `KL(Rπ*||Q_g)=0.2404 < KL(Rπ_uniform||Q_g)=0.4507`；可执行条件核 `P(y|a)` 与 Pθ 差 **1.11e-16**；目标联合 Q 的 within-action y tilt **0.436**，明确标记为**不可执行 proposal**；支持例 π0 无动作→π*=0。
4. **近邻/新意边界**：一步投影=**最大熵控制**；受控 Schrödinger 桥近邻；Diffusion Forcing/HGVD 覆盖部分联合生成；**公式不称创新**。候选创新点仅在未知随机药效+高维状态+受限程序下保持条件药效+同预算规划/校准，**未验证**。
5. **阶段**：Stage1 已知随机核离散系统（动作选择/给定动作结果/条件药效/支持/投影检查，不报效果）；Stage2 高维近似；Stage3 真实功能记录（当前 data_unavailable，不运行）。主端点=真实独立功能决策效用/后悔 δ=.05；headroom/MDE；cluster；6,282 仅 Fisher-z；次端点=校准/条件药效/规划质量。
6. **预算**：合成 compute-only 0 wells；pilot 计时；caps 1800s/2h/8GB；两跑 JSON 逐字节；schemas/失败模板先写；超 cap→design_invalid。

## 2. 形式化/反例（算术）

| 项 | 值 |
|---|---|
| A | 90% 0、10% 10；E[A]=1 |
| B | 100% 2；E[B]=2 |
| target Q 动作 | P(A)=0.99665795、P(B)=0.00334205 |
| 可执行投影 π* | A=0.26894142、B=0.73105858 |
| 条件核保持 | 可执行 `P(y|a)` 与 Pθ 差 1.11e-16；PASS |
| 目标 joint within-action tilt | 0.436（不可执行 proposal，不得作 Pθ） |
| 支持例 | π0=[.7,.3,0] → π*_3=0；PASS |
| Doob 边界 | target-tilted outcome 核不是可执行药物；P(y|a) 必须保留 |

**反例仅作推理**：目标生成可偏 A 的幸运分支；投影按期望选 B；标准随机控制同样能做对，因此不证明本候选优于控制。

## 3. 等预算对照（Stage1–3 共用）

- 随机 MPC
- 最大熵控制（一步投影等价）
- 条件密度 + Monte Carlo
- 受约束 Schrödinger 桥
- 同信息 Diffusion Forcing

同数据/物理反馈/计算/调参；**不得只比错误目标条件化**；标准控制等预算等效 → `rename_maxent`/撤主算法。

## 4. 三阶段/门（预注册，不运行）

**Stage1**：已知随机核离散系统；检查动作选择、给定动作后结果分布、条件药效保持、支持/受限程序、投影误差、反例；不输出效果/增益。
**Stage2**：高维近似；solver/校准能力边界；投影/采样误差；等预算。
**Stage3**：真实独立功能记录（未用于 target guidance/model selection）；主端点 decision utility/regret；δ=.05；headroom/MDE；cluster；6,282 仅 Fisher-z；次端点 calibration/conditional efficacy/planning quality；**当前 data_unavailable，不运行**。

**Gates**：G1 条件药效保持；G2 支持/程序；G3 投影/近似误差；G4 无泄漏（目标样本不作标签）；G5 两跑/schema/预算。
**失败类别**：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 5. Pilot/timing（最终代码，仅算术）

- 10 reps：**5.0e-6 s/rep**；projection arithmetic projected **0.0052 s**；caps **1800 s/2 h/8 GB**；实际远低；**0 wells**。
- result JSON 无 telemetry；timing 单独；两跑 result JSON 一致（见 §6）。
- 旧 timing/其他方向数值不混用。

## 6. 产出/两跑

| 文件 | SHA256/说明 |
|---|---|
| `formalism_M1.py` | 见 usage |
| `formalism_M1.json`（两跑一致） | `A38A6239…A080A5` |
| `timing_M1_pilot.json` | canonical telemetry |
| `PROBLEM_M1.md` / `DESIGN_M1.md` | 正式定义/设计 |
| `report_M1.md` / `record_M1.md` / `usage_M1.json` | 报告/记录/用量 |

- 两个独立进程 result JSON 一致；timing 单独；**无效果/增益/方法比较**。
- 未执行 Stage2/3；真实功能数据当前 `data_unavailable`（C203），不能由合成/RNA 替代。

## 7. 建议/边界

- **建议独立挑战**本预注册 + `formalism_M1.json`/`DESIGN_M1.md`；通过后才可另立 Stage1 执行协议；Stage2/3 需合格数据 + 再挑战 + Lead 批准。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 一步投影公式不称创新；候选新意未验证；N1 结果不作 M1 证据；M2 机制账不混同。
