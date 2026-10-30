# 常见廉价功能数据：入口、信息边界与取得条件

2026-10-28。资源证据角色初稿；不是科学假设/指标选择，也不是独立终审。中途按用户“稀有/难收集损害普适性”的新指示，把主比较改为本地 PRISM 与 GDSC；O'Neil/NCI 已完成的核查保留在末尾，不扩展其合同。

**结论：做只依赖 cell/drug/dose/functional response 的廉价开发性重放，现成 PRISM 发布功能矩阵和 GDSC 发布表已够作为输入候选，无须先配齐遗传、谱系或组学。** 本轮没有开功能数值、没有重跑旧效果。是否有足够可分辨决策空间由另立冻结协议决定，本证据表不认证效果、独立确认或生物机制。PRISM/GDSC 都历史暴露；换数据版本/剂量不能恢复盲态。

## 1. 可直接使用的本地入口（字节亲核）

前缀 P=`D:/MAESTRO/data/external/prism_19q4/raw/`；G=`D:/MAESTRO/data/external/gdsc_combinations/jaaks2022_figshare/`。所有数字是文件系统实际字节，不是估算下载体积。

| 输入 | 完整目录下的文件名 | 字节 | 本轮读取范围/含义 |
|---|---|---:|---|
| PRISM primary 发布功能矩阵 | P + primary-screen-replicate-collapsed-logfold-change.csv | 41,254,209 | **未打开**；README说是DMSO相对log2 fold change、ComBat校正、重复中位合并；不是原始荧光，也不保留重复 |
| PRISM primary 条件metadata | P + primary-screen-replicate-collapsed-treatment-info.csv | 1,185,606 | 全表metadata亲核；column_name/broad_id/name/dose/screen_id等 |
| PRISM primary 细胞metadata | P + primary-screen-cell-line-info.csv | 46,849 | 全表metadata亲核；row_name/depmap_id/ccle_name/STR等 |
| PRISM primary 字段字典 | P + primary-screen-readme.txt | 5,919 | 完整读取 |
| PRISM secondary 重复级发布功能矩阵 | P + secondary-screen-logfold-change.csv | 237,567,060 | **未打开**；保留条件重复列键，仍是归一/校正后的功能值 |
| PRISM secondary 合并功能矩阵 | P + secondary-screen-replicate-collapsed-logfold-change.csv | 91,620,551 | **未打开**；重复已合并 |
| PRISM secondary 重复级metadata | P + secondary-screen-replicate-treatment-info.csv | 15,690,740 | 全表metadata亲核；screen_id/detection_plate/compound_plate/well可定义来源组 |
| PRISM secondary 合并条件metadata | P + secondary-screen-replicate-collapsed-treatment-info.csv | 3,788,355 | 全表metadata亲核 |
| PRISM secondary 细胞metadata | P + secondary-screen-cell-line-info.csv | 40,979 | 全表metadata亲核 |
| PRISM secondary 细胞池metadata | P + secondary-screen-pooling-info.csv | 264,680 | 全表metadata亲核；pool/minipool/detection_pool/analyte/screen等 |
| PRISM secondary 字段字典 | P + secondary-screen-readme.txt | 7,647 | 完整读取 |
| GDSC/Jaaks 原筛拟合表 | G + Original screen_All tissues_fitted data.csv | 198,893,607 | **只读header**；不是单药GDSC2，不是原始well值 |
| GDSC/Jaaks 验证筛拟合表 | G + Validation screen_All tissues_fitted data.csv | 11,774,397 | **只读header**；便宜小文件，但“validation”文件名不证明本项目未用/独立培养 |
| GDSC/Jaaks 原筛原始CSV ZIP | G + Original_screen_All_tissues_raw_data.csv.zip | 60,669,525 | **只读ZIP目录**；里面唯一CSV未压缩为1,216,348,914B；未解压/未读header或值 |
| GDSC 字段字典 | G + Glossary.xlsx | 12,193 | 完整metadata读取 |

这里只把响应文件列为后续协议可引用的入口。没有声称这些文件已经通过本轮数据/切分/决策收益准入。

## 2. 不开功能值就能冻结什么

PRISM的实际metadata审计（路径、大小、SHA256、表头、计数）保存在 `sources/cheap_data/prism_metadata_audit.json`。

