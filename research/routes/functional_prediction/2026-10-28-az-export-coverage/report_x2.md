# R203-X2 报告：AZ/GDSC 2024 重复与功能子集的导出覆盖追踪（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-127）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_X2.md](PROTOCOL_X2.md)（v1 **FROZEN**，先于任何覆盖判定冻结）
**产物**：[audit_x2.py](audit_x2.py)、[audit_x2.json](audit_x2.json)、`receipts/`（论文锚点/导出清单/结构摘要/下载回执）、[record_x2.md](record_x2.md)、[usage_x2.json](usage_x2.json)。
**纪律**：metadata-only；**不拟合效果、不重扫 3.9M wells 做效应、不重算认证 A0 68 键**；不称新颖性/迁移/决策收益/机制；不晋升代码；只写本目录与 `tmp/`。

## 0. 结论（先行）

**当前公开导出对论文声明的覆盖是"部分覆盖"；R202 的 "0 repeats" 不能成立，必须撤回/降级为导出键导致的假 0。**

- **论文报告已做**（PMC11061612）：72 h 处理 + CellTiter-Glo 2.0；**A375, HT-29, PC-14, U-2-OS, SW620, C32, MHH-ES-1 七个具名细胞系在 6 次实验中作技术三重复**（每 compound 18 replicates，provided all plates pass QC）；selumetinib+venetoclax/AZD5991、capivasertib+AZD5991、venetoclax+AZD2811 等有 **apoptosis/caspase/PARP/western** 验证（Fig 4E/F、5C/D、6C–E）。
- **当前导出实际包含重复**：7 个具名系在 raw well ZIP/Table S18 中均有记录；每系 **109 个 pair**；7 系合计 **550,350 well 行**；**301 个 (line,pair) 单元恰好 18 个 matrix 记录**；**161 个单元可归为 6 个 QC 上传日期 × 每日期 3 个 matrix**（即 6 次 × 技术三重复的结构在部分单元中可直接恢复）。
- **但当前导出没有**：显式 `experiment/occasion/technical replicate` 标签、treatment date、passage/培养独立性字段；72 h/CellTiter-Glo 2.0 的逐记录协议字段；caspase/PARP/western 的 **numeric 数据表**（只有论文图与 55 MB 补充图 PDF）。
- **措辞**：未取得项写 **"论文报告已做，当前未取得可分析记录"**；**不是**"实验未做"，**也不是**"只能新湿实验提供"。补取路径是作者/Figshare 数据字典与映射、补充源数据、或重导，不是"再做一遍实验"。
- **与 R202 关系**：R202 的 **68 A0 键未重算、不认证**；R202 的 `units_with_ge2_platforms=0` 来自 `scan_azeraw.py` 把 `lib1_drug`/`lib2_drug` 字符串（如 `38690_L56`，内含 barcode）当 pair 身份，**不是作者没做重复**。R202 的 `not_qualified` 本轮不重做；其 **G4 fail 依据"0 repeats"应撤回/降级**，剩余缺口是显式实验/重复/培养标签、协议字段与功能 numeric 数据；是否影响 Q1 资格需另立重评（本审计不宣称）。

## 1. 论文声明锚点（本地 JATS 只读；`receipts/paper_claims.json`）

来源：Europe PMC PMC11061612 / DOI `10.1158/2159-8290.CD-23-0388`；本地副本 `research/2026-10-28-blocked-conclusion-review/PMC11061612.xml`（只读；未重下载、未绕过）。

