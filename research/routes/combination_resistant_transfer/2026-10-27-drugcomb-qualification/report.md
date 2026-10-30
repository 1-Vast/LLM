# DrugComb 第二资源资格审计报告（R190 线 E1）

2026-10-27。角色：数据资源资格审计员（独立于提案者；本轮不做 D 线设计、不训练模型、不跑任何效应估计）。本报告只回答 **R190 冻结结论（两药都未见时，通路粗化注释替代缺失身份，`ΔEMAX` 排序增益 ≈ +0.118）能否以 DrugComb 作为第二资源复现** 所需的**结构/身份/单位/注释可行性**；不读响应数值做任何统计，不回答端点饱和性、测量体制可比性与效应存在性。

- 冻结协议：[PROTOCOL_E1.md](PROTOCOL_E1.md)（运行前冻结；SHA256 `48f310028de08f3d11b634d9998ea20055d8a3de41dcf45afb6d347a61cca890`）
- 审计脚本：[e1.py](e1.py)（SHA256 `7684556dd766f0a0adb0fec030bcfe69177b99d30195863ef9f5c7fed5d2d916`），离线、确定性；结果：[e1.json](e1.json)（SHA256 `2FD636D84E8BEC816BCC429B691D962ED90D4B07FFF88608DB99C2BB49219DDB`，连续两次重跑逐字节相同）
- 取数脚本：[fetch_data.py](fetch_data.py)；下载回执：[download_receipt.json](download_receipt.json)；时间线/预算/决定：[record.md](record.md)；运行时账：[usage.json](usage.json)

## 0. 判定（PROTOCOL_E1 §9 冻结门槛，不做事后调整）

**`eligible_with_conditions`**（五道硬门槛全部通过；列出条件 1–7，见 §9）。

| # | 门槛 | 实测 | 结果 |
|---|---|---|---|
| ① | 文件可获得且解析成功 | 4 个冻结输入全部取到、字节/哈希核验通过；v1.5 summary 60/60 分块成功（HTTP 206）；v1.4 summary 全量解析 1,175,220 行 | **通过** |
| ② | 药物/细胞名可检索（归一后非空、可做交集） | v1.5 标识表 8,396 药 / 2,320 细胞归一后非空率 **100% / 100%**；v1.5 样本中细胞名对标识表匹配 **100%**、药名匹配 **100%**；v1.4 组合行两名+细胞名归一后全非空；与 Jaaks 归一交集计算成功（碰撞逐条报告） | **通过** |
| ③ | 排除 Jaaks/GDSC 组合屏来源后 cell×pair 单元 ≥2,000 | **v1.4 精确=380,418**；**v1.5 样本剔除 GDSC/Jaaks 组合 study 后下界=29,028**（样本内 GDSC 模式 study 组合行=0）；阈值 2,000 的 **14.5×–190×** | **通过** |
| ④ | 存在可覆盖 ≥50% 药物的粗注释来源 | 本地注释来源并集对 **D1（v1.4 组合药物全集，4,076）= 51.28%**（2,090 药）；≥12 水平潜力：DRH MoA 1,436 水平、PRISM MoA 1,072、Jaaks 通路 21 文本水平（双侧 one-hot=38）等；到项目通路定义的映射协议本地不存在 → 条件 | **通过（边际）** |
| ⑤ | 非饱和证据可后验 | v1.4 有 12 个响应/派生列（`css`、4 个 synergy、`S`、`ic50_*`、`ri_*`、`css_*`）；v1.5 有 14 个；v1.5 有 `study_name`/`tissue_name`/`clinical_phase`/`target_name` 等 study 级注释列；**无显式 QC flag 列**；饱和性检验按协议留待下一轮 | **通过** |

## 1. 方法与边界

- 输入：DrugComb 官方 Zenodo 记录（v1.4 summary、v1.5 summary、v1.5 标识表）+ NAR 2021 论文补充材料（Europe PMC）。`drugcomb.org` / `drugcomb.fimm.fi` / `api.drugcomb.org` 在本机不可达（HTTPS `UNEXPECTED_EOF` / 连接失败），**未使用**；全部数字来自 Zenodo 官方文件与 Europe PMC。
- 只读**身份/注释/单位字符串**列；响应列（`css`、`synergy_*`、`S_*`、`ic50_*`、`ri_*`、`css_*`）在 `e1.py` 中只以**表头字符串**出现，从不索引其数值（PROTOCOL_E1 §3）。
- 归一：`NFKC → casefold → 仅保留字母数字`；同一归一名对应 ≥2 个 casefold 后不同的原始名 = 碰撞键，**保守剔除**（C155 口径）。
- v1.4 summary 全量（193 MB）；v1.5 summary 1.42 GB 超下载预算 → 固定 60×1,000,000 B 字节均匀分块样本（4.22%），只用于结构与下界，不外推为全量精确值（PROTOCOL_E1 §2）。
- 未做：任何响应值统计/建模、效应估计、A2/D 线设计、机制/临床推断；未修改源数据与其它研究目录。

