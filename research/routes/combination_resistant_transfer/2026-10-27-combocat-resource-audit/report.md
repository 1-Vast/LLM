# ComboCat 稠密组合补充表资源资格审计报告（R189 线 A1）

2026-10-27。角色：数据资格审计员（独立于提案者，不参与 A2 设计与效果运行）。本报告只回答**资源资格**（结构/身份/注释/重复/剂量/外部重合/both-unseen 切分可行性），不读响应数值、不跑响应建模、不做效应估计、不做假设检验、不联网。

- 冻结协议：[PROTOCOL.md](PROTOCOL.md)（只读，SHA256 `3918548e546f117ee8868306b6a89143292c0d41572a551f714839bdd56a640e`）
- 审计脚本：[audit.py](audit.py)；结果：[audit.json](audit.json)、[counts.json](counts.json)、[overlap.json](overlap.json)；时间线/预算：[record.md](record.md)；运行时账：[usage.json](usage.json)
- 输入 zip：`research/2026-10-27-oneil-transfer-qualification/combocat_dense_supp_data1.zip`（73,327,836 B，SHA256 `5639020dbe8359c8020e09e6f63cc152ab1179da19200b00e893ef19d7959e9e`，与 `download_receipt.json` 一致）
- zip 内 `Supplementary_Table_1_REVISED.xlsx`：74,857,017 B，SHA256 `c2f28b7550071a04a5743153d5aced7d43beccd043b6bf58ce7bc57c8328571c`

## 0. 判定（PROTOCOL §8 冻结门槛，不做事后调整）

**`unqualified`** —— 两个口径均为 `unqualified`：

| 口径 | 判定 | 主因 |
|---|---|---|
| (a) zip-only | `unqualified` | 身份不可得（804/806 root 为不可解析的 32 位十六进制 id；无 cell line 列；药名为占位符）；Q1 注释水平上限 5 < 12；Q2 both-unseen 单元不可计算且解析上界 351 < 800 |
| (b) 含已发布元数据（AMENDMENT-001：MOESM8） | `unqualified` | 同上；且 MOESM8 是**稀疏模式 135 化合物清单**（Supplementary Data 5），不含与稠密 root 的键；仅 2 个描述性 root 的 4 个药名可恢复，804 个 root 不受影响；Q1 上限仍为 5 |

判定不是"数据质量差"，而是**该补充表按设计被匿名化**（804/806 root 为哈希 id；药名一律 `drug1`/`drug2`；细胞系只有整数 ID + organism + lineage，无名字；稠密 136 药物无已发布名称表）。因此冻结结论"第二资源"复现所依赖的**实体身份、药物注释、药对图**在本轮冻结输入下不可重建。

## 1. 方法与边界

- 单次流式扫描 `data` sheet（292,458 行 × 45 列），不整表 materialize；只取 PROTOCOL §1 READ 列的值。
- **DENY 列（18 个）只做 `cell is None` 存在性计数**，不转换、不比较、不聚合、不写出任何数值；`flagged_*`（4 个）只统计空/非空；`unclassified` 列（8 个）**完全不读**（连空值检查都不做）。
- 身份：按 PROTOCOL §2 归一（NFKC → casefold → 仅保留 Unicode 字母数字）解析 `root_id`；对 32 位十六进制 root 做**有界**的 md5 模板反解尝试（见 §3）。
- 已发布元数据（AMENDMENT-001，读取任何响应值之前记录于 record.md）：`research/2026-10-27-detectability-acquisition/sources/41467_2025_66223_MOESM8_ESM.xlsx`（135 药物元数据，**无响应值**，SHA256 见 audit.json）；另引用同出版物 MOESM1/MOESM3 的既有本地文本摘录（SHA256 见 audit.json），只用于已发布事实与补料编号，不引入响应值。
- 外部名清单：Jaaks GDSC 原始组合表与 O'Neil 原始工作簿，只读身份列，沿用 oneil-transfer-qualification 的归一/碰撞口径；本轮重算结果与 prior `counts.json` **逐项一致**（Jaaks 121 细胞/65 药物/1,294 药对/67,812 cell×pair；O'Neil 35/38/583/20,405；批次 358,560/5,232/5,040）。
- 未做：任何响应值读取、任何效应/相关性/预测性能计算、A2 预注册运行、机制/靶点/临床推断、联网检索、修改源文件或其它研究目录。

