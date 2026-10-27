# R198-A4 独立挑战（challenge_A4.md）——"表征遗漏关键状态"scout

2026-10-27 · 挑战者：endpoint-auditor（未参与 A4 设计；task-39）· 对象：`research/2026-10-27-innovation-scouting/missing_state/{spec.md, prior_art.md, protocol_draft.md, record.md, usage.json}`（A4 = task-27）。
方式：**只读审查 + 纯算术/元数据复核**（`tmp/challenge_a4_checks.py` → `tmp/challenge_a4_checks.json`；不读任何响应值、不训练、不拟合、不估 Q、不改 A4 产物）。
完整性：A4 四个交付物与 `usage.json` 登记 SHA 一致（spec `440275A7…`、prior_art `A22EC11C…`、protocol `FC4CD0B3…`、record `7CD92652…`；inventory `227124B4…`），**无事后改动**（§9 复核）。

## 0. 总判决

**作为独立候选：stop（当前形态不得进入候选冻结）。作为 A1 的"状态模块"：revise（≤5 必改，修完重审后可作模块冻结）——但只能作诊断/测量模块，不得独立下发 F1/F2/F3 判定。**

一句话：**A4 把"遗漏状态"写成了可证伪的三类失败框架（值得保留），但它的 Phase 0 判据在现有数据上不能把 F1 与 F3 分开、可用的联合状态集只有 54 个细胞（不是 111/125）、Phase 1 的 192 孔计数与功效都算不过来；而协议又把"Phase 0 显著"设为 Phase 1 的必要条件——预期 `inconclusive_power` 会变成程序性死锁。**

**最致命 3 条**

1. **F1 vs F3 在 Phase 0 结构性不可分**：`flip = 1[sign(Q_O)≠sign(Q_V)]` 本身是"跨唯一两组（O/V）的差异"，而 F1 对照 `M4 = K+g` 里的 `g` 在单位级不存在（每个单位同时含 O 与 V）；"按 g 分层/组内重拟合"对 flip 无定义（§2 引文）。F1（关系随背景变化）与 F3（缺状态）都会产生跨 screen flip；用**cell 级静态** S（表达/突变/培养注释）预测 flip 只能检验"状态关联的不稳定性"，**必要非充分**，不能判 F3。要分离必须有 **≥3 个独立测量 context** 或 **within-cell 状态操纵**（Phase 1），A4 把后者放在 Phase 0 通过之后——而 Phase 0 预期不过。
2. **可用性与功效被高估**：Jaaks 匹配 96 细胞中，表达仅 **84**、突变 95、`culture_type` **54**、`culture_medium` 55，**表达+突变+culture_type 联合只有 54 个细胞**（A4 只报"111/125"，未按 Phase 0 实际分析集披露）；`DAY1/GR/DT` 每细胞中位 **4 个不同值**（随 barcode/板变化；A4 自己在 spec:90 承认"随 barcode 变化"），是**同 screen 对照读数**、不是 cell 级 pre-treatment 状态——按 A4 自己的 F3 定义（s 不是 g 的函数）它们不能支持 F3，只能作 F1/F2/batch 控制。另：**A0 MDE=0.240 已被更正为五折主端点 0.112**（C168/SYNTHESIS:11，"资源不可用"表述撤回），A4 仍把 0.240 当边界（spec:84/128、protocol:19、record §3.4）；**1,312 是 A2 `q2.json` 的 barcode 分半标定数，不是 A0**（a0.json 无 1312）。Phase 0 若按现状执行，M2 的 MDE 只会更差，而 δ_min=0.10 无 operational 依据（C177 教训）。
3. **Phase 1 设计与算账都不成立**：`2×2×6×2×2 = 96` 不是 192（192 只有把"每条件对=2 孔"写死才成立，A4 未写）；扩到 `4×6×2×2×2 = 192` 不是 384（同）；两版**都不含单药参照/对照**——而 A4 用 ΔEMAX 端点（必须单药参照，见 A5 成本模型 anchored key 34–68 wells），真实板数/孔数被低估；2 细胞×6 条件对 = **12 个 pair-cell 单元**，`state×sign` 交互没有功效预计算（"pilot 再算"是循环）；操纵的"密度/培养基/氧"与 Phase 0 的 S（表达/突变/培养注释）**无桥接**，而且培养基/氧本质是测量背景 `g`——有把 F3 测成 F1 的风险。

