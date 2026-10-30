# R190 线 D 定向先例核验（prior_art）

**日期**：2026-10-27 ｜ **核验员**：cellstate-lit（task-5） ｜ **范围**：只做先例核验；不运行效果实验、不评估本机数据、不改 PROTOCOL。
**问题对象**：R190 线 D —— 用药物靶点基因的细胞表达作细胞状态特征，检验模型能否在**留出细胞**上把**同一药对内**的细胞按 `ΔEMAX` 排出次序（`research/2026-10-27-innovation-round-r190/BRIEF.md`；`research/2026-10-27-cellstate-qualification/PROTOCOL_A0.md`）。
**检索预算**：2 个 pass（PASS 1 广撒网 + PASS 2 补缺），合并查询；联网仅 Europe PMC REST / OpenAlex API / arXiv API；本地 `reference/`、`lit/`、既有 research 全文优先。查询清单、原始响应、失败与重试见 [`sources_lit/pass_log.md`](sources_lit/pass_log.md) 与 `sources_lit/raw/`。
**证据状态词**：`full-text`＝读到一手全文（或 PDF 抽取全文）并给行锚；`abstract-only`＝只有一手摘要；`local-secondary`＝本机二手整理（未回原文）；`search-result`＝检索结果（含零命中），**不写作"不存在"**。

---

## 0. 结论（一句话）

**部分覆盖。** 线 D 的三个构成要素——（i）用细胞系表达/通路/蛋白等**细胞状态特征**预测协同、（ii）**留出细胞**（cell-unseen / LOCO / LCO）评估、（iii）把**同一处理内跨细胞排序**当作独立评价对象——都已有发表先例（分别可追到 DeepSynergy 2018、One-Hot News 2026 / SynVerse 2025 / PDTSyn 2026、arXiv 2605.20885 2026）；但把三者合到**"`ΔEMAX` 的 within-pair 细胞排序"**这一个具体端点上、且同时**两药未见 × 细胞留出**的工作，**本轮未发现**（零命中只作检索结果，**不是"不存在"**）。
→ 因此：**不得声称新颖性/空白**；若线 D 的卖点是"新特征类/新评估对象/填补冷启动空白"，这三项**已被覆盖**，**应收窄为复现/评估修正或停线，不换名重启**；若继续，只能作为"把已发表的 reliability/room 门控与 per-treatment 排序口径迁移到 `ΔEMAX` 协同"的**复现 + 评估修正**来写，并且必须先补检索才能把任何"未发现"升级为"空白"。

---

## 1. 逐题结论

### Q1 细胞系组学/表达特征用于组合协同预测：是否做留出细胞评估？是否报告 within-pair 细胞排序？什么指标？

**已覆盖（留出细胞评估）**：DeepSynergy 2018 就做了 "novel cell lines" 的分层交叉验证，指标 MSE/RMSE/Pearson（F01/F02）；2025–2026 的 One-Hot News 2026（LCO 表）、SynVerse 2025（leave cell line、RMSE/PCC）、PDTSyn 2026（unseen cell line CV、MSE/RMSE/PCC）、SynProtX 2025（leave-cell-line-out cold start、AUROC/AUPRC/F1/kappa）、BMC Bioinformatics 2026 cold-start benchmark（unseen cell lines、balanced accuracy）都做了细胞留出评估（F03–F09）。**这些工作没有一个把"同一药对内细胞排序"作为报告指标**；它们报告全局 MSE/RMSE/PCC/SCC/AUC/AUPRC/balanced accuracy。
**未发现（within-pair cell ranking）**：在上述协同模型中未见以 within-pair 细胞排序为主端点或副端点者。

### Q2 冷启动（两药未见）+ 细胞状态特征是否已被覆盖？与 Candir `One-Hot News` "表示当标识符"路线的关系？

**部分覆盖。** 两药未见（LDO）已在 One-Hot News 里单独成表：细胞特征与 one-hot 都差，且细胞特征并不救场（F10/F11）；用**通路激活**作细胞特征的 DIPx 在"两药都不在训练集"的 262 个实验上中位相关 **−0.03**（对照 TAIJI-M 0.11）（F13）；Regulon 2026 直接做了 unseen cells、unseen scaffolds、**二者同时排除**三种 group-held-out，并报告"同时排除时增益下降"（F14）；Tahoe-100M LOCO 2026 用**基础（未处理）转录组**预测"去掉药物均值后的 context-specific 残差"，结论是整体上预测不了（F15/F20）。
**与 Candir 路线的关系**：我们的"表达特征 × 药对交互"是 One-Hot News 里被拿来与 one-hot 对拍的那条"特征分支"的一个实例；该文在 **LCO/LDO 两套切分下都已有"生物特征 vs one-hot"的对照**，SynVerse 与 Baptista 也各自独立做过"表达特征 ≈ 细胞标识符"的对照（F16）。所以这不是一条新路线；若在留出细胞下做 within-pair 排序，最接近的定位是"延续该文的特征分支并换一个更细的评估对象"，而不是"该文未覆盖的 regime"。

### Q3 靶点/通路表达或 CRISPR dependency 作细胞特征预测细胞特异药效/协同的定量结论（增益/失败量级）

