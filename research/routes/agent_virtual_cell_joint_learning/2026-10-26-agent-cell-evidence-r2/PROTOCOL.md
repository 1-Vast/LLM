# E002：新背景整板取证后，另采功能终点评分

2026-10-26。初版在首次加载响应前保存；具体处理/超参数须在数值前追加冻结。尚未执行预测实验。

## 阶段与动作

白名单为第一轮固定SHA的BATCHIE PAIR_SCREEN，不打开sealed/reserve/vault。source仅numeric rounds1—10；query仅numeric rounds11—15；terminal仅`validation (random, round 15)`。terminal中与全1—15轮重复的原始药名×剂量×细胞键统一删除，不按效应选择。无向排序不是化学实体映射。

元数据固定新背景：A673、BJ、MSKEWS-66647、SKNEP、TC-71，相对source都无观测。相同cell、iteration、完整well→药名/双方剂量布局的两个file组成一个重复板动作。后5轮108 files组成54动作，每组恰2 files；5背景各有12/3/3/6/6候选布局。source及静态特征不得读取这些细胞的query/terminal响应。

先固定每背景1个重复板动作预算，支付2个真实plate全部well（包括控制、QC失败），之后才揭示响应及Failed QC。terminal QC可用于所有方法共同的评分，但报告原始/失败/去重覆盖。菜单是历史已测菜单，不宣称包含全部可选动作或没有原始策略的选择偏差。

## 问题与比较

H005：同source与预算下，明确的条件更新改善未查询terminal的top3效用`-Viability`。Alamar Blue不是死亡率/临床效用；不把不同cell菜单拼成未配对治疗指数。

H006：固定更新器比较随机、GP不确定性、exploit和batch决策KG；更新器则用共享固定/多策略轨迹比较，不只评候选自己轨迹。至少包含强直接功能/单药完成基线、普通重训练、层级/多任务、GP后验。具体形式在读数前冻结；若候选等价于基线，记录等价并停创新主张，不用弱对照装饰。

所有方法同菜单、source、反馈和whole-plate预算；多随机seed或全部动作枚举给随机分布，计算消耗另记。按5个cell做配对95%探索CI并给逐cell结果，不以数百well当独立生物样本。最小实用差与功效未认证，此回放可筛掉无收益方案，正结果也不准直接晋升。

未见药物和跨独立来源任务仍为单独未完成门槛。若追加新药划分，先固定身份和source/query可见性再读响应。API不生成测量真值。

## 停止

动作无法复现、重叠不能保守排除、source特征含目标响应，或候选更新未明确，则停对应处理，不加载terminal。独立收益、新药和跨任务未通过前，不做元学习/RSI，不晋升src/tools。

## 响应读取前冻结：E002B普通更新与决策空间

下闭许可算子已被枚举为同先验层级MAP等价，不训练该新算法。E002B是时间新背景的基线/决策空间实验，不当作原目标达成。

每个drug-dose的静态描述仅为10个source cell单药响应均值；缺失按该drug-dose source均值、再全source均值填。query/terminal不能构造描述。pair特征为两单药描述的平均、绝对差、乘积共30维，加常数；只用source标准化。DMSO理想描述全1，不当实测药物效果。原始药名/剂量不等于化学结构统一。

静态预测器：source ExtraTrees，64树、min_leaf5、max_depth24、seed20261026，含source cell one-hot；新背景额外列在source为0。普通重训练：同模型source＋付费target反馈重拟合，36树，其余相同；此树数差是计算节约，不声称等实际算力。direct_mono用付费单药值替换/线性外推source单药，保留静态pair residual。

GP：同静态prior mean，RBF幅度0.25，长度尺度平方为标准化非constant维数，noise variance0.01；只更新已支付QC有效target条件。层级基线：source每cell线性残差Ridge系数估计跨cell协方差，加0.01I后empirical Bayes更新；另报isotropic residual Ridge（λ1）。参数不由terminal选择，后验未声明校准。

每cell枚举全部真实paired layouts，各更新器在共享动作下评分。策略固定同GP：random为全动作均匀期望；uncertainty为terminal integrated variance reduction；exploit为动作内预测top3低Viability；decision KG用16个Gaussian fantasy按动作后terminal top3平均改善。acquisition只读source模型和设计特征，不读query QC/响应或terminal响应；按整板联合观测，不拆免费label。

效用=-terminal Viability的top3均值，regret为共同菜单oracle减效用。枚举是历史菜单反事实回放，不是湿实验。重复有效条件取均值，失败仍收费；terminal始终共同。固定uncertainty/KG/random轨迹比较更新器，固定GP比较策略。记录真实预算、计算开销、hash/数据流、逐cell与探索CI；5背景不认证外部迁移，不启动RSI。

## 实现纠错v1

首版asrun_v0完成但不用于当前科学比较：acquisition使用QC过滤后的terminal池；修正为完整metadata设计池，QC只在评分端使用。独立元数据检查确认这5目标cell的terminal没有失败，故此风险在当前数据不会实际改变选板，不能称观察到了QC泄漏收益；仍修正通用数据流并加mutation检查。重训练树数36改为64以保持同容量，这是公平性修正，未按终点效用选参。核幅度、噪声、特征与标准不变，旧版保留不得择优。
