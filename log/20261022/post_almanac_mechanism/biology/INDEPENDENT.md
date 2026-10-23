# 独立生物问题与机制机会审查

2026-10-22。**NO_CANDIDATE：本次不提交可晋升的新更新机制。** 保留一个明确的功能瓶颈及新的可核事实，而不再检索泛数据源、追加锚点传播菜单或将普通误差校正换名。

## 已阅读范围与历史约束

已完整读取workspace外用户goal-objective.md（45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9附件），本轮ALMANAC DECISION/CONTINUATION，以及next_mechanism OBJECTIVE_STATUS、mechanism_gap CONTINUATION、operator_renewal CONTINUATION、repair_information_opportunity CONTINUATION。没有读取本阶段其他代理意见，没有生物响应或reserve访问，没有修改旧bound文件。

完整目标要求药物发现、虚拟细胞、agent各有实质贡献；RSI须比较更新前后改进策略在新任务上的改进效率，不能由普通适应或保存经验代替。现有强证据是ALMANAC强直接RBF加入反馈提高面MSE，但study排除后的排序变差；decryptE蛋白增量未通过；当前anchor传输创新扩张STOP。标记流/质量守恒、单锚点moment、continuation table、CDK简单混合、旧repair菜单等停止边界不因本次新论文元数据而撤销。

## 一个真实功能问题：状态分布正确不等于存活排序正确

问题是药物干预后**剩余多少细胞**与**存活细胞处于什么状态**必须分开。药物发现需要按净杀伤/生长抑制排序；仅对存活且被测到的细胞转录分布生成逼真样本，不能自动提供这个排序。ALMANAC已显示预测MSE与排序收益可分离，但本报告不宣称ALMANAC排序失败已由“质量缺失”因果解释；ALMANAC本身提供功能增长端点。

本次新事实来自2025–2026一手作者来源，而非又一数据集目录：

1. State已不只是2025预印本。EuropePMC精确标题元数据认证2026-08-31的Cell论文：*Predicting cellular responses to perturbation across diverse contexts with State*, DOI **10.1016/j.cell.2026.07.052**，PMID42673963；2025预印本DOI10.1101/2025.06.26.661135。作者摘要将主要成果表述为细胞集合扰动预测、效应辨别与DEG改善，167M观察细胞embedding。不能将这些作者结果当成我们已复现的功能收益。
2. 作者State官方README明确提供 `downsample_cells`，按 `(cell_type, perturbation[, batch])` group封顶加载细胞数；同时预处理normalize counts、log1p/HVG。**因此至少在启用该选项的合法训练流程中，进入模型的组细胞数由计算预算截断，不能直接作为实验存活总量。** 这是具体数据合同限制，不是臆测该论文所有分析都丢失存活信息。预印本摘要提及cell survival并不足以认证实际总细胞/绝对存活标签；发表摘要反而不作这个具体表述。
3. CellFlow作者2025预印本DOI **10.1101/2025.04.11.648220**，标题 *CellFlow enables generative single-cell phenotype modeling with flow matching*；官方README明确包括组合药物、morphogen和类器官protocol的条件phenotype生成。故“跨条件生成细胞分布/组合干预”本身已有直接先例，不构成新机制。该README不能认证其全部数学目标、是否含unbalanced质量建模或具体功能验证，本次未读全文，不作更强断言。

## 信息约束与最简单对手

若观测合同只给归一化存活细胞分布p(x|alive,a)，它不确定总存活量m(a)。两个干预可有相同p、但m相差百倍；重采样固定K个细胞后这两个世界给同一输入。这个经典归一化信息损失不是我们的创新定理；它说明不能仅加agent或更大分布生成器就声称恢复杀伤。

若已有合法绝对计数、spike-in或已校准捕获率，则最强简单对手是独立mass head/count likelihood加条件状态分布模型、标准选择模型/联合似然，而非刻意弱化的只有分布预测器。将mass和state拆开、用总量校准分布，或由agent选择计数实验，都已有标准统计表达。此前operator_renewal的一锚点moment路线已有明确测量合同与停止限制；本次没有新观测和新算子，所以不将该路线换名重启。

潜在可复用更新操作必须实质超出“得到新计数后重拟合count head/选择模型”。本次没有找到一个具体、简单且不同于普通联合回归、unbalanced transport或标准系统辨识的操作；也没有新的可获得真实计数反馈面板认证。更没有证据说明agent或继承改进策略必要。因此不提“mass-aware virtual cell RSI”候选。

## 可证伪边界与决定

若未来有人主张从固定采样细胞集合即可学到独立绝对存活排序，应首先核对可见字段与采样过程；在相同合法信息下比较强直接功能预测/标准count+state联合模型。若唯一新能力来自额外绝对测量，对手须获得同一测量；不能将信息优势算世界模型/agent贡献。若根本无绝对功能标签，则先明确任务只预测条件状态，不凭基因生存代理声称实测杀伤。

本次STOP的是尚无新机制的这项概念机会，不是断言State/CellFlow无用、没有任何功能证据或所有single-cell数据都不可用；也不延长为新来源资格流程。无需实施、下载响应或打开任何已有reserve。完整目标ACTIVE / NOT_ACHIEVED，等待另一独立立场有无实质不同候选，再实际交叉。

## 来源与实际成本

仅4次HTTP请求，全部200：两次EuropePMC metadata查询（TITLE:CellFlow；2025–2026精确Predicting cellular responses标题范围），两次官方GitHub raw README。Cellflow标题查询同时返回无关2026病理图像增强同名论文，已明确排除，不能混淆为单细胞CellFlow更新发表。原body、URL、UTC、status、bytes、SHA256和摘要均在本目录sources。无论文全文获取声明、无新数据下载、无DeepSeek调用、无新模型训练。代码只在research/post_almanac_biology_20261022/literature.py。
