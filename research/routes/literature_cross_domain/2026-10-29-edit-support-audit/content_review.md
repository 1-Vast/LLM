# 初次独立内容审阅

2026-10-29。审阅者未参与本轮协议、实现、检索或报告开发。Requested Sol/high；effective model/effort、provider usage、实付未知。本次仅核对派生证据与相应来源台账，没有运行任何脚本、联网、调用Harness、增加代理或修改核心。

## 初次结论

在实际允许核读的证据范围内，**未发现会推翻当前“暂缓E.v1药效实验与新算法推荐、总目标仍未达成”决定的实质科学错误**。报告没有把可映射子集的零边写成完整药物菜单的化学阴性，没有隐瞒独立原输入复算失败，也没有把DS025预置字段抄录升格为独立科学验证。这个结论是对解释和证据等级的内容核对，绝不是主计数的独立确认、化学查新完成或测量资格通过。

初读发现两项需要最终归档澄清的记账问题，见下文。没有发现新的药效、机制、泛化、独立决策收益证据。

## 逐条问题

1. **报告对pass与执行次数的措辞存在歧义。** `report.md:56`先称本轮两个pass耗尽，随后称“主审计和失败独立审计各耗用一次”；而`budget_usage.json:9-12`把主审计与失败独立复算共同列为一个pass outcome，化学检索列为另一个。按账本可以理解为“结构支持pass内的主执行额度、独立复算额度各用一次，加上化学先例pass，共两pass”，但报告原句可能被读为两次执行已经各占一个pass，化学检索又是第三个。建议明确区分两pass与结构支持pass中的两次执行，保留失败也消耗独立复算额度、零重试的事实。这是统计口径表述问题，现有材料不足以指控超额执行。

2. **最终代理账本尚未纳入本次内容审阅。** 审阅时`budget_usage.json:71-75`仅列化学先例和独立重写两位requested native agents。本次内容审阅已实际发生，最终归档宜追加本审阅角色及requested/effective未知边界，避免把这个快照称为本轮所有代理的完整实际账。无需把本次只读审阅伪记为新的化学/数据探索pass，也不能凭requested型号推断effective或费用。

以上两项均不使当前科学结论变成阳性或阴性结果。未发现需要改写成“完整公共数据已否定E.v1”“已有化学方法已完全覆盖E.v1”或“新算法已成立”的证据。

## 重点核对与证据等级

| 核对项 | 实际证据及解释 | 审阅判断 |
|---|---|---|
| 零边与化学阴性 | `primary_mapping.json`列11个ID，其中Olaparib admitted、10个no_exact_chemical_match；`primary_summary.json`列1个规范分子、0边、0跨母体组；报告17-21行明确是小表覆盖不足 | 给定这些派生输出，一分子不能形成两分子编辑是直接逻辑结果；不能证明其余10药无公开结构或完整菜单没有合格编辑。报告守住了这一界限。精确名称连接也未被写成实物身份认证。 |
| 主计数与工程准入 | 主summary、mapping与报告列出的行数/身份/分子/边计数相符；两个admission均明确engineering-only且outcome_or_algorithm_qualification=false | 准入、合成H→CH3检查、文件存在和hash只能支持工程/来源记录，不能认证真实结构计数，更不能认证效应。本审阅未重新计算1013803、733、8058、22239等原输入计数。 |
| 独立复算失败 | `independent_execution.json`为failed、exit1、wall0.781s；`independent_review.md`解释GDSC007与GDSC_007谓词不匹配，并明确没有生成真实well/结构/支持计数；报告29-31行完整披露 | 不存在独立原输入结果一致性证据。内容审阅无法填补该缺口。具体失败前读到什么、为何退出，在本次范围内依据冻结实施者诊断与执行回执，而非我重新读原ZIP或执行代码确认。 |
| 单药参照与真实孔 | DS025 packet中的glossary全文明确libN_drug是拟合单药比较曲线所用标识，treatment在该文件alwaysC，libN_conc为µM，libN_x为normalized max9；报告23行相应限定 | 单药曲线参照字段不是独立单药源well证明；项目/细胞模型ID也不是独立培养重复。记录只支持身份/物理剂量机会，尚无time/endpoint/control/source-well/独立培养或未暴露资格。报告没有用它们补出四项真实可比单药测量。 |
| 化学先例与2025—2026覆盖 | chemical_prior来源ledger有7动作，仅Crossref两项200；近期EPMC503、正文尝试303/403；annotations纠正了三项kind误标。报告35行与chemical_prior明确本轮新方法P/F=0 | 不能称2025—2026精确最近先例已查全；检索失败不是无先例。2026 MMP2Mol仅是Crossref摘要级先例警报，不能由“摘要未认证”推出正文未做某箭头。报告已如此限定。 |
| 已有摘要的科学用途 | 派生evidence_extracts中2020摘要确实描述汇总多个MMP为Transform并自动建议化合物；2023摘要确实强调attachment局部环境；2016摘要的single-MMP结论限定于该研究数据 | 这些内容足以反对把泛称的共享变换、局部适用域、分子建议直接当作新机制；不足以认定本稿固定剂量两细胞差分、跨母体传播与同成本序贯选择已被某文完整覆盖。本次未打开原论文正文或Crossref原响应body，不将派生摘要抄录认证为原文方法核读。 |
| 二阶差分与非加性 | chemical_prior给出两分子×两细胞差分的代数表达，并与两个化学编辑的四分子square区分；报告44行拒绝由代数同型推出细胞算子不对易 | 这个代数/语义区分成立；不是对尚未读到的nonadditivity原论文方法的确认，也没有提供额外算法差异或因果机制。 |
| DS025 | packet预置九行的kind、unit、quote、boundary；final逐项照录并另给六项ambiguity；format_checks与main_review只采纳54个固定字段，明确scientific_validation=false | boundary不是模型独立发现。F8完整packet原文已有max9，F4已有monotherapy curve-fitting目的，F5未说明stock/dilution不能否定既定µM或猜配液。报告与验收均未采纳这些过短quote引出的注释为新测量条件。 |

