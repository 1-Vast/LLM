# R195-A3 报告：条件级跨 screen 复验的资源资格审计（metadata-only）

2026-10-27。角色：独立资源资格审计员（不参与 A0/A1/A2/Q 设计，不估 Q、不训练）。工作目录 `D:\MAESTRO`。
**协议**：[PROTOCOL_A3.md](PROTOCOL_A3.md)（v1 **FROZEN**，SHA256 `E7E6ED2D2CD2836CF28B9F5299EC99374889B8D7DB5F38287C64783A3D8AD2AB`，在任何 A3 匹配计数之前冻结；偏离=无）。
**产物**：[a3.py](a3.py)（`CDFEA4F1…D2F5F9FA`）、[a3.json](a3.json)（`B466FE87…B1F6566`）、`a3_overlap/` 派生表与下载回执、[record_a3.md](record_a3.md)、[usage_a3.json](usage_a3.json)。

## 0. 判定

# `not_qualified`

| 门槛 | 阈值 | 实测（主候选 DrugComb v1.5） | 结果 |
|---|---|---|---|
| G1 独立测量组 | ≥2 个独立组合 study（每组 ≥100 combo blocks，非同板/同日分半） | **20 个**（provenance：Publication / AstraZeneca / NCATS Tripod） | ✅ |
| **G2 共享细胞** | **≥200** | **41**（在 ≥2 个独立组合 study 均有组合数据的细胞；最大单对 study 共享 **13** 个细胞） | ❌ |
| **G3 匹配条件/配对单元** | **≥10,000** | **4,179** 个跨 study 匹配的 `(cell, 无序药对)` 条件单元（4,158 个在 2 个 study、21 个在 3 个 study） | ❌ |
| G4 噪声标定覆盖 | ≥5% | **23.59%**（4,179 个匹配单元中 986 个至少一侧有组内重复；全部 combo blocks 的组内重复 19.05%） | ✅ |
| G5 组合协同端点 | 存在 | 14 个响应/派生列存在（`synergy_bliss/zip/loewe/hsa`、`S_*`、`css*`、`ic50*`、`ri*`）＋剂量单位/临床期/靶点元数据列存在 | ✅ |
| G6 与 Jaaks 重叠 | 报告 | 共享细胞 **49**、共享药物 **52**；匹配单元中 103 个（cell+双药均属 Jaaks 实体）、615 个（药对属 Jaaks 药对） | 报告 |

**失败门槛：G2、G3（失败类别 `data_insufficient`）。**

**边界（写死）**：在可得资源上，条件级跨 screen 复验**不可检验** → 记录 **`condition_level_cross_screen_untestable`**；这是"资源规格不满足/不可检验"的证据，**不是**"条件级结构不存在"的普遍结论。分析 A 收口：条件级共享份额 **1.43%**（C172）+ 跨 screen 不可及。
**G3 口径说明（稳健性）**：若把 G3 的"配对单元"读作**可行 Q 四元组**（cell-pair × condition-pair），主候选的上界为 **123,538 ≥ 10,000**（该读法下 G3 过）；但 **G2 仍以 41 ≪ 200 失败**，且这 123,538 个 Q 四元组集中在 ALMANAC×ONEIL（9 共享细胞）、ONEIL×FRIEDMAN（5）、ALMANAC×FRIEDMAN（6）三对 study 上——**cell 层有效样本 ~9–13，远小于 A1 的 96 个共享细胞**。因此判定对 G3 的两种读法都保持 `not_qualified`。

## 1. 方法与纪律

- **metadata-only**：只读身份/设计/注释列（`block_id/study_name/cell_line_name/drug_row/drug_col/conc_*_unit/clinical_phase/target_name` 等）；**14 个响应/派生列只做表头存在性检查**，从未读取、转换、聚合任何响应数值；未估 Q、未训练模型、未做效应/相关/预测计算。
- v1.5 全量下载（见 §2）后用流式 `csv.reader` 一次扫描；v1.4、Jaaks fitted、PRISM/BeatAML/O'Neil 元数据只读；未修改任何既有产物/其它目录/INDEX/SYNTESIS/git；只在本目录新增 A3 文件与 `tmp/` 下载文件。
- 确定性：固定解析顺序、JSON 键排序、无时间戳；连续两次运行 `a3.json` **逐字节相同**（`B466FE87…B1F6566`）；派生 CSV 同样一致。单命令：审计 ≈67 s（两次复跑合计 151 s）、下载 210.5 s（均 ≤15 min）。