## 2. 文件与下载回执（全部 ≤300 MB 预算）

| 文件 | URL | 字节 | 官方 MD5 | 本地 SHA256 |
|---|---|---|---|---|
| v1.4 summary table | `https://zenodo.org/api/records/11102665/files/summary_table_v1.4.csv/content` | 193,184,734 | `c11efbd…66599b` ✓ | `e08e3d35bfa4bea011afe1b05b7025acde5c669c5e8d265866b5e12b08037a2f` |
| v1.5 drug identifiers | `https://zenodo.org/api/records/18449193/files/DrugComb_drug_identifiers.xlsx/content` | 5,856,350 | `06894e6…d8808` ✓ | `02b1655ad15a81e0bef06909e147ff4c688938aa7f75eb04603f440e8b18438c` |
| v1.5 cell-line identifiers | `https://zenodo.org/api/records/18449193/files/DrugComb_cell_line_identifiers.xlsx/content` | 161,434 | `69c9b1a…455534` ✓ | `88c7c2a06351e715f1f5c276a98d049fbe33d038516f711b8d9a166e11cd045d` |
| NAR 2021 补充表 S1（Europe PMC） | `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8218202/supplementaryFiles` | 813,311 | — | `0df53c73d5f3caf0f147ac89c232167c79239d285a99170b60bb9767ef3c6465` |
| v1.5 summary table（**分块样本**） | `https://zenodo.org/api/records/15235991/files/summary_v_1_5.csv/content` | 全文件 1,421,694,989；取 60,000,000 | `cd3e247…26c32` | 全文件 SHA256 **null**（不完整）；逐块 SHA256 见回执 |

- **下载总量 260,015,829 B（260.0 MB）** + 两篇论文 fullTextXML 208,064 B（用于已发布事实，未入回执）= **260.2 MB ≤ 300 MB**。
- v1.4 文件同时出现在记录 18756096 与 11102665（MD5 相同）；采用记录 11102665（记录 18449193 的说明里指定的 v1.4 summary 官方位置）。
- 版本归属：记录 18449193 明确写 "raw data of DrugComb v1.4 … For the summary level data: v1.4 → record 11102665, v1.5 → record 15235991"；记录 15235991 的 version=1.5。
- 分块样本：i=0..59，起点 `round(i*1,421,694,989/60)`，每块 1,000,000 B，逐块 HTTP 206 校验 + SHA256；文件级 SHA256 因未全量下载记 `null`（未知记 null，不猜）。

## 3. 结构、单位与规模

### 3.1 列结构（按列名冻结分类；数值未读）

| 桶 | v1.4 summary（18 列） | v1.5 summary（26 列） |
|---|---|---|
| identity/design | `block_id`, `drug_row`, `drug_col`, `cell_line_name`, `conc_r_unit`, `conc_c_unit` | 加 `study_name`, `tissue_name`, `conc_row_unit`, `conc_col_unit` |
| response/derived（**仅表头存在性**） | `css`, `synergy_zip/bliss/loewe/hsa`, `ic50_row/col`, `ri_row/col`, `css_row/col`, `S`（12） | `ic50_row/col`, `ri_row/col`, `css_row/col`, `css_ri`, `S_sum/mean/max`, `synergy_zip/loewe/hsa/bliss`（14） |
| annotation | — | `drug_row_clinical_phase`, `drug_col_clinical_phase`, `drug_row_target_name`, `drug_col_target_name` |
| QC flag | **无显式 QC 列**（只有 ic50/ri 等拟合派生量可作间接线索） | 同左 |

- **单位**：v1.4 两列浓度单位全部为 `uM`（466,033/466,033 组合行）；v1.5 样本组合行出现 **`uM` 31,948 / `µM` 773** 两种微摩尔字符串（微符号不统一；本轮不读浓度数值，只记录单位字符串）。响应列本身无显式单位列，语义按已发表口径为 % inhibition / synergy score（reported，未核验）。

