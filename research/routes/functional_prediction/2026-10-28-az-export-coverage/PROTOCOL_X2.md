# R203-X2 协议：AZ/GDSC 2024 重复与功能子集的导出覆盖追踪（metadata-only）

**版本 v1，FROZEN（在任何覆盖判定前冻结）** ｜ 2026-10-28 ｜ 执行：drugcomb-auditor（task-127）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-28-az-export-coverage/`（`PROTOCOL_X2.md`、`audit_x2.py`、`audit_x2.json`、`report_x2.md`、`record_x2.md`、`usage_x2.json`、`receipts/`）与 `tmp/`；**不改 R202-Q1 产物、A/B/D 线产物、其它目录/INDEX/git**。
**纪律**：metadata-only；**不拟合效果、不重扫 3.9M wells 做效应**；允许元数据/结构/日期/板号/条件映射统计；不称新颖性/迁移/决策收益/机制；不晋升代码；**区分"实验未做"与"当前导出未取得"**。

## 0. 目标

R202-Q1 报告曾写 AstraZeneca/GDSC 2024 raw wells "0 重复/无暴露时间/无正交功能"，用户复核指出论文 Methods 明确报告 **72h 处理 + CellTiter-Glo 2.0**、**7 个具名细胞系在 6 次实验中技术三重复**、部分组合有 **凋亡/caspase/PARP 功能验证**（PMC11061612；Fig 4/6）。本审计只追踪这些**论文已报告的项目**在当前**公开导出/ZIP**中的覆盖，判定是"导出缺少 / 当前未取得 / 可解析但未标注 / 实验未做（仅明确证据）"，不作效果推断。

## 1. 论文声明锚点（先核对；原文 https://europepmc.org/articles/PMC11061612，DOI 10.1158/2159-8290.CD-23-0388）

**只引用原文可复核的段落/图注**；本审计使用已保存的 JATS 本地副本（`research/2026-10-28-blocked-conclusion-review/PMC11061612.xml`，只读）与 `primary_passages.json`，必要时用合法接口读取，不绕过限制。

| 编号 | 论文声明 | 锚点（待 audit_x2.py 从 XML 再抽取核对） |
|---|---|---|
| P1 | **72 小时药物处理** | Methods "Screening"（sec S15）："the duration of drug treatment was 72 hours" |
| P2 | **CellTiter-Glo 2.0（Promega）** 测 viability | 同上："Cell Titer Glo 2.0 (Promega), 2.5μl ... luminescence microplate reader" |
| P3 | **7 个具名细胞系在 6 次实验中技术三重复** | Methods "Quality Control"（sec S17）：A375, HT-29, PC-14, U-2-OS, SW620, C32, MHH-ES-1；"technical triplicate on six occasions"；"18 replicates for every compound across each of the seven lines"（provided all plates pass QC） |
| P4 | 作者另用 technical/biological replicates 措辞；QC 规则 | 同上 + 下一段 "technical and biological replicates ... drugs flagged ... failing QC" |
| P5 | **selumetinib + venetoclax/AZD5991**：cleaved PARP / cleaved caspase-3，24–72h，NOMO-1 | Results "Selumetinib plus venetoclax or AZD5991 in AML"（sec S8）；Fig 4E/F western blot |
| P6 | **capivasertib + AZD5991**：apoptosis/caspase/PARP，AN3-CA；QVD 预处理 | Results/Fig 6C–E（caspase activation, cleaved PARP/caspase 3, QVD） |
| P7 | **venetoclax + AZD2811**：时间依赖 apoptosis；QVD；Fig 5C/D | Results（AML）与 Fig 5C/D |
| P8 | 数据可得性：screening data 经 Figshare project 163378；combination response 经 GDSC Combinations website；fitted/raw through Figshare | Data Availability 段 |

## 2. 被核对的当前导出（只读；URL/大小/SHA 见 receipts）

1. **AstraZeneca/GDSC 2024 Figshare project 163378**（12 个 dataset；`https://figshare.com/projects/.../163378`）：
   - `gsdc_well_stats.zip`（raw well-level 7×7 matrix；241,088,863 B；SHA `E8CB50F6…D3259`；5 CSV，解压 3,915,245 行）
   - `gdsc-007/008/009/010_matrix_results.csv`、`sandpiper-01_matrix_results.csv`、`GDSC2_fitted_dose_response.csv`
   - `plate_qc_Sandpiper-01_13May22.csv`（978 barcodes）、`plate_qc_Sandpiper-02_13May22.csv`（6,233 barcodes）——每 barcode 的 `SCAN_ID`/`QC_UPLOAD_DATE`/`QC_FLAG`
   - `Overall_ANOVA_results.csv`（1.96 GB，>500MB，未下载）、`Overall_ANOVA_results_significant...csv`（4MB）
2. **GDSC Combinations website**（`https://gdsc-combinations.depmap.sanger.ac.uk/`）：论文称可用于浏览/下载 combination response；本轮只核 metadata/可得性，不下载大矩阵（如需要另记录）。
3. **PMC supplementary/figures**：论文的 Fig 4/5/6、Supplementary Figs/Tables；**当前导出/ZIP 是否含其底层数据**是本次核对重点。

## 3. 覆盖状态定义（冻结）

