# E.v1 化学最近先例：有界定向检索，原件核读未达标

2026-10-29。本worker仅调查化学先例，不开发候选，不作最终独立审判。**本批次不能判定 E.v1 已被原论文直接覆盖，也不能判定其未被覆盖。** 7次公开HTTP动作已耗尽；成功获得2份Crossref题录/摘要响应，未成功获得任何可核读原论文正文。近期Europe PMC主题查询503、Springer身份跳转、PMC/RSC403均按边界隔离。失败不是无先例证据。普通交互模型、模型树、VOI能复现骨架的已有判断不因本次检索改变；但也不能把它们当作化学对象所有最近先例的替代物。

事前问题/反例/预算保存在 `sources/chemical_prior/initial_questions.md`，早于首次请求。未读响应药效、新数据、作者代码、权重或.env；未编辑共享reference索引。Requested Sol/high；effective model/effort、provider usage、实付均unknown。

## 实际覆盖与访问账本

实际仅3个主题query动作：Q1 Europe PMC近期cell/selectivity/MMP布尔式（失败）；Q2 Crossref `matched molecular pairs active learning experimental design`；Q3 Crossref `matched molecular pairs nonadditivity selectivity`、`type:journal-article`。Q2/Q3是Crossref宽松相关性题录排名，**不是布尔检索等价物**：分别返回total-results 9,857,089与2,099,039，仅读首页25与60项；存在大量非化学matched-pairs噪声和SI。因此不能据此声称近期/主动设计/选择性已充分查全。原拟EPMC Q2/Q3未执行，改源动作不伪装为同一查询的独立重复验证。

| 动作 | 请求与保存tag | HTTP | 实际结果 |
|---|---|---:|---|
| 1 | EPMC Q1；q1 | 503 | 89B失败body；停止EPMC本批次 |
| 2 | Crossref Q2；q2_crossref | 200 | 52,420B题录/摘要，25项 |
| 3 | Crossref Q3；q3_crossref | 200 | 547,820B题录/摘要，60项 |
| 4 | Springer 2021 nonadditivity正文；nonadd2021 | 303 | 空body；Location指向idp.springer.com/authorize，未跟随身份跳转 |
| 5 | NCBI旧DOI-IDconverter；idconv | 301 | 418B迁移页，明确指向新公开API；没有原文 |
| 6 | 新公开PMC DOI-IDconverter；idconv_public | 403 | 134B拒绝；停止PMC该源 |
| 7 | RSC 2026 explainability HTML；rsc2026 | 403 | 5,621B拒绝；停止RSC该源 |

每次timeout=30s、0自动重试、0自动redirect；同host请求间隔≥1s。总7/7动作；主题3/3；成功body共600,240B，最大547,820B，均低于6MB/4MB。新原论文正文成功0篇；题录、摘要和错误页不计原件。根代理保留的3动作/6MB未占用。`retrieval.jsonl`保存URL、UTC时间、HTTP、原字节文件与SHA256，所有body保存在同目录；离线SHA复核另见`verification.json`。

日志分类更正：通用fetch包装在动作2、5、6把kind写成primary_original；实际动作2是主题query，动作5/6是纯ID元数据定位，**三者均非原论文正文**。不覆盖原请求日志；`retrieval_annotations.json`给出机器可读更正。所有题录只来自Crossref，没有用第二来源独立确认题名/日期/版本。

## 能改变后续核读优先级的证据

证据R=题录或参考文献；A=实际读完整摘要字段；P/F=实际读到方法/必要补充。**本轮P/F为0**。以下位置是保存响应内精确JSON pointer，不能当作论文Methods位置。

