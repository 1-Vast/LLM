# 第二轮实际双向交叉：selection-bound 候选

2026-10-22。advocate=mechanism_advocate；反方=selection_bound_skeptic。双方先各自完成独立稿，再实际发送问题、回复及反问。本文件不把 root 的逻辑核验当真实性能，不把解析反例当生物响应。

## 顺序与版本

1. advocate 已先写 `ADVOCATE.md`，未看本轮其他 agent 机制结论；parent 随后组织 cross。
2. skeptic 确认先写 `SKEPTIC.md`，之后才读 advocate 稿并发出 A1–A4 与 Q1–Q4。
3. advocate 回答全部问题，并反问 common measurement kernel、两类 marginal 与共同 joint null、core promotion 的边界；skeptic 实际作答。
4. skeptic 追加 generation-aware spontaneous switching 反例，advocate 明确接受。原倡议完整保留为 `ADVOCATE_INDEPENDENT.md`，`ADVOCATE.md` 为交叉后修订稿。

无本轮新网络、数据 body、架构实现、拟合、API 提案或生物实验。所有数字例子均为定义级构造。

## 1. 母群条件是否只是必要条件

advocate 问：只给 scalar 汇总，任意 hidden fixed type 与任意选择下，区间交集是否其实充要？

skeptic 答：是。母群量满足 `0≤Z_h≤L_h≤1`，`δ_h=1-L_h`。任选共同交集中的 p，令 type1 总质量 p、type0 总质量 1-p；历史 h 留下 type1 质量 Z_h、type0 质量 L_h-Z_h。可行条件恰是 `Z_h≤p≤Z_h+δ_h`。p=0/1 取退化群体。

advocate 接受并修订：这是**给定未联结母群 observable margins 的宽泛任意选择 null 的充要可行性条件**。并非完整 paired lineage tree／共同早期 branch／时间序列／整数 cohort 的充分性；也不证明现实无 memory。初稿“必要非充分”若不加这个对象限定，表述不准确。

categorical 也相同：`sum_k max_h q_h(k)≤1` 对共同母群支配未联结 subprobability marginals 充要；取 π(k)=max_h q_h(k)，剩余 mass 任意放置。binary q1=Z、q0=L-Z 与 scalar interval 等价，不能算两项独立确认。

## 2. finite samples 与 challenge 随机性

skeptic Q1：随机化只保证母群同分布，不能使有限 arm 的经验区间必定相交。四 founders 含两个固定 responders，随机 2:2 分组，6 个分组中 2 个得到经验 Z=1 与0；δ=0 仍可出现不交。

skeptic Q2：固定概率 r 不是固定 fate。两个 r=.5、完全无损的细胞独立受 B，可一活一死；plug-in 单点差异不表示类型改变。

advocate 接受：理论陈述改为共同母群期望／概率量。正式检验须对实际 randomization、founder 与 run clustering、共同控制和 challenge stochasticity 构建 calibrated simultaneous confidence region。不能将 observed interval nonintersection 直接设为模型编辑 gate；不能把所有后代细胞当独立 n。拟议 ε=.05 仅是未来需独立 calibration 的实用阈值，不是现成有效检验。

root 另报告的穷举纯逻辑核验也发现 2/6 情形；它只是独立确认代数／有限样本反例，未读取真实响应，未测任何药物性能。本 cross 的判断来自实际问题与回答，不以穷举代替反方。

## 3. conditioning 与 challenge 的 missing mass

advocate 问 B 期间删失如何计入。skeptic 答：设 z 为 endpoint 已知活质量、u 为 B 期间 unknown/censored 质量、d 为 B 已知死质量，conditioning 前丢失为 δ，完整 frontier 计数后 `z+u+d=1-δ`，故：

`μ_B ∈ [z, z+u+δ] = [known-live mass, 1-known-B-dead mass]`。

advocate 接受：conditioning 已知死者对反事实 B 潜能仍 unknown，纳入 δ；B 已知死者在此次功能终点贡献 0，不能又算 unknown；B 未知 fate 纳入 u。field exit／segmentation loss／未解分裂均保守计入，frontier 不得同时计母与女儿或多次计算同一失踪分支。初稿只有 δ 的式只适用于 B 无删失的特例。

## 4. null 范围与普通动态反解释

skeptic Q3：半权是 chronological random-daughter path，不是 population cell count；抗药细胞指数增长且无死时质量终点可不变，但肿瘤负荷恶化。

advocate 接受：Z 只用于 fixed-response selection null；N(t)、绝对存活数及应用 utility 必须另外报告。不能把重加权 endpoint 当唯一药物价值，也不能把质量守恒错叫物理 biomass 守恒。

