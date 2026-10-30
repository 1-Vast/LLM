# 原始数据、2026来源与实际读取范围

2026-10-29。公开获取截止本轮：8动作/2主题query已满，7成功响应1,942,462B，1次P7原HTML404；随后明确改取同v1 PDF成功，未重复同URL、未自动重试、未因不确定结果换后端。原URL/时间/类型/hash在retrieval.jsonl。PubMed query14命中均取得原XML；arXiv query仅最新15条，非全领域查新。新论文为预印本，正式venue未核，不称顶会/顶刊录用。ChemScreener只元数据/摘要，不冒充方法核读。

## 便宜数据的可获得性与观测身份

1. 当前Figshare原API article25266697返回public、CC BY4.0、文件45451363，241,088,863B；本地tmp/extq1/gsdc_well_stats.zip实算SHA256 `e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259`，与旧原清单相符，MD5 `ff3dab95ad59a1c956e3b11c397dcbd8`与当前公开file的computed/supplied值一致。仅刷新小元数据，未重复下载241MB。raw_metadata.json保存公开许可/来源、ZIP目录与5个CSV表头。
2. root实读ZIP原Glossary_combo_well_stats.pdf两页，原件148,064B已保存sources/well_glossary.pdf。其首页明确是每个组合well加按药物/浓度匹配的monotherapy数据，treatment在此文件总为C。`lib1/2_conc`为micromolar；`lib1/2_x`是max9归一化坐标；IC50是natural-log micromolar；`y`为抑制响应、`yhat`为拟合值。因此该表不能按行购买独立单药反馈，也不能把全曲线拟合列当免费特征/评定真值。字典说明没有逐条认证y为未经处理的原始仪器数；当前应称导出响应参照，与拟合yhat区分。
3. root回读原PMC11061612 JATS S15/S17（旧本地原件）：S15为24h接种后处理72h、CellTiter-Glo2.0、luminescence；S17为七细胞系六occasion技术三重复、QC规则。字典却将INTENSITY描述为fluorescence，保留原文措辞冲突，不据此推存在两个不同模态。处理时间是study-level协议，不补造逐记录time/培养字段。CELL_ID为stock expansion identifier，BARCODE为plate，cmatrix为layout内matrix，均不自动成为独立培养/occasion认证。
4. 固定前20000行的metadata_probe只投影13个身份/剂量字段，无响应/拟合列保留或数值解析。CSV压缩流实际读取含响应的行字节，不能称完全未读过该CSV；代码的usecols排除响应列，计数不以响应筛选。这个前缀有19cell、11drug、35barcode、438plate-matrix，20000行均C。两侧参照共40000次出现，仅5924个project/cell/ref/conc键；5923键重复，最大7次，未见该ref映到多个drugID。这证实字段重复出现，不认证真实单药测量来源的唯一性、数值一致、独立重复数或全局覆盖。浓度1e−6至30µM也是该前缀范围，不作共同剂量窗证明。
5. 同一固定前缀的source_key_structure进一步只检查8个身份/剂量字段：40000次参照中有876个不同ref，全部以当前BARCODE加下划线开头，ref跨当前plate/cell/drug多重映射均0。772个ref出现7个不同浓度字符串、104个出现5个；前缀截断可能影响覆盖，不能称772条独立完整实测曲线。示例同板同drug可有不同ref（如38690_L57/L58），所以不能只按drug/浓度合并。该命名规律缩小到板内参照关联问题，但不认证参照的原始单药well/强度或独立测量来源；组合行POSITION不能直接填成单药来源孔。未比较任何响应值是否相等。
6. 这些条件允许继续研究同协议功能曲线；不必为此要求RNA、显微、遗传救援或正交终点。当前尚未获得D.v0的完整包覆盖、合法独立噪声与动作/评定拆分；预测共享及实际选药收益未测。旧M2要求的多时间/正交/配对数据与本题不同，原M2结果原样保留；不将其旧data_unavailable当普通预测的普遍否决，也不把本轮结构资格升级成M2成功。

