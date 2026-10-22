# 独立序贯抗生素替代源：一个真实演化资产、公共功能菜单尚未认证

2026-10-22，Asia/Shanghai。固定PubMed查询找到22条记录，本轮仅取默认返回的前12条原始metadata/abstract；再对一个primary lead取全文方法。**3请求493,396 HTTP body bytes，均HTTP200，未超过登记的3请求/1MB，未下载任何数据矩阵、FASTQ或补充响应。** URL/status/hash在`NETWORK.json`，原始XML均保留。不是穷尽检索，不将未返回旧记录当不存在。没有重复Jeong/Tay3D或打开已关闭项目。

当前裁决：**一个真实多步抗生素演化/基因组+功能线索已认证；尚未认证完整公共action→state→function replay资产。** 不批准架构。以下最多两项精确primary leads，论文性能/终点均是作者报告先验，不是独立验证。

## Lead 1：Tripartite Loops Reverse Antibiotic Resistance

原始来源：PMID40478208，PMC12164588，DOI[10.1093/molbev/msaf115](https://doi.org/10.1093/molbev/msaf115)，2025，全文`TRIPARTITE.xml`，方法/链接摘录`TRIPARTITE_METHODS.json`。原文CC BY4.0。PubMed和全文Data Availability都明确**NCBI SRA BioProject [PRJNA1254677](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1254677/)**，用于作者的genomic data；本轮未查询该project身份表或下载序列。

与摘要空泛“可编程”不同，此处全文认证真实序贯实验：

- 基础背景为`E. coli K-12 substr. BW25113`，MH培养基37°C。作者另测试4个drug-resistant clinical isolates；本轮没有取得其strain→lineage→assay完整manifest，不能据此推断4个基因背景足够RSI。
- SAGE使用抗生素空间梯度培养7d，从板终端1.5cm提取耐药mutant。初始loop药物明确包括GEN/PIP/NIT；固定SAGE配方浓度列为5/40/80 μg/mL（方法参数，非本轮响应值）。这些浓度来自trial experiments，使耐药MIC超过clinical breakpoints，故不是无先验任意剂量发现。
- 每次SAGE后做3个flat-plate passage，药物为上一SAGE药，浓度为该mutant已测MIC的一半；时长2d、1d、1d。Figure1a明确MIC与collateral-sensitivity profiles在flat passages结束后测。真实序贯支路示例有GEN→PIP→NIT和NIT→PIP→GEN；不从这些例子推出所有六排列/全部prefix均测过。
- MIC采用broth microdilution、overnight37°C、visible growth判定；fitness为595nm吸光度24h growth curves及AUC。另有GEN uptake assay；这些是功能测量，不将genome变异自动等同功能或细胞内动态真值。
- WGS用IlluminaNextSeq2000/Breseq，以`CP009273.1`参考；本项目未读取变异值。方法明确用于uptake的3个resensitized strains也是被sequenced的3个，说明至少一部分分子检测是按终点结果挑选，不能当每个decision-prefix都有免费可用的前瞻genomic state。
- **灭绝不是简单终止。** 原文给initial失败lineage第二次相同条件evolution机会，并报告initial/final extinction。这可能是合理实验设计，但offline任务必须区分首次失败、重试动作、重新培养与真正不可恢复；不能只取最终幸存者计算最佳策略，也不能把重试当无成本。

上述实际过程有约11d/轮的适应/补偿演化，state可包含历史genotype、MIC及fitness。它不等于小时级药理cell-state恢复，不外推PHH或临床治疗；用作世界模型需按真实世代/培养状态和干预单位定义。半MIC flat passages是测量依赖动作，基线也必须知道并计其MIC查询成本，不可将其当固定免费日历。

公共资产边界：Data Availability**只明确genomic SRA**。全文存在supplement标签`msaf115_Supplementary_Data`，媒体文件`msaf115_supplementary_data.pdf`；本轮没有下载PDF，也未认证其中含可机器关联的lineage/schedule/原始growth/MIC表。基因组accession不自动提供功能表；“论文有supplement”不等于支持完整菜单replay。

必须先取得的identity keys：clinical/background isolate ID、founder、independent lineage、SAGE/flat passage index、actual challenge drug/dose、首次/重试/灭绝状态、MIC assay ID、growth run/replicate、sequenced sample→同一lineage/时点的对应。BioProject内部BioSample/SRA Run identifiers数量、prefix分支覆盖、每个动作的独立replicates都未核验，不虚构数量。摘要424+216 evolution experiments是作者规模，不等同640独立未来任务。

**是否值得下一步：** 可做一次outcome-blind supplementary/SRA metadata资格（需另登记预算），先查上述join和共同prefix之后的真实备选药。若只有终端selected-genome和论文汇总图，关闭“分子状态驱动完整闭环replay”；仍可作为已发表序贯演化先例。若有完整有限表，只能先支持跨实验query/update agent；同lineage自适应策略要认证真实状态条件分支/分配与positivity。三核心药/少背景可能不足heldout drug-family及RSI多阶段任务，不用时间/lineage复制掩饰。

## Lead 2：Systematic mapping of antibiotic cross-resistance and collateral sensitivity with chemical genetics

原始摘要：PMID39623067，PMC11726442，DOI[10.1038/s41564-024-01857-w](https://doi.org/10.1038/s41564-024-01857-w)，2024。仅本轮PubMed原始metadata/abstract，未取全文。作者使用已发表E.coli single-gene deletion library的40抗生素chemical-genetics data，推断cross-resistance/collateral-sensitivity，再以experimental evolution验证70项inferred interactions，并应用组合抑制耐药。它提供一个直接先例：**同一药对可因耐药机制不同而兼有cross-resistance与collateral-sensitivity**，所以仅按drug1→drug2固定pair表不足以代表细胞/遗传状态。

目前未取得该文确切dataset accession、删除株→药物→时点→功能keys或完整序贯动作菜单；PubMed记录没有DataBank accession。不要把40抗生素矩阵当temporal second-action screen，也不能从摘要64/70验证比例推断本项目性能。该lead的价值是有清楚genetic state+function系统测量的潜在线索及强常规机制baseline，尚非完整动态世界模型/Agent资产。

## 与目标的关系和停止条件

本轮前进是取得了Lead1可验证的实际序贯流程、公开genome accession及关键重试/测序选择偏差，不是证明世界模型、智能体、继承或RSI。未来若资产可用，最强对照至少包含MIC/最近growth+drug-history直接预测、经验collateral-sensitivity图、普通genotype-conditioned predictor/Markov模型、同状态/辅助监督动力学、普通重训练/continual、标准active learning与等预算schedule/program search。不能用genome-only模型输来证明显式世界模型必要；state测量/查询成本须统一。

若功能表与基因组/历史无法准确关联、必要action的真实结果不存在、只终端挑选样本、或独立背景不够继承/meta拆分，则停相应主张。若可构成科学实验选择replay，先预冻实际决策/utility/chemistry或genetic/context holdout，再开dev；对RSI仍需共同model/program/history起点及同k改进预算的m0/m1/m2检验。本文不建议为“再多一个数据集”跳过独有操作与实际用途资格。
