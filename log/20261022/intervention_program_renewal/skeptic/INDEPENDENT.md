# 独立近邻审查：具体算子与仍开放的缺口

2026-10-22，反方。**本稿先于读取本轮 mechanism/、improver/、rootaudit、root/provider 或 peer 独立草稿。** 只读本轮协议、既有冻结历史、旧一手材料与本代理取得的来源。没有新生物 response、拟合、API proposal、旧 freeze 修改或生成 agent 程序执行。

## 独立判断

目前不能推荐实现一个新的 world/agent/RSI 架构。仍开放而有价值的窄缺口是：**在模型类别确有错误的真实细胞干预任务中，从有限实验反馈学得的研究更新程序，是否能比同信息普通重拟合、模型选择与等预算程序搜索，更有效地修正后来独立任务的功能决策。** 最新工作并未封死这一问题，但“这串能力尚未一起验证”只是研究问题，不能冒充新算法。

本稿只提出一个具体归约来杀死一种可能的创新主张：**将原子实验/程序编辑打包成前瞻宏操作，不能在零调度成本、无共享实验折扣的串行条件下单靠打包获得更强策略表达能力。** 这比“学习改进器已有”更具体；不否定不满足这些条件的其他算子。待 root 给出具体新公式后，应逐项验证其是否落入此归约，而非由宽泛名字裁决。

## 已读一手近邻及实际操作

