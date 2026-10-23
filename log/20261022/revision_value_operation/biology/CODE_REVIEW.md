# S4功能增量实现：响应前代码审查

2026-10-22。实际读取cdk_functional_increment/PROTOCOL.md与run.py/test_run.py；未运行reader、未开S4、未读取prepared数值。**REVISE：源rank构造存在一处必须修复的协议不一致，其余范围可执行。** 未修改root代码。

predict目前 `target=rank_targets(labels[train])` 对整个challenge训练池排序，之后才减同condition均值。协议要求源condition内部percentile ranks；二者不等价。跨condition标签插入改变同组秩间距，因而即使减组均值也引入跨condition数值比较。应逐训练condition分别调用rank_targets再放回source位置；n1为0.5，所有有样本组平均均0.5。没有该条件源样本时预测baseline采用pooled source rank均值并记录fallback。

现测试只核global rank_targets和held labels不影响预测，没有验证condition内构造。建议新增有意义合成：各condition内保持顺序、对不同condition施加不同严格单调变换（使全局交错顺序改变），预测应不变；以及目标condition源n1残差为0。这样可直接抓到本次bug，而不是照抄代码自证。

q为每样本identity减源同组feature均值，qKq'对称中心化，对test只通过源成员计算均值，test pair不互相污染；kernel训练子矩阵不含test特征影响尺度。Early/Middle Grams分别使用合法stage、均分Early+Middle，End不输入，合成End NaN不变检查有意义。固定lambda1主/.1与10敏感不选择，符合小样本最简方案；线性Hellinger Gram替代此前建议的RBF是预先明确普通模型选择，合法。

source S4 reader仅B身份与选中resistant行C/D响应，vehicle不解码结果；公式/未知身份/重复identity/非正非有限拒绝，N/A和空保留；source hash与prepared hash验证存在。sharedStrings XML物理解析会包含全表字符串，不等于解码vehicle数值。实际原始curve/well、单位、缺失机制未知的边界保持。

预先将truth exact ties排除并计数，而非我的早先tie=.5建议，是可接受的另一合法合同；它没有ordering target，关键是开值前明确、原始数目和不可估condition保留。预测tie tolerance1e−12已固定，不按值调。source少于2时当前evaluate直接continue：建议为该pair明确记录不可估原因/源数，而不是静默不出现；challenge没有可评pairs时macro None，成功门不得视通过。

run保存全部records、逐pair truth/prediction/source/fallback、condition宏平均，足以独立审计；目前没有自动success字段并非错误，结果解释须逐challenge核lambda1同时优于Early与0.5、两个敏感lambda维持方向，不能事后挑一个。

统计边界：每条件3culture留2后只有1同condition源，实质检验其他condition序数结构迁移；互重叠pairs不独立、两个challenge不独立祖先，且接近IC50的顺序测量误差未知。不报告显著性合理。若修复rank并补对应合成检查，可freeze后一次执行功能探索；任何结果不回写组成STOP、不声称WM/agent/RSI。
