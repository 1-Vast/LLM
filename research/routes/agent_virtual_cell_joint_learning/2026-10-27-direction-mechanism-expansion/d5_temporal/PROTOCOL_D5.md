# R200-D5 早期状态→晚期响应：时间预测边界（PROTOCOL_D5，DRAFT）

2026-10-27 ｜ 执行：cellstate-lit（task-88） ｜ 状态：**DRAFT（资格 + 严格时间切分设计；本轮不运行效果、不拟合预测）**。
上位：`research/2026-10-27-innovation-round-r200/BRIEF.md`（D5 为设计/资格任务；通过独立挑战后才可运行最小实验）；`research/2026-10-27-direction-mechanism-expansion/{report.md:35,50,57; latest_evidence.md:39}`（D5 入口、最小判别与停止）；本轮资格机器可读结果：`d5.json`（`d5.py` 生成，metadata-only）。
定位：**"另问" L1 时间预测开发资产**；不进入候选冻结、不进入 L2 决策层、不进入机制主线。**不声称新颖性/细胞状态机制/迁移/决策收益/真实轨迹。**
上游 A3v2 的 `L1 feasible / L2 blocked` **仅作背景**；本协议**不复用其未认证部分**（功能结局、批次/剂量、同批配对等条件），D5 资格由 `d5.py` 从 h5ad 元数据独立复算。

---

## 0. 一页结论

- **本地资源能把"6h 早期 RNA → 24h 晚期 RNA"做群体层预测开发**：285 个 `(drug, cell_line)` 键 × 115 细胞系，合法药物（含时间匹配 control、每键 ≥20 QC-normal 细胞）细胞系 **BRD3379 95 / Bortezomib 22 / Idasanutlin 24 / Trametinib 24**；Trametinib 5 时点（3/6/12/24/48h + 时间匹配 DMSO）为**探索**（严格匹配后各对比仅 15–19 线 <20）。
- **功能分支 `not_qualified`（`data_unavailable`）**：本地 Mix-seq 资产**无任何晚期功能终点**（viability/apoptosis/再生长/存活），也无**同一细胞**的早期–晚期配对（破坏性快照；obs index 全唯一）。**RNA 代理 ≠ 功能终点。**
- **时间轴严格性 `unverified`**：无 batch/plate/run 列；6h 的 channel 全缺失、24h 部分缺失且与 6h 无重叠；hashed 臂每个 (treatment,time) 仅一个样本标签（无重复样本）；暴露时长/起始同步无记录。**不得把 6h/24h 差异直接当绝对时间效应/同板同批配对。**
- **判定**：`molecular_temporal_route = qualified_with_conditions`；`functional_route = not_qualified`；`overall_D5 = qualified_with_conditions`（**仅限分子代理开发层**）。**不建议本轮运行效果**；建议提交独立挑战（见 §11）。

---

## 1. 问题与范围

**D5 问题**：一个早期表达快照在什么条件下足以预测晚期响应？何时确实需要第二个**早于目标**的快照？失效域在哪？
**本协议的可检验版本（仅分子代理）**：
- **V1（confirmatory-development）**：6h 状态 → 24h 晚期**分子**效应；4 药 + 时间匹配 control；每药 n=95/22/24/24 细胞系。
- **V2（exploratory only）**：Trametinib 5 时点 + DMSO；比较"单早期快照 vs 两早期快照"的信息增量（目标 24h/48h；输入严格早于目标）；各对比 n=15–19（<20）→ 无判定权。

**明确排除/不做**：
- 晚期功能（viability/凋亡/再生长）、同细胞轨迹/谱系、绝对时间过程、同板同批配对、机制/靶点、跨背景迁移、决策收益、新颖性。
- 旧 A3 的 L1/L2 结论仅背景；不重复其未认证部分；不重开 R196v2/R197v2。
- 不补造缺失中间点；不把 24h 表达回流作为输入；不把流匹配/插值当物理时间/真实路径。

---

## 2. 资源资格（metadata-only；详见 `d5.json`）

### 2.1 资产与结构

