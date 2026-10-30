# R204-DATA3 协议：下载并本地核验 AZ/GDSC 2024 公开数据与映射重建（不运行效果）

**版本 v1，FROZEN（在任何核验/重建判定前冻结）** ｜ 2026-10-28 ｜ 执行：drugcomb-auditor（task-171）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-28-az-download-verify/`（`PROTOCOL_DATA3.md`、`download_data3.py`、`verify_data3.py`、`data3_manifest.json`、`data3_verify.json`、`report_data3.md`、`record_data3.md`、`usage_data3.json`、`data_raw/` 或复用既有下载路径）与 `tmp/`；**不改 R202/X1/X2/DATA1/DATA2 产物**。
**纪律**：公开合法下载；不绕过登录/terms；不运行效果/不做响应统计；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；技术三重复≠独立培养；QC 上传日期≠处理日期；阴性写"有界检索/本地核验未发现"不写不存在。

## 0. 目标

用户已明确允许下载公开数据。本任务：
1. 实际取得（或复用本地已下载副本并复算 SHA）AZ/GDSC 2024 公开数据、补充材料、GDSC Combos 公开 summary/docs、公开代码 repo tarball；
2. 本地字段核验；
3. 尝试从公开字段重建 per-(cell,pair,cmatrix) 的 6 occasions×3 technical 结构，并复算 301 exact-18/161 6×3/4,398≥2/68,710 单元/84,055 matrix 记录；
4. 评估公开代码能否生成部分 plate/date/assay 映射；
5. 只做资格重评（能做什么/仍不可做），**不运行效果**；
6. 给下一步（清洗/对账脚本或 DATA1 request spec）。

## 1. 下载/复用（冻结）

- 单文件 ≤500MB；公开 URL；不绕过登录/terms；若已有本地副本（R202/R204 既有下载），复用并**本地复算 SHA**，与既有 receipt/预期值比较；不一致则重新下载并记录。
- 必查清单：
  * Figshare 163378 raw well ZIP（241,088,863 B；预期 SHA `E8CB50F6…D3259`）；
  * Figshare NLME ZIP（57,350,378 B；预期 SHA `AD166FF2…517C90`）；
  * GDSC matrix results（gdsc-007/008/009/010/sandpiper；本地已有）；
  * GDSC2 单药（本地已有，按需）；
  * Europe PMC 补充 ZIP（95,000,784 B；预期 SHA `5CD77E49…3CCC7`）；
  * GDSC Combos 公开 matrix summaries（gdsc-007/008/009/010/sandpiper/anchor colon/pancreas/breast；完整下载）与 Docs（Matrix_documentation/glossary/Screening_documentation）；
  * 5 个公开 repo tarball（eac54、gdscmatrixanalyser、gdscmatrixexplorer、gdscIC50、gdsctools；本地已有，复算 SHA/许可/最后 push）。
- 记录：逻辑名、URL、HTTP 状态、bytes、SHA、许可、local path、`reused_local`/`downloaded`；所有下载回执写 `data3_manifest.json`。

## 2. 本地字段核验（冻结）

- raw well CSV 列名与含义：`BARCODE/SCAN_ID/QC_UPLOAD_DATE/DRUGSET_ID/CELL_ID/cmatrix/lib1_*/lib2_*/conc/intensity/viability` 等；核 `INTENSITY`/`inhibition`/`HSA_excess`/`Bliss_excess` 是否存在（只做存在性/空值计数，不做响应统计）。
- plate QC 文件字段；Table S18/Europe PMC 补充是否有额外映射字段。
- 明确列出**有/无** `experiment/occasion/technical replicate/treatment date/passage/culture` 字段；无则 `field_absent`，不推断。
- 只读元数据/表头/计数；**不读响应值做效应**。

## 3. 映射重建（冻结口径）

- **修正 pair 身份**（C202/C203）：`lib1_drug_id/lib2_drug_id` → canonical names；`(cell_norm, unordered canonical pair)` 作为 pair 单元；matrix 记录 = `(BARCODE,cmatrix)`；7 系按 Table S1 replicate flag。
- 复算（全导出）：
  * `(cell,pair)` 单元数（预期 68,710）；
  * matrix 记录总数（预期 84,055）；
  * 有 ≥2 matrix 的单元（预期 4,398）；
  * 恰好 18 matrix 的单元（预期 301）；
  * 恰好 6 个 **QC_UPLOAD_DATE** 且每日期 3 个 matrix 的单元（预期 161）。
- 重建 attempt：
  * 按 `(cell,pair,cmatrix)` 分组；以 `QC_UPLOAD_DATE` 的 distinct 组作为 candidate occasion 代理；`BARCODE`/`SCAN_ID` 作为 technical/plate 代理；
  * 报告：可分组为 6 日期×3 的单元数/比例；6 日期但每日期非 3 的单元；≤5 日期/≥7 日期；缺失日期/不可重建；
  * **QC_UPLOAD_DATE 只是上传日期，不是处理日期**；`cmatrix` 是 matrix 位置，不是重复标签；不能声称独立培养或官方 6 次 occasion 认证。
- 所有计数从本地 raw ZIP 现场流式扫描；与 X2 口径一致；若与旧值不一致，报告差异并解释（不擅自改旧值）。

## 4. 代码可用性（冻结）

- 只读/解压代码 repo，不执行依赖真实响应的分析。
- `gdscmatrixanalyser/R/pipeline.R`：`make_plate_list` 需要 `screen_data` 的 `DATE_CREATED/SCAN_ID/DRUGSET_ID/CELL_ID/BARCODE`；公开 raw 导出有无这些列？若无 `DATE_CREATED`/`ASSAY`/`DURATION`，不能生成完整 plate/date/assay 映射。
- `gdscmatrixexplorer/models.py`：`project_replicates/all_replicates` 是 same drug pair across projects，**不是** 6×3 technical triplicate/独立培养；不能当 mapping。
- `gdscIC50/R/nlme_fit_prep.R`：代码支持 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION`，但公开导出无这些列。
- `eac54` figure Rmd 只读 matrix results/aggregate replicates，无 mapping。
- 判定：`partial_plate_fields_possible` / `cannot_generate_occasion_technical_mapping` / `missing_fields` 列表；不执行代码。

