# PASS LOG — R190 线 D 先例核验（cellstate-lit / task-5，2026-10-27）

预算：**2 个定向 pass**（BRIEF §5；本地一手全文优先，联网仅 Europe PMC REST / OpenAlex API / arXiv API）。受限域名重试 ≤2 次；不下载 >20 MB 文件。
实际消耗：**PASS 1（18 个合并查询）+ PASS 2（12 个合并查询）= 2 pass**；已知条目全文/摘要抓取不计新 pass，单列"文档抓取"。所有原始响应在 `sources_lit/raw/`，查询脚本在 `sources_lit/` 下。

---

## PASS 1 — 2026-10-27 13:1x（广撒网：八类问题合并）

脚本：`pass1_queries.py`、`pass1_retry.py`、`pass1_retry2.py`；原始 JSON/XML：`raw/epmc_P1-*.json`、`raw/openalex_P1-*.json`、`raw/arxiv_P1-*.xml`。

| id | 数据库 | 查询要点 | hitCount | 原始文件 |
|---|---|---|---|---|
| P1-e1 | EPMC | synergy/combination × unseen cell line / LCO / cell-line-out | 5 | epmc_P1-e1_cell_unseen_synergy.json |
| P1-e2 | EPMC | synergy × ranking × cell line，2019–2026 | 15 | epmc_P1-e2_synergy_cell_ranking.json |
| P1-e3 | EPMC | pathway activity / transcriptomic / molecular features × synergy prediction，2018–2026 | 22 | epmc_P1-e3_pathway_expression_features.json |
| P1-e4 | EPMC | CRISPR / gene dependency × synergy / drug response，2019–2026 | 449 | epmc_P1-e4_crispr_dependency_synergy.json |
| P1-e5 | EPMC | cold-start / zero-shot / OOD × synergy，2023–2026 | 38 | epmc_P1-e5_coldstart_synergy.json |
| P1-e6 | EPMC | one-hot × synergy/drug combination | 8 | epmc_P1-e6_onehot_synergy.json |
| P1-e7 | EPMC | within-pair / per-drug-pair / pair-specific ranking / cell ranking | 988（全为双胞胎/配对研究，见 F35） | epmc_P1-e7_within_pair_terms.json |
| P1-e8 | EPMC | combination/synergy selectivity / cell-line-specific | 178 | epmc_P1-e8_synergy_selectivity.json |
| P1-e9 | EPMC | 已知标题：Pathway activation model for personalized prediction of drug synergy | 2 | epmc_P1-e9_known_pathway_activation.json |
| P1-e10 | EPMC | 已知标题：leakage-controlled cold-start benchmark | 0 | epmc_P1-e10_known_coldstart_benchmark.json |
| P1-o1 | OpenAlex | unseen cell lines + gene expression + synergy prediction（2021+） | 510 | openalex_P1-o1_unseen_cells_expression.json |
| P1-o2 | OpenAlex | ranking cell lines / drug combination synergy（2019+） | 2205 | openalex_P1-o2_rank_cells_synergy.json |
| P1-o3 | OpenAlex | pathway activity personalized synergy prediction（2022+） | 9801 | openalex_P1-o3_pathway_personalized_synergy.json |
| P1-o4 | OpenAlex | CRISPR dependency drug combination prediction（2019+） | 5175 | openalex_P1-o4_crispr_dependency_combination.json |
| P1-o5 | OpenAlex | cold start drug combination synergy（2023+） | 7848 | openalex_P1-o5_coldstart_combo.json |
| P1-o6 | OpenAlex | within-pair ranking drug combination cell lines（2018+） | 12485 | openalex_P1-o6_within_pair_ranking.json |
| P1-a1 | arXiv | "drug synergy" × cell line(s) | 7 | arxiv_P1-a1_synergy_cell.xml |
| P1-a2 | arXiv | (drug combination/synergy) × (unseen/cold-start) | 76（提取最近 20） | arxiv_P1-a2_synergy_unseen.xml |

