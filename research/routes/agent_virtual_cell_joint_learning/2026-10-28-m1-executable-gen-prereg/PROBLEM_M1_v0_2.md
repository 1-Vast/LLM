# PROBLEM_M1_v0_2 —— R204-M1.1 可执行生成式药理规划：形式化/等预算/Stage1 冻结（设计，不运行）

2026-10-28。对象：R204 第二独立主线 **M1/D2 可执行生成式药理规划**。本文件修正 v0.1（`PROBLEM_M1.md`，保留不改），落实 M1-C1 三项执行前必补：**G 编号统一 G1–G6**、**等预算基线实现规格冻结**、**Stage1 生成器/容差冻结**。
**状态：预注册设计草案 v0.2；不运行效果比较/训练/真实数据；机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性；Stage1 执行须另立挑战+Lead 批准。**

依据：`PROBLEM_M1.md` v0.1、`DESIGN_M1.md` v0.1、`formalism_M1.py/json` v0.1、`challenge_M1.md`、R204 BRIEF/report、ERRATA C197/C199/C201、R203 decision/power、M2/N1 边界。N1 `no_increment` 仅为其 own primary 判定，**不作 M1 证据**。

## 0. 三项必补落点

| # | 问题 | v0.2 落点 |
|---|---|---|
| 1 | 文档 G1–G5 vs JSON G1–G6 | **统一 G1–G6**（§7 + schema + `formalism_M1_v0_2.json` + 失败模板）；逐条冻结容差/失败类别 |
| 2 | 等预算基线实现规格未冻结 | **§4 表**：B1 random MPC/B2 max-ent/B3 conditional MC/B4 constrained SB/B5 same-info DF；目标函数/信息集/调参上限/计算预算/停止/等价审计全部写死；Stage1 可复现检查性比较 |
| 3 | Stage1 生成器/容差未冻结 | **§5 表**：有限 X/A/Y、Pθ 生成/seed、r/τ/π0、full/constrained、样本量、KL/采样/条件核/支持/投影误差容差、S1-a–e 判据 |

## 1. 形式化（冻结）

- 背景/历史 `X`；合法动作 `a∈A(X)`；真实随机药效核 `Pθ(y|X,a)`（θ 只在真实给药结果后更新）。
- 参考动作分布 `π0(a|X)`，合法动作支持；温度 `τ>0`；奖励 `r_g(y)` 有界。
- 可执行族：`Rπ(a,y|X)=π(a|X)Pθ(y|X,a)`；**执行不能选 y**。
- 目标联合提案：`Q_g(a,y|X)∝π0(a|X)Pθ(y|X,a)exp(r_g(y)/τ)`；它同时倾斜动作和结果，是**提案**，不是新药效核。
- 反向 KL 投影：`π*(a|X)∝π0(a|X)exp(E_{Pθ}[r_g(Y)|X,a]/τ)`；**先对随机药效取期望，再优化动作**。
- **目标生成样本不作实测标签**；只有真实给药结果更新 Pθ；有限时程保留物理条件核；target-tilted Doob 核不可作可执行药物。
- 支持/受限程序：`π0=0` 的动作 `π*=0`；不能声称无支持动作可达；受限程序显式编码。

## 2. 反例（构造，仅证风险）

A：90% 得 0、10% 得 10（E[A]=1）；B：稳定 2（E[B]=2）；τ=1，π0 各 1/2。

- target Q 动作：A≈**0.99665795**、B≈**0.00334205**；target 采样偏爱 A 的幸运轨迹。
- 可执行投影：`π*_A≈0.26894142`、`π*_B≈0.73105858`；按期望选 B 多数。
- **只证明目标条件化风险，不证明本候选优于标准随机控制**；max-ent/random MPC 同预算也可做对。

## 3. 近邻/新意边界

- 一步投影=**最大熵控制**；受控 Schrödinger 桥近邻；Diffusion Forcing/HGVD 覆盖部分联合生成；KoopCell/DisKO/TD-JEPA/BATCHIE 覆盖部分控制/反馈/选择。
- **公式本身不称创新**；候选创新点仅在**未知随机药效+高维群体状态+受限给药程序**下保持条件药效不被目标污染，并在同预算得到规划/校准能力；**未验证**。
- 只胜错误目标条件化、标准控制等预算等效、目标引导改变 Pθ、无支持声称可达 → 撤主算法/`rename_maxent`。

