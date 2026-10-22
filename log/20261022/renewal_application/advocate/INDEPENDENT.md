# 独立候选审查：药物下的 RNA 合成—降解分量更新

2026-10-22，`mechanism_advocate`。本稿先保存，尚未读取本轮其他代理的机制稿或数据结论。旧 frozen 目录只读；无 biological matrix、数值实验或 provider 调用。新来源请求实际共四次，含两次失败，body/receipt/SHA 均保存。结论不是对 root 尚未读取的候选作裁决。

## 独立结论

**0 个新核心通过；1 个真正不同的分子测量方向被具体化后，仍未达到新核心与可执行数据资格。** 不建议为了凑一个候选而现在实现。它没有复活 PRISM pools、AZ 效应坐标、quadratic update-value、一般 memory 或模块修复 wrapper；但“与本项目旧机制不同”不能代替“与领域已有工作实质不同”。

考察的唯一候选是：**在药物的早期 RNA 响应上，用代谢标记区分 RNA 合成改变与 RNA 降解改变，只更新可由这两个测量分量辨识的转录状态生成算子，并保留两种分量对未测时长的不同预测。** 具体用途是药物扰动下的转录作用机制与后续状态响应预测；不是 efficacy、viability 或临床药效声明。RNA proxy 可有独立方法价值，不要求每一个此类任务再配一个 viability assay。问题在于当前普通机制已有精确实现，且本轮未拿到可执行的来源证据，不能因此授予一个新框架核心。

## 为什么它有生物结构，而不只是换一个 latent

总 RNA 表达变化相同，可以来自合成变快，也可以来自降解变慢。两者在继续暴露或撤药后产生的状态轨迹可能不同。普通单时点 total-RNA 模型无法凭同一个均值区分它们；这是一项观测非识别性，而不是关于任何同信息 direct 模型的能力上界。

在一个非常窄的常系数窗口内，令 `x0` 为窗口开始的真实分子量，`alpha>=0` 为合成率，`beta>=0` 为一阶降解率。若期间合成的新 RNA 被完整准确标记，则

`old(Delta) = x0 * exp(-beta*Delta)`

`new(Delta) = alpha * (1-exp(-beta*Delta))/beta`

`total(Delta)=old(Delta)+new(Delta)`。

`beta=0` 时第二式取连续极限 `alpha*Delta`。同一 total 可由不同 `(alpha,beta)` 得到，另一时长上的 total 可以不同。因此候选更新不能只对 total expression 加一个 residual：它应分别把反馈写入合成与降解生成项，再由同一分子周转方程传播后续状态。源于可测 source/sink 的两分量更新是此方向的全部结构；不需要 LLM、多代理运行时、任意程序重写或搜索 archive 才能成立。

这些式子也暴露了严格的限制：单细胞破坏性采样不提供同一细胞的 `x0`；只有匹配群体与额外稳定性假设。标记不完全、RNA 标准化、细胞组成/周期/增殖稀释、测序捕获率、应激改变标记代谢，都可能把假定的 old/new 分量改变。没有校准的 old/new counts 与绝对/适当归一化测量时，不能直接声称识别出细胞内降解率。source/sink 拆分在一种状态中成立，也不等于它可跨药物/细胞迁移。

## 明确的更新算子，以及为什么目前仍属普通方法

最小算子为：共同起点具有 `(alpha0,beta0)`；从合法反馈估计 old/new 的似然，以非负约束、同一 source prior 做一个二维 rate refit，得到 `(alpha1,beta1)`，保留未被测量支持的分量/不确定性；未来时长由上述相同生成式计算。若逐基因独立估计过噪，可只在 source 数据上学习固定小的 rate 共享基，但这已经是层级/低秩 kinetic refit，不能自动称新。

