# record_data2 —— R204-DATA2 AZ 2024 公开代码/notebook/数据字典定向检索（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-167）｜ 工作目录 `D:\MAESTRO`
**范围**：只写 `research/2026-10-28-az-code-hunt/`（`PROTOCOL_DATA2.md`、`hunt_data2.py`、`hunt_data2.json`、`report_data2.md`、`record_data2.md`、`usage_data2.json`、`receipts/`）与 `tmp/`；不改 R202/X1/X2/DATA1 产物。
**纪律**：metadata-only；不拟合效果/不做响应统计；不执行依赖真实响应的代码；不绕过登录/许可；技术三重复≠独立培养；字段 glossary≠映射；不称新颖性/迁移/决策收益/机制；不晋升代码；有界检索阴性写"未发现"不写不存在。

## 0. 任务与结论

- 任务：定向检索 AZ 2024 公开代码/notebook/数据字典，寻找 `BARCODE/cmatrix/CELL_ID/SCAN_ID/DRUGSET_ID→experiment/occasion/technical replicate/treatment date/passage/culture` 映射脚本，以及 Fig 4/5/6 caspase/PARP/western numeric 源数据。
- **结论**：**公开代码存在，但未找到所需映射或功能数值**；**保留 DATA1 request spec 为优先**；**不建议独立挑战**；**不需要新湿实验来补 mapping**。
- 找到的公开代码：
  1. `eac54/Large-scale-pan-cancer-screening`（论文图/分析 Rmd；**无 license 声明**；pushed 2024-01-03；tarball 23,922 B SHA `58A5C869…FE8F`）；
  2. `CancerRxGene/gdscmatrixanalyser`（matrix parser/plate objects；**AGPL-3.0**；pushed 2023-01-09；23,643 B SHA `84952431…E64A`）；
  3. `CancerRxGene/gdscmatrixexplorer`（Dash app/models/field glossary/protocol doc；**NOASSERTION**；pushed 2024-02-15；5,068,735 B SHA `8D954567…B086A`）；
  4. `CancerRxGene/gdscIC50`（raw format/parser；**GPL-3.0**；pushed 2023-07-10；1,207,161 B SHA `66B1C464…23E6`）；
  5. `CancerRxGene/gdsctools`（general GDSC tools；NOASSERTION；pushed 2022-01-06；6,310,983 B SHA `441B9CE5…A9B9`）。
- **未找到**：mapping 脚本/README/notebook；**official per-barcode 18-replicate mapping**；**functional numeric**；README/data dictionary beyond field glossary。
- **关键区别**：`gdscmatrixexplorer.all_replicates` 是 same drug pair across projects，不是论文的 6 occasions×3 technical triplicate/独立培养；`gdscmatrixanalyser`/`gdscIC50` 可解析 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION`，但当前公开 AZ 导出没有这些列/没有公开 mapping 数据。

## 1. 时间线（2026-10-28）

| 步骤 | 内容 |
|---|---|
| 读输入 | task-167；DATA1 `report_data1.md`/request spec；X1/X2/X3；C200/C202/C203/C205；R204 BRIEF |
| 冻结协议 | `PROTOCOL_DATA2.md` v1 FROZEN（检索范围/状态定义/边界）；之后未改 |
| 仓库检索 | GitHub API：Code Availability 两 repo + `CancerRxGene` org repos + repository search；下载公开 tarball（均≤5.1MB）并列文件树/SHA/许可/最后 push |
| 代码检查 | 提取 tarball；grep mapping/date/replicate/functional 关键词；读 `pipeline.R`、`classes.R`、`models.py`、`nlme_fit_prep.R`、`Supplementary Figure 1.Rmd`；读 `screen_information_20190211.pdf` 文字声明 |
| 其他来源 | Zenodo/GitHub search/grep.app/Europe PMC/GDSC Combos 检索（GitHub search 有速率限制；记录 0 命中/边界） |
| 判定/输出 | `receipts/code_hunt_evidence.json`；`hunt_data2.py` → `hunt_data2.json`；`report_data2.md`/本记录/`usage_data2.json` |
| 不运行 | 不执行仓库代码/不读响应做效应/不拟合/不训练/不晋升代码 |

## 2. 关键证据/行锚

- **`gdscmatrixanalyser/R/pipeline.R:56`**：`plate_date = lubridate::ymd(unique(.x$DATE_CREATED))`；`SCAN_ID`/`DRUGSET_ID`/`CELL_ID`/`BARCODE`；无 occasion/technical replicate/passage/culture。
- **`gdscmatrixanalyser/R/classes.R`**：plate class 字段 barcode/plate_date/scan_id/drugset_id/cell_line/cmatrix_list；无重复/培养字段。
- **`gdscmatrixexplorer/models.py:70-97`**：`Combination.replicates_query` 只按 `lib1_id/lib2_id`（含反方向）跨 project；**不是实验重复/技术三重复**。
- **`models.py:195-224`**：`project_replicates`/`all_replicates_query` 为同 model/project 下同药对的 MatrixResult；**不是论文 6×3/独立培养**。
- **`pages/documentation.py:83`**：`cmatrix` 仅为 "Identifier for a combination matrix within a drug set"（field glossary，非映射）。
- **`gdscIC50/R/nlme_fit_prep.R:122,326-327`**：代码支持 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION` 等 raw 列；公开 AZ 导出无这些列。
- **`eac54/Supplementary Figure 1.Rmd:67/81`**：读 matrix results 后 "Aggregate replicates by mean"；无 mapping/functional numeric。
- **`screen_information_20190211.pdf` page 1**（public repo doc）："A subset of cell lines (7) … technical triplicate on six occasions … 18 replicates … provided all plates meet quality controls"；also 72h/CellTiter-Glo；**只是设计声明，无 per-barcode mapping**。
- **功能关键词扫描**：5 个 repo 中 `caspase/PARP/apoptosis/western/cleaved` 0 命中；无 numeric source data。

