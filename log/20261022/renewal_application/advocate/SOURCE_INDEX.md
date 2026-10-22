# 来源证据等级

本轮共4个HTTP请求；不得写成“已审查四篇一手论文”。`HTTP_RECEIPTS.jsonl`保留4个独立name/URL/UTC/body哈希，状态依次200/500/200/404。并发导致中间两条attempt均2，实际记录数与unique names均4；见WORK_AND_FAILURES。

| Body | 实际取得 | 可支持 | 不可支持 |
|---|---|---|---|
| epmc_scifate_search.body | EuropePMC题名索引200 | sci-fate原文身份/DOI/PMCID，索引有GEO标记 | 原文方法、药物与时间清单、可下载矩阵、重复独立性 |
| scifate_primary_xml.body | 500错误150bytes | 该次原文请求失败 | 原文不存在、数据不可获得、生物阴性 |
| epmc_dynamo_search.body | EuropePMC题名索引200 | Qiu等vector-field论文身份/DOI/PMCID，索引有GEO标记 | 已完成其更新算子的精确前驱比较 |
| scifate_ncbi_primary_xml.body | NCBI OA服务404错误1584bytes | 该次服务路径失败 | 取得原文XML、无数据、无OA |

四次额度耗尽，不再补抓第五次。独立稿的ordinarykineticrefit归约是对稿中明确方程的数学构造，不能伪写成已读dynamo原文后的文献等价结论。没有一份新的biological dataset在本轮被资格化。
