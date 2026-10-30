# R198-A4v2 规格：作为 A1 的 (iii) 状态模块（"表征遗漏关键状态"的测量与诊断）

2026-10-27 ｜ 执行：drugcomb-auditor（task-44，按 challenge_A4.md 修订）｜ 状态：**DRAFT / 不独立候选 / 未运行** ｜ 配套：[protocol_draft_v2.md](protocol_draft_v2.md)（DRAFT）、[REVISION_A4.md](REVISION_A4.md)（逐条修订账）、[record_v2.md](record_v2.md)、[usage_v2.json](usage_v2.json)。
**本文件不改 v1**（[spec.md](spec.md)/[protocol_draft.md](protocol_draft.md)/[prior_art.md](prior_art.md)/[record.md](record.md)/[usage.json](usage.json) 保持原样）；v2 是**收编为 A1 的 (iii) 支撑模块**后的修订版。
**纪律**：本轮不运行效果、不训练/拟合、不估 Q、不读响应做统计；不声称新颖性；阴性不写成"不存在"；**不把本模块当 A1 通过或三类判定器**。

## 0. 定位、所有权与输入（写死；对应挑战必改 1）

### 0.1 总定位

A4 **不再是独立候选**。它是 **A1（冲突信号与三类失败）的 (iii) 状态支撑模块**：

| 职责 | Owner | A4 做什么 / 不做什么 |
|---|---|---|
| (i) 数值调整（numeric adjustment） | **A1** | A4 不判 (i)；只在诊断中把"可重标定/数值解释"作为对照并报告 |
| (ii) 共享关系适用条件失效（relation conflict） | **A1** | A4 不判 (ii)；只消费 A1 的冲突证书/关系标识 |
| **(iii) 表征遗漏关键状态（missing state）** | **A1（总判定）；A4（状态证据模块）** | A4 提供：状态变量清单、`S_pre`/`S_measure` 分类、状态条件化诊断、Phase 1 状态测量设计、测量请求文本；**A1 负责**把它并入三类判定与更新器 |
| (iv) 设定错误（setup_error，A1 v2 第四解释） | **A1** | A4 不判 setup；但必须把 A1 的 setup/batch 诊断作为"不可归因状态"的排除项报告 |

**A4 永远不独立下发 `F1/F2/F3` 判定**。A4 的输出对象只有两类：`state_association` 诊断（描述/筛选）与 `measurement_request`（要测哪个状态/哪些条件），全部供 A1 使用。

### 0.2 启用门（修正 v1 的程序性死锁）

- **A1 冻结是 A4 Phase 0/1 的硬前提**：A1 当前为 **revise / 未冻结**（`challenge_A1.md` §0；A1 v2 的 §2(iii) 仍只是 `proxy_only`）。A4 状态记为 **`blocked_by_A1`**；A1 冻结后才允许启用。
- A4 的"Phase 0 → Phase 1"**不以 Phase 0 显著为条件**（见 §5.3/§6.2）；Phase 1 的进入条件是：**A1 已冻结 + A1 冲突证书可算 + Phase 0 描述性候选选择规则通过 + Phase 1 设计体检（操纵可行性/独立培养/功效模拟）通过**。
- 若 A1 在冻结时把 (iii) 继续标为 `proxy_only` 且不请求状态证据，则 A4 保持 `parked`，不执行。

### 0.3 输入二选一（写死：选 A1 冲突证书；不做 Q-flip 改名路径）

- **选择：输入 = A1 的冲突证书**（A1 v2 的证书字段：`{J, C_conf, X_flip, Δ_pred(U), setup 诊断}`；引用 `conflict_signal/spec_v2.md` §8 与 `protocol_draft_v2.md`；A1 冻结前不启用）。
- **删除 v1 的"Q 跨 screen 符号翻转"作为 A4 主对象**：v1 protocol 的主统计量（`flip = 1[sign(Q_O)≠sign(Q_V)]`）是 A1 的**原料**、不是 A1 证书；在 A4v2 中它**只能**作为 A1 证书内部的证据字段（由 A1 计算），A4 不另立一套 Q-flip 判定，也不改名重开（挑战必改 1 的"二选一"取"用 A1 证书"一侧）。
- **删除 SCC（State-Conditioned Conflict）独立机制陈述**：v1 spec §5 的"机制候选"不再作为 A4 的独立主张；保留其可操作内容为"A1 证书的状态条件化分解"（状态可解释性诊断 + 测量动作），机制/更新器问题归 A1/A5。若 Lead 要独立候选，必须改名（"Q 符号不稳定的状态关联诊断"）并另立协议，本 v2 不做。

