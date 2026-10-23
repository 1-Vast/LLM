# PLK1 SDL 新一手来源的独立合同审查

2026-10-22。这是旧INDEPENDENT.md之外的新source addendum，不修改旧sealed结论。先独立读root已保存的plk1.txt和receipt，检查研究结果流程、STAR Methods、data availability、supplement项目文字说明；未读本阶段peer source意见。正文DOI10.1016/j.xgen.2025.100876，EuropePMC PMC12230241，root保存XML HTTP200/290243bytes/SHA256 a4fbd1b664f35f53a04ca5709332e1d109656664548e6afdc8ff883052e9c05e。未下载、打开或数值读取任何补表/原始矩阵；仅文字说明。作者结果不是本项目实测。

**结论：真实且有价值的遗传靶点验证研究，但当前正文不足以认证一个可公平直接运行的“细胞状态→独立功能反馈→更新规律迁移”入口。NO_READY_STATE_FUNCTION_UPDATE_CONTRACT；不是数据不存在、论文性能失败或全称该资产无价值。**

## 干预、背景、时间与测量逐项核对

| 平台 | 真实干预与背景 | 时序和读数 | 对目标合同的限制 |
|---|---|---|---|
| genome-wide shRNA | HCT116 inducible constitutively active PLK1-S137D；约90000 hairpins/18000 genes；doxy induced vs isogenic uninduced | MOI .3，24h后puromycin48h；day0开始doxy；day0/8/16提genomic DNA、PCR hairpins、UT-GMAP1.0杂交，WDC dropout | **microarray CEL不是细胞基因表达状态**，而是shRNA条形码丰度/选择信号。不能把表达array→功能配对当已经具备。 |
| secondary arrayed CRISPR | HCI-010 breast PDX-derived line ±Cas9；105genes、每gene两sgRNA一孔 | lentiviral24h后换puromycin，再48h选择；brightfield confluency观测day0/4/6；methods又称相对baseline day2 | 独立于scRNA的真实功能类读数，但不同背景、不同观察时间，且是后续候选产生依据；baseline需数据说明澄清。 |
| secondary pooled in vivo CRISPR | 同一HCI-010 ±Cas9，210sgRNA | puromycin选择后每鼠3million cells入乳腺脂肪垫，3weeks肿瘤后gDNA/sgRNA dropout；作者七tumors/condition | 是遗传扰动肿瘤fitness，不是药物response；7鼠是该背景下重复，不是7种later背景任务。 |
| direct-capture Perturb-seq | MCF7-Cas9，65genes×2sgRNA=130，加15nontarget和16positive，合计161guides | 作者22041测序cells，QC单guide且UMI≥5000后7434；三batches聚合；正文/图注称选择后4days，STAR Methods称2days | 单一MCF7背景的survivor转录状态；时间冲突不能擅自择一。三batch或7434cells不等同独立任务。 |
| focused inhibitor validation | IGF2BP2相关化合物，在MCF7/MDA-MB-231/BT-549等作focused验证 | resazurin assay，5–75μM、72h，作者三experiments×六replicates；另有colony/tumor | 不构成65gene对应65drug功能panel，遗传loss与compound on/offtarget不可直接替换。 |

状态与功能确实出现在同一研究，但不是由同一细胞/同一扰动背景/前后时间组成的自动配对。MCF7的PLK1-high cell比例减少可能来自表达下调、群体重分配或消失；抽取到的单细胞转录与guide丰度不单独认证每cell死亡。作者用single-cell结果解释viability，不等于公开提供与其独立测得的逐gene MCF7功能label。

## 候选库的产生过程不可略过

HCT116全库功能筛出960hits（作者阈值至少2fold且p<.05）；再以TCGA共表达、已发表essentiality、临床自然SDL生存关联、19p13.2–3、ToppGene和细胞表面靶点等优先级选134genes，29未克隆，实际验证105。

HCI-010 arrayed assay得60hits，in vivo得15，重合10，合为**65已验证hits**；Perturb-seq库正是这65，不是随机独立全库。于是若用MCF7状态预测HCI-010这套功能标签，标签已经参与了基因被纳入的选择，且表达采集顺序在功能验证之后。它可以定义条件于已选候选的事后跨背景预测，但不能称“用状态在未经功能筛选的全候选发现hit”或独立prospective确认。必须包括库外/未成功克隆/未过筛的选择机制与目标范围，而非只把65做随机gene split便抹掉选择。

正文称65gene中六基因未显著knockdown后被排除（列LPL/CNN1/C19ORF35/CLPS/ATP4A/TMC，原文最后命名需核guide表）；这个排除依赖扰动表达结果，不应偷偷作为所有target任务免费预过滤。Positive housekeeping controls和nontarget controls也不能当足够代表性的普通负候选。本文尚未给均衡独立later tasks的保证。

## 可得 accession：哪些已认证，哪些没有

正文Data and code availability明确给出SuperSeries **GSE203242**，subseries **GSE203237**为shRNA raw microarray .CEL，**GSE203240**为CRISPR deep-sequencing .fastq.gz。它没有在所读方法/availability中逐样本清楚标出哪个独立accession覆盖MCF7 gene-expression+guide assignment、哪个覆盖HCI-010 in vivo dropout；不能凭“CRISPR fastq”自动声明Perturb-seq已公开可组装。尚需将来仅metadata层面的文件/样本映射认证才知道具体可得，不在本角色现在下载验证。

其余data按lead-contact request提供，且明确“did not report original code”。Supplement项目文字说明列S6 in vitro CRISPR结果、S7 in vivo、S8 guides、S9 focused RNAseq DEGs；本角色未打开这些数值。因此不能当前认证逐gene readout矩阵、重复/批次完整性、exact guide join、assay noise或实际有效交集。也不能把upon-request等同当前已获取；本任务未授权联系作者，本角色未联系。

## 独立任务轴与公平比较的最低要求

当前最多认证三个不同实验背景的设计：HCT116 isogenic PLK1诱导系统，HCI-010 PDX-derived ±Cas9 assay系统，MCF7转录扰动系统；它们不是三套同接口state+独立function的可互换episode。两个HCI assay是同一model的不同endpoint；三个MCF7batch、七tumors、sgRNA或cells不能扩大独立背景task n。65干预genes可以作为条件于预选库的任务单位，但共享来源、状态和selection，尚无独立later campaign轴。其他breast lines对单个IGF2BP2验证不等于多gene source/later矩阵。

若未来完整metadata证实MCF7状态和HCI-010独立功能可join，最小诚实问题只能先是“在已功能验证候选集合内，某种可见表达状态是否补充源gene注释对另一背景功能的预测”，并明确conditioned selection、expression测量成本、实际时间顺序与跨背景混杂。强普通direct预测、同信息source conditional regression、功能only与表达mask/value对照不可少；先问有无条件信息，不能直接跳到world/agent/RSI。本文没有给一个比这些对手独特的更新操作。

**当前不建议立即打开数据/数值补表或训练pilot。** 原因是配对/公开sample-map、独立functional目标与任务轴尚未认证，而非没有论文创新。未复用旧ALMANAC/PRISM入口、不放宽旧STOP；也不声称新来源被旧资产的性能结果否定。后续若只做metadata认证，须先由root在同样边界下决定是否值得，不能借本报告自动扩大为sourcehunt或作者联系。

完整world/agent/inheritance/joint/improved-improver目标仍ACTIVE / NOT_ACHIEVED；本报告只是新一手source合同审查。一次大范围grep输出截断，关键方法/availability/库选择过程随后聚焦读到；不把截断部分当未见证据。零新HTTP、数值数据读取、模型fit或代码执行。