## 2. 实测结构（与 BRIEF 先验对照）

| 先验（BRIEF/任务简报） | 实测 | 一致性 |
|---|---|---|
| 292,459 行 | **292,458 数据行**（292,459 含表头） | 一致（差 1 行为表头） |
| 45 列 | 45 列 | 一致 |
| 36 细胞 | 36 个整数 cell-line ID（**无名字**） | 一致（仅 ID） |
| 136 药物 | 136 个整数 drug ID（**无名字**） | 一致（仅 ID） |
| 806 组合 | **806 个 root_id = 806 个 (combination:cell_line) 单元 = 论文所称 806 块稠密组合板** | 一致，但语义需更正，见下 |
| 3 技术重复 | 每个 root 恰 3 个 replicate（各 97,486 行） | 一致 |
| 密集 10×10（论文） | 每 root 11 个 drug1 浓度 × 11 个 drug2 浓度 = 121 个设计孔 | 一致 |

**与先验假设不符处（均按实测复述，不判死）**

1. **`root_id` 并不承载真实实体名（任务简报的关键前提不成立）**：806 个 root 中 **804 个（99.752%）** 是 32 位十六进制（md5 形态）**不可解析 id**；仅 **2 个（0.248%）** 为描述性 id：
   - `CHP134_AZD1390_CX-5461.csv_AZD1390_CX-5461_CHP134`（细胞 `CHP134`，药 `AZD1390`/`CX-5461`；前缀 3 token 与后缀 3 token 均可解析）
   - `LUM_SMX_TMP.csv_Sulfamethoxazole_Trimethoprim_LUM_E. coli BW25113`（前缀可解析：细胞 `LUM`，药 `SMX`/`TMP`；后缀因细胞标签含空格/下划线而**歧义**（4 段而非 3 段）——药全名可按位置恢复为 `Sulfamethoxazole`/`Trimethoprim`，细胞全名不可无歧义恢复）
   即"真实实体在 root_id"只对 2/806 成立；其余 804 个 root 无法从本补充表恢复细胞系/药物身份。
2. **MOESM8 不是"136 行稠密药物名表"**：实测 135 行药物（表头 + 135）；按 MOESM3 补充文件索引，它是 **Supplementary Data 5 "The compounds used in the Combocat sparse mode screen"**（稀疏模式 135 化合物），与 zip 内 136 个稠密 drug ID **不是同一清单**（zip `drugs_summary` 含 antibiotic/antifungal/natural_product 类，MOESM8 Action_Class 只有 inhibitor/agonist/antagonist/degrader/binding disruptor）；且 MOESM8 **没有与 root_id 的键**。因此它无法把稠密 root 联到药名或 class（zip-only 与含元数据两种口径在这一点上同价）。
3. **806 是 cell×pair 单元总数，不是 both-unseen 子集**：806 root = 806 块板 = 806 个 (细胞, 无序药对) 单元（论文 MOESM1 图注："all 806 combination plates in the dense mode reference set"；zip 词表："Unique identifier (combination:cell_line)"）。BRIEF 的 Q2 门槛（≥800 both-unseen cell×pair 单元）与这一总量几乎相等，见 §6。
4. 缺失结构：**所有列都没有空白单元**（DENY 列 0/292,458 缺失）；设计元数据缺口以字符串 `"NA"` 表示：`Plate Barcode`/`plate_row`/`plate_col`/`plate_row_letter`/`transfer_type` 各 278,058 行；`drug1_nth_conc`/`drug2_nth_conc` 各 279,258 行。即"缺失"是**元数据未提供**，不是响应缺失。

## 3. 身份与注释

### 3.1 root_id 结构

| 类别 | 数量 | 占比 |
|---|---|---|
| 32 位十六进制（md5 形态）不可解析 | 804 | 99.752% |
| 描述性 `.csv_` id | 2 | 0.248% |
| 其它 | 0 | 0 |

