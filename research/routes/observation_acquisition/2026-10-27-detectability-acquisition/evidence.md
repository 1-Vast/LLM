# R189 线 B — 定向核验证据清单（evidence.md）

- 日期：2026-10-27（核验员：lit-verifier / task-2）
- 范围：I003「可分辨性约束的决策聚焦证据选择」最近先例覆盖核验 + ComboCat 原文 A2 事实提取。
- 检索预算：PASS 1（承接，完成）+ PASS 2（1 个新 pass，见 §4）。本地已存一手全文的阅读不计 pass。
- 证据状态定义：`reported` = 论文/文件原文自述；`observed` = 本次在原始文件/数据中直接检出的结构或计数；`summarized` = 仅依据题录/摘要或二手摘录，未读全文；`derived` = 由已核验事实推出的算术结论。
- 纪律：本文件不声称新颖性；不写 challenge_I003.md；不修改候选/PROTOCOL/INDEX/git。零命中只作为检索结果记录，不写成"不存在"。

## 0. 结论摘要（供 Lead 直接引用）

1. **先例覆盖判定：部分覆盖（partial coverage）**。decision-focused acquisition/BOED 已被 2026 年已发表工作直接实现（GoBOED，arXiv 2605.26093；决策聚焦序贯设计，arXiv 2602.05340）——I003 的核心动机"按决策价值买证据"**不再是差异**（F01–F06）。"acquisition 分数 × 门控函数"的乘积结构亦有先例（R-IDeA = R-I × DeA，DeA 为 sigmoid 门，但门控变量是**模型错设残差**而非测量噪声/MDE，F07）；"噪声/识别 SNR 决定采集是否值得"已在 regime 评估层被解析化（F09–F10）；"决策价值 vs 样本量/成本"在临床试验 EVSI/ENBS 文献中是成熟框架（F11）。
2. **I003 剩余差异（4 条，其中 R4 仅剩离散化实现差异）**（详见 §2，均属构成/应用层，未见机制级新意）：(R1) 以**每个动作实际重复数 r 与板内 σ** 计算 MDE 并作为 acquisition **准入闸**——未发现已发表先例（零命中见 §4），但门控乘积结构已有先例，剩余差异仅在"闸变量"；(R2) 测量按**组合行/板计费**、在同一物理批次内选择离散行——生物 AL 实践已有 batch capacity 预算约束，未见"行成本×可分辨性"联合 acquisition；(R3) **两药未见 regime 先验进入 acquisition**——未见先例，但 ComboCat 无法检验（F28–F30），本轮不可验证；(R4) "只在决策边界上买"的显式拒绝规则——GoBOED 的 decision-irrelevant 方向不敏感性提供了理论近邻（F16），剩余是 top-k 边界带离散化，属评估修正。
3. **对应 BRIEF 停止条件：应收窄为评估修正或停线，不换名重启。**（剩余差异 4 条：R1 闸变量、R2 行级成本、R3 先验注入、R4 边界带；R4 已被 F17 的理论近邻大幅覆盖。） 剩余差异不足以支撑"新算法"主张；若继续，只能作为对已有 decision-focused/regime 评估的**修正性评估**（把 MDE 门作为评估修正项），不得声称新颖性或收益。
4. **ComboCat 供 A2 用**：dense 模式 806 组合、每组合 3 个**同板技术重复**、每组合 1 块板（⇒ cell×pair 单元共 806，无跨细胞系成对重复）；端点 `perc_cell_death`（归一化 %细胞死亡，默认计算用）与派生 `bliss_synergy`；`raw_val` 为归一化前原始值；sparse 模式只实测对角 10 个剂量对，其余 90 个为**模型补全值（非实测）**，仅 40 个组合做过 dense 复筛验证。**A2 硬阻断**：发布 workbooks 中 804/806 个 root_id 为 32 位哈希、`drug1_name/drug2_name` 仅为占位符 "drug1"/"drug2"，`drugs_summary`/`cell_lines_summary` 为数字键摘要且与 root_id 无 join key → 药物身份/注释无法在发布文件内连接；且 806 cell×pair 总数使 A2 "两药未见 cell×pair ≥ 800 + ≥12 注释水平"门槛不可达。**按 BRIEF：A2 不运行，只记录资格结论（有效负结果）。**
5. 与平行挑战者的分歧/限定：同意 (a) decision-focused 已覆盖、(c) 强先验压平 acquisition 差异/贪心常胜、(b) 乘积门控结构先例——**但对 (b) 加限定**：2506.07805 的 sigmoid 门变量是 `|f̂−g|`（模型错设残差）而非测量噪声/MDE，故"乘积结构先例"成立而"可分辨性门控先例"不成立。(d) "与 R5 已停 I003 主张 B 同对象"**本任务未核验**（R5 文档不在本任务源集），记为未核验，请 Lead 与挑战者对齐。

