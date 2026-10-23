# 单次功能反馈的传播瓶颈：teacher 不能自行改写右侧关联

2026-10-22。已完整读 mandatory goal-objective、update_rule_renewal/CONTINUATION.md 与 DECISION.md；未读本阶段 peer 新稿。零 HTTP、零新数据/权重/保护响应访问，未执行数值实验。此稿提供一个可解析检验的具体药物功能结构，不重启 CDK prefix、ALMANAC anchor、decryptE protein 或旧 STOP。完整目标 ACTIVE / NOT_ACHIEVED。

## 一个具体有用结构与精确失败条件

应用是新细胞背景的一次药物功能反馈后，预测另一未测药物的功能响应。设合法源任务支持下的残差结构为 y_j−mu_j=l_j z+epsilon_j：z 是新背景的一个共同敏感性因素，l_j 是从源背景学到的药物 loading。它可能对应两个化学不同的药物共享的下游脆弱性；此处只是明确生物假设，不宣称任何真实药物对已被认证。mu、l、噪声尺度必须从源任务/合法控制学习，不得由未测目标响应倒推。

在 l_s,l_q 非零时，一个标量反馈能提供 z 的信息。若 z 先验方差 1、epsilon_s 方差 sigma²，则普通一维 Gaussian/ridge 更新给未测残差预测 l_q*l_s/(l_s²+sigma²)*e_s。它不需要分子伪标签，也不需要药物结构相似。若实际有多个未知独立敏感性因素，一个标量只能约束 loading 对应的一条组合；没有源学关联就无法识别其余方向。teacher 不能凭 scalar residual 制造这些信息。

审查指定规则：u=Ak，h=tanh(u)，e=y−b^T h，r=tanh(P[k;u;b])，A+=eta_A*r*e*k^T，b+=eta_b*e*h。所有量使用更新前状态。对单个 support s 和任意 query q，严格有

    u_q_new = u_q + eta_A*r_s*e_s*(k_s^T k_q).

所以 P 控制的是左侧隐藏写入方向，不能改变右侧 support/query 关联。若 k_s^T k_q=0，无论 r/P 如何，该反馈对 query 的隐藏表示写入严格为零。完整预测仍可能通过 b 更新改善，不能称全模型不传播；但是同 A0、b0 的 frozen-A head-only 控制在该单次更新后对 q 给出完全相同的预测。此 episode 的 query 损失关于 P 的梯度也为零，因 b 更新和 query hidden 均不依赖 P。该结论不要求 A0=0。

最干净见证是两个正交 one-hot 药物 key、A0=0、非零 b0，真实残差为共同 z，l_s=l_q=1、噪声为零。此时 h_s=h_q=0，b 通路也关闭，teacher 的 query 预测始终 0；普通一维 residual ridge 在 lambda=0 时给 e_s。该见证证明具体表示/初始化合同下的机制盲点，不证明源训练一定会选 A0=0、不证明所有药物 embedding 正交、更不证明整个 teacher 无经验价值。

## k 的来源决定什么能被归因给 teacher

化学结构 encoder 的相似性不是共同功能敏感性的认证：结构不同可共享下游作用，结构相近可受选择性/暴露差异影响。包含细胞状态的 key 也可能让细胞背景项支配内积，使所有药物互相传播而并非正确 target-specific 关系。若 k 经源功能 query 训练而学出 l_j 型关联，结构瓶颈可能解除；此时必须把同一 k 及其源训练成本给直接预测、head-only 和普通 residual ridge 控制，分离 k 的收益与 P 的收益。

若更新或重新学习 k 本身，公式的固定 key 假设改变，需明确其步骤和成本。多次 support 更新也可能通过被修改的 support h 影响后续 b，不能把单次相等结论外推成任意序列相等。这里选择单次反馈，是为了只检验当前写入算子的必要作用，而非另造完整任务银行。

## 唯一最小机制检验与最强普通对手

只预注册上述两药、一个 latent z、一次反馈的解析诊断；不拟合新 biological table。对齐两个条件：同一已知 l、mu、同一反馈/噪声、同一模型起点，改变 key 的 support/query 内积从 0 到非零，并报告 hidden 写入、head 通路及 query 误差，不能只报总误差。零内积处 teacher 与 head-only 完全相等为精确预测；源学 query teacher 若声称独立于 k 可恢复隐藏传播，该点即证伪。若实际目标中 key 已有可靠内积关联，此诊断不构成真实任务停止理由。

最强同信息 ordinary 对手是源学残差 covariance 的 ridge/线性 Gaussian 更新，使用相同 source episodes 得到 l 与噪声，并计入这项训练；在此 rank-one 结构下是一维 solve，不给全局 oracle。若候选采用一个 source-learned right-side metric M，写为 A+=eta*r*e*(M k_s)^T，则 q 传播由 k_s^T M^T k_q 控制，可能解除零内积盲点，但这正是普通 learned-kernel/residual covariance 的可用结构。本稿不把添加 M 当新机制，也不额外提第二候选。完整 teacher 对照还必须包括同信息 query-trained learned optimizer，不能用 true-gradient-supervised teacher 作为唯一弱对手。

此诊断只有机制可达性价值，没有生物性能结论，也不决定 query-only outer objective 的文献新颖性。即便 teacher 胜过 sample SGD，若 source-learned residual ridge/head-only 在相同信息与成本下解释收益，不能声称虚拟细胞/智能体/RSI 必要。

## 单位、顺序与真实反馈合同

相同药物必须固定剂量、暴露时长、assay 定义及背景状态；平行培养的独立终点可用于静态任务 replay，但不能当作同一培养的 sequential treatment counterfactual。support 结果必须是真实被允许揭示的测量，query 的误差只在源任务外训可见，目标任务不可拿未测 query 选步长或归一化。生存率、抑制率和原始信号的方向/零点不能默默混用。

该 tanh teacher 也非天然量纲等变。若合法换单位 y'=c y、b'=c b，保持 hidden 表示应要求 A 的修订不变；即使 r 不变，e'=c e 也使 hidden 步乘 c，需要相应 eta_A 调整。实际 r 输入 b，r 还会改变；单纯改 eta_A 不一定修复。加性单位偏移需合法 baseline/intercept，否则连残差对应也不成立。源固定或合法 control 归一化可处理，但目标 query 的均值/方差不能免费使用。不宣称这些一般缺陷足以否定经验能力。

单次支持没有排列问题；多反馈的 tanh 写入和 b 更新通常不交换，若实验只是无时间含义的平行 assay 集合，任意处理顺序造成的功能决策变化是应审计的程序依赖，不是生物时序学习。固定顺序或源随机顺序训练也须给所有普通对手。该问题不另开 order toy。

## 决策

HYPOTHESIS：真实未测药物是否具有源可学的共同功能 residual 结构尚无本轮新证据。VERIFIED_ANALYTIC：固定 key、单 feedback、正交 query 下 hidden 写入不可达，teacher 与同起点 head-only 的 query 输出相同；这是代数结论，未伪称数值或生物实验。

REVISE_SCOPE / NO_PROMOTION：完整 query-trained teacher 创新仍未决；若后续主张只有任意 tanh 左侧 teacher，它没有解决这里的右侧关联问题。若真实任务 key 与源学共享功能结构已充分对齐，仍须证明 P 在有限预算下超出 head-only/同信息普通更新的独立收益。没有新可区分算子在本稿诞生，不启动数据搜寻或大 pilot，也不拿局部停止代替完整研究目标。
