# 原始来源核对后的独立机制质疑

2026-10-27。冻结对象：mechanisms_v1.md。初判见 initial_challenge.md，先落盘后交流。有效模型/effort unknown。未读 structural_mechanisms.md、latest_evidence.md、initial_structural_leads.md 或协调者总结；没有共同设计新候选，没有训练/效果实验/数据下载。定点阅读论文不等于复现。以下保留四条待证伪机制，但不认可“四个新算法”或“三种已成立生物机制”的表述。

## 原始证据改变了哪些判断

### M1：双差结构是真实的，解释 R197 增益仍是假说

已读 r197.py 的 build_q（约207–310行），及 r197_v2.py 对该函数的导入。原始实现先按cell×condition×barcode聚合，再按barcode均值构造full；实际Q是 `full(ca,p)-full(ca,q)-full(cb,p)+full(cb,q)`，quad_keys保留四个key。因而在**聚合后的 SYNERGY_DELTA_EMAX 端点向量**上，Q=A y是准确的构造描述。这里的y并非所有最底层测量，SYNERGY_DELTA_EMAX已经是派生端点；不得把对它的线性闭包说成对原始细胞测量的一切非线性处理都成立。

同一组带噪raw实现生成的三条差分仍严格满足闭包，噪声通过A共享；“有噪声所以闭包不成立”是错误的。真正改变目标的是新独立培养：`q_new=a μ+ε_new`，此时可估计均值不等于恢复ε_new。合法评估应分别报告对已有实现的重建、对条件均值的估计和对新培养的预测分布；不同单位的方差不能混在一个Q边级CI里。

原始 r197_v2.json 的最终判定为 inconclusive：delta=0.51333063，95% CI=[0.44580795,0.5756033]，MDE80=0.0941995>0.07339553，identifiability检查未过。这个数值只用于核对状态，未重算。现有design identifiability门是矩阵覆盖条件，不等于本轮新增的A行空间审计。**未计算真实A_T的rank/rowspan，不能宣称闭包已解释0.5133增益，也不能据此撤销或改写原判。**r196_v2.json同样是inconclusive，不是负结论：point=0.141464，drug-CI=[0.062468,0.182579]，primary MDE80=0.08572，设计门未过。

数学新意仍不成立：线性可估函数、相关误差GLS、GP条件化及Fisher设计足以表达冻结操作。其独立价值可以是识别“标签扩增创造的信息幻觉”及面向物理测量的公平比较。需证明的额外增量是：同raw条件和同物理成本下，源信息在未识别方向提升真实独立预测/决策，而不只是重写矩阵补全。

### M2：动态改写细胞状态已有直接顺序治疗先例

