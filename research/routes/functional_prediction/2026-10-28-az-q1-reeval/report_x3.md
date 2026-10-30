# R203-X2 报告：修正 pair 身份后重评 AZ/GDSC 2024 Q1 资格（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-133）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_X3.md](PROTOCOL_X3.md)（v3 FROZEN，先于重评冻结；不改 R202 门槛）
**产物**：[reeval_x3.py](reeval_x3.py)、[reeval_x3.json](reeval_x3.json)、`receipts/`（输入 SHA 回执）、[report_x3.md](report_x3.md)、[record_x3.md](record_x3.md)、[usage_x3.json](usage_x3.json)。
**纪律**：metadata-only；**不拟合效果、不做效应统计、不读响应值做效应**；技术三重复≠独立培养；未取得功能数值写"论文报告已做，当前未取得可分析记录"，不写"作者未做/只能新湿实验"；不称新颖性/迁移/决策收益/机制；不晋升代码；不改 R202/X1 冻结产物；只写本目录与 `tmp/`。

## 0. 结论（先行）

### 0.1 修正 pair 身份后的事实

- R202 的 **"0 repeats" 被撤回**：R202 把含 barcode 的 `lib1_drug`/`lib2_drug`（如 `38690_L56`）当 pair 身份；本轮用 **`(cell, canonical drug1, canonical drug2, role direction)`** 重建，按 **`(BARCODE, cmatrix)`** 计 matrix 记录。
- 全导出重算：**68,710 个 (cell,pair) 单元**；**4,398 个单元有 ≥2 个 matrix 记录**；**301 个单元恰好 18 个 matrix 记录**；**161 个单元可归为 6 个 QC 日期 × 每日期 3 个 matrix 记录**；**matrix 记录总数 84,055**。
- 7 个具名重复系（A375, C32, HT-29, MHH-ES-1, PC-14, SW620, U-2-OS）：每系 109 pairs；合计 **550,350 well 行**；**301 个 exact-18**、**161 个 6×3** 全部来自 7 系（与 X1 独立重算数字相同；说明 X1 结构计数稳健；X1 的 0 repeat 问题属 R202 旧键，不是 X1 数字）。
- **技术三重复结构存在，但独立培养未认证**：没有显式 experiment/occasion/replicate/treatment date/passage/culture 字段；`QC_UPLOAD_DATE` 是上传日期，不是处理日期。

### 0.2 资格重评

**总体：`not_qualified`（按 R202 冻结门槛，不重做效果）。**

| 门 | 状态 | 关键理由 |
|---|---|---|
| **G1 实体/匹配规模** | **CONDITIONAL** | 共享 **114 细胞**（≥10 pass）、**8 个有向对（<10）**、**68 个精确 A0 键（<500）**；部分满足 → conditional。 |
| **G2 板孔不相交** | **PASS** | raw barcode 与 Jaaks barcode **0 重叠**；caveat：同 GDSC/AZ 细胞面板/programme family。 |
| **G3 合法暴露** | **CONDITIONAL** | 数字剂量有；论文 S15 报告 72 h/CellTiter-Glo 2.0；导出无逐记录 exposure/assay 字段。 |
| **G4 独立测量/培养** | **CONDITIONAL** | corrected identity 显示重复 matrix 记录（301 exact-18、161 6×3），但**技术三重复/QC 日期组**，无独立培养/passage/处理日标签。 |
| **G5 正交功能读数** | **FAIL（当前导出）** | 当前导出/补充**无 apoptosis/caspase/PARP 的 numeric 数据**（论文图/补充 PDF 存在）；这是数据未取得，**不是作者未做**。 |
| **G6 冻结聚合/Δ** | **CONDITIONAL** | raw viability + 数字剂量可预注册 Δ；无 exposure 字段、尚无冻结聚合。 |
| **G7 非重聚合 lineage** | **CONDITIONAL** | 独立 2024 发表、barcode 不重叠；同 GDSC/AZ 细胞面板/programme family，lineage 需来源链。 |

