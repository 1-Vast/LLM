# 独立支持方文献审查：什么证据才说明改进策略使后续改进更有效

2026-10-22。本稿在阅读其他新评审稿之前完成。未读取任何 AZ 实际响应、模型或实验成绩，未运行生物拟合，未改动任何 AZ 冻结文件。只评审六篇不同的一手工作；DGM 和 SEAL 在核对 arXiv 最新版本后分别以 v3、v2 为准，旧版本下载留档但不另算工作。所有 GET 的 URL、UTC 时间、状态、body/hash 见 `SOURCE_RECEIPTS.jsonl`；当前六篇正文 SHA 已逐一验证，索引见 `SOURCE_RECEIPTS.md` / `.json`。两次早期发现请求的解析失败及保存缺口在 `WORK_AND_FAILURES.md` 如实记录。2026 年两篇均是新公开预印本；下文不把其作者自报结果当成已独立复现结论。

## 独立结论

**“学习改进策略”可以是有意义的操作性能力，但这一概念、若干机制和同起点评测设计都已有明确前例，不能作为新的算法核心。** 冻结 LLM 权重不等于冻结改进策略：提示词、可执行工具、模型/算子选择统计、研究记忆和更新规则参数都能改变改进的分布。反之，继承更好的模型/程序、沿一条轨迹继续搜索、最终分数上升，都不足以证明后来的改进器更有效。

最稳妥的区分是**被改进的对象与产生改进的对象，以及有针对性的对照**。把后来的改进策略单独移植到完全相同的研究起点，给予相同观测权限和预算，检查其产生的后继系统在未参与选择的任务上是否更好。无须要求改进器必须重写代码，也无须无限追问“谁改进了改进改进器”；一个有明确状态、训练来源和替换试验的策略更新已足以检验用户所说的“改进策略本身使后续改进更有效”。更强的加速/复利主张则需额外证据。

**支持继续做一个最小的后续能力实验；反对现在将“世界模型+策略记忆/程序搜索”包装成新 RSI 核心。** 后续的真正技术候选只能是某个被数据支持的细胞干预结构，使改进决策比通用上下文策略或等预算程序搜索更能迁移；目前本次文献审查并未发现或验证这种结构。当前普通结构实验的任何结果不在本稿输入中，故没有据其授予后续数值实验许可。

## 六篇原文逐项判断

### 1. DGM，最新 v3（2026-03-12；原始 2025-05-29）

来源：<https://arxiv.org/html/2505.22954v3>，Zhang 等，*Darwin Godel Machine: Open-Ended Evolution of Self-Improving Agents*。

方法是冻结 foundation model、进化 coding-agent 自身的 Python 工具与工作流，并积累可分支的 agent archive。v3 §3 明确其可修改的 agent code **不包括外层 open-ended exploration 过程**；不能说所有外层控制规则均自主重写。§4.3 的 fixed-base-meta-agent 对照确实是有关改进器的有力前例，不应降格为“只是重训练”。但完整两臂会走到不同 archive/solver 状态；它测允许改进器变化对整条搜索过程是否有帮助，不能独立识别某个后期改进器在共同状态上的增益。

v3 增加重要的、不可忽略的产品迁移证据：§4.4 报告 SWE-bench 进化出的 agent 在从未用于该进化的 Polyglot 上 28.9%（base 14.2%），反方向迁移 24.5%（base 20.0%）。这比只报搜索子集强，应保留；仍不等同于“其后代生成能力已在同起点独立测得”。原文 §1 与 §6 明确依赖一个假设：coding benchmark 能力反映自我修改能力。该假设合理但可失败，不能被定义为真。

预算/评价：80 轮进化，分阶段较小到较大任务集评价；原文的人工 agent 对照在相同 benchmark subset 上比较，但这不自动意味着全部开发、LLM、候选失败与评价 CPU 成本相同。若借用其范式，应在本项目记录全过程实际成本，另做真正的策略替换。

定位：`dgm_v3.txt` 231（关键假设）、499（外层控制不在可编辑 code 范围）、555（80 轮）、633–647（两个消融）、760–763（跨 benchmark 未见任务迁移）、840（限制）。

### 2. AlphaEvolve（2025-06-16 v1；版本 API 未发现更新）

来源：<https://arxiv.org/html/2506.13131v1>，Novikov 等，*AlphaEvolve: A coding agent for scientific and algorithmic discovery*。

