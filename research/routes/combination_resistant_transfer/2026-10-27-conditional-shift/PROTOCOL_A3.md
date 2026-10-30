# PROTOCOL_A3 —— R195-A3 条件级跨 screen 复验：资源资格审计协议（v1 **FROZEN**，2026-10-27，在任何 A3 匹配计数之前）

> 依据：R195 BRIEF（唯一任务 A3）、R194 BRIEF/record（C172：σ²_cond=1.43%，条件级结构"可估但可忽略"）、R193-A1 `inconclusive`（C171：96 共享细胞、n_eff≈189、MDE80_obs 0.2042 > δ_min_obs 0.0893）、`PROTOCOL_A0/Q/Q2` 与 `ERRATA_A0.md`/`challenge_A0.md`（Q 定义、controlled_anchor 分层、匹配口径）、R190-E1 DrugComb 资格审计（v1.4/v1.5 结构与本地文件）。
> **本文件在运行 `a3.py` 之前冻结；冻结后不改，偏离写 AMENDMENT 并在报告中披露。** 这是**资源资格审计**：不读响应数值做统计、不估 Q、不训练模型、不启动 B/C/acquisition。

## 0. 问题与边界

- **问题**：是否存在一个**独立于 Jaaks** 的资源，具有 **≥2 个独立测量组**（不同 screen/study/lab，**不是**同日/同板 barcode 分半）、**≥200 个共享细胞系**、且**同一细胞上可匹配同一/等价条件（药对+剂量设计+端点）**，使"条件级 Q 跨 screen 复验"可被检验？
- Q 定义沿用 R193/R194：`Q = (y[c,p] − y[c,q]) − (y[c',p] − y[c',q])`，主分层 `controlled_anchor`（同 anchor、同 ANCHOR_CONC、同 LIBRARY_CONC，仅 library 不同）；端点主 `SYNERGY_DELTA_EMAX`（Jaaks）。**本审计只检查候选资源能否承载该设计所需的匹配结构，不计算 Q、不读响应值。**
- 边界：`not_qualified` 不等于"条件级结构不存在"；只表示"在可得资源上，条件级跨 screen 复验不可检验"。若 not_qualified → 记录 `condition_level_cross_screen_untestable`（分析 A 收口：条件级共享规律 1.43% + 跨 screen 不可及），并给出所需资源规格。

## 1. 输入与候选（按 BRIEF §2 顺序）

| # | 候选 | 输入（本机/下载） | 用途 |
|---|---|---|---|
| C1 | **DrugComb v1.5 full summary** | Zenodo record **15235991**，`summary_v_1_5.csv`，1,421,694,989 B，Zenodo MD5 `cd3e24758c10ffaea0124b6e80626c32`；本地仅有 60×1MB 字节样本（R190-E1） | 主候选：37 study / 2,320 细胞 / 8,396 药 / 组合+单药；本审计**下载全量（≤1.5 GB 预算）**仅做结构/匹配（不读响应值） |
| C2 | **DrugComb v1.4（本地全量）** | `research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv`（193,184,734 B，SHA256 `E08E3D35…A2F`） | block 分组作为"重复测量组"的可用性与局限 |
| C3 | 本机其它成对资源 | `data/external/prism_19q4`（primary/secondary）、`beataml2_20261017`、`data/raw/oneil2026_qualification`、`data/external/gdsc2_fitted`（空）、`batchie_zenodo_13871987`（空）、`nci_almanac_2017`（空）、`data/external/gdsc_combinations`（Jaaks，既有资源，仅作 G6 重叠参照） | 逐个核查独立组/共享细胞/组合端点/剂量元数据 |
| C4 | 外部其它候选 | — | 不主动下载；只报告缺口与所需规格 |

**下载预算**：仅 C1 需要下载；**1.42 GB ≤ 1.5 GB**。下载到 `tmp/a3_v15_summary.csv`，记录 URL/字节/SHA256（本地计算）/Zenodo MD5（交叉核对）到 `a3_overlap/download_receipt_a3.json`；单命令 ≤15 min（分步：下载、审计各为独立命令）。**若下载失败或超预算 → C1 记 `data_unavailable`，用本地 60×1MB 样本作描述性上界并如实记录。**

## 2. 允许读取 / 禁止读取（冻结）

**允许读取（元数据；流式按列位置索引）**
- C1/C2 v1.5/v1.4 summary：`block_id`、`study_name`、`cell_line_name`、`drug_row`、`drug_col`、`tissue_name`、`conc_row_unit`、`conc_col_unit`、`drug_*_clinical_phase`、`drug_*_target_name`（列名语义/存在性；文本注释只用于计数，不用于效应）。
- C3：各表表头、身份列（cell line / drug 名/ID）、`BatchID`/screen 列、剂量设计列（conc/dose）、端点列**仅列存在性与空串检查**。
- Jaaks fitted（仅身份列）：`CELL_LINE_NAME`、`ANCHOR_ID`、`LIBRARY_ID`、`ANCHOR_NAME`、`LIBRARY_NAME`、`ANCHOR_CONC`、`LIBRARY_CONC`（G6 重叠）。