| 编号 | 论文声明 | 锚点（sec / 本地 XML 行） |
|---|---|---|
| P1 | **72 h 药物处理** | Methods "Screening"（S15）；XML line 8："the duration of drug treatment was 72 hours" |
| P2 | **CellTiter-Glo 2.0（Promega）** | S15；XML line 8："Cell Titer Glo 2.0 (Promega), 2.5μl ... luminescence microplate reader" |
| P3 | **7 个具名细胞系在 6 次实验中技术三重复** | Methods "Quality Control"（S17）；XML line 8：A375, HT-29, PC-14, U-2-OS, SW620, C32, MHH-ES-1；"technical triplicate on six occasions" |
| P3b | **每 compound 18 replicates** | S17；XML line 8："18 replicates for every compound across each of the seven lines, provided all plates meet quality controls" |
| P3c | 作者 technical/biological replicates 措辞与 QC 规则 | S17；XML line 8：比较 "technical and biological replicates"；QC 失败药物被移除 |
| P4 | selumetinib + venetoclax/AZD5991：cleaved PARP/caspase-3，24–72 h，NOMO-1 | Results S8 / Fig 4E–F；XML line 8 |
| P5 | capivasertib + AZD5991：apoptosis/caspase/PARP、QVD，AN3-CA | Results / Fig 6C–E；XML line 8："The combination of capivasertib and AZD5991 led to apoptosis"；"cleaved PARP and cleaved caspase 3 as early as 1 hour" |
| P6 | venetoclax + AZD2811：时间依赖 apoptosis、QVD | Results / Fig 5C–D；XML line 8："led to a time dependent induction of apoptosis"；Q-VD-OPH 抑制 |
| P7 | 数据可得性：screening data → Figshare project 163378；combination response → GDSC Combinations website | Data Availability；XML line 11 |

> 以上只用于"论文报告已做"的事实锚点；不代表当前导出含对应数值记录。

## 2. 当前导出/ZIP 盘点（`receipts/export_inventory.json`）

### 2.1 Figshare project 163378 的 12 个 dataset

`Dose response models for all screens`、`Results recorded for each well in 7x7 matrix experiments for all screens`、`GDSC010/009/008/007 matrix results`、`Sandpiper 1 matrix results`、`Overall ANOVA results`、`Significant ANOVA hits`、`GDSC2 single agent responses`、`Plate QC GDSC7 onwards`、`Plate QC Sandpiper 1`。
**没有** apoptosis/caspase/PARP/western 的 dataset；**没有**独立实验/重复/培养元数据 dataset。

### 2.2 raw well ZIP 字段

实际列：`PROJECT_ID, PROJECT_NAME, BARCODE, DRUGSET_ID, CELL_LINE_NAME, MASTER_CELL_ID, COSMIC_ID, CELL_ID, TISSUE, CANCER_TYPE, POSITION, INTENSITY, lib1, lib1_dose, lib1_drug_id, lib1_conc, lib2, lib2_dose, lib2_drug_id, lib2_conc, treatment, cmatrix, lib1_drug, lib1_xmid, lib1_scal, lib1_x, lib1_IC50, lib1_auc, lib1_RMSE, lib1_maxc, lib1_y, lib1_yhat, lib2_*, inhibition, HSA, HSA_excess, Bliss_additivity, Bliss_excess`。
**缺**：`replicate, replicate_id, experiment, experiment_id, batch, date, treatment_date, passage, culture, assay, exposure, timepoint`（导出无协议/实验/培养字段）。`treatment` 仅 `C`；`cmatrix` 取值 1–15（matrix 位置，不是重复标签）。

### 2.3 补充材料（Europe PMC 合法接口）

`supplementaryFiles` 为 95,000,784 B ZIP；含 32 个成员：
- **Table S1**：`Replicate Cell Line` 列，**恰有 7 个 Yes**（A375, C32, MHH-ES-1, PC-14, SW620, U-2-OS, HT-29）——与论文 P3 对应。
- **Table S18**（37,827,630 B）：`Supplementary Table 18 Single`，**84,055 行/754 细胞/7,211 barcodes/15 cmatrix**；是 matrix-level 汇总（含 `BARCODE, cmatrix, CELL_LINE_NAME, Compound1/2_name, screen` 等），**不是** caspase/PARP 数据。
- **Supplementary figures PDF**（55,390,274 B）：图/补充图，**无 CSV/XLSX 数值源数据**；没有 functional numeric 表。
- Table S2 为组合/单药名册，S3–S17 为响应/基因组特征汇总；Table S10 空表。**没有** Table S1/S18 之外的重复/功能数值表。

### 2.4 板/日期/QC 元数据

