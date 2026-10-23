# CDK：中期组成信息未转化为本配置的功能排序增量

2026-10-22。完整目标 ACTIVE / NOT_ACHIEVED。本轮 PROGRESS：首次实际解码此前仅做身份认证的S4耐药培养物功能端点，完成响应前冻结的普通强对照与独立原始记录/全预测复核。不是新算法、湿实验或RSI成功。

## 功能合同与结果

同一MCF7祖先的12条培养轨迹，两个challenge分别评价；仅纳入各列positive finite IC50，N/A为机制未知的缺失。单位未认证，故不比较药间绝对效力，只评价同选择药×ER条件下培养物对的相对排序。每次联合留出两个目标培养物，不让一个目标标签进入另一个目标的训练；源内按condition/challenge构建midranks，以condition截距加固定普通Hellinger-feature ridge预测。所有方法共享相同合法Early与Middle信息，End不入特征。主lambda1，预固定.1/10敏感性，不择优。

| challenge | 有效培养物/12 | 可评分对/条件 | 条件均值loss | Early loss | Early+Middle loss |
|---|---:|---:|---:|---:|---:|
| Palbociclib | 2 | 0 / 0 | 不可估 | 不可估 | 不可估 |
| Abemaciclib | 9 | 7 / 3 | .5 | 1/3 | 2/3 |

loss先在condition内平均，再等权平均condition，越低越好。Palbo有一个同条件的真实已测配对，但联合留出后源样本数为0，因此不可训练评分，不是没有任何配对数据或该药全缺失。Abema缺3条，其7对共享9条培养物，不是7个独立试验；只有3个条件贡献指标。主lambda下Middle使Abema_WT唯一pair从正确转为错误，其他两条件的损失不变，故宏平均从1/3到2/3，不能形容为所有培养物普遍恶化。

lambda .1与主分析同方向；lambda10两输入均2/3。故Early相对条件均值的有限正向也不稳定；Middle没有通过任一预定增量方向。Abema_WT该对真实标量相差约3.24倍，不是原始数值几乎相等；但真实曲线/拟合误差未知，不能认证测量可重复性。模型预测rank差很小，按事先tie容差仍构成不同排序，不事后改容差挽救结果。

## 实际审查与独立复核

biology与skeptic先审功能合同，biology与frontier再做响应前代码审查。发现源rank错误地在整个challenge池构造，以及numpy整数序列化风险，均在S4值前修复并保留原REVISE稿。5项synthetic tests验证held-pair标签排除、End不变、constant source/no-signal严格tie、分condition独立单调变换不变及结果JSON可写；不是新生物证据。

FREEZE绑定协议、代码、测试、输入及评审13项。独立audit不import主run模块，重新解析原S4的24条selected resistant C/D记录，全部身份、原始值与缺失一致；不读vehicle C/D。用显式feature中心化和spectral ridge独立复算全部42条pair×lambda×输入预测行，最大差2.6645352591003757e-15，所有loss、分母、不可估配对、宏平均一致。未重新认证原S3全部Count；依赖上轮已独立认证的prepared与hash。完整npz会物化End，但两套实现均仅用Early/Middle。审计PASS详见audit/NUMERICAL_AUDIT.json及INTERPRETATION.md。

功能结果后两名独立评审再封存解释并实际交叉，原始材料在 `../revision_value_operation/biology/RESULT_REVIEW.md`、frontier同名文件及RESULT_CROSS。交叉质疑和未决测量限制不按多数票消除。

## 决策

**FAILED：Abema下本固定直接模型配置的Middle功能排序增量门。NOT_ESTIMABLE：Palbo下联合留出评测。STOP_EXPANDING_EXACT_FUNCTIONAL_PREFIX_KRR_CONFIGURATION。** 不增加lambda、噪声模型、barcode筛选或编辑器来追逐已读端点，不将N/A填为最大耐药，不改成组成指标救回功能结论。

这个限定STOP既不证明所有Middle信息无用，也不否定其他独立机制/数据。它将用户建议中“组成能否接功能”的未决问题推进为一个真实、可复现的阴性开发结果。极小独立样本、未知缺失机制/测量误差、共享祖先，以及留出pair后同条件最多一条source（Abema_WT为零）意味着实际主要依赖跨condition关系迁移，不能宣称普遍生物学反证、药物选择效用或独立外部确认。

主执行wall0.126秒，独立审计wall1.404秒；maestro Python3.11.16/numpy2.4.6，无随机训练、GPU、API、新下载或湿实验。原生代理计费/token未暴露。src/tools与历史STOP未改，所有protected分区关闭；原全局provenance漂移未解决。完整WM、agent、继承、联合和improved-improver证据仍未建立。
