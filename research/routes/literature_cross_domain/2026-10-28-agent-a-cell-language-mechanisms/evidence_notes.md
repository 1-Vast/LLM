# 原始来源与迁移约束

2026-10-28。六条query原请求/响应在sources/Q*_receipt.json与XML/JSON；Q1 12/50、Q4 10/36、Q5 10/44、Q6 10/72，仅首屏，未穷尽。Q2 Crossref未找回BioReason，Q3 arXiv题名精确核到唯一结果。最初六个核心来源中AlphaEdit已在旧库，实际新增五篇；第六个新增来源为同轮Q6已检出的Slot-JEPA，另记如下。均用reference_library.py存库/复用，人工核h1与arXiv页头版本，非摘要冒充全文。全部仅P级选节阅读，未运行代码。

| 来源 | 实际阅读范围 | 对候选的影响 |
|---|---|---|
| [BioReason 2505.23579v2](https://arxiv.org/html/2505.23579v2)，2025-10-24版本 | §3、3.1、3.3、3.4、Limitations；未核RL完整附录/代码 | 冻结DNA模型、可学习线性投影、LLM输入嵌入拼接与GRPO已直接覆盖生物基础模型接LLM；不能只改DNA为细胞就称新算法 |
| [PertMind 2608.16419v3](https://arxiv.org/html/2608.16419v3)，2026-10-06版本 | §2.1–2.4完整（含被截短后单独追回的末段）、3.1、4.3、6；未核所有附录/结果 | 已有Tahoe扰动监督+LLM、目标基因外的通路代理奖励、训练检索证据和留出细胞，以及AssayBench跨任务功能基因筛选排序。通路奖励不验证全部自由文本、也不是蛋白活动实测。不能声称“没人把细胞模型/细胞数据训练成Agent推理”或“没有跨任务功能证据” |
| [PertReason 2607.18777v1](https://arxiv.org/html/2607.18777v1)，2026-07-21 | §3.1、3.2的Splits/DE labels、3.3相关四段、§4.1 SFT/GRPO、4.2；§5.4两项局限、AppendixH | 已有细胞状态门控KG路径、结构化推理、边方向学习及化学/遗传混合任务。作者明确reference路径是curated proxy而非完备因果真值，化学→top2基因替代失配。CL1不能将其简化成仅文本，也不能重复“加入细胞状态/知识图谱” |
| [SUAVE 2610.04009v1](https://arxiv.org/html/2610.04009v1)，2026-10-02 | §III正文、III-B、III-C、III-D；未核全部机器人实验/代码 | 单transformer/共享词表/统一mask任务可使模型兼具world/policy/联合生成。图像目标在动作前，块因果mask不能免费给出动作条件正向细胞响应；CL2需调整可见性并区分条件与干预，不能照搬名称 |
| [CASE 2607.18820v1](https://arxiv.org/html/2607.18820v1)，2026-07-21 | Problem Formulation、Definition1、Training-Time Causal Alignment、Selective-loss SFT、Inference-Time Structural Enforcement；未审计定理/数值 | 反事实CoT数据及答案对instruction注意力遮挡已有。隐藏CoT侧状态仍可承载指令；结构约束不自动证明文字反映真实生物机制。CL1改用可执行、可实测检验的作用作为计算中介，教师改写不充生物反事实 |
| [AlphaEdit 2410.02355v4](https://arxiv.org/html/2410.02355v4)，2024首次，2025-04-22所读版本 | §3.1–3.3、§6；未核证明/代码；后续官方arXiv journal-ref核到ICLR2025 Oral | 旧键零空间投影与闭式编辑直接覆盖投影保护；更重要的是本项目旧轮已用同一原理保护真实功能关系，CL3据此撤位，不能计新机制 |
| [Slot-JEPA 2610.28074v1](https://arxiv.org/html/2610.28074v1)，2026-10-20 | §3.1、3.2、3.3的memory/predictor、3.4、§5；abstract/introduction仅开头选段；未核数值/代码 | stable slots+variable masks、槽内/跨槽预测和UOT已有；slots不保证物理实例，UOT空间质量不是活体数量。CL4必须有来源/数量锚点，不从视觉对应迁移出虚构细胞轨迹 |

身份/hash前12位：BioReason 75a4d21e9714，PertMind fc55918ac52b，PertReason 7429146ae985，SUAVE 4b230ac5e9e9，CASE 6c397175fbef，AlphaEdit a802b3e305c1。完整hash、来源URL及字节数以共享papers.tsv和本轮最终verify为准。抓取不是复现成功。

CellChain（2610.16346）、2026因果抽象新文等目前只读检索题录/摘要线索，未取得/核读核心方法，不用来支持新意判决；属于下一次必要的最近邻刷新，而非“不存在先例”。FlexTok/潜在推理等最初线索本轮未核读，当前候选不以它们作已验证机制依据。前轮PSR/EDMD/价值等价的重叠继续有效。Slot-JEPA原文hash前12位9e08187987a9。

PertMind官方GitHub已保存commit500da7b6ad3acf3854c55854cb1ce7a6679e6099，7文件，README/docs/assets/LICENSE；Apache-2.0实读。它是landing-page仓库，不是完整训练实现。原文及README另指向HuggingFace；本轮只核官方API文件清单，含推断脚本和8,044,982,080-byte模型文件，未下载权重、未安装运行。不能把官方快照已存说成训练复现条件已齐。

原始HTML的按标题抽取只为定位，不将提取的完整章节或hash视为全部已读。maestro没有bs4，本轮读取改用stdlib进行heading-bounded文本抽取，无安装。未执行任何从论文下载的代码。
