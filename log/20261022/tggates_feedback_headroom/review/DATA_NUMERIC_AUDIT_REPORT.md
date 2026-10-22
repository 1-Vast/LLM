# 独立source/dev转换与基础数值复核

2026-10-22。收到root冻结/执行授权后，按已冻data_independent_conversion.py和DATA_CONVERSION_AUDIT_PROTOCOL执行一次真实独立raw转换；先封DATA_INDEPENDENT_NUMERIC.json，SHA721cba13a1df7a16299ec084ef16c7c3c0f9860bbbfcddedca4ad575830ccfac，再读root数字比较。最初原始矩阵/功能转换不依赖root预测或聚合结果。

独立csv.reader+Decimal扫描5,986rows，严格先查source/dev预列key、核10identity字段，再读两assay：186records/372finitevalues，source288/development84。later168prelistedassay及所有controls均0访问/0cast。93condition×2assay均值/ddof1SD由Decimal独立算得；169records至少一assay超过0..100范围，原值保留，没有clip/logit/对照重归一化。原ZIP51,898bytes，SHAf790d45a5cb40e653bb3dada1aa2f40bfdd26b8bd1f7fdb86decc9c908c9cb14；member375,225uncompressedbytes/51,702compressedbytes。

比较2,792checks PASS/0mismatch：1,244exact身份/计数/flag/hash检查；1,548numeric checks用绝对1e-12容忍，最大差2.220446049250313e-16。372normalizedvalues、全部rootpublishedpercent审计值/flags、93conditionaggregates的means/SD和4种基本开发DNA预测/MAE均吻合。只对这4种基础DNA baseline独立复算，不因此声称ridge/KRR/search实现、sourceCV选择或bootstrap已独立复现。

| 开发DNA baseline | 独立MAE |
|---|---:|
| constant0.85 |0.11657142857142858|
| sourceHighmedian |0.02475|
| Middlecopy |0.023357142857142858|
| sourceMedian(High−Middle)offset |0.023928571428571428|

按冻结0.02绝对改善要求，Middlecopy的这个开发误差只留下约0.00335714的允许候选MAE：未来候选要改善严格超过0.02，须把MAE从0.02335714降到严格小于0.00335714（约85.6%以上减少）。这只是对已经固定门的算术解读，不能据此改门或声称达不到。该小幅headroom通过只允许另冻RNApilot；不建立RNA/world/agent价值。7开发proxygroups小样本、目录预筛与nameproxy边界保留，开发最优family选择不是独立确认。

失败完整保留：第一次post-seal比较脚本误用projection键audit，KeyError/exit1；失败脚本data_numeric_comparison_failed_v1.py及DATA_NUMERIC_COMPARISON_FAILURE_V1.json保留。改为实际numeric_exposure_records后只重跑比较，不修改原数字、门、分区或已冻converter，不再次转换raw。独立转换本身exit0，没有数值资格失败。

资源：独立真实raw转换1逻辑pass，比较期间无新增数字转换，2次比较尝试；newHTTP0、CEL0、fit0、biologicalobservations0。这是同一批source/dev观测的第二次计算核对，不是第二次湿实验、独立重复或新confirmation。所有新增代码/测试在research/tggates_feedback_headroom_20261022，协议、数字seal、比较与失败在本phase的review。
