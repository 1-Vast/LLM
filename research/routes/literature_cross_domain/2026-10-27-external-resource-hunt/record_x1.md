# record_x1 —— R202-Q1 外部资源定向征询与资格执行记录（metadata-only）

2026-10-28 ｜ 执行：drugcomb-auditor（task-126）｜ 工作目录 `D:\MAESTRO`
**范围**：只写 `research/2026-10-27-external-resource-hunt/`（`PROTOCOL_X1.md`、`hunt_x1.py`、`hunt_x1.json`、`report_x1.md`、`record_x1.md`、`usage_x1.json`、`receipts/`）与 `tmp/`；不改其它目录/INDEX/SYNTHESIS/git/已审资源产物。
**纪律**：metadata-only；不运行效果/不拟合预测/不读响应值做效应；不绕过登录/许可；阴性写"未发现/不可得"不写"不存在"；不把同一 96 细胞换聚合当新数据；不把已聚合挑战分数当原始重复；不称新颖性/迁移/决策收益/机制。

## 0. 任务与判定

- 任务：按 R202 BRIEF 定向征询本地未收录的公开独立组合/功能资源，资格判定能否重开 A/B/D3/4/5 的最小实验。
- **总体判定 `not_qualified`；建议停止本轮外部征询**；无 candidate 达到 `qualified` 或 `qualified_with_conditions`。
- 主要发现：**AstraZeneca/GDSC 2024 raw wells**（大、原始、可下载）与 **NCI-ALMANAC**（原始 well 表）都在 **G4 独立测量/独立培养** 与 **G1 A0 匹配键** 上失败；DREAM 2015 访问受限；其它候选为 processed/mono/synthetic/organoid。

## 1. 时间线（本机，Asia/Shanghai，2026-10-28）

| 步骤 | 内容 |
|---|---|
| 读背景 | `research/2026-10-27-innovation-round-r202/BRIEF.md`、`research/SYNTHESIS.md`（C188–C195 相关段）、`ERRATA_A3.md`/`a3.json`、`research/2026-10-27-core-module-design/qualification/`（Q0 规格）、R201 record/BRIEF、`agent-cell-colearning` 相关（A/B 测量需求） |
| 冻结协议 | 写 `PROTOCOL_X1.md`（冻结 G1–G7、判定/原因码、下载/许可规则、禁用表述）；之后不改阈值 |
| 检索/探查 | 有界 web search（12 条 query）+ Zenodo/Figshare/Dryad/Synapse/HuggingFace API 探测；见 `receipts/search_log.json` |
| 下载 | NCI-ALMANAC zip（85,966,226 B）与数据字典/化合物名；AstraZeneca/GDSC 2024 raw well zip（241,088,863 B）+ 5 个 matrix results + GDSC2 单药表；PanThera studies/readme；SAFER readme（详见 `receipts/download_manifest.json`） |
| 结构扫描 | `tmp/scan_nci.py`（NCI zip 流式 3,686,475 行，~28 s）、`tmp/nci_overlap.py`/`tmp/nci_matched_keys.py`（与 Jaaks/A0 重叠；~11–13 s）；`tmp/scan_azeraw.py`（AZ raw zip 3,915,245 行，~41 s）、`tmp/azeraw_entities.py`（ID→名/A0；~43 s） |
| 判定/写报告 | 逐候选 gate/原因码；写 `hunt_x1.py` → `hunt_x1.json`（0.1 s）；`report_x1.md`、本记录、`usage_x1.json`、`receipts/` |

## 2. 关键数字/证据（metadata-only）

### 2.1 AstraZeneca/GDSC 2024 raw wells（唯一值得保留的新关系开发资源）
- 来源：Figshare project 163378 / article 25266697；AACR Cancer Discovery 2024 CD-23-0388；Data Availability 明确指向该 project。
- 下载：`gsdc_well_stats.zip` 241,088,863 B，SHA `E8CB50F6…D3259`（≤500 MB）；内部 5 个 CSV 共 2,145,? 未解压到盘（zip 流式读）；共 3,915,245 well 行。
- 结构：5 projects（GDSC_007/008/009/010 + Sandpiper-01）；**754 cells**；**7,211 barcodes**；**84,055 (cell,pair) 单元**（每单元 7×7 = 49 wells）；数字剂量 `lib1_conc/lib2_conc`；raw `INTENSITY`/`inhibition`/HSA/Bliss 派生；**无 exposure time 列**。
- Jaaks 重叠：共享 **114/125 cells**；**14 drugs**；**8 distinct directed pairs**；**4,510 cell-pair 实体单元**；**精确 A0 浓度匹配键 68**（<500）；**barcode 0 重叠**。
- Gates：G1 fail（pairs 8<10；matched keys 68<500）；G2 pass（0 shared barcode）；G3 conditional（无暴露时间）；**G4 fail（84,055 单元中 0 个有 ≥2 板/独立重复）**；G5 conditional（无正交功能）；G6 conditional；G7 conditional（不同板/独立发表，但同细胞面板/programme family）。→ **not_qualified**。
- 价值：可用于**新关系/新细胞**的原始 7×7 剂量矩阵开发；不能当本任务的独立重复/功能验证目标。

### 2.2 NCI-ALMANAC
- 下载：`ComboDrugGrowth_Nov2017.zip` 85,966,226 B，SHA `69367A8B…96100`；内部 CSV 615,194,859 B（未解压写盘，流式读）。
- 结构：3,686,475 行（combo 2,873,514 / solo 812,961）；61 cells；5,242 NSC pairs；305,081 (cell,pair) 单元；1,570 studies / 26,687 plates / 3 screeners / 154 dates；`PercentGrowth…`（viability/OD）；数字剂量 `Conc1/Conc2`；无 exposure time。
- 重复：2,866,683 个 `(cell,pair,conc1,conc2)` keys，仅 **6,831（0.24%）**有 2 行且跨不同 plate/study。
- Jaaks 重叠：13 cells（12 A0）；17 drugs；186 NCI 对在 Jaaks 药物集内；**精确 A0 匹配键 0**。
- Gates：G1 conditional；G2 conditional；G3 conditional；**G4 fail**；G5 conditional；G6 conditional；G7 pass（NCI/DTP 原始；DrugComb ALMANAC 是派生）。→ **not_qualified**。

