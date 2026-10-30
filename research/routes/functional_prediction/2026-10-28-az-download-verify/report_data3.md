# R204-DATA3 报告：下载并本地核验 AZ/GDSC 2024 公开数据与映射重建（不运行效果）

2026-10-28 ｜ 执行：drugcomb-auditor（task-171）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_DATA3.md](PROTOCOL_DATA3.md)（v1 FROZEN）
**产物**：[download_data3.py](download_data3.py)、[verify_data3.py](verify_data3.py)、[data3_manifest.json](data3_manifest.json)、[data3_verify.json](data3_verify.json)、[build_partial_map.py](build_partial_map.py)（下一步清洗脚本，本轮未运行）、[report_data3.md](report_data3.md)、[record_data3.md](record_data3.md)、[usage_data3.json](usage_data3.json)。
**纪律**：公开合法下载；未绕过登录/terms；不运行效果/不做响应统计/不称药理/真实决策/迁移/机制/新颖性；不晋升代码；技术三重复≠独立培养；QC 上传日期≠处理日期。

## 0. 结论（先行）

**公开数据已实际取得/复用并本地复算 SHA；301/161/4,398/68,710/84,055 全部复现。** 本任务新增的可做分析是**同平台结构/描述层**，不是独立培养或功能验证。

| 项目 | 结果 |
|---|---|
| 下载/复用 | 26 个对象：**18 个复用本地副本 + 8 个新下载**；**0 error，0 SHA mismatch**；单文件≤500MB；raw ZIP 241,088,863 B SHA `E8CB50F6…D3259`，NLME 57,350,378 B SHA `AD166FF2…517C90`，Europe PMC 补充 95,000,784 B SHA `5CD77E49…3CCC7` |
| 本地字段 | raw well CSV 有 `BARCODE/DRUGSET_ID/CELL_ID/CELL_LINE_NAME/POSITION/INTENSITY/lib1_*/lib2_*/cmatrix` 等；**无 experiment/occasion/technical replicate/treatment date/passage/culture/assay/duration/SCAN_ID/QC_UPLOAD_DATE**；QC 文件按 BARCODE 提供 `SCAN_ID/QC_UPLOAD_DATE/QC_FLAG` |
| 复算计数 | **68,710 个 (cell,pair) 单元；84,055 个 matrix 记录；4,398 个 ≥2 matrix；301 个 exact-18；161 个 6 QC 日期×3 matrix（strict distinct barcode/scan 也是 161）**，与 X2/X3 完全一致 |
| 7 系 | 763 个 pair 单元；550,350 well 行；301 exact-18（**39.45%**）；161 6×3（**21.10%**）；100% 有 ≥2 matrix |
| 可重建比例 | 全导出 6×3 = **161/68,710 = 0.234%**；exact-18 = **301/68,710 = 0.438%**；≥2 matrix = **4,398/68,710 = 6.40%**；6×3 覆盖 2,898 个 matrix 记录 |
| 不可重建 | 6 日期但非每日期 3 个 = 116 单元；>6 日期 = 286；<6 日期 = 68,147；这些不能认证为 6 次实验/技术三重复 |
| 代码可用性 | 公开 parser 可生成**部分 cell/drug/dose/plate/cmatrix/QC-date/SCAN 代理映射**；**不能**生成 experiment/occasion/technical replicate/treatment date/passage/culture；`gdscmatrixexplorer.all_replicates` 是 same drug pair across projects，不能当 6×3/独立培养 |
| 资格重评 | `qualified_for_same_platform_technical_repeat_structure`（有 caveats）、`qualified_for_plate_barcode_qc_date_stratified_descriptive`（有 caveats）、`qualified_for_partial_field_mapping`（partial）；`still_unavailable_independent_culture`、`still_unavailable_official_six_occasion_certification`、`still_unavailable_functional_fig4_5_6_numeric`、`still_unavailable_cross_background/real_decision/mechanism`。**updated readiness = same_platform_structural_only / dev_only；不改旧判定；未运行效果。** |
| 建议 | **可重建部分结构映射**：用 `build_partial_map.py` 做清洗/对账；做同平台技术重复结构/一致性、plate/QC-date 分层描述的最小分析（**不运行效果**）；**官方 occasion/独立培养/功能 numeric 仍需 DATA1 request spec P0/P1**；不发起独立挑战。 |

