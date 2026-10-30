# record_data3 —— R204-DATA3 下载与本地核验/映射重建执行记录（不运行效果）

2026-10-28 ｜ 执行：drugcomb-auditor（task-171）｜ 工作目录 `D:\MAESTRO`
**范围**：只写 `research/2026-10-28-az-download-verify/`（`PROTOCOL_DATA3.md`、`download_data3.py`、`verify_data3.py`、`data3_manifest.json`、`data3_verify.json`、`build_partial_map.py`、`report_data3.md`、`record_data3.md`、`usage_data3.json`）与 `tmp/`；不改 R202/X1/X2/DATA1/DATA2 产物。
**纪律**：公开合法下载；未绕过登录/terms；不运行效果/不做响应统计；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；技术三重复≠独立培养；QC 上传日期≠处理日期。

## 0. 任务与结论

- 任务：实际下载/复用 AZ/GDSC 2024 公开数据、补充材料、GDSC Combos summaries/docs、公开代码 tarball；本地字段核验；尝试重建 6 occasions×3 technical 结构；本地复算 301/161/4,398/68,710/84,055；重评本地能做什么/仍不能做什么；不运行效果。
- **下载**：26 对象，**18 复用本地 + 8 新下载**，0 error，0 SHA mismatch；raw/NLME/supp/代码 tarball 均本地复算 SHA 与预期一致；GDSC full summaries/anchors 新下载。
- **计数**：本地复算全部复现：
  * **68,710** (cell,pair) 单元；**84,055** matrix 记录；**4,398** 个 ≥2 matrix；**301** 个 exact-18；**161** 个 6 QC 日期×3 matrix（strict distinct barcode/scan 亦 161）。
  * 7 系：**763** 单元；**550,350** well 行；301 exact-18（39.45%）；161 6×3（21.10%）；100% ≥2 matrix。
  * 全导出可重建比例：6×3 **0.234%**；exact-18 **0.438%**；≥2 **6.40%**；6×3 覆盖 2,898 matrix 记录。
- **字段**：raw 有 cell/drug/dose/plate/cmatrix/INTENSITY/inhibition 等；**无** experiment/occasion/technical replicate/treatment date/passage/culture/assay/duration；`SCAN_ID/QC_UPLOAD_DATE` 仅 plate QC 按 barcode 关联（QC 上传日期≠处理日期）。
- **代码**：公开 parser 可生成**部分** cell/drug/dose/plate/cmatrix/QC-date/SCAN 代理映射；**不能**生成 experiment/occasion/technical replicate/treatment date/passage/culture；`gdscmatrixexplorer.all_replicates` 是 same pair across projects，不是 6×3/独立培养。
- **资格重评（未运行效果）**：
  * `qualified_for_same_platform_technical_repeat_structure`（qualified_with_caveats）
  * `qualified_for_plate_barcode_qc_date_stratified_descriptive`（qualified_with_caveats）
  * `qualified_for_partial_field_mapping`（partial）
  * `still_unavailable_independent_culture`
  * `still_unavailable_official_six_occasion_certification`
  * `still_unavailable_functional_fig4_5_6_numeric`
  * `still_unavailable_cross_background_transfer/real_decision/mechanism`
  * updated readiness = **same_platform_structural_only / dev_only**；**不改旧判定**。
- **下一步**：可用 `build_partial_map.py`（本轮未运行）生成 partial structural map；官方 occasion/独立培养/功能 numeric 仍需 DATA1 request spec P0/P1；**不发起独立挑战**；不需要新湿实验来补 mapping。

## 1. 时间线（2026-10-28）

| 步骤 | 内容 |
|---|---|
| 读输入 | task-171；DATA1/2、X1/X2/X3、ERRATA C200/C202/C203/C205/C210 |
| 冻结协议 | `PROTOCOL_DATA3.md` v1 FROZEN（下载/字段/重建/代码/资格重评规则） |
| 下载/复用 | `download_data3.py`：复用 18 个既有本地文件并复算 SHA；下载 8 个 GDSC Combos 完整 matrix summaries/anchors；`data3_manifest.json`；34.6 s |
| 本地核验 | `verify_data3.py`：流式扫描 raw ZIP 3,915,245 行；字段/QC/Table S18；canonical pair 重建；复算计数；代码可用性；资格重评；72.9 s；两跑一致（SHA `36CB4306…3763A`） |
| 下一清洗脚本 | `build_partial_map.py` 写入（本轮仅编译、不运行；字段含 QC-date occasion/technical proxy + `certified_independent_culture=FALSE`） |
| 不运行 | 不运行效果/不做响应统计/不执行仓库代码/不晋升代码/不改旧判定 |