**部分覆盖，量级普遍小或为负。**
- 通路激活（DIPx，eLife 2025）：整体 Spearman **0.50（已知组合）/0.26（新组合）**；两药全新子组 ≈ **0**（F13/F18）。
- 通路/regulon（Regulon 2026）：unseen cell lines Macro-F1 **0.4737（pathway+regulon）vs 0.4503（expression alone）**，加 regulon **+0.0153**；同时排除 context+scaffold 时增益消失（F14/F19）。
- 基础转录组（Tahoe-100M LOCO 2026）：去药物均值残差上，最好模型 **+0.004 R²**、主模型 **−0.068**；107 个药的中位重复可靠性 **0.067**，仅 **4** 个药 >0.2（F15/F20）。
- 单药药敏（"Separating drug main effects" 2026，GDSC∪CTRP，leave-cell-line-out，drug-mean 基线）：去组织后仍存活的个人化信号 **held-out Spearman ρ ≈ 0.05**；去掉组织后 held-out skill 掉约 **2/5**，tissue-only 基线在相同目标上**高于**分子模型（F21）。
- 单药药敏（arXiv 2605.20885 2026）：RNA-seq 单独 per-drug r **0.651**，mutation **≤ +0.001**；药物特征对 per-drug r 的增益 **Δ ≤ +0.001**（F22）。
- 蛋白组（SynProtX 2025）：ONEIL 上 protein-only PCC **0.801 vs 0.728**（去掉蛋白），但主评估是随机切分，LCO 是最难设定（F23）。
- CRISPR dependency（FORGE 2026）：与 IC50 联合矩阵分解；test Pearson IC50 **0.31**、dependency **0.68**；joint 与 independent 对输出相关性**相当**，收益主要在 gene-level 一致性（Dabrafenib 0.89 vs 0.13）（F24）。VCAT 2026（abstract）称 CRISPR vulnerability 特征"complement baseline gene expression"（F25）。
- 细胞系特征 vs 药物特征（Baptista 2023）：药物特征更预测协同（R² **+41%**、Spearman **+26%** 相对"细胞系+药物标识符"基线）；表达特征"主要被当作区分细胞系的手段"（F16/F26）。
- 由响应数据训练出的细胞系 embedding（2025）：DrugComb ZIP 任务 PCC 仅 **+0.4%**，且用的是按细胞留权的折（F27）。

### Q4 是否已有工作把"within-pair cell ranking"当独立评估对象？

**在"同一处理内跨细胞排序"这一评价原则上：已被显式发表（单药）／部分发表（组合）。**
- arXiv 2605.20885（2026）：把 per-drug/within-drug 细胞排序命名为独立评价对象（原文 "…which isolates within-drug cell ranking"）；指出 global r 被 between-drug 差异主导；cell-blind（留出细胞）设定下 per-drug r **0.438**（drug-blind 0.645）（F28/F29）。该文明确把 **drug combinations 排除在范围外**（F30）。
- iScience 2025（"moving beyond synergy scores"）：**cell-blind（未见细胞）** 下预测组合敏感性，并报告**per-drug-combination 的 PCC**（26,946 个 drug-drug-cell line 组合，Figure 5C/D）；原文点明这类 per-treatment 相关"frequently not performed"，Zheng/Julkunen 都没给 drug-/combination-specific correlations（F31）；并指出"同一处理下细胞之间的差异"比"药物之间的差异"更难预测、per-drug PCC 仅 **0.1**（F32）。
- Nair 2023（本机二手转述）：跨筛选"哪些细胞系响应"的一致性"modest"——29 个组合中仅 12（Spearman）/15（Pearson）超过 ρ>0.25；组合层面排序一致性 ρ=0.61（F33）。这是对"within-pair 细胞响应排序"本身的**可靠性测量**（不是模型评估）。
- Tahoe-100M LOCO（2026 preprint）：采用"去掉 training-context 药物均值"的残差化端点，并称"to our knowledge no prior work uses the training-context drug mean as a residualized endpoint"（F34；作者声明，非我们的背书）。
**未发现（检索结果）**：没有任何工作把"同一药对内按 `ΔEMAX` 的细胞排序"作为独立评估对象；arXiv `abs:"drug synergy" AND (abs:"ranking" OR abs:"rank")` → **0** 条；Europe PMC "within-pair" 类查询 988 条全为双胞胎/配对研究（F35）。

### Q5 覆盖判定、可能的测量层面差异、处置

**判定：部分覆盖。** "细胞状态特征 + 留出细胞评估 + per-treatment 细胞排序"三项分别已发表；未发现的只是三者在 `ΔEMAX` 协同上的**具体拼装**。
**若已覆盖 → 处置**：被覆盖的三项不能当新颖性主张。**应收窄为复现/评估修正或停线，不换名重启**——即：（a）若线 D 的立项理由是"没人用细胞表达/没人做留出细胞/没人排细胞"，理由不成立，**停线**；（b）若仍要做，只能作为**复现 + 评估修正**（把可靠性/room 门控、per-treatment 排序、drug-mean/pair-mean 基线这些已发表口径搬到 `ΔEMAX`），并预先登记"未发现同对象"只是检索结果。
**可能的测量层面差异（2–4 条，供 Lead 决定是否值得做）**：
1. **端点对象**：within-pair 细胞排序（pair-mean 残差化）作用在 **`ΔEMAX` 协同**上；已发表的 per-treatment 排序是单药 IC50/viability（2605.20885、Tahoe LOCO）和组合敏感性 CMax viability（iScience 2025），尚未见 `ΔEMAX` 版本。
2. **regime 拼装**：**两药都未见 × 细胞留出**同时成立；One-Hot 明确说"truly zero-shot triplet set"在当前数据集里构造不出来（F11），LDO 留细胞、LCO 留药，Regulon 的 joint context+scaffold 最接近但端点不同、且未见 `ΔEMAX`。
3. **可靠性/room 门控的迁移**：Tahoe-100M LOCO 对单药 DE 做了同型可靠性门控（中位 0.067；3/377 药过基线），但**协同 `ΔEMAX` 的 within-pair 可靠性/room 未做**；A0 的 `ρ_ceiling`/MDE 门控与该逻辑同构，可算"评估修正"而非新方法。
4. **（反例）对拍设计不构成差异**：cell-blind 常数基线、one-hot、随机基因块、打乱药↔靶点映射等控制，One-Hot/SynVerse/Baptista 已各自发表同类对拍（F16），不能当差异化卖点。

