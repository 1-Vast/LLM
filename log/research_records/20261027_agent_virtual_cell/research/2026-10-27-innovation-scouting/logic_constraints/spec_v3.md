# R198-A2v3 规格：约束库 / constructive 判别体检（并入前修订；A1 支撑模块）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-43
派生自：[spec_v2.md](spec_v2.md)（保留不改）+ 独立挑战 [challenge_A2_v2.md](challenge_A2_v2.md)（revise，≤5 必改）。v3 = **并入 A1 整体冻结前的修订版**；仍为 DRAFT，**不单独冻结**；**不运行效果/模拟器、不声称新颖性**。

## 0. 状态与定位

- A2 = A1 的"约束库 + constructive 判别体检"支撑模块（非独立候选）；唯一交付：约束可否定性定义/统计量、constructive I/II/III 判别体检设计、候选状态与固定探针清单。
- 边界引用：C176（R196 `replicated_under_audit` 作废、C130 审计级可靠性未建立）、C177（R197 v1 协议作废、低秩结构未检验）——只引状态；C3→R196v2、C5→R197v2/校准线（A2 不重做）；III 认证→A4；acquisition→A5；replay 主判定→A1。
- 纪律：C1′ 只作 QA（即使显著也不得写"同靶点=同功能"）；replay 不报归因正确率/收益；不是新算子、不重开 R2 KG。

## 1. 挑战 5 条必改在本规格中的落点（摘要）

| 必改 | v3 落点 |
|---|---|
| 1. III/E2 可达性 + abstention 记账 | §4.3 z 改为**可观测但未进入模型/关系的元数据变量**；K_A2 规则 4 给出**可观测残差结构统计量 + 候选状态多重比较**；E1/E2/E3/E4 的 abstention 记账写死（§4.4） |
| 2. 预算-功效表重写 | §4.5 **显式单元分配与复用规则**（k=6/12/20/24/36；核心 = 20 单元结构化批次同时满足 I(6)/II(10+10)/III(2×6)）；模拟器规模/批数/≤30 min 预算核算（protocol_v3 §6） |
| 3. MDE/δ_min 同单位 | §4.4：四个终点各自"目标水平 − 机会/基线"δ_min（0.30/0.20/0.05/0.10）；MDE 定义为**可分辨的正确率/率差**，与同单位 δ_min 比较；模拟器/MDE 代码落盘（不运行） |
| 4. 药对单位 + U/S | §2.4：C2′ 组计数**有向**（2,025 个有向对/331/275/165/90,589 单元）；U/top-k 用**无序**（1,294 无序对）；S=24 定向单元且**24 个不同无序对**；U=both-unseen 对 − S 涉及对；逐折 U 大小见 `folds.json` |
| 5. 接口/冻结清单 | §6 schema 版本化 `a2_to_a1/v3`；κ≥0.60 **仅兼容性检查**、A1/A2 同类判别不互相当验证；`folds.json`/`constraints_check.json` 设计版已落盘（SHA 见 record_v3）；constructive 模拟器代码落盘不运行；冻结清单 §7 |

## 2. 三统一（v2 已定，v3 补单位口径）

- 数据：GDSC Jaaks Original fitted（SHA `1188968c…a278`）；只用 GDSC 表内每臂单标签（ANCHOR_PATHWAY 17 / LIBRARY_PATHWAY 21；TARGET 40/58）；**P-A2 映射不用**。
- 端点：`SYNERGY_DELTA_EMAX`（Lead 确认；P-B/P-B2 冻结口径）。
- 切分：drug-level 5 折×13 药（seed 20261027；`folds.json` 设计版已落盘）；四集合 Ref/S/E/U 不相交规则见 §2.4。

### 2.4 药对单位（有向/无序双口径，写死）

