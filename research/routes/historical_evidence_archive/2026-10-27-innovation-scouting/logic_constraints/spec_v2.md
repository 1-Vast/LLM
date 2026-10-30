# R198-A2v2 规格：约束库 / constructive 判别体检（A1 支撑模块）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-38
派生自：[spec.md](spec.md)（v1，保留不改）+ 独立挑战 [challenge_A2.md](challenge_A2.md)（revise，≤5 必改）。本文件是 **v2**：**不单独冻结、不作为独立候选**；定位为 **A1（conflict_signal）的"约束库 + constructive 判别体检"支撑模块**。
**本轮不运行效果/训练/回放/拟合，不读响应做效果**；所有"可检验"均指**设计上可检验**。

## 0. 状态、降级与先例边界

- **降级决定**（Lead 处置 + 挑战结论）：A2 不单独冻结；不主张新算法；不声称"三类失败已可区分"。A2 唯一交付 = **10 条约束的可否定性定义 + 可执行统计量**、**constructive I/II/III 判别体检**、**候选状态/固定探针清单**（供 A1 接口）。
- **先例状态引用**（不得当已认证结论）：
  - C176（R196 判定撤回）：`replicated_under_audit` 作废，C130 审计级可靠性**未建立** → A2 **不引用 C130 数字作为约束证据**，只把它当"待 R196v2 提供状态的关系候选"（C3 交 R196v2）。
  - C177（R197 v1 协议作废）：低秩结构**仍未检验** → A2 不引用 R197 当"结构不存在/已检验"。
  - C172/C174：1.43% 仅加性条件主效应份额；Q2 加权矩/依赖单位/可靠性需重核 → A2 不把方差分割当机制比例；依赖单位按细胞/药对聚类（不做 iid 近似）。
  - R2 本地先例：KG 动作设计 vs 随机 = +0.001884 [−0.081112,+0.063593]（本文件只在 §6/§8 讨论 acquisition 边界时引用；A2 不评 acquisition 收益）。
- **不是新算子**：v1 的"约束违反→I/II/III 归因"不再作为独立机制主张；v2 只检验"**约束统计量 + 预注册判别式能否在已知注入下把 I 与 II/III 分开**"。不得写"同靶点=同功能""通路=机制""归因正确=真实失败机制"。

## 1. 职责边界与去重（冻结前写死）

| 角色 | 拥有 | A2 只消费/输出 | 禁止 |
|---|---|---|---|
| **A1 conflict_signal** | 更新器（M1/M2）、(i)/(ii)/(iii) 的模型更新侧签名（χ²/Λ_null、X_flip/J_min、ΔR²_state）、replay 归因 | A2 输出：约束表、违反统计量、候选状态、固定探针；A2 不做更新器/不评归因收益 | 不得重复实现/评估更新器；不得把 A2 判别当 replay 归因 ground truth |
| **A4 missing_state** | 状态表征是否可加、如何加、III 的认证 | A2 只输出"候选状态变量清单 + 状态分层探针设计" | A2 不评状态表征收益、不认证 III |
| **A5 acquisition_stage3** | acquisition 比较（DPG/随机/方差/EIG/整板成本） | A2 的探针仅作**固定预注册探针**（评估协议），不做策略比较 | A2 不报 acquisition 收益；H-A2.1 的"CVT vs random"若保留必须并入 A5 目录 |
| **R196v2** | C130 审计级重估（C3） | A2 引用其状态，不重推 | 不引 C130 数字当证据 |
| **R197v2 / 校准线** | C5 单药解释/校准（含 Q2 重校准） | A2 引用其状态，不重做单药-交互方差分析 | 不重做方差份额分析 |
| A2（本文件） | 约束可否定性检验 + constructive 判别体检 | 见上 | 不评更新器/状态/acquisition/机制 |

## 2. 三统一（切分 / 端点 / 注释）

### 2.1 数据与注释源（二选一，v2 选 GDSC 表内）

