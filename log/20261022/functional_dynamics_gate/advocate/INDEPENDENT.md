# 独立倡议：在出生／死亡坐标中继承更新强度，而非继承模型权重

2026-10-22，mechanism_advocate。本稿先独立落盘；未读本轮其他 agent 稿或新 DeepSeek 输出，无本轮网络、API、数据 body 访问、拟合或架构实现。只认真展开这一项候选。

**裁决：保留一个很窄的、可由公开计数实验否证的“更新规则可迁移”经验假设；不批准新算法／RSI 核心。** 所给最简操作可以精确实现为普通 count-model 的经验 Bayes 更新，不能另起名字声称新技术。若它在真实跨药物／细胞背景中产生尚未建立的、可复现的反馈效率性质，这种经验贡献仍有可能成立；不能因通用预测器可表示就否定。反之，若只剩已知收缩更新，没有独立真实任务上的新性质，则本候选结论为 NONE。

## 1. 为什么选这个最小对象

历史教训不是“模型还不够大”：20261017 program_revision 的预写 seed 有用，但编辑收益为零；普通／LLM search 也未收回开发成本。20261017 feedback_attribution 中强药物 ridge、常规敏感性更新和信息预算已解释许多改进。近期 ADCC 终点分离不能识别动力学，WM1366 normalized-death 曲线在 wash 后不是累计死亡，Response-Dynamics 的早期 growth 已是作者发现；不能把这些重命名。

我尝试把“物理模型定位哪里错”压到最少可观察量：**同一培养孔随时间的 live count 与累计 death-event count**。不用 RNA、完整家谱或洗脱；也不把 OD／normalized dead fraction 冒充这些计数。应用是用稀疏早期真实反馈修正后续绝对 live/dead trajectory，区分抑制出生与增加死亡的时间响应。

## 2. 具体操作：物理残差怎样变成更新程序

在一个不含移液移除、进出视野或未校准 dead clearance 的短窗口 I 内，记：

- L(t)：活细胞数；K(t)：累计已观测死亡事件数；
- E(I)=∫_I L(t)dt：live-cell exposure；
- D(I)=ΔK；B(I)=ΔL+ΔK：从 balance 得到的 birth count。

假设窗口内 birth/death 强度 b、d 近似常数，且每次 division 使 live count 净增1，则 `Ldot=(b-d)*L`，`Kdot=d*L`。物理坐标的残差是 `r_b=B−b0E`、`r_d=D−d0E`。E 的数值积分和计数误差也需进入观测模型。这只是定位数据支持的 net birth/death mismatch；不能从 noisy counts 直接宣称分子机制。

模型起点 θ0 给出 b0、d0。最小 updater ψ 只含两个非负 pseudo-exposure κ_b、κ_d：

`b1 = b0 + r_b/(E+κ_b) = (κ_b b0+B)/(κ_b+E)`

`d1 = d0 + r_d/(E+κ_d) = (κ_d d0+D)/(κ_d+E)`。

这段程序是明确的可执行更新映射 `Uψ(θ0,feedback)`。κ=0 时完全相信当前窗口计数；大 κ 时保留原模型。它比“让智能体重写任意模型”少得多：只有 birth/death 两种实际可辨认的修正量和各自可信度。出生与死亡的 residual 必须由原始计数和同一观测模型得到；若 B<0、tracking/removal 未交代或 K 并非累计事件，就不能强套。

**继承操作：** 在历史独立实验任务上，用一段 prefix 产生上述更新，并在该任务未用于更新的真实 continuation 上评价；仅据这些已完成机会把 ψ0 修成 ψ1。随后锁定 ψ0/ψ1，把后续每个独立机会的 θ 重置成完全相同 θ0、给完全相同 feedback，再比较两程序产生的 θ1 的真实 continuation loss。任务-specific b1/d1 不跨任务携带。允许共同 frozen prior／backbone，但两组必须相同；不能把新训练 θ 偷算为 ψ 改进。

这明确区分了“权重 warm start”和“更会用同一反馈修模型”。ψ 仍然是普通更新程序的参数，不因为叫 updater 就有算法新颖性。

## 3. 唯一值得否证的经验性质

候选经验主张不是“Bayes 更新有效”，而是以下跨任务性质：

> 对独立的药物／细胞背景和真实批次，出生与死亡通道的“多少反馈才应信任局部残差”在 physical exposure 坐标下具有足够稳定的可迁移结构，使仅继承这两个更新强度，比在每个新任务从零选择更新强度更省反馈，并且该收益不能由共享 θ、总体敏感性重校准、单通道 net-growth 模型或更多计算解释。