plate QC 两文件共 **7,211 barcodes**（Sandpiper-01 978 + Sandpiper-02 6,233），字段 `BARCODE, SCAN_ID, QC_FLAG, QC_UPLOAD_DATE`；**QC_UPLOAD_DATE 是 QC 上传日期，不是实验处理日期**，`QC_FLAG` 为 P/N；无 passage/实验批次。

## 3. 7 个具名重复细胞系：覆盖计数（`receipts/structure_7lines_repeats.json`）

| 细胞系 | raw well 行 | barcodes | pairs | matrix 记录/pair 范围 | 恰 18 matrix 的 pair 单元 | 恰 18 matrix 且 6 QC 日期×3 matrix |
|---|---:|---:|---:|---|---:|---:|
| A375 | 85,970 | 160 | 109 | 9–33 | 28 | 13 |
| C32 | 75,946 | 144 | 109 | 7–32 | 51 | 27 |
| HT-29 | 78,643 | 144 | 109 | 8–34 | 47 | 13 |
| MHH-ES-1 | 74,148 | 136 | 109 | 3–33 | 37 | 22 |
| PC-14 | 78,578 | 148 | 109 | 8–33 | 64 | 51 |
| SW620 | 80,226 | 147 | 109 | 7–38 | 15 | 0 |
| U-2-OS | 76,839 | 143 | 109 | 7–33 | 59 | 35 |
| **合计** | **550,350** | 1,022（行内和） | **763** | — | **301** | **161** |

- 例：A375 某 pair 的 18 个 matrix 记录分布在 **6 个 QC 上传日期、每日期 3 个 matrix**（6 次 × 技术三重复的形态）；PC-14 有 51/109 个 pair 呈此形态；SW620 的 15 个 exact-18 pair 未按 6 日期×3 对齐（有额外/缺失矩阵），故 exact 6×3 为 0。
- **重复的 raw matrix/barcode 记录确实存在**，可按 `(cell, pair, BARCODE, cmatrix)` 枚举；这与论文 P3b 的 18 replicates 方向一致，但：
  - 没有显式 `experiment/occasion/replicate` 字段；`cmatrix` 是基质位置，不是重复编号；
  - 6 个 QC 日期是**上传日期**，不是处理日期；不能据此认证"6 次实验"的日期或技术三重复标签；
  - 不是所有 pair 都恰好 18/6×3（3–38 个 matrix，部分受 QC/额外 screen 影响）。
- **R202 的 0-repeat 问题**：R202 `scan_azeraw.py` 用 `lib1_drug`/`lib2_drug`（如 `38690_L56`，含 barcode）作 pair 身份，导致同一 pair 跨 barcode 被拆成不同"pair"，从而 G4 的 `units_with_ge2_platforms=0` 是导出键造成的假 0；不是作者未做重复。R202 的 `azeraw_entities.py` 只把 ID 用于 Jaaks 重叠，没有重做重复计数。

## 4. 逐项覆盖状态（冻结 taxonomy；`audit_x2.json` 的 `coverage_items`）

| 项目 | 状态 | 证据标签 | 摘要 |
|---|---|---|---|
| P1 72 h exposure | `not_obtained` | `not_in_export` | 论文报告 72 h；导出无 exposure/timepoint 字段（**论文报告已做，当前未取得逐记录可分析字段**） |
| P2 CellTiter-Glo 2.0 | `not_obtained` | `not_in_export` | 论文报告；导出无 assay/readout 字段（**论文报告已做，当前未取得字段**） |
| P3 7 个具名系 | `available_analyzable` | `parsed_export_records` | Table S1 7 个 Yes；raw/Table S18 有记录 |
| P4a 重复 matrix/barcode 记录 | `available_analyzable` | `parsed_export_records` | 7 系 109 pairs/line；301 个 exact-18；161 个 6×3 可枚举 |
| P4b 6 次×技术三重复显式标签 | `present_but_not_analyzable` | `metadata_missing` | 无 experiment/occasion/replicate 标签；QC 上传日期不是处理日期；不能统一认证所有 pair |
| P4c 独立培养/日/passage | `not_obtained` | `not_in_export` | 无 passage/culture/day 字段；论文自称 technical triplicate；**不能当独立培养** |
| P5 板/孔/matrix/剂量字段 | `available_analyzable` | `parsed_export_records` | BARCODE/POSITION/cmatrix/conc/lib drug IDs 均可关联 |
| P6 实验日期/批次标签 | `present_but_not_analyzable` | `metadata_missing` | 有 PROJECT/DRUGSET/QC 上传日期作代理；无处理日期/实验批次/replicate ID |
| P7 functional readout（图/补充图） | `present_but_not_analyzable` | `present_but_unparsed` | 论文图/补充 PDF 存在；当前导出无数值表 |
| P7b functional numeric 记录 | `not_obtained` | `not_in_export` | 无 caspase/PARP/western 数值；**论文报告已做，当前未取得可分析记录** |
| P7c 功能细胞/组合的 screening viability | `available_analyzable` | `parsed_export_records` | Table S18：NOMO-1 107 matrix 行/106 pairs；AN3-CA 80/80；3 个 target 组合各 1 matrix 行（仅为 viability） |