## 2. 下载/复用（摘要）

- **复用本地（复算 SHA 与预期一致）**：raw well ZIP 241,088,863 B `E8CB50F6…D3259`；NLME 57,350,378 B `AD166FF2…517C90`；supp ZIP 95,000,784 B `5CD77E49…3CCC7`；5 matrix results；GDSC2 单药；4 GDSC docs；5 code tarballs。
- **新下载**：GDSC full matrix summaries `gdsc_full_007/008/009/010/sandpiper`（4,240,832/4,726,121/4,365,995/2,299,653/418,215 B）；anchors colon 2,559,389 B、pancreas 2,234,607 B、breast 5,519,032 B；SHA 全记录于 `data3_manifest.json`。
- 26 项；0 error；0 expected-SHA mismatch；≤500MB/文件；未绕过登录/terms。
- 说明：raw/NLME/supp/代码为既有本地下载的复用（R202/R204 数据），本轮**重新计算 SHA**，不是复制旧值。

## 3. 字段/结构

- raw well CSV 列：`PROJECT_ID/PROJECT_NAME/BARCODE/DRUGSET_ID/CELL_LINE_NAME/MASTER_CELL_ID/COSMIC_ID/CELL_ID/TISSUE/CANCER_TYPE/POSITION/INTENSITY/lib1.../lib2.../treatment/cmatrix/... inhibition/HSA/HSA_excess/Bliss_additivity/Bliss_excess`。
- **有**：BARCODE 7,211、CELL_ID、DRUGSET_ID、cmatrix、数字浓度、INTENSITY 3,915,245 非空、inhibition/HSA/Bliss 非空。
- **无**：experiment/occasion/technical_replicate/treatment_date/passage/culture/assay/duration/SCAN_ID/DATE_CREATED；SCAN_ID/QC_UPLOAD_DATE 仅 QC 按 barcode 关联；QC 日期 620 个，flags P=6,884/F=327。
- Table S18：screening matrix-level，含 BARCODE/cmatrix/screen/day1...，无 mapping/caspase/PARP。
- 结论：本地字段只允许 cell/drug/dose/plate/cmatrix/QC 上传日/SCAN 的代理映射；不能生成实验/重复/处理日/passage/culture。

## 4. 复算/重建

- 全导出：68,710 单元；84,055 matrix 记录；4,398 ≥2；301 exact-18；161 6×3；strict 6×3=161；6×3 覆盖 2,898 records。
- 7 系：763 单元；550,350 rows；301 exact-18；161 6×3；per-line 见 report/verify JSON。
- 重建分类：exact 6×3 161；6 日期非 3/日期 116；>6 日期 286；<6 日期 68,147。
- 比例：全导出 6×3 0.2343%，exact18 0.438%，≥2 6.4008%；7 系 6×3 21.10%，exact18 39.45%，≥2 100%。
- 不可认证为官方 6 次实验/技术三重复；QC 上传日≠处理日；技术三重复≠独立培养。

## 5. 代码/资格重评

- `gdscmatrixanalyser` 需 `DATE_CREATED/SCAN_ID` 等；公开 raw 缺 `DATE_CREATED/ASSAY/DURATION`（`SCAN_ID` 可 join QC）；`gdscIC50` 需 `DATE_CREATED/SCAN_DATE/ASSAY/DURATION`；`gdscmatrixexplorer.all_replicates` 是 same-pair-across-project；`eac54` 无 mapping/功能 numeric。
- 可生成部分 plate/cell/drug/dose/QC-date/SCAN 代理映射；不能生成 occasion/technical/独立培养/处理日映射。
- 资格重评见 report §5；**没有运行效果**；updated readiness 只到 same_platform_structural_only/dev_only；不改旧判定。

## 6. 偏离/限制

- 未重下载 raw/NLME/supp（按任务允许复用+复算 SHA）；未运行 `build_partial_map.py`（仅编译）。
- 未执行效果/响应统计/仓库代码；未绕过许可；未下载 >500MB。
- raw 中 `n_drugs` 37 为 ID→名称映射到的 distinct drug names（不是全部 109；缺失名不影响结构计数，但共享药物下界需注意）。
- QC 日期/SCAN 只是代理；不能认证处理日/官方 occasion；技术三重复≠独立培养。
- 只写本目录/tmp；不改 R202/X1/X2/DATA1/DATA2；不晋升代码/不称新颖性/迁移/决策收益/机制。

## 7. 产物/SHA

见 `usage_data3.json`；`data3_verify.json` 两跑一致（SHA `36CB4306…3763A`）；`data3_manifest.json` 记录 26 项 URL/bytes/SHA/license/path。
