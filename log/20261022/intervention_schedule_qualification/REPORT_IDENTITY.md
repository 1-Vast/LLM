# GSE30516 样本身份独立审计

2026-10-22，functional auditor。**25 个 array 样本现已精确认证为 erlotinib 单药处理后的转录采样；GSE30516 不能单独提供本目标所需的实际多药先后/同步/反序行动及配对凋亡结局菜单。** 这是该 GEO 分子资产的可用范围结论，不是否定 Lee2012 论文中的药序效应，也不证明论文其他附件没有功能数据。

## 实际 sample 条件

先读 `ADVOCATE_SOURCE_REPORT.md` 和官方 PubMed→GEO 的 accession 证据，再登记 `PROTOCOL_AUDITOR_IDENTITY.md`。最终成功访问的是 [GSE30516 的 sample-only brief metadata](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE30516&targ=gsm&form=text&view=brief)。独立 worker 只导出样本身份和协议白名单（`auditor_sources/SAMPLES_BRIEF_METADATA.json`）；25 个 GSM accession 与原 official summary **完全一致，无缺/额外/重复**。全部 Homo sapiens、RNA、GPL570、GSE30516。

全部 25 个 sample 的 treatment characteristics 均为 `10 µM erlotinib`，treatment protocol 均为 `Erlotinib was added to a final concentration of 10µM`。growth protocol 说明接种后先允许贴壁 24h 再给 erlotinib，不能把此 24h 当两药间隔。按样本 metadata 原字符串，条件为：

| cell-line 字段 | erlotinib 后采样时间 | array sample 数 |
|---|---|---:|
| BT20 | 0 minutes | 4 |
| BT20 | 30 minutes | 3 |
| BT20 | 6 hours | 3 |
| BT20 | 24 hours | 3 |
| MDA-MB-453 | 0 minutes | 3 |
| MDA-MB-453 | 24 hours | 3 |
| MCF | 0 minutes | 3 |
| MCF | 24 hours | 3 |

这将 scout 的字面 `MD` 标签认证为 MDA-MB-453；`MCF` 的 cell-line 字段仍只有 `MCF`，**不猜为 MCF7/MCF10A 或其他亚型**。n3/n4 是 released array sample/rep 标签，不自动认证为独立培养、供体或独立后续研究任务。0-minute sample 仍有同样的 erlotinib 标签，不重命名为已认证 vehicle control。

这 25 个分子样本没有第二种药、先后/反序/同时给药 branch 的 treatment metadata，也没有这些 branch 的分子采样 identity。因此其时间轴是单药 erlotinib 后转录采样；不能将论文摘要所述 inhibitor/genotoxin 药序效果直接赋给这 25 个 GSM，不能把这些样本当已测完整药序世界模型 replay。

## 补充文件和协议完整性

每个 GSM 的一个 `Sample_supplementary_file` 均为带具体 sample accession 的 `.CEL.gz`，共 25 个不同文件链接，完整 manifest 在 `SAMPLE_IDENTITY_CENSUS.json`。这是该 brief sample metadata 里的补充链接范围，**不是完整论文 supplement manifest**。本轮没有认证到含原始 apoptosis/viability/磷蛋白功能响应的文件名、sheet/schema 或 sample→功能 join key；没有下载任一 CEL、processed matrix 或功能表。

label protocol 说明 biotin cRNA 的方法；data-processing 字段列明 R/affyPLM/preprocessCore/gcrma/affy/Biobase 版本，仅是方法 metadata。全部 25 个 hybridization-protocol 文本却写 `GeneChip Drosophila Genome Array`，与相同 sample 的 Homo sapiens / GPL570 字段明显不一致。保留该文字冲突，不自行校正，不猜它究竟是模板复制错误还是实验平台问题；完整 metadata 协议可靠性仍不能只靠复制字段认证。

资格状态：`ERLOTINIB_TRANSCRIPTIONAL_PRETREATMENT_IDENTITIES_AUTHENTICATED / MATCHED_DRUG_ORDER_FUNCTIONAL_MENU_NOT_QUALIFIED`。若把该 accession 单独指定为完整药序世界模型、研究 agent、继承或 RSI benchmark，应停止这项指定。若未来另有确切的公开功能文件证据，需重新登记其键/完整行动菜单访问资格；本报告不授权继续扩源，也不将未取得文件写成全体不存在。

## 访问格式失败、显式修订与资源账

原始两请求计划先取 family MINiML，再取 series-only SOFT。第一个 `targ=all&view=full&form=xml` 请求 HTTP200，但达到 **2,000,000-byte 硬上限**；worker 截断并关闭，不再发原计划第二请求。没有解析/输出其数据表。此宽 family source 包含庞大平台内容，属于**来源形状失败**，不是生物科学阴性结果。

另行登记的 offline recovery 只在已保存字节里定位第一个 XML Data-Table，从其前 **10,492 bytes** 的 metadata 前缀安全解析，得到零 sample/series entries；没有解析其后的平台/响应行。这一代码是后增 recovery，不伪称最初冻结代码。

随后 root 明确授权并在 `auditor_sources/AMENDMENT_BRIEF_METADATA.md` 事前登记一个**独立修订请求**：`targ=gsm&form=text&view=brief`，新增最多 65,536-byte body。该请求实际 HTTP200、**57,292 bytes**，未截断、未遇 sample_table_begin、25 样本完整恢复。不得把最初 2MB 隐去或称原计划干净通过。实际共两次新 HTTP 请求，消费 body 总计 **2,057,292 bytes**（原始 2MB + 显式新增 57,292）；没有第三次请求/重试。

每次 source bytes/hash/status/headers/UTC 在各自 `NETWORK.json` 和 `BRIEF_NETWORK.json`，raw bytes 封存在 `sealed_source/`，未由研究者打开。独立 worker 的 SOFT 路径在任何 sample_table_begin 前截止；MINiML 路径不会将 Data-Table 文本导出。白名单包括身份/处理/label 方法中的数值剂量与时间，不包括分子或功能响应值。该隔离是进程/数据流约束，不是 OS 加密/权限保证。

最初一次 pytest 的 Tee-Object 因 log 子目录未创建而退出，未发生源访问，记录在 `PRE_ACQUISITION_FAILURE.md`。创建目录后，初始代码 final 6 项、prefix 2 项、brief 1 项，共 **9 项不同合成检查通过**，包括数值 sentinel 不泄漏与遇 table 停止；原运行日志全部保留。

`auditor_verify_identity.py` 实际完成 **229 项 PASS 检查**：最初 8 个冻结输入 hash 未变、修订请求前 worker/协议 hash 未变、两次 source 实收长度/hash、25 GSM 集合、字段白名单与单药协议、平台/series/supplement 身份及消费 bytes。verifier 只用白名单投影，未解码 source 表行。它验证来源与身份，不验证生物效应、世界模型或 RSI。

所有新增代码以 `auditor_` 命名存放 `research/intervention_schedule_qualification_20261022/`；本轮原始字节/协议/测试/失败/冻结/执行记录在 `auditor_sources/`，本报告在其上级 qualification log。没有启动架构、数值响应开值、模型、GPU、DeepSeek 或真实药序实验。