**没有使用** `not_done_by_authors`：没有明确证据表明任何论文报告项未做；表内缺列不推断未做。

## 5. 映射（细胞/药物/剂量/板/日期/批次/协议）

| 维度 | 当前字段/来源 | 可关联性/限制 |
|---|---|---|
| 细胞 | raw/Table S18 `CELL_LINE_NAME, MASTER_CELL_ID, COSMIC_ID, SIDM`；Table S1 `Replicate Cell Line` | 7 系可精确识别；RRID/供应商见表 S1 |
| 药物 | `lib1_drug_id, lib2_drug_id` ↔ Table S2 `Compound1_ID/name, Compound2_ID/name`（matrix results 也有 ID/name） | 可映射；ID 为 AZ/GDSC 药物 ID，非 Jaaks ID |
| 剂量 | `lib1_dose, lib1_conc, lib2_dose, lib2_conc`；`cmatrix` 7×7 位置 | 数字剂量可关联；无 exposure time |
| 板/孔 | `BARCODE, POSITION, cmatrix`；plate QC `SCAN_ID, QC_FLAG, QC_UPLOAD_DATE` | 板/孔/matrix 可关联；QC 日期是上传日 |
| 日期/批次 | `PROJECT_ID/PROJECT_NAME, DRUGSET_ID, screen`（Table S18）；QC 上传日期 | 只有 screen/项目代理；无 treatment date/experiment batch |
| 协议 | 导出无；论文 Methods：72 h、CellTiter-Glo 2.0、Caspase-Glo 3/7、western 抗体等 | 论文协议常数可人工带入，但不能从导出自证逐键协议 |
| 功能 | 论文 Fig 4/5/6 + Supplementary Figures PDF；Table S18 仅 screening viability | 功能数值未在导出；只有图像级 |

## 6. 功能子集（P4–P6）具体覆盖

- **论文报告**：NOMO-1 的 selumetinib+venetoclax / selumetinib+AZD5991 出现 cleaved PARP/cleaved caspase-3（24–72 h，Fig 4E/F）；AN3-CA 的 capivasertib+AZD5991 有 apoptosis、cleaved PARP/caspase-3、caspase activation、QVD 抑制（Fig 6C–E）；venetoclax+AZD2811 时间依赖 apoptosis、QVD 抑制（Fig 5C–D）。
- **当前导出**：`Table S18` 中 NOMO-1 有 107 个 matrix 行/106 pairs，AN3-CA 有 80 个 matrix 行/80 pairs；上述 3 个 target 组合在 NOMO-1/AN3-CA 各 **1 个 matrix 行**（screening viability；不是重复功能数据）。
- **功能数值**：当前 12 个 Figshare dataset 无 caspase/PARP/western 数据；补充 ZIP 只有 PDF 图与 Table S1–S18（无 functional numeric 表）。因此：
  - 功能图/补充图：`present_but_not_analyzable`（只有图像级）；
  - 功能 numeric：`not_obtained`（**论文报告已做，当前未取得可分析记录**）。
