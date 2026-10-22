# 数值前协议：selection / state-change 的观测等价反例

2026-10-22。root 明确请求一个可执行反例/ordinary reproduction 审计，区分 selection 与 transport 的可识别性及最少额外反馈。这里只用事先手写整数规则，不读任何生物数据、不拟合、不 HTTP、不改变旧 STOP。

两个模型均从 A/B 各200个 founder 开始。每个 founder 只会不分裂存活、分裂一次或死亡。理想 H2B reporter 无噪声，精确分辨最终细胞的0/1次分裂历史。模型 S 无状态改变；模型 T 的一小部分 A-origin 分裂后为 B。两者设计为同时匹配：最终 state×division-history 的完整联合计数、总细胞数、总体出生/死亡数。cycling tail 为1%，不是药物实测比例。

预定审计成功条件：

1. 两模型初始 state 计数一致。
2. 上述全部允许的 endpoint/global observables 精确一致。
3. 隐藏 origin→destination flow 不同，S 的 A→B=0、T>0。
4. 普通 state-conditional two-component 表能复现相同观测联合分布；这只是 observational likelihood 复现，不是新任务预测胜利。
5. 添加一个 origin-A→late-B 的联合计数能区分这对模型；它不是一个标量普遍识别任意动态系统的定理，也不保证有限 noisy sample 的功效。

结果仅否定“总量/endpoint reporter 自动识别 state change”这一一般断言。它不否定特定附加假设下的识别，更不要求先解此分解才允许预测 survivor-conditional cycling risk。真实 barcode 若只标 clone、clone 内初态异质，不能自动当作每个 founder 的 initial-state label；若初始状态与 lineage 真的绑定，它可能已提供需要的 joint feedback。

code/tests 先 hash 封存后执行。任何断言失败保留失败，不改模型救同一次审计。所有代码在 research/renewal_application_20261022/，输出和 receipt 在本目录。
