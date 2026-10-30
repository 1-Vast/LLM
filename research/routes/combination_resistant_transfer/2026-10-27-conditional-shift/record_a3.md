# record_a3 —— R195-A3 资源资格审计执行记录（时间线 / 命令 / 决定 / 发现 / 局限）

2026-10-27。角色：独立资源资格审计员（metadata-only；不估 Q、不训练、不读响应值）。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / numpy 2.4.6 / pandas 2.3.3 / scipy 1.17.1 / openpyxl）。判定与数字以 [a3.json](a3.json) / [report_a3.md](report_a3.md) 为准。

## 1. 范围与纪律

- **只写** `research/2026-10-27-conditional-shift/` 下新增 A3 文件（`PROTOCOL_A3.md`、`a3.py`、`a3.json`、`a3_overlap/*`、`report_a3.md`、`record_a3.md`、`usage_a3.json`）与 `tmp/`（v1.5 全量文件 `tmp/a3_v15_summary.csv` 与临时脚本）；**未改** A0/A1/A2/Q 既有产物、其它研究目录、INDEX、SYNTHESIS、git、源数据。
- **协议先冻结**：`PROTOCOL_A3.md` 在任何 A3 匹配计数之前写成并冻结（SHA256 `E7E6ED2D…8AD2AB`）；冻结前只做了文件可用性/列名/大小的元数据侦察（不涉及跨 study 匹配计数）。运行过程中未改协议；偏离=无。
- **metadata-only**：只读身份/设计/注释列；14 个响应/派生列只做**表头存在性**检查，从未读取、转换、聚合数值；未估 Q、未训练模型、未计算效应/相关/预测性能；未启动 B/C/acquisition。
- 确定性：固定解析顺序、JSON 键排序、无时间戳；连续两次运行 `a3.json` 逐字节相同（`B466FE87…B1F6566`），派生 CSV 一致。

## 2. 时间线与运行

| 步骤 | 内容 | 结果/耗时 |
|---|---|---|
| 读背景 | R195 BRIEF、R194 BRIEF/record（C172）、PROTOCOL_Q2/q2.json/report_q2、A0/ERRATA/challenge、R190-E1 DrugComb report、`data/external` 候选盘点 | — |
| 候选侦察（冻结前） | PRISM primary/secondary 元数据结构；BeatAML/ O'Neil 表头与身份列；`gdsc2_fitted` / `batchie_zenodo_13871987` / `nci_almanac_2017` 目录为空；Zenodo 15235991 URL/大小/MD5 | 不含任何跨 study 匹配计数 |
| 冻结协议 | 写 `PROTOCOL_A3.md`（G1–G6 与判定写死） | SHA256 `E7E6ED2D…8AD2AB` |
| 下载 C1 | `python a3.py --fetch`（Zenodo 15235991 summary_v_1_5.csv） | **210.5 s**；1,421,694,989 B ≤ 1.5 GB 预算；MD5 与 Zenodo 一致；本地 SHA256 `18C038D1…C185A0`；回执 `a3_overlap/download_receipt_a3.json` |
| 审计首跑 | `python a3.py`：v1.5 全量流式扫描（1,432,351 行）→ 跨 study 结构 → v1.4 全量 → C3 元数据 → G6 → 判定 | **66.9 s**；写 `a3.json`＋`a3_overlap/*.csv`；判定 `not_qualified` |
| 确定性复核 | 连续两次运行，比较 a3.json/CSV SHA256 | 逐字节相同（a3.json `B466FE87…B1F6566`）；复跑合计 151.3 s |
| 报告/记录/账 | 写 `report_a3.md` / `record_a3.md` / `usage_a3.json` | — |

## 3. 关键发现（详见 report_a3.md）

1. **v1.5 全量文件与已发表 S1 表不同**：文件实测 34 study / 1,432,351 blocks（739,964 combo + 692,387 单药）vs S1 表 37 study / 1,469,182 blocks。**3 个纯单药 study（ELLINGER/GORDON/TOURET）不在文件中**，且若干 study block 数不同（FRIEDMAN 198,722 vs 208,008；CTRPV2 378,463 vs 395,263 等；逐 study 对照见 `a3_overlap/v15_vs_s1_study_counts.csv`）。所有门槛计数用实测文件（不按论文表改口径）。
2. **G1 过、G2/G3 失败**：20 个合格 combo study（≥100 blocks，来源 Publication/AstraZeneca/NCATS Tripod）；**跨 ≥2 个独立组合 study 的共享细胞仅 41 个（阈值 200）**；最大单对 study 共享细胞 13；**跨 study 匹配 `(cell, 无序药对)` 条件单元 4,179 个（阈值 10,000）**。
3. **匹配单元主要集中在 3 对 study**：ALMANAC×ONEIL（9 细胞/612 单元/78,314 Q 四元组上界）、ONEIL×FRIEDMAN（5/361/22,689）、ALMANAC×FRIEDMAN（6/381/22,529）；FRIEDMAN×FRIEDMAN2 有 2,850 匹配单元但只有 1 个共享细胞（**无法构造 cell-pair Q**）。4,179 个匹配单元中只有 1,362 个落在 ≥2 共享细胞的 study 对里。
4. **G3 口径稳健性**：若"配对单元"读作可行 Q 四元组（上界 123,538 ≥ 10,000）则该读法下 G3 过，但 **G2（41≪200）仍失败**，且 Q 结构集中在 9–13 个 cell 上（比 A1 的 96 个更少）→ 两种读法都 `not_qualified`。
5. **G4 过**：匹配单元 23.59% 有同 study 重复 block（≥5%），全 combo blocks 组内重复 19.05%（同 study 技术/重复板，不是独立组）。**G5 过**：14 个协同/敏感性响应列存在（仅表头）；非饱和不可验证（metadata-only）。
6. **C2 v1.4**：466,033 combo blocks / 112 细胞 / 380,418 单元；9.63% 单元有 ≥2 blocks（max 10）；**100% 的 v1.4 block_id 可映射到 v1.5 study**，其中仅 621 个重复单元来自 ≥2 study —— block 分组主要是同 study 重复；且总细胞 112 < 200 → 结构性 G2 失败（无 study 列 → G1 不满足）。
7. **C3 本机资源**：PRISM primary/secondary 共享 568 个 DepMap 细胞（G2 口径可过）但**均为单药 log2 fold-change**、无组合端点 → G5 失败；BeatAML 为单药患者样本；O'Neil 单研究/lab、3 个 BatchID、39 细胞 → G1/G2 失败；Jaaks 既有资源 96 共享细胞（C171）；`gdsc2_fitted`/`batchie`/`nci_almanac` 本地空目录 → `data_unavailable`（不写"不存在"）。
8. **G6 Jaaks 重叠**：共享细胞 49、共享药物 52；匹配单元中 103 个（cell+双药均属 Jaaks）、615 个（药对属 Jaaks 药对）→ "独立资源"表述须限定；条件级（含剂量）重叠不可验证。

