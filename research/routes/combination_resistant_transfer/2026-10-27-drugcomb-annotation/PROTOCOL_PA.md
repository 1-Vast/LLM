# PROTOCOL_PA —— DrugComb 药物→粗注释映射与覆盖资格审计（R191 阶段 1 P-A）

2026-10-27，**在运行 `pa.py` 之前冻结**。角色：注释映射与覆盖审计员（独立于提案者；本轮不读任何 DrugComb 响应数值、不训练模型、不评估效应、不做机制/临床主张）。
协议冻结后不再修改：实测与先验假设不符时，按 §11 如实记录，**不回头改口径、不做事后调整门槛、不按结果换规则**。

**版本**：v2（2026-10-27T14:07，`pa.py` 尚未存在、尚未运行）——按 Lead 补充指令在运行前修订两处：(a) §5 靶点 token 切分规则细化（`| ; , /` 与空白，含括号说明处理）；(b) §6 增加**规则 A（原始 argmax）与规则 B（超几何富集 z）**及**确定性选择开关**。修订发生时 `pa.py` 未运行、`pa.json` 未生成，因此不存在"看了结果再改规则"。两个版本间未改动任何门槛数值。

## 0. 范围与判定词汇

- 目标：把 DrugComb v1.4 组合块的分析宇宙（4,088 归一药；碰撞剔除后 4,076）映射到**≥12 个可分析粗注释水平**，并给出覆盖/单元资格判定，为主研究 R191 阶段 2 复现协议提供**冻结的 `mapping_table.csv`**。
- 本协议只使用：(i) v1.4 组合块的**身份列**（`drug_row`/`drug_col`/`cell_line_name`）、(ii) 公开药物注释表（DrugComb v1.5 药物标识表、Drug Repurposing Hub）、(iii) 公开基因集资源（MSigDB 2023.1.Hs）。**不读响应列**（§3）。
- 判定词汇（只用这两种）：`mapping_qualified` / `mapping_not_qualified`。判定由 §9 的硬门槛与审计检查共同决定；若 `mapping_not_qualified`，逐条列出失败门槛与解冻条件。

## 1. 冻结输入（只读；SHA256 在运行前于本协议内写死，`pa.py` 复核）

| # | 输入 | 路径（相对 `D:\MAESTRO`） | 字节 | SHA256（冻结） |
|---|---|---|---|---|
| I1 | DrugComb v1.4 summary table（**仅身份列**） | `research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv` | 193,184,734 | `e08e3d35bfa4bea011afe1b05b7025acde5c669c5e8d265866b5e12b08037a2f` |
| I2 | DrugComb v1.5 drug identifiers（`dname`/`target_name`） | `research/2026-10-27-drugcomb-qualification/downloads/DrugComb_drug_identifiers.xlsx` | 5,856,350 | `02b1655ad15a81e0bef06909e147ff4c688938aa7f75eb04603f440e8b18438c` |
| I3 | Drug Repurposing Hub（DRH；`skiprows=9`，列 `pert_iname`/`moa`/`target`） | `data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt` | 530,302 | `9c3a08b9d4369fe4257dc9aa763d682fc5ef6b7dd0615534bb44f92b48bc287b` |
| I4 | MSigDB **S1 = KEGG**（2023.1.Hs，symbols GMT） | `research/2026-10-27-drugcomb-annotation/resources/c2.cp.kegg.v2023.1.Hs.symbols.gmt` | 100,047 | `48de51190366ee388dffe34fa2931e590de43ee5e2a4c27c50c0fc33b9d194fc` |
| I5 | MSigDB **S2 = Hallmark**（2023.1.Hs，symbols GMT） | `research/2026-10-27-drugcomb-annotation/resources/h.all.v2023.1.Hs.symbols.gmt` | 48,649 | `27e48f776cda235ad5b63acaecc3136853ee79c6447d883ce2b070a4d2d47b75` |
| I6 | Jaaks GDSC 组合屏（**仅** `ANCHOR_NAME`/`LIBRARY_NAME`/`ANCHOR_PATHWAY`/`LIBRARY_PATHWAY`，对照模板） | `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv` | 198,893,607 | `1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278` |
| I7 | Jaaks GDSC 组合屏 Validation screen（同上四列） | `data/external/gdsc_combinations/jaaks2022_figshare/Validation screen_All tissues_fitted data.csv` | 11,774,397 | `dcbd4c3108d212fa771c52ae977c8e1c01a421162a2232cdc4273faf257b2775` |

