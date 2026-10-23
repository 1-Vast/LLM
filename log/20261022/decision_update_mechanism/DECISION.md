# 决策：确认任务内改进经验生成的直接先例，未找到合格迁移机制

2026-10-22。完整目标 ACTIVE / NOT_ACHIEVED。上一轮是PROGRESS；本轮也是有界文献/操作层面的PROGRESS，新增两份最新一手全文、直接API提案及对训练目标与信息合同的独立审查。没有新的药物性能、继承或RSI实验结果。

## 新证据改变了什么

**ReTTT2610.23942v1**有非常接近当前RSI问题的实质操作：由当前适应模型生成并修订后续程序经验，再把经验写入共享LoRA，继续行动和反思。原文Frozen Reflection对照仍允许action适应，作者报告56.43%→63.57%，增量7.14个百分点。应保留这项任务内改进经验生成的正面证据，不能因使用常规fine-tuning或只在episode内就抹去。

但adapter/optimizer/memory每episode清空，原文Cross-episode persistence=None，跨episode整合属未来工作。尚不满足本项目要求的独立后续任务继承，也不是从共同base updater出发衡量新旧编辑器产生有效后代的效率。该源的总worker runtime约为aTTT的1.085倍，而非更低；这不是相对Frozen Reflection的匹配成本证明。全部数值为作者结果，本项目未复现，不是细胞功能证据。

**SelectTTRL2610.16104v1**以校准集correct/incorrect隐藏表示均差构造方向，按COS选择固定25–60%分位问题，再跑原TTRL。Theorem4.5针对当前正确性关联，不是训练前后净utility。它给出了具体省采样的选择先例，但不能靠把“问题”换“药物实验”证明有益更新。保留35%样本不等于端到端省65%成本。

## 三种被具体审查而未晋升的操作

1. 固定共同初始模型/反馈下，以更新后动作效用减旧动作效用训练更新器，等于已发表SPO loss作用于组合updater/predictor后再减常数。停止目标差异本身的新颖性；不宣称完整有限训练算法等价。hard topK需说明离散优化/随机估计/替代损失及其成本，baseline可能改变近似优化方差。
2. 在两种药物关联结构间依反馈更新权重，具体等于普通有限Bayesian model averaging，暂无新结构构造/统计或成本性质。相同support似然不能区分相反query最优动作，生物解释未经认证。
3. ReTTT显式替换lesson未保证删除旧LoRA影响，这是真实语义区别，但不是原文承诺失败。完整checkpoint+optimizer suffix replay、凸充分统计downdate都是具体有限对手；当前没有给出更便宜又能保证后续功能决策的非线性修订操作，也没有合格的真实测量更正流。因此不把缺口描述当新算法。

## API提案与是否实验

一次真实调用，模型receipt为deepseek-flash，1908reported tokens，9.0秒，finish stop。输出自行NO_CANDIDATE，但给出pairmean锚点support-span传播的fallback。其假定可观察的pairmean并非旧预算的一条高高角测量，跨pair pooling违反旧合同；若另购买完整曲面将是新预算/任务，不能暗中改约。55%/69%误差收益占比不是存在该可观测生物锚点的证据。用旧开发最大swap7或任意5新cell作通过/失败门没有依据，不能据此开保护cell。

**NOT_RUN / REJECT_UNQUALIFIED_TEST_CONTRACT**，不是性能FAILED。不会执行该fallback、生成代码或重复旧anchor纠偏实验。没有合格新操作时，也不再运行target重写、DR识别或记忆删除的一般toy来代替生物研究。

## 去留

**NO_CANDIDATE / NO_PROMOTION**。保留普通反馈的真实功能能力、ReTTT的任务内改进生成经验先例，保持原创机制、继承能力、递归能力三个维度分开。当前未解决的是具有真实可得反馈合同的特殊更新机制及有限成本优势；不能以更多teacher/editor或新benchmark填补。

下一候选须明确：合法可见什么功能证据；它怎样改变更新/改进程序；与上述已发表具体操作相比新增什么；在独立未来药物任务以什么同信息强对手与成功/停止条件检验。需要世界模型/agent/继承/联合及改进策略自身收益的全套验证仍未完成。所有旧STOP和保护响应维持，src/tools不改。

资源：两HTTP200一手正文，零数据/权重下载或新生物数值访问；一API逻辑请求，transportattempts/费用不可见不估造；native计费不可见。无新模型训练、数值toy或湿实验。独立初稿后实际往返交叉与root源核读，所有记录log/、代码research/。局部hash不修复历史全局provenance漂移。
