# R201-A 报告：跨计划一致反事实细胞模型——形式化、O'Neil 资格与最小设计（不运行效果）

2026-10-28。角色：独立审计/设计员（未参与 R197/R200 模型开发）。任务 task-102（R201-A，机制 A 形式化+资格+最小设计）。
**只做形式化/资格/设计：不运行效果、不拟合预测、不读响应值做统计；不声称新颖性/机制/迁移/决策收益。**
- 形式化（先于资格脚本冻结）：[PROBLEM_A.md](PROBLEM_A.md)（SHA256 `dfb2dce81d59e2826ed5d5fb2beee6b8b7f0bdca54444f488fec80fbe0c84570`）
- 资格审计（metadata/结构/算子一致性）：[qualify_A.py](qualify_A.py)（`fbb9d3cf83b8a2167bcdc6eb40e9eb16872f9af37057cc820b42783c53cd113b`）→ [qualify_A.json](qualify_A.json)（`d1dd270629ef6449f08bc381d080155dfffc5cc562290929bdc5458f8457c2d4`）
- 设计（预注册草案，不执行）：[DESIGN_A.md](DESIGN_A.md)
- 记录/用量：[record_A.md](record_A.md)、[usage_A.json](usage_A.json)
- 状态：🟡 待独立挑战（endpoint-auditor/i003）；本轮不进入执行。

## 0. 结论摘要

1. **形式化完成**：计划 p（剂量组合/成员替换/程序）、共享算子 S（成员剂量响应 `f_{a,role}` + 伙伴函数 + 交互核 + 角色分层 + 噪声合同）、**联合矛盾度量** `J(p,q)=ε_{pq}−max(ε_p,ε_q)`（单独合法、无同一 S）、可辨识条件（重叠/角色/gauge/过识别/非矩形/噪声容差）、反事实查询 `V(p*)` 与同一世界最坏简单后悔 `R(p)=max_q h_V(c_q−c_p)`；给出 **3 个构造性矛盾例子**（群体单步边缘相同、联合不可能；4×4 剂量网格成员效应跨伙伴不一致；秩 1 交互下的跨计划不可能）。
2. **本地资格：O'Neil = `qualified_with_conditions`（仅开发性）**。complete-case 98.44%（363,090/368,832）；batch1 357,876 行/39 细胞/22,410 pair-cells；**完整 4×4 网格 pair-cells = 22,035（全批）/21,726（batch1）**；702 个 15 行 pair-cell、315 个 0 行（batch3 全失）与 ON2 数字逐项一致；39/39 细胞有完整网格；**target30 细胞 30/30**；drug-role 上下文 2,879（2,791 个 ≥2 上下文且剂量集完全对齐）；**共享成员+≥2 共同剂量的计划对 = 441,867**；加性算子设计 **每细胞过识别度 median 8,745（39/39 细胞 ≥1，target30 全 ≥1）** → 联合矛盾检验在结构上可行。
3. **判定与功效**：O'Neil 判 **`qualified_with_conditions`**（开发性：viability、技术重复≠独立培养、batch3 全失、702 行缺失、无双药参照、non-blind/peeked）；**决策收益终点判 `evaluation_cannot_distinguish`**：仅 30 个独立细胞，rank MDE80=**0.7625**、top-k MDE 0.33–0.36、regret MDE 0.10–0.26，全部 >δ_min=0.05；要决策认证需 **≈6,283 独立细胞（δ=0.05）** 或 **≈1,573（δ=0.10）**。Jaaks 判 `not_qualified`（ΔEMAX 端点、拟合表仅稀疏剂量对 ≤4、不可与 viability 拼接）。
4. **最小设计（预注册草案）**：主假设 H_A = 存在可检测联合矛盾（单独合法、联合不可行且 J≥δ_J=τ），且联合约束把最坏后悔区间收缩 ΔW≥δ_W=0.05；比较器 **C0–C9**（同信息全局求解/共享参数后验/约束生成/全历史重训/层级/GP/决策 AL/随机计划对/静态最佳预测+优化）；**等信息等预算**（≤256 wells/arm/折、≤2 CPU-h/arm、≤20 配置、5 折×6 细胞、同 mask）；主终点 P1 存在性 + P2 界收紧（开发性），决策终点 S1 仅描述性（`evaluation_cannot_distinguish`）；零模型（计划内置换/算子打乱/随机选择/半拆分 FPR/无约束对照）；失败类别与停止条件写死（`no_joint_contradiction`/`no_increment`/`no_decision_benefit` 等）。
5. **建议**：形式化+资格+设计提交独立挑战；**不执行效果**；先例 CoMap/LAWM/MDA/COPEx 已覆盖一般概念，**新意只在具体共享对象与更新运算且未认证**；决策/迁移需外部独立资源。