**为什么不是 qwc**：R202 规则要求 `qualified_with_conditions` 必须 **G1 PASS**；修正后 G1 仍只有 8 个共享有向对、68 个 A0 键（<10/<500），G1 为 conditional，且 G5 当前导出为 fail。因此总体 `not_qualified`。  
**若 Lead 希望暂不判资格、先补数据**：可另裁 **`unclear: needs_data_dictionary`**（需作者 `BARCODE/cmatrix→experiment/occasion/technical replicate/treatment date/passage` 映射 + 功能 numeric 源数据）；本审计按冻结规则选择 `not_qualified`，但**不把原因写成作者未做或“只能新湿实验”**。

## 1. 修正 pair 身份（与 R202 的差异）

### 1.1 规则

| 项 | R202 口径 | 本任务口径 |
|---|---|---|
| 细胞 | 细胞名归一 | 同，另核 COSMIC_ID 匹配（114/114） |
| 药物身份 | 初扫用 `lib1_drug`/`lib2_drug` 字符串（含 barcode；如 `38690_L56`） | **数值 `lib1_drug_id`/`lib2_drug_id` → canonical name**（Table S2 combos/single drugs、matrix results `lib1_ID/name`、GDSC2 单药表） |
| pair 身份 | 字符串对（跨 barcode 被拆） | 无序 canonical pair `(cell,{d1,d2})` 用于重复；**有向/角色** `(d1→d2)` 用于 Jaaks 有向对/A0 |
| matrix 记录 | 未以 `(BARCODE,cmatrix)` 统一计 | `(BARCODE,cmatrix)`；`cmatrix` 是 matrix 位置，不是重复标签 |
| 日期/批次 | 无 | plate QC `QC_UPLOAD_DATE`/`SCAN_ID`（**上传日，不是处理日**） |

- 映射结果：`id2name` 239 个 ID；**未映射 raw ID=0**；缺浓度行=0；名称冲突=0。raw 得到 **754 细胞、37 个可映射药名、109 个 distinct 有向对、7,211 barcodes**。
- **R202 0-repeat 的直接原因**：初扫的 pair 字符串含 barcode，同一 canonical pair 在不同 barcode 上被当成不同 pair；不是作者未做重复。

### 1.2 重算的重复结构（不抄 X1，独立重算）

**全导出：**

| 指标 | 数值 |
|---|---:|
| (cell,pair) 单元数 | 68,710 |
| matrix 记录总数（BARCODE×cmatrix） | 84,055 |
| 有 ≥2 matrix 记录的单元 | 4,398 |
| 恰好 18 matrix 记录的单元 | **301** |
| 恰好 6 个 QC 日期 × 每日期 3 matrix 的单元 | **161** |
| matrix 记录/pair 范围 | 1–38（7 系子集 3–38） |

**7 个具名重复系：**

| 细胞系 | pairs | matrix 记录/pair | exact-18 单元 | 6×3 单元 | raw well 行 | barcodes |
|---|---:|---:|---:|---:|---:|---:|
| A375 | 109 | 9–33 | 28 | 13 | 85,970 | 160 |
| C32 | 109 | 7–32 | 51 | 27 | 75,946 | 144 |
| HT-29 | 109 | 8–34 | 47 | 13 | 78,643 | 144 |
| MHH-ES-1 | 109 | 3–33 | 37 | 22 | 74,148 | 136 |
| PC-14 | 109 | 8–33 | 64 | 51 | 78,578 | 148 |
| SW620 | 109 | 7–38 | 15 | 0 | 80,226 | 147 |
| U-2-OS | 109 | 7–33 | 59 | 35 | 76,839 | 143 |
| **合计** | **763** | — | **301** | **161** | **550,350** | 1,022（行内和） |

