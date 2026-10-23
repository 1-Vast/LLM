# S4功能增量：独立结果解释

2026-10-22；读取冻结PROTOCOL及root RESULT.json，先独立封存再peer结果互读。未读原始S4/prepared数值、未独立重训或审计全部模型；这里只审保存records与判定，不夸称全数值独立复现。

**既定门未满足：STOP本固定functional-prefix KRR配置的扩张。** Palbociclib challenge不可估，Abemaciclib可估部分未支持Middle增量；二者性质不同，不能全写成“Middle无功能信息”。

Palbociclib只2条正有限标签，恰属同condition。二者联合留出后source数0，因此唯一可能pair被明确记录不可估，没有模型预测或排序loss。这是训练合同缺支持，不是生物假设失败；N/A不能补成无穷或借另一challenge填标签。既定双challenge成功门因此已经不能通过，但不将null当数值负结果。

Abemaciclib有9条有效culture，7个可评pair，覆盖3个condition（1+3+3）；另一个condition仅一个有效值无pair。主lambda1的condition等权ordering loss：Early=1/3，Early+Middle=2/3，tie baseline=1/2。lambda.1相同；lambda10两臂均2/3。因此Middle未胜Early与baseline，敏感性也未保持增量，符合预定停止条件，不追加模型/阈值/其它stage。

保留有限Early正向：主/.1平均loss低于tie，其中Abema_WT、Palbo_WT正确，Palbo_Mut反向；但lambda10 Early失去该优势，不是稳定泛化。Middle相对Early的宏loss恶化完全由Abema_WT一个test pair方向翻转贡献；另两condition不变。不能把2/3宏loss当7个独立失败或多个祖先复制；这种条件宏平均也不能与pair-pooled loss混用。

Abema_WT这对真实作者数值3.267e−6与1.007e−6，在共同未认证尺度下比值约3.24，不是原始IC50数字接近的pair；但主Early预测分数差约2.21e−4、Middle约−5.30e−4，模型排序边际很小。二者均高于预定1e−12预测tie阈值，故不能事后改阈值抹去反向。其它pair可能有接近的真实值；原始曲线/拟合误差未知，不能从精确小数断言生物排序显著，亦不能凭模型分数接近就改判真实tie。

Abema_WT留出后该condition没有合法source，走pooled fallback；其余3培养物condition留2也只剩1同组源，源内rank必0.5、残差0。因此该问题主要检验从其他condition学到的组成/ordinal关系能否迁移，不是丰富的目标条件内药敏函数学习。所有标签有缺失选择，结果条件于估得IC50的子集，不能外推N/A培养物或耐药天花板。

这次真正补上了过去尚未实测的功能边界：有限Early组成可在一个固定正则下提供探索性顺序信号，但当前Middle输入未带来可复用功能排序增量。它不改组成试点的小幅同类ridge增益，也不恢复可稳定选择的世界模型/agent/继承/RSI机制。没有下一实验选择或绝对效用目标，故不称药物决策成功。

建议按既定协议停止该配置，不为缺失列或单pair反向新增菜单、改rank变换、测量噪声门、pair权重或开其他response。极小样本、单MCF7祖先、重叠pairs和未知IC50测量误差限制结论；负向范围仅本固定prefix核/源rank/留pair合同，非“所有Middle生物信息不存在”。完整研究目标仍ACTIVE / NOT_ACHIEVED。
