# R198-A3 动态路线：Mix-seq 元数据资格（metadata-only）

2026-10-27 ｜ 执行：cellstate-lit（task-26） ｜ 范围：**只做元数据资格与设计，不训练、不跑时间预测、不读表达矩阵、不读响应做统计**。
问题：用户重审提出"哪些动态信息会改变具体药物决策？"。本文件只回答：**本地 Mix-seq 资产能否支撑这个问题、缺口在哪**；设计见 [`protocol_draft.md`](protocol_draft.md)，过程记录见 [`record.md`](record.md)。
前置（已读，不重复其结论）：`research/2026-10-27-cross-domain-directions/{report.md,evidence_notes.md,mixseq_metadata_check.json,metadata_replay.py}`（用户 17:44 重审：6h/24h 共同 285 干预×细胞键、4 处理+对照；剂量/批次/独立功能结局未认证）；`research/SYNTHESIS.md`（C160/C167/C172 边界）；`research/2026-10-27-innovation-round-r197/BRIEF.md:40`（动态路线另问）。

**本次实际读取**：`data/external/mixseq_scperturb/mcfarland_2020.h5ad` 的 **obs/var 元数据**（列名、设计列取值、计数、QC 标志、身份连接）、`research/eight_directions_20261026/evidence_audit/mixseq_design_census.csv`、`data/external/depmap_19q4/sample_info.csv`（列存在性与 ID 连接）、`data/external/prism_19q4/raw/*-treatment-info.csv` 与 `*-cell-line-info.csv`（药名/剂量/DepMap ID 列，**未打开 logfold-change 响应矩阵**），以及 CADENCE 论文 HTML（`tmp/cadence_2605.23470v1.*`）。
**未读取**：h5ad 的 `X`（表达矩阵，shape 仅取自元数据对象）、任何表达派生量；任何响应/存活数值；未训练任何模型。

脚本与产物：`a3_inspect.py` → `a3_meta.json`（本文件所有数字的机器可读来源；SHA 见 record.md）。

---

## 0. 结论（给 Lead）

1. **285 键复核通过**：h5ad obs 与旧 census 在 `(perturbation, cell_line)` × 精确 `time∈{6,24}` 定义下**完全一致 = 285**；per-drug 98/24/24/24/115（BRD3379/Bortezomib/Idasanutlin/Trametinib/control），common cell lines = 115；两源共同键集合逐元素相同。
2. **但"6h/24h 两快照"不是本地动态数据的全部**：h5ad 里还有 (a) **Trametinib 5 时间点（3/6/12/24/48 h）+ 时间匹配 DMSO 对照**的 hashed 子实验，per-cell 时间/处理可从 `hash_assignment` 恢复（17,553 个 single-tag 细胞；24 细胞系在全部 5 个时间点都有细胞，中位 55 细胞/条件）；(b) 9 个**只在 24h** 的药物臂（~94–98 细胞系/臂）；(c) 72/96h CRISPR 臂（与药物决策不直接相关）。
3. **资格判定：`design_data_partial`（部分可支撑）**。可支撑**群体层面**的两快照/时间过程**预测开发**；**不支撑**决策层检验，因为：**h5ad 无任何独立功能结局**（无 viability/apoptosis/IC50 列；obsm/layers/uns 为空）；`perturbation`/`dose` 字段在 hashed 臂存在**字段冲突**（DMSO 标签也被写成 perturbation=Trametinib、dose=0.1）；**无 batch/plate/run 列**；6h 与 24h 的 channel 可用性不同（6h 全缺失；63/285 键仅 24h 有 channel）；时间与批次/通道**不能从元数据证明匹配**；所有时间点是**破坏性快照**、无同细胞轨迹/谱系链接。
4. **本地外部功能结局候选**：PRISM 一级/二级 screen 的元数据里能找到 **Bortezomib/Trametinib/Idasanutlin**（24 个 focal 细胞系全在 PRISM 二级覆盖内），但 **BRD3379 不存在**；PRISM 的剂量/时间/assay 与 Mix-seq 不匹配（PRISM 单一终点，非 6/24h），只能作**外部、非时间匹配的**二级验证候选，不能当决策层主终点。另有 22 个前轮派生文件（20 npz + 2 json，`data/external/kinetic_horizon_20261010/`），**只列目录、不读内容、provenance 未审计**，不能当认证终点。
5. **对 CADENCE 类路线**：CADENCE 的可识别性依赖 DFA/COA/MRA + PR/FOA 等结构假设，**FOA 需要入组时间在区间内足够丰富**；本资产只有 2 个精确时间点（或单药 5 个固定时间点）、没有个体轨迹链接、没有 run/batch 记录 → **不能把 6h/24h（或 5 快照）当真实路径**；流匹配/插值只是估计器，不恢复路径（见 [`cadence_evidence.md`](cadence_evidence.md) 与 protocol §2）。
6. **处置**：动态路线的**决策层主实验当前不具备数据资格**；最多可做"群体时间预测开发 + 与静态/两快照对拍"的预注册开发研究（仍需先冻结噪声/可靠性口径），或按 [`protocol_draft.md`](protocol_draft.md) §6 的数据规格补数据后再启动。**不得声称动态世界模型/真实轨迹已被支持。**

