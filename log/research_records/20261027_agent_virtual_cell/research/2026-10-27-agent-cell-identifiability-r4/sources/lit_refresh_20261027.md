# 一手文献刷新 2026-10-27（R4）

执行方式：真实子代理（非模拟对话），独立上下文。**访问限制：该代理的 `web_fetch` 对全部出版方域名被拒（解析到非公网 IP），因此所有条目经 Europe PMC REST、arXiv API、Crossref API 取得，读的是题录＋摘要一级记录，没有打开全文或官方仓库。** 标 "V" = 读到的摘要级一手记录；"S" = 只在搜索片段/二次页面出现。因此下文只能作为**摘要级**先例判断，不能当作全文核实；三处最可能藏有"内部已做反馈 vs 随机消融"的预印本（VCHarness、CellForge、immune world model、CLARA）在宣称新颖性空隙前必须读全文。

刷新时点：2026-10-27（Asia/Shanghai）。检索式与引擎见文末。

## A. 直接新颖性威胁：无一条完成整闭环

1. **VCHarness / "Harnessing AI to Build Virtual Cells"** — bioRxiv 2026, DOI [10.64898/2026.04.11.717183](https://doi.org/10.64898/2026.04.11.717183)（Europe PMC PPR1212648），V。编码智能体＋多模态生物基础模型迭代生成/评估/精修扰动响应模型架构，称优于专家设计架构，开发周期由月降到天。**被占的是"智能体搭建虚拟细胞"这一半。** 无药物决策、无物理实验、无跨背景秩/竞争对象、无规则的反馈修订。
2. **"An immune world model for multiscale forecasting and therapeutic hypothesis generation"** — arXiv:2609.14709（2026-09-13），V。受治理的进化式 AI Scientist 构建动作条件世界模型；模型在独立确认前冻结，"generalized to unseen interventions and biological contexts"，并预测未见扰动组合。**被占的是"智能体造出、可外推到未见干预/背景的世界模型"。** 非共同学习、无实验选择、无决策收益测量。
3. **CellForge / "AI Scientists for Building Virtual-Cell Models"** — arXiv:2508.02276（v3），V。多智能体团队读文献、解析数据、辩论假设、写并跑训练代码；在六个扰动数据集上与手工 SOTA 相当。无与测量的闭环、无药物选择。
4. **"A world model of the virtual cell"** — *Cell* 2026, DOI [10.1016/j.cell.2026.08.042](https://doi.org/10.1016/j.cell.2026.08.042)，V。立场/框架论文，正式提出虚拟细胞世界模型（持久状态、动作条件模拟、反事实推理、长程规划）。**这预占了提法本身，而不是演示。** 它正是在呼吁本目标要做的东西。

**判断：** 组合（共同学习＋秩竞争的条件预测＋能改变药物选择的最小可执行实验＋规则边界修订＋同时迁移到未见细胞与未见药物）**未找到**。单项均有 2025–2026 先例，无人接起来。

## B. 最接近的分项先例

- **B1 智能体闭环实验设计**：Robin（*Nature* 2026, DOI 10.1038/s41586-026-10652-y，V；半自主，人执行实验）；BATCHIE（*Nat Commun* 2025, DOI 10.1038/s41467-024-55287-7，V；信息论批量设计，探索 1.4M 组合的 4%）；三药组合闭环优化（arXiv:2606.06562，V）；STELLA（arXiv:2507.02004，V；自演化多智能体，评测，无湿闭环）；Biomni（bioRxiv 2025，V）；AI co-scientist（arXiv:2502.18864，V）；POPPER（ICML 2025，**S 未读原文**）。
- **B2 跨背景秩/条件结构作为研究对象**：**"Two largely independent axes of drug transcriptional response in Tahoe-100M"**（Research Square 2026, DOI [10.21203/rs.3.rs-10448056/v2](https://doi.org/10.21203/rs.3.rs-10448056/v2)，V）——context-robustness（背景无关"core"占比）排序、dose-emergence 排序、方差分解（药身份＋背景 η²≈0.53–0.66 远大于剂量 ≈0.02）。**这是与本目标"秩/条件对象"最接近的先例，但它是描述性的，不预测、不选实验。** AssayBench（arXiv:2605.10876，V；基因秩预测、nDCG）；STATE（*Cell* 2026，V）；Virtual Cell Challenge 2026（*Cell* 2026, DOI 10.1016/j.cell.2026.08.004，V；未见细胞系零样本）；VCLMU（arXiv:2610.04475，V；机制单元式世界模型）；NetPolicy-RL（*J Comput Aided Mol Des* 2026，V；把每细胞系选药当离线 RL，理由正是"静态排序与实际决策不对齐"）。
- **B3 决策论获取**：BATCHIE；**CLARA**（bioRxiv 2026, DOI [10.64898/2026.10.05.756921](https://doi.org/10.64898/2026.10.05.756921)，V）——LLM 智能体在确定性 GP 批量主动学习环境里控策略，40/40 胜随机，但**在 2/4 靶点上与最强固定策略统计打平、另 2/4 输给靶点专用领先者**；200 次预设信息消融显示去掉不确定性/多样性/记忆只带来小幅端点变化，**打乱解释性证据在 39/40 配对战役中复现了完整分配路径**；SHIFT-DRP（*JCIM* 2026，V）；Query Matters（*JCIM* 2026，V）。

## C. 反证与阴性

1. **PerturbTrace: Evaluating Feedback Use by AI Co-Scientist Agents in Perturbation Discovery** — bioRxiv 2026, DOI [10.64898/2026.08.18.745260](https://doi.org/10.64898/2026.08.18.745260)（PPR1303031），V。**对"反馈→决策"这一转变，是已发表的空结果。** 四个 LLM 智能体、17 个筛选题，对随机/主动学习/LLM 引导 BO；智能体在 ≥15/17 上胜最强非智能体方法；但六个题上的受控检验显示**真反馈相对随机或无反馈没有一致优势**；576 次转变中仅 43 次（7.5%）完成 Feedback→State→Action→Outcome，其中 25 次发生在**随机**反馈下。结论：高召回不等于用了反馈。
2. **"An Empirical Comparison of Virtual Cell Models"** — Research Square 2026, DOI [10.21203/rs.3.rs-10434123/v1](https://doi.org/10.21203/rs.3.rs-10434123/v1)，V。11 方法 5 家族 6 任务族 9 数据集：未见单基因扰动上 State +26% 对线性 +19%、GEARS +22%；若干基础模型预测器**低于线性**；全基因 Pearson 由"不变模型"最高。在**组合（非加性）扰动**与**跨背景到未见细胞类型**上深度模型有可复现收益，但整体"表征强、预测弱"。
3. **CLARA**（见 B3）：与强固定策略打平/落后；显式推理非因果承载（39/40 证据打乱复现）。
4. **PertEval-scFM**（bioRxiv 2024，窗口外，V）：scFM 嵌入在分布偏移下无一致改善。
5. **"A Neural-Network-Free Calibration Matches or Beats Deep Single-Cell Perturbation Response Models Across Four Datasets"** — *Genes* 2026, PMID 42510856，V。CPU 解析校准在九指标面板上匹敌/超过 scGen。与"重训练/层级强静态对照很难打败"直接相关。
6. **AssayBench**（见 B2）：无方法接近经验上限，可训练基线输给零样本 LLM。

## D. 对本研究的具体含义（只是含义，不是结论）

- 目标里的"反馈修订规则边界并改善后续决策"正是 PerturbTrace 已发表空结果所在的一步；因此本项目**必须把"反馈是否改变后续选择"当作首要被测量**（条件在反馈上的决策改变），而不是用最终命中率/端点召回代替。R2 自己的结果（GP＋随机反馈劣于静态强预测、KG≈随机）与该空结果方向一致。
- "智能体造虚拟细胞""智能体跑扰动筛选""VCWM 提法"都已被占；本项目**不能**把其中任何一项当贡献。剩下的可辩护对象是**秩竞争的条件预测在什么条件下可辨识、以及据此选择的最小证据是否真的可执行且可读出**。
- CLARA/AssayBench/Empirical-VC-Comparison 共同说明"超过强静态基线"这一门槛在最近的可测场景里**尚未被满足**，因此本项目把该门槛保留为必要条件是对的。

## 检索记录

引擎：DSH web_search、Europe PMC REST `/search`（resultType=core）、arXiv API、Crossref API。主要检索式（原文照录）：

- web_search：`agent virtual cell co-learning drug response transfer unseen cell lines`；`DiscoBAX drug discovery Bayesian optimization Google`；`Robin multi-agent system drug discovery closed loop`；`STELLA self-taught LLM agent bioinformatics tool`；`Virtual Cell Challenge 2025 results paper Arc Institute`；`VCHarness virtual cell benchmark`；`POPPER agentic sequential falsification hypothesis`；`ARTEMIS agent drug discovery 2026`。
- Europe PMC：`(TITLE:"virtual cell") AND (FIRST_PDATE:[2025-01-01 TO 2026-12-31])`；`(ABSTRACT:"LLM" OR ABSTRACT:"large language model") AND ABSTRACT:"closed-loop" AND (ABSTRACT:"drug screening" OR ABSTRACT:"perturbation")`；`(ABSTRACT:"ranking" OR ABSTRACT:"rank order") AND ABSTRACT:"drug response" AND (ABSTRACT:"cell line" OR ABSTRACT:"context")`；`ABSTRACT:"active learning" AND ABSTRACT:"drug response"`；`ABSTRACT:"perturbation" AND ABSTRACT:"linear baseline" AND (FIRST_PDATE:[2024-06-01 TO 2026-12-31])`；`TITLE:"Tahoe-100M"`；`TITLE:"State" AND ABSTRACT:"perturbation"`。
- arXiv：`ti:"virtual cell" AND abs:"agent"`；`abs:"world model" AND abs:"perturbation" AND abs:"cell"`；`ti:"VCLMU"`；`ti:"immune world model"`；`ti:"AssayBench"`；`abs:"closed-loop" AND abs:"drug" AND abs:"LLM" AND abs:"experiment"`。

**未解决：** ARTEMIS 在本领域找不到一手来源，视为不可信/可能是讹传；POPPER 与 DiscoBAX 只有片段级；Robin 全文付费墙；四份预印本（VCHarness、CellForge、immune world model、CLARA）全文未读，其内部是否已做"反馈 vs 随机"消融无法从摘要排除。**没有任何 2025–2026 研究报告过 LLM 智能体在药敏选择上相对强静态预测器、同预算下的独立决策收益，也没有报告向未见药物的迁移；未见细胞系有 VCC 2026 覆盖。**