## 4. 决定与判定

- **`not_qualified`**（G2、G3 失败；失败类别 `data_insufficient`）；G1/G4/G5 通过；G6 报告。
- 记录 **`condition_level_cross_screen_untestable`**：在可得资源上条件级跨 screen 复验不可检验；**不是**"条件级结构不存在"的普遍结论；分析 A 收口（条件级份额 1.43% + 跨 screen 不可及）。
- 所需资源规格（≥2 独立组合 screen、≥200 共享细胞、≥10,000 匹配条件单元且剂量等价可验证、≥5% 组内重复、校准协同端点/QC/非饱和）写入 `a3.json → judgment.required_resource_spec` 与报告 §6。
- `qualified_with_conditions` 未使用：无候选仅差"下载/清洗"（C1 已下载并测完；剂量等价需要 raw dose-level 数据=超出 1.5 GB 预算且属于新协议，不是"可得但需清洗"）。

## 5. 实现选择（写入 a3.json / report）

1. G1 合格组：combo blocks ≥100/study（协议冻结）；独立性按 S1 study provenance（summary 无 lab/日期字段；同 study barcode/板不计独立组）。
2. G3 主口径 = 跨 study 匹配的 `(cell, 无序药对)` 条件单元 ≥10,000；Q 四元组上界按协议定义（每 study 对：共享细胞 × 每细胞匹配条件集交的两两条件对）报告、不设阈值。
3. C2 的 block 分组利用 v1.5 `block_id → study` 映射（v1.4 与 v1.5 block_id 100% 兼容）刻画"重复 block 是否来自不同 study"；未用窗口代理。
4. C3 的 PRISM/BeatAML/O'Neil 只读身份/设计/端点列名与计数；未读任何活力/剂量响应值。
5. 响应盲：v1.5 流式 `csv.reader` 仅按列位置取身份列；响应列仅比较表头字符串。
6. 下载：`tmp/a3_v15_summary.csv` 保留（1.42 GB）；回执含 URL/大小/MD5/本地 SHA256/耗时/预算核对。

## 6. 产物（SHA256）

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_A3.md` | `E7E6ED2D2CD2836CF28B9F5299EC99374889B8D7DB5F38287C64783A3D8AD2AB` |
| `a3.py` | `CDFEA4F1B8AE4CF94D779B7964877AF9488F5FDB9D6067CEE574E657D2F5F9FA` |
| `a3.json` | `B466FE870DB8DAB989AEB85E559BB7A6D6D9660B34A1F534519B0F959B1F6566` |
| `a3_overlap/v15_study_table.csv` | `1D14CA2B2F4355990E5098A2289D64A92C9901AB083559C9CA0F838B339B34F5` |
| `a3_overlap/v15_study_pair_overlap.csv` | `1839BE3AAA78D99791B5AD10C7BD73345EBC471B14AE24B953341A3D3C8CCB6D` |
| `a3_overlap/v14_block_structure.csv` | `35E0708C5F884B61B181485C5288054446F9092FF04D932FD00D7412F01EA976` |
| `a3_overlap/jaaks_overlap.csv` | `59F65D267E8FBD6D43F6F7EF3F5DDE26F59E0E820B996BBB334E827053A70144` |
| `a3_overlap/v15_vs_s1_study_counts.csv` | `7950C49AB816BB9024266BB09EFB371E093EF8F6EEC72ABE222BF99127FD7F37` |
| `a3_overlap/download_receipt_a3.json` | `5750F30558F43BE4D92A3D92550460B1F92526520C6534FC06BF5F611C22411F` |

## 7. 局限

- summary 无数值剂量 → 剂量等价（C1 条件层）不可验证；raw dose-level（v1.4 raw 2.0 GB）超预算未下载 → 不能据此声称"剂量匹配存在"。
- 文件 vs 发表 S1 表差异（34/37 study 等）已披露；门槛用实测文件。
- 独立组仅按 study provenance；lab/日期不可核验（FRIEDMAN/FRIEDMAN2 等同源未知）。
- 严格名归一、禁同义词推断 → 实体重叠计数可能低估；碰撞未逐条列出。
- 未读响应值 → 非饱和/QC 不可验证；本判定是资源资格结论，不是条件级结构评价。