不能把它简单称为“固定 LLM、固定提示词的搜索”。§2.2 明确含 **meta prompt evolution**：额外生成指令/上下文，在独立数据库中与 solution programs 类似地共同进化。§2.1 还明确可以进化一个在固定计算预算下寻找解的搜索算法，甚至共进化中间解和适合它的搜索程序。因此“把研究程序当程序进化”“同时进化解和搜索规则”“更新提示词”都不足以构成与它的实质区别。

核心 archive、evaluator、generation pipeline 与多模型能力并不因为程序在变化就自动变成被改进的对象。若新项目让一个函数/提示控制未来更新，应检验它作为改进器的能力，而不是仅展示最终发现的程序更强。原文中我未见独立的早期/后期 improver 在完全同一 solver/state、同预算上的替换实验；这是一项“原文中未找到”的证据范围陈述，不是声称该系统做不到。

预算：evaluation cascade 会给不同候选不同评价量；一个新 solution 的评估可达百计算小时量级，异步设计优化吞吐。程序 evaluation 次数、LLM calls、总 token、评价算力和总成本必须区分。对照只匹配已接受候选数会漏记 rejected proposals、meta prompts、novelty checks 与昂贵评估。

定位：`alphaevolve.txt` 902–915（进化搜索算法/共进化）、916–937（meta prompt evolution）、982–1044（cascade、并行、吞吐预算）。

### 3. ShinkaEvolve（2025-09-17 v1；版本 API 未发现更新）

来源：<https://arxiv.org/html/2509.19349v1>，Lange、Imajuku、Cetin，*ShinkaEvolve: Towards Open-Ended And Sample-Efficient Program Evolution*。

这是对“反馈使策略学习”的直接强前例。§3.3 更新 UCB1 风格的 LLM 选择概率，使用相对 parent/initial 的收益，经 `exp(max(delta,0))-1` 变换并归一化；同节每隔 T generations 总结成功策略，形成 meta-scratchpad，建议会加入后续 mutation prompts。这些是改进策略的可学习状态，即使外层 bandit 更新公式固定、LLM 权重不变。

§5 比较 adaptive bandit 与固定 uniform ensemble，比较 weighted parents、hill climbing、always-initial-parent best-of-N，比较 novelty rejection/no rejection。它已覆盖许多容易被重新命名的“新模块”。我没有找到把源任务末期 bandit/scratchpad 单独继承到新任务、重置 solution archive，然后和初始策略在共同起点比较的证据；不能把该缺失变成高层 novelty。

注意证据强度：Figure 9 caption 把 bandit 优势写为 “slightly”，正文用 “significantly”；未据此替作者证明统计显著。circle packing 的 150 指 program evaluations，不应未经核算等同于 150 总 LLM calls 或总成本。AIME 的三次 candidate 评估和后续新年份测试、MoE 更大模型训练，能支持产物的部分稳健性/迁移，但不是 improver-swap。此区别必须保留。

定位：`shinka.txt` 325–355（archive/parent sampling）、610–701（反馈、bandit、meta-scratchpad）、704–731（150 评估）、750–775（AIME）、1170–1208（消融）。

### 4. SEAL，最新 v2（2025-09-18；原始 2025-06-12）

来源：<https://arxiv.org/html/2506.10943v2>，Zweiger、Pari 等，*Self-Adapting Language Models*。

这是比“继承最佳程序”更接近本问题的前例。外循环学习生成 self-edit 的策略；内循环用 self-edit 指定的数据、增广或训练超参数进行实际权重更新；奖励来自更新后性能。它直接用未来适应效果优化“怎么学习”，不是仅优化当前回答。原文用 ReST-EM / 过滤正样本再 SFT，而不是必须发明新的 RL 算法；PPO/GRPO 在其设置下不稳定。原文也明确承认 state 中还含当前参数，所以过期编辑的收益会失真，采用当前模型上的采样/评价。

§4.1 的 ARC 子集是**人为筛到 oracle TTT 可解**的 11 train / 8 evaluation 任务；72.5% 对未 RL self-edit 的 20%，统计单位是 8 个任务生成的 40 个 self-edit configurations，不能写成 40 个独立任务或普适 ARC 成绩。知识整合用不同 passage 的训练/评价分离并与 passage-only、未训练 generator、GPT-4.1 synthetic data 比较。§5 明确有遗忘，未专门优化 retention；学习更新能力不会自然保证继承不遗忘。

