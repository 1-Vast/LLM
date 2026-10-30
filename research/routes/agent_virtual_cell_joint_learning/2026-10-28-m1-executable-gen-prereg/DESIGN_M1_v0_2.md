# DESIGN_M1_v0_2 —— R204-M1.1 可执行生成式药理规划执行设计（G1–G6 / 等预算 / Stage1 冻结；不运行）

2026-10-28。修正 v0.1（`DESIGN_M1.md`，保留不改），落实 M1-C1 三项必补：**统一 G1–G6**、**等预算基线实现规格**、**Stage1 生成器/容差**。依据 `PROBLEM_M1_v0_2.md`、`formalism_M1_v0_2.py/json`、`stage1_m1_schema_v0_2.json`、`timing_M1_pilot_v0_2.json`、R204 BRIEF/report、ERRATA C197/C199/C201、R203 decision/power、M2/N1 边界。
**状态：预注册设计草案 v0.2；不运行效果比较/训练/真实数据；机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性。Stage1 执行须另立挑战+Lead 批准。**

## 0. 批准范围/前置

- 本文件只定义 Stage1/2/3 设计与检查；**不批准执行**；不运行真实数据/湿实验。
- 冻结：形式化 `Pθ/Q_g/Rπ/π*`、先期望后动作、目标样本不作标签、Pθ 只由真实给药更新、Doob 不可执行、支持/受限程序；等预算 B1–B5；Stage1 生成器/容差；G1–G6；失败类别；caps。
- 不改旧门槛/旧判定；不恢复停止实验；不晋升代码。

## 1. Stage1 生成器/容差（冻结；详见 schema）

### 1.1 生成器

| 项 | 冻结值 |
|---|---|
| 有限系统 | X=4（0..3）、A=3、Y=4（0..3） |
| Pθ | 每个 (x,a) logits~Normal(0,0.6²)，Pθ=softmax；generator seed **20261112** |
| 评估采样 | independent **20261113** |
| reward | `r(y)=y`；有界 |
| τ | **1.0** |
| π0 | full `[1/3,1/3,1/3]`；constrained `[.5,.5,0]`；action2 无支持 |
| 版本 | full + constrained；同一 Pθ 表 |
| 标签边界 | target 生成样本不作标签；Pθ 不被 target 更新 |

### 1.2 S1-a–e 判据（通过标准）

| id | 检查 | 样本/方法 | 容差 | 失败 |
|---|---|---|---|---|
| S1-a | target 动作分布 vs 精确 Q_g 动作边际 | N=20,000/x，seed 20261113 | TV≤**0.02** | projection |
| S1-b | 可执行 Rπ 的 `P(y|X,a)` vs Pθ | N=20,000/condition（4×3） | max TV≤**0.02** | calibration |
| S1-c | 目标引导不改 Pθ；target 样本不作标签；可执行条件核=Pθ | 结构与精确算术 | ≤**1e-12** + label true | calibration |
| S1-d | 支持：constrained action2 π*=0；full 全正 | 精确枚举 | **exact** | support |
| S1-e | `π*` 公式 vs simplex grid（步骤 .001） | 精确+grid | KL gap≤**1e-8**；π*<uniform KL | projection |

**Stage1 只做检查性比较，不报效果/增益。** 允许数值差异但不得事后放宽阈值；JSON 无 telemetry；两跑逐字节。

## 2. 等预算基线实现规格（B1–B5；冻结）

**共同合同**：同数据/物理反馈、同信息集（同 X/a/y；目标样本不作标签；无额外 holdout）、同计算 cap 1800s/2h/8GB、同调参预算（每法≤20 configs；总调参同）、同 seed 20261112/20261113；只比**正确随机控制目标**；标准控制等效/≤容差→`rename_maxent`/撤主算法。