它具体预测 birth/death 两个 κ 的可迁移差异，而不只是所有通道同一 shrinkage：ψ1 必须比共享单 κ、通道置换 ψ、task-permuted feedback 学出的 ψ，以及 fixed ψ0 更好；只有双通道全 refit 更好而 ψ1 无 future update gain，主张失败。细胞数／时间单位改变时，E 和 κ 必须一致变换，防止用单位选择制造 transfer。相同 start/feedback 下比较 ψ 产生的改善，不靠 ψ1 更多参数或更多反馈。

即使成立，这也只是一个很窄的跨实验 update-law 经验性质；不是证明所有细胞共享 birth/death dynamics，更不是新 molecular memory。

## 4. 精确已有方法归约，不能规避

给 b,d 独立 Gamma priors，prior mean 为 b0,d0、rate 为 κ_b,κ_d；对 B,D 使用以 E 为 exposure 的 Poisson counting likelihood。posterior mean 正是上面的 b1,d1。若 b0/d0 本身由别处估计，需传播其不确定性；不能把它们视作无误差真值。

因此整个最小修正步骤被普通 birth-death inference **逐项精确复制**；用过去任务 continuation 调 κ 是 empirical Bayes／meta-learning of a shrinkage updater。它也可以由相同候选空间的 equal-budget search 得到。这里不复活已经停止的固定 Gaussian residual/kernel 新颖性：本候选非 Gaussian，但换 likelihood 本身不足构成贡献。

这意味着：

- 不能宣称“提出新 learned optimizer”“发明物理误差局部化”或“首次使世界模型自我修复”。
- 相同 residual 特征、likelihood 和 κ-learning 的普通更新器是实现等价对照；它应当打平，不能要求胜过自己。若最终所谓核心只等于这个实现，算法核心 **NONE**。
- 仍可问上述跨真实系统的经验性质是否新、是否有足够应用价值。已知组件在某个新生物识别／反馈效率条件下成立，可以有科学贡献；但必须有原作未回答的问题与近邻一手查新，不能凭本稿成立。

## 5. 所有强比较如何逐项落地

| 对照 | 必须给的相同信息／预算 | 它能否解释结果／本候选需报告什么 |
|---|---|---|
| 强 direct predictor | 完整 action/dose/time、同 live/death prefix、同历史任务、同 θ 基础特征与反馈 | 直接预测 continuation；若它同样做到而本候选无实用样本／计算收益，不能以“可解释”掩盖性能不足 |
| 普通 refit | 相同 count likelihood、相同窗口与参数化；含 joint birth-death MLE、固定正则及普通 EB | EB 同参数同准则是精确等价；对其它 refit 只评估未来反馈效率，不把不同信息当算法差 |
| CL | 相同 task stream、历史 replay、可用反馈和模型容量 | 与共享 θ、shared prior、ψ-only、两者共享四组分账；收益只来自 θ 不支持更新规则继承 |
| AL | 相同实际可查询的已存在 observation menu 与 costs；固定 queries 先比较 ψ | 没有真实可节省的独立 acquisition unit 时不虚构湿实验收益；AL 不给 ψ1 更多／更有利数据 |
| 简单 mixture | persistence、local net-growth、birth-only/death-only/full refit 的固定或经历史学习的混合 | 若混合相同表现，不能宣称必须局部模型修复；birth/death readout 贡献与更新程序贡献分开 |
| equal-budget program search | 相同 κ 范围、相同 count feature／likelihood、相同历史 continuation access、所有 trial 与失败成本 | 可搜索同一 ψ，可能完全相同；搜索若同等或更好，停止额外 agent/search 方法主张，不把其排除为“非RSI” |
| 同特征 learned optimizer | 相同 `(B,D,E,b0,d0)`、相同参数与历史目标 | 最简版本与本法等价；作为公开归约，不算应被击败的另一个新方法 |

世界模型贡献先比较：给定相同 feedback，把生死平衡模型与强 direct／单 net-growth／简单 trend 比对真实 N(t)、K(t)。若只改善 r_b/r_d 自洽残差而不改善真实 continuation，停止。agent 贡献在这个最小方法里不预设：没有额外有效选实验／修程序行为就报告 **no demonstrated agent gain**。

## 6. ψ1 是否真的“更会改”：可失败的未来检验

对每个未来独立机会 j，固定同一 θ0j、feedback F_j 和 untouched continuation T_j。定义：

