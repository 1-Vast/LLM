# R2 数据来源、15重叠键与板布局资格

2026-10-26。本worker仅读第二轮brief、第一轮原始XML与metadata映射，未读协调者新候选。用maestro解释器，未安装或运行上游代码，未加载Viability、Raw count或任何sealed/holdout/reserve值；未修改reference公共表。设置：requested_model/effort未向worker暴露；effective_model/effort unknown。

## 主要发现

15个重叠标签键有明确的库布局解释路径：原文Methods的 **Combination plates** 明确说206种药中4种重复，以210槽均分14 row plates和10 column plates。实际公开metadata把 **Axitinib** 放在数字库 **Plate 1的列17** 和 **Plate 5的列22**。第14轮和random validation使用不同数字库板，却共享字母库Plate I及剂量。因此不同板ID不保证药物实体键不重复。

这使“标签重叠必然说明论文采集错误”的推断不成立；但也不能因此称random validation在实体键上完全未见。药物供应商/批号/盐型身份尚缺Supplementary Data 2核验；这里证明的是同名同剂量的库槽重复，而非所有化学实体身份已经验证。确切原因得到原文设计与metadata互证，仍需保留该身份限制。

## 精确映射

重用第一轮 `independent_overlap_mapping.csv`，只含10列白名单。键为原始Cell line标签与无序药物剂量对；15键全部属于 `MSKEWS-33838`，Axitinib `0.1 uM` 加下列药 `1.0 uM`：Mitomycin、Trametinib、Fisetin、Ensartinib dihydrochloride、PF-5274857、Vinorelbine、Daunorubicin hydrochloride、Amuvatinib、PD 407824、Crizotinib、I-BRD9、Bortezomib、LDC000067、Dacarbazine、Vandetanib。

| 期别 | 原始Plate | 原始文件名关键部分 | 位置 | 白名单记录数 |
|---|---|---|---|---|
| 第14轮 | 231 | `MSKEWS38338_Plate 1_0.1uM + Plate I_1uM_2_11012022` | Axitinib在列17，A–P行 | 15组合键；另1控制孔不在组合重叠表 |
| 第14轮 | 232 | `MSKEWS38338_Plate 1_0.1uM + Plate I_1uM_1_11012022` | 同列17 | 同15键 |
| `validation (random, round 15)` | 267 | `MSKEWS33838_Plate 5_0.1uM + Plate I_1uM_1_11222022` | Axitinib在列22，A–P行 | 同15键 |

文件名日期标记分别为2022-11-01与2022-11-22；本次只认定它们是文件名信息，不把它们自动认证为独立培养日期。Cell line字段为MSKEWS-33838，训练文件名另写38338，正文细胞为MSKEWS-38338：存在拼写不一致。不能仅凭文件名把33838与38338当已认证同一细胞株；原数据字段已把三板归同一标签，故标签重叠计数成立，而细胞实体认证仍需原始样本字典。

更广的metadata支持：同细胞第6轮Plate79的 `Plate 5_0.1uM_Plate H_1uM` 同样列22为Axitinib；第5轮Plate69的数字Plate1同样列17。这不是只依据validation某一孔的临时解释。全表Axitinib位置记录存 `axitinib_design_locations.csv`，共71个分组；只解析设计列。

## 数据来源索引核验