---

## 1. 资产与文件结构

| 项 | 值 | 来源/状态 |
|---|---|---|
| h5ad 路径 | `data/external/mixseq_scperturb/mcfarland_2020.h5ad` | `a3_meta.json:files.h5ad` |
| 大小 / SHA256 | 1,459,410,830 B / `94a7240047b9ce6822dc2aa1e7a66c1fd8b00be842e5a95fc72cbeb6f2834d2c` | 本轮计算（`a3_inspect.py`） |
| 维度 | `n_obs=182,875` 细胞 × `n_vars=32,738` 基因 | 元数据对象 |
| `X` | CSC，shape [182,875, 32,738]；**本轮未读数值** | 仅取结构 |
| `obsm` / `layers` / `obsp` / `uns` | 全为空 | **可支撑"无嵌入/无额外层"** |
| `raw` | 不存在 | — |
| `obs` 设计列 | `time, perturbation, perturbation_type, cell_line, dose_value, dose_unit, channel, hash_tag, hash_assignment, DepMap_ID, chembl-ID, cancer, tissue_type, sex, cell_quality, nperts, ...` + QC 列（`ncounts/ngenes/tot_reads/percent.mito/doublet_*/singlet_*`） | 列存在性；QC 列**未做表达统计** |
| `var` 列 | `ensembl_id, ncounts, ncells` | 基因级元数据；表达值未读 |
| cell line 身份 | 209 个 `DepMap_ID`（与 `cell_line` 1:1，无一对多）；**209/209 可在 `depmap_19q4/sample_info.csv` 找到** | **可支撑身份连接** |
| 旧 census | `research/eight_directions_20261026/evidence_audit/mixseq_design_census.csv`（1,952 行；列 `time,perturbation,cell_line,channel,cells`；`cells` 合计 182,875 = n_obs） | 与 h5ad 元数据一致 |

**判定**：文件/结构 **可支撑**；但 `uns` 为空 → 无来源处理说明/无 provenance 记录（**未认证**）。

---

## 2. 时间点、处理与对照结构

### 2.1 `time` 列只有 4 个标签（其中 2 个是聚合标签）

| time 标签 | 细胞数 | perturbation_type 组成 | 解释 |
|---|---:|---|---|
| `24` | 101,610 | drug | 24h 精确标签（含 4 药 + 对照 + 9 个 24h-only 药臂） |
| `6` | 33,072 | drug | 6h 精确标签（仅 4 药 + 对照 = 285 键） |
| `72, 96` | 28,165 | CRISPR | 遗传扰动；**不是药物时间过程** |
| `3, 6, 12, 24, 48` | 20,028 | drug（全部 `perturbation=Trametinib`） | **聚合标签**：该臂各细胞只有一个真实时间；可从 `hash_assignment` 恢复（见 §4） |

**判定**：精确 6h/24h **可支撑**（仅限 4 处理 + 对照）；混合标签 **需清洗**（聚合标签不能逐细胞拆成 5 个时间，除非用 hash 赋值）；CRISPR 72/96h 与药物决策 **不相关**。