### 3.2 v1.4 summary（全量精确）

| 指标 | 值 |
|---|---|
| 数据行 / distinct `block_id` | 1,175,220 / 1,175,220（`block_id` 1–1,176,501） |
| 单药式记录（`drug_col ∈ {NA, NULL, 空}`） | 709,187 |
| **组合记录** | **466,033** |
| 药物实体（组合行） | 原始名 **4,150**；归一名 **4,088**（12 个碰撞键，见 §4） |
| 细胞实体（组合行） | 原始名 **112**（无碰撞） |
| 无序药对 | **62,826**；平均每对 6.06 个细胞 |
| **cell×pair 单元（归一、无序）** | **380,418** |
| `study_name` 列 | **不存在**（结构缺口，见 §5.3） |

### 3.3 v1.5 summary（1.42 GB，分块样本 + 论文 S1）

- 样本 60 块 = 60,000,000 B = 全文件 **4.22%**；解析出 **61,872 行**（组合 32,721 / 单药 29,151，组合占比 52.88%）。
- 样本内 **19 个 study**（对 S1 的 37 个 study；小 study 未被字节样本覆盖，见附录 B——**是抽样覆盖缺口，不是"不存在"**）。
- 样本内细胞名/药名对 v1.5 标识表匹配率均 **100%**；`drug_*_target_name` 非空行 93.1%、`drug_*_clinical_phase` 非空行 99.98%。
- **paper-reported（S1，37 study）**：组合块 **751,498** + 单药块 **717,684** = **1,469,182** 块；2,320 细胞系、8,397 药物（S1 数字与本轮字母表解析逐项吻合，见 §4.3）。
- **v1.5 样本 cell×pair 下界（剔除 GDSC/Jaaks 组合 study 后）= 29,028**（样本内每一 (cell, 无序药对) 都是全文件真实单元，故为严格下界）。全量 v1.5 cell×pair 精确值未得（分块样本 + 预算所限），记 `null`，只报下界。

## 4. 实体身份

### 4.1 v1.5 标识表（全量）

| 项 | 值 |
|---|---|
| 药物行 / distinct `dname`（原始） | 8,396 / 8,272 |
| 药物归一名 | **8,251**；128 个归一名碰撞键（保守剔除） |
| `target_name` 非空 | **4,442（52.91%）**；`target_type` 80 水平；`clinical_phase` 6,082 非空（0–4 五档） |
| 细胞行 | **2,320**；归一名 2,315；5 个碰撞键 |
| 细胞外部 ID | DepMap `ACH-*` **1,475**、COSMIC **1,002**、Cellosaurus **1,659**、`tissue_id` **2,313（34 组织水平）** |
| 论文 vs 文件 | 论文报 8,397 药；标识表 8,396 行（**差 −1，未解释，记为缺口**） |

### 4.2 名称碰撞（归一后多对一；主计数保守剔除）

- v1.4 组合药物：12 个碰撞键，例如 `10-DEACETYLBACCATIN-III`/`10-Deacetylbaccatin III`、`BIBR 1532`/`BIBR-1532`、`BIX 01294`/`BIX-01294`、`(+)-Blebbistatin`/`(-)-BLEBBISTATIN`（后者为**真正的异构体对**，注释/匹配时必须剔除）。完整清单见 `e1.json → v1.4_summary.drug_collisions`。
- v1.5 标识表：药物 128、细胞 5 个碰撞键；完整清单见 `e1.json → v1.5_identifiers`（仅计数）。
- Jaaks 身份列：细胞/药物碰撞键均为 **0**。
- 区分大小写的同名变体（如 `CARBOPLATIN`/`carboplatin`）在 `casefold` 后相同，按 C155 口径**不算**碰撞（同实体大小写变体）。

### 4.3 study 分层（v1.5；S1 全表见附录 A）

- S1 解析复算：组合块 751,498 / 单药块 717,684 / 合计 1,469,182，**与论文完全一致**；分类规则：`data_source==PharmacoDB` 或 study ∈ {BEATAML, TOURET, GORDON, ELLINGER} 记为单药。唯一与"矩阵 Nx1 启发式"分歧：`FALLAHI-SICHANI`（`10x1, 20x1`，111 块）——按论文总数必须记为**组合**（说明该 study 是单浓度-组合设计），已按此冻结并在 `e1.json` 记录分歧。
- v1.5 样本内按 study 的 cell×pair 下界见附录 B（19/37 study）；未抽样到的 18 个 study 都是小 study（S1 每 study 块数 ≤1,910，合计约 18k 块，占全量约 1.2%）。