- 结论：**技术三重复/重复 matrix 结构存在**（部分 pair 恰为 6 QC 日期×3 matrix），与论文 P3b 的 "18 replicates" 方向一致；但 **6 个 QC 日期只是上传日期**，不是处理日期；**技术三重复 ≠ 独立培养**；无 passage/独立培养/实验标签。
- 与 X1 独立重算数字一致（301/161/550,350）；X1 未使用含 barcode 列，因此可复现；R202 的 `0 repeats` 是旧初扫键问题，不是 X1 导致的。

## 2. 实体/A0 重叠重算（vs Jaaks）

| 指标（与 Jaaks） | R202 旧数字 | 本任务修正身份重算 | 说明 |
|---|---:|---:|---|
| 共享细胞 | 114 | **114**（COSMIC 114） | 同名归一下一致 |
| 共享药物（canonical） | 14 | **14** | 239 ID 映射后仍 14 个 Jaaks 共享药名 |
| 共享**有向药对** | 8 | **8**（either-orientation 9） | 仍 <10；角色方向按 Jaaks anchor→library |
| 共享 cell×directed-pair 实体单元 | 4,510 | **4,510** | 与旧一致 |
| **精确 A0 匹配键** | 68 | **68**（raw rows 70） | 2×7 vs 7×7；重算后仍 68 unique keys；旧 68 不作为认证 |
| barcode 与 Jaaks 重叠 | 0 | **0** | G2 pass |
| 原始 distinct directed pairs | — | 109 | 全导出 |

- A0 索引：`matched_conditions.csv` 9,154 rows；按 canonical 名称/细胞归一得到 **3,624 个可查条件键**（旧口径不同，见下）；raw 匹配 68 unique keys/70 rows，远低于 **500** 门槛。
- **修正前后差异**：共享细胞/药物/有向对/实体/A0 键的数字与 R202 相同（旧 68 恰好可重算复现），但 R202 的 **0-repeat** 被推翻为 4,398 个有重复 matrix 的单元/301 exact-18/161 6×3；这是身份口径修正的主要数值变化。
- **不重做效果**：未读 `INTENSITY`、`inhibition`、`HSA/HSA_excess`、`Bliss*` 或 `PercentGrowth` 做任何效应统计；仅做实体/结构/剂量设计匹配。

## 3. G1–G7 重评（沿用 R202 门槛，不改变阈值）

判定规则：全 PASS=`qualified`；G1 PASS 且其余 ∈{PASS,CONDITIONAL} 且至少一 conditional=`qualified_with_conditions`；任一 FAIL=`not_qualified`；无法判定可给 `unclear: needs_data_dictionary`。

| 门 | 状态 | 重评依据 | 需要的补充（不写作者未做） |
|---|---|---|---|
| G1 | **CONDITIONAL** | 细胞 114 pass；有向对 8<10；A0 键 68<500 | 需要更多共享有向对/可匹配 A0 键；当前导出不足以复用 Jaaks A0 关系 |
| G2 | **PASS** | barcode 0 重叠；不同 screen/plate | caveat：同细胞面板/programme family，G7 另计 |
| G3 | **CONDITIONAL** | 数字剂量；论文 72h/CellTiter-Glo 2.0；导出无逐记录 exposure/assay | 需要逐板/逐键协议映射 |
| G4 | **CONDITIONAL** | 重复 matrix 记录存在（4,398 个 ≥2；301 exact18；161 6×3）；但技术三重复/QC 上传日期；无独立培养/passage/处理日 | 需要 experiment/occasion/replicate/treatment date/passage 数据字典；技术三重复≠独立培养 |
| G5 | **FAIL（当前导出）** | 当前 Figshare/补充无 apoptosis/caspase/PARP numeric；只有论文图/PDF | **论文报告已做，当前未取得可分析记录**；需 western/caspase/PARP 源数据/定量 |
| G6 | **CONDITIONAL** | raw viability+数字剂量可预注册 Δ；无 exposure 字段/尚无冻结聚合 | 需预注册 Δ 与 exposure 映射 |
| G7 | **CONDITIONAL** | 独立 2024 发表、barcode 不重叠；同 GDSC/AZ 细胞面板 | 需来源链/lineage 证明 |

