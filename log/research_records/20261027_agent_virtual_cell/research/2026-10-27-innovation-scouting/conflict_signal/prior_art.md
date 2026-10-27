# 先例核验：冲突信号与三类失败区分的机制覆盖（R198-A1）

2026-10-27。目标：对本任务机制候选涉及的先例（AlphaEdit / LOGICZSL / Poke&Strike / PDTSyn / BATCHIE）逐条核验"其机制是否已被用于药理组合反馈 / 关系冲突诊断"，给出**已覆盖 / 部分覆盖 / 未发现**与一手锚点。**零命中一律写"本轮有界检索未发现"，不写"不存在"。**

证据级沿用 `cross-domain-directions/evidence_notes.md` 的标度：R=题录/索引，A=摘要，P=读过相关方法/限制片段，F=逐段全文核读。本轮**没有把任何文献新读成 F**；新增检索只到索引/摘要级（R/A）。**web_fetch 在本环境对域名返回"非公网 IP"（同 SYNTHESIS C58 记录的既有故障），因此本轮新检索只使用 web_search 返回的索引片段，不能据此声称读完全文。**

## 0. 检索范围（有界、可复核）

- 复用本地已核原文：`research/2026-10-27-cross-domain-directions/challenge_sources/`（AlphaEdit v4 HTML 659,872 B；AlphaEdit 复现研究 v2 HTML 358,099 B；LOGICZSL CVPR2025 PDF + 文本）；`data/external/research_sources/20261023/functional_mechanism_frontier/`（AlphaEdit 检索 Atom、revision/feedback/uncertainty 检索体、alphaedit/replication 全文 HTML）。
- 本轮新增 web_search 共 5 次调用、15 条 query（原文见 `record.md` §3）：
  - 知识编辑/冲突：`knowledge editing protected relations conflicting new evidence ...`、`model editing conflicting knowledge AlphaEdit ACL 2026 findings`、`knowledge editing drug response prediction biomedical ...`；
  - Poke&Strike/辨识：`Poke and Strike task sensitivity parameter identification drug screening feedback`、`... task-informed exploration policies ... abstract`、`active learning model selection misspecification detection number of experiments distinguish hypotheses`；
  - 药理学关系/失效：`drug combination prediction model failure mode relational conflict versus representation missing context`、`drug combination transfer learning applicability condition violation detection`、`context-specific drug combination effect inversion cell line prediction prior relation violated`、`logical constraints drug combination synergy prediction knowledge graph`、`knowledge added drug response prediction constrained relation violation test`；
  - 变化分类：`model misspecification detection structural change versus parameter drift online learning feedback`、`concept drift taxonomy real drift virtual drift conditional change relation`、`detect misspecification versus parameter shift online feedback experiment design`、`AlphaEdit biomedical model editing drug discovery pharmacogenomics`。
- 检索非穷尽；未命中不等于文献不存在；未复现任何作者代码或效果。

## 1. 逐条核验

### 1.1 AlphaEdit（Fang et al., ICLR 2025；arXiv:2410.02355v4）