## 5. Jaaks/GDSC 组合屏排除 与 外部重合

### 5.1 排除判定

- v1.5 study 名单（S1，37 个）中**没有 `Jaaks`**；唯一匹配 `GDSC` 模式的是 **`GDSC1`**（PharmacoDB 来源，矩阵 `5x1, 9x1` = **单药剂量-反应**，225,480 块）。v1.5 样本内 `GDSC1` 11,575 行**全部为单药记录、组合行 0** → **按 study 排除的组合单元 = 0**。
- 依据：① NAR 2021（v1.5 发布于 2021-03）**早于 Jaaks 2022**；② S1 中 GDSC1 为单药 study；③ v1.5 样本 0 组合行。**没有发现任何 Jaaks/GDSC 组合屏来源**——是"本轮版本内未发现"，不是"证明全库不存在"。
- v1.4 summary **无 study 列**：无法逐 study 排除；按"v1.4 是 v1.5 之前版本、其组合块 `block_id ≤ 1,176,501`（早于 v1.5 新增 study 的 `block_id` 段）"记录排除为 **0**（含假设说明，见条件 6）。

### 5.2 与 Jaaks 训练资源的实体重合（严格归一名；禁止同义词推断）

Jaaks 本地 fitted 表身份列（Original + Validation，**不读响应**）：Original 296,707 行 / **125 细胞** / **65 药物** / 108,259 个 (cell, anchor, library) 有序键 / 70,360 个 (cell, 无序药对) 归一单元；Validation 23,505 行 / 97 细胞 / 45 药物 / 4,933 有序键 / 3,836 单元；并集 **126 细胞 / 65 药物 / 70,439 单元**。

| 交集 | 值 | 占 v1.4 | 占 Jaaks |
|---|---|---|---|
| 细胞（v1.4 组合 112 个 vs Jaaks 126 个） | **18** | 16.07% | 14.29% |
| 药物（v1.4 组合 4,088 个 vs Jaaks 65 个） | **40** | 0.98% | **61.54%** |
| (cell, 无序药对) 单元键（v1.4 380,418 vs Jaaks 70,439） | **241** | 0.063% | 0.34% |
| v1.5 标识表（2,315 细胞 / 8,251 药）vs Jaaks | 细胞 **124** / 药物 **54** | — | — |

**读法**：DrugComb 与 Jaaks 训练集不是"无实体重叠"——细胞 18/112、药 40/4,088、单元键 241；但 Jaaks 的 65 个药物中 40 个（61.5%）在 DrugComb v1.4 出现，细胞有 18 个共同。复现时若要声称"未见实体"，必须由下一轮协议冻结 unseen-entity 切分（见条件 5）。

## 6. 注释可行性

**分母**：D1 = v1.4 组合药物归一名剔除碰撞键 = **4,076**（主口径，分析表可覆盖的参与组合药物）；D2 = v1.5 标识表药物归一名 = **8,251**（次口径，含单药专用药）。**匹配**：严格归一名相等，且来源表该药有非空注释；不做同义词合并。

| 本地来源 | 行数 | 有注释行 | 注释字段/水平 | D1 覆盖 | D2 覆盖 |
|---|---|---|---|---|---|
| Drug Repurposing Hub（`data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt`） | 6,798 | 6,330 | `target` 2,216 水平 / `moa` 1,436 水平 | **1,982（48.63%）** | 3,889（47.13%） |
| PRISM primary treatment info | 4,686 | 4,400 | `target` 1,829 / `moa` 1,072 | 1,620（39.74%） | 2,914（35.32%） |
| PRISM secondary treatment info | 13,008 | 12,576 | `target` 790 / `moa` 530 | 702（17.22%） | 1,016（12.31%） |
| MAPKG `drug_metadata.parquet`（=Tahoe drugs 同表） | 379 | 379 | `targets` 189 / `moa-fine` 26 | 196（4.81%） | 259（3.14%） |
| FPMTB 515 药库 | 515 | 515 | `Mechanism/Targets`；`Drug_Sub_Class` 61 / `Drug_Class` 11 | 317（7.78%） | 417（5.05%） |
| BeatAML drug families | 395 | 395 | `family` 86 水平 | 78（1.91%） | 56（0.68%） |
| Jaaks 通路模板（**项目现用注释**，`ANCHOR_PATHWAY`/`LIBRARY_PATHWAY`） | 320,212 | 65 药 | **21 文本水平**；双侧 one-hot = **38 列**（17+21，与 SYNTHESIS 的"38 通路水平"一致） | **40（0.98%）** | 54（0.65%） |
| **本地并集** | — | — | — | **2,090（51.28%）** | **4,053（49.12%）** |
| 资源内注释（不计入本地并集）：v1.5 标识表 `target_name` | 8,396 | 4,442 | 靶点名（80 个 `target_type`） | 1,969（48.31%） | 4,419（53.56%） |

