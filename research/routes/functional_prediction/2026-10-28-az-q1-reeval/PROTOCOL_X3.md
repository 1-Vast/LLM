# R203-X2 协议：修正 pair 身份后重评 AZ/GDSC 2024 资格（metadata-only）

**版本 v3，FROZEN（在任何重评判定前冻结）** ｜ 2026-10-28 ｜ 执行：drugcomb-auditor（task-133）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-28-az-q1-reeval/`（`PROTOCOL_X3.md`、`reeval_x3.py`、`reeval_x3.json`、`report_x3.md`、`record_x3.md`、`usage_x3.json`、`receipts/`）与 `tmp/`；**不改 R202/X1/A/B/D 产物**。
**纪律**：metadata-only；**不拟合效果、不做效应统计、不读响应值做效应**；可用 raw ZIP/Table S18 的结构字段（细胞/药物 ID/剂量/板/matrix/QC 日期）做身份、重复结构、实体重叠复算；不称新颖性/迁移/决策收益/机制；不晋升代码；技术三重复≠独立培养；未取得功能数值不写"作者未做"、不写"只能新湿实验"。

## 0. 背景/输入

- C202（`research/2026-10-27-agent-cell-colearning/ERRATA_R201_R202.md` 修正 4）：R202-Q1 的 AZ "0 repeats" 是导出键假 0；论文报告 72 h+CellTiter-Glo 2.0、7 个具名系×6 次实验技术三重复、部分组合凋亡/caspase/PARP 验证。
- X1（`research/2026-10-28-az-export-coverage/`）：当前导出 7 系 109 pairs/line、550,350 well 行、301 个 (line,pair) 恰 18 matrix 记录、161 个可归 6 QC 日期×3 matrix；无显式 experiment/重复/处理日/passage；功能数值未取得。X1 的计数是**基于 `lib1_drug_id`/`lib2_drug_id`** 的定向扫描；本轮按任务要求独立重算（不抄 X1 数字，若同则说明），并扩展到**全导出**的 corrected identity 结构。
- R202 冻结门定义/阈值：`research/2026-10-27-external-resource-hunt/PROTOCOL_X1.md` §3（G1–G7；**不改门槛**）。R202 AZ 自报数字：共享 114 细胞、14 药、8 个不同有向对、4,510 个 cell-pair 实体单元、**精确 A0 键 68**、barcode 0 重叠、0 重复（后者为导出口径假 0，C202）。

## 1. 修正 pair 身份（冻结规则）

- **不使用**含 barcode 的 `lib1_drug`/`lib2_drug` 列（形如 `38690_L56`；R202 的 0-repeat 来源）。
- 身份键：
  1. `cell`：`CELL_LINE_NAME` 归一（非字母数字去尾、casefold）；与 Jaaks 用归一细胞名匹配；另报告 COSMIC_ID 可匹配数（若可用）。
  2. `drug`：`lib1_drug_id`/`lib2_drug_id` 数值 ID → canonical name；映射优先 Table S2（`Compound1_ID/name`, `Compound2_ID/name`, `Single drugs Drug_ID/Drug_name`），其次 matrix results（`lib1_ID/name`,`lib2_ID/name`），再 GDSC2 单药表；同名多 ID 合并到 canonical name（记录映射冲突）。
  3. `pair`：canonical **无序**对用于重复结构统计 `(cell,{drug1,drug2})`；**有向**对 `(drug1→drug2)` 与角色方向用于 Jaaks 有向对/A0 匹配。
  4. `matrix record`：`(BARCODE, cmatrix)`；`cmatrix` 是 matrix 位置，不是重复标签。
  5. `QC 日期`：plate QC `QC_UPLOAD_DATE` 仅作批次代理，**不是处理日期**；`SCAN_ID` 同。
- 无法映射/ID 缺失的记录：单独计数并排除实体/A0 匹配；不得猜测名称。

## 2. 重算项（冻结）

1. **重复结构**：全导出每 `(cell,pair)` 的 matrix 记录数分布；**恰好 18 个 matrix 记录**的单元数；**恰好 6 个不同 QC 日期且每日期恰好 3 个 matrix 记录**的单元数（6×3 结构）；7 个具名系子集重复同一统计；报告 matrix 记录/pair 的 min/max/分位；**不把 6×3 当独立培养**。
2. **实体重叠（vs Jaaks）**：共享细胞、共享药物（canonical names）、共享**有向药对**（distinct tuples）、共享 cell×directed-pair 实体单元；旧 R202 数字并列。
3. **精确 A0 键**：按 A0 匹配口径（cell × 有向对 × concentration 设计可匹配）重算；用 A0 `matched_conditions.csv`（9,154 rows；4,668 condition keys）与 raw `lib1_conc/lib2_conc` + role orientation；统计 unique keys 与 raw rows；与 R202 的 68 对比并解释（旧映射/身份口径）。
4. **不一致**：报告 canonical 名称冲突/未映射 raw ID 数、null/invalid concentration、cell 归一匹配差异；不掩盖。
5. **不重做效果**：不读 `INTENSITY`/`inhibition`/HSA/Bliss/`PercentGrowth` 做统计；仅结构字段。

## 3. 资格门重评（沿用 R202 定义/阈值，不改门槛）

- **G1**：共享 ≥10 细胞、≥10 有向对、≥500 精确 A0 键；全满足 PASS；部分 CONDITIONAL；否则 FAIL。另报告 matching 上界（若有）。
- **G2**：raw `BARCODE` 与 Jaaks barcode/plate 交集=0 → PASS（若同源/无法核 → FAIL/CONDITIONAL）；同细胞面板/同 programme family 作为 caveat。
- **G3**：数字剂量可解析 + 暴露时间/检测方法可记录：raw 有数字剂量；无逐记录 exposure/assay 字段，但论文 Methods S15 明确 72 h/CellTiter-Glo 2.0 → **CONDITIONAL**（协议常数可带，逐键记录未取得；不称 pass）。
- **G4**：每键 ≥2 **独立**测量（不同日/plate/passage/flask）或独立培养：corrected identity 可重算重复 matrix 记录（技术三重复结构存在），但**无 passage/独立培养/处理日标签**；技术三重复≠独立培养 → **CONDITIONAL**（若重复结构可枚举但独立性未认证），不判 PASS；若 6×3 仅为 QC 日期/技术三重复，仍需 data dictionary。
- **G5**：≥1 正交功能读数：当前导出/补充无数值 apoptosis/caspase/PARP（仅论文图/PDF）；**FAIL（for current export）**，但注"论文报告已做，当前未取得可分析记录"，不是作者未做。
- **G6**：预注册聚合/Δ + 功能 viability：raw viability + 数字剂量可预注册；但无 exposure 字段、无预注册 Δ → **CONDITIONAL**。
- **G7**：独立 study/screen，不与已审资源共享原始 wells/keys：barcode 复用 0、独立 2024 发表；但同 GDSC/AZ 细胞面板/programme family → **CONDITIONAL**；若需更严格 lineage 证据，列条件。
- 总体规则（R202）：全 PASS=`qualified`；G1 PASS 且其余∈{PASS,CONDITIONAL} 且至少一 conditional=`qualified_with_conditions`；任一 FAIL=`not_qualified`；若关键项无法判定（如 G1 的 A0 键/身份不可认证）可给 `unclear: needs_data_dictionary`，但须列出具体缺口与数值。
- 本轮**不重做效果、不改 R202 结论**；重评是独立记录，差异写报告。

## 4. 边界/措辞

- 技术三重复 ≠ 独立培养；QC 上传日期 ≠ 处理日期；6 个 QC 日期组 ≠ 已认证 6 次实验。
- 未取得功能数值 → "论文报告已做，当前未取得可分析记录"；**不写**"只能新湿实验提供"、不写"作者未做"。
- 不称新颖性/迁移/决策收益/机制；不晋升代码；不重开 A/B/D 线；不改 R202 冻结产物（修正写本任务/C202）。
- 只写本目录与 tmp/；下载/接口回执记录 URL/状态/bytes/SHA/许可；不绕过登录/许可；单文件 ≤500 MB。

## 5. 输出/确定性

- `reeval_x3.py` 只做结构/身份/重复/实体/A0/门状态；输出 `reeval_x3.json`（键排序、无时间戳、协议/脚本/输入 SHA）。
- 报告 `report_x3.md`（修正身份规则、重算表、G1–G7、总体、与 R202 差异、补充获取项）、`record_x3.md`、`usage_x3.json`、`receipts/`。
- 两跑一致；单命令 ≤15 min；不读响应做效应。
