# 支持方独立结果审查与实际交叉讨论

2026-10-22。结论先行：**执行当前冻结方案的 STOP。** 两项预定主性能门均失败，且差值方向与要求相反；局部结构优势和计算速度不能改判，不能据此追加 agent、RSI 或更复杂架构来挽救该配置。停止范围是本次冻结 source/panel、两份 paid 接口、effect 压缩候选和注册模型菜单作为后续扩展根据；不是否定所有静态功能世界模型、所有 monotherapy 信息或整个 RSI 研究目标。

本代理独立读取已经解封的 `TEST_METRICS/GATES/ALL_PAIRED/COSTS/SUPPORT_PLATEAU`，以及后获授权的 `FIT_RUNS` 计时字段；未读 raw ZIP、模型、reserve 数值或重新拟合，未修改方法、阈值、面板、选择或预测。自己的证据摘要与原文件哈希见 `POST_RESULT_EVIDENCE.json`，生成代码在 `research/az_paid_reference_gate_20261022/post_result_evidence.py`。本审查从保存的终点结果独立重算主差值和门逻辑；不冒称自己重跑了 raw-test 评分。反方的完整数值重算属于其独立审计。

## 两项主门明确失败

| 主终点 | effect 候选 | validation 选定普通对照 | 候选收益（正值才有利） | 配对 MASTER 95% CI |
|---|---:|---:|---:|---|
| MAE | 0.077667654 | direct：0.066206799 | −0.011460855 | [−0.012786525, −0.010023394] |
| U | 0.048597279 | combo_direct：0.098467776 | −0.049870497 | [−0.057802529, −0.041956936] |

注册要求分别为至少 .02 绝对改进、至少 10% 相对改进/基线 regret 缩减，且收益区间下界大于零。实际 MAE 比直接模型高约17.31%；U 对应的 regret 比普通对照增加约71.74%。推荐基线 regret 为 .069511995，大于 .02，不能以“没有注册决策空间”解释失败。这里使用两个终点各自选定的策略；effect 的 MAE 配置与 U 配置不同，不能把两行装成同一参数的表现。

30212 个 nominal rows、644 episodes、96 个预定 MASTER 完整覆盖；所有22个报告策略的 coverage 均通过，input/forecast/recommendation episode coverage 与 finite-target-row coverage 均为1。失败是本定义下的性能失败，不能换 complete-case 子组、cancer subgroup、pair、指标或门槛来改判。96 MASTER 的配对 bootstrap 是给定该 screen、面板、训练/验证选择及源归一化下的内部不确定度，不是96个独立湿实验，也不是外部验证。

## 仍应如实保留的局部结果

### effect 相对同容量 dose 有限而真实的优势

预先规定的坐标归因比较中，effect 相对 dose 的 MAE 收益为 **.007757754**，95% CI [.006490712,.009035560]；U 收益为 **.010632225**，CI [.003491082,.017830112]。这是固定模型族内把 residual 的坐标从 dose 改为付费实测 effect 后的局部归纳偏置证据，两个终点仍各自选择配置。两臂都含相同 Bliss anchor 与付费 mono 信息，因此该对照不能被重述成“有 mono 对没有 mono”的因果试验。

这些预计划局部区间不替代两个 co-primary gate，也不构成普遍机制定理或多重探索后挑出的成功标准。它说明低容量 effect 坐标比该低容量 dose 坐标好；**不说明充分压缩后的效应状态能匹敌同信息强直接模型**。事实上后者已明显胜出。

### mono 输入包归因是不确定的终点差异

full direct 相对 without-mono 的 combo_direct：MAE 点收益 **.001161341**，CI [−.000363916,.002687441]；U 点收益 **−.003381651**，CI [−.007283168,.000515178]。两区间均跨零，不能称已证实的稳健 mono 增益，更不能说 mono 无用。

此比较改变整个 mono 输入包及其维度，并允许两臂在同12候选菜单上各自选参，只能作注册 pipeline 的描述性归因，不能升格为纯 mono 因果或独立 per-drug 参数识别。paid mono 来自其他 pair 的 attached observed fields，不是目标组合自身的一份独立 mono 金标准。强 direct 同时使用 mono、完整 paid combo 与设计信息；其胜利不意味着 mono 或所有功能状态无效。

### 普通校准很小，混合与枚举保留普通解释

effect_offset 在 MAE 策略下从 .077667654 降到 .076810636，改善 **.000857018**，对应 effect-vs-offset 收益区间 [−.001211555,−.000525566]。**这是整个 offset family 各自选参后的比较：effect 选 config6，effect_offset 选 config7/eta=.25，不能当作固定 base 模型上的纯 offset 因果贡献。** 它涉及普通 episode 常数校准和配置选择，远不足以接近 direct。按 U 选择时两者 config7、eta=0，effect 与 effect_offset 完全相同；每 episode 常数本就不改变内部 top5 排序，不能把该算子称为新的推荐策略。

两个终点的混合权重都在 validation 选为 w(effect)=0，测试中混合重现 direct。枚举器在 MAE 重现 direct，在 U 重现 combo_direct。既有普通方法已经解释注册菜单的最强选择；不能把枚举器输出叫新的 agent 发现。

### 计算便宜是实际工程特征，但不救性能判决

授权计时记录显示：同样12次 selection pipeline fits 的 fit+prediction 总时间，effect 为 **1.433 秒**、dose 为 **1.196 秒**、direct 为 **3079.554 秒**、combo_direct 为 **1247.388 秒**。effect 确实比这两个强直接实现便宜很多；它没有在此指标上胜 dose。最终缓存拟合中 effect 两次共 .279 秒，direct 一次99.904秒，combo_direct 一次400.968秒；这些是不同次数/配置的记录，不能当成相同单次任务的公平倍速比。