**PASS 1 故障与重试**：首轮 4 个请求出现 `SSL: UNEXPECTED_EOF_WHILE_READING`（E1/E3/O5/O6；非域名限制）。重试 1 次后 E1/E3 成功；O5 第 2 次成功、O6 第 3 次（第 2 次重试）成功。均未换查询、未新增 pass。**EPMC e1/e3、OpenAlex o5/o6 的 raw JSON 为最终成功版本。**

**PASS 1 判读（入选）**：DeepSynergy 2018、Baptista 2023、One-Hot News 2026、SynVerse 2025、PDTSyn 2026、SynProtX 2025、DIPx 2025、Regulon 2026、Separating main effects 2026、iScience 2025（beyond synergy scores）、FORGE 2026、VCAT 2026、cell-line embedding 2025。**BMC Bioinformatics 2026 cold-start benchmark 在 PASS 1 未命中（P1-e10 题名检索 0），由 PASS 2 的 OpenAlex P2-o1 落到 DOI。**

---

## PASS 2 — 2026-10-27 13:1x（补缺：per-treatment 排序 / 冷启动基准 / 细胞状态表示 / dependency 特征 / unseen 变体词）

脚本：`pass2_queries.py`；原始响应：`raw/pass2_epmc_*.json`、`raw/pass2_openalex_*.json`、`raw/pass2_arxiv_*.xml`。

| id | 数据库 | 查询要点 | hitCount | 原始文件 |
|---|---|---|---|---|
| P2-e1 | EPMC | cell line ranking / rank cell lines / per-drug / drug-wise / per-treatment / per-combination × drug response/synergy | 47 | pass2_epmc_P2-e1_per_treatment_ranking.json |
| P2-e2 | EPMC | cold-start benchmark / leakage-controlled × combination/synergy | 2 | pass2_epmc_P2-e2_coldstart_benchmark.json |
| P2-e3 | EPMC | cell state / cell-line embedding / cellular representation × synergy/combination，2022–2026 | 11 | pass2_epmc_P2-e3_cell_state_representation.json |
| P2-e4 | EPMC | gene dependency / CRISPR × combination/synergy prediction | 1 | pass2_epmc_P2-e4_dependency_feature_combo.json |
| P2-e5 | EPMC | unseen/novel cell lines × combination/synergy，2020–2026 | 8 | pass2_epmc_P2-e5_unseen_celllines_variants.json |
| P2-o1 | OpenAlex | leakage-controlled cold-start benchmark drug-combination synergy classification（2024+） | 133 | pass2_openalex_P2-o1_leakage_coldstart.json |
| P2-o2 | OpenAlex | cell line ranking / per drug correlation drug sensitivity（2018+） | 9971 | pass2_openalex_P2-o2_cellline_ranking.json |
| P2-o3 | OpenAlex | within-combination across-cell-line variation / synergy evaluation（2019+） | 20867 | pass2_openalex_P2-o3_within_treatment.json |
| P2-o4 | OpenAlex | cell state representation drug combination unseen cell lines（2023+） | 456 | pass2_openalex_P2-o4_cell_state_synergy.json |
| P2-a1 | arXiv | "drug synergy" × ranking/rank | **0**（F35 的零命中记录） | pass2_arxiv_P2-a1_synergy_ranking.xml |
| P2-a2 | arXiv | OOD-GraphLLM | 1（arXiv:2605.30247） | pass2_arxiv_P2-a2_ood_graphllm.xml |
| P2-a3 | arXiv | cold-start × drug combination/synergy | 2 | pass2_arxiv_P2-a3_coldstart_combo.xml |

