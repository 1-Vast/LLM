# E.faecalis temporal function: qualified source, failed resource gate

2026-10-22，Asia/Shanghai。**本配置停止扩展；总目标仍 ACTIVE / NOT_ACHIEVED。** 已执行一个预登记的真实数据资格实验，但没有得到值得扩展为世界模型/智能体/RSI研究的信号。DeepSeek的两个新机制提案也经独立正反评审和实际交叉质疑后停止作为创新核心。

## 实测裁决

完整协议、输出与限制见 [rank pilot](rank_pilot/REPORT.md)。以20个CRO适应群体的DOX逐日相对IC50为源，按固定哈希分10开发/10测试；用day1–6选择3个测试群体，持续优先复核day8–13。开发标签只由开发群体未来读数生成，测试未来不参与拟合。所有方法共享信息与18个未来复核名额。

| 方法 | 相对读数排序分配效用，越高越好 |
| --- | ---: |
| 六日历史ridge |0.600000 |
| day6持续排序 |0.588889 |
| day6-only ridge |0.588889 |
| 前缀平均秩 |0.650000 |
| kNN3 |0.538889 |
| 固定hash名单 |0.655556 |

候选对两个预冻day6对照仅+0.011111，低于所需+0.10；条件bootstrap敏感性2.5/97.5百分位为[−0.161111,+0.172222]，下界要求也失败。十个测试群体、固定训练拟合和非光滑top-k使该范围不具名义置信区间保证。45个delete-two子集差值有正有负，不构成45次独立验证。两个day6臂名单相同；hash名单的偶然高值不是新策略发现。

执行前12项合成测试通过，独立代码审查无阻塞问题；当前冻结的11项输入/代码/来源/评审均保持原hash。[独立事后复算](rank_pilot/POSTRUN_INDEPENDENT_REVIEW.md)另通过22项检查，以另一套midrank和带显式截距拟合重现六模型、10000次bootstrap与45个删二子集；它只读取已开值JSON，未重新打开工作簿。单次打开240个有限数字响应，无删除、插补、调参或换窗口。代码在 `research/efaecalis_dynamic_qualification_20261022/`，全部结果在本目录。停止在这一配置上扩模、Agent搜索或RSI包装；不能把这个局部阴性推广成所有历史信息或所有细胞世界模型无效。

## 一手来源与可执行边界

