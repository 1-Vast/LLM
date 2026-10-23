# 补表身份结果后的反方增补

2026-10-22。阅读范围仅 `WORKBOOK_HEADERS.json` 与 `IDENTITIES.json`，没有打开xlsx、原始XML或数值payload。首次将两个JSON直接长输出导致截断，随后只选择sheet2的A/B/U/V首4行及summary补读。未新增生物数值访问；数据结构计数属于metadata，不是功能值。

## 改变的判断

原先“也许只有最高剂量fitness”的风险已获得明确的相反结构证据。作者关联xlsx的 `TableS1 - Cpd via info` 有五剂量列：K:O为1—10000nM relative intensity，P:T为同五剂量Raw signal，J为relative intensity 0。另有C:I的拟合参数与摘要列，U为端点，V为Effect。必须区分这三类信息。

IDENTITIES summary认证144个drug身份、Jurkat432行，三个指定端点Confluency/Cytotoxicity/Metabolic activity，另有24行primary T cells四种状态，应单列而非混作主屏重复。A/B/U身份组合无重复，J:T结构均存在、无公式。因此可以将当前状态从“未认证是否存在多剂量功能列”推进为“已认证作者补表具有完整多剂量功能列结构和明确条件身份入口”。这值得继续有范围的资格工作，不能再泛称只有单点摘要。

## 没有改变的判断

1. **Raw signal是列名，不是完整测量溯源。** 无Excel公式只说明保存为值，不排除在上游经过平滑、均值、归一化、插补或导出。当前未认证逐孔原始值/独立重复、实际图像时间汇总、plate/control键及校正公式。不同drug×cell×assay键也不等于独立生物重复。
2. **结构完整不等于值合格。** 尚未检查有限性、符号、尺度、常数值、饱和、动态范围、离群、相对值与raw的对应关系。存在payload不排除无效数值或占位；没有公式不保证真实性或未使用全剂量信息。
3. **分子—功能连接仍需另认证。** 药名/剂量/背景/protocol的可认证condition-level映射足以限定条件均值预测，不强求same-well；目前只完成了功能表内部身份结构，未完成真实分子文件条件连接。same-well与个体残差等更细主张仍不得提出。
4. **噪声和应用价值仍未建立。** 作者48个DMSO的蛋白组19% CoV不可借作这些端点的噪声。432行不是432独立药物任务，24个primary行不是广泛跨背景验证。正文marginal fitness风险仍需先冻结后检验；尚无功能预测成绩、预算收益或药物决策效用。
5. **机制及RSI STOP不变。** 新数据结构不会改变旧shift估计与joint MAP的等价事实，也不建立世界模型、智能体、继承、联合或improved-improver。

## 暴露边界修订

首4行不能统称“仅headers，未见任何标签”：sheet2第2—4行已解码(+)-JQ-1的三个Effect字符串，分别为 `Confluency not affected`、`No Cytotoxicity`、`Metabolic activity not affected`。这是三个定性结果标签暴露，必须把(+)-JQ-1纳入开发暴露，不能分给未见药物的确认部分。没有见到其连续数值，不意味着该药完全未暴露。

同一首4行也包括表1药物身份/机制元数据，可能影响研究先验，但不应把它们假称为新增功能数值。任何分区应在进一步值/Effect读取前固定，并把其他已有文中具体机制曝光明确列入解释范围。禁止据这三条Effect的方向选择主端点、噪声门或通过条件。

## 下一步的窄许可与停止条件

继续认证列生成语义及分子条件连接，随后冻结独立数值开发协议和drug-level留出。若只能认证条件级汇总，可做条件级探索，明确无技术噪声分离；不用缺重复作为全面禁令。任何单点预算实验只允许揭露其合法局部测量，C:I和V不作低预算support；全剂量拟合曲线也不作独立实测target。

若后续发现P:T实为全曲线生成值而非局部测量，停止对应局部反馈合同或另立明确的拟合曲线任务；若分子条件不能可靠连接，停止当前跨模态合同；若功能信号在冻结的可支持误差/决策标准下没有可用价值，停止扩大该端点。上述均是条件式停止，不是对未开数值的预测结论。本次推荐为 **CONTINUE_SCOPED_QUALIFICATION；NO_MECHANISM_PROMOTION**。
