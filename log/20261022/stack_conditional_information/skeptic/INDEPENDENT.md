# 独立反方：STACK 条件信息数值 gate

2026-10-22。先读本阶段 `PROTOCOL.md`；本稿落盘前未读本阶段其他peer稿、root实现/数值freeze、raw/XLSX或assay值。已有source/identity资格与历史阴性暴露保留，不假称对来源一无所知。无GET、fit、provider call、raw/response访问，也不修改root protocol。曾向root发送设计级三处最小澄清，下文完整列出。

**结论：conditional GO，一次窄的registered strong-direct信息gate有意义。** 这个实验能判断固定来源、完整观测条件下，early SG特征是否使注册模型对later live-reporter预测达到预定实用增益；不能证明新world mechanism、conditional mutual information、真实viability或agent/RSI。不是HCT116改字段续跑。

## 完整样本与95%资格

全臂共用14个prefix观测的非负有限规则，train/validation还要求合法L72，test在先存prediction/abstention后才揭L72，科学上可以定义一个明确的complete-observation estimand。它不要求MAR，也不保证缺失者相同性能。live-only在此也受D是否取得影响：这是同一已采双通道资产上的channel ablation，不是只采L即可部署的无条件utility。不得把95%作为测量噪声、随机缺失或可推广至全库的证据。

最小澄清1：每role×screen的95%分母必须是**数值前冻结的该role全部named-entry rows**，包括collisiongroup的两个不同entry；不能先缩至prefix-eligible再算complete coverage。至少200/100/200 all-three-complete contributing groups另计，group不是row，尤其collisiongroup有两个成员。每screen全臂配对同一target-valid panel，虽不同screen可能缺失不同entry，macro仍是这三个条件panel的平均，不是假装共同全测集。

最小澄清2：从已授权prefix顺手保存L-only-prefix-valid、dual-prefix-valid、L-valid而D-invalid等数量及per-role/screen/key记录；无需额外读值或模型。这样可以审计额外通道带来的资格损失，而不偷偷把“共用mask”当live-only独立部署公平性已解决。完整比例通过时也要报告被排除的5%以内范围；其效果不由其余结果界定。

最小澄清3：train/validation完整资格失败就在fit前停，不为等结果而继续选模型；test最终完整资格失败归DATA_QUALIFICATION_INSUFFICIENT，不能将仍可算出的子集成绩升为useful-gain verdict。若test-prefix合法率已低于95%，其complete率不可能达到95%；可按数值前固定规则提前资格中止，或完成既定预测后只报告资格失败，不能在看到target后改路径。protocol目前已禁止换目标/clip/impute，方向正确。

这些澄清不要求all-complete或新湿实验，允许诚实处理source原有censoring。95%本身是事前pragmatic tolerance，不会使source-defined排除自动变成无偏；最终应用域必须写明。

## 标签开启与未来信息隔离

固定1832role groups、跨三个screen同role、known SMILES碰撞同group，且无chemical descriptor或row/hash输入，适合unseen recorded-entry问题。不能扩大为unseen chemical/scaffold，三个screen也不是独立run验证。

test prefix可在冻结后解析以判断资格和形成特征；只能fit train scaler、用train labels训练、validation选config，选后train+validation refit。**全部test keys的预测/abstention文件成功写盘后**才可开启test L72；单个模型的临时预测落盘不够。posthoc target-valid mask仅可用于冻结estimand的最终配对评分，不能反过来改变test features/predictions/abstentions。源XML字符串在内存/磁盘不等于数值封存；需要白名单地址访问账本与malformed closed-cell canary。

拟合前用于训练/验证目标资格是标签可用性的合理条件，不是“完全无outcome信息”。test-target访问日志、文件hash/顺序、选择配置和train/val arrays应能独立复核；不得通过一次预扫描把所有future字段数值化再声称最后才read test。未来D、LF/QC/result side table、87 unidentified rows全部保持关闭。

## 配置预算与snapshot嵌套

19=7absolute L+6relative L+3slopes+3contexts；两snapshot各21；history34=base19+7logD+7raw D/(L+1)+1slope。fullhistory明确含D0与D24两snapshot全部输入信息，修复了历史不严格嵌套时的解释风险。各arm同14候选、同监督/fit weights/scaler规则、同validation scorer及选后refit，不拿固定OLS对强dual，也不test上择最优D臂；56trials+4refits计数明确。每screen相同fit总权重，缺失后无需假设相同row数。train-only unweighted StandardScaler在这一预定义程序中可接受，并非泄漏。

三families是这个规模上有意义的direct基线集，预算匹配指配置数与规定超参，而非精确wallclock/FLOPs。相同预算不能保证同等最优，也不把有限家族null提升为无信息定理。history/snapshot的不同维度和ratio坐标会改变模型bias；特别D/(L+1)还提供L的非线性表示，理论上即使D可由L预测也可能改善有限模型。故阳性是**这些注册forecasters上的额外通道/表示实用价值**，不是对最优预测条件独立或条件互信息的数学证明。当前exploratory/无机制表述足以处理该限制，不为此强加新feature搜索或新模型臂。

world-model同信息优势还未测。ordinary kinetic/refit/clearance/LED、固定混合与equal-budget search未来仍是原目标必需；本gate已明确NOT_TESTED并把main claim限定direct信息，允许先低成本资格而非装饰世界模型。常率已知r时D不影响L的逻辑，也不意味着未知参数/噪声下D不能帮助普通推断。

## 评分、阈值和不确定性

每screen within-panel平均MAE再三screen等权，主overall绝对.05+相对10%并每screen增益>0，是合理的预定实用筛选条件。positive-per-screen并不要求每screen各自达到.05/10%，应明确避免事后改读；极小正值不代表跨screen稳健或显著复现。history还须按同overall双门槛、每screen正值胜D0与D24，支持历史property而非仅snapshot校准。若只有Dinitial/snapshot对L-only改善却history未过primary，不得改primary为最好的D臂救结果。

配对bootstrap要按冻结test role groups抽样，同group的entry与全部screen一起，保留同一重复抽样权重，按各screen合法panel重算macro。collisiongroup的两entry仍各贡献其合法row误差；bootstrap cluster并不把它们合并成化合物。10k与fixed seed仅描述这些recorded-entry条件panel的采样敏感性，不处理未来缺失偏差、测量偏差、未知chemical aliases或run/生物不确定性。point gates决定pass；95%interval不额外充当unregistered显著性门槛，也不能在不支持时忽略其方向，须完整报告。

资格通过而primary未过，只停止此fixed-dose24→72h/registered predictors设置，不能证明所有D、world或RSI无效。primary过而两snapshot未过，保留额外通道/静态校准层观察，不说历史必要；history全过仍需普通同信息模型、观察校准及新合法任务。prior source availability/positive seed count、同screen多entry、训练变多或普通选超参均不等于agent/inheritance/RSI。

运行前仍需看实现/white-list tests/freeze以确认上述程序真的被执行；本独立稿仅审设计，不提前认证代码、数据域或任何结果。