- 描述性 root 前缀解析成功 2/2；后缀完整解析 1/2，歧义 1/2（`LUM_..._LUM_E. coli BW25113`）。**整体可解析率 2/806 = 0.248%；不可解析率 99.752%**。
- 可恢复实体 token：细胞 `{chp134, lum}`；药物 `{azd1390, cx5461, smx, tmp}`；另从 LUM 后缀按位置得到候选全名 `{sulfamethoxazole, trimethoprim}`（**候选别名，不并入任何主计数**，见 §5）。

### 3.2 哈希反解尝试（有界、只读、离线）

probe 与 `audit.py` 共测试 **3,383,955** 个 md5 候选，**0 命中**：

- 5 种 id 模板（`cellid_drug1id_drug2id` 及其 `.csv_`/顺序/分隔变体）× 36 细胞 ID × 136 药物 ID × 136 药物 ID；
- 3 种名称模板（`name1_name2` 及排序/冒号变体）× MOESM8 的 135 个稀疏药名两两组合；
- 40 个真实 plate barcode 的 md5。

结论：**没有证据表明冻结输入中的已发布名称/ID 能解码 804 个不透明 root**。不能证明作者使用了何种不可逆映射——只报告"在本轮可用元数据下不可解析"。这与论文自述的社区数据可"anonymized, stripped"贡献设计（MOESM1 补充图 5b）方向一致。

### 3.3 注释可分析性

| 注释表 | 水平 | 数量 |
|---|---|---|
| zip `cell_lines_summary` | 36 个 cell ID；organism：Human 33 / bacteria 2 / fungus 1；lineage **14 个水平**（peripheral_nervous_system 15、bone 7、bacterial_pathogen 3，其余 11 类各 1） | 无名字 |
| zip `drugs_summary` | 136 个 drug ID；class **5 个水平**：investigational 73、chemotherapeutic 26、antibiotic 18、antifungal 15、natural_product 4（每水平均 ≥2 药物；≥3 药物 5 水平；≥5 药物 4 水平） | 无名字 |
| MOESM8（稀疏模式清单） | 135 药物；Action_Class **5 个水平**：inhibitor 127、agonist 4、antagonist 2、degrader 1、binding disruptor 1（≥2 药物的水平 3 个）；Reported_Target 99 个水平 | 有名字但无 root 键 |

**关键点**：即使身份完全解决，冻结的"注释水平 = class"定义下最多只有 **5** 个可分析水平（Q1 门槛 12），Reported_Target（99 个水平）不是 class，按冻结口径不能替代；且 zip 的 136 个 class 是粗分类（investigational/chemotherapeutic/antibiotic/antifungal/natural_product），与"通路粗化注释"的既有定义是否可比也未验证。

## 4. 重复、板与剂量布局

- **replicate**：每个 root 恰 3 个 replicate（`{"3": 806}`），每 replicate 97,486 行；zip 词表原文：`Replicate per root_id (out of 3), all reps are in the same plate` → **同板技术重复**，不是独立培养。
- **Plate Barcode**：41 个不同值 = `"NA"`（**766 个 root / 278,058 行**）+ **40 个真实 barcode**（每个 360 行、恰对应 1 个 root，无 barcode 跨 root 碰撞）；root ↔ 板 1:1；**无跨板重复**（同一 root 不出现在多于 1 块板）。
- **行/根**：363 行/root（766 个 root）或 360 行/root（40 个有 barcode 的 in-house root）；完整 806×3×121 网格应有 292,578 行，实际 292,458，**缺 120 行**（= 40 块 in-house 板 × 缺 1 个 (0,0) 设计孔 × 3 重复）。
- **transfer_type**（只对 40 个有 barcode 的板提供）：combination 12,000 行 / single_agent_drug1 1,200 / single_agent_drug2 1,200；其余 278,058 行为 `"NA"`。按剂量=0 的设计标记独立复算的孔类型（全表）：组合孔 241,800 行、drug1 单药孔 24,180、drug2 单药孔 24,180、(0,0) 对照孔 2,298，合计 292,458。
- **剂量布局**：每个 root 的 drug1 与 drug2 各 11 个唯一浓度值（10 个测试剂量 + 0），(d1,d2) 唯一设计对数：121（766 root）或 120（40 root）。单位：uM 532 root / ug_mL 145 / nM 113 / mg L-1 16。共 806 个 root 均有完整剂量设计值（该列不依赖身份）。

