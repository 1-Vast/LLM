# R198-A2v3 修订报告（REVISION_A2_v3.md）— 逐条回应 v2 挑战必改

日期：2026-10-27 · 角色：A2 提案者（lit-verifier）· task-43
对象：[challenge_A2_v2.md](challenge_A2_v2.md)（revise，≤5 必改；致命 3 条：III/E2 不可达、预算表算术冲突、MDE/δ_min 单位混用 + abstention 记账）。本文件逐条说明 v3 如何落实；**v1/v2 文件保留不改**（SHA 见 record_v3 §4），新增：[spec_v3.md](spec_v3.md)、[protocol_draft_v3.md](protocol_draft_v3.md)、本文件、[record_v3.md](record_v3.md)、[usage_v3.json](usage_v3.json)、设计版 `folds.json`/`constraints_check.json`、模拟器 `constructive_sim.py`（**落盘未运行**）。
**本轮不运行效果/模拟器/训练/回放/拟合；不读响应做效果；不改 A1 产物；不声称新颖性。**

## 必改 1：III/E2 可达性 + abstention 记账

| 挑战问题 | v3 落实 |
|---|---|
| III 的 z 随机指派、K_A2 看不到 → E2 构造上不可达 | **z 改为可观测但未进入模型/关系的元数据变量**：`BARCODE` 派生批次组（2 水平，真实存在于元数据列，模型/关系不使用）（spec_v3 §4.1/§4.3、protocol_v3 §3.1）。候选状态清单 ≤6 个（Tissue / drug_type / 剂量布局 / **BARCODE 派生 z** / 细胞系 8 组 / A4 状态），**冻结时固定**。 |
| 判别器必须"能看见" z，且不能直接喂答案 | K_A2 规则 4 改为**两步**：① 预注册可观测残差结构统计量（主：dip；备：2 vs 1 成分潜类 BIC 差、分组方差比）过零分布分位；② 在 ≤6 候选中做分层相关/组间差，用 **max-statistic 置换零**（1,000 次）控制多重性；只有"结构显著 ∧ 某候选过校正阈值"才判 III 并输出 `identified_state`；z 必须**靠数据被识别**，分类器不知道哪个候选被注入；未识别 → `unresolvable`（spec_v3 §4.3）。若仍失败 → `constructive_partial`（I 可分；II/III 不分），不删 E2 重跑。 |
| E1/E2 的分母未定义，可按 resolved 刷高 | **E1/E2 分母 = 全部非 null 世界（含 abstention），abstention 一律计错**；resolved-only balanced accuracy 只作**次级描述**、不参与判定（protocol_v3 §3.3）。 |
| E4 ≤0.25 与 E1 0.80 记账不相容（可全 abstain 过 E3） | **E4 收紧为 ≤0.10** + **E4b 每类 resolved rate ≥0.85**；E3 上 abstention 计为无假类（正确），但 null resolved rate ≤0.50 只作卫生上限（描述）；算术自洽：E4≤0.10 ⇒ resolved≥0.90；E1 all-worlds 0.80 ⇒ resolved acc≥0.889；E2 ⇒ ≥0.778（protocol_v3 §3.3 明写）。 |

## 必改 2：预算-功效表重写（消除 38 vs 36、26 vs 24）

- **核心修法**：不再把各判别单元需求相加；改为**一个 20 单元结构化批次同时满足三项**——10 单元"条件内"+10 单元"条件外"，每层按状态 z 平衡 5/5 → II（10 vs 10）、III（z 各 10 ≥6）、I（20 ≥6）全部满足（protocol_v3 §3.4、spec_v3 §4.5）。
- **显式分配表**：
  | k | 分配 | 可判 | 复用 |
  |---|---|---|---|
  | 6 | 3 in/3 out；z 3/3 | I vs null | I 用 6；II/III 不判 |
  | 12 | 6 in/6 out；每层 z 3/3 | I + III | I 用 12；III 用 z 各 6；II 不达（6/6<10） |
  | **20** | **10 in/10 out；每层 z 5/5** | **I + II + III** | I 用 20；II 用 10 vs 10；III 用 z 各 10 |
  | 24（replay） | 20 结构化 + 4 备用 | I + II（真实） | 备用只增 I 精度；III 只出 proxy flag |
  | 36 | 20 结构化 + 16 独立确认批次（8/8；z 4/4） | I+II+III + 稳定性复验 | 16 批次**不放宽阈值**（8/8<10 → II 不达），只描述方向复现 |
