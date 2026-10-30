# PROTOCOL_E1 —— DrugComb 第二资源资格审计协议（R190 线 E1）

2026-10-27，**在运行 `e1.py` 之前冻结**。角色：数据资源资格审计员（独立于提案者；本轮不做 A2/D 设计，不跑任何效应估计或模型训练）。协议冻结后不再修改；实测结构与先验假设不符时，按 §9 如实记录，不回头改口径、不做事后调整门槛。

## 0. 范围

- 目标：为 R190 冻结结论（两药都未见时，通路粗化注释替代缺失身份，`ΔEMAX` 排序增益 ≈ +0.118）资格化**第二资源 DrugComb**。只审**结构/身份/单位/注释可行性**，回答 C155/C156 规格是否满足。
- **本协议的回答范围**：文件可获得性、解析、实体身份、cell×pair 单元、study 分层、与 Jaaks 训练集的外部重合、注释可得性、端点/单位列的存在性与语义分类。**不回答**：端点饱和性检验、测量体制可比性、效应存在性、跨数据集复现是否成立——这些是资格通过后下一轮的事。
- 输入/输出目录：`research/2026-10-27-drugcomb-qualification/`（本目录，唯一写目录；临时文件只写 `tmp/`）。不修改任何源数据、其它研究目录、`research/INDEX.md`、`SYNTHESIS.md`、`reference/`、`log/`、git。

## 1. 输入（冻结）

| 输入 | 来源 | 大小 | 校验 |
|---|---|---|---|
| A. DrugComb v1.4 summary table | Zenodo record **11102665**（与 18756096 同文件）`https://zenodo.org/api/records/11102665/files/summary_table_v1.4.csv/content` | 193,184,734 B | 官方 MD5 `c11efbdcae4a860c2374c1505a66599b`；本地 SHA256/MD5 见回执 |
| B. DrugComb v1.5 summary table | Zenodo record **15235991** `https://zenodo.org/api/records/15235991/files/summary_v_1_5.csv/content` | 1,421,694,989 B | 官方 MD5 `cd3e24758c10ffaea0124b6e80626c32`；**全文件超下载预算 → 固定分块样本（§2）**，全文件 SHA256 不计算 |
| C. DrugComb v1.5 drug identifiers | Zenodo record **18449193** `DrugComb_drug_identifiers.xlsx` | 5,856,350 B | 官方 MD5 `06894e63e5e06baa23d2bd59d6bd8808`；本地 SHA256 |
| D. DrugComb v1.5 cell-line identifiers | Zenodo record **18449193** `DrugComb_cell_line_identifiers.xlsx` | 161,434 B | 官方 MD5 `69c9b1a20cfd36cb57dd539641455534`；本地 SHA256 |
| E. NAR 2021 论文补充材料（Supplementary Table S1，37 个 study 的登记表） | Europe PMC `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8218202/supplementaryFiles` | 813,311 B | 本地 SHA256；S1 只取 paper-reported 数字 |
| F. Jaaks GDSC 组合屏（训练来源，只读身份/通路列） | `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`（及 Validation screen 同名文件） | 198,893,607 B / 11,774,397 B | 只读 `CELL_LINE_NAME`, `ANCHOR_NAME`, `LIBRARY_NAME`, `ANCHOR_PATHWAY`, `LIBRARY_PATHWAY` |
| G. 本机药物注释表（§7 冻结清单） | `data/external/` 下 7 个表 | — | 只读身份+注释列 |

**下载预算**：全部下载 ≤ 300 MB。A+D/C+E 全量；B 取固定 60 × 1,000,000 B = 60,000,000 B 分块样本。预算合计 ≈ 260 MB（`download_receipt.json` 记录逐文件 URL/字节/SHA256）。

**协议前勘察声明**：写本协议之前已做的只读勘察仅有：Zenodo/Europe PMC 检索、文件头/表头、行数与列名、v1.5 标识表读取、注释覆盖预检。这些只用于**确定文件可用性与列名**；本协议的判定门槛、分母、归一化与判定规则均在运行 `e1.py` 前写死，`e1.py` 从原始文件重新计算全部数字。

## 2. v1.5 的固定分块样本（冻结）