## 2. C1：DrugComb v1.5 full summary（主候选，已下载）

| 项 | 值 |
|---|---|
| URL | `https://zenodo.org/api/records/15235991/files/summary_v_1_5.csv/content` |
| 大小 | **1,421,694,989 B（1.42 GB ≤ 1.5 GB 预算）** |
| Zenodo MD5 / 本地 SHA256 | `cd3e24758c10ffaea0124b6e80626c32`（一致 ✓）/ `18C038D157A20D768F4A3F012628E5791ED628C784473777975EAB7F75C185A0` |
| 下载耗时/回执 | 210.5 s；回执 `a3_overlap/download_receipt_a3.json`（`5750F305…411F`）；用途仅结构/匹配，**未读响应值** |

**实测结构（与已发表 Supplementary Table S1 的差异必须披露）**：文件实测 **1,432,351 行 = 739,964 combo blocks + 692,387 单药 blocks；34 个 study；1,993 个细胞（其中 combo 细胞 288）；73,167 个无序药对**。发表的 S1 表为 37 study / 1,469,182 blocks（751,498 combo / 717,684 mono）。差异：**3 个纯单药 study（ELLINGER / GORDON / TOURET）不在该文件中**，并且若干 study 的 block 数与 S1 不同（如 FRIEDMAN 198,722 vs 208,008；ASTRAZENECA 19,475 vs 20,482；CTRPV2 378,463 vs 395,263；FRIEDMAN2 28,122 vs 28,500）。**所有门槛计数使用实测文件，不按论文表改口径**（见 `a3_overlap/v15_vs_s1_study_counts.csv`）。

**G1（独立组）**：20 个 combo study 各 ≥100 blocks（详见 `a3_overlap/v15_study_table.csv`），来源为不同 publication / AstraZeneca / NCATS Tripod；同 study 内不同 barcode/plate 不计为独立组。✅

**G2（共享细胞）**：34 个 study 中只有 **14 对**（在 20 个合格 combo study 之内）存在共享细胞；跨 ≥2 个合格 combo study 的细胞共 **41 个**；最大单对 study 共享细胞 **13**（ALMANAC×ASTRAZENECA）、9（ALMANAC×ONEIL）、7（ALMANAC×FLOBAK）、6（ALMANAC×FRIEDMAN）等。阈值 200 → ❌。

**G3（匹配条件单元）**：`(cell, 无序药对)` 在 ≥2 个合格 combo study 中出现者 **4,179 个**（<10,000）；per-study-pair 明细见 `a3_overlap/v15_study_pair_overlap.csv`。前几对（匹配单元/可行 Q 四元组上界/共享细胞）：

| study 对 | 共享细胞 | 匹配条件单元 | 可行 Q 四元组上界 |
|---|---|---|---|
| ALMANAC × ONEIL | 9 | 612 | 78,314 |
| ONEIL × FRIEDMAN | 5 | 361 | 22,689 |
| ALMANAC × FRIEDMAN | 6 | 381 | 22,529 |
| ALMANAC × ASTRAZENECA | 13 | 8 | 6 |
| FRIEDMAN × FRIEDMAN2 | 1 | 2,850 | **0**（单细胞无法构成 cell-pair） |

**关键读法**：4,179 个匹配单元按 study-pair 展开求和为 4,221（21 个三 study 单元被重复计入）；其中只有 **1,362** 个落在"≥2 个共享细胞"的 study 对里（其余 2,859 个来自单细胞共享对，不能构造 Q）；其中真正有意义的组合集中在 3 对 study 上（9/5/6 个共享细胞）。即使把 G3 读作 Q 四元组（123,538 上界，全部来自上述 3 对 study），其 cell 层样本也只有 9–13 个细胞——**比 A1 的 96 个共享细胞更小**，且距 G2 的 200 更远。

