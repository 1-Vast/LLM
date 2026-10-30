# CDI 最近先例核读（2026-10-30）

## 核读范围与 CDI 定义

本核读只使用出版社原文页面、出版社 PDF（可访问者）、作者代码仓库和 Crossref 元数据；没有使用用户粘贴的摘要。实际读取的原始入口共 5 个：

1. AdaMBind：<https://doi.org/10.1038/s41467-026-70554-5>；出版社全文页面 <https://www.nature.com/articles/s41467-026-70554-5>。
2. PBCNet2.0：<https://doi.org/10.1038/s41589-026-02241-x>；出版社页面 <https://www.nature.com/articles/s41589-026-02241-x>；作者代码/复现实验 <https://github.com/YuJie-0202/PBCNet2.0>。
3. Robin：<https://doi.org/10.1038/s41586-026-10652-y>；出版社全文页面 <https://www.nature.com/articles/s41586-026-10652-y>。

本报告中的 CDI 候选定义为：对同一靶点的药物对 A/B，输入分子层相对作用差 Δa（实测 Kd/pChEMBL，或冻结 PBCNet2.0 的相对预测）与匹配的 drug×cell×dose/time 功能读出 y；估计

`D = [y(A,C1)-y(B,C1)] - [y(A,C2)-y(B,C2)]`，

并判断 Δa→Δy 是否受靶点依赖和细胞背景调制。Virtual cell 学习该条件关系；agent 在等预算下选择最能区分“结构模型错误、靶点依赖不足、细胞药理因素、实验错配”的药物对/细胞对。AdaMBind 仅作为新靶点少样本适配先验。

## 逐篇核读

### 1. AdaMBind（Nature Communications 2026）

**原文报告。** 论文题为 “A meta learning and task adaptive approach for drug target affinity prediction”，DOI `10.1038/s41467-026-70554-5`。摘要和 Results/Methods 明确：AdaMBind 将 DTA 数据按唯一蛋白靶点组织成任务；输入药物分子图与蛋白氨基酸序列，输出结合亲和力；核心是 MAML、adaptive task module 和标签噪声注入。测试时对未见靶点支持集做快速梯度适配，比较 5 对（few-shot）和 40 对（majority）支持集。Methods 的数据为 BindingDB、KIBA、Davis，另用 LIT-PCBA 做 ESR/TP53 虚拟筛选；随机 8:1:1 任务切分和 CD-HIT 40% 序列相似度的 novel-task 切分均被报告。模型基线包括 DeepDTA、HiSIF-DTA、ColdDTA、Co-VAE、PSICHIC、CML、MetaDTA 和 ZeroBind。论文还报告以 10 个随机 FLT3 抑制剂构造支持集、DrugBank 为查询集，结合 AutoDock/文献筛选候选，并用 ADP-Glo 对 Staurosporine 的 FLT3-WT/FLT3-ITD 做 `n=3` 的体外验证。

**与 CDI 的直接占位。**

- 已占据“同一靶点任务 + 少量已标注药物 + 亲和力预测 + 未见靶点适配”这一部分。CDI 若使用 AdaMBind，合理定位是支持集适配先验，而不是 CDI 的新颖性来源。
- adaptive task module 按查询集损失和 support/query 梯度相似度给训练任务赋权；这与 CDI agent 依据预期机制区分度选择实验对有表面相似性，但优化对象不同：前者优化模型训练任务采样，后者选择能识别结构/背景/错配机制的实验组合。
- AdaMBind 的 FLT3 验证是候选排名后对一个药物做靶点酶活验证，不是同靶点药物对 A/B，也没有 C1/C2 背景、剂量/时间条件的差异中的差异 D。

**尚未被原文占据的 CDI 差异。** 论文没有报告配对的细胞功能读出 y，也没有估计“药物对在不同细胞背景中的作用差异”；没有将相对亲和力差 Δa 与背景调制后的 Δy 建模；没有 agent 在固定实验预算下选择药物对×细胞对来区分竞争机制。其“novel target”是低序列相似度蛋白任务，不等于 CDI 的“同靶点、跨细胞背景”条件交互。论文自己将真实 zero-shot 预测列为未来方向，因此不能把其 few-shot 结果描述成 CDI 的零样本验证。

**证据边界。** 以上均来自出版社全文的 Abstract、Results（Overview、任务切分、基线、FLT3 验证）和 Methods（Datasets、Data split、Representations、Meta-learning、Adaptive task module）段落。论文报告的性能数字是作者在 BindingDB/KIBA/Davis/LIT-PCBA 上的内部评估；本核读没有复跑，也没有独立验证其 FLT3 生物学结论。

### 2. PBCNet2.0（Nature Chemical Biology 2026）