---

## 2. FACT 清单

> 引文均为逐字（≤40 词；LaTeX/公式符号按源文本原样保留；`…` 表示省略，其余逐字）。路径相对 `D:\MAESTRO`。

### Q1 —— 协同模型的留出细胞评估与指标

**F01｜DeepSynergy 2018 已做 leave-cell-line-out，指标是全局 MSE/RMSE/Pearson。** `full-text`
> "we performed stratified cross validation to determine the generalization ability of methods for novel drugs (see Fig. 3 third column) and novel cell lines (see Fig. 3 fourth column)."
> "the MSEs for the prediction of novel cell lines range between 387 and 461"
- 源：`research/2026-10-27-cellstate-qualification/sources_lit/raw/fulltext/deepsynergy_2018.txt:54,71`；DOI 10.1093/bioinformatics/btx806；PMC5925774。
- 含意：**"留出细胞"在 2018 年就是已发表设定**；我们的 G4/主端点不是新评估维度。其"novel cell lines"结果差（MSE 387–461），与 BRIEF 的"特征类限制"一致。

**F02｜DeepSynergy 的 per-cell-line 相关是"该细胞所有测试三元组"的相关，不是 within-pair 排序。** `full-text`
> "Correlation coefficients of the set of cell lines analyzed range from 0.56 to 0.84."
- 源：同上 `:91`。
- 含意：即便有 per-cell-line 指标，也不是"同一药对内"的细胞排序；不能据此说 within-pair 排序已被该文覆盖。

**F03｜One-Hot News 2026 在 LCO（留出细胞）下用细胞基因表达特征，只报 MSE/PCC/SCC；结果与 one-hot 相当。** `full-text`（R180 的 PDF 抽取全文）
> "LCO Drug & cell feature 161.68±1.50 0.52±0.013 0.45±0.012" / "One-hot-encoding 158.11±1.45 0.53±0.012 0.46±0.012"
> "Leave-Cell-Line-Out (LCO): This strategy sets aside test data based on cell lines."
- 源：`research/2026-10-27-agent-cell-identifiability-r180/raw/onehot.txt:397-403,374`；DOI 10.1093/bioinformatics/btag040（PMC13005728）。
- 含意：表达细胞特征 × 留出细胞的**组合已被测过**，端点是全局相关/误差，不是 within-pair 排序；在该文数据上细胞特征未超 one-hot。

**F04｜One-Hot News 的主结论：模型把表示当标识符，需泛化到未见药物/细胞。** `full-text`
> "our results highlight the need for better strategies to learn from intended features and to generalize to unseen drugs and cell lines."
- 源：`onehot.txt:24-26`。
- 含意：Candir 路线（"表示当标识符"）已覆盖"特征是否被当标识符"这一问题；我们的"表达特征×交互"落入其被检验的"intended features"分支。

**F05｜SynVerse 2025：16 个模型 × 8 种特征（含 CCLE 表达）在四种切分（含 leave cell line）下无模型超过 one-hot 基线。** `full-text`
> "Our analysis revealed that no model outperformed a baseline using one-hot encoding."
> "All models showed poor generalization to unseen drugs and cell lines."
> "four data-splitting methods: (i) leave triplet, (ii) leave drug pair, (iii) leave drug, and (iv) leave cell line"
- 源：`sources_lit/raw/fulltext/synverse_2025.txt:5,68`；DOI 10.1093/bib/bbaf676（PMC12753315）。
- 含意：2025 年已系统评估"细胞表达特征 × leave-cell-line × 与 one-hot 对拍"，结论为负；线 D 若重复该设定而只换端点，属复现/修正。

**F06｜SynVerse 的 leave-cell-line 结果是"基因表达模型本应泛化好，实际很差"。** `full-text`
> "A priori , we expected that models with gene expression-based features may generalize well to unseen cell lines in the test dataset. However, their performance fell short"
> "All models exhibited poor performance"（leave cell line 段）
- 源：`synverse_2025.txt:782`。
- 含意：先前工作已有"表达特征在留出细胞上失效"的直接引文；线 D 的阴性预期应据此写，而不是当新假设。

**F07｜PDTSyn 2026 用 unseen cell line 10 折 CV，指标 MSE/RMSE/PCC，无排序端点。** `full-text`
> "In the unseen cell line setting, none of the cell lines in the validation and test sets appear in the training data, ensuring evaluation on entirely novel cellular environments."
- 数值：PDTSyn 在 O'Neil unseen-cell-line CV 上 MSE **389.34 ± 185.30**（`pdtsyn_2026.txt:2064-2065`）。
- 源：`sources_lit/raw/fulltext/pdtsyn_2026.txt:2057-2058`；DOI 10.1093/bib/bbag199（PMC13109062）。
- 含意：2026 年的"cell line-aware/domain generalization"协同模型仍以全局回归指标评估；没有 within-pair 排序。