## 1. 形式化要点（详见 PROBLEM_A.md）

- **计划空间**：P-dose（4×4 网格的一行 `(d_a,d_b)`×4 技术重复）、P-replace（同成员/角色/剂量在不同伙伴上下文）、P-program（顺序/时点；本资源不支持，仅保留形式）。
- **共享算子 S**：`S_θ=(f_{a,role}(·), g_{b}(·), h, b_batch, σ_obs)`；`m(p;θ)=c_p^T m_H(θ)`；假设 A1–A4（刻度可比、共享分量重叠、状态充分、噪声可标定）。
- **联合矛盾**：`ε_p=min_θ r_p(θ)`、`ε_{pq}=min_θ max(r_p,r_q)`、`J=ε_{pq}−max(ε_p,ε_q)`；单独合法（≤τ）+ `J≥δ_J` = 存在联合矛盾；证书/见证由 θ*=argmin max 残差结构给出。
- **可辨识条件**：共享分量在 ≥2 计划中出现且剂量重叠；角色/gauge 固定；**过识别度 `over=#obs−rank≥1`**；联合约束非矩形（否则等效独立拟合）；`J>τ` 才可由数据支持。
- **反事实/决策**：`V(p*)={m(p*;θ):θ∈M_joint}`；`R(p)=max_q h_V(c_q−c_p)`；top-k/后悔；双预算规则（计算 vs 真实实验，成本全计）。
- **更新运算（"新意候选点"）**：反馈统一修订 `M`，所有复用该分量的计划边界一起更新（非逐点/逐计划重训）。
- **三个例子**：① 群体构造 BA=0 与 BAA=1/2 分别合法但同 p 不可能；② 加性 `y=f_a+g_b`：p1 推出 `f_a(d2)−f_a(d1)=2`、p2 推出 `=3`，各自单独精确拟合、联合不可能；③ 秩 1 交互下两对伙伴对成员交互方向要求 `u(d2)/u(d1)=1` vs `2` → 单独可行、联合不可行。**均为纸面/构造，不是数据发现。**

## 2. 本地资格审计（metadata/结构/算子一致性；`qualify_A.json`）

### 2.1 O'Neil 结构（数字与 ON2 逐项一致）
| 项 | 值 |
|---|---|
| 行/批次 | 368,832 行；batch1 358,560（39 细胞）/ batch2 5,232（9）/ batch3 5,040（15） |
| complete-case（viability1–4 全非空） | **363,090（98.44%）**；缺失 0/78/198/5,742；batch1 357,876 / batch2 5,214 / **batch3 0** |
| pair-cells | 23,052 总：**16 行完整=22,035 / 15 行=702 / 0 行=315**（全批；batch1=21,726） |
| 完整 4×4 网格 pair-cells | 全批 **22,035**；**batch1 21,726**（batch1 有 684 个 pair-cell 为 15 行） |
| 细胞/药物/无序药对 | 39 / 38 / 583；每细胞完整网格 pair-cells 中位 **565**（min 494） |
| drug-role 上下文（cell,drug,role） | **2,879**；≥2 pair-cell 上下文 **2,791**；剂量集完全对齐 **2,791（96.9%）** |
| 共享 (cell,drug,role,dose) 级别 | **11,164** 个剂量水平在 ≥2 上下文重复出现 |
| 计划对（同成员/同角色 + ≥2 共同剂量） | **441,867**（每细胞中位 11,623） |
| 加性算子设计 | obs=16×pair-cells；参数=角色剂量效应；rank 中位 295；**过识别度中位 8,745**；39/39 细胞 ≥1、≥16；target30 全 ≥1 |