| 项 | 值 | 判定 |
|---|---|---|
| 资产 | `data/external/mixseq_scperturb/mcfarland_2020.h5ad`；1,459,410,830 B；SHA `94a72400…` | 存在 |
| 维度 | 182,875 细胞 × 32,738 基因；`X` 值**本轮未读**（只取形状） | 可支撑 |
| `obsm`/`layers`/`uns`/`raw` | 全空/无 | 无嵌入/无额外层 |
| obs 列 | 设计列（time/perturbation/perturbation_type/cell_line/dose_value/dose_unit/channel/hash_tag/hash_assignment/DepMap_ID/chembl-ID/…）+ QC 列 | **无功能/形态/曝光/批次/重复/同细胞链接列** |

### 2.2 早期时点 vs 晚期终点（D5 核心资格项）

| 项 | 是否存在 | 证据/数值 | 判定 |
|---|---|---|---|
| 早期 RNA（6h） | ✅ | 33,072 细胞；6h 精确标签（4 药+control） | 可支撑分子预测 |
| 早期形态/成像 | ❌ | 无 imaging/morphology 列或 `obsm` | 缺失（本地） |
| 晚期分子 RNA（24h） | ✅ | 101,610 细胞；24h 精确标签 | 可支撑（分子代理） |
| 晚期功能（24h/再生长/存活） | ❌ | obs/var 无 viability/apoptosis/IC50/regrowth/response 列；`obsm/layers/uns` 空 | **缺失 → 功能分支 not_qualified** |
| 同一细胞（早期与晚期同细胞） | ❌ | obs index 全 182,875 唯一 → 无 barcode 同时出现在 6h 与 24h；无 lineage/cell_id 列 | **破坏性快照，非同细胞** |
| 同一干预同键 | ✅（键级） | 285 键在 6h/24h 共享同一 perturbation 名称 | 键级匹配，非同细胞 |
| 时间匹配 control | ✅ | control 在 6h/24h 均有 115 键 | 可支撑（病毒/载体身份另见 2.3） |

**结论**：**"早期 RNA → 晚期 RNA"同键（非同细胞）可用；"早期 → 晚期功能"本地无配对，不能检验。**

### 2.3 暴露、剂量、批次、独立培养

| 项 | 观测 | 判定 |
|---|---|---|
| 暴露时长/起始同步 | **无** exposure/duration 列；`time` 只是收割/时间标签 | **缺失/未认证** |
| 剂量 | `dose_value`/`dose_unit` 存在；每个 6/24 药臂单一剂量：BRD3379 0.0、Bortezomib 2.5、Idasanutlin 2.5、Trametinib 0.1、control 0.0 µM（6h/24h 同键无剂量冲突）；**BRD3379=0.0 与处理臂矛盾**；hashed 臂 dose=0.1（DMSO 标签亦为 0.1，字段冲突） | **需清洗/未认证** |
| 批次/板/run/donor | **无** batch/plate/well/run/donor 列 | **缺失** |
| channel | 6h 全缺失（33,072/33,072）；24h 63,754/101,610 缺失；6h 与 24h 无共同 channel 标识 | **不能作同批代理** |
| hash | 精确 6h/24h 细胞 hash_tag/assignment 全为 `nan` | 6/24 比较无 hash 批次信息 |
| 独立培养/重复 | 无 replicate/donor/passage 列；hashed 臂每个 (treatment,time) **仅 1 个样本标签**；非 hashed 6/24 臂无样本标签 | **无重复样本 → 不能估测量重复性** |

### 2.4 时间轴严格性（同板/同批）

- 无 plate/batch/run 列；6h 的 channel 全缺失、24h 部分有且与 6h 不重叠 → **同板同批配对无法认证**。
- hashed 多时间臂：每个 (treatment,time) 一个 hash 标签，符合"用 hashing 在单次/少数 run 内 multiplex"的**设计意图**，但**无 run ID/plate ID 可核**；不能据此认证同批。
- 混合时间标签：48,193 细胞为逗号聚合标签（Trametinib 臂 20,028 + CRISPR 臂 28,165）；Trametinib 臂的 per-cell 时间/处理可由 hash_assignment 恢复（single-tag 17,553），CRISPR 臂不用于 D5。
- **verdict：same-plate/same-batch pairing NOT verified；time-axis strictness unverified。**

