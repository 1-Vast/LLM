# ComboCat 稠密组合数据资格审计协议（R189 线 A1）

2026-10-27，**读取任何 ComboCat 数据之前冻结**。角色：数据资格审计员（独立于提案者，不参与 A2 设计/运行）。本协议冻结后不再修改；若实际结构与先验假设不符，按 §8 判定规则如实记录，不回头修改口径、不做事后阈值调整。

## 0. 范围与输入

- 输入：`research/2026-10-27-oneil-transfer-qualification/combocat_dense_supp_data1.zip`（73,327,836 B；SHA256 5639020dbe8359c8020e09e6f63cc152ab1179da19200b00e893ef19d7959e9e，与 download_receipt.json 一致），内含 `Supplementary_Table_1_REVISED.xlsx`（74,857,017 B 解压后）。
- 解释器：`D:\anaconda\envs\maestro\python.exe`（openpyxl 3.1.5 / pandas 2.3.3），只读解析，不修改、不另存源文件。
- 运行：本目录 `audit.py`，确定性、可重跑、不联网；不跑任何响应建模、不做效应估计、不做假设检验。
- 输出：`PROTOCOL.md`（本文件）、`audit.py`、`audit.json`、`counts.json`、`overlap.json`、`report.md`、`record.md`、`usage.json`。全部写入本目录（临时文件只写 `tmp/`）。
- 本审计回答的是**资源资格**：结构、身份、注释、重复、剂量设计、外部实体重合与 both-unseen 切分可行性。它**不能**验证终点可比性、独立功能终点或独立培养。

## 1. 允许读取 / 禁止读取的字段（先验冻结）

**允许读取（READ）**
1. 表结构：sheet 名、表头、行列数、每列缺失计数。
2. 身份/设计列（按列名归类；data sheet）：`root_id`、`replicate`、`Plate Barcode`、孔位坐标（well/row/column）、细胞系名、drug1/drug2 名与 ID、批次/板/日期/实验类型/文库（library）/模式（mode/dense/sparse/screen）等实验设计列。
3. 剂量设计列（列名含 concentration/conc/dose）：读取其设计数值仅用于**剂量布局计数**（每药唯一浓度点数、每 root well 数、浓度点列表），不用于任何效应判断。
4. 注释/摘要 sheet：`drugs_summary`、`cell_lines_summary` 及其它 summary/README sheet，**只读取字符串单元值**（class/target/pathway/MoA/tissue/名称等注释文本）；该 sheet 中的数值单元一律跳过、不读取、不统计（仅记录"有数值单元"这一存在性）。
5. QC/缺失结构：`flagged_*` 列只统计非空/空计数以便刻画 QC 标记结构；不读取、不使用其数值大小。

**禁止读取（DENY，不得读取数值、不得转换、不得聚合、不得写入任何输出/日志）**
- 响应/端点列（显式）：`raw_val`、`bliss_synergy`、`perc_cell_death`、`mean_syn`、`single_effect`。
- 以及 data sheet 中名称匹配以下响应语义模式的列（大小写不敏感）：`raw|val|value|bliss|synerg|syn_|_syn|death|viab|viabilit|response|effect|inhibit|sensitiv|resist|auc|ic50|ec50|gi50|dss|zscore|z_score|score|mean|median|var|std|sd|sem|delta|fold|log|ratio|label|^y$|predict|imput|complete`。
- 判定优先级：显式 DENY 与模式 DENY 覆盖同名列；若列名同时匹配 READ 关键词与 DENY 模式，**以 DENY 为准**，并在 audit.json 标记 `read_modality="null_check_only"` 或 `"not_read"`。`flagged_*` 是唯一豁免：只计非空计数。
- 未知列：不读值（连空值检查也不做），只在 audit.json 记录列名并归入 `unclassified`（用于报告"未能分类的列名"清单）。未知列若事后发现关键，只能作为后续轮次的新协议，不在本轮补读。

**唯一允许的"存在性"访问（结构性缺失，非数值读取）**：对 DENY 列允许做 `cell is None` 的二元检查，用于统计缺失结构（判断实测/补全列在哪些行缺失），**不materialize数值、不转 float、不比较大小、不排序、不筛选、不建模**。此计数只以"行数/比例"形式输出。

**硬性纪律**：任何脚本若意外把 DENY 列数值读入内存或写入输出/日志，立即停止并如实记入 record.md，不把数值写入任何产物。

## 2. 严格名归一与碰撞

