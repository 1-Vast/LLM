# record_M1 —— R204-M1-P1 可执行生成式药理规划预注册执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者。
**任务：R204-M1-P1（设计/预注册，不运行效果）。** 只写 `research/2026-10-28-m1-executable-gen-prereg/` 与 tmp/；未改 M2/N1/A-B-D 产物、旧门槛/旧判定/代码；未运行效果比较/训练/真实数据/湿实验；0 wells。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| 12:12 | 读 task-153、R204 BRIEF/report §3 M1、ERRATA C197/C199/C201、R203 decision/power、M2/N1 边界 |
| 12:12–12:18 | 写 `formalism_M1.py`：目标联合/反向 KL 投影/反例/条件核/支持/Doob/三阶段/gates/pilot；运行 → `formalism_M1.json` + `timing_M1_pilot.json` |
| 12:18 | 修正 condition 检查（可执行 Rπ 的条件核与 target joint within-action tilt 分开；前者差 1.1e-16，后者 0.436 标记不可执行 proposal） |
| 12:18 | 两独立进程运行；`formalism_M1.json` 一致 `A38A6239…A080A5`；timing 单独 |
| 12:18–12:20 | 写 PROBLEM/DESIGN/report/record/usage；核对 SHA；确认未执行效果 |

## 1. 输入（只读）

| 文件 | 用途 |
|---|---|
| `2026-10-28-deep-coupling-redesign/report.md` §3 M1 | 形式化/反例/近邻/最小验证 |
| `BRIEF_R204.md` | 主线/端点/冻结/边界 |
| `ERRATA_R201_R202.md` C197/C199/C201 | 6,282 仅 Fisher-z；门槛/两本账 |
| `2026-10-28-decision-power-scope/{PROBLEM_DECISION.md,power_scope.json}` | 决策终点/headroom/MDE/配对 |
| `2026-10-28-m2-operator-prereg` | M2 机制账边界/不混同 |
| `2026-10-28-n1-effect-run/report_n1_effect.md` | N1 no_increment 边界；**不作 M1 证据** |

## 2. 做了什么

- **形式化**：`Pθ(y|X,a)`；`Q_g∝π0Pθ exp(r_g/τ)`；`Rπ=πPθ`；反向 KL → `π*∝π0exp(E_P[r|X,a]/τ)`；先期望后动作；目标样本不作标签；仅真实给药更新 Pθ；保留物理条件核。
- **反例**：A 10%得10/其余0、B稳定2；target Q 动作 A≈.99666，实际 E_A=1<E_B=2；executable π*_B≈.731；只证风险。
- **投影算术**：KL star .2404 < uniform .4507；可执行条件核差 1.1e-16；target within-action tilt .436 标不可执行；支持无支持动作=0；Doob 核非药物。
- **等预算**：随机 MPC/最大熵/条件密度+MC/受约束 SB/同信息 DF；同数据/计算/调参；只比正确随机控制目标。
- **三阶段**：Stage1 已知随机核离散；Stage2 高维近似；Stage3 真实功能记录（data_unavailable，未运行）；主端点 decision utility/regret δ=.05；headroom/MDE/cluster；6,282 仅 Fisher-z；次端点 calibration/conditional efficacy/planning quality。
- **gates/失败**：G1 条件药效；G2 支持/程序；G3 投影；G4 无泄漏；G5 两跑/schema/预算；失败类别见 PROBLEM。
- **pilot**：10 reps **5.0e-6 s/rep**；projected **0.0052 s**；caps 1800 s/2 h/8 GB；0 wells。
- **两跑**：result JSON 一致 `A38A6239…A080A5`；timing 单独。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `PROBLEM_M1.md` | 形式化/反例/边界/阶段/门/预算 |
| `formalism_M1.py` | 仅形式化/投影/校准算术/合成 pilot；不跑效果比较 |
| `formalism_M1.json` | 形式化结果（两跑一致） |
| `DESIGN_M1.md` | 三阶段预注册执行设计（不运行） |
| `report_M1.md` | 设计报告 |
| `record_M1.md` | 本记录 |
| `timing_M1_pilot.json` | canonical timing（telemetry 单独） |
| `usage_M1.json` | 命令/输出 SHA/attestation，最后写出 |

## 4. 未做/边界

- **未运行效果比较/训练/真实数据/湿实验/Stage2/3**；未输出 regret/决策效用/增益/方法优劣；只做形式化算术/设计。
- 未改旧门槛/旧判定/代码；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养；不称药理/真实决策/迁移/机制/新颖性。
- **公式本身不称创新**（一步投影=最大熵控制；SB 近邻）；候选新意仅在未知随机药效+高维状态+受限程序下保持条件药效+同预算规划/校准，未验证。
- **M1 执行须另立预注册 + 独立挑战 + Lead 批准**；本文件只是预注册设计。
- N1 no_increment 仅其 own primary，不作 M1 证据；M2 机制账不混同。
