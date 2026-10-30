# 本轮来源、条件与实际阅读范围

2026-10-28。4/4次查询已用完，3/3篇新增核心来源已恢复。Q1是已知CellChain编号定点取元数据；Q2–Q4为Europe PMC专题查询，返回5/7/12条，均未分页。此前主题轮的6次查询不重新计为本轮成果。原始返回、时间、URL、字节数和SHA保存在sources/*receipt.json及source_summary.json。原生web工具在本轮中途重新出现；随后只定点打开相同原始页面与补充链接，没有新增主题搜索。网页工具对补充件报cache miss，而官方media URL经urllib实际下载成功；cache miss不解释为出版社拒绝或原数据不存在。

## P1 CellChain，arXiv:2610.16346v1，2026-10-12

全文HTML已落库。实际阅读：主文2.1–2.3的实体/条件对齐、任务目标和证据分配段，3.1实现与3.2部分指标段；Appendix D的Drug Reference-History Construction、Signal Diagnostic、Condition-Level Measurements开头。没有逐表复算18个模型；没有下载benchmark或实现，E节尚未完整阅读。不可标F级。

可核事实：药敏任务把query PRISM AUC隐藏，development历史与query药物分开，控制history归属匹配/交换；固定cohort上的简单历史均值规则达到64.2% compound-weighted accuracy。作者把此诊断解释为选定cohort的post-selection informative signal，并限制到该cohort。上述百分数是论文报告，不是本Agent复现。

对本项目的限制：跨尺度证据图、输入历史反馈、查看决策变化已有直接先例；单纯把同样工作接到Agent不能作为新贡献。CL1的待检验差异仍是实测锚定程序实际中介响应、以及共同反馈能否改善未测对象。这里需要同信息的普通历史/数值预测基线。CellChain的controlled evidence comparison不能自动升级为机制因果证明。

原始HTML sha256见cellchain_receipt.json；库文件reference/papers/arxiv-2610.16346/paper.html。

## P2 Khoshkenar et al.，Scientific Reports，2021，10.1038/s41598-021-94941-8

这是保留的原始生物学证据与资源线索，**不是2025–2026最新算法工作**。Original JATS已取得，实际读Sec3（bulk ERK）、Sec6（单细胞恢复与后代）、Sec9/11/12/14的体系与测量段；补充DOCX正文XML与包清单已检查。没有复算原图统计。

原文直接连接最初4h信号恢复与7天后代数量，Fig4记录180个始祖细胞；补充Fig4文字明确两次不同日实验。该原始研究已提出并观察这种关联，不能冒称本项目新发现。方法中的不同测量采用不同密度与处理程序，72h dose-response段另有1h给药后洗脱；不能默认所有面板同一暴露。pERK是下游近端通路读出，不是直接BRAF占据。

实际资源：609,157 byte官方DOCX，SHA `6b2ab2a92d8585675b6711ada8412b8143a5d835f299052345c208d1d53ef8fd`。包内4个media条目、0 charts/embeddings、0原生表格；正文为4幅补充图及说明。当前取得件没有逐细胞轨迹/后代原始数值表。这个判断只限于取得的附件，不能宣称作者没有或所有公共位置都没有原始数据。原图像不数字化为独立生物样本。

启发：优先研究可实测的恢复过程与后续功能能否作为共享程序锚，而不是把RNA相似或已知靶点当充分程序。原始数据若恢复，可以先检验测量接口；单药/两背景仍不足以验证跨化学复用及完整CL4相互作用。

## P3 Blanchard et al.，Cell Communication and Signaling，2024，10.1186/s12964-024-01742-3

同样是较早的原始资源，不作为2026前沿算法。实际阅读JATS Sec6/7的CTG与RPPA、Sec10/12的克隆与反应、补充PDF全件页面类型/标题及TableS3（PDF第17页）；其余分子讨论未完整读。

25个H1975来源单克隆，125个信号分子RPPA；RPPA段主要描述培养后基线样本，不能当作药后参与度。四类抑制剂存在于方法，不代表已获得“同程序多种化学实现”的完整交叉矩阵。原文对亲本dose curve记4个独立实验×2技术重复，克隆700nM端点段写4技术重复；不能将前者重复数推广给全部克隆。没有实测混合比例×总密度设计，不能支撑CL4跨群体相互作用。

实际资源：3,869,428 byte、17页官方补充PDF，SHA `0c7789c2c432474178e471e32cd77402f7bb8613671d1f68f9f344143cbba308`。1–11页主要补充图，12页TableS1，13–16页TableS2抗体/组间p值，17页TableS3有25个克隆及亲本的归一化药敏均值。用已安装pypdf提取，没有安装fitz；未对含图页面作像素级视觉审阅。TableS3两列文本可直接恢复，不把抗体列表/组间p值当125×克隆原始矩阵。

TableS3的25个克隆分数范围0.25–1.35（coordinator已读数并另存verification.json），都是作者报告均值；没有可用于独立培养CI的原始重复，也未取得样本×蛋白原始数值。本轮不做模型训练或重新宣称功能效应。

## 库与工具错误

三篇均经reference_library.py登记；P1落存原始HTML，P2/P3原始JATS和补充件保留在episode，库主文状态pending并注明真实阅读范围。没有把XML转成伪原文HTML，也没有把“已下载”记成完整阅读。

第一次登记误用了列名publication_date等，工具拒绝且未写论文；日志library_actions.json保留。依照工具真实schema改成first_public_date/landing_page/reading_scope/note后，library_actions_v1.json全部8步成功。此为本地登记错误，不是科学阴性结果。