本地工程读取：inspect_raw_metadata.py首次因maestro缺fitz在导入处退出，未触及ZIP/产物；改用环境已有pypdf后完成0.453s。metadata_probe0.094s，source-key局部检查0.110s。均为数据结构核查，0科学效果实验/拟合/训练/新增功能响应数值；没有安装依赖、GPU、湿实验。文件hash相符只证原字节身份。

## 三份新原件怎样改变判断

| 来源、版本及首发 | root实际方法读取 | 能借的原则与不能直接迁移的条件 |
|---|---|---|
| AutoRASOR，2609.22411v1，2026-09-18 | 原HTML §2.5–2.6（S2.SS5/S2.SS6），AppendixS2；从原件解析的段落导航27–45/93–94，独立显示公式未全核，未复现结果/代码 | 细尺度特征给定粗尺度特征的条件方差；对已采patch用k10邻居、NW方差、带宽ceiling估计，再用邻居删除jackknife度量估计误差并以GP+qLogNEI获取。重拍同位置只测成像噪声，跨位置差异才是其estimand。条件差异、估计不确定性和测量噪声要分清；低剂量不是低分辨率图，原粗embedding已存在，不能免费假定药物中段也已看见。 |
| Autonomous atomistic–continuum coupling through uncertainty-aware active learning，2610.33272v1，2026-10-23 | 原HTML §3.2、§4/4.1/4.2（S3.SS2、S4），段落34–46，未复现CFD/KMC/DFT或数值效果 | continuum传状态，atomistic去掉transient后取ensemble steady-state species flux作接口；六GP均以状态到flux拟合，最大方差超阈值才新增昂贵模拟并重拟合。低维接口依赖可测/可模拟量与steady-state假设；不能由此推普通存活率是细胞机制充分状态。在线GP触发本身已有明确方法。 |
| Multitask Scanning Probe Microscopy，2608.09104v1，2026-08-10 | 原PDF pp6–9、11、15：II.B–D、III.C–D及Fig4；公式3/4/7/11–13，未全审结果/附录/代码 | ICM Kx·B、B=WWᵀ+diagκ，LMC可分多尺度共享/特异项；每步超参数重估、paired seeds后非重合选点，共享传播已有实现。实际用随机Dirichlet加权UCB、每三步强制探索，两模态等隐含成本；式13成本方案只扩展，不能说已验证cost-aware。latent预测σ不含观测噪声，不能直接当新孔不确定性。 |

段落投影paragraphs.json与PDF文字p7_text.json仅导航，不是新独立来源；显示公式或图未读不能由投影补成已审。三原件与元数据入共享reference；作者仓库/commit/许可未取得，无作者代码执行。P7原HTML404不是论文不存在。

scout实读旧本地H-Net§2.1–2.2、MALocate§2–3、TEB§2–3；proposer实读P5两节及P7 pp1–10，P6未读。每角色实际读取及初判暴露范围留在其原文件，不将同篇多角色复读称多来源独立证据。

PubMed原记录重新检出LUDRP与SHIFT-DRP：前者已有本地方法证据，后者本轮仍只有原摘要，不重调其旧403。新增ChemScreener（10.1186/s13321-026-01204-7，PMC13235147）原摘要报告单剂量WDR5 HTRF迭代、后续剂量响应/counter assay/DSF；这不是细胞功能响应，更不能由摘要判最近主动曲线先例。条目记pending/A，正文与代码留待定向检查，本轮额度封账。

## 重复性辅助与成本

DS022一次真实headless、3.703s、1final/1step_end，7394B stdin；2211input/577output/256cache-read、reported total3044。root对10字段/预定单位与72×3600=259200复算，保留fluorescence/luminescence冲突。D7原quote86>64拒收，canonical另取原文56字符，原事件/正文/usage/格式失败不改。累计Harness14/14，无重试/换后端；effective/底层API请求/实付unknown，USD0.025是声明上限非已认证硬美元cap。详细验收见../deepseek/tasks/DS022/main_review.md。

库verify实际为118唯一来源、103论文文件，72HTML/14PDF/22pending/8restricted/2abstract_only；8代码快照关联7论文，61not_verified/50not_yet_checked，论文90.5MB/代码12.6MB，errors/warnings/changed均空。library_verify.json是实际返回字段的摘要，只证清单/文件完整性，不证明读全、数据资格、新颖或效果。
