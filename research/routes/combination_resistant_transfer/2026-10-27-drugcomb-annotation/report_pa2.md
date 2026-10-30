# P-A2 报告：HGNC 别名解析层 + 冻结 S1-A 规则重跑（R192 前置）

**日期**：2026-10-27 · **角色**：注释映射与覆盖审计员（独立于提案者）· **任务**：task-9
**协议**：`PROTOCOL_PA2.md`（**在 `pa2.py` 存在前冻结**），SHA256 `447ca67e787f7648ee3c274372bc3fd81c8cedb1288049fad1c225395d8ed1a0`
**脚本**：`pa2.py`（复用 P-A v1 的 `pa.py` 实现，`sys.dont_write_bytecode=True`），SHA256 `65e1113adfa50d4eda8915647e102f3ff4b1623d80ffe022e0faf35954e65f4d`
**范围**：只新增文件；**未修改 P-A v1 任何产物**（运行前后 SHA256 全等，A5）；**未读任何 DrugComb 响应值**；不训练模型、不评估效应。

---

## 判定

# `mapping_v2_qualified`

主变体 **V2-A**（base + token-symbol + token-alias + segment-name，HGNC 解析）通过**同一套** G1–G4 门槛与 A1–A5 审计：

| 门槛 | 阈值 | v1（P-A） | **v2（V2-A）** | Δ | 结果 |
|---|---|---|---|---|---|
| G1 药物覆盖 | ≥25%（≥1,022/4,088） | 1,418 = 34.69% | **1,800 = 44.03%** | **+382（+9.34 pp）** | ✅ |
| G2 可分析水平（PA 切分） | ≥12 | 62 | **79** | **+17**（E1 切分 63→72，+9） | ✅ |
| G3 both-unseen 有注释单元（PA 切分） | ≥800 | 2,682 | **3,056** | **+374**（E1 切分 3,739→4,654，+915） | ✅ |
| G4 训练有注释单元 | ≥5,000 | 85,436 | **117,106** | **+31,670**（严格口径 58,788→83,684，+24,896） | ✅ |

**冻结 v2 表 SHA256：`705a5e6476319b587c9b5e852590baef817cec7b8c4d69b0a54ec7cc686ed015`**（`mapping_table_v2.csv`，4,088 行 × S1 单库）
**HGNC 来源**：`https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt`；16,982,321 B；SHA256 `12363916be36f8f6f91879b0faade4eeaac973722de7136ec61329b77f2c2f91`；45,277 行（全 Approved）；**版本日期 = max(date_modified) = 2026-10-15**。
**无失败门槛、无解冻条件**；4 条随判定条件见 §11。

---

## 1. HGNC 资源与索引

| 项 | 值 |
|---|---|
| URL（首选，成功） / 备选（未用） | googleapis HGNC tsv / EBI genenames tsv |
| 字节 / 行数 / 列数 | 16,982,321 B / 45,277 数据行 / 53 列（只用 7 列） |
| SHA256（冻结） | `12363916be36f8f6f91879b0faade4eeaac973722de7136ec61329b77f2c2f91` |
| status | 45,277 行全部 `Approved`（仍按规则显式过滤） |
| 版本日期 | `max(date_modified) = 2026-10-15`（min 2003-10-09） |
| 归一匹配键（`NFKC→casefold→alnum`） | symbol 45,258（19 个归一冲突，取 hgnc_id 序第一个）；alias_symbol 42,151（1,508 个多 symbol 键）；prev_symbol 15,701（100）；name 45,260（14）；alias_name 11,595（116） |

归一规则（协议 §5）：`hnorm = NFKC → casefold → 只保留 alnum`，即"大小写不敏感 + 去标点/空格后精确相等"；候选符号过滤到 **MSigDB KEGG 基因符号（5,244）**。**base_v1（v1 精确层）始终保留**，故 v2 无"已映射→未映射"回退（实测 lost=0）。

## 2. 规则摘要（协议 §4–§7）

- 目标基因集 = `base_v1 ∪ token-symbol 解析 ∪ token-alias/prev 解析 ∪ segment-name/alias_name 解析`。
- **token 层**：token（P-A 的 T1 切分产物，保留原大小写）→ `hnorm` → 命中当前 symbol 取自身（优先），否则并集 alias/prev → 候选过滤到 KEGG 符号。
- **segment 层**：I2 `target_name` / I3 `target` 的原始 `| ; ,` 分段（**不切空白、不删括号**）→ `hnorm` → 命中 `name ∪ alias_name`（蛋白全名层）。
- **ambiguous 处理（冻结）**：候选 ≥2 的实体不直接猜；**枚举**候选组合（≤3 实体且积 ≤16），若所有组合的**下游 argmax 标签相同**才解析（每实体取候选名升序第一个），否则整药 ambiguous 不猜；超限药记为 capped 不猜。
- 评分/切分/门槛与 P-A **逐字相同**：`score=|S∩P|`、argmax、并列按通路名；PA 切分（N=已映射药）为主、E1 切分（N=4,088，k=818）为兼容口径。