## 5. QC / 缺失结构 与"未读列"清单

- DENY 列 **18 个**（只做 None 计数）：`raw_val`, `replicate_perc_cell_death`, `perc_cell_death`, `single_effect_drug1`, `single_effect_drug2`, `bliss_exp`, `bliss_synergy`, `single_agent_sd`, `prev_val_low_to_high`, `delta_val_low_to_high`, `prev_val_high_to_low`, `delta_val_high_to_low`, `mean_syn`, `median_syn`, `mean_syn_adj`, `median_syn_adj`, `mean_perc_cell_death`, `moran_i_pval`。全部 **0 个空值 / 292,458 行**（结构性完整；本轮从未读取其数值）。
- `flagged_*`（4 个，只统计空/非空，不读数值）：`flagged_sd`、`flagged_mono`、`flagged_resid`、`flagged_final`，均 0 空值。
- **未读列（连空值检查都不做）8 个**：`zprime`、`robust_zprime`、`moran_i`、`abs_res`、`nearest_pred`、`nearest_dose`、`Amount`、`...9`（表头字面值）。其中 `zprime`/`robust_zprime`/`moran_i`/`abs_res`/`nearest_pred`/`nearest_dose` 语义上属 QC/拟合派生诊断，但**列名不匹配 PROTOCOL §1 DENY 模式**（`moran_i_pval` 因含 `val` 命中 DENY）；按"未知列不读"的冻结规则，一律不读，仅在 §7 语义表按列名+zip 词表分类。
- **端点语义分类（§7，仅列名 + zip 内置词表证据；全部未读数值）**：
  - `measured_raw`：`raw_val`（"Raw value prior to any normalization"）
  - `derived`：`replicate_perc_cell_death`、`perc_cell_death`、`bliss_exp`、`bliss_synergy`、`prev_val_*`×2、`delta_val_*`×2、`mean_syn`、`median_syn`、`mean_syn_adj`、`median_syn_adj`、`mean_perc_cell_death`、`abs_res`、`moran_i`、`moran_i_pval`、`nearest_dose`
  - `single_agent_or_control`：`single_effect_drug1`、`single_effect_drug2`、`single_agent_sd`
  - `imputed_or_predicted`：`nearest_pred`（"nearest predicted response"，DR 曲线拟合派生）
  - `qc_flag`：`flagged_sd`、`flagged_mono`、`flagged_resid`、`flagged_final`、`zprime`、`robust_zprime`

## 6. 外部实体重合（PROTOCOL §3，严格文本名口径）

- 归一/碰撞口径：NFKC → casefold → 只保留字母数字；碰撞键在**两外部源并集**上检测并保守剔除（沿用 oneil-transfer-qualification `qualify.py` 口径；并集口径 4 个细胞碰撞键：`HCT-116/HCT116`、`HT-29/HT29`、`MDA-MB-436/MDAMB436`、`OCUB-M/OCUBM`；两源内部各自无碰撞键）。重算结果与 prior counts.json 完全一致 → 口径可复现。
- **严格交集（ComboCat 可恢复实体 vs 外部源）**：细胞 **0**、药物 **0**、药对 **0**。可恢复的 2 个细胞 token（`chp134`, `lum`）、4 个药物 token（`azd1390`, `cx5461`, `smx`, `tmp`）在 Jaaks/O'Neil 中均无同名项；宽松口径（不剔碰撞 + 别名候选）也仍为 0。
- **清单层面（口径 b，仅文本、无实体映射）**：MOESM8 的 135 个稀疏模式化合物名 vs Jaaks 药物名重合 **28**、vs O'Neil 重合 **13**。注意这是"稀疏模式化合物清单"的文本重合，**不是**稠密 root 的药物映射，不能据此推断稠密数据集与 Jaaks/O'Neil 的泄漏关系。
- 804 个不透明 root 的细胞/药物/药对是否与 Jaaks/O'Neil 重合**不可验证** → Q4 对"外部复现"表述只能加限定，不能证明"未见实体"。

