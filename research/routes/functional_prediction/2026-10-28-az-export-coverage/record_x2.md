# record_x2 —— R203-X2 AZ 导出覆盖追踪执行记录（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-127）｜ 工作目录 `D:\MAESTRO`
**范围**：只写 `research/2026-10-28-az-export-coverage/`（`PROTOCOL_X2.md`、`audit_x2.py`、`audit_x2.json`、`report_x2.md`、`record_x2.md`、`usage_x2.json`、`receipts/`）与 `tmp/`；不改 R202-Q1 产物、A/B/D 线产物、其它目录/INDEX/git。
**纪律**：metadata-only；不拟合效果、不重扫 3.9M wells 做效应、不重算认证 68 A0 键；不绕过登录/许可；不称新颖性/迁移/决策收益/机制；不晋升代码；**区分"实验未做"与"当前导出未取得"**。

## 0. 任务与总体结论

- 目标：追踪 AZ/GDSC 2024（Cancer Discovery CD-23-0388；PMC11061612）论文明确报告的 **72 h/CellTiter-Glo 2.0、7 个具名细胞系×6 次实验技术三重复、部分组合 apoptosis/caspase/PARP 验证** 在当前公开导出/ZIP 中的覆盖；判定 `available_analyzable` / `present_but_not_analyzable` / `not_obtained` / `not_done_by_authors`（仅明确证据）/ `unclear`。
- **结论**：当前导出是**部分覆盖**；**R202 的 "0 repeats" 是导出键造成的假 0，应撤回/降级**；7 个具名系有重复 matrix 记录（301 个 exact-18；161 个可归为 6 QC 日期×3 matrix），但缺显式实验/重复/培养标签、协议字段、功能 numeric 数据；未取得项均写"论文报告已做，当前未取得可分析记录"，**不写"只能新湿实验"**。
- 与 R202：68 A0 键未重算/未认证；R202 的 `units_with_ge2_platforms=0` 来自 `scan_azeraw.py` 用 `lib1_drug`/`lib2_drug`（含 barcode 的字符串）作 pair 身份；本轮用 `lib1_drug_id`/`lib2_drug_id` + `BARCODE`/`cmatrix` 重核 7 系结构。R202 的 `not_qualified` 本轮不重做；G4 的 "0 repeats" 依据应撤回/降级，剩余缺口是显式标签/协议/功能 numeric；是否影响 Q1 资格需另立重评。

## 1. 时间线（2026-10-28）

| 步骤 | 内容 |
|---|---|
| 读任务/背景 | task-127；`research/2026-10-28-blocked-conclusion-review/report.md` §5；`research/2026-10-27-agent-cell-colearning/ERRATA_R201_R202.md`（C200）；`research/2026-10-27-external-resource-hunt/{report_x1.md,hunt_x1.json}`；本地 PMC11061612 JATS 与 `primary_passages.json` |
| 冻结协议 | 写 `PROTOCOL_X2.md`（v1 FROZEN；状态 taxonomy、论文锚点、追踪项、R202 差异规则、措辞边界）；之后未改阈值/状态定义 |
| 补充材料 | Europe PMC `supplementaryFiles` 合法接口取 95,000,784 B ZIP（Table S1–S18 + Supplementary figures PDF）；本地只读；未绕过 |
| 导出结构侦察 | `tmp/recon_x2.py`、`tmp/recon_x2b.py`、`tmp/recon_x2c.py`、`tmp/recon_x2d.py`：raw well ZIP 的 7 系/重复 matrix/QC 日期/剂量条件结构；`tmp/func_x2.py`：Table S18 中功能细胞/组合覆盖；`tmp/inspect_supp.py`、`tmp/build_receipts_x2.py`：补充表/项目清单/回执 |
| 审计/报告 | `audit_x2.py` → `audit_x2.json`；写 `report_x2.md`、本记录、`usage_x2.json`；两跑一致 |
| 本轮不做 | 不重扫全部 3.9M wells 做效应；不重算 A0 68；不改 R202 结论；不晋升代码；不重开 A/B/D 线 |

## 2. 关键发现/证据

