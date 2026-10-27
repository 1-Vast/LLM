# prior_art：R198-A4 "表征遗漏关键状态" 先例核验

2026-10-27 · 只做先例核验，不运行效果、不评估本机数据效果、不改 PROTOCOL；不声称新颖性。
证据状态：`full-text`＝读到一手全文/PDF 抽取；`abstract-only`＝一手摘要；`P`＝读过方法/限制片段（本文件凡标 `P` 的均来自本项目已登记的一手读取记录，不是本轮新读全文）；`local-secondary`＝本机二手整理；`search-result`＝检索结果（含零命中，**不写作"不存在"**）。

## 0. 结论（先写）

1. **"细胞状态特征/上下文表征"本身已被大量覆盖**：细胞状态特征×协同预测、留出细胞评估、identity shortcut（One-Hot News）、细胞 embedding（BATCHIE）、共享+条件特异分解（PDTSyn）、context-specific residual（Tahoe-100M LOCO）、mechanism/context 解耦（DECANT）都已有先例；**不能**把"加细胞状态表示/换 embedding/换 context 分解"当新方向或新颖性来源。
2. **本任务的对象不是"新表示"，而是"诊断程序 + 测量动作"**：给定冻结关系与少量反馈，判断冲突残差是否可由（已测未表征或需新测量的）**状态变量**解释，并据此在"修订关系 / 重标定 / 补测状态"之间路由。就没有检索到直接先例（**检索结果，不是空白证明**）；但相邻构件（冲突信号、置信度/不确定性、batch effect、无混杂敏感性分析、context shift 基准）都有压力，必须先做独立挑战与最小区分实验。
3. **本轮不声称新意**；若 Lead 要升级，必须按 [protocol_draft.md](protocol_draft.md) 冻结并通过独立挑战，且与"最强静态预测器/普通残差/后验方差/leverage/距离"等对照分开归因。

## 1. 逐条覆盖核查

### 1.1 One-Hot News（Bioinformatics 2026, btag040）——identity shortcut / LDO

- **覆盖内容（full-text，本项目已逐段核读）**：
  - 模型会把"表示"当**细胞/药物标识符**使用；one-hot 与生物特征在面板内**相当甚至略好**（Candir 等；R179/R180 记录）。
  - **LCO（留出细胞）**下细胞基因表达特征与 one-hot 相当；**LDO（两药都未见）**单独成表，且"model fails to generalize"，细胞特征略好但都差（`prior_art.md` F03/F04/F11/F12；源 `onehot.txt:648-649,406-407,392-396,674-676`）。
  - "真正零样本三元组"在当前数据里构造不出来（F12）。
- **对本任务的含义**：**已覆盖**——"用表达特征代替 identity 不一定带来泛化"是已被发表的对照；本任务**不得**把"加入细胞状态特征"当作新颖性。
- **未覆盖（本任务观察）**：该文没有把冲突残差分解为"已知协变量 vs 状态 vs 噪声"，也没有"何时该补测状态、何时该改关系"的决策/测量动作分析；这是本候选的剩余差异候选（**非新颖性结论**）。

### 1.2 BATCHIE（Nat Commun 2025, 10.1038/s41467-024-55287-7）——cell embedding × drug-dose + 批次设计 + 后验更新

- **覆盖内容（`P`；本项目已登记读取：Methods Sec12/14/20、式 24–30；本地全文 `lit/batchie.txt` 可复查）**：
  - 层级贝叶斯张量分解：**细胞线 embedding**（cell-line latent coordinates，Gamma process 精度）× 药物/剂量 embedding；组合响应的后验更新（MCMC）。
  - **plate/batch 结构**是实验设计单位（每板=1 细胞系 + row plate + column plate）；**独立 duplicates**（rounds 11–15）与 **QC flag**（duplicate 差异 >0.5 活力）处理失败孔；PDBAL 动作距离用于选下一批板。
  - 有独立重复（Phase II）与 random unseen combinations 验证；作者明确"plate 无重叠"不等于实体键无重叠（本项目 evidence 记录已核）。
