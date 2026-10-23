# 响应前协议复核

2026-10-22。实际阅读PROTOCOL.md和元数据SPLIT.json；未打开响应或原始CSV。未修改root协议/代码。

**支持按本协议进行有限普通反馈价值pilot；排序指标有一处需在开值前消除的文字歧义。** 前40cell完整共同目录887pair、35,480task消除了不同cell样本组成差异；后20cell闭合。覆盖资格基于元数据且明确排除2148个不完整设计，属于有限目录任务，不能外推全部药物化学空间。

## Study敏感性

按target pair排除source中同study记录，重拟合原先已选择程序、不重调参数，是合理且可执行的依赖敏感性。它测试该pair直接同study响应能否解释收益；不证明study完全独立，也不控制跨pair协议潜在共同因素。由于模型严格pair独立、不读取其他目标pair锚点/单药，本轮无需附加全局跨pair模型排除。

source<2时停止整个敏感性并报告不可估，不删pair凑通过，合理。此时总门应记为“未满足/敏感性不可估”，不能把NA当通过，也不要称为负向生物结果。敏感性应同时重拟合selected B0/B1并在同样剩余source、相同887pair/8query上比较。均值/标准差、残差均值、kernel及Gaussian协方差也必须在排除后的source重算；只删某些目标向量但保留原全source预处理并不完成敏感性。

## 预算和模型选择

B0六solo/B1另一个最高×最高anchor、共同0..7query清晰。PERCENTGROWTH/100、负值保留、唯一row计数、禁止隐式OD/Score、原始重复和reserve闭合都正确。一次对887pair各回放一anchor不等于一个细胞只做一次测量；逐pair条件任务预算可报告，同时全cell目录累计887个组合揭示须如实计账。相同solo row在pair之间共享，只按unique记录计费；这不意味着模型可读取合同外其他pair单药。

15个B0与15个B1普通候选，额外B0fallback使B1有16次选择机会，已明确披露；本轮不声称等预算程序搜索优越性，因此可以接受。fallback应直接复用source-selected B0、完整B0输入和参数，不把目标anchor送入B0程序或借fallback重新按dev选择。

20fit->10tune选一个全目录程序、30source重拟合后10dev评估成立。强普通菜单包括非线性RBF与Gaussian，无需再扩展。Gaussian必须真正条件于同样合法solo+anchor信息；B0不得从九维source残差的target部分误读目标值。合成不变性测试能验证该边界。

## Gate与排序目标

正向平均gain、固定cell bootstrap下界、7/10cell改善、leave-one-cell-out均值正与study敏感性平均gain正，作为一个**开发资源分配门**合理。条件不互相独立，不能把五个通过当五份独立证据；只有10cell，bootstrap不覆盖训练不确定性、共享study或生物重复，协议已如实限定。不需要再发明效应阈值把普通pilot包装临床意义。

排序指标文字同时出现“观察query中最低growth作为参考”和“8点平均growth的selection regret”，存在minimum与mean混用风险。已实际发消息请root在开值前明确。建议唯一公式：每pair真值g为8query实际增长均值，预测值为8query预测均值；k=ceil(0.1×887)=89；选预测均值最低89pair，oracle选实际均值最低89pair；regret=预测所选集合实际g均值−oracle集合实际g均值，固定pair顺序破同分。若想用八点最小值，则应完整换成minimum定义，不能oracle按min、损失按mean而不解释。此为次要有限目录排序，不能替代MSE主门。

门失败即停止此固定菜单的创新扩张、不开放reserve、不换endpoint/anchor；通过也仅GO诊断。该边界与现有阴性历史一致且有限，不会把普通正向结果自动晋升RSI。

待模型代码独立审阅与合成测试通过、上述排序文字明确后，可冻结并执行本轮允许的前40cell响应读取。此审阅不授权额外数据/目标或修改已封存来源记录。