- 门槛值 51.28%，**距 50% 仅 +1.28 pp（52 个药物）**；累计贡献：DRH 48.63 → +PRISM 49.14 → +MAPKG 49.85 → +FPMTB 50.59 → +BeatAML 51.25 → +Jaaks 51.28（**过线依赖后三个小表**）。
- **≥12 水平潜力**：多个来源有 ≥12 的可分析水平（DRH MoA 1,436、PRISM MoA 1,072、BeatAML family 86 等），但**都不是项目冻结结论所用的"通路"语义**（项目通路 = Jaaks `ANCHOR_PATHWAY`/`LIBRARY_PATHWAY` 的 38 个双侧 one-hot 列）。把 MoA/靶点粗化为 ≥12 个"通路样"水平需要一份**可审计的映射表**（target→pathway / MoA→pathway），**本机没有**；Jaaks 通路模板本身只覆盖 DrugComb 药物的 0.98%。→ 按任务允许的口径记入**下一轮映射协议条件**，本轮不否决。
- **补充诊断（非判定项）**：按 v1.4 组合块加权，本地并集能同时注释**两药**的块 = **45.23%**（至少一药 = 88.83%）；即"药物数覆盖 51.28%"对应的"组合行覆盖"更低（45.23%），下一轮若用块级分析需注意。
- **口径敏感性（供 Lead 决定，不改变冻结判定）**：若把 ④ 收紧为"必须提供**项目同款通路标签**"，则覆盖率 = **0.98%**，④ 不满足 → 判定将转为 `not_eligible`，解冻条件为"提供可覆盖 ≥50% DrugComb 药物、≥12 个可分析通路水平的可审计映射表"。

## 7. 端点与测量体制（只记存在性/语义，未读数值）

- v1.4 有 12 个响应/派生列：`css`（组合敏感性）、`synergy_zip/bliss/loewe/hsa`（4 个协同指标）、`ic50_row/col`、`ri_row/col`、`css_row/col`、`S`。
- v1.5 有 14 个：`ic50_row/col`、`ri_row/col`、`css_row/col`、`css_ri`、`S_sum/mean/max`（synergy-sensitivity 三档复合分）、`synergy_zip/loewe/hsa/bliss`。
- **无显式 QC flag 列**（无 z′/flag 一类）；study 级信息 = `study_name` + `tissue_name` + 每行的 `drug_*_clinical_phase`/`drug_*_target_name`（v1.5）。
- **端点可比性（协议 §0 明确不回答，但必须作为下一轮前置条件记录）**：DrugComb summary 提供的是 css/S/synergy 分数，**不直接提供项目冻结结论所用的 `SYNERGY_DELTA_EMAX`（ΔEMAX）**；能否由 summary 派生 ΔEMAX 等价量（或必须取 2 GB 的 raw dose-level 数据、逐剂量重拟合）本轮**未核验**。这是"资格通过"之后**必须先冻结的端点映射协议**，不是本轮判定项。

## 8. C155/C156 规格对照

| C156 规格 | 本轮实测 | 判定 |
|---|---|---|
| 身份可连接（药物/细胞名/粗注释） | 名称 100% 可归一、v1.5 标识表含 DepMap/COSMIC/Cellosaurus/tissue；name↔summary 匹配 100%；注释见 §6 | 满足（注释语义见条件） |
| 总 cell×pair ≈2,000–5,000（为 20–40% 留药下 both-unseen ≥800） | v1.4 精确 **380,418**；v1.5 样本下界 **29,028**、paper 组合块 751,498；两者都远超区间上沿（区间是**下沿要求**，不是上限） | **满足（超出 1–2 个数量级）** |
| both-unseen 可行性（v1.4 精确、确定性字典序留出） | r=0.20: k=818 → **16,078** cell×pair 单元 / 2,671 药对；r=0.30: k=1,226 → **33,148** / 5,853；r=0.40: k=1,635 → **52,368** / 8,535 | 满足（≥800 的 20–65 倍） |
| 非饱和端点 | 响应列存在、可后验；未读值；无 QC flag 列 | 待下一轮（条件 4） |
| 与本项目训练集无实体重叠 | **不满足**：细胞 18、药物 40、cell×pair 键 241 与 Jaaks 重合 | 需 unseen-entity 切分（条件 5） |

