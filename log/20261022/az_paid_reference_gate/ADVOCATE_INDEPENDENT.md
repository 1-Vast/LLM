# Paid-reference gate：最小功能结构与独立支持方意见

2026-10-22。仅阅读本阶段初版 PROTOCOL、此前已读的冻结 AZ design/交叉记录和 parent 提供的 GDSC007/25pair 范围。未读本阶段 peer 新稿、ZIP rows/target、未 GET、未 fit、未改旧 freeze。此稿先于 root complete protocol 的交叉审查。

**裁决：值得做一个有明确停止条件的普通结构机会实验；当前仅 CONDITIONAL_GO_TO_COMPLETE_PROTOCOL，不是数值开值许可或新核心资格。** 重点是能否用合法付费单药参考建立可迁移、实用的组合功能预测偏置，不是发明新 kernel/spline，也不是将静态 CTG 面变成观测过的动态世界。

## 应用、动作与修正后的可观察性

一个 episode 固定为同 project/member/MASTER_CELL_ID/CELL_ID(stock)/BARCODE 下的未购 AB 矩阵。两次付费购买其他 pair 矩阵，使 A、B 的所需单药剂量都被覆盖；两个 witnesses 都不能是 target pair 的重复。AC 和 BD 已足够，C 与 D 不必相同，三角闭合只是充分例，不能以无 triangle 宣布不可行。除所需 A/B reference 外，两个 bundles 的其他单药和组合 outputs 全部计为已购且对所有模型可用。

应用是提出值得进一步确认的组合/剂量，而不是预测真实死亡或患者获益。先限制到设计选定 GDSC007 的25pairs，角色按 MASTER_CELL_ID 分组，stock/plate/repeats 从不跨角色。不同 target episodes 即使在同一 cell 中，也各自从同一历史模型与私有的两-bundle观测开始，不能将其他 episode 已购或评分的 AB 偷渡为本 episode 的输入，更不能把25个target评估合报为一次两-bundle campaign。

最小门先用**精确 µM 匹配**的 observed lib1_y/lib2_y。不要为了扩大覆盖先引入 IC50、fitted yhat 或目标附带mono，更不应把未购参考记成免费已知。若完整协议要插值，须单列合法规则、参考支持和额外限制；最初 gate 无需这项复杂性。重复参考需按 source model/stock/plate/drug/dose 的真实生成键清点，不能把每行重复引用当独立读数；若同一声明参考不一致，数值前规定共同失效或来源认可的聚合，不能看 target 后择值。

## 最小可证伪模型

已付费参考提供 u_e(dA)、v_e(dB)，都是源定义的72h normalized inhibitory response，保留有限负值/超过1等合法源值，不随意裁剪。令 p=AB，B(u,v)=u+v−uv 只是普通 Bliss 基准。主结构模型为

`M_E: Yhat_e(dA,dB)=B(u,v)+h_p(u,v)`。

h_p 用一个事先固定小维度的 pair-specific tensor spline（或固定基函数 ridge）拟合训练 MASTER 上的组合残差，正则化只在 validation 上选择。不要同时探索任意网络/复杂因果模块；root完整协议应固定一种基函数及有限预算。跨cell共享的是 h_p，不是单药剂量曲线；新cell信息经其已付费u/v进入。该模型的实质假设是**观察到的单药效应坐标能压缩相当部分背景依赖**。

需要承认：单药“效应为0”不等于药物“剂量为0”。不能未经论证强加 h(u,0)=0，因为无可测单药效应的剂量仍可能在组合中起作用。相同或近似 u/v 对应不同原始剂量、背景或组合效应，是这个压缩假设最重要的潜在失败。

训练模型的每个 episode 也必须用它自己的合法 witness 参考构造 u/v；不能为了训练方便改用 target attached mono，造成训练与部署特征意义不同。训练角色的标签属于共享历史、所有比较器相同；当前episode的 witness 标签另按两 bundles计费。

## 必要普通比较：同合法信息，不制造弱对照

| 模型 | 最简定义及作用 |
| --- | --- |
| M_B：paid-reference Bliss | B(u,v)，无target反馈；诊断单药已解释多少，不作为唯一竞争者 |
| M_E：effect residual | 上述共享 h_p(u,v)，使用已购mono坐标；普通 spline/ridge，不是新算子 |
| M_D：dose residual | B(u,v)+g_p(log-doseA,log-doseB)，g与h用相同基函数数/正则选择预算，含零剂量时统一预定变换；分离effect坐标与普通剂量平面 |
| M_R：cell-specific refit | 在普通共享残差模型上用两个 paid witness bundles 的残差估一个cell/plate局部校准项，例如带训练先验惩罚的一维offset；不得用未购AB refit，也不从两条边无依据识别每个药的独立delta |
| M_S：strong direct | 使用相同历史训练标签、target pair/raw doses、u/v、witness身份及全部合法付费mono/组合outputs的预定编码；固定常规模型族与validation预算，允许普通refit/在线更新；不能只给它剂量或freeze其反馈 |
| M_mix：简单混合 | M_E与最强ordinary预测器的一个预先固定混合或仅validation选有限权重，完整计入预算 |

M_E 可以选择不利用某些已购组合outputs，但不能独占额外信息；M_S/M_R必须可用它们。所有 arms 的输入权限与score keys相同。若设置用于归因的“只更新mono、冻结interaction”消融，仍按两个完整 bundles收费，不得把人工隐藏部分已购信息写成真实查询更省。

