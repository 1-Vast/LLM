# FF设计重建代码独立复核

2026-10-22。阅读 `research/almanac_feedback_pilot_20261022/design.py`、`root/DESIGN_SUMMARY.json`；另用 `assay_check_design.py` 只验证派生 `DESIGN_TASKS.json`，结果 `DESIGN_METADATA_CHECK.json`。未打开archive、原始CSV或响应；不是独立原始行审计。

结论：**支持当前方向规范化、单药重排和按元数据选择重复代表的实现**。没有发现需要阻止分割合同冻结的代码问题。

- 药轴按(NSC,SAMPLE)字符串排序，两药方向相反时同步交换浓度坐标；pair采用相同排序。字符串字典序不等于数值大小，但只需一致canonical排序，因此正确。
- 每轴按Decimal浓度排序，组合行按第一药外循环、第二药内循环重新排序。每轴3level且9个唯一坐标保证完整笛卡尔网格；高高角因此最后索引8。单药按canonical药物、同一真实浓度字符串、单位M重排为第一药3条/第二药3条，每项唯一匹配。因此可从单药位置与组合坐标确定合法单药预期。
- 原代码没有显式检查三个不同字符串是否代表同一数值，但本次派生metadata检查证明所有task每轴3个**不同正Decimal值**，升序；pair均不同药，9组合行/6单药行唯一且互不重叠；chosen任务间组合行引用不重复。当前数据不存在该潜在别名问题，无需为假设风险重建全部数据。
- 重复键为cell+canonical样本药对+实际剂量字符串，选择组合最早源行的完整网格，不看响应、不跨来源混合单药。1,844个两份组被保留一份，其他来源首行记录下来；后续响应读取必须只允许chosen组合/单药行，不能把丢弃重复重新当训练或额外feedback。
- 148,681个chosen任务，1,338,129个不同组合行引用，派生检查全部通过。chosen只含12,800个physical plate键；原150,525组共有12,859键，差异来自被丢弃重复出现，二者不矛盾。

**接受对独立稿的实质更正**：此前全ALMANAC的plate跨细胞统计不能套用FF精确3×3资格集。此次12,859个完整(lab,study,plate)键均只含一个cell，60个组件均singleton；chosen元数据也一致。因而本任务按cell分割自然没有所识别physical plate的跨cell共享，不再要求剔除一个不存在的plate交集。仍不把singleton plate证明成独立生物学重复；study层共同来源和support/query同plate校准是主张限制。

hash顺序20fit+10tune+10dev+10selection+10later可接受，后20cell不解码；hash盐、完整cell名单、分割文件与代码hash应冻结。pair-dose资格仅按metadata；推荐主任务使用全部20fit+10tune都有同样pair-dose的公共目录，简化knownpair及调参比较；若减少目录太多，可以预先选最低覆盖条件，但不能响应后改。

fit内仿真新细胞会少一个source，若公共目录要求20fit全覆盖，inner source有19cell属于正常，不该再套用20覆盖门槛导致空集。覆盖资格针对外层冻结目录，inner fold须明确用可用其余19cell，并按cell分隔标签。10tune只选超参/菜单；10dev只跑冻结pilot；selection/later尚不解码。若dev结果用于选择新算法，则dev已成为开发集，之后不可称未见测试。

成功层级澄清：当前无候选新机制，最强普通B1超过最强普通B0足以建立**反馈价值**；无需与自己比较。仅当要主张某个更新机制优于普通方法时，才要求其胜普通B1。若普通B1解释全部增益，就正向记录反馈价值，同时不晋升新算法或RSI。这也接受skeptic在实际交流中的澄清。