- **共同最低字段**：细胞ID、化合物/批次ID、剂量、筛选来源ID、响应列/行键；训练/可查询/评分角色可先按这些ID冻结。目标/遗传/组学列可以完全不用，不是启动基本重放的必要条件。
- **PRISM primary**：4,686个column_name、4,686个broad_id；screen_id为HTS/MTS004。metadata实际有416种dose字符串；不能把所有点默认为同一个2.5µM剂量。broad_id按官方字典标识drug-batch combination，不能静默当独立化学实体。相同名字也不能未经核查合并。primary只保留合并层metadata，当前本地不含它的重复级条件表/池表，不能凭README重建缺失来源组。
- **PRISM secondary**：13,008个合并列键、1,502个broad_id、4个screen_id（HTS002/MTS005/MTS006/MTS010）。重复级表有48,967个唯一列键、144个detection_plate、48个compound_plate。pooling表包含六种screen_id（另含HTS/MTS004），不能把该池表所有行直接当secondary可用条件。
- **剂量注意**：secondary合并metadata有1,058种dose字符串，重复级有1,064种（含NA及浓度修正）。README的“8-step, 4-fold, starting from 10uM”是筛选设计说明，不是本地每列已验证的8个相同数字。先冻结名义/实际剂量映射与缺失处理，不用读功能响应，也不靠四舍五入恢复网格。
- **重复与筛选**：secondary README明确2019-11-22增加147个oncology compounds的 **technical redos**，screen_id=MTS010，官方建议有则优先用MTS010。MTS010不是独立生物培养认证；不能同时把旧筛/redo拆在训练和确认两侧来声称独立。screen、plate、pool、well是来源组标识，不是独立培养证明。
- **细胞**：两份cell_info均588行，metadata的depmap_id字符串去重为569（含NA等未筛选项）；不等于569或588个合格实测细胞。README primary描述578/562、secondary描述489，是发布说明；实际合格集需按STR、ID缺失、筛选匹配先冻结，不能直接抄人数。
- **GDSC**：CSV表头与Glossary亲核支持BARCODE、COMBI_ID、CELL_LINE_NAME/SIDM/COSMIC_ID、ANCHOR_ID/NAME/CONC、LIBRARY_ID/NAME/CONC；必须保留anchor/library剂量角色，LIBRARY_CONC是最高library浓度。BARCODE为筛选板，不认证独立培养。SYNERGY_*、AUC、EMAX属于拟合/派生端点，不能伪装成dose-well原始观察。本轮没有提取任何metadata投影或切分。

## 3. 低成本和普适性的实际边界

本地开发读取不需要新下载、特殊仪器或专有API；标准CSV/ZIP/XLSX即可。PRISM原始研究使用条形码/Luminex检测，不代表重放算法的使用者需要该仪器；也不能因此假称任何实验室能够低成本复制整个原始screen。GDSC/PRISM是公开常见资源，不是本轮新的确认集。

以**严格十进制40,000,000B/文件、100,000,000B总量**解释下载预算：

- PRISM primary响应单文件41,254,209B略超40MB（约39.34MiB）；连两份metadata与README约42.49MB，总量小于100MB。不能说“严格40MB单文件已满足”；如果预算实际指40MiB则该响应文件满足，但此处不擅改口径。
- PRISM secondary合并响应91.62MB，连合并metadata/细胞metadata/README约95.46MB，总量小于100MB，单文件超40MB；重复级237.57MB超总预算。其本地存在可避免重下载，但不能据此声称远程小子集入口已核实。
- GDSC validation fitted11.77MB加Glossary满足两项预算，但只支持该发布拟合表的重放；原筛raw ZIP60.67MB单文件超40MB，解压1.216GB，不宜成为普适默认输入。
- **可操作的最小取得**：本机直接引用现有PRISM primary源路径与metadata，先冻结ID/剂量/屏来源，再按冻结名单顺序流式取子矩阵并写唯一provenance；该子集尚未生成、字节尚未测，不能报为已取得≤40MB。若严格要求“新用户远程每文件≤40MB且不先下载大文件”，本轮尚未核实PRISM服务端子集/压缩小包，需承认缺口，而非默默下载全secondary。GDSC validation是已亲核小文件候选，但本轮未刷新其官方直链。

## 4. 条件、许可、历史停线：已知与未核

PRISM两个README未写作用时长；本轮没有亲读Corsello原始方法，**不声称5天、120h或其他时间已经核实**。GDSC Glossary的GROWTH_RATE及DOUBLING_TIME说明含day4/day1及72公式，但这不是本轮亲读原文方法的替代，**不把公式升级为所有实验的72h终点认证**。时间缺口不妨碍只做明确限定的同一发布表内部开发重放；不允许据此做跨assay时间对齐。

