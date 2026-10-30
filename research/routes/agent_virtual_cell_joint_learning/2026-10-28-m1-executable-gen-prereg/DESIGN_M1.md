# DESIGN_M1 —— R204-M1-P1 可执行生成式药理规划执行设计（预注册草案；不运行）

2026-10-28。依据：`PROBLEM_M1.md`、`formalism_M1.py/json`、`timing_M1_pilot.json`、R204 BRIEF/report、ERRATA C197/C199/C201、R203 decision/power scope。
**状态：设计/预注册草案；不运行效果比较/训练/真实数据；机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性。Stage 1/2/3 均未执行；执行须另立预注册+独立挑战+Lead 批准。**

## 0. 批准范围/前置

- 本文件只定义 M1 三阶段检查/预注册，**不批准执行**；不运行 Stage1/2/3/真实数据/湿实验。
- 冻结形式：`Pθ(y|X,a)`；`Q_g∝π0 Pθ exp(r_g/τ)`；可执行 `Rπ=πPθ`；反向 KL 投影 `π*∝π0 exp(E_{Pθ}[r|X,a]/τ)`；先期望后动作；目标样本不作标签；仅真实给药更新 Pθ；有限时程保留物理条件核。
- 冻结：τ、r 有界、π0 支持、合法动作/受限程序、投影/校准阈值、失败类别、预算；不改旧门槛/旧判定；不恢复停止实验；不晋升代码。

## 1. Stage 1：已知随机核离散系统（只做检查，不报效果）

### 1.1 系统

- 有限 X、A、Y；已知 `Pθ(y|X,a)`（离散或小规模可枚举）；有界 `r_g(y)`；τ>0；π0 在合法动作上支持。
- 两个版本：
  - **full support**：所有合法动作 π0>0；
  - **constrained support**：某动作 π0=0 或程序禁用；目标不得声称该动作可达。
- 合成 generator/seed 预注册；**无真实数据/功能**。

### 1.2 检查（不输出 regret/增益）

| id | 检查 | 通过标准 |
|---|---|---|
| S1-a | 目标采样动作 vs `π*` vs 真实期望最优 | 报告差异；不要求 π* 优于标准控制 |
| S1-b | 给定动作后的结果分布 | 可执行 Rπ 的 `P(y|X,a)` 与 Pθ 一致（≤容差） |
| S1-c | 条件药效保持 | 目标引导前后 Pθ 不变；目标 y 样本不作标签（结构检查） |
| S1-d | 支持/受限程序 | 无支持动作 π*=0；不声称可达；约束合法 |
| S1-e | 投影/采样误差 | KL/采样误差≤预注册容差 |
| S1-f | 反例 | A(10%得10)/B(稳定2) 目标采样偏 A 而 E[A]<E[B]；仅证风险，不证候选优 |

### 1.3 等预算基线

- 随机 MPC；最大熵控制；条件密度+Monte Carlo；受约束 Schrödinger 桥；同信息 Diffusion Forcing。
- 同合成数据、同物理反馈/计算/调参预算；比较**正确的随机控制目标**，不得只比“错误目标条件化”。
- Stage1 只做检查性比较；**不输出效果/增益**；若基线等效→`rename_maxent`（撤回算法主张）。

### 1.4 失败/停止

- 投影误差超容差→`design_invalid: projection`；无支持→`design_invalid: support`；
- 目标引导改变 Pθ/目标样本作标签→`design_invalid: calibration`；
- 泄漏/两跑/schema/预算失败→对应 `design_invalid`；
- 只胜过错误目标条件化 → 不算结果；标准控制等效 → 撤主算法（`rename_maxent`）。

## 2. Stage 2：高维近似（不运行）

- 高维状态/结果、近似投影/采样；已知合成或可验证近似。
- 检查：求解能力/校准/投影误差/采样误差/等预算；不输出真实效果。
- 失败：近似误差超容差/不可校准→`design_invalid: projection|calibration`；无法等预算比较→`inconclusive`。

## 3. Stage 3：真实功能记录（数据不 available；不运行）

- **数据要求**：独立功能记录（viability/apoptosis/regrowth 等）、暴露/剂量/时间、独立培养/背景/任务留出、记录 π/动作、计数保留；**未用于 target guidance/model selection**；当前 **data_unavailable（C203）**；不拼 ΔEMAX；技术重复≠独立培养。
- **主端点**：真实独立功能下的决策效用/后悔；δ=**0.05 normalized**；先检 `headroom=U_max−U0`（<δ→`unreachable_gate`）；配对 MDE/CI；cluster=独立培养/背景/任务；**6,282 仅 Fisher-z、非通用门**。
- **次端点**：校准、条件药效保持、规划质量。
- 真实 stage 只在合格数据 + 独立挑战 + Lead 批准后另立执行协议；本文件不执行。

## 4. 校准/资格门（所有阶段）

- **G1 条件药效保持**：目标引导前后 `Pθ(y|X,a)` 不变；目标样本不进入训练；可执行 Rπ 的 `P(y|a)`=Pθ。
- **G2 支持/程序**：合法动作/受限程序；无支持不声称可达。
- **G3 投影/近似**：KL/采样/近似误差≤预注册容差。
- **G4 无泄漏**：target 样本/plan 不作标签；留出功能不参与 guidance/model selection；无未来时点泄漏。
- **G5 两跑/schema/预算**：两跑结果 JSON 逐字节一致；schema/失败模板先写；telemetry 单独；caps 1800 s/2 h/8 GB/0 wells。
- **失败类别**：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **停止**：目标引导改变 Pθ→calibration 失败；无支持→support 失败；标准控制等预算等效→撤算法；无合格功能/功效→停；只胜错误目标条件化→不算结果。

## 5. 预算

- 合成/机制账 **compute-only、0 wells**；caps **wall≤1800 s/CPU≤2 h/内存≤8 GB**；pilot 单独 timing；两跑/schema；超 cap→`design_invalid: compute_budget_exceeded`。
- Stage 2/3 真实数据/湿实验预算单列；当前不 available；**0 wells** for design。

## 6. 边界/不称

- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 一步投影=最大熵控制；SB 近邻；公式不称创新；候选新意仅在未知随机药效+高维状态+受限程序下保持条件药效+同预算规划/校准，未验证。
- N1 `no_increment` 不作 M1 证据；M2 机制账不混同。
- **不运行**；执行须另立预注册+独立挑战+Lead 批准。