- 不能将 Table S18 的 screening viability 当作 apoptosis/caspase/PARP 功能数据，也不能把 3 个 target 组合的单 matrix 行当作功能重复。

## 7. 与 R202 的 68 A0 键 / 0 重复统计口径差异（不重算认证）

| R202 声明 | 本审计处理 |
|---|---|
| AZ raw 与 Jaaks **68 个精确 A0 匹配键** | **未重算、未认证**；68 是 A0 浓度匹配键数（Jaaks 2×7 vs AZ 7×7），不是重复数；本轮只做 7 系结构覆盖，不改变其定义。 |
| AZ raw **0 repeats**（`units_with_ge2_platforms=0`） | **撤回/降级**：R202 的 pair 键用 `lib1_drug`/`lib2_drug` 字符串（含 barcode），同 pair 跨 barcode 被拆开；当前用 `lib1_drug_id`/`lib2_drug_id` + `BARCODE`/`cmatrix` 计数，7 系出现大量重复 matrix 记录（301 exact-18；161 exact 6×3）。这不是作者未做重复。 |
| **无暴露时间 / 无正交功能** | 改为：**导出无 exposure/assay 字段，但论文 Methods 报告 72 h/CellTiter-Glo 2.0**；**导出无 functional numeric 数据，但论文报告并展示 apoptosis/caspase/PARP 图**。不能写"实验未做"。 |
| R202 `not_qualified` | **不重做**；其 G4 "0 repeats" 作为 fail 的直接依据应撤回/降级；G1 68<500、功能 numeric/协议字段缺口仍存在；是否重评 Q1 需另立任务。 |

## 8. 建议的补充获取（不是新湿实验）

1. **作者/Figshare 数据字典**：`BARCODE`/`cmatrix` → experiment/occasion/technical replicate/treatment date/passage 的映射；当前导出缺显式标签，不能只凭 QC 上传日期认证"6 次实验"。
2. **功能源数据**：Fig 4E/F、5C/D、6C–E 与 Supplementary Figures 的 western/caspase/PARP 原始数值、图像定量或源表；当前只有 PDF 图。
3. **协议映射表**：72 h、CellTiter-Glo 2.0、Caspase-Glo 3/7、QVD 处理等与导出批次的对应；论文 Methods 有协议，导出无逐键字段。
4. **可选**：GDSC Combinations website 的组合响应下载/数据字典；核对 7 系 technical triplicate 与 18-replicate 的官方计数。
5. **重评条件**：若要把本资源用于 Q1 资格，应先用补充映射重建 7 系重复测量覆盖（技术三重复≠独立培养），再核 68 A0 keys/500 门槛与功能 numeric 数据；**本轮不重算、不宣称资格变化**。

## 9. 边界/限制

- 只做当前公开导出/补充材料的覆盖追踪；没有作者数据字典，不能把 QC 上传日期当处理日期，不能把 6 个 QC 日期直接等同于"6 次实验"。
- 未重扫全部 3.9M wells 做效应；未重算 A0 68 keys；结构计数仅限 7 个具名重复系与功能子集；不是对 R202 计数的重新认证。
- 补充材料是 Europe PMC 合法接口返回的 ZIP（≤500 MB）；未绕过任何登录/许可。
- 不称新颖性/迁移/决策收益/机制；不晋升代码；不改 R202 产物与 A/B/D 线产物。

## 10. 复现

```powershell
cd D:\MAESTRO\research\2026-10-28-az-export-coverage
& D:\anaconda\envs\maestro\python.exe audit_x2.py   # 读 receipts/；写 audit_x2.json
```

- 结构/补充清单生成：`tmp/recon_x2.py`、`tmp/recon_x2b.py`、`tmp/recon_x2c.py`、`tmp/recon_x2d.py`、`tmp/func_x2.py`、`tmp/build_receipts_x2.py`（只读 metadata/结构/设计，不读响应做效应）。
- SHA/确定性：`audit_x2.json` 两跑逐字节一致；协议/脚本/输入 SHA 见 `audit_x2.json` 与 `usage_x2.json`。
