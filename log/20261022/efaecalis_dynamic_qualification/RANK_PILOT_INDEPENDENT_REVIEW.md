# 独立审查：scale-invariant 的日内复核排序 pilot

2026-10-22。scientific_skeptic；应 Root 新任务审查。没有读取响应、HTTP、拟合或运行。审查对象是一个新的窄应用/资源门槛，不是被否决的 DeepSeek 算法构造。

**结论：可以避开 ratio 与 log2(ratio) 的歧义，条件性允许一个“已有完整训练 cohort 和早期 prefix 时，优先复核较低 relative readout 的新 cohort population”的回顾性排序 pilot。不能因此宣称原 20 个并行群体在 day6 已作前瞻预测，也不能声称总实验数净下降。仅有 pairwise concordance 改善不足以通过资源门槛，需预冻实际 top-k 分配效用。**

## scale 与可比较性：哪些是必要的

对同一天，若 `z_i=IC50_i/IC50_ancestor` 或 `z_i=log2(IC50_i/IC50_ancestor)`，则两者在所有有效正 ratio 上严格同向单调，给出完全相同的群体排序。用逐日 percentile rank 输入、相同日内相对次序作目标，既不需要选定 identity/log2，也不需要数值误差的物理单位。不能把 absolute-error pilot 的 scale 停止条件泛化成“任何排序预测都禁止”。

但这仅消除了**同方向严格单调变换**的不确定性，不是消除所有数据语义要求：

- ID、day 和该块确为同种 relative-IC50 读数必须成立；目前身份审计已支持 IDs1..20 × days1..14 的每日菜单。
- 需要数据类型/缺失/错误的 outcome-blind census，及预先冻结的 tie、无效值和缺失处理。不能在看性能后改 cohort、日期、目标或排序方向。
- 若各 population 使用不同未知 denominator，低 relative readout 不必等于低 absolute IC50。可仍预测“表内已导出 relative readout 的次序”，但不据此宣称哪一个 population 最易被 DOX 抑制、绝对药效更高或临床阈值达标。若要升级这一含义，则需共同祖先归一化/方向的明确证据。公开图注和同一 V583 祖先提供合理设计背景，但不能把尚未核实的 Excel 变换链描述成已核实。
- 排序方向固定为“较低导出 relative IC50 优先”；不得通过响应符号或性能把它反转。若后来文档证明存储的是反向 sensitivity score，应登记该任务定义错误，而不是事后悄然改目标。

## 最重要的时序边界

若训练模型使用 development populations 的 day8–13 目标，则需要一个已完成的 development cohort。原论文二十群体的未来观测在原 day6 尚不存在；把它们按 ID 分成 train/test 不会创造时间机器。

合法解释是：先有一批按同一方案完成的历史群体和完整药敏，再对一批新群体在其 day6 prefix 上作预测。这可用 whole-population split 回顾性模拟同方案新重复的泛化。它不等同于原二十群体的真实在线前瞻实验，也不等同于跨菌株、跨药对、跨研究任务继承。

输入 rank 若使用全二十 population 的 early-day 值，是允许的固定 cohort / transductive normalization，条件是所有二十的 prefix 确实可见且按同一规则计费。它提供 held-out 群体之间的早期相对位置信息，不是未来泄漏；但部署含义限于有这组 reference cohort 的排序。不能一边使用全二十 prefix，一边按只测一个新 population 的成本报告。

development 目标必须只在 development populations 内排序；不得先用全二十未来响应计算 rank 再抽 development 标签。test 未来响应只用来评分，在 test 内日内 pairwise 比较最直接，完全不用训练期的未来 test 值。

## 真正能改变的资源决定

全二十群体 × 六天 prefix 本身是 120 个 population/day 的 IC50 assay；十个 development 群体 × 六个未来日又提供 60 个训练目标。是否有 assay bundle 可合并另论。单一来源上，不能把这些当免费，再宣称只做少量未来复核就是净省实验。

**允许的条件性用途：** 当这些训练/prefix 已由一个既定监测流程取得时，在一个未来固定日，只能复核 test cohort 中 k 个 population，优先复核预期具有较低 relative readout 的群体。这是信息条件明确的分配问题。其收益是选中的有限确认对象次序更合意；尚非减少全部研究成本。若实际使用场景不需要 prefix、没有历史 cohort，或以后没有固定日复核的资源约束，则这个 pilot 只证明预测现象，对用户目标没有已展示的分配价值，应停止架构扩展。

资源门槛应直接问选择名单，而不只问全排序：pairwise concordance 可能改善中间八个群体的次序，而最想复核的两个仍然选错。可以将 concordance 作为诊断指标，但 primary allocation utility 必须对应冻结的 k。

一个无数值 scale 的可执行方案（Root 若采用，必须在开响应前正式注册）：

