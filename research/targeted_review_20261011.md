# 面向 MAESTRO 双核心系统的定向文献综述（2026-10-11）

## 项目现状与文献问题映射

仓库 `research/REPORT.md` 已明确记录：421 个已暴露化合物的自适应回放相对最强 calibration-selected Gaussian batch 基线仅 +0.00217（95% CI [-0.01562, 0.01970]，Holm p=0.40643），需要 16 次周转而批量基线只需 1 次；总体 simultaneous 90% coverage 为 90.74%，但 active-drug coverage 仅 62.38%；secondary screen 未确认收益；本轮策略确定性，普通 LLM tool loop 与 proposed agent 相当。故下一轮不应再以“增加反馈轮数”作为创新，而应验证：在预先固定预算和周转成本下，少量反馈是否降低 selected-set decision loss，并且选择条件下仍保持覆盖率。

## 1. 哪些观测值得购买、何时更新、何时停止

| 方向 | 关键论文/资源 | 可迁移的机制 | 对本项目的具体用法 |
|---|---|---|---|
| 批量主动学习 | Kirsch et al., **BatchBALD** (NeurIPS 2019) | 用联合互信息而非逐点 entropy，处理批内相关性，避免一批买到冗余样本。citeturn1search18 | 将 plate/turnaround 作为一个 cluster，比较 `joint information per turnaround` 与逐候选 acquisition；报告同预算 hit utility，而非只报告 posterior entropy。 |
| 药物组合主动学习 | **BATCHIE** (Nature Communications 2025) | Bayesian posterior + PDBAL + submodular batch；按 posterior 更新批次，并在预算耗尽或后验收敛时停止。citeturn0search2 | 将现有 16-readout policy 改为 cluster-level acquisition；停止规则写成预注册的净值阈值：\(\max_a \mathrm{EVSI}(a\mid D)-c_a\le 0\)。 |
| 成本敏感主动分类 | Greiner, Grove & Roth, **Learning cost-sensitive active classifiers** (Artificial Intelligence 2002) | 观测价值必须同时扣除 acquisition cost 和错误决策 penalty；一般测试集合上的最优策略可能难解。citeturn0search1 | 把“活性候选漏选/误选”的 utility penalty 与 plate turnaround、测量价格、deadline 统一写入目标；不要用未校准的 information gain 替代 decision value。 |
| 成本变化 BO | Cost-varying BO 文献（AAAI 2025） | 当不同 observation 有未知/随机成本时，需要显式建模成本，不能假设 cost 已知且恒定。citeturn1search33 | 为每个 observation 记录 plate、等待时间、失败概率和实际收费；做 oracle-cost 与 estimated-cost 两个条件，避免成本低估造成虚假收益。 |
| 机器人主动感知综述 | **Active learning in robotics: A review of control principles** (Mechatronics 2021) | 观测是“动作”；需要将信息度量、动作生成、实时约束、安全与恢复放到同一闭环，而不是只优化静态 uncertainty。citeturn0search3 | 把“买 readout/不买/终止”视为 action；评估 latency、失败和不可逆预算消耗；使用 receding-horizon policy 与固定批量 policy 对比。 |

建议的最小决策量：对候选集合 (S) 定义终点 utility (U(S,Y))，对观测 (a) 定义
\[
\mathrm{NetEVSI}(a\mid D)=\mathbb E_{y_a\mid D}[\max_S\mathbb E[U(S,Y)\mid D,y_a]]-\max_S\mathbb E[U(S,Y)\mid D]-c(a).
\]
只有当 NetEVSI 的保守下界大于 0 且超过预注册的 minimum useful benefit 才购买；否则直接执行 batch 或停止。更新应由“候选排序改变/selected-set loss 降低”触发，而不是每次得到反馈都更新。

## 2. 关键候选与完整决策过程的可靠性

| 方向 | 关键论文/资源 | 迁移结论 |
|---|---|---|
| 深度 Bayesian active learning | Gal, Islam & Ghahramani, **Deep Bayesian Active Learning with Image Data** (ICML 2017) | BALD 用参数不确定性与预测熵之差选择样本；CV 场景显示 epistemic uncertainty 可用于 acquisition，但不等于选择后 coverage。citeturn1search45 |
| 选择条件 conformal | **Confidence on the focal: conformal prediction with selection-conditional coverage** (JRSS-B 2025) | 针对 top-K、优化选择和 conformal p-value 等 selection rule 提供 selection-conditional coverage，并在 drug discovery 应用。citeturn1search42 |
| 批内相关性 | BatchBALD | 对“最终选中的一组药物”应校准 joint event/selected-set，而非平均逐点区间。citeturn1search18 |

对本项目，主指标应从总体 90% coverage 改为：
\[
\Pr\{Y_{S(D)}\in C_{S(D)}(D)\mid S(D)\text{ selected}\}\ge 1-\alpha,
\]
其中 (S(D)) 是依赖数据和策略选出的 active set。必须在 nested calibration 中冻结 selection rule，按药物、cell line、plate cluster 和完整 episode 分组；报告 top-1/top-k coverage、false discovery/omission、interval width、selective risk 和 worst-lineage coverage。若 active coverage 仍约 62%，停止任何“agent 提升决策”的论断。