## 1. 下载/复用清单与 SHA（`data3_manifest.json`）

- **26 项**；18 复用本地、8 新下载；0 error；0 预期 SHA mismatch；所有 ≤500MB。
- 关键大文件（复用本地，复算 SHA 与预期一致）：
  - Figshare raw well ZIP：**241,088,863 B**，SHA `E8CB50F6CE860FA17586A555130CB3B019F6011ED1976C0F0D3E00FB072D3259`；
  - Figshare NLME ZIP：**57,350,378 B**，SHA `AD166FF2096C7C16C9C0FD7B85BCCAE67059B36ADE568C1DD935C8ABD5517C90`；
  - Europe PMC 补充 ZIP：**95,000,784 B**，SHA `5CD77E495FA3EAFB249277130D7AA62A40E4997385DC2A88F2728789A433CCC7`。
- 复用/新下载的 GDSC Combos 公开 matrix summaries（完整文件，非 head）：
  - `gdsc_full_007_matrix_results.csv` 4,240,832 B SHA `974AF0CBAEB7…`（全 SHA 见 manifest）；
  - 008 4,726,121 B；009 4,365,995 B；010 2,299,653 B；sandpiper 418,215 B；
  - anchor colon 2,559,389 B；pancreas 2,234,607 B；breast 5,519,032 B。
- GDSC docs：`Matrix_documentation.pdf` 370,819 B、`Matrix_glossary.pdf` 181,578 B、`Screening_documentation.pdf` 217,875 B、`glossary.pdf` 84,942 B；SHA 与 DATA1 一致。
- 5 个代码 tarball（复用 DATA2 本地副本，复算 SHA）：eac54 23,922 B `58A5C869…FE8F`；gdscmatrixanalyser 23,643 B `84952431…E64A`；gdscmatrixexplorer 5,068,735 B `8D954567…B086A`；gdscIC50 1,207,161 B `66B1C464…23E6`；gdsctools 6,310,983 B `441B9CE5…A9B9`。
- 详细 URL/bytes/SHA/license/local path/`reused_local`/`downloaded_now` 见 `data3_manifest.json`。

## 2. 本地字段核验

- raw well CSV（3,915,245 行）列：`PROJECT_ID, PROJECT_NAME, BARCODE, DRUGSET_ID, CELL_LINE_NAME, MASTER_CELL_ID, COSMIC_ID, CELL_ID, TISSUE, CANCER_TYPE, POSITION, INTENSITY, lib1, lib1_dose, lib1_drug_id, lib1_conc, lib2..., treatment, cmatrix, ... inhibition, HSA, HSA_excess, Bliss_additivity, Bliss_excess`。
- **有**：`BARCODE`（7,211）、`DRUGSET_ID`、`CELL_ID`、`CELL_LINE_NAME`、`MASTER_CELL_ID`、`COSMIC_ID`、`POSITION`、`cmatrix`、`lib1/lib2` 数字浓度、`INTENSITY`（3,915,245 非空）、`inhibition/HSA/HSA_excess/Bliss*`（均非空）。
- **无**：`experiment, occasion, technical_replicate, replicate, treatment_date, passage, culture, assay, duration, SCAN_DATE, DATE_CREATED`；`SCAN_ID`/`QC_UPLOAD_DATE` 只在 plate QC 文件中按 `BARCODE` 关联。
- plate QC：**7,211 barcodes / 7,211 SCAN_ID / 620 QC_UPLOAD_DATE**；QC_FLAG P=6,884、F=327；日期范围 2016-09-19–2019-09-06。**QC_UPLOAD_DATE 是上传日期，不是处理日期。**
- Table S18（Europe PMC）：BarCode/DRUGSET_ID/cmatrix/CELL_LINE_NAME/Compound1/2/screen/day1...；**无** experiment/occasion/date/passage/culture；**无** caspase/PARP/western。
- **结论**：公开数据只允许 cell/drug/dose/plate/cmatrix/QC upload date/SCAN 的**代理**映射；不能从本地字段生成实验/重复/处理日/passage/culture 映射。

