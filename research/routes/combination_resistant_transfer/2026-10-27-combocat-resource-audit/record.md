# 轮次记录 — ComboCat 元数据资格审计（R189 线 A1，task-1）

角色：数据资格审计员（独立于提案者；不参与 A2 设计/运行）。工作目录 `D:\MAESTRO`，解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / openpyxl 3.1.5 / pandas 2.3.3）。

## 范围与预算

- 范围：ComboCat 补充表 `Supplementary_Table_1_REVISED.xlsx`（zip SHA256 5639020dbe8359c8020e09e6f63cc152ab1179da19200b00e893ef19d7959e9e，与 download_receipt.json 一致）的**结构/身份/注释/QC/重复/剂量设计**审计，及与 Jaaks GDSC、O'Neil 的严格名重合；不读响应数值、不跑响应建模。
- 预算：本地只读分析，BRIEF 规定 A1 不新增联网检索；CPU 单机，单命令 ≤15 分钟。
- 输出：PROTOCOL.md、audit.py、audit.json、counts.json、overlap.json、report.md、record.md、usage.json（全部在本目录）。
- 状态：本轮交付完成（7 件交付物齐全；不可计算项在 report.md §7/Q3 明示，未用猜测替代）。

## 时间线与命令

| 时间 (UTC+8) | 动作 | 命令/产物 | 耗时 |
|---|---|---|---|
| 11:19:51 | 建目录 | `New-Item research/2026-10-27-combocat-resource-audit` | <1 s |
| 11:20:22 | 复核 zip SHA256；冻结协议 | `Get-FileHash` + `PROTOCOL.md`（SHA256 `3918548e546f117ee8868306b6a89143292c0d41572a551f714839bdd56a640e`） | ~1 s |
| 11:21 | 仅表头结构探针 | `tmp/combocat_probe1.py` → 4 个 sheet、data 45 列/292,459 行、其余 3 表表头；**未读任何数据行数值** | 1 s |
| 11:21–11:31 | 前序只读探针（Lead） | `tmp/combocat_probe2.py`–`probe6.py`：summary 表、root_id 形态、xlsx 内部结构、sharedStrings/词表、md5 假设；仅 READ 列 | 各 ~1–60 s |
| 12:28–12:31 | 复核冻结协议（只读）与既有记录；确认 §1 纪律 | `read PROTOCOL.md`、`read record.md`、`read tmp/combocat_probe1.py/.json` | ~3 min |
| 12:32 | **记 AMENDMENT-001**（在读取任何 data 行响应值之前；当时尚未读任何 data 行数值） | 本文件 | — |
| 12:32–12:34 | 读 zip 词表/摘要 + MOESM8（已发布元数据；无响应值） | `tmp/combocat_probe7.py` → `tmp/combocat_probe7.json` | 1.7 s |
| 12:34–12:37 | 外部源/格式探针 | `tmp/combocat_probe8.py`（MOESM8 统计、docProps、units/barcode 结构、Jaaks；O'Neil 因 .xls 扩展名被 openpyxl 拒绝，该段未完成） | 64.8 s |
| 12:38–12:42 | O'Neil 重解析：发现文件是"`.xls` 扩展名 + ZIP/xlsx 内容"，改用 `BytesIO` | 368,832 行 / 39 细胞 / 38 药物 / 583 药对 / 批次 358,560+5,232+5,040；名称重合初查 | ~20 s |
| 12:42–12:45 | 写 `audit.py`（单次流式扫描 + 有界 md5 反解 + 外源重算 + both-unseen 解析界 + Q1–Q5） | `research/2026-10-27-combocat-resource-audit/audit.py` | — |
| 12:45–12:47 | 首跑失败：`drugs_summary` 列索引错误（IndexError，66.3 s 处停止；未写任何响应值、无产物泄漏）；修复 | `python audit.py` | 66.3 s |
| 12:47–12:49 | 二跑成功；与 prior `counts.json` 交叉核对 | Jaaks 121/65/1294/67,812；O'Neil 35/38/583/20,405 —— 逐项一致 | 87.9 s |
| 12:49–12:52 | 引入"外部源并集碰撞口径"（复现 prior 校准）与 dose/alias/well-type 字段；三跑成功 | `python audit.py` | 102.8 s |
| 12:52–12:56 | **确定性复核**：连续两跑 `audit.json`/`counts.json`/`overlap.json` 的 SHA256 完全一致（audit.json `B2066265E19663A58755BA7D7C91426C4DAC481FB696EDF0E1CB862B742800DD`） | `Get-FileHash` 对比 | ~100 s×2 |
| 12:56–13:05 | 写 report.md（数字取自 audit.json）、续写 record.md、写 usage.json；输出泄漏复核 | 本目录 | — |

## 结构性澄清（header-only 探针之后、读数据行之前）