## 9. 门槛判定、条件、失败类别与解冻条件

**判定：`eligible_with_conditions`。** 失败类别：**无**（五道门槛全过；不触发 `data_unavailable`/`assumption_contradicts`/`data_insufficient`/`evaluation_cannot_distinguish`）。

**条件（必须随结论一起传递，缺一不可）**

1. **v1.5 全表未全量核验**：1.42 GB 超出 ≤300 MB 预算 → 只取 4.22% 字节分块样本，文件级 SHA256=`null`（官方 MD5 已记录）。v1.5 的 cell×pair 是**下界**；当前"端到端全量核验的分析表"是 **v1.4 summary（193 MB 全量）**。若下一轮要用 v1.5 全表，需冻结分块/流式访问协议并补齐全表哈希。
2. **注释覆盖边际**：本地并集对 D1 = 51.28%（仅超线 +1.28 pp，过线依赖 FPMTB/BeatAML/Jaaks 三个小表）；对 D2（v1.5 药全集）= **49.12% < 50%**。若用 v1.5 全集，需扩展来源或把分析宇宙限定到组合药物集。
3. **通路映射协议待定**：本地无 "MoA/靶点 → 项目 38 通路水平" 的可审计映射；Jaaks 通路模板只覆盖 0.98% 药物。下一轮必须先冻结映射协议（并在 DrugComb 药物上验证 ≥12 个可分析水平）。
4. **端点饱和性未测**：本轮按协议不读响应值；必须先做饱和性/测量体制检查（含 §7 的 ΔEMAX 可派生性问题）。
5. **实体重叠**：与 Jaaks 细胞 18、药物 40、单元键 241 重合 → 必须冻结 unseen-entity 切分（both-unseen 或 external-only）。
6. **v1.4 无 study 列**：Jaaks/GDSC 的 study 级排除只能在 v1.5 上做（v1.5 样本中 GDSC1 组合行=0）；v1.4 的"排除 0"依赖版本先验（见 §5.1），不能逐 study 复核。
7. **标识表碰撞**：药物 128 / 细胞 5 个归一名碰撞键，严格匹配已保守剔除。

**若 Lead 把 ④ 收紧为"项目同款通路标签"** → `not_eligible`（失败类别 `data_insufficient`），解冻条件：提供覆盖 ≥50% DrugComb 药物、≥12 个可分析通路水平、可审计的映射表（或 DrugComb 原生通路注释）。

**未触发但需记录的解冻方向**（若后续发现本轮未覆盖的问题）：任何"响应列不可用/无 study 级 QC"的发现都会把 ⑤ 降级。

## 10. 局限与检索缺口

- **网络缺口**：`drugcomb.org`、`drugcomb.fimm.fi`、`api.drugcomb.org` 本机不可达（HTTPS `UNEXPECTED_EOF`/连接失败）；未取得门户的 per-study 下载页、API 的 study 列表与 QC 字段。**"没找到"≠"不存在"**。
- **版本缺口**：v1.5 full summary 未全量下载；v1.4 summary 无 study 列；论文报 8,397 药 vs 标识表 8,396 行（−1 未解释）；摘要表文件名/版本对应关系依赖 Zenodo 记录说明与 MD5 交叉核对。
- **抽样缺口**：v1.5 字节样本覆盖 19/37 study（未覆盖的 18 个都是小 study）；样本只给下界，不给全量精确 cell×pair；分块样本的 study 内单元数是"样本内下界"，不是"该 study 全量"。
- **注释缺口**：只用严格归一名；未使用同义词/ChEMBL ID/结构匹配（禁止同义词推断），因此覆盖率可能**低估**；`data/knowledge/` 为空（任务点名的目录之一无内容），注释来源全部来自 `data/external/`；MoA/target 语义与项目通路语义之间无本地映射。
- **端点缺口**：响应数值未读（按协议），饱和性、指标冗余、ΔEMAX 等价性、测量体制可比性都未核验。
- **Jaaks 口径**：本地 fitted 表 Original 296,707 行 / 125 细胞 / 65 药物 / 108,259 有序 (cell,anchor,library) 键（与 BRIEF 的 108,259 键一致）/ 70,360 无序单元（C155 报告的 67,812/121 细胞来自先前口径，未追查差异）；本报告只用本轮实测身份列。
- 判定是**资源资格**结论，不是对 DrugComb 科学价值的评价；不构成机制/靶点/临床主张。