**原文报告。** 论文题为 “Atomic-level protein–ligand recognition with PBCNet2.0 for probe discovery”，DOI `10.1038/s41589-026-02241-x`。出版社页面当前为订阅预览，能直接核实的摘要内容是：PBCNet2.0 为 Cartesian tensor-based Siamese neural network，做蛋白–配体相对结合亲和力预测；训练 8.6 million 个蛋白–配体复合物对；报告 zero-shot 与物理模拟相近、回顾性优化效率提升 7.18 倍、资源减少 41%；模型对结合口袋残基变化表现出未以突变数据训练的亲和力变化预测能力；在 ENPP1 和 ALDH1B1 上前瞻验证，六个选定残基中五个识别正确。出版社 Data availability 指向 Zenodo 训练数据和 GitHub 测试数据/代码。

作者 GitHub README 是可复现入口：模型权重、`model_code`、论文结果复现代码、测试数据、Zenodo 训练数据；输入示例为配体 SDF 和蛋白 PDB；另提供 FEP 数据微调脚本。README 没有细胞、剂量、时间或功能读出接口，目标是 relative binding affinity。可追溯性有一个需保留的差异：出版社页面 Data availability 指向 Zenodo `18299525`，而作者 README 指向 `15656365`；本核读未下载或核对两个记录，不能假定它们是同一版本。

**与 CDI 的直接占位。**

- PBCNet2.0 可以提供 CDI 的分子层 Δa 候选（尤其是同一蛋白口袋内 A/B 的相对亲和力差），并且其残基变异敏感性与 CDI 的“靶点依赖”部分有方法学关联。
- “同一靶点内的相对比较”并非 CDI 独有：PBCNet2.0 的 Siamese/relative-affinity 任务和 ENPP1/ALDH1B1 残基变化实验已经占据结构层相对差异、局部口袋变化和前瞻筛选。

**尚未被原文占据的 CDI 差异。** 可核实的原文没有把 Δa 与细胞功能 y 配对，也没有跨 C1/C2 背景的差异中的差异 D；没有将细胞药理、剂量/时间效应或实验错配纳入预测变量；没有实验 agent 在等预算下选择最有信息量的药物对/细胞对。PBCNet2.0 的“mutation/resistance”是结构口袋残基变化的亲和力推断，不是细胞背景条件交互。由于全文受订阅限制，本核读不能从出版社页面确认其全部训练/测试切分、模型消融和实验 protocol；这些细节只能标为未知，不能推断为不存在。

**证据边界。** 结构、数据规模、回顾性/前瞻验证和五/六残基命中率来自出版社摘要；代码/数据可得性、SDF/PDB 输入、FEP 微调来自作者 GitHub README。没有下载 Zenodo 训练包，也没有将其权重用于 CDI，故未验证冻结模型的 Δa 数值或跨数据集校准。

### 3. Robin（Nature 2026）

**原文报告。** 论文题为 “A multi-agent system for automating scientific discovery”，DOI `10.1038/s41586-026-10652-y`。Robin 由 Crow/Falcon 文献搜索 agent 和 Finch 数据分析 agent 组成：给定 dAMD，Crow 形成病理问题和体外模型报告，LLM judge 对候选机制/模型做成对排序；随后 Robin 提出 30 个候选药物，Falcon 生成逐候选证据/局限报告，LLM tournament 排名，人类审阅并执行人类生成的实验 protocol。实验结束后输入 FCS 或 RNA-seq gene counts，Finch 对流式或差异表达做分析；每个任务运行 8 条独立分析轨迹，再作 consensus meta-analysis，并可据结果提出 follow-up assay。论文案例中使用 ARPE-19 初筛，后以 RPE-SC 验证；发现 ripasudil、KL001 等候选，另做 Y-27632 RNA-seq 和 ABCA1 机制线索。Robin 的工作流和实验闭环是 semi-autonomous/lab-in-the-loop：实验执行、精确 protocol 和最终前临床确认仍由人完成。

原文还报告配置 `num_queries=5, num_assays=10, num_candidates=30` 时约 45 次 Crow + 30 次 Falcon 调用，平均约 US$10.76；一次运行约分析 551 篇论文。Finch 在论文所用 flow/RNA-seq 任务上的专家 rubric 得分分别为 100±0% 和 86±0%（各 n=3），但在 170 个更难的 BixBench 问题上总体为 22.8±1.7%，说明其能力依赖任务特定提示和工具链。将 Crow/Falcon 替换为 o4-mini 的消融降低候选质量并增加文献幻觉；OpenAI Deep Research 生成的 17 个独特候选在同一 RPE-SC assay 中无命中，且没有提出 ROCK inhibition。

**与 CDI 的直接占位。**

- Robin 已占据“文献综合→候选生成→实验读出分析→根据结果提出下一轮假设”的 agent/lab-in-the-loop 闭环，以及多轨迹分析和 follow-up assay。
- 它已经把 flow cytometry、RNA-seq differential expression 等功能读出纳入反馈；因此 CDI 不能仅以“agent 分析功能读出”作为新颖性主张。
- Robin 的 LLM judge/tournament 也占据候选/实验策略的相对排序形式，但其排序依据是文献科学合理性、药理资料和方法学支持，不是 Δa→Δy 的机制可辨识度或固定预算的信息增益。