### 2.5 缺失与重复

- V1：285 键，115 细胞系；每键 QC-normal 细胞数最小值 0（个别键）、≥10 normal 的键 **282/285**；每药每键 ≥20 normal 的键数：BRD3379 97、Bortezomib 22、Idasanutlin 24、Trametinib 24、control 112；**药物键 + 时间匹配 control 均 ≥20 的细胞系 = 95/22/24/24**。
- V2（hashed）：20,028 细胞 → 17,553 single-tag（13,713 normal）；24 细胞系；每 (treatment,time) 仅 1 个样本标签；严格匹配（Tram 与 DMSO 在全部输入/目标时间点均 ≥20 normal）后各对比 n=15–19。
- 重复：无 replicate/donor/passage 列；无样本级重复 → **不能估 split-half 之外的测量重复性**。
- QC：normal 155,164 / 182,875（84.85%）；doublet 16,775、low_quality 7,213、empty_droplet 3,672、low_confidence 51。

### 2.6 功能终点资格（RNA 代理 ≠ 功能）

- h5ad：**无**任何功能终点列/层（见 2.2）。
- 本地候选资产（只列文件名/字节数，**未读内容**）：`prism_19q4`（viability screen 响应矩阵；assay/时间/剂量与 Mix-seq 不匹配）、`tahoe_phenotype_20261010`（不同扰动 atlas；相对存活/形态衍生端点；与 Mix-seq 不匹配）、`kinetic_horizon_20261010`（前轮派生缓存；provenance/splits 未审计；不是认证端点）、GDSC 组合/单药资源、BeatAML 患者资源等——**均不是同一 Mix-seq 细胞×干预×时间点的晚期功能读数**。
- **本地缺失 ≠ 原始公共研究没有其它输出**：本资格只针对本地 scPerturb h5ad。
- **判定：`functional_route = not_qualified`（`data_unavailable`）；RNA 只作分子代理。**

### 2.7 资格判定汇总

| 维度 | 判定 |
|---|---|
| 早期 RNA × 晚期 RNA（同键、非同细胞） | **qualified_with_conditions**（V1 4 药；V2 探索） |
| 早期 RNA × 晚期功能（同细胞/同键功能） | **not_qualified**（data_unavailable：无晚期功能；非同细胞） |
| 暴露/剂量/批次/独立培养认证 | **not_qualified/unverified**（time_axis_unverified） |
| 同板同批时间轴 | **unverified** |
| 重复/缺失 | 无样本重复；细胞级 QC 可用；键级覆盖需门槛（≥20 normal） |
| **整体 D5** | **qualified_with_conditions（仅分子代理开发层）** |

---

## 3. 可证伪假设（预注册）

| 假设 | 内容 | 最小判别 | 反例/失败 |
|---|---|---|---|
| **H-D5-1**（V1，confirmatory-development） | 6h 早期状态对 24h 晚期分子效应的跨细胞系预测优于静态（无时间）与均值基线 | `mean_d Δρ_d = mean_d [ρ(early6h)−ρ(static)]`；点≥δ_min 且 95% CI 下界>0；门 G0–G5 全过 | 早期≈静态 → `no_increment`；MDE/room/可靠性不过 → `evaluation_cannot_distinguish` |
| **H-D5-2**（V2，exploratory only） | 增加一个更早快照（6h+12h vs 6h）能提高对 24h/48h 晚期分子效应的预测 | 配对 Δρ = ρ(E2)−ρ(E1)；capacity 对照（同维随机/第二时点打乱）不得复现；n=15–19<20 → 只描述 | 无增量/仅容量增量 → 单早期快照足够；n<20 → 不下判定 |
| **H-D5-3**（描述性） | 单早期快照的"充分性"：early 模型与 oracle（真实晚期状态）的差距可测 | `gap = ρ_oracle − ρ_early`（每药；均值）；若 gap ≤ MDE80 → 在精度内足够；若 gap > MDE80 且 Δ≥δ_min → 有信息但不足 | 若 oracle 估不准/room<MDE → 报告不可分辨；不转成技术主张 |
| **H-D5-F**（功能） | 6h 状态预测 24h/48h 功能（存活/再生长） | **本地不可检验**：无匹配功能终点 | `data_unavailable`；不得用 RNA 代理替代功能 |