- **对本任务的含义**：**部分覆盖**——反馈更新 + 细胞线 embedding + 批次/QC 设计已有；BATCHIE 的"cell 状态"实际是**细胞线 latent embedding**（以身份/响应学出来的），**不是**表达/突变/培养等可测状态变量；批次/plate 被当作设计与 QC 结构，**不是**"遗漏状态"检测。
- **剩余差异（候选）**：把**可测的**细胞状态变量与冲突残差做状态条件化，并把"测状态"作为反馈动作；BATCHIE 没有这种诊断/路由，也不保证 expression 状态相对 embedding 的增量。仍需与 BATCHIE 类 cell embedding 做**同信息对照**（不是赢弱预测器）。

### 1.3 PDTSyn（Brief Bioinform 2026, bbag199）——共享 + 细胞条件参数分解

- **覆盖内容（`P`；本项目已登记读取 JATS sec2g/2h/2m/2r、sec3j，部分表）**：共享分支 + 细胞条件参数分解（context-specific）、分布对齐；unseen cell/drug/pair 已有评估；端点 MSE/RMSE/PCC（O'Neil unseen-cell MSE 389.34 ± 185.30，本项目 prior_art F07）。
- **对本任务的含义**：**部分覆盖**——"共享 vs 背景特异"的分解已发表；本任务不是新分解，而是"哪一类残差差值需要补测状态"的诊断与动作；PDTSyn 的隐变量是转录表型/机制 latent，**不是**未测状态检测。
- **剩余差异（候选）**：状态条件化冲突的**决策相关**检验（补测状态是否改善未测选择），PDTSyn 未覆盖；但必须先过"同信息、同容量"对照（PDTSyn 类直接近邻/共享+条件分解基线）。

### 1.4 细胞状态特征 × 组合预测的近邻（已覆盖清单）

| 工作 | 覆盖点 | 锚点 | 证据 |
|---|---|---|---|
| DeepSynergy 2018 | 表达/化学特征×协同；novel cell lines 分层 CV；MSE/Pearson | cellstate-qualification `prior_art.md` F01/F02 | full-text |
| Baptista 2023 系统评估 | 随机切分；作者自认 LCO/leave-drugs-out 会显著降低；表达特征≈细胞标识符 | F10/F16（`baptista_systematic_eval_2023.txt:151,160`） | full-text |
| SynVerse 2025 | 16 模型×8 特征（含 CCLE 表达、LINCS、靶点）；四切分含 leave cell line；无一超过 one-hot | `prior_art.md` F16、§3 表 | full-text |
| DIPx 2025 | 通路激活细胞特征；两药均未见的 262 实验上中位相关 −0.03（TAIJI-M 0.11） | F13（`dipx_elife_2025.txt:31`） | full-text |
| Regulon 2026 | unseen cells/scaffolds/二者同时排除；联合排除时特征增益消失；端点 ZIP 三分类 | F14（`regulon_context_2026_ppr1330660.txt:8-13`） | abstract-only |
| Tahoe-100M LOCO 2026 | 基础转录组预测"去 drug mean 的 context-specific 残差"；整体不能；作者声明此前无人用 residue endpoint | F15/F20/F34（`tahoe_loco_basal_2026.txt:30,48`） | full-text |
| SynProtX 2025 | 蛋白/结构特征；随机切分 AUROC/AUPRC 增益，LCO 下退化 | F23（`synprotx_2025.txt`） | full-text |
| arXiv 2605.20885 | 单药 IC50 的 within-drug cell ranking 作为独立评估对象；cell-blind per-drug r=0.438；无 encoding 超过 cell-only；明确排除 combinations | F17/F28–F30（`arxiv_2605.20885.txt:25,37,462-475,79`） | full-text |
| iScience 2025 | cell-blind 组合敏感性 + per-combination PCC；指出 per-treatment 相关"frequently not performed" | F31/F32（`beyond_synergy_scores_2025.txt:85,93-94,99`） | full-text |
| cell-line embedding 2025 | 纯 cell-line embedding 的协同/药敏预测（+0.4% PCC 级） | F27（`cellline_embedding_2025.txt`） | full-text |
| Separating main effects 2026 | 组织/主效应基线；personalization ρ≈0.05；tissue-only 基线 | F21（`separating_main_effects`，本项目 prior_art 记录） | 摘要级（本项目登记） |
| FORGE/VCAT 2026 | 遗传依赖/CRISPR 特征补充表达特征（另有 LCO 退化/端点差异） | F24/F25（本项目 prior_art 记录） | 部分全文/摘要 |
| DECANT 2026 | single-cell 药物扰动表征中"mechanism vs context"解耦；输入含处理后细胞/对照/背景；作者明确 latent 是转录表型、非靶点参与 | cross-domain `evidence_notes.md:26`（`P`；JATS §§2.4–2.5,2.8–2.9,4） | P |
| State（Cell 2026） | 跨 diverse contexts 预测细胞扰动响应（context 表征） | `reference/papers.tsv`（`doi-10.1016-j.cell.2026.07.052`，A 级，全文受限） | abstract-only |
| Benchmarking virtual cell in-the-wild 2026 | 背景/扰动/跨数据集迁移的基准与强基线；池化不必然改善域移 | cross-domain `evidence_notes.md:18`（`P`） | P |

