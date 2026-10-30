# 来源、读取范围与证据级别

研究日期2026-10-27。O=本轮读取本地文件的记录/数值；P=读取原文相关方法的部分；A=仅题录/摘要。任何原文作者报告的效果均非本项目复现。新思想例子与E0–E3均为推理/计划，没有本轮生物效果结果。

## 当前项目证据

- R196：`../2026-10-27-c130-audit/r196.json`、`PROTOCOL_R196.md`、`r196.py`相关特征/拟合/聚类函数、`REVOCATION_R196.md`。已核当前判定撤回、常数身份基线、无cell特征、聚类范围与哈希。精确范围和限制见 evidence_audit.md。起始工具曾返回旧脚本hash与当前文件不符，稍后JSON记录已与当前脚本匹配；当前快照只能证明当前互相指向，不能证明原执行谱系。未重跑。
- R197：`../2026-10-27-q-structure/PROTOCOL_R197.md`、`REVOCATION_R197.md`；AMENDMENT文件已入hash快照，但未通读全文。截止18:23:40未见结果JSON；不能把协议和脚本当结果。v1已作废，v2未获本轮结果。
- R192–195：本轮沿用上一episode已核原始结果；重读相关记录与修正，不重算效果。数值边界见 ../2026-10-27-cross-domain-directions/report.md、late_results_audit.md 与当前source_snapshot.json。R194 1.43%仅加性主效应、Q2推断有待修正；R195只冻结大设计未准入。
- 旧线性状态编辑/混合支持/联合probe：本轮重读 log/RESEARCH_REPORT.md 相应已执行反例；底层旧DECISION文件并非全部再次收到。旧action_substitution原目录当前未找到报告，故“17%误差改善但决策未改善”只当历史二级摘要，不说本轮重验。
- 完整机制资源缺口：来自现有资格记录与本轮审计，不是已证明所有公共资源都不可用。尚未建立可执行的完整确认资源清单。

## 负载最大的近邻原文

| ID与原文 | 实际读取 | 对应事实/限制 |
|---|---|---|
| P1 BATCHIE，10.1038/s41467-024-55287-7，2025-01-02；原始JATS `../2026-10-26-agent-cell-evidence/sources/PMC11696745.xml` | 本轮独立质疑者Sec12/14/24/26全文，结构scout定点方法式25–30、三联及讨论 | 细胞条件模型、后验反馈、整板PDBAL与一般有界非负对称距离；实际top-K决策距离。已覆盖一般主动闭环，不据此声称完整覆盖本候选科学对象 |
| P2 PDTSyn，10.1093/bib/bbag199，2026；原始JATS `../2026-10-27-cross-domain-directions/cv_nlp_sources/PMC13109062.xml` | 本轮质疑者sec2g全文，sec2h开头至式12，sec2r全文；其余方法未全读 | 共享基与细胞特异系数、特征生成权重；不能把共享/特异双分支当新机制 |
| P3 DECANT，10.1093/bioinformatics/btag662，2026；同目录PMC13587831.xml | 本轮质疑者摘要与sec28 Discussion全文 | 转录表示不是target engagement或因果通路，已提出context-stratified/multi-prototype问题；不能替代独立药效 |
| P4 Compositional Behavioral Semantics for State Abstraction in RL，2606.25357v2，2026，`reference/papers/arxiv-2606.25357/paper.html` | 协调者§4.1–4.4、§5；证明未读；质疑者§4.1/4.4/5 | 同态/行为抽象、值等价已有原则；next-observation预测不自动保持转移/观测。当前精确结构保持，近似和实用学习算法仍需发展 |
| P5 Generalised Transportability via Causal Abstractions，2608.15645v1，2026，`reference/papers/arxiv-2608.15645/paper.html` | 协调者摘要/引言、§2.2定义、§3.1；认证定理证明未读 | 同变量、图、干预语义和已知shifted节点是重要前提；不能直接借其认证界。模型级迁移非空白 |
| P6 Task-Aware Exploration via a Predictive Bisimulation Metric，2602.18724v1，2026 | 协调者§3.1–3.3，Eq5–12及奖励预测；附录证明未读 | 表示与探索耦合已有；以预测奖励噪声维持非零距离不等于生物可识别差异，未将其定理移植 |
| P7 LOGICZSL，CVPR2025；`reference/papers/cvpr2025-logiczsl/paper.pdf`，sha d74f41ea6f2c… | 协调者已有PDF抽取§3.2、§3.3框架/模糊逻辑、§3.4 Eq13–16（PDF4–6页相关段），未完整核每条规则 | LLM概念树、模糊逻辑损失与兼容矩阵；视觉概念包含不等于药效蕴含 |
| P8 AlphaEdit，ICLR2025使用2410.02355v4；初次公开2024 | 上一episode已核方法，本轮复用其明确读取记录，未再次全读 | 线性旧键保护/投影编辑非新；不是因果或未测药效证据 |
| P9 SPI-Active，2505.14266v1，2025 | 本轮scout定点§2.3/3/7/A.5；其他位置继承上轮 | 主动激发方向依赖真实dense轨迹；参数耦合下预测改善不认证参数真值 |
| P10 Poke and Strike，2509.00178v1，2025 | 继承上轮§4–6部分读取记录 | 任务相关辨识、仿真特权与模型失配限制；本轮无新增实证 |
| P11 Formal Models of Active Learning from Contrastive Examples，2506.15893v1，2025 | 本轮scout摘要与§2定点；定理未读 | 对比查询/版本空间是已有；已知contrast-set oracle不是免费药物实验 |