### 2.3 其它候选
- **AstraZeneca-Sanger DREAM 2015**：Synapse syn4231880 公开 metadata/wiki（~11.5k combos/85 cells/118 drugs），数据文件实体匿名 **403**（terms/login）→ `access_restricted`；不绕过。
- **PanThera 2024**：Zenodo 14216168（models 877 MB >500 MB；data 276 MB；studies=Optuna logs）；PanTheraDB 14001717 是**预测**triplets → `aggregated_only`/`no_combination_data`。
- **SAFER 2024**：Zenodo 10076432（data 1.13 GB / database 1.14 GB >500 MB；readme 明示 O'Neil/ALMANAC/DrugComb processed）→ `reaggregated_lineage`/`data_unavailable`。
- **Dryad 类器官顺序给药 2025**：DOI 10.5061/dryad.0vt4b8h8x（CC0 metadata；data.zip 30 KB/README 14 KB；文件下载 401 bearer token；无 Jaaks cells）→ `jaaks_overlap_insufficient`/`access_restricted`；仅作方向 3 新协议候选。
- **HF ABX-CT-004**：合成抗生素顺序治疗基准（n<1k）→ `synthetic_benchmark`。
- **Novartis DRUG-seq U2OS**：mono 转录组（49,392 obs/3,742 compounds）→ `no_combination_data`/`mono_only`。
- **功能独立性资源**：有界检索未发现同组合 wells 的 apoptosis/caspase/靶点参与/再生长公开配对资源（`no_candidate_found`，不是"不存在"）。

## 3. 冻结规则执行与偏离披露

- **协议先冻结**：`PROTOCOL_X1.md`（v1）先于全部 gate 判定写死；**未在阈值/判定上做事后修改**。
- **单文件 ≤500 MB**：实际下载的 NCI 86 MB、AZ raw 241 MB、matrix/GDSC2 小文件均合规；SAFER/PanThera models/ANOVA >500 MB **未下载**；AZ raw zip 内部 CSV 615 MB 未解压到盘（zip 流式读取，仅结构/计数）。
- **未绕过许可**：DREAM 403、Dryad 401 记录为 `access_restricted`/`unavailable`，未尝试登录/付费。
- **未读响应做效应**：仅用列名/行数/设计/剂量/重复/实体计数；AstraZeneca `INTENSITY` 等响应列只做存在性/结构读取，未统计效应；NCI `PercentGrowth` 同。
- **候选映射下界披露**：AZ raw 的 drug 名映射仅覆盖 matrix results 中 46 个 ID（实际论文 109 drugs），因此共享药物/对计数是**下界**；但 G4（0 重复板）与 G1（68 matched keys 远<500）两处硬失败不受影响。
- **lineage/重叠**：未把 Jaaks Original/Validation/96 细胞换聚合当新数据；未把 DrugComb 的 ALMANAC 派生表当原始重复（使用 NCI 原始 zip）；PanTheraDB/SAFER 的处理数据未当原始测量。

## 4. 限制

- 有界检索，非系统综述；未查 Google Scholar/Scopus/WoS、未做引文回溯/前向追引；2024–2026 新资源可能漏检。
- AstraZeneca 2024 论文的 Figshare 项目可能还有未抓取的 supplement/QC/ANOVA 超大文件；未下载 >500 MB 文件；其 raw zip 未逐行校验字段完整性（只做结构/实体/A0 匹配）。
- 未联系作者/未申请受限数据（DREAM/Dryad）；未使用 Synapse/Dryad 账号。
- 未运行任何效果/模型/预测；所有"资源潜力"仅为结构判断，不是效果证据。
- 不声称任何资源"不存在"；未发现仅为本次检索/API 探测结果。

## 5. 产物与 SHA

见 `usage_x1.json`；主要：
- `PROTOCOL_X1.md` `3E06D9EDC780DB7E6FD40A8A769C29F29733214ECAD90A6EEEEC6130933BA516`
- `hunt_x1.py` `80CE3FEC8EB2A857F710F1075433A4E10E555AA28D7148AEFF4E16FF588D8413`
- `hunt_x1.json` `B5B8652B498F3618F7721CB12996775E5DF3FBED7912FE95DCB161DC1037EA89`（同脚本同输入两跑逐字节一致）
- `report_x1.md` `4E59DB4EFA0A58F7E7AE3FEA67893DB1CBC2E350609E45660914217E5070943C`
- receipts：`download_manifest.json` `E5B43EDE…B5FA`；`access_status.json` `563A348F…6E2`；`search_log.json` `963454F7…CB0`

## 6. 下一执行者从哪里开始

1. 先读 `report_x1.md` §0/§4：**不要继续外部征询**；无 qualified/qwc candidate；DREAM 403、Dryad 401、PanThera/SAFER processed、AZ 2024 raw 无重复/暴露/功能。
2. 若 Lead 要重开 A/B/D3：按 §4 的测量规格做**新湿实验**（独立重复板/培养、暴露时间、正交功能、A0 500 键/或新关系协议）；或先把 AZ 2024 raw 作为**新关系开发矩阵**（不声称独立验证）。
3. 不把本轮"未发现"写成"不存在"；不重开 C176/C177 旧判定；不称新颖性/迁移/决策收益/机制。