**G4（噪声标定）**：匹配单元中 23.59% 至少一侧有同 study 的重复 block（986/4,179）→ ✅；全部 combo blocks 的组内重复率 19.05%（重复组 6.33%）。**注意**这是同 study 技术/重复板，不是独立测量组。

**G5（端点）**：14 个响应/派生列存在（仅表头）；剂量单位、临床期、靶点注释列存在；**非饱和性本轮不可验证**（metadata-only，未读响应值）。✅

**G6（Jaaks 重叠）**：v1.5 combo 细胞 288（与 Jaaks 126 细胞交集 **49**）、combo 药物 4,263（与 Jaaks 65 药交集 **52**）、匹配单元中 103 个落在 Jaaks 细胞且双药均属 Jaaks 药物、615 个药对属于 Jaaks 药对（1,294）。→ "独立资源"表述必须限定；条件级（含剂量）重叠不可验证（summary 无数值剂量）。

## 3. C2：DrugComb v1.4（本地全量）

- 结构：1,175,220 块（466,033 combo / 709,187 单药）；**112 细胞**、62,826 药对、380,418 个 `(cell, 无序药对)` 单元；**无 study 列**。
- block 重复：**36,637 个单元（9.63%）有 ≥2 blocks，最多 10**；全部 466,033 个 combo block 的 `block_id` 都能映射到 v1.5 的 study（100%）——其中 **621 个（1.7%）重复单元来自 ≥2 个不同 study**，其余为同 study 重复板/技术重复。
- 结论：block 分组主要是**同 study 内重复测量**，不是独立 screen；更根本的是**总细胞数 112 < 200** → **G2 结构性失败**；无 study 列 → G1 不满足独立性。`not_qualified`（不是"可用资源"）。

## 4. C3：本机其它成对资源

| 资源 | 独立组 | 共享细胞 | 组合端点 | 结论 |
|---|---|---|---|---|
| `prism_19q4`（primary/secondary） | 两个 screen（同 lab/Broad） | **568**（DepMap ID 交集；满足 ≥200） | **无**：均为单药 log2 fold-change 活力端点（每孔一个化合物；`perturbation_type`=实验处理/对照） | **G5 失败**（不能构造组合协同 Q；G1/G3 亦失败） |
| `beataml2_20261017` | 单药 probit 曲线 | —（569 个 **患者样本**，非细胞系） | **无**（单药 auc/ic*） | G2/G5 失败 |
| `data/raw/oneil2026_qualification` | **1 个研究/lab**；3 个 `BatchID` 重复批 | **39 细胞** | 有（viability 重复列 + 单药剂量） | G1 失败（批次≠独立 screen/lab）+ G2 失败（39<200） |
| `gdsc_combinations`（Jaaks，既有资源） | 2 个 screen（同 publication/lab） | **96** | 有（`SYNERGY_DELTA_EMAX`） | 不是"更大的独立资源"：96<200（C171），且是 A1/A2 的既有数据 |
| `gdsc2_fitted` / `batchie_zenodo_13871987` / `nci_almanac_2017` | — | — | — | **本地目录为空：`data_unavailable`**（记录检索缺口，不写"不存在"）；ALMANAC（60 细胞）只能经 DrugComb C1/C2 访问，单组<200 |

## 5. C4：外部候选

不主动下载；BRIEF §2 的候选顺序在 C1–C3 内已耗尽。若未来要满足规格，需要新预算与新的资格协议（见 §6 `required_resource_spec`）。

## 6. 判定、失败原因与所需规格