**尚未被原文占据的 CDI 差异。** Robin 的实验对象是疾病机制候选和单药效应，文中没有同一靶点 A/B 的相对亲和力输入，也没有在匹配 C1/C2 细胞背景、剂量、时间下计算 D；没有把结构层差异和背景层功能差异的交互作为学习目标。其 follow-up 是由 Finch/Robin 根据已观察结果提出，论文没有报告“在等预算下，显式以区分结构模型错误、靶点依赖不足、细胞药理因素和实验错配为目标的主动选对”消融或决策收益。实验 protocol、细胞模型替换和候选执行均含人类选择，故不能把 Robin 的半自主闭环等同于 CDI 的全自动机制判别 agent。

**证据边界。** 以上来自 Nature 全文的 Robin workflow、Therapeutic hypothesis generation、Experimental data analysis、dAMD 实验、Validation of the Robin architecture、Discussion 和 Methods；论文的结论是 dAMD 个案和 agent/分析基准，不能外推为跨靶点、跨细胞背景的因果机制学习。作者明确指出当前系统不生成可直接执行的精确 protocol，Finch 依赖领域专家提示，且需要标准前临床验证。

## CDI 新颖性边界与可保留差异

### 已被先例覆盖的操作（不宜单独宣称创新）

1. 蛋白–配体相对亲和力/配对比较（PBCNet2.0）以及结构口袋残基变化敏感性。
2. 按靶点组织任务、少样本 support-set 适配、未见靶点泛化和任务重要性调度（AdaMBind）。
3. 文献驱动的候选生成、LLM 排名、人执行实验、流式/RNA-seq 分析、多轨迹共识和结果驱动 follow-up（Robin）。
4. 用单一功能读出验证候选药物或做后续转录组分析（AdaMBind 的 FLT3 酶活；Robin 的 RPE phagocytosis/RNA-seq）。

### 仍可能保留、但必须实验证明的差异

1. **条件化交互目标：** 同靶点药物对的 Δa 与跨背景 Δy/D 的可重复关系；关键不是再做一个 DTA predictor，而是证明同一 Δa 在 C1/C2 的功能效应可系统改变。
2. **成对、匹配、跨尺度设计：** A/B 必须作用于同一靶点且有可靠的相对亲和力；C1/C2 需匹配细胞、剂量、时间和 assay，避免把批次或暴露差异误当背景调制。
3. **机制判别式主动实验设计：** agent 的选择函数应明确比较四类错误（结构模型错、靶点依赖不足、细胞药理因素、实验错配），并在固定预算下与随机、亲和力贪心、单背景设计等基线比较；Robin 的 LLM tournament 和 AdaMBind 的任务采样都不能替代该证据。
4. **虚拟细胞的跨背景泛化：** 需要按细胞背景/药物对留出，避免同一药物、同一细胞或近重复样本泄漏；单纯在 BindingDB/KIBA/Davis 的随机切分上提高 DTA 指标不支持 CDI。
5. **从预测到功能验证的闭环：** 先冻结或预注册 PBCNet2.0/亲和力来源，再由 CDI agent 选对，盲测 D，最后做独立细胞/剂量/时间验证；不能用候选发现后的同一数据回填选择规则。

## 未知与不可外推项

- PBCNet2.0 全文受订阅限制；其完整训练切分、模型消融、残基选择规则和实验重复数未从可访问原文确认。出版社与 GitHub README 的 Zenodo 记录号不一致（`18299525` vs `15656365`），训练数据版本应在复现前单独核对。
- AdaMBind 的报告是作者内部 benchmark、虚拟筛选和单个 FLT3 体外验证；本核读未复跑，不能称为外部独立验证或因果机制证明。
- Robin 的 dAMD 结果是一个 lab-in-the-loop 个案；其时间/成本数字是估算，且实验 protocol、细胞替换和候选执行有人工参与。其 Finch 在任务特定数据上表现良好，不等于通用生物信息学可靠性。
- 本核读没有发现三篇论文报告 CDI 所需的完整组合（同靶点 A/B 的 Δa、匹配 C1/C2 的 D、显式机制判别式 agent 和等预算收益）。这是“在上述原始入口和可访问内容中未发现”，不是对所有 2026 文献的穷尽否定。

## 原始入口索引

- AdaMBind：DOI `10.1038/s41467-026-70554-5`; Nature full text <https://www.nature.com/articles/s41467-026-70554-5>。
- PBCNet2.0：DOI `10.1038/s41589-026-02241-x`; Nature preview <https://www.nature.com/articles/s41589-026-02241-x>; code/data <https://github.com/YuJie-0202/PBCNet2.0>；训练数据入口（论文 Data availability）<https://zenodo.org/records/18299525>。
- Robin：DOI `10.1038/s41586-026-10652-y`; Nature full text <https://www.nature.com/articles/s41586-026-10652-y>。
