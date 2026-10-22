# 作者Title追加：前缀genome样本确有来源标签，前瞻总体评估仍未认证

2026-10-22，Asia/Shanghai。独立反方`scientific_skeptic`。已实际读取`biosample_identity_followup/TITLE_SCOPE_AMENDMENT.md`及`TITLE_LABELS.json`，仅使用其获准导出的author categorical title、accession和sample alias；不读取原始XML其他字段、基因组、MIC/fitness/mutation测量或序列。无新HTTP、数字化或模型。

**此证据必须修正“全是终点genome/没有前缀genome”的过度概括。** 作者明确为多个干预前缀分别登记了样本；不能因为Title同时带resensitized终点分组，就抹掉这些前缀样本的存在。另一方面，来源标签认证不自动使它们成为无选择偏差、免费、前瞻可用的模型输入，也不自动建立图表行级join。

## 本次能够精确认定什么

获准Title中有以下结构：

| 作者分类及prefix | 独立accession数量 | 能认证的最窄来源事实 |
|---|---:|---|
| `GEN_resensitized` × `GEN`、`GEN-PIP`、`GEN-PIP-NIT` × `strain_1..3` | 9 | 成功终点分类下有三种前缀各三个作者命名样本。 |
| `GEN_resensitization_failed` ×同三前缀× `strain_1..3` | 9 | 失败终点分类下也有三种前缀各三个作者命名样本。 |
| `NIT_resensitized` × `GEN-PIP-NIT-GEN` × `strain_1..3` | 3 | 另有第四药物阶段的作者分类样本；不能当仅三步loop终点。 |

前三前缀的两分类各三编号构成**六条名义chain、十八个stage样本**的清晰作者命名结构。Title重复的strain编号和prefix支持这个来源级对应解释；尚未由培养/cryostock/ancestor键独立认证它们确为无换样、无重试替换的纵向lineages。因此本报告保留“名义”限定，不把图上strain1直接等同Title的strain1。

额外三个四步样本可能与前三步某些chain有关，但仅凭名称与alias数字不能认证其母系连接或当成三个新独立任务。本次修订明确禁止从PN/GR/FR/NG代码或末位数字反推FigureS1 row。**21 accessions不是21 tasks；六名义chain也不是六独立生物背景。**

这是source-conditioned prefix identity的新增认证，不是本反方已读取genotype或证明每个样本的实际测序内容/质量。项目有genomic deposition，具体测序/变异payload仍未下载。

## 前缀存在与前瞻状态可用是两件事

可以合理说：该public source不是仅保存最终stage样本；作者为GEN及GEN-PIP等较早阶段登记了genome样本标签，因而存在潜在的retrospective prefix→terminal研究材料。不能继续因先前小白名单未导出Title而断言“没有早期样本”。

但以下事项没有因此被证明：

- 对一个**尚不知道最终结果的新lineage**，能否在决策cut之前取得、处理并返回相同genome状态；sample的处理、建库/测序时间、是否后期复苏选株、成本/延迟均未认证。过去stage被保存、事后测序可以支持回顾研究，却不等于当时决策者免费拥有结果。
- 三stage样本与S1F具体row的准确映射、每次SAGE/flat/first-try/second-chance对应、是否同祖先继承。Title strain号可能是作者对选样组重新编号，不能直接用作图表的1–16 row键。
- 未选样、灭绝、再尝试、不同loop/临床背景的genome覆盖。能认定的是选中的六名义chain结构，不能反推整个cohort每个stage都测了genome。

如果未来仅把早prefix测量值当固定已持有资产，可定义一个**条件于已获得这些测量**的回顾预测问题，不需要先证明实际采购比MIC便宜；但所有模型必须获得同样prefix信息，且结论不包含实时采购效率。若声称agent主动购买早genome节省后续evolution/功能查询，必须把测序成本、返回时延及真实信息cut纳入所有臂。

## 终点选样对可研究问题的影响

作者以`GEN_resensitized`或`GEN_resensitization_failed`分组样本；结合已公开补充图的选序圈，这不是一个未经终点选择的普通前瞻cohort。这个选择**不使较早prefix的基因组内容不存在或自动无效**，也不禁止研究同一选中chain的基因组随stage变化。它限制的是可估计的目标总体和评价结论。

最窄可接受方向是：六名义chain映射认证后，对选中成功/失败历史做**明确终点条件的回顾分子演化对照/机制假设生成**；或者在同样selected case-control样本内做极小的探索性prefix→terminal诊断，并诚实标为selected/designer-exposed。这样的分析不能直接估计普通新lineage成功率、总体校准、实验查询净效用或任意药序控制收益。按终点分类选样本可能人为改变类比例及其他条件；未知选样规则又会进一步限制class-conditional外推，不能只校正一个类别比例就声称消除全部选择偏差。

作为预测输入时，**作者Title中的未来resensitized/failed分类、其编码alias、由终点标记生成的组别都必须隔离**；它们可用于来源审核与分组，但不是早期cell state。只能用合法cut时可计算的测量/历史。反之，也不能因这些标签会泄漏就连合法prefix测量一并抛弃：应分开处理annotation和实际输入。

六名义chain内三个stage不能拆作十八个独立test examples来夸大泛化；同chain全部stage和任何四步后代须共同分组。当前数量不足以仅靠train/test重排认证跨药、跨背景、程序继承或m0/m1/m2改进策略；普通小样本描述价值仍可保留。任何leave-one-chain评估也只是选中chains内部探索，不能变回未经设计曝光的外部确认。

## 对任务状态的精确更新

`TASK_REVIEW.md`提出的public MIC-only fixed-loop预测机会保持；本次新增的是`AUTHOR_LABELLED_PREFIX_GENOMIC_SAMPLES_PRESENT / SELECTED_NOMINAL_CHAINS / FIGURE_ROW_AND_PROSPECTIVE_JOIN_NOT_ESTABLISHED`。

因此不能再使用不加限定的“only endpoint genomes”作为停止理由。若停止genome-conditioned总体预测或serial agent benchmark，真正缺的是：前缀→功能row/实际culture的精确关联、非选样或可限定的目标总体、决策cut/成本、合法备选action与独立任务。若只研究选中链的回顾机制变化，所需条件更窄，不应因缺全RSI被一票否决。

当前没有获准/执行sequence下载或模型拟合。本次来源身份进展不会改变state-refinement操作与普通MDLsplit同算子的既有新颖性STOP；它改变的是数据事实和未来可提出的有条件研究问题，而不是自动增加world/Agent/继承/RSI证据。