也不能过度授予其严格的独立 ψ 因果识别：原文实现同一模型既生成 edit 又被更新，并描述 teacher-student 分离为可能扩展。因此我的结论是它**明确建立学习 adaptation strategy 的方法前例**，而不是宣称所有 proposer/student 状态交换控制均已完成。

预算：单轮 knowledge training 50 passages ×5 completions ×3 seeds =750 inner updates，约两张 H100 六小时；不能把训练后每任务少量 edits 的效率称为总开发成本免费。ARC 各 edit 可选更新超参数，须同时记实际 gradient steps/compute。

定位：`seal_v2.txt` §3 / Algorithm 1（约398–935）、1040–1084（ARC 选择与计数）、1217（遗忘）、2031–2068（训练隔离与50×5×3）、B.5（750 内循环成本）。

### 5. MaD-RSI（2026-10-20 v1）

来源：<https://arxiv.org/html/2610.28201v1>，Cui 等，*MaD-RSI: Model-as-Data for Recursive Self-Improvement of Agent Harnesses*。

方法把多个冻结 executor 的成功/失败轨迹作为共同 harness 优化的证据：收集 query×model×sampling 的响应，按 disagreement 与覆盖选择诊断样本，联合比较成功与失败后建议改 harness。多个模型是训练证据，不是部署时 ensemble。它提醒我们：跨 context/模型的成功-失败对比早已有之；多个评审/多个模型本身不是新机制。

它还很清楚地限制自己的成本主张：shared harness 与四个 independently optimized single-model baselines 的**总和**比较，资源统计不是在相同单次 optimizer 预算下的质量胜出。在四项任务里，其 token 节省与一项成本上升同时存在。main 的 coverage max 和 joint success 可来自不同 baseline harness，原文明确说这些 per-metric maxima 不等于同一配置。借鉴时必须保证研究框架不混用多配置的最佳成绩装成单个系统。

general tasks 三轮、每轮两个候选槽；不同 sampling repetitions 也是实际成本。其主张是更好共同 harness 及跨 executor 泛化；没有直接给出 later-versus-earlier 改进策略在同 solver 起点上的性能比较。failure contrast 可能改进诊断，不自动识别因果，也不自动使诊断策略自己学习。

定位：`mad_rsi.txt` 211–229（方法与范围）、711–717（证据选择与诊断）、940–990（三轮/候选/基线/模型外测试）、1036–1042（比较总成本的边界）。

### 6. Chen、Zhu、Zheng 的 RSI 评价实证审计（2026-10-20 v1）

来源：<https://arxiv.org/html/2610.27610v1>，*Auditing the Product, Not the Recursion: The Evaluation Evidence Behind Recursive Self-Improvement Claims*。

这是原始 empirical meta-research，不是把综述当成某个算法已实现的证明。它对114篇 eligible studies做全文编码，其中90篇自称RSI；作者报告26篇声称更好 improver，只有4篇使用 identical-start artifacts、matched budget。**这直接使“提出同起点策略替换评价”本身失去新颖性。** §3/§4 和 Table 1 区分 final product、累积、重复性、improver gain、compounding；固定 improver 的 loop 也可获得前3类，不因此已证明后两类。

我不独立背书其114篇编码，也不把它引用的算法当成已精读一手方法。特别是 STOP、MetaRSI、Sivia、AIDE2 等只作为**它提出的需核对的前驱线索**：Table 4 和 §7.3 指向已有 same-start improver probes，且有 mixed/inconclusive 结果。后续正式 novel claim 必须回到这些实际原文，尤其 MetaRSI 和 STOP；在本次六篇上限内没有另行下载它们，故本稿不能确认其全部预算与实现细节。

更重要的识别点：两个同分 solver 不等于同状态。若继承的 research memory 带入了解答组件/已训练模型，就不是只交换 improver。evolving-vs-frozen 整条 loop 和 fixed-state swap 各有作用，前者不能替代后者。原文还承认样本框偏向 RSI label、最终细则并未在全样本重新独立编码等限制，不能把它的比例当全领域普遍定律。

定位：`audit_rsi.txt` 553–614（claim/evidence 对应）、1273–1284（off-diagonal/swap 识别）、1483–1650（已有对照表与4/26）、2103–2137（STOP/AIDE2/DGM 区分）、2247–2257（研究限制）。

## 操作性区别：改变哪个状态，检验哪种能力

