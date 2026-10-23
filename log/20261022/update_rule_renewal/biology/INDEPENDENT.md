# 独立更新规律设计：功能保持的观测修订

2026-10-22。完整重读mandatory goal-objective及revision_value_operation/CONTINUATION，使用既有early_update、CiPA、PTPC、CellPhe审查报告，不读本阶段peer新稿；零HTTP、零原始数据/权重/保护响应读取。**一项可执行设计接受审查，但NO_QUALIFIED_CANDIDATE：字面操作有精确常规同操作对手，且关键生物观测合同尚未成立。** 不因learned optimizer家族身份否决，也不制造性能结果。

## 科学问题与唯一操作

将细胞状态观测的仪器/追踪修订错误地当作干预生物作用，会使一次功能反馈更新多个无关干预的效应。既有CellPhe一手审查已指出真实大细胞/分裂尝试与segmentation error的混淆，同时作者保留了“未排除重要亚群”的反证；它是有来源的问题结构，不是我们已证实的功能瓶颈。CiPA已观测control模式有信息但普通校准更强；因此仅添加校准头不足为新机制。

本次只考察一个小操作：**在已独立认证的观测nuisance变换下，约束功能反馈更新具有不变性**。设状态encoder给z，明确仪器/观察变化生成nuisance方向矩阵N；功能预测f_theta(z,a)，得到支持功能残差e=y−f。若局部adapter参数w以delta w改变未来预测，J_q为合法查询干预上的导数，则更新

    delta w = argmin_v ||J_s v−e||^2_R + lambda ||v||^2_P
              subject to C_N v=0 .

C_N行由“同一真实细胞状态、同一干预，只改变独立已知观察方式”下更新前后的预测改变量之差组成。约束的不是禁止细胞因药物改变，而是禁止功能反馈在已知等价观察之间引入不同修订。支持端只用已购买功能反馈；查询导数来自当前模型不是真实标签。P、R的低维或分块参数可在源任务按后续功能损失训练并继承；不要求正定P将分子梯度硬当功能梯度，支持梯度本身来自真实功能残差。

最小实现用8维adapter、少量nuisance contrasts，KKT解一次线性系统，不加编辑器、记忆库或搜索层。可继承对象仅为P/R及nuisance约束的构造规则；后续任务重置adapter与初始历史，不将更强incumbent算改进器继承。一次反馈后评未测功能/下一干预效用，不能以constraint满足率替代。

## 为什么可能节省有限数据，以及边界

如果真实响应修订落在ker(C_N)，去掉伪修订方向可降低少量功能标签下估计方差，且低维KKT比全模型重训便宜。若真实生物修订不在该空间，硬约束产生偏差，甚至阻止全部有用更新。因此优势要求**nuisance等价性外部认证**，不能用同结果相关或encoder相似性宣布方向不含生物信号。

CellPhe的人工事件修订并不自动提供这种等价对：不同tracking版本可能改变识别到的细胞/未来分裂标签；完整未来片段注释也不能在早时刻免费使用。CiPA不同site是真实培养与仪器混合，control共享不证明等价生物状态。当前没有本地已认证、可直接使用且非旧STOP重复的输入/功能/nuisance三方合同。此为该具体操作的观测缺口，不是要求先找完整RSI任务银行；也不提出新数据下载或sourcehunt。

## 最强具体普通对手与实质差异审查

必须给标准constrained generalized ridge/Gauss–Newton同J_s、C_N、P/R、起点和功能反馈；它求**完全相同KKT系统**。对线性adapter和固定N，等价也是reparameterize v=B u，其中B跨ker(C_N)，再做普通ridge/后验条件化。强对照还包括同等价对的数据增强直接预测、普通低秩adapter重训、固定/学习P与相同源任务训练的constrained metaoptimizer；不能只比无nuisance信息的模型。

因此“功能保持不变性”“继承P”或“低维求解”本身没有区别：同结构普通对手逐步完成相同操作，且享有相同计算量。约束如何由可认证生物观测构造若存在新的非平凡规则，可能成为具体贡献，但本稿尚未提供该规则；不能用“属于常规家族”泛化否定所有结构化optimizer，也不能把尚未指定构造器作为隐藏创新。

与旧梯度传送的差异是功能支持残差+观测等价约束，而非分子梯度SPD传送；然而这只改变标准问题输入，不足构成独特更新算子。它不涉及ALMANAC anchor平面、CDK prefix、蛋白增量、mass head、Lie bracket或DR，不授权这些STOP重跑。

## 最小否证与决定

无需新生物值即可先检字面公式：同输入KKT与nullspace参数化应一致；若一致，停止把此线性投影称新算法，不扩展toy积累通过数。本稿已给出代数理由，不要求root再重复旧投影式检查。若未来有实质新构造规则，必须预先给一个它与ordinary constrained optimizer不同的可执行步骤及有限资源优势预测，再考虑独立评审。

真实效用证伪应是：给定相同合法状态/功能反馈和成本，更新后的功能risk/下一干预utility未优于同结构ordinary对手；或外部等价对不能保持真实功能；或源学P在独立后续任务不如同信息普通optimizer。任一否定具体机制，不全称细胞状态无用。RSI另须新旧改进策略common-start效率，当前无此证据。

决定：**STOP_LITERAL_CONSTRAINED_UPDATE_CORE；NO_QUALIFIED_CANDIDATE。** 保留有条件的数据效率动机，但不启动新模型、来源资格或保护响应访问。完整世界模型/agent/继承/联合/improved-improver目标ACTIVE / NOT_ACHIEVED。