总实验53个 pipeline fits、215个 solver/estimator fits；fit+prediction 4830.856 秒。逻辑付费4208 bundles/192752 rows，物理 unique paid matrices2744/rows125496；不能把重复引用 paid witness 误作独立购买或独立生物复制。`episode_updates=0`，没有此门内 agent 闭环。

这些 timing 只说明固定实现、线程与所测配置上的质量—计算代价权衡。未搜索等实际 CPU 预算的所有强直接配置，也未建立全局 Pareto frontier；不能声称 effect 全局 Pareto 最优、同总预算性能更好、临床更省成本，或用速度重写 .02/10% 的注册门槛。

## 诊断与数据边界

30191/30212 行在训练 effect rectangle 内，只有21行在外；未见训练缺失 target source-pair。inside 的描述性 row-MAE 是 effect .077937073、direct .066155901，因此失败不能仅归咎于大量坐标外推。outside 极少且非 MASTER 宏估计，不能选它作为新面板，也不能外推分布外性能定律。

plateau 诊断覆盖549 episodes、37367个重叠 point-pairs：effect 坐标差至多 .02 而 raw dose 至少一轴相差一 decade，配对加权平均绝对响应差约 .069748943，最大 .940941724。它提示近邻效应坐标不保证相同 released response；但坐标只是近似、point-pairs相关、重复测量与噪声未分离，不能证明精确充分性不成立、因果机制、信息不可能性、或所有 functional world 无效。不把这一描述诊断变成新 hypothesis test。

化学字典资格单独保持 `NOT_ESTABLISHED`，见 `../../az_chemical_identity/QUALIFICATION.md`：source-ID query/target pairs 分离已核，当前11/11 ID 的 sourceID→chemical mapping 未解析；156个跨池化学比较不可裁决。**这既不建立未见化学组合泛化，也不证明别名泄漏。** 不猜药名、合并盐型/stock或改面板。化学不确定性不能被拿来抹掉不利结果，也不能被省略以宣传 prospective chemical novelty。

实际终点是该源约72h CTG inhibition/viability 代理；不是已验证细胞死亡、疗效、临床 synergy 或跨外部 assay 的药物发现。静态 action-conditioned 功能模型可以合法成为 world 组件；这个资格不等于本压缩模型已证明充分性或世界模型贡献。

## 实际双向交叉讨论

以下为与 skeptic/data 通过直接消息实际发生的问答；未读取 peer 新 post 文件后冒写独立判断。

**反方问我：速度若明显更快，是否仍不能救双主门？effect-vs-dose 小优势是否应该保留而不掩盖 strong direct 失败？** 我明确答复两项均同意。之后反方追问速度/Pareto 是否只能是所测点的代价、不是全局 frontier；我明确同意，并按上述真实 timing 限定。没有把支持方立场等同于必须支持继续。

**我的最强反问：STOP 是否被扩大为否定所有静态功能世界、实测 mono 价值或用户 RSI 目标？plateau 是否被当充分性/因果定理，化学未解是否被当 proved leakage？** 反方明确接受精准范围：仅关闭当前冻结二 paid 接口中 effect 压缩候选/本菜单作为 agent/RSI 扩展根据；direct 也用 mono，不能说 mono 无用；近似 plateau 不是不可能性定理；字典未解只限于化学独立未建立。

**反方实际要求我确认 mono CI 跨零。** 我确认不能称稳健正效应，保留 MAE 点正/U 点负及其不确定性。反方通知其首次独立 auditor 因 DESIGN MASTER 顺序与 production 字典序向量未对齐而失败，已保留失败并改为身份对齐；其第二次审计报告47项hash/动作、22策略、全部metrics/gates及24paired bootstrap通过、maxdiff=0。该修正属于 verification，不是模型方法变化；我不把它冒称自己的 raw-test 重算。

**数据方问我：source-ID 与 chemical 独立、CTG 与 cell death、MASTER bootstrap 与外部验证是否必须分开，资源差异是否改判？** 我接受全部边界，明确资源差异不改注册 FAIL。我的反问是是否仍可保留 full/without 输入包终点差异、而不把 candidate 失败写成 mono 全无用；数据方明确接受，同时补充输入维度、选参、paid field 来源的限制。我随后提供两 CI 均跨零的实际数值，确认只保留不确定描述结果。

## 支持、反对、未决及未来验证边界

**支持保留：** 同容量 effect 坐标的有限预测/选择优势、比强直接实现低的 CPU 成本、普通小幅校准、完整覆盖和可审计的封存评测链。它们是可复用的工程/研究负结果资产。

**反对继续本路线：** 两强普通对照都显著优于对应主候选；混合退化到 direct；局部改进不足；没有 agent 更新、solver/策略继承、联合贡献或 C4 的实际试验。此门失败不是 RSI 实验阴性，因为 RSI 尚未被测；也绝不构成 RSI 成功。

**未决：** 特定低维功能表征能否在新的合法任务、完整同信息预算下传递后续更新价值；更丰富静态功能模型是否有必要性；确切化学身份与生物噪声贡献。这些讨论中的未知不会推翻本门 STOP。

**允许的后续方案只到资格与评审：** 封存并复用当前反例、成本与普通基线；若再提候选，先给具体结构假设、普通解释和必要性证据，核真实数据/provenance、合法 development 反馈与独立 future audit、任务级样本量及完整预算，再作不同立场新颖性评审并另注册。C4 需同起点单换策略；joint gain不要求正交互；额外动态主张才需相应时序证据。**不在本审查执行新实验、不打开413 reserve数值、不追加超参/表征/架构或改变已暴露测试。**

