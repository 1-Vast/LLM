# Replogle独立生长预测：状态文件已取得，功能配对仍未认证

2026-10-22。完整目标ACTIVE / NOT_ACHIEVED。本轮PROGRESS：从真实一手论文到作者浏览器、正式Figshare manifest、实际raw-pseudobulk下载与哈希/结构认证，建立了此前未运行的不同能力入口。没有新增生物预测指标、更新规则或RSI成功。

## 具体应用与研究主张

应用为癌细胞遗传靶点功能评估：在K562中，已测CRISPRi扰动表达状态能否增加对独立bulk CRISPRi生长表型的预测信息。第一问题是付费实测状态的静态跨基因预测，不是新癌背景泛化、未测状态模拟、药物临床效力、继承或RSI。既有作者已报告表达响应强度与生长相关，故简单相关性不能构成创新。

本地独立历史审计见biology/HISTORY.md：旧PRESAGE确实有Replogle表达加载代码，但已执行P0为PRISM药物/pathwayadapter，没有找到原2022状态→独立bulk功能增量的执行记录。旧PRESAGE及其他scoped STOP不重启；不把Replogle-Nadig换成原2022而假装已复现。

## 一手设计与实际输入证据

Replogle et al., Cell2022，DOI10.1016/j.cell.2022.05.013，官方PMC9380471 XML HTTP200。K562的growth为独立dual-sgRNA gDNA screen，非单细胞capture数量；作者在文库合成时按growth调整表示，guide选择也使用过历史growth，因此历史先验/丰度通道必须公平控制。Methods day7→17与FigS1 day6→16冲突不静默解决，首试可限定静态关系。

RPE1growth用KOX1 KRAB、Perturb-seq用ZIM3，growth时间/计分尺度又不同。不能直接把K562/RPE1当相同接口的独立后来任务或用raw gamma差称癌选择性。

作者browser真实可访问。通过public Dash只读导航取得正式Figshare链接：processed20029387v1、additional21632564v1、sequencing20022944v2。未调用表达heatmap/guide-scatter的数值callback。UI默认construct名属于公开设计文字暴露，不是本阶段筛选出的响应子群。

按事前SCHEMA_ACCESS实际下载K562_gwps_raw_bulk_01.h5ad：374587922bytes，MD54570b53c9d62ff6df281e622f0350060与正式manifest一致，SHA2567cec96b3b76169abbf6b6ab9d10bf00d71d942d89e63292351f745e130b154db。只查看HDF5 keys/shapes/dtypes：X11258×8248；未解码X、obs数值或行ID。文件物理含全队列状态，已下载不冒称从未接触该artifact。raw_bulk是作者处理/聚合后文件，非原始reads。

## 功能入口的实质未决点与访问失败

已列HDF5字段没有明确gamma/growth字段；这不是证明所有文件/属性都没有功能结果。Additional annotated_embedding_coordinates.csv也已按manifest下载并核MD5，只读取header，含embedding坐标、细胞数/UMI/fold_expr/DEG数而无gamma；不把这些状态/QC字段替代独立growth。

原文补充工作簿NIHMS1812939-supplement-11.xlsx的PMC直链HTTP403，保存的同名文件实际是134byte HTML错误，不可当Excel载入。EuropePMC官方supplementaryFiles HTTP200但只返回162byte ZIP，其中只有一个0byte jpg，无工作簿；不按HTTP200误报已取得补表。NCBI旧OA manifest endpointHTTP404，未提供package链接。正式sequencing20022944仅给scRNA lane/gemgroup manifest，不提供已认证growth表。没有下载数GB单细胞或改用DepMap cached embedding补救。

独立bulk gamma数值表、construct→gene/TSS键、缺失/重复/打分来源尚未认证。因此本轮不能读数训练。保存公开状态文件是实质资产进展，不等于状态—功能配对完成。

## 独立审查、实际交叉与最小实验条件

biology和skeptic先分别封存历史/风险与一手SOURCE_INDEPENDENT，再双向质询，保留原稿与CROSS。共识为CONDITIONAL_GO_FOR_BOUNDED_K562_FUNCTION_PAYLOAD_QUALIFICATION；STATE_ARTIFACT_SCHEMA_VERIFIED；FUNCTION_PAYLOAD_AND_JOIN_PENDING；NOT_RUN。不是性能FAILED，也未晋升创新机制。

取得功能表后，先冻结允许字段/分组/目标及主门再开值。按gene合并全部TSS/construct分组，不能随机拆guide泄漏同gene。最低强对照包括可实际获得的历史growth/essentiality与guide先验、counts/UMI的普通直接模型、简单响应强度、RNA正则化/低秩直接预测、简单fusion，以及等预算正则化非线性直接对手。所有实际可观测prior公平给各方法；未知annotation如实列限制，不无限要求恢复全部DepMap/guide历史才准小试。

不能把obs全部称nuisance：DEG/energy/leverage/TE/CNV是状态派生summary；control_expr/fold_expr须核语义。不得用旧PRESAGE知识cache，因其中可能嵌入DepMap功能标签。Published >0.01UMI feature universe使用全队列无标签信息，允许首试明确retrospective/transductive固定特征空间；新学的归一化/降维/调参依然train-only，不能宣称严格新队列inductive验证。

成功/停止门尚不能在缺少精确功能尺度、缺失/重复定义时伪定。后续协议须预先指定实际端点、效用门与普通对手；若同信息强direct解释全部收益，则只保留普通能力结果，不加WM/agent/editor层追分。完整WM/agent/继承/联合/improved-improver仍需分别实证。

## 另一较新来源及资源

已识别16癌line预印本的canonicalHTML本轮一次请求仍HTTP429，Retry-After10；未读正文，也未立即循环重试。此前早期JATS429/EuropePMC500保存不变。暂无匹配fitness/payload结论，不用其摘要替代2025–2026方法新颖性研究。

本轮16次HTTP，含两次public Dash只读导航POST、一次375MB状态下载和一次229476byteannotation下载。结果13×200、1×429、1×403、1×404；其中supplement ZIP200无工作簿。0fit、0模型API调用、0新湿实验、0响应数值解码。原生代理实际执行；token/金额未暴露。代码仅research/multi_context_state_function_20261022/，记录/文件仅本目录。历史provenance问题未因本地哈希通过而修复。