**禁止读取（DENY）**：任何响应/派生数值——DrugComb `synergy_*`、`S_*`、`css*`、`ic50_*`、`ri_*`、`raw_val` 等；PRISM logfold-change 数值矩阵；BeatAML `auc/ic*` 等；O'Neil `viability*`、`mu/muMax`、`X/X0`。**响应列只允许表头存在性/空串存在性检查（不解析、不转换、不聚合、不写出数值）。** 任何匹配/分层/筛选不得使用响应值（响应盲）。
- 实现约束：流式 `csv.reader` 只按列位置取 READ 列；DENY 列仅比较列名字符串；不用 pandas 读 DENY 列。

## 3. 归一与"条件"定义（冻结）

- 归一：NFKC → casefold → 仅保留 Unicode 字母数字（沿用 prior 口径）；碰撞键逐条列出、主计数保守剔除；**禁止同义词推断**（不做别名合并）。
- **条件（C0，summary 可验证层）**：`(cell_norm, unordered( drug_row_norm, drug_col_norm ))` —— 即"同一细胞上的同一组合药对"。
- **剂量设计等价（C1，summary 不可验证层）**：需要每 block 的数值剂量/剂量矩阵；C1/C2 summary **不提供**（只有 `conc_*_unit` 字符串；v1.5 无矩阵尺寸、无浓度数值）。要验证 C1 需 raw dose-level 数据（DrugComb v1.4 raw = 2,008,117,325 B > 1.5 GB 预算；v1.5 raw 亦未下载）→ **C1 本轮记为"不可验证"**，作为条件/失败类别记录，不猜测。
- **独立测量组（G1）**：C1 的 `study_name`（S1 登记表：不同 publication/lab/NCATS Tripod/PharmacoDB/AstraZeneca 来源）；**同一 study 内不同 barcode/plate 不算独立组**；同一 publication 拆出的多个 study 只有在来源不同/由 S1 明确区分时才计入（逐条列出）。C2 v1.4 无 study 列 → 只能按 block_id 窗口/study 代理分组，**记为"非独立 screen 的重复测量组"，不满足 G1 的独立性**。C3 逐资源判定。

## 4. 冻结门槛 G1–G6（判定用；任何一条不过 → `not_qualified`）

| # | 门槛 | 冻结定义与阈值 |
|---|---|---|
| **G1** | 独立测量组 ≥2 | ≥2 个**组合测量** study（有 combo block，`drug_col` 非 NULL/NA），来源可辨认为不同 screen/study/lab（S1 表 data source + study 名），且**不是**同日/同板 barcode 分半；每组 ≥100 个 combo blocks（否则不计为可用组） |
| **G2** | 共享细胞 ≥200 | 在**≥2 个独立组合 study** 中均有 combo block 的归一细胞数 ≥ **200** |
| **G3** | 匹配条件/配对单元 ≥10,000（先写死） | **匹配条件单元** = `(cell_norm, unordered pair)` 在 **≥2 个独立组合 study** 中出现；计数 ≥ **10,000**。另报告：per-study-pair 匹配数、每单元 study 数分布、**可行的跨 screen Q 四元组上界**（对每个 study 对：共享细胞 S、每细胞匹配条件集交 C(c)；`Σ_{c<c'} C(|C(c)∩C(c')|,2)`）——报告但不额外设阈值 |
| **G4** | 噪声标定覆盖 ≥5% | **覆盖** = 匹配条件单元中至少一个组内该 `(study, cell, pair)` 有 **≥2 blocks**（技术/重复测量）的比例 ≥ **5%**；另报全部 combo blocks 的组内重复比例 |
| **G5** | 组合协同端点存在 | summary 表头存在组合协同/组合敏感性端点（`synergy_bliss`/`zip`/`loewe`/`hsa`、`S_*` 等）且剂量单位/注释元数据列可查；**非饱和性本轮不读数值、不可验证**（记限制） |
| **G6** | 与 Jaaks 重叠报告 | 与 Jaaks 资源的共享细胞/药物/条件键计数（严格归一名；只报告，不单独否决，但限定"独立资源"表述） |

- G1 为**组合端点**测量组门槛；单药/单药 screen 即使细胞多也不满足（不能构造组合协同 Q）。
- 若 G2 或 G3 在 C1 上以"近似口径"通过、但 C1 剂量等价不可验证 → 只能在 G1–G5 全过时判 `qualified_with_conditions`（条件=需 raw dose-level 数据补验；预算须重新批准）。
- **判定**：`resource_qualified`（G1–G5 全过）／`qualified_with_conditions`（G1–G5 全过但存在"可得但需下载/清洗/补验"的条件，逐条列清）／`not_qualified`（G1–G5 任一失败；逐条失败原因 + 所需规格/解冻条件）。任一种判定都必须报告 G6。