**F08｜SynProtX 2025 的 leave-cell-line-out cold start 是"最难设定"，指标是分类/回归全局量。** `full-text`
> "The leave-cell-lines-out validation (Fig. 13 ), simulating predictions in previously unseen biological systems, presented the most difficult setting."（源抽取中 `(Fig. 13 )` 括号前有空格，属抽取排版；引文照录）
- 源：`sources_lit/raw/fulltext/synprotx_2025.txt:761`；DOI 10.1093/gigascience/giaf080（PMC12343095）。
- 含意：蛋白/基因表达细胞特征 × LCO 已发表，且 LCO 下退化明显；同样无 within-pair 排序。

**F09｜BMC Bioinformatics 2026 cold-start benchmark：仅身份/上下文描述子，也能在标准切分拿高 balanced accuracy，但 unseen cell lines 掉到 0.482；大部分性能是"条件记忆"。** `abstract-only`（OA 落地页正文未渲染）
> "balanced accuracy falls to 0.694 for unseen drugs and to 0.482 for unseen cell lines"
> "a per-(cell line, drug) base-rate lookup recovers 0.778 balanced accuracy, within 0.027 of the full model, indicating that most of the standard-split performance reflects conditional memorization"（源抽取中数字带 `\(…\)` LaTeX 标记，引文按渲染文本誊录）
- 源：`sources_lit/raw/fulltext/bmc_coldstart_2026.txt:37-41`（原始落地页 `sources_lit/raw/bmc_coldstart_2026.html`）；DOI 10.1186/s12859-026-06665-z。
- 含意：2026 年已有"冷启动 + 泄漏控制"的协同分类基准，明确要求同时报告 cold-start；这是 C145 所指同型设定的最新一手证据。

**F10｜Baptista 2023 系统评估只做随机切分，并自己指出 leave-cell-lines-out 会显著降低性能。** `full-text`
> "Using a different validation scheme, such as a leave-drug-combinations-out approach ... or even a leave-drugs-out or leave-cell-lines out validation scheme would likely result in lower performance scores."
- 源：`sources_lit/raw/fulltext/baptista_systematic_eval_2023.txt:160`；DOI 10.1371/journal.pcbi.1010200（PMC10072473）。
- 含意：2023 年"系统评估"尚未做细胞留出，但明确把它列为必要下一步；说明我们"该做留出细胞"的观点也已被该文提出。

### Q2 —— 冷启动（两药未见）× 细胞状态特征；与 Candir 路线关系

**F11｜One-Hot News 明确把 LDO（两药都未见）单列，且说模型在 LDO 上失败；细胞特征略好但都差。** `full-text`
> "The model fails to generalize to the case when both drugs in the test data are new, the LDO setup."
> "LDO Drug & cell feature 237.42±3.34 0.13±0.012 0.14±0.010" / "One-hot-encoding 223.57±3.18 0.10±0.009 0.10±0.008"
- 源：`onehot.txt:648-649,406-407`；LDO 定义 `:392-396`。
- 含意："两药未见"regime 已被当作切分研究（虽然只引用为最难），且在 LDO 下细胞特征不救场（PCC 0.13 vs 0.10）。

**F12｜One-Hot News：真正的零样本三元组在当前数据里构造不出来。** `full-text`
> "constructing a truly zero-shot triplet set, where the members of the triplets are never seen in the training, is not possible with the current datasets."
- 源：`onehot.txt:674-676`。
- 含意：我们 A0 若要"两药未见 × 细胞留出"同时成立，只能做**留出细胞 + 留出药对**的近似；该限制已被发表，需要在协议里如实引用。

**F13｜DIPx（通路激活细胞特征）在"两药都不在训练集"的 262 个实验上中位相关为负。** `full-text`
> "For experiments in which both drugs were not in the training set ( n = 262 ), TAIJI-M achieved a median correlation of 0.11, while DIPx performed worse with a median correlation of –0.03."
- 源：`sources_lit/raw/fulltext/dipx_elife_2025.txt:31`；DOI 10.7554/elife.100071（PMC12133153）。
- 含意：靶点/通路的细胞特征在**两药全新**时没有可用的条件排序信号（至少在这个设定下）；与 BRIEF 的"两药都未见"最相关的一手定量结果。

**F14｜Regulon 2026：unseen cells / unseen scaffolds / 两者同时排除三种设定都做过；同时排除时增益消失。** `abstract-only`
> "We evaluated three group-held-out generalization settings: unseen cell lines, unseen drug scaffolds, and simultaneous exclusion of both"
> "the same addition reduced the mean under joint context and scaffold exclusion"
- 源：`sources_lit/raw/abstracts/regulon_context_2026_ppr1330660.txt:8-13`；DOI 10.64898/2026.09.23.753774（PPR1330660）。
- 含意：**"冷启动 + 细胞状态特征"的联合留出设定已被做过**；其结论是联合留出下特征增幅消失。我们的线 D 若只做"药对留出 + 细胞留出"的联合近似，需要说明与该文端点的差别（该文是 ZIP 三分类 Macro-F1）。