- 归一：`NFKC` → `casefold` → 只保留 Unicode 字母/数字（`str.isalnum()`），删除空白与标点。
- 多对一碰撞：同一归一名对应 ≥2 个 casefold 后不同的原始名 → 逐条列出，**主计数保守剔除**该键（不参与严格交集）。
- 敏感性：碰撞名与别名候选（如 `OCUB-M`/`OCUBM`、`HCT-116`/`HCT116` 等）只列为**候选合并**，在任何计数中不自动合并；禁止同义词推断、禁止用外部 ID 反查（不联网）。
- 全文区分"文本同名"与"生物学同一实体"；报告只声明前者。

## 3. 外部实体重合口径

- **Jaaks GDSC**：`data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`，只读 `usecols=['CELL_LINE_NAME','ANCHOR_NAME','LIBRARY_NAME']`，dropna。沿用 oneil-transfer-qualification 的归一/碰撞口径（counts.json/overlap.json 可对照）。
- **O'Neil**：`data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`，只读 `cell_line`、`drugA_name`、`drugB_name`、`BatchID` 四列（沿用 prior 口径）；三批次分列统计，batch 3 不假设为独立培养。若该文件无法解析，则只复用 prior counts.json/overlap.json 中的已有名清单口径，并在 audit.json 标 `oneil_parse="failed"` 说明不可复算部分。
- 分别对每源做 §2 归一与碰撞剔除后，与 ComboCat 的细胞/药物归一集合求交；同时给出"不剔除碰撞"的宽松候选交集（只作候选，不证明同一）。药对（无序）比较作为辅助输出。
- 注意：与 Jaaks **完整原始表**的交集不等于与某个具体训练切分的交集；本审计不做泄漏裁决，只报告重合。

## 4. 重复结构口径

- `root_id`：不预设编码；统计每 root 行数、distinct replicate 数、涉及细胞/药对/板数，并检验 root 与 (cell, 无序药对) 的对应关系（1:1 / 多对一 / 一对多，仅用集合关系计数）。
- `replicate`：同板内技术重复标记。**技术重复 ≠ 独立培养、≠ 生物学重复**；不合并为独立样本、不用于推断培养独立性。所有报告必须写明。
- `Plate Barcode`：统计不同板数、每板行数、每板 root 数、每板 replicate 结构。板是实验批次单位，不证明独立生物学来源。
- 统计"同 cell×pair 跨板出现"仅作为**重复机会**计数，不作为跨板独立培养证据。

## 5. 剂量布局口径

- 按归一药名聚合其浓度设计列，统计每药**唯一浓度点数**；统计每 root / 每板 well 数（行数近似，若存在孔位列则以孔位计）；统计浓度点组合数。
- `mode`/`dense`/`sparse` 一类的实验设计列（若存在）用于区分稠密与稀疏/补全部分；**只按设计标记分组计数，不按响应值分组**。
- 若浓度/孔位列缺失或无法分类，记录"不可得"，不猜测。

## 6. both-unseen 留药切分可行性（只用身份与 pair 图，不看响应）

- 节点 = 药物（归一名）；边 = 数据中出现的**无序药对**（用身份列构造）。cell×pair 单元 = 不同的 (细胞归一名, 无序药对)，要求该组合在数据中出现。
- 若存在可识别的"稠密/实测 vs 稀疏/补全"设计标记列，则分别报告 `all_edges` 与 `dense_edges`（只按设计标记，不按响应）。
- 留药比例 r ∈ {0.20, 0.30, 0.40}；k = round(r × N_drug)，N_drug 取 drugs_summary 的归一名数。
- **主估计**（确定性）：归一药名按字典序排序，holdout = `names[0::floor(N/k)][:k]`。
- **敏感性**：固定 seed 20261027 的 1000 次随机 holdout 子集，报均值与 2.5/97.5 分位。
- **结构性上界**：贪心 holdout——每步加入使"内部边数增量"最大的药，并列按归一名字典序；给"若允许按图结构设计留出集"的上限。上界只作可行性判断，不作 A2 实际切分先验。
- 每 r 报：both-unseen 药对数、both-unseen cell×pair 单元数、参与细胞数、内部边密度；与 BRIEF 门槛 **≥800 cell×pair 单元** 比较。
- 注释水平可分析性：class 水平数、每水平药物数；对每 r 报"训练药集合出现且留出药集合也出现的 class 水平数"。**"可分析注释水平"先验定义**：该水平在 drugs_summary 中至少有 2 个药物，且在留出药与训练药中各出现 ≥1 个药物。另报 ≥3、≥5 药阈值的敏感性。与 BRIEF 门槛 **≥12 个可分析注释水平** 比较。