## 3. 主结果：v1 → v2 全口径对比（V2-A）

| 指标 | v1 | v2(V2-A) | Δ |
|---|---|---|---|
| 映射药（D1，碰撞剔除后） | 1,418 | **1,800** | +382 |
| 覆盖率（/4,088） | 34.69% | **44.03%** | **+9.34 pp** |
| 覆盖率（/4,076） | 34.79% | 44.16% | +9.37 pp |
| 水平总数 | 123 | 125 | +2 |
| 水平（≥2 药） | 91 | 101 | +10 |
| 可分析水平（PA 切分） | 62 | **79** | +17 |
| 可分析水平（E1 切分） | 63 | 72 | +9 |
| 留出集内无药的水平（PA） | 51 | 34 | −17 |
| both-unseen 有注释单元（PA 切分，主口径） | 2,682 | **3,056** | +374 |
| both-unseen 有注释单元（E1 切分） | 3,739 | **4,654** | +915 |
| 两药均映射的 cell×pair 单元 | 88,118 | 120,162 | +32,044 |
| 训练有注释单元（PA 切分） | 85,436 | 117,106 | +31,670 |
| 严格训练单元（两药均不在留出集） | 58,788 | 83,684 | +24,896 |
| 并列率（规则 A） | 60.93% | 59.56% | −1.37 pp |
| 单基因命中（score=1）占比 | 52.33% | 50.39% | −1.94 pp |
| 最大水平占比 | 13.12%（186 药） | 12.39%（223 药） | −0.73 pp |

**r 敏感性（both-unseen 单元）**：

| r | PA 切分 v1 → v2 | E1 切分 v1 → v2 |
|---|---|---|
| 0.20 | 2,682 → **3,056** | 3,739 → **4,654** |
| 0.30 | 6,411 → **11,462** | 7,334 → **9,788** |
| 0.40 | 13,795 → **19,319** | 11,912 → **17,564** |

**两种切分口径给出不同的 both-unseen 数字（v2：PA 3,056 / E1 4,654）——阶段 2 必须先冻结用哪一个**（PA 切分让注释臂在测试集恒有注释；E1 切分与 R190 的 16,078 单元兼容，v2 下其中 29.0% 两药均有注释，v1 为 23.3%）。

## 4. 解析层归因（V2-A）

| 层 | 贡献符号数 | 贡献药数（有 ≥1 该层新符号） | 独占贡献药数 |
|---|---|---|---|
| segment-name（蛋白全名） | 1,614 | 590 | **322** |
| token-alias / prev symbol | 1,058 | 533 | **271** |
| token-symbol（大小写/标点归一后命中） | 155 | 118 | 37 |
| 多层同时贡献 | — | 277 | 277 |

- 共 **930 / 4,076 D1 药**（22.8%）获得 ≥1 个新符号，新增符号总数 **2,935**。
- **主增益来自"蛋白全名"层**（segment-name 590 药、独占 322 药），token-alias 层次之（533 / 271），token-symbol 层仅 118 / 37。
- 新映射药 382 个、丢失映射 0 个；标签改变 247 个（详见 §6）。

## 5. ambiguous 统计（任务要求）

| 指标 | 值 |
|---|---|
| 含 ambiguous 实体的 D1 药 | **211 / 4,076 = 5.18%** |
| ambiguous 实体总数 | 284（token-alias 281 + segment-name 3） |
| 其中经"不影响 argmax"判定**解析** | **206**（72.5%） |
| 其中**不猜**（unresolved） | 78（27.5%），涉及 57 个药 |
| 枚举截断（>3 实体或积>16）药 | 4（不猜） |

即：**95% 的 D1 药不含 ambiguous 实体；含 ambiguous 的药里只有约 27% 的实体因会改变 argmax 而被拒绝解析**。逐药计数（`ambiguous_entities` / `ambiguous_resolved`）记录在 `mapping_table_v2.csv` 的 `notes` 列；逐层与逐变体的汇总计数在 `pa2.json` → `variants.*.resolution_stats`。

## 6. 标签 churn（v1 → v2）

| 类别 | 药数 |
|---|---|
| 标签相同 | 3,447（含 v1/v2 均 unmapped 的 2,276） |
| **unmapped → mapped** | **382** |
| mapped → unmapped | **0** |
| 有标签但标签改变 | **247**（占 v1 映射药的 17.4%） |