---

## 1. 先例覆盖（decision-focused / 鲁棒 BOED / regime）

**F01｜decision-focused BOED 已实现（核心动机被覆盖）**
- 引文（≤40 词）："GoBOED combines an amortized variational posterior surrogate with a differentiable convex decision layer, enabling gradient-based design optimization that is fully decision-focused."
- 源：`sources/extracts/arxiv-2605.26093_sentences.txt` L26（arXiv:2605.26093v1，2026-05-25，GoBOED）。
- 状态：reported。
- 含意：I003 §1/§3 的"按下游决策价值选择证据"在 2026 已有完整框架；不能再作为差异点。

**F02｜decision-focused 目标是期望鲁棒决策损失最小**
- 引文："It prioritizes experiments that reduce the eventual robust decision loss the most while accounting for downstream feasibility."
- 源：同上 L68。
- 状态：reported。
- 含意：I003 的"决策价值 × ..."里"决策价值"分量与 GoBOED 同对象；I003 只能在其上追加约束。

**F03｜GoBOED 的风险约束作用于参数后验，不是测量可分辨性**
- 引文："which require critical conditions to hold with a specified posterior probability"
- 源：同上 L97（§3.3.2 chance constraints）。
- 状态：reported。
- 含意："把噪声/风险写进决策层"已有先例，但 chance constraint 约束的是参数后验不确定性；I003 的约束变量（该测量在现有重复下能否分辨，MDE）仍不同——这是**约束变量**差异，不是约束机制差异。

**F04｜GoBOED 非序贯；逐批序贯是作者列出的未来方向**
- 引文："Extending GoBOED to fully sequential adaptive designs"
- 源：同上 L244。
- 状态：reported。
- 含意：逐批 sequential acquisition 的操作空白存在，但属工程扩展而非概念空白；I003 不能把"逐批买行"当作机制差异。

**F05｜决策聚焦序贯设计＋提前停止已被覆盖**
- 引文："we demonstrate that our directional uncertainty–based design attains an earlier stopping time than decision-blind designs"
- 源：`sources/extracts/arxiv-2602.05340_sentences.txt` L13（arXiv:2602.05340v1，2026-02-05）。
- 状态：reported。
- 含意：I003 的"序贯 + 决策聚焦 + 停止"三件套已被覆盖。

**F06｜其停止由决策损失容差决定，而非 MDE**
- 引文："In practice, the stopping time for the experimental design is determined by a tolerance for the decision loss"
- 源：同上 L268。
- 状态：reported。
- 含意："何时停止买"已有决策损失判据；I003 的"可分辨性判据"若成立，只是替换容差口径，须以评估修正方式提出（且注意 F06 与 F09 的噪声条件已部分存在）。