1. 用固定 salted SHA 的 population-ID 排序选 10 development / 10 test；冻结 salt、ID清单及是否固定同一 cohort。Prefix days1–6，未来评分 days8–13；公开 window exposure 照实声明，不称窗口发现。
2. 对每个未来评分日，选 test 中预测 relative readout 最低的 **k=2** 个复核；预算每臂完全相同。
3. 真实效用定义为所选二者在当日 test cohort 内的平均 `1−midrank_percentile`，六天等权。该效用只依赖次序，越高越好；不是命中生物阈值。预测并列用预冻 ID 哈希打破；观测并列用 midrank，不用哈希制造生物次序。
4. 比较 day6 rank persistence、development-calibrated day6-only forecast，以及同资源的小型 full-prefix direct ridge。calendar/day strategy在同日群体分配中全 tie，只是随机水平参照，不是强对照。开发中的校准/正则化只用 development population 内验证；基线与候选给予相同信息和选择预算。
5. 若需一个有解释的分配扩展 hurdle，可在注册中取 **候选相对两项强基线的效用改善均至少 0.10，且预定的 population-level paired uncertainty lower bound 均高于零**。0.10 在十群体 test 中约相当于所选二者平均位置前移一位；这是研究资源分配门槛，不是临床或生物效应阈值。门槛不是本文件已经测得的结果，也不以本文件替代正式协议。可用更严格的业务阈值；不能看数据后降低。

上述门槛通过，只买一次进一步的窄实验分配验证/新候选审查，不自动买大架构、LLM agent 或 RSI。未通过/不确定则停止该配置上的扩展；不推论所有生物状态无信息。

## 依赖和不确定性

每天十个 test 群体产生的 pairwise 比较不是 45 个独立观测；六天也不是新的独立任务。须按整条 population 轨迹重采样，保留跨日依赖；若实现 pairwise bootstrap，应避免把同一 population 的重复抽样副本互相当独立生物 pair。十个 test 群体仍很小，区间应按 cohort-conditional exploratory uncertainty 报告，不把 bootstrap 当跨实验/菌株可信区间。

full-prefix ridge 若胜过 day6-only calibration，仅说明额外历史排序有预测价值；普通小模型可以实现该能力，恰恰应先测它。它不证明 latent world state、agent、自我修改、权重/程序继承或联合协同，也不挽救 DeepSeek 两个已归约构造的新颖性。

必须在正式协议中补齐且一次冻结：ridge特征/标准化/正则化规则；calibrated-persistence 的精确函数族；同 cohort 内 rank 的公式与 ties；missing/error census 后的 stop 规则；salt 和 split 清单；uncertainty 算法；预算账本。它们是一个小实验必要的可复核定义，不是要求新架构或额外分子数据。

## 对旧门槛的正式处置

原“individual daily AUC day8–13”门槛：**NOT_EXECUTED / NOT_SUPPORTED_BY_CURRENT_INDIVIDUAL_AUC_MENU**。不能用 AUC summary 或仅七个偶数日 OD panel 拼成该任务。

原有明确数值单位的 IC50 absolute-error 门槛：**NOT_EXECUTED / SCALE_UNRESOLVED**。`IC50_SCALE_GATE_NOTE.md` 对它继续适用。

新 rank pilot 是另一目标；其 scale-invariance 不确认表内原数值 scale，不将旧门槛改写为已执行，也不构成 biological/WM/agent/RSI 阳性证据。

**独立最终意见：条件性允许这个小型、固定 cohort 的排序/分配资格实验；必须将训练 cohort 的时间顺序和已付 prefix 成本写清，并以实际 k=2 名单效用而非 concordance 单独决定是否扩大研究。若 Root 不愿采用这些范围，或真实任务没有这些已具备的信息与后续分配约束，则不应为保留 pilot 而继续。**

## Root 选定 k=3 后的独立追加意见（开值前）

Root 随后明确采用历史完成的 development cohort → 新 test cohort 的回顾性用途，限定为 exported-relative-readout 次序；选 10dev/10test、days1–6 prefix → days8–13，固定 **k=3**。本节保留前文审查历史，**前文 k=2 和相应 0.10 hurdle 只是未执行建议，已被本次 k=3 任务规格取代，不能混用。** 最终统计与阈值由 Root 在读取响应前正式注册。本节也未读取响应。

### 可以把每个 population 压成一个明确目标

令 `r_it` 为 population i 在其所属评估 cohort 的 day t 之 normalized midrank percentile（低 readout 对应低 rank），定义

`z_i = mean_{t∈{8,9,10,11,12,13}} r_it`。

训练时每一天仅在 10 个 development populations 中计算 r；测试的 r 仅在 10 个 test populations 中计算，且未来 test ranks 只用于评分。禁止先在 20 个 future outcomes 中 rank，再抽 development 标签。

在 day6 一次选择预测 z 最低的固定三个 population，定义

`U = mean_{i∈selected_3}(1−z_i)`。

这个目标与实际选择名单完全一致：在一个预定的六日后续确认流程里，优先持续复核这三个具有较低平均相对 readout 次序的群体。它不是按天重新选不同三个，也不等于平均 absolute IC50 最低、更高杀菌效力、最优切换时点或已发现 days8–13 窗口。若真实操作要每天重选名单，应另注册 day-specific 目标，不能事后混为同一 utility。

