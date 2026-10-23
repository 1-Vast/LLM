# 真实交叉质疑与修订后决定

2026-10-23。constructive/PREFLIGHT.md先写完，再读取critic/PREFLIGHT.md；双方通过collaboration消息实际提问与回复。本报告不把交叉后的共同判断倒填为独立原稿。

critic质疑：相关差即使重复，也可能完全由组内响应方差、噪声或量程变化造成，条件回归斜率不变。因此能否称全局affine predictor发生错误/过量loss？

constructive回复：不能。一个纯手算反例为两组均满足Yq=Ys+epsilon，独立epsilon方差1，Ys方差分别1/4与4。两组真实条件均值同为Ys、斜率同为1，但相关分别1/sqrt(5)与2/sqrt(5)。若两半各有同样结构，contrast乘积为1/5，远大于.01，而正确共享条件均值仍无需改变。本例没有运行模拟、没有声称是生物现象；它说明本诊断只能为条件关联调查提供依据，不能直接证明预测器结构错误。该回复已实际发critic。

constructive质疑：固定median与eligible bootstrap非校准alpha检验，是否应完全取消门，还是允许作为事前资源screen？

critic实际回复：允许预承诺的conditional exploratory screen，但必须明确不涵盖median估计、历史设计与eligibility不确定性，也不能称校准alpha或完整学习程序区间。双方保留这种有限解释，未用投票证明统计有效性。

双方均确认数值constant<=1e-12分配0不删除pair，所以不是暗中结果驱动筛选；它仍是数值估计器的一部分。critic提出后续按pair直接中心化重算，避免raw second-moment cancellation被忽略；我同意。未因此提前看生物结果或调整容差。

## 修订核对及最终GO

收到根的修订通知后，实际重读协议相关条目及run新增代码，确认：

- discovery/replication/both的r_low*r_high<0计数已分别加入，zero不算反转；T与原GO门未改。
- 数值constant阈值及bootstrap固定median/group/eligibility的条件性已经写入协议。
- 根保存SYNTHETIC_CHECKS.json，记录一次synthetic test命令exit0。本角色读取该回执，没有自己再执行，不把它叫独立复现。

**GO_SOURCE_ONLY_ASSOCIATION_DIAGNOSTIC**。没有剩余阻止冻结/prepare/run的本角色修订要求。GO仅针对预声明source-only screen；不是模型适配、结构编辑、临床作用或RSI的认可。结果audit需用隔离SOURCE.npz直接pairwise centered重算，而不导入根moments；仍不得解析dev或保护结果。任何进一步预测试验须单独定义同信息普通条件模型强对照与功能决策门。

交叉阶段0GET、0API、0生物数值读取、0测试/prepare/run执行。没有改动根协议或代码。