**是否值得进入候选/模块冻结**：**不值得作为独立候选**（F1/F3 不可分 + 数据不够 + Phase 1 算账不成立）；**值得作为 A1 的 (iii) 状态模块**：A1 负责 (i)/(ii) 与三类总判定，A4 提供"状态变量清单 + 状态条件化诊断 + Phase 1 状态测量设计"，在 A1 冻结后启用。若 Lead 要独立候选，则必须改命题/改名（"Q 符号不稳定的状态关联诊断"），不得沿用"冲突/三类失败"的判定口径。

## 1. 六项判决摘要

| # | 审查项 | 判定 | 一句话依据 |
|---|---|---|---|
| ① | F1/F2/F3 可区分性（M0–M4、flip、ΔAUC、置换、分组重拟合/重标定） | **FAIL** | M4/F1 对照不可执行（g 无单位级取值；flip 跨唯一两组）；flip 噪声地板是同 screen 技术重复（1.43% 覆盖）≠ 跨 screen null；缺 cell one-hot/plate 基线；`inconclusive_design` 分类缺失且预期 `inconclusive_power` 会让 Phase 1 永不启动 |
| ② | 可用变量与功效（flip 诊断、噪声地板、DepMap 覆盖、M1/M2、A0/A1/A3 边界） | **WEAK（含 2 个 FAIL 子项）** | 匹配 96 细胞：表达 84、culture_type 54、联合 54（A4 未披露）；DAY1/GR/DT 是 barcode 级对照读数（A4 自承"随 barcode 变化"）不能当 cell 状态；A0 0.240 已被 C168 更正为 0.112；1,312 系 A2 非 A0；A1 0.2042/A3 41/4,179 继承正确 |
| ③ | 先例与差异（One-Hot News、BATCHIE/PDTSyn、未发现先例的检索边界） | **WEAK** | One-Hot News/ BATCHIE/PDTSyn 覆盖判定成立、不声称新颖性（PASS）；但**本轮无新检索回执**（usage: browsing=false），"未发现直接先例"仅来自既往登记阅读；缺"identity/one-hot 对照"与 latent-confounding/batch 文献补查 |
| ④ | 最小实验（Phase 0 可执行性、Phase 1 192 孔、对照、Phase 2 门控、失败类别） | **FAIL** | 96 vs 192（未写每对 2 孔）；扩 192 vs 384；均缺单药参照/对照；12 个 pair-cell 单元无功效；状态操纵与 S 无桥接；Phase 1 以 Phase 0 显著为条件 → 预期死锁；δ_min=0.10 无 operational 依据 |
| ⑤ | 接口/去重（A1/A2/A3、诊断模块定位、是否换名重开、措辞） | **WEAK** | 与 A1 P6/P7、A2 的 III 是**同一套三类失败测试的重复操作化**；protocol 用 Q flip（A1 原料）而 spec 说 SCC 是"状态条件化冲突信号"（A1 证书）——对象不一致；A1 挑战判 revise 未冻结，A4 无启用门；A3/ERRATA 边界基本正确；A5 未对齐；缺 C174/C176/C177 引用 |
| ⑥ | 总判决 | **独立候选 stop / 模块 revise（≤5 必改）** | 见 §0/§7；模块修订完成并重审前不冻结 |

## 2. ① F1/F2/F3 是否真可区分：**FAIL**

### 2.1 PASS 的部分（保留）

- 三类失败有了 operational 定义（spec §1，生成模型式），并明确 F3 必须涉及**新状态变量/新测量**与决策相关变化，不许"换模型/换损失"（spec:25）——方向正确。
- 强制性措辞写死（spec:73）："F3 成立只表示在该设定/该状态变量集上存在可复现、决策相关、不被已知协变量解释的状态结构"——**这段措辞合格**，建议保留。
- 嵌套模型 M0–M4 + 容量匹配随机 S（M3）+ S 置换 + 重标定/分组重拟合，作为"对照清单"是完整的思路；F2 的重标定对照、F1 的分组对照方向正确。

### 2.2 FAIL 的部分（决定判决）

