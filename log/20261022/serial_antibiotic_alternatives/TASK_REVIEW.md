# Tripartite公开MIC面板：最窄预测任务独立审查

2026-10-22，Asia/Shanghai。独立反方`scientific_skeptic`。已读`supplement_followup/REPORT.md`、`VISUAL_SCOPE.md`，并按PDF技能直接查看完整渲染第2页（S1F/G及完整caption）和第5页（S4及完整caption）。没有新HTTP、digitisation、数组导出或拟合；可见论文MIC数字属于designer-exposed文献结果。根代理已查看全部5页，我仅核本任务必要两页，不声称独立复核其余3页。

**来源进展应明确更新：真实公开individual-row MIC功能面板已确认，不能继续说只有genomic accession、没有public function。** 早期报告的“尚未认证完整action/state/function replay”仍成立，但这不否定下面的普通phenotypic预测任务。当前是`PUBLIC_FUNCTION_CONFIRMED / BOUNDED_PHENOTYPIC_TASK_POSSIBLE / COMPLETE_DYNAMIC_REPLAY_NOT_ESTABLISHED`。

## 面板实际承载的信息

S1F/G各有16个strain row、三个已完成evolution阶段以及GEN/PIP/NIT三个MIC readout，分别对应固定GEN→PIP→NIT与NIT→PIP→GEN路径，另有WT参考。stage横轴是已接受的药物历史，不是连续时间点；同stage三个MIC可构成phenotypic susceptibility profile。caption将同row作为沿已规定路径演化的strain展示，支持图内row-linked转移定义；它没有给出全球lineage/BioSample accession、独立培养batch或first/second-attempt row键。

S4B有A–D四个clinical strain组、各8个replicate row位置，PIT和GEN两个MIC面板及pre-SAGE adaptation参考行。caption精确说PIT/GEN MIC分别在PIT/GEN adaptation后测，**不是每个阶段都测了完整二药state vector**。PIT与PIP不同，含tazobactam；不能把S4硬拼作S1的同一action。NIT adaptation因已NIT-resistant省去，不能将其算一次已测新干预。两面板相同row是否完整延续同一replicate祖先应由图内定义/原始记录进一步核对；不靠相同y位置擅自建立BioSample级join。

交叉格确实表示某些条目不可得/未完成，caption与报告的extinction语义要逐项对齐；它们不是零MIC或自动阴性。主文的second-chance evolution会改变一个row究竟是首次轨迹、重试后轨迹还是选择性幸存记录。row可见数不等于独立founder数，也不等于未来任务数。

## 可以合法定义的最窄任务

以下任务都不需要先认证genome、所有备选药序或RSI；但正式数字化前仍应锁定各row转移/缺失语义和实验单位。

| 最窄任务 | 输入与目标 | 合法结论边界 |
|---|---|---|
| **固定loop内下一阶段MIC预测** | S1图内同row早stage的GEN/PIP/NIT MIC profile，加已知next drug和固定SAGE+flat protocol，预测下一stage同三readout或预定一个readout | 条件于该培养/已规定路径的phenotypic transition预测；不是任意下一药反事实。 |
| **早stage预测固定loop结束后的再敏感化** | S1最早可用MIC profile、loop identity，预测同row最后阶段的某预定MIC/临床breakpoint事件 | 可用于优先安排昂贵evolution/后期MIC复核的研究筛查；不是从未见药物或临床疗效。所有臂得同早profile与history。 |
| **S4固定PIT→GEN流程的窄临床strain诊断** | 若同replicate纵向对应认证，使用PIT adaptation后PIT MIC及A–D背景/可用baseline，预测GEN adaptation后GEN MIC | 两个不同功能读出、不同阶段的条件预测；不能称完整MIC-state动力学，也不能用32rows宣称32独立临床背景。 |
| **预定临床strain留一组的transfer诊断** | S4按A–D整体留一背景，而非随机拆replicates；相同有限输入预测同fixed protocol结果 | 至多四背景内小样本transfer诊断。跨strain基线/背景特异效应可能占主导，区间宽应报未决，不包装多任务继承。 |