## 11. 复现

```powershell
cd D:\MAESTRO
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-drugcomb-qualification\fetch_data.py   # 取数（幂等；固定 URL/分块）
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-drugcomb-qualification\e1.py           # 审计（离线、确定性）
```

- `e1.py` 实测耗时：**22.5–27.2 s**（v1.4 流式解析 ~10 s、Jaaks 身份列 ~8 s、v1.5 分块 ~2 s、注释表 ~4 s、其余 ~3 s）。
- 两次连续运行 `e1.json` SHA256 一致（`2FD636D8…19DDB`）；输入/协议/脚本 SHA256 均写在 `e1.json`。
- 响应保护：`e1.py` 对响应列只读取表头字符串，输出中 grep 复核未出现任何响应值。

## 附录 A：v1.5 的 37 个 study（Supplementary Table S1，paper-reported；本轮按字母表复算合计与论文一致）

| study | disease | data source | PubMed | blocks | cell lines | tissues | matrix | type |
|---|---|---|---|---|---|---|---|---|
| ONEIL | Cancer | Publication | 26983881 | 92208 | 39 | 6 | 5x5 | combo |
| CLOUD | Cancer | Publication | 28530711 | 40160 | 1 | 1 | 2x2 | combo |
| ALMANAC | Cancer | Publication | 28446463 | 311604 | 60 | 9 | 4x4, 4x6 | combo |
| FORCINA | Cancer | Publication | 28601558 | 1818 | 1 | 1 | 2x2 | combo |
| NCATS_ATL | Cancer | NCATS Tripod | - | 30 | 1 | 1 | 10x10 | combo |
| MATHEWS | Cancer | NCATS Tripod | 24469833 | 1119 | 1 | 1 | 6x6, 10x10 | combo |
| NCATS_DIPG | Cancer | NCATS Tripod | - | 8854 | 2 | 2 | 6x6, 10x10 | combo |
| NCATS_ES(FAKI/AURKI) | Cancer | NCATS Tripod | - | 1910 | 1 | 1 | 6x6 | combo |
| NCATS_ES(NAMPT+PARP) | Cancer | NCATS Tripod | - | 4628 | 4 | 3 | 6x6, 10x10 | combo |
| WILSON | Cancer | NCATS Tripod | 30289729 | 764 | 2 | 1 | 6x6, 10x10 | combo |
| NCATS_HL | Cancer | NCATS Tripod | - | 2694 | 4 | 2 | 6x6, 10x10 | combo |
| YOHE | Cancer | NCATS Tripod | 29973406 | 270 | 3 | 2 | 10x10 | combo |
| NCATS_2D_3D | Cancer | NCATS Tripod | - | 70 | 2 | 2 | 10x10 | combo |
| PHELAN | Cancer | NCATS Tripod | 29925955 | 62 | 1 | 1 | 10x10 | combo |
| NCATS_MDR_CS | Cancer | NCATS Tripod | - | 68 | 2 | 1 | 10x10 | combo |
| CCLE | Cancer | PharmacoDB | 22460905 | 11670 | 503 | 24 | 6x1, 7x1, 8x1 | mono |
| CTRPV2 | Cancer | PharmacoDB | 26482930 | 395263 | 887 | 24 | 8x1 ~ 29x1 | mono |
| FIMM | Cancer | PharmacoDB | 24056683 | 2561 | 50 | 5 | 5x1 | mono |
| GCSI | Cancer | PharmacoDB | 27193678 | 6455 | 409 | 23 | 8x1, 9x1 | mono |
| GDSC1 | Cancer | PharmacoDB | 23180760 | 225480 | 1074 | 30 | 5x1, 9x1 | **mono** |
| GRAY | Cancer | PharmacoDB | 24176112 | 9413 | 70 | 2 | 9x1 | mono |
| UHNBREAST | Cancer | PharmacoDB | 26771497 | 52 | 15 | 1 | 9x1, 18x1 | mono |
| BEATAML | Cancer | Publication | 30333627 | 59348 | 528 | 1 | 7x1 | mono |
| FLOBAK | Cancer | Publication | 31664030 | 9984 | 8 | 7 | 6x6 | combo |
| ASTRAZENECA | Cancer | AstraZeneca | 31209238 | 20482 | 153 | 10 | 6x6 | combo |
| FRIEDMAN | Cancer | Publication | 26461489 | 208008 | 36 | 1 | 3x3 | combo |
| SCHMIDT | Cancer | Publication | 24101737 | 100 | 5 | 1 | 8x8 | combo |
| MILLER | Cancer | Publication | 24065146 | 82 | 1 | 1 | 8x8 | combo |
| FRIEDMAN2 | Cancer | Publication | 28446504 | 28500 | 10 | 1 | 3x3 | combo |
| TOURET | SARS-CoV-2 | Publication | 32753646 | 1520 | 1 | 1 | 1x1 | mono |
| GORDON | SARS-CoV-2 | Publication | 32353859 | 290 | 1 | 1 | 5x1, 6x1, 7x1 | mono |
| ELLINGER | SARS-CoV-2 | ChEMBL | - | 5632 | 1 | 1 | 1x1 | mono |
| MOTT | Malaria | NCATS Tripod | 26403635 | 17072 | 3 | 1 | 6x6, 10x10 | combo |
| NCATS_SARS-COV-2DPI | SARS-CoV-2 | NCATS Tripod | - | 206 | 1 | 1 | 6x6 | combo |
| BOBROWSKI | SARS-CoV-2 | NCATS Tripod | 32637956 | 262 | 1 | 1 | 6x6 | combo |
| DYALL | Ebola | NCATS Tripod | 29939303 | 432 | 2 | 2 | 6x6 | combo |
| FALLAHI-SICHANI | Cancer | Publication | 28069687 | 111 | 5 | 1 | 10x1, 20x1 | combo* |