**F07｜"acquisition × sigmoid 门控"乘积结构已有先例（门控变量不同）**
- 断言：R-IDeA 的 acquisition 为 `R-I(ξt)·DeA(ξt)`，其中 `DeA(ξt)=Sigmoid((|f̂(ξt)−g(ξt)|−τ)/κ)`（模型错设残差的 sigmoid 门）。
- 引文："This robust acquisition function penalizes designs that are only representative or only informative"
- 源：`sources/extracts/arxiv-2506.07805_sentences.txt` L172；公式锚点同上 L193（原文含 LaTeX/零宽字符，逐字核对以行锚为准："The novel acquisition function is given by R-IDeA"）。
- 状态：reported。
- 含意：与挑战者一致——**乘积门控结构**已有先例；I003 若只是"决策价值分数 × 可分辨性 sigmoid 门"，结构不新。但门控变量在本例中是模型错设残差（|f̂−g| vs τ），不是测量噪声/重复数；"可分辨性门控"本身仍未见先例（见 F13）。两点须分开写，不可过度归并。

**F08｜regime 评估：先验质量×预算比决定 exploration 是否值得**
- 引文："Higher PRS = larger budget ratio and/or weaker prior = exploration more likely to pay."
- 源：`sources/extracts/arxiv-2605.04895_sentences.txt` L109（arXiv:2605.04895v2，2026-10-15，"Regime-Conditioned Evaluation in Multi-Context Bayesian Optimization"）。
- 状态：reported。
- 含意：与挑战者 (c) 一致——强先验时 acquisition 差异会被压平、exploitation 更优；I003 声称的 acquisition 优势在强先验下应消失，且该机制已被形式化。

**F09｜识别 SNR（gap²/σ²）已进入解析条件**
- 引文："i.e., the identification SNR is low"
- 源：同上 L619；同文 L748："noisier benchmarks require larger budgets before exploration pays off"（已逐字核对）。
- 状态：reported。
- 含意：I003 的"噪声/可分辨性决定采集是否值得"在 regime 评估层已有最近概念先例（噪声越大、越晚才值得 exploration）；I003 只剩"把它下沉为每测量 MDE 门"这一粒度差异。

**F10｜GDSC2 上贪心基线常胜（I003 H4 的领域风险）**
- 引文："At default budget ( B = 50 B=50 ), Greedy is strongest overall: Hit@1 0.389 0.389 , discovery AUC 0.338 0.338 ."
- 源：同上 L191（原文数字因 HTML 转换重复出现，行锚为准）。
- 状态：reported。
- 含意：与挑战者 (c) 一致；I003 的 H4（若 greedy 已最佳则停线）在 GDSC2 类基准上风险很高。

**F11｜"决策价值 vs 样本量/成本"是成熟临床设计框架（EVSI/ENBS）**
- 引文（题录，逐字）："Expected value of sample information to guide the design of group sequential clinical trials"
- 源：`sources/queries/pass2_epmc_P2-q1_EVSI_sample_size.json`（PASS 2 查询命中 477 条；该题录为 2021 年论文标题；同批含 "Determining optimal sample sizes for multi-stage randomized clinical trials using value of information methods"）。
- 状态：summarized（仅题录，未读全文）。
- 含意：I003 的"决策价值×测量成本"原则在临床试验设计中有数十年成熟文献；I003 的差异只能是具体测量结构（板内重复/MDE）与筛选域，而不是"决策价值与成本的权衡"这一原则本身。

**F12｜"决策相关≠学习必需"已有 2026 研究（决策相关性分量被覆盖）**
- 引文："Decision-focused learning encourages a model to retain what downstream decisions require, yet a learner may be trained on substantially more information than the deployed decision rule needs."
- 源：`sources/queries/epmc_decision_irrelevant.json` L31（PPR1307182，DOI 10.20944/preprints202608.1994.v1，2026-08-27，仅摘要级）。
- 状态：reported（仅摘要，未读全文）。
- 含意：I003 的"决策相关性"分量已被专门研究（虽方向是监督信息而非 acquisition）；I003 不能把"决策相关"当新概念。

