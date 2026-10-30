# 原始证据、实际阅读范围与数据条件

2026-10-29。原始URL、获取时间、版本、响应字节/hash及失败见[retrieval.jsonl](retrieval.jsonl)。本轮2主题/8获取动作已用完，7成功响应共2,913,478B、Cell正文1次403，0自动重试。arXiv只取最新20条；PubMed命中38、仅取最新30条元数据及其原记录，没有遍历余页。这是定向核查，不是2025–2026全领域或全部最近先例综述。

## 已读原文与对研究的实际约束

| 原始来源/版本与日期 | 实际核读范围 | 能支持什么；不能据此声称什么 |
|---|---|---|
| [You Don't Need to Run Every Eval](https://arxiv.org/abs/2606.24020)，取得v2，首发2026-06-22；原件p4_every_eval.html | root选读§3数据/几何、§4 bias ALS/设置、§5探针和时间划分、§6.2可靠性、§7；非全篇/附录/代码复现。宽输出截断后补回必要小段，未覆盖范围不记已读 | 已有全局/行列偏置+rank2 ALS与联合拟合，贪心共享探针；§6.2已有ensemble spread、matrix support和hybrid风险模型。不能再把这三件事认领新骨架。84×133、2604值、23.3%是固定May主实验快照，v2另有August更新，不能混用。探针值计零误差，当前矩阵上挑探针不等于独立通用面板迁移验证；有限预测drop的分母条件须保留 |
| [Active multiple matrix completion with adaptive confidence sets](https://arxiv.org/abs/2605.02458)，v1，首发2026-05-04；p5_active_multiple.html | root读§2–3投影全部段落与显示式E1、Ex9、Ex16–21；未读全部证明/实验/源码 | MALocate主动选矩阵k，**矩阵内entry均匀随机**，不是主动指定任意entry。平方根矩阵lasso无需rank和noise variance作为调参输入，但有有界/均匀等假设。使用训练/误差分半与同位置两个独立噪声读数估误差；普通拟合汇总不提供此重复。实践singletons/duplicates划分有作者明确承认的难分析依赖 |
| [MCLRP](https://doi.org/10.1186/s12915-025-02457-8)，PMC12781783，主文JATS发表2025-12-03、更早公开未知；p6_mclrp.xml | root Sec11–14、notes3；发展代理亦选读方法；未执行代码/完整SI或核全结果 | 转录组PCA约束低秩/核范数、ADMM及MC/岭/SRMF近邻。CCLE491×24 activity area越大越敏感；GDSC655×119 AUC/IC50越低越敏感，不能当同尺度。重复10折CV不自动证明新药/新细胞独立外推。零初始化及标准化后非零定义Ω的文字存在需源码核对的mask语义，**未证明代码错误或泄漏** |
| [Informative Missingness in Nominal Data / NIMAA](https://doi.org/10.34133/csbj.0099)，PMC13181165，主文JATS发表2026-05-18、更早公开未知；p7_missingness.xml | root sec3/5/9；中性scout选读sec2–5/9；非全篇/代码复现 | NA是未知边而非真实零；已有二部图、complete submatrix、投影/聚类和常规填补。原文明确完整区结构保持不能保证MNAR缺失区重建；其引用链也有按缺失空间推荐组合，不能认领“缺失图指导选药”首次 |
| [UniPert-G2CP](https://doi.org/10.1016/j.cell.2026.06.005)，PMID42497867；electronic2026-07-25、issue2026-08-06，更早公开未知 | 原PubMed完整摘要及direct ArticleIdList；A级。Cell正文403，未取得方法/SI/代码 | 遗传—化学跨屏迁移是相关近邻；不能由摘要的universal/causal措辞确认已识别因果机制、普通数据足够或本候选已被完整覆盖 |

前两篇的正式会议/期刊身份未核，不称顶会论文。MCLRP官方代码链接由主文给出 `https://github.com/kunwangouc/MCLRP`，数据链接 `10.5281/zenodo.8127448`；本轮均未取得/执行，不推定可复现或许可。新论文作者代码一律not_verified。

MALocate关键式由原HTML math alttext实际核对：

`Rhat=(1/N)Σ_i(Y_i-<X_i,Mhat>)(Y'_i-<X_i,Mhat>)`

它估计的是 **`||Mhat-M||F²/d²`** 的归一化误差，不是未归一化Frobenius误差；`B=Rhat+8A² sqrt(log(d)/N)`；分配为 `argmax_k d_k² B_k T_k^(-1/p)`。重复、均匀采样和已知有界A不能因迁移到药筛被省掉。原文“上界下降确保estimation error non-increasing”的强表述未经本轮证明审计，不能转写为真实误差每次下降。

## 与用户CV/NLP多尺度、多模态启发的连接

复用已核的[H-Net/DC-DiT/SimMLM原文记录](../2026-10-29-multiscale-common-function/source_evidence.md)，本轮不重复下载、运行作者模型或把旧读范围冒称新全文：H-Net2507.07955v2的动态粒度、DC-DiT2603.06351v2的实际预算与多预算训练、SimMLM2507.19264v2的缺模态条件/贡献拆分，分别提供**处理分辨率、资源匹配、信息条件比较**原则。三者已见完整细输入/训练模态的条件不同于尚未购买的药筛读数；压token/latent计算不能自动省实验，随机dropout不能自动代表选择性缺失。

新的NLP评测矩阵先例又提示：一个少量共享探针可以帮助多个目标的思路已有直接实现；支持度本身也已有风险预测用途。可迁移的研究问题仍是“任务需要学到哪些方向、反馈怎样改变可用判断”；**本轮没有从这些原则推出一项新算子**。剂量是干预强度、细胞系是实验背景，不自动构成CV缩放式尺度树。SMILES是真正廉价附加输入，协议更适合作观测条件；来自另一张表不自动构成新模态。

## 便宜不等于可以错配：证据与主张分层

| 要判断什么 | 最低观测与条件 | 本轮资格状态 |
|---|---|---|
| 预测公开拟合药敏指标 | 来源/身份、拟合指标/单位/方向、测试窗及合法拆分 | 旧普通拟合表可用于其特定端点；不能改叫固定剂量原始功能 |
| 同一剂量/时间的跨块功能借用 | 数值剂量/单位、处理时长、终点/控制归一化、真实交叉读数与mask；不要求全矩阵完整 | 本轮0响应读取/下载，未取得合格动作/评定小包；不能称ready |
| 成组策略省测量且可靠 | 同合法菜单/成本、直接目标选项、控制/重复/失败/开批/等待计入，动作与后续未查询评定分离 | 未冻结H或执行；现稿无新增算法步骤 |
| 推断靶点或分子因果机制 | 区分竞争解释的靶点/遗传/独立功能证据及合适重复 | 不由普通药敏表、低秩方向或掩码推出；本轮不作该主张 |

常见实验会产生剂量点/控制/重复，不等于每个公开资源都公开这些层级。只需与主张匹配的廉价观测，而非为普通功能预测强加组学门槛。现有GDSC拟合IC50缺固定q与独立重复资格；PRISM24Q2、CTRP、sealed/confirmation响应和.env保持未读。

## 解析更正与来源登记

首次投影缺bs4报ModuleNotFoundError，未安装，改标准库HTMLParser。PubMed初版递归`.//ArticleId`混入ReferenceList的被引ID；在任何新增全文获取前改为`PubmedData/ArticleIdList/ArticleId`，主PMID取`MedlineCitation/PMID`；原XML不变。独立显示公式另存[equations.json](equations.json)，不以p文本缺公式推断原文没有公式。这些是工程事故，不是科学负结果。

DS020只按固定规则编目八条原记录，root回读direct路径验收ID；八条quote均字面匹配，但4条93/82/89/89字符超80上限，拒收这些格式字段并由root从题名取60字符短quote。原JSON不改，[原回执与验收](../deepseek/tasks/DS020/main_review.md)保留，未用字段通过代替科学裁决。

五条新增来源已按实际P/A级入共享库；两个主文JATS借generic supplement技术槽存放，**是原主文而非科学SI**，主PDF/HTML仍缺。[library_verify.json](library_verify.json)实际核验110唯一来源、96件论文文件；68 downloaded_html、13 downloaded_pdf、19 pending、8 restricted、2 abstract_only（唯一主行口径）；8代码快照关联7篇，54 not_verified、49 not_yet_checked，changed/errors/warnings为空。论文86.6MB、代码12.6MB为工具报告。只证明清单与文件一致，不证明全文阅读、方法成立、数据可得或新颖性。transductive/bilinear/batch design的精确最近先例仍未闭合，不在耗尽预算后续取或据此声称首次。
