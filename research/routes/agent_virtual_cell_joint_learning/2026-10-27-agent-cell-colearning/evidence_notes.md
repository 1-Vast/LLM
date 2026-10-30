# Evidence, search and access boundaries

2026-10-27。面向2025-01-01—2026-10-27的定向近邻核查，必要早期原理不限窗。不是系统综述/首创证明。沿用项目reference，调用安装的lit-survey清单工具入库；本轮不执行作者代码。

## Primary sources actually inspected

R=题录，A=摘要，P=相关正文部分；没有一行代表全面复现。正文原件由reference/papers.tsv登记路径、版本和SHA，原始工具响应在本episode的sources。

| Source | Reading actually received | Decision supported and limit |
|---|---|---|
| [CoMap, 2606.02372v1](https://arxiv.org/html/2606.02372v1) | 协调者完整§3.3（分块）；challenger §3；scout相关方法 | 真实on-policy反馈与想象反思已共同更新policy/model；训练教师有真实完整下一状态，不能直接迁移成破坏性细胞观测的教师 |
| [Co-Evolving Latent Action World Models, 2510.26433](https://arxiv.org/html/2510.26433v2) | 协调者v1完整§3.1/3.2、§4.4前2600/4011字符；scout补§3.3/C.2；challenger v2 §3 | 动作表征/world model共同训练已有；v2为2026-04-06，v1/v2均留存。实际动作适配real→latent，不能据此否定所有latent→real研究 |
| [LAWM, 2512.10016v1](https://arxiv.org/html/2512.10016v1) | challenger §2–3及B联合目标/reward | 状态/动作/动力学及状态条件真实动作decoder已有；轨迹数据条件不同不自动建立新算法 |
| [HIJP, 2610.23615v1](https://arxiv.org/html/2610.23615v1) | challenger §3/§6，2026-10-16版本 | hindsight、goal-conditioned inverse及action-transition consistency已有，不能当本项目独创 |
| [MDA, 2608.09696v1](https://arxiv.org/html/2608.09696v1) | 协调者完整§3（重叠分块）；challenger §2–3/A.1–A.4，截断段已补回 | 机制池、结构/参数后验、VoI、query-sufficient摘要和模型池变化后重学已有；A.4把端到端摘要/机制共训练留未来，不把它说成已实现共同识别界 |
| [OPINE-World, 2607.01531v1](https://arxiv.org/html/2607.01531v1) | 协调者完整§3.3；challenger §3 | 反例触发ontology/model修订并影响探索已有。确定环境精确重放不等于生物机制认证；合并输出缺失处未作为依据 |
| [VCWorld, 2512.00306v1](https://arxiv.org/html/2512.00306v1) | 协调者标题/目录/§3.3（478字符） | 只支持所读symbolic/KG/CoT描述，不能完整判断所有训练能力；challenger未实质阅读 |
| [PRAXIS-VirtualCell, 2609.29221](https://arxiv.org/pdf/2609.29221) | 原始30页PDF存库；仅读前两页题名/摘要，A | 可确认agentic框架先例，不能凭摘要声称没有共同学习。HTML v1 404，依法使用官方PDF恢复 |
| [COPEx, ICML 2026](https://proceedings.mlr.press/v306/guo26g.html) | challenger原PDF页1–5，§3.1–3.4前半 | 动态constraint state、预算、scenario-tree规划已有；已知确定约束转移/静态likelihood不直接提供剩余隐藏群体组成 |
| [BOR, ICAPS 2016](https://web.engr.oregonstate.edu/~afern/papers/icaps16-dolatnia.pdf) | challenger页1–4 | 库存/生产/时间/POMDP早已有，且有生物制备动机；不谎称首次材料与信息控制 |
| [Robust POMDP, 2015](https://proceedings.mlr.press/v37/osogami15.pdf) | challenger §2/§3.2–3.3及上下文 | 局部/矩形ambiguity的robust规划已有；不能把该具体结构当成全部全局共享核问题的现成解 |
| [CLOUD, CoRL 2020 / PMLR 2021](https://proceedings.mlr.press/v155/wang21c/wang21c.pdf) | challenger页2–4/§3；协调者首页核题名 | 联合forward/inverse/state/action及随机响应已有；不是新发现 |

协调者未逐段重读challenger检索的所有原文；依赖其明确记录的原始段落核查。所有检索结论均限于上述范围。标准非矩形全局优化、矩/SOS、列/约束生成、option/off-policy和完整资源belief planner仍是必须补足的强近邻，不以本轮未穷尽证明无人做过。

## Thematic queries: 16/16

P1结构scout 4条，raw分别为scout1/P1_search_raw.json与scout2/query_{1,2}_raw.json：

1. `world model agent co-adaptation task discovery representation learning active goals 2025 2026`
2. `counterexample guided world model learning intervention program synthesis drug combinations`
3. `decision aware system identification predictive state abstraction active experiments bisimulation world model control 2025 2026`
4. `cell perturbation sequential treatment noncommutative operators active learning world model population distribution 2025 2026`

P2协调者4条：

1. `"virtual cell" "agent" "closed-loop" 2025 2026`
2. `perturbation world model agent active learning 2025 2026 scientific discovery`
3. `"decision" "world model" "learning" 2025 2026 value aware model`
4. `"dual control" "representation" experimental design 2025 2026`

**P2原始合并工具响应未在JS中完整落盘且展示截断。** 上述式子来自执行时记录，不伪造完整召回；主要决策来源后来定点读取/下载并核身份，原文响应coordinator/primary_open1.txt。不能从该pass计算完整命中率。

P3协调者4条，域过滤原样见coordinator/P3_queries.json，完整工具返回P3_tool_response.txt：

1. `"virtual cell" ("agent" OR "active learning") 2025 2026`
2. `"value-aware" "world model" 2025 2026`
3. `"dual control" cell population experimental design`
4. `"optimal transport" "experimental design" "cell" 2025 2026`

P4独立challenger 4条，完整原始响应challenger/p4_search_1_3_raw.json与p4_search_4_raw.json：

1. `partially identified Markov decision process model ambiguity robust model based reinforcement learning value function bounds`
2. `latent action world model goal conditioned inverse dynamics feasible action joint learning`
3. `sequential experimental design destructive sampling resource constrained branching samples POMDP`
4. `resource constrained Bayesian experimental design destructive sampling limited biological material sequential allocation`

P4第4条以已核原始JSON为准；challenge_sources.md的手工转录后缀不同，不计为另一查询。逐式机器记录见queries.json。之前三轮35条沿谱系保留，本轮新增16条，不把旧候选当全新预算。定点论文版本/原文读取不作为新增主题扩展，不做完整引文链。

## Access limits, local evidence and final snapshot

两个生物一手预印本的full页面返回403，保留在coordinator/biological_priors_open.txt：*Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation*（10.64898/2026.08.04.742916）；*Inferring virtual cell environments using multi-agent reinforcement learning*（10.1101/2025.11.21.689815）。本轮仅题录/搜索摘要，不能证明其方法是否覆盖本候选。未绕过限制；其它scout的PSR/QWM访问失败与TEB局部阅读也保留。最新生物近邻覆盖不完整，故不作细胞领域首创断言。

最新ON3读取到**正式v1.2**，不是旧summary中的v1.1 provisional。已核结果JSON/正式报告/usage、peek披露和当前protocol/freeze的字节指纹；未重跑效果。原始报告称两跑byte-identical及各门pass，本协调者不把这些自报升级成独立统计审查。统计意义和解释界见report §2。

library_verify_final.json：52篇唯一来源、43份原文文件（36 HTML文件+7 PDF；工具状态按唯一论文计35 downloaded_html，CoLA额外v2使HTML文件多1），另1 abstract_only、3 pending、6 restricted。仍3份旧官方源码快照，本轮新增代码均not_verified；未运行或复现。新增12篇原文及一个额外版本，主manifest由reference_library.py维护。errors=[]、warnings=[]仅表示清单/文件一致性。

source_snapshot.json保存本轮确实使用的来源与关键本地文件的有限SHA/大小快照。最终逻辑复核不等于真实效果；实际独立性、修订次数、操作边界及缺口见record.md和usage.json。