- **II 的"≥5 独立语境"**：语境 = 预注册 **8 个细胞组**（`folds.json.cell_groups_8`，按 (Tissue, CELL_LINE_NAME) 排序 round-robin）；II 注入在 **5 组**翻转（其余 3 组不变）；单元按 10 in（5 组×2）+10 out（3 组 4+3+3）；判别按组计数、按组置换零。
- **模拟器规模/时间核算**：96 世界（4 类×24）× ~90,589 单元 ≈ 8.7M 数值；MDE 4 终点×4 k×1,000 批 = 16,000 次轻量分类 → **估计 ≤5 min，硬上限 30 min**（protocol_v3 §6）。代码落盘不运行。

## 必改 3：MDE 与 δ_min 同单位化

- 四个终点分别定义 **δ_min = 目标水平 − 机会/基线**（同单位：正确率差/率差）：E1 = 0.80−0.50 = **0.30**；E2 = 0.70−0.50 = **0.20**；E3 = 0.10−0.05 = **0.05**；E4 = 0.10−0.00 = **0.10**（protocol_v3 §3.3）。
- **MDE 定义**：80% 功效下可分辨的**正确率/率差**（与 δ_min 同单位），每终点 ≥1,000 模拟批；`MDE ≤ δ_min` 才允许推进，否则 `design_uninformative`。
- **模拟器/MDE 代码落盘**：`constructive_sim.py`（DESIGN VERSION，未运行；含世界生成器/判别器/端点/预算计划骨架与 `--confirm-run` 门禁）；SHA256 `2d9e0d61c753eae6ee85352864e904f2a5758b7b624292ed84c5dcec5c621ae6`，已列入冻结清单（protocol_v3 §6）。

## 必改 4：药对单位统一 + U/S 不相交

- **单位写死**：C2′ 组计数主口径 = **有向**（2,025 有向对；331/275/165 组；1,698 对/90,589 单元）；无序仅敏感性（1,294 无序对；305/215/117 组）。U/top-k 主口径 = **无序**（1,294；每折 both-unseen 33/49/48/49/58）。双口径都报告（spec_v3 §2.4、protocol_v3 §1–§2）。
- **S**：24 cell×directed-pair 单元；**24 个不同 directed 对 ∧ 24 个不同 unordered 对**；响应盲抽样规则与 S 列表设计版在 `folds.json.S24`。
- **U 修正**：删除 v2"U 与 S 按药对不相交"的错误断言；改为 **U = both-unseen 对 − S 涉及的对**。逐折 U：一次口径 unordered **9/25/24/25/34**（fold0 U=9<10 → top-k=5 预注册；其余 top-k=10）；鲁棒性 directed **21/42/48/58/84**（top-k=10）。
- **断言**：`Ref∩S=∅`、`S∩E=∅`、S 的对 ∉ U（U 定义保证）；任一失败 → `data_unavailable`。

## 必改 5：接口/冻结清单补齐

