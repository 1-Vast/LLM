# H_FI v1执行前澄清

2026-10-29，fresh初判后、任何本轮效果读取前追加。原protocol_hfi_v1.md不改写；本文件与原稿一同冻结。下列操作定义优先于原稿含糊处，未改变科学H/门槛/菜单来源或增大候选族。

1. 顺序是先在全部metadata中为每(project,cell,drug)选最小字典序ref，保留该ref的正有限剂量；再汇总project2这些已选ref的每drug可用剂量集合，取距.1µM最近的剂量；再筛完整11列cell。距离由Decimal局部精度50计算abs(ln(q/.1))，正数下与绝对log10距离同序；并列取小q，不用响应和未选ref剂量。
2. PAV先按不同x升序合并相同值，各组权重w为个数、正例总数s、x加权总和h=w*x。相邻块若s_left/w_left > s_right/w_right则相加w/s/h；直到不违背。块概率p=s/w，块中心c=h/w。预测按(c,p)作普通线性插值、界外取端点，一块时常数；降序模型先将全部x变为-x再执行相同定义。所有求和按cellID排序输入的确定顺序和float64，不clip概率以修结果。
3. OOF blind在每折只用该折训练部分的两个目标empirical rates，不读该折验证标签来估rate；最终blind用全训练两目标rate，p>=.5。它付相同q部署动作并可记录收到的值，但预测函数完全忽略它。最终条件模型各(j,t)按完整OOF0/1损失选择，同一族和顺序用于reference/direct。
4. 五个inner fold的训练部分与验证部分必须都非空，否则全次设计不足、不改fold/补seed。训练或开发角色为空也停止。OOF输出顺序固定训练cellID字典序，模型选择损失按整数错误总数比较，避免浮点均值的假并列。三元组m也按双标签错误整数总数差比较；最大整数m<=0便停止开发评价。
5. bootstrap用numpy.random.Generator(numpy.random.PCG64(20261029))，integers(0,n_dev,size=(1999,n_dev))，相同索引用于三个配对差，quantile(.025, method='linear')。开发cell按ID字典序。均值/区间是该固定开发ID分布组成敏感性；不能称生物总体置信或强Bayes direct最优下界。主H仅限冻结菜单、模型族与预算的优势工作门。
6. 训练全11列不仅用于最终拟合，还参与probe/目标选择，其读取坐标和选择计算成本全部报告。reference固定任务通常需3列/direct2列的最少拟合需求，另与实际本次全11列搜索费用同时列出；不能用只算3列的账本宣传本次总成本。双直接动作2坐标是不同预算的零导出标签错误参照，不与1坐标策略作同成本优势主张。
7. 资格来源独立重建metadata已完成；glossary将y定义为抑制导出、yhat为拟合，浓度µM。研究级72h/CTG来源与glossary fluorescence字样冲突、实际版本、source-well/培养/控制/重复仍未逐键认证。本试验若准入仅同筛处理后y的开发回放，不是噪声真值、真实孔价或药理机制试验。旧化学支持审计的独立MMP映射部分不由此次metadata重建补齐。
