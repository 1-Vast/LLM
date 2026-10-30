# 原始来源核验（Pass 2）

2026-10-26。问题：旧重复/阶段门槛能否由真实设计解除。新搜索：

1. `site.nature.com "s41467-024-55287-7" replicates`
2. `site.zenodo.org/records/13871987 "PAIR_SCREEN"`
3. `site.nature.com PRISM repurposing MTS010 technical replicates ComBat Corsello`

后续仅打开这些资源。Nature的open认证跳转、PMC检查页均停止；改从独立公开Europe PMC API取得同文题录/XML，题名、DOI、PMID/PMCID一致。原始XML与URL/字节数/SHA256 receipt在sources/。

## P006 BATCHIE

[正式论文](https://doi.org/10.1038/s41467-024-55287-7)、[Europe PMC](https://europepmc.org/articles/PMC11696745)。题录firstPublicationDate=2025-01-02，PMID39746987。DOI中的024不是发表年。

读取P级：方法Pediatric sarcoma combination screen/Study design、Wetlab protocols/Cell viability assay、random validation结果/Fig6、Gene expression and CRISPR knockout analysis；未复核全部证明、图和补充。用XML的sec/title和段首定位。

1—10轮单板，11—15轮duplicate，重复差>0.5被QC标记。正文称independent duplicates，支持重复设计，尚未认证CSV file到独立培养来源。QC含响应差异，不能作为前瞻免费已知的动作资格。随机验证另采剩余plate；DepMap AURKA knockout用于合理性分析，不等于本候选匹配的正交识别。Wetlab写药物孵育72h，再加Alamar Blue孵育24h；不能说原文没有时间，也不能自动外推全部validation子协议。动作按细胞和row/column plate成批。PDBAL及TI-aware设计是直接药物先例。

## P007 PRISM

[官方19Q4](https://doi.org/10.6084/m9.figshare.9393293)，两份raw readme和design CSV由audit.py固定hash。读secondary readme全文，未加载响应矩阵。MTS010是147种药技术重做；replicate logfold change经过逐treatment ComBat。E001发现2.5μM有1281完整批次ID对齐，不能笼统以secondary剂量不同否决；仍需核培养/时间、缺测模式和参与参照。568只是STR metadata身份交集，不是实际实验规模。

## 影响下一决定的观测

BATCHIE随机验证按原始药名、剂量且忽略A+B/B+A方向的键，有15个与1—15轮重叠；名单见validation_overlap_keys.csv。没有做结构/盐型/同义词归一，15不是化学实体最终去重数。该阶段相对全训练没有新药/细胞标签。需核plate索引、重复库槽位、身份和QC，不能直接断言论文错误。拟合前必须先解释/排除重叠并冻结终点；现阶段不支持规则/Agent/迁移收益。
