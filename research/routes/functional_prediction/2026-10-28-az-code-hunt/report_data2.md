# R204-DATA2 报告：AZ 2024 公开代码/notebook/数据字典定向检索（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-167）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_DATA2.md](PROTOCOL_DATA2.md)（v1 FROZEN）
**产物**：[hunt_data2.py](hunt_data2.py)、[hunt_data2.json](hunt_data2.json)、`receipts/`（仓库/代码/搜索/文档回执）、[report_data2.md](report_data2.md)、[record_data2.md](record_data2.md)、[usage_data2.json](usage_data2.json)。
**纪律**：metadata-only；不拟合效果/不做响应分析；不执行依赖真实响应的代码；不绕过登录/许可；技术三重复≠独立培养；字段 glossary≠映射；不称新颖性/迁移/决策收益/机制；不晋升代码；**有界检索未发现 ≠ 不存在**。

## 0. 结论（先行）

**公开代码存在，但没有找到所需的 mapping 或 Fig 4/5/6 numeric 功能源数据。**

- **`available_public_code`**：
  1. `eac54/Large-scale-pan-cancer-screening`（论文图/分析 Rmd；**未声明 license**；pushed 2024-01-03）；
  2. `CancerRxGene/gdscmatrixanalyser`（matrix parser/plate objects；**AGPL-3.0**；pushed 2023-01-09）；
  3. `CancerRxGene/gdscmatrixexplorer`（Dash app/models/glossary；**NOASSERTION**；pushed 2024-02-15）；
  4. `CancerRxGene/gdscIC50`（raw format/parser；**GPL-3.0**；pushed 2023-07-10）；
  5. `CancerRxGene/gdsctools`（general GDSC tools，非 AZ 特定；NOASSERTION；pushed 2022-01-06）。
- **`available_public_data`**：Figshare 163378 raw well ZIP/matrix summaries（DATA1 已取得；不是 mapping/功能数值）。
- **`not_found_in_public_code`（有界）+ `requires_author_request`**：
  - `BARCODE/cmatrix/CELL_ID/SCAN_ID/DRUGSET_ID → experiment/occasion/technical replicate/treatment date/passage/culture` 的脚本/README/notebook；
  - 7 系×6 次×3 technical replicate 的**逐 barcode/cmatrix 官方映射/对账**；
  - Fig 4/5/6 的 caspase/PARP/western **numeric/source data**；
  - 超过 field glossary 的 README/数据字典。

**关键区别（C205）**：
- `gdscmatrixexplorer` 的 `all_replicates`/`project_replicates` 是**同一药对在不同 project 的矩阵**（same pair across projects），**不是**论文的 6 次 occasion×3 technical triplicate，也不是独立培养；不能拿来当重复/独立培养映射。
- `gdscmatrixanalyser`/`gdscIC50` 可以解析 `DATE_CREATED`、`SCAN_DATE`、`ASSAY`、`DURATION` 等**若数据中有这些列**；当前公开 AZ 导出没有这些列，也没有公开 mapping 文件；因此是"代码可解析、数据/映射未公开"，不是"没有代码"。
- 公共 repo 文档 `screen_information_20190211.pdf` 确有 7 系/6 occasions/technical triplicate/18 replicates + 72h/CellTiter-Glo 的文字声明，但**没有逐 barcode/cmatrix 映射**；不能当 mapping。

**建议**：**保留 DATA1 request spec 为优先**，发 P0/P1 请求（映射/功能源数据）；**不发起独立挑战**；**不需要新湿实验来补 mapping**；若作者提供 mapping/源数据，再用公开 parser 做清洗/对账。若拿不到，R204 数据 readiness 保持 open，不改旧判定。

## 1. 检索清单（有界）

| 来源 | 结果 |
|---|---|
| GitHub 官方论文 Code Availability 链接 | `eac54/Large-scale-pan-cancer-screening`（9 files，23,922 B tarball，SHA `58A5C869…FE8F`，无 license）与 `CancerRxGene/gdscmatrixanalyser`（11 files，23,643 B，SHA `84952431…E64A`，AGPL-3.0）均可公开取得 |
| GitHub `CancerRxGene` org（11 repos） | 发现 `gdscmatrixexplorer`（5,068,735 B tarball，SHA `8D954567…B086A`）、`gdscIC50`（1,207,161 B，SHA `66B1C464…23E6`）、`gdsctools`（6,310,983 B，SHA `441B9CE5…A9B9`）等；均公开 |
| GitHub repository search | `gdscmatrixanalyser`/`gdscmatrixexplorer` 命中；精确关键词如 `combo_well_stats`/`Sandpiper-01 GDSC`/`CD-23-0388` 返回 0；搜索受 API 速率限制影响，已记录 |
| Zenodo API | `combo_well_stats`/`GDSC007`/`gdscmatrixanalyser` 返回 0；宽关键词返回大量无关记录；**没有精确 AZ-2024 code/dictionary hit**（有界） |
| grep.app | `combo_well_stats`/`matrix_well_stats`/`cmatrix BARCODE` 均 0 hits |
| Europe PMC | 论文 Code Availability 指向 GitHub 两 repo；补充无 code/notebook；DATA1 已核 supplement |
| GDSC Combos | DATA1 已核公开 matrix summaries/docs；本任务复核 `screen_information_20190211.pdf`（public repo）文字设计声明；无 mapping |

