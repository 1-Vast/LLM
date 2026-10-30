# R204-DATA1 协议：AZ/GDSC 2024 数据字典与功能数值获取性检查（metadata-only）

**版本 v1，FROZEN（在任何判定前冻结）** ｜ 2026-10-28 ｜ 执行：drugcomb-auditor（task-144）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-28-az-data-acquisition/`（`PROTOCOL_DATA1.md`、`check_data1.py`、`check_data1.json`、`report_data1.md`、`record_data1.md`、`usage_data1.json`、`requests/`）与 `tmp/`；**不改 R202/X1/X2/A/B/D 产物**。
**纪律**：metadata-only；不拟合效果、不做效应统计、不重扫 3.9M wells 做响应分析；不绕过登录/许可；技术三重复≠独立培养；未取得功能数值写"论文报告已做，当前未取得可分析记录"，不写"作者未做/只能新湿实验"；不称新颖性/迁移/决策收益/机制；不晋升代码。

## 1. 目标

R204 主线需要 **AZ/GDSC 2024 的重复/培养独立性映射** 与 **Fig 4/5/6 的 caspase/PARP 功能数值**，以便判断 M2 可做哪些内部功能问题。本轮检查这些数据是否**已经公开可获得**，整理获取清单与请求规格；不做效果、不做资格重评、不改旧判定。

## 2. 检查对象（冻结）

1. **Figshare project 163378**：当前公开项目/文件清单；文件名/大小/类型；README/数据字典/补充表；`BARCODE/cmatrix → experiment/occasion/technical replicate/treatment date/passage/culture` 映射；72h/CellTiter-Glo/Caspase-Glo 元数据；Fig 4/5/6 caspase/PARP 数值源表。另核 plate QC 直接 article（可能不在当前 project listing）。
2. **GDSC Combinations（depmap.sanger.ac.uk）及其他官方页**：`/downloads` 的 matrix summaries/anchor processed、Documentation/Glossary PDF；是否有响应原始下载、字段字典、7 具名系×6 实验/18 replicate 的官方计数/映射；是否需登录/terms。其他官方来源（GDSC/Cell Model Passports/Figshare 117084 等）只记录与 AZ 2024 的关系。
3. **Europe PMC 补充材料**：ZIP 成员/Table S1–S18 清单与表头/内容摘要；哪些含重复/功能/协议字段；Supplementary Figures PDF 是否只有图、无 numeric 表。
4. **R204 所需补充项**：给作者/Figshare 的请求规格（字段/格式/范围/优先级）与替代路径（重导映射、notebook/代码生成映射、补充源数据）。

## 3. 状态定义（冻结）

对每个检查项给出且仅给出一个状态：

- `available_in_listing`：当前**公开清单/文件**中已存在，可直接取得（无需登录/terms 或已公开挂载）；若有内容限制（如只有图像/字段字典但不含映射），在 `content_scope` 说明。
- `available_but_restricted`：公开页面指向/声明存在，但需要登录、terms、申请或权限（本轮不绕过）；记录限制与可公开替代。
- `not_in_listing`：**当前公开清单/已取得文件中没有该文件/字段/表**；只记录"not in listing"，**不推断作者未做、不推断不存在**。
- `unclear`：清单状态/归属/内容无法由公开信息判定（如 article 直链 200 但不在 project listing、页面 SPA 未加载）。
- `content_scope` 可选：`field_glossary_only`、`processed_summary_only`、`pdf_figure_only`、`raw_well_structure`、`protocol_docs_general` 等。

## 4. 检查方法（冻结）

- 用公开 API/网页/合法下载；不提交账号/不绕过 terms；单文件 ≤500 MB；只取清单/表头/小文件/文档；大文件只 HEAD/大小，不下载做效应。
- Figshare：project articles API + article details（文件名/大小/类型/描述）；对 raw/NLME ZIP 检查内部成员清单（已下载）；对 plate QC 检查直接 article 状态与 project listing 差异。
- GDSC：Dash `/downloads` 页面（matrix/anchor tabs）与 Documentation/Glossary PDF；HEAD matrix summary 下载；检查文本中 replicate/18/experiment/passage/date/72h/CellTiter 关键词；不登录。
- Europe PMC：supplementaryFiles ZIP 成员/表头/行列摘要；`Supplementary_table_legend` 说明；PDF 仅确认文件类型/页数，不用图像做定量。
- 每个 URL/文件记录 status/bytes/SHA（大文件 HEAD 记 content-length）；回执写 `receipts/`。
- 两跑一致；`check_data1.json` 键排序、无时间戳；不读响应值做效应。

## 5. 请求规格（冻结要求）

若缺失，按以下优先级整理（详见 `requests/data_request_spec.json`）：
- **P0**：`BARCODE/cmatrix → experiment/occasion/technical replicate/treatment date/passage/culture` 映射；7 具名系 ×6 实验 ×3 technical replicate 的官方计数/映射；字段单位/空值/QC 规则。
- **P0**：Fig 4E/F、5C/D、6C–E 的 caspase/PARP/western 原始数值/定量源表（细胞/药物/剂量/时间点/重复/单位/抗体/图像）；不是仅 PDF 图。
- **P1**：72h/CellTiter-Glo 2.0/Caspase-Glo 3/7/QVD 与导出批次/板的逐键协议映射。
- **P1**：Figshare 各 dataset 的 README/数据字典与代码 notebook（`gdscmatrixanalyser` 等）以生成/校验映射；`CELL_ID` 的 stock expansion 语义。
- **P2**：补充图数值源表/原始扫描强度与 plate/well/scan 元数据（若可获得）。
替代路径：作者重导映射/补充数据；Figshare/Europe PMC 补充提交；用公开 notebook 从 `BARCODE/SCAN_ID/DRUGSET_ID/cmatrix` 生成候选映射（需作者确认语义）；不写"只能新湿实验"。

## 6. 边界

- 只做获取性检查；不重算 G1–G7、不改 R202/X1/X2 判定；不拟合/不训练/不晋升代码；不称新颖性/迁移/决策收益/机制。
- 技术三重复≠独立培养；补充 PDF 图≠numeric 功能数据；`available_in_listing` 不等于可分析（content_scope 说明）。
- 不绕过登录/terms；不把 SPA 未加载/直链 200 当作已获取；`not_in_listing` 不是"未做/不存在"。
- 只写本目录与 tmp/；回执/SHA/两跑一致。

## 7. 输出

- `check_data1.py` 只读 receipts/本地清单/文档，写 `check_data1.json`（每项状态/证据/内容范围/SHA）。
- `report_data1.md`：清单复核、逐项可获取性、总体"当前可获取性"、下一步（获取/清洗/重导/另立协议）、请求规格摘要。
- `record_data1.md`、`usage_data1.json`、`receipts/`、`requests/data_request_spec.json`（或 md）。
