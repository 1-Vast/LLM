# P7 原始证据侦察：独立初始记录

2026-10-28。证据侦察职责；不开发算法、不判定候选成功。先读本 episode record、reference/papers.tsv 中 P100/2015 perturbation biology/2025 Punzi/FAK–MEK 行与 matched-signal-function 既有资源边界。未读功能矩阵、sealed、confirmation、.env；未调用模型 API、运行作者代码或修改共享资料库/index。

## 尚未接收候选讨论的初始判断

1. **MYST 药理层级是新开口。** Nature Communications 2026 原始研究 *Hierarchical small molecule inhibition of MYST acetyltransferases*, DOI 10.1038/s41467-026-70574-1。取得真实 JATS，选读 Sec3/5/6/7、Sec10/13/27–30 和 Data/Code availability。作者直接在 HeLa 核提取物测 CoA 竞争捕获，随后以 MCF-7 和 BT-549 的组蛋白乙酰化位点作细胞内近端活性指标；六化合物的剂量层级揭示商业“靶点标签”不能替代作用。独立 NCI60 增殖只测 PF-9363 与 CPI-1612；BT-549 96h ATP 功能只测 PF-9363。因此不是现成的六药×多背景×同条件作用—功能联合完整矩阵。
2. **MeRLin 是群体选择/状态混淆的约束资源，不是已证可逆性资源。** Molecular Cancer 2026 原始研究 *Clonal dynamics shaped by diverse drug-tolerant persister states in melanoma resistance*, DOI 10.1186/s12943-026-02622-9。取得 JATS，选读 Sec4–7、Sec30–32 及 Data availability。条形码把同一克隆的治疗前后表达联系起来；但实际方法为连续 dabrafenib+trametinib 与长期 PDX，已读实验未提供 washout/rechallenge。文章引言“reversible”不能当本研究的撤药功能证明。尚需第三访问用于另一个明确可逆状态原始线索，以免把谱系证据升级。

当前预算：3/3 主题查询 + 2/3 原始来源访问，5 次 HTTP；所有单次 timeout25s，≤15MB，0失败重试。查询原件/回执及两篇 JATS 均在 sources/evidence_p7。尚未核实的补充数值和来源链接不按缺失处理。


## 完成核读后的证据增量（仍未接收候选讨论）

优先保留两个改变资格的资源：**MYST 剂量药理（实测作用结构）与 BCL11B（选择/状态/撤药功能结构）**。MeRLin 保留为有价值但不满足本次可逆功能资格的检索阴性边界，不另扩展它。未设计或裁决算法，以下“可用”均为来源层级，不是执行准入。

### R-P7-1：MYST 药理层级

原始身份：Xuemin Chen 等，*Hierarchical small molecule inhibition of MYST acetyltransferases*，Nature Communications，原始 JATS 日期 2026-05-13，DOI `10.1038/s41467-026-70574-1`，PMCID `PMC13172425`。证据层级 P，核读的是相关方法/结果/availability，不是全部全文和补充。原件 `sources/evidence_p7/myst.xml`，SHA256 `b1efcaec3bdb1e531acf777409e3175c5e12737c66c8410503c11854a6a68fdf`。