---

## 4. 数据、端点与单元

- **独立单位**：细胞系（不是 key、不是细胞、不是时间点）。V1 每药 n=95/22/24/24；V2 每对比 n=15–19。
- **目标 `y`（晚期分子）**：对 (drug d, line c, target t∈{24h,48h})，用 QC-normal 单细胞表达聚合为 pseudobulk；logFC = log2((pseudo+1)/(time-matched control+1))；再投影到 **train-only 冻结基因集**（按训练线平均 |logFC| 取 top-K=200），标量 = 200 基因 logFC 均值；向量版为副端点。
  - 对照：6h/24h 用 `perturbation=control`；V2 用同时间点 DMSO hash 标签。
- **早期特征**：V1 = 6h 的 logFC（相对 6h control），同一 200 基因面板；V2 = 严格更早时间点的 logFC（相对同时间点 DMSO）拼接。
- **静态特征**：DepMap/CCLE basal expression（与 h5ad 基因 symbol 交集）；训练折内标准化/PCA/ridge。
- **禁止**：目标时间 t 或其派生量进入输入/特征选择/标准化/调参；V1 不设"两快照拼接"臂。

---

## 5. 比较器（同信息、同调参预算）

| 代号 | 模型/基线 | 说明 |
|---|---|---|
| B0 | mean | 每药/时间训练线均值（组内排序 ρ=0 by construction） |
| B1 | static | 只给未处理/CCLE 特征（无时间） |
| B2 | cell identity | 细胞系 one-hot（留出细胞系时退化为均值；参考用） |
| B3 | linear ridge | 早期状态 → 晚期效应（主线性基线） |
| B4 | tree/GBM | 充分调参的树模型（R200 BRIEF 的强基线要求；调参预算预注册） |
| B5 | GP | RBF/类别核 GP（同输入） |
| B6 | simple time model | 仅 V2：按基因对"更早时间点 → 目标"做线性时间外推（exploratory） |
| B7 | single early snapshot | 严格早于目标的单个时点 |
| B8 | two early snapshots | 严格早于目标的两个时点拼接（仅 V2） |
| Oracle | late state | 真实目标时间状态（上界/room 用，不是候选） |
| Functional | — | **本地不可得**（见 §2.6） |

所有臂共享：目标/输入数据、细胞系过滤、调参预算、种子；禁止动态臂额外信息或额外预算。

---

## 6. 切分、泄漏与零模型

### 6.1 切分（写死）

- **V1**：外层 = 按细胞系分组 5 折 leave-cell-line-out（合格细胞系按名称排序，`fold = index % 5`；同细胞系所有键同折）；内层 = 训练折内按细胞系分组 5 折（λ/PCA-k/基因集选择只在训练折拟合）。
- **V2**：目标时间固定（24h/48h 各一组），输入严格更早；外层 = 按细胞系分组 5 折；内层同上；3h 无更早输入 → 不作目标。
- 全部折清单/SHA 见 `d5.json:split_design`（manifest SHA `c258f5b0…`；种子 `20261027`）。

### 6.2 泄漏与时间规则（G5 一票否决）

1. 目标时间/未来时间**不得**进入任何输入、特征、标准化、基因选择、调参。
2. V1 **不得**出现"两快照拼接"臂（目标 24h 本身会被误用为输入）；两快照仅 V2 且只用严格更早时间。
3. 折必须按细胞系分组，禁止随机行/键切分；禁止测试细胞系统计进入预处理。
4. 同批/同板信息缺失：**不得**声称"同板同批"或绝对时间效应；只能作群体预测开发。
5. 代码级断言 + 独立复审重放（G5）。

### 6.3 零模型（设计；尚未运行）