## 7. 端点字段语义分类

只用**列名 + 已记录原文事实**分类，禁止按数值分布反推。已记录事实（来源：`research/2026-10-27-oneil-transfer-qualification/report.md` §近邻文献，证据状态 reported；本轮按 BRIEF 不新增联网核验）：论文报告 806 种组合密集参考集、三次技术重复；稀疏筛部分包含预测补全值，补全点不应视为实测。
分类桶：`measured_raw`（实测原始值）、`derived`（论文派生/归一/聚合）、`single_agent_or_control`（单药/对照）、`imputed_or_predicted`（补全/预测，需列名或缺失结构支持，否则 unknown）、`qc_flag`、`unknown`。
每个端点列记录：列名、分类、分类证据（列名关键词 / 缺失结构 / 原文表述）、是否允许在本审计中读取（全部 DENY 列只允许空值计数）。

## 8. 判定规则（先验，冻结）

**前置检查**（任一不满足 → 记录 `unqualified: data_unavailable` 或 `unqualified: structure_mismatch`，不猜内容）：
P1. zip SHA256 与回执一致、xlsx 可读、含 data sheet。
P2. 与 BRIEF 先验假设的一致性核对（2026-10-27 BRIEF 的已知/待核实前提：292,459 行、45 列、36 细胞、136 药物、806 组合、3 技术重复）。不一致**不判死**，但作为 `assumption_contradicts` 记录，并按实测结构重述所有结论；所有计数以实测为准。
P3. 细胞/药物身份列齐全，可做 §2 归一。

**资格门槛**（BRIEF §1 A2，全部满足才 `qualified`）：
- Q1 注释水平：所选留药比例下 ≥12 个可分析注释水平（§6 定义）。
- Q2 both-unseen 规模：≥800 cell×pair 单元（§6 定义；主估计与结构上界分别报，判定用**主估计**；上界只说明设计空间）。
- Q3 注释水平在训练出现：留出药所属每个 class 水平都在训练药集合中出现（"training-unseen class" 数 = 0，或列出并判不满足）。
- Q4 外部性：报告与 Jaaks/O'Neil 的细胞、药物、药对重合；若重合，则"第二资源"只在未见实体上成立，须在 A2 按未见实体切分。Q4 只报告，不单独否决；但对"外部复现"表述加限定。
- Q5 端点/重复限制：即使 Q1–Q3 全满足，ComboCat 端点是 viability 派生指标、重复是板内技术重复 → 只能检验"粗注释替代身份"的可重复性，不构成独立功能终点/独立培养/机制/临床结论。

**输出判定**：`qualified` / `qualified_with_conditions`（列出条件）/ `unqualified`（列出失败门槛、失败类别与所需解冻条件）。判定只用本协议冻结的门槛，不做事后调整。

## 9. 失败类别与停止条件

- 读取失败 → `data_unavailable`：记录异常与尝试，不猜内容。
- 先验结构不符 → `assumption_contradicts`：记录实测结构并重述结论。
- 门槛不满足 → 记录具体失败门槛与类别（`data_insufficient` / `evaluation_cannot_distinguish` / `transfer_unsupported` 等）与所需解冻条件；**不运行 A2、不做响应建模、不用相关性代替资格**。
- 任何误触响应数值 → 立即停止，记入 record.md。
- 单条命令 ≤15 分钟；大文件分块/只读流式处理。

## 10. 确定性与产物规范

- `audit.py` 重跑结果一致：输入 SHA256、脚本 SHA256、协议 SHA256 均记录；JSON key 排序、无运行时间戳；随机仅固定种子 20261027。
- `record.md` 记录：范围、预算、实际命令与耗时、观测、决定、局限。
- `usage.json`：token/费用等运行时不可得数值记 `null`（不记 0）；记录命令与实际耗时。
- 只写本目录与 `tmp/`；不改 `reference/`、`research/INDEX.md`、`log/`、git；不跑响应建模、不晋升代码。

## 11. 明确不做

不读响应数值、不估计任何效应量/相关性/预测性能、不做 A2 预注册运行、不做机制/靶点/临床主张、不联网新增检索（沿用本地已有原文记录与已有回执）、不修改任何既有源数据或研究目录。