| 量 | 有向（directed） | 无序（unordered） | 用途 |
|---|---|---|---|
| 药对总数 | **2,025** | **1,294** | — |
| cell×pair 单元总数 | **108,259** | — | 分析单元 |
| both-unseen（每折） | **45/66/72/82/108** | **33/49/48/49/58** | 池 |
| cell×pair 单元（每折） | **1,898/3,693/3,588/4,613/6,232** | — | 功效 |
| C2′ 组计数（主口径） | **331 组；≥2=275（1,969 对）；≥4=165（1,698 对；90,589 单元）** | 敏感性：305 组；≥2=215；≥4=117 | 约束检验 |
| S（反馈） | 24 个 directed 单元；**24 个不同 directed 对 ∧ 24 个不同 unordered 对** | — | 反馈 |
| U（行动菜单，主口径） | both-unseen directed 对 − S 的 24 对 → **21/42/48/58/84** | both-unseen unordered 对 − S 覆盖的 24 个 → **9/25/24/25/34** | 选药评估 |
| top-k | directed-U top-k=10（鲁棒性） | **unordered-U top-k=10**；fold0（U=9）预注册 top-k=5 | 未测药物选择描述 |

- 断言：S 的 directed 对与 unordered 对都**不在 U** 中（U 定义已减）；S 单元 ∉ E；Ref 与 S/E 按药对组不相交；删除 v2 "U 与 S 按药对不相交"的错误断言（改为"U = both-unseen − S 涉及对"）。
- 组计数主口径用**有向**（因为每折/每臂角色不同：anchor/library 的角色与通路标签绑定）；无序口径仅敏感性报告（305/215/117 组）。

## 3. 约束库 v3（沿用 v2 C1′/C2′/C4′/C6′，仅补单位与状态候选）

- **C2′（主）**：directed（anchor 通路, library 通路）组，主检验 ≥4 配对 165 组（1,698 对/90,589 单元）；统计量/零分布/多重比较同 v2；输出字段见 §6。
- **C1′（QA only）**：library 臂 58 标签（51 单药+7 双药，无 ≥3 组）；只描述；即使正显著也不得写"同靶点=同功能"。
- **C4′（exploratory）**：3 组织；组织×通路有 0 细胞格（`constraints_check.json` 记录口径）。
- **C6′（QA）**：KEGG/Hallmark 重叠 vs 组相似度。
- **交出的 C3/C5**：不重做。
- **候选状态清单（≤6 个，预注册；用于 III 检出与 A1 接口）**：① `Tissue`；② `*_DRUG_TYPE`（2 水平）；③ 剂量布局（anchor/library 浓度档设计列）；④ `BARCODE` 派生批次组（见 §4.3）；⑤ 细胞系身份组（8 组，见下）；⑥ A4 提供的状态列（若可用，命名版本冻结）。

## 4. Constructive 判别体检（主实验；不运行，仅设计冻结）

### 4.1 世界生成器（元数据维度）
- 维度：65 药/2,025 directed 对/125 细胞/3 组织/165 主组/90,589 单元；细胞分 **8 组**（按 (Tissue, CELL_LINE_NAME) 排序 round-robin，`folds.json.cell_groups_8` 已落盘）→ 用于 II 的语境单位。
- 观测模型：`y = b_cell + b_pair + b_dose + g_group + h_state·z + ε`；`z` = **BARCODE 派生批次组**（从 Barcode 数字后缀奇偶/分组构造 2 水平；**可观测、真实存在于元数据，但模型/关系不使用它**）；σ 网格 {0.5,1.0,2.0}（预注册单位）、δ 网格 {1σ,2σ}。
- 噪声/效应尺度为**设计参数**（不读响应估计）；构造世界只用元数据维度与生成器，不接触真实响应。

### 4.2 注入（每类 ≥24 独立世界；3σ×2δ×4 世界/格）
| 类 | 注入 | 期望证据 |
|---|---|---|
| I 数值 | 只扰动 nuisance（b_cell/b_pair/b_dose 加 δ） | r_I 小（≤q_0.10 零分布分位）+ C2′ 违反率不超基线 |
| II 条件 | g 在 **8 细胞组中的 5 组**内符号翻转（−2δ），其余 3 组不变 | C2′ 违反 + 条件内/外一致率差 ≥δ_scope=0.20（内/外各 ≥10 单元）+ **≥5 个独立语境符号翻转**（语境=细胞组，构造里直接是 5 组） |
| III 状态 | `h_state·z` 非零（z=BARCODE 派生 2 水平，可观测未入模型） | 残差结构统计量显著 + 候选状态多重比较中 z 被识别（跨 ≤6 候选校正） |
| null | 只有 ε（无注入） | 不得判 I/II/III（false-class ≤0.10） |