## 1. v2 相对 v1 的关键修订（摘要）

1. **所有权收敛**（§0）：A4 = A1 的 (iii) 模块；A1 owns 三类总判定；A4 只出状态证据/测量请求；启用门 = A1 冻结。
2. **F1/F3 判据重写**（§2–§3）：Phase 0 只能做 `state-associated instability`（必要非充分），不判 F1/F3；删除单位级不可执行的 `M4=K+g`（g 不存在于单位级），改为 `K + barcode/plate + screen 元数据` 的可执行 F1/batch 对照；新增 cell one-hot/identity、plate/barcode、leverage/投影核基线；flip 阈值由噪声模型预注册（禁止按结果选阈值）；噪声地板用 barcode 数分层并披露选择偏差；"flip > 同 screen 技术噪声"只作描述、不作 F3 判据。
3. **可用性/功效数字改正**（§4）：Phase 0 实际分析集披露为 **matched 96 细胞**：表达 **84**、突变 **95**、`culture_type` **54**、`culture_medium` **55**、三者联合 **54**（不是 v1 的 111/125）；`S` 拆 `S_pre`/`S_measure`；A0 MDE 改 **0.112（C168 更正；0.240 是各折均值，旧"资源不可用"表述撤回）**；**1,312 归属 A2 q2.json 的 barcode 分半标定（约 1.43% 覆盖、barcode-rich、同 screen）**，不是 A0；δ_min 改为 operational（见 §5.4）；MDE 模拟写死维数上限（EPV）/seed/聚类。
4. **Phase 1 重写**（§6）：完整 well 账（combo + 单药参照 + 对照 + QC + day1 对照/密度优化，引用 A5 cost_model 锚点）；按 12 pair-cell 单元做功效说明，不足则扩 4–8 细胞系或降级为可行性/操纵检查；操纵对象与 Phase 0 的 `S` 明确桥接；补 vehicle/阳性对照/板边/盲法/独立培养认证；失败类别补 `inconclusive_design`/`leakage`/`indistinguishable_F1_F3`；删除未定义的"192/384 孔"。
5. **先例/去重/措辞**（§8–§10）：明确**本轮无新检索**（v1 prior_art 的"有限检索"降级为"复用既往登记"）；逐条标注与 A1（P6/P7 的 v1 编号与 v2 重编号）、A2 III、R197/C177、A5 的重叠/所有权；引用 C174/C175/C176/C177；Phase 2 直接复用 A5 等成本设计；保留"不得声称动态世界模型/机制/决策收益/新颖性"模板（A4 语境：不得声称"状态已证实/表征遗漏已判类"）。

## 2. 三类失败与 A4 的可判范围（重写；对应挑战 ①）

### 2.1 三类 + 第四解释（A1 v2 口径，A4 只借用定义）

- (i) **数值调整**：存在 θ' 使关系满足 + 反馈拟合可行 + nuisance 占优（可由重标定/更新吸收）。
- (ii) **关系适用条件失效**：在 `Cond_r` 内关系空间违约 `C_conf` 超阈值、跨 ≥n_min 独立上下文一致翻转（`X_flip`）、最小释放集非空且稳定，且排除多解释。
- (iii) **表征遗漏关键状态**：存在**未进入表征 φ** 的可测状态 z（`S_pre` 静态或 `S_measure` 测量时状态），使"同一 x 下的响应/决策"随 z 变化；**计入类别判定需可测 z + 留出增量**。
- (iv) **设定错误**：噪声/σ/区间/批次重估可解释（A1 v2 第四解释；A4 只作为排除项）。

### 2.2 Phase 0 结构性不可分（v1 的 FAIL 已修）