- **schema 版本化**：`a2_to_a1/v3`，字段名/类型/单位冻结（spec_v3 §6、protocol_v3 §5）；新增 `residual_structure`/`identified_state` 字段。
- **κ≥0.60 仅兼容性检查**：明写"κ 高≠验证；A1/A2 同类判别不互相当独立验证；`X_flip`/`δ_scope` 只作口径对齐、不互作验证"（spec_v3 §6、protocol_v3 §5）。
- **设计版已落盘**（metadata-only，无响应读取，未跑构造）：
  - `folds.json`：5 折分配（13 药/折）、both-unseen directed/unordered 计数、S24 抽样结果、U（directed/unordered）大小、top-k、`cell_groups_8`；SHA256 `3546e34eba1caf41c206f3c5742905f908c27083cdcf354265e055ee193c9dd7`；
  - `constraints_check.json`：331/275/165 组 + 90,589 单元、无序敏感性 305/215/117、target 组（ANCHOR 40=34+6；LIBRARY 58=51+7）、逐折组覆盖、零分布计划；SHA256 `b35018f70c97bf2a67fc473b708654501a8be6b6e454d40f8d58b28271e93039`；
  - `constructive_sim.py`：落盘未运行（SHA 同上）。
- 保持：C1′ QA only（不主张同靶点=同功能）、replay 不报归因正确率/收益、C176/C177 作废状态引用、constructive 先于 replay。

## 仍然撤回/保持的限制（不掩盖）

- constructive 模拟器与 MDE 模拟**未运行**；E1–E4 是否可达、MDE 是否 ≤δ_min 尚**未验证**——这是冻结后执行项，不是本轮结论。
- `SYNERGY_DELTA_EMAX` 列义按 R198 record 引用，尚未独立核列。
- A1 更新器/归因 schema 尚未由 A1 提供；本文件的 `a2_to_a1/v3` 是 A2 侧契约。
- A4 状态资源未知 → III 的**真实数据认证**仍不可得（A2 只做 constructive 与候选状态）。
- general-ML 先例仍只到元数据级（不声称空白）。
- A2 仍**不单独冻结**；本 v3 待复审后并入 A1 整体冻结。

## v2 → v3 变更摘要

| 项 | v2 | v3 |
|---|---|---|
| III 的 z | 随机指派、判别器不可见 → E2 不可达 | BARCODE 派生可观测状态 + 残差结构统计量 + ≤6 候选 max-stat 识别；不可识别→unresolvable/partial |
| abstention | 未定义（E1/E2 分母不明；E4=0.25 可被刷） | E1/E2 全非 null 世界、abstention 计错；E4≤0.10 + 每类 resolved≥0.85；E3 null 记账与卫生上限；算术自洽 |
| 预算表 | 6+20+12=38 vs k=36；k=24 装不下 26 | 20 单元结构化批次一次满足 I/II/III；k=6/12/20/24/36 显式分配与复用；II 5/8 细胞组定义 |
| MDE/δ_min | MDE（差）直接比 0.80/0.70/0.10/0.25 | δ_min = 目标−机会（0.30/0.20/0.05/0.10），同单位比较；≥1,000 批；代码落盘 |
| 药对单位 | 有向/无序未写死 | C2′ 有向主、U/top-k 无序主、双口径报告 |
| U/S | "U 与 S 按药对不相交"错误断言 | U = both-unseen − S 涉及对；逐折 U 大小与 top-k 规则写死 |
| 接口 | schema 未版本化；κ 描述 | `a2_to_a1/v3` 版本化；κ 仅兼容性；不互作验证 |
| 设计版产物 | 未生成 | folds.json/constraints_check.json/constructive_sim.py 已落盘（未运行） |

## 是否可并入 A1 整体冻结

完成本 5 条后，A2 具备"约束库 + constructive 判别体检"的**可冻结设计**：约束/统计量/零分布、切分与 U/S、判别与记账、预算-功效、接口 schema 与设计版产物均齐；**但 constructive 体检与 MDE 必须在冻结后实际执行**才能判断 A2 模块是否可用（未运行=未验证）。因此：**建议在 Lead 冻结 A1 时把 A2 作为模块并入（草案转冻结），但报告中 A2 只能是"设计已冻结、体检待执行"，不得写"constructive 已通过"或任何效应。**