- 文件字节数 `S = 1,421,694,989`。`N = 60` 块，块大小 `1,000,000 B`，第 i 块起点 `start_i = round(i*S/N)`（i = 0..59），终点 `min(start_i+10^6, S)-1`。总样本 60,000,000 B ≈ 全文件 4.22%。
- 每块解析规则：从块内第一个换行字节之后开始（i=0 除外，含表头），到最后一个换行字节为止；只解析**完整行**；按 UTF-8 严格解码（换行字节不可能是多字节字符的一部分，故无截断损坏）。
- 样本只用于：列名/结构核验、study 出现与分类、组合/单药行比例估计、**cell×pair 单元的验证下界**（样本内出现的每个 (cell, 无序药对) 都是全文件中的真实单元）、GDSC/Jaaks study 名称检查。**不用于**任何响应值统计。
- 因样本是字节均匀抽样（非随机行抽样），报告为"字节均匀分块样本"，下界与比例均标注为样本口径，不外推为精确全量值。

## 3. 单元格内允许/禁止读取的字段（冻结）

**允许读取（READ，只用于身份/元数据/注释）**
- 身份：`block_id`、`drug_row`、`drug_col`、`cell_line_name`、`study_name`、`tissue_name`。
- 设计：`conc_r_unit` / `conc_c_unit`（v1.4）、`conc_row_unit` / `conc_col_unit`（v1.5）——只统计**单位字符串**取值分布，不读浓度数值。
- 注释文本：`drug_row_clinical_phase`、`drug_col_clinical_phase`、`drug_row_target_name`、`drug_col_target_name`（v1.5 summary）、标识表中的 `dname/name/target_name/clinical_phase/depmap_id/cosmic_id/tissue_id/synonyms` 等注释列。
- 表头：全部列名（用于 §8 端点语义分类，只记列名与存在性）。

**禁止读取（DENY：不转换、不聚合、不比较、不写任何输出/日志）**
- 响应/派生数值列：v1.4 `css`, `synergy_zip`, `synergy_bliss`, `synergy_loewe`, `synergy_hsa`, `ic50_row`, `ic50_col`, `ri_row`, `ri_col`, `css_row`, `css_col`, `S`；v1.5 `ic50_row`, `ic50_col`, `ri_row`, `ri_col`, `css_row`, `css_col`, `css_ri`, `S_sum`, `S_mean`, `S_max`, `synergy_zip`, `synergy_loewe`, `synergy_hsa`, `synergy_bliss`。
- 实现约束：解析时**只按列位置取 READ 列**，DENY 列的值不进入任何 Python 对象（`csv.reader` 行对象按索引取列；不使用 DataFrame 的 `.values`/数值转换）。`e1.py` 对 DENY 列的唯一访问是**表头字符串存在性**。
- 若脚本意外把 DENY 列数值读入内存或写入产物：立即停止，记入 `record.md`，不把数值写入任何产物。

## 4. 名归一与碰撞（冻结；沿用 C155 口径）

- 归一：`NFKC` → `casefold` → 只保留 `str.isalnum()` 字符。
- 多对一碰撞：同一归一名对应 ≥2 个 casefold 后不同的原始名 → 每个碰撞键逐条列出；**主计数保守剔除该键**（不参与严格交集/覆盖率的分母与分子）。碰撞逐条写入 `e1.json`。
- 报告只声明"文本同名"，不声明"生物学同一实体"；**禁止同义词推断**（不做别名合并）。DrugComb 标识表中的 `synonyms` 列只用于报告的敏感性说明，**不用于主匹配**。

## 5. 结构/身份审计的定义（冻结）

1. **组合记录**：v1.4 中 `drug_col` 不为 `NA`/`NULL`/空 的行；v1.5 同规则（`drug_row`/`drug_col` 均非空且非 `NULL`）。单药记录（709,187 行 v1.4；717,684 块 v1.5，paper-reported）不参与 cell×pair 与药物实体计数（另报）。
2. **实体数**：归一后 distinct 药物名（`drug_row`∪`drug_col`）、distinct 细胞名；另报原始名数。
3. **cell×pair 单元** = distinct `(cell_norm, unordered(drug_row_norm, drug_col_norm))`；**药对** = distinct 无序药对。v1.4 精确计算；v1.5 报样本内下界（§2）。
4. **study 分层**：v1.5 有 `study_name` 列——按 study 统计样本内组合记录数、单药记录数、distinct cell×pair 下界；v1.4 **无 study 列**（记录为结构缺口，不猜测）。paper-reported 的 v1.5 study 分层取 Supplementary Table S1（E），并与样本内 study 名逐一对表。
5. **Jaaks/GDSC 组合屏排除**：在 v1.5 记录中，`study_name` 归一后命中 `jaaks`/`gdsc`/`gdsc1`/`gdsc2` 等模式的**组合记录**整 study 排除，并报告排除的 study 列表与单元数（下界）。v1.4 无 study 列，无法逐 study 排除 → 按已知版本事实（v1.4 早于 Jaaks 2022；S1 中 GDSC1 为单药 study）记录为"排除 0 组合单元（含假设说明）"。
6. **Jaaks 外部重合**（E/F）：Jaaks 训练集细胞/药物（Original + Validation 两个 fitted 文件的身份列）与 DrugComb 细胞/药物按 §4 归一后求严格交集；逐条报告碰撞；另报与 Jaaks 训练 cell×pair 集合的键级重合（v1.4 可算精确值）。