Maltas、Huynh、Wood，[*Dynamic collateral sensitivity profiles highlight opportunities and challenges for optimizing antibiotic treatments*](https://doi.org/10.1371/journal.pbio.3002970)，PLoS Biology2025，PMC11709278。原文、发布数据与版本收据、访问失败分别保留，不以失败证明数据不存在。

- [身份与来源报告](redirect_followup/REPORT.md)：官方S1Data164,331bytes，SHA256273cc82c826f245be228a7fd21673fca13eaee1b949183f3b179b86bbce1fb27。主实验5药×4谱系×days2/4/6/8，共80克隆采样键；独立Fig4B实验20个CRO适应群体×14天，样本分支挑战DOX24h。不是已测多轮换药治疗。
- [数字身份审计](numeric_identity/REPORT.md)：仅275个身份/设计坐标得到初始资格；9项测试、12个冻结输入及此前8个来源输入不变。七偶数日OD面板与每日相对IC50块应区分。它们不把时间点变成独立任务。
- 原individual daily AUC门槛是 **NOT_EXECUTED / INDIVIDUAL_MENU_UNQUALIFIED**；不能用日期汇总AUC代替个体轨迹。原IC50绝对误差门槛是 **NOT_EXECUTED / SCALE_UNRESOLVED**。新秩目标另行登记，不假定Excel已是log2，也不从响应符号猜变换。
- 秩实验只依赖共同同方向单调变换下的日内次序；未知个体归一化分母仍限制绝对敏感性解释。它模拟“历史完整开发cohort→新cohort”的回顾性泛化，不声称原并行20群体在真实day6已经知道开发群体未来。训练/前缀和全部测试评分读数的成本已公开，未证明总实验净节约。
- 已打开的240有限读数现在全部暴露。最初字符串投影还泄露过S3的240个非有限标记，[暴露更正](redirect_followup/EXPOSURE_CORRECTION.md)原样保留；此研究不是完全盲测或独立确认。空的根目录xlsx是原302body，应使用redirect_followup内真实文件。

## 原作已有机制与新提案评审

[原始v1.0代码I/O审计](code_io/REPORT.md)认证完整tree和`main_td.rs`。原作已用耐药向量状态、动作药物、时间变化经验profile与backward value iteration做规划。代码对任意当前state施加同一个drug/replicate profile增量并clip；这是假定state-independent additive transport，而非已观测任意背景换药的因果转移。早期规划能访问后期profile，是已完成实验的已知未来条件。四个输入CSV未在完整pinnedtree中，profile到底累计值还是相邻增量尚未认证；不能据此断言作者计算错误。取得代码不等于模型/Agent性能成功。

一个明确预算的DeepSeek提案调用后，支持方和反方先独立保存草稿，再实际双向问答：[支持方](DEEPSEEK_ADVOCATE.md)、[反方](DEEPSEEK_SKEPTIC.md)、[交叉记录](DEEPSEEK_CROSS_SKEPTIC.md)。共同来源提示已给出，独立不等于盲评。

| 提案 | 最强支持与反对 | 裁决 |
| --- | --- | --- |
| 学习实验成本，已观测集合Q在状态中，c=1[a∉Q] | 正确账本可避免重复付费；但成本已由状态/动作确定，条件方差为零，普通cost-aware AL/belief MDP逐步实现。drug-only键还会错把新日期免费。 |STOP_AS_NOVEL_CORE |
| 预测未来药敏翻转时点，按h改变残差和样本数 | 动态数据确有转折；原目标有短前缀偏差和断点右段无观测。固定观测集修正后是普通分段回归；未来断点没有前驱证据时不可识别。 |STOP_AS_NOVEL_CORE |

双方无剩余算法新颖性分歧。仍允许具有合法完整菜单的archive masking/reveal回放，不要求重建作者原查询顺序；单次DOX定时用途也不要求挑战后持续演化。限制更强结论的缺失证据，不应错误否决更窄合法问题。这两个方案没有给出可编辑improver I0→I1及后续独立改进机会，最终策略效用不能替代RSI。

已知成本、普通分段回归和原作MDP可保留作公平基线，不能因日后普通模型阳性而改写本次创新裁决。Hyperagents/AIDE²等可编辑任务/元程序和共同起点检验的一手文献约束见[既有最新文献审计](../../20261021/rsi_next_qualification/DECISION.md)；新颖性检索有范围，未宣称穷尽。

另一次在pilot结果揭晓前独立委托的[机制尝试](NEXT_MECHANISM_ATTEMPT.md)提出对所有相容unphased基因组合求功能排序界。它避免无根据的单haplotype猜测，但当前操作分别归约为普通LP/正分母分式优化和稳健实验设计，且实际allele增长/挑战功能与混合assay校准缺失。提案者自行停止为新核心；没有因此另开响应或数值搜索。该草稿不是已完成跨立场辩论的新候选，也未获得晋级；它只保留明确推导与未来必要数据条件。

## 当前缺口、资源和停止范围

本来源尚未测得世界模型相对同信息强直接预测的贡献，也未执行Agent、权重/程序继承、联合效应或改进策略自身的后续改进收益。完整目标要求的普通重训练、持续学习、主动学习、简单混合、等预算程序搜索比较仍是 **NOT_TESTED**；当前小门槛失败，不能启动这些更昂贵实验来追逐本测试集。

研究继续时必须提出不同且具体的可否证问题，并保留本配置停止与曝光边界。新方法即使由已知组件组成也可有实质贡献，但需给出新操作、识别条件或可测性质；不能仅重命名通用meta编辑、失败检索、残差更新或普通程序搜索。后续机制尝试是待独立审查的草稿，不预先获得晋级。

资源：本次真实数据运行2个ridge拟合、0调参，wall1.0744s/processCPU1.046875s，0HTTP/API/GPU；仅本执行范围，不含来源资格和代理推理。此前DeepSeek1个decoded调用，4827prompt+1033completion=5860tokens；transport尝试次数client未暴露。所有来源GET、503/302和后续访问按各自NETWORK收据保留，不用未核对的总数替代它们。[Root工作和失败记录](ROOT_WORK_RECORD.md)保留本地只读失败、守卫失败与时间顺序。