### 2.1 论文声明（本地 JATS；`receipts/paper_claims.json`）
- P1/P2：S15 "Screening"：72 h 处理；CellTiter-Glo 2.0（Promega）；XML line 8。
- P3/P3b/P3c：S17 "Quality Control"：A375, HT-29, PC-14, U-2-OS, SW620, C32, MHH-ES-1 在 6 次实验中 technical triplicate；每 compound 18 replicates（provided all plates pass QC）；XML line 8。
- P4/P5/P6：Fig 4E–F（selumetinib+venetoclax/AZD5991，NOMO-1，cleaved PARP/caspase-3，24–72 h）；Fig 5C–D（venetoclax+AZD2811，时间依赖 apoptosis、QVD）；Fig 6C–E（capivasertib+AZD5991，AN3-CA，apoptosis/caspase/PARP、QVD）；XML line 8。
- P7：Data Availability：screening data → Figshare project 163378；combination response → GDSC Combinations website；XML line 11。

### 2.2 当前导出覆盖（`receipts/export_inventory.json`、`structure_7lines_repeats.json`）
- Figshare project 163378 共 12 个 dataset：dose response models、raw well stats（7×7）、GDSC007–010/Sandpiper matrix results、Overall/Significant ANOVA、GDSC2 single agent、Plate QC×2；**无 functional dataset、无 experiment/replicate/passage 映射 dataset**。
- raw well ZIP 列：`PROJECT_ID/PROJECT_NAME/BARCODE/DRUGSET_ID/CELL_LINE_NAME/MASTER_CELL_ID/COSMIC_ID/CELL_ID/TISSUE/CANCER_TYPE/POSITION/INTENSITY/lib1_dose/lib1_drug_id/lib1_conc/lib2_dose/lib2_drug_id/lib2_conc/treatment/cmatrix/...`；**缺** `replicate/experiment/batch/date/treatment_date/passage/culture/assay/exposure/timepoint`。
- plate QC：2 文件共 7,211 barcodes；`SCAN_ID/QC_FLAG/QC_UPLOAD_DATE`；QC 上传日期≠处理日期。
- 补充 ZIP：32 成员；**Table S1** 的 `Replicate Cell Line=Yes` 恰 7 系；**Table S18** 84,055 行/754 细胞/7,211 barcodes（matrix-level 汇总，screening，不是功能）；**Supplementary figures PDF** 55 MB（图像级）；无 caspase/PARP numeric 表。

### 2.3 7 系重复覆盖
- 7 系各 109 pairs；合计 **550,350 well 行**；每 pair matrix 记录 3–38 个；**301 个 pair-line 单元恰 18 matrix**；**161 个可归为 6 个 QC 上传日期×每日期 3 matrix**（A375 13、C32 27、HT-29 13、MHH-ES-1 22、PC-14 51、SW620 0、U-2-OS 35）。
- 示例：A375 一个 pair 的 18 个 matrix = 6 QC 日期×3 matrix；PC-14 51/109 pairs 呈此形态；SW620 的 exact-18 有 15 个但未按 6×3 对齐（额外/缺失矩阵）。
- 含义：**重复记录存在且可按 barcode/cmatrix/QC 日期枚举**；但缺显式 experiment/replicate 标签、处理日期、passage/独立培养；不能把 QC 上传日期直接当处理日期，也不能把技术三重复当独立培养。
- R202 假 0：R202 `scan_azeraw.py` 中 `lib1_drug`/`lib2_drug` 值形如 `38690_L56`（含 barcode），pair 身份被 barcode 化；同一 pair 跨 barcode 被拆开 → `units_with_ge2_platforms=0`。R202 `azeraw_entities.py` 用 ID 做 Jaaks 重叠，但未重做重复计数。**本轮不重算 A0 68，不认证，不改 R202 结论；只纠正 G4 0 repeat 归因。**

### 2.4 功能子集
- NOMO-1 / AN3-CA 均出现在 Table S18（NOMO-1：107 matrix 行/106 pairs；AN3-CA：80/80）；三个 target 组合（selumetinib+venetoclax、selumetinib+AZD5991、capivasertib+AZD5991）各 **1 个 matrix 行**（screening viability，非功能读数）。
- 功能验证（Fig 4E/F、5C/D、6C–E）只在论文图/Supplementary Figures PDF；**无 numeric 数据/源表**。状态：功能图 `present_but_not_analyzable` (`present_but_unparsed`)，功能 numeric `not_obtained` (`not_in_export`)；措辞"论文报告已做，当前未取得可分析记录"。

## 3. 状态判定表（最终）

