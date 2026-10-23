# 独立API提案审查：rank约束可研究，但当前任务与参数来源未闭合

2026-10-23。先读取本阶段biology/INDEPENDENT、AUTHOR_TASK_ADDENDUM、frontier/INDEPENDENT与API原文，再独立写本稿；未读其他角色的本轮API审查。0GET、0拟合、0toy、0数值payload访问。API一次调用/3174tokens为根提供的回执信息，本角色没有重复请求。

**REVISE_BEFORE_ANY_FIT / NO_CURRENT_GO**。主要反对不是属于lowrank家族，而是提案的任务信息、药载荷与最强对照未对齐；当前也没有支撑特定rank1限制的重复误差。

## 最强成立点

- 一个明确的diag+rank1约束可以改变有限样本偏差/方差；强direct能表达它不等于实际低反馈效用必然相等。不能仅凭“低秩已知”否决任何应用结构贡献。
- 提案有公式与可继承参数对象，并承认updater不是自主agent、一次MSE提升不是RSI。这些范围限定正确。
- 药物部分CellHealth预测health不能作真值，PRISM剂量rank对齐不能当精确暴露匹配，这两点与一手审查一致。
- 源期学习的药特异反馈增益如果可依法估计且目标任务是新患者，可以作为普通结构适配的受限实现；这是可修正的科学问题，不是不可计算命题。

## 具体不成立/未定义点

**1. 任务从同患者八种药，变成每药八个患者。** 已有BeatAML阳性是给一个患者揭示八个已测药物AUC，预测该患者其余药。它不是每个query药都有该患者八次独立反馈，更不是每药从八个患者收集反馈的新药迁移任务。API的bar r_d是在同药多x_i上平均；对原任务未支付的query药d，bar r_d不可得。直接把旧23.49%阳性当新任务证据或同预算依据是错误。

新药八患者任务本身可以有科学意义，但必须另定义源/目标药及患者的双向隔离、每个功能束成本与固定f0如何给新药预测。不能借旧划分/旧分数声称已经资格通过。当前不足以授权另起这个fit。

**2. 新药u_d没有来源。** 源只学u_d对d∈Dsrc，新药身份未出现；“冻结u_d”无可冻结项，“最近邻”没有指定药描述符、度量、相似度/载荷估计程序及训练信息。同理a_d可有源分布prior，但不能把新药特异参数凭字符串ID生成。若用新药八反馈同时估u_d，应改自由度/预算声明并检验设计矩阵秩；不能仍说目标只fit一个a_d。为使其可执行而另加chemistry encoder将是实质新方法选择，需要独立审查，不在此代填。

**3. 原阳性对照本来就药身份依赖。** 原协方差更新是mu_Q+Sigma_QS(Sigma_SS+I)^-1 z_S，其Jacobian在固定S和源统计下确实常量，但每个query/support药身份对应的矩阵元素一般不同。常量不等于全局标量、不等于不依赖药身份。API把此前方法共同归为固定全局标量，再宣称新增药身份自由度，是对实际对照的误述。

**4. rank1不是八反馈下唯一可辨识结构。** 可辨识性取决于源信息、设计、先验与估计对象，不从n=8推出diag+rank1唯一。源期可以估计其他正则化多任务/低秩模型；rank1有缩放不识别u→cu,v→v/c，也不妨碍预测，但若解释载荷集中性，必须规范化并说明其意义。

**5. bar r_pool与合法信息需闭合。** API一处允许跨已测药pool，另一处目标信息只允许该药八AUC，且排除其他药目标功能。若合法集合仅一个新药，pool就是同一bar r_d，输出为y0+[a_d+u_d(v'phi(x))]bar r_d，即一个含basal交互的残差校准。它仍可不同于不含交互的弱scalar对照，但普通同feature交互回归/结构条件预测必须纳入；不能把任意conditional EB缩成只向一个global scalar收缩。若pool跨已测药，必须明确哪些患者/药如何购买、如何对新x聚合，否则任务不完整。

**6. 计算/方差论证不充分。** 比一参数与两参数少一半参数不证明少一半总计算；源u/v学习、f0、phi选择与新药映射都要计成本。8点斜率方差也不是简单1/8，取决于输入spread、噪声/误差变量和正则化。u_d“分布集中”是整个药集合的属性，不会自动形成可前向定义的药子集；即使可定义，其集中也不必意味着效用集中。此分层规则尚未成可执行证伪条件。

**7. CellHealth真标签范围表述过宽。** API末段“CellHealth…health是预测非真值”若指整个CellHealth则错误。357个遗传guide×line条件有独立实验测得的Cell Health共识标签；药物10752profile上的70health才主要是预测标签。分别测量、无法跨replicate匹配不等于遗传condition标签是假。可合法研究condition级mapping，不能研究同细胞功能或药物完整health oracle。

**8. BeatAML不是只有一个生物背景任务。** 它有多个真实患者背景，可按患者做功能反馈任务；单疾病标签不消除患者变化。它确实没有因此自动提供动态细胞世界或多代RSI。反对它的原因应是当前精确机制与评测未闭合，不能借“单背景静态”把合法患者迁移也否决。

## 最强对手与当前结论

对原同患者八药任务，最强近邻至少包括实际full/regularized covariance conditioning、同固定支持id的rank1/多rank条件残差模型、同basal/药描述符的非高斯conditional EB或完整支持集合预测器、普通union refit。所有对手拿到同源历史、phi、药物映射与反馈；稠密低效实现不是合理成本对照。

对另定义的八患者新药任务，则需要同drug descriptor、同患者信息、同source targets的普通multitask/残差交互/同rank约束估计对手。一个恰相同公式的普通实现不是要被击败的独立方法，而是命名等价性边界；创新若在新生物限制/预算优势，须单独给理由与实测。

目前不把rank1公式改写后立即fit，也不以它重开旧lowrank/CD14路线。先缺一项精确而有依据的结构假设，以及可执行任务信息合同。没有证据支持世界/agent/inheritance/joint/G1-G0。

## 对本角色copula尝试的源契约修正

condition consensus的952维Cell Painting summary并不提供每细胞联合z_i及w0_i。即使单well特征原本含texture/相关统计，也不能从MODZ condition向量重建完整单细胞copula或条件内pairwise co-expression。Cell Health跨assay replicate无法匹配，因此也没有单细胞z_i↔ψ_i功能监督。source paper给357个独立assay的**条件期望/共识**，不是它们的joint single-cell distribution。

故本角色I-projection操作当前无法由该共识源直接实现；不能把condition之间的特征相关当condition内单细胞copula。公开原图/objects若未来确实可得可能支持别的任务，但本次没有认证，不增GET或另开资产链弥补。原稿NO_FIT结论加强，不改写原稿。