**读法**：O'Neil 的 4×4 网格 + 每个细胞 ~565 个伙伴 pair-cells + 剂量集对齐 → **跨计划（成员替换/剂量行）共享算子的重叠与过识别充足**，联合矛盾检验在结构上可行；但每个 pair-cell 的 16 行共享 wells/批次，留出必须整块（§4 设计）。

### 2.2 参照/端点
- 组合工作簿**无单药/vehicle 参照行**（0 行；两药齐全）；单药工作簿存在（16,752 行/39 细胞/38 药，metadata only 未读）——若要锚定绝对 `f_a` 曲线需另立资格。
- **Jaaks 拟合表 `not_qualified`**：296,707 行/125 细胞/1,294 无序药对/70,360 cell-pair 键；**每键剂量对最多 4（稀疏，无完整 4×4 网格）**；端点为 ΔEMAX（与 viability 不同族）→ **不可拼接、不作 CL1 目标**。

### 2.3 判定
**O'Neil = `qualified_with_conditions`（开发性）**。条件（写死）：仅 viability；技术重复≠独立培养；batch3 全失；**702 个 15 行 pair-cell 排除**、不插值；无双药参照；**non-blind/peeked 继承 ON3**（QUICK invalid artifact 已见；不得称盲验/独立确认）；联合矛盾只在过识别≥1 且成员/剂量重叠处可检；决策收益在本资源 `evaluation_cannot_distinguish`；不与 Jaaks ΔEMAX 拼接；不称迁移/机制/新颖性。

## 3. 已冻结（或明确边界）的预注册要素

| 要素 | 冻结值/规则 |
|---|---|
| δ_min | **0.05**（归一化决策效用尺度；operational：最小可靠秩/排序信息差，非效用阈值） |
| MDE | `MDE80=2.801585×SD_cluster_bootstrap(Δ)`（cluster=细胞）；30 细胞下 rank **0.7625**、top-k **0.33–0.36**、regret **0.10–0.26** → **决策终点 `evaluation_cannot_distinguish`** |
| 决策认证所需独立细胞 | **≈6,283（δ=0.05）/≈1,573（δ=0.10）** |
| 计划对/δ_J/δ_W | S-add 主族；`δ_J=τ`（95% 噪声界）、`δ_W=0.05`；预注册后不得改 |
| 切分 | 5 折×6 细胞；留出整 pair-cell/剂量行；训练不得见留出计划 wells |
| 等信息/预算 | 同 prior 数据、同 wells（≤256/arm/折）、同计算 cap（≤2 CPU-h/arm、≤20 配置、≤8 GB）；求解/证书/重认证计费 |
| 比较器 | C0 均值 / C1 同信息全局求解 / C2 共享参数后验 / C3 约束生成 / C4 全历史重训 / C5 层级 / C6 GP / C7 决策 AL / C8 随机计划对 / C9 静态最佳预测+优化 |
| 零模型 | 计划内置换、算子打乱、随机选择（C8）、技术分半 FPR、无约束对照；不拼 ΔEMAX |
| 失败类别 | `data_unavailable` / `design_invalid: identifiability/coverage/leakage/budget` / `evaluation_cannot_distinguish` / `no_joint_contradiction` / `no_increment` / `no_decision_benefit` |
| 停止条件 | P0 不过 → design_invalid；P1 不达 → `no_joint_contradiction` 停前提；任何强基线等预算等效 → 撤回算法主张；只改已测计划 → 停反馈迁移；决策不成立 → 停决策创新 |

## 4. 最小实验设计要点（DESIGN_A.md；本轮不执行）