最透明的第一项可以只做已有完整paired entries的**survivor/observed-transition条件**预测，只要明确estimand、报告全部起始rows及排除原因，不将它外推到全部evolution attempts。若应用目标是“实验是否成功/是否灭绝”，则不能只做complete-case MIC；需要逐row首次/重试/灭绝事件和成本，未知的交叉格不能代填结果。可以把审查未知保留为暂不可评估，而不是为了完成模型把它忽略。

同一mic readout在前后两个阶段重复测量不是label leakage：早MIC预测晚MIC是合法问题。但必须有last-MIC persistence、stage/loop常数、普通offset/transition、early full-profile conditional tree/ridge/kernel这些强对照；不能把早MIC提供给world arm而不给direct arm。MIC是离散serial-dilution表型，若后续拟用log2误差、censoring或breakpoint，应在数字化前确认assay floor/ceiling/精度，不能假设图上每个数都是无误差连续真值。

**Published/designer-exposed不等于不能研究。** 可做诚实标为exploratory的数字化、预定partition和重采样稳健性检查；同row全部stage、姐妹/ancestor相关units须同fold。此后重新随机split不能把已见figure变回盲外部验证，后见预测或复核也不能称independent confirmation。S1同WT的16lineages/arm和S4共享临床founder的8replicates应按实际培养依赖处理；目前没有认证独立run数，不制造不存在的生物重复。

## 为什么它们暂不证明完整动态药序策略

缺的不是“没有在同菌落自适应分叉”这一项通用禁令。固定全schedule结果表本来可以支持**跨实验研究agent**逐轮买实验、更新后选下一实验；不必同colony同时接受两种潜在药物。但本面板要支持更强主张仍分别缺：

- **任意下一药/剂量选择的覆盖。** 每row只有预定loop推进，无同匹配prefix后所有实际可选continuations的结果，也没有已认证处理分配/支持交叠。因此不能用学得模拟器补齐缺失action后再拿模拟值充当真实策略评价。
- **动态state充分性。** MIC profile是有价值的phenotype，但尚无证据说明它含尽未来响应所需历史，也无匹配前瞻genotype。没有配对genome并不妨碍普通MIC预测；它只阻止把结果叫genome-conditioned/molecular机制世界模型贡献。一个显式state-transition模型有用，仍须越过同信息history/direct和普通transition/refit。
- **可执行实验query与成本。** 一个action可以买早MIC、末MIC还是整个11d左右evolution+compensatory培养，返回哪些bundle、首试灭绝与second chance如何计费、all attempted units是否完整，尚未统一。可只把已公开完整paired rows视作有限offline query菜单，但结论限于这个选择后的子集，不能宣称真实完整实验政策净效用。
- **独立迁移任务及策略起点。** 两个WT固定loop和四clinical backgrounds不是自动充分的source→transfer→meta1→meta2任务流；S4 action/readout与S1还不同。可以测试窄phenotypic跨背景预测，不能用drug/time/replicate数复制meta任务。程序/权重继承及RSI需共同model/program/history起点和等预算后继改进，公开面板不自行提供这些证据。

这些是各项主张的具体假设缺口，**不是用全RSI条件去否决普通MIC预测**。Agent也可以从上述bounded prediction中衍生一个窄的lineage-prioritization任务，但它需要明确还未查询的目标、合法query、独立单位与utility，以及fixed/SOP/AL/equal-budgetsearch强比较。当前只是“可能定义”，尚未实验验证。

## 独立建议

保留公开phenotypic资产的实际价值；允许在明确用途下预注册一次bounded designer-exposed MIC-transition诊断，不需要等待所有RSI条件都满足。最小必要前置是row/stage配对及crossed-cell/重试语义、完整case分母、lineage依赖、目标/成本和强直接基线；不是先下载FASTQ或搭世界模型。

是否投入这次诊断，应由它能否改变一个实际药序复核/下一步资源决定判断。若仅为得到一项小样本正数字而运行，无法推进当前新颖核心或独立验证目标，则可选择不做；停止的应是该研究投入，不是宣称该public source没有function。

21BioSample身份另由functional auditor核查，本代理未重复fetch，也未用其数量推断21任务。state-refinement的新颖性STOP仍独立有效：新公开功能能够改善数据资格，却不会让已等价的MDL leaf-split操作变新。当前world/Agent/inheritance/joint/RSI效益仍全部未测试。