### 2.2 处理/对照（精确 6h/24h 的 5 个臂）

| perturbation | 类型 | 6h 键数 | 24h 键数 | 共同键数 | cell line 数 | dose_value（µM） |
|---|---|---:|---:|---:|---:|---|
| BRD3379 | drug | 98 | 98 | 98 | 98 | **0.0**（与"处理臂"矛盾） |
| Bortezomib | drug | 24 | 24 | 24 | 24 | 2.5 |
| Idasanutlin | drug | 24 | 24 | 24 | 24 | 2.5 |
| Trametinib | drug | 24 | 24 | 24 | 24 | 0.1 |
| control | 对照 | 115 | 115 | 115 | 115 | 0.0 |
| **合计** | | **285** | **1346（含 24h-only 臂）** | **285** | **115** | — |

- 24h 精确标签下另有 **9 个只出现于 24h 的药臂**：AZD5591(7,098 cells/94 lines)、Afatinib(3,807/95)、Dabrafenib(12,814/98)、Everolimus(3,825/94)、Gemcitabine(2,093/95)、JQ1(5,591/94)、Navitoclax(9,623/98)、Prexasertib(3,972/95)、Taselisib(3,098/95)。**单快照，不能做 6h vs 24h 动态比较**（可作 24h 静态外部验证/药物泛化候选）。
- **臂结构**：Bortezomib/Idasanutlin/Trametinib 的 24 个细胞系集合**完全相同**（"focal24"，与 hashed 臂的 24 行完全一致）；BRD3379 的 98 个细胞系 ⊆ control 的 115；`control = BRD3379(98) ∪ focal24(24)`（交集 7）。**可支撑**设计层"24 focal / 98 单药 / 115 对照"的结构描述；**需注意**有 7 个细胞系同时属于 BRD3379 与 focal24。
- `perturbation=control` 仅说明"对照"；**vehicle/DMSO 身份、浓度、是否时间匹配不能从元数据认证**（`dose_value=0.0` 只是字段值）。

**判定**：处理/对照结构 **可支撑**；BRD3379 的 0.0 剂量、control 的载体身份 **需清洗/未认证**。

---

## 3. 285 键复核（核心交付项）

### 3.1 方法与结果（与旧 census 双源一致）

- 定义（与旧轮一致）：实体键 = `(perturbation, cell_line)`，分别取 `time == "6"` 与 `time == "24"` 的 exact 标签，求交集。
- h5ad obs 结果：`6h` 285 键；`24h` 1346 键；**共同键 285**；common perturbations = 5；common cell lines = 115；per-drug `{BRD3379:98, Bortezomib:24, Idasanutlin:24, Trametinib:24, control:115}`。
- 旧 census CSV 独立复算：**完全相同**（同为 285、同 per-drug、同 115 细胞系）；两源共同键集合**逐元素相同**（`census_vs_h5ad_agreement.common_key_sets_identical = true`）。
- 键定义敏感性：在 `(pert, cell, channel)` 下，6h = 285（每键单 channel），24h = 1424（有键跨多个 channel）；在 `(pert, cell, dose_value)` 下两时间点均为 285/1346。**285 是"忽略 channel/dose"后的实体键数，不是独立培养数/独立样本数**。

### 3.2 每键的细胞数与 QC

| 指标 | 6h | 24h |
|---|---|---|
| 细胞数 min / median / max | 4 / 108 / 398 | 7 / 104 / 378 |
| QC-normal 细胞数 min / median / max | 0 / 96 / 389 | 0 / 88 / 345 |
| ≥10 normal cells 的键数 | **282 / 285**（BRD3379 97、Bortezomib 23、Idasanutlin 24、Trametinib 24、control 114） | 同左（同一批键） |
| ≥20 / ≥30 normal cells 的键数 | 279 / 264 | 同左 |

**判定**：群体 pseudobulk 的**键级细胞数可支撑**（282/285 键在两侧均 ≥10 normal 细胞）；但 3 个键 <10、且最小 0 normal → **需清洗**（设定最小细胞数门槛）。

### 3.3 剂量、channel、批次