| 来源/版本与访问层级 | 实际操作及有用边界 |
| --- | --- |
| [VCLMU，2610.04475v1](https://arxiv.org/html/2610.04475v1)，旧核元数据2026-10-03；本轮新取完整HTML | control-conditioned top-K router 选择 LMU；每 LMU 身份结合可刷新候选基因集与共享 query，状态由当前表达定义；干预引起残差随机转移；观测状态 stop-gradient 对齐与重构约束。见 §2、A.4–A.7。已有明确机制单元、重用身份、状态转移与表征更新操作，不能只据这些另命名。D.1明确 downstream test 干预可能已在别的背景预训练出现，因此不是所有历史都从未见该干预。主要评价单基因表达响应；没有本项目所需的功能决策与研究 improver 效率实验。 |
| [VCWorld，2512.00306v1](https://arxiv.org/html/2512.00306v1)，2025-12 v1（本轮未另取提交日元数据）；本轮完整HTML | 原问题被改写为 `(cell lineage, drug, gene)` 的 DE/DIR 二分类；构建知识图谱和实体描述，按 MoA/结构等检索 analogue/comparison cases，再 CoT 输出分类及解释。见 §3.1、§3.4。这是具体知识条件预测流程，不能从名称推断已有持久状态、可组合时序干预或长期规划性能。反过来，也不能将它的分类任务贬成没有实际预测意义。 |
| [CellForge，2508.02276v1](https://arxiv.org/html/2508.02276v1)，2025-08 v1；本轮body达到8MiB上限，**仅认证所保留的主文/方法/附录段，不称完整全文** | Task Analysis→多专家设计→Critic/peer confidence更新（0.3历史+0.4critic+0.3peer，最多10轮）→OpenHands代码/traceback修复→训练、验证下轻量调参。§4.2、§4.3，已覆盖真实单细胞数据上的多代理架构设计与执行。§Limitations 明说没有后续wetlab验证。该设计讨论中的confidence不是实验性改进credit；所读段落未建立初始/改进improver在共同起点上对后来功能研究任务的效率差。 |
| [Deep Adaptive Model-Based Design of Experiments，2603.16146v2](https://arxiv.org/html/2603.16146v2)，旧核v2元数据2026-03-24；本轮完整HTML | 已知ODE、未知target/nuisance参数，history→下一输入的Transformer policy；targeted sPCE边际化nuisance，离线对可微模拟反传。§3–4、Appendix A。不是只有一个泛称DAD：其一次episode需 L+M+2 次ODE rollout，明确对比信息目标与myopic/Dirac BIM。§6明确 prior shift需重训、未处理model misspecification、过程噪声未纳入，physical closed-loop deployment仍是后续工作。故“学机制模型下适应性测量/干预、处理nuisance”已有；**真实模型错误下更新模型结构/研究方法**仍不能由此论文宣称解决。 |
| [SpecRSI，2610.16491v1](https://arxiv.org/html/2610.16491v1)，2026-10-12；本轮复用已保留完整primary body，并重新投影具体段 | VATS选择DRAFT或付费VERIFY bundle；Scorer预测后续已验证净收益，GVO用相同起点独立完整search的回报更新drafter/policy，同状态强制续程只训练Scorer，验证contract Γ保持固定。D.1已区分reset/carry/same released artifact；F.5有paid same-state continuation。因此后继credit、失败编辑、冻结初/新improver共同起点比较均不是空白。**G.2.2 Proposition 4进一步给出宏计划与singleton策略的准确等价条件**，下节用它而非宽泛RSI标签作归约。作者科学任务为PyBaMM/AQM/FDTD/Reactor/IRP，不把其成绩当真实细胞药物效用。 |

CellForge另一个2026-09-17 Research Square版本题为 *AI Scientists for Building Virtual-Cell Models*，本轮只从EuropePMC原始abstract/元数据读到，**不将其与所取2025 arXiv v1静默当同一版本**。ProteinTalks（Nature，2026-09-09）摘要已有动态蛋白组到药效/联合/类器官用途，项目PTV历史也已测试过相关路线，不由本轮摘要重新晋级。2026-08-11的virtual-cell immune-rejuvenation预印本摘要报告equal-weight到balance-constrained minimum目标修订及独立13-compound T-cell assay，说明“生物反馈让agent改评分”也不是空白；本轮未取得该文全文或重验其效果。

Hyperagents/AIDE²/MetaShare只沿用 `log/20261021/autonomous_rsi_round1/NOVELTY_ADVOCATE.md` 的旧证据层级：Hyperagents曾读全文且整份task+meta转移的边界保留；AIDE²与MetaShare为原始摘要层。没有重复下载，也不把摘要升级为详尽方法/控制核验。

## 唯一具体归约：宏研究操作的串行展开

考虑主张“把模型更新、实验验证与下一步编辑联合成多步宏操作，比普通逐步AL/程序搜索在原则上更强”。令全部可见状态为 `S=(真实已购数据D, 模型/程序p, 版本档案V, 已付检查E, 剩余预算b, history)`；宏操作是允许依历史停止/分支的有限原子操作树。每个原子操作可以是真实数据查询、一次确定修复、编辑提案或验证，成本/观测核由同一实验合同规定。

在以下条件下，编译器将宏操作树的当前第一个原子操作执行后，把剩余树和宏策略内部记忆写入history；下一步从同一已更新状态续行：

1. 串行执行，原子许可与信息相同；没有宏操作专有的查询或编辑。
2. 调度/重新规划成本为零，没有共同setup、并行折扣、时间窗口或宏交易原子性。
3. 具有有限原子预算；singleton策略允许相同history/internal memory，而非故意只给myopic分数。

对原子步数归纳，两者每步观测、状态、剩余预算的联合分布相同，故最终程序/模型、真实功能效用与全部原子成本的分布相同。该结论与SpecRSI G.2.2 Proposition4直接对应，**不是本项目新定理**。若候选只改变bundle边界、分数名字或先算计划的代码位置，应停止其“策略表达能力的新机制”主张；最便宜反证是代码/代数映射，无需打开生物response。

这不说宏方法没有工程价值。若原子政策被限定myopic、调用LLM有真实调度成本、湿实验存在shared plate setup、并行延迟或不可逆状态变更后的时窗，归约条件可能不成立。此时必须把真实条件、可用信息与成本同时给对照；收益应归因于具体计算/实验结构，不能用故意削弱的singleton基线造出world/RSI创新。也不能用“宏策略一般能表达任意政策”反过来否定所有新算法：本文只处理上述具体claim及条件。

## 数据/应用与下一决定

目前没有为本归约另立细胞实验，也没有认证新action/function lineage；**本稿不给一个toy实验生物验证身份，不推荐据它启动fit**。最有价值的下一步是对root提出的唯一具体operator检验：它是否真的改变允许的更新/预测，是否存在上述归约之外可观测的性质，是否有真实细胞干预/功能数据能反证；再决定数据资格或数值试验。

若仅是参数/模型候选搜索，普通refit、持续学习、AL、混合与相同候选的等预算搜索必须能访问同样反馈、历史与知识；不能让新方法独享mechanism labels。若有超出归约的精确性质，可用真实静态公共功能screen测试，只要action menu与观测身份合格；不强行要求washout或wetlab。world、agent、继承、联合与improver1>improver0要分别给预测；尤其新旧improver须共同p0/w0与后续独立任务，改进器形成成本及失败全部计入。

本稿停止的是**尚无实质算子就启动框架**及特定宏表达能力claim，不停止总目标，也不根据旧阴性预判新的具体性质失败。

## 请求与失败记录

已用7次显式GET，timeout25s、cap8MiB、无自动retry/redirect：3份完整arXiv方法HTML（VCLMU、VCWorld、Adaptive）、1份EuropePMC检索body、1份arXiv429、1份Nature303、1份CellForge截断HTML。每次body与receipt（URL/status/UTC/size/hash）保留。Nature转去idp cookie授权，未跟随；不称取得BATCHIE全文，仅保留旧摘要层结论。未花掉第8次额度。CellForge截断使全文完整性失败，不能隐去此限。

本地投影最初因maestro缺bs4两次失败，已换标准库HTMLParser；一次PowerShell内嵌日期正则命令有解析错误，未执行Python/网络/生物访问。详见 `WORK_AND_FAILURES.md`。主要来源段落和哈希在 `*_PROJECTION.json` 与 `SOURCE_DETAILS.json`；作者叙述结果只作来源暴露，非独立复现。