## 7. both-unseen 留药切分可行性（§6，只用身份与药对图）

- 冻结参数：N_drug = 136（`drugs_summary` 的整数身份 id 数），N_cell = 36，**总 cell×pair 单元 = 806**；r ∈ {0.20, 0.30, 0.40} → k = round(r×136) = **27 / 41 / 54**。
- **主估计（确定性字典序）**：**不可计算**（null）。需要 root → (细胞, 药对) 身份才可建药对图；804/806 root 不可解析。
- **随机敏感性（seed 20261027，1000 次 holdout）**：**不可计算**（null），同因。
- **结构上界（贪心）**：**不可计算**（null），需要药对图；改为给出与身份无关的解析界：
  - both-unseen 单元 ≤ 总单元数 = **806**；
  - both-unseen 单元 ≤ 只由留出药构成的无序药对数 C(k,2) = **351 / 820 / 1,431**；
  - 二者合并的保守上界 = min(806, C(k,2)) = **351 / 806 / 806**；
  - 若药对在 136 药上近似均匀，both-unseen 期望单元 ≈ (k/136)²×806 = f²×806 = **31.8 / 73.3 / 127.1**（r=0.2/0.3/0.4）。
- **与 BRIEF 门槛 ≥800 cell×pair 单元比较**：
  - r=0.20：硬上界 351 < 800 → **确实不满足**（与身份无关的解析结论）；
  - r=0.30/0.40：只有把 806 个总单元中 ≥99.25% 都变成 both-unseen 才可能 ≥800；在 136 药/806 药对/均匀假设下期望只有 73.3/127.1 → **实际上不可达**（且药对图不可得，无法证明存在这种极端集中）。
  - 换言之：BRIEF 的 800 门槛是对"远多于 806 个单元的资源"设定的；ComboCat 稠密表**总单元数 806**，即便身份全部公开，20–40% 留药也几乎不可能达到 800。**Q2 失败是结构性的，不只是匿名化造成的。**
- **注释水平可分析性（Q1）**：冻结定义为 class 水平（≥2 药物、训练/留出各 ≥1）。已发布 class 分类最多 **5 个水平** → 远低于 12。**Q1 失败同样是结构性的**（不依赖身份）。

## 8. Q1–Q5 逐条判定（冻结门槛）

| 门槛 | 实测/上界 | 门槛 | 判定 |
|---|---|---|---|
| **Q1 注释水平** | 可分析 class 水平上限 **5**（zip class 5 水平；MOESM8 Action_Class 5 水平；每水平≥2 药物的水平：zip 5 / MOESM8 3） | ≥12 | **不满足**（结构性：已发布注释分类只有 5 个水平；且逐 root 的 class 不可得） |
| **Q2 both-unseen 规模** | 主估计 **null**、随机敏感性 **null**、贪心上界 **null**（不可计算）；解析上界 351/806/806；总单元 806；均匀期望 31.8/73.3/127.1 | ≥800 | **不满足**（r=0.2 硬上界 351<800；r=0.3/0.4 需要 ≥99.25% 单元集中才可能，实际不可达） |
| **Q3 注释水平在训练出现** | 不可计算（无逐 root 药物/class 归属；training-unseen class 数无法统计） | =0 | **不可判定 → 不满足**（无法证明满足） |
| **Q4 外部性** | 可恢复实体严格重合 0/0/0；清单层面 MOESM8 与 Jaaks/O'Neil 文本重合 28/13；804 个不透明 root 不可验证 | 只报告 | **报告级**：只能在可恢复的 2 个 root 上声明无同名重合；"第二资源/未见实体"对外部复现的表述必须加限定 |
| **Q5 端点/重复限制** | 端点为 luminescence 活力派生 %Cell Death（raw_val → 归一化 → Bliss 派生）；3 个重复为**同板技术重复**（zip 词表原文） | 限制性 | **始终成立**：只能检验"粗注释替代身份"的可重复性，不构成独立功能终点/独立培养/机制/临床结论 |