PRISM README的moa/target是Broad Repurposing Hub注释；GDSC ANCHOR/LIBRARY_TARGET/PATHWAY为注释；都不是逐条件靶点占据或遗传功能参照。当前基本任务可不使用这些列。PRISM/GDSC许可本轮未亲核完整官方许可文件；不得凭公开可下载就补写CC BY。GDSC/Jaaks名称与来源由 `data/INVENTORY.md` 第74行及既有研究记录定位；此处只核本地字节和字典，不认证新下载条款。

历史边界：`data/INVENTORY.md` 把PRISM标为exposed internal development；GDSC/Jaaks用于action substitution、kinobeads、residual gate等。`research/INDEX.md` 和 `research/EVIDENCE_REGISTER.md` 载有大量GDSC/BATCHIE旧分析、饱和/低功效/度量失配等约束。用户取消“必须算法新颖”不取消这些旧停止原因。新问题可以有独立的新开发协议，不能靠重命名复活旧确认或重新选择旧效果。

## 5. 调整前完成的O'Neil/NCI核查（保留，停止扩展）

O'Neil原始三个AACR附件已经在 `D:/MAESTRO/data/raw/oneil2026_qualification/`，SOURCE_RECEIPTS.json给出下载URL、SHA256、版本和exposed internal development。

| 附件 | 官方file ID/直链 | 实际字节 |
|---|---|---:|
| combination response（xls扩展名、OOXML内容） | https://ndownloader.figshare.com/files/39962566 | 38,829,879 |
| single agent response | https://ndownloader.figshare.com/files/39962560 | 1,678,111 |
| response legends | https://ndownloader.figshare.com/files/39962563 | 10,430 |

合计40,518,420B；每文件严格≤40MB、总≤100MB，**0新下载即可取得**。metadata articles22503133/22503127/22503130为CC BY4.0。亲读的是原生legend.xlsx，不是响应工作簿：它逐字说明96h assay、single最多6个、combo最多4个technical replicates；三批按cell growth/drug batches划分，1/2为primary，3为选择性partial repeat/validation。legend已抽为 `sources/cheap_data/oneil_legend_extracted.json`，含源SHA。旧metadata-only资格报告列39细胞/38药/583药对/4×4网格，但本轮不重算。独立培养及靶点/遗传参照未认证。O'Neil已用于旧拟合/选择和ON1–ON3；ON3正式report为non-blind/peeked且no_increment（仅原预注册描述阈值未达），本轮不重跑、不解冻原结论。便宜不等于新确认。

NCI官方入口 https://dtp.cancer.gov/ncialmanac 本轮HTTP200，明确指向 https://wiki.nci.nih.gov/display/NCIDTPdata/NCI-ALMANAC （HTTP200，最终page338237347）。下载页实际列：ComboCompoundSet.sdf、ComboCompoundNames_small/all.txt、ComboDrugGrowth_Nov2017.zip、ALMANAC_DataFields.txt/docx。官方页面不含文件字节/独立重复/时长/完整许可；预算内未再请求附件，**不声称原始ALMANAC≤40MB、dose/time/生物重复已核**。页面原生药物NSC/结构映射可与匿名二次分发区分，但未打开它们。`data/INVENTORY.md`载有ALMANAC旧缓存已使用、原始目录空，因此也不是fresh确认。

既有BATCHIE Zenodo12764821二次分发的nci_almanac.screen.h5=15,028,403B、merck_2016.screen.h5=2,957,309B；R172/R173记录没有匿名处理索引到真实药名映射。这只排除该特定二次分发用途，不证明NCI/O'Neil原始数据无真实药名。未打开这些H5，本轮不继续追映射。

## 6. 回执与本轮实际消耗

`sources/cheap_data/`保存每次访问前写的receipt和实际响应：

1. query.receipt.json / query.json：Europe PMC精确DOI OR NCI-title query，HTTP200，20,352B；O'Neil PMID26983881、非OA无PMC；查询未命中原始ALMANAC论文，不能用其返回的2019预测论文代替原始资源方法。
2. nci_official.receipt.json / nci_official.html：官方入口HTTP200，7,886B。
3. nci_download.receipt.json / nci_download.html：官方Data Download页面HTTP200，86,540B。

合计3次公开HTTP、1query+2官方metadata，114,778B响应；每次timeout25s、0重试。未下载新功能文件，未安装依赖/运行作者代码/旧实验；未修改索引、src/tools。仅目录枚举时看见既有sealed文件名，未打开sealed/confirmation/环境密钥。标准库和现有openpyxl只用于metadata/legend/glossary；源Excel均只读未保存。