### 4.3 III/E2 可达性修法（挑战必改 1）
- z 改为**可观测元数据变量**（BARCODE 派生批次组，2 水平，真实存在于元数据列、模型/关系不使用）；K_A2 规则 4 = 两步：
  1. **可观测残差结构统计量**（预注册三选一主 + 两备）：残差双峰 dip 统计量 / 2 成分 vs 1 成分潜类模型的 BIC 差 / 分组方差比（组间/组内）超零分布分位；
  2. **候选状态多重比较**：对 ≤6 预注册候选状态逐个做残差分层相关（或组间均值差），用 **max-statistic 置换零**（1,000 次）控制多重性；只有"结构统计量显著 ∧ 某候选（含 z）过校正阈值"才判 III，并输出被识别的候选变量。
- **公平性**：判别器不知道哪个候选被注入；z 必须在 ≤6 候选中"被识别"而非被直接喂入；若 z 未被识别 → 输出 `unresolvable`（不判 III）。
- E2（II vs III）因此在构造上可达：II 有 C2′ 条件内外结构、III 有可观测状态相关；若判别器仍不能分开 → `constructive_partial`（I 可分、II/III 不可分），不得删 E2 后重跑。

### 4.4 四个终点 + abstention 记账（预注册；挑战必改 3）
- **机会/基线**：balanced accuracy 机会 = 0.50；type-I 名义 α = 0.05；unresolvable 目标 0。
- **δ_min（同单位）**：E1 = 0.80−0.50 = **0.30**；E2 = 0.70−0.50 = **0.20**；E3 = 0.10−0.05 = **0.05**；E4 = 0.10−0.00 = **0.10**。
- **MDE 定义**：在给定世界池/批数下，80% 功效可分辨的 **正确率/率差**（与 δ_min 同单位）；每终点做 ≥1,000 模拟批估计 MDE；要求 **MDE ≤ δ_min**，否则 `design_uninformative`（不进入 replay）。
- **abstention 记账（写死）**：
  - E1/E2：分母 = **全部非 null 世界（含 abstention）**；abstention 一律**计错**；另报 resolved-only balanced accuracy 作为**次级描述**（不作判定）。
  - E4：unresolvable 率（非 null 世界上）= 1 − resolved rate；判定 **≤0.10**（从 v2 的 0.25 收紧，见下）。
  - 每类 resolved rate ≥ **0.85**（E4b，防对某一类全 abstain）。
  - E3：null 上 false-class 率 ≤0.10；abstention 在 null 上**计为无假类（正确）**，但 null resolved rate 只作描述且 **≤0.50** 为卫生上限（不作为判定；防"全 abstain 过 E3"由 E1/E2/E4b 挡住）。
  - **算术自洽检查**：E4≤0.10 ⇒ resolved≥0.90；E1 在 all-worlds 分母下 0.90·resolved_acc ≥0.80 ⇒ resolved_acc≥0.889；E2 ⇒ ≥0.778。三者相容且已写进协议；若把 E4 放宽到 0.25，E1 0.80 与 all-worlds 记账数学上不可同时满足——故 v3 收紧 E4 至 0.10。

### 4.5 预算-功效表（挑战必改 2；消除 38 vs 36、26 vs 24 冲突）
**核心创新：一个 20 单元结构化批次同时满足三项需求**——10 单元"条件内" + 10 单元"条件外"；每个 10 元层内按状态 z 平衡 5/5 → II（10 vs 10）、III（z 各 10 ≥6）、I（20 ≥6）全部满足。无需求相加（不再有 6+20+12=38）。