skeptic 追加：与处理无关的每 division 自发 switching，也可在 conditioning 改变世代数时违反 fixed-type bound。例：每代 0→1 概率 q，d 代后的 response fraction `1-(1-q)^d`；h/c 的 d 不同，即使 δ=0 也不同，无需新增 treatment-specific memory。

advocate 接受并收窄结论：拒绝的仅是**固定 endpoint 响应类型的任意选择**。世代数依赖自发转移、细胞周期、损伤、残药、突变等均未排除。不能据拒绝就要求世界模型新增隐记忆／处理特异状态边；普通 generation-aware birth-death/switching dynamics 必须作强反解释。cell-intrinsic operational history effect、epigenetic memory、药物诱导新转移是不同强度的主张。

## 5. q 标签与 measurement drift

advocate 问：history-invariant stochastic measurement kernel 是否保留共同母群限制？

skeptic 答：若明确 `q_h=K a_h`，K 为同一非负 kernel，latent retained measures `a_h≤p`，则 `q_h≤Kp`，共同 π 成立。但这仍是母群／期望；selection 后的 conditional kernel 也要共同成立。只说 unselected baseline assay 一样、却让选择依赖未纳入 type 的 assay noise，不足。K_h 漂移可使 q 违反仅因为 assay artifact 或 dynamic readout 变化。

advocate 接受：state bins、测量映射和误分类界限须前锁；不能搜索分区至违反而不给预算／多重比较控制。固定 drug-response type 不蕴含 AP-1、cell cycle 或 RNA label 固定。状态 bound 拒绝不能代替 B 功能响应变化。

## 6. joint state/function 的两种不同缺口

advocate 问：无配对是否无法定位 state→function，且两类 marginal bounds 各通过不保证同一 joint null？

skeptic 答两层：

- 不唯一：`P(S=1)=P(Y=1)=.5` 同时允许 Y=S 与 Y=1-S；没有 linkage 不能定位中介映射，即便有配对也首先是关联，因果中介还需干预／假设。
- 不必然 joint feasible：h0 的 L=1，q(A)=q(B)=.5，Z=.5；h1 的 L=.5，q(A)=.5、q(B)=0，Z=.5；h2 的 L=.5，q(A)=.5、q(B)=0，Z=0。state `sum max=1` 通过，scalar `p=.5` 也通过。但 fixed joint 要求 baseline `P(A,Y1)≥.5` 和 `P(A,Y0)≥.5`，与 baseline `P(A)=.5` 冲突。

advocate 接受：不能把各 marginal 检验通过叠成 state-mediated memory；也不能反向过度声称“没有配对就不能检验任何 joint restriction”。实际 marginal capacities 仍可产生可检验联合限制，但须明确推导和真实样本设计；本轮不新增一个架构／LP模块，也不将上述已知 coupling 逻辑命名为新算法。

## 7. 新颖性与行动裁决

skeptic Q4：当前是标准 missing-outcome bounds／common dominating subprobabilities＋树路径记账，没有合格资产、新生物观察或额外 temporal/paired 识别约束，是否应只做一次 bounded source/theory qualification？

advocate 明确同意。初稿的“经验候选保留”现降为**资格入口，不晋升核心机制创新**。这不是因为 universal predictor 可表达，也不否定未来有价值的生物观察；而是此时现有完整操作已是标准界限，应用数据与新现象尚未建立。

共同决定：

1. 不实现架构、训练、API 搜索程序或性能实验。
2. 后续若进入资产阶段，仅一次有界核验最邻近一手理论与真实 lineage→division/death/loss→washout→common rechallenge 的 manifest/schema；不得把不完整活细胞 tracks 或不同图的 aggregates 补成完整数据。
3. 若无足够 lineage/frontier/censor/run 键，或只剩已知同条件同结论，停止 core promotion；可保留标准 null audit 用途。
4. 即使未来 calibration 后拒绝 strict null，也需强普通动态反解释与真实 endpoint 外推比较。world、agent、参数继承、联合收益、RSI 各自另验证；本轮均无证据。

## 支持、反对、未决与最终状态

支持：问题针对实际选择混淆，具清楚母群可行性与 missingness 定义；一手 AP-1／ADCC 提供相近真实生物设计动机。标准界限仍可能帮助防止错误机制归因。

反对：代数本身已有标准理论；原始 gate 忽略 finite sampling；固定类型 null 太窄，世代依赖自发切换已给出无需 memory 的替代；完整真实资产未认证，Z 也不是唯一药物效用。

**双方无核心逻辑分歧。** 未决只有实际 source/theory 身份、可得的完整数据、未知经验效应及未来应用收益。没有任何未执行实验被记录为阴性结果。

最终状态：**NONE 当前新核心；保留一次有界资格机会。总目标未完成。**
