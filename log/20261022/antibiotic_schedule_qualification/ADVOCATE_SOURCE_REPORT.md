# 3D微菌落抗生素时序来源：实际取得内容与资格

2026-10-22，Asia/Shanghai。**本轮只认证到原始摘要和书目信息；没有取得方法全文或公开data/code manifest，故真实处理—轨迹—功能菜单 `NOT_QUALIFIED`。** 不将访问失败解释为作者没有数据或只upon-request；这两项也未获认证。没有新机制或架构批准。

## 来源及已经知道的应用

Jeong et al., *Massively multiplexed microfluidics maps combinatorial and sequential antibiotic responses in 3D*，2025-10-31 preprint，DOI [10.1101/2025.10.30.684665](https://doi.org/10.1101/2025.10.30.684665)，PMID41278959，PMC12636614。根代理先前取得的PubMed摘要为本轮线索。本轮官方NCBI EFetch再次核到相同作者、title、DOI与abstract，状态为preprint，未据此认定同行评审。

具体可考虑的应用是**3D水凝胶内细菌微菌落抗生素配伍/先后时序的体外研究**。这是从人肝细胞任务转向抗感染药物schedule研究的明确领域变化，不称原代人细胞、临床疗程或对患者处方。微菌落/群体状态也不自动等同完整单细胞世界模型。

摘要作者声称：512 independently programmable hydrogel chambers；自动化live-cell microscopy追踪10,000 colonies、约half-million单菌落图像；改变hydrogel stiffness和nutrient timing；同时与时序给予antibiotic pairs，覆盖2,700 drug–dose combinations。上述都是**作者摘要的规模/功能陈述**，不是本轮独立复现或实际可下载文件数。

`independently programmable`描述chamber可独立设定程序，不能作为512独立生物背景/实验run；10,000 colonies也不能作10,000未来继承任务。摘要把growth、drug response、morphology均联系到同一成像平台，不能凭措辞把它们当相互独立测量。early morphology→future growth在严格帧时序下可以是合法任务，但若终点和输入使用同帧/同size feature会造成目标泄漏或普通growth extrapolation；具体provenance未取得。

## 尚未认证的必要身份

| 问题 | 本轮状态及禁止推断 |
|---|---|
| 菌株/背景数 | 未认证具体strain、wildtype/mutant、independent culture/run与colony/chamber层级；不能猜为E.coli或声称多菌株继承。 |
| 药物/剂量 | 未认证drug names、剂量网格、单位或每对药完整条件数；2,700组合不是可执行action table。 |
| 时序/切换 | 未认证A→B的lag、duration、washout、追加/overlap与液体置换；不得把sequential自动解释为纯washout。 |
| stiffness/nutrient | 摘要确认研究这些因素，但level、factorial交叉与药序共同覆盖均未认证。 |
| 决策时state | 未认证哪帧/时间、哪些molecular或morphological features真实已测；没有分子assay承诺。 |
| 功能终点 | growth/morphology的帧/track/feature定义、早晚独立性、失败denominator及重复关系未认证。 |
| 第二动作分支 | 未认证相同first-action/history/prefix下B/C替代结局是否完整；静态schedule之间对照不自动支持同一colony的state-feedback策略。 |
| 公开source/menu keys | 未取得data accession、代码repository、文件manifest或drug/run/chamber/colony/time join键；也未认证upon-request。 |
| 真正独立任务 | 无从计算strain/context/action完整菜单数或可分离的source→future task流；不能用chamber/dose/time复制任务。 |

## 三次请求与真实访问层级

预登记 `PROTOCOL_ADVOCATE.md` 限定最多3次新增请求/10分钟，本轮3次均顺序执行，单writer ledger，在请求前检查同名文件并拒绝覆盖，失败先写原始body及receipt后再raise。

| 请求 | 结果 | 可用内容 |
|---|---|---|
| Europe PMC `PMC12636614/fullTextXML` | HTTP500，151bytes，`advocate_sources/PAPER.xml` | 错误body；不是paper XML，不应作为全文解析。 |
| NCBI PMC EFetch | HTTP200，7,020bytes，`PAPER_NCBI.xml` | 只有front+abstract，**无body**。XML原文注释：`The publisher of this article does not allow downloading of the full text in XML form.` 不把200当全文成功，不绕过该格式限制。 |
| bioRxiv原站 `...684665v1.full` | HTTP429，12,010bytes，`BIORXIV_FULL.html` | 访问限制body；未重试或改mirror。不能当方法HTML。 |

合计3次scripted GET、HTTP response body **19,181 bytes**。URL/status/hash/bytes/UTC保存在 `advocate_sources/NETWORK.json`；原始失败body均保留。自动抽出的 `advocate_sources/PAPER_TEXT.txt` **仅有NCBI返回的abstract**，文件名不意味着取得全文。没有取得官方data/code manifest，因此不再把剩余请求移到猜测repository，也未超出注册预算。

## 资源决定及范围

当前状态为 `ABSTRACT_SCHEDULE_CLAIM_AUTHENTICATED / EXACT_INTERVENTION_STATE_FUNCTION_MENU_NOT_QUALIFIED`。这是一项有真实时序平台叙述的来源线索，优于凭持续暴露的时间标签编造第二干预；但本轮未达到可执行资产身份认证。**不下载图像、响应矩阵、药效数值或训练模型，不以这项线索启动新架构。**

若后续能够合法取得作者公开方法与manifest，先核共同prefix的真实分支、所有尝试/失败、各层独立单位及early state/late growth来源，才可定义数值任务。静态已测schedule可支持跨实验query/update research agent的离线研究；若同一colony没有真实反馈分支，则不能声称部署了state-feedback schedule controller。若growth主要由count/area或早期增长率解释，直接growth extrapolation、dose/order predictor、普通系统辨识与重训应成为必要强比较，不能把同一成像信息只给world一臂。

本轮代码全部在 `research/antibiotic_schedule_qualification_20261022/`；日志/协议/来源全部在本目录。未读取单样本数值、图像、表达/形态矩阵，未运行GPU/DeepSeek/模型/真实实验，未对任何抗生素组合提名。旧Lee2012来源预算与不合格结论保持结束。根代理已收到请求状态与边界，反方也已收到真实可读文件路径；不把其未读到的方法当已完成跨源核查。