`PROTOCOL.md` §1 READ#4 原写"summary sheet 数值单元一律跳过"，该条是为防止 summary 表藏响应数值而设。表头探针显示 `cell_lines_summary`（37 行×3 列：`unique_cell_line/organism/lineage`）与 `drugs_summary`（137 行×2 列：`unique_drug/class`）**不含任何响应语义列**；其第一列为整数**身份 ID**。为使"药物→class"与"细胞→lineage"可联结，本轮把 summary 表中的整数**身份 ID** 视为 §1 READ#2 允许的"名与 ID"读取（只作身份/注释联结，不作数值统计）；**其余数值单元仍跳过**；不涉及任何响应列、不改变任何门槛或分析选择。此澄清在读取任何数据行之前记录。

## AMENDMENT-001（在读取 data sheet 任何响应列数值之前记录；2026-10-27 12:32 UTC+8）

- **事由**：zip 内 `Supplementary_Table_1_REVISED.xlsx` 的 `data` sheet 无细胞系名列，`drug1_name`/`drug2_name` 为占位符（`drug1`/`drug2`）；`cell_lines_summary` 只有整数身份 ID + organism + lineage（无名字）、`drugs_summary` 只有整数身份 ID + class（无名字），因此无法仅凭 zip 内容把 `root_id` 中的文本药名联结到已发布 class 注释。这是读取任何数据行之前由表头探针（`tmp/combocat_probe1.py`/`.json`，只读表头与行2类型，未读数据行数值）发现的。
- **引用的已发布元数据**：同一出版物（Nat Commun 2025, DOI 10.1038/s41467-025-66223-8）补充材料 `research/2026-10-27-detectability-acquisition/sources/41467_2025_66223_MOESM8_ESM.xlsx` Sheet1（`Drug_id`/`Name`/`Action_Class`/`Reported_Target` 等，约 136 行；**不含任何响应值**）。该文件为既有下载，不联网新增检索。
- **使用范围**：仅用于 (a) `root_id` 文本标识 ↔ 已发布药物身份/`Action_Class` 的联结、(b) **身份解析**：以已发布药物名（及同出版物补充材料中若存在的细胞系名称/注释元数据，如细胞系清单、lineage/组织注释表）为候选集合，离线检验 `root_id` 的编码/哈希格式能否被**发布名称**确定性地解码（哈希猜解属于身份解码，不联网、不引入外部 ID 库）；(c) 药名归一与外部源比较时的名称清单核对。细胞组织 lineage 联结仅用于注释可分析性统计。**不读取、不转换、不聚合任何响应数值**；不改变 PROTOCOL 任何门槛、口径或判定规则；不用于挑选留出药/切分（切分按 PROTOCOL §6 对归一名字典序/种子执行）。若身份解码失败或存在歧义，如实报告不可解析比例，不用部分匹配替代身份。
- **时点**：本记录写于读取 `data` sheet 任何数据行响应列值**之前**；此前只做过表头/结构探针与 summary 表头探针。
- **影响**：`report.md` 必须同时给出 (a) **zip-only 口径**（仅 zip 内信息，药名→class 不可解析 → Q1/Q3 不可判定）与 (b) **含已发布元数据口径** 两种资格判定；`audit.json` 标注每个结论的 `caliber`。
- **失败保护**：若 MOESM8 与 zip 内药名无法匹配或匹配有歧义，按实测如实报告不可解析/歧义比例，不猜测、不外部反查。
- **实测后的补充事实（供核对，不修改上述条款）**：MOESM8 实测为 135 个药物行（`Drug_id` 1–135 连续），按 MOESM3 补充文件索引为 **Supplementary Data 5「稀疏模式筛所用化合物」**，与 zip 内 136 个**稠密** drug ID 不是同一清单、且无 root 键 → 两种口径在"稠密 root 药名/class"上均不可解析（见 report.md §2/§3）。

## 观测（实测；数字均来自 audit.json）