- 一手锚点：[arXiv:2410.02355v4](https://arxiv.org/abs/2410.02355v4)（本地 HTML 快照 `challenge_sources/AlphaEdit_2410.02355v4.html`）；摘要与 v4 方法：把编辑扰动投影到**被保护知识的零空间**，使旧键输出在编辑后不变；作者称平均提升 36.7%。复现研究（[arXiv:2606.26783v2](https://arxiv.org/abs/2606.26783v2)，本地 HTML 快照）报告：保护在原始范围内可复现，但**保护有界而非无条件**——扩展编辑规模/新模型架构下退化，且大范围顺序编辑会损伤通用下游能力与安全拒答。
- 机制：**保护旧知识 vs 写入新证据，取最小改动**（零空间投影）。
- 覆盖判定：
  - 作为**机制**：**已覆盖**（NLP 知识编辑域；P 级）。
  - 用于**药理组合反馈 / 关系冲突诊断**：**本轮有界检索未发现直接应用**。药理上没有可直接引用的"旧键"；线性移植=约束回归/投影核（本规格已列为必做等价控制，见 spec §3）。
- 不能支持什么：AlphaEdit 的"保护"是对旧**输出**的保持，不检验旧关系是否**有适用条件**；"保护有界"的复现结论恰恰支持本规格把"保护对象选择/释放"当显式对象，但这不是新颖性证据。

### 1.2 AlphaEdit+：冲突/不一致知识下的模型编辑（ACL 2026 Findings，索引级）

- 索引锚点：[AlphaEdit+: Model Editing in the Presence of Conflicting and Inconsistent Knowledge](https://aclanthology.org/2026.findings-acl.728/)（R 级：本轮只从检索索引看到题名/位置，未能取全文——web_fetch 不可用）。
- 机制（从题名/索引可推断的范围，不外推）：把"冲突/不一致知识"作为模型编辑的显式问题对象。
- 覆盖判定：作为"冲突"在知识编辑域的**问题提出**：**部分覆盖**（R 级；不能据此声称其方法=本规格）。用于**药理组合反馈**：**本轮有界检索未发现**。不能支持"三类失败可区分"或"冲突可预测未测决策"。

### 1.3 LOGICZSL（Wu et al., CVPR 2025，官方 PDF）

- 一手锚点：[CVPR2025 官方 PDF](https://openaccess.thecvf.com/content/CVPR2025/papers/Wu_LOGICZSL_Exploring_Logic-induced_Representation_for_Compositional_Zero-shot_Learning_CVPR_2025_paper.pdf)（本地 `challenge_sources/LOGICZSL_CVPR2025.pdf` + 提取文本；协调者核读 §§3.2–3.4、式 2–16，P 级）。
- 机制：LLM 构建对象/属性关系树；蕴含/合取/量词松弛为可微损失与分类损失联合训练；开放组合推断另用兼容矩阵。
- 覆盖判定：
  - "把共享关系显式化为可被数据检验的约束"：**部分覆盖**（CV 组合零样本；P 级）。
  - 用于**药理组合反馈**：**本轮有界检索未发现直接应用**。
- 不能支持什么：其语义树前提不支持"同靶点→同功能"；把 LLM 药理树编成硬蕴含不等同于"有实测误差的功能关系"；不区分"关系失效"与"数值偏差"。

### 1.4 Poke & Strike（Aoyama & Moura, 2025；arXiv:2509.00178）

- 一手锚点：[arXiv:2509.00178](https://arxiv.org/html/2509.00178v1)（P 级：evidence_notes 记录读 §§4.1–4.5、5.3、6；本轮只从检索索引复核题名/主题，R 级片段）。
- 机制：**任务信息（task-informed）的探索策略**——按任务对参数误差的敏感度分配探索，决定需要辨识到什么精度；依赖仿真中的特权真值；作者明确动态结构失配未解决。
- 覆盖判定：
  - "按任务精度决定辨识/停止"：**部分覆盖**（RL/参数辨识；P 级）。
  - 用于**药理组合反馈 / 药物筛选**：**本轮有界检索未发现直接应用**。
- 不能支持什么：其"任务敏感度"来自仿真真值/同个体轨迹，迁入细胞必须替换这些条件（本规格 M2 已显式处理：不把仿真真值当可用特权；用可购买菜单与决策翻转概率）。

### 1.5 PDTSyn（2026, Briefings in Bioinformatics, DOI 10.1093/bib/bbag199）

- 一手锚点：[doi:10.1093/bib/bbag199](https://doi.org/10.1093/bib/bbag199)（P 级：evidence_notes 记录读 JATS §§2g/2h/2m/2r、3j 与部分表；未核补充/源码）。
- 机制：共享药理知识 + 细胞条件特异参数分解、分布对齐；已做未见细胞、药物和药对设置。
- 覆盖判定：
  - "共享关系 + 背景特异通道并做冷启动预测"：**已覆盖**（预测架构层；P 级）。
  - "局部功能反馈揭示的条件边界与修订迁移"：**未覆盖**（其评估是留出泛化，不是反馈更新/冲突分类）。
- 不能支持什么：三类单轴 holdout 不能自动当双轴同时冷启动；其机制措辞不作靶点真值。

### 1.6 BATCHIE（2025, Nature Communications, DOI 10.1038/s41467-024-55287-7）

- 一手锚点：[doi:10.1038/s41467-024-55287-7](https://doi.org/10.1038/s41467-024-55287-7)（P 级：evidence_notes 记录读旧库 JATS Sec12/14/20、式 24–30）。
- 机制：条件组合模型 + 后验更新 + 整板选择；一般有界非负对称模型距离可表示动作分歧。
- 覆盖判定：
  - "组合反馈的更新 + 整板选择"：**已覆盖**（外层流程/能力；P 级）。
  - "三类失败 operational 区分 / 关系适用条件失效的证书"：**未覆盖**。
- 不能支持什么：独立培养/完全双冷启动需另核；普通共同学习外层或动作距离不新（本规格不主张）。

### 1.7 其它相关先例（本轮检索新增，索引级 R；不足以支撑覆盖判定）

| 来源 | 与本题最接近之处 | 覆盖判定 | 限制 |
|---|---|---|---|
| SynergyGraph: predicting cell line specific drug combination synergy scores using knowledge graph representation and hypergraph（Scientific Reports 2025；检索索引） | 细胞系特异的药对协同 + 知识图谱/超图关系表示 | **部分覆盖**（药对关系建模；R） | 未取全文/方法；不能证明其含冲突诊断或反馈更新 |
| What Changed? Drift Detection with Real, Virtual, and Incomparable Diagnosis（arXiv:2609.27865；检索索引） | 区分真实变化/虚拟变化/不可比较的诊断思想 | **部分覆盖**（变化类型诊断的一般框架；R） | 非药物组合、非本三类定义，未见全文，不能映射为同构 |
| From Concept Drift to Model Degradation: performance-aware drift detectors（arXiv:2203.11070；检索索引） | 概念漂移分类（数据/标签/关系变化的术语体系） | **部分覆盖**（术语与检测传统；R） | 与"共享关系适用条件失效/表征遗漏状态"不是同一对象，引用只作类比 |
| Lovell et al., 2011（PMLR；检索索引） | "用最少实验区分竞争假设"的设计原则 | **部分覆盖**（实验设计原则；R） | 生物网络参数辨识、非组合药筛；不能当药理实现 |
| constrained regression + 不可行诊断 / minimal correction set（数学/优化常规） | 约束最小二乘、不可行集合诊断（IIS/MCS）是标准运筹/统计工具 | **已覆盖**（数学操作层，教材级） | 本规格**不主张**算法新意；只用它把"冲突"显式化 |
| 本项目 R193-A0/A1、R194/Q2、R197（内部先例） | 匹配四元组与 Q 对比（R193-A0 qualified）、Q 主检验 inconclusive（C171）、1.43% 仅加性主效应份额（C174） | **部分覆盖本题的数据对象** | 不得回改旧结论；本规格只在已登记边界内设计新对象 |

## 2. 覆盖结论汇总

| 机制 | 作为机制本身 | 用于药理组合反馈 | 用于"三类失败区分" |
|---|---|---|---|
| AlphaEdit 零空间保护/最小改动 | 已覆盖（P，NLP 知识编辑） | 未发现（有界检索） | 未发现 |
| AlphaEdit+ 冲突/不一致知识编辑 | 部分覆盖（R，题名/索引） | 未发现 | 未发现 |
| LOGICZSL 逻辑关系约束 | 部分覆盖（P，CV） | 未发现 | 未发现 |
| Poke&Strike 任务精度/辨识-停止 | 部分覆盖（P，RL 参数辨识） | 未发现 | 未发现 |
| PDTSyn 共享+背景特异预测 | 已覆盖（P，生物信息） | 部分覆盖（预测架构，非冲突更新） | 未发现 |
| BATCHIE 条件模型+后验更新+整板选择 | 已覆盖（P，生物信息） | 部分覆盖（外层更新/采样） | 未发现 |
| 约束回归/不可行诊断/最小释放集 | 已覆盖（数学常规） | 未发现（作为"关系适用条件失效证书"） | 未发现 |

**结论（边界内）**：本规格的机制成分**全部有已知先例**；把"保护旧关系 vs 新证据 + 冲突证书 + 决策精度门控"组合起来**不被任何单篇覆盖**，但这是组合结果，**不构成新颖性主张**。真正可研究的对象是：三类失败在独立功能测量中能否被上述对照量区分，并改善未测动作——这只能由下一轮的预注册实验回答。

## 3. 本规格不得引用先例支持的主张

1. 不得写"AlphaEdit/LOGICZSL/Poke&Strike 已被用于药理学组合反馈"——本轮有界检索未发现。
2. 不得写"冲突信号已被证明有用"——没有实测。
3. 不得写"某方法首创新算法"——机制成分均有先例；组合贡献待未来证据。
4. 不得把"冲突"写成相对残差/距离/leverage 的新颖信息——spec §2–§4 已把它定义为须与这些对照量正交、可区分的量；是否正交是**要检验的**，不是声称的。
5. 不得越 C174/C171/C167 的边界：不把 1.43% 当规律总量，不把 `inconclusive`/`not_replicated` 当阴性，不把旧等价性结果当已否证全部共同学习。