**资源来源与版本（下载于本协议冻结前，已哈希）**
- S1：`https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/c2.cp.kegg.v2023.1.Hs.symbols.gmt`（MSigDB release 2023.1.Hs / KEGG legacy gene sets，186 集）
- S2：`https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/h.all.v2023.1.Hs.symbols.gmt`（MSigDB release 2023.1.Hs / Hallmark，50 集）
- 下载总字节 = 148,696 B ≪ 50 MB 预算；`pa.py` 内写死上述 SHA256 并逐字节复核（不符即中止，不静默继续）。
- I1 的 Zenodo 官方 MD5 见 `research/2026-10-27-drugcomb-qualification/download_receipt.json`（`c11efbdcae4a860c2374c1505a66599b`），本协议只做本地 SHA256 冻结。

## 2. 协议前勘察声明（诚实披露）

写本协议之前已做的**只读勘察**只有：MSigDB 两个 GMT 的下载与结构查看（基因集数 186/50、无重名、基因数范围）、I2 与 I3 的列名与行数、I1 表头与身份列解析、以及**用同一批输入把 §5–§7 的统计做了一遍原型复算**（目的是确认规则可实现、并与 Lead 预探数字对照）。原型复算看到的主策略数字（S1 覆盖约 1,300/4,076、可分析水平约 60、both-unseen 约 5k）**没有导致任何规则或门槛修改**：本协议的规则、门槛、切分、并列仲裁均取自 R191 task-7 规格与 R190/E1 既有口径，在写本协议时逐字写死；v2 修订只来自 Lead 的补充指令（§5、§6），不来自上述数字。`pa.py` 是独立实现（不复用原型脚本），从原始文件重算全部数字。

## 3. 允许/禁止读取的字段（冻结）

**允许（READ）**
- I1：`block_id`、`drug_row`、`drug_col`、`cell_line_name`。解析时只按**列位置**取这四个列；其余列不进入任何 Python 对象（不用 DataFrame `.values`、不做数值转换）。
- I2：`dname`、`target_name`（另只读 `target_type` 的**非空行数**作注释缺口统计，不参与映射）。
- I3：`pert_iname`、`target`、`moa`（`moa` 只用于机制类水平的缺口说明，**不参与** §5 映射）。
- I4/I5：GMT 文件的基因集名与基因符号。
- I6/I7：四列通路模板。

**禁止（DENY：不转换、不聚合、不比较、不写任何输出/日志）**
- I1 的响应/派生数值列：`css`、`synergy_zip`、`synergy_bliss`、`synergy_loewe`、`synergy_hsa`、`ic50_row`、`ic50_col`、`ri_row`、`ri_col`、`css_row`、`css_col`、`S`。
- 任何 DrugComb 数值型响应/协同/敏感性/IC50/RI 字段；I6/I7 的响应与拟合列（只读上述四列）。
- 实现约束：`pa.py` 对 DENY 列的唯一访问是**表头字符串存在性**（记入 `pa.json` 的 `deny_columns_present`，只记列名、不取值）。

## 4. 名归一与碰撞（冻结；沿用 C155 / E1 §4 口径）

- 归一：`NFKC` → `casefold` → 只保留 `str.isalnum()` 字符；空串视为不可用。
- 分析宇宙 **U** = I1 组合块（`drug_row` 与 `drug_col` 均非空且非 `NA`/`NULL`）中出现的归一药物名集合。
- 碰撞键 **C** = 同一归一名对应 ≥2 个 casefold 后不同的原始名。主分析宇宙 **D1 = U \ C**（保守剔除，不参与覆盖率分子/分母的严格口径）。
- 不做同义词推断、不做别名合并；只声明"归一后文本同名"。

## 5. 药物靶点基因集 T_j（冻结规则）

对药物 j（按归一名匹配）：
1. 来源 A：I2 中归一 `dname` == j 的行的 `target_name`；
2. 来源 B：I3 中归一 `pert_iname` == j 的行的 `target`；
3. **token 切分（v2 细化，Lead 指令）**：对每个字段执行
   a. 先删除**括号说明**内容：正则 `\([^)]*\)` 与 `（[^）]*）` 匹配的片段整段删除（含括号本身）；数字里的括号不构成基因符号，删除只会减少噪声；
   b. 按 `|`、`;`、`,`、`/`、以及**任意空白字符**（`\s+`）切分；
   c. 每段 `strip()`，再剥掉首尾的引号与标点（`"'`、`.`、`*`、`:`、`[`、`]`、`{`、`}`、`+`、`-` 中的首尾字符反复剥离，直到首尾不是这些字符）；丢弃空串；
   d. token 保留**原始大小写**（不转大写、不做别名/蛋白名→基因符号推断）；