**F13｜BATCHIE 先例描述更正（候选 v1 的 "SNR 惩罚的 DBAL" 未获正文支持）**
- 断言：BATCHIE 的 acquisition 是 PDBAL（最小化后验样本间期望距离），正文未检出"SNR 惩罚"项；"undetectable"仅出现在 phase-I 孔失败数据质量语境。
- 引文："The key idea behind PDBAL is to select experiments which will minimize the expected distance between any two posterior samples after observing the outcomes of the selected experiments."
- 源：`sources/extracts/batchie_fulltext.txt`（`batchie_sentences.txt` L98；另 L544 "we identified that BATCHIE was sensitive to undetectable random well failures producing corrupted data"）。
- 状态：observed（全文 grep；**补充材料 PDBAL theory 未下载，未核验**）。
- 含意：候选 v1 §4 的"BATCHIE SNR 惩罚 DBAL"表述应改为"PDBAL 概率型批量主动学习（以噪声模型处理噪声，正文无显式 SNR 惩罚）"；否则先例差异基线被错误设置。

---

## 2. 最近邻差异（I003 剩余差异逐条判定）

**F14｜R1：以每动作实际重复数计算的 MDE 作为 acquisition 准入闸 — 未发现已发表先例**
- 断言：在 PASS 1/2 检索与本地 7 份一手全文中，未检出"逐测量 MDE（由该动作重复数 r 与 σ 计算）作为 acquisition 准入闸"的已发表工作。
- 引文（零命中记录，逐字）：`"hitCount": 0`
- 源：`sources/queries/pass2_epmc_P2-q3_power_acquisition_recent.json`（查询式见 `pass2_summary.json`：power analysis/MDE/power-aware × acquisition/BOED/batch AL，2023–2026）；另 OpenAlex 标题摘要过滤两条 0 命中见 §4。
- 状态：observed（检索结果；**不作为"不存在"证据**）。
- 含意：这是 I003 唯一未被直接覆盖的"物件"；但 F07 表明其乘积门控结构已有先例，因此差异仅在"闸变量=MDE"这一层，属评估修正材料，不足以支撑新算法主张。

**F15｜R2：同一物理批次内按组合行/板计费选择离散测量 — 生物 AL 已有容量预算约束，未见"行成本×可分辨性"联合**
- 引文："For the experimental tests, the critical parameter is the batch size (the number of experimental tests per cycle), which is limited by the laboratory equipment capacity."
- 源：`sources/extracts/AL_guide_2025_sentences.txt` L234（Sci Rep 2025，DOI 10.1038/s41598-025-85600-3）。
- 状态：reported。
- 含意："物理批次/平台容量"在生物 AL 实践中已被明确当作约束（同文 L469/L472：每组合 4–5 个重复）；I003 的差异是"把行成本放进 acquisition 分数"，属应用层构成，不是新机制。

**F16｜R3：两药未见 regime 先验进入 acquisition — 未见先例；但本轮不可验证**
- 断言：2605.04895 把先验质量（ρ）作为 regime 轴，但用于**评估** acquisition 差异，不是把"两药未见"先验注入 acquisition；未检出把 leave-drug-out 先验写入 acquisition 的已发表工作。
- 引文："The same GDSC2 benchmark yields opposite conclusions depending only on budget"
- 源：`sources/extracts/arxiv-2605.04895_sentences.txt` L52。
- 状态：observed（检索/全文）；先例侧为 reported。
- 含意：差异存在但不可在 ComboCat 上检验（F29–F30：identity 不可连接、cell×pair 仅 806），且档案内证据（R163"通路注释替代身份"）不是 acquisition 问题；本轮**不应**把它写成候选收益来源。

**F17｜R4：显式"仅在决策边界上买"的拒绝规则 — 决策无关方向过滤已有理论近邻**
- 引文："We theoretically show that GoBOED gradients are insensitive to parameter directions irrelevant to the decision objective"
- 源：`sources/extracts/arxiv-2605.26093_sentences.txt` L27。
- 状态：reported。
- 含意："决策无关就不值得买"已有理论保证（梯度对决策无关子空间不敏感）；I003 剩余的只是"排序 top-k 边界带 + MDE"的离散化实现，属评估修正，不构成机制新意。

