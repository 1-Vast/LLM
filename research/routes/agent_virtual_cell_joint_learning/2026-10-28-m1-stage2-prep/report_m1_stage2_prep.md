# report_m1_stage2_prep —— R204-M1 Stage2 高维近似设计准备报告（不运行效果）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者（endpoint-auditor）。
**状态：Stage2 设计准备完成；仅规划/结构单测/计时；不运行效果/训练/真实数据；机制账 only；compute-only 0 wells；Stage2 执行未批准；Stage3 未执行；不称药理/真实决策/迁移/机制/新颖性。**

依据：M1 Stage1 报告（C208：**B2 等价→rename_maxent，一步投影主算法撤回**）、M1 v0.2、R204 BRIEF/report、R203 decision/power、ERRATA C197/C199/C201/C207/C208。

## 1. 定位（最重要）

- Stage1 已检出 **B2 max-entropy control 与 π* 解析等价**：**一步投影不构成 M1 增量**；本 Stage2 准备**不把它写成算法创新**。
- Stage2 仅针对**未验证候选**：高维群体状态 + 未知随机药效核 + 受限给药程序下，联合生成/推断能否**保持条件药效不被目标污染**，并在同预算得到规划/校准能力。
- 当前只做设计/可执行性/预算/失败类别；**不执行 Stage2**；Stage3 真实数据不运行。

## 2. 高维设置

| 项 | 冻结设计 |
|---|---|
| X | **d_X=64**（8 历史步×8 特征） |
| A | **A=4**；剂量/程序层级；合法动作集可变 |
| Y | **d_Y=4** 连续功能结果；r_g 有界 |
| Pθ | 未知核：3 分量 Gaussian mixture、条件异方差、Student-t(5) 重尾选项；合成已知真值；seed 20261201 |
| reward | `r_g(y)=w^T y−λ||y||²` |
| τ | {0.5,1.0} |
| π0 | full：4 动作均匀；constrained：仅 {0,1}；动作2/3 无支持/受限 |
| 样本/seeds | train 4096、eval 2048；20261201/20261202 |
| 标签边界 | target 样本不作标签；Pθ 不被 target 更新；Doob 非可执行药物 |

**Stage1 保留检查**：G1 条件药效、G2 支持/程序、G4 无泄漏、G5 两跑、G6 schema/预算。
**Stage2 新增**：G3 近似/投影；H1 近似误差随维数/样本；H2 Sinkhorn/SB 收敛（marginal≤1e-8）；H3 planning quality vs exact small case（只诊断，不作效果）。
**full + constrained 两版本**均保留；约束显式编码。

## 3. 等预算对照（仅规格，不执行比较）

B1 random MPC；B2 max-entropy control；B3 conditional density+MC；B4 constrained SB；B5 same-information DF。
同数据/物理反馈/信息集/compute cap/调参≤20/合法实验包；target 样本不作标签；标准控制等预算复制/超过/解析等价→`rename_maxent`/撤；**不得只比错误目标条件化**。
Stage2 只登记规格；**不执行方法比较**。

## 4. 校准/失败/预算

- 校准：G1–G6 + H1–H3；条件药效保持、支持/程序、近似/投影误差、无泄漏、两跑/schema/预算。
- 失败类别：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止：标准控制复制→撤；目标改 Pθ→calibration；无支持→support；Sinkhorn/近似不收敛→projection；无合格功能/功效→停。
- **caps 1800 s/2 h/8 GB/0 wells**；两跑逐字节；JSON 无 telemetry。

## 5. Stage3 端点（不执行）

- 主端点：独立功能决策效用/后悔；**δ=.05 normalized**；headroom=U_max−U0；配对 MDE≤δ；cluster=独立培养/背景/任务。
- **6,282.1038 / 1,572.7759 仅 Fisher-z**；非整数、非门、非 paired DR；决策用 MDE/n_req/headroom/cluster。
- 数据当前 **data_unavailable（C203/C205）**；Stage3 另立预注册+挑战+Lead 批准；不得用合成/RNA 替代独立功能决策。

## 6. 可执行骨架/单测/计时

- `stage2_m1_plan.py` 仅规划算术/结构单测/计时；不训练/不比较/不读真实数据。
- 单测 PASS：X/A/Y 形状、有限性、full/constrained 支持、seed 可复现、Sinkhorn 收敛、内存 cap。
- `stage2_m1_plan.json`：chain/Pθ 设置/Stage1 B2 撤回/单测/规划/失败类别/无效果；**无 telemetry**。
- 两独立进程 result JSON **逐字节一致**（见 §7）；timing 单独。
- pilot **2.9322e-04 s/rep**；projected **0.002932 s**；full wall **0.051557 s**；caps 1800s/2h/8GB；0 wells。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `stage2_m1_plan.json`（两跑一致） | `CD15CF33394327302F5D35A245414310655C8E5C6097D11DC98AEAC2E29ECDA5` |
| `stage2_m1_schema.json` | 见 usage |
| `timing_m1_stage2_prep.json` | 见 usage；result SHA `CD15CF33…` |
| `stage2_m1_plan.py` / report / record / usage | 见 usage |

- schema/失败模板先写；chain 实算 match；Stage1 B2 `rename_maxent_detected=true` 且 M1 increment=false；**一步投影撤回**。

## 8. 建议/边界

- **建议独立挑战**本 Stage2 准备（高维设置/等预算/校准门/端点/失败/预算）；通过后 Stage2 执行仍需另立预注册+挑战+Lead 批准。
- Stage2/3 **不执行**；真实数据当前 `data_unavailable`（C203/C205）；不得用合成/RNA/预测替代独立功能决策。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX。
- **一步投影已撤**，不得写成 M1 增量；M1 不与 M2/M3 混同；N1 `no_increment` 仅其 own primary，不作 M1 Stage2 证据。