| 代号 | 零模型 | 预期 |
|---|---|---|
| N0 | 均值基线 | 组内排序 ρ=0 |
| N1 | cell-shuffle（早期特征按细胞系打乱） | ρ≈0 |
| N2 | drug-shuffle（仅 V1；早期特征按药物打乱） | 失去药物特异性 |
| N3 | time-shuffle（仅 V2；更早时间标签在允许的早时点间置换） | 检验时间特异性 |
| N4 | capacity control（V2：给 E1 加同维随机特征/把第二时点换成打乱特征） | Δρ 不应复现；否则是容量不是时间信息 |
| N5 | future-leak sentinel（把早期特征替换为目标时点特征） | 应显著高于早期模型；若不高说明管道/指标失效（阳性对照，不是主结果） |
| N6 | static-capacity（同维随机基因块） | 静态基线容量对照 |

---

## 7. 指标

- **主指标（V1）**：`Δρ_d = ρ(early6h_d, y24_d) − ρ(static_d, y24_d)`（留出细胞系上跨线 Spearman，每药；主统计量 = 4 药等权平均；不对药物总体推断）。
- **主指标（V2，exploratory）**：配对 `Δρ = ρ(E2) − ρ(E1)`（同一批合格线；E2/E1 = 两个/一个严格更早时点）；capacity control 比较。
- **副指标**：MAE/RMSE（标准化效应）、基因级 Spearman、top-k 恢复、校准斜率；**决策选择描述性指标**（top-quartile 命中/列表排序）仅描述，**不称决策收益**。
- **充分性**：`gap = ρ_oracle − ρ_early`（每药；均值）；报告 gap 与 MDE 的关系。
- **V2 单药**：只报描述，不作跨药推断。

---

## 8. 预注册判定门（冻结；先测后比）

- **δ_min = 0.10**（Δ Spearman 绝对差；运营定义：n=15–95 时约对应 top-5 名单 1–2 个位置的稳定改变；小于此不改变开发层动作；不依赖未读表达值；不得事后改）。
- **G0 资格**：V1 每药合格线 ≥20（实际 95/22/24/24 → pass）；V2 每对比 ≥20（实际 15–19 → exploratory_only）。
- **G1 split-half 可靠性**：目标条件细胞分半 → 两套 pseudobulk → 跨线相关 → Spearman–Brown `rho_sb`；门 `rho_sb ≥ δ_min + MDE80`。
- **G2 room**：`room = ρ_oracle − ρ_static ≥ max(δ_min, MDE80)`。
- **G3 MDE80**：配对 Δ 的细胞系 cluster bootstrap（1,000 次，种子 20261027）；门 `MDE80 ≤ δ_min`。
  **预运行解析上界（冻结）**：`MDE80_upper = 2.802·sqrt(2/(n−1))`：
  - V1 n=95/22/24/24 → **0.409 / 0.865 / 0.826 / 0.826**；达到 δ_min=0.10 所需跨模型误差相关 **0.940 / 0.987 / 0.985 / 0.985**。
  - V2 n=15–19 → **0.93–1.06**；所需 r_err **0.989–0.991**。
  → **除非两模型误差高度相关，V1 的 Bortezomib/Trametinib/Idasanutlin（n=22–24）与 V2 很可能在 G3 失败并判 `evaluation_cannot_distinguish`**；这是预注册门的预期用途，不是"动态信息不存在"。
- **G4 主效应（V1）**：mean Δ ≥ δ_min 且 95% CI 下界 > 0。
- **G5 泄漏审计**：§6.2 全过；否则 `design_invalid`。

**判定语义**：G1–G3 任一失败 → `evaluation_cannot_distinguish`（不写阴性）；G0 → `data_unavailable`；G5 → `design_invalid`；G1–G3 过、G4 不过 → `no_increment`（停动态必要性主张）；全过 → `development_increment_present`（**仅表达层开发结论**，不升级）。V2 任何情况只写 `exploratory_only`。

---

## 9. 失败类别与停止条件