**F18｜F13 相关更正：BATCHIE 的批量选择是板级序列子模选择（不是"逐行 MDE"）**
- 引文："To select a batch of plates, we select sequentially."
- 源：`sources/extracts/batchie_fulltext.txt`（`batchie_sentences.txt` L471）。
- 状态：reported。
- 含意：最接近的"批量 acquisition"先例以板为单位、信息准则为目标；I003 若要做行级成本，须说明与板级子模批量选择的差异（属构成差异）。

---

## 3. ComboCat 事实（供 A2 冻结用）

**F19｜dense 模式定义：10×10 全剂量对、三重复**
- 引文："measures all pairwise dose combinations in a dense 10 × 10 matrix format, tested in triplicate to ensure high fidelity and data quality"
- 源：`sources/combocat_fulltext.txt`（`combocat_sentences.txt` L46；原文此句主语为 "The “dense mode”"）。
- 状态：reported。
- 含意：A2 的真值来源只能是 dense 模式全矩阵；剂量对为测量单位（每组合 100 个剂量对）。

**F20｜规模：806 组合、>290,000 测量**
- 引文："reference dataset of 806 drug combinations comprising over 290,000 individual measurements"
- 源：`sources/combocat_fulltext.txt`（`combocat_sentences.txt` L65；另 L47 同义表述已核对）。
- 状态：reported。
- 含意：A2 的可分析单元上限由此决定（见 F26–F27）。

**F21｜重复结构：每药对 3 个 10×10 组合矩阵重复 + 单药 3 重复 + 对照 12 重复**
- 引文："Three replicate 10 × 10 combination matrices are generated for each drug pair, along with three replicates of each single-agent dose-response."
- 源：`sources/combocat_fulltext.txt`（`combocat_sentences.txt` L29；对照句 L29/L226 已核对："Twelve replicates each of cell death (orange) and vehicle (yellow) controls are included for normalization"）。
- 状态：reported。
- 含意：σ_technical 可在板内估计；不存在独立培养重复。

**F22｜每块 dense 板只测一个组合 ⇒ 板=组合×细胞系单元**
- 引文："Each dense mode plate tested exactly one drug combination, making the total plate count for a dense mode experiment scale linearly with the number of drug pairs"
- 源：`sources/combocat_fulltext.txt`（`combocat_sentences.txt` L231）。
- 状态：reported。
- 含意：配合 F20/F23 ⇒ 806 块板=806 个(组合,细胞系)单元 ⇒ **没有药对在 >1 个细胞系上被重复测量**（derived，见 F27）。

**F23｜806 块板、平均 Z′=0.747**
- 引文："Distribution of Z’ values across all 806 combination plates"
- 源：`sources/extracts/combocat_supp_MOESM1_docx.txt` L1（Supplementary Fig. 1 图注；同句 "The mean Z’ across all plates is 0.747"）。
- 状态：reported。
- 含意：板数=806 与 F20/F22 三方一致；QC 基线（Z′）可直接引用。

**F24｜重复是"同板技术重复"（数据字典原话，且数据中每 root_id 恰为 3 重复）**
- 引文："Replicate per root_id (out of 3), all reps are in the same plate"
- 源：`sources/extracts/combocat_dense_supp_workbook_audit.txt` L4（= Supplementary Data 1 workbook sheet `Supp_Table_All_Dense_Mode_Summa` 第 3 行）；observed：806/806 个 root_id 的 `replicate` 取值集合均为 {1,2,3}（同文件 §data）。
- 状态：reported + observed。
- 含意：A2 的 r=3 是**板内技术重复**；MDE 只能按技术 σ 计算，不得写成独立生物学重复；跨板重复不可得（除少数有条码的板，见 F28 注）。