- **`not_qualified`**，失败门槛 **G2（41 < 200）、G3（4,179 < 10,000）**；失败类别 **`data_insufficient`**。G1/G4/G5 通过；G6 报告。
- **`condition_level_cross_screen_untestable` = true**：在可得资源上条件级跨 screen 复验不可检验（不是"条件级结构不存在"的普遍结论）。分析 A 收口（条件级共享规律 1.43% + 跨 screen 不可及）。
- **所需资源规格**（解冻/下一资源门槛，写死）：
  1. **≥2 个独立组合 screen/study**（不同 lab/publication/screen；**不是**同板/同日 barcode 分半），每组 ≥100 combo blocks；
  2. **≥200 个共享细胞系**（在 ≥2 个独立组合组中都有组合测量；严格归一名 + 碰撞报告）；
  3. **≥10,000 个跨组匹配的条件单元**（cell × 无序药对），且**剂量设计等价可验证**（summary 层药对匹配不够；需数值剂量设计或 raw dose-level 数据）；
  4. ≥5% 匹配单元有**组内重复**（技术/重复板）可标定噪声；
  5. 校准的组合协同端点（Bliss/ZIP/ΔEMAX 类）+ QC 元数据 + 非饱和证据；条件×细胞交互不得主导（A2：48.5% 交互 / 46.1% 噪声）。
- 不得把 A3 结果写成"条件级结构不存在/不可迁移"；也不得把 C1 的"存在跨 study 匹配"写成"Q 可复验"。

## 7. 局限

1. **只能到 summary 层**：v1.5 summary 无数值剂量/矩阵尺寸（只有单位字符串），C1（剂量等价）层**不可验证**；要验证需 raw dose-level 数据（v1.4 raw = 2,008,117,325 B > 1.5 GB 预算，未下载）。
2. **发表表 vs 文件差异**：S1 表 37 study / 1,469,182 blocks vs 文件 34 / 1,432,351（3 个单药 study 缺失、若干 study 计数不同）；全部门槛用实测文件，已披露（`assumption_contradicts` 级披露）。
3. 独立组只按 study provenance（S1 来源）判定：summary 无 lab/日期字段；"different screen/study/lab" 中 lab 层不可逐条核验（FRIEDMAN/FRIEDMAN2 等同为 Publication 的 study 是否同 lab 未知，已按 S1 区分披露）。
4. 名归一严格（禁同义词推断）→ 共享实体计数可能**低估**；碰撞未逐条列出（pairs 由归一字符串构成，无外部别名合并）。
5. 未读响应值 → 端点非饱和/QC 不可验证（只记列存在）；未估 Q、未训练 | 本判定是资源资格结论，不是对条件级结构科学价值的评价。

## 8. 复现

```powershell
cd D:\MAESTRO\research\2026-10-27-conditional-shift
& D:\anaconda\envs\maestro\python.exe a3.py --fetch   # 210.5 s；1.42 GB；写 a3_overlap/download_receipt_a3.json
& D:\anaconda\envs\maestro\python.exe a3.py           # ~67 s；写 a3.json + a3_overlap/*.csv
```

**产物 SHA256**：a3.py `CDFEA4F1B8AE4CF94D779B7964877AF9488F5FDB9D6067CEE574E657D2F5F9FA`；PROTOCOL_A3.md `E7E6ED2D2CD2836CF28B9F5299EC99374889B8D7DB5F38287C64783A3D8AD2AB`；a3.json `B466FE870DB8DAB989AEB85E559BB7A6D6D9660B34A1F534519B0F959B1F6566`；v15_study_table.csv `1D14CA2B2F4355990E5098A2289D64A92C9901AB083559C9CA0F838B339B34F5`；v15_study_pair_overlap.csv `1839BE3AAA78D99791B5AD10C7BD73345EBC471B14AE24B953341A3D3C8CCB6D`；v14_block_structure.csv `35E0708C5F884B61B181485C5288054446F9092FF04D932FD00D7412F01EA976`；jaaks_overlap.csv `59F65D267E8FBD6D43F6F7EF3F5DDE26F59E0E820B996BBB334E827053A70144`；v15_vs_s1_study_counts.csv `7950C49AB816BB9024266BB09EFB371E093EF8F6EEC72ABE222BF99127FD7F37`；download_receipt_a3.json `5750F30558F43BE4D92A3D92550460B1F92526520C6534FC06BF5F611C22411F`。
关键输入 SHA256：v1.4 summary `E08E3D35…A2F`；Jaaks Original `1188968C…A278` / Validation `DCBD4C31…B2775`；O'Neil workbook `A0E2E002…4818`；BeatAML probit `D4BC5F0D…8314`。