4. `T_j` = 来源 A ∪ 来源 B 的 token 集合；
5. 基因符号匹配 = 与 GMT 基因符号**精确字符串相等**（大小写敏感；GMT 符号为人类 HGNC 大写符号）。敏感性：token 与基因符号都转大写后再匹配（只报告，不改主规则）。
6. 记录每药 token 数、其中"精确等于某基因符号"的 token 数、以及来源归属（仅 A / 仅 B / 两者）。

> 已知结构性事实（协议前勘察）：I2 的 `target_name` 是**蛋白全名**（如 `Thymidylate synthase`），大多数 token 不是基因符号；因此映射在实践上主要由 I3（DRH `target` 基因符号）驱动。这**不改变规则**，但必须在报告中量化来源归属。

## 6. 候选基因集库、评分规则 A/B 与主策略（冻结规则）

- **S1 = KEGG**（I4，186 集）、**S2 = Hallmark**（I5，50 集）、**S3 = KEGG ∪ Hallmark**（236 集，混合库）。
- 每个库 L 的**背景基因全集** `G_L` = L 中所有基因集的并集；`N_L = |G_L|`。

### 6.1 规则 A（默认，原始 argmax）

- 药物 j 的**命中基因数** `n_j = |T_j ∩ G_L|`（§5 精确匹配到的基因符号数）。
- `score_A(j,P) = |T_j ∩ P|`（集合交大小，**不做集合大小归一**）。
- 若 `max_P score_A ≥ 1`：登记为 `argmax` 通路；并列（≥2 个 P 同分）时按**通路名升序**（Python 字符串序）取第一个，并记录并列数；否则 `unmapped`。

### 6.2 规则 B（超几何富集 z；v2 新增，Lead 指令）

- 对每个通路 P（`K_P = |P|`），在背景 `N_L` 下用超几何分布：`X ~ Hypergeom(N=N_L, K=K_P, n=n_j)`，观测 `x = |T_j ∩ P|`。
- `E[X] = n_j K_P / N_L`；`sd[X] = sqrt( n_j (K_P/N_L) (1 - K_P/N_L) (N_L - n_j)/(N_L - 1) )`；
- `z(j,P) = (x - E[X]) / sd[X]`（只对 `x ≥ 1` 的通路计算；`sd=0` 时 `z=0`；`n_j=0` → `unmapped`）。
- 取 `argmax z`（并列按通路名升序；浮点相等按精确值判定）；**仅当 `max z ≥ 1.64`（近似单侧 p<0.05）才登记**，否则 `unmapped`。
- 同时记录所选通路的精确超几何上尾 p 值（scipy `hypergeom.sf(x-1, N, K, n)`，仅作诊断，不参与登记判定），并报告"`z≥1.64` 与 `p<0.05` 判定不一致"的药数。
- 说明：`n_j` 只计**在背景基因全集内**的命中基因（不是全部 token 数）——这是超几何检验的正确抽样规模，也避免蛋白名词汇 token 虚增 n。

### 6.3 主策略与确定性选择开关（v2 冻结，Lead 指令）

**逐库选择规则**：对每个库 L，先计算规则 A 的映射结果；若 **(i) 单一水平占映射药 > 40%**（`max_ℓ n_ℓ / n_mapped_A > 0.40`）**或 (ii) 可分析水平数 < 12**（PA 切分口径，§7），则该库主规则 = **B**；否则 = **A**。该判断只用映射/覆盖/水平分布数字，**不看任何响应值**。

**策略层级（按序递补）**：`(S1, chosen(S1))` → `(S2, chosen(S2))` → `(S3, chosen(S3))`。第一项即**主策略**；若它未通过 §9 任一硬门槛，依次尝试下一项；三项都不通过 → `mapping_not_qualified`。
先验理由（与响应无关）：项目冻结结论用的是"通路"粗化（GDSC 21 通路模板），KEGG 命名通路的语义最可比；S2 是 hallmarks；S3 混合库的 argmax/富集分数对集合大小与库混合敏感、语义异质，只作诊断顺序的最后一项。

