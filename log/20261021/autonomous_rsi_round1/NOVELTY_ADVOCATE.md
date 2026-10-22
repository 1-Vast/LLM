# 独立机制提出与新颖性审查：先证明有应当继承的改进

2026-10-21 启动，2026-10-22 00:00 后收尾，Asia/Shanghai；文献资格截止仍按任务固定为 2026-10-21。角色：独立支持/机制提出方 `novelty_advocate`。这是一份新记录，不修改旧研究、冻结协议或阴性结论。没有访问 sealed/masked 结局，没有读取任何 OASIS MT/LDH/count/形态数值，没有训练、API 调用或数值性能计算。本次只新增本文。

## 当前裁决

**没有找到足以批准实现新 Agent/RSI 架构的独有核心机制。** 保留一个未通过资格的机制问题：真实地改变测量过程，能否区分应当修复细胞响应模型、测量模型还是两者，并把有效的诊断/更新程序迁移到未来任务。该问题有实际意义，但固定 counter-screen SOP、贝叶斯模型鉴别与普通结构选择是强而直接的已有解释；当前没有候选独有操作。OASIS 也没有认证必要的测量过程干预菜单。

支持根代理开展 **OASIS dev-only raw MT/LDH + 真实 count 的重复一致性和同信息强基线资格**。这是未来状态—功能桥接的信息基础检验，不是上述机制、因果归因、Agent、继承或 RSI 试验。即使通过，也只能说明值得继续资格，不能晋级为已发现科研创新。

本轮不另列第二个架构来回避前述失败。分子残差核、门控混合、经验检索、改进程序搜索与 learned experimental design 都需要先通过普通方法归约；它们尚不足成为独立候选创新。

## 读取的项目证据与边界

按任务读取 `research/REPORT.md` 头部；`oasis_mechanism_review/pro.md`；`rsi_next_qualification/DECISION.md`、`NEXT_EXECUTION_PLAN.md` 和支持/反对/数据文献评审；`oasis_source_qualification/REPORT.md`；OASIS identity、pairing、structure 盲摘要；`oasis_evaluation_contract/PROTOCOL.md` 和 `SPLIT_STATUS_v2.json`。部分长批量输出截断，随后定向读取关键文件；不声称逐行审计全部历史。

- PTV 原 14 药池中，同训练范围的 selection 混合选权均选新增分数权重 0；保留 STOP_FURTHER_PTV_SEARCH。修复研究不同 20 药池的半混合信号不能跨配置替换原阴性。真实更新能改变概率，因此不重复旧报告“分子反馈在结构上无法影响输出”的错误解释。
- Beat AML 的逐药普通 offset、PRISM 的同信息 ridge/kernel、固定设计及混合是必须首先击败的解释。历史不存在“反馈一概无用”的结论；失败的是多个附加模型/程序在所测任务中没有越过强常规方法。
- 当前 OASIS 盲身份结果为 1085 标签、960 已知结构、119 缺结构、6 冲突；化学预留记录 dev 641 标签/400 组、selection 163/137、reserve 156/125，125 标签隔离。分区已建立不等于生物资格成立。
- 配对盲摘要有 8668 个命名 compound-dose 动作；1073 标签有 8 剂量、12 标签有 7 剂量。每动作可配对物理孔数有 2/1/8 三类。这里不把 well、dose、plate 或五供体混池内供体数当独立背景。没有从盲目录取得任何数值结局。
- 单 PHH 混池、固定 44 h 同时 readout 只支持此体系内化学组泛化；不支持恢复动力学、早到晚预测、未见供体或跨背景 RSI。MT 是代谢读数，不改称 ATP；LDH 也不是临床 DILI 真值。

## 一个机制问题：通过真实测量干预约束可更新对象

具体用途：未见药族在固定肝细胞体系出现形态、代谢与膜损伤读数不一致时，以更少控制实验确定下一步应该复核什么，避免把检测链变化当作可迁移细胞响应。最终裁决对象仍应是未参与诊断的真实功能/剂量复核结果，不是模型自身模拟或分子相似度。