**PASS 2 判读（新增关键项）**：
- `P2-o1` 第 1 条即 **"A leakage-controlled cold-start benchmark for drug-combination synergy classification"（BMC Bioinformatics 2026, 10.1186/s12859-026-06665-z）**——正是 C145 提到的同型设定；P2-e2 的 EPMC 未检索到该篇（EPMC 题录缺失），由 OpenAlex 命中。
- `P2-o2` 发现 **arXiv 2605.20885 "Training distribution determines the ceiling of drug-blind cancer sensitivity prediction"**：摘要与正文明确使用 **"per-drug Pearson r, which isolates within-drug cell ranking"** → F17/F28/F29/F30。
- `P2-e1` 发现 **Research Square 预印本 "Basal expression predicts context-specific drug responses only where they are reproducible"（Tahoe-100M 47-line LOCO）** → F15/F20/F34。
- `P2-o2` 另命中 **DRUML（Nat Commun 2021，药物排序）** 与 **Reliable anti-cancer drug sensitivity prediction and prioritization（Sci Rep 2024）**：两者都是"给定细胞排药物"，不是"给定药排细胞"；用于 F31/F32 的语境（处理内排序的镜像对象），不单独列 FACT。
- arXiv P2-a1 的 0 命中是 F35 的零命中记录之一。

---

## 文档抓取（不计 pass；均为 PASS 1/2 已命中条目）

脚本：`pass1_fetch_fulltext.py`、`pass2_doc_retrieval.py`、`pass2_doc_retrieval2.py`、`build_abstract_extracts.py`。
- Europe PMC `fullTextXML`（OA JATS，11 篇，全部 <20 MB）：deepsynergy_2018（PMC5925774）、baptista_systematic_eval_2023（PMC10072473）、synverse_2025（PMC12753315）、pdtsyn_2026（PMC13109062）、synprotx_2025（PMC12343095）、dipx_elife_2025（PMC12133153）、beyond_synergy_scores_2025（PMC12152377）、forge_2026（PMC13396380）、reliable_eval_2026（PMC13358880）、cellline_embedding_2025（PMC12205321）、metasynergy_2025（PMC12710477）。→ `raw/fulltext/*.xml|.txt`，抓取日志 `raw/fulltext_fetch_log.json`。
- Springer OA 落地页：`bmc_coldstart_2026`（正文未渲染，仅摘要+元数据）→ `raw/bmc_coldstart_2026.html`、`raw/fulltext/bmc_coldstart_2026.txt`。
- Research Square 预印本 HTML：`tahoe_loco_basal_2026` → `raw/tahoe_loco_basal_2026.html`、`raw/fulltext/tahoe_loco_basal_2026.txt`。
- arXiv HTML v1：`arxiv_2605.20885.txt`（`raw/fulltext/`）；arXiv API 摘要：OOD-GraphLLM 2605.30247、SynCell 2511.17695、CausalDDS 2511.02146、drug-blind ceiling 2605.20885 → `raw/arxiv_*.xml` + `raw/abstracts/*`。
- EPMC 按 DOI 取题录（已命中条目）：DRUML 2021、reliable prioritization 2024、general principles 2025、SynergyX 2024、DrugCell 2020 → `raw/epmc_doi_*.json`。
- 摘要抽取（含行锚）：`raw/abstracts/*.txt`（regulon、separating main effects、VCAT、DrugCell、OOD-GraphLLM、SynCell；每文件第 1 行=来源头，第 2 行起=逐字摘要、仅按空格换行）。
- 未取得（受限/故障）：
  - Regulon 2026 与 Separating 2026 的**全文**：EPMC `PPR*/fullTextXML` 返回 HTTP 500；Research Square/bioRxiv DOI 首页对 Regulon 返回 **HTTP 429**（1 次；未继续重试）→ 只用摘要。
  - One-Hot News 的**补充表 S7–S12** 未下载（PDF 抽取文本不含 supplement）——检索缺口。
  - BMC cold-start 的**正文 body** 未在落地页 HTML 中渲染（early access 分享页）→ 只用摘要。

---

## 本地一手/二手核验（不计 pass）