## 4. 等预算基线实现规格（冻结；B1–B5）

**共同合同**：
- 同数据/物理反馈、同信息集（同 X/动作/结果；**目标生成样本不作标签**；无额外 holdout outcome）、同计算预算（wall≤1800 s/CPU≤2 h/内存≤8 GB/0 wells）、同调参预算（**每方法 ≤20 configs**，总调参预算相同）、同 generator/eval seed（20261112/20261113）。
- 只比较**正确的随机控制目标**；不得只比“错误目标条件化”或生成逼真度。
- 停止：超 cap/solver 失败/泄漏/目标样本作标签→对应失败类别；标准控制与候选解析等价或差距≤预注册容差→`rename_maxent`/撤主算法。

| id | 方法 | 目标函数/实现 | 信息集 | 调参上限 | 计算预算 | 停止 | 等价审计 |
|---|---|---|---|---|---|---|---|
| **B1** | random MPC | 合法动作均匀随机 rollout；不按 target 选动作 | 同合法支持；不读额外结果标签 | 0 configs | 同 cap；N_rollout=20,000 actions | 仅 cap | random 动作 TV 对照均匀；只检测“只赢随机” |
| **B2** | max-entropy control | `max_π E_{πP}[r]+τH(π)`；精确 `π_ME∝π0 exp(E_P[r]/τ)` | 同 Pθ/r/π0/τ；无 target y 标签 | τ 固定 1.0；0 configs | 闭式；精确 | 公式/等价失败即重设计 | **与候选 π* 解析等价 → rename_maxent，候选无增量** |
| **B3** | conditional density + MC | 每动作 `N_MC=20,000` 采样估计 `E_P[r|a]`，plug-in `π_MC∝π0 exp(mean_hat/τ)` | 同 Pθ 采样器/样本预算；无额外标签 | 0 configs | 20,000/动作；同 cap | MC SE>0.02→precision_insufficient | 报告 seed/SE；`TV(π_MC,π*)≤0.02` 视为近似等价 |
| **B4** | constrained Schrödinger bridge | one-step entropic OT/SB：`min_R KL(R||π0⊗Pθ)`，约束 action marginal=π0、target outcome marginal 来自 Q_g；ε grid | 同 Pθ/π0/target/τ；无 target y 标签 | ≤5 ε configs `{.1,.25,.5,1,2}` | 离散 Sinkhorn；≤1800 s | 不收敛/约束违反→design_invalid: projection | 与可执行投影比较；等效/≤容差→不称增量 |
| **B5** | same-information Diffusion Forcing | 同 `(X,a,y)` 数据训练条件生成/DF 代理；planning-time target guidance；只生成条件结果 | 同训练/评估数据/历史/动作/结果；无额外标签 | ≤20 configs；同总调参 | 同 cap；同生成样本/rollout 数 | 训练/生成/泄漏失败→calibration/leakage | 同信息等价审计；等效→不称增量；不比较错目标 |

**Stage1 只做检查性比较**：B1–B5 在已知 Pθ 的离散系统上按同一 seed/评估集复现；不输出效果/增益，只输出可复现检查（动作分布/条件核/等价审计）。

## 5. Stage1 生成器/容差（冻结）

### 5.1 系统

- **有限**：X=4（x∈{0,1,2,3}）、A=3、Y=4（y∈{0,1,2,3}）；有界 `r(y)=y`；τ=1.0；`π0` full=`[1/3,1/3,1/3]`，constrained=`[.5,.5,0]`（action2 无支持）。
- **Pθ 生成**：对每个 `(x,a)`，`logits ~ Normal(0, 0.6²)`，`P_theta=softmax(logits)`；generator seed **20261112**；`known_to_method=true`；**目标样本不参与 Pθ**。
- **采样 seed**：**20261113**（独立 evaluation RNG）。
- **版本**：full（全支持）与 constrained（action2 无支持）；同一 Pθ 表。
- **不运行真实数据/湿实验**；Stage1 只做合成检查。