所有代码 tarball 均 <500MB；许可/最后更新/SHA 在 `receipts/code_hunt_evidence.json` 与 `hunt_data2.json`。

## 2. 代码/README/notebook 是否给出 mapping？

### 2.1 `eac54/Large-scale-pan-cancer-screening`
- `README.md:5` 只写 "Data is available via Figshare project 163378"；无字段字典/mapping。
- `Supplementary Figure 1.Rmd:67/81` 读取 matrix results 后 "Aggregate replicates by mean"，但没有定义 experiment/occasion/technical replicate/date/passage/culture；无 functional numeric 代码。
- `Figure 1.Rmd`/`Figure 3.Rmd`/其它 Rmd 为 figure/analysis code；无 mapping。
- **判定：`available_public_code`，`paper_analysis_code_only`；license 未声明。**

### 2.2 `CancerRxGene/gdscmatrixanalyser`
- `R/classes.R` 的 `plate` class 支持 `barcode/plate_date/scan_id/drugset_id/cell_line/intensities/mean.../cmatrix_list`；
- `R/pipeline.R:56` `make_plate_list()` 从输入 `screen_data` 取 `DATE_CREATED` → `plate_date`，并取 `SCAN_ID`、`DRUGSET_ID`、`CELL_ID`、`BARCODE`；
- 但**没有** experiment/occasion/technical-replicate/passage/culture 字段；`DATE_CREATED` 只是输入列，**当前公开 AZ 导出没有该列**。
- **判定：`available_public_code`（parser/plate objects），但不能据此生成所需 mapping；需要作者提供带 `DATE_CREATED`/`SCAN_ID` 的 screen_data。**

### 2.3 `CancerRxGene/gdscmatrixexplorer`
- `README.md` 为 Dash app；`pages/documentation.py:83` 定义 `cmatrix` 为 "Identifier for a combination matrix within a drug set"（field glossary，不是重复/实验标签）。
- `models.py:70-97` `Combination.replicates_query` 仅按 `lib1_id/lib2_id`（含反方向）跨 project 查同药对组合；
- `models.py:195-224` `project_replicates`/`all_replicates_query` 为同一 model/project 下同药对的 MatrixResult；**不是六次 occasion×三 technical replicate，也不是独立培养**；不能当 mapping。
- 公共 repo 的 `downloads/screen_information_20190211.pdf`（page 1）含原文：
  > "A subset of cell lines (7) are included in both cell line sets and are screened in technical triplicate on six occasions … This generates 18 replicates for every compound across each of the seven lines provided all plates meet quality controls …"
  以及 72h/CellTiter-Glo 2.0；但**只有设计声明，没有逐 barcode/cmatrix 的 occasion/replicate 表**。
- **判定：`available_public_code`（app/field glossary/protocol doc）；`combination_replicate_property_only` 不是技术三重复 mapping。**

