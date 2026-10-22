# 撤药／再挑战路线：一手来源资格报告

2026-10-22，独立 advocate 源审查；本报告在任何新响应数据和后续实验结果之前形成。来源可用、任务可识别、方法新颖和性能有效是四个不同结论。

## 本轮边界与收据

预登记见 `PROTOCOL.md`。4 次 GET 全部完成，HTTP 200，共 **265,911 bytes**；无重试、重定向、作者联系、数据矩阵或作者代码下载／执行。`NETWORK.json` 保存 URL、UTC、状态、字节和 SHA256。4 个原始响应经本地 `Get-FileHash` 核对，均与收据一致。

| 文件 | bytes | SHA256 |
|---|---:|---|
| SEARCH.json | 725 | 14a90cd676c9b9dfbbfa9f266f5039102dfe17f0a15c936b770ec3d6509b320e |
| ABSTRACTS.xml | 104044 | e7f2ef007c4ff4c3261c353233be47940da099371d9546a218071de4766237bf |
| PRIMARY.xml | 146125 | 3c4e857e89b74dbf4b1d707cbdebf9740877cd465a64c902f5b0b87731c5b3dc |
| REPO_TREE.json | 15017 | c9f314e7e612ecc7185ebfca6cc9c8b6612ed6b630f7fd89ac6d5544b5c2317c |

投影阶段读了已发表 Methods、availability、设计相关结果段及图注。嵌套段落包含发表的模型拟合参数表；这些数值属于文献已暴露内容，不能称作本项目独立结果。本轮没有取得或解析生物响应矩阵，也未读取待出的 E. faecalis pilot 结果。

## 选中的一手论文

**Phenotypic switching as a non-genetic mechanism of resistance predicts antibody therapy regimens.** iScience，2024；PMID 38544569，PMC10966312，DOI **10.1016/j.isci.2024.109450**。全文来自 NCBI PMC。搜索只是日期范围内的窄查询，不代表完整系统综述。

其他三条仅读 PubMed abstract／元数据：PMID40414926（osimertinib/AP-1，2025）；PMID41303417（serum withdrawal）；PMID42546410（PARPi dormancy，2026）。它们的公开响应数据和本任务资格均未认证。本轮不再追加请求。

## 真正认证的设计

LIM1215、SW48、Caco-2 从单克隆起始；cetuximab 1 μg/mL + NK-CD16（E:T=1:1）挑战 72h，PBS 洗除，肿瘤细胞恢复 **1–7 天直到足够下一轮**，20 轮约 4 个月。R5/R10/R20 测功能；R20 再无 ADCC 压力传代，W10/W20 测功能；P/R5/R10/R20/W10/W20 扩增一代后冻存。W 的 cycles/passages 和叙述中的 generations 不能直接换算为固定小时。每轮不是持续携带同一批衰竭 NK 的实验。

标准 ADCC 检测另以肿瘤 5,000/well、NK 10,000/well、同浓度 cetuximab，4/24/48/72h，triplicates。CTG 用 `(B_sample-B_NK-only)/B_tumor-control`。若研究不同 NK 历史，该背景与其增殖／活性必须分别核查，不能把 CTG 一律当靶细胞死亡数。

这支持真实“治疗→撤压→功能再挑战”。它**没有认证**共同起点、等累积剂量的 A→W/W→A 成对顺序网格，也没有验证模型提出的连续与 3on/3、5、10off 方案之间的真实比较。后者是模拟。恢复时长受细胞数量影响，不能当均匀采样时间序列。

## 公开分子数据及可取得路径

- **GSE255674**：3 肿瘤细胞系的 P/R20/W20，triplicates。论文虽写 bulk RNA sequence，具体实验是 **Affymetrix Clariom S microarray**，不是 RNA-seq。
- **PRJNA1076459**：LIM1215 P/R20/W20 scRNA，triplicates 经 hashtag pooling；3,560 cells 为发表叙述，并非本项目重新计数。未查询 registry 样本级表或 raw 文件。
- 未认证 R5/R10/W10 的分子测量、每轮时点、独立 founder/clone 生物复现、功能样本与分子样本的一对一 join。

公开表达终点不能补造未实施的交叉 NK 历史干预。它们可作描述性先例，当前不能单独验证下文新的识别操作。

## 原论文已做的动力学

已有 S/R 两肿瘤亚群；on 时 S→R，off 时 R→S；S/R 有各自死亡率，杀伤效能随 `exp(-k t)` 下降，作者归因于 effector function 衰退；R 死亡还随 `exp(-w t)` 变化。scRNA 群比例初始化，主要拟合 LIM1215。P/R20/W20 的 R 死亡率分别拟合，部分参数不确定并固定一个死亡参数。

因此“可逆耐药、撤药记忆、间歇给药、两个群体的 on/off 世界模型”本身均有直接先例。on/off 的不交换也可由普通固定动力学产生，不能据此宣布发现隐藏机制或 RSI。论文 μ_RS 的正文拟合描述与表中计算来源不完全一致，本轮保留歧义。

## 官方仓库 manifest 身份

论文链接 `https://github.com/zhoujw14/ADCC_model.git`。只 GET HEAD recursive tree，完整 **tree SHA `d144baf5a841db27976c9db4507b2e91e6316730`**，`truncated=false`，60 entries／47 blobs。tree SHA 不是 commit SHA；也未认证其等于发表时 release。

| manifest 路径 | bytes | blob SHA |
|---|---:|---|
| model_estimation/data.csv | 420 | 31a43c95c2ea5ee44ee7c4fc27180914d6d298e3 |
| model_estimation/test1.mlxtran | 1812 | b4d70c0e4097a926169598f3706eb404540e28e7 |
| model_estimation/SRcell | 405 | c1077d9bb44f7e5a2ae7daf4b3a23125e108498a |
| mu_RS estimation/mRS.mlxtran | 1095 | 4b5264b5bafa183e310055410fdccb26d7fc94aa |
| single_cell_RNAseq/RNAseq.R | 12601 | ed753f55d06766d96decd62d02de68380e15a573 |
| Simulation_figure5/Sim_on_and_off.R | 7357 | 2020a9552cdc85ef863a52b6edb62784b518f505 |

只读名称、大小和 SHA，未取 README/code/data blob。`data.csv` 存在不代表其 schema、所有 functional truth 或交叉实验存在。`Simulation_figure5/result/*.csv` 按文件身份及论文图说明属于模拟，不能冒充真实 regimen 验证。

结论：认证了一个相关真实细胞实验和已有动力学先例；**未认证足以离线验证新识别／继承机制的数据闭环**。下一个文件给出的操作必须明确承认此缺口。