**F15｜Tahoe-100M LOCO 2026：把"基础转录组能否预测去药物均值的 context-specific 残差"作为预注册基准；整体不能。** `full-text`（preprint HTML）
> "does the basal (untreated) transcriptome of a completely held-out cell line predict the context-specific component of its drug response — the residual after removing the drug’s mean effect across training contexts?"
- 源：`sources_lit/raw/fulltext/tahoe_loco_basal_2026.txt:30,48`；DOI 10.21203/rs.3.rs-10846736/v1。
- 含意：我们"细胞状态特征 → 留出细胞上的 context-specific 响应"的**问题表述本身已被发表**（单药 log2FC）；线 D 是协同版本，只能算延伸/复现。

**F16｜表达特征在面板内相当于细胞标识符，已被 2023/2025 两次独立系统评估支持。** `full-text`
> "the expression features are mainly being used by the models as a way to distinguish between cell lines, just as the cell line identifiers."
- 源：`baptista_systematic_eval_2023.txt:151`；SynVerse 的 shuffled-feature 结论见 `synverse_2025.txt:5,1452-1454`。
- 含意：我们的"表达特征 × 药对交互"不构成新表示路线；与 Candir 的"标识符"诊断同向。

**F17｜单药留出细胞下，per-drug 细胞排序 r=0.438（drug-blind 0.645）；"未见细胞即便知道药也难排"。** `full-text`（arXiv HTML v1）
> "which isolates within-drug cell ranking, reveals that no drug encoding improves over cell-only features across four independent datasets."（源文本公式 `r` 排版重复为 "r r"，引文从 "which" 起取）
> "Cell-blind CV on held-out cell lines inverts the conventional ranking: familiar cells enable accurate ranking without drug information, but unfamiliar cells cannot be ranked even when the drug is known"
- 源：`sources_lit/raw/fulltext/arxiv_2605.20885.txt:25,37`；表 2 数值 `:470-475`（cell-blind 0.438；drug-blind 0.645）；arXiv:2605.20885。
- 含意：**留出细胞上的"处理内细胞排序"已被作为独立对象测量且给出量级**；线 D 的"期望方向"应从该文出发（很可能低于 0.44），而不是从"空白"出发。

### Q3 —— 细胞状态特征的定量增益/失败量级

**F18｜DIPx 整体 Spearman 0.50（已知组合）/0.26（新组合）。** `full-text`
> "The Spearman’s correlation coefficients between predicted and observed drug synergy were 0.50 (95% CI: 0.47–0.53) in Test Set 1 and 0.26 (95% CI: 0.22–0.30) in Test Set 2"
- 源：`dipx_elife_2025.txt:4`；DOI 10.7554/elife.100071。
- 含意：通路激活细胞特征在协同预测上的量级参照；其 Test Set 2（新组合）0.26 可作为"两药未见"的乐观上界。

**F19｜Regulon 2026 在 unseen cells 上相对 expression alone 的 Macro-F1 增益 0.4503→0.4737，加 regulon +0.0153。** `abstract-only`
> "Pathways plus regulons achieved the highest mean Macro-F1 on unseen cell lines (0.4737, compared with 0.4503 for expression alone)"
> "adding regulons increased mean Macro-F1 by 0.0153 on unseen cell lines"
- 源：`abstracts/regulon_context_2026_ppr1330660.txt:9-12`。
- 含意：细胞状态特征在留出细胞上的增益是 **0.0x 的 Macro-F1 级别**，不是数量级提升；线 D 的最小效应 δ 应据此设定。

**F20｜Tahoe-100M LOCO：基础表达 PCA ridge 的 residual R² = −0.068；最好模型 +0.004；可靠性中位 0.067。** `full-text`
> "the best overall model (metadata ridge) attains a mean reliability-weighted residual R² of only + 0.004, and the primary basal-PC ridge model scores − 0.068"
> "the median reliability is only 0.067 and just 4 drugs exceed 0.2"
- 源：`tahoe_loco_basal_2026.txt:30,111,113`。
- 含意：**"基底表达 → context-specific 残差"整体为负**；A0 的 room/MDE 门槛很可能同样不通过（对协同更可能如此），这是线 D 最需要预注册的失败类别。

**F21｜单药药敏：去组织后仍存的个人化信号 ρ≈0.05；tissue-only 基线高于分子模型。** `abstract-only`
> "Pooling all tissues does expose a small personalization signal that survives removal of tissue-of-origin structure (held-out Spearman ρ ≈ 0.05 against a within-tissue permutation null)"
> "a tissue-only baseline outscores the molecular model on the same target"
- 源：`abstracts/separating_main_effects_2026_ppr1290788.txt:16-19`；DOI 10.21203/rs.3.rs-10579394/v1。
- 含意：细胞层面 personalization 的已发表量级 ~0.05，正好在我们 δ_min=0.05 附近；若协同交互更弱，主端点很可能不可分辨。

**F22｜单药药敏：RNA-seq 单独 per-drug r=0.651，mutation 仅 +0.001；药物编码对 per-drug r 无增益（Δ≤0.001）。** `full-text`
> "RNA-seq alone achieves per-drug r" … "mutations and further modalities each add ≤ + 0.001"（源抽取中公式重复为 "r = 0.651 r=0.651"，此处按报告值 0.651 转述）
- 源：`arxiv_2605.20885.txt:42`；另 "No encoding improved per-drug r beyond Δ = +0.001 of the cell-only baseline" `:47`。
- 含意：细胞状态特征（表达）在单药上很强（0.65），但那是**单药药敏**且非协同；不能直接外推到 `ΔEMAX`。