设一个完整研究起点 `s=(theta,D,p,H,E,B_remaining)`：包括世界/直接预测模型参数、拟合数据、研究程序、已经获得的干预反馈、开发评价器以及剩余预算。改进器 `I_psi` 接收这个状态、决定试什么/查什么/如何更新，产生一个后继程序或模型。保护起来的 audit `A` 不参与提案选择。

`g(psi,s,B) = A(I_psi(s;B)) - A(s)`，其中把所有 endpoint 方向转成“越大越好”。用户关心的直接量是对**同一个 s**比较 `g(psi_later,s,B)-g(psi_early,s,B)`，并在预先定义的后续任务/起点分布与独立完整运行上平均。相同 artifact、模型、原始/变换数据、历史和预算均需克隆；“相同初始分数”不足以保证相同起点。

| 改变的对象 | 可合理称为什么 | 仍不能单独证明什么 |
|---|---|---|
| theta 或最终 research program p 更好，后续直接复用 | 模型/程序继承与产品能力 | 改进器更有效 |
| 固定 proposer 在扩大 archive 中持续选更优 p | 普通累计程序搜索 | later ψ 的共同起点优势 |
| 固定 LLM，提示/工具/路由统计变为 ψ_later | 可学习改进策略状态；需实测 | 新算法或普适递归加速 |
| 后期 self-edit generator 产出的更新更有效 | 学到更新/适应策略（SEAL 前例） | 无遗忘、总代价更低、细胞机制正确 |
| ψ_later 被单独移植后共同起点同预算胜 ψ_early | 指定起点分布上的 improver gain | improver gain 随时间增长的复利 |

程序搜索和策略学习没有绝对的表示边界：一个被搜索到的程序本来就可能是优化器。区别在 artifact 的**角色**和被验证的能力，不在它是代码、自然语言、参数还是 memory。若固定程序搜索也在相同预算发现同样有效的策略，那是必须保留的强普通解释。

可学习的 ψ 不必大：三到五个已审计更新动作的效用估计；哪些失败诊断应触发哪个更新的映射；数据重加权/回放与正则强度；实验选择/评价预算分配；生成 patch 的提示/示例；可执行 update function。UCB/贝叶斯计数、普通 contextual bandit、SEAL 式生成训练数据、meta prompt evolution 都已有前例。评价器若也变，要另有固定 audit；否则“更好”可能只是评分定义跟着变。

## 最简后续实验：先测缺失能力，不把它冒充创新

这是**方案，不是新预注册或数值执行指令**。若当前精确结构任务按既定规则停止，不得用下面的测试复活已暴露配置。若考虑仍未打开的新任务，先完成其独立数据/观测合同与新颖性评审。

具体应用可收窄为：在新的细胞 context 中，用相同已付干预反馈预算，选择一个普通更新程序，使随后隐藏药物响应预测/推荐更好。现有项目尚未打开的 source-model contexts 是可能的功能响应研究材料；其仍是静态功能观测，不能被称为已获得细胞动态世界模型或临床验证。此稿未打开/使用这些 context。若研究问题需要时间动力学或转录状态，应另行验证相应公开数据及任务，不可用静态终点替代。

最小设计如下：

1. 将 source meta-training tasks、策略选择 tasks、最终新 tasks 按独立 MASTER/任务族事先分开；任务总体、观察权限、审计指标及共同起点分布均先写定。每个起点保存 theta、D、p、H 和随机种子。source 训练可以通过随机分配普通更新动作，得到该状态下每个动作的实际后继收益。只保存指导更新的 ψ；单独标记可能携带解答代码/模型的 payload。
2. 只设3–5个有实际不同效果的普通动作（例如同数据普通重训练、保留历史的固定回放/正则更新、一个有明确参数变化的模型更新），加 identity/no-update。预算先固定；一个廉价 pilot 可用每任务8次被评价更新作为上限，并记录失败尝试和所有拟合成本。**纯每episode常数 offset不改变该episode推荐排序**，不可把它当有新动作能力的推荐算子。
3. 在共同后续起点上比较 psi_early 与 psi_later，先只学一个小的 state-to-action value map；冻结 proposer LLM、模型 family、action menu、evaluator 和可获得数据。需做真实 on-policy运行，不能用已知所有候选结果的离线最优选择冒充在线改进。
4. 强对照共用相同 source traces 和选择预算：固定 LLM/固定提示的程序搜索；含 meta-prompt evolution 的普通搜索；固定/均匀动作、UCB 或同输入 contextual bandit；简单检索与投票/混合；无策略状态继承；**只继承最佳 solver/program但不再改进**。常规模型对照仍保留 strong direct、普通重训练、CL、AL、简单混合，并给予相同付费信息或相同观测成本。若动作影响采样，后续 history 可以不同，那是 policy 的作用，但初始 history 必须相同。
5. 分开做两个实验。A：克隆同 solver 起点、只换 ψ，识别 improver gain。B：初始/继承 solver artifact ×早期/后期 ψ 的2×2配对设计，分别测继承主效应和交互，不让“起点本来更强”污染 A。若还要称联合世界模型收益，加一个 matched direct-model 分支；仅在强直接模型同样的ψ/预算对照下才讨论 world×agent 交互。
6. 评价预算也固定，audit任务不能用于策略选择。至少预定独立 MASTER 数和完整loop重复数，按MASTER配对；例如可行性目标60个新MASTER×3独立完整运行，若元数据不支持则先停止可行性而不是把dose行当重复。正式样本数需用source阶段方差/最小实际收益进行事前精度设计；例子不是功效保证。

