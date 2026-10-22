# 干预转换一致性与可继承更新：独立一手审查

2026-10-22；scientific_skeptic。**结论：固定干预下的半群一致性已有精确方法先例；跨撤药/第二干预的选择性记忆建立、维持与擦除有很具体的 2026 年一手生物资产。当前未产生已经成立的新模型更新算子，但存在一个值得做身份资格的极小机制空间：更新能否迁移“何种干预改变哪一种持久状态”的约束，并在未参与更新的其他分支上改进功能预测。** 这是一条条件性研究问题，不是把评估协议命名成算法。新数据尚未下载、响应尚未打开、性能未测；没有具体新候选稿前，不声称完成交叉辩论。E. faecalis 与所有既有停止构造不重开。

## 1. 范围、请求与复用

先写 `skeptic/PROTOCOL.md`，搜索本地已有记录，复用 scNODE 全文摘录与 CellFlow2025 原始摘要元数据，未重新下载其一手对象。全部新代码在 `research/intervention_dynamics_renewal_20261022/skeptic_*.py`。

本轮严格执行 **6 GET，全部 HTTP200，共1,253,039 bytes，最大单份791,288 bytes**；无自动重定向、重试或原始数据。原始 bodies、精确 URL、UTC、SHA256、长度在 `NETWORK.json`。两份检索、一个 PubMed 批量摘要、一个 arXiv 结果和两个 primary full texts。没有一份达到3,000,000-byte cap。检索只看有限排序结果，不能声称穷尽最新文献或整个领域没有其他方法。

获得的 primary full texts：

- **Deep-OSG: Deep Learning of Operators in Semigroup**，arXiv **2302.03358v2**；原始 HTML `DEEP_OSG_PRIMARY.body`，逐段方法投影 `DEEP_OSG_PRIMARY_METHODS.json`。这是数学/机器学习方法先例，不是细胞实验。
- **AP-1 mediates cellular adaptation and memory formation**，Li et al.，Nature Communications **17,4265 (2026)**，DOI **10.1038/s41467-026-70862-w**，PMC **13168276**；完整 XML `AP1_MEMORY_PRIMARY.body`，方法/图注/availability 投影 `AP1_PRIMARY_METHODS.json`。该文已公开的结果属于 literature/design-exposed，不能成为本项目盲评发现。

最新补充的 discovery-only primary lead：**Semigroup Consistency as a Diagnostic for Learned Physics Simulators**，arXiv **2605.26324v1**（2026-05-25）。本轮只获得作者摘要，不冒充全文方法审查。作者报告 autonomous/state-complete 条件下 semigroup error 与 rollout degradation 有关联、正则化收益不一致；这支持“诊断不等于普遍有效训练目标”的警惕，不是本项目重复验证。另有2026-09 arXiv2609.02727v1 关于 Chernoff one-step operator approximation，只有摘要，不据此作细胞机制结论。

PubMed 检索首先返回的 **Cellular memory after cancer therapy...**（PMID42898467）是 Review，严格只用其参考文献定位 AP-1 primary，未把综述当实验。没有单独取得新的 causal-representation primary full text，故这一分支查新仍不完整。不能据本轮 none 声称全领域无相关识别理论。

## 2. 半群一致性：哪些已被精确实现

Deep-OSG 不是泛泛地“也做 dynamics”。已读 primary 的式(5)、(8)、(13–15) 与其解释，操作明确如下：

- 用时间间隔 Δ 作为网络输入，`Nθ(x,Δ)=x+Δ·nθ(x,Δ)`，严格保证零时长为 identity。
- 除实测拟合项外，在随机 state x 和随机正时间 s,t 上直接惩罚 `Nθ(x,s+t)` 与 `Nθ(Nθ(x,s),t)`（以及反序时间拆分）的差异。它不要求额外标注。
- 另有仅沿观测轨迹的 indirect two-step loss，同时拟合直接总时长和两步 rollout；原文明确推导它间接约束半群误差。
- 原文假设 autonomous dynamics、可观测的完整状态轨迹，并讨论误差/方差与多时间步预测。

所以如果新稿的唯一新增项就是 `||F_a(x,s+t)−F_a(F_a(x,s),t)||²`，并以一段连续暴露数据作随机拆分，它已与这个具体先例同操作。把 a 作为固定上下文输入并不会凭空产生新算子。**此项应作强基线和正确性约束，不单独担任新颖性核心。**

但不能由此归约所有干预新问题。对 A→withdraw→B，通常没有 `F_B∘F_A=F_A∘F_B`，也没有 `F_withdraw=F_A^{-1}`。即使每个固定药物条件各自有半群，这种不同条件之间的交换/逆关系也不成立。可用的最低数学身份是**相同完整控制 schedule 的拆分重组**：`F_[u1;u2]=F_u2∘F_u1`，前提是接口 state 足够、环境/时间和群体质量也被正确传递；不同 schedule 不是应该被强行拉到相同终点的“正例”。

