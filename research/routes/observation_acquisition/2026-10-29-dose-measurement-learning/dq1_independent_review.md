# DQ1 独立重写的后续执行及审阅

2026-10-29。本报告作者为后续执行/审查代理 dq1_source_check_completion；此前 fresh 独立作者写了 dq1_independent_check.py，句柄消失、未留结果，不能称此前执行完成。本次未改独立脚本，在读 root 的 audit_dq1.py、dq1_result.json 前，审查脚本并真正执行一次，结果先落盘。后续比较阶段已看到 root 实现，本报告不冒称新的盲写作者或独立科学挑战。requested Sol/medium；effective model、usage、费用无元数据，均 unknown。0 新代理。

执行前结果文件不存在。实际子进程命令：

`D:\anaconda\envs\maestro\python.exe D:\MAESTRO\research\2026-10-29-dose-measurement-learning\dq1_independent_check.py`

由 PowerShell Start-Process -WindowStyle Hidden 启动，PID 2328，exit 0；100ms 轮询 TotalProcessorTime、PeakWorkingSet64，CPU>120s / RAM>1GiB / wall>120s 则终止。执行器 wall 1.0441876s，采样 peak working set 37,679,104 bytes；脚本内部 CPU 0.515625s、wall 0.5723977000016021s。轮询是观测加终止护栏，不是 OS 硬内存配额；采样峰值不能当完整私有提交内存证明。结果 12,418 bytes，16 arithmetic packets，0 conflict examples，未触及20MB输出限额。无网络/API/GPU/安装/作者R代码执行，无科学性能 run。

独立脚本先校验指定ZIP SHA256，再只扫描指定member前20000数据行。标准csv解释器必然短暂分词整行，然后只投影14允许字段；未对 yhat/IC50/AUC/组合 inhibition 做数值解析、保留或标签使用。只读身份/dose/y；未访问其他功能数据、PRISM24Q2、CTRP、sealed、confirmation或.env。

保留此前作者披露的顺序偏差：此前曾先看header及前两行允许字段投影，之后才核hash。本次hash-gated执行不能抹去那次hash-before-inspection违例，也不能把已暴露前缀当新确认集。

## 逐字段比较

root元数据 protocol_sha256、script_sha256 与当前对应文件重新计算一致。root columns 与独立ALLOWED字段集合一致（顺序无科学意义）。

| root字段 | root值 | 独立结果 |
|---|---|---|
| raw_sha256 | e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259 | 一致 |
| member | combo_well_stats_GDSC_007_05May22.csv | 一致 |
| fixed_prefix_rows | 20000 | 一致 |
| response_fields_examined | 40000 | 一致 |
| invalid_nonfinite_or_negative_dose_appearances | 0 | 一致 |
| zero_dose_appearances | 0 | 一致 |
| invalid_or_nonfinite_y_appearances | 0 | 一致 |
| y_appearances_outside_zero_one | 0 | 一致 |
| unique_exported_keys | 5924 | 一致 |
| repeated_exported_keys | 5923 | 一致 |
| keys_with_multiple_raw_y_strings | 0 | 一致 |
| keys_with_multiple_finite_numeric_y | 0 | 一致 |
| reference_identity_mapping_conflicts | 0 | 一致 |
| first_conflict_keys_lexicographic | [] | 一致 |
| exported_key_usable_for_retrospective_development | True | 一致 |

root csv_row_bytes_include_fitted_fields=true、fitted_fields_retained_or_numerically_parsed=[] 与独立流式解析边界一致；first_response_exposure 与独立 qualification.scope 均确认开发暴露。numeric_consistency_tolerance 两实现均为 exact Decimal equality、零容差、不舍入/平均/clip。qualification_scope 与独立 supports/does_not_support 一致，支持导出层级确定观测，不支持来源测量独立性。seconds 是各自运行时间，root 0.469s，独立内部wall 0.5723977000016021s，非应当相等的科学输出。

另逐键比较 root dq1_arithmetic_packet.json 与独立 packets：16键集合相同，各键appearance、raw字符串集合、invalid_y数量全部一致。不能声称按数组索引完全相同：root按浓度Decimal数值排序，独立按序列化浓度文本字典序排序，38906_L56 的10与3.16255534次序相反。本次选入键集合仍相同。协议写“键字典序”但浓度类型为Decimal，排序约定存在歧义；独立明确采用文本顺序，均非按响应选样，不静默修正root历史。

独立额外结果：35 plate、19 master cell、876 ref，ref映射与master→cell_id冲突均0；146个(project,cell,drug_id)组含多个ref，不能自动跨ref合并。lib1/lib2各2998/2926键，跨侧共享0；不能由零交集推断生物独立。

## 实现偏差与实际影响

独立eligible额外排除[0,1]外y；协议只要求记录不clip，不能把范围外值自动否决。本次范围外0，故5924键结论不受影响；未来不能照此筛选。脚本理论最多可给16 packets另加16 conflict_examples，可能超协议最多16算术packet；本次冲突0，实际只16，未发生超限。独立missing/nonfinite分类比root更细；本次所有40000浓度及y均有限，差异无实际影响。root只在合法dose后计y与mapping，独立在其前计，且ref映射范围更严格；本次非法dose0且映射冲突0，输出一致不能验证所有病理输入下等价。

## 限定源码语义复核

仅定向读取缓存 CancerRxGene_gdscmatrixanalyser/CancerRxGene-gdscmatrixanalyser-00c04b4/R/classes.R:313–350、402–410，R/matrix_well_stats.R:48–66，以及 CancerRxGene_gdscIC50/CancerRxGene-gdscIC50-34d8422/R/nlme_fit_prep.R:779–824；未执行R。

classes.R把S单药layout按POSITION关联强度，以NC1+B算viability并trim至[0,1]，传MASTER_CELL_ID及BARCODE+lib_drug至prepNlmeData。后者把normalized_intensity重命名y，再y=1-y，所以该旧源码支持“导出y为inhibition-like规范化响应”的解释。matrix_well_stats.R的剂量join前移除单药POSITION、CL，因此组合行POSITION不能还原单药源well。仅凭这些旧缓存片段不能认证实际ZIP生成版本、完整导出链、原始仪器well或培养独立。

结论：本次独立实际执行复现5924确定同筛导出键（5923重复键）、零y/身份冲突，支持另行冻结的同筛导出响应开发预测资格。不能由重复一致推测噪声均值、独立培养、跨筛迁移或方法优势；缺RNA/正交读出不能自动否决这一有限预测任务。未选择阳性子集、拟合模型或晋升科学结论。独立源码语义字段原由此前作者写入，本次限定行阅读后核对，不认证实际生成版本。
