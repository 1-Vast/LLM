# R202-Q1 报告：外部独立组合/功能资源定向征询与资格（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-126）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_X1.md](PROTOCOL_X1.md)（v1 **FROZEN**；在任何外部资格判定前冻结）
**产物**：[hunt_x1.py](hunt_x1.py)、[hunt_x1.json](hunt_x1.json)、`receipts/`（下载/访问/检索回执）、[record_x1.md](record_x1.md)、[usage_x1.json](usage_x1.json)。
**纪律**：metadata-only；**未运行效果/未拟合预测/未读响应值做效应**；不称新颖性/迁移/决策收益/机制；阴性写"未发现/不可得"不写"不存在"；不把同一 96 细胞换聚合当新数据；不把已聚合挑战分数当原始重复。

## 0. 判定（先行）

# 总体：`not_qualified`——**建议停止本轮外部征询**

**没有任何候选**满足冻结的 G1–G7 全部门槛；连 `qualified_with_conditions` 也没有。原因不是"没找到组合数据"——本轮找到了**比本地更原始、更大的外部组合数据**（AstraZeneca/GDSC 2024 raw 7×7 wells、NCI-ALMANAC 原始 well 表），但两者都在**同一处失败**：

- **G4 独立测量/独立培养**：外部组合资源每个 `(cell, pair)` 的剂量条件**只有一次测量**（AstraZeneca 2024：84,055 个 pair-cell 中 **0** 个有 ≥2 个重复板；NCI-ALMANAC：2,866,683 个 key 中仅 **0.24%** 有跨板重复）。技术重复/相邻剂量不能替代独立培养。
- **G1 与 Jaaks 的匹配键**：AstraZeneca 2024 有 114/125 共享细胞、14 个共享药物、4,510 个共享 cell-pair 实体（8 个不同有向对），但**精确 A0 浓度匹配键仅 68 个（<500）**；NCI-ALMANAC 只有 13 个共享细胞、17 个共享药物、186 个"在 Jaaks 药物集内"的对，**精确 A0 匹配键 0**。
- **G3/G5**：两者都**没有暴露时间字段**、都只有 viability 派生端点（无 apoptosis/caspase/靶点参与/再生长等正交功能读数）。

| 候选 | 判定 | 原因码 |
|---|---|---|
| **AstraZeneca/GDSC 2024 raw wells**（AACR Cancer Discovery CD-23-0388；GDSC007-010 + Sandpiper-01） | `not_qualified` | `no_independent_replicate_or_culture`、`jaaks_overlap_insufficient`、`no_exposure_time`、`no_orthogonal_functional_readout` |
| **NCI-ALMANAC**（NCI-60） | `not_qualified` | `no_independent_replicate_or_culture`、`jaaks_overlap_insufficient`、`no_exposure_time`、`no_orthogonal_functional_readout` |
| AstraZeneca-Sanger DREAM 2015 | `not_qualified` | `access_restricted`（Synapse 数据文件匿名 403、需 terms/login） |
| PanThera 2024 | `not_qualified` | `aggregated_only`、`no_combination_data`（模型/predicted triplet 数据库，无原始 wells） |
| SAFER 2024 | `not_qualified` | `reaggregated_lineage`、`data_unavailable`（1.13 GB 处理数据，源自 O'Neil/ALMANAC/DrugComb，>500 MB） |
| Dryad 类器官顺序给药 2025 | `not_qualified` | `jaaks_overlap_insufficient`、`access_restricted`（类器官、无 Jaaks 细胞系；文件下载 401） |
| HuggingFace ABX-CT-004 顺序治疗 | `not_qualified` | `synthetic_benchmark`、`no_cancer_combination_data` |
| Novartis DRUG-seq U2OS（HuggingFace 镜像） | `not_qualified` | `no_combination_data`、`mono_only` |
| 功能独立性资源（apoptosis/caspase/靶点参与/再生长 + 同组合 wells） | 未发现/不可得 | `no_candidate_found`（有界检索结果，不是"不存在"） |

