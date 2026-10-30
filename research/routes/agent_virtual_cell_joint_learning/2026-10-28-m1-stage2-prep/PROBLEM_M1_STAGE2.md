# PROBLEM_M1_STAGE2 —— R204-M1 Stage2 高维近似设计准备（不运行效果）

2026-10-28。对象：M1 Stage2（高维/未知随机核/受限程序）设计草案。**状态：仅设计/规划；不运行效果、训练、真实数据；机制账 only；compute-only 0 wells；Stage2 执行未批准；Stage3 未执行。不称药理/真实决策/迁移/机制/新颖性。**

依据：M1 Stage1 报告（C208：**B2 等价→rename_maxent**；一步投影主算法主张**撤回**）、M1 v0.2 PROBLEM/DESIGN、R204 BRIEF/report、R203 decision/power、ERRATA C197/C199/C201/C207/C208。

## 0. 定位（写死）

- Stage1 已检出 **B2 max-entropy control 与 π* 解析等价**：**一步投影公式不构成 M1 增量**，不得写成 M1 算法创新。
- Stage2 **只针对未验证候选**：**高维群体状态 + 未知随机药效核 + 受限给药程序**下，联合生成/推断能否**保持条件药效不被目标引导污染**，并以**同预算**得到规划/校准能力。
- 不得把 Stage1 一步投影、M2 算子、M3 DR 的结论混同；M1 Stage2 是独立机制账设计。

## 1. 高维设置

| 项 | 冻结设计值 |
|---|---|
| X | **d_X=64**（8 历史步×8 特征；含必要历史/群体状态） |
| A | **A=4**（剂量/程序层级；合法动作集可变） |
| Y | **d_Y=4** 连续功能结果向量；`r_g(y)` 有界 |
| Pθ 族 | **未知核**：3 分量 Gaussian mixture、条件异方差尺度、Student-t(5) 重尾选项；Stage2 合成已知真值；**无真实数据** |
| reward | 预注册有界 `r_g(y)=w^T y − λ||y||²` |
| τ | {0.5, 1.0}（预注册网格） |
| π0 | full：4 动作均匀；constrained：仅 {0,1} 合法；动作2/3 无支持/程序受限 |
| 样本 | train N=4096、eval N=2048；seeds 20261201/20261202 |
| 目标样本 | **不作实测标签**；目标引导不更新 Pθ |
| Doob | target-tilted/Doob 核**不是可执行药物**；执行只能 `Rπ=πPθ` |

**full 与 constrained 两版本**均纳入；支持/程序约束显式编码，不用生成提案声称不可达动作可用。

## 2. 检查：Stage1 保留 vs Stage2 新增

### 2.1 保留（Stage1 检查）

- **G1** 条件药效保持（目标引导前后 Pθ 不变；target 样本不作标签；可执行 Rπ 的 `P(y|a)=Pθ`）。
- **G2** 支持/程序合法（无支持 π*=0；受限程序合法）。
- **G4** 无泄漏（评价样本独立于拟合/策略选择；target 样本不作标签）。
- **G5** 两跑 result JSON 逐字节；telemetry 单独。
- **G6** schema/失败模板先写；caps 1800 s/2 h/8 GB/0 wells。

### 2.2 新增（Stage2 高维诊断）

- **G3** 投影/近似误差（高维）。
- **H1** 近似误差随维数/样本（d∈{8,16,32,64}、N∈{512,1024,2048,4096}）的变化；预注册容差在 Stage2 执行协议中冻结。
- **H2** Sinkhorn/constrained SB 收敛（marginal error≤1e-8；有限迭代；失败→`design_invalid: projection`）。
- **H3** planning quality vs exact small-case oracle（只作规划质量诊断，不作效果/增益）。
- **不得**用 H1–H3 的合成诊断替代 Stage3 独立功能决策；不得把条件核校准升级为细胞动力学。

## 3. 等预算对照（仅规格，不执行比较）

- **B1** random MPC；**B2** maximum-entropy control；**B3** conditional density + MC；**B4** constrained Schrödinger bridge；**B5** same-information Diffusion Forcing。
- 同数据/物理反馈/信息集/计算 cap/调参≤20/合法实验包；目标样本不作标签。
- 标准控制等预算复制/超过或解析等价→`rename_maxent`/撤主算法主张；**不得只比错误目标条件化**。
- Stage2 只做诊断/规划；**不做效果/方法比较结论**。

## 4. 校准/资格门

- G1–G6 + H1–H3；**校准包括**条件药效保持、支持/程序、近似/投影误差、无泄漏、两跑、schema/预算。
- 高维额外：近似误差随 d/N、Sinkhorn 收敛、planning quality vs exact small case。
- 失败类别：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 失败只写类别，不报效果。

## 5. Stage3 主端点/功效（不执行；真实数据才用）

- 主端点：独立功能决策效用/后悔；**δ=.05 normalized**；先检 `headroom=U_max−U0`（<δ→`unreachable_gate`）；配对 MDE≤δ；cluster=独立培养/背景/任务。
- **6,282.1038 / 1,572.7759 仅 Fisher-z 连续参考**；非整数、非门、非 paired DR；决策用 MDE/n_req/headroom/cluster。
- **data_unavailable（C203/C205）**；不得用合成/RNA 替代独立功能决策；Stage3 另立预注册+挑战+Lead 批准。

## 6. 失败/停止/预算

- **停止**：标准控制等预算复制/超过→撤；目标改变 Pθ/样本作标签→calibration；无支持→support；近似/Sinkhorn 不收敛→projection；无合格功能/功效→停。
- **预算**：合成 compute-only 0 wells；caps **1800 s/2 h/8 GB/0 wells**；两跑/无 telemetry；Stage2 执行需另立预注册+独立挑战+Lead 批准。

## 7. 可执行骨架/单测/计时（仅规划）

- `stage2_m1_plan.py`：仅规划算术/结构单测（shape/finite/support/seed/Sinkhorn）/pilot 计时；**不跑方法比较/不训练/不读真实数据**。
- 单测必须通过：形状、有限性、支持表、seed 可复现、Sinkhorn 收敛、内存 cap。
- Stage2 实际执行**未批准**。

## 8. 边界

- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX。
- **一步投影已撤**，不得写成 M1 增量；B2 等价是 `rename_maxent` 证据，不是新算法。
- M1 Stage2 不与 M2/M3 混同；N1 `no_increment` 仅其 own primary，不作 M1 Stage2 证据。
- Stage2 执行须另立预注册+独立挑战+Lead 批准；Stage3 需合格真实功能数据。
