# R204-DATA1 报告：AZ/GDSC 2024 数据字典与功能数值获取性检查（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-144）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_DATA1.md](PROTOCOL_DATA1.md)（v1 FROZEN，先于检查冻结）
**产物**：[check_data1.py](check_data1.py)、[check_data1.json](check_data1.json)、`receipts/`（Figshare/GDSC/Europe PMC 回执）、[requests/](requests/)（P0/P1/P2 获取规格与模板）、[report_data1.md](report_data1.md)、[record_data1.md](record_data1.md)、[usage_data1.json](usage_data1.json)。
**纪律**：metadata-only；不拟合效果、不做响应统计、不重扫 3.9M wells 做效应；不绕过登录/许可；技术三重复≠独立培养；不写"作者未做/只能新湿实验"；不称新颖性/迁移/决策收益/机制；不晋升代码；不改 R202/X1/X2/A/B/D 产物。

## 0. 结论（先行）

**当前可获取性：`partial`。**

- **可公开取得（available_in_listing）**：Figshare 163378 的 raw well ZIP（241,088,863 B；SHA `E8CB50F6…D3259`）与 matrix/NLME summaries；两个 ZIP **内部**的字段 glossary（`Glossary_combo_well_stats.pdf`、`Glossary_matrix_nlme_stats.pdf`）；GDSC Combos 的 matrix-summary 下载与 Documentation/Glossary PDF；Europe PMC 补充 ZIP（Table S1–S18、Supplementary Figures PDF）；论文 Methods 的 72 h/CellTiter-Glo 2.0 描述。
- **缺失（not_in_listing）**：
  1. `BARCODE/cmatrix/CELL_ID → experiment/occasion/technical replicate/treatment date/passage/culture` **映射**；
  2. **7 系×6 实验×3 technical replicate 的官方计数/映射**（以及和 301 exact-18/161 6×3 单元的对账）；
  3. **Fig 4E/F、5C/D、6C–E 的 caspase/PARP/western numeric 源数据**（当前只有论文图/Supplementary Figures PDF）；
  4. 72 h/CellTiter-Glo/Caspase-Glo/QVD 的逐批/逐键协议映射；
  5. Figshare 各 dataset 的 README/数据字典（只有 ZIP 内字段 glossary）。
- **不明确（unclear）**：两个 plate QC 文章（22362712/22362631）**直接 article URL HTTP 200**，但**不在当前 project listing（10 项）**；文件本身可用，project 关联/清单归属 unclear。
- **登录/terms**：本轮检查的公开 Figshare/GDSC/Europe PMC 文件**未遇到登录/terms**；未绕过。GDSC breast anchor 的 HEAD 有一次 SSL EOF，重试后 200；不作不可得结论。
- **未取得 ≠ 未做**：以上缺失只记录为"not in listing"，**不推断作者未做**；请求/清洗/重导可补，**不写"只能新湿实验"**。

## 1. Figshare project 163378 文件清单复核（当前 10 项）

来源：`https://api.figshare.com/v2/projects/163378/articles`（HTTP 200；当前 listing **10** articles；X1 曾记录 12 项，其中两个 plate QC 现不在 project listing，但 direct article 仍 200）。

| article | 文件 | 大小/类型 | 内容 |
|---|---|---|---|
| 25266508 Dose response models | `matrix_nlme_stats_GDSC_007_010_plus_Spiper1.zip` | 57,350,378 B zip | 5 CSV + `Glossary_matrix_nlme_stats.pdf` |
| 25266697 Results recorded for each well | `matrix_well_stats_GDSC_007_010_plus_Spiper1.zip` | **241,088,863 B zip** | 5 CSV + `Glossary_combo_well_stats.pdf` |
| 22362808/802/793/769 matrix results | `gdsc-010/009/008/007_matrix_results.csv` | 8.0/15.5/16.9/14.9 MB CSV | matrix summaries |
| 22362760 Sandpiper 1 matrix results | `sandpiper-01_matrix_results.csv` | 1.3 MB CSV | matrix summary |
| 22362958 Overall ANOVA results | `Overall_ANOVA_results.csv` | **1,958,509,070 B** CSV | >500 MB，未下载 |
| 22362871 Significant ANOVA hits | `..._significant_large_effect_10_FDR_cutoff.csv` | 4.1 MB CSV | summary |
| 22362739 GDSC2 single agent responses | `GDSC2_fitted_dose_response_25Feb20.csv` | 20.4 MB CSV | comparison |

