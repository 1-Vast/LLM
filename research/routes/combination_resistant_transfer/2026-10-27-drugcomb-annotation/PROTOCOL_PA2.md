# PROTOCOL_PA2 —— HGNC 别名解析层 + 冻结 S1-A 规则重跑（R192 前置）

2026-10-27，**在运行 `pa2.py` 之前冻结**。角色：注释映射与覆盖审计员（独立于提案者）。本轮**只新增文件**，不修改 P-A v1 的任何产物；不读任何 DrugComb 响应值；不训练模型；不评估效应。
协议冻结后不再修改：实测与先验不符时按 §11 如实记录，**不回头改口径、不做事后门槛调整、不按结果换规则**。

**版本**：v1（2026-10-27T14:35 前后写定；`pa2.py` 尚不存在）。

## 0. 范围与判定词汇

- 目标：在 P-A v1 的 token 归一之上增加**确定性别名解析层**，用公开 HGNC 完整表把 DrugComb `target_name` 的**蛋白全名/别名**解析成基因符号；然后**逐字重跑冻结的 S1-A 规则**（KEGG argmax；规则与门槛不变），报告 v1→v2 的覆盖率/可分析水平/both-unseen 单元（PA 与 E1 两口径）/训练单元变化，以及新增的 ambiguous / unmapped 计数。
- 判定词汇（只用两种）：`mapping_v2_qualified` / `mapping_not_qualified`（按**同一** G1–G4 门槛，见 §9）。
- 本任务**不**回答：注释特征是否带来效应/排序增益（阶段 2 问题）、端点可用性、v1 结论是否解冻。

## 1. 输入（只读；SHA256 在本协议内写死，`pa2.py` 复核）

**新增资源（HGNC；下载于本协议冻结前，已哈希）**

| 资源 | 值 |
|---|---|
| 下载 URL（首选，成功） | `https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt` |
| 备选 URL（未使用） | `https://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt` |
| 本地路径 | `research/2026-10-27-drugcomb-annotation/resources_hgnc/hgnc_complete_set.txt` |
| 字节数 | 16,982,321 B（≤50 MB 预算） |
| SHA256（冻结） | `12363916be36f8f6f91879b0faade4eeaac973722de7136ec61329b77f2c2f91` |
| 行数 / 列数 | 45,277 数据行（全部 `status == Approved`）/ 53 列 |
| 版本日期 | `max(date_modified) = 2026-10-15`（由文件内容确定性计算，写入产物） |
| 使用列 | `symbol`, `name`, `alias_symbol`, `alias_name`, `prev_symbol`, `status`, `date_modified` |

**复用 P-A 输入（只读；SHA256 见 `PROTOCOL_PA.md` §1，`pa2.py` 逐条复核）**：I1 v1.4 summary（仅身份列）、I2 DrugComb v1.5 drug identifiers（`dname`/`target_name`）、I3 DRH（`pert_iname`/`target`）、I4 MSigDB KEGG GMT、I5 MSigDB Hallmark GMT（本轮只用 KEGG 作 S1；Hallmark 仅用于符号全集口径说明，不参与评分）。

**P-A v1 产物（只读；不修改）**

| 产物 | SHA256 |
|---|---|
| `mapping_table.csv`（v1 冻结表） | `45ede63521dc44fefec52d717765b4d2ba7d08ec3fde4372811c4d516de038d4` |
| `pa.json` | `f5559d26a86679bd7be77ffd00fc5c4195be50eb611e8677a87434fb842c9fa3` |
| `pa.py` | `25e64208a95b0c92b126823020e361ad208e517eef95c4f093f6be835ff470f3` |
| `PROTOCOL_PA.md` | `16c40f9f61765637185bd061b1aeb4e62886bdfa027b8baf509830775bae607d` |

`pa2.py` 以 `import pa`（`sys.dont_write_bytecode = True`，不写 `__pycache__`）复用 v1 的**完全相同**实现：身份列解析、U/D1/碰撞、token 归一（T1）、MSigDB 库构建、规则 A（argmax）、确定性切分（PA/E1）。v1 数字在 `pa2.py` 内重算并与 v1 `pa.json` 的冻结值逐项断言相等（§11 A3）。

## 2. 协议前勘察声明（诚实披露）

