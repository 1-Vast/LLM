# 来源、实际阅读与数据边界

2026-10-29。本文件按实际原件/局部阅读记录，不认证完整领域优先权。身份由原Atom题名/arXiv ID与HTML题名相配；SHIFT按原PubMed文章节点，只读该文PubmedData/ArticleIdList，不把参考文献的标识混入本体。

## 新原文
- Mixed Signals: Understanding Model Disagreement in Multimodal Empathy Detection，arXiv2505.13979v3；Atom首发2025-05-20，非v3更新时间或正式接受日。原件sources/p1_mixedsignals_2505.13979v3.html，234176B，SHA256 6791f3a3589c0e60efb8ed839109d8ff35c26c3e68c696a4dbad33d77b04f90b。root核S3实验设置、3.2熵、S4 annotation/results；reviewer读S3/S4及表。S4按四象限抽204例，由作者和外部标注者两人标注。分歧象限是观察性分析，不是随机付费获取实验。原文链接 https://github.com/mayasrikm/multimodal-empathy-disagreement 仅登记not_verified，未取得commit/许可/源码。
- Multi-level Conflict-Aware Network for Multi-modal Sentiment Analysis，arXiv2502.09675v1；Atom首发2025-02-13。原件sources/p2_mcan_2502.09675v1.html，183840B，SHA256 c10e894a54c8180b6407f17c1645290776239a5220279d9d6401a829f126c7e4。root读2.2、E7–10、3.1，reviewer补2.1/E1–10。E8/9是输出平方差，E10以+β加入，3.1给β=1e-3；只能指出该项与“encourage distinct predictions”字面方向不一致，未核作者实际实现。两篇正式venue未核，不称录用顶会论文。
- reading_extracts.json只是标准库解析助读，原HTML/MathML alttext和方程ID为依据；未执行论文代码、图像模型或复现实验。

## 目标域原始来源
- DrEval，10.1038/s41467-026-72903-w，已有原JATS research/2026-10-27-direction-mechanism-expansion/primary/PMC13168506.xml。root本轮完整读Par24/44并读Sec5/Par19局部；reviewer读Sec5/14/16/18。未见药LDO不显著胜均值效应是所测模型/数据/设置的原文结论，不是对paid-pilot或所有结构方法的否证。Sec18明确GDSC已有SMILES/PubChem来源；不认证本地表具体join键。
- 固定官方代码reference/code/daisybio-drevalpy/c5a7274e9c84/drevalpy/models/utils.py:178–207，root读完整load_drug_fingerprint_features；源码全NaN/部分NaN分支和默认fill_na行为已核，缺失数量和真实运行使用未核。datasets/loader.py:91–107的_frame_to_dataset只发出response、cell_line_ids、drug_ids、tissues、dataset_name；不由接口缺字段推整个上游无原始数据。
- DRP，10.1093/bioinformatics/btag293；已有XML reference/papers/doi-10.1093-bioinformatics-btag293/supp-P2_drp2026.xml实际是文章主文而非SI。root本轮读MACCS、QSAR及223参考药/157候选库工作流的Methods/3.3对应段；reviewer完整读2 Methods、3.1/3.3。固定面板/QSAR生成值不能当免费新实测。
- Training distribution determines the ceiling of drug-blind cancer sensitivity prediction，arXiv2605.20885，已有库原HTML。root本轮直接读Methods Sx5.SSx5.p1.1（response matching）；reviewer范围见其报告。K个pilot后Pearson top5/负相关零权/CV混合、无需训练为原文方法；K1相关不定义为数学限定，不证明所有少量测量迁移失败。
- SHIFT-DRP，DOI10.1021/acs.jcim.5c02453、PMID41392432。原摘要/作者/日期来自sources/q4_selected_pubmed_abstracts.xml指定文章；电子2025-12-14，期刊issue2026-01-12，不能笼统只写“2026首发”。正文ACS full URL403；SemanticScholar DOI查询返回同题/DOI，openAccessPdf.url为空。其year2025与电子日期一致，不作期刊年份冲突。摘要报告动态采样、cross-attention、四数据集、24%资源节省；未核全文、代码、公式、真实成本与统计，不将该数采纳为本地或独立验证效果。
- Science adi8577在本次PubMed结果中再次出现；已有库PDF和此前阅读保留，本轮未新增读该PDF，不把摘要重新出现计为新原文方法核读。

## 获取与检索覆盖
retrieval.jsonl保留每次精确URL、开始UTC、成功字节/SHA或错误。9次动作中4次主题query；7成功共708101B，两新原HTML418016B。单文件8MB、总25MB、30s、0自动重试；底层重定向数未测。q1 EuropePMC药物结构×few-shot/active/in-context返回503；q2 arXiv多模态conflict/complementarity返回前10/66；q3 drug-function-structure返回1/1（DeepDTF，标题/摘要层筛查，未核其多组学方法）；q4 PubMed2025–2026药物×active/cell-line-selection/design返回12/22，再一次批量efetch取该12篇原记录。无进一步主题扩展，未翻完余页。

## 数据只读边界及独立性
本轮GDSC CSV只用csv.reader读第一行表头；没有消耗任何响应值，metadata_audit/freeze只核键名。未读sealing/confirmation/PRISM24Q2/CTRP响应，不读.env。当前拟合表可支持受限标签探索；其独立重复/原始剂量/处理时长是否另可取得仍未知，不因该表缺列判整个资源不存在。

INDEX以207表行扫描，8条主题定向命中，并读R140与C4报告相关段，不称逐篇重审207轮。上一轮8pass、Harness8calls保留，本轮3pass+1call追加。中性scout先形成问题但其初稿落盘前收到了root数据/源码补充，暴露时序见原稿；fresh challenger只给候选与原文，初判先保存后才收到SHIFT摘要，不读scout/旧数值。来源阅读和角色意见不是独立生物确认。

DS017只接四段来源packet，主Agent独立核字节/quote/实际源码；main_review与canonical_fields保留接受及拒收字段。帧中无单位/时间字段不是实证单位缺失。没有新科学实验或模型API重试。