## 5. 资格重评（只重评，不运行效果）

- 本地实际数据可做（仅描述/结构，不运行）：
  * `qualified_for_same_platform_technical_repeat_structure`: 4,398 个 ≥2 matrix 单元 / 301 exact-18 / 161 6×3 可枚举；可做同平台技术重复的方差/一致性结构设计；
  * `qualified_for_plate_barcode_qc_date_stratified_descriptive`: BARCODE/SN/QC 日期/DRUGSET/cmatrix 可分层描述；
  * `qualified_for_partial_field_mapping`: 可生成 cell/drug/dose/plate/cmatrix/QC date 代理映射（不等于实验/重复/培养）。
- 仍不可做：
  * `still_unavailable_independent_culture`（无 passage/culture/独立培养字段）；
  * `still_unavailable_official_six_occasion_certification`（QC 上传日期不等于处理日；无 official mapping）；
  * `still_unavailable_functional_fig4_5_6_numeric`（公开导出/补充无 caspase/PARP/western numeric）；
  * `still_unavailable_cross_background_transfer/real_decision/mechanism`（无独立培养/功能/目标数据，本轮不运行效果）。
- updated readiness 只写 `dev_only`/`same_platform_only`；**不改 R202/X1/X2/DATA1/DATA2 旧判定**。

## 6. 边界/输出

- 下载公开合法；不绕过登录/terms；不下载 >500MB；不运行效果/不读响应做统计；技术三重复≠独立培养；不称药理/真实决策/迁移/机制/新颖性；不晋升代码。
- 输出：`data3_manifest.json`（下载/复用/SHA）、`data3_verify.json`（字段/重建/代码/资格重评/比例）、`report_data3.md`、`record_data3.md`、`usage_data3.json`。
- 两跑一致（如脚本重算）；JSON 键排序/无时间戳；回执/SHA。