对细胞尤其有三个区别：

1. 投影后的 RNA/影像不必是 Markov-sufficient state；同读数、不同隐含染色质状态可有不同后续反应。若只因半群残差大就调时钟或增记忆字段，尚未识别具体原因。
2. 对随机/异质群体，应组合转移 kernel 或分布演化；均值 `E[X]` 的直接/组合相等一般不由个体 Markov 性保证。细胞死亡/增殖还改变质量，不能把 survivor-only 表达分布默认为完整功能状态。
3. 一个模型可完全自洽地预测错误，最简单 `F(x,t)=x` 就符合半群。减少自预测 composition residual 必须同时改善未参与更新的真实功能读数，才有应用证据；不能用一致性本身充当药物效果。

## 3. AP-1 2026：真实存在的 state/action/function/run

主要细胞背景是 **WM989-A6-G3 melanoma single-cell-derived subclone**（降低遗传异质性，不是保证无选择或无新突变）。双 AP-1 reporter 进一步分离为独立 integration clones。原文还报告 H358 KRAS-G12C/sotorasib 的相关剂量适应现象；其独立可用数据数量本轮未认证，不把一段叙述当跨模型验证集。

| 分支 | state / 可观测量 | 真实 action/schedule | function / 输出 | 独立 run 和限制 |
|---|---|---|---|---|
| 主要剂量适应 Fig2B | 同起始 clone；生长/colony；其他 arm 有条码、转录类型 | trametinib低1nM持续、高5nM持续、低2weeks→高2weeks | day28 resistant-colony count | **7 biological replicates**。同一run各arm由同passage/culture起始；原始run→well→schedule键未取。不是7个不同药物任务 |
| 条码分支 Fig2D–E | barcoded sibling lineages、UMI、FateMap expression types | barcode后扩增4–5divisions，再分6arms | barcode survival/diversity、colony-type分布 | Fig2E **4 biological replicates**；barcode/细胞不是独立研究run。支持区别简单选择解释，但模型评估仍需真实键 |
| 阻断适应 Fig2G | 同clone适应期 | low-dose期加JNK-IN-8，再转high-dose；T5224为独立药理支持 | day28 resistant-colony count | Fig2G **3 biological replicates**；作者报告JNKalone在naive无显著growth影响，不等于所有state无off-target/毒性 |
| 乘客记忆 Fig3B | FKBP5/TGM2/LTBP1 single-molecule RNAFISH；同设计ATAC | DEX3days→撤DEX+DMSO vs 撤DEX+trametinib；加JNK从DEX末日进入TM期 | 原始刺激撤去后的基因表达保持/回落；ATAC accessibility | FISH **6 biological replicates**、每run多细胞；ATAC图注 **2 replicates**。这是分子记忆读数，不自动等于后续耐药功能 |
| 初始state→colony Fig4 | 双AP-1 EGFP/mCherry reporter、单细胞time-lapse、descendantcolony | trametinib诱导colonies；reporter验证有PMA/JNK/noAP1motifcontrols | reporter ratio/intensity继承、colony形成 | 原文 **46 tracks**，不是46independent biologicalruns；展示图部分 n1；独立integrationclones不是同一culture重复 |
| 维持/擦除 Fig5 | reportercloneCC10，持续记录phase/fluorescence | TM2weeks→持续TM3weeks vs DMSO3weeks；TM2weeks→A485或SGC-CBP30 2weeks→DMSO1week；另有同步联合 | reporter保持、下降及洗掉抑制剂后是否恢复；colony-growth表型 | 图注明确 **n=1**，只限制该部分，不否定Fig2/3重复。此处function主读数是reporter，不是新一次同药杀伤/长期生存 |

Fig3还做了已耐药但未先诱导DEX的细胞→DEX→撤药对照；其作用是排查耐药背景本身改变一般DEX诱导/回落速度。本文的n1 dose-timecourse不能和n7endpoint混为一个强度；n6FISH的数百单细胞也不能当数百任务。

最贴近父任务的实验证据是：**建立与维持可被不同时间位置的干预分离**。作者将 AP-1/JNK 与建立/适应关联，将 CBP/p300 HAT/bromodomain 与维持关联；撤去trametinib并不自动擦除reporter记忆，CBP/p300抑制后再洗脱也未恢复。此为作者已发表的机制主张和设计，不能重新包装成我们发现的“写入/擦除门控细胞世界模型”。双reporter用于区分cis/trans的论证也已在原文执行。

同样不能把 Fig3 乘客转录保持或 Fig5 reporter 擦除解释成已经证明对同一细胞后续药物再挑战有用。原文设计比普通 snapshots 强，但 state→后续drugfunction的精确 sample/run join 仍需资格。AP-1变化、colony growth、viability和药敏并非可互换的功能标签。

## 4. Public asset：已认证和未认证