**总判定：`unqualified`**（zip-only 与含已发布元数据两口径一致）。

## 9. 失败类别与解冻条件

**失败类别**（PROTOCOL §9）：
- `assumption_contradicts`：root_id 匿名化（804/806 哈希）、MOESM8 为稀疏模式清单而非稠密药物名表、806 为 cell×pair 总单元数；
- `data_unavailable`：无 cell-line 列、药名占位符、804/806 root 不可解析、无稠密药物名↔class 表；
- `data_insufficient`：Q1（class 水平 5 < 12）、Q2（both-unseen 上界 351 < 800，总单元 806）；
- `evaluation_cannot_distinguish`：Q3（逐 root 药物/class 归属不可得）。

**解冻条件**（全部为资源层面，非统计层面）：
1. 提供**非匿名化的 root_id → (细胞系名, drug1 名, drug2 名) 映射**（或去匿名化稠密表），使药对图与 both-unseen 切分可构造；
2. 提供**稠密 136 药物的名称 + class 注释**，且 class 水平 ≥12（可分析水平，训练/留出均出现）；
3. 单元数足够：要满足"≥800 both-unseen 单元"且留药 20–40%，粗估需要总 cell×pair 单元 ≥ 800/f² ≈ **2,000–5,000**（当前 806，差一个数量级）；若维持 ComboCat 现有 806 单元，则门槛必须重新冻结（本轮不允许事后调整）；
4. 若要把结论升级为独立功能终点/独立培养证据：需要非 viability 的独立功能端点与独立培养重复——当前资源结构性没有。

## 10. 局限

- **技术重复 ≠ 独立培养**：3 个 replicate 全部同板（zip 词表原文），本审计只能刻画"同板技术重复"，不能推断培养独立性；40 块有 barcode 的板也不证明独立生物学来源。
- **viability 派生端点 ≠ 独立功能终点**：端点链为 raw_val → 归一化 %Cell Death → Bliss 派生量（全部 DENY、未读数值）；不构成独立功能终点，不能支持机制/靶点占据/临床主张。
- 身份结论只到"在本轮冻结输入 + AMENDMENT-001 已发布元数据下不可解析"，**不能证明**作者用了何种不可逆映射，也不能证明 804 个匿名 root 的数据来源或是否与 Jaaks/O'Neil 重叠（Q4 外部性对 804 root 不可验证）。
- 严格文本名匹配不是化学/细胞实体解析；不做同义词推断、不联网、不引入外部 ID 库（按协议）。
- 与 Jaaks 的重合是对**完整原始表**的文本重合，不是对某个具体训练切分的重合；不构成泄漏裁决。
- `Supp_Table_All_Dense_Mode_Summa`（zip 内 39×2 词表）与论文补充材料（MOESM1/MOESM3 的既有本地摘录）只用于已发布事实引用；MOESM8 只用于元数据（无响应值）。
- 本轮没有运行 A2、没有估计任何效应量/相关性/预测性能；`unqualified` 是资源资格结论，不是对 ComboCat 科学价值的评价。

## 11. 复现

```powershell
cd D:\MAESTRO
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-combocat-resource-audit\audit.py
```

- 脚本只读、确定性：JSON 键排序、无时间戳、无未定种子随机；输入（zip/xlsx/协议/MOESM8/Jaaks/O'Neil/prior counts）、脚本自身 SHA256 均写入 `audit.json`。
- 实测耗时（本机）：约 85–103 s（数据流式扫描 54–64 s、外部源 26–32 s、写盘与哈希 4–5 s）；单命令远低于 15 分钟上限。
- 复跑一致：连续两次运行 `audit.json`/`counts.json`/`overlap.json` 的 SHA256 逐一相同（见 record.md）。
- 响应数值保护：DENY 列仅 `cell is None` 计数；输出 grep 复核未出现任何响应值。