在**只有 O/V 两个 context、S 为 cell 级静态**时，F1（关系随 context 改变）与 F3（缺少未记录状态）产生**同一个跨 screen flip**；`S_pre` 能预测 flip 只说明"不稳定与细胞属性有关"，对 F1/F3 是同一预测。**因此 Phase 0 的上限 = `state-associated instability` 诊断（必要非充分）**，不得输出 `missing_state_supported`/F3 判定。
- **F1/F3 的真正分离**只能来自：**≥3 个独立测量 context**（A3 已 not_qualified 于大规模，窄子集需 ERRATA_A3 限定，A4 不依赖）**或 within-cell 状态操纵（Phase 1）**。A4 v2 明确：Phase 1 是 F3 证据的**唯一新测量入口**，且其结论仍交 A1 归类。

### 2.3 可执行对照（替换 v1 的 M4）

- `M4=g` 删除（`g∈{O,V}` 是"侧"，不是单位级协变量；对 flip 无分层定义）。
- 新 M4（A1/batch 对照，可执行）：`K + barcode/plate + screen 元数据`（barcode 3,106；每细胞中位 19；plate/barcode 作为**已知设计协变量**进入模型，可检验"flip 是否只是 plate/barcode/screen 的已知结构"）。
- 必须补的基线：**cell one-hot/identity**（One-Hot News 的直接推论；没有它 ΔAUC 不能归因状态）、**plate/barcode**、**leverage/投影核**（A1 的等价对照）、**容量匹配随机 S**、**S 置换**、**重标定**（F2 对照）。

## 3. 状态变量分类（S_pre / S_measure；写死）

| 类 | 定义 | 允许用途 | 本机变量（metadata 实测） |
|---|---|---|---|
| **`S_pre`** | 用药前可得的**细胞级静态**变量，不是同屏测量读数 | 可支持 (iii) 的"可测状态"候选（Phase 0 描述性/Phase 1 桥接） | DepMap `CCLE_expression`（matched 96 中 **84**）、`CCLE_mutations`（**95**）、`sample_info` 的 `culture_type`（**54**）/`culture_medium`（**55**）/`sample_collection_site`/`primary_or_metastasis`/`age`/`sex`/`lineage`（cells 级，覆盖见 §4） |
| **`S_measure`** | 与端点同 assay/同屏的**测量时对照读数**（barcode/板级、随板变化），或 Phase 1 的操纵后状态读数 | **不能**单独支持 F3（按定义它们是测量背景的读数；v1 自承"随 barcode 变化"）；只作 F1/F2/batch 控制或 Phase 1 的桥接**中介** | Jaaks `DAY1_NORM_MEAN/SD`、`GROWTH_RATE`、`DOUBLING_TIME`（289,759/296,707 非空；**每细胞中位 4 个不同 level**）、`BARCODE`（3,106）；Phase 1 的 day1 growth/viability |

**规则**：v1 把 `DAY1/GR/DT` 列为 `S_state` 支持 F3 → **自相矛盾，v2 改正**：它们只能进 `S_measure`，不得作为 F3 判据；F3 证据需要 `S_pre`（作为候选状态面板）**或** Phase 1 操纵的 `S_measure`（作为中介/桥接），且必须由 A1 归类。

## 4. 可用性与功效边界（改正数字；对应挑战必改 3）

### 4.1 matched 96 细胞的真实覆盖（本挑战实测，metadata-only）

| 变量 | 96 匹配细胞中可用 | 说明 |
|---|---:|---|
| 表达（DepMap CCLE） | **84** | v1 写"111/125"是全体 Jaaks 细胞，不是 Phase 0 分析集 |
| 突变（DepMap） | **95** | — |
| `culture_type` | **54** | — |
| `culture_medium` | **55** | — |
| 表达+突变+`culture_type` 联合 | **54** | Phase 0 M2 的**实际上限** |
| 联合 + medium | **54** | 同上 |