| 类别 | 触发 | 动作 |
|---|---|---|
| `data_unavailable` | 功能终点缺失/不匹配；资格 G0 不过 | 停相应分支；不写"不存在" |
| `design_invalid` | G5 泄漏/时间顺序/折错误 | 停并修协议；不得解释旧输出 |
| `evaluation_cannot_distinguish` | G1/G2/G3 任一不过（含预运行上界已 >δ_min） | 判 inconclusive；不写阴性；不升级 |
| `no_increment` | G1–G3 过、G4 不过（早期≈静态） | 停"需要早期动态信息"主张；保留描述 |
| `exploratory_only` | V2 n<20 | 只报描述；无判定/不跨药推断 |
| `time_axis_unverified` | 无 batch/plate/exposure/同细胞记录 | 禁止绝对时间过程/同板同批/同细胞轨迹主张 |
| `functional_route_not_qualified` | 无匹配晚期功能读数 | 功能/决策主张停止；RNA 代理仅作分子层 |
| `identifiability_unsupported` | 任何真实轨迹/个体路径主张 | 禁止；本协议不产出 |

**停止规则**：任一判定门失败即停；不换端点/阈值/切分；不补造中间时点；不把 L1 结果升级 L2/候选；阴性不写不存在。

---

## 10. 若升级功能/绝对时间所必需的数据规格

1. **同细胞/同键的晚期功能**：与 Mix-seq 同细胞系、同药物、同剂量、同时间点（6/24/48h）的独立功能读数：viability（CellTiter-Glo 类）+ 凋亡/死亡（caspase/Annexin V、PI）或再生长；**时间匹配 vehicle**；≥3 复孔 × ≥2 独立培养/批次；报告孔间 CV 与批次效应。
2. **暴露与时间轴**：暴露起始同步、暴露时长、洗脱方案；plate/run/batch/孔位；同板同批配对。
3. **重复**：独立培养/批次的最低数量（由 δ_min/MDE 反推）；技术重复不能充生物 n。
4. **轨迹（若主张）**：同一细胞/谱系链接（lineage barcoding/活细胞成像）或可辩护的结构假设 + 更丰富入组时间；否则只能做群体边缘预测。
5. **剂量×时间/序贯**：剂量序列、洗脱/再挑战，才可检验延迟/可逆性（D5 不涵盖）。
6. **决策层**：明确动作、效用/成本、δ_min 与 MDE；独立功能终点；否则不进入决策收益。

---

## 11. 与旧 A3、边界与预注册

- **旧 A3 dynamic route**：`L1 feasible / L2 blocked` **仅背景**；本协议资格独立复算；不把 A3 的未认证部分（功能、批次、剂量、同批）当输入；A3 的 `V1 95/22/24/24` 与本轮一致属独立复算而非引用。
- **C 边界**：
  - C176（R196 `replicated_under_audit` 作废、inconclusive）、C177（R197 v1 协议作废、结果不得解释）、C179（R197v2 描述量未认证）、C181（R199 A1 资格失败=data_unavailable）、C186（O'Neil non-blind，仅开发性描述）——**均不提供时间可预测性的证据或反证；禁止引用旧判定；R196v2/R197v2 未完成前不重开**。
  - R195/ERRATA_A3：其 `not_qualified` 只针对冻结的大规模跨 screen 设计，不关闭较窄问题；本轮不重跑/不改旧门。
- **预注册清单**：δ_min、门顺序、比较器、切分、种子、指标、零模型、失败类别/停止条件均在运行前冻结；**通过独立挑战后才可运行**；运行需另立任务。
- **SHA/确定性**：`d5.py`（SHA `1422cb54…`）两次运行 `d5.json` 逐字节一致（SHA `82330743…`）；折清单 SHA `c258f5b0…`；本轮未读表达/响应、未拟合、未联网。
- **建议**：提交独立挑战（**建议：是**）；挑战通过前不运行；功能分支需新测量。

---

## 12. 不做 / 不得声称（保留模板）

1. 本轮**不训练、不拟合预测、不跑效果、不读表达/响应**。
2. **不得声称**：动态世界模型成立、真实轨迹恢复、早期快照"证明"机制、跨背景迁移、决策收益、新颖性。
3. **不得**把 6h/24h 差异直接当时间效应（同板同批未认证）；**不得**把 RNA 代理当功能终点；**不得**把流匹配/插值当物理时间。
4. **不得**把"未发现"写成"不存在"；阴性写 `evaluation_cannot_distinguish`/`no_increment`，不写"动态信息不存在"。
5. **不得**在挑战前运行或改阈值/端点/切分；不重开 R196v2/R197v2；不改其它目录/INDEX/git。