## 5. 候选核查方法（冻结）

1. **C1（主）**：下载全量 → 流式扫描 v1.5 summary：行数、combo/mono 行数、study 数、每 study 的 combo blocks/细胞/药对、per-study 细胞集；计算 G1（组合 study 计数与来源）、G2（跨组合 study 共享细胞）、G3（`(cell,pair)` 跨 study 匹配计数、per-study-pair 表、Q 可行四元组上界）、G4（组内重复 block 覆盖）、G5（端点/元数据列存在性）；报告 study 级表（`a3_overlap/v15_study_table.csv`）与 per-study-pair 表（`a3_overlap/v15_study_pair_overlap.csv`）。
2. **C2（v1.4）**：流式扫描身份列：112 细胞上限（R190-E1 已实测）→ 检查 block 重复结构（每 cell×pair block 数分布、≥2 blocks 比例、最大 block 数）；用 v1.5 的 block_id→study 映射（若 v1.4/v1.5 block_id 可对齐）描述"重复 block 是否来自不同 study"；**结论上限**：总细胞 112 < 200 → G2 结构性失败；无 study 列 → G1 不满足独立性。报告其作为"重复测量组"的可用性与局限。
3. **C3（本机）**：逐资源只读元数据：
   - `prism_19q4`：primary/secondary 细胞表与 treatment info；判定端点类型（logfold change；是否组合）、screen 独立性（同一 lab/Broad；primary mono vs secondary mono）、共享细胞数；→ 组合端点缺失则 G5 失败。
   - `beataml2_20261017`：probit 单药端点、无组合 → G5 失败；细胞为患者样本非细胞系（报告）。
   - `oneil2026_qualification`：组合表（drugA×drugB×dose）；`BatchID` 3 批（同一 publication/lab，非独立 screen）；39 细胞 <200 → G1/G2 失败。
   - `gdsc2_fitted`/`batchie_zenodo_13871987`/`nci_almanac_2017`：目录为空 → `data_unavailable`（记录检索缺口，不写"不存在"）；ALMANAC/其他仅能经 DrugComb C1/C2 访问，其细胞数（S1：ALMANAC 60/ONEIL 39 等）单组 <200 → 不满足 G2。
4. **C4**：不下载；报告缺口与所需规格。
5. **G6**：Jaaks fitted 身份列（126 细胞/65 药）；与 C1 跨 study 匹配条件集/细胞集/药物集求交（严格归一名 + 碰撞报告）。

## 6. 判定与失败类别（冻结）

- `resource_qualified`：G1–G5 全过。
- `qualified_with_conditions`：G1–G5 全过，但存在"资源可得、需下载/清洗/补验"的条件（逐条列清；例如 C1 剂量等价需 raw dose-level 数据）。
- `not_qualified`：G1–G5 任一失败。逐条记录失败门槛、实测值/上界、失败类别（`data_unavailable` / `data_insufficient` / `design_mismatch` / `evaluation_cannot_distinguish`）与**所需资源规格/解冻条件**；并记录 **`condition_level_cross_screen_untestable`**（分析 A 收口），措辞写死：**"在可得资源上，条件级跨 screen 复验不可检验；这不是'条件级结构不存在'的普遍结论。"**
- 不把同一 96 细胞（Jaaks Original/Validation）当更大资源；不把 barcode 分半当独立 screen；不换 Q 聚合来救资格。

## 7. 确定性、产物与纪律

- `a3.py` 离线（C1 下载由独立取数步骤完成并记录回执）、确定性：JSON 键排序、无时间戳、固定解析顺序、无随机；输入/脚本/协议 SHA256 写入 `a3.json`；连续两跑 `a3.json` 与派生 CSV 逐字节相同。
- 产物（`research/2026-10-27-conditional-shift/` 下新增）：`PROTOCOL_A3.md`、`a3.py`、`a3.json`、`a3_overlap/`（`v15_study_table.csv`、`v15_study_pair_overlap.csv`、`v14_block_structure.csv`（如需）、`jaaks_overlap.csv`、`download_receipt_a3.json`）、`report_a3.md`、`record_a3.md`、`usage_a3.json`。不修改 A0/A1/A2/Q 既有产物、其它目录、INDEX、SYNTHESIS、git。
- 单命令 ≤15 min（下载与审计分步）；响应盲（§2）；不读响应数值、不估 Q、不训练、不启动 B/C/acquisition、不做机制/临床主张。
- **明确不做**：不把 A3 的"匹配结构存在"写成"条件级结构存在/可迁移"；不把候选资源的存在当成 A1/A2 的证据；不下载用于效应建模的数据。