## 预算逐项相符程度

从两个来源ledger直接数出化学7动作、root metadata 2动作，共9个逻辑动作；主题query为3。成功body为52420+547820+40475=640715B；全部保存body为606502+8102+40475=655079B；最大547820B，与`budget_usage.json`一致。化学ledger原始kind误标已由annotations纠正，未把题录/ID定位当成正文成功。根metadata 410不是结构来源，200的40,475B是小型元数据下载。存在redirect后的final URL，因此逻辑动作数不能替代底层HTTP请求数，后者保留null是适当的。

primary/independent两份execution回执中的wall、采样CPU/RSS与总账一致；采样内存守卫不是OS硬配额，回执已明示。主审计19.344s与失败独立审计0.781s均在所列资源门内，但本审阅没有检查wrapper或重新运行，不能独立证明实际未访问任何非白名单值。

DS025 usage中的1838 input+612 output+256 cache-read=2706 reported total，与预算及报告相符。实际后端、底层请求次数、实付、0.025美元硬上限验证均没有证实；账本保留unknown/false，没有伪称已控费。一次pre-model预检失败与模型重试被分开记账。历史29 pass、此前16次Harness调用，以及DS025原始事件数/隔离进程事实不在本审阅所读原事件范围内；这里核到的是账内算术与派生回执一致，不能宣称已独立核实全部历史调用。

## 实际覆盖与无法确认项

已读：本目录report、canonical support_protocol、primary_summary、primary_mapping、两份admission、两份execution、independent_review、chemical_prior、budget_usage；chemical_prior的retrieval、annotations、verification、evidence_extracts；root_metadata的retrieval；DS025的source_packet、final、main_review、format_checks、usage。首次合并工具输出发生截断后，已分开补读chemical_prior、预算、独立review后半与report开头，不依赖被截断段作结论。

未读原ZIP、原matrix、原parquet/metadata body、原well响应、任何.env、PRISM24Q2、CTRP、sealed/confirmation、新网络响应；未读或执行主/独立脚本；未重开glossary PDF或论文原件。未查前轮报告、冻结候选全文或旧reference库，所以报告关于前轮11件原文、普通模型逐步对应、123来源/108论文/10代码关联9篇、历史预算的陈述仅作为明确的外部依赖，未获本次重新确认。无本轮实证支持的算法优越性、机制、功效、置信区间或预算节省结论可由本审阅产生。

本次只写本文件，不改主报告或总账。维持`independent_recompute_incomplete`、`full_measurement_qualification_unknown`、本轮新方法P/F=0以及`ACTIVE_NOT_ACHIEVED`；后续任何更强结论仍需分别补足结构覆盖、独立复算、真实测量合同、最近先例方法原文及同信息同成本决策证据。
