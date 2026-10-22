# 独立方法反方：功能动力学与后继纠错的最小增量

2026-10-22。在阅读支持方稿件或本轮 DeepSeek 输出之前形成。根代理在本轮只告知一个操作梗概：birth/death 局部 innovations 后继承 repair ψ；下文不假称对此梗概盲法。复用既有历史阴性和 RSI 文献审计，新增六次有界 GET，未下载任何原始生物响应文件、未检查其响应值、未拟合模型或调用模型 API。公开论文叙述中的作者结果已暴露，不能作为未来封存确认。本稿是方法/来源资格判断，不是性能实验。

**建议：保留 BESTDR 真实计数资产与局部失配修复的开发资格；尚无可批准为新 RSI 核心的独有操作。** 不能以“同信息直接预测器能表示所有函数”否决动力学归纳偏置，也不能因一个直接预测器不胜常数就断言无可利用信息。真正要问的是哪一项具体操作，在同信息、同预算下，比强直接预测、既有分支过程后验更新、常规模型扩展和等预算搜索改善了未参与修复的实测功能。

## 一手主 lead：BESTDR 已经做了什么

**BESTDR Enables Bayesian Quantification of Mechanism-Specific Drug Responses**，Cancer Research，2026，DOI [10.1158/0008-5472.CAN-25-1181](https://doi.org/10.1158/0008-5472.CAN-25-1181)，[PMC13055639](https://pmc.ncbi.nlm.nih.gov/articles/PMC13055639/)。本轮读完整原始 XML 的方法、相关结果及讨论；结果是作者报告，未复现。

其操作不是普通静态 IC50：

1. 细胞以连续时间多类型 Markov 分支过程分裂、死亡、转换状态；速率随药物浓度变化。由过程得到条件均值和协方差，使用大初始群体下的多元正态近似似然。
2. 每条相邻观测用上一时刻各状态计数、间隔及浓度构造条件似然。分解依赖 Markov 与时间齐次假设，不能把“相邻间隔成为似然因子”误称增加了独立生物实验。
3. 计数方差提供均值净增长之外的约束，以估计分裂率与死亡率；另设测量误差项。速率的浓度响应可用四参数 logistic，也展示 GP、B-spline 和双头神经网络，不能只用弱 logistic 作为“既有方法”。HMC/Stan 估计后验。
4. 已有 live/dead 两类、dead-cell clearance、多状态 cell-cycle/reprogramming 及跨 cell-line 层级参数共享。以“引入死亡、状态转换、共享速率先验”本身为新贡献不成立。
5. 作者在独立的谱系追踪与群体计数实验间比较分裂/死亡时间尺度。这支持实际功能相关性，但不是所有潜在速率均被无假设识别，也不是本项目未见任务预测结果。

关键可测限制：模型的时间齐次/指数等待假设与早期同步、药效延迟有冲突。HCT116 数据分析截掉前20小时，高浓度 CR 分析从24小时后开始；讨论明确承认细胞周期非指数等待、低计数的近似误差，以及观测噪声可能被误归为过程变异并抬高速率。线性链扩展和常规模型选择已被作者提出。因此“自动找到延迟/选更合适动力学类”需要击败这些具体扩展，并不是无人处理的空白。

## 一个足够具体的普通更新归约

将文中条件模型写为：

    x_next | x_now,c,Δ,θ ~ Normal(mθ(x_now,c,Δ), Vθ(x_now,c,Δ)+R),
    e = x_next - mθ,   r = (Vθ+R)^(-1/2)e.

这是本审查对文中方法的形式化，不声称作者新增了名为 innovation 的算法。用 r 定位失配并重估 birth/death/clearance 参数，就是同一条件似然的后验更新/系统辨识。若候选的修复恰好为线性化加权残差写回：

    Δθ = (J'WJ + Λ)^(-1) J'W e,

则在同一线性化、先验/正则与 W 下，普通 Gauss–Newton/MAP 或 Kalman 型更新可给出同一步；给它新名称不产生技术差异。若 ψ 实际改变可更新对象、模型类、动作或计算顺序，并不自动落入这个精确归约；应列出实际操作，测量改变的预测/行为及成本，不能仅凭“是元学习”否决。

特别不能从仅有 live-count 均值残差唯一判断 birth 错还是 death 错：均值主要约束二者差。BESTDR 利用过程方差增加信息，但当测量误差、群体依赖或动态失配未校准时，方差不能被无条件当作 birth+death 的真值。加入 live/dead 计数和 clearance 会改变可辨识性；应以具体观测模型、噪声和重复结构判断，不能泛称计数必然无法识别。

## 同信息直接预测必须怎样比较

直接功能预测器必须得到相同的时间/浓度、当前 live/dead/state 计数、完整合法早期历史、cell-line/context 及相同辅助监督；不能让世界模型看到实际前缀和 dead-cell readout，却让 direct 只看药物结构或初始 RNA。保留末值/局部指数增长、regularized history regression、强非线性 prefix forecast、层级多输出模型和同容量直接头；late fusion/简单混合接收相同信息。

动力学模型则应包括 BESTDR 类随机 birth/death/state-transition、测量误差、dead clearance、层级共享，以及开发预算内预先列明的 time-inhomogeneous/阶段型/线性链扩展。参数重估、普通 refit/pooling、CL 与主动学习分别保留。所有前处理只用允许的前缀/训练资料；作者用全轨迹确定的20h截断或药效时间可作为共享已暴露先验，不能只赠予候选，也不能在新任务看未来后重新挑截断。

世界模型的可争取收益是可检验的有限样本归纳偏置、跨时间/动作预测、经实测裁决的速率解释或真实决策收益；不是“输出多条模拟轨迹”本身。现有 HCT116 恒定给药计数可支持前缀到后期 live/dead 读数预测；不自动认证换药、washout、恢复、未测组合等操作。无需为了所有预测都要求完整谱系树。

## ψ 的一手近邻：SpecRSI 的实际操作

新读 [SpecRSI, arXiv:2610.16491v1](https://arxiv.org/html/2610.16491v1)，2026-10-12。方法 §3.2–3.4，附录 D、F.5 及相关正文已保留投影。其具体近邻是：

- 内层冻结 improver，允许从未完成验证的程序草拟后继，按未来可验证收益和剩余成本选择 edit/check。VATS 的工作单元包括验证组合，预测不能代替真实证据。
- 外层 GVO 对相同根程序、预算和快照下的独立完整搜索分配信用。只有已完成可采纳改进计收益，失败和未完成搜索仍计成本；更新 drafter 与 work-selection policy。
- continuation scorer 用实际 suffix return 回归，另以同一已付费状态的真实后继分支比较训练差值；分支成本收费。策略变化后重新收集以校准，论文明确不保证逐编辑因果归因或单调改进。
- reset/carry 及同 released-artifact fork 区分保留更强任务程序与更新 improver。共同起点评价本身不是我们的新算法。论文的 contract 和外层更新规则保持固定；可学习的 proposer/scorer/policy 已很具体。

所以“学习 residual→repair 选择”“记住成功失败”“按后继收益更新改进器”“新旧 ψ 在相同 θ/p 起点比较”均不能单独成立新颖性。历史 Hyperagents 的任务/meta程序可编辑、AIDE² 的科研程序改写与迁移、MetaShare 的失败/成功 signed-delta 检索沿用已有审计；本轮未重读这些全文，不夸大摘要层证据。

真正仍未被这两个主方法直接解决的最小问题可以写成：**相同诊断信息下，在新药物功能预测发生失配时，一个可移植的修复操作如何把有限实测证据用于正确的更新对象/模型结构，并使后续纠错比相同信息的后验重估、固定诊断策略和 generic search 更有效？** 这是待提出的算法缺口，不是已存在的新操作。生物相关的结构化信用或不变性可能有用，但必须给出式子/可执行变换及能反驳它的测量，不能用固定评价协议充当该变换。

最少归约挑战：固定同一 θ、历史、候选修复指令集和评价反馈，比 ψ 与 (i) 全参数 Bayesian/refit，(ii) score/Fisher/sensitivity 选择坐标或模型类，(iii) 同数据训练的 contextual bandit/learned optimizer，(iv) SpecRSI 类完整搜索收益 scorer/policy，(v) 相同提案与评价次数 random/BO/program search。若所有增益由适当速率先验、额外 dead counts、普通模型扩展或更多搜索解释，应按实际来源报告，而不是宣布新 RSI。

后继效率需要冻结 ψ0/ψ1，在共同模型/程序起点上给同数修复与真实反馈，用更后新任务的未参与更新功能裁决。继承速率先验、继承 repair 程序、继承更新 repair 的策略是不同对象。若要主张策略本身进一步变得更会改进，必须再检验后续策略改进效率；仅 θ 更准或 ψ1 首次优于 ψ0 不能支持无限递归加速。上述是必要归因要求，单独不作为算法贡献。

## 真实数据与代码可以具体取得

新读取 figshare 元数据 [29610530v1](https://api.figshare.com/v2/articles/29610530)，标题 HCT116 with Cisplatin Experiments，2025-07-21，CC BY4.0；描述明确 viable/dead counts，0/12.5µM重复及浓度范围实验。**只读清单，无响应文件下载**：

| 原文件 | 大小 | 原始下载指针 / MD5 |
| --- | ---: | --- |
| HCT116_Cisplatin_Replicates.csv | 295392 B | `https://ndownloader.figshare.com/files/56428388`；`ae55aacf1f6549b04471f9d9d68e6cfe` |
| HCT116_Cisplatin_DoseResponse.csv | 392663 B | `https://ndownloader.figshare.com/files/56428391`；`010489434a9e563f4f23afa304c70aca` |

这些是具体小资产，值得根代理另行冻结后下载、审计表头/身份并做实测资格。当前尚未认证 CSV 中 run/well/state/control 键、起始计数、缺失规则及真实独立重复，不把文件名 Replicates 当生物复现。论文 HTS 指针正文为 Zenodo18292966，availability 为18292967；这里只保留两者，不擅自修复其关系。HTS 数据为每条件两个技术重复，cell-cycle 数据为三个技术重复；不能当跨生物实验的 RSI 机会。

原始代码 [olliemcdonald/bestdr](https://github.com/olliemcdonald/bestdr) 的完整 Git tree 已认证，根 SHA `03753e15c789bee671ff39dfe8c6cbc50e5967e5`，`truncated=false`。本轮未读/执行代码正文；方法判断来自论文。可供后续定向读取的真实路径包括：

- `R/attach_data.R`，2952 B，blob `c5ab7381a72f3a7e105e50548bf73e7814dcbf4d`。
- `inst/model_library/1type-livecell/logistic/birthdeath_error.stan`，3897 B，blob `16edbf5b370ddcc9ffeb02c4dc8bcca3644e1c53`。
- `inst/model_library/1type-livecell/gaussianprocess/birthdeath_error.stan`，3193 B，blob `499b8e0873b5ba31133be5aa83aabf4e901b494c`。
- 多状态、live/dead、mixed-effects 路径见 `BESTDR_CODE_PATHS.json`，不能只测试最弱单率版本。

## 成功、停止与资源身份

本来源 gate 成功仅指认证具体功能轨迹、同信息比较及足够独立纠错单位。若有 authentic prefix→later counts 且无跨 run，可保留窄预测开发，停止独立-run/继承/RSI确认，不停止所有预测。若信息/噪声不足以区分修复对象，只能预测或按观测等价类选修复；不能把 latent rate 叙述当已测机制标签。

后续性能阈值必须在读取响应前按具体功能与成本冻结。本轮不凭空规定 δ 或 power。候选若精确归约普通更新，停止“新操作”主张；若强常规方法在实际任务/预算匹配净收益，停止候选独有效果主张；数据不够则记录 inconclusive/not-testable，而非生物阴性。弱基线失败不提供无 headroom 的证明。世界、agent、权重/程序继承、联合及 RSI 收益当前全部 **NOT_TESTED**。

资源：六 GET、全部 HTTP200、保留正文共 **1,359,053 B**，无 retry/redirect，单响应≤3MiB，timeout25s；每请求 receipt/body/SHA256/UTC 均留本目录。第一轮按时间排序的广查询过宽，第二轮锁 TITLE_ABS 得到 BESTDR；不是无限综述。离线投影初次因 maestro 无 bs4 失败，已改标准库 HTMLParser 后成功，不安装依赖。原数据 payload0，DeepSeek0，模型拟合0，生物实验0。检索是有限近邻审查，不保证穷尽新颖性；取得数据清单不等于取得新算法或总目标完成。