写本协议之前只做了**只读勘察**：HGNC 文件结构（45,277 行 × 53 列、status 全 Approved、`max(date_modified)=2026-10-15`、alias/prev/name 索引规模与 multi-target 键数）、以及**可行性原型**（用 HGNC 索引估计：D1 的 2,802 个 token 中 869 个 v1 精确命中、**134 个可唯一解析**、**28 个候选多 symbol**、1,771 个不可解析；1,678 个 segment 中 **290 个 name/alias_name 唯一命中**、2 个多 symbol；粗估约 **398 个当前未映射 D1 药**可获得 ≥1 个 KEGG 符号）。还观察到短 token 经 alias 解析会产生**噪声**（如 `II`/`of`/`H`/`H1`/`p38` 等，属于 HGNC 里的通用/编号式别名），因此 §6.4 预注册"通用短别名"精度诊断与 §8 的四个变体，但**主规则仍按任务给定**。上述勘察**没有**导致任何规则/门槛修改；v2 的最终门槛数字在冻结后由 `pa2.py` 重算。

## 3. 允许/禁止读取的字段（冻结）

同 `PROTOCOL_PA.md` §3：I1 只按列位置读 `block_id`/`drug_row`/`drug_col`/`cell_line_name`；**12 个响应/派生列（`css`, `synergy_zip`, `synergy_bliss`, `synergy_loewe`, `synergy_hsa`, `ic50_row`, `ic50_col`, `ri_row`, `ri_col`, `css_row`, `css_col`, `S`）只做表头存在性记录，永不取值**。I2 只读 `dname`/`target_name`；I3 只读 `pert_iname`/`target`；I4/I5 只读基因集名与基因符号；HGNC 只读 §1 的 7 列。

## 4. 宇宙、token 与 segment（冻结；沿用 P-A）

- 归一（名）：`NFKC → casefold → 只保留 alnum`；U = v1.4 组合块归一药集合（4,088）；D1 = U 减 C155 碰撞键（4,076）。**校验目标**：组合块 466,033 / U 4,088 / D1 4,076 / 细胞 112 / 药对 62,826 / cell×pair 380,418 / E1 切分 both-unseen 16,078（与 R190 一致）。
- **token 集合 T_j**：同 P-A §5（I2 `target_name` ∪ I3 `target`，删括号说明、按 `| ; , /` 与空白切分、剥首尾标点、保留原始大小写）。
- **segment 集合 E_j（本轮新增概念，只用于蛋白全名匹配）**：把 I2 `target_name` 与 I3 `target` 的**原始字段**按 `|`、`;`、`,` 切分（**不切空白、不删括号**），逐段 `strip()`，丢弃空串；保留原始大小写与空格。E_j = 两来源并集。
- **base_v1（v1 精确层）**：`{t ∈ T_j : t 与 MSigDB S1(KEGG) 基因符号逐字符相等（大小写敏感）}`——即 P-A v1 的符号集合，v2 中**始终保留**（防止 v2 相对 v1 回退）。

## 5. HGNC 索引与归一（冻结）

- 匹配归一 `hnorm(s)` = `NFKC → casefold → 只保留 alnum`（即"大小写不敏感 + 去标点/空格后精确相等"）。
- 只用 `status == "Approved"` 的行（本文件全部为 Approved，仍按规则显式过滤）；多值字段按 `|` 切分后逐项 `strip()`。
- 索引（键 = `hnorm(值)`）：
  1. `SYM[hnorm(symbol)] → symbol`（当前符号，单值；若同键多值则取 `hgnc_id` 升序第一个并记冲突数）；
  2. `ALIAS[hnorm(alias_symbol)] → set(symbol)`；
  3. `PREV[hnorm(prev_symbol)] → set(symbol)`；
  4. `NAME[hnorm(name)] → set(symbol)`；
  5. `ALIAS_NAME[hnorm(alias_name)] → set(symbol)`。
- **候选过滤**：所有候选符号只保留在 **MSigDB S1(KEGG) 基因符号集合**（5,244 个）内的；集合外的候选丢弃（不参与评分，也不引发 ambiguous）。过滤后 0 个 → 该实体无贡献；1 个 → 唯一解析；≥2 个 → ambiguous 实体（§7）。

## 6. 解析层与优先级（冻结；主规则 = 任务给定）

对药物 j（按 §4 的 T_j / E_j）：

1. **base**：`base_v1`（§4）——直接进入符号集。
2. **token-symbol 层**：对每个 token `t ∈ T_j`，若 `hnorm(t) ∈ SYM` → 候选 = {SYM[hnorm(t)]}；若候选在 S1 符号集内 → 唯一解析。
3. **token-alias 层**：对每个 token `t ∈ T_j` 且 `hnorm(t) ∉ SYM` → 候选 = `(ALIAS ∪ PREV)[hnorm(t)]` 过滤到 S1 符号集；0/1/≥2 → 无贡献/唯一/ambiguous。
4. **segment-name 层**：对每个 segment `e ∈ E_j` → 候选 = `(NAME ∪ ALIAS_NAME)[hnorm(e)]` 过滤到 S1 符号集；0/1/≥2 → 无贡献/唯一/ambiguous。
5. **符号集 S_j(v2)** = base ∪ 所有唯一解析 ∪ 所有"经 §7 判定可解析"的 ambiguous 实体的候选（每个被解析实体取**候选符号名升序第一个**，确定性）。
6. 若 S_j 为空 → 该药 `unmapped`。`n_target_genes`（v2 表）= |S_j|。