## 3. 本地映射重建与计数复算（`data3_verify.json`）

### 3.1 复算结果（与 X2/X3 口径一致）

| 指标 | 全导出 | 7 个具名系 |
|---|---:|---:|
| (cell,pair) 单元 | **68,710** | **763** |
| matrix 记录 `(BARCODE,cmatrix)` | **84,055** | — |
| 有 ≥2 matrix 的单元 | **4,398** | **763（100%）** |
| 恰好 18 matrix 的单元 | **301** | **301（39.45%）** |
| 6 个 QC 日期 × 每日期 3 matrix 的单元 | **161** | **161（21.10%）** |
| strict distinct barcode+scan 的 6×3 | **161** | — |
| 6×3 覆盖的 matrix 记录 | **2,898** | — |

- 分布（全导出 matrix 记录数/单元）：`1`→64,312；`2`→3,225；`3`→309；`4`→39；`5`→41；`6`→16；`7`→29；`8`→83；`9`→44；`10`→15；`11`→38；`12`→0；`13`→3；`14`→27；`15`→21；`16`→28；`17`→74；**`18`→301**；`19`→49；`20`→16；`21`→14；`22`→2；`23`→11；`24`→6；`32`→1；`33`→4；`34`→1；`38`→1。合计 **84,055**。
- 重建分类：exact 6×3 **161**；6 日期但非每日期 3 **116**；>6 日期 **286**；<6 日期 **68,147**；总 **68,710**。
- 7 系 per-line（pair 单元/rows/barcodes/exact18/6×3）：A375 109/85,970/160/28/13；C32 109/75,946/144/51/27；HT-29 109/78,643/144/47/13；MHH-ES-1 109/74,148/136/37/22；PC-14 109/78,578/148/64/51；SW620 109/80,226/147/15/0；U-2-OS 109/76,839/143/59/35。

### 3.2 可重建比例

- 全导出 6×3 可重建：**161/68,710 = 0.2343%**；exact-18：**301/68,710 = 0.438%**；≥2 matrix：**4,398/68,710 = 6.4008%**。
- 7 系：6×3 **161/763 = 21.10%**；exact-18 **301/763 = 39.45%**；≥2 **100%**。
- **不可重建**：6 日期但非每日期 3（116）、>6 日期（286）、<6 日期（68,147）——不能认证为 6 次实验/技术三重复；只能当 QC 日期/plate 结构分类。
- **重要 caveat**：`QC_UPLOAD_DATE` 是上传日期，不是处理日期；`cmatrix` 是 matrix 位置不是重复编号；6×3 分组是**结构候选**，不是官方 occasion 认证；技术三重复≠独立培养。

## 4. 代码可用性