`gain_j(ψ)=Loss(θ0j,T_j)−Loss(Uψ(θ0j,F_j),T_j)`。

核心 contrast 为未来 mean gain(ψ1)−gain(ψ0)，不是 ψ1 当前模型绝对分数更高。ψ1 从历史 repair opportunities 获得，T_j 在 ψ1 锁定后才揭示；drug/cell背景的分组拆分与 biological run 才是单位，连续时点和 technical wells 不当独立改进机会。

未来 gain 的更高本身还不够：要与**普通历史 κ tuning／EB、相同空间等预算搜索**比较。若 ψ1 与普通 tuning 一样，只能报告常规 meta-update 的继承收益，不能报告新 RSI 算法。若以后再改 ψ-learning 的程序 Ω，要另锁 Ω0/Ω1，在未用于改 Ω 的机会流比较它们如何产出 ψ；本轮不预设必须无限递归，也不提前宣称该层已存在。

推荐最小门槛（正式数值访问前需据任务数量锁定）：ψ1 的未来 paired improvement 有 run-clustered 95% 下界>0，并相对预定 loss 至少有 10% 的实用改善；至少一个 drug/cell group 外推成立，且不是只缩小同批次技术噪声。门槛不可通过事后选择窗口、通道或任务重定义。如果任务数不足以测到，则停止继承／RSI性能主张，不能用更多 cells 补 n。

## 7. 可获得数据路径与最低资格；不要求新湿实验

本候选优先用已有公开 live/dead count time-lapse 资料回放固定反馈，不要求新做 lineage／washout／RNA。根据一般领域记忆，STACK／fractional-killing 类方法常含活细胞标记和死亡染料连续读数；**这只是待核验的 primary/source lead，不是已认证本项目资产，不声称有具体 manifest、独立批次或可用累计事件**。有界下一步应先认证一个原作明确的 raw count table／导出 schema 与 run/drug/cell keys，再决定是否值得取数。

已审项目资产不能硬补此缺口：

- WM1366 Suppl Data03：只有 normalized dead fraction、一个可定位 imaging export，无 raw L／K 与独立 run holdout；不能做这项 reaction-coordinate identification。
- Response-Dynamics：真 growth／reporter 时间序列与独立 population OD，但 OD 非 death，genotype/cell/time 不是独立未来改进流；不满足目前双通道 κ 的资格。
- ADCC：4/24/48/72h CTG 与 growth controls 可以做 net viability 拟合，不能直接当同孔累计 death events，也不足未来 updater 任务流。

因此本稿没有一个已合格、可立即跑完 ψ 继承的 task stream。下一对象必须是已存在的公开小表及 schema，不是新 wetlab；若一个有界资格后仍无真实累计事件／可解释 dead-clearance model及独立 run/group，停止这条路线，不追加架构。

## 8. 成功／停止与当前裁决

先后次序应是：source keys／count semantics→普通物理模型是否确能定位 net birth/death residual→相同 θ 起点的 ψ-only future gain→常规 EB／refit／CL／AL／mixture／search 归因→近邻一手新颖性。前三步失败即停，不让程序编辑掩盖缺数据或简单模型不足。

**停止条件：** count channel 不可辨认；只有一独立 run；growth/death feedback 相比 net-growth 不提供实用 future endpoint 收益；ψ1 不能提高未来 gain；通道置换／共享单κ同等有效；或普通同信息搜索／EB完全解释收益且无新生物经验性质。所有失败分别记为 source/identification/performance/novelty，不混写为 biology negative。

**当前：不实现，不调用 DeepSeek，不开始拟合。候选仅剩待验证的“物理坐标中的通道特异更新强度可跨真实任务继承”经验性质；已知数学本身不新。若无法给出合格公开任务流或新于普通 EB 的经验识别主张，结论明确为 NONE 新核心。** 这比扩大可编辑程序空间更可证伪，但尚未完成用户总目标。

## 9. 本轮暴露与限制

本轮读了先前 program_revision／feedback_attribution README、上一轮 Response-Dynamics 与 WM1366 source qualification 报告，未读其 response arrays。检索旧文件时读 `log/README.md`，其中索引一行已写入 E.faecalis gate 的比较数值；这是额外 designer exposure，已告 parent，不用于本候选推断。没有读取原 pilot response／结果文件。不得继续声称自己完全未见该 gate 数值。

无新网络、API、数据 body、代码实现或生物结果。本文的 Poisson／Gamma 归约是解析机制审查，不是针对数据的拟合证据；跨系统可迁移性、count-noise 假设和来源可得性均未验证。
