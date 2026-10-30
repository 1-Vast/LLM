# record_x3 —— R203-X2 修正 pair 身份后重评 AZ/GDSC 2024 Q1 资格（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-133）｜ 工作目录 `D:\MAESTRO`
**范围**：只写 `research/2026-10-28-az-q1-reeval/`（`PROTOCOL_X3.md`、`reeval_x3.py`、`reeval_x3.json`、`report_x3.md`、`record_x3.md`、`usage_x3.json`、`receipts/`）与 `tmp/`；不改 R202/X1/A/B/D 产物。
**纪律**：metadata-only；不拟合效果、不做效应统计、不读响应值做效应；技术三重复≠独立培养；未取得功能数值写"论文报告已做，当前未取得可分析记录"；不称新颖性/迁移/决策收益/机制；不晋升代码；不改 R202 冻结产物。

## 0. 任务与结论

- 任务：按 C202/X1 的修正，用 **canonical drug ID/名称 + role direction** 重建 pair 身份，重算重复结构、与 Jaaks 实体/A0 重叠，并沿用 R202 G1–G7 门槛重评 AZ/GDSC 2024 Q1 资格。
- **总体判定：`not_qualified`（按 R202 冻结门槛）**；G1 conditional（114 细胞 pass；8 有向对 <10；68 A0 键 <500）；G5 fail（当前导出无 functional numeric；论文报告已做，不是作者未做）；其余 G2 pass、G3/G4/G6/G7 conditional。若 Lead 选择延后，可另裁 `unclear: needs_data_dictionary`（需作者映射/功能源数据），但本审计按冻结规则选 not_qualified。
- **R202 0 repeat 撤回**：旧初扫用 `lib1_drug`/`lib2_drug`（含 barcode）作身份；修正后全导出 **4,398 个 (cell,pair) 单元有 ≥2 matrix 记录；301 个 exact-18；161 个 6 QC 日期×3 matrix**；技术三重复结构存在，但独立培养未认证。
- **68 A0 键重算仍为 68**（70 raw rows）；不是 R202 旧值认证；仍 <500。共享细胞 114、药物 14、有向对 8（either 9）、cell-pair 4,510、barcode 0 重叠；与 R202 旧数字相同（旧 68 可复现），主要变化是 0-repeat 被推翻。

## 1. 时间线（2026-10-28）

| 步骤 | 内容 |
|---|---|
| 读输入 | task-133；C202/`ERRATA_R201_R202.md`；X1 `report_x2.md`/`audit_x2.json`；R202 `PROTOCOL_X1.md`/`hunt_x1.json`/`report_x1.md`；用户复核报告 §5；本地 paper JATS |
| 冻结协议 | `PROTOCOL_X3.md` v3 FROZEN（身份规则、重算项、G1–G7 沿用阈值、措辞边界）；之后未改门槛/状态定义 |
| 实现 | `reeval_x3.py`：Table S2+matrix results+GDSC2 → canonical ID/name；raw ZIP 元数据结构扫描；QC barcode 日期；Jaaks/A0 索引；重复统计；门重评；输入 SHA 回执 |
| 运行 | `reeval_x3.py` 68.5 s；两跑 `reeval_x3.json` 字节一致（SHA `3A95EA89…B9F42C`） |
| 写报告/记录 | `report_x3.md`、本记录、`usage_x3.json`；未改 R202/X1 |
| 不运行 | 不拟合效果、不做响应统计、不训练/预测、不晋升代码、不重开 A/B/D 线 |

## 2. 方法/关键数字

### 2.1 身份修正
- R202 初扫把 `lib1_drug`/`lib2_drug` 字符串（如 `38690_L56`，含 barcode）当 pair；本轮只用 `lib1_drug_id`/`lib2_drug_id` → canonical name。
- ID→名称来源：Table S2 combos/single（218/46 条）、matrix results（168,110 条）、GDSC2 单药（135,242 条）；`id2name` 239 个；**unmapped raw IDs=0**；缺浓度行=0；名称冲突=0。
- 配对：无序 canonical pair `(cell,{d1,d2})` 用于重复；有向 `(d1→d2)`/角色用于 Jaaks/A0。

### 2.2 重复结构（全导出 + 7 系）
- 全导出：**68,710 个 (cell,pair) 单元；84,055 个 matrix 记录；4,398 个单元 ≥2 matrix；301 个 exact-18；161 个 6×3**；matrix/pair 范围 1–38。
- 7 系（A375/C32/HT-29/MHH-ES-1/PC-14/SW620/U-2-OS）：各 109 pairs；**合计 550,350 well 行**；exact-18 **301**；6×3 **161**；每 pair matrix 范围 3–38；barcodes 行内和 1,022。
- 与 X1 独立重算数字一致（301/161/550,350），说明 X1 结构计数稳健；R202 的 0 repeat 是旧键造成的假 0，不是 X1 数字。
- **技术三重复≠独立培养**：无 experiment/occasion/replicate/treatment date/passage/culture 字段；QC_UPLOAD_DATE 是上传日期，不是处理日期。