\* 矩阵启发式判 mono，但按论文总数（751,498/717,684）必须记 combo；已在 `e1.json → s1_study_table.mono_combo_classification_divergences` 记录。

## 附录 B：v1.5 分块样本覆盖的 19 个 study（样本口径下界，非全量）

| study | sample rows | combo rows | mono rows | sample cell×pair 下界 | cells | drugs | block id range |
|---|---|---|---|---|---|---|---|
| ALMANAC | 13494 | 13494 | 0 | 13397 | 19 | 103 | 132375–443923 |
| ASTRAZENECA | 585 | 585 | 0 | 572 | 3 | 82 | 1186503–1206937 |
| BEATAML | 2776 | 0 | 2776 | 0 | 0 | 0 | — |
| CCLE | 418 | 0 | 418 | 0 | 0 | 0 | — |
| CLOUD | 1450 | 1450 | 0 | 1450 | 1 | 270 | 100338–132368 |
| CTRPV2 | 13378 | 0 | 13378 | 0 | 0 | 0 | — |
| DYALL | 213 | 213 | 0 | 97 | 1 | 17 | 1468640–1469065 |
| FIMM | 224 | 0 | 224 | 0 | 0 | 0 | — |
| FLOBAK | 825 | 825 | 0 | 171 | 1 | 19 | 1185239–1186395 |
| FRIEDMAN | 10024 | 10024 | 0 | 10024 | 20 | 108 | 1206978–1414958 |
| FRIEDMAN2 | 889 | 889 | 0 | 889 | 3 | 76 | 1420339–1443607 |
| GCSI | 368 | 0 | 368 | 0 | 0 | 0 | — |
| GDSC1 | 11575 | 0 | 11575 | 0 | 0 | 0 | — |
| GRAY | 412 | 0 | 412 | 0 | 0 | 0 | — |
| MATHEWS | 857 | 857 | 0 | 708 | 1 | 477 | 451709–465929 |
| MOTT | 1901 | 1901 | 0 | 1051 | 2 | 124 | 1452133–1467211 |
| NCATS_MDR_CS | 68 | 68 | 0 | 60 | 2 | 17 | 466192–466259 |
| ONEIL | 2353 | 2353 | 0 | 588 | 4 | 38 | 689–91284 |
| PHELAN | 62 | 62 | 0 | 31 | 1 | 16 | 445791–445852 |

未覆盖的 18 个 study（**抽样缺口，不是不存在**）：BOBROWSKI、ELLINGER、FALLAHI-SICHANI、FORCINA、GORDON、MILLER、NCATS_2D_3D、NCATS_ATL、NCATS_DIPG、NCATS_ES(FAKI/AURKI)、NCATS_ES(NAMPT+PARP)、NCATS_HL、NCATS_SARS-COV-2DPI、SCHMIDT、TOURET、UHNBREAST、WILSON、YOHE。