最常见转移（前 5）：`KEGG_CALCIUM_SIGNALING_PATHWAY→KEGG_NEUROACTIVE_LIGAND_RECEPTOR_INTERACTION`(13)、`CHEMOKINE→MAPK`(8)、`ACUTE_MYELOID_LEUKEMIA→PATHWAYS_IN_CANCER`(7)、`PATHWAYS_IN_CANCER→MAPK`(6)、`ADHERENS_JUNCTION→CHRONIC_MYELOID_LEUKEMIA`(4)。churn 主要来自新增符号改变 argmax 分数分布（更多靠前通路竞争），**方向上是"更细的粗注释"而不是回退**（无 mapped→unmapped）。

## 7. 敏感性变体（协议 §8；主判定只用 V2-A）

| 变体 | 层 | 映射药（/4,088） | 可分析水平 PA / E1 | both-unseen PA / E1 | 训练单元 |
|---|---|---|---|---|---|
| **V2-A（主）** | base+token-symbol+token-alias+segment | **1,800（44.03%）** | **79 / 72** | **3,056 / 4,654** | 117,106 |
| V2-B | base+segment-name | 1,648（40.31%） | 75 / 70 | 2,078 / 4,580 | 106,788 |
| V2-C | base+token-symbol | 1,458（35.67%） | 73 / 63 | 2,660 / 3,752 | 88,915 |
| V2-D | V2-A 但剔除 hnorm≤2 的短别名解析 | 1,770（43.30%） | 73 / 70 | 3,068 / 4,647 | 113,147 |

- **注意 V2-B 的 both-unseen PA（2,078）低于 v1（2,682）**：切分建在各自映射药集合上，映射集合变化会改变留出集组成 → **both-unseen 单元数对映射集合非单调**；四个变体的 both-unseen 不能当作"覆盖越高越多"直接比较，报告以各自切分为准。
- **通用短别名精度诊断**：hnorm 长度 ≤3 且经 alias/prev 解析的 token 有 **52 个**（如 `II`/`of`/`H`/`H1`/`p38`/`tau`/`A1`/`B1`，见 `pa2.json` 列表）。剔除 ≤2 长度（V2-D）→ 55 个药的标签改变；剔除 ≤3 长度 → **111 个药的标签改变（约 6.2% 映射药）**。这些是"通用/编号式 HGNC 别名"的已知噪声源，**未从主规则中剔除**（任务给定规则），但已量化：**v2 的覆盖/水平提升中约 43.30%（V2-D）在不含 ≤2 短别名时仍成立**。

## 8. 12 个机制类药（v1 vs v2）

| 药 | v1 标签 | v2 标签 | 符号数 v1→v2 | 说明 |
|---|---|---|---|---|
| 5-FU | unmapped | unmapped | 0→0 | **药物名**同义词失配（`5-FU` vs `5-Fluorouracil`），不属本轮靶点别名层；仍未映射 |
| Bortezomib | PROTEASOME | PROTEASOME | 23→26 | 新增 CD79A/CTSG/NFKB1 等 |
| Cisplatin | APOPTOSIS | APOPTOSIS | 1→1 | 仍为单基因弱证据 |
| Docetaxel | GAP_JUNCTION | GAP_JUNCTION | 18→18 | tubulin 家族偏置未变 |
| Gemcitabine | PYRIMIDINE_METABOLISM | PYRIMIDINE_METABOLISM | 4→4 | — |
| Oxaliplatin | unmapped | unmapped | 0→0 | I3 无 target，I2 无该药 |
| Paclitaxel | PATHOGENIC_ESCHERICHIA_COLI_INFECTION | 同左 | 19→21 | 新增 MTOR/THRB，标签仍为家族偏置例 |
| Pictilisib | 不在宇宙 | 不在宇宙 | 0→0 | v1.4 组合块无此药 |
| Taselisib | ACUTE_MYELOID_LEUKEMIA | **INOSITOL_PHOSPHATE_METABOLISM** | 2→4（+PIK3C3/SGCG） | 标签改变，但仍弱证据 |
| Temozolomide | unmapped | unmapped | 0→0 | `DNA`/`MGMT` 不在 KEGG |
| Vinorelbine | GAP_JUNCTION | GAP_JUNCTION | 16→16 | — |
| Vorinostat | 不在宇宙 | 不在宇宙 | 0→0 | v1.4 组合块无此药 |

**结论**：v2 主要提升"覆盖面"与"水平多样性"，**不改变规则 A 的语义局限**（taxane→tubulin 家族偏置、单基因弱证据依旧），5-FU 之类的**药物名**同义词问题不在本轮解决范围。