**F23｜SynProtX：蛋白组细胞特征相对 gene-expression-only 的 PCC 增益 +0.073（ONEIL，0.801 vs 0.728）。** `full-text`
> "in ONEIL, the model with only protein-level data achieved a PCC of 0.801 compared to 0.728 without protein data"
- 源：`synprotx_2025.txt:717`。
- 含意：蛋白层面细胞特征有正增益（约 0.07 PCC），但主评估为随机切分；在 LCO 下退化（F08）。

**F24｜FORGE（CRISPR dependency + IC50 联合分解）：IC50 Pearson 0.31、dependency 0.68；joint 与 independent 对输出相关性相当，收益在 gene-level 一致性。** `full-text`
> "For the test set, Pearson r was 0.68 and 0.31 for the dependency and IC 50 values, respectively"
> "the joint modeling achieved significantly higher concordance than independent models"
- 源：`sources_lit/raw/fulltext/forge_2026.txt:99,181`；DOI 10.1038/s41467-026-73977-2（PMC13396380）。
- 含意：CRISPR dependency 作为细胞特征主要用于机制/一致性解释，未见"dependency 特征 → 协同 within-pair 排序"的定量收益；且是单药 IC50。

**F25｜VCAT：CRISPR-derived vulnerability 特征 complement baseline expression（abstract 级）。** `abstract-only`
> "Ablation analyses showed that CRISPR-derived vulnerability features complement baseline gene expression"
- 源：`abstracts/vcat_2026_doi_10.1093_bib_bbag559.txt:10`；DOI 10.1093/bib/bbag559。
- 含意：dependency/CRISPR 特征有"互补"的摘要级主张，但全文仅摘要可得；不能引用其数字，需求全文后再用。

**F26｜Baptista：药物特征比细胞特征更预测协同；表达特征与细胞标识符相当。** `full-text`
> "Drug features appeared to be more predictive of drug response, with a 41% increase in coefficient of determination (R 2 ) and 26% increase in Spearman correlation relative to a baseline model that used only cell line and drug identifiers."
- 源：`baptista_systematic_eval_2023.txt:27`（结论见 `:113,151`）。
- 含意：把"细胞表达特征"当主卖点与已发表结论相反；协同预测的主要信息在药物侧（在该数据/模型上）。

**F27｜响应数据训练的细胞系 embedding 只给 ZIP 协同预测 +0.4% PCC（留细胞折权重）。** `full-text`
> "the ZIP score prediction task in DrugComb showed a 0.4% increase"
> "evaluated model outputs using fold-specific weights that excluded each target cell line during training"
- 源：`sources_lit/raw/fulltext/cellline_embedding_2025.txt:78,90`；DOI 10.1016/j.csbj.2025.06.018（PMC12205321）。
- 含意：细胞表示（哪怕用了响应数据）对协同指标的增益是 0.4% 量级；线 D 应据此设 MDE，并注意该特征是响应派生（有泄漏风险，不能当"细胞注释"）。

### Q4 —— within-pair cell ranking 作为独立评估对象

**F28｜arXiv 2605.20885 明确把 "within-drug cell ranking" 命名为独立评价对象，指出 global r 被 between-drug 差异主导。** `full-text`
> "which isolates within-drug cell ranking, reveals that no drug encoding improves over cell-only features across four independent datasets."（源文本公式 `r` 排版重复为 "r r"，引文从 "which" 起取）
- 源：`arxiv_2605.20885.txt:25`；另 `:28` "between-drug potency ranking and within-drug cell ranking"（同段：global r 把两个信号混在一起）。
- 含意：**"处理内细胞排序"作为评价对象已发表**；我们的 within-pair 版本是同一评价原则的协同版，不能声称"首次把处理内排序当评估对象"。

**F29｜该文用 cell-blind（留出细胞）per-drug r=0.438 给出量级。** `full-text`
> 表 2 数值誊录（非连续引文）：cell-blind 行 "≈ 0.22 / 0.438"；drug-blind 行 "≈ 0.34 / 0.645"（global r / per-drug r）
- 源：`arxiv_2605.20885.txt:462-475`。
- 含意：留出细胞的细胞排序在单药 IC50 上可到 0.44；协同 `ΔEMAX` 的 a priori 预期必须显著低于此，否则应怀疑泄漏/基线问题。

**F30｜该文明确把 drug combinations 排除在范围外。** `full-text`
> "all results rest on cell-line IC 50 values, which abstract away in vivo pharmacokinetics, tumor microenvironment effects, clonal heterogeneity, and drug combinations"
- 源：`arxiv_2605.20885.txt:79`。
- 含意：**协同版未被该文覆盖**（这是"未发现"的边界，不是空白证明）；线 D 的精确对象只能据此写"该文未覆盖协同"。

**F31｜iScience 2025 在 cell-blind 下报告 per-combination 的 PCC，并指出此类 per-treatment 相关"frequently not performed"。** `full-text`
> "For the combination CMax viability (26,946 drug-drug-cell line combinations), we obtained similar results that are depicted in Figures 5 C and 5D."
> "neither Zheng et al. ... nor Julkunen et al. ... provide drug-/combination-specific correlations"
- 源：`sources_lit/raw/fulltext/beyond_synergy_scores_2025.txt:93-94`；DOI 10.1016/j.isci.2025.112622（PMC12152377）。
- 含意：**组合层面"同一组合跨细胞"的相关已在 cell-blind 下报告**（虽然单位是 combination CMax viability 而非 ΔEMAX），并且作者把"不报告 per-treatment 相关"当作领域缺陷；这直接削弱"within-pair 排序没人做"的立项理由。

