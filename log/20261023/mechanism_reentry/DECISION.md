# 新核心未通过：学习更新目标已有直接先例，存活场限制与功能数据尚未闭合

2026-10-23。完整目标 **ACTIVE / NOT_ACHIEVED**；本轮 **PROGRESS**，非全局阻塞。决策 **NONE / NO_NEW_CORE_GO**。没有新生物训练结果、世界模型必要性、智能体优势、继承、联合或递归收益。

实际新增四项证据：

1. **DiscoRL已直接学习更新目标与预测语义。** Nature2025原Methods及官方pinned实现认证了learnedtarget→stop-gradient/KLinnerupdate→outerreturnmeta-learning，不仅是学习率/超参数搜索。以后“改变如何从反馈学习”必须与它及普通向量更新器正面比较。改进U不自动等于改进G；固定Adam也不自动否定所有可学习的改进策略。
2. **执行并独立重建了一个有限操作边界。** critic的二维detached-target场可非固定光滑标量损失的梯度，普通stopgrad目标损失/状态向量优化器却能精确实现。根以有理数独立重建导数和8个point/step更新。它是数学操作审计，不是细胞性能、作者RL复现或新算法；只停止该狭窄新颖性区别。
3. **新细胞方法给出了具体观测限制与强对照。** ARTEMIS用采集细胞数近似群体规模、用下一时点表达偏差构造死亡先验；不能当独立存活反馈。scBalFlow已有强弱响应路由。考虑的“冻结transport、更新survival”可由普通同约束推断实现；潜在贡献应在可验证的生物限制或有限资源优势。终末比例/总活性不能区分转移、出生与死亡；没有把另一份静态RNA+活性数据拼成该缺失测量桥。
4. **完成一个明确新来源的有限核查并停止当前入口。** 2025ALL597设计真实，公开RNA已认证；根实际取得官方补充包，检查8工作簿row1text/维度，并检查两个指定SciLifeLabDOI元数据，仍未认证个体response→RNAjoin。多数schema是汇总/DEG/DMC/pathway；第二DOI虽同标题，实际描述55例DNAm/onrequest/files=[]。停止该具体数值启动，未宣称所有数据不公开。无PDF读取、数值响应/表达矩阵拟合或外部联系。

三方先独立seal后实际交叉，另存原意见、最强反对与回复。实际修正包括：ARTEMIS的K(t)/K(z,t)记号不足以判断实现只依赖时间；普通方法家族不是否决理由；必须区别数学操作相同与可验证生物限制；最小反证先观察处理前标记状态在药物/对照下的迁移，并处理分裂/死亡混淆或降低到净增长结论。source对新schema另封增补，未改原稿。详见ROOT_REVIEW.md及各角色CROSS/SCHEMA_ADDENDUM。

下一阶段不加编辑器/智能体层级，不重新搜同一缺失映射，不以新随机划分重置已曝标签。先提出一项明确的新限制：用何种真实反馈、纠正强普通方法的哪种重复错误、为何可能在样本或总成本上更有效。允许在已曝source上进行诚实的探索性新机制证伪，不要求完整RSI数据齐备才允许任何研究；但当前没有这样的可执行候选，因此不运行旧菜单或泛learned-target训练来充当突破。真正候选仍须对强直接、重训练、持续/主动学习、简单混合、普通learned-target/vectoroptimizer与等预算程序搜索公平比较，并分别验证world/agent/inheritance/joint，最后再比较同起点/同经验/同总成本G1/G0后代效果。

成本/失败见COST_LEDGER.json与EXECUTION_FAILURES.md。代码research/mechanism_reentry_20261023/，证据均在本目录；既有61/166/48/84文件checkpoint与当前独立seals在VERIFICATION.json实际重算。局部字节完整性不能修复历史全局provenance drift。完整原始目标没有缩减或达成。
