# LIST小表身份核查：900行不是900个独立药序实验

2026-10-22。两个事前指定Git blobs取得成功并通过Git SHA和byte长度校验；
**含响应的CSV已下载并由隔离脚本解码，但没有向研究者导出Growth值、分布、
预测或任何性能结果。** 本轮只确认schema/identity，不认证实测来源或独立重复。

## 实际结果

`growth_data.csv`共901行含表头、每行5列。第一阶段只导出事前允许的
`Time,Dose_A,Dose_B,Growth`，第5列被遮蔽。支持方另取的固定源码
`Calculation.m`第23行明确规定第5列是`Dosing_Type`，随后单独离线修订才
允许核对该列与三种标签，没有重新请求或开放Growth。

| 身份事实 | 结果 | 限定 |
|---|---:|---|
| 数据行数 | 900 | 不等于900个独立实验或query action。 |
| A+B / A-B / B-A行数 | 各300 | 是字面类别，实际药名/洗脱/切换未认证。 |
| 名义dose-pair/type组 | 75，三类各25 | 无culture/colony/run ID，不认证连续个体轨迹。 |
| Time值并集数 | 6 | 数值和物理单位没有导出/认证。 |
| 每名义组不同Time数 | 均4 | 不说明每时点是同菌落或独立破坏性采样。 |
| 唯一Time/dose/type键 | 300 | 另外600行与已有身份键重复；没有删除。 |
| body数值型cell/空cell | 3600 / 0 | 仅类型/空值旗标计数，非响应数值或可靠性验证。 |

重复键可能来自实测重复、技术重复、复制示例或其他过程；**现有来源不能区分**。
没有replicate标识，不能把平均每键三行报告为三个独立生物重复。表头没有真实药名、
strain、run、chamber、colony、replicate、switch/lag或环境键；这只描述本CSV，
不是证明论文从未记录它们。源码只按dose/type/time聚合，也不能补出这些键。

`Supplementary File (Multiplexing control).xlsx`有3个sheet：

- `512 Seqeunce Control`：556×35，5,120个公式cell。
- `Input Combination Control`：545×11，4,608个公式cell。
- `Chamber Control`：593×23，无公式cell。

只导出sheet名、维度、类型计数及首行白名单header（`Chamber Control`）。
它是公开GUI/valve配置线索；未扫描所有文字寻找隐藏表头，未导出单元格行值，
因此不把此schema审计说成已完整解读该workbook，也不认证它与CSV响应的join。

## 决定

**TABLE_IDENTITY_PROJECTED / REAL_ACTION_STATE_FUNCTION_JOIN_NOT_ESTABLISHED。**
不能把9个静态形态示例、这一个generic A/B表、512腔控制配置或两个不同图像版本
拼接成世界模型或RSI数据集。不拟合任何模型，也不消费Growth来比较不知实际动作的
演示条件。合法跨实验研究agent并不要求同菌落内自适应分支；此处缺的是实际动作、
终点来源与独立实验单位，而不是强加控制任务条件。

仍未认证CSV究竟是实测还是演示数据；不按其规则网格擅断synthetic。世界模型、
agent、普通重训练、持续学习、主动学习、混合、程序搜索、继承及RSI均NOT_TESTED。
独立完整数据可得性证据另见`../title_registry_audit/version_followup/REPORT.md`。

## 可复现验证和成本

两次HTTP200，无重试/redirect：API body共2,820,980 bytes，其中固定blob内容
分别17,137和2,029,932 bytes；API JSON/base64体积不是源文件体积。原始body、
status、UTC和SHA256均在`NETWORK.json`和`sealed_sources/`保留。
Git blobs为`4197e4588383cd2a2441704f758f2533a3abe6bf`及
`0dc02c1c85a7d10d6783a361d2ae41f91d9bb685`。

第一阶段3个不同export检查通过：数值/未知header遮蔽、重复header位置保留、
data-row数值不进入schema输出。离线身份阶段5个检查通过：重复行计数保留、
改变Growth不改变投影、错误schema/非有限identity/未知type各拒绝。
`SCHEMA.json`、`IDENTITY.json`分别记录执行代码SHA256和来源SHA256。
这些是信息边界/来源验证，不能当药物效用、独立培养或模型准确性证据。

代码仅位于`research/antibiotic_schedule_qualification_20261022/`，没有执行
第三方MATLAB源码，没有修改原始来源，没有图像下载或DeepSeek调用。