**(a) M4/F1 对照在单位级不可执行。** spec:42 写 "M4：K + g（F1 对照；g 是已测背景）"，protocol:43 又把 `g ∈ {Original, Validation}` 写死。但 flip 的定义是 `1[sign(Q_O)≠sign(Q_V)]`（spec:34），**每个单位同时含 O 与 V 两侧**——`g` 是"侧"而不是单位的协变量；不存在"某单位的 g 取值"可用于 M4 的行级拟合。因此 "flip 由 g 解释"、"组内重拟合/按 g 分层后消失"（spec:42）对 flip **没有操作定义**：按 g 分层后每层里没有任何 flip 事件（flip 是跨层定义的）。这不是实现问题，是定义矛盾。要可执行，F1 对照必须换成：**已知协变量 K + plate/barcode + screen 元数据**（可执行的 batch/背景代理），或引入**第 3 个独立 context** 让 flip/一致性可在多组上定义。

**(b) F1 与 F3 在 Phase 0 都产生"跨 screen flip"，不可分。** F1 = "关系换了适用条件"（背景内可重复的偏移/符号翻转，是 g 的函数）；F3 = "s 未进 φ 且不是 g 的函数（或 g 只是粗代理）"。在只有 O/V 两组、且 S 是 **cell 级静态**（表达/突变/培养注释）的设定下：两组的差异既可能来自关系随 context 改变（F1），也可能来自两测之间状态的未记录变化（F3）。S 能预测 flip 只说明"不稳定与细胞属性有关"，**对 F1/F3 是同一预测**（F1 下状态变量是 context 的代理；F3 下状态变量是缺失变量本身）——A4 的 phenotype table（spec:64–70）把 "M2 有增量" 单独记 F3，**在只有 2 组时不可识别**。
- 因此 Phase 0 的上限是：**"state-associated instability diagnostic（必要非充分）"**，不能写 `missing_state_supported`。F3 的判定必须移到 Phase 1（within-cell 状态操纵 + 至少 3–4 个细胞系/批/重复）或引入第 3 个独立 context（A3 已 not_qualified 于大规模，但窄子集可另议，需 ERRATA_A3 限定）。

**(c) 噪声地板不是 flip 的 null。** spec:35/109 用 1,312 个"重复齐全回路"估 `P(flip|纯噪声)`；但这些是 **A2 `q2.json` 的 barcode 分半标定四元组**（`n_calibration_quadruples=1312`，占 92,039 观测的 1.43%，集中在 barcode-rich 细胞，且**同 screen/同批**），只给技术噪声，不给跨 screen/跨批 null——A4 自己写了"只给技术噪声，不给跨批"（spec:35）。可是判定条件 (a) 仍是 "flip 率显著高于噪声地板"（spec:41、protocol §4.1）——**跨 screen flip 高于同 screen 技术噪声是必然的（批次/周期/板效应），不能作为 F3 证据**。必须换 null：barcode 数分层估计 + 报告选择偏差；或明确"该条只作描述性不稳定检查，不是 F3 判据"。

**(d) 缺最关键的两个对照：cell identity 与 plate/barcode。** One-Hot News 已证"细胞特征≈标识符"（A4 prior_art §1.1，判断正确）——那么 M2 的 ΔAUC 首要竞争解释就是 **cell identity/one-hot**；A4 的 M3 是"容量匹配随机 S"，**没有 cell one-hot**。此外跨 screen flip 的最自然混杂是 **plate/barcode（3,106 barcodes，每细胞中位 19）**——A4 把 barcode 列为"部分可立即检验"（spec:88）却没有进 M1/M4。没有这两个基线，`ΔAUC(M2−M1)` 不能归因 F3。

**(e) flip 阈值与标签。** "仅用两侧 |Q|>预注册阈值/非零的单元"（spec:46）在结果上做选择（flip 只在 |Q| 大时稳定），阈值必须从噪声模型预注册（如 |Q|>2σ 的解析/模拟依据），且报告全单元敏感性；否则 flip 率随阈值漂移，`ΔAUC` 不可比。

**(f) 退出分类缺口 && 预期 inconclusive 造成死锁。** spec:72 用 `inconclusive_design`，但失败类别清单（spec:150）没有它（也没有 `leakage`）；protocol §5 又写"预期 MDE 与'很可能 inconclusive'的先验"（protocol:71），而升级条件（spec:157、protocol §7）要求 "Phase 0 出现 `missing_state_supported` 且 MDE≤δ_min → Phase 1"。**如果 Phase 0 预期 inconclusive_power，Phase 1 永远不启动**——这不是设计稳健，是程序性死锁。必须把 Phase 1 的进入条件改为"Phase 0 的描述性 flip 候选（预注册选择规则）+ 设计体检通过"，而不是"Phase 0 显著"。

## 3. ② 可用变量与功效：**WEAK（含 2 个 FAIL 子项）**