## 3. 预测如何连接到生物终点

BATCHIE 的实验范式明确把预测模型、posterior uncertainty、批次设计和最终体外验证分开；其贡献不能替代同单位 endpoint bridge。仓库现有 `BRIDGE_NOT_SAME_UNIT`、`CONTEXT_UNDERCOUNTED` 和 `plan_measure_or_predict` 规则与这一要求一致。下一轮应采用三层门槛：

1. **same-unit bridge**：同一 culture unit、dose、time、platform 同时得到 forecast readout 和 functional endpoint；
2. **reference ceiling**：用 observed readout 替换 forecast，leave-one-context-out 后相对最强 cheap prior 达到预注册 MUB；
3. **independent confirmation**：在未参与 STATE 训练/参考拟合的 biological units 上重复 selected-set utility，并保留 QC failure/nondetection 的 missing mass。

跨平台 basal RNA 对齐只能证明 axis identity，不能证明 response transport；因此应将“平台/剂量/时间 transport”作为单独 null/control，而非在主结果中合并。

## 4. Agent 的独立贡献与方法创新

| 方向 | 关键论文/资源 | 对 agent claim 的约束 |
|---|---|---|
| ReAct | Yao et al., **ReAct** (ICLR 2023) | 将 reasoning trace 与 action 交错，用行动获得外部信息并处理异常。citeturn1academia97 | 只能说明一种 tool-loop 组织方式，不能证明生物决策增益；必须记录 action trace、invalid actions 和 cost。 |
| Toolformer | Schick et al., **Toolformer** (NeurIPS 2023) | 学习何时调用 API、调用什么参数、如何吸收结果。citeturn1search2 | 可作为“普通 LLM tool loop”基线，但不应把 API 调用能力当作 scientific value。 |
| SayCan | Ahn et al., **Do As I Can, Not As I Say** (CoRL 2022) | 语言模型语义相关性与机器人 affordance 相乘；可执行性约束可以覆盖语言模型建议。citeturn1search4 | 双核心系统应将可购买观测、预算、条件和 QC 视为 affordance mask；LLM 不得输出不可执行/不合规动作。 |
| Voyager | Wang et al., **Voyager** (TMLR 2024) | 通过技能库和环境反馈持续探索；展示长期 memory 与 embodied feedback 的组织方式。citeturn1academia96 | 可借鉴 skill/memory 接口，但其开放世界发现指标不能替代 same-budget biological endpoint。 |
| Agent 实验基准 | Huang et al., **MLAgentBench** (2023) | 评估代码执行、实验迭代和成功率；显示长期规划和 hallucination 是主要瓶颈。citeturn0academia81 | 采用过程级指标：计划有效率、工具错误、恢复成功率、token/latency、单位实验成本，不只看最终 hit count。 |

真正可检验的 agent 新颖性应是“在相同合法输入、相同 observation menu、相同预算/期限和相同 deterministic planner 约束下，agent 能学习或识别何时 observation 的 NetEVSI 为正，并减少 selected-set loss”。如果只是在 prompt 中重述 EVSI、active learning 或使用 ReAct，不构成方法创新。

## 推荐的下一轮最小实验

**研究假设 H1**：在同一 biological unit 和固定 total budget/deadline 下，经过 selection-conditional calibration 的少量反馈策略，比最强 one-shot batch baseline 的 net utility 至少提高预注册 MUB，并且额外 turnaround cost 后下界仍为正。

**三臂（至少）**：

- BatchStrong：同一 posterior、同一候选菜单、一次性 batch acquisition；
- Deterministic-EVSI：相同模型和工具，固定的 cluster-level NetEVSI + stop rule；
- Agent-EVSI：LLM 只负责语义解析、异常恢复和候选解释，实际 acquisition 必须通过相同 deterministic evaluator/affordance mask；另加普通 ReAct/Toolformer-style loop。

**关键对照**：permuted feedback、forecast-only、observed-readout oracle、no-feedback、matched same-posterior batch；所有臂记录实际 plate/turnaround cost、等待时间、失败概率、token/API cost。

**主要终点**：

- net decision utility（以实际成本计）；
- selected-set utility 与 top-k hit/false omission；
- selection-conditional 90% coverage；
- 每增加一次 observation 的 marginal net value；
- independent secondary endpoint 上的确认率。

**停止标准**：预先固定 MUB、最大 turnarounds 和 cost cap；若 Agent-EVSI 相对 BatchStrong 的 paired cluster CI 下界不超过 MUB，或 active-set coverage 低于注册阈值，停止 agent/scientific superiority claim，只保留工程结果。

## 结论

最有希望的论文级贡献不是“LLM + EVSI + active learning”的组合，而是一个可证伪的 **condition-bound, selection-calibrated, cost-aware evidence acquisition**：它在生物 endpoint 自身的 domain 内校准最终选中集合，按实际周转成本购买少量反馈，并在 NetEVSI 不再为正时停止。CV 提供 selection-aware uncertainty 与 batch diversity，NLP 提供可审计的 tool/action trace，机器人提供 affordance-constrained closed-loop action；三者都要求与强 deterministic baseline 在相同资源约束下比较。