- **没有** README/数据字典/补充表文件在 listing 中；描述只有一句话（如 raw zip：“Well by well analysis of matrix experiments…”）。
- **两个 ZIP 内部有 field glossary**：
  - `Glossary_combo_well_stats.pdf`（148,064 B）：定义 `PROJECT_ID/PROJECT_NAME/BARCODE/DRUGSET_ID/CELL_LINE_NAME/MASTER_CELL_ID/COSMIC_ID/CELL_ID/TISSUE/CANCER_TYPE/POSITION/INTENSITY/lib1*/lib2*/treatment/cmatrix` 等；
  - `Glossary_matrix_nlme_stats.pdf`（147,835 B）：定义 `CL/drug/BARCODE/SCAN_ID/POSITION/DRUGSET_ID/time_stamp/...`。
  - 这些是**字段语义 glossary**，不提供 experiment/occasion/technical replicate/treatment date/passage/culture 映射；`cmatrix` 被定义为"matrix identifier in plate layout"，不是重复/实验标签；`CELL_ID` 是 stock expansion identifier，不等于 passage。
- **两个 plate QC 文章**：direct 200（`plate_qc_Sandpiper-01_13May22.csv` 234,688 B；`plate_qc_Sandpiper-02_13May22.csv` 1,492,134 B），但**不在当前 project listing**（status `unclear`）；文件无 experiment/replicate/passage 字段。
- **功能数值**：listing 中**没有** caspase/PARP/apoptosis/western 文件或描述命中；paper 的 Fig 4/5/6 只出现在论文/补充 PDF。

## 2. GDSC Combinations / 官方来源

公开页面：`https://gdsc-combinations.depmap.sanger.ac.uk/`；Dash `/downloads`（matrix/anchor tabs）可用。下载 links 的 HEAD：

| link | HTTP | content-type | content-length |
|---|---|---:|---:|
| `/downloads/gdsc-007/matrix_results` | 200 | text/csv | 4,240,832 B |
| `/downloads/gdsc-008/matrix_results` | 200 | text/csv | 4,726,121 B |
| `/downloads/gdsc-009/matrix_results` | 200 | text/csv | 4,365,995 B |
| `/downloads/gdsc-010/matrix_results` | 200 | text/csv | 2,299,653 B |
| `/downloads/sandpiper-01/matrix_results` | 200 | text/csv | 418,215 B |
| `/downloads/breast/anchor_combo` | 200（重试后） | text/csv | 5,519,032 B |
| `/downloads/colon/anchor_combo` | 200 | text/csv | 2,559,389 B |
| `/downloads/pancreas/anchor_combo` | 200 | text/csv | 2,234,607 B |

- **available_in_listing**：matrix summaries（processed）与 anchors；Documentation/Glossary PDF：`Matrix_documentation.pdf`（370,819 B）、`Matrix_glossary.pdf`（181,578 B）、`Screening_documentation.pdf`（217,875 B）、`glossary.pdf`（84,942 B）——均 HTTP 200 公开可下载。
- **字段 glossary**：`BARCODE/DRUGSET_ID/cmatrix/well_treatments/matrix_size...`；`cmatrix` 是 matrix identifier，不是 experiment/replicate。
- **协议文档**：`Screening_documentation.pdf` 明确 general GDSC 协议含 **72 h 处理 + CellTiter-Glo 2.0**；单药 anchor/library 有 **5/4 technical replicate wells**；但**没有** 7 个具名系×6 实验×3 technical triplicate 的官方计数/映射（文中“18”只是 CV≤0.18，不是 18 replicates）。
- **18-replicate official count / experiment mapping**：**not_in_listing**；没有任何 per-barcode/per-cmatrix 的 occasion/replicate/treatment date/passage/culture 表。
- **raw AZ 2024 response**：not_in_listing；anchor 页“Raw data available ... Figshare”指向 **Jaaks 相关 Figshare project 117084**，不是 AZ 2024 project 163378；AZ raw 仍是 Figshare 163378 的 raw well ZIP（已有），但没有 experiment 映射。
- **登录/terms**：公开 matrix summaries/docs 未遇到登录/terms；未绕过任何访问限制。breast HEAD 第一次 SSL EOF，重试 200；记录为 transient，不判不可得。

