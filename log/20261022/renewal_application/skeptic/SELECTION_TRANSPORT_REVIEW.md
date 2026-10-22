# 构造审计的科学解释与最小额外反馈

2026-10-22。手写反例，不是生物实验、拟合结果、新算法或新定理。预先协议/代码/tests 在 SELECTION_TRANSPORT_FREEZE.json；三项测试 PASS，一次 main exit0，六项预定 check PASS。HTTP=0，真实生物数值读取=0，fit=0。旧已冻结阶段不改。

## 两个可实现生成过程

两者初始均为 A/B 各200个 founder，每个 founder 只不分裂存活、分裂一次或死亡。

| 过程 | A-origin founder 结果 | B-origin founder 结果 |
|---|---|---|
| S：无状态改变 | 198存活A，2死亡 | 198存活B，2分裂，各产生2个B |
| T：有状态改变 | 198存活A，1分裂产生2个B，1死亡 | 198存活B，1分裂产生2个B，1死亡 |

理想 reporter 完全准确且无噪声。两个过程最终都产生 A/gen0=198、A/gen1=0、B/gen0=198、B/gen1=4；总细胞400、cycling tail 1%、两个分裂事件和两个死亡。因此二者的最终 RNA-state 分布、理想 H2B division-history 联合分布、绝对总量及这些 aggregate event counts 都完全一样；A-origin→late-B 分别是0与2。

**字段术语纠正：** code 的 `birth_events_total=Σfounders×(descendants−1)` 是二分裂导致的净新增细胞数；在本模型等于分裂事件数2。若把 birth 定义为 daughter-cell births，则每模型都是4。支持方独立复算提出该命名歧义，已接受，冻结 code/result 保留原字段不改。等价性不受约定影响。

普通两状态条件表即可复现 endpoint likelihood：`P(B)=101/200`，`P(cycling|A)=0`，`P(cycling|B)=2/101`。这是一种饱和 static 表，使用 endpoint 估计同一 endpoint，**不是**未见药物、早期预测或小反馈条件下的性能胜利。不能据此断言 world 没有有限样本/分布外预测价值。

## 反例证明什么、没有证明什么

它是对“有总量和末端增殖 reporter 就自动识别 selection vs state change”的反例。它不证明所有 source、完整 barcode lineage 或其他 origin-resolved feedback 都不可识别。加入额外可观测约束可以排除其中一个过程。它也不要求在开展 survivor-conditional cycling 预测前解出真实 transport。

当前模型的“状态改变”仅指 A-origin 后代落入观测 B；不等于证明药物诱导、不可逆记忆或某个分子因果调控。即使观测到 A→B，普通 spontaneous switching、测量误分与 reporter calibration 仍是替代解释，drug-induced 主张需要相应对照与假设。

## 最少额外反馈的正确表述

对**这对已指定的模型**，一个精确的 `A-origin→late-B` 联合计数即可区分0与2；甚至 origin-A 后代总数198与200也不同。这不是任意系统只需一个标量的识别定理，更不保证在有限 noisy sampling 下能检测两细胞之差。

可执行的测量形态是：在治疗前把明确的初态身份与可追踪 founder/branch 绑定，然后在末端读状态与功能，例如校准的 live reporter+heritable label，或 initial-sort+独立 tag。应把 sort 诱发变化、标签误分、回收率、分支丢失与未知 mass 纳入合同。无需执着于某一特定技术或真实连续全转录轨迹。

clone barcode 若只说明共同祖先，而 clone 内已有多个早期状态，早 RNA 与晚 gate 的 clone 内边缘并不自动给出 individual founder 的 origin→destination joint。相反，若源数据已经提供足够纯的、校准的 initial-state lineage mapping，它可能就是上述额外反馈；不能未查 schema 就宣布它无效。

## 对当前 Watermelon pilot 的含义

本文没有读取 expression、clone_size 或功能结局。原始文章和当前审查都允许一个较窄的、设计条件下的 cycling-gate 预测任务，使用确实释放的早期/lineage信息比较强同信息 classifiers、hierarchical/mixture models 与显式 state 模型。

若 day14 数据按 cycling/mid/noncycling strata 分别测序，而 per-replicate sampling weights 未认证，仍可明确做 released sorting-design 条件下的 discrimination；不能把该设计中的 class fraction、未经目标 prevalence 校准的 Brier/AUPRC 当总体 survivor risk。论文已有 stratified correction 的事实应保留，未认证当前权重不等于论文无权重。绝对 reservoir mass 又需要相应 denominator，比例与总量不能混淆。

因此，合理下一步是认证具体身份/动作/采样口径并界定预测 gate；不是因未能识别 transport 就全面 STOP，也不是因为有 barcode 就宣布新动态因果机制。root 已实际接受这一缩窄。多任务/agent/继承/C4 是否有足够真实机会仍须另定义，不能把每个 cell 或同一 pooled assay 中的 clone 当廉价独立实验。