**建议**：停止外部征询，不再逐库追索；若重开 A/B/D3 线，所需的是**新测量**（独立重复板/培养 + 暴露时间 + 正交功能读数 + 与 Jaaks 可匹配的 500 键），而不是"再找一个大组合表"。**AstraZeneca/GDSC 2024 raw 是唯一值得保留的"新关系开发资源"**（754 细胞/109 药物/7×7 原始 wells），但它不是本任务的合格独立重复/功能目标（见 §4）。

## 1. 方法、检索与下载记录（摘要；回执见 `receipts/`）

- **检索日期 2026-10-28**；有界定向，不是系统综述；查询与 API 探测见 `receipts/search_log.json`。
- **下载/HTTP 记录**：`receipts/download_manifest.json`（URL/HTTP 状态/bytes/SHA256/许可）；访问限制见 `receipts/access_status.json`。单文件 ≤ **500 MB** 规则执行；未绕过登录/许可。
- 没有读任何响应值做效应；`hunt_x1.py` 只读结构/元数据/空值/实体计数。

### 1.1 实际下载（≤500 MB；SHA 已记录）

| 文件 | 来源 | 大小 | SHA256 |
|---|---|---:|---|
| `ComboDrugGrowth_Nov2017.zip`（NCI-ALMANAC） | NCI wiki attachment | 85,966,226 B | `69367A8B…96100` |
| `gsdc_well_stats.zip`（AstraZeneca/GDSC 2024 raw wells） | Figshare project 163378, article 25266697 | **241,088,863 B** | `E8CB50F6…D3259` |
| `gdsc010_matrix_results.csv`（AZ/GDSC） | Figshare 163378 | 8,026,089 B | `403212F4…5F1C5` |
| `gdsc-007/008/009_matrix_results.csv`、`sandpiper-01_matrix_results.csv` | Figshare 163378 | 15–17 MB / 1.3 MB | 见回执 |
| `GDSC2_fitted_dose_response.csv` | Figshare 163378 | 20,355,833 B | `0883B3EF…B50302` |
| `ComboCompoundNames_all.txt`、`ALMANAC_DataFields.txt` | NCI wiki | 50,857 / 3,880 B | 见回执 |
| PanThera `studies.zip` | Zenodo 14216168 | 658,429 B | `23E8418A…EE88AC` |
| SAFER `readme.txt` | Zenodo 10822779 | 9,138 B | `B4F0F86D…AAF796` |

- 未下载：SAFER `data.tar.gz` 1,131,872,853 B / `database.tar.gz` 1,136,276,427 B（>500 MB；且其 readme 表明是 O'Neil/ALMANAC/DrugComb 的处理数据）；AZ 2024 的 ANOVA 结果 1.96 GB（>500 MB）；PanThera models 877 MB（>500 MB）；DRYAD 文件下载 401。
- 访问受限：AstraZeneca-Sanger DREAM 2015 的 Synapse 数据文件实体（`syn4923182`、`syn4925540`、`syn4925542`、`syn4925546`、`syn4925534`）匿名 HTTP **403**；公开 wiki/项目元数据可用，提示需登录/接受 terms。**这是"访问受限"，不是"不存在"。**

### 1.2 关键一手来源

- AstraZeneca 2024 paper：*Large-scale Pan-cancer Cell Line Screening Identifies Actionable and Effective Drug Combinations*, Cancer Discovery 2024, DOI `10.1158/2159-8290.CD-23-0388`；PMC11061612。其 Data Availability 写明：screening data 经 **Figshare project 163378**、combination response 经 **GDSC Combinations website**。项目 12 个 dataset；本项目抓取的是其中**原始 well-level 7×7 matrix** zip。
- NCI-ALMANAC wiki：`https://wiki.nci.nih.gov/display/NCIDTPdata/NCI-ALMANAC`；数据字典（字段/计算公式）、`ComboDrugGrowth_Nov2017.zip`。
- AstraZeneca-Sanger DREAM 2015：Synapse `syn4231880`（public wiki 描述：~11.5k combinations / 85 cell lines / 118 drugs / monotherapy；数据需 terms）。
- PanThera：Zenodo 14216168（模型/数据/tuning logs）；PanTheraDB 14001717 是**预测** triplets。
- SAFER：Zenodo 10076432/10076433（数据+readme；processed）。
- Dryad：DOI `10.5061/dryad.0vt4b8h8x`（Science Advances 2025，类器官顺序给药；CC0 元数据；文件 401）。
- Novartis DRUG-seq U2OS：HuggingFace 镜像（mono 转录组，无组合）。
- ABX-CT-004：HuggingFace 合成顺序治疗基准。