| 项 | 观测 | 判定 |
|---|---|---|
| 剂量字段 | `dose_value`/`dose_unit` 存在；每药单值：BRD3379 0.0、Bortezomib 2.5、Idasanutlin 2.5、Trametinib 0.1、control 0.0 µM；**6h 与 24h 同键的剂量集合无冲突** | 字段**可支撑**"单剂量"描述；**无剂量序列**；BRD3379=0.0 与处理矛盾 → **需清洗/未认证** |
| channel | 6h 全部缺失；24h 63,754/101,610 缺失；common keys 中 222/285 两时间点均缺失，63/285 仅 24h 有（Trametinib 24 + control 39）；无任何键在两侧都有相同 channel 集合 | **不能作为匹配批次代理**；6h vs 24h 的 channel 可用性不同 → **时间与 plate/channel 混淆未排除**（未认证） |
| hash 字段 | 精确 6h/24h 细胞 `hash_tag`/`hash_assignment` 全为 `nan` | 6h/24h 比较**无 hash 批次信息** |
| 显式 batch/plate/run/donor 列 | **不存在** | **缺失** |
| cell line 身份 | 209 DepMap_ID 与 sample_info 全匹配；无一对多 | **可支撑** |
| 独立培养/生物学重复 | 无 donor/passage/replicate 列；census 的 "cells" 只是细胞计数 | **未认证/缺失** |

---

## 4. 新发现：hashed 臂实为 **Trametinib 5 时间点 + 时间匹配 DMSO 对照**（需清洗）

`time == "3, 6, 12, 24, 48"` 的 20,028 个细胞全部 `perturbation=Trametinib`、`perturbation_type=drug`；其 `hash_tag`/`hash_assignment` 携带**样本水平**的"处理_时间"标签。逐项统计（全部为元数据）：

| 分类（`hash_assignment`） | 细胞数 |
|---|---:|
| single tag（`Tram_3/6/12/24/48hr`、`DMSO_3/6/12/24/48hr`、`Untreated_48hr`） | **17,553** |
| combo（逗号连接的两个 tag，疑似 doublet/混合） | 2,339 |
| unresolved（`multiplet`/`unknown`/missing） | 136 |
| 合计 | 20,028 |

- **single-tag 覆盖**：Trametinib 3h/6h/12h/24h/48h = 1,137 / 1,347 / 1,168 / 2,080 / 1,876 细胞；DMSO 3h/6h/12h/24h/48h = 1,329 / 1,156 / 1,262 / 1,545 / 2,942；`Untreated_48hr` = 1,711。
- **24 个细胞系在全部 5 个时间点对 Tram 与 DMSO 均有细胞**（`lines_with_all_times = {Tram:24/24, DMSO:24/24}`）；这 24 行**恰好等于非 hashed 臂的 focal24**（`clean_lines_equal_focal24 = true`）。
- 条件数 = 24 × (5 Tram + 5 DMSO) + 24 × 1 (Untreated_48) = **264**；**中位 55 细胞/条件（min 11, max 250）**；仅保留 `cell_quality=="normal"` 时：13,713 细胞、中位 42 细胞/条件（min 8, max 212），24 行仍覆盖全部 5 个时间点。
- **字段冲突（必须清洗）**：① 该臂 `perturbation` 字段对所有细胞都写 `Trametinib`，但 hash 标签里约 **9,945 个是 DMSO/Untreated 对照** → `perturbation` 不能作为该臂的处理标签；② `dose_value` 对所有细胞（含 DMSO）都是 **0.1** → 剂量字段不可信；③ `hash_tag` 与 `hash_assignment` 在 **2,475** 个细胞上不一致。
- **不能认证**：hash 赋值不是本轮重新推导的（来自原数据处理）；combo/multiplet 细胞不可用；无 10x run/batch/plate 列；`Untreated_48hr` 与 `DMSO_48hr` 的差别未知；这些是**破坏性快照**，不是同一细胞的轨迹。