P4/P5/P6本轮新入库。P5正文Appendix H直接指向 https://github.com/yfelekis/traca ，已通过库工具存作者链接代码快照commit `30eb685ac6725efd3cbc15abdd5c53998182a0be`（79文件）。只看README/目录/入口；**未运行**，许可unknown，论文版本对应提交未知。第一次落盘rename被WinError32锁住，第二次成功；保留故障，不删历史。未执行其README安装/取数命令。

## 检索与覆盖

本轮用原生可用工具发现没有web/search浏览工具，改用已安装lit-survey的公开Europe PMC/arXiv API；没有读取凭据或外部模型桥接。实际成功5条新检索：S1–S4结构侦察、T1定向覆盖。完整语句、日期、数量在 search/00_index/searched_queries.tsv；原始题录在 search/raw/。代理新增查询0（上限2，未使用）。

- S1：药物/扰动×substitutability、mechanistic equivalence、causal abstraction、equivalence class；EPMC 17/17题录。
- S2：bisimulation/causal abstraction/intervention equivalence×ML/AI/robotics/q-bio；arXiv86条取最近60条，**26条未展开**。
- S3：drug combination/perturbation response×causal/mechanism/compositional×active learning/transfer/context；EPMC14/14题录。CASynergy等仅题录/摘要筛查，不据摘要认定真实因果或方法细节。
- S4：drug/cell perturbation×counterexample/bisimulation/substitutability/abstraction refinement；arXiv18/18题录。
- T1：perturbation/drug×equivalence/contrastive/model revision；arXiv430条只取最近50条，**380条未展开**；该query很宽，不能据其未命中排除先例。

窗口2025-01-01至2026-10-27；EPMC有first-public-date在窗口内但issue year=2027的记录，不当2027未来实证。所有检索均为机制设计的定向补查，未完成系统领域调查、引用链或全部源码收集。新文件字节完整不等于全篇已读，更不等于复现。

开始库verify：30篇、21文件（19HTML+2PDF），1份官方代码；最终：33篇、24文件（22HTML+2PDF），2份官方代码；仍3pending、6restricted。errors=[]、warnings=[]。参见 library_verify.json 与 library_verify_final.json。5条检索保存159条返回记录（跨query可能重复），不能说159篇相关论文或159篇阅读。

## 主张标签

- 已知：指定旧算子等价性；R196撤回；R197v1作废/截止未见v2结果；近邻方法中实际读到的操作。
- 推断：本候选的一般实现可由条件响应模型、受约束模型选择和任务实验设计表达；生物机制需要更多区分信息。
- 待验证：条件替换结构存在且有用、可迁移分裂、未购决策净收益、新算法不可约差异。
- 不主张：已识别靶点机制、已证明最佳小面板、全域安全替换、完整细胞世界模型、RSI或首创。