**结论**：本任务若只停留在"状态特征 + 组合预测 + context 分解"→ 已覆盖，不能当新贡献；必须定位在**冲突/残差的诊断路由与补测动作**。

### 1.5 "遗漏状态"直接先例（含检索缺口）

- **未发现**（本项目本地文献库 + 已登记的一手/摘要 + 本任务有限检索）把"**冲突残差 → 已测未表征状态 vs 未测状态 → 补测哪个状态/条件**"作为可控程序、并给出**决策相关**检验的协同/组合工作。
- **相邻压力（不是先例，但必须写进挑战）**：
  - **不确定性/置信度基线**：后验方差、leverage、距离、GP 方差都能"预测失败"；F3 增量必须超过这些（cross-domain report §5 H1 已要求）。
  - **batch effect/批次校正**：批次可当已测协变量；若状态就是批次，则属 F1/F2（可测背景），不是 F3。BATCHIE 已把 plate/QC 纳入设计。
  - **无混杂敏感性分析/未测混杂**：因果推断中的 E-value/negative control 等说明"未测混杂"本身是成熟概念；本任务只有在**功能/决策层面**的可检验签名，不能声称提出"未测混杂"概念。
  - **context shift/OOD 基准**：virtual cell in-the-wild 等基准已测"跨数据集/背景迁移"；本任务差异只在"把误差来源路由为测量动作"，仍需同基准对照。
- **检索缺口（如实披露）**：本任务未做系统综述；未查 Google Scholar/Scopus/Web of Science、未做引文回溯/前向追引；"within-pair""missing state""unmeasured covariate"等术语可能漏检其他措辞；One-Hot 补充表（S7–S12）与 BATCHIE 补充材料未逐页核；全文仅到本项目已登记范围。**"未发现"不能写成"不存在"或"空白"**。

## 2. 最近先例的"最强替代解释"清单（挑战用）

1. **普通残差/不确定性**：F3 增益可由残差幅度、距离、后验方差、leverage 完全解释 → 本候选无额外贡献。
2. **已知批次/协变量**：所有"状态"其实是已测背景（组织/批次/剂量/培养注释）的代理 → 归 F1/F2，不是 F3。
3. **容量/参数量**：状态增广只是增加容量/正则差异 → 需容量匹配与同信息对照。
4. **测试标签泄漏**：状态变量或阈值用响应挑选 → 需预注册变量集、无响应派生状态、细胞分组 CV。
5. **端点/资源限制**：A0 MDE=0.240、A1 inconclusive、A3 not_qualified → 阴性/不显著只能报 `inconclusive`，不能当 F3 不存在或 F1/F2 成立。

## 3. 本方向剩余差异（候选，非新颖性结论）

- 不在"新表示/新模型"：状态表示、identity shortcut、细胞 embedding、共享+条件分解均已被覆盖。
- 候选差异只在**程序对象**：(i) 把冲突残差做"状态可解释性"分解（已知协变量/状态/噪声）；(ii) 以**补测状态/条件**作为可选动作，与关系修订、数值重标定并列比较；(iii) 用**决策相关**指标（未测选择）而不是全局预测相关验收。
- 若最强替代（普通残差/不确定性/已知协变量）在同信息下完全复现 → 撤本候选，不换名保留。

## 4. 本文件不修改其它目录与记录；先例引用沿用本项目已登记的证据状态，不把 `P`/摘要级提升为全文级。