预测并列的选名单规则、响应并列的 midrank 公式、日期等权和 k=3 必须预先固定。较低“平均 rank”可以对固定资源有清楚含义，无须知道 ratio/log2 storage scale。

### 基线和 gate 的独立意见

- **必须有 day6 rank persistence。** 同时保留 day1–6 mean-rank 这一无训练基线，以免把简单平滑误认为复杂历史价值。若 Root 的“past6 rank”指最近 day6，应在协议中用明确名称；不要与六天均值混称。
- 小 ridge 和 kNN 使用相同六维 daily rank prefix 和相同 development z，是合适的普通预测器。超参/标准化/模型选择只用 development 内验证；test future 不能成为模型挑选依据。日历策略在这个同日/同窗口群体排序问题中没有差异化输入，只能是弱参照。
- “优于 day6 persistence 且不劣最佳简单 prefix 模型”可作资源 gate，但“未检出显著更差”不等于不劣。Root 应在开值前给出实用优势阈值、非劣界和相应不确定性定义，并冻结何谓最佳（development 选择，或预先固定的多个对照均须满足）。不能在 test 上挑对自己有利的 baseline。
- 如果候选本身就是 development 选出的 ridge/kNN，则本次只检验**普通 prefix 预测/分配是否有机会空间**；“不劣最佳简单 prefix”不提供世界模型的独有证据。后续新模型若要立项，仍须对这些普通模型作同信息、同预算比较。
- 把六天折叠成 z 让任务定义更简洁，但未来 daily ranks 共享同一 cohort，z_i 彼此仍有排序耦合。不能把 60 个未来日记录或 45 个 pairwise comparisons 当独立样本，也不能因只有一个 z_i 就自动使用独立标量标准误。按整条 population 处理、明确 cohort-conditional 评估与 bootstrap/reranking/ties 的规则即可；n=10 test 的局限如实记录。

**最终意见保持 CONDITIONAL_GO_FOR_SMALL_RANK_QUALIFICATION。** 该小实验可合法避开 ratio/log2 变换不明；它只能决定是否有必要继续本来源上的架构探索。若未达到预注册 gate 或不确定，则停止扩展。旧 AUC 与 absolute-error gates 仍为 NOT_EXECUTED；本次新目标不回填旧门槛结果，也不确认原数值单位。

## Root 固定协议的统计审查（仍在开值前）

Root 再次明确：primary 为 ridge6（lambda=1，无调参），对照 day6 persistence 与 ridge1（lambda=1）；补充 prefix mean、kNN3、calendar/hash。固定 k=3、六天平均 rank target。不宣称新机制。拟要求 ridge6 相对两项 day6 对照各自 U 改善至少 0.10，并且 10,000 次 paired whole-trajectory bootstrap 的指定 percentile 下界大于零；固定已训练模型不重调。Bootstrap 中十个抽样位置的未来逐日 midrank 和 predicted top3 按经验质量计算，重复抽中的原 population 不是新的独立生物轨迹。另完整报告 45 个 delete-two 子集差值。

**独立意见：这没有致命的计算不自洽问题，可以作为预注册的探索性资源门槛，但不支持名义 95% 覆盖率的确证性声明。**

- 重采样整条 trajectory、按 draw 的 empirical mass 重算 ranks，再计算同一定义的 top3，是可解释的经验分布扰动。实际主结果仍为十个唯一 test 群体中的三个唯一 population；不能把 bootstrap 重复副本解释成可实际重复分配的新增对象。
- 固定 top-k、ranks 和 ties 构成非光滑统计量，n=10 下 ordinary percentile bootstrap 没有自动的 nominal coverage 保证。可将其明确称为 conditional exploratory bootstrap sensitivity percentile，预定其下界大于零作为继续研究的规则；不能把它转述为已严格控制错误率的 95% CI 或“统计显著”。更严格的 point threshold 不会自动证明区间在统计上保守。
- 固定拟合后重采样仅覆盖 test-cohort composition 扰动，不包括训练集重采样、模型选择、其他实验批次和菌株。这个范围与本次小门槛一致，报告时必须保留。
- Delete-two 的 45 个子集能暴露 roster 敏感性，但每次是固定预算 3/8，而主分析是 3/10。它们互相高度重叠，不是额外 45 个实验或独立验证。完整报告比挑选稳定子集更有意义。
- 正式协议应固定：ridge 是否标准化、未惩罚 intercept、目标与特征秩公式、missing/tie rules、用于预测并列的固定 hash、以及“95% 下界”具体是 2.5th percentile 还是 one-sided 5th percentile。除定义补全外，无需再加调参或数据。

本次最终建议仍是有范围的允许：一个普通模型的分配 headroom pilot。门槛通过只足以授权后续独立验证；未过则停止本来源上的架构扩展。没有打开响应，也没有利用本轮数值选择统计规则。