### 6.4 必须报告两种规则的全部数字

对每个库 × 每个规则（6 个组合）都报告：药物覆盖数/率、可分析水平数、both-unseen 单元、训练单元、并列比例、score/z 分布、单一水平最大占比。**主策略只按 §6.3 的确定性开关选择**，不得按结果改选。

## 7. 切分与单元定义（冻结规则）

记某库某规则下已映射药物集合为 M（⊆ D1），`N = |M|`，`names = sorted(M)`（归一名升序，Python `sorted` 字符串序）。

- **PA 切分（主口径，task-7 §3 指定）**：`k = max(1, round(0.20 * N))`（Python `round`，半偶入），`step = max(1, N // k)`，留出集 `H = set(names[0::step][:k])`；训练药集 `M \ H`。**N 用有注释（已映射）药物数**，与 E1 同一确定性规则。
- **E1 切分（敏感性/阶段 2 兼容口径）**：把同一规则作用在**全宇宙** `U` 上（`N = |U| = 4,088`，`k = 818`，`step = 4`），得到 `H_E1`；用它报告"两药均被映射且两药均在 H_E1"的单元数，以及水平的训练/留出覆盖。
- **单元**：`(cell_norm, unordered(drug_norm_1, drug_norm_2))`，来自 I1 组合块（与 E1 §5.3 完全同口径）。
- **both-unseen 单元**（主口径）：`H` 内两药都在、且（由 H ⊆ M 自动）两药均有注释的单元数。
- **训练单元**：两药均 ∈ M 且**不满足**"两药都在 H"的单元数；另报更严格变体（两药都不在 H）。
- **可分析水平**（对给定切分）：水平 ℓ 同时满足（a）`|{j∈M: label(j)=ℓ}| ≥ 2`，（b）训练药集内 ≥1 药，（c）留出药集内 ≥1 药。主口径用 PA 切分；E1 切分版本作敏感性。

## 8. 必报数字（全部写入 `pa.json` / `report.md`）

1. 各库：基因集数、背景基因数、可分靶点 token 数、精确符号 token 数、有 token 药数、有命中基因药数、**药物覆盖数/率**（分母同时给 `|D1| = 4,076` 与 `|U| = 4,088`），按规则 A/B 各一套。
2. 可分析水平数（PA 切分主、E1 切分敏感性，A/B 各一套）；每水平的 `n_all/n_train/n_holdout`（PA 与 E1 两种切分）与是否可分析（完整表进 `pa.json`）。
3. both-unseen 单元数（PA 切分主）；训练单元数；E1 切分下的"两药均映射且均留出"单元数；全体 4,088 口径覆盖率。
4. **选择开关诊断**：A 的单一水平最大占比、PA 切分可分析水平数 → 每库 chosen rule。
5. **诊断**：argmax/argmax-z 并列比例、`score_A` 与 `z` 分布、单基因命中（score=1）占比、所选通路基因集大小分布、来源归属（仅 DRH/仅 DrugComb/两者）、12 个机制类药逐条处理结果、Jaaks 通路模板覆盖对照、BRIEF §P-A 的"两药均映射药对比例"诊断（仅报告，不参与本任务判定）、token 切分敏感性（§5 的 T0 规则：不切空白/斜杠）。
6. **敏感性**（只报告不改主策略）：r=0.30/0.40 的 both-unseen 单元（PA 与 E1 切分各一套）；`names[0::5][:k]` 字面变体；S2/S3 全部等价数字；大小写不敏感匹配的覆盖；留出集内每水平是否出现；并列比例。
7. **非响应派生检查**：映射输入仅为 §3 READ 字段 + §5 公开注释；DENY 列只做表头存在性统计；产物中无任何响应数值。

## 9. 门槛与判定（先验冻结）

**硬门槛**（全部通过才 `mapping_qualified`；任一失败 → `mapping_not_qualified`）