**F32｜同一处理下细胞之间的差异比药物间差异更难预测；per-drug PCC 仅 0.1。** `full-text`
> "the derived measures only indicate a general trend in sensitivity but cannot be used to compare the effect of a drug monotherapy on different cell lines"
> "the drug-specific PCC is only 0.1"
- 源：`beyond_synergy_scores_2025.txt:85,93,99`。
- 含意：**"排细胞"的难度已有定量警告**；A0 的 room<MDE 风险应按此先验提高。

**F33｜跨筛选"哪些细胞系响应"的一致性本身是 modest 的（Nair 2023，本机二手转述）。** `local-secondary`
> "For *which cell lines* respond, agreement is "modest": 12 (Spearman) and 15 (Pearson) of 29 combinations above ρ > 0.25."
> "Spearman's ρ = 0.61, P = 0.00069."（组合层面排序一致性；`lit/report.md` 原文引号）
- 源：`lit/report.md:35`（原始：Nair et al., Nat Commun 2023, DOI 10.1038/s41467-023-39528-9；本轮未重读原文）。
- 含意：within-pair 细胞响应排序的**测量可靠性**已被测过且不高；A0 的 `ρ_ceiling`/跨筛核对正是同一思路，应引用而不是当新发现。

**F34｜Tahoe-100M LOCO 声称"此前无人用 training-context drug mean 作残差化端点"。** `full-text`（作者声明）
> "to our knowledge no prior work uses the training-context drug mean as a residualized endpoint"
- 源：`tahoe_loco_basal_2026.txt:48`。
- 含意：该声明限定在单药/DE；协同 pair-mean 残差化端点是否有人做过，我们**未发现**（见 F35），但这是作者级声明，不能替代系统检索。

**F35｜零命中记录（只作检索结果）。** `search-result`
- Europe PMC `"within-pair" OR "within pair" OR "per-drug-pair" ...` → 988 条，经标题核对均为双胞胎/配对研究，**无**协同/药对细胞排序工作（`epmc_P1-e7_within_pair_terms.json`）。
- arXiv `abs:"drug synergy" AND (abs:"ranking" OR abs:"rank")` → **0** entries（`pass2_arxiv_P2-a1_synergy_ranking.xml`）。
- Europe PMC/OpenAlex 查询组合（见 pass_log）**未返回**以"within-pair cell ranking on ΔEMAX"为端点的工作。
- 含意：**未发现**（不是"不存在"）。要升级为"空白"，必须扩库（Google Scholar/Scopus/文献追引）并读 One-Hot 补充表与冷启动基准正文。

---

## 3. 最接近的 3 个先例（及其设定）

| # | 先例 | 设定（数据 / 切分 / 特征 / 端点） | 与线 D 的关系 |
|---|---|---|---|
| 1 | **SynVerse，Brief Bioinform 2025（bbaf676）** | DrugComb `S_mean`；四种切分含 leave cell line；16 模型 × 8 特征（含 CCLE 表达、LINCS、靶点）；端点 RMSE/PCC；结论：无一超过 one-hot 基线、LCO 下全部很差 | 覆盖"细胞表达特征 × 留出细胞 × 协同"整条设定；线 D 若只换端点，是复现/修正 |
| 2 | **One-Hot News，Bioinformatics 2026（btag040）** | DrugComb/NCI-ALMANAC，MatchMaker；LPO/LCO/LODO/LDO；细胞基因表达特征 vs one-hot；端点 MSE/PCC/SCC；LCO 下特征≈OHE，LDO 下都很差 | 覆盖"表达特征 vs 标识符"与"留出细胞/两药未见"两个设定；其 LCO/LDO 表是线 D 最近的直接对拍 |
| 3 | **arXiv 2605.20885（2026-05）** | GDSC2 等四数据集，drug-blind/cell-blind；RNA-seq 细胞特征；端点 **per-drug Pearson r（"isolates within-drug cell ranking"）**；global r 被 between-drug 主导；cell-blind per-drug r=0.438；明确排除 combinations | 覆盖"处理内细胞排序作为独立评估对象"这一**评价原则**；线 D 是其协同版延伸 |

**次级近邻（同样重要）**：Tahoe-100M LOCO 2026（残差化端点 + 可靠性门控，单药）＝线 D 的"方法学骨架"；iScience 2025（cell-blind 组合敏感性 + per-combination PCC + 治疗排序）＝线 D 的"组合版评价近邻"；Regulon 2026（pathway/regulon × unseen cells × joint exclusion）＝线 D 的"特征与联合留出近邻"；BMC Bioinformatics 2026 cold-start benchmark＝"冷启动 + 泄漏控制"近邻。

---

## 4. 剩余差异（2–4 条）

1. **端点对象**：没有检索到把 **`ΔEMAX` 的 within-pair 细胞排序**（pair-mean 残差化）作为主/副端点的已发表工作；已发表的是单药 per-drug 排序（2605.20885、Tahoe LOCO）与组合敏感性 per-combination 相关（iScience 2025）。
2. **regime 拼装**：没有检索到 **两药都未见 × 细胞留出 × within-pair 排序**同时成立的工作；One-Hot 说真 zero-shot triplet 当前数据构造不出（F12），LDO 留细胞/ LCO 留药，Regulon 的 joint exclusion 最接近但端点是 ZIP 三分类。
3. **可靠性/room 门控迁移到 `ΔEMAX`**：单药 DE 已有人做同型门控（Tahoe LOCO），协同 `ΔEMAX` 未见；这是可测的"评估修正"差异，但也意味着很可能 room<MDE（F20/F21/F32）。
4. **反例（不构成差异）**：cell-blind 常数基线、one-hot、随机基因块、打乱药物↔靶点映射这几类对拍已分别在 One-Hot/SynVerse/Baptista 发表（F16），不能再当"首次对拍"。

