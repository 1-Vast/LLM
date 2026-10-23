# 开值前独立审查：高剂量分子增量信息

2026-10-22。只读START.md与NUMERICAL_PROTOCOL_DRAFT.md，以及先前已读功能试点/来源。未读新实现、peer意见或任何新分子数值。先前功能OOF已开发暴露，当前仍是同48药开发探索，不是新的独立确认。

## 结论

**可推进这个有限普通信息试点，但开值前需明确下述三个细节。** 无需先制造新WM机制，也不需要添加更多基线。九个程序、有限λ、source-only预处理及嵌套group验证足以支持当前问题：“高剂量功能已给定时，已发布高剂量蛋白表是否额外改善已发布中剂量功能预测”。其能给出有用正/负结果，但不能单靠改善分数建立世界模型、干预因果、智能体、传承或RSI。

## 需要具体修改的点

1. **数值贡献门应保留mask再添加value。** 草案要求“a value-containing direct program”优于M-mask-direct，范围不唯一；若用M-value-direct替换mask，即使提高也混合了删mask与加value两种变化，不能据此说隔离了数值贡献。最小固定修订为：M-both-direct相对M-mask-direct平均gain>0。两者都有同chemistry+functional+mask，唯一新增信息块为value；各自同λ菜单source-only选择是完整程序比较而非单个参数的纯效应，需如实解释。无需新增方法；若仍采用任一value-containing直接程序，要事先列明范围且只能称较弱的程序差异，不能说“isolate”。
2. **数值退化与kernel公式。** M-RBF要固定exp(−d²/h)或exp(−d²/(2h))，h为median positive source d²，不能在见结果后选；无value/mask特征时相应block贡献0，联合空时全1RBF经中心化变0。PC nonzeroeigenvalues需固定容差、PC分数标准化尺度与λ协方差归一化（N或N−1），才能完成宣称的primal/dual比较。任选一致简单约定即可，不需加新超参网格。
3. **残差嵌套须按每次实际train重建。** 不只外层source内crossfit：当inner验证某组时，残差训练target也必须在该inner-train集合里重新group-crossfit，不能复用外层source的crossfit残差，因为其中其他药的base模型可能已经读过本inner-heldout query。内层heldout残差不能参与训练；该heldout原始query只能用于候选风险。root实现前明确这点即可。所有缓存必须包含实际训练集合、程序与λ等相关键，不能为提速复用泄漏统计量。

## 已具备的公平条件

每个target都给10000nM功能，query固定10/100/1000nM；分子程序额外用同名高剂量蛋白向量，并承认完整profile成本。不能把低剂量蛋白、全曲线fit参数或其他剂量检测掩码免费加入。没有这些额外dose读取，是本合同中可验证的范围约束。

外层group全部移除、内层group全部移除；value eligibility/观测率/均值/std、mask变异、PCA、RBF带宽、中心化均在当前source训练集合算。全局identifier union仅作为存储索引，不必当作非法test信息；真正的目标专有蛋白不能改变source eligibility或标度。某个identifier来自已知target表但source均无观测时，必须对当前预测没有影响。目标missing数据用source均值，而非目标队列均值。

功能portfolio1—2相对分子portfolio3—9的源搜索机会不相等，草案已披露28对8配置，所以结果只能作信息探索。嵌套选择减少泄漏，不会让预算差自动消失。当前不主张equal-budgetsearch或agent优势，无需为这个pilot建立更大搜索控制。

M-PC没有chemistry，属于信息子集的普通baseline；它与直接线性条件形式等价的数值检查可证明实现一致，不是新世界模型贡献。Mask与value块固定加和并非学到了适应性程序。M-residual的固定Gaussianλ.1应保留这个限制，不拿它单独失败否定所有残差方法。

## 未来掩码与独立性的限制

ALL文件的行存在性及上游Normalized_Intensity_10000可能依赖全剂量处理，已经在协议中正确披露。即使仅读最后一列，也不能声称获得了纯10000nM独立实验检测掩码。所谓M-mask信息是**已发布processed-ALL行存在/有效性信息**；mask胜出不能叫细胞动力学贡献，更不能叫真实单次dose预算。数值胜出也仍可能部分继承上游处理依赖。

功能侧已归一化、时间window及分子侧处理之间是条件连接，不是同个体状态的因果干预链。48药/42scaffold组来自同Jurkat背景，不是42细胞世界或独立实验代数；同开发集再次试机制不会创造新的独立证据。先前(+)-JQ-1定性暴露和paper机制知识继续保留。

## 门与解释

95%bootstrap lower>0、两dose非负、逐个删前三绝对gain仍正，是预设开发allocation门；F-Gaussian总体MSE和value-vs-mask附加门能防弱portfolio参照，但并不形成临床效用门或生物噪声分离。只有一个事先主要portfolio比较时无需沿用前轮两个budget的Bonferroni；若同时试多种门后选一则不合规。

bootstrap仍仅对固定OOF配对损失group重采样，不重训。此次不能把过去48功能曲线和当前48蛋白profile说成零source成本；下载/解码/拟合时间和有限源任务数分别记账。不应预先承诺完整高维嵌套实现的运行时；可缓存同源集合的统计量但不改变算法。

若失败，STOP这个精确高dose增量合同往WM/agent/RSI扩张；保留任何窄信号，不借新端点、新λ、第二蛋白dose或保留96药救结果。若通过，只支持普通conditional-information候选，需要围绕同信息强直接基线的残差提出具体可证伪差异，并组织独立反方审查。没有理由把已停止的profileMAP/OED换名复活。

后续独立审计应重构冻结48药每行ID/drug/high-dose payload与missingness、验证source eligibility统计及预定OOF指标/门；不importroot模型，不假称独立重训所有模型。审计代码仅research/decrypte_molecular_audit_20261022/。此时尚未运行新数据实验。