- **冻结资源**：GDSC Jaaks **Original** fitted 表（`data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`；SHA256 `1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278`，198,893,607 B；数量事实：296,707 行 / 2,025 药对 / 125 细胞 / 3 组织 / 65 药（46 anchor + 65 library））。Validation（I7，SHA `dcbd4c31…2775`）**本轮/本轮 A2 不使用**（外部确认不在 A2 范围）。
- **注释源固定为 GDSC 表内每臂单标签**：`ANCHOR_PATHWAY`（17 水平）+ `LIBRARY_PATHWAY`（21 水平），按臂角色使用、**不合并成药物级标签**；`ANCHOR_TARGET`（40 水平）/`LIBRARY_TARGET`（58 水平）同理。
- **P-A2 映射（mapping_table_v2）在 v2 中不使用**：它是 DrugComb 药物→KEGG 的映射（4,088 药中 1,800 映射、125 水平），与 GDSC 每臂单标签是两套口径；v1 混用是挑战指出的三处不一致之一。若未来必须用 P-A2：**先写独立映射协议**（版本 SHA `705a5e64…d015`、覆盖率、未映射处理、损失），且不得与 GDSC 模板混算。

### 2.2 端点

- 主端点固定 **`SYNERGY_DELTA_EMAX`**（Lead 已在 R198 record §1 确认；P-B/P-B2 已冻结该列口径）。**不得**再用 `SYNERGY_OBS_EMAX − SYNERGY_EXP_EMAX` 的"待确认"表述；不得换端点/换聚合救结论。
- 其它连续协同指标（Bliss/Loewe/ZIP 等，ρ=0.806–0.967 非独立，C99/C100）只作诊断，不入主判定。

### 2.3 切分（drug-level，四者不相交）

- **折**：65 药按**预注册随机排列**分 **5 折 × 13 药**（种子 20261027；分配表在冻结时以 `folds.json` 落盘并记 SHA；不按字母序/药物名系列切，以免同类化合物聚集）。
- **四集合（互不相交）**：
  1. **参考集 Ref**：两药均不在本折 held 集合中的药对单元（用于约束/参考统计/关系表估计）；
  2. **反馈集 S**：从本折 both-unseen 药对池中按**响应盲**规则抽 k=24 个 cell×pair 单元（固定种子、按细胞/组织/药对分层）；
  3. **评估集 E**：本折 both-unseen 池中 S 之外的 cell×pair 单元；
  4. **行动菜单 U**：本折 both-unseen 药对（按药对聚合，用于"未测药物选择"描述性评估），**不使用 U 的响应值做选择**（冻结 U 与 E 的划分：U 是药对层面，E 是单元层面，二者预注册分离）。
- **fold 规模（本元数据实测，冻结时以落盘为准）**：种子 20261027 下 5 折 both-unseen 药对数 = **45 / 66 / 72 / 82 / 108**，对应 cell×pair 单元 = **1,898 / 3,693 / 3,588 / 4,613 / 6,232**（median cells/pair = 47；各折不均衡，分析按折为 block 的配对统计，并报最小折）。**v1 的"20% 药对 + 按药物聚类"自相矛盾表述删除**：只有 drug-level 一种切分。
- 反馈与评估的单元严格 disjoint：S 的 24 个 cell×pair 从未进入 E；Ref 与 S/E 按药对分组不相交。

## 3. 约束库 v2（C1′/C2′/C4′/C6′ + 交出的 C3/C5 + 排除项）

**统一形式**：`C_k = (A_k 前件关系, Π_k 适用条件, B_k 可测关系, T_k 统计量, N_k 零分布, R_k 修订动作, F_k 失败类别)`；所有区间/检验按**药对与细胞双向聚类 bootstrap**（≥2,000 次）与**分层置换**（≥1,000 次），不做 iid 近似（C174）。

### C1′（target 级单药谱相似；**exploratory only，不作门控**）
- 定义：同 `*_TARGET` 标签的 library-臂药物（仅 library 臂有单药拟合列 `LIBRARY_EMAX/XMID/AUC`；anchor 臂只有单点 `ANCHOR_VIABILITY`，**不能**构造单药谱，故 C1′ 只覆盖 library 臂）在共同细胞上的单药功能谱（log XMID / EMAX 向量）相似度 − 匹配零。
- **可执行性实测**：`LIBRARY_TARGET` 58 个标签中，**51 个单药、7 个双药**（无 ≥3 组）；`ANCHOR_TARGET` 40 个中 34 单药、6 双药。**同靶点只有 size-2 组** → 检验功效极低（MDE 将由 §5 的模拟给出，预计不可分辨）。
- 判定：C1′ **只作描述性 QA**，不用于门控/删除任何约束；**即使未来某资源上显著，也只支持"单药功能谱相似"，不得升级为组合功能等价或"同靶点=同功能"**（纪律规则，不是经验结论）。
- 零分布：打乱药↔target 标签（层内保组大小、匹配 `*_DRUG_TYPE` 2 水平）；报告组内相似度与匹配零的并列差。