- 因此 Phase 0 的 M2 分析集是 **54（要求 S_pre 完整）或 84（表达子集）** 个细胞簇；**92,039 条 unit 不是独立 n**（独立单位是细胞，A1 n_eff≈189 是主 Q 的；Phase 0 的 M2 必须按 54/84 细胞重算 MDE，不得引用 189）。
- **EPV 规则（写死）**：对 54 细胞，模型特征数上限 **≤5**（EPV≈10 的宽松上限；推荐 3 PCs + 2 个二值突变/培养特征）；84 细胞上限 **≤8**；若选择 penalty/内层 CV，仍须报告 EPV 与 54/84 两版敏感性。20 PCs 不可用于 54/84 细胞。
- **A0 MDE 更正**：**0.112**（五折主端点；C168/SYNTHESIS:11）。0.240 是各折 MDE 均值，v1 引用的"资源不可用"表述已撤回；A4v2 统一用 0.112 并在设计中继续标"仍 >0.05，预期分析集更小 → 很可能 inconclusive_power"。
- **1,312 归属更正**：1,312 = **A2 `q2.json` 的 `n_calibration_quadruples`**（coverage 1.43%；barcode-rich、同 screen），不是 A0；只能作同 screen 技术噪声标定，不能当跨 screen null。

### 4.2 噪声模型与 flip 阈值（写死；替换 v1 的"结果上选阈值"）

- **同一条件对的方向规则**：沿用 A1/A0 冻结的 directed 条件对/权重定义（`a_r`、`Cond_r`）；A4 不另立定向。
- **flip 阈值**：由预注册的**噪声模型**给出——用 A2 的 barcode 分半标定（1,312）按 barcode 数分层估计 `σ_tech`、`P(flip|纯噪声)` 的上下界；阈值写成 `|Q| > z*σ_tech`（z 预注册，例如 2；并用 z=1/2/3 的敏感性报告）。**禁止**用"结果上观察到稳定的 |Q|"反选阈值。
- **噪声地板分层**：按 barcode 数（每细胞 19 中位，最多 109）分层报告 flip 率与 `P(flip|noise)`；披露 1.43% 覆盖/选择偏差（barcode-rich 细胞）；**"跨 screen flip > 同 screen 技术噪声"只作描述性不稳定检查，不作 F3 判据**（跨 screen 差异必然含批次/周期，A1 的 (ii) 也承认）。

## 5. Phase 0：状态关联诊断（描述/筛选；不是 F3 判定）

### 5.1 输入与输出

- 输入：A1 冻结后的冲突证书（`C_conf`/`X_flip`/`J_min`/`Δ_pred(U)` 等）；Jaaks matched 96 的 `S_pre` 面板（§4）；barcode/plate/screen 元数据。
- 输出：`state_association` 诊断（每个冲突证书/关系上的状态可解释性分数 + 不确定性 + 敏感性）、`S_pre` 覆盖/缺失报告、`measurement_request` 候选（测哪个状态/哪些细胞/条件）。

### 5.2 统计（可执行；先冻结）

- 模型（按 EPV 限维）：`M0` 常数/噪声；`M1 = K`（tissue/lineage + dose design + screen/plate/barcode 元数据 + cell one-hot 作为 identity 基线）；`M2 = K + S_pre`（≤5/≤8 维）；`M3 = K + 容量匹配随机 S`；`M4 = K + barcode/plate + screen`（batch/F1 对照）；`M5 = A1 证书基线`（A1 自带分数）。
- 主统计量：在**按细胞分组的 CV** 下，用状态关联预测 A1 冲突标签（或 A1 的连续冲突量）的 ΔAUC（M2−M1），同时报告 ΔAUC(M2−M0)、对 cell one-hot/plate/leverage 的增量、以及 54/84 两版敏感性。
- **δ_min operational 化**（对应挑战必改 3）：
  - **定义**：`δ_min` = 使 A1 的"状态测量请求"决策**净成本 ≤0** 的最小状态增量。测量成本用 A5 `cost_model.md` 的 anchored key 锚点（**34–68 wells/key**）或 1 张 state-readout 板（1,536 wells/cell）计；收益侧必须先由 A1/A5 冻结"错误关系修订"的 CU 成本——**在 A1/A5 未冻结前，Phase 0 不产出判定**。
  - **Phase 0 的可执行替代**（在决策效用未冻结时）：用 **reliability-adjusted 门**：`δ_min_AUC = max(0.05, 2×SE_null(ΔAUC))`，其中 `SE_null` 由预注册的按细胞 cluster bootstrap（≥2,000 次，seed 固定）在 null 下给出；敏感性网格 **{0.05, 0.10, 0.15}** 全部报告；**任一门不过 → `inconclusive_design`/`evaluation_cannot_distinguish`，不写成 F3 阴性/阳性**。
  - 明确：v1 的 `δ_min=0.10` 无 operational 依据 → **不作为 v2 的判据**；只保留为敏感性档。