**总体：`not_qualified`**（G5 fail；G1 也仅 conditional，不能 qwc）。  
**若 Lead 选择延后资格判断**：可标 `unclear: needs_data_dictionary`；这不是说作者未做功能实验，而是当前公开导出没有可分析的功能 numeric/重复标签。

## 4. 与 R202 的差异（摘要）

| 项 | R202 | 本任务（修正身份） |
|---|---|---|
| AZ 0 repeats | `units_with_ge2_platforms=0` → G4 fail | **撤回**：4,398 个有 ≥2 matrix 的单元；301 exact-18；161 6×3；G4 → **conditional** |
| 68 A0 键 | 68 | **68**（重算；70 raw rows）；仍 <500；不把旧值当认证 |
| 共享有向对 | 8 | **8**（either 9）；仍 <10 |
| 共享细胞/药物/实体 | 114/14/4,510 | **114/14/4,510** |
| 无暴露时间 | 写"无 exposure" | **改**：论文报告 72h/CellTiter-Glo 2.0；导出无逐记录字段 → G3 conditional |
| 无正交功能 | G5 fail | **保持 G5 fail（当前导出）**，但原因是 **当前未取得 numeric**，不是作者未做；论文报告已做 |
| 总体 | not_qualified | **not_qualified**（按冻结门槛；G4 依据已改；G1/G5 是真正缺口） |

- R202 冻结产物不改；本报告作为修正/重评记录；C202/ERRATA 引用本任务。
- **不重做效果、不改门槛、不晋升代码**。

## 5. 是否建议独立挑战 / 后续

**当前不建议对 AZ/GDSC 2024 发起独立挑战**：按 R202 冻结门槛，G1 只有 8 个共享有向对、68 个精确 A0 键（<10/<500），G5 当前导出无 functional numeric；即使补上重复标签也不满足 G1。

**建议先做“补充获取/清洗/映射”，再决定是否另立协议：**
1. 作者/Figshare 数据字典：`BARCODE/cmatrix → experiment/occasion/technical replicate/treatment date/passage/culture`；当前导出缺这些标签，不能认证 6 次实验/独立培养。
2. Fig 4E/F、5C/D、6C–E 与 Supplementary Figures 的 **western/caspase/PARP 原始数值/定量源表**（当前只有 PDF 图）。
3. 论文 Methods 的 72h/CellTiter-Glo 2.0/Caspase-Glo 3/7/QVD 与导出批次的逐键映射。
4. 可选：GDSC Combinations website 的组合响应下载/数据字典；核对 7 系 18-replicate 官方计数。
5. **若**补到 G1 所需共享有向对/A0 键或决定另立“新关系”协议，另做任务；不要把本导出直接当 Jaaks A0 复现资源。

## 6. 边界/限制

- 不读响应做效应、不拟合模型/预测、不做决策收益/机制/新颖性/迁移；不晋升代码；不改 R202/X1/A/B/D 产物。
- 重复结构只证明 matrix 记录重复/技术三重复结构，**不证明独立培养**；QC 上传日≠处理日；技术三重复≠独立重复。
- 功能 numeric 未取得 → "论文报告已做，当前未取得可分析记录"；**不写作者未做、不写只能新湿实验**。
- A0 68 是重算结果（70 raw rows），不是 R202 旧值的认证；未重做效果分析；未重扫全部 wells 做响应。
- 只写本目录/tmp；输入 SHA 见 `receipts/input_manifest_x3.json` 与 `reeval_x3.json`。

## 7. 复现

```powershell
cd D:\MAESTRO\research\2026-10-28-az-q1-reeval
& D:\anaconda\envs\maestro\python.exe reeval_x3.py   # 读 raw ZIP/Table S2/Jaaks/A0；写 reeval_x3.json
```

`reeval_x3.json` 键排序、无时间戳；两跑一致（见 `usage_x3.json`）。