### 3.1 独立复核（metadata-only，`tmp/challenge_a4_checks.py`）

| 量 | A4 报告 | 本次复核（匹配 96 细胞） | 含义 |
|---|---|---|---|
| Jaaks 匹配细胞 | 96 | **96**（A0 `matched_conditions.csv`） | 一致 |
| 表达（DepMap CCLE） | 111/125 | 125 中 111 ✓；**96 匹配中 84** | M1/M2 的有效细胞簇 84，不是 111 |
| 突变 | 124/125 | 125 中 124 ✓；**96 匹配中 95** | 好，但不足以补表达 |
| culture_type | 66/125 | 125 中 66 ✓；**96 匹配中 54** | S 的静态注释覆盖 ~56% |
| culture_medium | 67/125 | 125 中 67 ✓；**96 匹配中 55** | 同上 |
| 表达+突变+culture_type 联合 | 未报告 | **54 个细胞** | Phase 0 的 M2 分析集上限 |
| `DAY1/GR/DT` 粒度 | 97.7% 行；"随 barcode 变化（每细胞 growth 中位 4 个不同值）"（spec:90） | 289,759/296,707 非空；unique levels 588；125 细胞；**每细胞中位 4 个不同值** | 是 barcode/板级对照读数，**不是 cell 状态** |
| Phase 1 计数 | "2×2×6×2×2 = 192 孔"；扩展 "4×6×2×2×2 = 384" | 2×2×6×2×2 = **96**（192 需"每条件对 2 孔"且未写）；4×6×2×2×2 = **192**（384 同） | 计数未定义；且均不含单药参照/对照 |
| A0 MDE | 0.240 | SYNTHESIS C168：0.240 是各折均值，**五折主端点 MDE=0.112**（仍>0.05；"资源不可用"表述撤回） | A4 继承过时数字 |
| 1,312 个重复齐全回路 | "A0 已记录"（spec:35/109） | a0.json 无 1312；**q2.json `n_calibration_quadruples=1312`**（A2） | 归属错误；且同 screen、1.43% 覆盖 |
| 92,039 controlled_anchor | A0 | a0.json `quadruples/strata_R4/controlled_anchor=92039` ✓ | 正确 |

### 3.2 判决拆解

- **FAIL（覆盖/粒度）**：Phase 0 的实际分析集是 **54–84 个细胞簇**（取决于是否要求 S 完整），不是 111/125；M1 的"表达 PC 20 维"在 54–84 个细胞上严重过拟合（EPV 不允许），A4 未给维数上限/EPV 规则。M2 若要求 S 完整，则 54 细胞 ×（20 PCs + 突变 + culture + 缺失指示）→ 不可估。**必须**：按细胞簇数写死维度上限（如 ≤3–5 PCs 或 penalized + 内部 CV）、报告 EPV、并给出 54/84 两个版本的敏感性。
- **FAIL（S 的类别错误）**：`DAY1/GR/DT` 是**同 screen、同板、与端点同 assay 的对照读数**，且随 barcode 变化（每细胞中位 4 个值）——按 A4 自己的 F3 定义（s 不是 g 的函数），它们**不能**进入 S_state 支持 F3；它们应归 `S_measure`（F1/F2/batch 控制）。A4 在 spec:90 已知"随 barcode 变化"却在 protocol:34 把它们列为 `S_state`，**自相矛盾**。必须拆成 `S_pre`（表达/突变/培养注释）与 `S_measure`（DAY1/GR/DT/barcode），并规定只有 `S_pre` 可支持 F3 判定。
- **WEAK（边界数字）**：A0 0.240→0.112（C168）；1,312→A2 且披露 1.43%/barcode-rich；A1 0.2042/δ_min 0.0893、A3 41/4,179 继承**正确**（这部分 PASS）。预期 inconclusive_power 的表述出现在 protocol:71，但必须**操作化**（见 ①(f) 与 §5）。
- **WEAK（flip 诊断是否够）**：96 细胞/92,039 单元足以算 flip 率，但**独立单元是细胞（84/54）**；把 92,039 当 n 会高估精度。A4 在 spec:128/record §3.4 提 n_eff≈189（A1），但 Phase 0 的 M2 用 84/54 细胞，必须重新算 MDE（不是引用 A1 的 189）。
- **PASS（discipline）**：A4 明确"阴性只能写 inconclusive、不写 F3 不存在/表征无信息"（spec:128、protocol §7）——**方向正确**，但需与"inconclusive_power 预期"一起写成可执行规则（见 ①(f)）。