- **One-Hot News 全文**（前轮 R180 的 PDF 抽取）：`research/2026-10-27-agent-cell-identifiability-r180/raw/onehot.txt`，本报告用其行锚（LCO/LDO 表 :397-420；LCO 定义 :374-381；LDO 定义 :392-396；"truly zero-shot" :674-676；LCO/LDO 结论 :644-661；摘要 :20-26）。
- **`lit/report.md`**：Nair 2023 的跨筛排序一致性（FACT 3，:35）与重复噪声（FACT 2）作为 `local-secondary` 引用（原文本轮未重读）。
- **`reference/`、`reference/papers.tsv`、`reference/README.md`**：核对本机已存 15 条来源，无 DeepSynergy / SynVerse / PDTSyn / One-Hot 全文（One-Hot 只有 R180 抽取文本）；未重复下载 reference 中已有文件。
- **`research/2026-10-27-detectability-acquisition/sources/`**：本地已有 BATCHIE、AL_guide、ComboCat、arXiv 5 篇等；本轮只在需要时 grep，不重复下载。BATCHIE 全文的参考文献列表给出 DeepSynergy 的 DOI/PMCID（10.1093/bioinformatics/btx806 / PMC5925774），用于定位 F01。
- **`research/SYNTHESIS.md` §0/§2d**：C141（只排组合不排细胞）、C145–C148（One-Hot News 全文已核、LDO/LPO 分类、Li 2024 已核）作为前置；本报告不重复其结论，只补充"细胞特征 × 留出细胞 × within-pair 排序"的先例。
- **引文逐字审计**：`verify_quotes.py` 对 `prior_art.md` 中 56 条引文做 whitespace-normalized 比对（HTML/抽取文本按空格换行；BMC 数字的 `\(…\)` LaTeX 标记与 SynProtX 的 `(Fig. 13 )` 排版空格按报告中的注释处理）：**TOTAL 56 FAILS 0**。

---

## 零命中 / 反面检索记录（只作检索结果，不写"不存在"）

1. Europe PMC `within-pair` 系列（988 条）——全部与双胞胎/配对研究相关，**无**协同/药对细胞排序工作（P1-e7）。
2. arXiv `abs:"drug synergy" AND (abs:"ranking" OR abs:"rank")`——**0 entries**（P2-a1）。
3. Europe PMC 题名检索 `leakage-controlled cold-start benchmark`——0（P1-e10）；该文题录不在 EPMC，用 OpenAlex 命中（P2-o1）。
4. Europe PMC `gene dependency/CRISPR × combination/synergy prediction`——1 条（TranSynergy 2021，机制解释性 DNN，非 within-pair 排序）；说明"CRISPR dependency 作协同细胞特征"在本轮查询内几乎无直接命中，**不能写成不存在**。
5. 未检索到以"within-pair cell ranking on ΔEMAX"为主/副端点的任何工作（综合 P1-e1/e2/e7、P2-e1/e5、P2-a1）。

---

## 未决缺口（供 Lead 决定是否追加）

- **G1 全文缺口**：Regulon 2026、Separating 2026 全文；BMC cold-start 正文；One-Hot 补充表 S7–S12；VCAT 全文。
- **G2 库缺口**：Google Scholar/Scopus/引文回溯未做；PRISM 侧协同模型未单独检索；中文库/会议未查。
- **G3 术语缺口**：PubMed 中 "within-pair" 被双胞胎研究占据；其他措辞（如 per-drug correlation、context-specific residual、combination-specific concordance）已尽量覆盖，但可能仍有别称。
- **G4 证据等级**：Regulon/Separating/VCAT/BMCC（BMC 正文）为 abstract-only；One-Hot News 为 PDF 抽取（图表未逐页核）；F33 为 local-secondary。引用其数字时必须在正文标注相应证据状态。

---

## 产物清单

- 主报告：`../prior_art.md`（F01–F35 + 逐题结论 + 先例表 + 差异 + 缺口 + 处置）。
- 本日志：`pass_log.md`。
- 查询脚本：`pass1_queries.py`、`pass1_retry.py`、`pass1_fetch_fulltext.py`、`pass2_queries.py`、`pass2_doc_retrieval.py`、`pass2_doc_retrieval2.py`、`build_abstract_extracts.py`。
- 原始响应：`raw/`（epmc/openalex/arxiv 查询 JSON/XML、fulltext/、abstracts/、doc_retrieval_log.json、fulltext_fetch_log.json、pass1_summary.json、pass2_summary.json）。
- 未改：`PROTOCOL_A0.md`、`research/INDEX.md`、`SYNTHESIS.md`、`git`、其它研究目录。