Primary availability 明确新NGS在 **GSE311825、GSE311827、GSE311829**；再分析数据为 GSE97682、GSE161300。作者 code 为 **github.com/arjunrajlaboratory/cellularmemory**；all raw/processed 链接是论文列出的 Dropbox folder；Source Data 随文提供。

本轮只认证这些**公开声明/指针**，没有取manifest或dataset。尚未认证：每个GSE是哪种assay/条件、sourceworkbooksheet/celltype、全部schedule/run/sample键、Fig2function与Fig3/Fig5state是否同run配对、图像追踪表是否含全部attempt/失败、跨clone的真实任务数、独立验证cohort，以及能否组合成one-step transition数据。不能因为两个图都用WM989而硬join。

具体下一最小对象应是 **Source Data/作者repo的文件manifest和身份字段**，不是先下载FASTQ、图像包或训练模型。优先核验：Fig2B/G的biologicalreplicate→arm→colonycount；Fig3B的同run跨arm/时间FISH与ATAC；Fig5的reporterclone/well/time/处理前后连接。若这些只能以不同图的aggregate提供，按aggregate机制复现或描述报告；停止其作为可训练state-transition/agentfeedback资产，不停止全部生物问题。

## 5. 值得保留的极小机制空间及反证

可以保留一个**尚未给出新算子的具体问题**：连续暴露、撤药和选择性第二干预的分支，能否使同一模型更新只修正“持久状态的写入/维持/擦除关系”，从而改善未用于本次反馈的其他分支/后继clone上的功能预测，同时保留已知瞬时反应？

形式上把cell dynamics `Fθ(x,u,Δ)` 与model update `Uψ(θ,Dfeedback)` 分开。原Deep-OSG约束F在固定条件下的时间拆分；拟研究的是U产生的θ'在**多个真实干预分支**上有没有可迁移约束和额外样本收益。ψ的跨任务继承与细胞的cis epigeneticmemory不是同一个现象。

支持理由：

- 原论文有选择性干预和时间位置对照，可针对“只让所有表达一起衰减”的粗糙修正提出反例；不同阶段的动作不是任意词串。
- naive-Dexreversal、DEX→TMmemory、JNKencodingblock、TMwithdraw、CBPp300erase的响应模式不同，能够否证错误的通用可逆/交换/单时间常数约束。
- 如果未来身份资格证明相同run的state/function配对，可能不必下载新组学便能研究反馈应改哪个转移，而非泛泛在线增加数据。

最强反对与止损边界：

- 把这些分支残差加进一个训练loss，或从候选中选λ/小模型，就是普通constrainedfine-tuning/regularization/search；如果新稿的Uψ仅是这一步，它在操作层仍没有新贡献。**不能把这个测试问题本身当算法。**
- 这不是要求universal direct不能表达；应比较相同state、标注、预算下的普通受约束更新、controlledODE/latentstate/分层模型、directhistory和简单mixture。若新组合给出一项明确生物识别条件、可验证样本/计算性质或稳健的分支外收益，可以是实质贡献；当前尚未提供。
- 已知AP-1/write、CBPp300/maintenance/erase不能当新生物发现；要说明新技术处理了原作未做的哪一种反馈与迁移。n1擦除分支不支持大规模improver继承统计；n7/n6其他分支不能自动补足它。
- 只下降自预测compositionerror可能是collapse；真实branchprediction不改善则停止该配置。只有continuousarm的改善、没有withdraw/secondaction外推则不支持该核心主张。
- 即便θ'更好，也不是RSI。需有明确ψ0→ψ1改动，然后在未用于改ψ的后续更新机会中比较它们各自产生的改进。当前资产是否有足够独立机会未认证。

因此建议**资格新AP-1资产，但暂不批准新架构或把任何机制命名为创新**。若资格后只剩aggregate/不配对，保留它为世界模型应满足的biological counterexample suite或外部机制stresscase；suite有用途但不是新算法，不以此宣称用户目标完成。

## 6. 失败、限制和待交叉事项

脚本两处本地探索错误已纠正并保留记录：首次PubMed projection错误地搜索所有后代ArticleId，可能把参考文献ID归给主文；在任何source选择/报告前改成精确 `PubmedData/ArticleIdList/ArticleId`，最终 `ADAPTATION_PRIMARY_LEADS.json` 为修正版本。最初HTML投影依赖maestro没有的bs4，报ModuleNotFoundError；改用标准库HTMLParser，无安装/额外网络。它们是检索/解析失败，不是科研阴性结果。

本轮没有新hiddenoutcome、API模型提案、拟合、软件测试或生物实验；所有来源结果是作者已发表叙述。没有完成新的causal-representation全文覆盖；没有以abstract代全文；没有把新paper发布时间当新颖性保证。独立支持稿/具体机制稿尚未交叉，后续须对照其真实算子、source身份和stop规则实际质疑，再另记cross。
