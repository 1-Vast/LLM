# PHH肝毒性独立转题候选：限额元数据筛查，2026-10-21

**优先OASIS进入下一次schema/动作覆盖资格检查；DILImap暂缓。两者当前均不合格于跨背景继承或RSI确认。** 应用拟从肿瘤候选命中改为未见药物的安全剂量与毒性读出区分，须另建任务/端点/冻结；不改变PTV阴性结论，不拿新指标救旧结果。本次没有下载任何实验数值payload。

## OASIS：可达的功能矩阵，单一混池背景

Primary [PMC11785178](https://pmc.ncbi.nlm.nih.gov/articles/PMC11785178/) 对应2025-01-24所载bioRxiv v1，[DOI 10.1101/2025.01.22.634152](https://doi.org/10.1101/2025.01.22.634152)。实验为1085化合物×8预设浓度（0.01–100µM）×2重复，44h处理后CellPainting、LDH、RealTime-Glo MT，来源是BioIVT Liverpool **5-donor pool**。五供体已混合，故可识别背景数是**1**，不能当五个独立donor。这里的CellPainting是形态状态，不是RNA。检索出现后续期刊DOI `10.1016/j.cels.2026.101566`，但本次发布方打开失败，未将其当成已经核验的最新版本或认定与v1完全相同。

原作者已研究形态直接预测细胞毒性；新项目须超过这一直接基线。由于形态含细胞数与死亡信号，必须加入cell-count-only与同信息直接多任务模型。44h同批形态与功能不能证明时间因果或“早期状态预测晚期毒性”。

[官方分析库](https://github.com/broadinstitute/2024_09_09_Axiom_OASIS) 已pin当前tree commit **ca4872de0f1f0a4f203bee41271a6512b314a076**。只读代码/schema，无结果表：

- [`1A_download_metadata.py`](https://github.com/broadinstitute/2024_09_09_Axiom_OASIS/blob/ca4872de0f1f0a4f203bee41271a6512b314a076/0_prepare_data/1A_download_metadata.py) 指向公开S3 `cpg0037-oasis/axiom/workspace/metadata/{prod_25,prod_26,prod_27,prod_30}/{plate}/biochem.parquet` 与`metadata.parquet`。
- [`2A_format_metadata.py`](https://github.com/broadinstitute/2024_09_09_Axiom_OASIS/blob/ca4872de0f1f0a4f203bee41271a6512b314a076/0_prepare_data/2A_format_metadata.py) 声明well、plate、compound、concentration和`mtt_lumi`、`ldh_abs_signal`、`ldh_abs_background`、`ldh_abs`及归一化功能字段。代码会为缺列补null，因此存在列名尚不证明每个药/浓度都有功能值。
- S3 bounded listing HTTP200，限定prod_25的前12个对象；第一`plate_41002687/biochem.parquet` HEAD200，**28,654 bytes**，Last-Modified **2024-09-23 16:51:41 GMT**。没有GET Parquet body。由此确认的是公开对象存在和发布代码意图，不是完整矩阵覆盖或质量。

[Zenodo17067683](https://zenodo.org/records/17067683)，网页v1、发布2025-09-06，API version=null，dataset **CC BY4.0**。五文件共 **864,821,118 bytes**：CellProfiler413,433,180，CP-CNN48,201,019，DINO399,927,644，index2,524,798，metadata734,477。所有尺寸与MD5来自API元数据；0文件下载。代码BSD3不能替代数据许可；S3原始图片/原始功能文件条款仍须核对其自己的dataset说明。

**特别边界：`metadata.parquet`可能包含功能数值，不能为了拿药物名称就直接当纯无标签metadata载入。** 下一块须先只读schema并由独立工具拆出compound/dose/plate/well/replicate清单，数值结局留给外部盲评器。验证每药8剂量2重复是否完整、两读出与形态是否同well，三个被上游删除的不同显微镜plate如何进入coverage分母。随后才可宣布药物/药族留出的公开回放单元合格。

下一块若通过，应用可限定为同一PHH混池中未见药物的毒性剂量决策；以原子compound/chemotype为独立拆分单位，多剂量/同药双重复均锁在同组。无新背景反馈单位时，不检验支持药背景校正、更不检验跨背景继承/RSI。对机制的最小审问是：形态预测残差是否能改善未测药的功能决策，还是仅借助同well死亡读出或普通浓度曲线拟合。

## DILImap：原始训练RNA不公开，剂量选择也用功能

[Nature Communications](https://www.nature.com/articles/s41467-025-65690-3)，2025-11-13，DILImap300药×4 RNA浓度；24h PHH，单供体 **1917277-01**。协议先用LDH/ATP进行六浓度三重复功能筛选，并以IC10等信息选RNA剂量。它和DMG共享“结局生成了dose”风险，不能把dose当无泄漏输入。

[作者数据说明](https://pmc.ncbi.nlm.nih.gov/articles/PMC12615732/) 明确：训练原始gene-count矩阵专有且不公开；公开训练通路特征与验证数据，另列GSE308567和[dilimap.org](https://dilimap.org)。申请原始数据有用途/期限限制，不能把可读论文或有S3桶等同完整可下载干预训练集。全药全剂量LDH/ATP公开矩阵本次**未认证**，没有申请、联系作者或下载数值。暂缓理由是单背景、原始分子限制及功能菜单不明；并非断言通路级开发绝对不可能。

## 本项目曝光与复现

在写本记录前运行：

```powershell
rg --no-ignore --hidden -n -i -g '*.md' -g '*QUALIFICATION*' -g '*CATALOG*' -g '*MANIFEST*' 's41467-025-65690|PHH300|Axiom_OASIS|PMC11785178|toxicogenomics|OASIS' log research data/INVENTORY.md
```

exit1/no matches。仅证明所搜文本无匹配，不证明无历史开发或第三方模型训练曝光；下一块还须按数据源血缘核对。脚本 `python research/rsi_next_qualification_20261021/liver_metadata.py` 可复现S3前12对象、Zenodo文件清单及一个biochem HEAD，收据为 `liver_metadata_receipt.json`。没有数值实验、模型训练、DeepSeek请求或GPU；随机种子不适用。限额筛查至此停止，不扩到所有S3对象或下载864.8MB。