**F25｜端点定义（数据字典逐字）：raw_val / perc_cell_death / single_effect / bliss_synergy / mean_syn**
- 引文："Normalized value as a function of %Cell death, averaged across replicates. This is used for all calculations unless specified otherwise."
- 源：`sources/extracts/combocat_dense_supp_workbook_audit.txt` L8（字典行 `perc_cell_death`）；配套逐字：L3 "Raw value prior to any normalization"；L9–L10 "single_effect_drug1/drug2 = %Cell Death caused by drug1 alone"（原文 `single_effect_drug2` 定义有笔误，逐字如此）；L12 "Excess % Cell Death over Bliss expecation"；L25 "The mean synergy of 100 values per combination matrix"；L23 "flagged_final … if any or none of the QC parameters were violated"。
- 状态：reported。
- 含意：A2 端点二选一并冻结：`perc_cell_death`（归一化 %细胞死亡，默认计算口径）或 `bliss_synergy`（派生协同）；聚合单位必须写死（按 100 剂量对 mean，或 `mean_syn_adj`=仅非 flagged 值），并预先规定 `flagged_final==0` 过滤。端点仍是 viability 派生指标，**不构成独立功能终点**（与 BRIEF 一致）。

**F26｜sparse 模式：只实测对角 10 个剂量对，其余 90 个为模型补全（非实测）**
- 引文："Sparse mode reduces the number of direct experimental measurements by testing only the diagonal (10 dose pairs) of the 10 × 10 matrix and single-agent responses, then uses predictive modeling to obtain the remaining 90 values."
- 源：`sources/combocat_fulltext.txt`（`combocat_sentences.txt` L50；L109 "predicting the non-measured response values within a sparse matrix" 已核对）。
- 状态：reported。
- 含意：A2 只能用 dense 模式实测值；任何 sparse/补全值不得当实测标签；补全值若要验证只能靠 dense 复筛。

**F27｜补全值验证仅 40 个组合（dense 复筛）**
- 引文："To validate these sparse mode predictions, we re-screened a subset of 40 combinations in dense mode"
- 源：`sources/combocat_fulltext.txt`（`combocat_sentences.txt` L161）。
- 状态：reported。
- 含意：sparse 模式 9045 组合（CHP-134）绝大多数无实测验证 → 不可作为 A2 的"第二资源"观测标签；A2 应明写"仅 dense 模式"。

**F28｜注释来源与等级：36 细胞系（14 lineage 水平，1 行不一致）、136 药物（5 class 水平）；MOESM8 另有 ChEMBL/Action_Class/Reported_Target**
- 断言：发布 workbook 的 `cell_lines_summary` = 36 行（Human 33/bacteria 2/fungus 1；`lineage` 14 个水平，其中第 29 行 organism="Human" 与 lineage="bacterial_pathogen" 不一致）；`drugs_summary` = 136 行、`class` 仅 5 个水平（investigational 73 / chemotherapeutic 26 / antibiotic 18 / antifungal 15 / natural_product 4）；`41467_2025_66223_MOESM8_ESM.xlsx`（sparse 模式化合物表）135 行，含 CHEMBLID、Action_Class（5 水平）、Reported_Target（99 个不同值）。
- 引文（observed 计数，逐字来自审计文件）："drug class levels: {"chemotherapeutic": 26, "antibiotic": 18, "investigational": 73, "antifungal": 15, "natural_product": 4}"
- 源：`sources/extracts/combocat_dense_supp_workbook_audit.txt` §cell_lines_summary/§drugs_summary；MOESM8 计数见本文件 §4 备注（openpyxl 直读）。
- 状态：observed。
- 含意：A2 门槛"至少 12 个可分析注释水平"在**发布文件的 drug class=5 水平**下不达标；`lineage`=14 水平达标但那是细胞系注释、且 leave-drug-out 设计不用它。若要 12+ 水平只能依赖 `Reported_Target`（99 水平），但需先解决 F29 的身份连接问题。