最小表示是：

    z = T_theta(z0, drug, dose, exposure, context)
    y = H_phi(z, q) + I_psi(drug, dose, z, q) + batch + noise
    p(history) -> (next real experiment, permitted update set, update operation)

q 是可执行的测量程序。I 保留 z 依赖，因为进入细胞、结合蛋白/核酸或不同基质可能改变干扰。把 I 简化为仅依赖药物与 q，是需要验证的 transport 假设，不能为了可识别性默认成立。

这个修正带来两个必要约束：

1. **不能强制二选一。** 一个药物可以同时产生真实损伤与检测干扰；允许更新集合为 `{T}`、`{H/I}`、`{T,H/I}` 或空集。若人为限定互斥 H_bio/H_obs，诊断程序可能在最重要病例中错误，但看似很自信。
2. **blank/spike 本身不保证能运输到主实验。** 无细胞 blank 只测 I(a,0,q)，不自动等于 I(a,z,q)；加性 background 不排除乘性酶抑制/淬灭。spike-recovery 也需要认证基质、浓度、试剂、药物接触顺序、取样/读板条件的映射。部分荧光干扰仅在药物进入细胞后出现；去掉细胞可能一起去掉干扰机制。

因此，必须先存在能在主体系验证 transport 的真实控制及独立功能复核。固定 q 的多端点相关性不能裁决哪个程序对象应改；加入更多自由潜变量也不解决这一点。对固定观测，任何共享偏差 g 都可在 H 与 I 之间重新分配而保持 y 不变。细胞计数、图像或 RNA 能增加预测信息，但除非它们的测量机制亦被认证，不能仅凭一致性解除混淆。

一个严格最小反例：令状态含细胞是否存在 c 与损伤 d。世界 A 的主实验 d=a、I=0；世界 B 的主实验 d=0、I=a*c。主实验 c=1 时二者 y=a；无细胞 blank/spike 的 c=0 时二者分别输出 0/k。因此 blank/spike 都正常仍可与细胞存在才显现的干扰完全相容。此构造是识别约束，不是拟合结果或候选算法的优势证明。

**最强可证伪主张**只有：在同样允许信息、训练监督、控制菜单与实验/计算预算下，该分解诱导的诊断/更新程序，比固定 SOP、同信息条件多输出预测器及贝叶斯主动模型鉴别，用更少真实控制，改善未来新药族的预先冻结功能决策效用。预测更准但不改变真实决策、只复现已知 SOP、或者收益来自额外控制数据，均不支持此主张。

**当前新颖性失败点：** 还没有给出上述方法独有、且应当优于同知识贝叶斯鉴别/SOP 的最小数学操作。仅将 T/H/I 写成代码、修改其结构或把选择交给 LLM，是模块化系统辨识与程序搜索。不能以一般 conditional NN 能表达一切为由否定归纳偏置；但归纳偏置的实用增量仍必须测出。现阶段只批准寻找识别资产，不批准搭建该系统。

## 最新一手证据与实质区别

检索/访问于 2026-10-21 深夜至 2026-10-22 00:00 前后，纳入的论文版本截止 2026-10-21；以下是作者报告，未独立复现。有限检索不能保证穷尽新颖性。每条保留实际访问层级，避免把摘要或搜索索引冒充全文。

