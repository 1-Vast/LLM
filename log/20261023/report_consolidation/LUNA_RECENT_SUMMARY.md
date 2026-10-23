# Luna近期研究报告整合（2026-10-22—23）

本整合按研究根目录最终 DECISION/REPORT 为准；纠错/复核晚于旧结果时，采用后续更正后的范围。跨日结论只能作为各自任务的局部证据，不能合并成通用更新器性能结论。

## 可保留的有限阳性与入口

- **真实功能反馈在限定任务中有用。** BeatAML 暴露开发回放中的普通协方差条件预测，用8个已测药物反馈后，MSE下降23.49%、top-3 regret下降15.07%；这是该任务中的普通预测效用，未证明外部验证、世界模型必要性或RSI。[2026-10-23 functional_state_sufficiency](../functional_state_sufficiency/DECISION.md)；[2026-10-23 functional_error_renewal](../functional_error_renewal/DECISION.md)。
- **decryptE 的一条功能反馈门通过。** 固定Jurkat处理协议下，揭示一个高剂量点的B1相对无药物功能信息基线降低约45% MSE，跨剂量方向均正、34/48药改善；但B2整套选择门未过，预测对象是公开代谢活性，不是细胞杀伤/临床效力。属于有限公开条目预测回放，不是新核心。[2026-10-22 decrypte_feedback_pilot](../../20261022/decrypte_feedback_pilot/DECISION.md)。
- **可继续的是受约束的数据/问题资格，不是已获性能。** distribution health 已冻结306个guide×line条件、102 guides、51个规范目标ID的资格与排除；该映射只保证数据成员/身份分组资格，不证明样本独立、功能性能或51个独立后续任务。可进入有限提取/目标处理协议；若合格后同信息常规模型吸收收益，应停止新世界/更新器主张。[distribution_health_qualification](../distribution_health_qualification/DECISION.md)。
- **另外两个真实公开数据入口仍需限定。** functional_state_sufficiency 保留“条件内状态分布是否补充均值摘要”的待检验小问题，实际未取数拟合；rechallenge_task 获得可用公开资产，但没有新更新操作；organoid_schedule_qualification 资格为有限历史后续批次功能预测任务，随后forecast明确停止固定ridge配置、保留普通FAC反馈效用。[state sufficiency](../functional_state_sufficiency/DECISION.md)；[rechallenge task](../rechallenge_task/DECISION.md)；[organoid qualification](../organoid_schedule_qualification/DECISION.md)；[organoid forecast](../organoid_schedule_forecast/DECISION.md)。

## 归并后的停止结果

- **候选更新规律未形成。** 2026-10-23多条功能更新、反馈充分性、状态转移/决策探针路线的最终判断一致是无获支持的新核心：固定组合/对角乘积、裸 resolvent、固定反馈规则、快照到控制捷径、特定继承方向等均因可识别性、任务闭合或强常规对照缺口而停止或要求改写。不能把多个形式相似的 STOP 相加成对整个方法族的否定。[functional_mechanism_frontier](../functional_mechanism_frontier/DECISION.md)；[update_law_search](../update_law_search/DECISION.md)；[functional_rule_discovery](../functional_rule_discovery/DECISION.md)；[grounded_feedback_renewal](../grounded_feedback_renewal/DECISION.md)。
- **有真实信号也可能止于特定依据。** CD14分层关联未过预设继续门，停止当前分层来源理由；它不证明CD14无效或所有条件效应为零。[functional_error_renewal](../functional_error_renewal/DECISION.md)。历史Norman重叠规则初始小幅正向结果被更简单的全局收缩超越，应保留初始数值、停止重叠特异优势主张。[functional_mechanism_frontier](../functional_mechanism_frontier/DECISION.md)。
- **任务级预测配置有明确STOP。** VUScope moving-midpoint配置的冻结预测门各项失败；常规直接/共享剂量方法有异质预测效用但非稳定通用胜者。[2026-10-23 VUScope](../vuscope_prefix_diagnostic/DECISION.md)。Organoid固定ridge配置被停止；可保留普通FAC反馈价值但不晋升更新机制。[organoid forecast](../organoid_schedule_forecast/DECISION.md)。
- **资格成功不等于效应结论。** HCC方案已认证但响应工作簿未取得；AML身份审查停止未认证功能预测入口；SRS前缀、regrowth配对等资格研究尚未形成可运行数值基准。[HCC](../hcc_task_qualification/DECISION.md)；[AML](../aml_identity_qualification/DECISION.md)；[SRS](../srs_prefix_qualification/DECISION.md)；[regrowth](../regrowth_data_qualification/DECISION.md)。