先用GitHub connector读取已点名 [tansey-lab/batchie](https://github.com/tansey-lab/batchie)：根目录、README、docs、nextflow目录。README公开数据格式为Screen对象；其retrospective来源链接12764821。根与docs目录没有已标示的prospective plate/drug CSV索引，未对整个仓库穷举。connector原始结构化输出已存sources，未克隆/执行仓库。

随后仅打开3个已点名Zenodo公开API record，原始JSON和URL/status/bytes/SHA256 receipts在sources：

| 官方记录 | 实际文件索引 | 与当前问题的关系 |
|---|---|---|
| [12764821](https://zenodo.org/records/12764821) | `merck_2016.screen.h5`、`nci_almanac.screen.h5`、`gdsc_sq.screen.h5` | 回顾性数据，不是15重叠键的prospective药库映射；未下载h5 |
| [12765294](https://zenodo.org/records/12765294) | `tansey-lab/batchie-v0.0.1-zenodo.zip` | 初版源码归档，不是独立药库/培养元数据；未下载源码zip |
| [13871987](https://zenodo.org/records/13871987) | `PAIR_SCREEN.csv`、`TRIPLET_SCREEN.csv` | prospective数据，准确索引中没有单独plate/stock/culture字典；本次未重新下载响应CSV |

原文XML（第一轮已获取，SHA256 `26676788f66df184c07fa1bd7b9d385c040a9933a1b71be52c03b17c9c7c4e8c`）明确Supplementary Data 1为细胞/培养条件，Data2为药物/来源，Data3为实验流程。XML media href和文件大小分别为MOESM4 xlsx13221B、MOESM5 xlsx28483B、MOESM6 pdf74915B。未把64MB Source Data（MOESM8）下载/读入。

按原文DOI及media href定位publisher CDN的小xlsx，两个请求均SSL `UNEXPECTED_EOF_WHILE_READING`；MOESM5做一次同URL requests transport重试仍失败，停止。没有关闭TLS验证、猜测其他端点或绕验证码。PMC HTML出现recaptcha即停，Europe PMC HTML工具不可访问，使用已有XML。药物来源表未取到，不能声称已核供应商、批号、盐型或14×10完整布局。

## 独立培养、重复和功能回放

原文P级定位（抽取片段及section名保存在 `sources/xml_design_passages.json`）：

- **Study design**：1–10轮单板；11–15轮duplicate；两次viability差>0.5的孔被QC标记。
- **A prospective pediatric sarcoma study with BATCHIE**：PhaseII用independent duplicates过滤失败孔。这支持作者的“独立重复”设计措辞，但不足以认证每对CSV file来自独立培养、不同传代、不同接种批次或不同培养瓶。
- **Cytotoxicity assay**：按细胞优化密度和培养基接种，药物处理72h，再Alamar Blue24h读取；不能误称缺乏时间协议，也不能把Alamar代谢荧光等同细胞内engagement。
- **Validation of BATCHIE predictions on random unseen combinations**：选择剩余空间随机板，每个phaseII细胞1板，MG-63 QC失败排除；“板没有重叠”须区分库槽与实体键。

可支持的最窄功能回放资格：第14轮231/232可构成一个duplicate训练/反馈块，随机验证267包含同15标签键的后期重新测量，且Axitinib由列17移至列22。若未来授权打开response并由独立评估者冻结读取，这15键可用于**同药物标签、同细胞标签、同剂量、跨板位置/时间标记的功能重复性检查**。当前只完成metadata，不报告测量相关性、收益或通过。

不能支持的升级：

1. 不是未见药物或未见细胞测试；第一轮复算random validation没有新药/细胞标签。
2. 不是已证实独立培养；原始接种批次/传代/culture ID未取得，文件名日期不替代这些字段。
3. 不是匹配engagement或独立机制金标准。正文DepMap RNA/CRISPR用于正交合理性分析，不是这些键在同剂量同时间的target engagement。
4. 不能把response派生Failed QC当预测前免费信息。15键在第一轮“QC-pass组合”定义下产生，若未来做实验应先固定使用QC的时点与规则，或将其作为事后可评分资格，不能用于伪前瞻动作选择。
5. 原始未见组合评分可在排除这15标签键后保留第一轮计数3397个QC-pass非重叠validation键（原validation共3412唯一键、3448行）；这仍是同药/细胞库组合补全，不能替代跨任务泛化目标。

## 本次预算、脚本与失败

新增定向query恰好2条：`"41467_2024_55287_MOESM5_ESM.xlsx"`；`"BATCHIE" "Axitinib" "plate"`。打开已指名资源与原始索引不另立搜索目标。继承前轮17query，worker新增2；全轮pass计数由协调者汇总，不归零。

`source_metadata.py`只获取固定record元数据并保存receipt；`map_metadata.py`仅pd.read_csv(usecols=10列白名单)，输出mapping_summary.json、overlap_metadata_reused.csv、axitinib_design_locations.csv。首次运行末尾打印调用Index.eq报错，已改为Index比较，复跑退出0；报错发生时无响应列读取。没有上游代码运行、依赖安装、API模型推断或公共reference表更新。

结论：布局重复已足以解释为何板ID分离仍出现15同标签键；确切stock/cell实体和独立培养仍未认证。可把后期测量作为受限功能重复性审计候选，不能宣布独立生物重复或机制真值，也不能以它取代原目标的跨细胞/药物/任务迁移验证。