P4_1查得 Lee et al., *Sequential application of anticancer drugs enhances cell death by rewiring apoptotic signaling networks*, Cell 2012, DOI [10.1016/j.cell.2012.03.031](https://doi.org/10.1016/j.cell.2012.03.031), PMID22579283/PMC3501264。完整摘要明确报告：time-staggered EGFR inhibition而非simultaneous coadministration使一部分三阴性乳腺癌细胞对genotoxic drugs更敏感；结合时间分辨信号、基因表达、表型和数学建模解释intrinsic state及apoptotic network rewiring。阅读级别A：全文XML返回HTTP500；PMC HTML虽HTTP200却是RecaptchaChallengePageUi，已识别并保存，不把它当全文。

这足以将“顺序药物通过历史状态改变后一药响应”标为**Close，已有生物先例**，不足以判整条M2 Done：洗脱后持续多久、同细胞而非选择、A′跨实现迁移与agent的鉴别采样是否已经被该文覆盖，摘要不能回答。M2不能靠把先例改称非交换算子获得新意。未见日程预测与新A′复用是尚待证的差异，不是已确立差异。

最小反证不变：总AUC和总clock相同仍保留药物距终点时间差，应以位置匹配单药/vehicle、实际残留、恢复时间、群体组成和生长状态为竞争解释。C_AB≠0仅说明指定日程不交换；只有暴露历史/普通状态空间模型解释不足，并在未见实现或背景上复用，才支持更强主张。P4_2限定近24个月的order+memory检索有66命中，前15多为fractional dynamics/神经记忆，明显噪声；不继续扩预算，不把未命中当新意证据。

### M3：统一校准的最危险失败已有直接原始实验

P4_3查得 Chan et al., *A simple high-content cell cycle assay reveals frequent discrepancies between cell number and ATP and MTS proliferation assays*, PLoS One 2013, DOI [10.1371/journal.pone.0063583](https://doi.org/10.1371/journal.pone.0063583), PMC3656927。阅读级别P：完整摘要，Compound Treatment、Comparison of Assay Formats、Time Dependence of Inter-assay Format Variation章节。原文用平行replicate plates施相同剂量系列，48h后分别做CellTiter-Glo、MTS、CyQuant和image-based cell count，已具非常接近“同条件分流测量”的实证结构。

原文结果不是统一饱和压缩：etoposide的ATP/MTS与cell-count曲线偏移，gemcitabine的ATP/MTS每细胞升高，BI-2536可呈非单调曲线；ATP/cell随处理时长和背景变化。故 `h_m(z)`在相关药理问题中是**已有实验证据反对的强简化**。一个untreated count ladder不能自动校准药物诱导的每细胞代谢变化。不同通道可能刻画不同真实对象，校准失败也可能是科学信息。

因此M3的可行正例仍成立，但仅在经验证的共同功能对象与条件不变映射范围。同源分流及校准本身有近邻，cycle-consistency无法消除 `z'=g(z), h'_m=h_m∘g^-1` 的规范自由度；全图自洽也能全图错误。最小区分：冻结映射后持出药物×背景×时长，以独立绝对数/功能读出验证，并与允许assay×condition交互的层级测量模型比较。若只有cycle变小而独立功能决策不改善，否定迁移收益；不能通过删除“难校准”的药物恢复成功表述。

### M4：实测参与优于名义靶点是成熟事实，部分参与不保证分层可识别

P4_4同时命中两个直接原始先例：

- Vasta et al., *Quantitative, Wide-Spectrum Kinase Profiling in Live Cells for Assessing the Effect of Cellular ATP on Target Engagement*, Cell Chemical Biology 2017, DOI [10.1016/j.chembiol.2017.10.010](https://doi.org/10.1016/j.chembiol.2017.10.010), PMC5814754。阅读P：完整摘要、target engagement与intracellular kinase activity对应章节、ATP interference机制章节。178个full-length kinases的live-cell profiling及crizotinib分析，明确显示biochemical亲和力不等于细胞参与；ATP耗竭/通透化对照检验参与差异。其参与与功能比较主要为细胞内磷酸化/kinase activity，不是这里所需跨细胞存活决策。
- *A Probe-Based Target Engagement Assay for Kinases in Live Cells*, Molecular & Cellular Proteomics 2025, DOI [10.1016/j.mcpro.2025.100963](https://doi.org/10.1016/j.mcpro.2025.100963), PMC12076712。阅读P：完整摘要、Experimental Design and Statistical Rationale、Discussion。dasatinib/dinaciclib、活细胞与lysate比较；原文明确说两类实验都不能解析complex-specific engagement，给出所有conformations/activation states/complexes的平均亲和估计；还指出细胞进入、胞内分布、ATP和probe干扰。统计段说明多数实验biological duplicates，dasatinib engagement五个生物重复；这不是M4完整多背景×功能×rescue资格。

两篇足以拒绝“真实参与坐标替代名义靶点本身全新”。冻稿承认该点，因而保留稀疏交叉下区分应修改drug→e还是F的研究问题，但可识别性还未证明。即使测e，平均参与相同可能掩盖局部/复合体/时间差；y不同只能拒绝“当前e充分”，不能直接宣告细胞规律不同。`r_{a,b,c}`若不事先限制，任何反例都可吸收，机制就没有失败条件。需要预先声明可识别假设及留出化学实现上的预测约束。

遗传干预与药物不能硬等价是本轮逻辑/生物条件检查，不以这两篇来源冒充遗传等价研究。慢性缺失/补偿、催化抑制与支架功能、rescue本身网络改变都应成为具体排除限制。当前来源并未完整验证任何遗传rescue合同，保留未决。

## 本地资源资格与最小区分结论

qualification.json的原始记录（2026-10-26-agent-cell-evidence）明确：PRISM目标注释不是engagement；BATCHIE已载列缺少exposure/time、engagement、genetic perturbation和independent-endpoint linkage，file/plate/well不识别独立培养。资格门是STOP_MECHANISTIC_MAIN_EXPERIMENT_AT_QUALIFICATION_GATE。这里只核对该次已加载元数据范围，不声称全世界/整个磁盘都不存在所需数据。

| 机制 | 操作区别与构造例 | 最危险假象 | 下一最小判别及合理成果 |
|---|---|---|---|
| M1 | raw端点方向与差分闭包；四端点双差有代码依据 | 同raw复用当独立预测、源先验当当前证据 | A/quad_keys审计；独立培养与不可闭包目标分开；可做评估纠正或信息边界成果 |
| M2 | A→恢复→B而非静态组合；持久k使B依赖A | 不平衡作用年龄、残留、群体选择 | 位置匹配控制和残留/恢复曲线，再未见A′迁移；当前条件研究 |
| M3 | 同源平行分流与anchor；统一压缩可被识别 | cycle自洽当正确、ATP变化当统一测量偏差 | anchor与共享对象认证，冻结h后持出条件；可做测量边界/桥接资源 |
| M4 | 化学实现×参与水平×背景交叉 | 部分/平均e匹配当充分，任意r事后解释 | 限定F/r与参与时程，持出实现并与同e的PKPD比较；可做实现/响应分离边界 |

四者仍是操作不同且有构造可行例的**候选**。M1近期可在现有档案做只读构造审计；M2–M4的实际开工依赖新资格证据。无一条已有净决策收益、跨任务迁移或因果机制成立证据。负结果、不可辨识边界及测量合同仍可作为成果方向，但不能以成果类型的宽泛性掩盖机制未验证。

## 查询、来源与过程账本

P4恰用4条新查询，没有扩额。精确query、URL、时间保存在search/p4_challenge/P4_1_request.json至P4_4_request.json，原始返回保存对应_response.json。渠道Europe PMC，pageSize15，resultType core，无翻页。四条依次为：

1. `TITLE_ABS:("sequential" AND "drugs" AND "rewiring")`：2命中，返回2。
2. `TITLE_ABS:("drug" AND "order" AND "memory") AND FIRST_PDATE:[2024-10-27 TO 2026-10-27]`：66命中，仅首15；噪声高，保留覆盖限制。
3. `TITLE_ABS:("ATP" AND "cell number" AND "drug" AND "assay")`：11命中，返回11。
4. `TITLE_ABS:("target engagement" AND "live cells" AND "kinase")`：15命中，返回15。

定点全文读取另记，不算新主题查询：primary/p4_challenge中3个XML成功保存，附URL/HTTP/bytes/SHA256收据；PMC3501264 XML HTTP500，HTML恢复HTTP200但为验证码页，保留拒绝证据。没有进一步尝试绕过访问控制。阅读层级均P或A，没有全文+补充全部阅读，不给Done判定。未检索顶会/完整引文链，不能做全面查新声明。

还读了本轮primary/三个2026论文的完整摘要：DrEval、AMM-SimWMag、heterogeneity-aware synergy benchmark；它们提示强基线/异质性，但不是证明M1–M4首创或失败的直接机制证据。JSON初次整读发生工具截断，随后对R196 judgment必要键、R197 design checks/judgment/构造以及脚本build_q分块重读；本报告仅使用已重新收到的字段，不依赖被截断部分。技能按定向少量核验范围使用innovation-research与lit-survey，没有启动完整资料库采集。