| 一手来源 | 本次核验的内容 | 对本项目的约束 |
| --- | --- | --- |
| [SpecRSI, arXiv:2610.16491v1](https://arxiv.org/html/2610.16491v1)，2026-10-12 | 原始摘要及方法、Appendix D.1、F.5 相关全文。VATS 预测已验证后继收益，GVO 学 improver；D.1 有 reset/carry/同 released artifact fork，F.5 有同状态付费后继 rollout。 | “学习改进策略”“共同起点检验更会改进”“从真实后继收益分配 credit”本身均已有。真实生物控制下的具体可识别更新机制才可能另有贡献。没有复现性能数字。 |
| [Hyperagents, arXiv:2603.19461v1](https://arxiv.org/html/2603.19461v1)，arXiv 元数据 2026-03-19 | 原始全文 §3、§5.2。任务/meta 程序可编辑，冻结 meta 测 improvement@k；但 §5.2 明确 transfer 时 task+meta 整份 implementation 一起带入。 | 元策略可改、继承与未来改进效率不是新意；不能过度声称该文已在所有比较中隔离共同 task 起点。共同 p0 的更严格控制仍是实验要求，不足单独构成新算法。HTML 内部另见 2026-08-24 标注，本文以 arXiv v1 元数据识别版本，不推断版本历史。 |
| [AIDE², arXiv:2609.26457v1](https://arxiv.org/abs/2609.26457)，2026-09-22 | 原始摘要。自改科研智能体代码，报告后续重写及未见任务迁移。 | 继承更好的科研程序并持续改写已有直接先例；不从摘要推断其真实药物/细胞效果。 |
| [MetaShare, arXiv:2610.21887v1](https://arxiv.org/abs/2610.21887)，2026-10-15 | 原始摘要。记录成功/失败编辑及 signed delta，跨谱系检索、多 meta-agent 提案、确定性选择器和去冗余。 | 失败记忆、交叉批评、跨谱系经验继承与节约进化轮次均已有直接主张；这些工程组件不能单独补足本项目新颖性。未从摘要把轮次减少当成总成本或生物效用验证。 |
| [Toward Generative Virtual Cells, ICLR 2026 Gen²](https://openreview.net/pdf?id=64iwpu7HO0) | 原始 PDF 搜索索引含摘要；直接 OpenReview 打开为浏览器验证，未逐页核验。世界模型/规划器共同更新，验证及容量门控；测试是五基因合成系统。 | 双核/共同演化架构不是新颖点；作者本身把主要改进归于 continual retraining。真实功能评价及非普通重训的独立贡献仍需证明。 |
| [VCLMU, arXiv:2610.04475v1](https://arxiv.org/abs/2610.04475)，2026-10-03 | 原始摘要。机制潜态单元、干预转移与扰动互斥分子响应评价。 | 可复用机制潜变量、状态转移与富集解释已有；没有因此获得功能决策、实验程序或 RSI 贡献。 |
| [Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation](https://www.biorxiv.org/content/10.64898/2026.08.04.742916v1.full)，原站索引标 Posted 2026-08-11 | 原始站点全文搜索索引中读取 Results/Discussion；直接 open 403。外层 Analyzer/Planner/Auditor 根据实验改评分规则，内层固定；作者说明仅一个 revision round。 | 真实细胞反馈下修改发现评分已有；一般“虚拟细胞+审查+改目标”不是本项目新颖性。DOI 内 08.04 不直接当实际发表日。未从该文推断规则继承或 meta 效率已证。 |
| [Deep Adaptive Design, ICML 2021](https://proceedings.mlr.press/v139/foster21a.html) | 原始 PMLR 摘要：离线学序贯设计策略，history→下一实验，复用以摊销设计计算。 | “学习实验选择并跨实验复用”是普通 amortized Bayesian experimental design，不能换名 RSI。 |
| [Deep Adaptive Model-Based Design of Experiments, arXiv:2603.16146v2](https://arxiv.org/abs/2603.16146v2)，2026-03-24 | 原始摘要：机制动力学、nuisance 参数和可微模拟下学习设计策略，含 bioreactor/PK。 | 加机制模型、噪声/干扰参数、快速自适应实验选择仍已有先例；不能把它们的组合说成独有操作。 |
| [Counting cells can accurately predict small-molecule bioactivity benchmarks, Nature Communications](https://www.nature.com/articles/s41467-026-68725-5)，2026-02-06 | 原始出版方全文相关节。许多 benchmark 可由 count 预测；在作者策划的 24 个 protein-target assay/269 compound 任务中 full CP 仍超过 count。 | count 是必要强对照；count 不足不能推出 morphology 不足。该策划数据也涉及过滤与两阶段筛选，不是自动完整任意政策 replay，更不是 RSI 资产。 |
| [Interference and Artifacts in High-content Screening, Assay Guidance Manual](https://www.ncbi.nlm.nih.gov/sites/books/NBK615088/?report=reader)，2025-05-28 | 原始技术手册搜索索引中读取 controls/orthogonal/counter-screen 节；常规 open 遇验证。 | assay 干扰鉴别和控制级联是成熟实验知识。资料明确提到进入细胞后才显现的荧光及 primary-like counterscreen，支持不可默认 blank transport；该手册是原始操作指导，不冒称新研究性能证据。 |

上述摘要只作为相关先例/限制，不按论文自报排名断言本候选无用。尤其 SpecRSI 的普通程序搜索成本、Hyperagents 的 starting-agent 混合及细胞论文的分子终点，仍不能替代本项目的公平真实功能比较。

## OASIS 最小开发资格为什么合理、又不能裁决什么

根代理提出的 readout/count 资格能先回答：原始读出在当前测量单位上是否重复；结构+剂量能否解释；有偿真实 count 是否有额外信息；是否存在足以改变功能复核优先级的可达空间。这比先增加架构更能决定后续投入。

冻结门槛应根据用途、dev 噪声及确认成本制定，在开数值前固定；本代理没有见数值，不为得到正信号建议具体 margin。至少区分以下信息条件：

| 信息条件 | 最小强对照/解释 |
| --- | --- |
| 无目标实验 | 结构+剂量强直接预测；同训练多输出 MT/LDH/count；普通 regularization/ensemble；目标 count 只能用严格 out-of-group 预测值。 |
| 已买目标形态/count | count-only、count+结构+剂量、相同数据强条件预测；所有臂承担实验成本。真实 count 增益仅证明测量价值。 |
| 未来有完整 morphology | 同 count 信息下 full morphology 的额外信息；在 count 匹配区域诊断，主终点不改。尚无 features 时，不允许由 count 阴性判定 full morphology 阴性。 |
| 模型学到预测 morphology | 相同辅助监督与容量的直接多任务对照；预测状态收益需越过普通多任务和简单混合，不能靠多拿训练标签。 |

重复 plate/well 的相关只属相应技术重复一致性；若独立培养资格未知，不称生物复现。MT 与 LDH 分别报告，不用二者不一致自动产生“伪影标签”。control-only 归一化、缺失处理及全部拟合参数只能用 dev；reserve/selection 数值不得泄漏。若只比较一个 endpoint 的 MSE 而没有事先合法决策单位，结果只算测量/预测资格。

若 count 没有额外信息，合理停止 count→功能这个具体桥；是否再拿完整 CP 由事先信息价值与成本决定，不能事后视为必然补救。若连噪声可靠性/主要终点可达空间都失败，可以停止该任务配置，而无需把所有可能分子模态逐个训练一遍。若 count 有用，也不能直接宣布 world-model 必要。

## 如果未来得到识别资产，最少公平比较与可证伪判据

先检验同历史下模型/更新算子的贡献，再检验不同闭环政策，避免两者一起变化。候选不能独占同样可公开的控制知识、先验、历史或失败案例。

| 要隔离的贡献 | 必需对照/裁决 |
| --- | --- |
| 真实观测价值 | 相同预算功能确认 vs 分子/形态测量；已测支持动作不能算未测目标的传播命中。 |
| 世界模型 | 同输入直接功能预测、同监督直接多输出/conditional predictor、分解结构的普通 kernel/GP/refit、容量匹配无转移模型及简单混合。固定同一支持集/政策。 |
| Agent 程序 | 同一模型、同一菜单下固定 SOP、exploit-first/信息增益/贝叶斯模型鉴别、主动学习及相同候选族/评价次数的 random/CV/BO/program search。先验全部共享。 |
| 继承 | 新任务共同模型与起点；移植程序 vs restart、案例检索、蒸馏 SOP、同历史从头拟合。权重、实例与程序继承分别开关，实际内容必须不同。 |
| 联合收益 | direct/world × conventional/adaptive 2×2；报告交互和最终系统相对最强常规臂的绝对净效用，正交互但总性能输不算达标。 |
| RSI | 源流学 m1 后冻结，从同一 p0/w0/history 分叉 m0、m1、手工强策略、等预算搜索；同 k 次修改与真实 query，用更后未优化任务裁决。另学 m2，再共同起点对 m1，才能检验后续改进策略是否进一步更有效。 |

所有真实实验、失败提案、验证、计算、API token、形成 meta 的历史成本与延迟计入资源曲线。不以接受次数、编辑哈希变化或更强初始权重代替决策收益；按程序诱导行为去重。

停止/反证条件在未来结果前保留：

1. 缺真实 q 控制或 control→主 readout 的 transport 不能认证：本机制 NOT_IDENTIFIED/NOT_TESTABLE，不用 discordance 推断原因。
2. 无细胞/短接触控制仍不能区分共同作用、或要靠编造未测数值：停止该诊断机制。
3. 相同信息 fixed SOP/conditional predictor/Bayesian discrimination 匹配效用及样本效率：新颖性 NO-GO，可保留正常流程应用价值。
4. 预冻主要效用差的区间上界小于 δ_use：NO_USEFUL_GAIN；区间宽为 INCONCLUSIVE，不把它当支持或换指标续命。
5. 程序“改进”仅为参数重拟合、混合选权、检索或普通搜索匹配：按实际类别报告，停止 Agent 特有效果主张。
6. 继承内容不能移植，或共同起点的 m1/m2 不能增加后续改进效率：停止继承/RSI 主张。累计成本不回本时不能声称总体效率更高。

## 独立交叉质疑与回应

反方 `historical_skeptic` 原话（内部协作消息，不是外部文献引文）：

> 独立反方在读历史后认为测量过程 repair 当前未形成新颖算法：固定 counter-screen SOP / Bayesian model discrimination / 同菜单等预算 program search 都可解释。请你给出一个最小反例：同一组已知控制和先验下，候选独有的哪一步应优于它们？又如何避免 blank/spike 改变生物/试剂上下文，导致从 control 无效外推到主 readout？我保留机制层机会，但不同意先实现 Agent。

我的回应：接受两项质疑；当前没有可辩护的独有操作，因此不批准先实现 Agent。保留的窄命题必须同 SOP/同信息条件模型公平竞争；blank 只鉴别加性背景，乘性干扰及基质依赖需另作真实验证，否则不可运输。另指出损伤和干扰可并存，不能强制互斥二选一。

我向反方提出的可裁决问题：若具真实同基质控制，可否只保留“同预算诊断后能否正确限制更新对象并改善未来功能”的一次资格？要求其给出 transport 失败、SOP 匹配及效用上界三类明确反证，并挑战 OASIS dev count 资格的解释边界。反方具体后续回应到达后仅追加，不改上方立场。

收尾状态：协作状态查询显示反方在已发出上述原始质疑后发生工具层内容访问错误，未收到它对本次回答的最终复核。因此只记录实际已完成的一轮独立质疑和回应，不声称反方接受了形式反例或三项判据，也不把未回复算共识。尚未解决的争点是任何候选独有操作及控制可运输性的实证资格；两者目前均未建立。

已向根代理发送两项文献细节：Hyperagents 整份 transfer 的 starting-agent 混合边界；SpecRSI 的同起点/同状态后继控制已有。因此不把这些实验设计据为本项目创新。

## 检索失败、资源与结果身份

首次四项混合搜索返回空；改为直接一手 URL 后可读取。bioRxiv 直接 open 403，但原站搜索索引返回相关正文；OpenReview 直接为浏览器验证，只据原始 PDF 索引摘要；NCBI 常规 open 验证，只据原站 reader/搜索索引相关节。没有绕过访问控制，没有把访问失败当成论文无结果。跨日收尾时一次追加补丁因上下文顺序不匹配被原子拒绝，随后拆正顺序成功；没有触及旧文件或改变科学数值。

本次 10 次 web 工具调用；部分含多个独立 query/open/find。网络检索字节未计量；数据集 payload 下载 0，DeepSeek 调用 0，GPU/训练 0，生物实验 0。没有数值实验结果。本文件中的项目性能只来自已暴露的历史摘要，OASIS 数值从未进入本代理上下文。

当前建议是：继续已授权的一次 OASIS dev 测量/信息资格；本候选保留 DATA/IDENTIFICATION_REQUIRED，不增加新架构，不称发现 RSI 机制。总目标仍未完成。