| 条件/字段 | 已核原文与限制 |
|---|---|
| 直接作用实验 | Sec3 P1–3；Sec13 P1–2：HeLa 核提取物，H3K14-CoA 活性位点竞争捕获。WB PF-9363=0/0.01/0.1/1/10/30 μM；4℃预孵育2h、加捕获珠2h。MS PF-9363/WM-3835=0/0.1/1/10 μM，每条件作者称3 biological replicates；提取物批次是否独立不明确。不是活细胞占据。内源 KAT6A/B 未检出，另加重组 KAT6A 单剂量1μM PF-9363/PF-8144补盲。 |
| 多药细胞近端读出 | Sec6 P1–2、Sec28 P1：MCF-7，PF-9363、PF-8144、WM-8014、WM-1119、WM-3835、MOZ-IN-3；0/0.1/1/10/30μM，24h；histone WB，duplicate（独立培养/技术重复层级未明）。Sec5、Sec29：PF-9363 的MCF-7 histone MS，triplicate。H3K23Ac/H3K14Ac/H4K16Ac分别作KAT6A/B、KAT7、KAT8近端活性标志；它们不是细胞内直接占据。 |
| 真实反例 | Sec6 P2：WM-3835常被商业标成KAT7 inhibitor，但在MCF7对H3K23Ac影响比H3K14Ac约强100倍；MOZ-IN-3虽生化有效却未改变细胞标志，作者提出摄取不足的可能。该解释不是已验证摄取机制。 |
| 独立功能 | Sec30 P1：NCI60，PF-9363/CPI-1612，0.01/0.1/1/10/100μM，48h，sulforhodamine B growth assay；重复数本段未核。注意 Sec7 P2写0.1–100μM，和方法最低剂量0.01存在文字不一致，应追Source Data，不自行修正。BT549 PF-9363，60/30/15/7.5/3.75/1.88/0.94/0.47/0.23/0μM，96h CellTiter-Glo，quadruplicate，独立培养数未明。 |
| 背景/培养 | Sec27：MCF7 EMEM+10%FBS+0.01mg/mL insulin+2mM glutamine；BT549 RPMI1640+10%FBS+0.023U/mL insulin+2mM glutamine。Sec7P3/Fig6E BT54924h组蛋白标志，与96h功能非同时、剂量网格亦非逐点相同。其他NCI60背景没有逐背景匹配作用测量。 |
| 遗传参照/机制强度 | Sec7 P3引用DepMap CRISPR依赖，不是同培养同步遗传实验；作者原话 “unambiguous confirmation will require ... mutants of KAT8 resistant to PF-9363 ... beyond the scope”。不能将高剂量KAT8标志变化与生长抑制相关升级为已证KAT8因果。 |
| 许可/元数据 | CC BY4.0。Data availability：PXD074488 raw MS/database search；Zenodo15238967仅结构/FOXK2界面；8DD5结构。文章列9个Supplementary Data XLSX及Source Data XLSX；JATS可见文件名 MOESM3–11、MOESM14。未访问数据库/附件，直接下载可用性、表格schema、独立培养元数据仍unknown；原文列出不等于本轮已下载。 |

**资格改变：**已有多化学实现的实测剂量作用区间，可约束药名/靶点标签的外推语义；但“六药×背景×同条件独立功能”未齐。不能据此启动整药留出、断言同作用可替代或作用结构已充分。

### R-P7-2：BCL11B 选择与可逆状态的功能分离

Zhen Qi 等，*BCL11B predetermines a persister state in breast cancer that is reversed by TNFα*，Science Advances，JATS日期2026-09-09，DOI `10.1126/sciadv.aec5436`，PMCID `PMC13557094`。原件 `bcl11b.xml`，237592 bytes，SHA256 `271d74d587abd4305d66680bd6ff29297dfeae3b5f201bb9c284d7e5a4479e0a`。实际核读 sec5、sec6、sec8、sec9、sec14、sec18、sec19、sec21、sec29、sec33、Fig2/5 caption；Figs S3/S12等仅正文引用，附件未取得，不能当已读。

| 字段 | 已核内容和边界 |
|---|---|
| 背景/干预 | MMTV-PyMT×Bcl11b-tdTomato原发乳癌来源单细胞/类器官；FACS分别纯化tdTomato+与−。Doxorubicin、paclitaxel及体内Doxo+cyclophosphamide，不是多靶点药库；人HCC1954/HCC1937另有研究但本轮未核对应功能。 |
| 选择 vs 状态 | sec5P2：治疗前FACS阳性细胞更易形成persister organoids；阴性细胞少量survivors重新表达tdTomato（提示可塑性，但非全谱系条码追踪）。sec5P4：persister organoids解离为单细胞、换新Matrigel重长，KRT14+/BCL11B+比例回到接近治疗前，再长类器官仍对Doxo有响应。原文明确区分预存耐受群体与后代分化/状态回落，而非仅看治疗后比例。 |
| 撤药与再次给药原文 | sec5P4 “to eliminate ... residual drugs ... clonally derived ... dissociated ... single cells and re-embedded ... fresh Matrigel”；“regrown organoids remained responsive to Doxo treatment ... (fig. S3, I and J).” 这是正文确证存在该实验；再次给药确切浓度/间隔及S3I/J独立重复未核，不能填写推测值。 |
| 剂量/时间/功能 | Fig2J：先长3d，100nM Doxo7d，撤药后生长，到day17数active-growing organoids；n=6 wells来自3 experiments。Fig2F/G：24h Doxo后washout、day11功能，浓度该caption未给。Fig5E/F：TNFα200ng/mL预处理2d，Doxo200nM24h，再单细胞replate，persister organoid frequency；n=6 wells/3experiments。Fig5C/D：TNFα200ng/mL6d，BCL11B/KRT14状态，n=15organoids/3experiments。 |
| 独立功能和避免选择混淆 | sec9P3：纯化单个BCL11B+细胞+TNFα，organoid formation efficiency未受损，但后代KRT14+/BCL11B+比例下降（S12B/C，附件未核）。该设计比仅以群体均值说“转变”更有约束力；仍不能按未读附件断言排除所有差异生存。sec5P5有残余细胞等数移植后肿瘤再生功能，WT再生而KO无肿瘤，十周。 |
| 遗传参照 | sec19：CRISPR exon1 Bcl11b，2个单类器官克隆经Sanger和免疫染色验证，≤6 passages；sec5P3/P5有KO和表达救援；不能将同一来源2克隆当跨病人2背景。 |
| 培养 | sec18：Matrigel；Advanced DMEM/F12+2%FBS+PSA+N2+B27+10mM HEPES+EGF10ng/mL+Rspo1250ng/mL+Y2763210μM+Noggin100ng/mL；37℃/5%CO2，2–3d换液。这些诱导背景属于结论合同。 |
| 重复/风险 | Fig2E18 organoids/3experiments，Fig2G/K6wells/3experiments；Fig2M、Fig5G6mice/group；类器官/孔/培养实验/鼠必须分层，非细胞数。sec29说each experiment≥3次，no prespecified animal power、no blinding/no randomization；但sec21说mice randomized，原文内部不一致，保留而不选择有利版本。Fig5G特别说明WT和KO分开做，绝对肿瘤大小不可直接比。 |
| 数据/许可 | CC BY-NC4.0，非商业；GEO GSE228442生成的scRNA/bulk RNA；作者声明不报告original code，plasmids upon reasonable request。JATS列 `sciadv.aec5436_sm.pdf` 与 `sciadv.aec5436_tables_s1_to_s7.zip`；未下载，原始功能图数值/再次给药协议是否可直接机读仍unknown。 |