## 4. ③ 先例与差异：**WEAK**

- **PASS**：One-Hot News 的覆盖判定正确（identity shortcut/LCO/LDO；"细胞特征≈标识符"）；BATCHIE（cell line embedding、plate/QC、后验更新、PDBAL）与 PDTSyn（共享+条件分解）判"部分覆盖"**成立**；"本任务对象=诊断路由+测量动作"的定位诚实；明确"不声称新颖性"、"未发现≠不存在"、列出检索缺口（prior_art §1.5：未查 GS/Scopus/WoS、无引文回溯、术语漏检、One-Hot 补充表/BATCHIE 附录未逐页核）——**这些都是好实践**。
- **WEAK（无本轮检索回执）**：A4 `usage.json` 写 `browsing_or_network_downloads: false`，record 无检索 query/pass 记录；prior_art §1.5 却说"本任务有限检索"。二者矛盾。**"未发现直接先例"必须要么附 query log/零命中回执（像 A1/R189 那样），要么改写为"本轮未做新检索，仅复用既往登记阅读"**——后者可以，但不能同时声称"有限检索"。
- **WEAK（缺关键对照/文献）**：
  1. **cell one-hot/identity 基线**缺失（One-Hot News 的直接推论；没有它 ΔAUC 不能归因状态）；
  2. **plate/barcode/batch** 作为已知协变量的处理（A4 只在"批次/板"表里列了可用性，未进模型/对照）；
  3. **latent confounding / batch effect / ComBat/SVA** 一类文献未补查（A4 只在 prior_art §1.5 列了"无混杂敏感性/E-value"作为相邻压力，没有逐条核）；
  4. 与 **A1 的 P6/P7**、**A2 的 III**、**R197/C177** 的重叠未逐条标注（见 ⑤）。
- **结论**：先例"部分覆盖 + 诊断路由未发现直接先例"的判断**可以保留**，但**不能**作为差异/新颖性结论；A4 的"剩余差异"只有作为 A1 模块的工程价值，不是独立候选理由。

## 5. ④ 最小实验：**FAIL**

### 5.1 Phase 0（零新增测量诊断）

- **PASS**：分期、预注册 δ_min/α/按细胞分组 CV/细胞聚类 CI 的**方向**正确；"MDE>δ_min 停、不进入 Phase 1/2"的意图正确；预期 inconclusive_power 被预先写出（protocol:71）是诚实的。
- **FAIL**：
  1. **δ_min=0.10（ΔAUC）无 operational 依据**：没有说明为什么 0.10 AUC 等于"决策有用差异"；按 C177 的教训（δ_min 必须由决策/效用或 reliability-adjusted 定义，且不得用旧 CI 反推），必须给出 operational 定义 + 敏感性（如 0.05/0.10/0.15）或改用决策相关指标。
  2. **MDE 模拟未写死**：模型（M0–M4 的具体形式/维数/λ 网格）、特征集上限、seed、聚类 bootstrap、AUC 比较口径（配对/独立）均未定；"MDE 用置换/分层 bootstrap 预计算"不能替代一个可复现的预注册模拟方案。
  3. **Phase 1 的门是 Phase 0 显著**（spec:157、protocol §7）——在 54/84 细胞、S 覆盖稀疏、A0/A1 边界已示 MDE 很大的情况下，这等于**设计上预期不通过**；必须改为：Phase 0 只做**描述性筛选**（预注册选择规则：平衡 flip/non-flip、覆盖度、可测状态读数可得），Phase 1 不依赖 Phase 0 显著性；同时明确 "Phase 0 inconclusive ≠ F3 不存在 ≠ 表征无信息"。
  4. **"可立即检验"的边界**：spec §3.3 的"可立即检验"指"不新增测量"，但其中 flip 率/M1/M2 需要读 Jaaks 响应拟合值（Q）→ 属响应统计；A4 `usage.json` 的 `response_value_statistics: false` 只对"本轮"成立，协议必须写明 Phase 0 执行时会读响应（描述性），避免"零响应"误解。
  5. **flip 的方向/阈值**：Q 的符号依赖条件对定向（A0/A1 冻结方向规则），A4 未写死定向规则；|Q| 阈值在结果上选择（见 ①(e)）。

### 5.2 Phase 1（最小新增测量）