---

## 5. 检索缺口

- **预算限制**：2 个 pass、Europe PMC/OpenAlex/arXiv 三个 API；未查 Google Scholar/Scopus/Web of Science、未做引文回溯/前向追引（仅凭 One-Hot 的 Li et al. 2024 在 C148 已被核过）。
- **全文缺口**：Regulon 2026 与 Separating 2026 的全文（Publisher 429/EPMC 500）；BMC cold-start 正文未渲染（仅摘要+元数据）；VCAT 2026 仅摘要；MoCo、OrderCombo、SynCell、MDCDR 等 2025–26 模型仅摘要/题目级。
- **补充材料缺口**：One-Hot News 的 Table S7–S12（含 average baseline 全表、LCO/LDO 的逐模型数、合成实验）未读；可能含 per-cell-line 或排序类结果。
- **术语撞车**："within-pair" 在 PubMed 主要指数双胞胎研究（F35）；我们只能用 per-drug/per-combination/residual ranking 等代理词，可能漏掉用别的措辞的同对象工作。
- **PRISM 侧**：Q1 问"DrugComb/Prism 相关模型"；本轮命中的是 DrugComb/NCI-ALMANAC 模型，PRISM 相关主要是单药药敏/ordering（未做协同 within-pair 排序搜索的独立查询），**这是检索缺口而非"无工作"**。
- **未覆盖语言/库**：中文数据库、专利、会议（NeurIPS/ICML/ISMB 的 workshop）未检索。

---

## 6. 处置（写给 Lead）

1. **不得声称新颖性**。本报告的结论是"部分覆盖"，覆盖的是线 D 的三个构成要素；"未发现"仅是检索结果，**不能写成"不存在"或"空白"**。
2. **被覆盖的三项（特征类、留出细胞评估、per-treatment 排序原则）按"已覆盖"处理**：若线 D 的立项理由是其中任一项，**应收窄为复现/评估修正或停线，不换名重启**。
3. 若 Lead 决定继续，建议把线 D 明确定义为**复现 + 评估修正**：
   - 主端点保留 within-pair `ΔEMAX` 排序，但必须在协议里写明其近邻（2605.20885 的 per-drug r、Tahoe LOCO 的 residual R²、iScience 的 per-combination PCC），并预注册 A0 的 `ρ_ceiling`/MDE/room 门控（对齐 Tahoe LOCO 的 M2 validity gate）；
   - 对照基线用**已发表的 pair-mean/drug-mean 常数基线**（per-unit ranking r=0 by construction），不要写成"我们新定义"；
   - 明确"两药未见 × 细胞留出"只能做近似，引用 One-Hot 的 zero-shot 不可构造声明；
   - 结果无论正负都只能表述为"在该设定下复现/未复现某已发表现象"，不得升级为机制/临床结论。
4. **若线 D 的唯一目的是产生"新方法/新机制/空白填补"**：建议**停线**，不换名重启（BRIEF §4 的停止条件）。

---

## 7. 产物与证据状态索引

| 类别 | 文件 | 证据状态 |
|---|---|---|
| 本地一手全文（前轮 PDF 抽取） | `research/2026-10-27-agent-cell-identifiability-r180/raw/onehot.txt` | full-text（抽取；图表未逐页核） |
| 本机二手整理 | `lit/report.md` | local-secondary（F33；原文未重读） |
| 本轮抓取全文（EPMC JATS） | `sources_lit/raw/fulltext/*.txt`（deepsynergy_2018, baptista_2023, synverse_2025, pdtsyn_2026, synprotx_2025, dipx_elife_2025, beyond_synergy_scores_2025, forge_2026, cellline_embedding_2025） | full-text |
| 本轮抓取全文（HTML/preprint） | `sources_lit/raw/fulltext/arxiv_2605.20885.txt`（arXiv v1 HTML）、`tahoe_loco_basal_2026.txt`（Research Square HTML） | full-text |
| 本轮抓取的 OA 落地页（正文未渲染） | `sources_lit/raw/bmc_coldstart_2026.txt` | **abstract-only**（BMC early-access 分享页只渲染摘要+元数据） |
| 摘要抽取 | `sources_lit/raw/abstracts/*.txt` | abstract-only |
| 查询原始响应 | `sources_lit/raw/epmc_*.json`, `pass2_epmc_*.json`, `openalex_*.json`, `pass2_openalex_*.json`, `arxiv_*.xml`, `pass2_arxiv_*.xml` | raw |
| 查询脚本 | `sources_lit/pass1_queries.py`, `pass1_retry.py`, `pass1_retry2.py`, `pass1_fetch_fulltext.py`, `pass2_queries.py`, `pass2_doc_retrieval.py`, `pass2_doc_retrieval2.py`, `build_abstract_extracts.py`, `verify_quotes.py`（56 条引文逐字审计，FAILS 0） | raw |
| 检索日志 | `sources_lit/pass_log.md` | — |

**未改动**：`PROTOCOL_A0.md`、`research/INDEX.md`、`SYNTHESIS.md`、其它研究目录、`git`、`src/`、`tools/`。本报告不含任何本机数据的效应估计。