M_R 的一维offset是普通校准，不是FSI或真实normalization原因的认证。可分别在 M_D/M_E 上加相同offset，防止把坐标与局部refit机会混淆；若预算只能留一种，选validation最强普通基线，不能按test挑。更大因子结构需要更多数据支持，不应为本最小门发明。

M_S 可以是固定Ridge/boosted tree/ExtraTrees等有限直接族；root需在开值前写清付费bundle的完整编码、结构缺失mask、训练/validation处理及预算。高容量不是必须取胜，有限比较失败也不证明所有坐标函数不存在；结论始终限定该注册family。相同trial机会不等相同计算，实际训练/预测时间必须计费。

## Forecast 与 recommendation：两种用途分别可失败

预测primary应是原始 normalized inhibition 的 MAE，先在一个 MASTER 内按 target pair/episode、再按剂量等权，最后 MASTER 等权；避免49点或重复stock/plate支配结论。每screen/plate结构的权重在完整协议固定。不要为方便把未校准抑制值改为死亡概率或Brier。

推荐不能只在AB内挑最大剂量再称 drug discovery。一个不额外打开target mono的实用代理是**相对已付费单药参考的组合增益**：

`U_e(a)=Y_AB,e(a)−max{u_e(dA),v_e(dB)}`。

在metadata固定的合法剂量候选中，模型按 `Yhat−max(u,v)` 推荐一个点或固定小k（完整协议选定一种），seal后只开目标组合y，用上式计算推荐平均utility及相对同候选oracle的regret。这样只用已付费参考，既不读目标附带mono也不调用预计算HSA/Bliss表。它是**paid-reference功能增益**，不是已认证临床协同或靶向机制，参考噪声/跨矩阵transport必须说明。若root坚持仅预测绝对组合抑制，也应加入最大剂量/固定角点推荐，先证明非平凡headroom；无headroom就停止推荐主张，不换有利utility续关。

可预注册的实用margin提议：normalized inhibition MAE至少降低0.02且相对>=10%；推荐regret也至少降低0.02且相对>=10%，均相对最强预定ordinary comparator，cluster敏感性下界>0。0.02是2个百分点的源内实用代理，**不是已测assay噪声或临床阈值**；完整协议可在任何新数值前给出更有根据的固定margin，但不能开值后降低。预测通过而推荐失败，只能保留forecast；要支撑后续决策组件需两者均达到其门槛。具体k、dose restrictions、样本功效与comparison correction仍须root完整协议冻结。

这一步目前仍是固定witness的离线结构检验，不是adaptive agent；M_R得到反馈后的改善不是程序继承。即使全过，也先只支持一种功能表征/运输偏置的非平凡源内实证，不自动world/agent/RSI。

## Support 与 plateau：可以预注册，但别把诊断写成因果定理

三层必须分开：

1. **dose/reference资格**：target每个剂量都有来自两个已购non-target witnesses的同stock/plate、实际drugID与精确µM observed reference。只看metadata选择witness，看到无效mono不换第二优witness救结果。输入缺失时共同abstain并统计原冻结panel的coverage。
2. **effect支持**：用训练角色的合法paid(u,v)固定pair-specific支持集（例如闭合convex hull），在test target打开前，以当前已购(u,v)标记插值/外推。primary不要后验只保留容易支持点；统一预测所有合格dose-supported点，报告预定support strata。若打算用覆盖门槛拒绝用途结论，必须开值前写定，不根据target表现选择阈值。
3. **plateau/坐标折叠诊断**：只用 paid(u,v) 与raw dose定义同一episode内的近坐标候选对，例如max effect差<=0.02且某剂量相差>=1 decade；阈值是预定diagnostic，并非噪声推断。seal后报告其组合响应差、M_E与M_D/M_S误差差，按MASTER聚合。真实重复资格若足够，再用已授权训练重复估噪声；不得用held-out target选择plateau cutoff。

近似相同坐标上单个不同Y不能反驳所有任意陡峭h，重复噪声和潜在真实效应也可能不同。可以否定的是**当前固定平滑transport模型的实用充分性**，或在真实独立重复/明确误差界下拒绝所测观测坐标的确定性压缩；不要夸大成一般生物可识别性定理。若原始dose在plateau层显著有用，应保留该失败，不能加dose进h后继续称效应坐标已足够。

同plate并不自动等于相同参照读数：公开C-well附带mono字段的来源仍需审计。没有raw DMSO/blank/control luminosity，不把任何剩余误差归因为仪器归一化，也不要求为这个静态功能机会补造早期RNA。

## 可以推进与必须停止的内容

完成协议后若有足够独立MASTER、有效paid-reference覆盖及共同未购target支持，可做一次普通机会门；它比继续为FSI/CCIP添模块更值得。事先保存角色/episode/witness选择、输入权限、所有预测和abstention，再开目标；完整同信息反馈/计算预算、eligibility规则、样本权重和code须经独立实际交叉。

若资格不足、支持退化、直接/剂量/refit或简单混合追平，停止精确effect-transport配置作为核心依据，保留数据及负结果。若只有拟合/forecast小正差，不到实用或推荐门槛，也不加agent/RSI救关。若双用途门成立，仍需新独立功能任务及world/agent/继承/联合/psi1>psi0分离测试；本阶段既没有这些收益也没有新操作。

此前过强triangle表述在本新稿明确修正；旧冻结记录不改。没有用“通用NN也能表示”拒绝此结构，因为相同表达力不否定良好有限样本偏置。我们要测的是一个简单、可失败的真实功能压缩性质，而不是给已知kernel/spline换名字。
