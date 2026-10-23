# 决策：功能误差确有改善，但不等于选择边界风险改善

2026-10-22。完整目标 ACTIVE / NOT_ACHIEVED。本轮 PROGRESS：完成此前未做的冻结预测精确分解及top89交换核算；没有训练新模型或建立新核心机制。

## 实际结果

唯一脚本 decompose.py 在maestro执行exit0。两套固定比较、全部10cell的MSE三项分解和top89交换恒等式均与历史保存指标在绝对1e-12内一致。输入与程序在计算前保存hash。RESULT包含完整逐cell三项与swap集合，不从中筛子组。

主all-source：MSE .0094443827034→.0084953821375，regret .0086369803371→.0077671488764。净MSE收益 .0009490005660，其中global-mean .0000246726376、centered-pairmean .0005263076517、withinpair-dose .0003980202767。分别约3%、55%、42%；centered-pairmean和withinpair-dose项都在10/10cell改善。

study-exclusion敏感性：MSE .0100466786860→.0094438056521，regret .0096032022472→.0097194522472。净MSE收益 .0006028730338，其中global-mean .0000209438373、centered-pairmean .0004131592568、withinpair-dose .0001687699398。分别约3.5%、68.5%、28%；centered-pairmean仍10/10cell改善，而regret仅4/10cell改善。

每cell B1与B0的top89集合只交换1–7个成员（主分析）或1–6个成员（敏感性）。swap真值总差/89精确复现regret变化；它只是冻结选择结果的账本，不是用query真值决定下一步动作的策略。

## 改变了什么判断

**排除一个过强解释**：不能说功能MSE收益主要只是cell共同offset校准，或仅是对pairmean决策无作用的曲面形状修复。两套比较最大净收益都来自centered pairmean误差，且逐cell一致改善。

**定位一个真实有限缺口**：即使10/10cell的pairmean平方误差改善，top89选择仍可在敏感性分析6/10cell恶化。全目录平均平方误差与少数选择集合交换的效用不是同一目标。此证据没有证明某种新更新器能预测并修复这些交换，也没有识别其来自assay校准、生物相互作用或共享study。

**纠正措辞**：此前笼统的“MSE改善但ranking恶化”应限定为study-exclusion敏感性；主分析两者都改善。不能混用不同配置的指标。

## 科学决策

VERIFIED_LOCAL：上述固定预测算术分解、交换身份与保存指标一致。SUPPORTED_EXPLORATORY：普通反馈包含pairmean预测收益，但该收益未稳定改善固定top89决策。NO_NEW_MECHANISM / NO_PROMOTION：不能把centering、ranking loss、swap账本或边界门控换名当原创贡献。

维持STOP_CURRENT_ANCHOR_TRANSPORT_NOVELTY_AND_RSI_EXPANSION。不拟合新corrector、不开reserve、不根据这个已暴露开发集挑交换门、top-k或阈值。真正的新方案须针对功能反馈为何能在合法可见信息中预测决策交换的价值，给出与普通decision-focused learning/主动学习/残差预测不同的具体操作及有限统计/成本优势，并在独立任务上证伪。

世界模型、智能体、能力继承、联合与改进策略改进收益均未建立。无需增加teacher/editor层级。本阶段是一次真实误差定位，不能冒充算法性能实验或RSI。

## 范围与资源

仅使用已经暴露的first40缓存中开发10cell与四套保存预测；NPZ y成员物化已暴露40cell后切片。未读原始CSV、未访问任何保护响应。零fit、零网络请求、零DeepSeek调用、零新湿实验。三native角色独立检查旧记录，随后做实际交叉质询与静态结果审查；他们没有独立重跑数值分析。HEAD47a0e2dea5a7dd42379fa17eb3621caf6bd0114c；历史provenance漂移仍未被局部hash修复。