- **FAIL（算账）**：192/384 的计数依赖未写明的"每条件对 2 孔"；且**不含单药参照与对照**。A4 用 ΔEMAX 端点（组合协同需单药参照）；按 [A5 成本模型](../acquisition_stage3/cost_model.md) 的 anchored key（14 combo wells + 12–38 refs + 8–16 controls = 34–68 wells/key），Phase 1 的真实孔数至少是 combo 孔的 2–4 倍；Phase 1 的成本/可行性没有被算过。必须在协议里给"combo + 单药参照 + 对照 + QC"的完整账，并与 A5 的 equal-cost 设计对齐（Phase 2 尤其应复用 A5 的同预算比较框架）。
- **FAIL（功效）**：2 细胞 × 6 条件对 = **12 个 pair-cell 单元**（每 state/批/重复）；`state×sign` 交互、操纵检查（2 状态×2 批）、以及"平衡 flip/non-flip"筛选后的样本量都远不足以给出可判定的 CI；"MDE 按 pilot 噪声与 2 比例功效预先算（不给具体效应则先 pilot）"是循环（Phase 1 本身就是 pilot）。必须：先给解析/模拟功效（基于 12 单元与预期效应），若不足则扩到 4–6 细胞系/更多条件对，或明确 Phase 1 只作**可行性/操纵检查**、不作 F3 判定。
- **FAIL（状态桥接）**：Phase 1 操纵"接种密度/培养基/氧"与 Phase 0 的 S（DepMap 表达/突变/培养注释）**不是同一对象**；且培养基/氧是测量背景 `g`（按 A4 自己的 F1 定义，测量条件属于 g）→ 若操纵这些，可能测的是 F1（context change）而非 F3（missing state）。必须：(i) 明确操纵的是"未表征状态"还是"测量背景"；(ii) 同批测 state readouts（表达/活力/生长）并预注册"操纵→状态变量"的桥接与操纵检查；(iii) 用 state-matched 对照排除"只是换了培养条件"。
- **PASS（对照清单方向）**：技术重复、state-matched、K-only、重标定、按批分组重拟合、随机状态、S 置换、A1/A2 约束排除——覆盖面好；需补 vehicle/阳性对照、板边位置/边缘效应、盲法/随机化、独立培养认证（R2 教训：板/barcode 分离 ≠ 独立培养）。
- **失败类别**：spec:150 的类别（numeric_only/relation_invariant/missing_state_supported/state_irrelevant/inconclusive_power/manipulation_failed/confounded）方向好，但缺 `inconclusive_design`、`leakage`、`indistinguishable_F1_F3`；必须补，且规定"每类触发条件 + 报告内容"，避免退出条件吞掉阴性。

### 5.3 Phase 2

- **PASS**：门控在 Phase 1 之后、固定更新器、同预算/同成本、未测净收益、预注册 MDE/δ_min——方向正确。
- **WEAK**：未与 A5（acquisition 等成本设计，本目录 `../acquisition_stage3/`）对齐；Phase 2 的比较器/指标/停止规则应直接引用 A5 的 spec/protocol_draft（同菜单、同更新器、同 total CU、menu headroom vs MDE 预检），避免另起一套。

## 6. ⑤ 接口/去重/措辞：**WEAK**

- **与 A1**：A1 的 spec 已有 **(i)/(ii)/(iii) 的 operational 签名**与 **P6（state z 改进残差）、P7（三类签名互不替代）**；A4 的 Sig-A/M2−M1 本质是 P6/P7 的另一种操作化。**两套协议都声称能判三类失败 = 两个 owner**，必须明确：
  - **A1 owns** (i)/(ii) 与三类总判定（含 F1/F2 的更新器/证书）；
  - **A4 owns** (iii) 的状态变量清单、状态条件化分解、Phase 1 状态测量设计；A4 不独立下发 F1/F2/F3 verdict，只输出"状态可解释性/测量动作"；
  - A4 的 Phase 0 只作为 A1 P7 的**输入模块**（在 A1 冻结 (i)/(ii) 之后启用）；A1 当前挑战判 **revise、未冻结**（challenge_A1 §0），A4 必须写"启用门"（A1 冻结后才可执行 A4 Phase 0/1）——现在 protocol 没有这个门。