| k | 显式单元分配 | 可判 | 复用规则 |
|---|---|---|---|
| 6 | 6 单元：3 in/3 out（z 各 3） | 仅 I vs null | I 用全部 6；II/III 不判 |
| 12 | 12 单元：6 in/6 out；每层 z 3/3 | I + III | I 用 12；III 用 z 各 6（≥6）；II 不达（内/外各 6<10） |
| **20** | **20 单元：10 in/10 out；每层 z 5/5** | **I + II + III** | I 用 20；II 用 10 vs 10；III 用 z 各 10（≥6） |
| 24（replay） | 20 单元结构化批次 + 4 单元备用（I/II 用；III 不认证） | I + II（真实数据） | 4 备用于 I 精度；II 仍用 10/10；III 只出 proxy flag |
| 36 | 20 结构化 + 16 独立确认批次（8 in/8 out；z 4/4） | I+II+III + **稳定性复验** | 16 批次**不用于放宽阈值**（内/外各 8<10 → II 不达），只检验"方向是否在独立批次复现"（描述性） |
- II 的"≥5 独立语境"：构造中 **语境=8 个预注册细胞组**；II 注入在 **5 组**翻转（5≥5 达标），单元按 10 in（5 组×2 单元）+10 out（3 组：4+3+3）；判别时按组给符号、计跨组一致数。
- 预算核算（constructive 模拟器，仅供冻结后运行）：96 世界（4 类×24）× 平均 90,589 单元 ≈ 8.7M 数值；分类器每批 ≤36 单元 + 每世界预计算参考统计；MDE 4 终点 × 4 k × 1,000 批 = 16,000 次轻量分类 → **估计 ≤5 min（CPU），硬上限 30 min**；代码落盘不运行（`constructive_sim.py`，SHA 记 record_v3）。

## 5. 真实 replay（次级，不变）
- 仅 constructive_pass（或 Lead 允许 partial）后；每折：Ref 参考/关系表，S=24（§2.4 规则），E=余下 both-unseen 单元，U=§2.4 菜单。
- 只报：C2′ 违反统计量分布（与零分布对比）；归因分布（描述，含 unresolvable）；U 上 top-k 预测排序与描述性后悔——**不报归因正确率/收益/机制**。
- 失败类别：`insufficient_units`/`not_identifiable`/`design_uninformative`；不得写成阴性。

## 6. A1/A4/A5 接口（schema 版本化；挑战必改 5）
- **schema id：`a2_to_a1/v3`**（字段名/类型/单位冻结）：`constraint_id:str, group_key:{directed:(str,str), unordered:str}, n_pairs:int, n_units:int, stat:float, ci_low:float, ci_high:float, null_p:float, bh_q:float, sign_flip_contexts:int, in_condition_units:int, out_condition_units:int, candidate_states:list[str], identified_state:str|null, residual_structure:{name:str,stat:float,p:float}, fixed_probe_list:list[{cell:str, pair:str}]`。
- **κ≥0.60 仅兼容性检查**（描述性）：A1/A2 对同一构造世界输出的一致性；κ 高只说明口径兼容，**不作验证/主判定证据**；A1/A2 的同一类判别**不互相当独立验证**；`X_flip`/`δ_scope` 只作为预注册口径对齐，不互作验证。
- 仲裁：replay 冲突→`interface_disagreement`，不取单一归因，A2 让位 A1，冲突样本全保留。
- A4：III 认证归 A4（A2 只给候选状态与每状态 k=6 探针）；A5：probe 收益归 A5；C3→R196v2、C5→R197v2。
- 引用 C176/C177 作废状态；不引 C130 数字/R197 结论当证据。

## 7. 冻结清单（并入 A1 时执行）
- [x] `folds.json`（种子 20261027；5×13 药；directed/unordered/U/top-k；S24 抽样设计；cell_groups_8）——设计版已落盘，SHA 见 record_v3
- [x] `constraints_check.json`（331/275/165 组 + 90,589 单元；有向/无序双口径；目标组；逐折组覆盖；零分布计划）——设计版已落盘
- [ ] `constructive_sim.py` 已落盘但**未运行**（SHA 见 record_v3）；constructive 体检与 MDE 模拟须在冻结后执行
- [ ] `SYNERGY_DELTA_EMAX` 列义确认（引 R198 record）
- [ ] 候选状态清单版本（BARCODE 派生规则、细胞系身份 8 组、A4 状态）写死
- [ ] 明确：constructive 先于 replay；replay 不报归因正确率/收益；C1′ QA only
