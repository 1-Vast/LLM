# S4功能排序探索：响应前最小合同审查

2026-10-22。只读既有S4_HEADER/ADDENDUM、CDK组成DECISION与NUMERICAL_PROTOCOL；未打开S4数值、prepared矩阵或protected响应。**可以开展一次明确限定的功能增量探索；它不挽救组成STOP，也不是新机制晋升。** 但source ranks如何定义必须先固定，不能把仅一个源培养物的条件当作已学会条件内排序。

## 数据与评价单位

仅12条resistant evolutionary cultures，四个selection-drug×ER条件、每条件三条培养物；两个challenge分别处理。S4 vehicle六行不加入，因为与S3选择study的历史join未认证。challenge只取已给定正、有限IC50；N/A保留原缺失身份，不作无穷、不填最大值、不视作检测上限。非正/非有限/未识别文本应停止并记录，而非自动删去不利样本。两个challenge不是24个独立生物任务。

单位尚未认证，主要目标仅同challenge、同selection-drug×ER条件内的已观察IC50顺序。对两个均可观察的同条件培养物i,j，预测顺序与实际顺序比较；预测tie计0.5错误。实际IC50完全相等建议也固定计0.5（即无方向信息），并另报实际tie数；不能通过任意浮点容差创造/消除tie。解释为更高/低作者IC50，不称固定剂量杀伤或换药收益。

以两个培养物为联合留出单元，i,j两条历史在该fold都不进入训练、秩转换、核带宽、正则选择或监督预处理；两个challenge若同一fold用于选择，也都不能让i/j其他challenge标签泄入。历史Early cohort定义的公共barcode宇宙可沿用，明确这是已声明transductive Early特征资格；不能用Middle/End频率重选宇宙。Early+Middle预先定义为sqrt组成拼接/√2，Early-only不读取Middle作输入。prepared NPZ含End时，数组物理解码与算法输入分开披露，End绝不进入功能模型、调参或feature universe。

## 最小固定模型与source-rank陷阱

建议固定一个KRR程序、lambda=1，不额外小网格；强条件baseline在同条件test pair必预测相同，pair loss=0.5，不应包装成条件均值实际数值预测。kernel直接沿用前组成实验的固定RBF距离规则（sqrt composition、source距离带宽、context mismatch），且每fold独立重估source尺度；不要为S4值重新挑带宽。模型输出只是challenge内rank score。

可执行且最省变更的源标签是：每challenge、每condition中，仅用该fold训练源可见IC50计算midrank，再映射为(rank−0.5)/n。n=1时为0.5；n=0没有训练样本。不使用held pair的终点确定源秩或分位数。Early与Early+Middle用完全相同源标签/同核及正则/同样本支持，不把不同目标尺度当Middle贡献。

**关键限制**：每condition只有3培养物，联合留出两条后目标condition最多只剩一个源标签，其normalized rank必为0.5。因此该fold没有任何来自目标condition的源内排序对；能产生不同预测依赖其他condition的相对排序结构迁移，或核相似度对跨condition标签的外推，不能叫“学会目标条件内IC50函数”。source midrank在不同fold变化也是预定label定义的一部分，不等同一个固定物理IC50回归函数。

这个限制不使探索非法，但若其他condition也没有足够可观测标签/排序变异，source标签全相同，则模型没有可识别监督排序信号。应报告该foldsource rank方差/各condition n；若全常数，可直接输出tie而不是让数值jitter或非中心化核插值制造虚假的数据支持。KRR含不惩罚截距（source标签中心化后预测再加均值）最简单，保证常数标签时严格tie；不要把零均值GP向0回缩造成的距离次序误当功能知识。

若认为rank-regression代理不足，唯一事前小修订是换成明确的**source内同条件pairwise kernel ranker**：只用其他训练condition里可观测培养对的差分特征和方向拟合固定ridge，再预测held pair差值。这样监督目标与评价更一致；但依旧只检验跨condition排序迁移、且有效sourcepairs很少，不能同时跑两个方案并事后择优。本次优先固定有截距的rank-KRR即可，不为代理缺陷增加菜单。

## 缺失、统计与measurement边界

既有文本元数据已表明Palbociclib challenge的多个condition没有或仅少量有限值。须在开值前固定：有至少2个有效值的condition才产生评价pairs；不足的condition记“不可估”，不凑成全四条件泛化。每challenge报告有效culture/condition/pair数、每pair方向损失及Middle−Early差，再在有资格condition内先平均pairs、再condition等权；两challenge分开列主结果，不合并24个端点或假装独立。

同一condition三培养物产生的三pairs共享培养物，LOPO训练集也高度重叠；pair不能独立bootstrap或t检验。最多12培养物/4条件/单一MCF7祖先，无法支持常规稳定统计显著性或独立祖先外推。报告逐pair及逐condition方向、删除单condition的描述性变化即可；若只一个condition有资格，根本不存在该删除敏感性，不发明置信区间。

IC50是作者四参数曲线拟合的标量估计，原始well/curve、单位、拟合误差、censoring及N/A机制均未认证。接近的两值排序可能由拟合噪声反转，不能以数字不同自动宣称生物学可分。rank规避未知共同正尺度，但不解决跨样本尺度不一致或曲线不可比；因此结果是作者标签顺序预测，非临床耐药程度确认。

## 最小成功与停止

一次固定程序比较Early与Early+Middle在相同可评价pairs上的ordering loss，并同时与0.5 tie基线比较。若Middle仅比Early好但仍不胜0.5，不能称建立功能可预测性；若只少数pair改向，报告原始分数而不添加新阈值。若没有任何有效pair、source监督全无变异或样本join不唯一，停止相应challenge；不开放新response、不改N/A含义或引入End追分。

正结果至多SUPPORTED exploratory Middle信息增量，负结果限定本kernel/ordinal合同，不否定所有功能信息；任一结果都不能验证世界模型必要性、下一实验选择、继承或RSI。本次为得到真实功能边界的有限探索，允许条件合同冻结后执行，无需先获得完整RSI任务银行，也不再无限来源资格审查。