**最强普通复现是构造性的，而非“通用网络理论上能表达”：** 将同一 old/new likelihood、同一非负约束、同一 source prior、相同测量和相同迭代预算交给普通 kinetic system identification，就逐步执行了本候选的全部 rate 更新。用解析式估计 rate 再外推，甚至不需要研究智能体。若候选只在合成/降解两个现成更新中选一个，普通等预算两臂搜索可枚举并复现。此时学习“何时选哪个”属于普通 contextual/meta selection，并非新的 RSI。

同信息强 direct 也应拿到 total、new、old/标记效率、全部时长/药物/context 及相同反馈，不可只给 total 后声称 world 胜。它不被数学保证以有限样本/预算复现 rate 归纳偏置的未见时长外推；所以**存在真实的有限样本经验机会**。但该机会属于明确分子周转约束与普通 rate model 的比较，不能把 direct 不自动相等当成候选已新颖。最重要对照是同信息普通 rate refit、RNA kinetic/vector-field 方法，而不只是一个黑箱 baseline。

因此，我不能指出一项已可信地超出现有 RNA 动力学辨识的具体操作；当前 **NO_NEW_CORE**。若未来有人提出比普通 source/sink refit 多出的可验证结构性质，应单独明确那一步，而非加深模型后回填新颖性。

## 已查历史，避免改名复活

已定向查阅 `research/REPORT.md` 的最新决定/研究地图，以及本代理旧稿：lineage founder-mass selection 界限、干预误差模块修复、RSI later-task 文献、quadratic update-value。旧报告已经排除单 eta time warp、普通 mutation-selection、Gaussian gene writeback、semigroup consistency、ADCC endpoint factorization、常规 EB/shrinkage 等作为新核心。

本次 RNA source/sink 是新的具体测量方向，既不是 live/dead-stock 的换名，也不认为旧 live/dead 失败能否定 RNA source/sink；分子标记与群体计数的测量机制不同。反过来，source/sink 在生物上更具体，也不会使普通 kinetic refit 自动变成新方法。旧 PTV、TG-GATEs、STACK、AZ、PRISM 的停止均保持。

## 一手来源与数据可用性的真实边界

实际四次 GET（不是四篇原文）如下；完整 URL、状态、字节与 SHA 见 `HTTP_RECEIPTS.jsonl`：

1. Europe PMC `sci-fate` 题名索引：200，1742 bytes，SHA `831a52a8096d3911d92663b3f5379977875008b188fe1b578a369bc6888d0a51`。它核实 Cao 等 2020 *Sci-fate characterizes the dynamics of gene expression in single cells*，DOI `10.1038/s41587-020-0480-9`，PMID32284584/PMC7416490；索引标注有 GEO、全文与 supplement。**这是原文定位元数据，不是已读取原文或已下载数据。**
2. 同文 primary fullTextXML 请求：500，错误 body150 bytes，SHA `45b5605a888ef0c1b34474485c738f590dd13555274109437c1e9e20c5f26395`。未得到原文。
3. Europe PMC `Mapping transcriptomic vector fields` 题名索引：200，2045 bytes，SHA `12bfd2e984912afe54f9e5d531a9b875cb3d03a29b2927a9c9c0b55a93315da4`。核实 Qiu 等 2022 *Mapping transcriptomic vector fields of single cells*，DOI `10.1016/j.cell.2021.12.045`，PMID35108499/PMC9332140，有 GEO 标记。仅据题名与元数据不能声称核对了其全部更新机制；这是必须核对的最近前驱，不是本轮已完成精确 novelty 比较的证据。
4. NCBI PMC OA service 的 sci-fate 文章资格端点：404，错误 body1584 bytes，SHA `61ae67fc047161fdc11b32cf46270882aea1887aeff3b0e788d75c54b628efcd`。这是服务路径请求失败，不能写成论文或数据不存在。该端点本来也只是 OA 资产描述，不是 dataset matrix；保留失败，不继续第五次请求。

