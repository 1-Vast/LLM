# 宽表 schema 后的限域审查与真实交叉

2026-10-22。独立稿及第一轮 CROSS 已先封存。此后仅读 `IDENTITY_SUMMARY.json`、`SECOND_MARKER_PROJECTION.json` 的获准身份/标签投影，另接受 root 提供的 exact manifest/file-description 与 metadata-collision证据；未读 raw workbook、response/QC decisions、fit 或 GET。原稿与数据不改。

**判断：已足以继续“paired exported-row”的限定 joint marker forecast 资格；不必先证明原 well/run。** 三 Full 各1920 metadata rows，1833非空 named library entries各一行并 exact-unique join到库；SG+与第二marker位于同一 Compound宽表行、两块时间header对齐。T98G为0:4:96、U2OS为0:2:118。这解决先前多行marker不知如何配对的export层问题，支持同一导出行的合法 early双通道→later readout任务。它未证明该行是单孔、独立run或已平均的哪种replicate，不能增报well级n、eventcounts或birth/death守恒。时间为来源支持的nominal acquisition time，不擅加逐plate精确给药时间。

第二marker literal：T98GDMSO=`NLS`，TMZ/U2OS=`mKate2+`。root提供的exact v1 T98GDMSO文件描述明确live(mKate2+)/dead(SG+) counts及96h/4h，与primary唯一Nuc::mKate2 reporter和两block设计一致。**此证据链足以source-supported operational live-reporter mapping，可继续使用literal NLS；不要求不存在的逐字exportlegend才可预测。** 未有export script直接定义NLS键，因此不能写成逐字同义已证、跨screen校准等价或true viability。继承到后续数据模型时保存`raw_label=NLS`与mapping依据/推断层次，不静默覆盖为“真实活细胞”。

87行 A601:A687 的原身份是Excel error `#N/A`；保留为unidentified export rows，不凭数量87推DMSO。三个screen均87且primary U2OS控制数79，更不支持自动vehicle赋值。可在数值前将1833 named-library-entry panel明确定义为身份限定应用，这不是通过future QC；87行保留原文件，但不作为已认证controls作归一化/噪声估计。库Plate/Position不自动是screen plate/well；TMZ side AUC/Norm.AUC/Compound/Targets/Pathway/Plate仅headers已知，可能是结果表，不能把side Plate搬给raw rows。

root后提供、auditor独立核对：CatalogNo与非空CAS exactunique，但SMILES1有一处重复literal，涉及库row574 Doxycycline Hyclate与row587 E-64。不同name/CAS与相同SMILES构成annotation冲突，不能由同串宣布alias或手修。1833 unique recorded entries不等于1833 verified unique chemicals；未排chemical aliases时仅称unseen recorded library entry。后续结构/chemical-group holdout需在响应前注册对冲突的处理，可保守collision grouping或停用歧义结构，均不声称修复了真实化学身份；不妨碍原始entry层forecast。

实际双向交叉已完成：反方向functional_auditor问“同row宽表是否足够export配对、file描述是否可支持NLS alias”；对方答export配对足够但不补well/run，alias可用注明推断链。对方反问“仅dataset泛称live/dead是否仍partial、87NA是否不得认vehicle、exactjoin是否不等uniquechemical”；反方逐项接受，并挑战“不应要求source逐字出现Excel NLS键”。对方明确接受证据链可支持operational mapping，区分export-row pairing已足、source-supported reporter解释、lexical/calibration未证三层。root补exactfile描述后，双方均接受operational mapping；对SMILES碰撞亦均拒绝宣称alias/修正。原始往来由双方消息与auditor的POST_SCHEMA记录保留，共识不填补实证未知。

后续仅可据此预注册数值合法性/QC/missingness、具体prefix/target与预算/阈值，再做条件D与同信息world对照。source pairing/identity资格不是响应域通过，更不是信息增益、新算法、agent、继承或RSI结果。87NA、原plate/run/rep、化学注释与跨screenmeasurement差异均保持明确限制。