## 6. 端点 / 单位列的存在性审计（冻结；不读数值）

- 只按**列名**做语义分类（`measured/derived/single_agent_or_control/qc_flag/annotation/design/unknown`）；禁止按数值分布反推。
- 记录：v1.4 / v1.5 summary 中"响应列存在"的清单；`css`（敏感性）、`S_*`（三档 synergy-sensitivity 复合分）、四个 synergy 指标（zip/loewe/hsa/bliss）、`ic50`、`ri` 的存在性；剂量单位列的存在（并统计单位字符串种类）；`study_name`/`tissue_name`/`clinical_phase`/`target_name` 等 study 级注释列的存在性。
- **饱和性判定留给下一轮**：本轮不读响应分布，只记录"非饱和证据可后验"所需的字段是否存在（criteria ⑤）。

## 7. 注释可行性（冻结口径）

**分母（drug universe）**
- **D1（主口径）**：v1.4 组合记录中出现的归一药物名，剔除 §4 碰撞键 → 分析表可覆盖的"参与组合的药物"全集（精确）。
- **D2（次口径）**：v1.5 标识表 `dname` 的归一集合（含单药专用药；精确）——代表 NAR 2021 版本药物全集。
- **D3（诊断）**：v1.5 样本中出现于组合记录的 distinct 归一药物名（下界，不用于判定）。

**注释来源（S，冻结清单）**——只读药物身份+注释列；匹配用 §4 严格归一名；"覆盖"要求该药在来源表中存在**非空注释**（target/moa/pathway 至少一个非空）：
1. `data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt`（Drug Repurposing Hub；`pert_iname` + `target`/`moa`）
2. `data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv`（`name` + `target`/`moa`）
3. `data/external/prism_19q4/raw/secondary-screen-replicate-collapsed-treatment-info.csv`（同上）
4. `data/external/mapkg_20261009/drug_metadata.parquet`（`drug` + `targets`/`moa-fine`）
5. `data/external/fpmtb_zenodo_7370747/File_2_Drug_library_515D.xlsx`（`Preferred name`/`Non-proprietary name` + `Mechanism/Targets`）
6. `data/external/beataml2_20261017/beataml_drug_families.xlsx`（`drug_family` sheet：`inhibitor` → `family`）
7. `data/external/gdsc_combinations/jaaks2022_figshare/*_fitted data.csv`（`ANCHOR_NAME`/`LIBRARY_NAME` + `ANCHOR_PATHWAY`/`LIBRARY_PATHWAY`；项目现用通路注释模板）

排除在"注释来源"之外（只作名称连接表，另报）：`Klaeger ChEMBL molecules.json`（无注释字段）、`tahoe_drugs.parquet`（与 MAPKG 同一 379 行表，重复）、LINCS `pert_info`（纯名称）。
**资源内注释**（另报、不计入本地来源并集）：`DrugComb_drug_identifiers.xlsx` 的 `target_name` 列（由 DrugComb 自 ChEMBL/PubChem 等整理，非独立本地表）。

**指标**：各来源对 D1 的覆盖率；本地来源**并集**对 D1 的覆盖率（主判定值）；对 D2/D3 的覆盖率（报告/条件）。另报来源可提供的**可分析水平数潜力**：`Jaaks pathway` 水平数、DRH `moa`/`target` 与 PRISM `moa`/`target` 的 distinct 水平数（只数注释字符串，不涉及响应）；"到项目通路/靶点粗化定义的映射协议"本轮不做，如本地无映射表则记为**下一轮待定条件**（任务允许）。