## 3. Europe PMC 补充材料（Table S1–S18）

来源：`https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11061612/supplementaryFiles`（95,000,784 B ZIP；32 成员；合法公开接口）。

- **没有 CSV/TSV 成员**；xlsx 表 + 图像 + **Supplementary Figures PDF**（55,390,274 B）+ 表 legend DOCX。
- 表清单/内容摘要（按 legend + 表头/行列）：
  - **S1**：755 系 cell line 表；列含 `Replicate Cell Line`（**7 个 Yes**）、Supplier、Tissue、Screen Media、Growth Properties；**无** experiment/occasion/treatment date/passage/culture。
  - **S2**：Combinations_used / Single drugs（drug IDs/names）。
  - **S3/S4/S6–S9**：combination×cancer type 响应/选择性汇总。
  - **S5**：R1_C3_data/Sheet1/SynLethDB（组合/合成致死汇总）。
  - **S10**：空表（9 行空白）。
  - **S11/S12**：组合药物类别/命中计数。
  - **S13/S14/S17**：biomarker/ANOVA 汇总。
  - **S15/S16**：通路 gene sets。
  - **S18**：`Supplementary Table 18 Single`，**84,055 行**；matrix-level screening response（BARCODE/DRUGSET_ID/cmatrix/CELL_LINE_NAME/Compound1/2_name/screen/day1_intensity_mean/day1_viability_mean 等）；**无** experiment/occasion/replicate/treatment date/passage/culture；**无** caspase/PARP/western 字段。
- **Supplementary Figures PDF**：图上/补充图；**无 machine-readable numeric 表**；没有 CSV/TSV 供给。
- **结论**：Table S1 可提供 7 系 replicate 标志；Table S18 提供 screening matrix 汇总；**没有** Fig 4/5/6 的 caspase/PARP numeric 源表或逐实验映射。

## 4. 逐项可获取性判定（`check_data1.json`）

| 检查项 | 状态 | content_scope / 说明 |
|---|---|---|
| Figshare project listing | `available_in_listing` | 10 articles；无 README/dict/supp table |
| Figshare raw well ZIP | `available_in_listing` | raw_well_structure；内部含 field glossary |
| Figshare field glossary（ZIP 内） | `available_in_listing` | field_glossary_only；不提供 experiment/replicate/date/passage 映射 |
| Figshare experiment/occasion/replicate/date/passage/culture mapping | **`not_in_listing`** | 缺；不推断未做 |
| Figshare 72h/CellTiter-Glo/Caspase-Glo metadata | **`not_in_listing`** | 论文 Methods 有；Figshare 无逐记录字段 |
| Figshare Fig 4/5/6 caspase/PARP numeric | **`not_in_listing`** | 只有论文图/PDF；不推断未做 |
| Figshare plate QC | `unclear` | direct article 200，但不在当前 project listing；文件无实验映射 |
| GDSC matrix summaries | `available_in_listing` | processed_summary_only；公开无登录 |
| GDSC field glossary | `available_in_listing` | field_glossary_only；`cmatrix` 非重复标签 |
| GDSC protocol docs | `available_in_listing` | protocol_docs_general（72h/CellTiter-Glo；5/4 technical replicate wells） |
| GDSC 18-replicate official count/mapping | **`not_in_listing`** | docs 无 18 count；无 per-plate mapping |
| GDSC experiment mapping | **`not_in_listing`** | 无 |
| GDSC raw AZ response | **`not_in_listing`** | matrix summaries processed；anchor raw link 指向 Jaaks 117084，不是 AZ 163378 |
| Europe PMC supplementary ZIP | `available_in_listing` | 32 成员；Table S1–S18 |
| Table S1 replicate flags | `available_in_listing` | replicate_flag_only（7 Yes；无 date/passage） |
| Table S18 screening summary | `available_in_listing` | processed_screening_summary（84,055 行；无 caspase/PARP） |
| Supplementary functional numeric | **`not_in_listing`** | PDF figure only；无数值表 |
| Supplementary Figures PDF | `available_in_listing` | pdf_figure_only |
| Paper protocol text | `available_in_listing` | publication_text；非 per-batch mapping |
| Other official sources | `unclear` | GDSC/Cell Model Passports/Figshare 117084 仅元数据级别检查；无 AZ 2024 字典/功能表 |

