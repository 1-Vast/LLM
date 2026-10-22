# Bounded independent NCBI primary-lead scout

2026-10-22，Asia/Shanghai，请求前登记。当前Root两次EuropePMC503为传输失败，不代表没有研究。本独立区块只使用官方NCBI EUtils及其明确引用的官方availability身份，最多4 GET；每响应body最多2,000,000bytes；不retry、不跟redirect、不请求作者、不下载FASTQ/响应矩阵/补充工作簿。每次顺序singlewriter，保存URL/status/UTC/body bytes/SHA256/exception，包括所有失败；拒绝覆盖。无API credential。

范围：2024-01-01至2026-10-22，抗生素实验演化中真实sequential/switching/cycling/longitudinal，优先多selection drugs/tasks及公开状态+功能来源。明确排除已查LIST/Jeong(PMID41278959)、Tripartite(PMID40478208)、chemicalgen(PMID39623067)，不重开历史STOP。

第一GET PubMed ESearch，明确query、retmax10、relevance；第二GET最多同10条PubMed EFetch abstracts及bibliographic IDs。最多2次余量，只对最有希望的一条查官方可用性/身份；若无可信新lead则停止，不消耗次数凑结果。摘要只支持abstract-level claims；PMCID存在不等于fullmethods或数据资格。全文如可取得，仅投影方法/availability；公开题名、作者、gene/drug设计名不遮蔽，所有阅读明确为literature/designer-exposed，作者性能不当本项目结果。

成功：给出一条未查过的真实primary lead，准确区分已证设计、公开状态/功能身份与具体join缺口。若只有摘要线索或失败，按访问层级报告；不得把sourcefind当创新，也不启动模型。所有代码只research/dynamic_source_followup_20261022/，所有数据/失败/决策只本日志目录；maestro python -B。