### 2.4 `CancerRxGene/gdscIC50`
- `R/nlme_fit_prep.R:122` 选择 `SCAN_ID/BARCODE/RESEARCH_PROJECT/DATE_CREATED/DRUGSET_ID/CELL_LINE_NAME/CELL_ID/COSMIC_ID/POSITION/TAG/DRUG_ID/CONC/INTENSITY`；
- `R/nlme_fit_prep.R:326-327` 选择 `DATE_CREATED/SCAN_DATE/CELL_ID/.../SEEDING_DENSITY/DRUGSET_ID/ASSAY/DURATION`；
- 代码支持这些列，但**公开 AZ 导出没有 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION`**；没有公开 mapping 数据。
- **判定：`available_public_code`（raw format/parser）；数据/mapping `requires_author_request`。**

### 2.5 `CancerRxGene/gdsctools`
- 通用 GDSC tools/ANOVA/回归；与 AZ 2024 matrix field mapping/functional numeric 无直接关系。
- **判定：`available_public_code`，非 AZ 特定。**

## 3. 功能数值（Fig 4/5/6 caspase/PARP/western）

- 在 5 个公开 repo 的代码/README/Rmd 中扫描 `caspase|PARP|apoptosis|western|cleaved`：
  - 0 命中（`gdscIC50/vignettes/gdscIC50.Rmd` 只有 "culture" 词，不是功能数据）。
- 公共 repo 无 caspase/PARP/western numeric/source-data 文件；无 figure source workbook。
- 论文/Supplementary Figures PDF 有图；**not found in public code ≠ 作者未做**。
- **判定：`not_found_in_public_code`（有界）+ `requires_author_request`；DATA1 P0 REQ-FUNC-01 保留。**

## 4. 逐项判定

| 项目 | 状态 | 证据/说明 |
|---|---|---|
| 论文分析代码 `eac54` | `available_public_code` | 公开；figure/analysis only；无 license；无 mapping/functional numeric |
| matrix parser `gdscmatrixanalyser` | `available_public_code` | AGPL-3.0；plate objects/DATE_CREATED support；无公开 mapping 数据 |
| matrix explorer `gdscmatrixexplorer` | `available_public_code` | NOASSERTION；app/models/field glossary；`all_replicates` 不是技术三重复 mapping |
| `gdscIC50` raw format | `available_public_code` | GPL-3.0；支持 DATE_CREATED/SCAN_DATE/ASSAY/DURATION 字段，但公开导出无这些列 |
| `gdsctools` | `available_public_code` | 非 AZ 特定，无 mapping/functional |
| Figshare raw data | `available_public_data` | DATA1 raw well ZIP/matrix summaries；无 mapping |
| protocol doc 7 系/18 rep | `available_public_code` | public repo `screen_information` page 1 文字声明；非 per-barcode mapping |
| field glossary | `available_public_code` | `cmatrix`=matrix identifier；不是 experiment/replicate label |
| **mapping to experiment/occasion/technical replicate/treatment date/passage/culture** | **`not_found_in_public_code`** + `requires_author_request` | 无公开脚本/README/notebook；DATA1 request spec 优先 |
| **official per-barcode 18-replicate mapping** | **`not_found_in_public_code`** + `requires_author_request` | 只有文字声明；无逐 barcode/cmatrix 映射/对账 |
| **functional numeric Fig4/5/6** | **`not_found_in_public_code`** + `requires_author_request` | 代码/数据均未发现；保留 DATA1 REQ-FUNC-01 |
| README/data dictionary beyond glossary | **`not_found_in_public_code`** + `requires_author_request` | 只有 field glossary/general docs |

## 5. 下一步（若找到脚本/字典 / 未找到）

**未找到 mapping/功能数值（本任务结论）**：保留 DATA1 request spec 为优先，不发起独立挑战。具体：
1. 按 `research/2026-10-28-az-data-acquisition/requests/data_request_spec.json` 发 P0/P1 请求（mapping、per-barcode 18 映射、Fig4/5/6 source data、README）；
2. 若作者提供带 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION` 的 raw screen_data：可用 `gdscmatrixanalyser` 的 `make_plate_list()`/`gdscIC50` 构造 plate 对象并核对日期/assay；**仍需作者提供 occasion/technical replicate/passage/culture 标签**，parser 不能凭空生成；
3. 若使用 `gdscmatrixexplorer`：只可用其 field glossary/app 解析 matrix fields；**不得把 `all_replicates` 当作 6×3 technical triplicate 或独立培养**；
4. 若 mapping/功能数值到位：先清洗/映射/对账，再另立任务更新 R204 readiness / 资格重评；本轮不做；
5. **不把"未找到"写成"不存在"；不写"只能新湿实验"**；mapping/source data 通过作者/公开仓库补取，不是必须重做实验。

## 6. 边界/复现

- metadata-only；未执行仓库代码/未跑 R/Python 分析；不拟合效果/不做响应统计；不称新颖性/迁移/决策收益/机制；不晋升代码；不改 R202/X1/X2/DATA1 判定。
- 代码/小数据均 ≤500MB；tarball SHA/许可/最后 push 记录于 `receipts/` 与 `hunt_data2.json`；未绕过 GitHub/Zenodo/Europe PMC 登录/许可。
- 有界检索：受 GitHub unauth search rate limit 影响，未做全 GitHub 代码搜索（code search 需登录），未做跨库引文追踪；`not_found_in_public_code` 仅本任务范围。
- 复现：
  ```powershell
  cd D:\MAESTRO\research\2026-10-28-az-code-hunt
  & D:\anaconda\envs\maestro\python.exe hunt_data2.py
  ```
- `hunt_data2.json` 键排序、无时间戳；两跑一致；SHA 见 `usage_data2.json`。