### C2′（pathway-pair 交互方向共享；**主约束**）
- 定义：关系单位 = (anchor 通路, library 通路) 组，B_k = 组内药对在细胞语境上的交互（`SYNERGY_DELTA_EMAX` 符号/秩）的一致性；Π_k = 两臂通路标签均为表内单标签、且两组通路在训练侧均已出现、剂量布局为已发布设计列；**删除 v1 的"两药身份缺失"条件**（那是 C130 regime，属 C3→R196v2，与 C2 统计量错配，挑战已指出）。
- **组计数写死（本元数据实测）**：331 个 (anchor,library) 通路对；**≥2 药对组 275 个（覆盖 1,969 药对）**；**≥4 药对组 165 个（覆盖 1,698 药对、90,589 cell×pair 单元）**。**主检验只用 ≥4 药对组（165 组）**；≥2 药对组（275）作敏感性；<2 药对组只登记、不检验。
- 统计量 T：组内药对×语境符号与组参考符号的一致率（或组均值秩相关），与同规模随机（保持每组药对数、通路水平可观测性）比较；按药对/细胞聚类 bootstrap。
- 零分布 N：在药物层面置换 pathway 标签（保持每臂水平计数与药对图结构）；另做尺寸匹配随机块（C152 式）。
- 修订动作 R：违反只记录为"约束违反"，**不自动删/改关系**（删改属 A1 的发布/释放决策）；A2 输出 `constraint_id, group, violation_stat, in/out-condition split, candidate probe cells×pairs`。
- 失败类别 F：见 §5（I/II/III 判别）。

### C4′（组织适用性；**exploratory**）
- GDSC `Tissue` 仅 3 水平（Breast/Colon/Pancreas）；`Tissue × 通路` 交叉有多处 0 细胞（例如 Chromatin histone acetylation 在 Colon/Pancreas 为 0；WNT/IGF1R 等在部分组织为 0，见 `tmp/a2v2_metadata_counts.py` 输出）→ **不能作主约束**；只描述"同组织内 vs 跨组织的 C2′ 一致率差"，并提供给 A1 作适用条件候选。

### C6′（注释谱系一致性；**QA only**）
- KEGG/Hallmark 基因集重叠与 C2′ 组相似度的秩相关；仅用于注释源 QA，不入主判定。

### 交出的两项（不在 A2 重做）
- **C3（C130 both-unseen 检验）→ R196v2**：A2 只引用状态（C176：审计未通过，不得当已认证约束）。
- **C5（单药解释界/交互方差份额）→ R197v2/校准线**：A2 不重做；不把 R194/Q2 的方差分割当机制比例（C172/C174）。

### 排除项（登记，不检验）
- C8 已知药对先验（同源泄漏）；C9 独立培养重复（不可得）；C10 靶点占据/通路激活（不可得）；C7 剂量占据（GDSC 有数值浓度可部分做，但超出 A2 支撑模块范围，登记给未来线）。

## 4. 主实验：constructive I/II/III 判别体检（**取代 replay 成为主终点**）

### 4.1 为什么是 constructive
真实 GDSC 没有 I/II/III 的 ground truth（挑战最致命 1）。v2 **不**把 replay 当效果实验：**主实验 = 在已知注入的合成世界上检验判别式**；真实 replay 只作次级描述（§5）。这是"体检协议"，不是"归因正确率"的实证主张。

### 4.2 合成世界（只用元数据维度，不读响应）
- 结构复制 GDSC 元数据：65 药 / 2,025 药对（按实际药对图）/ 125 细胞 / 3 组织 / **331 个 pathway-pair 组（主检验 165 组；敏感性 275 组）** / 单元数按实际 cell×pair（90,589 主组单元）；**噪声/效应尺度是设计参数网格**（不是从响应估计）：σ ∈ {0.5, 1.0, 2.0}（以 `SYNERGY_DELTA_EMAX` 的预注册单位），效应幅度 δ ∈ {0.5σ, 1σ, 2σ}。
- 观测模型：`y = b_cell + b_pair + b_dose + g_{pathway-pair} + z-effect(仅 III) + ε`（前四项=nuisance；g=关系效应；z=未表征状态效应）。