**注**：DRH（I3）的 `target` 段也会走 segment-name 层（同一规则），但 DRH 值基本是符号，name 索引命中极少；token 层对两来源 token 一视同仁。不做别名推断以外的任何推断（不猜基因家族、不用同义词表、不用 Uniprot/RefSeq）。

## 7. ambiguous 实体的确定性处理（冻结；任务要求）

定义 ambiguous 实体 = §6 中候选 ≥2 的 token/segment（同一 token 在 T_j 内只算一次；segment 同）。

对药物 j 收集全部 ambiguous 实体 `A_j = {(实体, 候选集 C)}`：
1. 若 `A_j = ∅`：全部唯一解析直接生效。
2. 若 `|A_j| ≥ 1` 且 `|A_j| ≤ 3` 且 `Π|C| ≤ 16`：**枚举**所有候选组合（`Π|C|` 个）。对每个组合，用 `base ∪ 唯一解析 ∪ 组合` 计算规则 A 的 argmax 标签 L（S1、并列按通路名升序；此处只看标签，不看门槛）。
   - 若所有组合的 **L 完全相同** → 判定"取法不影响下游 argmax"，**解析**：每个 ambiguous 实体取候选名升序第一个，计入符号集；记 `ambiguous_entities_resolved`。
   - 否则 → 该药的**全部** ambiguous 实体不解析（只保留 base ∪ 唯一解析），记 `ambiguous_entities_unresolved`、`drugs_with_unresolved_ambiguity += 1`。
3. 若 `|A_j| > 3` 或 `Π|C| > 16`：不枚举，按"不猜"处理（同上，记 `drugs_capped_by_enumeration_limit`）。
4. 枚举组合按**候选名升序的笛卡尔积**（`itertools.product`，确定性顺序）；不引入随机。

## 8. 变体（主规则 + 3 个预注册敏感性；只报告，不改主判定）

| 变体 | 层 | 用途 |
|---|---|---|
| **V2-A（主规则）** | base + token-symbol + token-alias + segment-name | 任务给定的完整别名解析层 |
| V2-B | base + segment-name | 隔离"蛋白全名"层（高精度层）的增益 |
| V2-C | base + token-symbol | 隔离"大小写/punctuation 归一后的符号命中"（不含 alias/prev） |
| V2-D | V2-A 但剔除 `hnorm(token)` 长度 ≤2 的 token-alias/prev 解析（如 `II`/`of`/`H`） | 通用短别名精度诊断 |

四个变体都用 §7 的 ambiguity 规则（各自的实体集合）。**主判定只用 V2-A**；B/C/D 只作报告（§10）。另报告"通用短别名"（`hnorm` 长度 ≤3 的 token-alias/prev 解析，52 个 token/686 次药- token 出现，见 §2）对**标签 churn** 的影响（剔除后有多少药的 v2 标签改变）。

## 9. 评分、切分、门槛（冻结；与 P-A **逐字相同**）

- 评分：`score(j,P) = |S_j ∩ P|`（P ∈ I4 KEGG 186 集）；`max ≥ 1` → argmax 通路，并列按通路名升序；否则 `unmapped`。
- 切分：**PA 切分**（主口径）= 在 V2-A 已映射药集合 `M` 上 `k=max(1,round(0.2·|M|))`、`step=max(1,|M|//k)`、`H=names[0::step][:k]`；**E1 切分**（兼容口径）= 同一规则作用在 U（k=818，step=4）。
- 单元：`(cell_norm, unordered pair)`，共 380,418（与 v1 完全同口径）；both-unseen = H 内两药都在且均有注释；训练单元 = 两药均映射且非 both-unseen；严格训练 = 两药都不在 H。
- 可分析水平：≥2 药、训练 ≥1、留出 ≥1。
- **门槛（与 P-A 相同，不得改）**：G1 覆盖率（V2-A 映射药 / 4,088 ≥25%，即 ≥1,022，同时报 /4,076）；G2 可分析水平 ≥12（PA 切分）；G3 both-unseen 有注释单元（PA 切分）≥800；G4 训练有注释单元 ≥5,000。
- **判定**：G1–G4 与审计 A1–A5 全通过 → `mapping_v2_qualified`；任一失败 → `mapping_not_qualified`（列失败门槛与解冻条件）。