**资格改变：**这不是把“细胞状态”直接当作用。它有预存状态分选、遗传KO/救援、撤药后单细胞重长、再次Doxo功能和TNFα状态操作，足以迫使未来问题分别记录群体组成、状态后代与干预后功能。尚不支持跨背景/跨药共享动力学，不声称TNFα普遍消除耐药或临床获益。

### MeRLin 边界证据（不作为第二优先资源扩展）

Haiyin Li等，Molecular Cancer，2026-03-03，DOI10.1186/s12943-026-02622-9，CC BY4.0。`clonal_melanoma.xml`200576bytes，SHA256 `3863a6f2f53583199f70c153427f7d19c397d2bf5873665ff6ca0145b8429c9c`。WM4237-1单背景；0.3μM dabrafenib+30nM trametinib1week，3replicates pooled；PDX饮食150mg/kg dabrafenib+1.5mg/kg trametinib，day0/21/57/91；bulk n3/3/3/6鼠，endpoint scRNA n3。此处mg/kg是饮食配方，不能擅自改为实际体重日剂量。条码+表达能对照同克隆，却连续用药；全文字符串和已读方法未定位withdrawal/rechallenge，其存在保持未核而非证明没有。Data availability GSE299711、GSE299589、GSE245582与GitHub Yeqing95/MeRLin，未访问；独立再给药功能未知。作者克隆频率还按肿瘤体积和总体转录活性归一，不能把条码RNA频率直接当细胞存活率。

## 检索/预算/真实收据

- 现工具未暴露web搜索，实际用公开EuropePMC search(core,pageSize30)，精确查询见3个 `q*_receipt.json`。Q1=target engagement/chemoproteomic+viability/proliferation，Q2=lineage tracing/barcoding+persister/resistance+reversible/rechallenge/selection，Q3=phosphoproteomics+drugresponse+celllines/doseresponse；均2025-01-01至2026-10-28。
- 分别hitCount5564/1341/299，实际各返回30条。命中数是该数据库范围，不等于相关论文总数；未全分页。Q2大量综述，按pubType识别原始研究，只对可改变边界者全文。90条题录没有当作90篇全文。Q1/Q3仅选读相关摘要；Q2原始文献摘要按实际线索读。非系统综述、不据此次未见断言不存在其他资源。
- **6/6 HTTP =3主题查询+3原始JATS访问；0重试、0 403/429，预算耗尽后停止。** 全部请求timeout25s、单响应≤15MB；总原始响应体体积由 `manifest.json` 汇总。未下载大型数据/功能矩阵；未开浏览器、执行作者代码、安装依赖或调用模型API。source XML是原始正文格式，不伪装为PDF/HTML。
- `*_sections.json`为本地JATS按section提取，每个paragraph序号仅在相应section直属p内计数。原始来源回执保留URL/时间/status/type/bytes/hash；查询回执保留exact query。root可据本文件入共享库，本代理未写库/index。