- **MDE 模拟（写死；本轮只写方案不运行）**：模型/特征集/λ 网格（内层按细胞分组 CV）、维数上限（54→≤5、84→≤8）、AUC 比较口径（配对 cluster bootstrap）、seed（20261027）、bootstrap 次数 ≥2,000、零模型（置换状态标签/打乱 plate）、power@δ_min；任何未写死的实现选择视为 `design_invalid`。

### 5.3 判定上限与死锁修正

- Phase 0 的输出**不判 F3**：最多输出 `state_associated_instability = present/absent/inconclusive_design`（描述性）。
- **Phase 0 inconclusive ≠ F3 不存在 ≠ 表征无信息**；不得据此停止 A4（`inconclusive_design` 只说明本数据/本状态面板不能做描述性筛选）。
- **Phase 1 进入条件不依赖 Phase 0 显著**：`A1 冻结 && A1 冲突证书可算 && Phase 0 描述性候选选择规则（预注册：按 state_association 分层平衡选细胞/条件、S_pre 覆盖足够、Phase 1 可测状态读数可得）&& Phase 1 design check 通过`。

## 6. Phase 1：状态操纵的最小设计（F3 证据；对应挑战必改 4）

### 6.1 设计与桥接（修正 v1 的"操纵与 S 无桥接"）

- **要操纵的是什么**：不是"培养基/氧"（那是测量背景 `g`，按 A1 定义应归 (ii)/(iv) 而非 (iii)），而是**与 Phase 0 `S_pre` 可桥接的、测量时状态变量 `S_measure`**：**接种密度/接种后时间 → day1 生长率/活力/汇合度**（Jaaks 的 `DAY1`/`GR`/`DT` 正是这类同屏培养状态读数；Phase 0 用 `S_pre` 预测"哪些细胞不稳定"，Phase 1 用 `S_measure` 检验"状态是否真的驱动符号/幅度"）。
- **桥接规则（预注册）**：
  1. Phase 1 细胞按 Phase 0 的 `state_association` 分层（高/低不稳定）选取，**两组都纳入**；
  2. 每细胞做 **2 个状态水平**（低/高接种密度，或短/长接种后时间；同培养基、同板型、同批次框架）；
  3. 同批测 `S_measure` 读数（day1 活力/生长率、处理后 viability）与组合端点；
  4. 预测：Phase 0 判为高不稳定的细胞，其 `sign/幅度` 在状态操纵下变化更大；且把 `S_measure` 作为**显式状态**加入模型后，flip/误差减少，而只做重标定/只加 cell one-hot 不够；
  5. **培养基/氧只作次级、明确标注为 `g`**，不得用于 F3 主证据（若用，最多作 (ii)/(iv) 对照）。
- **对照（补齐 v1）**：vehicle（DMSO，每状态每板）、阳性对照（已知协同对/plate positive）、blank/edge wells、位置随机化、盲法读数、独立培养认证（不同日/不同 passage/不同培养瓶；**barcode 不相交 ≠ 独立培养**，R2 教训）、批次=2（不同日/培养批）、技术重复=2 孔。
- **端点**：与参考同尺度的功能端点（`SYNERGY_DELTA_EMAX` 类）；每 (细胞,药对) 的 **anchored 设计** = 14 combo wells（2 anchor 浓度 × 7 library 剂量）+ 5 anchor-alone + 4 library-alone + 8–16 controls/QC → **34–68 wells/key**（A5 `cost_model.md` 锚点）；day1 无药对照板 **1,536 wells/细胞**；新状态需密度优化 **1,344 wells/细胞**（A5 锚点）。

### 6.2 Well 账与功效（明确算术；替换 v1 的 192/384）

**先修正 v1 计数**：v1 的 `2×2×6×2×2 = 96`（不是 192）、`4×6×2×2×2 = 192`（不是 384）；且两版都**未含**单药参照/对照/QC，不能当完整板数。