- **结构**：4 个 sheet；`data` 292,458 数据行（292,459 含表头）× 45 列；完整 806×3×121 网格应 292,578 行，缺 120 行（40 块 in-house 板各缺 1 个 (0,0) 孔 × 3 重复）。全部列**无空白单元**；设计缺口是字面 `"NA"` 字符串（Plate Barcode/plate_row/plate_col/plate_row_letter/transfer_type 各 278,058 行；nth_conc 各 279,258 行）。
- **身份**：806 个 root；**804 个（99.752%）为 32 位十六进制不透明 id**；仅 2 个（0.248%）描述性 root（`CHP134_AZD1390_CX-5461...`、`LUM_SMX_TMP...`）；`drug1_name`/`drug2_name` 全表占位符（292,458 行均为 `drug1`/`drug2`）；无 cell line 名列。描述性根前缀解析 2/2、后缀完整解析 1/2（LUM 细胞名标签含空格/下划线 → 歧义 1/2）。3,383,955 次 md5 模板反解 **0 命中**（5 种 id 模板 × 36×136×136、3 种名称模板 × 135²、40 个 barcode）。
- **注释**：zip `cell_lines_summary` 36 个 ID（Human 33/bacteria 2/fungus 1；lineage 14 水平）；`drugs_summary` 136 个 ID、class **5 水平**（investigational 73、chemotherapeutic 26、antibiotic 18、antifungal 15、natural_product 4）。MOESM8：135 药物、Action_Class **5 水平**（inhibitor 127/agonist 4/antagonist 2/degrader 1/binding disruptor 1）、Reported_Target 99 水平；覆盖可恢复药 token 2/4（AZD1390、CX-5461；SMX/TMP 不在其中）。
- **重复/板**：每 root 3 replicate（各 97,486 行），zip 词表原文"all reps are in the same plate"→ 技术重复；41 个 plate 值 = `"NA"`（766 root/278,058 行）+ 40 个真实 barcode（每块 360 行、1:1 对应 root、无碰撞）；无跨板重复（root↔板 1:1）。
- **剂量**：每 root drug1/drug2 各 11 个唯一浓度（10 剂量 + 0）；(d1,d2) 唯一设计对 121（766 root）或 120（40 root）；单位 uM 532 / ug_mL 145 / nM 113 / mg L-1 16 个 root；孔类型（按 0 设计标记复算）组合 241,800、单药各 24,180、对照 2,298 行。
- **QC/未读列**：DENY 列 18 个，全部 0 空值/292,458 行（只做 `cell is None` 计数，未读数值）；`flagged_*` 4 个 0 空值；`unclassified`（完全不读）8 个：`zprime`、`robust_zprime`、`moran_i`、`abs_res`、`nearest_pred`、`nearest_dose`、`Amount`、`...9`。
- **外部重合**：重算与 prior counts.json 完全一致（Jaaks 121/65/1294/67,812；O'Neil 35/38/583/20,405；批次 358,560/5,232/5,040；并集碰撞键 4 个细胞键，源内无碰撞）。ComboCat 可恢复实体严格重合 **0 细胞 / 0 药物 / 0 药对**；清单层面 MOESM8 与 Jaaks/O'Neil 文本重合 28/13（仅文本、无实体映射）。
- **both-unseen**：N_drug=136、N_cell=36、总单元 806；k=27/41/54；主估计/随机敏感性/贪心上界 **null（不可计算）**；解析上界 min(806, C(k,2))=351/806/806，均匀期望 31.8/73.3/127.1，门槛 800 → **Q2 结构性不满足**（r=0.2 硬上界 351<800）。

## 决定

- 判定 **`unqualified`**（zip-only 与含已发布元数据两口径一致），不做事后门槛调整（PROTOCOL §8）。
- 采用 AMENDMENT-001 两口径并列报告；MOESM8 只作已发布元数据（无响应值），实测其为稀疏模式清单后**未**把稀疏药名当作稠密药物身份（不猜测、不映射）。
- DENY 纪律：18 个 DENY 列只做 `cell is None` 计数；`flagged_*` 只统计空/非空；8 个未分类列完全不读（连空值检查也不做）；端点语义只按列名 + zip 内置词表（`Supp_Table_All_Dense_Mode_Summa` 的 39 行词表）分类，不按数值分布反推。
- 外部源采用**并集碰撞口径**以复现 prior 校准（源内单独检测碰撞会得到 125/39，与 prior 的 121/35 不同；并集口径 = prior 口径，逐项一致后才用于交集）。
- both-unseen 在身份不可得时**不用**任何替代推断（例如按剂量网格聚类反推药身份）——超出冻结协议；只给身份无关的解析上界与期望。
- 未完成项：**无交付物缺失**；不可计算项（both-unseen 主估计/随机敏感性/贪心上界、Q3、804 root 的外部重合）按"不可计算"报告，未用猜测填充。

## 局限

- 本审计只验证文本结构/身份/注释，不验证生物学同一实体、终点可比性、独立功能终点或独立培养。
- 技术重复 ≠ 独立培养；板 = 实验批次单位，不证明独立生物学来源（3 个 replicate 全部同板）。
- viability 派生端点（raw_val → 归一化 %Cell Death → Bliss 派生量）≠ 独立功能终点；不能支持机制/靶点占据/临床结论。
- 身份结论只到"在本轮冻结输入 + AMENDMENT-001 元数据下不可解析"，不能证明作者的映射方式；对 804 个匿名 root 的数据来源、是否与 Jaaks/O'Neil 重叠**不可验证**。
- 严格文本名匹配不是化学/细胞实体解析；不做同义词推断、不联网、不引入外部 ID 库。
- 与 Jaaks 的重合是对完整原始表的重合，不是对某个具体训练切分的重合，不构成泄漏裁决。
- 本轮没有运行 A2、没有估计任何效应量/相关性/预测性能；`unqualified` 是资源资格结论，不是对 ComboCat 科学价值的评价。