- **对象不一致（spec vs protocol）**：spec §5 SCC 说输入 = "A1 的冲突信号 + A2 的约束可行域"，输出 = 对每个冲突标 F1/F2/F3 + 测量动作；但 protocol §3 的主统计量是 **Q 的跨 screen 符号翻转**（A1 的原料，不是 A1 的冲突证书 `C_conf`/`X_flip`）。二者不是同一对象：要么 A4 用 A1 证书（则依赖 A1 冻结），要么用 Q flip（则改名、不能叫"冲突信号"，且不能继承 SCC 的机制陈述）。**必须二选一写死**。
- **与 A2**：A2 的 III（状态分层相关）与 A4 重叠；A2 挑战判 revise（其 object 是逻辑约束），A4 应引用 A2 的现状并声明"A4 不评价 A2 约束，只用其排除域"，避免互相借结论。
- **与 A3**：A4 正确地把 A3 限定为描述性对照（spec:20、prior_art §?）；应引用 **C175/ERRATA_A3**："not_qualified 只对冻结大规模门槛，不能关闭较窄问题"，并且不得把 A3 的 41/4,179 当 A4 的证据。
- **与 R197/C177**：A4 未引用 R197 撤销（C177）。A4 的"状态条件化残差"与 R197 的"特征 vs Q 低秩"相邻；必须写清：A4 不检验 Q 低秩结构（那是 R197v2/AMENDMENT-002），不把 A4 的 M2 当作 R197 的复活；并引用 C174（1.43% 仅是加性份额）与 C172 的边界。
- **与 A5**：Phase 1/2 的成本/等成本设计与 A5 重叠（A5 已给菜单/成本模型/等成本核查/停止规则）；A4 应引用 `../acquisition_stage3/{spec.md,cost_model.md,protocol_draft.md}`，不另造预算口径。
- **是否重开旧路线/换名**：A4 的对象（诊断路由+测量动作）与 I003/固定探针不同，**不是换名重开**；但 "state-conditioned conflict" 若同时出现在 A1 与 A4 两个协议里，就是**同一主张的两个名字**——必须按上面的 ownership table 收敛。
- **措辞（PASS 部分）**：spec:73 的强制措辞合格；"F3 只到该设定/状态变量集"足够；"不声称新颖性/未发现≠不存在"合格。**需补**：不得写"可检测=已检测"、不得把 `inconclusive_power` 写成 F3 阴性/阳性、不得把 A4 当 A1 通过、不得把 1.43% 当规律总量（C174）、不得把 A3 not_qualified 推广（C175）。

## 7. ⑥ 总判决与 5 条必改（≤5）

**总判决：作为独立候选 stop；作为 A1 的 (iii) 状态模块 revise（≤5 必改，修完重审后可模块冻结，不得独立下发 F1/F2/F3）。**

必改项（每条都必须落到文件，不是口头）：

1. **对象与所有权**：写 ownership table——A1 拥有 (i)/(ii) 与三类总判定；A4 只做 (iii) 的状态变量/状态条件化/测量动作；A4 启用门 = A1 冻结（引用 challenge_A1 的 revise 状态）。二选一写死输入：A1 证书（则依赖 A1）或 Q flip（则改名"Q 符号不稳定的状态关联诊断"，删 SCC 机制陈述），不得两边都占。
2. **F1/F3 判据与对照重写**：Phase 0 明确上限 = "state-associated instability（必要非充分）"，不判 F3；删除/改写 M4（g 无单位级取值）为 **K + barcode/plate + screen 元数据** 的可执行 F1 对照；补 **cell one-hot/identity**、plate/barcode、leverage/投影核基线；flip 阈值由噪声模型预注册（非 |Q| 事后选择）；噪声地板用 barcode 数分层 + 报告 1.43% 覆盖/选择偏差，且"flip > 同 screen 技术噪声"只作描述、不作 F3 判据；`inconclusive_design` 加入失败类别；明确 "Phase 0 inconclusive ≠ F3 不存在/表征无信息"，Phase 1 不以 Phase 0 显著为条件。
3. **可用性/功效/边界数字改正**：协议写入 matched-96 的 per-variable 覆盖（表达 84、突变 95、culture_type 54、medium 55、联合 54）；S 拆 `S_pre`（表达/突变/培养注释）与 `S_measure`（DAY1/GR/DT/barcode，同 screen 对照读数，只作 F1/F2/batch 控制）；A0 MDE 改 **0.112（C168 更正；0.240 各折均值、"资源不可用"已撤回）**；1,312 改引 A2 q2.json（1.43% 覆盖、barcode-rich、同 screen）；δ_min=0.10 必须 operational 化（决策/效用或 reliability-adjusted + 敏感性），MDE 模拟写死模型/维数上限（按 54/84 细胞 EPV）、seed、聚类 bootstrap。
4. **Phase 1 重写（算账+功效+桥接+对照）**：给完整 well 账（combo + 单药参照 + 对照 + QC，引用 A5 cost_model 的 anchored key 34–68 wells）；按 12 个 pair-cell 单元做解析/模拟功效，若不足则扩 4–6 细胞系/更多对/批或降级为"可行性/操纵检查"；写明操纵的是"未表征状态"还是"测量背景 g"（培养基/氧属 g 的风险），同批 state readouts + 预注册桥接与操纵检查；补 vehicle/positive/edge-position/blinding/独立培养认证；失败类别补 `inconclusive_design`、`leakage`、`indistinguishable_F1_F3`。
5. **先例/去重/措辞**：补本轮有界检索的 query log/pass 回执**或**明确"本轮无新检索"并降级"未发现"；逐条标注与 A1 P6/P7、A2 III、R197/C177、A5 的重叠与所有权；引用 C174/C176/C177/C175 边界；Phase 2 直接复用 A5 的等成本设计；删除/改写未定义的"192 孔"表述；保留 spec:73 措辞并补"不得把 inconclusive 写成 F3 阴性/阳性、不得把 A4 当 A1 通过"。