**Pilot（2 细胞 × 6 药对 × 2 状态 × 2 批）**：组合单元 = 2×6=12 pair-cell；状态×批展开 = 2×6×2×2 = **48 个 anchored keys**。
- combo+refs+controls：48 × (34–68) = **1,632–3,264 wells**
- day1 无药对照：2 × 1,536 = **3,072 wells**
- 密度优化：2 × 1,344 = **2,688 wells**
- 合计 **7,392–9,024 wells ≈ 4.8–5.9 张 1,536 孔板**（若用 384 孔格式按 A5 另外计；未含失败/QC 1.5% 与重复；重复×2 时上述翻倍）。

**Main（4–8 细胞 × 6–8 药对 × 2 状态 × 2 批）**：pair-cell = 24–64；anchored keys = cells×pairs×2×2 = 96–256；wells：
| 组件 | 4×6 设计 | 6×8 设计 |
|---|---:|---:|
| anchored keys | 4×6×2×2=96 | 6×8×2×2=192 |
| combo+refs+controls（34–68/键） | 3,264–6,528 | 6,528–13,056 |
| day1 对照板（1,536/cell） | 6,144 | 9,216 |
| 密度优化（1,344/cell） | 5,376 | 8,064 |
| **合计 wells** | **14,784–18,048** | **23,808–30,336** |
| **≈ 1,536 孔板** | **9.6–11.8** | **15.5–19.8** |

- **功效（写死算法；本轮不运行）**：独立单位 = pair-cell（4×6=24 或 6×8=48），状态×符号用**配对 exact McNemar**；按预期 discordant 比例做预注册功效模拟（seed 20261027、≥2,000 次）。粗算：24 配对在 discordant 25%、OR≈4 时功效约 50–60%，**不足 80%**；48 配对在同假设下约 80%+。因此：
  - **24 pair-cell 设计只作 pilot/可行性/操纵检查**，不产出 F3 证据；
  - **主 F3 证据需 ≥36–48 pair-cell**（6–8 细胞 × 6–8 对）或更多重复/批；若预算只够 24，则 Phase 1 输出 `inconclusive_design`（可行性）并以 `measurement_request` 结束，不写 F3。
- **成本口径**：Phase 2 的等成本比较直接复用 A5 `cost_model.md`（total CU、三价格场景、filler/容差、`MDE_decision ≤ δ_min ≤ headroom`、`cost_sensitive`），A4 不另造预算口径。

### 6.3 Phase 1 失败类别（补齐）

`manipulation_failed`（操纵检查无差异/读数缺失）、`leakage`（状态读数/标签泄漏）、`indistinguishable_F1_F3`（只摆动 g、或 state-matched 对照同样变化）、`inconclusive_design`（pilot 功效/操纵检查不过）、`inconclusive_power`（主设计 MDE>δ_min）、`state_irrelevant`（状态相关但决策指标无改善）、`cost_sensitive`（A5 三价格场景排序不一致，若接 Phase 2）。

## 7. Phase 2（仅在 A1 请求且 A4 Phase 1 支持后）

- **不另立**：直接复用 A5 的 acquisition 等成本框架（菜单/成本模型/三价格场景/净收益与 headroom 预检）；A4 只提供"状态测量动作"作为菜单里的一类动作，比较对象/指标/停止规则按 A5 冻结版本，不越权改 A5。
- 门控：A4 Phase 1 支持 + A1 冻结 + A5 冻结（A5 当前也 revise，未冻结）→ 否则不做。

## 8. 接口/去重/边界（对应挑战必改 5）