### 4.3 注入的 I/II/III + null（每类 ≥20 个独立世界 × 3 σ × 3 δ）
| 类 | 注入 | 期望判别证据 |
|---|---|---|
| **I 数值** | 仅扰动 nuisance（细胞加性/药对加性/剂量斜率/批次截距）δ_num；关系 g 不变 | 残差可被 ≤2 标量吸收；C2′ 违反率为 0/近 0；无 condition in/out 差；无状态相关 |
| **II 条件** | g 在预注册语境子集（如 1 个组织或 1 个细胞组）内符号翻转（δ_scope），条件外不变 | C2′ 违反；**条件内 vs 外一致率差 ≥ δ_scope=0.20**；≥5 个独立语境符号翻转（与 A1 挑战修正后的 X_flip n_min 对齐） |
| **III 状态** | 加未表征状态 z（2 水平，如"处理时间/培养基"类），其效应对 y 结构化、不可被 nuisance/关系吸收 | 全释放后残差结构化；与候选状态 z 分层相关；加入 z 后留出残差下降（同维随机块对照） |
| **null** | 只有噪声（无注入） | 不得判 I/II/III 任一（false-class 率 ≤0.10） |

### 4.4 判别器与主终点（预注册）
- **K_A2**（只用 A2 约束统计）：输入 `C2′ 违反统计量 + 条件内/外一致率差 + 候选状态分层相关`；规则见 §5。
- **K_joint**（A1 接口版本）：K_A2 + A1 签名（χ²/Λ_null、X_flip/J_min、ΔR²_state），用于 §6 的一致性检查；**K_A2 是 A2 的主检验对象**。
- 主终点（constructive，每格 ≥20 世界 × 预注册种子）：
  1. **I vs {II,III}** 的平衡正确率（先验预注册类别权重）≥ **0.80**；
  2. **II vs III** 平衡正确率 ≥ **0.70**（constructive 允许；真实数据不评）；
  3. **null false-class 率** ≤ **0.10**（type-I）；
  4. **unresolvable 率** ≤ **0.25**（定义：判别器输出 unidentifiable/mixed 的比例，在非 null 注入上算）。
- **MDE/功效预注册**：对上述 4 个终点各做 ≥500 次模拟批（预注册模拟器代码 + 种子）；**MDE 计算 = 在给定世界数与 σ/δ 网格下能达到 80% 功效的最小可分辨正确率差**；若任一终点的 MDE 超过其 δ_min（0.80/0.70/0.10/0.25）→ `design_uninformative`，**不得进入 replay**。
- 判定：4 个终点全过 → `constructive_pass`（可向 A1 提供约束库+判别器接口）；任一失败 → 记录 `constructive_fail`（哪一终点/MDE/不可判率），不换阈值重试；若只有 II vs III 失败而 I vs {II,III} 过 → 输出"constructive_partial（I 可分；II/III 需 A4 状态或更多预算）"。

### 4.5 预算-功效表（解决 k∈{6,12,24} 与判别式样本量冲突）
| 判别需要 | 最小单元/语境 | 说明 |
|---|---|---|
| I（≤2 标量吸收） | ≥6 单元 | 2 参数 × 3 df；CV 折=按药对分组 ≥3 折 |
| II（条件内/外） | ≥20 单元（内 ≥10 + 外 ≥10）+ ≥5 独立语境符号 | δ_scope=0.20 的 operational 理由：等价于"两比例 0.7 vs 0.5"的最小可操作差，且低于它不改变 A1 的发布/释放决策 |
| III 状态探针 | 2 状态 × 6 = ≥12 单元 | 每状态 k=6 由 §5 状态分层检验的最小配对组决定（3 df + 2 重复余量） |
| **全三类单批** | **≥38 单元** | 6+20+12；**k=24 单批不可行** → 分期：constructive 用 k∈{6,12,24,36} 网格给出"可判别到哪类"的曲线；**真实 replay 只用 k=24（I/II）**；III 真实认证归 A4（不再是 A2 的 replay 终点） |
- k=6：只能判 I vs null；k=12：I + 部分 II（内/外各 6 <10，**不达 II 门槛**）；k=24：I + II 达标（12/12 ≥10）；k=36：I+II+III（12/12/12）constructive 可行；**结论：v1 的"k∈{6,12,24} 同时判三类"不可能，v2 删除该说法**。

## 5. 真实 replay（**次级，仅描述**）