## 5. 获取清单/请求规格摘要（详见 `requests/data_request_spec.json`、`requests/request_template.md`）

给作者/Figshare 的具体请求（不伪造联系方式；走 Figshare/期刊公开联系方式）：

| 优先级 | 请求 | 关键交付 |
|---|---|---|
| **P0** | `BARCODE/cmatrix/CELL_ID → experiment/occasion/technical replicate/treatment date/passage/culture` 映射 | CSV/TSV + field dictionary；覆盖 7 系 109 pairs/六 occasions×三 technical；最好全 754 系 |
| **P0** | Fig 4E/F、5C/D、6C–E caspase/PARP/western numeric source | CSV/XLSX + uncropped blot images + antibodies/controls/timepoints/replicates |
| **P1** | 72h/CellTiter-Glo 2.0/Caspase-Glo 3/7/QVD 与批次/plate 的协议映射 | 每行可标 protocol 或 unknown；7 系全覆盖 |
| **P1** | Figshare 各 dataset 的 README/字段字典（含 `CELL_ID` stock expansion vs passage） | README/PDF；`cmatrix`/`DRUGSET_ID` 语义 |
| **P0** | 7 系×6 实验×3 technical replicate 的官方计数/映射；与 301 exact-18/161 6×3 对账 | mapping table + methods note；区分 technical vs independent |
| **P1** | 公开 notebook/代码生成/校验映射（`gdscmatrixanalyser` 等） | Python/R notebook；author 确认语义 |
| **P2** | 补充图/表 numeric source data（CSV/XLSX 而非 PDF） | 图 panel/sheet 对应关系 |

**替代路径**：作者重导映射/补充数据；Europe PMC/Figshare 更新；用公开 `BARCODE/SCAN_ID/DRUGSET_ID/cmatrix` + plate QC 生成候选映射并由作者确认 technical/biological 语义；**不写只能新湿实验**。

## 6. 总体判定与下一步

- **当前可获取性 = `partial`**：raw 结构/字段 glossary/processed matrix summaries/Table S1–S18/论文协议文本可取得；**关键 experiment/replicate/date/passage/culture 映射**与**Fig 4/5/6 功能 numeric** 不在公开 listing/补充中；plate QC 清单归属 unclear。
- **下一步（获取/清洗/重导，不是新湿实验）**：
  1. 按 `requests/data_request_spec.json` 发 P0/P1 请求；
  2. 先使用公开代码/notebook 从 barcode/scan/drugset/cmatrix 生成候选映射（不认证独立培养）；
  3. 若拿到映射+功能数值，再更新 R204 数据 readiness / 另立资格重评；本轮不改 R202/X1/X2 判定；
  4. 不把技术三重复当独立培养；不把 Table S18 screening viability 当 caspase/PARP 功能读数。
- **不写**"作者未做"或"只能新湿实验"；`not_in_listing` 仅表示当前公开清单/文件中没有。

## 7. 边界/复现

- metadata-only；无响应值/效果拟合；无训练/预测；无代码晋升；无新颖性/迁移/决策收益/机制主张；不改旧判定。
- 单文件 ≤500 MB；>500 MB 文件（Overall_ANOVA 1.96 GB）仅记录未下载；公开接口/页面记录 URL/HTTP/bytes/SHA 于 `receipts/`。
- 复现：
  ```powershell
  cd D:\MAESTRO\research\2026-10-28-az-data-acquisition
  & D:\anaconda\envs\maestro\python.exe check_data1.py
  ```
- `check_data1.json` 键排序、无时间戳；两跑一致；SHA 见 `usage_data1.json`。
