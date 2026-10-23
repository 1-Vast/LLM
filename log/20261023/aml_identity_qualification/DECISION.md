# AML身份核查：获得真实格式证据，停止当前未认证的功能预测入口

2026-10-23。完整目标 **ACTIVE / NOT_ACHIEVED**；本轮 **PROGRESS**，非全局阻塞。当前具体决策：**STOP_AML_BASELINE_DRUG_SPECIFIC_FATE_UNTIL_IDENTITY_MANIFEST**。不构建founder词典、不启动RNA/功能数值拟合，不把身份诊断当作新方法性能。

## 真实执行及新证据

1. 本地完整投影既有GEO SOFT样本/处理/文库/关联信息。独立支持方指出pre/post MULTIseq样本的description明确写“Antibody Capture in processed data files”，因此sample supplement NONE并非没有处理后MULTIseq信号。
2. 真实下载官方series声明的pre/post features与barcodes四个文件，全部HTTP200；未请求matrix。Pre有36604 Gene Expression与8 Antibody Capture特征，标签HL1/HL2/HL3/TF1/TF2/TF3/OA1/OA2。Post同样36604+8，标签BC1..BC8。GEX barcode文件分别28645和26524个唯一16位条形码，均带-1后缀。上述数字是标识文件基数，不是生物独立任务或功能结果。
3. 原预冻结语法要求readName第二字段全为DNA；对每个旧4096压缩字节前缀的首记录均失败。原合约/代码/结果单独seal保留，没有重写失败。首记录受限诊断确定第二字段长31、7个下划线字段/38列/第三字段整数语法均成立。
4. 独立质疑方新取得官方SingleCellLineage tree和README，commit0efc48dd02994029ec5fd6f56d6197fab9aea704，README SHA256 e496d5e3368a1a18d1c04721ceaf3946df658b4d07716ba6fbc17af1d14b2a66。README184–187明确示例28nt+FWD，前16为cellBC、后12为UMI。根的全字段DNA假设过强，不是原始文件损坏证据。依据这个独立新来源，另冻v2，固定28nt+FWD而不试其他后缀。
5. v2对相同非随机tiny前缀全部完整记录检查：pre29/29、post36/36语法通过，各有29/36不同barcode；与同声明GEX集合直接匹配均为0。未检索转换、reverse-complement、模糊匹配或读取founder标签。**这只否定了这些prefix的直接匹配候选，不能证明全库不可连接或必须采用某种chemistry转换。** 混合library、GEX过滤及namespace等仍是竞争解释。原v1因0valid而输出的direct_matches=0没有可用分母，应读为不可评估，不能作为零恢复率。
6. 两个准确关联的BioSample accession通过官方ENA XML取得，pre/post均只给混合细胞系与一般处理信息，没有tag→flask/time key。既有MOESM3的Supplemental Data15只做text-only读取，确认是lineage/clone PCR引物，不是MULTIseq培养物映射。未读取其他sheet数值或公式。
7. 论文链接Zenodo metadata给出实际5,590,433byte代码归档；下载成功，官方MD5 a2911704152af9f9312c8e0f419fe12b匹配，SHA256 e70fa26194426fc404222ff2f768b0f0d42d6ebf7c8b1738292ed566fc5d370a。ZIP102members、86files与pinned仓库86file路径集合一致。仅五个已审关键Python/R身份处理文件读bytes做比较，全部逐字节一致。未执行作者代码、未解码归档树/图/guide/FASTA值。未声称整个归档每个内容与仓库均一致；这些已核查来源未增加所需身份契约。

## 独立与实际交叉审查

constructive/INDEPENDENT.md先封存，提供样本字段原文/行号、Methods段落、代码sample→time声明与缺失join；critic/INDEPENDENT.md先封存，独立核查chemistry、suffix、namespace并取得新官方README。随后双方实际交叉，另封constructive/CROSS_ADDENDUM.md、critic/CROSS.md及v2审查，不覆盖原稿。根执行65record的受限identifier检查，代理仅审核结果/代码，不冒充独立数值复现。新归档比较在交叉后由根执行，未声称已被他们独立复核。

支持理由：真实Antibody Capture元数据存在，作者明确读取GEX/FB转换表，官方pipeline记录格式可认证；因此“没有可重建数据”的全局断言不成立。反对意见被采纳：HL/TF/OA名字仅相容，不能把数字猜成replicate/flask/time；BC1..8仍匿名；README示例不是AML完整pipeline版本/化学/方向证明；prefix零匹配也不能补成特定转换证据。

双方接受的硬条件仍缺：实验适用的FB_bc→GEX_bc规则或认证identity rule；library/GEM routing及条形码namespace；MULTIseq feature→细胞系/培养物/处理/实际时间key。Baseline-only tag词典只能定义baseline可检测、可明确分配的founder总体，不能用endpoint共现/丰度重聚类补齐身份；共享多integration tags需冻结歧义拒绝规则。未匹配不等于灭绝/新克隆。样本身份、功能测量和独立培养任务是不同条件。

## 为什么现在停止这项数值入口

已按预声明有限来源完成真实检查，身份契约仍不足。继续下载GB级raw或读取RNA/endpoint数值来猜标签，不会认证丢失的实验语义；它会使功能测试依赖选择后的解释。停止的是“当前可用来源下的pretreatment→drug-specific fate比较”，不是整个AML数据集/该论文无效，不是所有公开来源都不存在映射，更不是整个研究目标阻塞。

重入条件必须是一个具体新公开artifact：sample-tag→culture/time manifest、实验适用chemistry whitelist/identity规则及library routing，或等价且可审计的处理后annotation。只增加更多同源细胞、更多匿名tag、不同噪声或一般10x翻译表不满足重入条件。没有这种新证据，不重复同一metadata检索或调解析规则。

## 对完整研究目标的影响与下一阶段

没有新预测性能、功能增量、新更新规律、world-model必要性、agent优势、继承、联合或G1/G0进步证据。前Emerald普通预测正信号及固定anchor STOP、CDK等历史阴性结论保持不变；没有打开保留标签。本轮进展是一个新可复现格式诊断、实际公共身份数据获取及对具体数值入口的有据停止。

下一阶段回到机制与可执行任务的联合筛选：要求候选同时给出明确、可被强常规方法反驳的更新差异，以及具备已认证干预/功能/任务身份的独立数据单元。不要以另一个未闭合的功能桥无限延迟最小证伪，不因普通数学家族名否定候选，也不把已知操作重命名。先检验功能与决策增量，再分别验证world/agent/inheritance/joint；改进策略G1/G0还须共同起点、同历史、同总成本及独立后续任务。完整目标未达成，继续active。

## 成本与完整性

本轮root8次公开逻辑GET、critic2次，共10次，全部200。无DeepSeek请求、GPU拟合或湿实验；原生代理精确模型/token/货币费用未暴露。逻辑请求不能当完整transport/redirect/retry次数。COST_LEDGER.json列实际receipts。代码research/aml_identity_qualification_20261023/，所有来源/诊断/失败/评审在本目录。VERIFICATION.json检查前166文件checkpoint及既有48/84文件和本轮各封存；局部hash不修复历史全局provenance drift。