**当前没有资格化的可执行数据集。** 未确认任何具体 drug/time/physical-replicate manifest、old/new 格式、标记校准、accession 下载地址或独立 later-task 数量；不把题名、有 GEO 标记或我对 sci-fate 的一般记忆当作“数据可获得”证明。不声称已核 A549/dexamethasone/若干时点等细节，不以未读取原文支持这些设定。CellFlow PBMC 无这种分量测量的已核证据，不能为了来源便利强行推荐；此方向也未调用其文件。

本轮四次额度已用完，接下来只能利用 root/数据代理已合法取得的现有来源；若没有，停止本候选数据资格。不能用无限 API 权限冲淡本次有界查证规则或临时第五次 GET。

## 若未来来源合格，最小可证伪实验是什么

以下是未来合同要验证的问题，**本阶段不执行，也不预注册未知数据上的任意性能阈值**。

**零拟合 kill：** 提交确切更新代码，普通二维/层级 kinetic refit 使用同 likelihood、约束、prior 与反馈。如果完全复现生成器与更新，那么关闭“新更新算法”主张，可保留旧方法在新测量/应用上的实证机会。当前方程已给出该精确替代，因此本阶段算法核心门已失败，不需要打开生物数据证明。

**数据/测量门：** 作者级下载与 manifest 必须真实提供处理、时长、标记方案、physical replicate/control、total与new（及可识别 old 的校准）。至少存在未用于 rate 拟合/策略选择的真实测量时长或新药物/context，而非同一 scRNA 样本拆 cell 充当新任务；不存在合适结构则停止。可只验证 RNA response，不强行要求 efficacy。

**最小经验 kill：** 在一个已确认药物/context 系统，用最早合法反馈窗口更新一次，预先封存另一实际采样时长的 RNA 响应。比较 total-only 与同信息 old/new direct、普通 source/sink joint refit、原始候选和相同预算简单混合；包括错配 old/new 标记及固定参数/no-update 对照。评价除总 RNA 误差外还要对封存 old/new 分量单独评分，避免两项互相抵消后伪称机制正确。若 rate model 不胜同信息 ordinary/direct 或只拟合 total 却预测错分量，停止该配置的结构贡献；不能切换测量目标救门。

这里一个系统只能杀掉局部机制假设，不能建立跨任务继承。效用可以预定为 RNA trajectory 预测质量/反馈效率，不是药效；实用幅度和区间精度须按来源测量噪声与实际查询成本在数值前冻结，当前无来源故不虚构。

**之后才有 agent 与 RSI：** 若 molecular world 相对 ordinary kinetics/strong direct 确有必要，再在多个合法后续任务中让程序决定一次确实可购买的标记窗口/脉冲长度或更新方式；若历史只含一种固定标记方案，就没有该动作，不能模拟不存在的实验。与固定程序、AL、CL、全重训、简单混合、同菜单等预算搜索比较。分别开关 world、agent、模型继承与程序继承，报告各自主效应与总联合收益；不要求联合必有正交互，只有 synergy 主张才须检验交互。

策略 `psi` 必须有确切输入输出，早晚版本仅单独交换到同一初始 world/数据/history/program/预算上，测后续真实更新收益。若晚期 psi 仅靠更多 source 标签、不同模型起点或记录答案取胜，C4 不成立。即使 C4 成立，也不自动建立新算法；当前 source/sink refit 没有独特改进策略操作，故不提前宣称 RSI 候选已资格。

## 最终建议

不提交一个“可直接开跑”的虚假候选。保留的具体科学问题是：可测的合成—降解分量能否使少反馈分子响应外推比同信息直接预测/普通动力学更好；它与旧功能测量路线不同，但在本轮既无新核心差异也无合格数据合同。下一轮 cross 应直接质疑上述精确普通替代与数据缺口，允许 root 的不同候选提供反例；不应把本稿的无新核心结论扩大成所有 RNA proxy 研究无价值。