**判定**：这是一个 **需清洗后可用的单药密集时间过程**（1 药 × 5 时间点 × 24 细胞系 × 时间匹配 DMSO 对照），比"仅 6h/24h 两快照"强；但**未认证**（hash 赋值/批次/剂量/独立培养），且**仍无功能结局**。此前轮报告（`report.md:88`）只拆出精确 6/24 与混合标签、未做 hash 解析，本文件是**新增元数据发现**，不是对旧结论的否定。

---

## 5. 功能结局与决策层可行性

| 项 | 观测 | 判定 |
|---|---|---|
| h5ad 内独立功能结局（viability/apoptosis/GR/IC50/synergy） | obs/var 列名检索 **0 命中**；obsm/layers/uns 空；var 只有 `ensembl_id/ncounts/ncells` | **缺失** |
| h5ad 内单细胞表达（可作"预测目标"） | `X` 为 182,875 × 32,738 表达矩阵（本轮未读） | 可作**表达层开发目标**；不等于功能结局 |
| 本地外部功能结局候选：PRISM 一级 screen | 元数据中有 Bortezomib / Trametinib / Idasanutlin（各 1 行，单一剂量 **2.5 µM**）；**BRD3379 无记录** | 外部终点**部分可得**；剂量/时间与 Mix-seq 不匹配（Trametinib Mix-seq 0.1 vs PRISM 2.5） |
| PRISM 二级 screen（dose-response 元数据） | Bortezomib/Trametinib/Idasanutlin 各有 16 个剂量点；BRD3379 无 | 外部终点**部分可得**；仍是 PRISM 自己的 assay/终点，**不是 6/24h 时间匹配存活** |
| PRISM 细胞系覆盖 | Mix-seq 209 DepMap IDs 中 **207** 在 PRISM 一级/二级；focal24 全在；BRD3379 98 行中 97 在 PRISM 二级 | **身份连接可支撑** |
| 前轮派生缓存 | `data/external/kinetic_horizon_20261010/` 下 22 个文件（20 个 npz + 2 个 json；含 mixseq A/C/D control/treated、mixseq_state、prism_* 匹配缓存） | **只列目录、未打开、未审计**；不能当认证终点 |
| 独立培养/重复 | 无 replicate/donor/plate 列；重复无法从元数据估计 | **缺失** |

**结论**：**决策层（动态信息是否改变具体药物选择）无法在本资产上检验**；PRISM 只能作为**非时间匹配的外部二级验证候选**；主决策终点需要新测的、与 Mix-seq 同细胞×同药×同时间/同剂量的功能读数。

---

## 6. 逐项资格判定表（任务要求）

| 项目 | 状态 | 依据 |
|---|---|---|
| h5ad 文件结构/维度/obs-var 列 | **可支撑** | §1 |
| 209 DepMap_ID ↔ sample_info 身份连接 | **可支撑** | §1/§3.3 |
| 精确 6h/24h 共同 285 键（4 处理+对照，115 细胞系） | **可支撑（复核一致）** | §3.1 |
| census 与 h5ad 键集合一致性 | **可支撑（逐元素相同）** | §3.1 |
| 每键细胞数/QC-normal 细胞数 | **可支撑，需设门槛** | §3.2（282/285 ≥10 normal；3 键不足） |
| 单剂量/剂量单位字段 | **需清洗/未认证** | §3.3（BRD3379=0.0；hashed 臂 DMSO 也写 0.1） |
| channel 作为批次代理 | **不能支撑（混淆未排除）** | §3.3（6h 全缺失；63 键仅 24h 有） |
| 显式 batch/plate/run | **缺失** | §3.3 |
| hashed Trametinib 5 时间点 + 时间匹配 DMSO（24 系） | **需清洗（hash 赋值/字段冲突/批次未认证）** | §4 |
| 24h-only 9 个药物臂 | **可支撑为单快照静态层，不能作动态比较** | §2.2 |
| 72/96h CRISPR 臂 | **与药物决策不直接相关** | §2.1 |
| 表达矩阵（预测目标/特征） | **存在但本轮未读** | §5 |
| 独立功能结局（viability/apoptosis） | **缺失（h5ad 内）**；PRISM 仅外部、非时间匹配 | §5 |
| 独立培养/生物学重复 | **缺失/未认证** | §3.3 |
| 个体轨迹/谱系链接 | **缺失（破坏性快照）** | §4/§5 |
| CADENCE 类路径可识别性所需条件 | **不满足**（入组时间仅 2 或 5 个固定点；无 linkage；批次未认证） | protocol_draft §2 |
| 决策层主实验资格 | **不够格**（无功能结局 + 批次/剂量未认证 + 时间与通道混淆） | §5 |