## 3. 判定（`hunt_data2.json`）

- `available_public_code`：5 个 repo（含 parser/app/field glossary/protocol doc）；license/最后更新/SHA 已记录。
- `available_public_data`：Figshare raw data（DATA1；无 mapping）。
- `not_found_in_public_code`（有界）+ `requires_author_request`：mapping、official per-barcode 18 mapping、functional numeric、README/data dictionary beyond glossary。
- 无 `available_but_restricted` 项（本次公开 GitHub/Zenodo/Europe PMC 未遇登录/受限；Zenodo/GitHub search 限速为检索限制，不是 data restriction）。
- 保留 DATA1 `requests/data_request_spec.json`；本轮不生成新请求规格，仅引用并补充"若有 raw screen_data 可用 parser 校验日期/assay"。

## 4. 下一步

1. 继续 `DATA1` P0/P1 请求（mapping、per-barcode 18 映射、Fig4/5/6 source data、README）；
2. 若作者给带 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION` 的 raw screen_data，可用 `gdscmatrixanalyser`/`gdscIC50` 构造 plate 对象/核对日期；**仍需作者 occasion/technical replicate/passage/culture 标签**；
3. **不得**用 `gdscmatrixexplorer.all_replicates` 当 6×3/独立培养；**不得**用 field glossary 当 mapping；
4. 若 mapping/功能数值到位，另立任务做清洗/对账/资格重评；本轮不改旧判定；
5. 不写"只能新湿实验"/"不存在"；`not_found_in_public_code` 是本任务有界检索结果。

## 5. 偏离/限制

- GitHub unauth repository search 有速率限制；GitHub code search 未用登录接口，因此覆盖有限；未做全网/全部 GitHub 代码搜索。
- Zenodo 宽关键词返回大量无关记录；未做精确全文检索；`combo_well_stats/GDSC007/gdscmatrixanalyser` 返回 0；不作为不存在。
- 未执行仓库代码；未读响应做效应；未下载 >500MB；未绕过任何登录/许可。
- 仓库许可：eac54 无 license 声明、gdscmatrixexplorer/gdsctools 为 NOASSERTION——公开可读但不等于可自由再分发；使用前需确认许可。
- 只写本目录/tmp；不改 R202/X1/X2/DATA1；不晋升代码/不称新颖性/迁移/决策收益/机制。

## 6. 产物/SHA

见 `usage_data2.json`；`hunt_data2.json` 两跑一致；receipts/仓库/SHA 齐全。