**F29｜A2 硬阻断：root_id 为哈希、药物名仅为占位符，身份/注释无法在发布文件内连接**
- 引文（审计记录逐字）："named root_id: 2; 32-hex-hash root_id: 804"
- 源：`sources/extracts/combocat_dense_supp_workbook_audit.txt` §data（observed：`data` sheet 292,458 行；`drug1_name`/`drug2_name` 唯一取值仅 "drug1"/"drug2" 占位符；命名 root_id 仅 2 个：`CHP134_AZD1390_CX-5461...`、`LUM_SMX_TMP...`；其余 804 个为 32 位十六进制哈希；`drugs_summary`/`cell_lines_summary` 的数字键与 root_id 无 join key）。另：`Plate Barcode` 多数为 NA，抽样行中少量有值（如 `ASY0623030`），`Amount`/`failed_transfer`/`transfer_type` 同样仅部分行有值。
- 状态：observed。
- 含意：**按发布文件，A2 无法构造"留药"切分所需的两药身份/注释映射**（804/806 单元不可连接），必须先由 A1 从其他渠道取得映射（作者/仓库/另行分发），否则 A2 不满足"注释水平可分析"前提。此事实不排除其他分发渠道存在映射，只说明**本任务已核验的发布文件不足**。

**F30｜A2 门槛算术：cell×pair 单元总数=806，两药未见单元必 <806 ⇒ "≥800 + ≥12 注释水平"不可达**
- 断言：由 F20（806 组合）、F22（每组合 1 板）、F23（806 板）与审计（806 root_id = combination:cell_line）推出：dense 参考数据共 **806 个 cell×pair 单元**，且没有药对在 >1 细胞系上重复；任何合理"留药"切分中"两药都未见"的单元数都远小于 806（且需训练中出现的注释水平 ≥12，而发布注释仅 5 类）。
- 引文（derived 依据，逐字）："data rows (excl header): 292458; unique root_id: 806"
- 源：`sources/extracts/combocat_dense_supp_workbook_audit.txt` §data。
- 状态：derived（由 F20/F22/F23/F29 推出）。
- 含意：**A2 达标门槛不满足**。按 BRIEF §1/§3：不运行复现，只记录资格结论（这本身是有效负结果）；不得通过改门槛或换聚合单位使 A2 "过关"。

---

## 4. 检索缺口与零命中（PASS 1 完成 + PASS 2）

**PASS 1（承接并完成）**：本地 `sources/queries/` 下已有 Europe PMC/OpenAlex 查询 JSON（A/B/C 系列共 30+ 条，含题录与命中数）；本任务完成核对与判读，不重复消耗 pass。关键判读（全部 observed，文件为准）：
- EPMC `C-q1_MDE_AL`（"minimum detectable effect" × AL/design）hit=1 → 唯一命中为 2017 年厄瓜多尔膳食多样性政策研究，**无关**。
- EPMC `C-q3_detectabilityconstrained`（"detectability-constrained"）hit=1 → 唯一命中为 2026 年箱型水母 eDNA 可检测性研究，**无关**。
- EPMC `C-q6_poweraware_acq`（"power-aware" × design/acquisition/AL）hit=1 → 唯一命中为 2019 年 IoT 功耗感知移动性论文，**无关**。
- EPMC `C-q2b_powerconstrained_TITLEABS` hit=0；OpenAlex `OA-s1_powerconstrained_design` hit=0。
- EPMC `C-q4_decisionfocused_TITLEABS` hit=1 → 即 F12 的 2026 preprint；OpenAlex `OA-s3_decisionfocused_design` hit=5，其中前两名为 F01/F05 的 2605.26093/2602.05340。
- OpenAlex `OA-s4_MDE_AL` hit=1（2026 农业害虫监测 AL 预算约束评估，仅相邻）；`OA-s6_batch_AL_combo` 命中 AL_guide_2025（F15）；`OA-s8_power_AL` 15 条均非 acquisition 功效问题。