## 8. 端点字段语义分类（按列名冻结）

| 桶 | 判据 | 例子（仅列名） |
|---|---|---|
| identity/design | 名称/ID/study/tissue/板/块/浓度单位 | `block_id` `drug_row` `drug_col` `cell_line_name` `study_name` `tissue_name` `conc_*_unit` |
| measured/derived response（DENY） | 敏感性或协同派生量 | `css` `S_sum/mean/max` `synergy_zip/loewe/hsa/bliss` `ic50_*` `ri_*` `css_*` |
| annotation | 临床期/靶点名 | `drug_row_clinical_phase` `drug_col_clinical_phase` `drug_row_target_name` `drug_col_target_name` |
| qc_flag | 显式质控列 | v1.4/v1.5 summary **无**显式 QC 列（如 z′/flag）；只有拟合派生量（`ic50/ri`）可作间接质控线索 → 记录为缺口 |

## 9. 判定（先验冻结，只取三种）

**硬门槛**（全部通过才可能 eligible；任一失败 → `not_eligible`）

| # | 门槛 | 通过条件（冻结） |
|---|---|---|
| ① | 文件可获得且解析成功 | A/B/C/D/E 全部按 §1 取到、字节/SHA256 记录、CSV/XLSX/zip 解析成功；B 的 60 块全部成功（HTTP 206 + 完整 1,000,000 B） |
| ② | 药物/细胞名可检索 | v1.5 标识表 8,396 药/2,320 细胞中归一后非空比例 ≥99%；v1.4 组合记录两药名+细胞名归一后均非空；且可与 Jaaks 名称做归一交集（交集计算成功，碰撞逐条报告） |
| ③ | 排除 Jaaks/GDSC 组合屏后 cell×pair 单元 ≥2,000 | **主判定**：v1.5 样本中剔除 `jaaks`/`gdsc*` study 的组合记录后，样本内 distinct cell×pair 下界 ≥2,000；**佐证**：v1.4 精确组合 cell×pair（v1.4 无 study 列，按 §5.5 记录排除 0 的假设与依据）也 ≥2,000 |
| ④ | 存在可覆盖 ≥50% 药物的粗注释来源 | 本地来源并集对 **D1** 的覆盖率 ≥50%（严格归一名 + 非空注释）；且报告 ≥12 水平潜力（若到项目定义的映射协议本地不存在，则明确记为下一轮待定条件——任务允许，不单独否决） |
| ⑤ | 非饱和证据可后验 | v1.4 与 v1.5 summary 的响应/派生列存在（只按列名）；`study_name`/`tissue_name`/`target_name`/`clinical_phase` 等 study 级注释列存在；本轮不读响应分布，饱和性检验留待下一轮 |

**判定映射**
- `eligible`：①–⑤ 全通过，且无重大条件；
- `eligible_with_conditions`：①–⑤ 全通过，但存在**重大条件**（必须逐条列出，如：v1.5 全文件超下载预算需分块/流式访问；注释覆盖率贴近门槛或对 D2 不足；通路映射协议待定；饱和性检验待做；与 Jaaks 实体重合需按未见实体切分）；
- `not_eligible`：任一硬门槛失败（记录失败类别与解冻条件）。

**失败类别**（沿用 C155 词汇）：`data_unavailable` / `assumption_contradicts` / `data_insufficient` / `evaluation_cannot_distinguish` / `transfer_unsupported`。

## 10. 确定性与产物

- `e1.py` 只读本地文件（不联网），确定性：JSON key 排序、无时间戳、无随机；输入/脚本/协议 SHA256 写入 `e1.json`。
- 产物：`PROTOCOL_E1.md`（本文件）、`fetch_data.py`、`download_receipt.json`、`e1.py`、`e1.json`、`report.md`、`record.md`、`usage.json`。
- `record.md` 记录：协议前勘察、实际命令与耗时、观测、决定、局限、预算。
- `usage.json`：token/费用等运行时不可得数值记 `null`（不记 0）。

## 11. 明确不做

不读响应数值做任何统计；不训练模型；不跑效应估计/相关性/预测性能；不联网提交数据；不修改源数据；不把"没找到"写成"不存在"（检索缺口逐条记录）；不重开 I003/预测方差/ComboCat A2；不做机制/靶点/临床主张。