## 10. 必报数字（v1 → v2 对比；全部写入 `pa2.json` / `report_pa2.md`）

1. v1 参考值（从 `pa.json` 读入 + 重算断言）：映射药 1,418；覆盖 34.69%；可分析水平 62（E1 63）；both-unseen PA 2,682 / E1 3,739；训练 85,436（严格 58,788）；水平总数 123；并列率 60.93%；score=1 占比 52.33%。
2. v2（V2-A）同口径全部数字 + Δ；r=0.30/0.40 的 both-unseen（PA 与 E1 各一套）。
3. **解析层归因**：新增符号数（`|S_j(v2) \ base_v1|`）、新映射药数、按层的独有贡献（token-alias only / segment-name only / both）、被解析/未解析 ambiguous 实体计数与药数、枚举截断药数。**ambiguous 比例** = 含 ambiguous 实体的药数 / D1 药数，及 `ambiguous_entities_*`。
4. **标签 churn**：v1→v2 标签改变药数、改变方向（unmapped→有标签、有标签→unmapped、标签 A→B）、最常见转移对、示例（含 taxane/tubulin 类是否被纠正或恶化）。
5. **敏感性**：V2-B/C/D 的覆盖/水平/both-unseen/训练；通用短别名剔除后标签变化药数。
6. **12 个机制类药** v1 vs v2 对照（5-FU/Bortezomib/Cisplatin/Docetaxel/Gemcitabine/Oxaliplatin/Paclitaxel/Pictilisib/Taselisib/Temozolomide/Vinorelbine/Vorinostat）。
7. **审计**：v1 重算断言；v1 产物 SHA256 运行前后不变；输入+HGNC 哈希；非响应派生 grep；确定性（重复运行产物哈希一致）；HGNC URL/版本日期/SHA256。

## 11. 审计检查（冻结）

| # | 检查 | 通过条件 |
|---|---|---|
| A1 | 输入/资源完整性 | HGNC + I1–I5 存在、字节数/SHA256 与 §1 一致（不符即中止） |
| A2 | 非响应派生 | DENY 列从未取值（I1 只按列位置取身份列）；产物 grep 响应列名 0 命中；`pa2.json` 记录"仅列名、未取值" |
| A3 | v1 可复现（交叉校验） | `pa2.py` 重算的 v1 S1-A 数字与 `pa.json` 冻结值逐项相等：映射药 1,418 / 覆盖 34.6869% / 可分析水平 62 / both-unseen PA 2,682 / E1 3,739 / 训练 85,436 |
| A4 | 确定性 | `pa2.py` 无随机、无时间戳、JSON `sort_keys=True`；连续两次运行 `pa2.json`/`mapping_table_v2.csv` SHA256 相同 |
| A5 | v1 产物未被修改 | 运行前后 v1 四个产物的 SHA256 与 §1 冻结值相等 |

## 12. 产物（**只新增文件**，全部写在 `research/2026-10-27-drugcomb-annotation/`）

`PROTOCOL_PA2.md`（本文件，先冻结）、`pa2.py`、`pa2.json`、`mapping_table_v2.csv`、`report_pa2.md`、`record_pa2.md`、`usage_pa2.json`、`resources_hgnc/hgnc_complete_set.txt`。
`mapping_table_v2.csv`：V2-A 冻结映射表，4,088 行（U 全部药，S1 单库），列 = `drug_normalized_name, source_library, pathway, n_target_genes, n_genes_in_pathway, drug_drop, notes`；`source_library="S1"`；`pathway=unmapped` 未映射；`drug_drop ∈ {none, collision_key_conservatively_dropped, no_target_annotation, no_exact_or_resolved_gene_symbol}`；`notes` 为 `key=value;...`（含 `rule=A`、`n_symbols_v1`、`n_new_symbols`、`via_token_alias`、`via_segment_name`、`ambiguous_entities`、`ambiguous_resolved`、`max_score`、`tie_pathways`、`jaaks_pathway`）；排序 = 药名升序；`\n` 行尾。

## 13. 明确不做

不读响应值；不训练模型；不评估效应；不改 P-A v1 产物；不改其它目录/INDEX/SYNTHESIS/git；不改门槛或规则；不做同义词表以外的推断（不用 Uniprot/RefSeq/Ensembl 名称）；不把"v2 覆盖提升"写成"冻结结论已复现"；不因结果调整主变体。