### 2.3 实体/A0
- 修正重算：共享 **114 细胞**（COSMIC 114）、**14 药**、**8 有向对**（either 9）、**4,510 cell-pair 实体单元**、**68 精确 A0 keys**（70 raw rows）、**barcode 0 重叠**。
- R202 旧：114/14/8/4,510/68/0——旧 68 可重算复现，但旧 0-repeat 不可复现（被推翻）。
- A0 索引：9,154 rows；canonical 名称下 3,624 condition keys；68 unique keys / 70 rows；2×7 vs 7×7；远 <500。
- 未读 `INTENSITY/inhibition/HSA/Bliss/PercentGrowth` 做效应；仅结构/身份/剂量设计匹配。

## 3. G1–G7 重评（冻结阈值不变）

| 门 | 状态 | 依据 |
|---|---|---|
| G1 | CONDITIONAL | 114 细胞 pass；8 有向对 <10；68 A0 键 <500 |
| G2 | PASS | barcode 0 重叠；同细胞面板/programme caveat |
| G3 | CONDITIONAL | 数字剂量；论文 72h/CellTiter-Glo 2.0；导出无逐记录 exposure/assay |
| G4 | CONDITIONAL | 4,398 个 ≥2 matrix、301 exact18、161 6×3；技术三重复/QC 日期；无独立培养/passage |
| G5 | FAIL（当前导出） | 当前导出/补充无 functional numeric；论文图/PDF 存在；**论文报告已做，不是作者未做** |
| G6 | CONDITIONAL | raw viability+数字剂量；无 exposure 字段/尚无冻结 Δ |
| G7 | CONDITIONAL | 独立发表/barcode 不重叠；同 GDSC/AZ 面板家族 |

- 总体 **`not_qualified`**；若延后资格可标 `unclear: needs_data_dictionary`（具体缺口：experiment/occasion/replicate/treatment date/passage 映射 + 功能 numeric 源数据；仍不是"作者未做"或"只能新湿实验"）。
- 与 R202：G4 0-repeat 依据撤回/降级；68 重算不变；G1/G5 仍是缺口；R202 `not_qualified` 不重做，但本次重评在修正身份下仍为 not_qualified。

## 4. 是否建议独立挑战/补充获取

- **不建议**在当前导出上对 AZ/GDSC 2024 发起 Q1 独立挑战：G1 8 有向对/68 A0 键远低于 10/500；G5 当前无 functional numeric。
- 建议先：
  1. 作者/Figshare 数据字典：`BARCODE/cmatrix → experiment/occasion/technical replicate/treatment date/passage/culture`；
  2. Fig 4E/F、5C/D、6C–E 与 Supplementary Figures 的 western/caspase/PARP 原始数值/定量源表；
  3. Methods 72h/CellTiter-Glo 2.0/Caspase-Glo 3/7/QVD 与导出批次映射；
  4. 可选 GDSC Combinations website 组合响应下载/数据字典；
  5. 若补到 G1 所需或另立新关系协议，再另做任务。

## 5. 偏离/限制

- 不读响应做效应；不拟合；不训练；不晋升代码；不改 R202/X1/A/B/D 产物。
- 技术三重复结构存在，但不认证独立培养/6 次实验处理日期；QC 上传日≠处理日；不能把技术三重复当独立重复。
- 功能数值未取得：写"论文报告已做，当前未取得可分析记录"；不写作者未做/不写只能新湿实验。
- A0 68 是重算值（70 rows），非旧值认证；未重扫 wells 做响应分析；本轮不重做效果。
- 只写本目录与 tmp/；输入清单/SHA 见 `receipts/input_manifest_x3.json`；脚本/协议 SHA 见 `reeval_x3.json`。

## 6. 产物与下一执行者

- `PROTOCOL_X3.md`、`reeval_x3.py`、`reeval_x3.json`、`report_x3.md`、本记录、`usage_x3.json`、`receipts/input_manifest_x3.json`。
- 两跑一致；SHA 见 `usage_x3.json`。
- 下一执行者：先读 `report_x3.md` §0/§4；不要再写 R202 0-repeat/只做新湿实验；若补到数据字典/功能 numeric，另立重评任务；不重算/不改 R202 冻结产物、不晋升代码。
