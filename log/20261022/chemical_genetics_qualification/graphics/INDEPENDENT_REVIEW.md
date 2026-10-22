# 独立原图复核：公开genomic state确实存在，nominal匹配应保留限定

2026-10-22，Asia/Shanghai。独立反方`scientific_skeptic`。先读root登记的`GRAPHIC_SCOPE.md`、`INVENTORY.json`及其`VISUAL_REVIEW.md`，随后以`view_image(detail=original)`分别直接查看两张**完整**原始JPEG：

- Fig5：`41564_2024_1857_Fig5_HTML.jpg`，730×1087。
- ED5：`41564_2024_1857_Fig11_ESM.jpg`，787×1086。

无HTTP、剪裁/重绘、OCR、数字化、数组导出、FASTQ、训练或模型。本轮可见的所有数字、曲线、mutation annotations与作者分组均是**published/designer-exposed literature**，不再盲，不构成项目性能。

## 独立看见的状态证据

Fig5c明确展示**Lineage11**的三个同心时间环，旁标Day3、Day5、Day7；环上有按基因/等位变异注释定位的气泡，包含hldE、waaF等可读标签及其他注释。下方有mutation frequency气泡大小图例20%、50%、100%，以及genomic coordinate参照。它不是只有示意空白的机制图，而是公开展示了该lineage的时间分层genomic observations。

ED5完整图中其余11个标题逐个可辨：Lineage1、4、12、8、9、3、6、2、5、7、10。每个面板也标Day3/Day5/Day7环，并有gene/locus、substitution/indel/deletion或new-junction等注释和frequency bubble；总图例包括20%、50%、100%和new-junction evidence。与Fig5c的11合起来，公开图覆盖作者所述全部**12条TET-evolved lineages**的三时间genomic展示。部分小字在此原始分辨率下密集，不宜凭肉眼完整逐字符导出allele identity。

Fig5a则是12lineages在TET与AZI两个功能轴上的轨迹，day marker/legend可见。它不是每lineage只有一个endpoint。论文叙述/caption把这些lineage编号与genome图关联，并给了功能day2/3/5/7/10，故genome的day3/5/7有**名义同lineage/时间**的功能对应线索。

**应据此修正任何“没有public genomic state”“工作簿没sheet所以只能下载FASTQ”的说法。** 图就是一个真实、较低成本的published state-information来源。XLSX的schema缺某列不抹掉图中存在的观测；FASTQ是获得更完整/精确数据的路线之一，不是默认必要的下一步。

## 可精确认定的程度

root称它为“12lineages、一个TET selecting drug、nominal matched-time retrospective state/function source lead”，**在nominal和source lead限定保留时，我认为不过宽**。公开论文图确实给出这些作者identity与时间层。不能把它升级为“12个独立背景、已认证精确matched numerical benchmark”或“36个独立任务”，也不能把图中全部stage拆进不同fold。

目前不能仅由看图认证：

- 每个bubble的精确频率、read-depth/variant-calling denominator、误差区间、检测阈值，以及未画bubble代表没有变异还是低频/未展示。图中有观测不等于完整全variant矩阵；缺图项不能自动填零。
- 单一图例大小与每个bubble的精确面积映射、JPEG/缩放/叠加造成的测量误差。未经验证的图像测量不能假装精确原频率；若未来只提取presence/宽frequency类别，也须预先规定不确定/不可辨条目和独立复核。
- 远距mutation的haplotype/连锁、全部群体的真实组成、Methods的clone与Results的population词义冲突、同culture/同管与功能assay aggregation。频率bubble不自动提供构造二所需的q；它改善state观测资格但不解决该反例。
- lineage的实验run/batch、培养祖先独立性、sampling之前/之后实际操作顺序、响应依赖最高dose选择历史、技术重复与功能表的精确列级join。相同作者lineage/day是强于纯文件名的来源对应，但不是未核验细节的证明。

## 未来分组泄漏与合法早期信息分开

作者按day5的CS/neutral/XR把Fig5a/ED5安排、着色或命名分组。未来功能组别、图的位置顺序、lineage ID lookup、与图例同源的CS/XR颜色不能作为early-cut预测feature；否则模型可读到未来target。mutation glyph的位置/标签中作者附带的CS/XR解释也应与实际early allele presence/frequency分开，不把作者已知终点机制结论当免费的测量。

**实际早期mutation仍是合法候选输入**；不能因为图按未来分组，就断言早期state全部不可用。若以后数字化获准，应固定以day ring中实际观测为准的提取、遮蔽未来分组/无关面板、去除终点lookup，并记录此图已被设计者看过。后续新split不能让这些published outcomes变回盲验证。

## 可以考虑的最窄任务，不必先满足全RSI

最清楚的潜在问题是**固定TET适应protocol中，早期genomic observations是否为后期AZI susceptibility预测增加信息**：以day3（或另预定cut）的允许mutation presence/类别/经认证频率，加入同cut已知pastIC90、day、actualselectiondose、mutationburden及technical/history信息，预测laterday的IC90/预冻功能事件。same-lineage全部时点共同分组，未来day5 class/group annotation隔离；先与persistence、pastIC90+day/dose、same-state directridge/tree/kernel及普通动态/refit比较。

这项任务可以先是12lineage内的**designer-exposed、retrospective development诊断**，若精度/样本量有限则报未决；它不需要先取得全药序动作交叉或证明RSI。图分辨率若仅容分类presence，任务只能用该信息层，不能默补精确frequency。是否值得执行取决于合法精确join/可读性与它能改变的实际实验复核决定，当前看图没有授权数字化或fit。

另一个合法用途是复核/重现原作选定gene机制与时间演替的描述；这有复现价值，但原作已解释这些现象，不能把它报新发现。单纯以同day genotype预测同day function是static state→function问题；若只此范围成立，可研究它，不把它包装前向转移。

以上结果即使阳性，也先认证state信息或常规预测应用价值。world-model结构贡献需要同信息direct/multitask/普通transition对照；Agent需要真实query菜单与cost/replay；继承/RSI需要独立未来任务和共同起点后继改进。它们分别未测，不是窄预测的通行证前提，也不能靠12lineages×3times补齐。

## 独立结论

**PUBLIC_TIME_LABELLED_GENOMIC_OBSERVATIONS_CONFIRMED / TWELVE_LINEAGE_ONE_TET_NOMINAL_RETROSPECTIVE_LEAD / EXACT_NUMERIC_AND_PROSPECTIVE_BENCHMARK_NOT_YET_QUALIFIED。** root的有条件表述成立；精确任务仍需小范围feature/cut/uncertainty/功能join资格，不能自动FASTQcampaign。

新公开state事实不能重开两个已STOP构造：Gaussian写回的精确核等价仍成立，marginal-only不提供haplotypeq的生物假设仍未解决。它改善的是来源与可研究的窄信息问题，而不是给world/Agent/继承/RSI或方法新颖性增加已验证收益。
