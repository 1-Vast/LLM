# R204-DATA2 协议：AZ 2024 公开代码/notebook/数据字典定向检索（metadata-only）

**版本 v1，FROZEN（在任何可获取性判定前冻结）** ｜ 2026-10-28 ｜ 执行：drugcomb-auditor（task-167）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-28-az-code-hunt/`（`PROTOCOL_DATA2.md`、`hunt_data2.py`、`hunt_data2.json`、`report_data2.md`、`record_data2.md`、`usage_data2.json`、`receipts/`）与 `tmp/`；**不改 R202/X1/X2/DATA1 产物**。
**纪律**：metadata-only；不拟合效果、不做效应统计、不执行需要真实响应的分析；不绕过登录/terms；技术重复≠独立培养；字段 glossary≠映射；不称新颖性/迁移/决策收益/机制；不晋升代码；阴性写"有界检索未发现"不写不存在。

## 0. 目标

DATA1 已确认：当前 Figshare 导出没有 `BARCODE/cmatrix/CELL_ID→experiment/occasion/technical replicate/treatment date/passage/culture` 映射，也没有 Fig 4/5/6 的 numeric 功能源表；只有 raw 结构、字段 glossary、论文/补充图。本任务定向检索**公开代码/notebook/数据字典**，看是否已有脚本能重建/映射这些字段，或已有功能数值源表；若没有，保留 DATA1 request spec 为优先。

## 1. 检索范围（冻结）

1. **AZ 2024 论文/Data Availability 指向**： `CD-23-0388`/PMC11061612、Figshare project 163378、GDSC Combinations (`https://gdsc-combinations.depmap.sanger.ac.uk/`)。
2. **公开仓库/代码**（合法公开 API）：
   - 论文 Code Availability 两个仓库：`eac54/Large-scale-pan-cancer-screening`（paper analysis code）、`CancerRxGene/gdscmatrixanalyser`（matrix analyser）。
   - GDSC 组织相关仓库：`CancerRxGene/gdscmatrixexplorer`（Dash app + docs）、`CancerRxGene/gdscIC50`（raw data format/nlme）、`CancerRxGene/gdsctools`（GDSC tools）。
   - GitHub repository search（关键词：GDSC combinations pipeline、cmatrix BARCODE、Sandpiper-01、GDSC007-010、combo_well_stats、matrix_well_stats、CD-23-0388、Large-scale pan-cancer screening 等）。
3. **Zenodo**：公开 API 检索相关关键词；只记录结果元数据；不下载无关大文件。
4. **Europe PMC/补充**：论文全文/补充（已有 DATA1 结果）复核代码链接/Data Availability；不再下载已取 ZIP。
5. **GDSC Combos 文档**：DATA1 已下载的 Docs/Glossary；本任务复核其中是否有 mapping/18-replicate 计数。
6. **其他搜索**：`grep.app` 公共代码搜索；记录命中/无命中；必要时用 web_search 找公开仓库（记录 query）。

**不纳入**：需登录/付费的私有仓库、个人通讯、非公开 lab notebook、超出 500MB 的单个文件；不绕过许可。只检查公开代码/文档，不执行依赖真实响应的分析。

## 2. 判定状态（冻结）

- `available_public_code`：公开仓库/脚本/notebook 存在，可取得，含与映射或字段解析相关的代码/文档；记录 URL、许可、last update、文件路径/行锚。
- `available_public_data`：公开仓库/关联发布中含有可下载数据（小数据/文档）；记录 URL/大小/SHA/许可；不把 processed summary 当 raw。
- `requires_author_request`：公开代码/数据不足以给出所需映射/功能数值，需作者/Figshare 重导或补充；保留 DATA1 request spec。
- `not_found_in_public_code`：本次有界检索未在公开代码/notebook 中找到该对象；**不写"不存在"**；记录检索范围/关键词/负结果。
- 可选证据标签：`field_glossary_only`（只有字段 glossary）、`protocol_doc_only`、`combination_replicate_property_only`（如 app 的 all_replicates 只是同药对不同 project 的矩阵，不是技术三重复/实验日）、`paper_analysis_code_only`、`functional_numeric_missing`、`mapping_missing`。

## 3. 必核内容

1. **映射**：公开 README/脚本/notebook 是否定义
   `BARCODE`、`cmatrix`、`CELL_ID`、`SCAN_ID`、`DRUGSET_ID` 与 `experiment/occasion/technical replicate/treatment date/passage/culture` 的对应。
   - 字段 glossary 只给字段语义，不算映射；若代码只读 `DATE_CREATED`/`SCAN_DATE` 但公开数据无该列，记录"代码可解析但数据列/映射未公开"。
   - 若 app 有 `all_replicates`/`replicate` 属性，必须核其分组逻辑（同药对不同 project vs 技术三重复/独立培养）；不得把 `all_replicates` 当实验重复/独立培养。
2. **功能数值**：公开代码/补充是否含 Fig 4/5/6 的 caspase/PARP/western numeric 或绘图源数据（非 PDF）。无则 `not_found_in_public_code`（有界），不推断未做。
3. **协议/18 replicate**：公开 repo 文档是否有 7 系×6 次 technical triplicate/18 replicates 的**映射/官方计数**；只有文字声明不够，必须映射到 barcode/cmatrix/实验记录。
4. **许可/last update/大小/SHA**：每个仓库/下载记录 URL、license（如 NOASSERTION/无 license 如实记录）、last push/update、文件大小/SHA；代码/小数据 ≤500MB/文件。
5. **输出路径**：找到可解析脚本 → 给具体获取/清洗/映射/对账步骤与限制；未找到 → 保留 DATA1 request spec，列新证据与仍需请求项。

## 4. 边界

- 不执行代码分析/不跑 R/Python 依赖真实响应；只读代码/文档/元数据；不拟合效果/不做决策收益/机制。
- 不把 `gdscmatrixexplorer.all_replicates`（同药对不同 project）当技术三重复/独立培养；不把 fields glossary 当 experiment/replicate/date/passage/culture mapping。
- 不绕过 GitHub/Zenodo/Europe PMC 登录/许可；不下载 >500MB 单文件；不把 "not found" 写成 "does not exist"。
- 只写本目录与 tmp/；两跑一致/SHA/回执；不晋升代码、不改旧判定。

## 5. 输出

- `hunt_data2.py` 读 receipts/本地代码清单，写 `hunt_data2.json`（每项状态/证据/URL/许可/行锚/SHA）。
- `report_data2.md`：检索清单、仓库/脚本、映射与功能数值判定表、总体建议、下一步（获取/清洗/重导或回 request spec）。
- `record_data2.md`、`usage_data2.json`、`receipts/`。
