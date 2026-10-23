# ESG独立审查：边差符号门控

2026-10-22。只读api_completion/RESPONSE.md，未读peer本轮API评语；不作数据/权重/保护响应访问，不与本角色原生约束更新稿混淆。**STOP当前写出的ESG核心晋升；无需先找数据。** 它确实指定了比sample SGD更具体的门控操作，但所称nuisance消去及二项统计保证不成立，且最近faithful ordinary对手被弱化。

## 主效应究竟在哪条边消去

令真实y=b_true(s)+g_true(s,d)，冻结模型b_psi不一定校准。r_i−r_j包含[b_true(s_i)−b_psi(s_i)]−[b_true(s_j)−b_psi(s_j)]。

- 同state、异drug边：该差异严格为0，因此可以消去纯state加性误差；但药物特异测量/剂量尺度误差不消去。
- 同drug、异state边：该项一般**不为0**，恰好把未校准state主效应引入g更新。若药效与state真正相互作用，也不能说同drug差分是无药效的nuisance。

最小实数反例：两个state的真实主效应为1/0、真实药效均0；冻结b=0、g=0，同drug观察y=1/0。某个g方向只改变第一state，a=1、rho=1，一致性门偏好该方向，更新把纯state主效应错误写进药物模块。多次同类观察不会修复可辨识性。若所有state都有自由g(s,d)，b与g的分解本就可沿h(s)相互补偿，冻结b不认证g的生物意义。

所以当前并集边不能声称全部消去state nuisance；只用同state边是另一有限合同，不能默认为本API已实现，且那仍是普通pairwise学习。

## 二项门不是独立重复证书

边共享样本端点，sign(r_i−r_j)之间高度依赖。按B×B写法同一无序pair的(i,j)/(j,i)同时出现，rho与a均翻号，一致事件完全重复；即使去掉反向，n个样本的n(n−1)/2边也不是相同数量独立Bernoulli。Bin(m,.5) tail因此不能按宣称控制错误方向；Bonferroni只处理方向间多重检验，不修复每方向p值失准。

另外Pr(sign agreement)=.5需要明确null、对称性及固定方向选择机制，不由“随机”二字保证。异方差、系统状态偏差及数据选方向可破坏null。cluster-level置换/符号翻转也只有在相应exchangeability认证时才合法，不是现阶段可自动补入的新保证。

公式k未限制|a|>epsilon，而伪代码有该限制；以可执行伪代码善意审查，不用这个文字瑕疵否决核心。V_h为空须无操作，rho=0的tie规则须固定，不能当半次成功以外任意挑选。

## 方向与排序意义

gate只接受sign(rho)=sign(a)超过半数，对v与−v不对称。若所有合法反馈都明确要求−v，+v一致率0被拒，之后的sign(S)也不能复活它；除非预先V包含两个方向或做双侧检验。此为真实方向白名单假设，不是一般自适应符号更新。通过gate后sign(S)按|a|加权，可能与无权多数一致性结论相反；门控统计与实际步方向不完全一致。

rho是目标**残差差**，不是目标标签的rank差。它可指导修正差值但不认证Kendall改善。固定eta、非正交方向累加、局部导数失效也会越过正确区间，或者损害其它已正确排序的边。没有line search/信赖域或功能效用保证；即使补这些也属于后续不同提案，不是当前证据。

## 最强specific ordinary counterpart

不能只比sample MSE-SGD/sign-SGD。对同一观测边建立

    L(phi)=sum_e |[y_i−y_j]−[f_phi(i)−f_phi(j)]| .

在当前参数处，负subgradient沿v的投影就是S_v=sum_e sign(rho_e)*a_e,v。对固定basis的coordinate/sign descent再加**同一个**m/k门、同一个V_h和eta，逐步实现所写ESG；edge权重、缓存Jacobian和方向搜索计算也能完全相同。这是字面L1 pairwise residual目标的门控方向下降，非等同于所有logistic rank loss，但足以给出忠实specific baseline。另需强pairwise rankloss、普通conditional calibration与同历史learned gate作实用对手。

只因属于该family不能否定未来有独特统计规则；然而当前gate没有有效依赖校正，nuisance说法又错，未提供超出上述同操作baseline的新性质/预算优势。继承V_h本身是方向筛选知识复用，不证明门控策略更会学习或RSI；冷启动强对手须同源方向筛选和common-start，不只无白名单sampleSGD。

## 真实生物合同、必要性和决定

连续高维状态s“相等”通常意味着同culture/同处理前状态定义，不能按转录相似或不同细胞假装完全同state；drug相等还需样本、剂量、时间与测量单位一致。study-out也不保证不同study量纲/控制可比。当前没有认证满足这些边的真实功能矩阵，因此不能先用未读reserve补结构。

世界模型仅在此提供f及Jacobian，强直接差分模型同样能提供；agent非平凡实验动作与改进策略更新均未指定。全局误差比sampleSGD好不构成二者必要性。

决定：**STOP_LITERAL_ESG_CORE / NO_CANDIDATE_AS_WRITTEN**。保留“显式利用合法pairwise功能反馈”这一标准工具，不将错误统计保证修补成新门控菜单再追分。若支持者要重提，须先给真正可认证的nuisance合同与依赖有效检验，并指出相对同pairwise目标+同门控ordinary程序的具体技术差异；本轮不启动这些修补、sourcehunt或生物实验。