- **P0 门槛**（先于打分）：每折覆盖/可识别/噪声标定（资格审计 median over-id 8,745、rank 295、plan pairs 441,867 支持；阈值预注册）。
- **P1 主终点**：联合矛盾存在性（单独合法 + `J≥δ_J` 的计划对比例/数；预注册 ≥5 细胞各 ≥1 对且 pooled ≥1%——阈值在挑战后冻结，不得看结果改）。
- **P2 主终点-2**：联合约束的界收紧 `ΔW≥δ_W=0.05`（相对单计划界）。
- **S1 决策终点**：仅描述性（MDE>δ_min → `evaluation_cannot_distinguish`）；**不得写决策收益**。
- **S2 算法/预算**：active 计划差选择 vs C7（决策 AL）/ C8（随机）在等 wells+计算下达到 ΔW/后悔界目标的成本；任一等效 → 撤回主张。
- **双预算**：每步比较"继续计算缩小 V 的成本"与"真实计划对 VoI"；两类成本全计；超过 cap → design_invalid。

## 5. 边界与措辞（写死）

- 仅开发性 O'Neil；**不称**新颖性/机制/迁移/决策收益/独立确认；先例 CoMap/LAWM/MDA/COPEx 覆盖一般概念（模型+策略共同更新、动作-状态联合、机制后验/VoI、动态约束实验设计），**新意只在具体共享对象与更新运算**且未认证。
- **不重复**：D1 跨计划一致独立目标 stop（C189）/D3 design_invalid（C187）/A1 data_unavailable（C181）。
- **不拼 ΔEMAX**；不把技术重复当独立生物单位；阴性 ≠ 不存在；宽界 = 未决而非失败。
- peek 披露：ON3 QUICK invalid artifact 已见 → 本方向设计/执行均为 non-blind/peeked，不得称盲验。

## 6. 所需测量/缺口

- **决策认证**：≥6,283 独立细胞（δ=0.05）或 ≥1,573（δ=0.10）；独立生物单位（细胞系/患者来源培养），非 wells/技术重复/计划数。
- **迁移/机制**：不同测量模态或独立培养的组合资源（≥10 共享细胞、≥10 有向对、≥500 匹配键/四元组，A0 复用门槛；与 O'Neil wells 不相交）；P-program（顺序/时点）资源本地不存在。
- **单药参照**：若锚定绝对剂量响应曲线，需单药工作簿独立资格（同 lab 技术重复 ≠ 独立培养）。
- 当前缺口记录于 `qualify_A.json → qualification.required_measurements_for_decision_claim`。

## 7. 产物与确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A.md` | `dfb2dce81d59e2826ed5d5fb2beee6b8b7f0bdca54444f488fec80fbe0c84570` |
| `qualify_A.py` | `fbb9d3cf83b8a2167bcdc6eb40e9eb16872f9af37057cc820b42783c53cd113b` |
| `qualify_A.json` | `d1dd270629ef6449f08bc381d080155dfffc5cc562290929bdc5458f8457c2d4` |
| `DESIGN_A.md` / `report_A.md` / `record_A.md` | 见 `usage_A.json` |

**确定性**：同脚本两次运行 `qualify_A.json` 逐字节一致（两次运行 `qualify_A.json` 逐字节一致（`d1dd270629ef6449f08bc381d080155dfffc5cc562290929bdc5458f8457c2d4`；run1 wall 137.5 s、run2 wall 136.4 s；差异仅来自机器负载，产物无差异））；输入 SHA 全部写入 JSON；JSON 键排序/无时间戳/allow_nan=False；单命令 wall ≈137.5 s（≤15 min 预算）。

## 8. 建议

- 将 **PROBLEM_A（形式化）+ qualify_A（资格）+ DESIGN_A（预注册设计）** 提交独立挑战（endpoint-auditor/i003）；挑战通过前**不执行效果**。
- 挑战重点：联合矛盾度量的可辨识/噪声容差（δ_J=τ）、over-id 与计划对计数的解释、P1/P2 阈值选择、留出整块防泄漏、等信息/预算 cap、决策终点 `evaluation_cannot_distinguish` 的边界措辞。
- 若挑战通过：先做 **P0+P1**（开发性形式/存在性），再在等预算下做 **P2+S2** 的算法比较；**S1 决策终点保持描述性**，升级需外部独立细胞资源。