## 2. 冻结门槛与候选逐项结果

**门槛**（PROTOCOL_X1 §3，冻结）：G1 与 Jaaks ≥10 细胞/≥10 有向对/≥500 匹配键；G2 原始板孔与 Jaaks O/V 不相交；G3 数字剂量+暴露时间；G4 独立测量或独立培养（技术重复不算）；G5 ≥1 正交功能读数（若主张功能）；G6 冻结聚合 Δ/功能 viability；G7 非重聚合 lineage。判定 `qualified`/`qualified_with_conditions`/`not_qualified`。

### 2.1 AstraZeneca/GDSC 2024 raw wells——最大、最原始，但 G4/G1 失败

- **规模**（原始数据，不是挑战分数）：5 个 screen（GDSC_007/008/009/010 + Sandpiper-01）；**3,915,245 个 well 行**；**754 个细胞系**；**7,211 个 plate barcode**；**84,055 个 (cell,pair) 单元**（每个 7×7 矩阵 = 49 wells）；每行含 `BARCODE/POSITION/INTENSITY`、`lib1/lib2` 数字浓度、单药拟合参数、`HSA/Bliss` excess；**没有暴露时间列**。
- **与 Jaaks 重叠**：共享 **114/125 细胞**（通过名称/COSMIC 映射；Jaaks 只有 11 个细胞不在其中）；共享 **14 个药物**；**8 个不同有向对**（distinct）；**4,510 个 cell-pair 实体单元**；**精确 A0 浓度匹配键仅 68 个**。**plate barcode 与 Jaaks 0 重叠**（不同板/轮次）。
- **G1：fail**（cells pass；distinct pairs 8<10；matched keys 68<500）。
- **G2：pass**（barcode 0 重叠；但同细胞面板/同 programme family，见 G7）。
- **G3：conditional**（数字剂量存在；**无 exposure time/assay 方法字段**）。
- **G4：fail**：84,055 个 pair-cell 中 **0** 个有 ≥2 个 barcode；每个 pair-cell 只有一张 7×7 矩阵（每剂量条件 1 个 well），**没有独立重复板/培养**。
- **G5：conditional**：只有 viability/inhibition 及 HSA/Bliss 派生；无 apoptosis/caspase/靶点参与/再生长。
- **G6：conditional**：可预注册 Δ/剂量聚合，但无 exposure time、目前无冻结聚合。
- **G7：conditional**：与 Jaaks 板 barcode 不同、独立 2024 发表；但共享同一 GDSC/AZ 细胞面板与 14 个药物、同一 programme family → plate/round 层独立，lineage 层不独立。
- **判定：`not_qualified`**。价值：这是**新关系开发**（new cells/pairs）的强资源；但作为本任务需要的"独立重复 + 正交功能 + A0 可匹配"目标不合格。

### 2.2 NCI-ALMANAC——原始 well 表，但重复/匹配/功能不足

- **规模**：**3,686,475 行**（combo 2,873,514 + solo 812,961）；**61 个细胞**（NCI-60 + 1 变体）；**5,242 个 NSC 对**；**305,081 个 (cell,pair) 单元**；**1,570 studies / 26,687 plates / 3 screeners / 154 dates**；`PercentGrowth/PercentGrowthNoTZ/TestValue/ControlValue/TZValue`（viability/OD 原始）；数字剂量 `Conc1/Conc2`。
- **重复结构**：`(cell,pair,conc1,conc2)` 共 **2,866,683 个 key**，其中只有 **6,831 个（0.24%）有 2 行且跨不同 plate/study**；其余为单次测量。
- **与 Jaaks 重叠**：共享 **13** 个细胞（12 个在 A0 96 细胞集）；共享 **17** 个药物；**186 个 NCI 对**完全在 Jaaks 药物集内；**精确 A0 浓度匹配键 = 0**（Jaaks 2 anchor × 7 library 与 NCI 3×3 浓度设计不匹配）。
- **G1：conditional**（cells 13 pass；matched keys 0 <500；无 ≥10 有向对的可靠匹配——186 只是"药物集内"的上界）；**G2 conditional**（plate 命名空间不同、无共享标识，不能证明物理 disjoint）；**G3 conditional**（数字剂量，无 exposure time）；**G4 fail**（0.24% 重复）；**G5 conditional**（viability/OD 派生，无正交功能）；**G6 conditional**；**G7 pass**（NCI/DTP 原始 lineage；DrugComb ALMANAC 是它的派生）。
- **判定：`not_qualified`**。