| 项目 | 状态 | 证据标签 |
|---|---|---|
| P1 72 h exposure | `not_obtained` | `not_in_export` |
| P2 CellTiter-Glo 2.0 | `not_obtained` | `not_in_export` |
| P3 7 个具名系 | `available_analyzable` | `parsed_export_records` |
| P4a 重复 matrix/barcode 记录 | `available_analyzable` | `parsed_export_records` |
| P4b 6 次实验×技术三重复显式标签 | `present_but_not_analyzable` | `metadata_missing` |
| P4c 独立培养/日/passage | `not_obtained` | `not_in_export` |
| P5 板/孔/matrix/剂量字段 | `available_analyzable` | `parsed_export_records` |
| P6 实验日期/批次标签 | `present_but_not_analyzable` | `metadata_missing` |
| P7 functional readout（图/补充图） | `present_but_not_analyzable` | `present_but_unparsed` |
| P7b functional numeric 记录 | `not_obtained` | `not_in_export` |
| P7c 功能细胞/组合的 screening viability | `available_analyzable` | `parsed_export_records` |

**未使用** `not_done_by_authors`：没有论文/官方材料明确说未做；表内缺列不推断未做。`qc_filtered` 未用于直接归因（7 系 plate QC 记录未见失败；matrix 数差异有额外/缺失，原因未明）。

## 4. 与 R202 / 用户复核的关系

- **接受用户/ERRATA C200 指出的落差**：R202 把"导出无字段/无重复计数"写成资源层面"无重复/无暴露/无功能"过强；论文明确报告 72 h/CellTiter-Glo、7 系×6 实验技术三重复、部分功能验证。
- **修正 R202 的 0-repeat 归因**：不是作者未做重复；是 R202 初步扫描的 pair 键使用了含 barcode 的 `lib1_drug`/`lib2_drug` 字符串。7 系重复 matrix 记录存在；不再写"0 repeat"。
- **不重算/不认证 68 A0 keys**：R202 的 68 是 A0 精确浓度匹配键；本轮只做 7 系结构覆盖，不重扫全部 wells 做效应、不重算 A0 匹配、不改 Q1 资格。
- **不改 R202 结论**：R202 `not_qualified` 仍按当时数据成立；但其 G4 的 "0 repeats" 作为 fail 依据应撤回/降级；R202 的"无暴露时间/无正交功能"应改为"导出无字段/无 numeric 数据；论文报告已做"。
- **不称"只能新湿实验"**：当前缺的是公开导出/补充中的可分析记录与映射；可向作者/Figshare 获取数据字典、源数据、重导，不能据此断言必须再做实验。

## 5. 偏离/限制

- 未取得作者数据字典，因此不能把 6 个 QC 上传日期严格等同于 6 次实验处理日期；"161 个 exact 6×3" 是按 QC 日期分组的结构证据，不是官方实验标签认证。
- 未重扫全部 3.9M wells 做效应；结构计数仅对 7 系/功能子集；不重算 68 A0 keys；不是 R202 计数认证。
- 补充材料来自 Europe PMC 合法接口（ZIP 95 MB，≤500 MB）；未绕过登录/许可；本地 paper XML 只读。
- 未尝试联系作者/未提交数据申请；未使用 Synapse/Dryad 等受限资源（与 R202 无关）。
- 不称新颖性/迁移/决策收益/机制；不晋升代码；不做效果拟合。

## 6. 产物/SHA 与下一执行者

- 主要产物：`PROTOCOL_X2.md`、`audit_x2.py`、`audit_x2.json`、`report_x2.md`、本记录、`usage_x2.json`、`receipts/{paper_claims,export_inventory,structure_7lines_repeats,r202_claims,download_manifest_x2}.json`。
- `audit_x2.json` 两跑逐字节一致；SHA 见 `usage_x2.json`。
- 下一执行者：
  1. 先读 `report_x2.md` §0/§8：**不要再说 R202 0 repeat 或只能新湿实验**；
  2. 若继续 Q1 重评：先取得 barcode/cmatrix→experiment/occasion/replicate/treatment date/passage 映射与功能源数据；用补充映射重建 7 系重复覆盖（技术三重复≠独立培养），再核 68 A0 keys/500 门槛与功能 numeric；
  3. 不重算 A0 68、不重扫 3.9M wells 做效应、不改 R202 产物/不晋升代码；不称新颖性/迁移/决策收益/机制。