| # | 门槛 | 通过条件（冻结） |
|---|---|---|
| G1 | 主策略药物覆盖 ≥25% | 主策略已映射药物数（d1 口径）/ 4,088 ≥ 25%（即 ≥1,022）；同时报告 /4,076 |
| G2 | 可分析水平 ≥12 | PA 切分下同时满足 §7（a)(b)(c）的水平数 ≥12（E1 切分版本同时报告） |
| G3 | both-unseen 有注释单元 ≥800 | PA 切分（N = M 的 0.20 留出）内两药均有注释的 (cell, 无序药对) 单元数 ≥800 |
| G4 | 训练有注释单元 ≥5,000 | §7"训练单元"口径（两药均映射且非 both-unseen）≥5,000 |

**审计检查**（任一失败 → 不能给 `mapping_qualified`，因为可审计性不成立）

| # | 检查 | 通过条件 |
|---|---|---|
| A1 | 输入/资源完整性 | I1–I7 存在、字节数与 §1 一致、SHA256 与 §1 冻结值逐条相等 |
| A2 | 非响应派生 | DENY 列未被读取（结构上按列位置取 READ 列）；`pa.json` 记录 DENY 列的**列名清单**与"未取值"标志；产物不含响应数值 |
| A3 | E1 口径可复现（交叉校验） | 本脚本从 I1 身份列重算的 `组合块行数 / U / D1 / 细胞数 / 无序药对 / cell×pair 单元 / E1 切分 both-unseen 单元` 必须等于 R190 已核验值 `466,033 / 4,088 / 4,076 / 112 / 62,826 / 380,418 / 16,078` |
| A4 | 确定性/冻结 | `pa.py` 无随机、无时间戳、JSON 键排序；两次运行产物 SHA256 相同；`mapping_table.csv` 的 SHA256 写入 `pa.json` 与报告 |

**判定映射**
- `mapping_qualified`：G1–G4 与 A1–A4 全通过。必须同时列出**随判定带走的条件**（语义/解释限制、已知偏差、阶段 2 必须固定的切分选择）。
- `mapping_not_qualified`：任一硬门槛失败。逐条列失败门槛、实测值、**解冻条件**（例如：扩展注释来源、换归一化规则、补同义词表、改用纵向机制库等——但任何替换都要作为**新协议**重新冻结，不得在本轮事后修改）。

**失败类别**（沿用 C155/E1 词汇）：`data_unavailable` / `assumption_contradicts` / `data_insufficient` / `evaluation_cannot_distinguish` / `transfer_unsupported`。

## 10. 产物与确定性

- 唯一写目录：`research/2026-10-27-drugcomb-annotation/`（另允许 `tmp/`）。不修改源数据、其它研究目录、`research/INDEX.md`、`SYNTHESIS.md`、git。
- 产物：
  - `PROTOCOL_PA.md`（本文件，先冻结）
  - `resources/*.gmt`（S1/S2，已哈希）
  - `pa.py`：只读本地文件、不联网、确定性；JSON `sort_keys=True`；无时间戳；输入/资源/脚本/协议 SHA256 写入 `pa.json`。
  - `pa.json`：全部数字与判定。
  - `mapping_table.csv`：**冻结映射表**，列为 `drug_normalized_name, source_library, pathway, n_target_genes, n_genes_in_pathway, drug_drop, notes`；每个 U 内药物 × 三个库各一行（12,264 行）；`source_library` ∈ {S1,S2,S3} 且该行映射由 §6.3 为该库选定的规则产生（规则写在 `notes` 的 `rule=`）；排序 = 药名升序 → 库序 S1<S2<S3；纯 ASCII 安全 CSV，`\n` 行尾；`pathway` 未映射写 `unmapped`；`n_genes_in_pathway` 未映射写 0；`drug_drop` ∈ {`none`,`collision_key_conservatively_dropped`,`no_target_annotation`,`no_exact_gene_symbol_overlap`}；`notes` 为 `key=value;...` 分号串（含 `rule`、`max_score` 或 `max_z`、`tie_pathways`、`jaaks_pathway` 等）。**主策略 = `source_library == <主策略库>` 的行（`notes.rule=` 等于该库选定规则）**。
  - `mapping_table_rules_AB.csv`（辅助审计表，非冻结主表）：每药 × 每库 × 每规则一行，用于复算 A/B 全部数字。
  - `report.md`、`record.md`、`usage.json`（运行时不可得数值记 `null`，不记 0）。

## 11. 明确不做

不读响应数值做任何统计/筛选；不训练模型；不跑效应估计/相关性/预测性能；不联网提交数据；不修改源数据与其它目录；不把"没找到"写成"不存在"（缺口逐条记录）；不做机制/靶点/临床主张；不把"映射资格通过"写成"冻结结论已解冻/已复现"；不重开线 D；不因结果调整门槛或规则。