### 2.3 AstraZeneca-Sanger DREAM 2015——访问受限

- 公开 wiki 报 **~11.5k 组合 / 85 细胞 / 118 药物 + monotherapy**；Synapse 数据文件实体匿名 **403**（需登录/接受 terms），无法核重复/剂量/端点/重叠；不下载、不绕过。
- **判定：`not_qualified`（`access_restricted`）**。若 Lead 能提供 Synapse 账号/terms，需重新走 Q1 资格（不能凭 wiki 宣称合格）。

### 2.4 PanThera / SAFER / 其他 2024–2026

- **PanThera 2024**：Zenodo 14216168 有 models（877 MB，>500 MB）、data.zip（276 MB）、studies.zip（Optuna tuning logs）；PanTheraDB 14001717 是**预测** synergy triplets。没有原始 wells ⇒ `aggregated_only` / `no_combination_data`。
- **SAFER 2024**：Zenodo 10076432 的 data/database 各 ~1.13 GB（>500 MB），readme 明确是 O'Neil/ALMANAC/DrugComb 的处理数据 ⇒ `reaggregated_lineage` + `data_unavailable`（超单文件限制）。
- **Dryad 类器官顺序给药 2025**：public CC0 元数据（Science Advances 2025，patient-derived organoids/spheroids，sequential multidrug）；data.zip 30 KB + README 14 KB，但文件下载 **401（bearer token）**；**没有 Jaaks 细胞系/实体重叠** ⇒ `jaaks_overlap_insufficient`/`access_restricted`。它对方向 3（顺序程序）是**潜在新方向资源**，但须新协议与新资格标准（非本 Q1 的 Jaaks 门槛）。
- **HuggingFace ABX-CT-004**：合成抗生素顺序治疗基准（n<1k），非实验癌症组合数据 ⇒ `synthetic_benchmark`。
- **Novartis DRUG-seq U2OS（HuggingFace 镜像）**：49,392 个 mono 转录组观测、3,742 化合物；**无组合/功能端点** ⇒ `no_combination_data`。
- **功能独立性资源**：有界检索 + API 探测**未发现**公开的"同组合 wells + apoptosis/caspase/靶点参与/再生长"配对资源；这是检索结果，不是"不存在"。

## 3. Δ 可估性与"为什么仍不合格"

- AstraZeneca 2024 raw 有数字剂量、7×7 每 pair-cell wells、raw viability；Δ 可在**新关系**上定义（预注册剂量平均/聚合），但：
  - **无独立重复**：每个 (cell,pair,dose) 只有 1 well；pair-cell 级 0 重复板 → 不能独立标定噪声或做独立重复验证；
  - **无暴露时间**：无法证明 6/24/48h 等暴露等价；
  - **无正交功能**：INTENSITY/inhibition/HSA/Bliss 均 viability 派生；
  - **与 Jaaks 精确匹配键仅 68**：不足以重开现有 A0/Jaaks 条件规律检验（G1）。
- NCI-ALMANAC 的 0.24% 重复只覆盖少数 key，且与 A0 设计不匹配（0 精确键）；同样不能形成可比较的独立测量/培养目标。
- 因此**不是 MDE/精度问题**（这些资源本身规模大），而是**独立测量/功能端点/匹配设计**缺失；与 R201 A 线收束原因一致（C192/C194/C195：O'Neil 4×4 技术重复无法独立校准零模型/σ）。本轮外部寻找**没有改变该瓶颈**。

