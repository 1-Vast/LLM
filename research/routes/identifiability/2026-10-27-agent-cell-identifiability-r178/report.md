# 这条现象是已知的——文献核对后必须收窄本项目的自我定位

2026-10-27。**目标第一段要求“检索 2025–2026 一手论文，辨别与已有知识增强、机制推断及主动学习的差异”，而我已连续多轮 `external_literature_queries = 0`。本轮补上。**

## 1．检索到的直接先例

| 工作 | 与本项目的关系 |
|---|---|
| **One-hot news: drug synergy models shortcut molecular features**（[Bioinformatics, btag040](https://openurl.ebsco.com/EPDB%3Agcd%3A12%3A3376524/detailv2?sid=ebsco%3Aocu%3Arecord&id=ebsco%3Adoi%3A10.1093%2Fbioinformatics%2Fbtag040)） | **标题即断言“模型走 one-hot 药物身份这条捷径”——正是我量到的现象** |
| **A leakage-controlled cold-start benchmark for drug-combination synergy classification**（[BMC Bioinformatics 2026](https://link.springer.com/article/10.1186/s12859-026-06665-z)） | **冷启动 + 泄漏控制基准**——正是我做的那套结构/容量/死块控制的问题设定 |
| **A systematic evaluation of deep learning methods for the prediction of drug synergy in cancer**（[PLoS Comput Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1010200)） | 描述的模型即“**one-hot 药物标识 + 基因/注释**”——**与我 `identity + 通路` 同构** |
| [OOD-GraphLLM](https://export.arxiv.org/pdf/2605.30247)、[SynVerse](https://pmc.ncbi.nlm.nih.gov/articles/PMC12753315/) | 分布外泛化 / 模块化评估框架 |
| [Pathway activation model for personalized prediction of drug synergy](https://pubmed.ncbi.nlm.nih.gov/40459126/)（eLife 2025） | 以**通路**作为协同预测核心表示 |

## 2．判决：H420 成立——现象已知

**“one-hot 身份是捷径、注释只在冷启动起作用”在 2025–2026 文献里已有明确工作（至少标题级已断言）。所以本项目不能把这套东西表述为机制或方法上的新发现。**

## 3．差异到底在哪（目标要求的那句话）

| 维度 | 文献常见做法 | 本项目做了什么 |
|---|---|---|
| **定位** | 提出新模型/新表示，报告平均性能 | **不提出新方法**；只**测量**一条既有现象在什么条件下成立 |
| **条件形状** | 通常二选一（冷启动 vs 非冷启动） | **量化为阶跃而非渐变**（完全可用时 **+0.0000**，缺失时最大），并给出 6 倍衰减 |
| **对拍对象** | 多与随机/旧模型比 | **同维随机块、打乱映射块、死块、药物边际、靶点注释逐一对照** |
| **模型家族** | 多为单一架构 | **ridge 与树都用**，并区分“幅度依模型”与“排序不依模型” |
| **能力边界** | 少有人写 | **明确写出：只排组合、不排细胞**（C141） |
| **验证成本** | 少有人算 | **约 1,600 个测量、分配近乎中性**（C136/C144） |

**一句话：不是提出了一个新机制，而是把一条已知现象的条件、对拍、边界与验证成本量化了。**

## 4．必须承认的方法限制

**本机 `web_fetch` 对所有域名返回“非公网 IP”（C58 再次确认），所以本轮只能到标题与摘要级。**

- **我没有读到这些论文的方法与数字**，不能引用其具体结果；
- **“现象已知”这个判断建立在标题与片段上**——虽然 `One-hot news` 标题相当明确，**严格说仍是二手判断**。

## 5．处置

**新增 C145**（现象为先例、贡献限定在测量层面），**综合 §1 加一句提醒**：读本文前应知道 one-hot 捷径与冷启动问题已有工作，**本文不主张发现它**。

## 6．限制

**只到标题/摘要级**；三组查询、**非系统综述**；未读全文、**不引用其数字**；回顾性；不涉及机制/临床/药物选择；**元学习/RSI 未做**。

## 7．下一步

**要让这条定位站得住，需要读到至少 `One-hot news` 的摘要全文**——但那需要能访问该域名的网络路径，**本机做不到**。所以记为**外部依赖**，不再在本机反复检索。

## 8．边界

无下载、无实验、0 次付费 LLM 调用；**3 组检索 + 2 次抓取尝试（均因非公网 IP 失败）**。**未晋升代码**。未改 `src/`、`tools/`、sealed。

数值：[E178_RESULTS.json](E178_RESULTS.json)｜预注册：[PROTOCOL_E166.md](PROTOCOL_E166.md)｜记录：[record.md](record.md)
