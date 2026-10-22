# Lee 2012 实际药序来源身份资格

2026-10-22，Asia/Shanghai。登记协议 `PROTOCOL_ADVOCATE.md` 后执行6次primary HTTP请求，约2.5分钟。**认证到公开分子来源GSE30516；没有认证到可配对的多药序功能结局菜单。当前不是可执行世界模型/Agent/RSI数据资产。** 不将本轮访问不足等同原论文或补充资料不存在相应数据。

## 已直接认证的来源

原始论文 [Lee et al., Cell 2012](https://doi.org/10.1016/j.cell.2012.03.031)，PMID22579283，PMC3501264，NIHMS370678。Europe PMC primary metadata表明 `isOpenAccess=N`、`nihAuthMan=Y`、`hasSuppl=Y`。摘要明确 time-staggered EGFR inhibition 与 simultaneous administration不同，使用信号网络、gene expression和cell phenotypic measurements；这是作者研究概述，不是本轮完整药序/功能资产的认证。

官方 [NCBI PubMed→GEO link](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=gds&id=22579283&retmode=xml) 精确返回 `pubmed_gds` UID200030516；[GEO GSE30516](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE30516) 的官方esummary元数据将其与PMID22579283关联。

| 资产项 | 实际primary元数据 |
|---|---|
| accession/title | GSE30516, *Dynamic re-wiring of apoptotic signaling networks enhances tumor cell killing by DNA damage* |
| species/assay/platform | Homo sapiens；Expression profiling by array；GPL570 |
| sample总数 | 25 |
| 文件类型/项目 | CEL；PRJNA143289；GEO给定公开FTP根目录 |
| BT20 sample标题 | 0 minute n4；30 minute n3；6 hour n3；1 day n3，共13 |
| 字面MD sample标题 | 0 minute n3；1 day n3，共6 |
| 字面MCF sample标题 | 0 minute n3；1 day n3，共6 |

`MD`、`MCF` 在本轮只以原样标签记录，未用常识猜具体细胞系。BT20为肿瘤细胞标签，不能称原代人肝细胞。标题中的时间是sample time label，**不自动等于两次给药的间隔**；n3/n4是标为rep的样本，未认证独立培养或个体。未将25样本算25独立继承任务。

GEO summary原文也主张系统分析inhibitor/genotoxin的order/timing，并包括phenotypic responses和mathematical modeling；但一个series的文字摘要并不能证明所有表型原始值都存放于该series。这里只认证表达数据accession存在，未取CEL或processed expression matrix。

## 缺失与当前资格判定

1. **具体行动菜单未认证。** 不能从摘要补出每一drug、dose、先后顺序、lag、overlap、washout或终点采样。特别是早期阵列可能只测单药priming，而完整药序功能测量在另一实验；本轮没有足够元数据判定。
2. **分子→功能identity join未认证。** 尚无公开phospho/apoptosis/viability文件manifest、样本键、时间与药序映射；未认证每个context/action都有measured terminal response。
3. **替代行动是否完整未认证。** 作者定性声称顺序与同步不同，不等于多个context/多个drug order的完整replay矩阵。缺测动作不能用模型生成填上，更不能用单一成功药序包装后续任务流。
4. **继承/RSI任务资格未认证。** 现有25阵列来源只有三个字面context标签、极少时间，且药序未解码。不能证明足以化学/背景独立分成源任务、策略学习、未来共同起点meta改进验证。

因此状态为 `PUBLIC_MOLECULAR_ACCESSION_AUTHENTICATED / MATCHED_SCHEDULE_FUNCTIONAL_MENU_NOT_QUALIFIED`。本轮遵守≤6请求限制，在取得上述证据后停止；不启动新架构、功能数值/表达下载或性能实验。该结论没有重开已停止PTV/PRISM/O'Neil。

若后续独立决定查此源，最小下一对象应是GSE30516的**纯sample metadata**与原论文supplemental文件manifest，明确不读表达/表型响应值；只有exact drug-order-dose-time与实际apoptosis表identity能join、多个完整替代菜单成立，才有理由另登记dev-only开值。不能为了获得一个阳性例子继续下载所有mirror或把原论文图中结论当新实验。当前不建议把它指定为下一研究框架基准。

## 请求、失败与完整性

六次请求的URL、status、bytes、sha256与UTC记录在 `advocate_sources/NETWORK.json`，原始响应保留；合计HTTP body **13,477 bytes**。依次涉及精准paper metadata200、fullTextXML500、主PMC页403、错误GEO查询200、正确PubMed→GEO elink200、GEO esummary200。响应状态200不表示查询语义有效。

错误GEO查询使用了不支持的`[PubMedID]`字段，返回`FieldNotFound`及零结果；这不是“无GEO数据”的阴性证据。后续通过官方elink纠正并认证GSE30516，保留错误返回。

PMC page和错误GEO查询曾被并行执行，两个payload都保留，但共享aggregate ledger出现覆盖，遗漏PMC403条目。随后根据原始文件与工具控制台重建403条目的bytes/hash/status/URL，UTC明确记null；没有伪造时间，之后请求全部顺序执行。此缺口涉及来源记账，不涉及响应值或科学结果。原始来源名字在请求前检查存在并拒绝覆盖，六请求计数已重建为实际数。

没有请求原始CEL、表达矩阵、phosphoprotein、apoptosis或viability数值，没有训练、GPU、DeepSeek、真实实验或药物提名。所有脚本在 `research/intervention_schedule_qualification_20261022/`，所有本轮证据在此日志目录。
