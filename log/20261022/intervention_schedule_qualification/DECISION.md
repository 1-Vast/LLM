# 真实药物时序资产资格：两项候选仍未认证完整可执行菜单

2026-10-22，Asia/Shanghai。上一阶段已独立评审并关闭单eta时钟修正核心（见`../tggates_functional_qualification/DECISION.md`）。本阶段实际取得了新的来源与样本条件证据，改变了后续行动，属于PROGRESS；没有把文献、数据资格或软件测试算作世界模型/RSI成果。总目标继续ACTIVE/NOT_ACHIEVED，未完成的归因实验不能改称已完成。

## Lee2012：分子存档已核清，但不是已认证的多药序菜单

支持方通过官方PubMed→GEO链接认证GSE30516；独立数据代理进一步核全部25个GSM的brief metadata。**25个都是10µM erlotinib单药后转录采样**：BT20 0/0.5/6/24h，MDA-MB-453 0/24h，字面MCF 0/24h。未认证MCF亚型、独立培养或0h vehicle对照；没有第二药/正反序/同步给药的sample标签，25个补充链接均CEL.gz。Homo sapiens/GPL570与hyb protocol里的Drosophila Genome Array文字冲突被保留，没有擅改。

**停止把GSE30516单独指定为完整药序世界模型/Agent/RSI基准。** 这不推翻原论文药序效应，也不证明论文其他附件没有功能表。详细证据、9个不同合成检查及229项身份/hash验证在`REPORT_IDENTITY.md`。首次family全XML请求耗尽2MB但没有取得sample metadata，未发原计划后续请求；单独事前修订后，brief sample-only请求57,292 bytes成功。两次合计2,057,292 bytes，原失败、修订、前缀安全截断与原8文件冻结均记录。

## 抗生素微流控：有真实干预摘要，但方法/数据manifest尚未认证

根代理PubMed替代查询实际返回46项，只读取最新20篇的作者记录；2请求442,043 bytes，见`ROOT_SEARCH_REPORT.md`。其中 [Massively multiplexed microfluidics maps combinatorial and sequential antibiotic responses in 3D](https://doi.org/10.1101/2025.10.30.684665)，PMID41278959、PMC12636614，前文metadata实际epub为2025-10-31，为真实同步/顺序给药和图像状态/生长终点提供线索。512 chambers、10,000 colonies、2,700 dose combinations均为作者摘要数字，不是本项目已核独立任务数。

该单源的后续资格与独立反方记录位于`../antibiotic_schedule_qualification/`。原3请求分别EPMC500、NCBI200但仅front/abstract并注明publisher不允许fulltextXML、bioRxiv429；没有重试/绕过。随后独立预登记2个data-registry精确DOI关联查询，DataCite及Zenodo均200/零项。五次请求共19,943 bytes。**EXACT_INTERVENTION_STATE_FUNCTION_MENU_NOT_QUALIFIED**：尚没有公开data/code linkage、菌株/给药时间和剂量/腔及run键/状态时点及growth frame的认证。限定DOI检索零项不等于公开数据不存在，不等于只upon-request。

若未来取得源，应用应明确为3D细菌微菌落抗菌给药研究，不能称PHH或临床疗效，也不能把菌落图像模型自动等同完整分子虚拟单细胞。独立反方提出的必要对照包括early size+slope/growth-only预测、相同早期image信息直接schedule predictor、普通curve/dynamics refit与主动查询。相同图像流**并非天然泄漏**：严格提前的state可合法预测未来growth；但未来frame、全轨迹tracking/normalization或同终点面积伪装输入会泄漏，须先核时间与预处理。必须按chamber/run/strain等真实干预单位评估，不能把共处理colonies当独立task。

保留关键设计边界：完整静态schedule表可以支持跨实验的query→模型更新→下次实验选择replay，**不必强制要求同一个菌落内的自适应动作**。只有要声称同菌落根据state选择第二药时，才另需共同prefix的实际替代分支和覆盖。不能通过加入过强的数据先决条件把本来合法的科学agent任务拒之门外；也不能用缺失schedule的模型模拟充当实测反事实裁判。

## 实际失败与下一次执行

独立补充文献搜索初始6请求均EPMC503，首次脚本未保留error body，字节未知；事前修订允许的第7个简化诊断仍503，89-byte原始错误完整保留。结果是访问受限，非公开序贯资产缺乏的科学结论。根代理已用不同官方服务取得上面的真实新线索，没有因此把整个目标标为blocked。Lee来源还保留一次无效PubMedID字段查询及一次并行ledger覆盖的重建缺口，准确界定于`ADVOCATE_SOURCE_REPORT.md`。

下一次可执行动作是按**真实标题/作者而非仅DOI关联**在官方data/code registry或作者公开仓库定位该抗生素源的manifest；优先复用现有front/作者信息，不重复publisher429或把非全文200当全文。先登记具体查询及停止边界，得到manifest后只导出真实动作/时间/上下文identity，确认完整跨实验replay机会；若不能认证则关闭该资产配置并保留访问限制。当前不批准以摘要先搭新模型或编造缺失功能矩阵。没有向作者发消息，也未授权后续代理发外部消息。

完整总目标仍未完成：本轮没有真实响应值开放、拟合、功能决策性能、世界模型/智能体分离、继承收益、联合收益或共同起点meta改进效率。强直接、普通重训练、持续学习、主动学习、简单混合和等预算程序搜索仍须在合格资产上实际执行公平比较；来源可用性或理论反例不能代替它们。

所有新实验/测试代码仅在research，全部协议、原始来源、失败、冻结、审查和裁决在log。本轮源资格脚本及已有有意义检查均完成；不因未找到核心创新而宣布研究成功，也未暂停用户目标。