- **`gdscmatrixanalyser/R/pipeline.R:56`**：`make_plate_list` 需要 `screen_data` 的 `BARCODE/DATE_CREATED/SCAN_ID/DRUGSET_ID/CELL_ID/CELL_LINE_NAME/MASTER_CELL_ID/COSMIC_ID`；公开 raw 有 `BARCODE/DRUGSET_ID/CELL_ID/...`，但**缺 `DATE_CREATED` 和 `SCAN_ID`**（`SCAN_ID` 可由 QC join 补）；仍不能生成处理日期/assay。
- **`gdscIC50/R/nlme_fit_prep.R:122/326`**：要求 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION` 等；公开 raw 均缺。
- **`gdscmatrixexplorer/models.py:70-97/195-224`**：`all_replicates` 是 same drug pair across projects，**不是 6×3 technical triplicate/独立培养**；不能当映射。
- **`eac54` figure Rmd**：无 mapping/functional numeric。
- **判定**：`partial_plate_fields_possible = TRUE`（cell/drug/dose/plate/cmatrix/QC-date/SCAN 可组装）；`occasion_technical_mapping_possible = FALSE`。
- **下一步清洗/对账脚本**：[build_partial_map.py](build_partial_map.py)（本轮未运行；只生成 partial structural map，字段含 `qc_date_occasion_proxy`/`technical_replicate_proxy`，并显式 `certified_independent_culture=FALSE`）；不执行效果。

## 5. 资格重评（只重评，不运行效果）

### 5.1 现在可做（结构/描述，same-platform）

- **`qualified_for_same_platform_technical_repeat_structure`（qualified_with_caveats）**：有 4,398 个 ≥2 matrix 单元、301 exact-18、161 6×3；可设计同平台技术重复的 matrix-to-matrix 方差/一致性/描述分析。**不能**声称独立培养/重复/处理日；不是效果/药理推断。
- **`qualified_for_plate_barcode_qc_date_stratified_descriptive`（qualified_with_caveats）**：按 BARCODE/SCAN_ID/QC_UPLOAD_DATE/DRUGSET/cmatrix 分层描述；QC 日期不是处理日期。
- **`qualified_for_partial_field_mapping`（partial）**：可组装 cell/drug/dose/plate/cmatrix/QC date/SCAN 代理键；仍缺 experiment/occasion/technical replicate index/treatment date/passage/culture/assay/duration。

### 5.2 仍不可做

- **`still_unavailable_independent_culture`**：无 passage/culture/flask/独立日字段；技术三重复≠独立培养。
- **`still_unavailable_official_six_occasion_certification`**：QC 上传日期不是处理日期；无官方 per-barcode occasion 映射。
- **`still_unavailable_functional_fig4_5_6_numeric`**：公开 raw/补充无 caspase/PARP/western numeric；只有论文图/PDF。
- **`still_unavailable_cross_background_transfer/real_decision/mechanism`**：无独立培养/功能/决策数据；本轮不运行效果。

- **updated readiness = `same_platform_structural_only` / `dev_only`**；**不改** R202/X1/X2/DATA1/DATA2 旧判定。**

## 6. 下一步

- **若只需结构层**：可运行 `build_partial_map.py` 生成 partial map（cell/drug/dose/plate/cmatrix/QC date/SCAN；候选 QC-date occasion/technical proxy，显式未认证），再做同平台技术重复一致性/描述分析（**不运行效果**）；不要宣称独立培养/6 次实验/药理结论。
- **若需官方重复/功能层**：**DATA1 request spec P0/P1 仍是优先**：
  1. 作者 mapping：BARCODE/cmatrix/CELL_ID→experiment/occasion/technical replicate/treatment date/passage/culture；
  2. official per-barcode 7 系×6×3 mapping/对账；
  3. Fig 4/5/6 caspase/PARP/western numeric/source data。
- **不建议独立挑战**；不需要新湿实验来补 mapping；若作者补充到位，再另立资格重评/分析任务。

## 7. 边界/复现

- 未运行效果/响应统计；未执行仓库代码；未读响应做效应；技术三重复≠独立培养；QC 上传日期≠处理日期；raw 导出无官方 experiment/重复/处理日/passage/culture。
- 下载公开合法通；不绕过登录/terms；≤500MB/文件；SHA 回执见 `data3_manifest.json`。
- 复现：
  ```powershell
  cd D:\MAESTRO\research\2026-10-28-az-download-verify
  & D:\anaconda\envs\maestro\python.exe download_data3.py   # 复用/下载并复算 SHA
  & D:\anaconda\envs\maestro\python.exe verify_data3.py     # 本地结构核验/重建（不效果）
  # build_partial_map.py 仅作下一清洗步骤，本轮未运行
  ```
- `data3_verify.json` 键排序/无时间戳；两跑一致；SHA 见 `usage_data3.json`。