---

## 7. 对动态路线的直接含义

- **能做的（开发层，不涉及决策）**：在 4 药+对照 × 115 系 × {6h,24h} 上做**群体层面的时间预测/排序开发**（例如用 6h 预测 24h，或反之），主对照是静态（无时间）与 drug/time 均值；在 hashed Trametinib 的 24 系 × 5 时间点 × DMSO 上做**单药时间过程**的开发预测；两者都必须报告"时间与批次/字段未认证"的限制。
- **不能做的（决策层）**：没有独立功能结局，无法回答"动态信息是否改变具体药物决策"；PRISM 不是时间匹配的终点，且缺少 BRD3379。
- **不能声称的**：动态世界模型成立、真实路径被恢复、时间点越多越好——6h/24h（或 5 点）是破坏性快照；按 CADENCE 的条件，缺个体链接/丰富入组时间/可验证批次时只能做群体边缘分布级别的预测，不能当轨迹。
- **已有边界的引用**：C160（线 D 停：检定力/设计失败，非"细胞状态无信息"）、C167（R192 `not_replicated`，不证明"不能复现"）、C172（Q 条件主效应 1.43% 且解释更正，条件级共享规律不构成前提）；R197 BRIEF 已把动态路线列为"另问"，本文件不改变这些结论。

---

## 8. 限制

1. **metadata-only**：未读表达矩阵，因此不能估计任何时间预测/功能效应；本文件不含效果、不含 MDE 的实测值（设计中的 MDE 只能预注册计算方式，见 protocol）。
2. hash 时间/处理标签来自原处理流程，**本轮未重建 demultiplexing**；combo/multiplet 不可用；`hash_tag` 与 `hash_assignment` 有 2,475 细胞不一致。
3. 无 batch/plate/run/donor/passage 列 → 时间与批次/通道混淆**只能在设计上承认，不能在数据上校正**。
4. PRISM 元数据只用于"是否有药/细胞系/剂量"的存在性检查；**未读任何 PRISM 响应矩阵**；PRISM 与 Mix-seq 的 assay/时间/剂量不匹配。
5. 未复核 CADENCE 之外的近期动态/可识别性文献（本任务不是文献综述）；CADENCE 引用为用户报告 P 级阅读 + 本轮 HTML 复核（见 `cadence_evidence.md`）。

---

## 9. 引用的一手来源

- Mix-seq / scPerturb 本地资产：`data/external/mixseq_scperturb/mcfarland_2020.h5ad`（hash 见上）。
- 旧轮元数据复算：`research/2026-10-27-cross-domain-directions/mixseq_metadata_check.json`、`metadata_replay.py`（285 键定义与来源 hash）。
- 本地 census：`research/eight_directions_20261026/evidence_audit/mixseq_design_census.csv`（SHA `0ef7b1c7…`）。
- 用户 17:44 重审：`research/2026-10-27-cross-domain-directions/report.md:88,151-163`；`evidence_notes.md:19-30`；`directions_v2.md:17`。
- CADENCE：arXiv:2605.23470v1，<https://arxiv.org/html/2605.23470v1>（本轮 HTML 复核，引用与 hash 见 `cadence_evidence.md`；旧 `evidence_notes.md:20` 为 P 级阅读）。
- CellFlow（插值 t ≠ 物理时间）：`research/2026-10-27-cross-domain-directions/evidence_notes.md:19` 引 <https://arxiv.org/html/2502.09775v1>（用户报告 P 级，本轮未重读）。
- SYNTHESIS 边界：`research/SYNTHESIS.md:11`（C160）、`:263`（C167）、`:25`（C172）。
- PRISM 源：`data/external/prism_19q4/raw/`（README 与官方 figshare 归档；仅元数据）。