**PASS 2（2026-10-27，1 个新 pass；合并查询）**：原始响应与汇总见 `sources/queries/pass2_*`（脚本 `pass2_targeted_queries.py`、`pass2_followup_queries.py`，汇总 `pass2_summary.json`）。
- `P2-q3_power_acquisition_recent`（EPMC：power analysis/MDE/power-aware × acquisition function/BOED/batch AL，2023–2026）：**hitCount=0**（逐字记录 `"hitCount": 0`）。
- `P2-q2_decision_acq_noise`（EPMC：decision-focused/goal-oriented/VOI × acquisition/design/AL × MDE/power/detectability/replication/sample size，2023–2026）：hitCount=1，唯一命中为法医学文献综述工具，**无关**。
- OpenAlex 标题摘要精确过滤：`P2-o4_decisionfocused_acq`（"decision-focused" ∧ "acquisition function"）**hitCount=0**；`P2-o5_power_boed`（"statistical power" ∧ "Bayesian experimental design"）**hitCount=0**。
- OpenAlex `P2-o3_mde_acq`（"minimum detectable effect" ∧ "active learning"）hitCount=1 → 2026 Zenodo 农业害虫监测"预算约束下 AL 评估"预印本，仅相邻（预算约束 AL，非 MDE 门控、非组合筛选）。
- EPMC `P2-q1_EVSI_sample_size`（VOI/EVSI/ENBS × sample size/power/cost × trial/decision/design）hitCount=477 → EVSI/ENBS 成熟文献群（F11，仅题录）。
- OpenAlex `P2-o6_detectability_al`（"detectability" ∧ "active learning"）hitCount=1552 → 均为"检测类任务"（入侵/异常/欺诈检测），与"效应可分辨性"术语撞车，无关。

**检索缺口（必须写进限制）**
- **G1**：arXiv API 本轮不可达（2 次 read timeout + 1 次 HTTP 429），PASS 2 未执行 arXiv 侧检索；已用本地 5 篇 arXiv 全文覆盖 decision-focused/robust BOED/regime 四个最近邻方向，但不能排除未下载的 arXiv 先例（尤其 2026-10 之后新预印本）。
- **G2**：EVSI/ENBS 先例（F11）仅题录级（477 命中中未读全文），若 Lead 需要精确差异边界，需另读 2–3 篇全文（会消耗新 pass）。
- **G3**：BATCHIE 补充材料（PDBAL theory）未下载，F13 只能写"下载正文未见 SNR 惩罚项"，不能据此否证其在补充材料中存在。
- **G4**：ComboCat 数据身份问题（F29）只覆盖"已下载的 Supplementary Data 1（REVISED）"；若作者另有映射分发渠道，需 A1 线取得后重判 A2 门槛。
- **零命中纪律**：以上 0 命中（`P2-q3`、`P2-o4`、`P2-o5`、`C-q2b`、`OA-s1`）仅记录为"本任务检索范围内未命中"，**不写成"不存在"**；对"I003 是否已被覆盖"的判定基于已读一手全文（F01–F17），不依赖零命中。

---

## 5. 对 Lead 的判定建议（不替代 challenge_I003.md）

- **覆盖结论：部分覆盖。** I003 的 decision-focused 动机、乘积门控结构、噪声/识别 SNR 条件、决策价值 vs 成本原则均已有先例；唯一未覆盖物件是"以每动作实际重复数计算的 MDE 作为 acquisition 准入闸"＋"行级物理成本"的构成。
- 该构成属**评估修正材料**，非新机制；且对应 ComboCat A2 身份/门槛均不满足（F29/F30），本轮无法提供第二资源验证。
- 按 BRIEF §3 停止条件：**应收窄为评估修正或停线，不换名重启**；不得声称新颖性/收益。若 Lead 与挑战者决定 stop，本 evidence.md 的 F01–F18 可直接作为支持；唯一需 Lead 对齐的未核验项是挑战者理由 (d)（R5/I003 主张 B 同对象）与本文件 F07 的限定（乘积门控变量不同）。