一个明确的 pilot 成功条件建议是：在共同起点、8次更新评价的预算下，后期 ψ 相比最强普通策略的最终隐藏响应 MAE 至少降低0.01（released fractional单位）且相对降低至少5%，按MASTER配对95%区间下界大于0；这些只是待预注册的实际门槛，不能在看到新任务成绩后挑选。同时要求旧任务保持性未超出事先容忍范围、查询/计算权限一致。推荐U作为完整报告的次要终点，不能在MAE失败后替代主终点宣布成功。若只想检验能力存在，正的同起点差异足以回答狭义ψ问题，但不满足有用性能的科研核心门槛。

**停止条件**：ψ_later 只在更强 inherited solver 上好、共同起点不胜；收益被同输入普通 bandit/检索/等预算搜索解释；继承payload带入解答/模型却称策略；靠多次试验与更大query/评价预算获胜；最终audit用于更新；收益只在已选择的模型/细胞子组；前定实用阈值失败。出现这些情况，保留普通实证并停止把该配置称为新RSI机制。若只证明一个后期ψ更好，可以说 improver gain；若称“改进越来越有效”，至少要再冻结多个早/中/晚ψ，在共同起点分布上做替换曲线并计总成本，不能用一条历史最优曲线替代。

## 有可能值得研究的窄问题与 novelty 门

窄问题可以是：**“模型更新的价值是否比细胞标签/原始dose更能按实测干预响应的几何及模型残差结构跨context迁移？”** 例如一个小的 `value(update | paid response pattern, model residual diagnostics)` 在source上由随机更新对照学习，在新context中决定哪些普通更新值得预算。它要求world/functional representation真的提供了额外信息；把metadata换成一个大latent名字并不构成机制。

这仍首先是普通 contextual policy/meta-learning。可发表的技术贡献必须进一步证明一个具体、简洁、未被现有工作涵盖的可验证结构：该干预表征为何能传递更新价值、何种响应塌缩/不一致会使迁移失败，以及为什么同预算raw-feature策略、强direct、固定搜索、普通更新不能复现收益。有限数据上的相关性不能被升级为普遍充分性或因果定理。**本稿不宣称已找到这样的新结构。**

深入前必须越过四道门：

- 原文核对：先核查 audit 指向的 STOP、MetaRSI、Sivia、AIDE2/相近元优化工作；本次只读到审计的引用与编码，不能把未下载的前驱当作空白。
- 简约性：先固定少量普通动作和一个低维策略状态；若同输入简单bandit/检索已解释，不追加code-rewrite/多代理模块救新颖性。此前被判为普通operator或普通Beta表的核心不得改名复活。
- 识别性：ψ单独移植、相同起点、相同预算，保护audit，并分开solver继承与策略继承；仅“训练时改了meta参数”不够。
- 生物与用途：world贡献、agent贡献、继承、联合交互和后续改进器收益各自有对照；静态药物终点收益不能支持动态虚拟细胞、分子机制或临床药物发现结论。

**最终独立意见：泛化的“学改进策略/存策略记忆/共同起点评测”作为新核心 NO-GO；把一个小型策略替换实验作为尚缺的能力验证 CONDITIONAL-GO；任何更强新机制结论须等待具体生物结构及完整强对照的证据。** 下一步应由不同立场评审直接质疑上述窄问题是否只是普通上下文策略、以及提出的实际阈值/预算是否有用；本稿完成前未读他们的回答。