## 统一边界

World、agent、updater inheritance、joint benefit、以及 improved-improver RSI 均尚未建立。这里的有限功能预测阳性、身份/数据资格、审计通过和候选机制停止，均不替代相应共同起点、合法反馈和独立后续任务上的直接比较。全局研究目标仍 ACTIVE / NOT_ACHIEVED。


## 跨阶段重点

- **CDK两阶段：** Early→Middle barcode组成试验得到有限的组成预测信号，但不是固定时点/绝对存活/药敏；随后功能排序增量未通过：Abema固定配置的Middle使唯一可评分条件从1/3正确变2/3错误，Palbo联合留出不可估。停止该功能prefix配置，不把组成预测转写成功能收益。[组成反馈](../../20261022/cdk_middle_feedback/DECISION.md)；[功能增量](../../20261022/cdk_functional_increment/DECISION.md)。
- **PTPC两阶段：** 新S8支持HCT116中结构注释有有限排序信号，当前锚定更新器按普通联合残差基线处理，不能据此晋升新颖/RSI；后续晚期分子信息screen的冻结继续门失败，停止该表示/归一/选择配置扩张。[更新机会](../../20261022/ptpc_update_opportunity/DECISION.md)；[晚期信息](../../20261022/ptpc_late_information/DECISION.md)。
- **Norman来源与混合/反馈：** 普通RNA条件化在K562来源与匹配端点上有预测增量（source calibration开发约24.2%相对无RNA完成、matched tasks的RNA nuclear相对identity nuclear约14.0%/15.9%）；这些属于有限、同域探索性普通信息价值，未证新算法。一个early-kernel mixing更新器在共同起点下有窄门内1.6464%开发MSE增益，但搜索机会不等、不是等预算优势，最终停止其独特更新器主张。RNA复测来源审计保留残差相关结构，但无法识别噪声来源/可靠性权重。[source calibration](../../20261022/norman_baseline_calibration/DECISION.md)；[matched-guide tasks](../../20261022/norman_matched_guide/DECISION.md)；[feedback transport](../../20261022/norman_feedback_transport/DECISION.md)；[replicate reliability](../../20261022/norman_function_reliability/DECISION.md)。
- **BeatAML与CD14：** 暴露开发域的普通协方差功能反馈确有任务内阳性（8药反馈后MSE−23.49%、top-3 regret−15.07%）；CD14分层相关复现screen下界未达预定继续门，停止该来源依据。二者都没有测试同信息最强直接/refit/CL/AL/预算匹配搜索下的新规则收益。[BeatAML反馈/状态充分性](../functional_state_sufficiency/DECISION.md)；[CD14纠错决策](../functional_error_renewal/DECISION.md)。
- **Organoid：** 资格阶段留下有限历史后续批次任务入口；之后固定ridge forecast配置停止，保留普通FAC反馈效用的局部结论。[资格](../organoid_schedule_qualification/DECISION.md)；[forecast](../organoid_schedule_forecast/DECISION.md)。
- **Distribution health：** 306 conditions/102 guides/51 canonical IDs是响应前身份与资格分组，尚无数值预测结论；可做有限提取/目标处理资格，whole-gene分组需覆盖同一规范ID。[最终资格决策](../distribution_health_qualification/DECISION.md)。

完整逐根目录索引见 [STUDY_INDEX.md](STUDY_INDEX.md)；实际检查路径、每根的reviewed/missing状态及多份最终文件清单见 [COVERAGE_RECENT.json](COVERAGE_RECENT.json)。

## 覆盖范围

近期归组摘要基于全部可找到的研究根最终 DECISION.md/REPORT.md。两日期目录共枚举128个既存研究根：113根有最终报告并逐份读取，15根没有根级或root/最终 DECISION/REPORT；逐项名单及具体缺件原因见 `COVERAGE_RECENT.json`。各根一行决策与原始链接见 `STUDY_INDEX.md`。

