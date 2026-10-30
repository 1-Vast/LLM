# record_data1 —— R204-DATA1 AZ/GDSC 2024 数据字典与功能数值获取性检查（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-144）｜ 工作目录 `D:\MAESTRO`
**范围**：只写 `research/2026-10-28-az-data-acquisition/`（`PROTOCOL_DATA1.md`、`check_data1.py`、`check_data1.json`、`report_data1.md`、`record_data1.md`、`usage_data1.json`、`receipts/`、`requests/`）与 `tmp/`；不改 R202/X1/X2/A/B/D 产物。
**纪律**：metadata-only；不拟合效果、不做响应统计、不重扫 3.9M wells 做效应；不绕过登录/许可；技术三重复≠独立培养；不写"作者未做/只能新湿实验"；不称新颖性/迁移/决策收益/机制；不晋升代码。

## 0. 任务与结论

- 任务：检查 AZ/GDSC 2024 公开来源是否已有 `BARCODE/cmatrix→experiment/occasion/technical replicate/treatment date/passage/culture` 数据字典/映射、72h/CellTiter-Glo/Caspase-Glo 元数据、Fig 4/5/6 caspase/PARP 数值源表；整理获取清单/请求规格。
- **总体当前可获取性：`partial`**：
  - 可取得：Figshare 163378 raw well ZIP/matrix summaries（+ ZIP 内字段 glossary）、GDSC Combos matrix summaries/docs、Europe PMC Table S1–S18、Supplementary Figures PDF、论文 Methods 文本。
  - 缺失：experiment/replicate/date/passage/culture 映射、7 系×6×3 官方计数/映射、Fig 4/5/6 功能 numeric、逐批协议映射、Figshare README/data dictionary（仅字段 glossary）。
  - plate QC 两 article direct 200 但**不在当前 project listing** → `unclear`；不推断不存在。
- **未取得 ≠ 未做**：缺项记录 `not_in_listing`，请求/重导可补；**不写作者未做、不写只能新湿实验**。
- **登录/terms**：公开 Figshare/GDSC/Europe PMC 文件未遇到；未绕过。GDSC breast HEAD 一次 SSL EOF，重试 200（记录 transient）。

## 1. 时间线（2026-10-28）

| 步骤 | 内容 |
|---|---|
| 读输入 | task-144；R204 `BRIEF_R204.md`/`report.md`；X1/X2/X3 报告与 JSON；C200/C202/C203；用户复核 §5 |
| 冻结协议 | `PROTOCOL_DATA1.md` v1 FROZEN（状态 taxonomy、检查对象、请求规格、边界）；之后未改定义 |
| Figshare | 重新查 project 163378 articles API（当前 10 项）与 article details/files/descriptions；核 plate QC direct articles；检查 raw/NLME ZIP 内部成员/glossary |
| GDSC | 查 `/downloads`（matrix/anchor tabs）、Documentation/Glossary PDF、matrix summary HEAD；`Screening_documentation` 文本；不登录 |
| Europe PMC | 取 supplementaryFiles ZIP（95,000,784 B；32 成员）；Table S1–S18 表头/行列/legend；确认 PDF 图-only |
| 回执/判定 | `receipts/figshare_listing.json`、`gdsc_access.json`、`europepmc_supplementary.json`；`check_data1.py` → `check_data1.json`；请求规格/模板 |
| 不运行 | 不拟合效果、不做响应统计、不重扫 wells、不晋升代码、不改旧判定 |

## 2. 关键事实

### 2.1 Figshare project 163378（当前 listing 10 项）
- raw ZIP：`matrix_well_stats_GDSC_007_010_plus_Spiper1.zip` **241,088,863 B**（SHA `E8CB50F6…D3259`），5 CSV + `Glossary_combo_well_stats.pdf`（148,064 B）。
- NLME ZIP：57,350,378 B，5 CSV + `Glossary_matrix_nlme_stats.pdf`（147,835 B）。
- matrix results/GDSC2/ANOVA summary files；无 README/data dictionary/supp table/functional 文件。
- **字段 glossary 仅定义字段语义**（BARCODE/cmatrix/CELL_ID 等）；`cmatrix` 是 matrix identifier，不是 experiment/replicate；**无** experiment/occasion/technical replicate/treatment date/passage/culture 映射。
- plate QC direct 200（22362712/22362631；234,688/1,492,134 B），但**不在当前 project listing（10）**；status `unclear`。X1 曾记录 12 项，本轮为 10 项+direct 200；不推断原因。
- Listing/描述无 caspase/PARP/apoptosis/western 命中；Fig 4/5/6 只有论文/补充 PDF。