| id | 方法 | 目标/实现 | 信息集 | 调参 | 计算 | 停止/审计 |
|---|---|---|---|---|---|---|
| B1 | random MPC | legal actions 均匀随机 rollout；不 target 选动作 | 同支持；不读额外标签 | 0 | N_rollout=20,000 actions | cap；只检测“赢随机” |
| B2 | max-entropy control | `π_ME∝π0 exp(E_P[r]/τ)`；精确闭式 | 同 Pθ/r/π0/τ | τ 固定；0 | 闭式/精确 | 与 π* 解析等价→rename_maxent |
| B3 | conditional density+MC | `N_MC=20,000/动作` 估计均值，plug-in | 同样本预算；无额外标签 | 0 | 20k/动作 | SE>0.02→precision；TV(π_MC,π*)≤.02 等价 |
| B4 | constrained SB | one-step entropic OT：`min_R KL(R||π0⊗Pθ)`，约束 action marginal=π0、target outcome marginal=Q_g；ε grid | 同 Pθ/π0/target/τ | ≤5 ε `{.1,.25,.5,1,2}` | Sinkhorn≤1800s | 不收敛/约束违反→projection；等效→不称增量 |
| B5 | same-info DF | 同 `(X,a,y)` 训练条件生成/DF 代理；planning-time target guidance；只生成条件结果 | 同训练/评估数据/历史/动作 | ≤20 configs；同调参 | 同 cap/生成量 | 训练/生成/泄漏→calibration/leakage；等效→不称增量 |

Stage1 用已知 Pθ 离散系统按同一 seed/评估集复现这些规范；**不输出增益**。

## 3. 三阶段（预注册，不运行）

### Stage 1：已知随机核离散系统

- 系统/容差见 §1；检查 S1-a–e + B1–B5 检查性比较。
- 不报效果/增益；通过只表示 Stage1 检查合格。

### Stage 2：高维近似

- 高维状态/结果、近似投影/采样；检查 solver/校准能力边界、投影/采样误差、等预算。
- 失败：误差超容差→`design_invalid: projection|calibration`；无法等预算→`inconclusive`。

### Stage 3：真实功能记录

- 数据：独立功能记录（未用于 target guidance/model selection；独立培养/背景/任务；剂量/时间/function readout；记录 π/动作；计数保留）；当前 **data_unavailable（C203）**。
- 主端点：真实独立功能决策效用/后悔；δ=**0.05 normalized**；headroom/MDE 先检；cluster=独立培养/背景/任务；**6,282 仅 Fisher-z**。
- 次端点：校准、条件药效保持、规划质量。
- 不运行；需合格数据 + 独立挑战 + Lead 批准。

## 4. 校准/资格门（统一 G1–G6）

| 门 | 名称 | 定义 | 容差/失败 |
|---|---|---|---|
| G1 | 条件药效保持 | target guidance 不改 Pθ；target 样本不作标签；可执行 `P(y|a)=Pθ` | ≤1e-12；失败 calibration |
| G2 | 支持/程序 | 支持/受限程序合法；无支持 π*=0 | exact；失败 support |
| G3 | 投影/近似 | KL/采样/近似误差 | KL gap≤1e-8；TV≤.02；失败 projection |
| G4 | 无泄漏 | target 样本不作标签；holdout 不参与 guidance/model selection | 结构；失败 leakage |
| G5 | 两跑 | 两独立进程 result JSON 逐字节；telemetry 单独 | byte-identical；失败 two_run_mismatch |
| G6 | schema/预算 | schema/失败模板先写；caps 1800s/2h/8GB/0 wells | schema+cap；失败 compute_budget_exceeded |

失败类别：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 5. 预算/边界

- 合成/机制账 compute-only 0 wells；caps **wall≤1800 s/CPU≤2 h/内存≤8 GB**；超 cap→`design_invalid: compute_budget_exceeded`；pilot timing 单独。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 一步投影=最大熵控制、SB 近邻；公式不称创新；候选新意未验证。
- N1 `no_increment` 仅其 own primary，不作 M1 证据；M2 机制账不混同。
- **Stage1 执行须另立预注册+独立挑战+Lead 批准**；本文件只是设计/预注册。