## 4. 建议与所需测量规格（写死）

**建议：停止本轮外部征询**（不再逐库追索/下载），因为：
1. 现有公开组合资源要么访问受限（DREAM），要么已聚合/处理（PanThera/SAFER），要么 mono-only（Novartis DRUG-seq/PRISM/BeatAML/Mix-seq），要么无独立重复/暴露/正交功能（AZ 2024 raw、NCI-ALMANAC）；
2. 唯一的大 raw 资源（AZ 2024）已抓取到本地（241 MB zip，SHA 记录）；它可用于**新关系开发**或**设计新实验的剂量矩阵参考**，但不能作为本任务的独立验证目标；
3. 继续找"更大的组合表"不会产生独立重复/功能读数——这些只能由新湿实验提供。

**若 Lead 要重开 A/B/D3 线，所需测量规格（最小）：**
1. **独立重复**：每 `(cell, directed pair, dose)` 至少 **2 个独立培养/板**（不同日/passage/flask；技术孔不算）；报告培养/批次元数据。
2. **合法暴露**：数字剂量设计 + **暴露时间/检测方法**，伙伴浓度匹配，预注册剂量平均/聚合与 Δ 定义。
3. **同族端点**：与 Jaaks `SYNERGY_DELTA_EMAX` 同族，或提供单药参照/校准并用预注册规则换算；不得把 raw viability 直接与 ΔEMAX 混合。
4. **正交功能读数**：同组合 wells 的 apoptosis/caspase、靶点参与、再生长/live imaging 至少一项。
5. **A0 可匹配**：≥500 个 A0 浓度匹配键（或明确另立"新关系"协议，不再声称复用 A0/Jaaks 条件规律）。
6. **lineage**：报告 screen/plate/well 来源链与与 Jaaks/DrugComb/PRISM/BeatAML/Mix-seq/O'Neil 的不重聚合关系；**不得把 96 细胞换聚合当新数据**；不得把已聚合挑战分数当原始重复。

## 5. 边界与限制

- **不声称**：机制、迁移、决策收益、新颖性；**不写"外部不存在此类资源"**——只写本次有界检索未发现/不可得（`未发现` 不是 `不存在`）。
- **不重开** R196/R197 旧判定（C176/C177），不把本轮资源当作 C192/C194/C195 的否定或 A 线复活。
- 检索范围有限：未查 Google Scholar/Scopus/WoS、未做引文回溯；2024–2026 新资源可能漏检；未尝试登录/付费/提交申请（用户允许下载，但本任务不越许可）。
- AZ 2024 的 drug 名称映射只覆盖 46 个 ID（matrix results 5 个文件；实际 109 drugs），因此**共享药物/对计数是下界**；但**matched A0 keys 68（即使完整映射也很难达到 500）** 与 **0 重复板** 两处硬失败不受影响。
- NCI-ALMANAC 的 3×3 设计 vs Jaaks 2×7 的匹配不成立；不同端点/暴露的跨资源比较不作效果解释。
- 所有下载文件 SHA/HTTP 状态/许可写入 `receipts/`；`hunt_x1.json` 记录每个候选的 gate/原因码/整体建议。

## 6. 复现

```powershell
cd D:\MAESTRO\research\2026-10-27-external-resource-hunt
& D:\anaconda\envs\maestro\python.exe hunt_x1.py   # 读 tmp/extq1/*.json 元数据摘要 + receipts；写 hunt_x1.json
```

- 结构性扫描脚本（已运行；输出在 `tmp/extq1/`）：`tmp/scan_nci.py`、`tmp/nci_overlap.py`、`tmp/nci_matched_keys.py`、`tmp/scan_azeraw.py`、`tmp/azeraw_entities.py`；仅读设计/身份/行数/空值，未读响应做效应。
- 下载回执：`receipts/download_manifest.json`；访问/检索：`receipts/access_status.json`、`receipts/search_log.json`。
- 产物 SHA 见 `usage_x1.json`；`hunt_x1.json` 为键排序、无时间戳、确定性输出。