## 8. 保留项（A4 值得留下的东西）

- 三类失败的 operational 定义（spec §1）与 F3 的强制措辞（spec:73）。
- 状态变量可用性清单（spec §3；需按 §7-3 修正粒度/覆盖/A0 数字）。
- 先例覆盖框架与"不声称新颖性/未发现≠不存在"的诚实（prior_art §0/§1.5；需补检索回执）。
- Phase 0「零新增测量先做诊断」的思路——但需降级为描述性/筛选，不能作为 F3 判定或 Phase 1 的门。
- Phase 1 的对照清单方向（需补功效/算账/桥接/独立培养认证）。
- 失败类别与"阴性不写成不存在"的纪律（需补类别与操作化）。
- 明确"不是 A1 的通过、不重估 A1 主 Q、不启动 B/C/acquisition"的边界（正确保留）。

## 9. 复核证据与本轮边界

- **完整性**：A4 交付物 SHA 与 usage.json 一致（spec `440275A72A52C2536C18AD29A356A56FB0B5A21AEDA7FB6380DBE8C8780D4C1A`；prior_art `A22EC11CFF4CBBB2D2ECF86018B2DACE69D3193D1A07377D06EB916AC47F8CB3`；protocol `FC4CD0B33903DD788A5BA998F68407B79B5AF270C80099F051C59A2CE32D8A10`；record `7CD9265242ADC2AB0DB008D5EDBDDAF80CC5B9DD8CC1265A225DD8EE8FDECD2A`；inventory `227124B4998DF4DD38F54EC44CCE03ECFB39E7A51FEDCF94FA4D3C7806EDE6F6`），**无事后改动**。
- **本轮复核脚本**：`tmp/challenge_a4_checks.py`（只读元数据/身份/计数；不读响应值）→ `tmp/challenge_a4_checks.json`。要点：匹配 96 细胞；表达 84、突变 95、culture_type 54、medium 55、联合 54；DAY1/GR/DT 每细胞中位 4 个不同 level；Phase 1 计数 96/192 与 192/384 的两种读法。
- **引用的背景数字**：SYNTHESIS C168（0.240→0.112）；a0.json `controlled_anchor=92039`；q2.json `n_calibration_quadruples=1312`（A2）；challenge_A1 §0（A1 revise）；A2 challenge（revise，III 重叠）；C174/C175/C176/C177 登记（1.43% 仅加性份额；A3 边界；R196 撤回；R197 v1 作废）。
- **边界**：本轮**不运行效果/不训练/不拟合/不估 Q/不读响应值/不改 A4 产物/不改其它目录/INDEX/SYNTHESIS/git**；只新增本文件与 `tmp/`。所有数字是设计/元数据核查，不是生物学效果证据；挑战结论不构成对 A4 作者身份或既往记录的改写。
- 建议 Lead 的下一步：若保留 A1 线，则把 A4 收为 A1 的 (iii) 模块并按 §7 五条修改后由**另一名未参与**的挑战者复审；若 Lead 要独立候选，则按 §0 改命题/改名（不得沿用"冲突"判定口径），并将 Phase 0 降为描述、Phase 1 作唯一 F3 判定入口且先补功效/算账。