### 2.2 GDSC Combos / 官方
- `/downloads` 公开 matrix summaries HEAD 200（gdsc-007 4.24MB, gdsc-008 4.73MB, gdsc-009 4.37MB, gdsc-010 2.30MB, sandpiper 0.42MB；anchor colon 2.56MB/pancreas 2.23MB/breast 5.52MB 重试后 200）。
- docs/glossary 公开：`Matrix_documentation.pdf` 370,819 B、`Matrix_glossary.pdf` 181,578 B、`Screening_documentation.pdf` 217,875 B、`glossary.pdf` 84,942 B。
- `Screening_documentation.pdf`：**72 h + CellTiter-Glo 2.0**；单药 anchor/library **5/4 technical replicate wells**；无 `18 replicates` 官方计数（“18”是 CV≤0.18）；无 experiment/occasion/passage/culture 映射。
- `cmatrix` 在 glossary 中为 matrix identifier；无 per-plate occasion/replicate mapping。
- Anchor 页 raw-data link 指向 **Jaaks 相关 Figshare 117084**，不是 AZ 2024 163378；raw AZ 仍是 163378 raw ZIP（已有）。
- **登录/terms**：公开下载未遇到；未绕过；breast HEAD 一次 SSL EOF 后重试 200。

### 2.3 Europe PMC 补充材料
- 95,000,784 B ZIP；32 成员；无 CSV/TSV；含 Table S1–S18 + images + Supplementary Figures PDF（55,390,274 B）+ table legend DOCX。
- **Table S1**：755 系表；`Replicate Cell Line` 7 个 Yes；无 experiment/occasion/date/passage/culture。
- **Table S18**：84,055 行 matrix-level screening response；BARCODE/DRUGSET_ID/cmatrix/CELL_LINE_NAME/Compound1/2_name/screen/day1_intensity_mean/day1_viability_mean；无 caspase/PARP/western 字段；无 experiment/replicate/date/passage/culture。
- **S10** 空表；S3–S17 为响应/类别/biomarker/gene set 汇总；**无** Fig 4/5/6 numeric 源表。
- Supplementary Figures PDF = 图/补充图 only；无 machine-readable numeric 表。

## 3. 逐项判定（`check_data1.json`）

`available_in_listing`：Figshare listing/raw ZIP/field glossaries（ZIP 内）、GDSC matrix summaries/glossary/protocol docs、Europe PMC supplement/Table S1/S18/PDF、paper protocol text。
`not_in_listing`：Figshare experiment/replicate/date/passage/culture mapping、72h/CellTiter-Glo/Caspase-Glo 元数据、Fig 4/5/6 functional numeric、GDSC 18-replicate count/mapping/experiment mapping/raw AZ response、supp functional numeric。
`unclear`：Figshare plate QC（direct 200 但不在 listing）、other official sources（仅元数据级别检查）。
`available_but_restricted`：**无**（本轮公开文件未遇登录/terms；不绕过）。

## 4. 请求/下一步

- `requests/data_request_spec.json`（7 项 P0/P1/P2）+ `requests/request_template.md`：
  - P0 映射（BARCODE/cmatrix/CELL_ID→experiment/occasion/technical replicate/treatment date/passage/culture；7 系，最好全 754）；
  - P0 Fig 4/5/6 caspase/PARP/western numeric/原图；
  - P1 72h/CellTiter-Glo/Caspase-Glo/QVD 批次映射、README/字典、公开 notebook、补充 numeric source。
- 替代：作者重导/补充数据/Europe PMC 更新/公开 notebook 生成候选映射并由作者确认；**不写只能新湿实验**。
- 若拿到数据：更新 R204 数据 readiness，另立资格重评/内部功能问题设计；本轮不改 R202/X1/X2 判定。

## 5. 偏离/限制

- Listing 状态是 2026-10-28 当前快照；X1 12→本轮 10 的差异未解释（plate QC direct 200），不推断原因。
- 只做公开元数据/清单/表头/小文档；未下载 Overall_ANOVA 1.96GB；未做全站/全库搜索；other official sources 仅 limited metadata。
- 不读响应做效应；不拟合/不训练；不晋升代码；技术三重复≠独立培养；PDF 图≠numeric 功能数据。
- 不写作者未做/只能新湿实验；`not_in_listing` 不是"不存在"。

## 6. 产物/SHA

见 `usage_data1.json`；协议/脚本/检查 JSON、报告、收据、请求规格均记录 SHA；`check_data1.json` 两跑一致。