对每个被追踪项给出且仅给出一个状态：

| 状态 | 定义 |
|---|---|
| `available_analyzable` | 当前导出中**存在记录**，且具备定位/分析所需字段（ID、剂量/条件、板/日期/实验批/重复/协议等按该项需要），可被独立分析（不需再猜测） |
| `present_but_not_analyzable` | 当前导出中**存在部分记录/图像/汇总**，但缺关键元数据或不是可解析数据（如只有图、只有聚合值、缺板/日期/重复列、无法对应到具体测量） |
| `not_obtained` | 论文**报告了该实验**，但当前公开导出/可访问文件中**没有取得**对应可用记录（**不是**"实验未做"） |
| `not_done_by_authors` | **仅当**论文/官方材料有明确证据表明该实验**未做**（例如作者明确写未做/不适用）；不得因导出缺列推断 |
| `unclear` | 现有证据不足以在以上四类中判定 |

**附加证据标签**（可选）：`metadata_missing`（缺列/缺关联）、`qc_filtered`（记录存在但被 QC 去掉）、`present_but_unparsed`（原始文件可能有但当前未解析/未下载）。

## 4. 追踪项（逐项判定）

1. **P1/P2 协议元数据**：72h、CellTiter-Glo 2.0 是否出现在导出字段/表头/元数据/README/QC 文件；若只在论文文字、导出无字段 → `not_obtained`（或 `present_but_not_analyzable` 若导出有间接标记但不完整）。
2. **7 个具名细胞系记录**：A375、HT-29、PC-14、U-2-OS、SW620、C32、MHH-ES-1 是否在 raw well zip / matrix results / plate QC 中出现；各自行数、barcode 数、pair 数；是否能与 `BARCODE→SCAN_ID/QC_UPLOAD_DATE` 关联。
3. **技术三重复 × 6 次（每 compound 18 replicates）**：
   - 对 7 个细胞系，统计每个 `(cell, pair/drug set, dose condition)` 的记录数、distinct `BARCODE`、distinct `SCAN_ID`、distinct `QC_UPLOAD_DATE`、`cmatrix` 值、`POSITION`；
   - 若存在 ≥2 个不同 barcode/scan/date 覆盖同一条件且可关联 → 检查是否足以标成重复记录；若只有一个 barcode/矩阵或无法 labeling → `present_but_not_analyzable` / `not_obtained`；
   - 明确区分"技术三重复"（paper 措辞）与"独立培养/独立日/passage"（paper 未认证）。
4. **板/日期/实验批次/well 级重复列**：当前 raw well 表头/矩阵结果/QC 文件是否含 `replicate`、`experiment`、`date`、`passage`、`batch`、`well_id` 等；列出实际字段及缺口。
5. **功能子集（P5–P7）**：NOMO-1/C32? /AN3-CA? 等相应组合（selumetinib+venetoclax/AZD5991；capivasertib+AZD5991；AZD2811+venetoclax）在 raw well/矩阵中是否有对应 viability 组合记录；**caspase/PARP/western/apoptosis 数值数据**是否在导出/补充中；只有图像/无数据 → `present_but_not_analyzable`；无任何对应 → `not_obtained`（不得说未做）。
6. **与 R202 的 68 A0 keys / 0 repeat 的差异说明**：
   - R202 的 68 是**A0 精确浓度匹配键**（Jaaks 2 anchor ×7 library vs AZ 7×7；仅 68）；0 repeat 是 R202 在**当前导出**按 `(cell, pair)` 分组、无重复 barcode 的结果；
   - 本轮**不重扫 3.9M wells 做效应、不重算认证**；只重核"导出中 7 个具名重复系与功能子集记录是否存在/可否关联"；
   - 必须写明：R202 的 0 repeat 是**导出/元数据分析口径**，不能推出"作者没做重复"；68 keys 也不能推出"无可比条件"。
7. **总体覆盖结论**：当前导出中可分析重复/功能子集是否存在；列出需补充获取项（论文补充材料/作者/数据库/网站）与是否建议后续获取/清洗/另立协议。

## 5. 判定与措辞

- 论文报告已做但当前导出无可用记录 → **`not_obtained` + "论文报告已做，当前未取得可分析记录"**。
- 表内缺列不能推断实验未做；只有明确作者声明才用 `not_done_by_authors`。
- 不写"只能新湿实验提供"；应写"当前公开导出未取得可分析记录，需向作者/补充材料/GDSC website 获取或重导"。
- 不称新颖性/迁移/决策收益/机制；不晋升代码；不改 R202 产物与结论（R202 的 not_qualified 仍就**其当时导出**成立，但归因措辞按本审计修正）。

## 6. 输出与确定性

- `audit_x2.py` 只读本地/已记录元数据与文本（paper XML、figshare project metadata、raw zip 表头/结构、plate QC、matrix results），输出 `audit_x2.json`（键排序、无时间戳、脚本/协议/输入 SHA）。
- `report_x2.md`：论文锚点表 + 逐项状态表 + 字段映射 + 与 R202 口径差异 + 结论/措辞 + 需补充获取项。
- `record_x2.md`、`usage_x2.json`、`receipts/`（下载/访问/结构证据）。
- 确定性：如脚本重算，连续两跑一致；单命令 ≤15 min。