### 5.2 S1-a–e 判据/容差/样本量

| id | 检查 | 样本量/方法 | 通过容差 | 失败类别 |
|---|---|---|---|---|
| **S1-a** | target 采样动作分布 vs 精确 Q_g 动作边际；目标可偏 A 幸运分支而 π* 用期望 | N_target=**20,000 per x**，固定 seed | 动作 TV **≤0.02**；报告 target-vs-projection 差异 | design_invalid: projection |
| **S1-b** | 可执行 Rπ 的条件下 `P(y|X,a)` vs Pθ | N_kernel=**20,000 per condition**（4×3） | 所有 (x,a) max TV **≤0.02** | design_invalid: calibration |
| **S1-c** | target guidance 不改变 Pθ；target y 样本不作标签；可执行条件核=Pθ | 结构检查+精确算术 | 条件核 max abs diff **≤1e-12**；label 检查 true | design_invalid: calibration |
| **S1-d** | constrained：unsupported action π*=0；full：全支持正 | 精确枚举 | **exact** support equality | design_invalid: support |
| **S1-e** | `π*` 公式 vs simplex grid（step .001）最小 KL | 精确公式+grid | `KL(π*)-best_grid_KL ≤1e-8` 且 `KL(π*)<KL(uniform)` | design_invalid: projection |

**允许数值差异，但必须用上述预注册阈值判定；不得事后放宽。** JSON 无 telemetry；两跑 result JSON 逐字节。

## 6. 三阶段最小验证（预注册，不运行）

- **Stage 1**：上述有限随机核离散系统；只做 S1-a–e + B1–B5 检查性比较；**不报效果/增益**。
- **Stage 2**：高维近似；solver/校准能力边界；投影/采样误差；等预算；不运行真实效果。
- **Stage 3**：真实独立功能记录（未用于 target guidance/model selection；独立培养/背景/任务；剂量/时间/function readout；记录 π/动作；计数保留）；当前 **data_unavailable（C203）**。
  - 主端点：真实独立功能决策效用/后悔；δ=**0.05 normalized**；headroom/MDE 先检；cluster=独立培养/背景/任务；**6,282 仅 Fisher-z**。
  - 次端点：校准、条件药效保持、规划质量。
  - 不运行；需合格数据+独立挑战+Lead 批准。

## 7. 校准/资格门（统一 G1–G6）

| 门 | 名称 | 定义 | 容差/失败 |
|---|---|---|---|
| **G1** | 条件药效保持 | target guidance 不改变 Pθ；target 样本不作标签；可执行 Rπ 的 `P(y|a)=Pθ` | 条件核≤1e-12；label 结构 true；失败 `design_invalid: calibration` |
| **G2** | 支持/程序 | 动作支持/受限程序合法；无支持动作 π*=0 且不声称可达 | exact；失败 `design_invalid: support` |
| **G3** | 投影/近似 | reverse-KL 投影/近似误差 | KL grid gap≤1e-8；采样 TV≤.02；失败 `design_invalid: projection` |
| **G4** | 无泄漏 | target 样本/plan 不作实测标签；holdout 功能不参与 guidance/model selection；无未来时点泄漏 | 结构 true；失败 `design_invalid: leakage` |
| **G5** | 两跑 | 两独立进程 result JSON 逐字节一致；telemetry 单独 | byte-identical；失败 `design_invalid: two_run_mismatch` |
| **G6** | schema/预算 | schema/失败模板先写；caps 1800 s/2 h/8 GB/0 wells | schema 存在+cap；失败 `design_invalid: compute_budget_exceeded` |

**失败类别全集**：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
**停止**：只胜错误目标条件化→不算结果；标准控制等预算等效→撤算法；目标引导改变 Pθ→calibration；无支持→support；无合格功能/功效→停。

## 8. 预算/边界

- 合成/机制账 **compute-only、0 wells**；pilot/caps **wall≤1800 s/CPU≤2 h/内存≤8 GB**；不运行真实效果/湿实验/Stage2/3。
- 不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- **Stage1 执行须另立预注册 + 独立挑战 + Lead 批准**；本文件只是设计/预注册草案。
- N1 `no_increment` 仅其 own primary，不作 M1 证据；M2 机制账不混同。