- **仅在 constructive_pass（或 partial 且 Lead 明确允许）后**运行；每折：Ref 训练参考/关系表；S=24 单元；更新器由 A1 提供（A2 不实现）；E=余下 both-unseen 单元；U=本折 both-unseen 药对菜单。
- **报告内容（预注册，只有三类）**：① 约束违反统计量分布（C2′ 组级，与零分布对比）；② 归因分布（K_A2/K_joint 输出计数，含 unresolvable）——**只作描述，不报"归因正确率"**（无 ground truth，挑战致命 1）；③ 下游选择描述（U 上 top-k 的预测排序/描述性后悔，不给收益结论、不评 acquisition）。
- **禁止**：把 replay 归因分布当效果、把下游描述当选药收益、把不同 k/折的差异事后择优、用 E/U 响应调任何阈值。
- 真实 replay 的**唯一用途**：给 A1 提供约束库的违反率/候选探针/接口一致性数据；任何"三类已在真实数据区分"的表述禁止。

## 6. 与 A1/A4/A5 的接口契约（预注册）

| 项 | 规则 |
|---|---|
| 主判定归属 | 真实 replay 的 (i)/(ii)/(iii) 归因**主判定 = A1**（其签名与更新器）；A2 的判别式只在 constructive 中作主检验，在 replay 中只作**数据侧证据** |
| A2→A1 输出字段 | `constraint_id, group_key, violation_stat, ci, null_p, in_condition_units, out_condition_units, sign_flip_contexts, candidate_state_text, fixed_probe_list`（JSON schema 冻结） |
| 一致性检查 | 在**同一 constructive 世界**上比较 K_A2 与 A1 签名：Cohen's κ ≥ 0.60 记 `interface_consistent`（描述性、非验证）；κ<0.60 记 `interface_divergent`，A1 冻结前必须解释 |
| 仲裁 | replay 中 A2 与 A1 归因冲突 → 标 `interface_disagreement`，**不取单一归因**；A2 让位于 A1 的更新侧判定；冲突样本全部保留并报告，禁止按结果挑一致样本 |
| A4 | III 的状态表征/认证归 A4；A2 只给"候选状态清单（tissue/drug_type/dose_layout + A4 新增变量）"与"每状态 k=6 探针设计" |
| A5 | probe/采样收益归 A5；A2 的 `fixed_probe_list` 只作评估协议，不作 acquisition 策略比较 |
| C176/C177 | 引用作废状态；不把 C130 数字、R197 结论当证据 |

## 7. 措辞模板、失败类别、冻结清单

**措辞模板（写死）**：
- 允许："在 constructive 注入下，K_A2 对 I vs {II,III} 的平衡正确率 = X（预注册阈值 0.80）"、"真实 replay 中 C2′ 违反率为 X（描述性）"。
- 禁止："三类失败已被区分/已证明"、"归因正确率 X"（真实 replay）、"同靶点=同功能"（即使 C1′ 正显著）、"约束迁移=新算法"、"通路=机制"、"unresolvable/无违反 = 关系不存在"。

**失败类别**：`data_unavailable`（注释/折/关系组无法冻结）、`design_uninformative`（MDE > δ_min 或 budget table 不达）、`constructive_fail`（4 终点任一失败）、`constructive_partial`（I 可分、II/III 不可分）、`interface_divergent`/`interface_disagreement`、`insufficient_units`（组计数/折单元不达标）、`not_identifiable`（真实 replay 描述性；不得写成阴性）。

**冻结清单（待 Lead/A1 整体冻结时并入）**：
- [ ] `folds.json`（种子 20261027 分配 + 每折药对/单元计数 SHA）
- [ ] 约束库 C1′/C2′/C4′/C6′ 的 `constraints_check.json`（331/275/165 组计数、每折组覆盖、零分布校准）
- [ ] constructive 模拟器代码 + 种子 + MDE 模拟结果（≥500 批）
- [ ] 判别器阈值（r_I、δ_scope=0.20、状态相关阈值、unresolvable≤0.25）与接口 schema
- [ ] 端点 `SYNERGY_DELTA_EMAX` 列义确认（引用 R198 record）
- [ ] 所有 SHA、seeds、失败类别落盘格式、预算/时间（CPU、单命令 ≤30 min）
- [ ] 明确：constructive 体检先于 replay；replay 不得报归因正确率/收益

## 8. 缺口（不声称空白）

- general-ML 先例只做**有界元数据检索**（belief revision+experiment 260 命中 / constraint learning+active learning 6 命中 / abductive+active learning 30 命中；均未读全文，未发现直接匹配）→ **不声称"空白/首创"**。
- C1′ 同靶点只有 size-2 组（13 组），功效不足 → 只作 QA。
- C4′ 组织仅 3 水平且组织×通路有 0 细胞格 → 只作 exploratory。
- III 的认证依赖 A4 的状态资源；A2 只做 constructive 与候选清单。
- replay 的真实归因无 ground truth → 只描述，不给正确率。