| 相邻对象 | 关系 | 写死边界 |
|---|---|---|
| **A1（v1 spec）** | A1 v1 的 **P6 = (iii) 加入可测状态 z 后留出残差下降**、**P7 = 三类签名互不替代** | A4 v2 是 P6 的**状态证据供应商**；P7 的"互不替代"由 A1 判定，A4 不判 |
| **A1（v2 spec/protocol，当前 revise 未冻结）** | A1 v2 的 P6/P7 已重编号（P6=`setup_error` 注入、P7=注入体检/泄漏），(iii) 仅 `proxy_only` | A4 v2 以 **A1 v2 接口**为准（证书字段 `{J,C_conf,X_flip,Δ_pred(U),setup诊断}`）；A1 冻结后启用；**A4 不复活 A1 v1 的 (iii) 判定** |
| **A2 III**（logic_constraints v3） | A2 v3 §0/§1 已把 **III 认证 → A4**；A2 只出约束/违反/候选状态/固定探针 | A4 不评价 A2 约束；只用 A2 的排除域；A2 的 III 不重复 A4 的状态面板 |
| **A3/C175** | A3 `not_qualified` 只对冻结大规模门槛；窄子集需另议 | A4 不把 A3 的 41/4,179 当证据；不依赖 A3 资源；A3 只作"跨 screen 不可及"背景 |
| **R196/C176、R197/C177** | R196 `replicated_under_audit` 作废；R197 v1 协议作废（低秩结构未检验） | A4 不复活 R196/R197；不把 A4 的 M2 当 R197 低秩结论；需重开须 R196v2/R197v2 |
| **C174/C172** | 1.43% 仅是加性条件主效应份额 | A4 不以 1.43% 为前提，不写"规律总量" |
| **A5** | `acquisition_stage3/{spec,cost_model,protocol_draft}`；当前 revise 未冻结 | Phase 1 成本/Phase 2 等成本全部引用 A5；A5 冻结前不启动 Phase 2 |
| **R198 record / 其它模块** | A1/A2/A3/A4/A5 并行；A4 v2 不改 v1 与其它目录 | A4 仅写本目录新增文件；不重开旧路线/换名 |

## 9. 先例与检索状态（对应挑战必改 5）

- **v1 prior_art 结论保持不变**：One-Hot News（identity shortcut/LCO/LDO；细胞特征≈标识符）→ **已覆盖**；BATCHIE（cell line embedding×drug-dose、plate/QC、后验更新、PDBAL）→ **部分覆盖**；PDTSyn（共享+条件分解）→ **部分覆盖**；细胞状态特征近邻（DeepSynergy/Baptista/SynVerse/DIPx/Regulon/Tahoe LOCO/SynProtX/arXiv 2605.20885/iScience 2025/cell-line embedding/Separating main effects/FORGE/VCAT/DECANT/State/虚拟细胞 in-the-wild 基准）→ **已覆盖/部分覆盖**。
- **本轮（v2）明确：无新检索**。v1 prior_art §1.5 的"本任务有限检索"降级为"复用既往登记阅读"；`usage_v2.json` 记录 `new_literature_search: false`。**"未发现直接先例"只作既往检索结果，不是空白证明，也不作为差异/新颖性结论。**
- **缺口的补查建议（不声称完成）**：latent confounding/batch effect（ComBat/SVA 类）、identity/one-hot 对照、plate/barcode 文献；若要冻结，至少给出一次有界 query log 或明确"无新检索、复用旧登记"。

## 10. 措辞模板与失败语义（保留并加强）

- **不得写**：状态已证实/表征遗漏已判类/F1 与 F3 已区分/A4 通过 A1/机制/因果/决策收益/新颖性；`inconclusive_power` 不得写成 F3 阴性或阳性；A3 `not_qualified` 不得推广（C175）；1.43% 不得当规律总量（C174）；C176/C177 旧判定不得复活。
- **允许写**：本模块在给定状态面板/数据上给出 `state_association` 描述与 `measurement_request`；Phase 1 设计可检验"状态是否驱动决策相关符号变化"；结果无论正负均只作该资源/该状态的证据。
- **失败类别语义**：`inconclusive_design`（设计/操纵/泄漏/功效检查不过）与 `inconclusive_power`（MDE>δ_min）分开；`leakage` 立即停并修；`indistinguishable_F1_F3` 只表示"本设计未分离"，不表示 F3 不存在。

## 11. 本轮不做 / 剩余缺口

1. 不运行 Phase 0/1/2；不训练/不拟合/不估 Q/不读响应（本文件所有数字是元数据/设计算术）。
2. **A1 未冻结** → A4 状态 `blocked_by_A1`；A4 v2 的 Phase 0 不能启用。
3. **Phase 1 需真实新测量/预算/采购**；well 账给出，但成本系数未由报价替换（A5 同状态）。
4. **Phase 0 分析集只有 54（完整 S_pre）/84（表达子集）**；MDE 很可能仍 > δ_min → 预期 `inconclusive_power`，不得当 F3 阴性。
5. 先例本轮无新检索；需要时的补查点见 §9；不声称新颖性/不声称解决三类失败区分。
