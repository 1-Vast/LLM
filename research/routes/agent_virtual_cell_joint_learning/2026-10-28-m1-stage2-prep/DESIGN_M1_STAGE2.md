# DESIGN_M1_STAGE2 —— R204-M1 Stage2 高维近似执行设计（设计；不运行）

2026-10-28。依据：`PROBLEM_M1_STAGE2.md`、`stage2_m1_schema.json`、`stage2_m1_plan.json`、M1 Stage1（C208：B2 等价→一步投影撤）、M1 v0.2、R203 decision/power、ERRATA C197/C199/C201/C207/C208。
**状态：Stage2 设计准备；不运行效果/训练/真实数据；机制账 only；compute-only 0 wells；Stage2 执行未批准；Stage3 未执行；不称药理/真实决策/迁移/机制/新颖性。**

## 0. 定位/前置

- Stage1 B2 等价：**一步投影公式撤回**；Stage2 只研究“高维/未知随机核/受限程序下联合生成推断保持条件药效 + 同预算规划/校准”。
- Stage2 执行前置：独立预注册 + 独立挑战 + Lead 批准；当前没有 Stage2 执行授权。
- 任何 Stage2 结果只用于机制/校准/规划诊断；**不报效果/增益/方法比较**；真实功能决策在 Stage3，数据当前 `data_unavailable`。

## 1. Stage2 设置（冻结草案）

| 项 | 值 |
|---|---|
| X | d_X=64（8 历史步×8 特征） |
| A | 4 个动作/程序层级；合法动作集可变 |
| Y | d_Y=4 连续功能结果；r_g 有界 |
| Pθ | 未知核：3 分量 Gaussian mixture + 条件异方差 + Student-t(5) 重尾选项；合成已知真值；seed 20261201 |
| reward | `r_g(y)=w^T y − λ||y||²`，预注册 |
| τ | {0.5,1.0} |
| π0 | full：4 动作均匀；constrained：仅 {0,1}；动作2/3 无支持/程序受限 |
| N | train 4096、eval 2048 |
| seeds | 20261201/20261202 |

## 2. 检查/门

### 2.1 Stage1 保留

- G1 条件药效保持；G2 支持/程序；G4 无泄漏；G5 两跑；G6 schema/预算。

### 2.2 Stage2 新增

- G3 投影/近似误差。
- H1 近似误差随 d∈{8,16,32,64}/N∈{512,1024,2048,4096}；容差在 Stage2 执行协议中预注册。
- H2 Sinkhorn/constrained SB 收敛：marginal error≤1e-8、有限迭代；失败→`design_invalid: projection`。
- H3 planning quality vs exact small-case oracle；只作规划诊断，不作效果/增益。
- 高维诊断不得替代 Stage3 独立功能决策。

## 3. 等预算对照（仅规格）

- B1 random MPC；B2 max-entropy；B3 conditional density+MC；B4 constrained SB；B5 same-info DF。
- 同数据/物理反馈/信息集/cap/调参≤20/合法实验包；target 样本不作标签。
- 标准控制等预算复制/超过/解析等价→`rename_maxent`/撤；不得只比错误目标条件化。
- Stage2 只登记规格；**不执行比较**。

## 4. 校准/失败/停止

- 校准：条件药效保持（目标前后 Pθ 不变、target 样本不作标签）、支持/程序、近似/投影误差、无泄漏、两跑/schema、预算。
- 失败：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止：标准控制复制→撤；目标改 Pθ→calibration；无支持→support；Sinkhorn/近似不收敛→projection；无合格功能/功效→停。
- caps：1800 s/2 h/8 GB/0 wells；两跑逐字节；JSON 无 telemetry。

## 5. Stage3 主端点（不执行）

- 独立功能决策效用/后悔；δ=.05 normalized；headroom/MDE 先检；cluster=独立培养/背景/任务。
- **6,282 仅 Fisher-z**；非门/非 paired DR；决策用 MDE/n_req/headroom/cluster。
- 数据当前 `data_unavailable`（C203/C205）；Stage3 另立预注册+挑战+Lead 批准；不得用合成/RNA 替代。

## 6. 可执行骨架/单测/计时（仅此）

- `stage2_m1_plan.py`：规划算术/结构单测/pilot 计时；不训练/不比较/不读真实数据。
- 单测：X/A/Y 形状、有限性、full/constrained 支持、seed 可复现、Sinkhorn 收敛、内存 cap。
- 结果 JSON 无 telemetry；两跑逐字节；schema/失败模板先写；pilot canonical。
- **Stage2 实际执行未批准。**

## 7. 边界

- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX。
- **一步投影已撤**；B2 等价是 `rename_maxent` 证据，不是 M1 增量；M1 不与 M2/M3 混同；N1 no_increment 不作 M1 Stage2 证据。
- Stage2 执行须独立预注册+独立挑战+Lead 批准；Stage3 需合格真实功能数据。