| 文献与身份 | 实际已读位置/等级 | 对E.v1哪一箭头构成先例警报 | 尚不能判定 |
|---|---|---|---|
| *The Derivation of a Matched Molecular Pairs Based ADME/Tox Knowledge Base for Compound Optimization* (2020), DOI 10.1021/acs.jcim.0c00583 | q3_crossref.body `/message/items/51/abstract`，A | 摘要明说将描述同一结构变化的多个MMP汇总为一个Transform进行预测，统计汇总、多个ADME/Tox assay、根据库自动suggest improved compounds。共享edit增量→推荐分子这一骨架已是很近先例，不能把单纯共享θ和建议analog当新机制。 | 是否同时估计两细胞匹配物理剂量下的ΔS；是否反馈触发适用域拆分；是否实际有同信息预算下的序贯query/付费观测；public cell/dose/time/control/repeats均未核。不能据摘要认定完整循环已覆盖。 |
| *Chemical rules for optimization of chemical mutagenicity via matched molecular pairs analysis and machine learning methods* (2023), DOI 10.1186/s13321-023-00707-x | q3_crossref.body `/message/items/54/abstract`，A | 摘要明说8576 compounds的Ames数据导出变换规则，以模型及applicability domain评估规则generalizability，且attachment局部化学环境对成功关键。因此“共享规则只在结构局部环境适用”已是近先例，不能把结构条件限制本身当新。 | 摘要不是反馈驱动的规则修订算法；不是两细胞相同dose/time的连续功能ΔS证据。未核实际适用域计算、数据开放程度、重复、query成本。 |
| *Hierarchical Analysis of Bioactive Matched Molecular Pairs, Encoded Chemical Transformations, and Associated Substructures* (2016), DOI 10.1002/minf.201600092 | q3_crossref.body `/message/items/1/abstract`，A | MMP→transformation→substructure层级；摘要报告多数transform仅关联单一MMP，近半substructure只组成single-target transformations。它使“普通菜单是否真有重复编辑跨母体支持”成为优先资格门，不能把全库结构数量当可迁移支持。 | 这是该文数据的摘要结论，不能转写成本轮GDSC/AZ实测统计；没有核本候选细胞、剂量、时间或噪声条件。 |
| *MMP2Mol: a matched molecular pairs-based framework for ligand-based de novo drug design* (Crossref日期2026-09-01), DOI 10.1093/bib/bbag548 | q3_crossref.body `/message/items/36/abstract`，A | 摘要给出target-specific SAR transformations→prioritized transformations生成virtual focused library→CLM fine-tuning→target-relevant molecule generation。2026已有具体MMP引导生成/优化工作；E.v1不能把MMP+模型+选择泛称新。 | 摘要目标为新分子生成，评价含validity/uniqueness/novelty等；本候选为已有菜单、真实功能四观测、跨母体未查询analog选择。正文未读，不能说该文没有两细胞ΔS/反馈更新/query，只能说**摘要未认证**这些箭头。新合成/成本/public匹配endpoint unknown。 |
| *Prospective Prediction of Antitarget Activity by Matched Molecular Pairs Analysis* (2012), DOI 10.1002/minf.201200020 | q3_crossref.body `/message/items/6/abstract`，A | 摘要同时谈aggregate multiple transformations、绝对性质预测、novel entities和antitarget activity；提示多目标/反靶点与MMP并非新组合。 | antitarget不是自动正常细胞，也不是已核的T/R同dose/time差值。MMP统计、前瞻实验/合成成本、反馈循环以及cell functional endpoints需正文；本轮没有。 |
| *Nonadditivity in public and inhouse data: implications for drug design* (2021), DOI 10.1186/s13321-021-00525-z | q3_crossref.body `/message/items/7/reference/` 中 DOI=该值的条目，R；其Springer正文请求303 | 是应核的决定性nonadditivity原论文，题名/作者由2022论文参考文献返回；未读摘要/方法。 | **不能**根据题名声称该文使用哪种square、误差模型、cell matching、支持度或主动查询，更不能声称已覆盖/未覆盖E.v1。此项原件核读失败。 |

所列摘要字段原样保留于query body；`evidence_extracts.json`另存明确标为派生的身份/摘要与JSON位置，不把派生文件伪称原件。DOI网页身份均未用第二来源确认。2014 *Prediction-driven matched molecular pairs to interpret QSARs and aid the molecular optimization process*, DOI 10.1186/s13321-014-0048-0；2014 *Prediction of Compound Potency Changes in Matched Molecular Pairs Using Support Vector Regression*, DOI 10.1021/ci5003944；2017 *Coupling Matched Molecular Pairs with Machine Learning for Virtual Compound Optimization*, DOI 10.1021/acs.jcim.7b00298，此处仅R级题录，不能引用为方法覆盖。

## 对比本身与真正未决项

以下是直接代数分析，**不是已完成经典原论文核验**。E.v1的ΔS可写为 `[y(T,d')−y(R,d')]−[y(T,d)−y(R,d)]`，是drug edit×cell background的二阶交互对比。把两个factor改为两个化学变换，可构造四化合物square的同型差分。代数同型不能说明因子语义、测量合同、共享条件或跨母体迁移相同：E.v1的四项是两个分子×两个细胞，常规两个化学编辑的square则可能是四个分子×一个endpoint；E.v1还要求另一个母体上的同edit，以测试跨母体传播。经典nonadditivity原文未读，不能将此一般区分指定为那篇论文的实际设定。

本轮**未认证任何文献存在合格public matched cell×drug×physical-dose×time×endpoint×repeat矩形**。摘要中的public数据库、Ames compounds、assay sets或多个targets都不足以通过资格门；反过来，没有核到这些字段也不证明数据不存在。无数据下载和作者代码执行，因此也没有建立逐运算replay或成本等价。

能保留的具体研究问号仅是：在通过root结构/剂量/时间/重复资格门后，同edit的两细胞功能差增量能否跨母体预测，并在相同历史与成本下改变未查询已有analog的选择；条件化适用域/反馈拆分/query是否提供了强交互回归、层次模型与既有MMP transform系统之外的新增决策收益。它目前是待证问题，既不是算法创新结论，也不是已通过化学查新。

停止原因为7动作硬预算耗尽和合法原文访问缺口，不是检索饱和。若后续另行准入，仅需补足2020 Transform库、2023结构适用域、2021 nonadditivity的合法原文方法及必要补充，再核一个直接cell-selectivity/序贯MMP最近先例；需逐一定位更新规则、query效用、目标/参照与dose/time/replicate合同。2025–2026主题查询与完整原件覆盖保持unknown，不能为本轮制造Not found或Done标签。