## 9. 审计

| # | 检查 | 结果 |
|---|---|---|
| A1 | 输入/资源完整性 | I1–I7 + HGNC 字节/SHA256 逐条匹配（全 ok） |
| A2 | 非响应派生 | v1.4 只按列位置读身份列；12 个响应列仅记列名；`mapping_table_v2.csv` grep `synergy|bliss|loewe|ic50|css|ri_row|ri_col|S_mean|S_sum` = **0 命中** |
| A3 | v1 可复现 | `pa2.py` 重算 v1 S1-A：1,418 / 34.6869% / 62 / 2,682 / 3,739 / 85,436 与 `pa.json` 冻结值**逐项相等** |
| A4 | 确定性 | 连续两次运行 `pa2.json`、`mapping_table_v2.csv` SHA256 完全一致（`41edb023…` / `705a5e64…`） |
| A5 | v1 产物未修改 | 运行前后 v1 四个产物 SHA256 全等于协议 §1 冻结值 |

## 10. 产物 SHA256

| 产物 | 字节 | SHA256 |
|---|---|---|
| `PROTOCOL_PA2.md`（先冻结） | 15,018 | `447ca67e787f7648ee3c274372bc3fd81c8cedb1288049fad1c225395d8ed1a0` |
| `pa2.py` | 40,184 | `65e1113adfa50d4eda8915647e102f3ff4b1623d80ffe022e0faf35954e65f4d` |
| `pa2.json` | 58,233 | `41edb023e8fffc20607a5eff9048fb1bc9560108c50c818715a43a145b697c61` |
| **`mapping_table_v2.csv`（冻结 v2 表）** | 1,104,670 | **`705a5e6476319b587c9b5e852590baef817cec7b8c4d69b0a54ec7cc686ed015`** |
| `resources_hgnc/hgnc_complete_set.txt` | 16,982,321 | `12363916be36f8f6f91879b0faade4eeaac973722de7136ec61329b77f2c2f91` |
| `report_pa2.md` | — | 见 `usage_pa2.json` |
| `record_pa2.md` | — | 见 `usage_pa2.json` |

`mapping_table_v2.csv` 格式：4,088 行（U 全部药，`source_library="S1"`），列 `drug_normalized_name, source_library, pathway, n_target_genes, n_genes_in_pathway, drug_drop, notes`；`pathway=unmapped` 2,288 行（其中 1,709 `no_target_annotation`、567 `no_exact_or_resolved_gene_symbol`、12 `collision_key_conservatively_dropped`），映射 1,800 行；`notes` 含 `rule=A;n_symbols_v1;n_symbols_v2;n_new_symbols;via_token_symbol;via_token_alias;via_segment_name;ambiguous_entities;ambiguous_resolved;max_score;tie_pathways;jaaks_pathway`。

## 11. 局限与随判定带走的条件

1. **切分口径仍需阶段 2 冻结**：v2 同时报告 PA 3,056 / E1 4,654 两种 both-unseen 有注释单元；两者都 ≥800 但含义不同，不可事后换。
2. **短/通用别名噪声**：52 个 hnorm≤3 的 alias/prev 解析 token 影响约 55–111 个药的标签（取决于剔除阈值）；若阶段 2 追求精度，可用 `V2-D`（1,770 药，43.30%，73 可分析水平）或"仅蛋白全名层"的 `V2-B`（1,648 药，40.31%，75 可分析水平）——**v2 主判定按任务规定用 V2-A**。
3. **规则 A 语义不变**：并列率 59.56%、单基因命中 50.39%、taxane→tubulin 家族偏置仍在；v2 是"更多药获得粗注释"，不是"粗注释变成机制注释"。
4. **药物名同义词不在本轮范围**：5-FU 等仍 unmapped（本轮只解析**靶点**别名/蛋白名）。
5. **HGNC 是活文件**：本报告冻结的是 2026-10-15 版本（SHA256 已记录）；后续更新需重新冻结。
6. **v2 表只覆盖 S1(KEGG) 单库**；若阶段 2 需要 Hallmark/混合库，需新协议。

## 12. 复现

```powershell
cd D:\MAESTRO\research\2026-10-27-drugcomb-annotation
& 'D:\anaconda\envs\maestro\python.exe' pa2.py
# 期望：VERDICT mapping_v2_qualified；v2 mapped 1800 (44.03%) levels 79 both_pa 3056 both_e1 4654 train 117106
# mapping_table_v2.csv SHA256 = 705a5e6476319b587c9b5e852590baef817cec7b8c4d69b0a54ec7cc686ed015
```
